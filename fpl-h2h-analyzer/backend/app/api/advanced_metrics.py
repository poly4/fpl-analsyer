"""
API endpoints for advanced metrics and analytics.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, List, Optional, Any
import logging
from ..services.advanced_metrics_engine import AdvancedMetricsEngine, MetricResult, ManagerInsight
from ..services.live_data_v2 import LiveDataService
from ..services.h2h_analyzer import H2HAnalyzer
from ..services.enhanced_h2h_analyzer import EnhancedH2HAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/advanced-metrics", tags=["Advanced Metrics"])

# Dependencies
def get_live_data_service():
    return LiveDataService()

def get_h2h_analyzer():
    return H2HAnalyzer(LiveDataService())

def get_enhanced_h2h_analyzer():
    return EnhancedH2HAnalyzer(LiveDataService())

def get_metrics_engine(
    live_data: LiveDataService = Depends(get_live_data_service),
    h2h_analyzer: H2HAnalyzer = Depends(get_h2h_analyzer),
    enhanced_analyzer: EnhancedH2HAnalyzer = Depends(get_enhanced_h2h_analyzer)
):
    return AdvancedMetricsEngine(live_data, h2h_analyzer, enhanced_analyzer)


@router.get("/manager/{manager_id}/comprehensive")
async def get_comprehensive_metrics(
    manager_id: int,
    league_id: int = Query(..., description="League ID for context"),
    timeframe: str = Query("season", description="Analysis timeframe (season, recent, all)"),
    metrics_engine: AdvancedMetricsEngine = Depends(get_metrics_engine)
):
    """
    Get comprehensive advanced metrics for a manager.
    
    Returns detailed performance analytics including:
    - Consistency score
    - Form analysis  
    - Captain success rate
    - Transfer efficiency
    - Mental strength
    - And more...
    """
    try:
        logger.info(f"Calculating comprehensive metrics for manager {manager_id}")
        
        # Validate timeframe
        valid_timeframes = ["season", "recent", "all"]
        if timeframe not in valid_timeframes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid timeframe. Must be one of: {valid_timeframes}"
            )
        
        # Calculate metrics
        metrics = await metrics_engine.calculate_comprehensive_metrics(
            manager_id, league_id, timeframe
        )
        
        # Convert MetricResult objects to dictionaries for JSON serialization
        metrics_dict = {}
        for metric_name, metric_result in metrics.items():
            metrics_dict[metric_name] = {
                "value": metric_result.value,
                "percentile": metric_result.percentile,
                "grade": metric_result.grade,
                "description": metric_result.description,
                "trend": metric_result.trend,
                "confidence": metric_result.confidence
            }
        
        return {
            "manager_id": manager_id,
            "league_id": league_id,
            "timeframe": timeframe,
            "metrics": metrics_dict,
            "summary": {
                "overall_rating": metrics_dict.get("overall_rating", {}).get("value", 0),
                "grade": metrics_dict.get("overall_rating", {}).get("grade", "N/A"),
                "potential": metrics_dict.get("potential_rating", {}).get("value", 0),
                "top_strengths": _identify_top_metrics(metrics_dict, top_n=3),
                "improvement_areas": _identify_bottom_metrics(metrics_dict, bottom_n=2)
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculating comprehensive metrics for manager {manager_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/manager/{manager_id}/insights")
async def get_manager_insights(
    manager_id: int,
    league_id: int = Query(..., description="League ID for context"),
    metrics_engine: AdvancedMetricsEngine = Depends(get_metrics_engine)
):
    """
    Get actionable insights and recommendations for a manager.
    
    Returns personalized insights based on performance patterns,
    strengths, weaknesses, and improvement opportunities.
    """
    try:
        logger.info(f"Generating insights for manager {manager_id}")
        
        # First get comprehensive metrics
        metrics = await metrics_engine.calculate_comprehensive_metrics(
            manager_id, league_id, "season"
        )
        
        # Generate insights
        insights = await metrics_engine.generate_manager_insights(
            manager_id, league_id, metrics
        )
        
        # Convert ManagerInsight objects to dictionaries
        insights_dict = []
        for insight in insights:
            insights_dict.append({
                "manager_id": insight.manager_id,
                "insight_type": insight.insight_type,
                "title": insight.title,
                "description": insight.description,
                "priority": insight.priority,
                "data": insight.data,
                "confidence": insight.confidence
            })
        
        # Categorize insights
        categorized_insights = {
            "strengths": [i for i in insights_dict if i["insight_type"] == "strength"],
            "improvements": [i for i in insights_dict if i["insight_type"] in ["performance", "strategy"]],
            "patterns": [i for i in insights_dict if i["insight_type"] == "pattern"],
            "high_priority": [i for i in insights_dict if i["priority"] == "high"],
            "actionable": [i for i in insights_dict if i["insight_type"] == "strategy"]
        }
        
        return {
            "manager_id": manager_id,
            "league_id": league_id,
            "total_insights": len(insights_dict),
            "insights": insights_dict,
            "categorized": categorized_insights,
            "summary": {
                "strengths_count": len(categorized_insights["strengths"]),
                "improvement_areas": len(categorized_insights["improvements"]),
                "high_priority_items": len(categorized_insights["high_priority"])
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating insights for manager {manager_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/league/{league_id}/analytics")
async def get_league_analytics(
    league_id: int,
    timeframe: str = Query("season", description="Analysis timeframe"),
    include_distributions: bool = Query(True, description="Include metric distributions"),
    include_archetypes: bool = Query(True, description="Include manager archetypes"),
    metrics_engine: AdvancedMetricsEngine = Depends(get_metrics_engine)
):
    """
    Get comprehensive league analytics and insights.
    
    Returns league-wide metrics including:
    - Power rankings
    - Competitiveness analysis
    - Manager archetypes
    - Statistical distributions
    - Trends and patterns
    """
    try:
        logger.info(f"Calculating league analytics for league {league_id}")
        
        # Calculate comprehensive league analytics
        analytics = await metrics_engine.calculate_league_analytics(league_id, timeframe)
        
        # Filter response based on parameters
        if not include_distributions:
            analytics.pop("distributions", None)
        
        if not include_archetypes:
            analytics.pop("archetypes", None)
        
        # Add summary statistics
        if "power_rankings" in analytics:
            rankings = analytics["power_rankings"]
            analytics["summary"] = {
                "total_managers": len(rankings),
                "average_rating": sum(r["power_rating"] for r in rankings) / len(rankings) if rankings else 0,
                "rating_spread": max(r["power_rating"] for r in rankings) - min(r["power_rating"] for r in rankings) if rankings else 0,
                "top_performer": rankings[0] if rankings else None,
                "most_improved": _find_most_improved(rankings),
                "biggest_surprises": _find_biggest_surprises(rankings)
            }
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error calculating league analytics for league {league_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/manager/{manager_id}/comparison/{opponent_id}")
async def get_advanced_comparison(
    manager_id: int,
    opponent_id: int,
    league_id: int = Query(..., description="League ID for context"),
    metrics_engine: AdvancedMetricsEngine = Depends(get_metrics_engine)
):
    """
    Get advanced comparison between two managers.
    
    Returns detailed metric-by-metric comparison with insights
    about relative strengths and weaknesses.
    """
    try:
        logger.info(f"Advanced comparison: manager {manager_id} vs {opponent_id}")
        
        # Calculate metrics for both managers
        metrics1 = await metrics_engine.calculate_comprehensive_metrics(
            manager_id, league_id, "season"
        )
        metrics2 = await metrics_engine.calculate_comprehensive_metrics(
            opponent_id, league_id, "season"  
        )
        
        # Compare metrics
        comparison = {}
        advantages = {"manager1": [], "manager2": []}
        
        for metric_name in metrics1.keys():
            if metric_name in metrics2:
                value1 = metrics1[metric_name].value
                value2 = metrics2[metric_name].value
                
                difference = value1 - value2
                advantage = "manager1" if difference > 0 else "manager2"
                
                comparison[metric_name] = {
                    "manager1_value": value1,
                    "manager2_value": value2,
                    "difference": abs(difference),
                    "advantage": advantage,
                    "significance": _classify_difference(abs(difference))
                }
                
                # Track significant advantages
                if abs(difference) > 10:  # Significant difference threshold
                    advantages[advantage].append({
                        "metric": metric_name,
                        "difference": abs(difference),
                        "description": metrics1[metric_name].description or metrics2[metric_name].description
                    })
        
        # Overall comparison summary
        manager1_wins = sum(1 for comp in comparison.values() if comp["advantage"] == "manager1")
        manager2_wins = sum(1 for comp in comparison.values() if comp["advantage"] == "manager2")
        
        overall_winner = "manager1" if manager1_wins > manager2_wins else "manager2"
        if manager1_wins == manager2_wins:
            overall_winner = "tie"
        
        return {
            "manager1_id": manager_id,
            "manager2_id": opponent_id,
            "league_id": league_id,
            "comparison": comparison,
            "advantages": advantages,
            "summary": {
                "overall_winner": overall_winner,
                "manager1_wins": manager1_wins,
                "manager2_wins": manager2_wins,
                "total_metrics": len(comparison),
                "significant_differences": len(advantages["manager1"]) + len(advantages["manager2"]),
                "closeness_score": _calculate_closeness_score(comparison)
            }
        }
        
    except Exception as e:
        logger.error(f"Error in advanced comparison {manager_id} vs {opponent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/league/{league_id}/power-rankings")
async def get_power_rankings(
    league_id: int,
    include_metrics: bool = Query(False, description="Include detailed metrics for each manager"),
    metrics_engine: AdvancedMetricsEngine = Depends(get_metrics_engine)
):
    """
    Get power rankings for the league based on advanced metrics.
    
    Power rankings consider overall performance, form, consistency,
    and other advanced metrics beyond just points.
    """
    try:
        logger.info(f"Calculating power rankings for league {league_id}")
        
        # Get league analytics (includes power rankings)
        analytics = await metrics_engine.calculate_league_analytics(league_id, "season")
        
        power_rankings = analytics.get("power_rankings", [])
        
        if include_metrics:
            # Add detailed metrics for each manager
            for ranking in power_rankings:
                manager_id = ranking["manager_id"]
                try:
                    metrics = await metrics_engine.calculate_comprehensive_metrics(
                        manager_id, league_id, "season"
                    )
                    ranking["detailed_metrics"] = {
                        metric_name: {
                            "value": metric.value,
                            "grade": metric.grade,
                            "trend": metric.trend
                        }
                        for metric_name, metric in metrics.items()
                    }
                except Exception as e:
                    logger.warning(f"Failed to get detailed metrics for manager {manager_id}: {e}")
                    ranking["detailed_metrics"] = {}
        
        return {
            "league_id": league_id,
            "power_rankings": power_rankings,
            "metadata": {
                "total_managers": len(power_rankings),
                "calculation_method": "Advanced composite metrics",
                "includes_detailed_metrics": include_metrics,
                "last_updated": analytics.get("generated_at")
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculating power rankings for league {league_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/league/{league_id}/archetypes")
async def get_manager_archetypes(
    league_id: int,
    metrics_engine: AdvancedMetricsEngine = Depends(get_metrics_engine)
):
    """
    Get manager archetypes/playing styles in the league.
    
    Identifies different types of managers based on their
    performance patterns and strategic approaches.
    """
    try:
        logger.info(f"Identifying manager archetypes for league {league_id}")
        
        # Get league analytics
        analytics = await metrics_engine.calculate_league_analytics(league_id, "season")
        archetypes = analytics.get("archetypes", {})
        
        # Add descriptions for each archetype
        archetype_descriptions = {
            "consistent_performer": "Managers who deliver steady, reliable performance week after week",
            "high_risk_high_reward": "Managers who take big risks with differentials and bold choices",
            "steady_eddie": "Conservative managers who focus on safe, consistent strategies",
            "comeback_kid": "Managers who excel at recovering from poor performances",
            "clutch_player": "Managers who perform best under pressure and in crucial moments",
            "transfer_master": "Managers who excel at timing transfers and avoiding hits",
            "captain_genius": "Managers with exceptional captain selection skills"
        }
        
        # Enrich with manager details
        enriched_archetypes = {}
        for archetype_name, manager_ids in archetypes.items():
            enriched_archetypes[archetype_name] = {
                "description": archetype_descriptions.get(archetype_name, ""),
                "manager_count": len(manager_ids),
                "manager_ids": manager_ids,
                "percentage": (len(manager_ids) / len(analytics.get("power_rankings", []))) * 100 if analytics.get("power_rankings") else 0
            }
        
        return {
            "league_id": league_id,
            "archetypes": enriched_archetypes,
            "summary": {
                "total_archetypes": len(enriched_archetypes),
                "most_common_archetype": max(enriched_archetypes.items(), key=lambda x: x[1]["manager_count"])[0] if enriched_archetypes else None,
                "archetype_diversity": len([a for a in enriched_archetypes.values() if a["manager_count"] > 0])
            }
        }
        
    except Exception as e:
        logger.error(f"Error identifying archetypes for league {league_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions
def _identify_top_metrics(metrics_dict: Dict[str, Dict], top_n: int = 3) -> List[Dict]:
    """Identify top performing metrics for a manager."""
    metric_values = []
    for metric_name, metric_data in metrics_dict.items():
        if metric_name not in ["overall_rating", "potential_rating"]:  # Exclude composite metrics
            metric_values.append({
                "metric": metric_name,
                "value": metric_data.get("value", 0),
                "grade": metric_data.get("grade", "N/A")
            })
    
    # Sort by value and return top N
    metric_values.sort(key=lambda x: x["value"], reverse=True)
    return metric_values[:top_n]


def _identify_bottom_metrics(metrics_dict: Dict[str, Dict], bottom_n: int = 2) -> List[Dict]:
    """Identify lowest performing metrics for a manager."""
    metric_values = []
    for metric_name, metric_data in metrics_dict.items():
        if metric_name not in ["overall_rating", "potential_rating"]:  # Exclude composite metrics
            metric_values.append({
                "metric": metric_name,
                "value": metric_data.get("value", 0),
                "grade": metric_data.get("grade", "N/A")
            })
    
    # Sort by value and return bottom N
    metric_values.sort(key=lambda x: x["value"])
    return metric_values[:bottom_n]


def _classify_difference(difference: float) -> str:
    """Classify the significance of a metric difference."""
    if difference < 5:
        return "negligible"
    elif difference < 15:
        return "moderate"
    elif difference < 25:
        return "significant"
    else:
        return "major"


def _calculate_closeness_score(comparison: Dict[str, Dict]) -> float:
    """Calculate how close two managers are in overall performance."""
    if not comparison:
        return 0.0
    
    total_difference = sum(comp["difference"] for comp in comparison.values())
    average_difference = total_difference / len(comparison)
    
    # Convert to closeness score (lower difference = higher closeness)
    closeness = max(0, 100 - average_difference * 2)
    return round(closeness, 1)


def _find_most_improved(rankings: List[Dict]) -> Optional[Dict]:
    """Find the most improved manager (placeholder - would need historical data)."""
    # This would require historical power rankings to compare
    # For now, return the manager with the biggest positive difference between league position and power rank
    if not rankings:
        return None
    
    biggest_overperformer = None
    biggest_improvement = 0
    
    for ranking in rankings:
        league_pos = ranking.get("league_position", 0)
        power_rank = ranking.get("power_rank", 0)
        
        if league_pos > 0 and power_rank > 0:
            improvement = league_pos - power_rank  # Positive if power rank is better
            if improvement > biggest_improvement:
                biggest_improvement = improvement
                biggest_overperformer = ranking
    
    return biggest_overperformer


def _find_biggest_surprises(rankings: List[Dict]) -> List[Dict]:
    """Find the biggest surprises (positive and negative)."""
    if not rankings:
        return []
    
    surprises = []
    
    for ranking in rankings:
        league_pos = ranking.get("league_position", 0)
        power_rank = ranking.get("power_rank", 0)
        
        if league_pos > 0 and power_rank > 0:
            difference = abs(league_pos - power_rank)
            if difference >= 3:  # Significant position difference
                surprise_type = "positive" if league_pos > power_rank else "negative"
                surprises.append({
                    **ranking,
                    "surprise_type": surprise_type,
                    "position_difference": difference
                })
    
    # Sort by difference and return top surprises
    surprises.sort(key=lambda x: x["position_difference"], reverse=True)
    return surprises[:5]