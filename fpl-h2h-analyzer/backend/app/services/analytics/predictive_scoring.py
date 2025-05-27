"""
Predictive Scoring Engine
Uses player form, fixtures, and xG/xA data to predict scores
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import statistics
import math
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class PlayerPrediction:
    """Prediction for a single player"""
    player_id: int
    name: str
    position: str
    team: str
    
    # Base prediction
    expected_points: float
    confidence: float  # 0-1
    
    # Component predictions
    expected_goals: float
    expected_assists: float
    expected_clean_sheet_prob: float
    expected_bonus: float
    expected_minutes: float
    
    # Risk factors
    injury_risk: float
    rotation_risk: float
    
    # Confidence intervals
    floor_points: float  # 5th percentile
    ceiling_points: float  # 95th percentile


@dataclass
class MatchPrediction:
    """Prediction for H2H match outcome"""
    manager1_expected: float
    manager2_expected: float
    
    # Win probabilities
    manager1_win_prob: float
    manager2_win_prob: float
    draw_prob: float
    
    # Score distributions
    manager1_range: Tuple[float, float]  # 90% confidence interval
    manager2_range: Tuple[float, float]
    
    # Key factors
    decisive_players: List[Dict[str, Any]]
    confidence_level: float
    volatility: float


class PredictiveScoringEngine:
    """
    Predicts likely scores using advanced analytics
    """
    
    def __init__(self):
        # Position-specific scoring weights
        self.scoring_weights = {
            1: {  # GKP
                'saves': 1/3,
                'clean_sheet': 4,
                'goals_conceded': -1/2,
                'penalty_save': 5
            },
            2: {  # DEF
                'clean_sheet': 4,
                'goals': 6,
                'assists': 3,
                'goals_conceded': -1/2
            },
            3: {  # MID
                'goals': 5,
                'assists': 3,
                'clean_sheet': 1
            },
            4: {  # FWD
                'goals': 4,
                'assists': 3
            }
        }
        
        # Fixture difficulty multipliers
        self.fixture_multipliers = {
            1: 1.4,   # Very easy
            2: 1.2,   # Easy
            3: 1.0,   # Medium
            4: 0.8,   # Hard
            5: 0.6    # Very hard
        }
        
        # Home/away adjustments
        self.venue_adjustments = {
            'home': 1.1,
            'away': 0.9
        }
    
    async def predict_match_outcome(
        self,
        manager1_picks: Dict[str, Any],
        manager2_picks: Dict[str, Any],
        live_data: Dict[str, Any],
        bootstrap_data: Dict[str, Any],
        fixtures: List[Dict[str, Any]],
        historical_data: Optional[Dict[str, Any]] = None,
        gameweek: Optional[int] = None
    ) -> MatchPrediction:
        """
        Predict H2H match outcome with confidence levels
        """
        try:
            # Get player predictions
            m1_predictions = await self._predict_team_score(
                manager1_picks, live_data, bootstrap_data, fixtures
            )
            
            m2_predictions = await self._predict_team_score(
                manager2_picks, live_data, bootstrap_data, fixtures
            )
            
            # Calculate expected scores
            m1_expected = sum(p.expected_points * p.confidence for p in m1_predictions)
            m2_expected = sum(p.expected_points * p.confidence for p in m2_predictions)
            
            # Add captain multiplier
            m1_captain_id = next(p['element'] for p in manager1_picks['picks'] if p['is_captain'])
            m2_captain_id = next(p['element'] for p in manager2_picks['picks'] if p['is_captain'])
            
            m1_captain_pred = next((p for p in m1_predictions if p.player_id == m1_captain_id), None)
            m2_captain_pred = next((p for p in m2_predictions if p.player_id == m2_captain_id), None)
            
            if m1_captain_pred:
                m1_expected += m1_captain_pred.expected_points * m1_captain_pred.confidence
            if m2_captain_pred:
                m2_expected += m2_captain_pred.expected_points * m2_captain_pred.confidence
            
            # Calculate win probabilities using historical variance
            variance = await self._calculate_score_variance(historical_data)
            win_probs = await self._calculate_win_probabilities(
                m1_expected, m2_expected, variance
            )
            
            # Calculate confidence intervals
            m1_range = await self._calculate_confidence_interval(m1_predictions, m1_captain_id)
            m2_range = await self._calculate_confidence_interval(m2_predictions, m2_captain_id)
            
            # Identify decisive players
            decisive = await self._identify_decisive_players(
                m1_predictions, m2_predictions, manager1_picks, manager2_picks
            )
            
            # Calculate overall confidence and volatility
            confidence = await self._calculate_prediction_confidence(
                m1_predictions, m2_predictions, fixtures
            )
            
            volatility = await self._calculate_match_volatility(
                m1_predictions, m2_predictions
            )
            
            return MatchPrediction(
                manager1_expected=round(m1_expected, 1),
                manager2_expected=round(m2_expected, 1),
                manager1_win_prob=win_probs['manager1'],
                manager2_win_prob=win_probs['manager2'],
                draw_prob=win_probs['draw'],
                manager1_range=m1_range,
                manager2_range=m2_range,
                decisive_players=decisive,
                confidence_level=confidence,
                volatility=volatility
            )
            
        except Exception as e:
            logger.error(f"Error predicting match outcome: {e}")
            # Return default prediction
            return MatchPrediction(
                manager1_expected=50.0,
                manager2_expected=50.0,
                manager1_win_prob=0.33,
                manager2_win_prob=0.33,
                draw_prob=0.34,
                manager1_range=(40, 60),
                manager2_range=(40, 60),
                decisive_players=[],
                confidence_level=0.1,
                volatility=0.5
            )
    
    async def _predict_team_score(
        self,
        picks: Dict[str, Any],
        live_data: Dict[str, Any],
        bootstrap_data: Dict[str, Any],
        fixtures: List[Dict[str, Any]]
    ) -> List[PlayerPrediction]:
        """Predict scores for all players in a team"""
        predictions = []
        
        players_by_id = {p['id']: p for p in bootstrap_data['elements']}
        teams_by_id = {t['id']: t for t in bootstrap_data['teams']}
        
        for pick in picks['picks']:
            player_id = pick['element']
            player = players_by_id.get(player_id)
            
            if not player:
                continue
                
            prediction = await self._predict_player_score(
                player, live_data, fixtures, teams_by_id
            )
            
            if prediction:
                predictions.append(prediction)
        
        return predictions
    
    async def _predict_player_score(
        self,
        player: Dict[str, Any],
        live_data: Dict[str, Any],
        fixtures: List[Dict[str, Any]],
        teams_by_id: Dict[int, Any]
    ) -> Optional[PlayerPrediction]:
        """Predict score for a single player"""
        try:
            # Get player's recent performance
            live_player = next(
                (p for p in live_data.get('elements', []) if p['id'] == player['id']), 
                {}
            )
            
            # Base expected points from FPL
            ep_next = float(player.get('ep_next', '0'))
            
            # Get fixture context
            fixture_info = await self._get_player_fixture(
                player, fixtures, teams_by_id
            )
            
            # Adjust for fixture difficulty
            fixture_mult = self.fixture_multipliers.get(
                fixture_info['difficulty'], 1.0
            )
            venue_mult = self.venue_adjustments.get(
                fixture_info['venue'], 1.0
            )
            
            # Form adjustment
            form = float(player.get('form', '0'))
            form_mult = 1.0 + (form - 5.0) / 10.0  # 5.0 is average
            
            # Minutes prediction
            expected_minutes = await self._predict_minutes(player, live_player)
            minutes_mult = expected_minutes / 90.0
            
            # Calculate component predictions
            position = player['element_type']
            
            xG = float(player.get('expected_goals', '0'))
            xA = float(player.get('expected_assists', '0'))
            
            # Adjust xG/xA for fixture
            xG_adjusted = xG * fixture_mult * venue_mult
            xA_adjusted = xA * fixture_mult * venue_mult
            
            # Clean sheet probability
            cs_prob = await self._predict_clean_sheet_prob(
                player, fixture_info, teams_by_id
            )
            
            # Bonus prediction
            bonus_pred = await self._predict_bonus(
                player, xG_adjusted, xA_adjusted, position
            )
            
            # Calculate expected points
            expected = (
                ep_next * fixture_mult * venue_mult * form_mult * minutes_mult
            )
            
            # Add appearance points
            if expected_minutes >= 60:
                expected += 2
            elif expected_minutes > 0:
                expected += 1
            
            # Calculate confidence
            confidence = await self._calculate_player_confidence(
                player, fixture_info, expected_minutes
            )
            
            # Calculate floor and ceiling
            volatility = await self._calculate_player_volatility(player, position)
            floor = max(0, expected * (1 - volatility))
            ceiling = expected * (1 + volatility * 2)
            
            # Risk assessments
            injury_risk = await self._assess_injury_risk(player)
            rotation_risk = await self._assess_rotation_risk(
                player, fixture_info, expected_minutes
            )
            
            return PlayerPrediction(
                player_id=player['id'],
                name=player['web_name'],
                position=['GKP', 'DEF', 'MID', 'FWD'][position - 1],
                team=teams_by_id[player['team']]['short_name'],
                expected_points=round(expected, 2),
                confidence=confidence,
                expected_goals=xG_adjusted,
                expected_assists=xA_adjusted,
                expected_clean_sheet_prob=cs_prob,
                expected_bonus=bonus_pred,
                expected_minutes=expected_minutes,
                injury_risk=injury_risk,
                rotation_risk=rotation_risk,
                floor_points=round(floor, 1),
                ceiling_points=round(ceiling, 1)
            )
            
        except Exception as e:
            logger.error(f"Error predicting player score for {player.get('web_name')}: {e}")
            return None
    
    async def _get_player_fixture(
        self,
        player: Dict[str, Any],
        fixtures: List[Dict[str, Any]],
        teams_by_id: Dict[int, Any]
    ) -> Dict[str, Any]:
        """Get fixture information for a player"""
        team_id = player['team']
        
        # Find next fixture
        next_fixture = next(
            (f for f in fixtures if not f['finished'] and 
             (f['team_h'] == team_id or f['team_a'] == team_id)),
            None
        )
        
        if not next_fixture:
            return {
                'difficulty': 3,
                'venue': 'unknown',
                'opponent': 'unknown',
                'opponent_form': 3
            }
        
        if next_fixture['team_h'] == team_id:
            return {
                'difficulty': next_fixture['team_h_difficulty'],
                'venue': 'home',
                'opponent': teams_by_id[next_fixture['team_a']]['short_name'],
                'opponent_form': teams_by_id[next_fixture['team_a']].get('strength', 3)
            }
        else:
            return {
                'difficulty': next_fixture['team_a_difficulty'],
                'venue': 'away',
                'opponent': teams_by_id[next_fixture['team_h']]['short_name'],
                'opponent_form': teams_by_id[next_fixture['team_h']].get('strength', 3)
            }
    
    async def _predict_minutes(
        self,
        player: Dict[str, Any],
        live_player: Dict[str, Any]
    ) -> float:
        """Predict expected minutes for a player"""
        # Get recent minutes
        recent_minutes = live_player.get('stats', {}).get('minutes', 0)
        
        # Get starts data
        starts = player.get('starts', 0)
        starts_per_90 = player.get('starts_per_90', 0)
        
        # Base prediction on recent form
        if recent_minutes > 0:
            if starts_per_90 > 0.9:
                return 90.0  # Regular starter
            elif starts_per_90 > 0.7:
                return 75.0  # Rotation risk
            elif starts_per_90 > 0.3:
                return 45.0  # Sub
            else:
                return 15.0  # Bench player
        
        # No recent data - use season average
        total_minutes = player.get('minutes', 0)
        games_played = max(1, player.get('starts', 0) + player.get('subs', 0))
        
        return min(90, total_minutes / games_played) if games_played > 0 else 0
    
    async def _predict_clean_sheet_prob(
        self,
        player: Dict[str, Any],
        fixture_info: Dict[str, Any],
        teams_by_id: Dict[int, Any]
    ) -> float:
        """Predict clean sheet probability"""
        if player['element_type'] > 2:  # Not GKP or DEF
            return 0.0
        
        # Base probability by fixture difficulty
        base_probs = {
            1: 0.5,   # Very easy
            2: 0.4,   # Easy
            3: 0.3,   # Medium
            4: 0.2,   # Hard
            5: 0.1    # Very hard
        }
        
        base_prob = base_probs.get(fixture_info['difficulty'], 0.25)
        
        # Adjust for home/away
        if fixture_info['venue'] == 'home':
            base_prob *= 1.2
        else:
            base_prob *= 0.85
        
        # Cap at reasonable levels
        return min(0.6, max(0.05, base_prob))
    
    async def _predict_bonus(
        self,
        player: Dict[str, Any],
        xG: float,
        xA: float,
        position: int
    ) -> float:
        """Predict expected bonus points"""
        # Base on BPS data and position
        bps = player.get('bps', 0)
        influence = float(player.get('influence', '0'))
        
        # Position multipliers for bonus likelihood
        position_mults = {
            1: 0.8,   # GKP
            2: 1.0,   # DEF
            3: 1.2,   # MID
            4: 1.1    # FWD
        }
        
        # Expected involvement
        involvement = xG + xA * 0.8
        
        # Rough bonus calculation
        if involvement > 0.5:
            bonus_prob = 0.6
        elif involvement > 0.3:
            bonus_prob = 0.3
        elif involvement > 0.1:
            bonus_prob = 0.1
        else:
            bonus_prob = 0.05
        
        # Adjust for position
        bonus_prob *= position_mults.get(position, 1.0)
        
        # Expected bonus (0-3 scale)
        return bonus_prob * 2.0  # Average of 2 bonus when getting any
    
    async def _calculate_player_confidence(
        self,
        player: Dict[str, Any],
        fixture_info: Dict[str, Any],
        expected_minutes: float
    ) -> float:
        """Calculate confidence in player prediction"""
        confidence = 0.5  # Base confidence
        
        # Adjust for minutes certainty
        if expected_minutes >= 85:
            confidence += 0.2
        elif expected_minutes >= 60:
            confidence += 0.1
        elif expected_minutes < 30:
            confidence -= 0.2
        
        # Adjust for form
        form = float(player.get('form', '0'))
        if form > 6:
            confidence += 0.1
        elif form < 3:
            confidence -= 0.1
        
        # Adjust for fixture predictability
        if fixture_info['difficulty'] in [1, 5]:  # Extreme fixtures
            confidence += 0.1
        
        return max(0.1, min(0.95, confidence))
    
    async def _calculate_player_volatility(
        self,
        player: Dict[str, Any],
        position: int
    ) -> float:
        """Calculate player scoring volatility"""
        # Base volatility by position
        position_volatility = {
            1: 0.3,   # GKP - relatively stable
            2: 0.4,   # DEF - moderate
            3: 0.6,   # MID - higher variance
            4: 0.7    # FWD - highest variance
        }
        
        base = position_volatility.get(position, 0.5)
        
        # Adjust for player type
        goals = player.get('goals_scored', 0)
        assists = player.get('assists', 0)
        
        if goals + assists > 10:  # Attacking returns
            base *= 1.2
        elif player.get('penalties_order', 0) and player['penalties_order'] <= 2:
            base *= 1.1  # Penalty takers more volatile
        
        return min(0.9, base)
    
    async def _assess_injury_risk(self, player: Dict[str, Any]) -> float:
        """Assess injury risk (0-1 scale)"""
        # Check injury status
        status = player.get('status', 'a')
        
        injury_risks = {
            'a': 0.0,    # Available
            'd': 0.5,    # Doubtful
            'i': 1.0,    # Injured
            'u': 0.2,    # Unavailable (might be tactical)
            's': 0.8     # Suspended
        }
        
        return injury_risks.get(status, 0.1)
    
    async def _assess_rotation_risk(
        self,
        player: Dict[str, Any],
        fixture_info: Dict[str, Any],
        expected_minutes: float
    ) -> float:
        """Assess rotation risk (0-1 scale)"""
        risk = 0.1  # Base risk
        
        # High rotation risk positions
        if player['element_type'] in [3, 4]:  # MID, FWD
            risk += 0.1
        
        # Easy fixtures increase rotation risk
        if fixture_info['difficulty'] <= 2:
            risk += 0.2
        
        # Low expected minutes indicate rotation
        if expected_minutes < 60:
            risk += 0.3
        elif expected_minutes < 75:
            risk += 0.1
        
        return min(0.9, risk)
    
    async def _calculate_score_variance(
        self,
        historical_data: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate historical score variance"""
        if not historical_data:
            return 15.0  # Default variance
        
        # Extract scores from historical data
        scores = []
        for match in historical_data.get('matches', []):
            scores.append(match.get('entry_1_points', 50))
            scores.append(match.get('entry_2_points', 50))
        
        if len(scores) > 10:
            return statistics.stdev(scores)
        else:
            return 15.0
    
    async def _calculate_win_probabilities(
        self,
        m1_expected: float,
        m2_expected: float,
        variance: float
    ) -> Dict[str, float]:
        """Calculate win/draw/loss probabilities"""
        # Use normal distribution approximation
        diff = m1_expected - m2_expected
        combined_variance = variance * math.sqrt(2)  # Two independent scores
        
        # Z-scores for different outcomes
        z_win = diff / combined_variance
        z_draw_upper = 5 / combined_variance  # Within 5 points is a draw
        z_draw_lower = -5 / combined_variance
        
        # Simple probability calculation
        if diff > 10:
            m1_prob = 0.7 + min(0.25, diff / 100)
            m2_prob = 0.15 - min(0.1, diff / 200)
        elif diff < -10:
            m1_prob = 0.15 - min(0.1, abs(diff) / 200)
            m2_prob = 0.7 + min(0.25, abs(diff) / 100)
        else:
            # Close match
            m1_prob = 0.35 + diff / 50
            m2_prob = 0.35 - diff / 50
        
        draw_prob = 1 - m1_prob - m2_prob
        
        # Ensure valid probabilities
        m1_prob = max(0.05, min(0.9, m1_prob))
        m2_prob = max(0.05, min(0.9, m2_prob))
        draw_prob = max(0.05, 1 - m1_prob - m2_prob)
        
        # Normalize
        total = m1_prob + m2_prob + draw_prob
        
        return {
            'manager1': round(m1_prob / total, 3),
            'manager2': round(m2_prob / total, 3),
            'draw': round(draw_prob / total, 3)
        }
    
    async def _calculate_confidence_interval(
        self,
        predictions: List[PlayerPrediction],
        captain_id: int
    ) -> Tuple[float, float]:
        """Calculate 90% confidence interval for score"""
        # Sum up floor and ceiling
        floor_sum = sum(p.floor_points for p in predictions)
        ceiling_sum = sum(p.ceiling_points for p in predictions)
        
        # Add captain bonus
        captain_pred = next((p for p in predictions if p.player_id == captain_id), None)
        if captain_pred:
            floor_sum += captain_pred.floor_points
            ceiling_sum += captain_pred.ceiling_points
        
        # Adjust for correlation (players don't all hit floor/ceiling together)
        correlation_factor = 0.7
        expected = sum(p.expected_points for p in predictions)
        if captain_pred:
            expected += captain_pred.expected_points
        
        adjusted_floor = expected - (expected - floor_sum) * correlation_factor
        adjusted_ceiling = expected + (ceiling_sum - expected) * correlation_factor
        
        return (round(adjusted_floor, 1), round(adjusted_ceiling, 1))
    
    async def _identify_decisive_players(
        self,
        m1_predictions: List[PlayerPrediction],
        m2_predictions: List[PlayerPrediction],
        m1_picks: Dict[str, Any],
        m2_picks: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify players likely to decide the match"""
        decisive = []
        
        # Get unique players
        m1_ids = {p['element'] for p in m1_picks['picks']}
        m2_ids = {p['element'] for p in m2_picks['picks']}
        
        m1_unique = m1_ids - m2_ids
        m2_unique = m2_ids - m1_ids
        
        # High ceiling differentials
        for pred in m1_predictions:
            if pred.player_id in m1_unique and pred.ceiling_points > 15:
                decisive.append({
                    'player': pred.name,
                    'team': 'manager1',
                    'ceiling': pred.ceiling_points,
                    'expected': pred.expected_points,
                    'type': 'high_ceiling_differential'
                })
        
        for pred in m2_predictions:
            if pred.player_id in m2_unique and pred.ceiling_points > 15:
                decisive.append({
                    'player': pred.name,
                    'team': 'manager2',
                    'ceiling': pred.ceiling_points,
                    'expected': pred.expected_points,
                    'type': 'high_ceiling_differential'
                })
        
        # Captain picks if different
        m1_cap = next(p['element'] for p in m1_picks['picks'] if p['is_captain'])
        m2_cap = next(p['element'] for p in m2_picks['picks'] if p['is_captain'])
        
        if m1_cap != m2_cap:
            m1_cap_pred = next((p for p in m1_predictions if p.player_id == m1_cap), None)
            m2_cap_pred = next((p for p in m2_predictions if p.player_id == m2_cap), None)
            
            if m1_cap_pred:
                decisive.append({
                    'player': m1_cap_pred.name,
                    'team': 'manager1',
                    'expected': m1_cap_pred.expected_points * 2,
                    'type': 'captain_pick'
                })
            
            if m2_cap_pred:
                decisive.append({
                    'player': m2_cap_pred.name,
                    'team': 'manager2',
                    'expected': m2_cap_pred.expected_points * 2,
                    'type': 'captain_pick'
                })
        
        # Sort by impact
        decisive.sort(
            key=lambda x: x.get('ceiling', x.get('expected', 0)), 
            reverse=True
        )
        
        return decisive[:5]  # Top 5 decisive factors
    
    async def _calculate_prediction_confidence(
        self,
        m1_predictions: List[PlayerPrediction],
        m2_predictions: List[PlayerPrediction],
        fixtures: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall prediction confidence"""
        # Average player confidences
        all_confidences = [p.confidence for p in m1_predictions + m2_predictions]
        avg_confidence = statistics.mean(all_confidences) if all_confidences else 0.5
        
        # Adjust for fixture clarity
        upcoming_fixtures = [f for f in fixtures if not f['finished']]
        if upcoming_fixtures:
            # Clear fixtures (mostly easy or hard) increase confidence
            difficulties = []
            for f in upcoming_fixtures[:5]:
                difficulties.extend([f['team_h_difficulty'], f['team_a_difficulty']])
            
            if difficulties:
                diff_variance = statistics.stdev(difficulties) if len(difficulties) > 1 else 0
                if diff_variance > 1.5:  # High variance = clear fixtures
                    avg_confidence *= 1.1
        
        return min(0.9, max(0.1, avg_confidence))
    
    async def _calculate_match_volatility(
        self,
        m1_predictions: List[PlayerPrediction],
        m2_predictions: List[PlayerPrediction]
    ) -> float:
        """Calculate expected match volatility"""
        # Average player volatilities
        all_volatilities = []
        
        for pred in m1_predictions + m2_predictions:
            # Infer volatility from floor/ceiling spread
            if pred.expected_points > 0:
                spread = (pred.ceiling_points - pred.floor_points) / pred.expected_points
                all_volatilities.append(spread)
        
        if all_volatilities:
            avg_volatility = statistics.mean(all_volatilities)
            # Normalize to 0-1 scale
            return min(1.0, avg_volatility / 3)
        
        return 0.5