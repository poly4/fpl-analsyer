"""
Season Manager for handling season transitions and live features.

This module manages season state, transitions between seasons,
and coordinates live features when seasons are active.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class SeasonState(str, Enum):
    """Season states for tracking and transitions."""
    PRE_SEASON = "pre_season"
    ACTIVE = "active"
    BREAK = "break"
    FINISHED = "finished"
    UNKNOWN = "unknown"


class GameweekState(str, Enum):
    """Gameweek states for live tracking."""
    SCHEDULED = "scheduled"
    FIXTURES_RELEASED = "fixtures_released"
    DEADLINE_APPROACHING = "deadline_approaching"
    LIVE = "live"
    FINISHED = "finished"
    BONUS_AWARDED = "bonus_awarded"
    COMPLETED = "completed"


@dataclass
class SeasonInfo:
    """Information about a specific season."""
    id: str
    name: str
    start_date: datetime
    end_date: datetime
    current_gameweek: int
    total_gameweeks: int
    state: SeasonState
    active_chips: List[str] = field(default_factory=list)
    new_features: List[str] = field(default_factory=list)
    rule_changes: List[str] = field(default_factory=list)


@dataclass
class GameweekInfo:
    """Information about a specific gameweek."""
    id: int
    name: str
    deadline_time: datetime
    state: GameweekState
    fixtures_count: int
    finished_fixtures: int
    average_score: Optional[float] = None
    highest_score: Optional[int] = None
    most_captained: Optional[int] = None
    most_transferred_in: Optional[int] = None
    chip_plays: Dict[str, int] = field(default_factory=dict)


class SeasonManager:
    """
    Manages season lifecycle, transitions, and live features.
    """
    
    def __init__(self, live_data_service, websocket_manager=None):
        """
        Initialize the season manager.
        
        Args:
            live_data_service: Service for fetching FPL data
            websocket_manager: WebSocket manager for live updates (optional)
        """
        self.live_data_service = live_data_service
        self.websocket_manager = websocket_manager
        
        # Season state
        self.current_season: Optional[SeasonInfo] = None
        self.current_gameweek: Optional[GameweekInfo] = None
        self.season_history: List[SeasonInfo] = []
        
        # Live features state
        self.live_features_enabled = False
        self.live_tracking_active = False
        self.price_change_tracking = False
        
        # Background tasks
        self._season_monitor_task: Optional[asyncio.Task] = None
        self._live_updates_task: Optional[asyncio.Task] = None
        self._price_tracker_task: Optional[asyncio.Task] = None
        
        # Callbacks for season events
        self.season_start_callbacks: List[Callable] = []
        self.season_end_callbacks: List[Callable] = []
        self.gameweek_start_callbacks: List[Callable] = []
        self.gameweek_end_callbacks: List[Callable] = []
        self.deadline_callbacks: List[Callable] = []
        
        # Cache and persistence
        self.cache_file = Path("season_cache.json")
        self.load_cached_state()
    
    async def initialize(self) -> bool:
        """
        Initialize the season manager and start monitoring.
        
        Returns:
            True if initialization successful
        """
        try:
            logger.info("Initializing Season Manager")
            
            # Detect current season state
            await self.detect_season_state()
            
            # Start background monitoring
            await self.start_monitoring()
            
            # Enable live features if season is active
            if self.current_season and self.current_season.state == SeasonState.ACTIVE:
                await self.enable_live_features()
            
            logger.info(f"Season Manager initialized. Current season: {self.current_season.state if self.current_season else 'Unknown'}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Season Manager: {e}")
            return False
    
    async def detect_season_state(self) -> SeasonState:
        """
        Detect the current season state from FPL API.
        
        Returns:
            Current season state
        """
        try:
            # Get bootstrap data to understand current season
            bootstrap = await self.live_data_service.get_bootstrap_static()
            
            if not bootstrap:
                logger.warning("Could not fetch bootstrap data")
                return SeasonState.UNKNOWN
            
            events = bootstrap.get('events', [])
            if not events:
                logger.warning("No events found in bootstrap data")
                return SeasonState.UNKNOWN
            
            # Find current gameweek
            current_event = None
            next_event = None
            
            for event in events:
                if event.get('is_current', False):
                    current_event = event
                elif event.get('is_next', False):
                    next_event = event
            
            # Determine season state
            now = datetime.utcnow()
            
            if current_event:
                # Season is active
                deadline_time = datetime.fromisoformat(current_event['deadline_time'].replace('Z', '+00:00'))
                
                if current_event.get('finished', False):
                    # Check if season is finished
                    if current_event['id'] >= 38:  # Assuming 38 gameweeks
                        state = SeasonState.FINISHED
                    else:
                        state = SeasonState.ACTIVE
                else:
                    state = SeasonState.ACTIVE
                
                # Create season info
                self.current_season = SeasonInfo(
                    id=f"2024-25",  # Would need to derive from API
                    name="2024/25 Season",
                    start_date=datetime.fromisoformat(events[0]['deadline_time'].replace('Z', '+00:00')),
                    end_date=datetime.fromisoformat(events[-1]['deadline_time'].replace('Z', '+00:00')),
                    current_gameweek=current_event['id'],
                    total_gameweeks=len(events),
                    state=state,
                    active_chips=self._get_active_chips(bootstrap),
                    new_features=self._get_new_features(bootstrap),
                    rule_changes=self._get_rule_changes(bootstrap)
                )
                
                # Create current gameweek info
                self.current_gameweek = GameweekInfo(
                    id=current_event['id'],
                    name=current_event['name'],
                    deadline_time=deadline_time,
                    state=self._determine_gameweek_state(current_event, now),
                    fixtures_count=0,  # Would need to fetch from fixtures endpoint
                    finished_fixtures=0,
                    average_score=current_event.get('average_entry_score'),
                    highest_score=current_event.get('highest_score'),
                    most_captained=current_event.get('most_captained'),
                    most_transferred_in=current_event.get('most_transferred_in'),
                    chip_plays={chip['chip_name']: chip['num_played'] for chip in current_event.get('chip_plays', [])}
                )
                
            elif not events[0].get('finished', True):
                # Pre-season
                state = SeasonState.PRE_SEASON
                self.current_season = SeasonInfo(
                    id="2024-25",
                    name="2024/25 Season",
                    start_date=datetime.fromisoformat(events[0]['deadline_time'].replace('Z', '+00:00')),
                    end_date=datetime.fromisoformat(events[-1]['deadline_time'].replace('Z', '+00:00')),
                    current_gameweek=0,
                    total_gameweeks=len(events),
                    state=state
                )
            else:
                # Season finished or in break
                state = SeasonState.FINISHED
                self.current_season = SeasonInfo(
                    id="2023-24",  # Previous season
                    name="2023/24 Season",
                    start_date=datetime.fromisoformat(events[0]['deadline_time'].replace('Z', '+00:00')),
                    end_date=datetime.fromisoformat(events[-1]['deadline_time'].replace('Z', '+00:00')),
                    current_gameweek=38,
                    total_gameweeks=len(events),
                    state=state
                )
            
            # Save state
            self.save_cached_state()
            
            logger.info(f"Detected season state: {state}")
            return state
            
        except Exception as e:
            logger.error(f"Error detecting season state: {e}")
            return SeasonState.UNKNOWN
    
    def _determine_gameweek_state(self, event: Dict[str, Any], now: datetime) -> GameweekState:
        """Determine the current state of a gameweek."""
        deadline_time = datetime.fromisoformat(event['deadline_time'].replace('Z', '+00:00'))
        
        if event.get('finished', False):
            if event.get('data_checked', False):
                return GameweekState.COMPLETED
            else:
                return GameweekState.BONUS_AWARDED
        elif now > deadline_time:
            return GameweekState.LIVE
        elif now > deadline_time - timedelta(hours=2):
            return GameweekState.DEADLINE_APPROACHING
        elif event.get('fixtures_released', False):
            return GameweekState.FIXTURES_RELEASED
        else:
            return GameweekState.SCHEDULED
    
    def _get_active_chips(self, bootstrap: Dict[str, Any]) -> List[str]:
        """Extract active chips for the season."""
        # This would be determined from game settings or events
        return ['wildcard', 'freehit', '3xc', 'bboost']
    
    def _get_new_features(self, bootstrap: Dict[str, Any]) -> List[str]:
        """Extract new features for the season."""
        # This would be determined from API or configuration
        return []
    
    def _get_rule_changes(self, bootstrap: Dict[str, Any]) -> List[str]:
        """Extract rule changes for the season."""
        # This would be determined from API or configuration
        return []
    
    async def start_monitoring(self):
        """Start background monitoring tasks."""
        if self._season_monitor_task is None or self._season_monitor_task.done():
            self._season_monitor_task = asyncio.create_task(self._season_monitor_worker())
        
        logger.info("Started season monitoring")
    
    async def stop_monitoring(self):
        """Stop background monitoring tasks."""
        tasks = [
            ('season_monitor', self._season_monitor_task),
            ('live_updates', self._live_updates_task),
            ('price_tracker', self._price_tracker_task)
        ]
        
        for task_name, task in tasks:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                logger.info(f"Stopped {task_name} task")
    
    async def enable_live_features(self):
        """Enable live features during active season."""
        if self.live_features_enabled:
            return
        
        self.live_features_enabled = True
        
        # Start live tracking
        if self.current_gameweek and self.current_gameweek.state in [GameweekState.LIVE, GameweekState.DEADLINE_APPROACHING]:
            await self.start_live_tracking()
        
        # Start price change tracking
        await self.start_price_tracking()
        
        logger.info("Live features enabled")
    
    async def disable_live_features(self):
        """Disable live features during off-season."""
        self.live_features_enabled = False
        await self.stop_live_tracking()
        await self.stop_price_tracking()
        
        logger.info("Live features disabled")
    
    async def start_live_tracking(self):
        """Start live gameweek tracking."""
        if self.live_tracking_active:
            return
        
        self.live_tracking_active = True
        
        if self._live_updates_task is None or self._live_updates_task.done():
            self._live_updates_task = asyncio.create_task(self._live_updates_worker())
        
        logger.info("Started live tracking")
    
    async def stop_live_tracking(self):
        """Stop live gameweek tracking."""
        self.live_tracking_active = False
        
        if self._live_updates_task and not self._live_updates_task.done():
            self._live_updates_task.cancel()
            try:
                await self._live_updates_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped live tracking")
    
    async def start_price_tracking(self):
        """Start price change tracking."""
        if self.price_change_tracking:
            return
        
        self.price_change_tracking = True
        
        if self._price_tracker_task is None or self._price_tracker_task.done():
            self._price_tracker_task = asyncio.create_task(self._price_tracker_worker())
        
        logger.info("Started price change tracking")
    
    async def stop_price_tracking(self):
        """Stop price change tracking."""
        self.price_change_tracking = False
        
        if self._price_tracker_task and not self._price_tracker_task.done():
            self._price_tracker_task.cancel()
            try:
                await self._price_tracker_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped price change tracking")
    
    async def handle_season_transition(self, new_state: SeasonState):
        """Handle transition to new season state."""
        if not self.current_season:
            return
        
        old_state = self.current_season.state
        self.current_season.state = new_state
        
        logger.info(f"Season transition: {old_state} -> {new_state}")
        
        # Handle state-specific transitions
        if new_state == SeasonState.ACTIVE and old_state == SeasonState.PRE_SEASON:
            # Season starting
            await self.enable_live_features()
            await self._execute_callbacks(self.season_start_callbacks)
            
        elif new_state == SeasonState.FINISHED and old_state == SeasonState.ACTIVE:
            # Season ending
            await self.disable_live_features()
            await self._execute_callbacks(self.season_end_callbacks)
            
        elif new_state == SeasonState.PRE_SEASON and old_state == SeasonState.FINISHED:
            # New season starting
            await self._prepare_new_season()
        
        # Broadcast season state change via WebSocket
        if self.websocket_manager:
            from ..websocket.live_updates import WebSocketMessage, MessageType, generate_global_room_id
            
            message = WebSocketMessage(
                type=MessageType.CONNECTION_STATE,
                data={
                    "season_state": new_state.value,
                    "current_gameweek": self.current_season.current_gameweek,
                    "season_info": {
                        "name": self.current_season.name,
                        "total_gameweeks": self.current_season.total_gameweeks,
                        "new_features": self.current_season.new_features,
                        "rule_changes": self.current_season.rule_changes
                    }
                }
            )
            
            await self.websocket_manager.broadcast_to_room(generate_global_room_id(), message)
        
        # Save updated state
        self.save_cached_state()
    
    async def handle_gameweek_transition(self, new_gameweek: int, new_state: GameweekState):
        """Handle gameweek state transitions."""
        if not self.current_gameweek:
            return
        
        old_gameweek = self.current_gameweek.id
        old_state = self.current_gameweek.state
        
        # Update gameweek info
        if new_gameweek != old_gameweek:
            # New gameweek started
            await self._update_gameweek_info(new_gameweek)
            await self._execute_callbacks(self.gameweek_start_callbacks)
            
            if old_gameweek > 0:
                await self._execute_callbacks(self.gameweek_end_callbacks)
        else:
            # State change within same gameweek
            self.current_gameweek.state = new_state
        
        logger.info(f"Gameweek transition: GW{old_gameweek}({old_state}) -> GW{new_gameweek}({new_state})")
        
        # Handle state-specific actions
        if new_state == GameweekState.DEADLINE_APPROACHING:
            await self._execute_callbacks(self.deadline_callbacks)
        elif new_state == GameweekState.LIVE:
            await self.start_live_tracking()
        elif new_state == GameweekState.COMPLETED:
            await self.stop_live_tracking()
        
        # Broadcast gameweek state change
        if self.websocket_manager:
            from ..websocket.live_updates import WebSocketMessage, MessageType, generate_live_room_id
            
            message = WebSocketMessage(
                type=MessageType.LIVE_SCORES,
                data={
                    "gameweek": new_gameweek,
                    "state": new_state.value,
                    "gameweek_info": {
                        "name": self.current_gameweek.name,
                        "deadline_time": self.current_gameweek.deadline_time.isoformat(),
                        "average_score": self.current_gameweek.average_score,
                        "highest_score": self.current_gameweek.highest_score
                    }
                }
            )
            
            await self.websocket_manager.broadcast_to_room(generate_live_room_id(new_gameweek), message)
    
    async def _season_monitor_worker(self):
        """Background worker to monitor season state changes."""
        while True:
            try:
                # Check for season state changes every 5 minutes
                old_state = self.current_season.state if self.current_season else SeasonState.UNKNOWN
                new_state = await self.detect_season_state()
                
                if new_state != old_state:
                    await self.handle_season_transition(new_state)
                
                # Check for gameweek changes if season is active
                if self.current_season and self.current_season.state == SeasonState.ACTIVE:
                    await self._check_gameweek_changes()
                
                await asyncio.sleep(300)  # 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in season monitor: {e}")
                await asyncio.sleep(60)  # Wait before retry
    
    async def _live_updates_worker(self):
        """Background worker for live gameweek updates."""
        while self.live_tracking_active:
            try:
                # Fetch live gameweek data
                if self.current_gameweek:
                    await self._update_live_scores()
                
                await asyncio.sleep(30)  # Update every 30 seconds during live gameweeks
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in live updates worker: {e}")
                await asyncio.sleep(60)
    
    async def _price_tracker_worker(self):
        """Background worker for price change tracking."""
        last_bootstrap = None
        
        while self.price_change_tracking:
            try:
                # Fetch current bootstrap data
                bootstrap = await self.live_data_service.get_bootstrap_static()
                
                if bootstrap and last_bootstrap:
                    price_changes = self._detect_price_changes(last_bootstrap, bootstrap)
                    if price_changes:
                        await self._broadcast_price_changes(price_changes)
                
                last_bootstrap = bootstrap
                await asyncio.sleep(3600)  # Check every hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in price tracker: {e}")
                await asyncio.sleep(1800)  # Wait 30 minutes before retry
    
    async def _check_gameweek_changes(self):
        """Check for gameweek state changes."""
        if not self.current_season or not self.current_gameweek:
            return
        
        try:
            bootstrap = await self.live_data_service.get_bootstrap_static()
            if not bootstrap:
                return
            
            events = bootstrap.get('events', [])
            current_event = next((e for e in events if e.get('is_current', False)), None)
            
            if current_event:
                new_gameweek = current_event['id']
                new_state = self._determine_gameweek_state(current_event, datetime.utcnow())
                
                if (new_gameweek != self.current_gameweek.id or 
                    new_state != self.current_gameweek.state):
                    await self.handle_gameweek_transition(new_gameweek, new_state)
        
        except Exception as e:
            logger.error(f"Error checking gameweek changes: {e}")
    
    async def _update_gameweek_info(self, gameweek_id: int):
        """Update current gameweek information."""
        try:
            bootstrap = await self.live_data_service.get_bootstrap_static()
            if not bootstrap:
                return
            
            event = next((e for e in bootstrap['events'] if e['id'] == gameweek_id), None)
            if not event:
                return
            
            deadline_time = datetime.fromisoformat(event['deadline_time'].replace('Z', '+00:00'))
            
            self.current_gameweek = GameweekInfo(
                id=event['id'],
                name=event['name'],
                deadline_time=deadline_time,
                state=self._determine_gameweek_state(event, datetime.utcnow()),
                fixtures_count=0,  # Would need fixtures endpoint
                finished_fixtures=0,
                average_score=event.get('average_entry_score'),
                highest_score=event.get('highest_score'),
                most_captained=event.get('most_captained'),
                most_transferred_in=event.get('most_transferred_in'),
                chip_plays={chip['chip_name']: chip['num_played'] for chip in event.get('chip_plays', [])}
            )
            
            self.current_season.current_gameweek = gameweek_id
            
        except Exception as e:
            logger.error(f"Error updating gameweek info: {e}")
    
    async def _update_live_scores(self):
        """Update live scores during active gameweek."""
        if not self.current_gameweek:
            return
        
        try:
            # Get live gameweek data
            live_data = await self.live_data_service.get_live_gameweek_data(self.current_gameweek.id)
            if not live_data:
                return
            
            # Extract relevant live information
            # This would include player scores, bonus points, etc.
            
            # Broadcast live updates via WebSocket
            if self.websocket_manager:
                from ..websocket.live_updates import WebSocketMessage, MessageType, generate_live_room_id
                
                message = WebSocketMessage(
                    type=MessageType.LIVE_SCORES,
                    data={
                        "gameweek": self.current_gameweek.id,
                        "live_data": live_data,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                await self.websocket_manager.broadcast_to_room(
                    generate_live_room_id(self.current_gameweek.id), 
                    message
                )
        
        except Exception as e:
            logger.error(f"Error updating live scores: {e}")
    
    def _detect_price_changes(self, old_bootstrap: Dict, new_bootstrap: Dict) -> List[Dict[str, Any]]:
        """Detect price changes between bootstrap updates."""
        changes = []
        
        old_elements = {e['id']: e for e in old_bootstrap.get('elements', [])}
        new_elements = {e['id']: e for e in new_bootstrap.get('elements', [])}
        
        for element_id, new_element in new_elements.items():
            if element_id in old_elements:
                old_element = old_elements[element_id]
                old_price = old_element.get('now_cost', 0)
                new_price = new_element.get('now_cost', 0)
                
                if old_price != new_price:
                    changes.append({
                        "player_id": element_id,
                        "player_name": new_element.get('web_name', ''),
                        "old_price": old_price,
                        "new_price": new_price,
                        "change": new_price - old_price,
                        "timestamp": datetime.utcnow().isoformat()
                    })
        
        return changes
    
    async def _broadcast_price_changes(self, price_changes: List[Dict[str, Any]]):
        """Broadcast price changes via WebSocket."""
        if not self.websocket_manager or not price_changes:
            return
        
        from ..websocket.live_updates import WebSocketMessage, MessageType, generate_global_room_id
        
        message = WebSocketMessage(
            type=MessageType.PLAYER_EVENT,
            data={
                "event_type": "price_changes",
                "changes": price_changes,
                "count": len(price_changes)
            }
        )
        
        await self.websocket_manager.broadcast_to_room(generate_global_room_id(), message)
        logger.info(f"Broadcasted {len(price_changes)} price changes")
    
    async def _prepare_new_season(self):
        """Prepare for new season start."""
        # Archive current season
        if self.current_season:
            self.season_history.append(self.current_season)
        
        # Reset caches
        # Clear old data
        # Prepare for new season data
        
        logger.info("Prepared for new season")
    
    async def _execute_callbacks(self, callbacks: List[Callable]):
        """Execute list of callbacks asynchronously."""
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.error(f"Error executing callback: {e}")
    
    def add_season_start_callback(self, callback: Callable):
        """Add callback for season start events."""
        self.season_start_callbacks.append(callback)
    
    def add_season_end_callback(self, callback: Callable):
        """Add callback for season end events."""
        self.season_end_callbacks.append(callback)
    
    def add_gameweek_start_callback(self, callback: Callable):
        """Add callback for gameweek start events."""
        self.gameweek_start_callbacks.append(callback)
    
    def add_gameweek_end_callback(self, callback: Callable):
        """Add callback for gameweek end events."""
        self.gameweek_end_callbacks.append(callback)
    
    def add_deadline_callback(self, callback: Callable):
        """Add callback for deadline approaching events."""
        self.deadline_callbacks.append(callback)
    
    def get_season_info(self) -> Optional[SeasonInfo]:
        """Get current season information."""
        return self.current_season
    
    def get_gameweek_info(self) -> Optional[GameweekInfo]:
        """Get current gameweek information."""
        return self.current_gameweek
    
    def is_live_features_enabled(self) -> bool:
        """Check if live features are enabled."""
        return self.live_features_enabled
    
    def is_season_active(self) -> bool:
        """Check if season is currently active."""
        return (self.current_season and 
                self.current_season.state == SeasonState.ACTIVE)
    
    def get_status(self) -> Dict[str, Any]:
        """Get detailed status information."""
        return {
            "season": {
                "state": self.current_season.state.value if self.current_season else "unknown",
                "name": self.current_season.name if self.current_season else None,
                "current_gameweek": self.current_season.current_gameweek if self.current_season else 0,
                "total_gameweeks": self.current_season.total_gameweeks if self.current_season else 0
            },
            "gameweek": {
                "id": self.current_gameweek.id if self.current_gameweek else 0,
                "name": self.current_gameweek.name if self.current_gameweek else None,
                "state": self.current_gameweek.state.value if self.current_gameweek else "unknown",
                "deadline_time": self.current_gameweek.deadline_time.isoformat() if self.current_gameweek else None
            },
            "features": {
                "live_features_enabled": self.live_features_enabled,
                "live_tracking_active": self.live_tracking_active,
                "price_change_tracking": self.price_change_tracking
            },
            "tasks": {
                "season_monitor": self._season_monitor_task is not None and not self._season_monitor_task.done(),
                "live_updates": self._live_updates_task is not None and not self._live_updates_task.done(),
                "price_tracker": self._price_tracker_task is not None and not self._price_tracker_task.done()
            }
        }
    
    def save_cached_state(self):
        """Save current state to cache file."""
        try:
            state_data = {
                "current_season": {
                    "id": self.current_season.id,
                    "name": self.current_season.name,
                    "start_date": self.current_season.start_date.isoformat(),
                    "end_date": self.current_season.end_date.isoformat(),
                    "current_gameweek": self.current_season.current_gameweek,
                    "total_gameweeks": self.current_season.total_gameweeks,
                    "state": self.current_season.state.value,
                    "active_chips": self.current_season.active_chips,
                    "new_features": self.current_season.new_features,
                    "rule_changes": self.current_season.rule_changes
                } if self.current_season else None,
                "current_gameweek": {
                    "id": self.current_gameweek.id,
                    "name": self.current_gameweek.name,
                    "deadline_time": self.current_gameweek.deadline_time.isoformat(),
                    "state": self.current_gameweek.state.value,
                    "fixtures_count": self.current_gameweek.fixtures_count,
                    "finished_fixtures": self.current_gameweek.finished_fixtures,
                    "average_score": self.current_gameweek.average_score,
                    "highest_score": self.current_gameweek.highest_score,
                    "chip_plays": self.current_gameweek.chip_plays
                } if self.current_gameweek else None,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(state_data, f, indent=2)
        
        except Exception as e:
            logger.error(f"Error saving cached state: {e}")
    
    def load_cached_state(self):
        """Load state from cache file."""
        try:
            if not self.cache_file.exists():
                return
            
            with open(self.cache_file, 'r') as f:
                state_data = json.load(f)
            
            # Load season info
            season_data = state_data.get('current_season')
            if season_data:
                self.current_season = SeasonInfo(
                    id=season_data['id'],
                    name=season_data['name'],
                    start_date=datetime.fromisoformat(season_data['start_date']),
                    end_date=datetime.fromisoformat(season_data['end_date']),
                    current_gameweek=season_data['current_gameweek'],
                    total_gameweeks=season_data['total_gameweeks'],
                    state=SeasonState(season_data['state']),
                    active_chips=season_data.get('active_chips', []),
                    new_features=season_data.get('new_features', []),
                    rule_changes=season_data.get('rule_changes', [])
                )
            
            # Load gameweek info
            gameweek_data = state_data.get('current_gameweek')
            if gameweek_data:
                self.current_gameweek = GameweekInfo(
                    id=gameweek_data['id'],
                    name=gameweek_data['name'],
                    deadline_time=datetime.fromisoformat(gameweek_data['deadline_time']),
                    state=GameweekState(gameweek_data['state']),
                    fixtures_count=gameweek_data['fixtures_count'],
                    finished_fixtures=gameweek_data['finished_fixtures'],
                    average_score=gameweek_data.get('average_score'),
                    highest_score=gameweek_data.get('highest_score'),
                    chip_plays=gameweek_data.get('chip_plays', {})
                )
            
            logger.info("Loaded cached season state")
        
        except Exception as e:
            logger.error(f"Error loading cached state: {e}")