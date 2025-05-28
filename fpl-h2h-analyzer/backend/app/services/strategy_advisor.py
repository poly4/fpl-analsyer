import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import numpy as np

from app.services.match_simulator import MatchSimulator, H2HPrediction
from app.services.ml_predictor import MLPredictor
from app.services.live_data import LiveDataService
from app.services.redis_cache import RedisCache

logger = logging.getLogger(__name__)


class RecommendationType(str, Enum):
    """Types of strategic recommendations"""
    CAPTAIN = "captain"
    TRANSFER = "transfer"
    CHIP = "chip"
    FORMATION = "formation"
    DIFFERENTIAL = "differential"
    BENCH = "bench"
    H2H_SPECIFIC = "h2h_specific"


class Priority(str, Enum):
    """Recommendation priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TransferTarget:
    """Transfer recommendation target"""
    player_id: int
    player_name: str
    position: str
    team: str
    price: float
    expected_points: float
    ownership: float
    fixtures_rating: float
    form_rating: float
    value_rating: float
    h2h_advantage: float
    reasoning: str


@dataclass
class CaptainChoice:
    """Captain recommendation"""
    player_id: int
    player_name: str
    expected_points: float
    ceiling: float
    floor: float
    safety_rating: float
    differential_value: float
    fixture_appeal: float
    form: float
    h2h_impact: float
    reasoning: str


@dataclass
class ChipRecommendation:
    """Chip usage recommendation"""
    chip_type: str  # "wildcard", "free_hit", "bench_boost", "triple_captain"
    gameweek: int
    expected_gain: float
    confidence: float
    conditions: List[str]
    risks: List[str]
    opportunity_cost: float
    reasoning: str


@dataclass
class StrategicRecommendation:
    """Strategic recommendation"""
    type: RecommendationType
    priority: Priority
    title: str
    description: str
    expected_impact: float
    confidence: float
    timeframe: str  # "immediate", "this_gw", "next_gw", "long_term"
    h2h_specific: bool
    reasoning: List[str]
    data: Dict[str, Any]
    created_at: datetime


class StrategyAdvisor:
    """Strategic advisor for FPL decisions"""
    
    def __init__(
        self,
        match_simulator: MatchSimulator,
        ml_predictor: MLPredictor,
        live_data_service: LiveDataService,
        cache: RedisCache
    ):
        self.match_simulator = match_simulator
        self.ml_predictor = ml_predictor
        self.live_data_service = live_data_service
        self.cache = cache
        
        # Strategy parameters
        self.fixture_horizon = 5  # Look ahead 5 gameweeks
        self.min_expected_gain = 1.0  # Minimum expected points gain
        self.high_ownership_threshold = 30.0  # High ownership %
        self.differential_threshold = 10.0  # Low ownership for differentials
        
    async def generate_h2h_recommendations(
        self,
        manager_id: int,
        h2h_opponent_id: int,
        gameweek: int,
        budget: float = 100.0
    ) -> List[StrategicRecommendation]:
        """Generate H2H-specific strategic recommendations"""
        
        recommendations = []
        
        # Get H2H prediction
        h2h_prediction = await self.match_simulator.predict_h2h_match(
            manager_id, h2h_opponent_id, gameweek
        )
        
        if not h2h_prediction:
            return recommendations
            
        # Get team data
        manager_data = await self._get_manager_team_data(manager_id, gameweek)
        opponent_data = await self._get_manager_team_data(h2h_opponent_id, gameweek)
        
        # Captain recommendations
        captain_recs = await self._generate_captain_recommendations(
            manager_data, opponent_data, h2h_prediction, gameweek
        )
        recommendations.extend(captain_recs)
        
        # Transfer recommendations
        transfer_recs = await self._generate_transfer_recommendations(
            manager_data, opponent_data, h2h_prediction, gameweek, budget
        )
        recommendations.extend(transfer_recs)
        
        # Differential recommendations
        diff_recs = await self._generate_differential_recommendations(
            manager_data, opponent_data, h2h_prediction, gameweek
        )
        recommendations.extend(diff_recs)
        
        # Chip recommendations
        chip_recs = await self._generate_chip_recommendations(
            manager_data, h2h_prediction, gameweek
        )
        recommendations.extend(chip_recs)
        
        # Formation recommendations
        formation_recs = await self._generate_formation_recommendations(
            manager_data, h2h_prediction, gameweek
        )
        recommendations.extend(formation_recs)
        
        # Sort by priority and expected impact
        recommendations.sort(
            key=lambda x: (x.priority.value, -x.expected_impact)
        )
        
        return recommendations
        
    async def _generate_captain_recommendations(
        self,
        manager_data: Dict,
        opponent_data: Dict,
        h2h_prediction: H2HPrediction,
        gameweek: int
    ) -> List[StrategicRecommendation]:
        """Generate captain choice recommendations"""
        
        recommendations = []
        
        # Get captain options from team
        captain_options = await self._analyze_captain_options(
            manager_data, gameweek
        )
        
        # Find best captain choice
        best_captain = max(captain_options, key=lambda x: x.expected_points) if captain_options else None
        
        if best_captain:
            # Check if different from opponent's likely captain
            opponent_captain = self._predict_opponent_captain(opponent_data)
            
            is_differential = (
                opponent_captain and 
                best_captain.player_id != opponent_captain.get("player_id")
            )
            
            priority = Priority.HIGH if is_differential else Priority.MEDIUM
            
            recommendation = StrategicRecommendation(
                type=RecommendationType.CAPTAIN,
                priority=priority,
                title=f"Captain {best_captain.player_name}",
                description=f"Expected {best_captain.expected_points:.1f} points with {best_captain.fixture_appeal:.1f}/5 fixture appeal",
                expected_impact=best_captain.expected_points - (best_captain.expected_points / 2),  # Captain bonus
                confidence=best_captain.safety_rating,
                timeframe="this_gw",
                h2h_specific=is_differential,
                reasoning=[
                    best_captain.reasoning,
                    f"Form: {best_captain.form:.1f}/5",
                    f"Ceiling: {best_captain.ceiling:.1f} points",
                    f"H2H impact: {best_captain.h2h_impact:.1f}"
                ],
                data=asdict(best_captain),
                created_at=datetime.utcnow()
            )
            
            recommendations.append(recommendation)
            
        return recommendations
        
    async def _generate_transfer_recommendations(
        self,
        manager_data: Dict,
        opponent_data: Dict,
        h2h_prediction: H2HPrediction,
        gameweek: int,
        budget: float
    ) -> List[StrategicRecommendation]:
        """Generate transfer recommendations"""
        
        recommendations = []
        
        # Identify weak spots in team
        weak_players = await self._identify_weak_players(manager_data, gameweek)
        
        # Find transfer targets
        for weak_player in weak_players[:3]:  # Top 3 weak spots
            targets = await self._find_transfer_targets(
                weak_player, manager_data, opponent_data, budget, gameweek
            )
            
            if targets:
                best_target = targets[0]  # Already sorted by value
                
                expected_gain = best_target.expected_points - weak_player.get("expected_points", 0)
                
                if expected_gain >= self.min_expected_gain:
                    priority = Priority.HIGH if expected_gain > 3 else Priority.MEDIUM
                    
                    recommendation = StrategicRecommendation(
                        type=RecommendationType.TRANSFER,
                        priority=priority,
                        title=f"Transfer {weak_player['name']} → {best_target.player_name}",
                        description=f"Expected gain: {expected_gain:.1f} points over next {self.fixture_horizon} GWs",
                        expected_impact=expected_gain,
                        confidence=best_target.value_rating,
                        timeframe="next_gw",
                        h2h_specific=best_target.h2h_advantage > 0,
                        reasoning=[
                            best_target.reasoning,
                            f"Fixtures rating: {best_target.fixtures_rating:.1f}/5",
                            f"Form: {best_target.form_rating:.1f}/5",
                            f"Value: £{best_target.price}m"
                        ],
                        data={
                            "transfer_out": weak_player,
                            "transfer_in": asdict(best_target)
                        },
                        created_at=datetime.utcnow()
                    )
                    
                    recommendations.append(recommendation)
                    
        return recommendations
        
    async def _generate_differential_recommendations(
        self,
        manager_data: Dict,
        opponent_data: Dict,
        h2h_prediction: H2HPrediction,
        gameweek: int
    ) -> List[StrategicRecommendation]:
        """Generate differential player recommendations"""
        
        recommendations = []
        
        # Find players in your team but not opponent's
        your_players = {p["element"] for p in manager_data["picks"]}
        opponent_players = {p["element"] for p in opponent_data["picks"]}
        
        # Your unique players
        unique_players = your_players - opponent_players
        
        # Analyze differential impact
        for player_id in unique_players:
            player_data = await self._get_player_analysis(player_id, gameweek)
            
            if player_data and player_data["expected_points"] > 5:  # High expected points
                recommendation = StrategicRecommendation(
                    type=RecommendationType.DIFFERENTIAL,
                    priority=Priority.MEDIUM,
                    title=f"Differential Advantage: {player_data['name']}",
                    description=f"You own {player_data['name']} while opponent doesn't - expect {player_data['expected_points']:.1f} pts",
                    expected_impact=player_data["expected_points"],
                    confidence=0.7,
                    timeframe="this_gw",
                    h2h_specific=True,
                    reasoning=[
                        "Player not owned by H2H opponent",
                        f"Expected points: {player_data['expected_points']:.1f}",
                        f"Ownership: {player_data['ownership']:.1f}%"
                    ],
                    data=player_data,
                    created_at=datetime.utcnow()
                )
                
                recommendations.append(recommendation)
                
        # Find potential differential targets not owned by either
        differential_targets = await self._find_differential_targets(
            your_players, opponent_players, gameweek
        )
        
        for target in differential_targets[:2]:  # Top 2 targets
            recommendation = StrategicRecommendation(
                type=RecommendationType.DIFFERENTIAL,
                priority=Priority.LOW,
                title=f"Consider Differential: {target['name']}",
                description=f"Low-owned player with {target['expected_points']:.1f} expected points",
                expected_impact=target["expected_points"],
                confidence=0.5,
                timeframe="next_gw",
                h2h_specific=True,
                reasoning=[
                    f"Only {target['ownership']:.1f}% ownership",
                    "Neither you nor opponent own this player",
                    f"Good fixtures ahead"
                ],
                data=target,
                created_at=datetime.utcnow()
            )
            
            recommendations.append(recommendation)
            
        return recommendations
        
    async def _generate_chip_recommendations(
        self,
        manager_data: Dict,
        h2h_prediction: H2HPrediction,
        gameweek: int
    ) -> List[StrategicRecommendation]:
        """Generate chip usage recommendations"""
        
        recommendations = []
        
        # Check available chips
        available_chips = manager_data.get("chips", [])
        
        # Triple Captain recommendation
        if "3xc" in available_chips:
            tc_rec = await self._analyze_triple_captain_opportunity(manager_data, gameweek)
            if tc_rec:
                recommendation = StrategicRecommendation(
                    type=RecommendationType.CHIP,
                    priority=Priority.MEDIUM,
                    title=f"Triple Captain {tc_rec['player_name']}",
                    description=f"Expected {tc_rec['expected_gain']:.1f} extra points vs normal captain",
                    expected_impact=tc_rec["expected_gain"],
                    confidence=tc_rec["confidence"],
                    timeframe="this_gw",
                    h2h_specific=True,
                    reasoning=[
                        f"Excellent fixture: {tc_rec['fixture_appeal']}/5",
                        f"High ceiling: {tc_rec['ceiling']} points",
                        "Good opportunity for chip usage"
                    ],
                    data=tc_rec,
                    created_at=datetime.utcnow()
                )
                
                recommendations.append(recommendation)
                
        # Bench Boost recommendation
        if "bboost" in available_chips:
            bb_rec = await self._analyze_bench_boost_opportunity(manager_data, gameweek)
            if bb_rec:
                recommendation = StrategicRecommendation(
                    type=RecommendationType.CHIP,
                    priority=Priority.LOW,
                    title="Bench Boost Opportunity",
                    description=f"Expected {bb_rec['expected_gain']:.1f} points from bench",
                    expected_impact=bb_rec["expected_gain"],
                    confidence=bb_rec["confidence"],
                    timeframe="this_gw",
                    h2h_specific=False,
                    reasoning=[
                        f"Strong bench with {bb_rec['playing_count']} likely starters",
                        "Good fixtures for bench players"
                    ],
                    data=bb_rec,
                    created_at=datetime.utcnow()
                )
                
                recommendations.append(recommendation)
                
        return recommendations
        
    async def _generate_formation_recommendations(
        self,
        manager_data: Dict,
        h2h_prediction: H2HPrediction,
        gameweek: int
    ) -> List[StrategicRecommendation]:
        """Generate formation and lineup recommendations"""
        
        recommendations = []
        
        # Analyze current formation
        current_formation = self._analyze_current_formation(manager_data)
        
        # Check for better formation options
        alternative_formations = await self._find_better_formations(
            manager_data, gameweek
        )
        
        if alternative_formations:
            best_formation = alternative_formations[0]
            
            expected_gain = best_formation["expected_points"] - current_formation["expected_points"]
            
            if expected_gain > 1.0:
                recommendation = StrategicRecommendation(
                    type=RecommendationType.FORMATION,
                    priority=Priority.MEDIUM,
                    title=f"Switch to {best_formation['formation_name']}",
                    description=f"Expected gain: {expected_gain:.1f} points with better starting XI",
                    expected_impact=expected_gain,
                    confidence=0.6,
                    timeframe="this_gw",
                    h2h_specific=False,
                    reasoning=[
                        f"Current: {current_formation['formation_name']}",
                        f"Suggested: {best_formation['formation_name']}",
                        "Better player selection based on fixtures"
                    ],
                    data={
                        "current": current_formation,
                        "suggested": best_formation
                    },
                    created_at=datetime.utcnow()
                )
                
                recommendations.append(recommendation)
                
        return recommendations
        
    async def _get_manager_team_data(self, manager_id: int, gameweek: int) -> Dict:
        """Get manager's team data"""
        picks = await self.live_data_service.get_manager_picks(manager_id, gameweek)
        manager_info = await self.live_data_service.get_manager_info(manager_id)
        
        return {
            "id": manager_id,
            "name": f"{manager_info.get('player_first_name', '')} {manager_info.get('player_last_name', '')}",
            "picks": picks["picks"],
            "chips": picks.get("active_chip", []),
            "transfers": picks.get("entry_history", {}).get("event_transfers", 0)
        }
        
    async def _analyze_captain_options(self, manager_data: Dict, gameweek: int) -> List[CaptainChoice]:
        """Analyze captain options in team"""
        
        captain_options = []
        bootstrap = await self.live_data_service.get_bootstrap_static()
        
        # Get top 5 most expensive players as captain candidates
        players_by_price = sorted(
            manager_data["picks"], 
            key=lambda x: self._get_player_price(x["element"], bootstrap),
            reverse=True
        )[:5]
        
        for pick in players_by_price:
            if pick["multiplier"] == 0:  # Skip benched players
                continue
                
            player_id = pick["element"]
            
            # Get ML prediction
            ml_prediction = await self.ml_predictor.predict_player_points(player_id, gameweek)
            
            if ml_prediction:
                player_data = self._get_player_data(player_id, bootstrap)
                
                captain_choice = CaptainChoice(
                    player_id=player_id,
                    player_name=player_data["web_name"],
                    expected_points=ml_prediction.predicted_points * 2,  # Captain doubles
                    ceiling=ml_prediction.predicted_points * 2.5,  # Optimistic scenario
                    floor=ml_prediction.predicted_points * 0.5,   # Pessimistic scenario
                    safety_rating=ml_prediction.confidence,
                    differential_value=1.0 - (player_data["selected_by_percent"] / 100.0),
                    fixture_appeal=self._calculate_fixture_appeal(player_data, gameweek),
                    form=float(player_data.get("form", 0)),
                    h2h_impact=ml_prediction.predicted_points * 1.5,
                    reasoning=f"Strong form and favorable fixture"
                )
                
                captain_options.append(captain_choice)
                
        return sorted(captain_options, key=lambda x: x.expected_points, reverse=True)
        
    def _predict_opponent_captain(self, opponent_data: Dict) -> Optional[Dict]:
        """Predict opponent's likely captain choice"""
        # Simplified - would use more sophisticated prediction
        picks = opponent_data["picks"]
        captain_pick = next((p for p in picks if p["is_captain"]), None)
        
        if captain_pick:
            return {"player_id": captain_pick["element"]}
            
        return None
        
    async def _identify_weak_players(self, manager_data: Dict, gameweek: int) -> List[Dict]:
        """Identify weak players in team"""
        
        weak_players = []
        bootstrap = await self.live_data_service.get_bootstrap_static()
        
        for pick in manager_data["picks"]:
            if pick["multiplier"] == 0:  # Skip bench
                continue
                
            player_id = pick["element"]
            player_data = self._get_player_data(player_id, bootstrap)
            
            # Criteria for weak players
            is_weak = (
                float(player_data.get("form", 0)) < 3.0 or
                player_data.get("minutes", 0) < 500 or
                float(player_data.get("points_per_game", 0)) < 3.0
            )
            
            if is_weak:
                ml_prediction = await self.ml_predictor.predict_player_points(player_id, gameweek)
                expected_points = ml_prediction.predicted_points if ml_prediction else 2.0
                
                weak_players.append({
                    "player_id": player_id,
                    "name": player_data["web_name"],
                    "position": player_data["element_type"],
                    "price": float(player_data.get("now_cost", 0)) / 10.0,
                    "expected_points": expected_points,
                    "form": float(player_data.get("form", 0)),
                    "reasoning": "Poor form or limited minutes"
                })
                
        return sorted(weak_players, key=lambda x: x["expected_points"])
        
    async def _find_transfer_targets(
        self, 
        weak_player: Dict, 
        manager_data: Dict, 
        opponent_data: Dict, 
        budget: float,
        gameweek: int
    ) -> List[TransferTarget]:
        """Find transfer targets for weak player"""
        
        targets = []
        bootstrap = await self.live_data_service.get_bootstrap_static()
        
        # Get players in same position
        same_position_players = [
            p for p in bootstrap["elements"]
            if p["element_type"] == weak_player["position"]
            and p["id"] not in [pick["element"] for pick in manager_data["picks"]]
            and float(p.get("now_cost", 0)) / 10.0 <= budget + weak_player["price"]
        ]
        
        # Analyze top candidates
        for player in same_position_players[:20]:  # Top 20 by price
            ml_prediction = await self.ml_predictor.predict_player_points(player["id"], gameweek)
            
            if ml_prediction and ml_prediction.predicted_points > weak_player["expected_points"]:
                # Check if opponent owns this player
                opponent_owns = player["id"] in [p["element"] for p in opponent_data["picks"]]
                h2h_advantage = -2.0 if opponent_owns else 1.0
                
                target = TransferTarget(
                    player_id=player["id"],
                    player_name=player["web_name"],
                    position=self._position_name(player["element_type"]),
                    team=player.get("team_name", "Unknown"),
                    price=float(player.get("now_cost", 0)) / 10.0,
                    expected_points=ml_prediction.predicted_points,
                    ownership=float(player.get("selected_by_percent", 0)),
                    fixtures_rating=self._calculate_fixture_appeal(player, gameweek),
                    form_rating=float(player.get("form", 0)),
                    value_rating=ml_prediction.confidence,
                    h2h_advantage=h2h_advantage,
                    reasoning=f"Good fixtures and form, {ml_prediction.predicted_points:.1f} expected points"
                )
                
                targets.append(target)
                
        # Sort by value (expected points per price)
        targets.sort(key=lambda x: x.expected_points / max(x.price, 4.0), reverse=True)
        
        return targets[:5]
        
    async def _find_differential_targets(
        self, 
        your_players: set, 
        opponent_players: set, 
        gameweek: int
    ) -> List[Dict]:
        """Find differential player targets"""
        
        targets = []
        bootstrap = await self.live_data_service.get_bootstrap_static()
        
        # Find players not owned by either manager with low overall ownership
        for player in bootstrap["elements"]:
            if (
                player["id"] not in your_players and 
                player["id"] not in opponent_players and
                float(player.get("selected_by_percent", 100)) < self.differential_threshold
            ):
                ml_prediction = await self.ml_predictor.predict_player_points(player["id"], gameweek)
                
                if ml_prediction and ml_prediction.predicted_points > 4.0:
                    targets.append({
                        "player_id": player["id"],
                        "name": player["web_name"],
                        "expected_points": ml_prediction.predicted_points,
                        "ownership": float(player.get("selected_by_percent", 0)),
                        "price": float(player.get("now_cost", 0)) / 10.0
                    })
                    
        return sorted(targets, key=lambda x: x["expected_points"], reverse=True)[:5]
        
    async def _get_player_analysis(self, player_id: int, gameweek: int) -> Optional[Dict]:
        """Get player analysis data"""
        
        bootstrap = await self.live_data_service.get_bootstrap_static()
        player_data = self._get_player_data(player_id, bootstrap)
        
        if not player_data:
            return None
            
        ml_prediction = await self.ml_predictor.predict_player_points(player_id, gameweek)
        expected_points = ml_prediction.predicted_points if ml_prediction else 2.0
        
        return {
            "player_id": player_id,
            "name": player_data["web_name"],
            "expected_points": expected_points,
            "ownership": float(player_data.get("selected_by_percent", 0)),
            "form": float(player_data.get("form", 0)),
            "price": float(player_data.get("now_cost", 0)) / 10.0
        }
        
    async def _analyze_triple_captain_opportunity(self, manager_data: Dict, gameweek: int) -> Optional[Dict]:
        """Analyze triple captain opportunity"""
        
        # Find best captain candidate
        captain_options = await self._analyze_captain_options(manager_data, gameweek)
        
        if not captain_options:
            return None
            
        best_captain = captain_options[0]
        
        # Check if it's a good TC opportunity
        if (
            best_captain.expected_points > 12 and  # High expected points
            best_captain.fixture_appeal > 3.5 and  # Good fixture
            best_captain.safety_rating > 0.7       # High confidence
        ):
            normal_captain_points = best_captain.expected_points
            tc_points = normal_captain_points * 1.5  # Triple vs double
            
            return {
                "player_id": best_captain.player_id,
                "player_name": best_captain.player_name,
                "expected_gain": tc_points - normal_captain_points,
                "confidence": best_captain.safety_rating,
                "fixture_appeal": best_captain.fixture_appeal,
                "ceiling": best_captain.ceiling * 1.5
            }
            
        return None
        
    async def _analyze_bench_boost_opportunity(self, manager_data: Dict, gameweek: int) -> Optional[Dict]:
        """Analyze bench boost opportunity"""
        
        bench_players = [p for p in manager_data["picks"] if p["multiplier"] == 0]
        
        if len(bench_players) < 4:
            return None
            
        total_expected = 0
        playing_count = 0
        
        for pick in bench_players:
            ml_prediction = await self.ml_predictor.predict_player_points(pick["element"], gameweek)
            
            if ml_prediction:
                total_expected += ml_prediction.predicted_points
                if ml_prediction.predicted_points > 1.5:  # Likely to get minutes
                    playing_count += 1
                    
        if total_expected > 6 and playing_count >= 3:
            return {
                "expected_gain": total_expected,
                "confidence": 0.6,
                "playing_count": playing_count
            }
            
        return None
        
    def _analyze_current_formation(self, manager_data: Dict) -> Dict:
        """Analyze current formation"""
        
        starting_xi = [p for p in manager_data["picks"] if p["multiplier"] > 0]
        
        # Count by position
        gk_count = len([p for p in starting_xi if self._get_position(p["element"]) == 1])
        def_count = len([p for p in starting_xi if self._get_position(p["element"]) == 2])
        mid_count = len([p for p in starting_xi if self._get_position(p["element"]) == 3])
        fwd_count = len([p for p in starting_xi if self._get_position(p["element"]) == 4])
        
        formation_name = f"{def_count}-{mid_count}-{fwd_count}"
        
        return {
            "formation_name": formation_name,
            "expected_points": 50,  # Simplified calculation
            "gk": gk_count,
            "def": def_count,
            "mid": mid_count,
            "fwd": fwd_count
        }
        
    async def _find_better_formations(self, manager_data: Dict, gameweek: int) -> List[Dict]:
        """Find better formation options"""
        
        # Simplified - would analyze all valid formations
        alternative_formations = [
            {"formation_name": "3-5-2", "expected_points": 52},
            {"formation_name": "4-4-2", "expected_points": 51},
            {"formation_name": "3-4-3", "expected_points": 49}
        ]
        
        return alternative_formations
        
    def _get_player_price(self, player_id: int, bootstrap: Dict) -> float:
        """Get player price"""
        player = self._get_player_data(player_id, bootstrap)
        return float(player.get("now_cost", 0)) / 10.0 if player else 0.0
        
    def _get_player_data(self, player_id: int, bootstrap: Dict) -> Optional[Dict]:
        """Get player data from bootstrap"""
        for player in bootstrap["elements"]:
            if player["id"] == player_id:
                return player
        return None
        
    def _get_position(self, player_id: int) -> int:
        """Get player position (simplified)"""
        # Would need bootstrap data here
        return 3  # Default to midfielder
        
    def _position_name(self, position_id: int) -> str:
        """Convert position ID to name"""
        names = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}
        return names.get(position_id, "Unknown")
        
    def _calculate_fixture_appeal(self, player_data: Dict, gameweek: int) -> float:
        """Calculate fixture appeal rating (1-5)"""
        # Simplified fixture appeal calculation
        # Would analyze upcoming fixtures, difficulty, home/away etc.
        return 3.5  # Default decent appeal