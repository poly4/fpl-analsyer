import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from app.services.match_simulator import MatchSimulator, H2HPrediction, MatchState, PlayerPrediction
from app.services.live_data_v2 import LiveDataService
from app.services.redis_cache import RedisCache
from app.websocket.live_updates import WebSocketManager

logger = logging.getLogger(__name__)


@dataclass
class LiveAdjustment:
    """Live adjustment to predictions"""
    player_id: int
    player_name: str
    adjustment_type: str  # "minutes", "goal", "assist", "card", "injury"
    old_prediction: float
    new_prediction: float
    impact: float
    timestamp: datetime
    reason: str


@dataclass
class PredictionUpdate:
    """Updated prediction with live adjustments"""
    original_prediction: H2HPrediction
    updated_prediction: H2HPrediction
    adjustments: List[LiveAdjustment]
    confidence_change: float
    key_changes: List[str]
    updated_at: datetime


class LivePredictionAdjustor:
    """Adjusts predictions in real-time as matches progress"""
    
    def __init__(
        self, 
        match_simulator: MatchSimulator,
        live_data_service: LiveDataService,
        cache: RedisCache,
        websocket_manager: WebSocketManager
    ):
        self.match_simulator = match_simulator
        self.live_data_service = live_data_service
        self.cache = cache
        self.websocket_manager = websocket_manager
        
        # Adjustment parameters
        self.update_interval = 60  # Update every minute during matches
        self.significant_change_threshold = 2.0  # Points difference to trigger update
        
        # Active predictions being tracked
        self._active_predictions: Dict[str, H2HPrediction] = {}
        self._update_tasks: Dict[str, asyncio.Task] = {}
        
    async def start_live_adjustments(
        self, 
        manager1_id: int, 
        manager2_id: int, 
        gameweek: int,
        base_prediction: H2HPrediction
    ) -> str:
        """Start live prediction adjustments for an H2H match"""
        
        prediction_id = f"h2h_{min(manager1_id, manager2_id)}_{max(manager1_id, manager2_id)}_{gameweek}"
        
        # Store base prediction
        self._active_predictions[prediction_id] = base_prediction
        await self.cache.set(f"prediction:{prediction_id}", asdict(base_prediction), ttl=7200)
        
        # Start live update task
        if prediction_id in self._update_tasks:
            self._update_tasks[prediction_id].cancel()
            
        self._update_tasks[prediction_id] = asyncio.create_task(
            self._live_update_loop(prediction_id, manager1_id, manager2_id, gameweek)
        )
        
        logger.info(f"Started live adjustments for prediction {prediction_id}")
        return prediction_id
        
    async def stop_live_adjustments(self, prediction_id: str):
        """Stop live prediction adjustments"""
        
        if prediction_id in self._update_tasks:
            self._update_tasks[prediction_id].cancel()
            del self._update_tasks[prediction_id]
            
        if prediction_id in self._active_predictions:
            del self._active_predictions[prediction_id]
            
        logger.info(f"Stopped live adjustments for prediction {prediction_id}")
        
    async def _live_update_loop(
        self, 
        prediction_id: str, 
        manager1_id: int, 
        manager2_id: int, 
        gameweek: int
    ):
        """Main loop for live prediction updates"""
        
        try:
            while True:
                # Get current live data
                live_data = await self.live_data_service.get_live_gameweek_data(gameweek)
                
                if not live_data:
                    await asyncio.sleep(self.update_interval)
                    continue
                    
                # Determine match state
                match_state = self._determine_match_state(live_data)
                
                # Skip if matches haven't started
                if match_state == MatchState.PRE_MATCH:
                    await asyncio.sleep(self.update_interval)
                    continue
                    
                # Update prediction
                update = await self._update_prediction(
                    prediction_id, manager1_id, manager2_id, gameweek, match_state, live_data
                )
                
                if update:
                    # Broadcast update to WebSocket clients
                    await self._broadcast_prediction_update(prediction_id, update)
                    
                # Stop if matches are finished
                if match_state == MatchState.FINISHED:
                    break
                    
                await asyncio.sleep(self.update_interval)
                
        except asyncio.CancelledError:
            logger.info(f"Live update loop cancelled for {prediction_id}")
        except Exception as e:
            logger.error(f"Error in live update loop for {prediction_id}: {e}")
            
    def _determine_match_state(self, live_data: Dict) -> MatchState:
        """Determine current match state from live data"""
        
        fixtures = live_data.get("fixtures", [])
        
        if not fixtures:
            return MatchState.PRE_MATCH
            
        # Check if any fixtures have started
        started_fixtures = [f for f in fixtures if f.get("started", False)]
        finished_fixtures = [f for f in fixtures if f.get("finished", False)]
        
        if not started_fixtures:
            return MatchState.PRE_MATCH
            
        if len(finished_fixtures) == len(fixtures):
            return MatchState.FINISHED
            
        # Determine state based on average minutes
        total_minutes = sum(f.get("minutes", 0) for f in started_fixtures)
        avg_minutes = total_minutes / len(started_fixtures) if started_fixtures else 0
        
        if avg_minutes < 30:
            return MatchState.EARLY
        elif avg_minutes < 60:
            return MatchState.MID
        else:
            return MatchState.LATE
            
    async def _update_prediction(
        self,
        prediction_id: str,
        manager1_id: int,
        manager2_id: int,
        gameweek: int,
        match_state: MatchState,
        live_data: Dict
    ) -> Optional[PredictionUpdate]:
        """Update prediction based on live data"""
        
        original_prediction = self._active_predictions.get(prediction_id)
        if not original_prediction:
            return None
            
        # Generate new prediction with live adjustments
        new_prediction = await self.match_simulator.predict_h2h_match(
            manager1_id, manager2_id, gameweek, match_state, live_data
        )
        
        # Calculate adjustments
        adjustments = await self._calculate_adjustments(
            original_prediction, new_prediction, live_data
        )
        
        # Check if update is significant enough
        score_change = abs(
            (new_prediction.manager1_expected - new_prediction.manager2_expected) -
            (original_prediction.manager1_expected - original_prediction.manager2_expected)
        )
        
        if score_change < self.significant_change_threshold and not adjustments:
            return None
            
        # Create update
        update = PredictionUpdate(
            original_prediction=original_prediction,
            updated_prediction=new_prediction,
            adjustments=adjustments,
            confidence_change=new_prediction.confidence - original_prediction.confidence,
            key_changes=self._identify_key_changes(original_prediction, new_prediction),
            updated_at=datetime.utcnow()
        )
        
        # Update stored prediction
        self._active_predictions[prediction_id] = new_prediction
        await self.cache.set(f"prediction:{prediction_id}", asdict(new_prediction), ttl=7200)
        
        # Store update history
        await self._store_update_history(prediction_id, update)
        
        logger.info(f"Updated prediction {prediction_id} with {len(adjustments)} adjustments")
        return update
        
    async def _calculate_adjustments(
        self,
        original: H2HPrediction,
        updated: H2HPrediction,
        live_data: Dict
    ) -> List[LiveAdjustment]:
        """Calculate specific adjustments made to player predictions"""
        
        adjustments = []
        
        # This would require more detailed player-level prediction tracking
        # For now, we'll identify major changes based on live data
        
        elements = live_data.get("elements", {})
        
        for player_id_str, stats in elements.items():
            try:
                player_id = int(player_id_str)
                
                # Check for significant events
                if stats.get("goals_scored", 0) > 0:
                    adjustments.append(LiveAdjustment(
                        player_id=player_id,
                        player_name=stats.get("web_name", "Unknown"),
                        adjustment_type="goal",
                        old_prediction=0.0,  # Would need to track original
                        new_prediction=stats.get("goals_scored", 0) * 4,  # Points per goal
                        impact=stats.get("goals_scored", 0) * 4,
                        timestamp=datetime.utcnow(),
                        reason=f"Scored {stats.get('goals_scored', 0)} goal(s)"
                    ))
                    
                if stats.get("assists", 0) > 0:
                    adjustments.append(LiveAdjustment(
                        player_id=player_id,
                        player_name=stats.get("web_name", "Unknown"),
                        adjustment_type="assist",
                        old_prediction=0.0,
                        new_prediction=stats.get("assists", 0) * 3,
                        impact=stats.get("assists", 0) * 3,
                        timestamp=datetime.utcnow(),
                        reason=f"Made {stats.get('assists', 0)} assist(s)"
                    ))
                    
                if stats.get("red_cards", 0) > 0:
                    adjustments.append(LiveAdjustment(
                        player_id=player_id,
                        player_name=stats.get("web_name", "Unknown"),
                        adjustment_type="card",
                        old_prediction=0.0,
                        new_prediction=-3.0,
                        impact=-3.0,
                        timestamp=datetime.utcnow(),
                        reason="Received red card"
                    ))
                    
                # Check for non-appearance
                if stats.get("minutes", 0) == 0:
                    # Check if match is well underway
                    fixture_minutes = self._get_fixture_minutes(live_data, player_id)
                    if fixture_minutes and fixture_minutes > 30:
                        adjustments.append(LiveAdjustment(
                            player_id=player_id,
                            player_name=stats.get("web_name", "Unknown"),
                            adjustment_type="minutes",
                            old_prediction=2.0,  # Expected appearance points
                            new_prediction=0.0,
                            impact=-2.0,
                            timestamp=datetime.utcnow(),
                            reason="Did not start/unlikely to play"
                        ))
                        
            except (ValueError, KeyError) as e:
                logger.warning(f"Error processing player {player_id_str}: {e}")
                continue
                
        return adjustments
        
    def _get_fixture_minutes(self, live_data: Dict, player_id: int) -> Optional[int]:
        """Get fixture minutes for a player's team"""
        
        # This would require mapping player to team to fixture
        # Simplified implementation
        fixtures = live_data.get("fixtures", [])
        
        for fixture in fixtures:
            if fixture.get("started", False):
                return fixture.get("minutes", 0)
                
        return None
        
    def _identify_key_changes(
        self, 
        original: H2HPrediction, 
        updated: H2HPrediction
    ) -> List[str]:
        """Identify key changes in prediction"""
        
        changes = []
        
        # Score changes
        score_diff_change = (
            (updated.manager1_expected - updated.manager2_expected) -
            (original.manager1_expected - original.manager2_expected)
        )
        
        if abs(score_diff_change) > 3:
            if score_diff_change > 0:
                changes.append(f"Team 1 advantage increased by {score_diff_change:.1f} points")
            else:
                changes.append(f"Team 2 advantage increased by {abs(score_diff_change):.1f} points")
                
        # Win probability changes
        prob_change = updated.manager1_win_prob - original.manager1_win_prob
        
        if abs(prob_change) > 0.1:
            if prob_change > 0:
                changes.append(f"Team 1 win probability increased by {prob_change:.1%}")
            else:
                changes.append(f"Team 2 win probability increased by {abs(prob_change):.1%}")
                
        # Confidence changes
        conf_change = updated.confidence - original.confidence
        
        if abs(conf_change) > 0.1:
            if conf_change > 0:
                changes.append(f"Prediction confidence increased by {conf_change:.1%}")
            else:
                changes.append(f"Prediction confidence decreased by {abs(conf_change):.1%}")
                
        return changes
        
    async def _store_update_history(self, prediction_id: str, update: PredictionUpdate):
        """Store update in history for analysis"""
        
        history_key = f"prediction_history:{prediction_id}"
        
        # Add to list (keep last 50 updates)
        await self.cache.lpush(history_key, asdict(update))
        await self.cache.ltrim(history_key, 0, 49)
        await self.cache.expire(history_key, timedelta(hours=24))
        
    async def _broadcast_prediction_update(self, prediction_id: str, update: PredictionUpdate):
        """Broadcast prediction update to WebSocket clients"""
        
        # Extract manager IDs from prediction ID
        parts = prediction_id.split('_')
        if len(parts) >= 4:
            manager1_id = int(parts[1])
            manager2_id = int(parts[2])
            
            # Broadcast to H2H room
            room_name = f"h2h_{min(manager1_id, manager2_id)}_{max(manager1_id, manager2_id)}"
            
            await self.websocket_manager.broadcast_to_room(
                room_name,
                {
                    "type": "prediction_update",
                    "prediction_id": prediction_id,
                    "update": {
                        "manager1_expected": update.updated_prediction.manager1_expected,
                        "manager2_expected": update.updated_prediction.manager2_expected,
                        "manager1_win_prob": update.updated_prediction.manager1_win_prob,
                        "manager2_win_prob": update.updated_prediction.manager2_win_prob,
                        "confidence": update.updated_prediction.confidence,
                        "adjustments": [asdict(adj) for adj in update.adjustments],
                        "key_changes": update.key_changes,
                        "updated_at": update.updated_at.isoformat()
                    }
                }
            )
            
    async def get_prediction_history(self, prediction_id: str) -> List[Dict]:
        """Get prediction update history"""
        
        history_key = f"prediction_history:{prediction_id}"
        return await self.cache.lrange(history_key, 0, -1)
        
    async def get_active_predictions(self) -> List[str]:
        """Get list of active prediction IDs"""
        
        return list(self._active_predictions.keys())
        
    async def force_update(self, prediction_id: str) -> Optional[PredictionUpdate]:
        """Force an immediate prediction update"""
        
        if prediction_id not in self._active_predictions:
            return None
            
        # Extract info from prediction ID
        parts = prediction_id.split('_')
        if len(parts) < 4:
            return None
            
        try:
            manager1_id = int(parts[1])
            manager2_id = int(parts[2])
            gameweek = int(parts[3])
            
            # Get current live data
            live_data = await self.live_data_service.get_live_gameweek_data(gameweek)
            match_state = self._determine_match_state(live_data) if live_data else MatchState.PRE_MATCH
            
            # Update prediction
            return await self._update_prediction(
                prediction_id, manager1_id, manager2_id, gameweek, match_state, live_data
            )
            
        except (ValueError, IndexError) as e:
            logger.error(f"Error parsing prediction ID {prediction_id}: {e}")
            return None