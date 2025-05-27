from typing import Dict, List, Optional, Any, Tuple
import logging
import numpy as np
from scipy import stats
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PredictiveEngine:
    """
    ML-based prediction service for FPL H2H match outcomes.
    Uses statistical models to predict expected points, win probabilities,
    and identify decisive players.
    """
    
    def __init__(self):
        """
        Initialize the Predictive Engine.
        
        Note: Can accept LiveDataService for additional historical data,
        but we prioritize using data passed directly to methods.
        """
        logger.info("PredictiveEngine initialized")
        
        # Model parameters
        self.form_weight = 0.35  # Weight given to recent form vs season average
        self.home_advantage_factor = 1.05  # 5% boost for home fixtures
        self.fixture_difficulty_impact = {
            1: 1.25,  # Very easy - 25% boost
            2: 1.10,  # Easy - 10% boost
            3: 1.00,  # Average - no change
            4: 0.85,  # Hard - 15% reduction
            5: 0.70   # Very hard - 30% reduction
        }
        
        # Position-based point volatility (std dev multipliers)
        self.position_volatility = {
            1: 0.8,   # GKP - lower volatility
            2: 1.0,   # DEF - medium volatility
            3: 1.2,   # MID - higher volatility
            4: 1.4    # FWD - highest volatility
        }
    
    async def _get_player_historical_performance(
        self,
        player_id: int,
        player_static: Dict[str, Any],
        num_gameweeks: int = 5,
        current_gameweek: int = 38
    ) -> Dict[str, Any]:
        """
        Calculate player's historical performance metrics.
        
        Args:
            player_id: Player ID
            player_static: Player data from bootstrap
            num_gameweeks: Number of recent gameweeks to consider
            current_gameweek: Current gameweek number
            
        Returns:
            Dict with performance metrics
        """
        # Extract key metrics from static data
        total_points = float(player_static.get('total_points', 0))
        games_played = max(1, player_static.get('minutes', 0) // 60)  # Rough estimate
        points_per_game = float(player_static.get('points_per_game', 0))
        
        # Form is average over recent games
        form = float(player_static.get('form', 0))
        
        # Calculate volatility based on position and historical variance
        position_type = player_static.get('element_type', 3)
        base_volatility = self.position_volatility.get(position_type, 1.0)
        
        # Estimate standard deviation (simplified)
        # In reality, would calculate from detailed historical data
        if points_per_game > 0:
            # Higher scoring players tend to have higher variance
            estimated_std_dev = max(1.5, points_per_game * 0.4 * base_volatility)
        else:
            estimated_std_dev = 2.0 * base_volatility
        
        # Additional performance indicators
        selected_by_percent = float(player_static.get('selected_by_percent', 0))
        value_season = float(player_static.get('value_season', 0))
        
        return {
            "avg_points": points_per_game,
            "form_points": form,
            "std_dev": estimated_std_dev,
            "total_points": total_points,
            "games_played": games_played,
            "ownership": selected_by_percent,
            "value_per_million": value_season,
            "is_consistent": estimated_std_dev < points_per_game * 0.3 if points_per_game > 0 else False
        }
    
    async def predict_player_expected_points(
        self,
        player_id: int,
        player_fixture_difficulty: float,
        player_team_strength: float,
        opponent_team_strength: float,
        bootstrap_static_data: Dict[str, Any],
        current_gameweek: int,
        is_home: bool = True
    ) -> float:
        """
        Predict expected points for a player in a specific fixture.
        
        Args:
            player_id: Player ID
            player_fixture_difficulty: Fixture difficulty (1-5)
            player_team_strength: Player's team strength
            opponent_team_strength: Opponent team strength
            bootstrap_static_data: Bootstrap data
            current_gameweek: Current gameweek
            is_home: Whether playing at home
            
        Returns:
            Expected points for the player
        """
        # Get player data
        players = {p['id']: p for p in bootstrap_static_data.get('elements', [])}
        player_static = players.get(player_id)
        
        if not player_static:
            logger.warning(f"Player {player_id} not found in bootstrap data")
            return 0.0
        
        # Get historical performance
        hist_perf = await self._get_player_historical_performance(
            player_id, player_static, current_gameweek=current_gameweek
        )
        
        # Base expected points - weighted average of form and season average
        if hist_perf['form_points'] > 0:
            base_xp = (
                hist_perf['form_points'] * self.form_weight +
                hist_perf['avg_points'] * (1 - self.form_weight)
            )
        else:
            base_xp = hist_perf['avg_points']
        
        # Apply fixture difficulty adjustment
        difficulty_factor = self.fixture_difficulty_impact.get(
            int(player_fixture_difficulty), 1.0
        )
        
        # Apply team strength differential
        if opponent_team_strength > 0:
            strength_ratio = player_team_strength / opponent_team_strength
            strength_factor = min(1.3, max(0.7, strength_ratio))  # Cap between 0.7 and 1.3
        else:
            strength_factor = 1.0
        
        # Apply home advantage
        home_factor = self.home_advantage_factor if is_home else 1.0
        
        # Calculate final expected points
        expected_points = base_xp * difficulty_factor * strength_factor * home_factor
        
        # Additional adjustments for special cases
        
        # Penalty takers get a small boost
        if player_static.get('penalties_order', 0) == 1:
            expected_points *= 1.05
        
        # Players on good form get extra boost
        if hist_perf['form_points'] > hist_perf['avg_points'] * 1.5:
            expected_points *= 1.1
        
        # Injury doubt penalty
        chance_of_playing = player_static.get('chance_of_playing_next_round')
        if chance_of_playing is not None and chance_of_playing < 100:
            expected_points *= (chance_of_playing / 100)
        
        return max(0, round(expected_points, 2))
    
    async def predict_team_expected_points(
        self,
        manager_picks_data: Dict[str, Any],
        fixture_difficulties: Dict[int, float],
        team_strengths: Dict[int, float],
        bootstrap_static_data: Dict[str, Any],
        current_gameweek: int
    ) -> Tuple[float, float]:
        """
        Predict total expected points for a manager's team.
        
        Args:
            manager_picks_data: Manager's picks
            fixture_difficulties: Dict mapping team_id to difficulty
            team_strengths: Dict mapping team_id to strength
            bootstrap_static_data: Bootstrap data
            current_gameweek: Current gameweek
            
        Returns:
            Tuple of (total_expected_points, uncertainty_metric)
        """
        if not manager_picks_data or 'picks' not in manager_picks_data:
            return 0.0, 0.0
        
        # Get player and fixture data
        players = {p['id']: p for p in bootstrap_static_data.get('elements', [])}
        teams = {t['id']: t for t in bootstrap_static_data.get('teams', [])}
        
        total_xp = 0.0
        total_variance = 0.0
        active_chip = manager_picks_data.get('active_chip')
        
        # Process each player in starting XI
        for pick in manager_picks_data.get('picks', []):
            if pick['position'] > 11 and active_chip != 'bboost':
                continue  # Skip bench unless bench boost
                
            player_id = pick['element']
            player_static = players.get(player_id)
            
            if not player_static:
                continue
            
            # Get team and fixture info
            team_id = player_static.get('team')
            team_info = teams.get(team_id, {})
            
            # Determine fixture difficulty and opponent
            fixture_diff = fixture_difficulties.get(team_id, 3)  # Default to average
            team_strength = team_strengths.get(team_id, 3)
            
            # For simplicity, assume average opponent strength
            # In reality, would look up specific opponent
            opponent_strength = 3.0
            
            # Predict expected points
            player_xp = await self.predict_player_expected_points(
                player_id=player_id,
                player_fixture_difficulty=fixture_diff,
                player_team_strength=team_strength,
                opponent_team_strength=opponent_strength,
                bootstrap_static_data=bootstrap_static_data,
                current_gameweek=current_gameweek
            )
            
            # Apply captaincy multiplier
            if pick.get('is_captain'):
                if active_chip == '3xc':
                    player_xp *= 3
                else:
                    player_xp *= 2
            
            total_xp += player_xp
            
            # Accumulate variance (simplified)
            hist_perf = await self._get_player_historical_performance(
                player_id, player_static, current_gameweek=current_gameweek
            )
            player_variance = hist_perf['std_dev'] ** 2
            
            if pick.get('is_captain'):
                multiplier = 3 if active_chip == '3xc' else 2
                player_variance *= multiplier ** 2
            
            total_variance += player_variance
        
        # Calculate total standard deviation
        total_std_dev = np.sqrt(total_variance)
        
        return total_xp, total_std_dev
    
    async def predict_match_outcome(
        self,
        manager1_id: int,
        manager2_id: int,
        manager1_history: Dict[str, Any],
        manager2_history: Dict[str, Any],
        current_gw_picks_m1: Dict[str, Any],
        current_gw_picks_m2: Dict[str, Any],
        fixture_data: List[Dict[str, Any]],
        gameweek: int
    ) -> Dict[str, Any]:
        """
        Predict H2H match outcome with probabilities and confidence intervals.
        
        Args:
            manager1_id: First manager ID
            manager2_id: Second manager ID
            manager1_history: Manager 1's historical data
            manager2_history: Manager 2's historical data
            current_gw_picks_m1: Manager 1's current picks
            current_gw_picks_m2: Manager 2's current picks
            fixture_data: Current gameweek fixtures
            gameweek: Current gameweek number
            
        Returns:
            Dict with match predictions
        """
        logger.info(f"Predicting match outcome for managers {manager1_id} vs {manager2_id}, GW{gameweek}")
        
        # Prepare fixture difficulties and team strengths
        # This is simplified - in reality would parse fixture_data properly
        fixture_difficulties = self._calculate_fixture_difficulties(fixture_data)
        team_strengths = self._calculate_team_strengths(fixture_data)
        
        # Get bootstrap data (would normally be passed in)
        # For now, using empty dict as fallback
        bootstrap_data = {}
        
        # Predict expected points for both teams
        m1_xp, m1_std = await self.predict_team_expected_points(
            current_gw_picks_m1, fixture_difficulties, team_strengths,
            bootstrap_data, gameweek
        )
        
        m2_xp, m2_std = await self.predict_team_expected_points(
            current_gw_picks_m2, fixture_difficulties, team_strengths,
            bootstrap_data, gameweek
        )
        
        # Calculate win probabilities using normal distribution
        score_diff_mean = m1_xp - m2_xp
        score_diff_std = np.sqrt(m1_std**2 + m2_std**2)
        
        if score_diff_std > 0:
            # Create normal distribution for score difference
            diff_distribution = stats.norm(loc=score_diff_mean, scale=score_diff_std)
            
            # Calculate probabilities
            # Win if score difference > 0.5 (to account for rounding)
            prob_m1_wins = 1 - diff_distribution.cdf(0.5)
            # Lose if score difference < -0.5
            prob_m2_wins = diff_distribution.cdf(-0.5)
            # Draw otherwise
            prob_draw = 1 - prob_m1_wins - prob_m2_wins
        else:
            # No variance, deterministic outcome
            if score_diff_mean > 0.5:
                prob_m1_wins, prob_draw, prob_m2_wins = 1.0, 0.0, 0.0
            elif score_diff_mean < -0.5:
                prob_m1_wins, prob_draw, prob_m2_wins = 0.0, 0.0, 1.0
            else:
                prob_m1_wins, prob_draw, prob_m2_wins = 0.0, 1.0, 0.0
        
        # Calculate confidence intervals
        z_95 = 1.96  # 95% confidence interval
        margin_ci_lower = score_diff_mean - z_95 * score_diff_std
        margin_ci_upper = score_diff_mean + z_95 * score_diff_std
        
        # Identify decisive players
        decisive_m1 = await self._identify_decisive_players(
            current_gw_picks_m1, bootstrap_data, gameweek
        )
        decisive_m2 = await self._identify_decisive_players(
            current_gw_picks_m2, bootstrap_data, gameweek
        )
        
        # Determine predicted winner and confidence
        if prob_m1_wins > prob_m2_wins + prob_draw:
            predicted_winner = manager1_id
            win_probability = prob_m1_wins
        elif prob_m2_wins > prob_m1_wins + prob_draw:
            predicted_winner = manager2_id
            win_probability = prob_m2_wins
        else:
            predicted_winner = None  # Draw most likely
            win_probability = prob_draw
        
        # Calculate confidence level
        confidence = self._calculate_confidence_level(
            win_probability, score_diff_std, m1_xp, m2_xp
        )
        
        # Key factors for the prediction
        key_factors = self._identify_key_factors(
            m1_xp, m2_xp, m1_std, m2_std,
            decisive_m1, decisive_m2, 
            current_gw_picks_m1, current_gw_picks_m2
        )
        
        return {
            "predicted_winner": predicted_winner,
            "win_probability": round(win_probability, 3),
            "manager1_win_probability": round(prob_m1_wins, 3),
            "manager2_win_probability": round(prob_m2_wins, 3),
            "draw_probability": round(prob_draw, 3),
            "manager1_expected_points": round(m1_xp, 1),
            "manager2_expected_points": round(m2_xp, 1),
            "predicted_margin": round(score_diff_mean, 1),
            "margin_confidence_interval_95": [
                round(margin_ci_lower, 1),
                round(margin_ci_upper, 1)
            ],
            "decisive_players_m1": decisive_m1[:3],
            "decisive_players_m2": decisive_m2[:3],
            "confidence": confidence,
            "key_factors": key_factors[:3]
        }
    
    def _calculate_fixture_difficulties(
        self,
        fixture_data: List[Dict[str, Any]]
    ) -> Dict[int, float]:
        """Calculate fixture difficulties for each team."""
        # Simplified implementation
        # In reality, would parse fixture_data and calculate based on opponent strength
        difficulties = {}
        
        # Default all teams to average difficulty
        for i in range(1, 21):  # 20 teams
            difficulties[i] = 3.0
        
        return difficulties
    
    def _calculate_team_strengths(
        self,
        fixture_data: List[Dict[str, Any]]
    ) -> Dict[int, float]:
        """Calculate team strengths."""
        # Simplified implementation
        # In reality, would use league position, recent form, etc.
        strengths = {}
        
        # Default all teams to average strength
        for i in range(1, 21):  # 20 teams
            strengths[i] = 3.0
        
        # Top teams get higher strength
        top_teams = [1, 2, 3, 11, 12, 13]  # Example team IDs
        for team_id in top_teams:
            strengths[team_id] = 4.0
        
        return strengths
    
    async def _identify_decisive_players(
        self,
        picks_data: Dict[str, Any],
        bootstrap_data: Dict[str, Any],
        gameweek: int
    ) -> List[Dict[str, Any]]:
        """Identify potentially decisive players based on expected points and volatility."""
        if not picks_data or 'picks' not in picks_data:
            return []
        
        decisive_players = []
        players = {p['id']: p for p in bootstrap_data.get('elements', [])}
        
        for pick in picks_data.get('picks', []):
            if pick['position'] > 11:  # Skip bench
                continue
                
            player_id = pick['element']
            player_static = players.get(player_id, {})
            
            if not player_static:
                continue
            
            # Simple heuristic for potential swing factor
            form = float(player_static.get('form', 0))
            is_captain = pick.get('is_captain', False)
            position_type = player_static.get('element_type', 3)
            
            # Higher swing potential for:
            # - Captains
            # - High form players
            # - Attacking players
            swing_factor = form
            if is_captain:
                swing_factor *= 2.5
            if position_type in [3, 4]:  # MID or FWD
                swing_factor *= 1.2
            
            decisive_players.append({
                "player_id": player_id,
                "name": player_static.get('web_name', 'Unknown'),
                "expected_points": form,
                "potential_swing_factor": round(swing_factor, 1),
                "is_captain": is_captain,
                "position": position_type
            })
        
        # Sort by swing factor
        decisive_players.sort(key=lambda x: x['potential_swing_factor'], reverse=True)
        
        return decisive_players
    
    def _calculate_confidence_level(
        self,
        win_probability: float,
        score_diff_std: float,
        m1_xp: float,
        m2_xp: float
    ) -> float:
        """Calculate overall confidence level in the prediction."""
        # Base confidence on win probability
        if win_probability > 0.8:
            base_confidence = 0.9
        elif win_probability > 0.65:
            base_confidence = 0.75
        elif win_probability > 0.5:
            base_confidence = 0.6
        else:
            base_confidence = 0.4
        
        # Adjust for uncertainty (high std dev = lower confidence)
        avg_xp = (m1_xp + m2_xp) / 2
        if avg_xp > 0:
            uncertainty_ratio = score_diff_std / avg_xp
            if uncertainty_ratio > 0.5:
                base_confidence *= 0.8
            elif uncertainty_ratio > 0.3:
                base_confidence *= 0.9
        
        return round(base_confidence, 2)
    
    def _identify_key_factors(
        self,
        m1_xp: float,
        m2_xp: float,
        m1_std: float,
        m2_std: float,
        decisive_m1: List[Dict[str, Any]],
        decisive_m2: List[Dict[str, Any]],
        picks_m1: Dict[str, Any],
        picks_m2: Dict[str, Any]
    ) -> List[str]:
        """Identify key factors influencing the prediction."""
        factors = []
        
        # Factor 1: Expected points difference
        xp_diff = abs(m1_xp - m2_xp)
        if xp_diff > 15:
            factors.append(f"Large expected points gap of {xp_diff:.1f} points")
        elif xp_diff < 5:
            factors.append("Very close expected points - could go either way")
        
        # Factor 2: Captain differential
        if decisive_m1 and decisive_m2:
            m1_cap = next((p for p in decisive_m1 if p.get('is_captain')), None)
            m2_cap = next((p for p in decisive_m2 if p.get('is_captain')), None)
            
            if m1_cap and m2_cap and m1_cap['player_id'] != m2_cap['player_id']:
                factors.append(f"Captain differential: {m1_cap['name']} vs {m2_cap['name']}")
        
        # Factor 3: Volatility difference
        if m1_std > m2_std * 1.5:
            factors.append("Manager 1's team has higher volatility - more unpredictable")
        elif m2_std > m1_std * 1.5:
            factors.append("Manager 2's team has higher volatility - more unpredictable")
        
        # Factor 4: Chip usage
        m1_chip = picks_m1.get('active_chip')
        m2_chip = picks_m2.get('active_chip')
        if m1_chip and not m2_chip:
            factors.append(f"Manager 1 using {m1_chip} chip")
        elif m2_chip and not m1_chip:
            factors.append(f"Manager 2 using {m2_chip} chip")
        elif m1_chip and m2_chip:
            factors.append(f"Both managers using chips: {m1_chip} vs {m2_chip}")
        
        # Factor 5: High impact players
        if decisive_m1:
            top_player = decisive_m1[0]
            if top_player['potential_swing_factor'] > 10:
                factors.append(f"{top_player['name']} could be decisive for Manager 1")
        
        return factors