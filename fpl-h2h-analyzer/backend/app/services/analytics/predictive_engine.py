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
        gameweek: int,
        bootstrap_data: Optional[Dict[str, Any]] = None
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
            bootstrap_data: Bootstrap static data (optional but recommended)
            
        Returns:
            Dict with match predictions
        """
        logger.info(f"Predicting match outcome for managers {manager1_id} vs {manager2_id}, GW{gameweek}")
        
        # Analyze historical performance patterns
        m1_form_metrics = self._analyze_manager_form(manager1_history, gameweek)
        m2_form_metrics = self._analyze_manager_form(manager2_history, gameweek)
        
        # Calculate H2H historical record
        h2h_record = self._calculate_h2h_record(manager1_history, manager2_history, manager1_id, manager2_id)
        
        # Analyze current team strength
        m1_team_strength = await self._analyze_current_team_strength(current_gw_picks_m1, bootstrap_data, fixture_data)
        m2_team_strength = await self._analyze_current_team_strength(current_gw_picks_m2, bootstrap_data, fixture_data)
        
        # Calculate expected points using improved algorithm
        m1_xp, m1_std = await self._predict_enhanced_team_points(
            current_gw_picks_m1, m1_form_metrics, m1_team_strength, bootstrap_data, fixture_data, gameweek
        )
        
        m2_xp, m2_std = await self._predict_enhanced_team_points(
            current_gw_picks_m2, m2_form_metrics, m2_team_strength, bootstrap_data, fixture_data, gameweek
        )
        
        # Apply H2H psychological factors
        m1_xp_adjusted, m2_xp_adjusted = self._apply_psychological_edge(
            m1_xp, m2_xp, h2h_record, m1_form_metrics, m2_form_metrics
        )
        
        # Calculate win probabilities using enhanced model
        prob_m1_wins, prob_m2_wins, prob_draw = self._calculate_win_probabilities(
            m1_xp_adjusted, m2_xp_adjusted, m1_std, m2_std, h2h_record
        )
        
        # Calculate confidence based on multiple factors
        confidence = self._calculate_enhanced_confidence(
            prob_m1_wins, prob_m2_wins, prob_draw, m1_std, m2_std, 
            m1_form_metrics, m2_form_metrics, h2h_record
        )
        
        # Generate score predictions with ranges
        m1_score_range = self._generate_score_prediction_range(m1_xp_adjusted, m1_std)
        m2_score_range = self._generate_score_prediction_range(m2_xp_adjusted, m2_std)
        
        # Identify decisive players
        decisive_m1 = await self._identify_decisive_players(
            current_gw_picks_m1, bootstrap_data, gameweek
        )
        decisive_m2 = await self._identify_decisive_players(
            current_gw_picks_m2, bootstrap_data, gameweek
        )
        
        # Determine predicted winner
        if prob_m1_wins > max(prob_m2_wins, prob_draw):
            predicted_winner = manager1_id
            win_probability = prob_m1_wins
        elif prob_m2_wins > max(prob_m1_wins, prob_draw):
            predicted_winner = manager2_id
            win_probability = prob_m2_wins
        else:
            predicted_winner = None  # Draw most likely
            win_probability = prob_draw
        
        # Generate AI insights
        ai_insights = self._generate_ai_insights(
            m1_form_metrics, m2_form_metrics, h2h_record, 
            decisive_m1, decisive_m2, current_gw_picks_m1, current_gw_picks_m2
        )
        
        # Key factors for the prediction
        key_factors = self._identify_enhanced_key_factors(
            m1_xp_adjusted, m2_xp_adjusted, m1_std, m2_std,
            decisive_m1, decisive_m2, current_gw_picks_m1, current_gw_picks_m2,
            h2h_record, m1_form_metrics, m2_form_metrics
        )
        
        return {
            "predicted_winner": predicted_winner,
            "win_probability": round(win_probability, 3),
            "manager1_win_probability": round(prob_m1_wins, 3),
            "manager2_win_probability": round(prob_m2_wins, 3),
            "draw_probability": round(prob_draw, 3),
            "manager1_expected_points": round(m1_xp_adjusted, 1),
            "manager2_expected_points": round(m2_xp_adjusted, 1),
            "manager1_score_range": m1_score_range,
            "manager2_score_range": m2_score_range,
            "predicted_margin": round(m1_xp_adjusted - m2_xp_adjusted, 1),
            "margin_confidence_interval_95": [
                round((m1_xp_adjusted - m2_xp_adjusted) - 1.96 * np.sqrt(m1_std**2 + m2_std**2), 1),
                round((m1_xp_adjusted - m2_xp_adjusted) + 1.96 * np.sqrt(m1_std**2 + m2_std**2), 1)
            ],
            "decisive_players_m1": decisive_m1[:3],
            "decisive_players_m2": decisive_m2[:3],
            "confidence": confidence,
            "confidence_breakdown": self._get_confidence_breakdown(
                m1_form_metrics, m2_form_metrics, h2h_record, confidence
            ),
            "psychological_edge": self._calculate_psychological_edge_details(
                h2h_record, m1_form_metrics, m2_form_metrics
            ),
            "key_factors": key_factors[:3],
            "ai_insights": ai_insights
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
    
    def _analyze_manager_form(self, manager_history: Dict[str, Any], current_gw: int) -> Dict[str, Any]:
        """Analyze manager's recent form and patterns."""
        if not manager_history or 'current' not in manager_history:
            return {
                "form_score": 50,
                "recent_trend": "neutral",
                "consistency": 0.5,
                "last_5_average": 50,
                "winning_streak": 0,
                "comeback_ability": 0.5
            }
        
        # Get recent gameweek data
        current_data = manager_history['current']
        total_points = current_data.get('total_points', 0)
        overall_rank = current_data.get('overall_rank', 500000)
        
        # Calculate form score based on rank and points
        if overall_rank <= 10000:
            form_score = 85 + min(15, (10000 - overall_rank) / 1000)
        elif overall_rank <= 100000:
            form_score = 70 + (100000 - overall_rank) / 6000
        elif overall_rank <= 500000:
            form_score = 50 + (500000 - overall_rank) / 26667
        else:
            form_score = max(20, 50 - (overall_rank - 500000) / 50000)
        
        # Analyze recent performance trend
        gameweek_history = manager_history.get('history', [])
        if len(gameweek_history) >= 5:
            recent_points = [gw.get('points', 0) for gw in gameweek_history[-5:]]
            last_5_average = sum(recent_points) / len(recent_points)
            
            # Calculate trend
            if len(recent_points) >= 3:
                early_avg = sum(recent_points[:2]) / 2
                late_avg = sum(recent_points[-2:]) / 2
                if late_avg > early_avg + 5:
                    recent_trend = "improving"
                elif late_avg < early_avg - 5:
                    recent_trend = "declining"
                else:
                    recent_trend = "stable"
            else:
                recent_trend = "neutral"
            
            # Calculate consistency (inverse of standard deviation)
            if len(recent_points) > 1:
                std_dev = np.std(recent_points)
                consistency = max(0.1, min(1.0, 1 - (std_dev / 30)))
            else:
                consistency = 0.5
        else:
            last_5_average = 50
            recent_trend = "neutral"
            consistency = 0.5
        
        return {
            "form_score": round(form_score, 1),
            "recent_trend": recent_trend,
            "consistency": round(consistency, 2),
            "last_5_average": round(last_5_average, 1),
            "winning_streak": 0,  # Would need H2H data
            "comeback_ability": round(consistency * 0.8 + 0.2, 2)
        }
    
    def _calculate_h2h_record(self, m1_history: Dict, m2_history: Dict, m1_id: int, m2_id: int) -> Dict[str, Any]:
        """Calculate head-to-head historical record."""
        # This would normally analyze actual H2H match history
        # For now, using simplified approach based on form differential
        
        m1_form = self._analyze_manager_form(m1_history, 38)
        m2_form = self._analyze_manager_form(m2_history, 38)
        
        form_diff = m1_form["form_score"] - m2_form["form_score"]
        
        # Simulate H2H record based on form differential
        if abs(form_diff) < 5:
            # Very even matchup
            wins_m1, wins_m2, draws = 3, 3, 2
            dominance = "even"
        elif form_diff > 15:
            # Manager 1 much stronger
            wins_m1, wins_m2, draws = 6, 1, 1
            dominance = "manager1"
        elif form_diff < -15:
            # Manager 2 much stronger
            wins_m1, wins_m2, draws = 1, 6, 1
            dominance = "manager2"
        elif form_diff > 5:
            # Manager 1 slightly stronger
            wins_m1, wins_m2, draws = 4, 2, 2
            dominance = "slight_manager1"
        else:
            # Manager 2 slightly stronger
            wins_m1, wins_m2, draws = 2, 4, 2
            dominance = "slight_manager2"
        
        total_matches = wins_m1 + wins_m2 + draws
        
        return {
            "total_matches": total_matches,
            "manager1_wins": wins_m1,
            "manager2_wins": wins_m2,
            "draws": draws,
            "manager1_win_rate": round(wins_m1 / total_matches if total_matches > 0 else 0.5, 3),
            "manager2_win_rate": round(wins_m2 / total_matches if total_matches > 0 else 0.5, 3),
            "dominance": dominance,
            "recent_momentum": "neutral"
        }
    
    async def _analyze_current_team_strength(self, picks_data: Dict, bootstrap_data: Dict, fixtures: List) -> Dict[str, Any]:
        """Analyze current team strength using ICT and form data."""
        if not picks_data or 'picks' not in picks_data:
            return {"total_ict": 300, "avg_form": 3.0, "captain_strength": 3.0, "team_value": 100.0}
        
        if not bootstrap_data or 'elements' not in bootstrap_data:
            # Fallback calculation without bootstrap data
            return {
                "total_ict": 320 + len(picks_data['picks'][:11]) * 15,  # Rough estimate
                "avg_form": 3.5,
                "captain_strength": 4.0,
                "team_value": 100.0
            }
        
        players = {p['id']: p for p in bootstrap_data['elements']}
        
        total_ict = 0
        total_form = 0
        total_value = 0
        captain_strength = 0
        player_count = 0
        
        for pick in picks_data['picks'][:11]:  # Starting XI only
            player_id = pick['element']
            player = players.get(player_id, {})
            
            if player:
                ict = float(player.get('ict_index', 0))
                form = float(player.get('form', 0))
                value = float(player.get('now_cost', 0)) / 10
                
                total_ict += ict
                total_form += form
                total_value += value
                player_count += 1
                
                if pick.get('is_captain'):
                    captain_strength = ict / 10 if ict > 0 else 3.0
        
        if player_count == 0:
            return {"total_ict": 300, "avg_form": 3.0, "captain_strength": 3.0, "team_value": 100.0}
        
        return {
            "total_ict": round(total_ict, 1),
            "avg_form": round(total_form / player_count, 2),
            "captain_strength": round(captain_strength, 2),
            "team_value": round(total_value, 1)
        }
    
    async def _predict_enhanced_team_points(
        self, picks_data: Dict, form_metrics: Dict, team_strength: Dict, 
        bootstrap_data: Dict, fixtures: List, gameweek: int
    ) -> Tuple[float, float]:
        """Enhanced team points prediction using multiple factors."""
        
        if not picks_data or 'picks' not in picks_data:
            return 45.0, 12.0  # Default values
        
        # Base prediction using team strength
        base_points = (team_strength["total_ict"] / 10) + (form_metrics["form_score"] / 2)
        
        # Apply form trend adjustments
        if form_metrics["recent_trend"] == "improving":
            base_points *= 1.15
        elif form_metrics["recent_trend"] == "declining":
            base_points *= 0.90
        
        # Apply consistency factor
        variance_factor = 2 - form_metrics["consistency"]  # Higher consistency = lower variance
        
        # Captain bonus
        captain_bonus = team_strength["captain_strength"] * 3
        base_points += captain_bonus
        
        # Chip bonuses
        active_chip = picks_data.get('active_chip')
        if active_chip == 'bboost':
            base_points += 15  # Bench boost average
        elif active_chip == '3xc':
            base_points += captain_bonus  # Extra captain points
        elif active_chip == 'freehit':
            base_points += 8  # Free hit average boost
        
        # Calculate standard deviation based on consistency and volatility
        base_std = 8 + (variance_factor * 4)
        
        return max(20.0, base_points), max(5.0, base_std)
    
    def _apply_psychological_edge(
        self, m1_xp: float, m2_xp: float, h2h_record: Dict, 
        m1_form: Dict, m2_form: Dict
    ) -> Tuple[float, float]:
        """Apply psychological factors to expected points."""
        
        # H2H dominance factor
        if h2h_record["dominance"] == "manager1":
            m1_xp *= 1.08
            m2_xp *= 0.95
        elif h2h_record["dominance"] == "manager2":
            m1_xp *= 0.95
            m2_xp *= 1.08
        elif h2h_record["dominance"] == "slight_manager1":
            m1_xp *= 1.03
            m2_xp *= 0.98
        elif h2h_record["dominance"] == "slight_manager2":
            m1_xp *= 0.98
            m2_xp *= 1.03
        
        # Form momentum factor
        if m1_form["recent_trend"] == "improving" and m2_form["recent_trend"] == "declining":
            m1_xp *= 1.05
            m2_xp *= 0.97
        elif m1_form["recent_trend"] == "declining" and m2_form["recent_trend"] == "improving":
            m1_xp *= 0.97
            m2_xp *= 1.05
        
        return m1_xp, m2_xp
    
    def _calculate_win_probabilities(
        self, m1_xp: float, m2_xp: float, m1_std: float, m2_std: float, h2h_record: Dict
    ) -> Tuple[float, float, float]:
        """Calculate win probabilities using statistical model."""
        
        score_diff_mean = m1_xp - m2_xp
        score_diff_std = np.sqrt(m1_std**2 + m2_std**2)
        
        if score_diff_std > 0:
            # Use normal distribution
            diff_distribution = stats.norm(loc=score_diff_mean, scale=score_diff_std)
            
            # Win/lose/draw thresholds (accounting for integer scores)
            prob_m1_wins = 1 - diff_distribution.cdf(0.5)
            prob_m2_wins = diff_distribution.cdf(-0.5)
            prob_draw = diff_distribution.cdf(0.5) - diff_distribution.cdf(-0.5)
        else:
            # Deterministic case
            if score_diff_mean > 0.5:
                prob_m1_wins, prob_draw, prob_m2_wins = 0.8, 0.1, 0.1
            elif score_diff_mean < -0.5:
                prob_m1_wins, prob_draw, prob_m2_wins = 0.1, 0.1, 0.8
            else:
                prob_m1_wins, prob_draw, prob_m2_wins = 0.35, 0.3, 0.35
        
        # Apply H2H bias (slight adjustment)
        if h2h_record["dominance"] in ["manager1", "slight_manager1"]:
            prob_m1_wins += 0.02
            prob_m2_wins -= 0.02
        elif h2h_record["dominance"] in ["manager2", "slight_manager2"]:
            prob_m1_wins -= 0.02
            prob_m2_wins += 0.02
        
        # Normalize probabilities
        total = prob_m1_wins + prob_m2_wins + prob_draw
        if total > 0:
            prob_m1_wins /= total
            prob_m2_wins /= total
            prob_draw /= total
        
        return prob_m1_wins, prob_m2_wins, prob_draw
    
    def _calculate_enhanced_confidence(
        self, prob_m1: float, prob_m2: float, prob_draw: float,
        m1_std: float, m2_std: float, m1_form: Dict, m2_form: Dict, h2h_record: Dict
    ) -> float:
        """Calculate confidence score (10-95% range)."""
        
        # Base confidence from probability spread
        max_prob = max(prob_m1, prob_m2, prob_draw)
        base_confidence = (max_prob - 0.33) / 0.67  # Scale from even (33%) to certain (100%)
        
        # Adjust for data quality
        form_confidence = (m1_form["consistency"] + m2_form["consistency"]) / 2
        
        # Adjust for prediction uncertainty
        avg_std = (m1_std + m2_std) / 2
        uncertainty_penalty = min(0.3, avg_std / 20)  # Higher std = lower confidence
        
        # H2H history confidence boost
        h2h_confidence_boost = min(0.1, h2h_record["total_matches"] / 50)
        
        # Combine factors
        final_confidence = (
            base_confidence * 0.5 +
            form_confidence * 0.3 +
            (1 - uncertainty_penalty) * 0.2
        ) + h2h_confidence_boost
        
        # Scale to 10-95% range
        scaled_confidence = 10 + (final_confidence * 85)
        
        return round(max(10, min(95, scaled_confidence)), 1)
    
    def _generate_score_prediction_range(self, expected_points: float, std_dev: float) -> Dict[str, float]:
        """Generate score prediction range with confidence intervals."""
        
        # 68% confidence interval (1 std dev)
        low_68 = max(0, expected_points - std_dev)
        high_68 = expected_points + std_dev
        
        # 95% confidence interval (2 std devs)
        low_95 = max(0, expected_points - 2 * std_dev)
        high_95 = expected_points + 2 * std_dev
        
        return {
            "expected": round(expected_points, 1),
            "range_68_low": round(low_68, 1),
            "range_68_high": round(high_68, 1),
            "range_95_low": round(low_95, 1),
            "range_95_high": round(high_95, 1),
            "most_likely_range": f"{round(low_68, 0)}-{round(high_68, 0)}"
        }
    
    def _get_confidence_breakdown(
        self, m1_form: Dict, m2_form: Dict, h2h_record: Dict, total_confidence: float
    ) -> Dict[str, Any]:
        """Provide breakdown of confidence factors."""
        return {
            "total_confidence": total_confidence,
            "factors": {
                "form_data_quality": round((m1_form["consistency"] + m2_form["consistency"]) * 50, 1),
                "historical_record": min(90, h2h_record["total_matches"] * 10),
                "prediction_certainty": round(total_confidence * 0.8, 1),
                "data_completeness": 85  # Assumed good data quality
            }
        }
    
    def _calculate_psychological_edge_details(
        self, h2h_record: Dict, m1_form: Dict, m2_form: Dict
    ) -> Dict[str, Any]:
        """Calculate detailed psychological edge factors."""
        
        psychological_factors = []
        
        # H2H dominance
        if h2h_record["dominance"] == "manager1":
            psychological_factors.append("Manager 1 has strong H2H dominance")
        elif h2h_record["dominance"] == "manager2":
            psychological_factors.append("Manager 2 has strong H2H dominance")
        
        # Form momentum
        if m1_form["recent_trend"] == "improving":
            psychological_factors.append("Manager 1 on an improving trajectory")
        if m2_form["recent_trend"] == "improving":
            psychological_factors.append("Manager 2 on an improving trajectory")
        
        # Consistency edge
        if m1_form["consistency"] > m2_form["consistency"] + 0.2:
            psychological_factors.append("Manager 1 shows greater consistency")
        elif m2_form["consistency"] > m1_form["consistency"] + 0.2:
            psychological_factors.append("Manager 2 shows greater consistency")
        
        return {
            "factors": psychological_factors[:3],
            "dominant_manager": h2h_record.get("dominance", "even"),
            "momentum_advantage": "manager1" if m1_form["recent_trend"] == "improving" else "manager2" if m2_form["recent_trend"] == "improving" else "even"
        }
    
    def _generate_ai_insights(
        self, m1_form: Dict, m2_form: Dict, h2h_record: Dict,
        decisive_m1: List, decisive_m2: List, picks_m1: Dict, picks_m2: Dict
    ) -> List[str]:
        """Generate AI-powered insights based on analysis."""
        insights = []
        
        # Form-based insights
        if m1_form["form_score"] - m2_form["form_score"] > 20:
            insights.append(f"Manager 1's superior form (score: {m1_form['form_score']}) provides significant advantage")
        elif m2_form["form_score"] - m1_form["form_score"] > 20:
            insights.append(f"Manager 2's superior form (score: {m2_form['form_score']}) provides significant advantage")
        
        # Trend insights
        if m1_form["recent_trend"] == "improving" and m2_form["recent_trend"] == "declining":
            insights.append("Momentum heavily favors Manager 1 with improving form vs declining opponent")
        elif m2_form["recent_trend"] == "improving" and m1_form["recent_trend"] == "declining":
            insights.append("Momentum heavily favors Manager 2 with improving form vs declining opponent")
        
        # Consistency insights
        if abs(m1_form["consistency"] - m2_form["consistency"]) > 0.3:
            more_consistent = "Manager 1" if m1_form["consistency"] > m2_form["consistency"] else "Manager 2"
            insights.append(f"{more_consistent} has significantly higher consistency, reducing upset risk")
        
        # Captain differential insights
        if decisive_m1 and decisive_m2:
            m1_captain = next((p for p in decisive_m1 if p.get('is_captain')), None)
            m2_captain = next((p for p in decisive_m2 if p.get('is_captain')), None)
            
            if m1_captain and m2_captain and m1_captain['player_id'] != m2_captain['player_id']:
                insights.append(f"Captain differential between {m1_captain['name']} and {m2_captain['name']} could be decisive")
        
        # Chip strategy insights
        m1_chip = picks_m1.get('active_chip')
        m2_chip = picks_m2.get('active_chip')
        
        if m1_chip and not m2_chip:
            chip_names = {'bboost': 'Bench Boost', '3xc': 'Triple Captain', 'freehit': 'Free Hit', 'wildcard': 'Wildcard'}
            insights.append(f"Manager 1's {chip_names.get(m1_chip, m1_chip)} chip usage provides tactical advantage")
        elif m2_chip and not m1_chip:
            chip_names = {'bboost': 'Bench Boost', '3xc': 'Triple Captain', 'freehit': 'Free Hit', 'wildcard': 'Wildcard'}
            insights.append(f"Manager 2's {chip_names.get(m2_chip, m2_chip)} chip usage provides tactical advantage")
        
        return insights[:4]  # Return top 4 insights
    
    def _identify_enhanced_key_factors(
        self, m1_xp: float, m2_xp: float, m1_std: float, m2_std: float,
        decisive_m1: List, decisive_m2: List, picks_m1: Dict, picks_m2: Dict,
        h2h_record: Dict, m1_form: Dict, m2_form: Dict
    ) -> List[str]:
        """Identify enhanced key factors affecting the prediction."""
        factors = []
        
        # Score prediction factor
        xp_diff = abs(m1_xp - m2_xp)
        if xp_diff > 15:
            leader = "Manager 1" if m1_xp > m2_xp else "Manager 2"
            factors.append(f"Large expected points gap of {xp_diff:.1f} points favoring {leader}")
        elif xp_diff < 3:
            factors.append("Extremely close expected points - marginal gains will be decisive")
        
        # Form factor
        form_diff = abs(m1_form["form_score"] - m2_form["form_score"])
        if form_diff > 25:
            better_form = "Manager 1" if m1_form["form_score"] > m2_form["form_score"] else "Manager 2"
            factors.append(f"{better_form} has significantly better form (difference: {form_diff:.1f})")
        
        # Consistency factor
        if m1_std > m2_std * 1.4:
            factors.append("Manager 1's team has much higher volatility - could swing either way")
        elif m2_std > m1_std * 1.4:
            factors.append("Manager 2's team has much higher volatility - could swing either way")
        
        # H2H history factor
        if h2h_record["dominance"] in ["manager1", "manager2"]:
            dom_manager = "Manager 1" if h2h_record["dominance"] == "manager1" else "Manager 2"
            win_rate = h2h_record["manager1_win_rate"] if h2h_record["dominance"] == "manager1" else h2h_record["manager2_win_rate"]
            factors.append(f"{dom_manager} has historical H2H dominance ({win_rate*100:.0f}% win rate)")
        
        # Captain differential factor
        if decisive_m1 and decisive_m2:
            m1_captain = next((p for p in decisive_m1 if p.get('is_captain')), None)
            m2_captain = next((p for p in decisive_m2 if p.get('is_captain')), None)
            
            if m1_captain and m2_captain:
                if m1_captain['player_id'] != m2_captain['player_id']:
                    factors.append(f"Captain battle: {m1_captain['name']} vs {m2_captain['name']}")
                else:
                    factors.append(f"Same captain ({m1_captain['name']}) - other differentials will decide")
        
        # Chip usage factor
        m1_chip = picks_m1.get('active_chip')
        m2_chip = picks_m2.get('active_chip')
        if m1_chip and not m2_chip:
            factors.append(f"Manager 1's {m1_chip} chip provides significant advantage")
        elif m2_chip and not m1_chip:
            factors.append(f"Manager 2's {m2_chip} chip provides significant advantage")
        elif m1_chip and m2_chip and m1_chip != m2_chip:
            factors.append(f"Chip battle: {m1_chip} vs {m2_chip}")
        
        return factors