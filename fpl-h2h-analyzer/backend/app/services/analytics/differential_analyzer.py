from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DifferentialAnalyzer:
    """
    Service responsible for in-depth analysis of player differentials between two FPL managers.
    Calculates Point Swing Contribution (PSC), Risk/Reward Scoring, and Strategic Value.
    """
    
    def __init__(self):
        """
        Initialize the Differential Analyzer.
        
        Note: LiveDataService can be passed if needed for additional data,
        but we prioritize using data passed directly to methods.
        """
        logger.info("DifferentialAnalyzer initialized")
        
        # Position type mappings
        self.position_names = {1: 'GKP', 2: 'DEF', 3: 'MID', 4: 'FWD'}
        
        # Fixture difficulty ratings (simplified - in reality would come from API)
        self.fixture_difficulty_base = {
            1: 0.5,  # Very easy
            2: 0.7,  # Easy
            3: 1.0,  # Medium
            4: 1.3,  # Hard
            5: 1.5   # Very hard
        }
    
    async def analyze_differentials(
        self,
        manager1_picks_data: Dict[str, Any],
        manager2_picks_data: Dict[str, Any],
        live_gameweek_data: Dict[str, Any],
        bootstrap_static_data: Dict[str, Any],
        manager1_id: int,
        manager2_id: int,
        gameweek: int
    ) -> Dict[str, Any]:
        """
        Perform comprehensive differential analysis between two managers.
        
        Args:
            manager1_picks_data: Manager 1's picks from API
            manager2_picks_data: Manager 2's picks from API
            live_gameweek_data: Live gameweek data
            bootstrap_static_data: Bootstrap static data
            manager1_id: First manager's ID
            manager2_id: Second manager's ID
            gameweek: Current gameweek
            
        Returns:
            Dict containing differential analysis results
        """
        logger.info(f"Analyzing differentials for managers {manager1_id} vs {manager2_id}, GW{gameweek}")
        
        # Extract picks and create lookup structures
        m1_picks = self._extract_starting_xi(manager1_picks_data)
        m2_picks = self._extract_starting_xi(manager2_picks_data)
        
        # Get player and team data
        players_dict = {p['id']: p for p in bootstrap_static_data.get('elements', [])}
        teams_dict = {t['id']: t for t in bootstrap_static_data.get('teams', [])}
        live_elements = {e['id']: e for e in live_gameweek_data.get('elements', [])}
        
        # Identify differentials
        m1_differentials = []
        m2_differentials = []
        captain_analysis = {}
        
        # Process Manager 1's unique players
        for player_id, pick_info in m1_picks.items():
            if player_id not in m2_picks:
                differential_data = await self._analyze_differential_player(
                    player_id, pick_info, players_dict, teams_dict, 
                    live_elements, manager1_id, manager1_picks_data
                )
                if differential_data:
                    m1_differentials.append(differential_data)
        
        # Process Manager 2's unique players
        for player_id, pick_info in m2_picks.items():
            if player_id not in m1_picks:
                differential_data = await self._analyze_differential_player(
                    player_id, pick_info, players_dict, teams_dict, 
                    live_elements, manager2_id, manager2_picks_data
                )
                if differential_data:
                    m2_differentials.append(differential_data)
        
        # Analyze captaincy
        captain_analysis = await self._analyze_captaincy(
            m1_picks, m2_picks, players_dict, live_elements,
            manager1_picks_data, manager2_picks_data
        )
        
        # Determine key differentials based on strategic value
        all_differentials = m1_differentials + m2_differentials
        key_differentials = sorted(
            all_differentials, 
            key=lambda x: x['strategic_value'], 
            reverse=True
        )[:5]
        
        return {
            "manager1_differentials": sorted(m1_differentials, key=lambda x: x['psc'], reverse=True),
            "manager2_differentials": sorted(m2_differentials, key=lambda x: x['psc'], reverse=True),
            "key_differentials": key_differentials,
            "captain_analysis": captain_analysis,
            "total_psc_swing": {
                "manager1": sum(d['psc'] for d in m1_differentials),
                "manager2": sum(d['psc'] for d in m2_differentials),
                "net_advantage": sum(d['psc'] for d in m1_differentials) - sum(d['psc'] for d in m2_differentials)
            }
        }
    
    def _extract_starting_xi(self, picks_data: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
        """Extract starting XI players from picks data."""
        starting_xi = {}
        if not picks_data or 'picks' not in picks_data:
            return starting_xi
        
        for pick in picks_data.get('picks', []):
            if pick['position'] <= 11:  # Starting XI only
                starting_xi[pick['element']] = pick
        
        return starting_xi
    
    async def _analyze_differential_player(
        self,
        player_id: int,
        pick_info: Dict[str, Any],
        players_dict: Dict[int, Dict[str, Any]],
        teams_dict: Dict[int, Dict[str, Any]],
        live_elements: Dict[int, Dict[str, Any]],
        owner_id: int,
        picks_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze a single differential player.
        
        Returns:
            Dict with player analysis or None if data missing
        """
        player_static = players_dict.get(player_id)
        player_live = live_elements.get(player_id)
        
        if not player_static or not player_live:
            return None
        
        # Get team info
        team = teams_dict.get(player_static.get('team', 0), {})
        
        # Calculate live points with captaincy
        base_points = player_live.get('stats', {}).get('total_points', 0)
        is_captain = pick_info.get('is_captain', False)
        is_triple_captain = is_captain and picks_data.get('active_chip') == '3xc'
        
        if is_triple_captain:
            actual_points = base_points * 3
        elif is_captain:
            actual_points = base_points * 2
        else:
            actual_points = base_points
        
        # PSC for H2H is simply the points gained from having this player
        psc = actual_points
        
        # Calculate risk/reward scores
        risk_score = self._calculate_risk_score(player_static, player_live, team)
        reward_score = self._calculate_reward_score(player_static, player_live)
        
        # Calculate strategic value
        strategic_value = self._calculate_strategic_value(
            psc, risk_score, reward_score, player_static
        )
        
        return {
            "player_id": player_id,
            "name": player_static.get('web_name', 'Unknown'),
            "team": team.get('short_name', 'Unknown'),
            "position": self.position_names.get(player_static.get('element_type', 0), 'Unknown'),
            "owner": owner_id,
            "psc": psc,
            "live_points": base_points,
            "actual_points": actual_points,
            "is_captain": is_captain,
            "is_triple_captain": is_triple_captain,
            "risk_score": risk_score,
            "reward_score": reward_score,
            "strategic_value": strategic_value,
            "ownership": float(player_static.get('selected_by_percent', 0)),
            "price": player_static.get('now_cost', 0) / 10,
            "form": float(player_static.get('form', 0)),
            "minutes": player_live.get('stats', {}).get('minutes', 0),
            "xG": player_static.get('expected_goals', 0),
            "xA": player_static.get('expected_assists', 0),
            "threat": player_static.get('threat', 0),
            "influence": player_static.get('influence', 0),
            "creativity": player_static.get('creativity', 0)
        }
    
    def _calculate_risk_score(
        self, 
        player_static: Dict[str, Any], 
        player_live: Dict[str, Any],
        team: Dict[str, Any]
    ) -> float:
        """
        Calculate risk score for a player (1-5, lower is better).
        
        Factors:
        - Injury/availability risk
        - Form trending
        - Team fixture difficulty
        - Recent minutes played
        """
        risk_score = 2.5  # Base neutral score
        
        # Injury/availability risk
        chance_of_playing = player_static.get('chance_of_playing_next_round')
        if chance_of_playing is not None and chance_of_playing < 100:
            if chance_of_playing < 25:
                risk_score += 2.0
            elif chance_of_playing < 50:
                risk_score += 1.5
            elif chance_of_playing < 75:
                risk_score += 1.0
            else:
                risk_score += 0.5
        
        # Form risk (if form is dropping)
        form = float(player_static.get('form', 0))
        points_per_game = float(player_static.get('points_per_game', 0))
        if form > 0 and points_per_game > 0:
            if form < points_per_game * 0.5:  # Form much lower than average
                risk_score += 0.5
            elif form > points_per_game * 1.5:  # Form much higher than average (lower risk)
                risk_score -= 0.5
        
        # Minutes risk
        minutes = player_live.get('stats', {}).get('minutes', 0)
        if minutes < 30:  # Rotation risk
            risk_score += 0.5
        elif minutes >= 90:  # Nailed on
            risk_score -= 0.5
        
        # Team strength (simplified - in reality would check upcoming fixtures)
        team_strength = team.get('strength', 3)
        if team_strength <= 2:  # Weaker team
            risk_score += 0.5
        elif team_strength >= 4:  # Stronger team
            risk_score -= 0.5
        
        # Ensure score is within bounds
        return max(1.0, min(5.0, risk_score))
    
    def _calculate_reward_score(
        self, 
        player_static: Dict[str, Any], 
        player_live: Dict[str, Any]
    ) -> float:
        """
        Calculate reward potential score (1-5, higher is better).
        
        Factors:
        - Position (attackers have higher ceiling)
        - Recent form trajectory
        - Underlying stats (xG, xA, threat)
        - Historical explosive performances
        """
        position_type = player_static.get('element_type', 0)
        
        # Base score by position
        position_base = {
            1: 2.0,  # GKP - limited ceiling
            2: 2.5,  # DEF - moderate ceiling
            3: 3.5,  # MID - high ceiling
            4: 4.0   # FWD - highest ceiling
        }
        reward_score = position_base.get(position_type, 2.5)
        
        # Form bonus
        form = float(player_static.get('form', 0))
        if form > 7.0:
            reward_score += 0.5
        elif form > 5.0:
            reward_score += 0.25
        
        # Underlying stats bonus for attackers
        if position_type in [3, 4]:  # MID or FWD
            xG = float(player_static.get('expected_goals', 0))
            xA = float(player_static.get('expected_assists', 0))
            threat = float(player_static.get('threat', 0))
            
            # Combined attacking threat
            attacking_threat = xG + (xA * 0.7) + (threat / 100)
            if attacking_threat > 15:
                reward_score += 0.5
            elif attacking_threat > 10:
                reward_score += 0.25
        
        # Penalty taker bonus
        if player_static.get('penalties_order', 0) == 1:
            reward_score += 0.25
        
        # Set piece taker bonus
        if player_static.get('corners_and_indirect_freekicks_order', 0) == 1:
            reward_score += 0.15
        
        # Historical max score bonus (explosive potential)
        # This would ideally come from historical data
        # For now, use a simple heuristic based on total points
        total_points = player_static.get('total_points', 0)
        event_points = player_static.get('event_points', 0)
        if total_points > 0 and event_points > 15:  # Had a huge haul recently
            reward_score += 0.25
        
        # Ensure score is within bounds
        return max(1.0, min(5.0, reward_score))
    
    def _calculate_strategic_value(
        self,
        psc: float,
        risk_score: float,
        reward_score: float,
        player_static: Dict[str, Any]
    ) -> float:
        """
        Calculate overall strategic value of a differential.
        
        Combines PSC, risk, reward, and other factors into a single score.
        """
        # Normalize risk score (invert so higher is better)
        normalized_risk = (6 - risk_score) / 4  # Converts 1-5 to 1.25-0.25
        
        # Normalize reward score
        normalized_reward = reward_score / 5  # Converts 1-5 to 0.2-1.0
        
        # Price value factor
        price = player_static.get('now_cost', 0) / 10
        value_per_million = player_static.get('value_season', 0)
        price_factor = 1.0
        if value_per_million > 0:
            if value_per_million > 7.0:  # Great value
                price_factor = 1.2
            elif value_per_million > 5.0:  # Good value
                price_factor = 1.1
            elif value_per_million < 3.0:  # Poor value
                price_factor = 0.9
        
        # Calculate strategic value
        # PSC is most important, then reward potential, then risk mitigation
        strategic_value = (
            psc * 0.5 +  # 50% weight on actual point swing
            (psc * normalized_reward) * 0.3 +  # 30% weight on reward-adjusted PSC
            (psc * normalized_risk) * 0.15 +  # 15% weight on risk-adjusted PSC
            (psc * price_factor) * 0.05  # 5% weight on value
        )
        
        return round(strategic_value, 2)
    
    async def _analyze_captaincy(
        self,
        m1_picks: Dict[int, Dict[str, Any]],
        m2_picks: Dict[int, Dict[str, Any]],
        players_dict: Dict[int, Dict[str, Any]],
        live_elements: Dict[int, Dict[str, Any]],
        m1_picks_data: Dict[str, Any],
        m2_picks_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze captain choices and their impact."""
        m1_captain_id = None
        m2_captain_id = None
        
        # Find captains
        for player_id, pick in m1_picks.items():
            if pick.get('is_captain'):
                m1_captain_id = player_id
                break
        
        for player_id, pick in m2_picks.items():
            if pick.get('is_captain'):
                m2_captain_id = player_id
                break
        
        if not m1_captain_id or not m2_captain_id:
            return {"error": "Could not identify captains"}
        
        # Get captain details
        m1_captain_static = players_dict.get(m1_captain_id, {})
        m2_captain_static = players_dict.get(m2_captain_id, {})
        m1_captain_live = live_elements.get(m1_captain_id, {})
        m2_captain_live = live_elements.get(m2_captain_id, {})
        
        m1_captain_points = m1_captain_live.get('stats', {}).get('total_points', 0)
        m2_captain_points = m2_captain_live.get('stats', {}).get('total_points', 0)
        
        # Apply triple captain if active
        if m1_picks_data.get('active_chip') == '3xc':
            m1_captain_multiplier = 3
        else:
            m1_captain_multiplier = 2
        
        if m2_picks_data.get('active_chip') == '3xc':
            m2_captain_multiplier = 3
        else:
            m2_captain_multiplier = 2
        
        # Calculate captain swings
        # Swing is the advantage gained from captain choice
        # If same captain, no swing unless different multipliers
        if m1_captain_id == m2_captain_id:
            # Same captain - swing comes from multiplier difference
            m1_swing = m1_captain_points * (m1_captain_multiplier - m2_captain_multiplier)
            m2_swing = -m1_swing
        else:
            # Different captains
            # M1's swing: points from their captain minus what M2 would get if they had M1's captain
            m1_owned_by_m2 = m1_captain_id in m2_picks
            m2_owned_by_m1 = m2_captain_id in m1_picks
            
            if m1_owned_by_m2:
                # M2 owns M1's captain but didn't captain them
                m1_swing = m1_captain_points * (m1_captain_multiplier - 1)
            else:
                # M2 doesn't own M1's captain at all
                m1_swing = m1_captain_points * m1_captain_multiplier
            
            if m2_owned_by_m1:
                # M1 owns M2's captain but didn't captain them
                m2_swing = m2_captain_points * (m2_captain_multiplier - 1)
            else:
                # M1 doesn't own M2's captain at all
                m2_swing = m2_captain_points * m2_captain_multiplier
        
        return {
            "manager1_captain": {
                "player_id": m1_captain_id,
                "name": m1_captain_static.get('web_name', 'Unknown'),
                "points": m1_captain_points,
                "multiplier": m1_captain_multiplier,
                "total_points": m1_captain_points * m1_captain_multiplier
            },
            "manager2_captain": {
                "player_id": m2_captain_id,
                "name": m2_captain_static.get('web_name', 'Unknown'),
                "points": m2_captain_points,
                "multiplier": m2_captain_multiplier,
                "total_points": m2_captain_points * m2_captain_multiplier
            },
            "same_captain": m1_captain_id == m2_captain_id,
            "captain_swing_potential_m1": m1_swing,
            "captain_swing_potential_m2": m2_swing,
            "net_captain_advantage": m1_swing - m2_swing
        }