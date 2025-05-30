"""
Advanced Metrics Engine for FPL H2H Analysis

This module provides comprehensive custom metrics, league analytics, and intelligent insights
beyond basic FPL statistics.
"""

from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import asyncio
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MetricResult:
    """Container for metric calculation results."""
    value: float
    percentile: Optional[float] = None
    grade: Optional[str] = None
    description: Optional[str] = None
    trend: Optional[str] = None
    confidence: Optional[float] = None


@dataclass
class ManagerInsight:
    """Container for manager-specific insights."""
    manager_id: int
    insight_type: str
    title: str
    description: str
    priority: str  # high, medium, low
    data: Dict[str, Any]
    confidence: float


class AdvancedMetricsEngine:
    """
    Advanced metrics calculation engine providing sophisticated FPL analytics.
    """
    
    def __init__(self, live_data_service, h2h_analyzer, enhanced_h2h_analyzer=None):
        """
        Initialize the metrics engine.
        
        Args:
            live_data_service: Service for fetching FPL data
            h2h_analyzer: Core H2H analysis service
            enhanced_h2h_analyzer: Enhanced analytics service (optional)
        """
        self.live_data_service = live_data_service
        self.h2h_analyzer = h2h_analyzer
        self.enhanced_h2h_analyzer = enhanced_h2h_analyzer
        
        # Metric definitions and weights
        self.metric_weights = {
            'consistency': 0.25,
            'form': 0.20,
            'captain_success': 0.15,
            'transfer_efficiency': 0.15,
            'chip_timing': 0.10,
            'differential_impact': 0.10,
            'mental_strength': 0.05
        }
        
    async def calculate_comprehensive_metrics(
        self,
        manager_id: int,
        league_id: int,
        timeframe: str = "season"  # season, recent, all
    ) -> Dict[str, MetricResult]:
        """
        Calculate comprehensive metrics for a manager.
        
        Args:
            manager_id: Manager ID
            league_id: League ID
            timeframe: Analysis timeframe
            
        Returns:
            Dictionary of metric results
        """
        logger.info(f"Calculating comprehensive metrics for manager {manager_id}")
        
        # Gather required data
        manager_data = await self._gather_manager_data(manager_id, league_id, timeframe)
        league_data = await self._gather_league_data(league_id, timeframe)
        
        # Calculate individual metrics
        metrics = {}
        
        # Core performance metrics
        metrics['consistency'] = await self._calculate_consistency_score(manager_data, league_data)
        metrics['form'] = await self._calculate_form_score(manager_data, league_data)
        metrics['captain_success'] = await self._calculate_captain_success_rate(manager_data, league_data)
        
        # Strategic metrics
        metrics['transfer_efficiency'] = await self._calculate_transfer_efficiency(manager_data, league_data)
        metrics['chip_timing'] = await self._calculate_chip_timing_score(manager_data, league_data)
        metrics['differential_impact'] = await self._calculate_differential_impact(manager_data, league_data)
        
        # Psychological metrics
        metrics['mental_strength'] = await self._calculate_mental_strength(manager_data, league_data)
        metrics['clutch_performance'] = await self._calculate_clutch_performance(manager_data, league_data)
        
        # Advanced composite metrics
        metrics['overall_rating'] = await self._calculate_overall_rating(metrics)
        metrics['potential_rating'] = await self._calculate_potential_rating(manager_data, metrics)
        
        return metrics
    
    async def generate_manager_insights(
        self,
        manager_id: int,
        league_id: int,
        metrics: Dict[str, MetricResult]
    ) -> List[ManagerInsight]:
        """
        Generate actionable insights for a manager based on their metrics.
        
        Args:
            manager_id: Manager ID
            league_id: League ID
            metrics: Calculated metrics
            
        Returns:
            List of insights
        """
        insights = []
        manager_data = await self._gather_manager_data(manager_id, league_id, "season")
        
        # Form-based insights
        if metrics['form'].value < 40:
            insights.append(ManagerInsight(
                manager_id=manager_id,
                insight_type="performance",
                title="Poor Recent Form Detected",
                description=f"Your form score of {metrics['form'].value:.1f} suggests recent struggles. Consider reviewing your recent transfers and captain choices.",
                priority="high",
                data={"form_score": metrics['form'].value, "trend": metrics['form'].trend},
                confidence=0.85
            ))
        
        # Captain success insights
        if metrics['captain_success'].value < 60:
            insights.append(ManagerInsight(
                manager_id=manager_id,
                insight_type="strategy",
                title="Captain Selection Needs Improvement",
                description=f"Your captain success rate of {metrics['captain_success'].value:.1f}% is below average. Focus on captaining players with favorable fixtures.",
                priority="medium",
                data={"success_rate": metrics['captain_success'].value},
                confidence=0.75
            ))
        
        # Transfer efficiency insights
        if metrics['transfer_efficiency'].value < 50:
            insights.append(ManagerInsight(
                manager_id=manager_id,
                insight_type="strategy",
                title="Transfer Strategy Review Needed",
                description=f"Your transfer efficiency of {metrics['transfer_efficiency'].value:.1f}% suggests room for improvement. Consider taking fewer hits and planning transfers better.",
                priority="medium",
                data={"efficiency": metrics['transfer_efficiency'].value},
                confidence=0.80
            ))
        
        # Consistency insights
        if metrics['consistency'].value > 80:
            insights.append(ManagerInsight(
                manager_id=manager_id,
                insight_type="strength",
                title="Excellent Consistency",
                description=f"Your consistency score of {metrics['consistency'].value:.1f}% is excellent. This steady approach is serving you well.",
                priority="low",
                data={"consistency": metrics['consistency'].value},
                confidence=0.90
            ))
        
        # Mental strength insights
        if metrics['mental_strength'].value > 75:
            insights.append(ManagerInsight(
                manager_id=manager_id,
                insight_type="strength",
                title="Strong Mental Game",
                description=f"Your mental strength score of {metrics['mental_strength'].value:.1f}% indicates good resilience under pressure.",
                priority="low",
                data={"mental_strength": metrics['mental_strength'].value},
                confidence=0.70
            ))
        
        # Add custom insights based on patterns
        custom_insights = await self._generate_custom_insights(manager_id, manager_data, metrics)
        insights.extend(custom_insights)
        
        # Sort by priority and confidence
        insights.sort(key=lambda x: (
            {"high": 3, "medium": 2, "low": 1}[x.priority],
            x.confidence
        ), reverse=True)
        
        return insights[:10]  # Return top 10 insights
    
    async def calculate_league_analytics(
        self,
        league_id: int,
        timeframe: str = "season"
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive league analytics.
        
        Args:
            league_id: League ID
            timeframe: Analysis timeframe
            
        Returns:
            Dictionary of league analytics
        """
        logger.info(f"Calculating league analytics for league {league_id}")
        
        # Get league standings and all managers
        standings = await self.h2h_analyzer.get_h2h_standings(league_id)
        managers = standings.get('standings', {}).get('results', [])
        
        if not managers:
            return {"error": "No managers found in league"}
        
        # Calculate metrics for all managers
        all_metrics = {}
        for manager in managers:
            manager_id = manager.get('entry')
            if manager_id:
                try:
                    all_metrics[manager_id] = await self.calculate_comprehensive_metrics(
                        manager_id, league_id, timeframe
                    )
                except Exception as e:
                    logger.warning(f"Failed to calculate metrics for manager {manager_id}: {e}")
        
        # Calculate league-wide analytics
        analytics = {
            "league_id": league_id,
            "total_managers": len(managers),
            "metrics_calculated": len(all_metrics),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Power rankings
        analytics["power_rankings"] = self._calculate_power_rankings(managers, all_metrics)
        
        # League competitiveness
        analytics["competitiveness"] = self._calculate_league_competitiveness(managers, all_metrics)
        
        # Manager archetypes
        analytics["archetypes"] = self._identify_manager_archetypes(all_metrics)
        
        # Statistical distributions
        analytics["distributions"] = self._calculate_metric_distributions(all_metrics)
        
        # League trends
        analytics["trends"] = await self._analyze_league_trends(league_id, managers, timeframe)
        
        # Competitive analysis
        analytics["competitive_analysis"] = self._analyze_competitive_balance(managers, all_metrics)
        
        return analytics
    
    async def _gather_manager_data(
        self,
        manager_id: int,
        league_id: int,
        timeframe: str
    ) -> Dict[str, Any]:
        """Gather comprehensive manager data for analysis."""
        try:
            # Get basic manager info
            manager_info = await self.live_data_service.get_manager_info(manager_id)
            
            # Get manager history
            history = await self.live_data_service.get_manager_history(manager_id)
            
            # Get transfer history
            transfers = await self.live_data_service.get_manager_transfers(manager_id)
            
            # Get H2H matches
            h2h_matches = []
            for gw in range(1, 39):
                try:
                    matches = await self.h2h_analyzer.get_h2h_matches(league_id, gw)
                    for match in matches:
                        if (match.get('entry_1_entry') == manager_id or 
                            match.get('entry_2_entry') == manager_id):
                            h2h_matches.append(match)
                except Exception:
                    continue
            
            return {
                "manager_info": manager_info,
                "history": history,
                "transfers": transfers,
                "h2h_matches": h2h_matches,
                "timeframe": timeframe
            }
        except Exception as e:
            logger.error(f"Error gathering manager data for {manager_id}: {e}")
            return {}
    
    async def _gather_league_data(
        self,
        league_id: int,
        timeframe: str
    ) -> Dict[str, Any]:
        """Gather league-wide data for context."""
        try:
            standings = await self.h2h_analyzer.get_h2h_standings(league_id)
            return {
                "standings": standings,
                "timeframe": timeframe
            }
        except Exception as e:
            logger.error(f"Error gathering league data for {league_id}: {e}")
            return {}
    
    async def _calculate_consistency_score(
        self,
        manager_data: Dict[str, Any],
        league_data: Dict[str, Any]
    ) -> MetricResult:
        """Calculate consistency score based on point variations."""
        history = manager_data.get('history', {}).get('current', [])
        if not history:
            return MetricResult(value=0.0, description="No data available")
        
        points = [gw.get('points', 0) for gw in history]
        if len(points) < 3:
            return MetricResult(value=0.0, description="Insufficient data")
        
        # Calculate coefficient of variation (lower is more consistent)
        mean_points = statistics.mean(points)
        std_points = statistics.stdev(points)
        
        if mean_points == 0:
            cv = 100
        else:
            cv = (std_points / mean_points) * 100
        
        # Convert to 0-100 scale (lower CV = higher consistency)
        consistency_score = max(0, 100 - cv * 2)
        
        # Determine grade
        if consistency_score >= 80:
            grade = "A"
        elif consistency_score >= 65:
            grade = "B"
        elif consistency_score >= 50:
            grade = "C"
        else:
            grade = "D"
        
        # Trend analysis (last 5 vs previous 5)
        if len(points) >= 10:
            recent_cv = statistics.stdev(points[-5:]) / statistics.mean(points[-5:]) * 100
            previous_cv = statistics.stdev(points[-10:-5]) / statistics.mean(points[-10:-5]) * 100
            trend = "improving" if recent_cv < previous_cv else "declining"
        else:
            trend = "stable"
        
        return MetricResult(
            value=consistency_score,
            grade=grade,
            description=f"Based on coefficient of variation: {cv:.1f}%",
            trend=trend,
            confidence=0.85
        )
    
    async def _calculate_form_score(
        self,
        manager_data: Dict[str, Any],
        league_data: Dict[str, Any]
    ) -> MetricResult:
        """Calculate recent form score."""
        history = manager_data.get('history', {}).get('current', [])
        if not history:
            return MetricResult(value=0.0, description="No data available")
        
        # Get last 5 gameweeks
        recent_gws = history[-5:] if len(history) >= 5 else history
        
        if not recent_gws:
            return MetricResult(value=0.0, description="No recent data")
        
        # Calculate form based on points and rank changes
        form_score = 0
        weight_sum = 0
        
        for i, gw in enumerate(recent_gws):
            weight = i + 1  # More weight to recent gameweeks
            points = gw.get('points', 0)
            
            # Points contribution (0-40 scale)
            points_score = min(40, points)
            
            # Rank change contribution (if available)
            rank_score = 0
            if i > 0:
                prev_rank = recent_gws[i-1].get('rank', 0)
                curr_rank = gw.get('rank', 0)
                if prev_rank > 0 and curr_rank > 0:
                    rank_change = prev_rank - curr_rank  # Positive if rank improved
                    rank_score = max(-10, min(10, rank_change))
            
            gw_score = points_score + rank_score
            form_score += gw_score * weight
            weight_sum += weight
        
        if weight_sum > 0:
            form_score = (form_score / weight_sum) * 2  # Scale to 0-100
        
        form_score = max(0, min(100, form_score))
        
        # Determine grade and trend
        if form_score >= 80:
            grade = "A"
            trend = "excellent"
        elif form_score >= 65:
            grade = "B"
            trend = "good"
        elif form_score >= 50:
            grade = "C"
            trend = "average"
        else:
            grade = "D"
            trend = "poor"
        
        return MetricResult(
            value=form_score,
            grade=grade,
            description=f"Based on last {len(recent_gws)} gameweeks",
            trend=trend,
            confidence=0.80
        )
    
    async def _calculate_captain_success_rate(
        self,
        manager_data: Dict[str, Any],
        league_data: Dict[str, Any]
    ) -> MetricResult:
        """Calculate captain selection success rate."""
        # This would require gameweek pick data
        # For now, return a calculated estimate based on history patterns
        history = manager_data.get('history', {}).get('current', [])
        if not history:
            return MetricResult(value=0.0, description="No data available")
        
        # Estimate captain success based on points patterns
        # This is a simplified calculation - real implementation would need pick data
        total_points = sum(gw.get('points', 0) for gw in history)
        avg_points = total_points / len(history) if history else 0
        
        # Estimate success rate based on average points
        if avg_points >= 65:
            success_rate = 75
        elif avg_points >= 55:
            success_rate = 65
        elif avg_points >= 45:
            success_rate = 55
        else:
            success_rate = 45
        
        # Add some variance based on consistency
        consistency_factor = await self._calculate_consistency_score(manager_data, league_data)
        success_rate += (consistency_factor.value - 50) * 0.2
        
        success_rate = max(0, min(100, success_rate))
        
        return MetricResult(
            value=success_rate,
            description="Estimated based on scoring patterns",
            confidence=0.60  # Lower confidence due to estimation
        )
    
    async def _calculate_transfer_efficiency(
        self,
        manager_data: Dict[str, Any],
        league_data: Dict[str, Any]
    ) -> MetricResult:
        """Calculate transfer efficiency score."""
        transfers = manager_data.get('transfers', [])
        history = manager_data.get('history', {}).get('current', [])
        
        if not transfers or not history:
            return MetricResult(value=50.0, description="No transfer data available")
        
        # Calculate transfer metrics
        total_transfers = len(transfers)
        total_hits = sum(1 for t in transfers if t.get('event_transfers_cost', 0) > 0)
        
        if total_transfers == 0:
            return MetricResult(value=50.0, description="No transfers made")
        
        # Hit ratio (fewer hits is better)
        hit_ratio = total_hits / total_transfers
        hit_score = max(0, (1 - hit_ratio) * 50)
        
        # Timing score (transfers early in gameweek are better)
        # This would need more detailed timestamp data
        timing_score = 25  # Default average score
        
        # Overall efficiency
        efficiency = hit_score + timing_score
        efficiency = max(0, min(100, efficiency))
        
        return MetricResult(
            value=efficiency,
            description=f"Based on {total_transfers} transfers, {total_hits} hits",
            confidence=0.70
        )
    
    async def _calculate_chip_timing_score(
        self,
        manager_data: Dict[str, Any],
        league_data: Dict[str, Any]
    ) -> MetricResult:
        """Calculate chip timing effectiveness."""
        history = manager_data.get('history', {})
        chips = history.get('chips', [])
        
        if not chips:
            return MetricResult(value=50.0, description="No chips used yet")
        
        # Analyze chip timing
        chip_scores = []
        
        for chip in chips:
            chip_gw = chip.get('event', 0)
            chip_name = chip.get('name', '').lower()
            
            # Get points for that gameweek
            gw_data = next((gw for gw in history.get('current', []) if gw.get('event') == chip_gw), None)
            if not gw_data:
                continue
            
            points = gw_data.get('points', 0)
            
            # Score based on chip type and timing
            if chip_name in ['wildcard', 'freehit']:
                # These should ideally be used for high-scoring weeks
                if points >= 70:
                    score = 90
                elif points >= 60:
                    score = 75
                elif points >= 50:
                    score = 60
                else:
                    score = 40
            elif chip_name in ['3xc', 'triple_captain']:
                # Triple captain should score very high
                if points >= 80:
                    score = 95
                elif points >= 70:
                    score = 80
                elif points >= 60:
                    score = 65
                else:
                    score = 30
            else:
                score = 60  # Default for other chips
            
            chip_scores.append(score)
        
        if not chip_scores:
            return MetricResult(value=50.0, description="No scorable chips")
        
        avg_score = statistics.mean(chip_scores)
        
        return MetricResult(
            value=avg_score,
            description=f"Based on {len(chip_scores)} chips used",
            confidence=0.75
        )
    
    async def _calculate_differential_impact(
        self,
        manager_data: Dict[str, Any],
        league_data: Dict[str, Any]
    ) -> MetricResult:
        """Calculate impact of differential player selections."""
        # This would require detailed squad data and ownership information
        # For now, return an estimate based on performance variance
        
        history = manager_data.get('history', {}).get('current', [])
        if not history:
            return MetricResult(value=50.0, description="No data available")
        
        points = [gw.get('points', 0) for gw in history]
        
        # High variance might indicate good differential picks
        if len(points) < 3:
            return MetricResult(value=50.0, description="Insufficient data")
        
        variance = statistics.variance(points)
        mean_points = statistics.mean(points)
        
        # Normalize variance score
        if mean_points > 0:
            variance_ratio = variance / mean_points
            differential_score = min(100, variance_ratio * 10)
        else:
            differential_score = 50
        
        return MetricResult(
            value=differential_score,
            description="Estimated from performance variance",
            confidence=0.50
        )
    
    async def _calculate_mental_strength(
        self,
        manager_data: Dict[str, Any],
        league_data: Dict[str, Any]
    ) -> MetricResult:
        """Calculate mental strength and resilience."""
        h2h_matches = manager_data.get('h2h_matches', [])
        history = manager_data.get('history', {}).get('current', [])
        
        if not h2h_matches or not history:
            return MetricResult(value=50.0, description="No data available")
        
        # Analyze comeback ability and performance under pressure
        mental_score = 50  # Base score
        
        # Factor 1: Recovery after bad gameweeks
        recovery_scores = []
        for i in range(1, len(history)):
            prev_gw = history[i-1]
            curr_gw = history[i]
            
            prev_points = prev_gw.get('points', 0)
            curr_points = curr_gw.get('points', 0)
            
            # If previous week was bad (< 35 points), check recovery
            if prev_points < 35:
                if curr_points >= 50:
                    recovery_scores.append(80)  # Good recovery
                elif curr_points >= 40:
                    recovery_scores.append(60)  # Decent recovery
                else:
                    recovery_scores.append(30)  # Poor recovery
        
        if recovery_scores:
            mental_score += (statistics.mean(recovery_scores) - 50) * 0.3
        
        # Factor 2: Performance in close H2H matches
        close_match_performance = []
        for match in h2h_matches:
            entry1_points = match.get('entry_1_points', 0)
            entry2_points = match.get('entry_2_points', 0)
            margin = abs(entry1_points - entry2_points)
            
            # Close match (within 10 points)
            if margin <= 10:
                # Check if this manager won
                manager_id = manager_data.get('manager_info', {}).get('id')
                if manager_id:
                    if ((match.get('entry_1_entry') == manager_id and entry1_points > entry2_points) or
                        (match.get('entry_2_entry') == manager_id and entry2_points > entry1_points)):
                        close_match_performance.append(70)  # Won close match
                    else:
                        close_match_performance.append(40)  # Lost close match
        
        if close_match_performance:
            mental_score += (statistics.mean(close_match_performance) - 50) * 0.4
        
        mental_score = max(0, min(100, mental_score))
        
        return MetricResult(
            value=mental_score,
            description=f"Based on {len(recovery_scores)} recovery situations and {len(close_match_performance)} close matches",
            confidence=0.65
        )
    
    async def _calculate_clutch_performance(
        self,
        manager_data: Dict[str, Any],
        league_data: Dict[str, Any]
    ) -> MetricResult:
        """Calculate performance in high-pressure situations."""
        history = manager_data.get('history', {}).get('current', [])
        
        if not history:
            return MetricResult(value=50.0, description="No data available")
        
        # Identify high-pressure gameweeks (end of season, big rank changes)
        clutch_performances = []
        
        for i, gw in enumerate(history):
            is_clutch = False
            
            # End of season pressure (last 5 gameweeks)
            if i >= len(history) - 5:
                is_clutch = True
            
            # Big rank movements
            if i > 0:
                prev_rank = history[i-1].get('rank', 0)
                curr_rank = gw.get('rank', 0)
                if abs(prev_rank - curr_rank) > 5:  # Significant rank change
                    is_clutch = True
            
            if is_clutch:
                points = gw.get('points', 0)
                if points >= 60:
                    clutch_performances.append(80)
                elif points >= 50:
                    clutch_performances.append(65)
                elif points >= 40:
                    clutch_performances.append(50)
                else:
                    clutch_performances.append(30)
        
        if not clutch_performances:
            return MetricResult(value=50.0, description="No clutch situations identified")
        
        clutch_score = statistics.mean(clutch_performances)
        
        return MetricResult(
            value=clutch_score,
            description=f"Based on {len(clutch_performances)} high-pressure gameweeks",
            confidence=0.70
        )
    
    async def _calculate_overall_rating(
        self,
        metrics: Dict[str, MetricResult]
    ) -> MetricResult:
        """Calculate weighted overall rating."""
        total_score = 0
        total_weight = 0
        
        for metric_name, weight in self.metric_weights.items():
            if metric_name in metrics:
                total_score += metrics[metric_name].value * weight
                total_weight += weight
        
        if total_weight == 0:
            return MetricResult(value=50.0, description="No metrics available")
        
        overall_score = total_score / total_weight
        
        # Determine grade
        if overall_score >= 85:
            grade = "A+"
        elif overall_score >= 80:
            grade = "A"
        elif overall_score >= 75:
            grade = "A-"
        elif overall_score >= 70:
            grade = "B+"
        elif overall_score >= 65:
            grade = "B"
        elif overall_score >= 60:
            grade = "B-"
        elif overall_score >= 55:
            grade = "C+"
        elif overall_score >= 50:
            grade = "C"
        else:
            grade = "D"
        
        return MetricResult(
            value=overall_score,
            grade=grade,
            description="Weighted composite of all metrics",
            confidence=0.85
        )
    
    async def _calculate_potential_rating(
        self,
        manager_data: Dict[str, Any],
        metrics: Dict[str, MetricResult]
    ) -> MetricResult:
        """Calculate potential ceiling rating."""
        # Base potential on best performances and positive trends
        history = manager_data.get('history', {}).get('current', [])
        
        if not history:
            return MetricResult(value=50.0, description="No data available")
        
        # Find peak performance periods
        points = [gw.get('points', 0) for gw in history]
        
        if len(points) < 5:
            return MetricResult(value=metrics.get('overall_rating', MetricResult(50)).value)
        
        # Calculate potential based on top 25% of performances
        top_quartile = sorted(points, reverse=True)[:len(points)//4]
        peak_performance = statistics.mean(top_quartile) if top_quartile else 50
        
        # Adjust based on trends
        consistency = metrics.get('consistency', MetricResult(50)).value
        form = metrics.get('form', MetricResult(50)).value
        
        # Higher consistency suggests more reliable potential
        # Good form suggests current potential
        potential = (peak_performance * 0.6 + consistency * 0.2 + form * 0.2)
        potential = max(0, min(100, potential))
        
        return MetricResult(
            value=potential,
            description=f"Based on top performances (avg: {peak_performance:.1f})",
            confidence=0.75
        )
    
    def _calculate_power_rankings(
        self,
        managers: List[Dict],
        all_metrics: Dict[int, Dict[str, MetricResult]]
    ) -> List[Dict[str, Any]]:
        """Calculate power rankings based on advanced metrics."""
        rankings = []
        
        for manager in managers:
            manager_id = manager.get('entry')
            if manager_id in all_metrics:
                metrics = all_metrics[manager_id]
                overall_rating = metrics.get('overall_rating', MetricResult(50))
                
                rankings.append({
                    "manager_id": manager_id,
                    "player_name": manager.get('player_name', 'Unknown'),
                    "entry_name": manager.get('entry_name', 'Unknown'),
                    "power_rating": overall_rating.value,
                    "grade": overall_rating.grade,
                    "league_position": manager.get('rank', 0),
                    "total_points": manager.get('total', 0)
                })
        
        # Sort by power rating
        rankings.sort(key=lambda x: x['power_rating'], reverse=True)
        
        # Add power rank
        for i, ranking in enumerate(rankings):
            ranking['power_rank'] = i + 1
        
        return rankings
    
    def _calculate_league_competitiveness(
        self,
        managers: List[Dict],
        all_metrics: Dict[int, Dict[str, MetricResult]]
    ) -> Dict[str, Any]:
        """Calculate league competitiveness metrics."""
        if not managers:
            return {"competitiveness_score": 0, "description": "No data"}
        
        # Points spread
        points = [m.get('total', 0) for m in managers]
        points_range = max(points) - min(points) if points else 0
        points_std = statistics.stdev(points) if len(points) > 1 else 0
        
        # Power rating spread
        power_ratings = []
        for manager in managers:
            manager_id = manager.get('entry')
            if manager_id in all_metrics:
                power_rating = all_metrics[manager_id].get('overall_rating', MetricResult(50)).value
                power_ratings.append(power_rating)
        
        power_range = max(power_ratings) - min(power_ratings) if power_ratings else 0
        power_std = statistics.stdev(power_ratings) if len(power_ratings) > 1 else 0
        
        # Calculate competitiveness (lower spread = more competitive)
        max_possible_points = 38 * 100  # Theoretical maximum
        points_competitiveness = max(0, 100 - (points_range / max_possible_points * 100))
        power_competitiveness = max(0, 100 - power_range)
        
        overall_competitiveness = (points_competitiveness + power_competitiveness) / 2
        
        if overall_competitiveness >= 80:
            description = "Highly competitive league"
        elif overall_competitiveness >= 60:
            description = "Moderately competitive league"
        else:
            description = "Low competition league"
        
        return {
            "competitiveness_score": overall_competitiveness,
            "points_range": points_range,
            "power_rating_range": power_range,
            "description": description
        }
    
    def _identify_manager_archetypes(
        self,
        all_metrics: Dict[int, Dict[str, MetricResult]]
    ) -> Dict[str, List[int]]:
        """Identify manager playing styles/archetypes."""
        archetypes = {
            "consistent_performer": [],
            "high_risk_high_reward": [],
            "steady_eddie": [],
            "comeback_kid": [],
            "clutch_player": [],
            "transfer_master": [],
            "captain_genius": []
        }
        
        for manager_id, metrics in all_metrics.items():
            consistency = metrics.get('consistency', MetricResult(50)).value
            form = metrics.get('form', MetricResult(50)).value
            mental_strength = metrics.get('mental_strength', MetricResult(50)).value
            clutch = metrics.get('clutch_performance', MetricResult(50)).value
            transfer_eff = metrics.get('transfer_efficiency', MetricResult(50)).value
            captain_success = metrics.get('captain_success', MetricResult(50)).value
            differential = metrics.get('differential_impact', MetricResult(50)).value
            
            # Classify based on metric combinations
            if consistency >= 75:
                archetypes["consistent_performer"].append(manager_id)
            
            if differential >= 65 and form >= 60:
                archetypes["high_risk_high_reward"].append(manager_id)
            
            if consistency >= 65 and transfer_eff >= 60 and captain_success >= 60:
                archetypes["steady_eddie"].append(manager_id)
            
            if mental_strength >= 70:
                archetypes["comeback_kid"].append(manager_id)
            
            if clutch >= 70:
                archetypes["clutch_player"].append(manager_id)
            
            if transfer_eff >= 75:
                archetypes["transfer_master"].append(manager_id)
            
            if captain_success >= 75:
                archetypes["captain_genius"].append(manager_id)
        
        return archetypes
    
    def _calculate_metric_distributions(
        self,
        all_metrics: Dict[int, Dict[str, MetricResult]]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate statistical distributions of metrics."""
        distributions = {}
        
        metric_names = ['consistency', 'form', 'captain_success', 'transfer_efficiency', 
                       'mental_strength', 'overall_rating']
        
        for metric_name in metric_names:
            values = []
            for metrics in all_metrics.values():
                if metric_name in metrics:
                    values.append(metrics[metric_name].value)
            
            if values:
                distributions[metric_name] = {
                    "mean": statistics.mean(values),
                    "median": statistics.median(values),
                    "std": statistics.stdev(values) if len(values) > 1 else 0,
                    "min": min(values),
                    "max": max(values),
                    "q25": statistics.quantiles(values, n=4)[0] if len(values) >= 4 else min(values),
                    "q75": statistics.quantiles(values, n=4)[2] if len(values) >= 4 else max(values)
                }
        
        return distributions
    
    async def _analyze_league_trends(
        self,
        league_id: int,
        managers: List[Dict],
        timeframe: str
    ) -> Dict[str, Any]:
        """Analyze league-wide trends over time."""
        # This would analyze trends like:
        # - Average points progression
        # - Transfer activity trends
        # - Competitive balance changes
        # - Form patterns
        
        # Simplified implementation
        return {
            "trend_analysis": "In development",
            "average_points_trend": "stable",
            "competitive_balance_trend": "improving",
            "transfer_activity_trend": "increasing"
        }
    
    def _analyze_competitive_balance(
        self,
        managers: List[Dict],
        all_metrics: Dict[int, Dict[str, MetricResult]]
    ) -> Dict[str, Any]:
        """Analyze competitive balance in the league."""
        if len(managers) < 4:
            return {"balance_score": 50, "description": "Too few managers"}
        
        # Calculate Gini coefficient for points distribution
        points = sorted([m.get('total', 0) for m in managers])
        n = len(points)
        
        if n == 0:
            return {"balance_score": 0, "description": "No data"}
        
        # Gini coefficient calculation
        numerator = sum((i + 1) * points[i] for i in range(n))
        denominator = n * sum(points)
        
        if denominator == 0:
            gini = 0
        else:
            gini = (2 * numerator / denominator) - (n + 1) / n
        
        # Convert to balance score (0 = perfect equality, 1 = maximum inequality)
        balance_score = (1 - gini) * 100
        
        if balance_score >= 80:
            description = "Highly balanced competition"
        elif balance_score >= 60:
            description = "Moderately balanced"
        else:
            description = "Unbalanced competition"
        
        return {
            "balance_score": balance_score,
            "gini_coefficient": gini,
            "description": description
        }
    
    async def _generate_custom_insights(
        self,
        manager_id: int,
        manager_data: Dict[str, Any],
        metrics: Dict[str, MetricResult]
    ) -> List[ManagerInsight]:
        """Generate custom insights based on data patterns."""
        insights = []
        history = manager_data.get('history', {}).get('current', [])
        
        if not history:
            return insights
        
        # Pattern 1: Strong finisher
        if len(history) >= 10:
            early_avg = statistics.mean([gw.get('points', 0) for gw in history[:5]])
            late_avg = statistics.mean([gw.get('points', 0) for gw in history[-5:]])
            
            if late_avg > early_avg + 5:
                insights.append(ManagerInsight(
                    manager_id=manager_id,
                    insight_type="pattern",
                    title="Strong Season Finisher",
                    description=f"Your performance has improved significantly as the season progressed. Late season average: {late_avg:.1f} vs early: {early_avg:.1f}",
                    priority="medium",
                    data={"early_avg": early_avg, "late_avg": late_avg},
                    confidence=0.80
                ))
        
        # Pattern 2: Streaky performer
        points = [gw.get('points', 0) for gw in history]
        if len(points) >= 6:
            # Look for consecutive high/low scoring periods
            streaks = []
            current_streak = 1
            for i in range(1, len(points)):
                if (points[i] >= 55) == (points[i-1] >= 55):  # Same category (high/low)
                    current_streak += 1
                else:
                    streaks.append(current_streak)
                    current_streak = 1
            streaks.append(current_streak)
            
            max_streak = max(streaks)
            if max_streak >= 4:
                insights.append(ManagerInsight(
                    manager_id=manager_id,
                    insight_type="pattern",
                    title="Streaky Performance Pattern",
                    description=f"You tend to have hot and cold streaks. Longest streak: {max_streak} gameweeks",
                    priority="low",
                    data={"max_streak": max_streak, "avg_streak": statistics.mean(streaks)},
                    confidence=0.70
                ))
        
        return insights