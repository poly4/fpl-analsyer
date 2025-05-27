"""
Differential Impact Calculator
Analyzes the impact of unique players between H2H teams
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import statistics

logger = logging.getLogger(__name__)


@dataclass
class DifferentialPlayer:
    """Represents a differential player with impact metrics"""
    player_id: int
    name: str
    team: str
    position: str
    owned_by: str  # 'manager1' or 'manager2'
    
    # Core stats
    ownership_overall: float
    ownership_league: float
    ownership_h2h: float  # Within this H2H matchup
    
    # Performance metrics
    current_points: int
    expected_points: float
    form: float
    minutes_played: int
    
    # Impact scores
    differential_impact: float  # Main impact score
    captain_impact: float  # Impact if captained
    volatility_score: float  # How unpredictable
    ceiling_score: float  # Maximum potential
    floor_score: float  # Minimum expected
    
    # Fixture analysis
    fixture_difficulty: float
    home_away: str
    opponent_team: str


class DifferentialImpactCalculator:
    """
    Calculates the impact of differential players in H2H battles
    """
    
    def __init__(self):
        self.position_weights = {
            1: 1.0,   # GKP
            2: 1.2,   # DEF
            3: 1.5,   # MID
            4: 1.8    # FWD
        }
        
    async def calculate_differential_impact(
        self,
        manager1_picks: Dict[str, Any],
        manager2_picks: Dict[str, Any],
        live_data: Dict[str, Any],
        bootstrap_data: Dict[str, Any],
        league_ownership: Optional[Dict[int, float]] = None,
        fixtures: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive differential impact analysis
        """
        try:
            # Extract picks
            m1_players = {p['element'] for p in manager1_picks['picks']}
            m2_players = {p['element'] for p in manager2_picks['picks']}
            
            # Find differentials
            m1_unique = m1_players - m2_players
            m2_unique = m2_players - m1_unique
            
            # Get player data
            players_by_id = {p['id']: p for p in bootstrap_data['elements']}
            teams_by_id = {t['id']: t for t in bootstrap_data['teams']}
            positions = {et['id']: et['singular_name_short'] for et in bootstrap_data['element_types']}
            
            # Calculate league ownership if not provided
            if not league_ownership:
                league_ownership = await self._estimate_league_ownership(
                    bootstrap_data, m1_players | m2_players
                )
            
            # Analyze differentials
            m1_differentials = []
            m2_differentials = []
            
            for player_id in m1_unique:
                differential = await self._analyze_differential(
                    player_id, 'manager1', players_by_id, teams_by_id, 
                    positions, live_data, league_ownership, fixtures
                )
                if differential:
                    m1_differentials.append(differential)
                    
            for player_id in m2_unique:
                differential = await self._analyze_differential(
                    player_id, 'manager2', players_by_id, teams_by_id,
                    positions, live_data, league_ownership, fixtures
                )
                if differential:
                    m2_differentials.append(differential)
            
            # Sort by impact
            m1_differentials.sort(key=lambda x: x.differential_impact, reverse=True)
            m2_differentials.sort(key=lambda x: x.differential_impact, reverse=True)
            
            # Calculate aggregate metrics
            analysis = {
                "manager1_differentials": [self._serialize_differential(d) for d in m1_differentials],
                "manager2_differentials": [self._serialize_differential(d) for d in m2_differentials],
                "total_differential_impact": {
                    "manager1": sum(d.differential_impact for d in m1_differentials),
                    "manager2": sum(d.differential_impact for d in m2_differentials),
                    "net_advantage": sum(d.differential_impact for d in m1_differentials) - 
                                   sum(d.differential_impact for d in m2_differentials)
                },
                "captain_analysis": await self._analyze_captain_differentials(
                    manager1_picks, manager2_picks, players_by_id, live_data
                ),
                "key_battlegrounds": await self._identify_key_battlegrounds(
                    m1_differentials, m2_differentials
                ),
                "effective_ownership": {
                    "manager1_advantage": len(m1_unique),
                    "manager2_advantage": len(m2_unique),
                    "shared_players": len(m1_players & m2_players)
                }
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error calculating differential impact: {e}")
            return {}
    
    async def _analyze_differential(
        self,
        player_id: int,
        owned_by: str,
        players_by_id: Dict[int, Any],
        teams_by_id: Dict[int, Any],
        positions: Dict[int, str],
        live_data: Dict[str, Any],
        league_ownership: Dict[int, float],
        fixtures: Optional[List[Dict[str, Any]]]
    ) -> Optional[DifferentialPlayer]:
        """Analyze a single differential player"""
        try:
            player = players_by_id.get(player_id)
            if not player:
                return None
                
            # Get live stats
            live_player = next((p for p in live_data.get('elements', []) if p['id'] == player_id), {})
            
            # Calculate ownership levels
            ownership_overall = player.get('selected_by_percent', '0')
            ownership_overall = float(ownership_overall) if isinstance(ownership_overall, str) else ownership_overall
            ownership_league = league_ownership.get(player_id, ownership_overall)
            ownership_h2h = 50.0  # One manager owns in a 2-person matchup
            
            # Get performance metrics
            current_points = live_player.get('stats', {}).get('total_points', 0)
            form = float(player.get('form', 0))
            minutes = live_player.get('stats', {}).get('minutes', 0)
            
            # Calculate expected points
            ep_next = float(player.get('ep_next', '0'))
            
            # Get fixture difficulty
            fixture_diff, home_away, opponent = await self._get_fixture_context(
                player, fixtures, teams_by_id
            )
            
            # Calculate impact scores
            position_weight = self.position_weights.get(player['element_type'], 1.0)
            
            # Differential impact formula
            ownership_factor = (100 - ownership_league) / 100  # Higher impact for lower ownership
            form_factor = form / 10 if form > 0 else 0.1
            minutes_factor = minutes / 90 if minutes > 0 else 0.5
            
            differential_impact = (
                ep_next * position_weight * ownership_factor * form_factor * minutes_factor
            )
            
            # Captain impact (double the differential impact)
            captain_impact = differential_impact * 2
            
            # Volatility based on past performance variance
            volatility_score = await self._calculate_volatility(player, live_player)
            
            # Ceiling and floor
            ceiling_score = ep_next * 2.5 * position_weight
            floor_score = max(0, ep_next * 0.3 * minutes_factor)
            
            return DifferentialPlayer(
                player_id=player_id,
                name=player['web_name'],
                team=teams_by_id[player['team']]['short_name'],
                position=positions[player['element_type']],
                owned_by=owned_by,
                ownership_overall=ownership_overall,
                ownership_league=ownership_league,
                ownership_h2h=ownership_h2h,
                current_points=current_points,
                expected_points=ep_next,
                form=form,
                minutes_played=minutes,
                differential_impact=differential_impact,
                captain_impact=captain_impact,
                volatility_score=volatility_score,
                ceiling_score=ceiling_score,
                floor_score=floor_score,
                fixture_difficulty=fixture_diff,
                home_away=home_away,
                opponent_team=opponent
            )
            
        except Exception as e:
            logger.error(f"Error analyzing differential player {player_id}: {e}")
            return None
    
    async def _get_fixture_context(
        self,
        player: Dict[str, Any],
        fixtures: Optional[List[Dict[str, Any]]],
        teams_by_id: Dict[int, Any]
    ) -> Tuple[float, str, str]:
        """Get fixture context for a player"""
        if not fixtures:
            return 3.0, 'unknown', 'unknown'
            
        team_id = player['team']
        next_fixture = next(
            (f for f in fixtures if not f['finished'] and 
             (f['team_h'] == team_id or f['team_a'] == team_id)),
            None
        )
        
        if not next_fixture:
            return 3.0, 'unknown', 'unknown'
            
        if next_fixture['team_h'] == team_id:
            difficulty = next_fixture['team_h_difficulty']
            home_away = 'home'
            opponent_id = next_fixture['team_a']
        else:
            difficulty = next_fixture['team_a_difficulty']
            home_away = 'away'
            opponent_id = next_fixture['team_h']
            
        opponent = teams_by_id[opponent_id]['short_name']
        
        return float(difficulty), home_away, opponent
    
    async def _calculate_volatility(
        self,
        player: Dict[str, Any],
        live_player: Dict[str, Any]
    ) -> float:
        """Calculate player volatility score"""
        try:
            # Get recent gameweek scores (would need historical data)
            # For now, use form and position as proxy
            form = float(player.get('form', 0))
            position = player['element_type']
            
            # Higher volatility for attackers, lower for defenders
            position_volatility = {
                1: 0.3,  # GKP
                2: 0.4,  # DEF
                3: 0.6,  # MID
                4: 0.8   # FWD
            }
            
            base_volatility = position_volatility.get(position, 0.5)
            
            # Adjust based on form variance
            if form > 6:
                volatility = base_volatility * 0.8  # Consistent high performer
            elif form < 3:
                volatility = base_volatility * 1.3  # Inconsistent
            else:
                volatility = base_volatility
                
            return min(1.0, max(0.1, volatility))
            
        except:
            return 0.5
    
    async def _estimate_league_ownership(
        self,
        bootstrap_data: Dict[str, Any],
        league_players: set
    ) -> Dict[int, float]:
        """Estimate league ownership based on overall ownership"""
        # In a real implementation, this would calculate from actual league data
        # For now, use overall ownership with slight adjustments
        ownership = {}
        
        for player in bootstrap_data['elements']:
            overall = float(player.get('selected_by_percent', '0'))
            
            # Assume league ownership is slightly higher for popular players
            if player['id'] in league_players:
                league_own = min(100, overall * 1.2)
            else:
                league_own = overall * 0.9
                
            ownership[player['id']] = league_own
            
        return ownership
    
    async def _analyze_captain_differentials(
        self,
        manager1_picks: Dict[str, Any],
        manager2_picks: Dict[str, Any],
        players_by_id: Dict[int, Any],
        live_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze captain choice differentials"""
        m1_captain = next(p['element'] for p in manager1_picks['picks'] if p['is_captain'])
        m2_captain = next(p['element'] for p in manager2_picks['picks'] if p['is_captain'])
        
        same_captain = m1_captain == m2_captain
        
        # Get captain points
        m1_cap_live = next((p for p in live_data.get('elements', []) if p['id'] == m1_captain), {})
        m2_cap_live = next((p for p in live_data.get('elements', []) if p['id'] == m2_captain), {})
        
        m1_cap_points = m1_cap_live.get('stats', {}).get('total_points', 0)
        m2_cap_points = m2_cap_live.get('stats', {}).get('total_points', 0)
        
        # Captain swing is the differential doubled
        captain_swing = (m1_cap_points - m2_cap_points) * 2
        
        return {
            "same_captain": same_captain,
            "manager1_captain": {
                "id": m1_captain,
                "name": players_by_id[m1_captain]['web_name'],
                "points": m1_cap_points,
                "effective_points": m1_cap_points * 2
            },
            "manager2_captain": {
                "id": m2_captain,
                "name": players_by_id[m2_captain]['web_name'],
                "points": m2_cap_points,
                "effective_points": m2_cap_points * 2
            },
            "captain_swing": captain_swing,
            "net_captain_advantage": captain_swing
        }
    
    async def _identify_key_battlegrounds(
        self,
        m1_differentials: List[DifferentialPlayer],
        m2_differentials: List[DifferentialPlayer]
    ) -> List[Dict[str, Any]]:
        """Identify key areas where the match will be won/lost"""
        battlegrounds = []
        
        # Position battles
        positions = ['GKP', 'DEF', 'MID', 'FWD']
        for pos in positions:
            m1_pos = [d for d in m1_differentials if d.position == pos]
            m2_pos = [d for d in m2_differentials if d.position == pos]
            
            if m1_pos or m2_pos:
                m1_impact = sum(d.differential_impact for d in m1_pos)
                m2_impact = sum(d.differential_impact for d in m2_pos)
                
                battlegrounds.append({
                    "area": f"{pos} differentials",
                    "manager1_impact": m1_impact,
                    "manager2_impact": m2_impact,
                    "advantage": "manager1" if m1_impact > m2_impact else "manager2",
                    "swing_potential": abs(m1_impact - m2_impact)
                })
        
        # High ceiling players
        high_ceiling_m1 = [d for d in m1_differentials if d.ceiling_score > 15]
        high_ceiling_m2 = [d for d in m2_differentials if d.ceiling_score > 15]
        
        if high_ceiling_m1 or high_ceiling_m2:
            battlegrounds.append({
                "area": "High ceiling differentials",
                "manager1_players": len(high_ceiling_m1),
                "manager2_players": len(high_ceiling_m2),
                "key_players": [d.name for d in high_ceiling_m1 + high_ceiling_m2]
            })
        
        return sorted(battlegrounds, key=lambda x: x.get('swing_potential', 0), reverse=True)
    
    def _serialize_differential(self, diff: DifferentialPlayer) -> Dict[str, Any]:
        """Serialize differential player to dict"""
        return {
            "player_id": diff.player_id,
            "name": diff.name,
            "team": diff.team,
            "position": diff.position,
            "owned_by": diff.owned_by,
            "ownership": {
                "overall": diff.ownership_overall,
                "league": diff.ownership_league,
                "h2h": diff.ownership_h2h
            },
            "performance": {
                "current_points": diff.current_points,
                "expected_points": diff.expected_points,
                "form": diff.form,
                "minutes": diff.minutes_played
            },
            "impact_scores": {
                "differential_impact": round(diff.differential_impact, 2),
                "captain_impact": round(diff.captain_impact, 2),
                "volatility": round(diff.volatility_score, 2),
                "ceiling": round(diff.ceiling_score, 2),
                "floor": round(diff.floor_score, 2)
            },
            "fixture": {
                "difficulty": diff.fixture_difficulty,
                "venue": diff.home_away,
                "opponent": diff.opponent_team
            }
        }