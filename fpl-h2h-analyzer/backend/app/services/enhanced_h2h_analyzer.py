from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import os
import logging
from pathlib import Path

from .h2h_analyzer import H2HAnalyzer
from .live_data import LiveDataService
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
    
    async def analyze_battle_comprehensive(
        self, 
        manager1_id: int, 
        manager2_id: int, 
        gameweek: int
    ) -> Optional[Dict[str, Any]]:
        """
        Perform comprehensive H2H battle analysis combining all analytics modules.
        
        Args:
            manager1_id: First manager's ID
            manager2_id: Second manager's ID
            gameweek: Gameweek number to analyze
            
        Returns:
            Comprehensive analysis dictionary or None if analysis fails
        """
        # Check cache first
        cache_key = self._generate_cache_key(manager1_id, manager2_id, gameweek)
        cached_result = await self._get_cached_analysis(cache_key)
        if cached_result:
            return cached_result
        
        logger.info(f"Starting comprehensive analysis for managers {manager1_id} vs {manager2_id}, GW{gameweek}")
        
        try:
            # Core Analysis
            core_analysis = await self.h2h_analyzer.analyze_battle(manager1_id, manager2_id, gameweek)
            if not core_analysis:
                logger.error("Core analysis failed")
                return None
            
            # Fetch supporting data for advanced analytics
            bootstrap_data = await self.live_data_service.get_bootstrap_static()
            live_gw_data = await self.live_data_service.get_live_gameweek_data(gameweek)
            
            # Fetch manager-specific data
            manager1_history = await self.live_data_service.get_manager_history(manager1_id)
            manager2_history = await self.live_data_service.get_manager_history(manager2_id)
            
            manager1_picks = await self.live_data_service.get_manager_picks(manager1_id, gameweek)
            manager2_picks = await self.live_data_service.get_manager_picks(manager2_id, gameweek)
            
            # Fetch fixture data for the current gameweek
            fixture_data = await self.live_data_service.get_fixtures(event=gameweek)
            
            # Advanced Analytics
            
            # 1. Differential Analysis
            differential_results = await self.differential_analyzer.analyze_differentials(
                manager1_picks_data=manager1_picks,
                manager2_picks_data=manager2_picks,
                live_gameweek_data=live_gw_data,
                bootstrap_static_data=bootstrap_data,
                manager1_id=manager1_id,
                manager2_id=manager2_id,
                gameweek=gameweek
            )
            
            # 2. Predictive Analysis
            prediction_results = await self.predictive_engine.predict_match_outcome(
                manager1_id=manager1_id,
                manager2_id=manager2_id,
                manager1_history=manager1_history,
                manager2_history=manager2_history,
                current_gw_picks_m1=manager1_picks,
                current_gw_picks_m2=manager2_picks,
                fixture_data=fixture_data,
                gameweek=gameweek
            )
            
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
                fixture_data=fixture_data,
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
                fixture_data=fixture_data,
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
            
            # Calculate summary metrics
            advantage_score, confidence_level = self._calculate_summary_metrics(
                core_analysis, differential_results, prediction_results, 
                chip_strategy_m1, chip_strategy_m2, patterns_m1, patterns_m2
            )
            
            # Compile comprehensive results
            comprehensive_analysis = {
                "meta": {
                    "manager1_id": manager1_id,
                    "manager2_id": manager2_id,
                    "gameweek": gameweek,
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                    "cache_key": cache_key
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
                    "advantage_score": advantage_score,
                    "confidence_level": confidence_level,
                    "key_insights": self._extract_key_insights(
                        differential_results, prediction_results, 
                        chip_strategy_m1, chip_strategy_m2, h2h_patterns
                    )
                }
            }
            
            # Cache the results
            await self._cache_analysis(cache_key, comprehensive_analysis)
            
            logger.info(f"Comprehensive analysis completed for {cache_key}")
            return comprehensive_analysis
            
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
        """Extract historical H2H matches from manager histories."""
        # This is a simplified implementation
        # In reality, you'd need to cross-reference league matches
        h2h_matches = []
        
        # For now, return empty list as this requires more complex logic
        # to match up historical gameweeks where they faced each other
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