from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import asyncio
import json
import os
import logging
from pathlib import Path

from .h2h_analyzer import H2HAnalyzer
from .live_data_v2 import LiveDataService
from .analytics.differential_analyzer import DifferentialAnalyzer
from .analytics.predictive_engine import PredictiveEngine
from .analytics.chip_analyzer import ChipAnalyzer
from .analytics.pattern_recognition import PatternRecognition

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedH2HAnalyzer:
    """
    Orchestrator service that combines results from multiple analytics modules
    to provide comprehensive H2H battle analysis with advanced insights.
    """
    
    def __init__(
        self,
        h2h_analyzer: H2HAnalyzer,
        differential_analyzer: DifferentialAnalyzer,
        predictive_engine: PredictiveEngine,
        chip_analyzer: ChipAnalyzer,
        pattern_recognition: PatternRecognition,
        live_data_service: LiveDataService
    ):
        """
        Initialize the Enhanced H2H Analyzer.
        
        Args:
            h2h_analyzer: Core H2H analysis service
            differential_analyzer: Differential analysis service
            predictive_engine: ML-based prediction service
            chip_analyzer: Chip strategy analysis service
            pattern_recognition: Pattern detection service
            live_data_service: Live FPL data service
        """
        self.h2h_analyzer = h2h_analyzer
        self.differential_analyzer = differential_analyzer
        self.predictive_engine = predictive_engine
        self.chip_analyzer = chip_analyzer
        self.pattern_recognition = pattern_recognition
        self.live_data_service = live_data_service
        
        # Analytics cache configuration
        self.cache_dir = ".analytics_cache"
        self.cache_ttl_seconds = 300  # 5 minutes
        self._ensure_cache_directory()
        
        logger.info("EnhancedH2HAnalyzer initialized with all analytics modules")
    
    def _ensure_cache_directory(self) -> None:
        """Ensure the analytics cache directory exists."""
        Path(self.cache_dir).mkdir(exist_ok=True)
    
    def _generate_cache_key(self, manager1_id: int, manager2_id: int, gameweek: int) -> str:
        """
        Generate a unique cache key for the analysis.
        
        Args:
            manager1_id: First manager's ID
            manager2_id: Second manager's ID
            gameweek: Gameweek number
            
        Returns:
            Cache key string
        """
        # Sort manager IDs to ensure consistent caching regardless of order
        sorted_ids = sorted([manager1_id, manager2_id])
        return f"enhanced_analysis_{sorted_ids[0]}_{sorted_ids[1]}_gw{gameweek}"
    
    async def _get_cached_analysis(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Check for and return cached analysis data if valid.
        
        Args:
            cache_key: Cache key to look up
            
        Returns:
            Cached analysis data if valid, None otherwise
        """
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if not os.path.exists(cache_path):
            return None
        
        # Check if cache is still valid
        file_modified_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        if datetime.now() - file_modified_time > timedelta(seconds=self.cache_ttl_seconds):
            logger.info(f"Cache expired for {cache_key}")
            return None
        
        try:
            with open(cache_path, 'r') as f:
                logger.info(f"Using cached analysis for {cache_key}")
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading cache {cache_key}: {str(e)}")
            return None
    
    async def _cache_analysis(self, cache_key: str, data: Dict[str, Any]) -> None:
        """
        Save analysis data to cache.
        
        Args:
            cache_key: Cache key to save under
            data: Analysis data to cache
        """
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Cached analysis for {cache_key}")
        except Exception as e:
            logger.error(f"Error caching analysis {cache_key}: {str(e)}")
    
    async def _fetch_battle_data(self, manager1_id: int, manager2_id: int, gameweek: int) -> Dict[str, Any]:
        """
        Fetch all required data for battle analysis.
        
        Args:
            manager1_id: First manager's ID
            manager2_id: Second manager's ID
            gameweek: Gameweek number
            
        Returns:
            Dict containing all battle data
        """
        try:
            # Fetch all required data in parallel for better performance
            results = await asyncio.gather(
                self.live_data_service.get_manager_info(manager1_id),
                self.live_data_service.get_manager_info(manager2_id),
                self.live_data_service.get_manager_history(manager1_id),
                self.live_data_service.get_manager_history(manager2_id),
                self.live_data_service.get_manager_picks(manager1_id, gameweek),
                self.live_data_service.get_manager_picks(manager2_id, gameweek),
                self.live_data_service.get_bootstrap_static(),
                self.live_data_service.get_live_gameweek_data(gameweek),
                self.live_data_service.get_fixtures(gameweek=gameweek),
                return_exceptions=True
            )
            
            # Check for errors
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error fetching data at index {i}: {result}")
                    return None
                    
            return {
                "manager1_info": results[0],
                "manager2_info": results[1],
                "manager1_history": results[2],
                "manager2_history": results[3],
                "manager1_picks": results[4],
                "manager2_picks": results[5],
                "bootstrap_data": results[6],
                "live_data": results[7],
                "fixtures": results[8]
            }
        except Exception as e:
            logger.error(f"Error in _fetch_battle_data: {e}")
            return None
    
    async def analyze_battle_comprehensive(
        self, 
        manager1_id: int, 
        manager2_id: int, 
        gameweek: int
    ) -> Optional[Dict[str, Any]]:
        """
        Perform comprehensive H2H battle analysis combining all analytics modules.
        """
        # Check cache first
        cache_key = self._generate_cache_key(manager1_id, manager2_id, gameweek)
        cached_result = await self._get_cached_analysis(cache_key)
        if cached_result:
            return cached_result
        
        logger.info(f"Starting comprehensive analysis for managers {manager1_id} vs {manager2_id}, GW{gameweek}")
        
        try:
            # Fetch all required data
            battle_data = await self._fetch_battle_data(manager1_id, manager2_id, gameweek)
            if not battle_data:
                logger.error("Failed to fetch battle data")
                return None
            
            # Extract data
            manager1_info = battle_data["manager1_info"]
            manager2_info = battle_data["manager2_info"]
            manager1_history = battle_data["manager1_history"]
            manager2_history = battle_data["manager2_history"]
            manager1_picks = battle_data["manager1_picks"]
            manager2_picks = battle_data["manager2_picks"]
            bootstrap_data = battle_data["bootstrap_data"]
            live_data = battle_data["live_data"]
            fixtures = battle_data["fixtures"]
            
            # Core H2H analysis
            core_analysis = await self.h2h_analyzer.analyze_battle(manager1_id, manager2_id, gameweek)
            if not core_analysis:
                logger.error("Core analysis failed")
                return None
            
            # Run all analytics modules
            try:
                # 1. Differential Analysis
                differential_results = await self.differential_analyzer.analyze_differentials(
                    manager1_picks_data=manager1_picks,
                    manager2_picks_data=manager2_picks,
                    live_gameweek_data=live_data,
                    bootstrap_static_data=bootstrap_data,
                    manager1_id=manager1_id,
                    manager2_id=manager2_id,
                    gameweek=gameweek
                )
            except Exception as e:
                logger.error(f"Differential analysis failed: {e}")
                differential_results = {"error": str(e)}
            
            try:
                # 2. Predictive Analysis
                prediction_results = await self.predictive_engine.predict_match_outcome(
                    manager1_id=manager1_id,
                    manager2_id=manager2_id,
                    manager1_history=manager1_history,
                    manager2_history=manager2_history,
                    current_gw_picks_m1=manager1_picks,
                    current_gw_picks_m2=manager2_picks,
                    fixture_data=fixtures,
                    gameweek=gameweek,
                    bootstrap_data=bootstrap_data  # Pass bootstrap data for better predictions
                )
            except Exception as e:
                logger.error(f"Prediction failed: {e}")
                prediction_results = {
                    "manager1_win_probability": 0.45,
                    "manager2_win_probability": 0.45,
                    "draw_probability": 0.10,
                    "confidence": 25.0,
                    "predicted_winner": None,
                    "manager1_expected_points": 45.0,
                    "manager2_expected_points": 45.0,
                    "error": str(e)
                }
            
            # 3. Chip Strategy Analysis
            # Prepare H2H context for chip recommendations
            h2h_context = {
                "opponent_id": manager2_id,
                "score_difference": core_analysis["score_difference"],
                "is_leading": core_analysis["leader"] == manager1_id,
                "opponent_chip": core_analysis["manager2"]["chip"]
            }
            
            chip_strategy_m1 = await self.chip_analyzer.get_chip_recommendations(
                manager_id=manager1_id,
                manager_history=manager1_history,
                fixture_data=fixtures,
                gameweek=gameweek,
                h2h_context=h2h_context
            )
            
            # Reverse H2H context for manager 2
            h2h_context_m2 = {
                "opponent_id": manager1_id,
                "score_difference": -core_analysis["score_difference"],
                "is_leading": core_analysis["leader"] == manager2_id,
                "opponent_chip": core_analysis["manager1"]["chip"]
            }
            
            chip_strategy_m2 = await self.chip_analyzer.get_chip_recommendations(
                manager_id=manager2_id,
                manager_history=manager2_history,
                fixture_data=fixtures,
                gameweek=gameweek,
                h2h_context=h2h_context_m2
            )
            
            # 4. Pattern Recognition
            # Fetch transfer data for pattern analysis
            manager1_transfers = await self.live_data_service.get_manager_transfers(manager1_id)
            manager2_transfers = await self.live_data_service.get_manager_transfers(manager2_id)
            
            patterns_m1 = await self.pattern_recognition.analyze_manager_patterns(
                manager_id=manager1_id,
                manager_history=manager1_history,
                transfer_history=manager1_transfers
            )
            
            patterns_m2 = await self.pattern_recognition.analyze_manager_patterns(
                manager_id=manager2_id,
                manager_history=manager2_history,
                transfer_history=manager2_transfers
            )
            
            # Get historical H2H data for pattern analysis
            h2h_historical = await self._get_historical_h2h_matches(
                manager1_id, manager2_id, manager1_history, manager2_history
            )
            
            h2h_patterns = await self.pattern_recognition.analyze_h2h_patterns(
                manager1_id=manager1_id,
                manager2_id=manager2_id,
                historical_h2h_matches=h2h_historical
            )
            
            # Build comprehensive response
            analysis = {
                "meta": {
                    "manager1_id": manager1_id,
                    "manager2_id": manager2_id,
                    "gameweek": gameweek,
                    "timestamp": datetime.utcnow().isoformat()
                },
                "core_analysis": core_analysis,
                "differential_analysis": differential_results,
                "prediction": prediction_results,
                "chip_strategies": {
                    "manager1": chip_strategy_m1,
                    "manager2": chip_strategy_m2
                },
                "patterns": {
                    "manager1": patterns_m1,
                    "manager2": patterns_m2,
                    "h2h": h2h_patterns
                },
                "summary": {
                    "advantage_score": self._calculate_advantage_score(core_analysis, differential_results),
                    "confidence_level": self._calculate_confidence_level(prediction_results),
                    "key_insights": self._generate_key_insights(core_analysis, differential_results, prediction_results)
                }
            }
            
            # Cache the results
            await self._cache_analysis(cache_key, analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {str(e)}", exc_info=True)
            return None
    
    async def get_analysis_summary(
        self, 
        manager1_id: int, 
        manager2_id: int, 
        gameweek: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get a summarized version of the comprehensive analysis.
        
        Args:
            manager1_id: First manager's ID
            manager2_id: Second manager's ID
            gameweek: Gameweek number
            
        Returns:
            Summarized analysis dictionary or None if analysis fails
        """
        # Get full analysis
        full_analysis = await self.analyze_battle_comprehensive(manager1_id, manager2_id, gameweek)
        if not full_analysis:
            return None
        
        # Extract summary
        try:
            summary = {
                "meta": {
                    "manager1_id": manager1_id,
                    "manager2_id": manager2_id,
                    "gameweek": gameweek
                },
                "scores": {
                    "manager1": full_analysis["core_analysis"]["manager1"]["score"]["total"],
                    "manager2": full_analysis["core_analysis"]["manager2"]["score"]["total"],
                    "difference": full_analysis["core_analysis"]["score_difference"]
                },
                "prediction": {
                    "predicted_winner": full_analysis["prediction"]["predicted_winner"],
                    "win_probability": full_analysis["prediction"]["win_probability"],
                    "confidence": full_analysis["prediction"]["confidence"]
                },
                "key_differentials": full_analysis["differential_analysis"]["key_differentials"][:2],
                "chip_alert": self._get_chip_alert(
                    full_analysis["chip_strategies"]["manager1"],
                    full_analysis["chip_strategies"]["manager2"]
                ),
                "key_pattern": self._get_key_pattern(full_analysis["patterns"]),
                "overall": {
                    "advantage_score": full_analysis["summary"]["advantage_score"],
                    "confidence_level": full_analysis["summary"]["confidence_level"],
                    "headline": self._generate_headline(full_analysis)
                }
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error creating summary: {str(e)}")
            return None
    
    def _calculate_summary_metrics(
        self,
        core_analysis: Dict[str, Any],
        differential_results: Dict[str, Any],
        prediction_results: Dict[str, Any],
        chip_strategy_m1: Dict[str, Any],
        chip_strategy_m2: Dict[str, Any],
        patterns_m1: Dict[str, Any],
        patterns_m2: Dict[str, Any]
    ) -> Tuple[float, str]:
        """
        Calculate advantage score and confidence level.
        
        Returns:
            Tuple of (advantage_score, confidence_level)
        """
        # Advantage Score calculation (0-100)
        advantage_components = []
        
        # Score difference component (0-40 points)
        score_diff = abs(core_analysis["score_difference"])
        score_component = min(score_diff / 2, 40)
        advantage_components.append(score_component)
        
        # Differential impact component (0-30 points)
        if differential_results.get("key_differentials"):
            total_psc = sum(d.get("psc", 0) for d in differential_results["key_differentials"][:3])
            diff_component = min(total_psc / 3, 30)
            advantage_components.append(diff_component)
        
        # Prediction confidence component (0-20 points)
        pred_confidence = prediction_results.get("confidence", 0.5)
        pred_component = pred_confidence * 20
        advantage_components.append(pred_component)
        
        # Pattern strength component (0-10 points)
        pattern_score = 0
        if patterns_m1.get("consistency_score", 0) > patterns_m2.get("consistency_score", 0):
            pattern_score = 5
        if patterns_m1.get("form_trajectory") == "improving":
            pattern_score += 5
        advantage_components.append(pattern_score)
        
        advantage_score = sum(advantage_components)
        
        # Confidence Level calculation
        if pred_confidence >= 0.8 and score_diff > 20:
            confidence_level = "very_high"
        elif pred_confidence >= 0.65 and score_diff > 10:
            confidence_level = "high"
        elif pred_confidence >= 0.5:
            confidence_level = "medium"
        elif pred_confidence >= 0.35:
            confidence_level = "low"
        else:
            confidence_level = "very_low"
        
        return advantage_score, confidence_level
    
    def _extract_key_insights(
        self,
        differential_results: Dict[str, Any],
        prediction_results: Dict[str, Any],
        chip_strategy_m1: Dict[str, Any],
        chip_strategy_m2: Dict[str, Any],
        h2h_patterns: Dict[str, Any]
    ) -> List[str]:
        """Extract key insights from the analysis."""
        insights = []
        
        # Differential insights
        if differential_results.get("key_differentials"):
            top_diff = differential_results["key_differentials"][0]
            insights.append(
                f"Key differential: {top_diff['name']} "
                f"(PSC: {top_diff['psc']:.1f} points)"
            )
        
        # Prediction insights
        if prediction_results.get("key_factors"):
            insights.append(prediction_results["key_factors"][0])
        
        # Chip insights
        if chip_strategy_m1.get("immediate_recommendation"):
            insights.append(f"Manager 1 chip opportunity: {chip_strategy_m1['immediate_recommendation']}")
        
        # Pattern insights
        if h2h_patterns.get("dominant_manager"):
            insights.append(f"Historical dominance by Manager {h2h_patterns['dominant_manager']}")
        
        return insights[:3]  # Return top 3 insights
    
    async def _get_historical_h2h_matches(
        self,
        manager1_id: int,
        manager2_id: int,
        manager1_history: Dict[str, Any],
        manager2_history: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Get historical H2H matches between two managers from FPL API.
        
        This fetches actual H2H match data from the FPL API by finding
        leagues where both managers compete against each other.
        
        Args:
            manager1_id: First manager's ID
            manager2_id: Second manager's ID
            manager1_history: Manager 1's historical data
            manager2_history: Manager 2's historical data
            
        Returns:
            List of H2H match dictionaries with actual FPL data
        """
        h2h_matches = []
        
        try:
            # Get the leagues that both managers are in
            # The manager history contains league information
            m1_leagues = manager1_history.get('leagues', {})
            m2_leagues = manager2_history.get('leagues', {})
            
            # Find H2H leagues that both managers are in
            m1_h2h_leagues = m1_leagues.get('h2h', []) if m1_leagues else []
            m2_h2h_leagues = m2_leagues.get('h2h', []) if m2_leagues else []
            
            # Find common H2H leagues
            m1_h2h_ids = {league['id'] for league in m1_h2h_leagues if 'id' in league}
            m2_h2h_ids = {league['id'] for league in m2_h2h_leagues if 'id' in league}
            common_h2h_leagues = m1_h2h_ids.intersection(m2_h2h_ids)
            
            if not common_h2h_leagues:
                logger.info(f"No common H2H leagues found between managers {manager1_id} and {manager2_id}")
                return h2h_matches
            
            # For each common H2H league, fetch the matches
            for league_id in common_h2h_leagues:
                try:
                    # Use the FPL API endpoint for H2H matches
                    endpoint = f"leagues-h2h-matches/league/{league_id}/"
                    league_matches_data = await self.live_data_service._fetch_with_priority(endpoint)
                    
                    if not league_matches_data:
                        continue
                    
                    # The API returns paginated results
                    matches = league_matches_data.get('matches', league_matches_data.get('results', []))
                    
                    # Filter for matches between our two managers
                    for match in matches:
                        entry_1 = match.get('entry_1_entry')
                        entry_2 = match.get('entry_2_entry')
                        
                        # Check if this match is between our two managers
                        if (entry_1 == manager1_id and entry_2 == manager2_id) or \
                           (entry_1 == manager2_id and entry_2 == manager1_id):
                            
                            # Normalize the match data
                            if entry_1 == manager1_id:
                                h2h_match = {
                                    'gameweek': match.get('event'),
                                    'manager1_score': match.get('entry_1_points', 0),
                                    'manager2_score': match.get('entry_2_points', 0),
                                    'finished': match.get('finished', False),
                                    'league_id': league_id,
                                    'match_id': match.get('id')
                                }
                            else:
                                h2h_match = {
                                    'gameweek': match.get('event'),
                                    'manager1_score': match.get('entry_2_points', 0),
                                    'manager2_score': match.get('entry_1_points', 0),
                                    'finished': match.get('finished', False),
                                    'league_id': league_id,
                                    'match_id': match.get('id')
                                }
                            
                            h2h_matches.append(h2h_match)
                    
                except Exception as e:
                    logger.warning(f"Error fetching H2H matches for league {league_id}: {e}")
                    continue
            
            # Sort matches by gameweek
            h2h_matches.sort(key=lambda x: x.get('gameweek', 0))
            
            logger.info(f"Found {len(h2h_matches)} actual H2H matches between managers {manager1_id} and {manager2_id}")
            
        except Exception as e:
            logger.error(f"Error in _get_historical_h2h_matches: {e}")
            # Return empty list if there's an error
            return []
        
        return h2h_matches
    
    def _get_chip_alert(
        self,
        chip_strategy_m1: Dict[str, Any],
        chip_strategy_m2: Dict[str, Any]
    ) -> Optional[str]:
        """Generate chip usage alert if relevant."""
        alerts = []
        
        if chip_strategy_m1.get("immediate_recommendation"):
            alerts.append(f"M1: {chip_strategy_m1['immediate_recommendation']}")
        
        if chip_strategy_m2.get("immediate_recommendation"):
            alerts.append(f"M2: {chip_strategy_m2['immediate_recommendation']}")
        
        return " | ".join(alerts) if alerts else None
    
    def _get_key_pattern(self, patterns: Dict[str, Any]) -> str:
        """Extract the most significant pattern."""
        if patterns.get("h2h", {}).get("trend"):
            return f"H2H Trend: {patterns['h2h']['trend']}"
        elif patterns.get("manager1", {}).get("key_pattern"):
            return f"M1 Pattern: {patterns['manager1']['key_pattern']}"
        elif patterns.get("manager2", {}).get("key_pattern"):
            return f"M2 Pattern: {patterns['manager2']['key_pattern']}"
        else:
            return "No significant patterns detected"
    
    def _generate_headline(self, full_analysis: Dict[str, Any]) -> str:
        """Generate a headline summary of the battle."""
        score_diff = full_analysis["core_analysis"]["score_difference"]
        leader = full_analysis["core_analysis"]["leader"]
        confidence = full_analysis["summary"]["confidence_level"]
        
        if abs(score_diff) < 5:
            return "Nail-biting battle - Too close to call!"
        elif abs(score_diff) < 15:
            return f"Competitive match with slight edge to Manager {leader}"
        elif confidence in ["high", "very_high"]:
            return f"Manager {leader} dominating with {confidence} confidence"
        else:
            return f"Manager {leader} ahead but anything can happen"
    
    def _calculate_advantage_score(self, core_analysis: Dict, differential_results: Dict) -> float:
        """Calculate overall advantage score."""
        score = 0.0
        
        # Score difference component
        if core_analysis:
            score_diff = abs(core_analysis.get("score_difference", 0))
            score += min(score_diff / 2, 20)  # Max 20 points from score diff
        
        # Differential component
        if differential_results and "total_psc_swing" in differential_results:
            psc_swing = differential_results["total_psc_swing"]
            net_advantage = psc_swing.get("net_advantage", 0)
            score += min(abs(net_advantage) / 3, 15)  # Max 15 points from differentials
        
        return round(score, 2)

    def _calculate_confidence_level(self, prediction_results: Dict) -> float:
        """Calculate confidence level in the analysis."""
        if not prediction_results or "error" in prediction_results:
            return 25.0
        
        # Base confidence on prediction probability spread
        win_prob_m1 = prediction_results.get("manager1_win_probability", 0.5)
        win_prob_m2 = prediction_results.get("manager2_win_probability", 0.5)
        
        prob_diff = abs(win_prob_m1 - win_prob_m2)
        confidence = min(prob_diff * 100, 95)  # Max 95% confidence
        
        return round(confidence, 1)

    def _generate_key_insights(self, core_analysis: Dict, differential_results: Dict, prediction_results: Dict) -> List[str]:
        """Generate key insights from the analysis."""
        insights = []
        
        # Score insight
        if core_analysis:
            score_diff = core_analysis.get("score_difference", 0)
            if abs(score_diff) > 20:
                leader_id = core_analysis.get("leader")
                insights.append(f"Manager {leader_id} has a significant {abs(score_diff)} point lead")
        
        # Differential insight
        if differential_results and "key_differentials" in differential_results:
            key_diffs = differential_results["key_differentials"]
            if key_diffs:
                top_diff = key_diffs[0]
                insights.append(f"Key differential: {top_diff.get('name', 'Unknown')} with PSC of {top_diff.get('psc', 0)}")
        
        # Prediction insight
        if prediction_results and "predicted_winner" in prediction_results:
            winner = prediction_results["predicted_winner"]
            prob = prediction_results.get("win_probability", 0)
            if prob > 0.7:
                insights.append(f"Manager {winner} is strongly favored to win ({prob*100:.0f}% probability)")
        
        return insights[:3]  # Return top 3 insights