import asyncio
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import math
import random
from enum import Enum

from app.services.live_data_v2 import LiveDataService
from app.services.redis_cache import RedisCache

logger = logging.getLogger(__name__)


class MatchState(str, Enum):
    """Match state for predictions"""
    PRE_MATCH = "pre_match"
    EARLY = "early"  # 0-30 mins
    MID = "mid"      # 30-60 mins
    LATE = "late"    # 60-90+ mins
    FINISHED = "finished"


class PlayerPosition(int, Enum):
    """Player positions"""
    GK = 1
    DEF = 2
    MID = 3
    FWD = 4


@dataclass
class PlayerPrediction:
    """Prediction for individual player"""
    player_id: int
    player_name: str
    position: PlayerPosition
    team_id: int
    team_name: str
    is_captain: bool
    is_vice_captain: bool
    
    # Base stats
    fixture_difficulty: float  # 1-5 scale
    form: float
    minutes_probability: float
    ownership: float
    
    # Prediction outputs
    expected_points: float
    min_points: float
    max_points: float
    variance: float
    
    # Event probabilities
    goal_probability: float
    assist_probability: float
    clean_sheet_probability: float
    bonus_probability: float
    card_probability: float
    
    # Impact metrics
    differential_impact: float
    captaincy_value: float
    ceiling: float  # Best case scenario
    floor: float    # Worst case scenario


@dataclass
class H2HPrediction:
    """Head-to-head match prediction"""
    manager1_id: int
    manager1_name: str
    manager1_expected: float
    manager1_min: float
    manager1_max: float
    manager1_variance: float
    
    manager2_id: int
    manager2_name: str
    manager2_expected: float
    manager2_min: float
    manager2_max: float
    manager2_variance: float
    
    # Probabilities
    manager1_win_prob: float
    manager2_win_prob: float
    draw_prob: float
    
    # Key insights
    key_differentials: List[Dict[str, Any]]
    captain_comparison: Dict[str, Any]
    risk_factors: List[str]
    opportunities: List[str]
    
    # Meta
    confidence: float
    predicted_at: datetime
    gameweek: int
    match_state: MatchState


@dataclass
class ScenarioResult:
    """Result of a what-if scenario"""
    scenario_name: str
    manager1_points: float
    manager2_points: float
    probability: float
    point_swing: float
    description: str


class MatchSimulator:
    """Advanced match simulator for H2H predictions"""
    
    def __init__(self, live_data_service: LiveDataService, cache: RedisCache):
        self.live_data_service = live_data_service
        self.cache = cache
        
        # Simulation parameters
        self.monte_carlo_runs = 10000
        self.confidence_threshold = 0.7
        
        # FPL scoring system
        self.scoring = {
            PlayerPosition.GK: {
                "appearance": 2, "goal": 6, "assist": 3, "clean_sheet": 4,
                "saves_per_point": 3, "penalty_save": 5, "yellow": -1, "red": -3
            },
            PlayerPosition.DEF: {
                "appearance": 2, "goal": 6, "assist": 3, "clean_sheet": 4,
                "yellow": -1, "red": -3
            },
            PlayerPosition.MID: {
                "appearance": 2, "goal": 5, "assist": 3, "clean_sheet": 1,
                "yellow": -1, "red": -3
            },
            PlayerPosition.FWD: {
                "appearance": 2, "goal": 4, "assist": 3,
                "yellow": -1, "red": -3
            }
        }
        
    async def predict_h2h_match(
        self, 
        manager1_id: int, 
        manager2_id: int, 
        gameweek: int,
        match_state: MatchState = MatchState.PRE_MATCH,
        live_data: Optional[Dict] = None
    ) -> H2HPrediction:
        """Predict H2H match outcome"""
        
        # Get team data
        manager1_data = await self._get_manager_data(manager1_id, gameweek)
        manager2_data = await self._get_manager_data(manager2_id, gameweek)
        
        # Get fixture difficulty and form data
        fixtures = await self._get_fixture_data(gameweek)
        
        # Predict individual players
        manager1_predictions = await self._predict_team(
            manager1_data, fixtures, gameweek, match_state, live_data
        )
        manager2_predictions = await self._predict_team(
            manager2_data, fixtures, gameweek, match_state, live_data
        )
        
        # Calculate team totals
        manager1_expected = sum(p.expected_points for p in manager1_predictions)
        manager1_variance = sum(p.variance for p in manager1_predictions)
        manager1_min = sum(p.floor for p in manager1_predictions)
        manager1_max = sum(p.ceiling for p in manager1_predictions)
        
        manager2_expected = sum(p.expected_points for p in manager2_predictions)
        manager2_variance = sum(p.variance for p in manager2_predictions)
        manager2_min = sum(p.floor for p in manager2_predictions)
        manager2_max = sum(p.ceiling for p in manager2_predictions)
        
        # Calculate win probabilities using Monte Carlo
        win_probs = await self._calculate_win_probabilities(
            manager1_predictions, manager2_predictions
        )
        
        # Identify key differentials
        key_differentials = self._identify_key_differentials(
            manager1_predictions, manager2_predictions
        )
        
        # Compare captains
        captain_comparison = self._compare_captains(
            manager1_predictions, manager2_predictions
        )
        
        # Analyze risks and opportunities
        risk_factors, opportunities = self._analyze_risks_opportunities(
            manager1_predictions, manager2_predictions
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            manager1_variance, manager2_variance, abs(manager1_expected - manager2_expected)
        )
        
        return H2HPrediction(
            manager1_id=manager1_id,
            manager1_name=manager1_data["name"],
            manager1_expected=manager1_expected,
            manager1_min=manager1_min,
            manager1_max=manager1_max,
            manager1_variance=manager1_variance,
            
            manager2_id=manager2_id,
            manager2_name=manager2_data["name"],
            manager2_expected=manager2_expected,
            manager2_min=manager2_min,
            manager2_max=manager2_max,
            manager2_variance=manager2_variance,
            
            manager1_win_prob=win_probs["manager1"],
            manager2_win_prob=win_probs["manager2"],
            draw_prob=win_probs["draw"],
            
            key_differentials=key_differentials,
            captain_comparison=captain_comparison,
            risk_factors=risk_factors,
            opportunities=opportunities,
            
            confidence=confidence,
            predicted_at=datetime.utcnow(),
            gameweek=gameweek,
            match_state=match_state
        )
        
    async def _get_manager_data(self, manager_id: int, gameweek: int) -> Dict:
        """Get manager team data"""
        # Try cache first
        cache_key = f"manager_team:{manager_id}:{gameweek}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
            
        # Get from API
        picks = await self.live_data_service.get_manager_picks(manager_id, gameweek)
        manager_info = await self.live_data_service.get_manager_info(manager_id)
        
        data = {
            "id": manager_id,
            "name": manager_info.get("player_first_name", "Unknown") + " " + manager_info.get("player_last_name", ""),
            "picks": picks["picks"],
            "captain": next(p["element"] for p in picks["picks"] if p["is_captain"]),
            "vice_captain": next(p["element"] for p in picks["picks"] if p["is_vice_captain"]),
        }
        
        # Cache for 1 hour
        await self.cache.set(cache_key, data, ttl=3600)
        return data
        
    async def _get_fixture_data(self, gameweek: int) -> Dict:
        """Get fixture difficulty and team data"""
        cache_key = f"fixtures:{gameweek}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
            
        bootstrap = await self.live_data_service.get_bootstrap_static()
        fixtures = await self.live_data_service.get_fixtures(gameweek)
        
        # Create fixture difficulty mapping
        fixture_map = {}
        team_difficulty = {}
        
        for fixture in fixtures:
            home_team = fixture["team_h"]
            away_team = fixture["team_a"]
            
            # Calculate difficulty (1=easy, 5=hard)
            home_difficulty = fixture.get("team_h_difficulty", 3)
            away_difficulty = fixture.get("team_a_difficulty", 3)
            
            team_difficulty[home_team] = home_difficulty
            team_difficulty[away_team] = away_difficulty
            
            fixture_map[fixture["id"]] = {
                "home_team": home_team,
                "away_team": away_team,
                "home_difficulty": home_difficulty,
                "away_difficulty": away_difficulty,
                "started": fixture.get("started", False),
                "finished": fixture.get("finished", False)
            }
            
        data = {
            "fixtures": fixture_map,
            "team_difficulty": team_difficulty,
            "teams": {t["id"]: t for t in bootstrap["teams"]},
            "elements": {e["id"]: e for e in bootstrap["elements"]}
        }
        
        # Cache for 6 hours
        await self.cache.set(cache_key, data, ttl=21600)
        return data
        
    async def _predict_team(
        self, 
        manager_data: Dict, 
        fixtures: Dict, 
        gameweek: int,
        match_state: MatchState,
        live_data: Optional[Dict] = None
    ) -> List[PlayerPrediction]:
        """Predict all players in a team"""
        predictions = []
        
        for pick in manager_data["picks"]:
            if pick["multiplier"] == 0:  # Benched player
                continue
                
            player_id = pick["element"]
            player_data = fixtures["elements"][player_id]
            team_id = player_data["team"]
            
            # Get fixture difficulty
            difficulty = fixtures["team_difficulty"].get(team_id, 3)
            
            # Calculate prediction
            prediction = await self._predict_player(
                player_data, difficulty, pick, gameweek, match_state, live_data
            )
            
            predictions.append(prediction)
            
        return predictions
        
    async def _predict_player(
        self,
        player_data: Dict,
        difficulty: float,
        pick: Dict,
        gameweek: int,
        match_state: MatchState,
        live_data: Optional[Dict] = None
    ) -> PlayerPrediction:
        """Predict individual player performance"""
        
        player_id = player_data["id"]
        position = PlayerPosition(player_data["element_type"])
        is_captain = pick["is_captain"]
        is_vice = pick["is_vice_captain"]
        multiplier = pick["multiplier"]
        
        # Base stats
        form = float(player_data.get("form", 0))
        minutes = player_data.get("minutes", 0)
        total_points = player_data.get("total_points", 0)
        
        # Calculate minutes probability
        games_played = max(1, player_data.get("games_played", 1))
        avg_minutes = minutes / games_played
        minutes_prob = min(1.0, avg_minutes / 90.0)
        
        # Adjust for live data if available
        if live_data and match_state != MatchState.PRE_MATCH:
            live_stats = live_data.get("elements", {}).get(str(player_id), {})
            if live_stats.get("minutes", 0) > 0:
                minutes_prob = 1.0
            elif live_stats.get("minutes", 0) == 0 and match_state in [MatchState.MID, MatchState.LATE]:
                minutes_prob = 0.1  # Unlikely to play
                
        # Calculate event probabilities
        goals_per_90 = (player_data.get("goals_scored", 0) / max(1, minutes)) * 90
        assists_per_90 = (player_data.get("assists", 0) / max(1, minutes)) * 90
        
        # Adjust for difficulty
        difficulty_multiplier = (6 - difficulty) / 5.0  # Invert so easier = higher
        
        goal_prob = min(0.8, goals_per_90 * difficulty_multiplier * (form / 5.0) * minutes_prob)
        assist_prob = min(0.6, assists_per_90 * difficulty_multiplier * (form / 5.0) * minutes_prob)
        
        # Clean sheet probability for defenders/goalkeepers
        if position in [PlayerPosition.GK, PlayerPosition.DEF]:
            team_cs_rate = 0.3  # Default
            cs_prob = team_cs_rate * difficulty_multiplier * minutes_prob
        else:
            cs_prob = 0.0
            
        # Bonus probability (simplified)
        bonus_prob = (goal_prob * 0.7 + assist_prob * 0.3) * 0.4
        
        # Card probability
        cards_per_90 = (player_data.get("yellow_cards", 0) + player_data.get("red_cards", 0) * 2) / max(1, minutes) * 90
        card_prob = min(0.3, cards_per_90 * minutes_prob)
        
        # Calculate expected points
        expected_points = self._calculate_expected_points(
            position, minutes_prob, goal_prob, assist_prob, cs_prob, bonus_prob, card_prob
        )
        
        # Apply captain multiplier
        if is_captain:
            expected_points *= 2
        elif is_vice and multiplier > 1:
            expected_points *= multiplier
            
        # Calculate variance and bounds
        variance = self._calculate_variance(
            position, minutes_prob, goal_prob, assist_prob, cs_prob, bonus_prob, card_prob
        )
        
        # Apply captain multiplier to variance
        if is_captain:
            variance *= 4  # Variance scales with square of multiplier
        elif is_vice and multiplier > 1:
            variance *= multiplier ** 2
            
        # Calculate floor and ceiling
        std_dev = math.sqrt(variance)
        floor = max(0, expected_points - 2 * std_dev)
        ceiling = expected_points + 2 * std_dev
        
        # Differential impact (simplified)
        ownership = player_data.get("selected_by_percent", 50) / 100.0
        differential_impact = (1 - ownership) * expected_points
        
        # Captaincy value
        captaincy_value = expected_points if not is_captain else expected_points / 2
        
        return PlayerPrediction(
            player_id=player_id,
            player_name=player_data["web_name"],
            position=position,
            team_id=player_data["team"],
            team_name=player_data["team_name"] if "team_name" in player_data else "Unknown",
            is_captain=is_captain,
            is_vice_captain=is_vice,
            
            fixture_difficulty=difficulty,
            form=form,
            minutes_probability=minutes_prob,
            ownership=ownership,
            
            expected_points=expected_points,
            min_points=floor,
            max_points=ceiling,
            variance=variance,
            
            goal_probability=goal_prob,
            assist_probability=assist_prob,
            clean_sheet_probability=cs_prob,
            bonus_probability=bonus_prob,
            card_probability=card_prob,
            
            differential_impact=differential_impact,
            captaincy_value=captaincy_value,
            ceiling=ceiling,
            floor=floor
        )
        
    def _calculate_expected_points(
        self,
        position: PlayerPosition,
        minutes_prob: float,
        goal_prob: float,
        assist_prob: float,
        cs_prob: float,
        bonus_prob: float,
        card_prob: float
    ) -> float:
        """Calculate expected FPL points"""
        
        scoring = self.scoring[position]
        
        expected = 0.0
        
        # Appearance points
        expected += minutes_prob * scoring["appearance"]
        
        # Goal points
        expected += goal_prob * scoring["goal"]
        
        # Assist points
        expected += assist_prob * scoring["assist"]
        
        # Clean sheet points
        if "clean_sheet" in scoring:
            expected += cs_prob * scoring["clean_sheet"]
            
        # Bonus points (1-3 points)
        expected += bonus_prob * 2.0  # Average bonus
        
        # Card penalty
        expected += card_prob * scoring["yellow"]  # Assume mostly yellow cards
        
        return max(0, expected)
        
    def _calculate_variance(self, position: PlayerPosition, minutes_prob: float, 
                          goal_prob: float, assist_prob: float, cs_prob: float,
                          bonus_prob: float, card_prob: float) -> float:
        """Calculate variance in points"""
        
        scoring = self.scoring[position]
        
        # Simplified variance calculation
        variance = 0.0
        
        # Goal variance
        variance += goal_prob * (1 - goal_prob) * (scoring["goal"] ** 2)
        
        # Assist variance
        variance += assist_prob * (1 - assist_prob) * (scoring["assist"] ** 2)
        
        # Clean sheet variance
        if "clean_sheet" in scoring:
            variance += cs_prob * (1 - cs_prob) * (scoring["clean_sheet"] ** 2)
            
        # Bonus variance (more complex distribution)
        variance += bonus_prob * (1 - bonus_prob) * 4  # Simplified
        
        return variance
        
    async def _calculate_win_probabilities(
        self, 
        team1: List[PlayerPrediction], 
        team2: List[PlayerPrediction]
    ) -> Dict[str, float]:
        """Calculate win probabilities using Monte Carlo simulation"""
        
        wins_1 = 0
        wins_2 = 0
        draws = 0
        
        for _ in range(self.monte_carlo_runs):
            # Simulate team 1
            score_1 = 0
            for player in team1:
                score_1 += self._simulate_player_score(player)
                
            # Simulate team 2
            score_2 = 0
            for player in team2:
                score_2 += self._simulate_player_score(player)
                
            # Determine winner
            if score_1 > score_2:
                wins_1 += 1
            elif score_2 > score_1:
                wins_2 += 1
            else:
                draws += 1
                
        total = self.monte_carlo_runs
        return {
            "manager1": wins_1 / total,
            "manager2": wins_2 / total,
            "draw": draws / total
        }
        
    def _simulate_player_score(self, player: PlayerPrediction) -> float:
        """Simulate a single player's score"""
        # Use normal distribution with expected points and variance
        if player.variance > 0:
            score = np.random.normal(player.expected_points, math.sqrt(player.variance))
        else:
            score = player.expected_points
            
        return max(0, score)
        
    def _identify_key_differentials(
        self, 
        team1: List[PlayerPrediction], 
        team2: List[PlayerPrediction]
    ) -> List[Dict[str, Any]]:
        """Identify players who could swing the match"""
        
        differentials = []
        
        # Get all unique players
        team1_players = {p.player_id for p in team1}
        team2_players = {p.player_id for p in team2}
        
        # Find players only in one team
        unique_to_1 = [p for p in team1 if p.player_id not in team2_players]
        unique_to_2 = [p for p in team2 if p.player_id not in team1_players]
        
        # Sort by potential impact
        all_differentials = unique_to_1 + unique_to_2
        all_differentials.sort(key=lambda p: p.differential_impact, reverse=True)
        
        # Take top differentials
        for player in all_differentials[:5]:
            team = "team1" if player in unique_to_1 else "team2"
            differentials.append({
                "player_name": player.player_name,
                "team": team,
                "expected_points": player.expected_points,
                "ceiling": player.ceiling,
                "differential_impact": player.differential_impact,
                "ownership": player.ownership
            })
            
        return differentials
        
    def _compare_captains(
        self, 
        team1: List[PlayerPrediction], 
        team2: List[PlayerPrediction]
    ) -> Dict[str, Any]:
        """Compare captain choices"""
        
        captain1 = next((p for p in team1 if p.is_captain), None)
        captain2 = next((p for p in team2 if p.is_captain), None)
        
        if not captain1 or not captain2:
            return {"comparison": "Unable to compare captains"}
            
        advantage = captain1.expected_points - captain2.expected_points
        
        return {
            "captain1": {
                "name": captain1.player_name,
                "expected": captain1.expected_points,
                "ceiling": captain1.ceiling,
                "floor": captain1.floor
            },
            "captain2": {
                "name": captain2.player_name,
                "expected": captain2.expected_points,
                "ceiling": captain2.ceiling,
                "floor": captain2.floor
            },
            "advantage": advantage,
            "advantage_team": "team1" if advantage > 0 else "team2" if advantage < 0 else "neutral"
        }
        
    def _analyze_risks_opportunities(
        self, 
        team1: List[PlayerPrediction], 
        team2: List[PlayerPrediction]
    ) -> Tuple[List[str], List[str]]:
        """Analyze risks and opportunities"""
        
        risks = []
        opportunities = []
        
        # Captain risks
        captain1 = next((p for p in team1 if p.is_captain), None)
        captain2 = next((p for p in team2 if p.is_captain), None)
        
        if captain1 and captain1.minutes_probability < 0.8:
            risks.append(f"Team 1 captain {captain1.player_name} has rotation risk")
            
        if captain2 and captain2.minutes_probability < 0.8:
            opportunities.append(f"Team 2 captain {captain2.player_name} has rotation risk")
            
        # High ceiling differentials
        for player in team1:
            if player.ceiling > 15 and player.ownership < 0.3:
                opportunities.append(f"{player.player_name} is a low-owned differential with high ceiling")
                
        for player in team2:
            if player.ceiling > 15 and player.ownership < 0.3:
                risks.append(f"Opponent has {player.player_name} - low-owned differential with high ceiling")
                
        return risks[:5], opportunities[:5]
        
    def _calculate_confidence(self, var1: float, var2: float, score_diff: float) -> float:
        """Calculate prediction confidence"""
        
        total_variance = var1 + var2
        
        if total_variance == 0:
            return 1.0
            
        # Higher variance = lower confidence
        # Larger score difference = higher confidence
        confidence = min(1.0, score_diff / math.sqrt(total_variance))
        
        return max(0.1, confidence)
        
    async def run_scenario_analysis(
        self, 
        h2h_prediction: H2HPrediction,
        scenarios: List[str]
    ) -> List[ScenarioResult]:
        """Run what-if scenario analysis"""
        
        results = []
        
        for scenario in scenarios:
            if "captain blank" in scenario.lower():
                result = await self._simulate_captain_blank(h2h_prediction)
            elif "differential haul" in scenario.lower():
                result = await self._simulate_differential_haul(h2h_prediction)
            elif "red card" in scenario.lower():
                result = await self._simulate_red_card(h2h_prediction)
            else:
                continue
                
            results.append(result)
            
        return results
        
    async def _simulate_captain_blank(self, prediction: H2HPrediction) -> ScenarioResult:
        """Simulate captain getting 2 or fewer points"""
        
        # Simplified scenario simulation
        # In reality, you'd re-run the full prediction with captain adjusted
        
        captain_reduction = 15  # Assume captain was expected to get ~15 points
        
        return ScenarioResult(
            scenario_name="Captain Blank",
            manager1_points=prediction.manager1_expected - captain_reduction,
            manager2_points=prediction.manager2_expected,
            probability=0.15,  # 15% chance of captain blank
            point_swing=-captain_reduction,
            description="Your captain gets 2 or fewer points"
        )
        
    async def _simulate_differential_haul(self, prediction: H2HPrediction) -> ScenarioResult:
        """Simulate differential player having exceptional game"""
        
        differential_boost = 20  # Assume differential hauls for 20+ points
        
        return ScenarioResult(
            scenario_name="Differential Haul",
            manager1_points=prediction.manager1_expected,
            manager2_points=prediction.manager2_expected + differential_boost,
            probability=0.05,  # 5% chance of massive haul
            point_swing=differential_boost,
            description="Opponent's differential player hauls 20+ points"
        )
        
    async def _simulate_red_card(self, prediction: H2HPrediction) -> ScenarioResult:
        """Simulate key player getting red card"""
        
        red_card_impact = -5  # Red card = -3 points + lost attacking returns
        
        return ScenarioResult(
            scenario_name="Red Card",
            manager1_points=prediction.manager1_expected + red_card_impact,
            manager2_points=prediction.manager2_expected,
            probability=0.02,  # 2% chance of red card
            point_swing=red_card_impact,
            description="One of your key players gets a red card"
        )