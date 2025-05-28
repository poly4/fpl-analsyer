import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
import hashlib
from dataclasses import dataclass, asdict
from enum import Enum

from app.services.live_data import LiveDataService
from app.websocket.live_updates import WebSocketManager

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Types of live events"""
    GOAL = "goal"
    ASSIST = "assist"
    CLEAN_SHEET = "clean_sheet"
    BONUS = "bonus"
    CARD = "card"
    SUBSTITUTION = "substitution"
    SAVE = "save"
    PENALTY_SAVE = "penalty_save"
    PENALTY_MISS = "penalty_miss"
    OWN_GOAL = "own_goal"
    GAME_STARTED = "game_started"
    GAME_FINISHED = "game_finished"
    LINEUP = "lineup"


@dataclass
class LiveEvent:
    """Represents a live match event"""
    event_type: EventType
    player_id: int
    player_name: str
    team_id: int
    team_name: str
    points: int
    minute: Optional[int]
    gameweek: int
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class LiveMatchData:
    """Live match data for a fixture"""
    fixture_id: int
    home_team: str
    away_team: str
    score: str
    started: bool
    finished: bool
    minutes: int
    bonus: Dict[int, int]  # player_id -> provisional bonus
    events: List[LiveEvent]


@dataclass
class H2HLiveUpdate:
    """Live update for H2H battle"""
    manager1_id: int
    manager1_name: str
    manager1_score: int
    manager1_live_score: int
    manager2_id: int
    manager2_name: str
    manager2_score: int
    manager2_live_score: int
    score_diff: int
    events: List[LiveEvent]
    momentum: str  # "manager1", "manager2", "neutral"
    key_players: Dict[str, Any]


class LiveMatchService:
    """Service for real-time match updates and live data processing"""
    
    def __init__(self, live_data_service: LiveDataService, websocket_manager: WebSocketManager):
        self.live_data_service = live_data_service
        self.websocket_manager = websocket_manager
        self._last_data_hash: Dict[int, str] = {}  # gameweek -> hash
        self._last_update: Dict[int, datetime] = {}  # gameweek -> timestamp
        self._cached_live_data: Dict[int, Dict] = {}  # gameweek -> data
        self._active_fixtures: Set[int] = set()
        self._polling_task: Optional[asyncio.Task] = None
        self._is_running = False
        
    async def start_live_updates(self, gameweek: int):
        """Start polling for live updates"""
        if self._polling_task and not self._polling_task.done():
            logger.info(f"Live updates already running for gameweek {gameweek}")
            return
            
        self._is_running = True
        self._polling_task = asyncio.create_task(self._poll_live_data(gameweek))
        logger.info(f"Started live updates for gameweek {gameweek}")
        
    async def stop_live_updates(self):
        """Stop polling for live updates"""
        self._is_running = False
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped live updates")
        
    async def _poll_live_data(self, gameweek: int):
        """Poll FPL API for live data every 30 seconds"""
        while self._is_running:
            try:
                # Get current live data
                live_data = await self.live_data_service.get_live_gameweek_data(gameweek)
                
                if live_data:
                    # Calculate hash to detect changes
                    data_hash = self._calculate_data_hash(live_data)
                    
                    # Check if data has changed
                    if self._last_data_hash.get(gameweek) != data_hash:
                        logger.info(f"Detected changes in live data for gameweek {gameweek}")
                        
                        # Process deltas and broadcast updates
                        await self._process_live_updates(gameweek, live_data)
                        
                        # Update cache
                        self._last_data_hash[gameweek] = data_hash
                        self._cached_live_data[gameweek] = live_data
                        self._last_update[gameweek] = datetime.utcnow()
                    
                # Wait 30 seconds before next poll
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error polling live data: {e}")
                await asyncio.sleep(30)  # Continue after error
                
    def _calculate_data_hash(self, data: Dict) -> str:
        """Calculate hash of live data to detect changes"""
        # Convert to JSON string for consistent hashing
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(json_str.encode()).hexdigest()
        
    async def _process_live_updates(self, gameweek: int, live_data: Dict):
        """Process live data and detect events"""
        # Get previous data for comparison
        previous_data = self._cached_live_data.get(gameweek, {})
        
        # Track all events
        all_events = []
        
        # Process each fixture
        for fixture in live_data.get("fixtures", []):
            fixture_id = fixture["id"]
            
            # Check if fixture has started/finished
            if fixture["started"] and fixture_id not in self._active_fixtures:
                self._active_fixtures.add(fixture_id)
                event = LiveEvent(
                    event_type=EventType.GAME_STARTED,
                    player_id=0,
                    player_name="",
                    team_id=fixture["team_h"],
                    team_name=fixture["team_h_name"],
                    points=0,
                    minute=0,
                    gameweek=gameweek,
                    timestamp=datetime.utcnow(),
                    metadata={"away_team": fixture["team_a_name"]}
                )
                all_events.append(event)
                
            if fixture["finished"] and fixture_id in self._active_fixtures:
                self._active_fixtures.remove(fixture_id)
                event = LiveEvent(
                    event_type=EventType.GAME_FINISHED,
                    player_id=0,
                    player_name="",
                    team_id=fixture["team_h"],
                    team_name=fixture["team_h_name"],
                    points=0,
                    minute=90,
                    gameweek=gameweek,
                    timestamp=datetime.utcnow(),
                    metadata={
                        "away_team": fixture["team_a_name"],
                        "final_score": f"{fixture['team_h_score']}-{fixture['team_a_score']}"
                    }
                )
                all_events.append(event)
            
            # Process player stats
            for stats in fixture.get("stats", []):
                stat_type = stats["identifier"]
                
                # Map to our event types
                event_type_map = {
                    "goals_scored": EventType.GOAL,
                    "assists": EventType.ASSIST,
                    "clean_sheets": EventType.CLEAN_SHEET,
                    "yellow_cards": EventType.CARD,
                    "red_cards": EventType.CARD,
                    "saves": EventType.SAVE,
                    "penalties_saved": EventType.PENALTY_SAVE,
                    "penalties_missed": EventType.PENALTY_MISS,
                    "own_goals": EventType.OWN_GOAL
                }
                
                if stat_type in event_type_map:
                    # Compare with previous data
                    prev_fixture = self._find_fixture(previous_data, fixture_id)
                    prev_stats = self._find_stats(prev_fixture, stat_type) if prev_fixture else None
                    
                    # Check home team stats
                    for player in stats.get("h", []):
                        player_id = player["element"]
                        value = player["value"]
                        
                        # Check if this is a new event
                        prev_value = self._get_player_stat_value(prev_stats, "h", player_id) if prev_stats else 0
                        
                        if value > prev_value:
                            # New event detected
                            for _ in range(value - prev_value):
                                event = await self._create_live_event(
                                    event_type_map[stat_type],
                                    player_id,
                                    fixture["team_h"],
                                    fixture["team_h_name"],
                                    gameweek,
                                    fixture.get("minutes", 0),
                                    stat_type
                                )
                                if event:
                                    all_events.append(event)
                    
                    # Check away team stats
                    for player in stats.get("a", []):
                        player_id = player["element"]
                        value = player["value"]
                        
                        # Check if this is a new event
                        prev_value = self._get_player_stat_value(prev_stats, "a", player_id) if prev_stats else 0
                        
                        if value > prev_value:
                            # New event detected
                            for _ in range(value - prev_value):
                                event = await self._create_live_event(
                                    event_type_map[stat_type],
                                    player_id,
                                    fixture["team_a"],
                                    fixture["team_a_name"],
                                    gameweek,
                                    fixture.get("minutes", 0),
                                    stat_type
                                )
                                if event:
                                    all_events.append(event)
        
        # Process bonus points
        bonus_events = await self._process_bonus_updates(gameweek, live_data, previous_data)
        all_events.extend(bonus_events)
        
        # Broadcast events
        if all_events:
            await self._broadcast_events(gameweek, all_events, live_data)
            
    def _find_fixture(self, data: Dict, fixture_id: int) -> Optional[Dict]:
        """Find fixture by ID in live data"""
        for fixture in data.get("fixtures", []):
            if fixture["id"] == fixture_id:
                return fixture
        return None
        
    def _find_stats(self, fixture: Dict, stat_type: str) -> Optional[Dict]:
        """Find stats by type in fixture"""
        if not fixture:
            return None
        for stats in fixture.get("stats", []):
            if stats["identifier"] == stat_type:
                return stats
        return None
        
    def _get_player_stat_value(self, stats: Dict, team: str, player_id: int) -> int:
        """Get stat value for a player"""
        if not stats:
            return 0
        for player in stats.get(team, []):
            if player["element"] == player_id:
                return player["value"]
        return 0
        
    async def _create_live_event(
        self, 
        event_type: EventType, 
        player_id: int, 
        team_id: int, 
        team_name: str, 
        gameweek: int,
        minute: int,
        stat_type: str
    ) -> Optional[LiveEvent]:
        """Create a live event object"""
        try:
            # Get player details
            bootstrap = await self.live_data_service.get_bootstrap_static()
            player = None
            for p in bootstrap["elements"]:
                if p["id"] == player_id:
                    player = p
                    break
                    
            if not player:
                return None
                
            # Calculate points for this event
            points = self._calculate_event_points(event_type, player["element_type"])
            
            # Add metadata based on event type
            metadata = {"stat_type": stat_type}
            if event_type == EventType.CARD:
                metadata["card_type"] = "red" if stat_type == "red_cards" else "yellow"
                
            return LiveEvent(
                event_type=event_type,
                player_id=player_id,
                player_name=player["web_name"],
                team_id=team_id,
                team_name=team_name,
                points=points,
                minute=minute,
                gameweek=gameweek,
                timestamp=datetime.utcnow(),
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error creating live event: {e}")
            return None
            
    def _calculate_event_points(self, event_type: EventType, position: int) -> int:
        """Calculate FPL points for an event"""
        # Position: 1=GK, 2=DEF, 3=MID, 4=FWD
        
        if event_type == EventType.GOAL:
            return {1: 6, 2: 6, 3: 5, 4: 4}.get(position, 0)
        elif event_type == EventType.ASSIST:
            return 3
        elif event_type == EventType.CLEAN_SHEET:
            return {1: 4, 2: 4, 3: 1, 4: 0}.get(position, 0)
        elif event_type == EventType.PENALTY_SAVE:
            return 5
        elif event_type == EventType.SAVE and position == 1:
            return 1  # Every 3 saves = 1 point
        elif event_type == EventType.CARD:
            return -1  # Yellow card
        elif event_type == EventType.OWN_GOAL:
            return -2
        elif event_type == EventType.PENALTY_MISS:
            return -2
        else:
            return 0
            
    async def _process_bonus_updates(self, gameweek: int, live_data: Dict, previous_data: Dict) -> List[LiveEvent]:
        """Process bonus point updates"""
        events = []
        
        # Get element data for BPS to bonus conversion
        bootstrap = await self.live_data_service.get_bootstrap_static()
        elements = {e["id"]: e for e in bootstrap["elements"]}
        
        for fixture in live_data.get("fixtures", []):
            if not fixture["started"] or not fixture.get("stats"):
                continue
                
            # Find BPS stats
            bps_stats = None
            for stats in fixture["stats"]:
                if stats["identifier"] == "bps":
                    bps_stats = stats
                    break
                    
            if not bps_stats:
                continue
                
            # Get all players' BPS
            all_bps = []
            for player in bps_stats.get("h", []):
                all_bps.append((player["element"], player["value"]))
            for player in bps_stats.get("a", []):
                all_bps.append((player["element"], player["value"]))
                
            # Sort by BPS (descending)
            all_bps.sort(key=lambda x: x[1], reverse=True)
            
            # Calculate provisional bonus (3-2-1 system)
            bonus_points = {}
            if len(all_bps) >= 1:
                bonus_points[all_bps[0][0]] = 3
            if len(all_bps) >= 2:
                bonus_points[all_bps[1][0]] = 2
            if len(all_bps) >= 3:
                bonus_points[all_bps[2][0]] = 1
                
            # Check for ties
            if len(all_bps) >= 2 and all_bps[0][1] == all_bps[1][1]:
                bonus_points[all_bps[1][0]] = 3
            if len(all_bps) >= 3:
                if all_bps[1][1] == all_bps[2][1]:
                    bonus_points[all_bps[2][0]] = 2
                if len(all_bps) >= 4 and all_bps[2][1] == all_bps[3][1]:
                    bonus_points[all_bps[3][0]] = 1
                    
            # Compare with previous bonus
            prev_fixture = self._find_fixture(previous_data, fixture["id"])
            if prev_fixture:
                # Check for bonus changes
                for player_id, bonus in bonus_points.items():
                    # This is simplified - in reality we'd track actual bonus changes
                    pass
                    
        return events
        
    async def _broadcast_events(self, gameweek: int, events: List[LiveEvent], live_data: Dict):
        """Broadcast events to relevant WebSocket rooms"""
        # Broadcast to gameweek room
        await self.websocket_manager.broadcast_to_room(
            f"live_gw_{gameweek}",
            {
                "type": "live_events",
                "gameweek": gameweek,
                "events": [asdict(e) for e in events],
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Get H2H battles and broadcast updates
        h2h_updates = await self._calculate_h2h_impacts(gameweek, events, live_data)
        
        for update in h2h_updates:
            # Broadcast to H2H room
            room_name = f"h2h_{min(update.manager1_id, update.manager2_id)}_{max(update.manager1_id, update.manager2_id)}"
            await self.websocket_manager.broadcast_to_room(
                room_name,
                {
                    "type": "h2h_update",
                    "gameweek": gameweek,
                    "update": asdict(update),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        # Broadcast league table updates
        await self._broadcast_league_updates(gameweek, live_data)
        
    async def _calculate_h2h_impacts(self, gameweek: int, events: List[LiveEvent], live_data: Dict) -> List[H2HLiveUpdate]:
        """Calculate impact of events on H2H battles"""
        updates = []
        
        # This would integrate with h2h_analyzer to get current battles
        # and calculate live scores based on events
        # For now, returning empty list
        
        return updates
        
    async def _broadcast_league_updates(self, gameweek: int, live_data: Dict):
        """Broadcast league table updates"""
        # Get active leagues from connected clients
        active_leagues = set()
        for room in self.websocket_manager._rooms:
            if room.startswith("league_"):
                league_id = int(room.split("_")[1])
                active_leagues.add(league_id)
                
        # Update each active league
        for league_id in active_leagues:
            try:
                # Get updated standings
                standings = await self.live_data_service.get_h2h_league_standings(league_id)
                
                # Broadcast to league room
                await self.websocket_manager.broadcast_to_room(
                    f"league_{league_id}",
                    {
                        "type": "league_update",
                        "league_id": league_id,
                        "gameweek": gameweek,
                        "standings": standings,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            except Exception as e:
                logger.error(f"Error broadcasting league {league_id} updates: {e}")
                
    async def get_live_match_data(self, gameweek: int, fixture_id: Optional[int] = None) -> List[LiveMatchData]:
        """Get current live match data"""
        matches = []
        
        live_data = self._cached_live_data.get(gameweek)
        if not live_data:
            live_data = await self.live_data_service.get_live_gameweek_data(gameweek)
            
        if not live_data:
            return matches
            
        bootstrap = await self.live_data_service.get_bootstrap_static()
        teams = {t["id"]: t["name"] for t in bootstrap["teams"]}
        
        for fixture in live_data.get("fixtures", []):
            if fixture_id and fixture["id"] != fixture_id:
                continue
                
            # Extract events for this fixture
            fixture_events = []
            
            # Calculate provisional bonus
            bonus = {}
            
            match_data = LiveMatchData(
                fixture_id=fixture["id"],
                home_team=teams.get(fixture["team_h"], "Unknown"),
                away_team=teams.get(fixture["team_a"], "Unknown"),
                score=f"{fixture.get('team_h_score', 0)}-{fixture.get('team_a_score', 0)}",
                started=fixture["started"],
                finished=fixture["finished"],
                minutes=fixture.get("minutes", 0),
                bonus=bonus,
                events=fixture_events
            )
            
            matches.append(match_data)
            
        return matches
        
    async def subscribe_to_h2h_battle(self, client_id: str, manager1_id: int, manager2_id: int):
        """Subscribe a client to H2H battle updates"""
        room_name = f"h2h_{min(manager1_id, manager2_id)}_{max(manager1_id, manager2_id)}"
        await self.websocket_manager.subscribe_to_room(client_id, room_name)
        logger.info(f"Client {client_id} subscribed to H2H battle {manager1_id} vs {manager2_id}")
        
    async def subscribe_to_league(self, client_id: str, league_id: int):
        """Subscribe a client to league updates"""
        room_name = f"league_{league_id}"
        await self.websocket_manager.subscribe_to_room(client_id, room_name)
        logger.info(f"Client {client_id} subscribed to league {league_id}")
        
    async def subscribe_to_gameweek(self, client_id: str, gameweek: int):
        """Subscribe a client to gameweek updates"""
        room_name = f"live_gw_{gameweek}"
        await self.websocket_manager.subscribe_to_room(client_id, room_name)
        logger.info(f"Client {client_id} subscribed to gameweek {gameweek}")
