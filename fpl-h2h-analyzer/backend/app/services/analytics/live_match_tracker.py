"""
Live Match Tracker
Real-time score updates with provisional bonus and position changes
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class LivePlayerStatus:
    """Real-time status of a player"""
    player_id: int
    name: str
    team: str
    position: str
    
    # Live stats
    minutes: int
    goals: int
    assists: int
    clean_sheet: bool
    yellow_cards: int
    red_cards: int
    saves: int
    penalties_saved: int
    penalties_missed: int
    own_goals: int
    
    # Live scoring
    current_points: int
    provisional_bonus: int
    bps: int
    
    # Match status
    is_playing: bool
    is_benched: bool
    subbed_off: bool
    subbed_on_minute: Optional[int]
    
    # Ownership in this H2H
    owned_by: List[str]  # ['manager1', 'manager2', 'both']
    is_captain: Dict[str, bool]  # {'manager1': False, 'manager2': True}
    is_vice_captain: Dict[str, bool]


@dataclass
class LiveMatchState:
    """Current state of the H2H match"""
    gameweek: int
    last_updated: datetime
    fixtures_status: Dict[int, str]  # fixture_id: 'not_started', 'in_progress', 'finished'
    
    # Current scores
    manager1_score: int
    manager2_score: int
    manager1_projected: int  # Including provisional bonus
    manager2_projected: int
    
    # Score breakdown
    manager1_players: List[LivePlayerStatus]
    manager2_players: List[LivePlayerStatus]
    
    # Key events
    score_changes: List[Dict[str, Any]]
    position_changes: List[Dict[str, Any]]
    
    # Live advantage
    current_advantage: str  # 'manager1', 'manager2', 'tied'
    advantage_margin: int
    momentum: str  # 'manager1_gaining', 'manager2_gaining', 'stable'


@dataclass
class BonusProjection:
    """Provisional bonus point projection"""
    player_id: int
    player_name: str
    bps: int
    projected_bonus: int
    confidence: float  # 0-1 scale
    owned_by: List[str]


class LiveMatchTracker:
    """
    Tracks H2H matches in real-time during gameweeks
    """
    
    def __init__(self):
        self.update_interval = 30  # seconds
        self.bps_thresholds = {
            3: 0,    # Top BPS gets 3 bonus
            2: -5,   # Within 5 BPS gets 2 bonus  
            1: -10   # Within 10 BPS gets 1 bonus
        }
        self._tracking_tasks = {}
    
    async def track_live_match(
        self,
        manager1_id: int,
        manager2_id: int,
        manager1_picks: Dict[str, Any],
        manager2_picks: Dict[str, Any],
        live_data: Dict[str, Any],
        fixtures: List[Dict[str, Any]],
        bootstrap_data: Dict[str, Any]
    ) -> LiveMatchState:
        """
        Get current live match state
        """
        try:
            # Get player data
            players_by_id = {p['id']: p for p in bootstrap_data['elements']}
            teams_by_id = {t['id']: t for t in bootstrap_data['teams']}
            
            # Get current gameweek
            current_gw = next(
                e['id'] for e in bootstrap_data['events'] 
                if e['is_current']
            )
            
            # Track fixture status
            fixtures_status = await self._get_fixtures_status(fixtures)
            
            # Get live player statuses
            m1_players = await self._get_live_player_statuses(
                manager1_picks, live_data, players_by_id, 
                teams_by_id, 'manager1', manager2_picks
            )
            
            m2_players = await self._get_live_player_statuses(
                manager2_picks, live_data, players_by_id,
                teams_by_id, 'manager2', manager1_picks
            )
            
            # Calculate scores
            m1_score = sum(p.current_points for p in m1_players[:11])  # Starting XI
            m2_score = sum(p.current_points for p in m2_players[:11])
            
            # Add captain points
            m1_captain = next((p for p in m1_players if p.is_captain.get('manager1')), None)
            m2_captain = next((p for p in m2_players if p.is_captain.get('manager2')), None)
            
            if m1_captain:
                m1_score += m1_captain.current_points
            if m2_captain:
                m2_score += m2_captain.current_points
            
            # Calculate provisional bonus
            bonus_projections = await self._calculate_provisional_bonus(
                fixtures, live_data, m1_players + m2_players
            )
            
            # Add provisional bonus to projected scores
            m1_projected = m1_score
            m2_projected = m2_score
            
            for proj in bonus_projections:
                if 'manager1' in proj.owned_by:
                    m1_projected += proj.projected_bonus
                    # Double if captain
                    player = next((p for p in m1_players if p.player_id == proj.player_id), None)
                    if player and player.is_captain.get('manager1'):
                        m1_projected += proj.projected_bonus
                        
                if 'manager2' in proj.owned_by:
                    m2_projected += proj.projected_bonus
                    # Double if captain
                    player = next((p for p in m2_players if p.player_id == proj.player_id), None)
                    if player and player.is_captain.get('manager2'):
                        m2_projected += proj.projected_bonus
            
            # Determine advantage and momentum
            if m1_projected > m2_projected:
                current_advantage = 'manager1'
                advantage_margin = m1_projected - m2_projected
            elif m2_projected > m1_projected:
                current_advantage = 'manager2'
                advantage_margin = m2_projected - m1_projected
            else:
                current_advantage = 'tied'
                advantage_margin = 0
            
            # Track score changes (would need history for real implementation)
            score_changes = []
            position_changes = []
            
            # Determine momentum (simplified)
            momentum = await self._calculate_momentum(
                m1_players, m2_players, fixtures_status
            )
            
            return LiveMatchState(
                gameweek=current_gw,
                last_updated=datetime.now(),
                fixtures_status=fixtures_status,
                manager1_score=m1_score,
                manager2_score=m2_score,
                manager1_projected=m1_projected,
                manager2_projected=m2_projected,
                manager1_players=m1_players,
                manager2_players=m2_players,
                score_changes=score_changes,
                position_changes=position_changes,
                current_advantage=current_advantage,
                advantage_margin=advantage_margin,
                momentum=momentum
            )
            
        except Exception as e:
            logger.error(f"Error tracking live match: {e}")
            raise
    
    async def start_continuous_tracking(
        self,
        manager1_id: int,
        manager2_id: int,
        callback: Any
    ) -> str:
        """
        Start continuous tracking with updates via callback
        Returns tracking ID
        """
        tracking_id = f"{manager1_id}_{manager2_id}_{datetime.now().timestamp()}"
        
        async def track_loop():
            while tracking_id in self._tracking_tasks:
                try:
                    # Get latest data (would fetch from API)
                    # For now, simulate with callback
                    await callback(tracking_id)
                    await asyncio.sleep(self.update_interval)
                except Exception as e:
                    logger.error(f"Error in tracking loop: {e}")
                    await asyncio.sleep(self.update_interval)
        
        task = asyncio.create_task(track_loop())
        self._tracking_tasks[tracking_id] = task
        
        return tracking_id
    
    async def stop_tracking(self, tracking_id: str):
        """Stop continuous tracking"""
        if tracking_id in self._tracking_tasks:
            self._tracking_tasks[tracking_id].cancel()
            del self._tracking_tasks[tracking_id]
    
    async def _get_fixtures_status(
        self,
        fixtures: List[Dict[str, Any]]
    ) -> Dict[int, str]:
        """Get current status of all fixtures"""
        status = {}
        
        for fixture in fixtures:
            if fixture.get('finished'):
                status[fixture['id']] = 'finished'
            elif fixture.get('started'):
                status[fixture['id']] = 'in_progress'
            else:
                status[fixture['id']] = 'not_started'
        
        return status
    
    async def _get_live_player_statuses(
        self,
        manager_picks: Dict[str, Any],
        live_data: Dict[str, Any],
        players_by_id: Dict[int, Any],
        teams_by_id: Dict[int, Any],
        manager_name: str,
        opponent_picks: Dict[str, Any]
    ) -> List[LivePlayerStatus]:
        """Get live status for all players in a team"""
        statuses = []
        
        # Get opponent's players for ownership info
        opponent_players = {p['element'] for p in opponent_picks['picks']}
        
        for pick in manager_picks['picks']:
            player_id = pick['element']
            player = players_by_id.get(player_id)
            
            if not player:
                continue
            
            # Get live data
            live_player = next(
                (p for p in live_data.get('elements', []) if p['id'] == player_id),
                None
            )
            
            if not live_player:
                continue
            
            stats = live_player.get('stats', {})
            
            # Determine ownership
            owned_by = [manager_name]
            if player_id in opponent_players:
                owned_by.append('both')
            
            # Captain/vice captain status
            is_captain = {
                manager_name: pick['is_captain'],
                'opponent': any(
                    p['element'] == player_id and p['is_captain'] 
                    for p in opponent_picks['picks']
                )
            }
            
            is_vice_captain = {
                manager_name: pick['is_vice_captain'],
                'opponent': any(
                    p['element'] == player_id and p['is_vice_captain']
                    for p in opponent_picks['picks']
                )
            }
            
            # Playing status
            minutes = stats.get('minutes', 0)
            is_playing = minutes > 0
            is_benched = pick['position'] > 11
            
            # Check if subbed off (simplified - would need detailed data)
            subbed_off = is_playing and minutes < 90 and minutes > 0
            
            status = LivePlayerStatus(
                player_id=player_id,
                name=player['web_name'],
                team=teams_by_id[player['team']]['short_name'],
                position=['GKP', 'DEF', 'MID', 'FWD'][player['element_type'] - 1],
                minutes=minutes,
                goals=stats.get('goals_scored', 0),
                assists=stats.get('assists', 0),
                clean_sheet=stats.get('clean_sheets', 0) > 0,
                yellow_cards=stats.get('yellow_cards', 0),
                red_cards=stats.get('red_cards', 0),
                saves=stats.get('saves', 0),
                penalties_saved=stats.get('penalties_saved', 0),
                penalties_missed=stats.get('penalties_missed', 0),
                own_goals=stats.get('own_goals', 0),
                current_points=stats.get('total_points', 0),
                provisional_bonus=0,  # Set later
                bps=stats.get('bps', 0),
                is_playing=is_playing,
                is_benched=is_benched,
                subbed_off=subbed_off,
                subbed_on_minute=None,  # Would need detailed data
                owned_by=owned_by,
                is_captain=is_captain,
                is_vice_captain=is_vice_captain
            )
            
            statuses.append(status)
        
        # Sort by position (1-15)
        statuses.sort(key=lambda x: manager_picks['picks'][
            next(i for i, p in enumerate(manager_picks['picks']) if p['element'] == x.player_id)
        ]['position'])
        
        return statuses
    
    async def _calculate_provisional_bonus(
        self,
        fixtures: List[Dict[str, Any]],
        live_data: Dict[str, Any],
        relevant_players: List[LivePlayerStatus]
    ) -> List[BonusProjection]:
        """Calculate provisional bonus points based on current BPS"""
        projections = []
        
        # Group by fixture
        fixture_players = {}
        for player in relevant_players:
            if player.is_playing:
                # Find player's fixture (simplified)
                for fixture in fixtures:
                    if fixture['id'] not in fixture_players:
                        fixture_players[fixture['id']] = []
                    # Would need to match player team to fixture
                    # For now, add to first in-progress fixture
                    if fixture.get('started') and not fixture.get('finished'):
                        fixture_players[fixture['id']].append(player)
                        break
        
        # Calculate bonus for each fixture
        for fixture_id, players in fixture_players.items():
            if not players:
                continue
            
            # Sort by BPS
            players.sort(key=lambda x: x.bps, reverse=True)
            
            # Assign provisional bonus
            if len(players) >= 1 and players[0].bps > 0:
                projections.append(BonusProjection(
                    player_id=players[0].player_id,
                    player_name=players[0].name,
                    bps=players[0].bps,
                    projected_bonus=3,
                    confidence=0.8 if players[0].bps > 30 else 0.6,
                    owned_by=players[0].owned_by
                ))
            
            if len(players) >= 2 and players[1].bps > 0:
                # Check if within threshold of top player
                if players[0].bps - players[1].bps <= 5:
                    bonus = 2
                    confidence = 0.6
                else:
                    bonus = 2
                    confidence = 0.8
                
                projections.append(BonusProjection(
                    player_id=players[1].player_id,
                    player_name=players[1].name,
                    bps=players[1].bps,
                    projected_bonus=bonus,
                    confidence=confidence,
                    owned_by=players[1].owned_by
                ))
            
            if len(players) >= 3 and players[2].bps > 0:
                # Check if within threshold
                if players[1].bps - players[2].bps <= 5:
                    bonus = 1
                    confidence = 0.6
                else:
                    bonus = 1
                    confidence = 0.8
                
                projections.append(BonusProjection(
                    player_id=players[2].player_id,
                    player_name=players[2].name,
                    bps=players[2].bps,
                    projected_bonus=bonus,
                    confidence=confidence,
                    owned_by=players[2].owned_by
                ))
        
        return projections
    
    async def _calculate_momentum(
        self,
        m1_players: List[LivePlayerStatus],
        m2_players: List[LivePlayerStatus],
        fixtures_status: Dict[int, str]
    ) -> str:
        """Calculate match momentum based on recent events"""
        # Count players still playing
        m1_active = sum(1 for p in m1_players[:11] if p.is_playing and not p.subbed_off)
        m2_active = sum(1 for p in m2_players[:11] if p.is_playing and not p.subbed_off)
        
        # Count fixtures in progress
        in_progress = sum(1 for status in fixtures_status.values() if status == 'in_progress')
        
        if in_progress == 0:
            return 'stable'
        
        # Simple momentum based on active players
        if m1_active > m2_active + 2:
            return 'manager1_gaining'
        elif m2_active > m1_active + 2:
            return 'manager2_gaining'
        else:
            return 'stable'
    
    def get_score_timeline(
        self,
        match_state: LiveMatchState
    ) -> List[Dict[str, Any]]:
        """Get timeline of score changes"""
        timeline = []
        
        # Add key events
        for player in match_state.manager1_players + match_state.manager2_players:
            if player.goals > 0:
                for _ in range(player.goals):
                    timeline.append({
                        'type': 'goal',
                        'player': player.name,
                        'team': player.owned_by[0],
                        'points': 6 if player.position == 'FWD' else 5 if player.position == 'MID' else 6,
                        'is_captain': player.is_captain.get(player.owned_by[0], False)
                    })
            
            if player.assists > 0:
                for _ in range(player.assists):
                    timeline.append({
                        'type': 'assist',
                        'player': player.name,
                        'team': player.owned_by[0],
                        'points': 3,
                        'is_captain': player.is_captain.get(player.owned_by[0], False)
                    })
        
        return timeline
    
    def get_live_differentials(
        self,
        match_state: LiveMatchState
    ) -> Dict[str, Any]:
        """Get live differential impact"""
        m1_unique = [p for p in match_state.manager1_players if 'both' not in p.owned_by]
        m2_unique = [p for p in match_state.manager2_players if 'both' not in p.owned_by]
        
        return {
            'manager1_differentials': [
                {
                    'player': p.name,
                    'points': p.current_points,
                    'is_captain': p.is_captain.get('manager1', False),
                    'effective_points': p.current_points * (2 if p.is_captain.get('manager1') else 1)
                }
                for p in m1_unique
            ],
            'manager2_differentials': [
                {
                    'player': p.name,
                    'points': p.current_points,
                    'is_captain': p.is_captain.get('manager2', False),
                    'effective_points': p.current_points * (2 if p.is_captain.get('manager2') else 1)
                }
                for p in m2_unique
            ],
            'differential_advantage': sum(
                p.current_points * (2 if p.is_captain.get('manager1') else 1) 
                for p in m1_unique
            ) - sum(
                p.current_points * (2 if p.is_captain.get('manager2') else 1)
                for p in m2_unique
            )
        }