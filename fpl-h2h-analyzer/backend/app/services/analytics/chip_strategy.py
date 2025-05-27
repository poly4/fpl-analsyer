"""
Chip Strategy Analyzer
Analyzes optimal chip timing and historical chip success
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import statistics

logger = logging.getLogger(__name__)


@dataclass
class ChipRecommendation:
    """Recommendation for chip usage"""
    chip_name: str
    recommended_gameweek: int
    confidence: float  # 0-1
    reasoning: List[str]
    expected_benefit: float  # Expected points gain
    risk_level: str  # 'low', 'medium', 'high'
    h2h_context: Dict[str, Any]


@dataclass
class ChipAnalysis:
    """Analysis of a chip's usage"""
    chip_name: str
    gameweek_used: int
    points_gained: float  # Actual or estimated
    success_rating: float  # 0-10
    timing_quality: str  # 'perfect', 'good', 'suboptimal', 'poor'
    h2h_impact: str  # 'won', 'lost', 'no_impact'


@dataclass
class ChipStrategy:
    """Overall chip strategy profile"""
    chips_used: List[str]
    chips_remaining: List[str]
    
    # Historical performance
    avg_chip_success: float
    best_chip_usage: Optional[ChipAnalysis]
    worst_chip_usage: Optional[ChipAnalysis]
    
    # Strategy patterns
    preferred_timing: str  # 'early', 'mid', 'late', 'reactive'
    planning_quality: float  # 0-10
    h2h_chip_success_rate: float  # Win rate when using chips


class ChipStrategyAnalyzer:
    """
    Analyzes chip usage strategies and provides recommendations
    """
    
    def __init__(self):
        self.all_chips = ['wildcard', 'bboost', 'freehit', '3xc']
        self.chip_limits = {
            'wildcard': 2,  # Can use twice
            'bboost': 1,
            'freehit': 1,
            '3xc': 1
        }
        
        # Optimal timing windows
        self.optimal_windows = {
            'wildcard': [(4, 8), (20, 30)],  # Early season, mid-season
            'bboost': [(35, 38)],  # DGWs typically late
            'freehit': [(18, 18), (29, 33)],  # Blank GWs
            '3xc': [(36, 38)]  # Late season doubles
        }
    
    async def analyze_chip_strategy(
        self,
        manager_id: int,
        manager_history: Dict[str, Any],
        fixtures: List[Dict[str, Any]],
        current_gameweek: int,
        h2h_history: Optional[List[Dict[str, Any]]] = None,
        bootstrap_data: Optional[Dict[str, Any]] = None,
        opponent_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive chip strategy analysis
        """
        try:
            # Get chips used
            chips_used = manager_history.get('chips', [])
            
            # Analyze historical chip usage
            chip_analyses = []
            for chip in chips_used:
                analysis = await self._analyze_chip_usage(
                    chip, manager_history, h2h_history
                )
                if analysis:
                    chip_analyses.append(analysis)
            
            # Calculate strategy profile
            strategy = await self._calculate_strategy_profile(
                chips_used, chip_analyses, h2h_history
            )
            
            # Get remaining chips
            remaining_chips = self._get_remaining_chips(chips_used)
            
            # Generate recommendations
            recommendations = await self._generate_chip_recommendations(
                remaining_chips, current_gameweek, fixtures,
                manager_history, h2h_history, bootstrap_data,
                opponent_data
            )
            
            # Analyze upcoming opportunities
            opportunities = await self._analyze_upcoming_opportunities(
                remaining_chips, fixtures, current_gameweek
            )
            
            # Compare to optimal strategy
            comparison = await self._compare_to_optimal_strategy(
                chip_analyses, current_gameweek
            )
            
            return {
                "strategy_profile": self._serialize_strategy(strategy),
                "historical_usage": [
                    self._serialize_chip_analysis(ca) for ca in chip_analyses
                ],
                "remaining_chips": remaining_chips,
                "recommendations": [
                    self._serialize_recommendation(r) for r in recommendations
                ],
                "upcoming_opportunities": opportunities,
                "optimal_comparison": comparison,
                "insights": await self._generate_insights(
                    strategy, chip_analyses, recommendations
                )
            }
            
        except Exception as e:
            logger.error(f"Error analyzing chip strategy: {e}")
            return {}
    
    async def _analyze_chip_usage(
        self,
        chip: Dict[str, Any],
        manager_history: Dict[str, Any],
        h2h_history: Optional[List[Dict[str, Any]]]
    ) -> Optional[ChipAnalysis]:
        """Analyze a single chip usage"""
        try:
            chip_name = chip['name']
            gameweek_used = chip['event']
            
            # Get gameweek data
            gw_data = next(
                (gw for gw in manager_history.get('current', [])
                 if gw['event'] == gameweek_used),
                None
            )
            
            if not gw_data:
                return None
            
            # Estimate points gained (simplified)
            # In reality, would need detailed analysis
            avg_score = statistics.mean([
                gw['points'] for gw in manager_history.get('current', [])
            ]) if manager_history.get('current') else 50
            
            points_gained = gw_data['points'] - avg_score
            
            # Chip-specific adjustments
            if chip_name == 'bboost':
                # Bench boost benefit is bench score
                bench_points = gw_data.get('points_on_bench', 0)
                points_gained = bench_points
            elif chip_name == '3xc':
                # Triple captain benefit is 2x captain score
                # Estimate captain got 10 points
                points_gained = 20  # Simplified
            elif chip_name == 'wildcard':
                # Wildcard benefit is harder to measure
                # Look at next few gameweeks
                future_gws = [
                    gw for gw in manager_history.get('current', [])
                    if gameweek_used < gw['event'] <= gameweek_used + 5
                ]
                if future_gws:
                    future_avg = statistics.mean([gw['points'] for gw in future_gws])
                    points_gained = (future_avg - avg_score) * 3  # 3 GW benefit
            
            # Success rating
            success_rating = self._calculate_chip_success(
                chip_name, points_gained, gameweek_used
            )
            
            # Timing quality
            timing_quality = self._assess_chip_timing(
                chip_name, gameweek_used
            )
            
            # H2H impact
            h2h_impact = 'no_impact'
            if h2h_history:
                h2h_match = next(
                    (m for m in h2h_history if m['event'] == gameweek_used),
                    None
                )
                if h2h_match:
                    won = h2h_match.get('points_winner') == h2h_match.get('entry_1_entry')
                    h2h_impact = 'won' if won else 'lost'
            
            return ChipAnalysis(
                chip_name=chip_name,
                gameweek_used=gameweek_used,
                points_gained=points_gained,
                success_rating=success_rating,
                timing_quality=timing_quality,
                h2h_impact=h2h_impact
            )
            
        except Exception as e:
            logger.error(f"Error analyzing chip usage: {e}")
            return None
    
    def _calculate_chip_success(
        self,
        chip_name: str,
        points_gained: float,
        gameweek: int
    ) -> float:
        """Calculate chip success rating 0-10"""
        # Base thresholds by chip type
        thresholds = {
            'bboost': {'excellent': 20, 'good': 12, 'average': 6},
            '3xc': {'excellent': 30, 'good': 20, 'average': 10},
            'freehit': {'excellent': 15, 'good': 8, 'average': 0},
            'wildcard': {'excellent': 20, 'good': 10, 'average': 0}
        }
        
        chip_thresholds = thresholds.get(chip_name, thresholds['freehit'])
        
        if points_gained >= chip_thresholds['excellent']:
            base_rating = 8.5
        elif points_gained >= chip_thresholds['good']:
            base_rating = 6.5
        elif points_gained >= chip_thresholds['average']:
            base_rating = 4.5
        else:
            base_rating = 2.5
        
        # Adjust for timing
        timing_bonus = 1.0 if self._assess_chip_timing(chip_name, gameweek) in ['perfect', 'good'] else 0
        
        return min(10, base_rating + timing_bonus)
    
    def _assess_chip_timing(self, chip_name: str, gameweek: int) -> str:
        """Assess the timing quality of chip usage"""
        optimal_windows = self.optimal_windows.get(chip_name, [])
        
        for window in optimal_windows:
            if window[0] <= gameweek <= window[1]:
                return 'perfect'
        
        # Check if close to optimal
        for window in optimal_windows:
            if abs(gameweek - window[0]) <= 2 or abs(gameweek - window[1]) <= 2:
                return 'good'
        
        # Check if reasonable
        if chip_name == 'wildcard' and gameweek in [1, 2, 19, 20]:
            return 'good'
        elif chip_name == 'bboost' and gameweek > 30:
            return 'suboptimal'
        
        return 'poor'
    
    async def _calculate_strategy_profile(
        self,
        chips_used: List[Dict[str, Any]],
        chip_analyses: List[ChipAnalysis],
        h2h_history: Optional[List[Dict[str, Any]]]
    ) -> ChipStrategy:
        """Calculate overall chip strategy profile"""
        if not chip_analyses:
            return ChipStrategy(
                chips_used=[],
                chips_remaining=list(self.all_chips),
                avg_chip_success=0,
                best_chip_usage=None,
                worst_chip_usage=None,
                preferred_timing='none',
                planning_quality=5.0,
                h2h_chip_success_rate=0
            )
        
        # Average success
        avg_success = statistics.mean([ca.success_rating for ca in chip_analyses])
        
        # Best and worst
        best_chip = max(chip_analyses, key=lambda x: x.success_rating)
        worst_chip = min(chip_analyses, key=lambda x: x.success_rating)
        
        # Timing preference
        gameweeks_used = [ca.gameweek_used for ca in chip_analyses]
        avg_gw = statistics.mean(gameweeks_used)
        
        if avg_gw <= 10:
            preferred_timing = 'early'
        elif avg_gw <= 25:
            preferred_timing = 'mid'
        elif avg_gw <= 35:
            preferred_timing = 'late'
        else:
            preferred_timing = 'very_late'
        
        # Check if reactive (poor timing)
        poor_timing_count = sum(1 for ca in chip_analyses if ca.timing_quality == 'poor')
        if poor_timing_count > len(chip_analyses) / 2:
            preferred_timing = 'reactive'
        
        # Planning quality
        timing_scores = {
            'perfect': 10,
            'good': 7,
            'suboptimal': 4,
            'poor': 1
        }
        
        planning_quality = statistics.mean([
            timing_scores.get(ca.timing_quality, 5)
            for ca in chip_analyses
        ]) if chip_analyses else 5.0
        
        # H2H success rate
        h2h_wins = sum(1 for ca in chip_analyses if ca.h2h_impact == 'won')
        h2h_total = sum(1 for ca in chip_analyses if ca.h2h_impact in ['won', 'lost'])
        h2h_success_rate = h2h_wins / h2h_total if h2h_total > 0 else 0
        
        return ChipStrategy(
            chips_used=[c['name'] for c in chips_used],
            chips_remaining=self._get_remaining_chips(chips_used),
            avg_chip_success=avg_success,
            best_chip_usage=best_chip,
            worst_chip_usage=worst_chip,
            preferred_timing=preferred_timing,
            planning_quality=planning_quality,
            h2h_chip_success_rate=h2h_success_rate
        )
    
    def _get_remaining_chips(self, chips_used: List[Dict[str, Any]]) -> List[str]:
        """Get list of remaining chips"""
        used_counts = {}
        for chip in chips_used:
            name = chip['name']
            used_counts[name] = used_counts.get(name, 0) + 1
        
        remaining = []
        for chip_name, limit in self.chip_limits.items():
            used = used_counts.get(chip_name, 0)
            if used < limit:
                remaining.extend([chip_name] * (limit - used))
        
        return remaining
    
    async def _generate_chip_recommendations(
        self,
        remaining_chips: List[str],
        current_gameweek: int,
        fixtures: List[Dict[str, Any]],
        manager_history: Dict[str, Any],
        h2h_history: Optional[List[Dict[str, Any]]],
        bootstrap_data: Optional[Dict[str, Any]],
        opponent_data: Optional[Dict[str, Any]]
    ) -> List[ChipRecommendation]:
        """Generate recommendations for chip usage"""
        recommendations = []
        
        for chip in set(remaining_chips):
            if chip == 'wildcard':
                rec = await self._recommend_wildcard(
                    current_gameweek, fixtures, manager_history
                )
            elif chip == 'bboost':
                rec = await self._recommend_bench_boost(
                    current_gameweek, fixtures, bootstrap_data
                )
            elif chip == 'freehit':
                rec = await self._recommend_free_hit(
                    current_gameweek, fixtures
                )
            elif chip == '3xc':
                rec = await self._recommend_triple_captain(
                    current_gameweek, fixtures, bootstrap_data
                )
            else:
                continue
            
            if rec:
                # Add H2H context
                rec.h2h_context = await self._get_h2h_context(
                    current_gameweek, h2h_history, opponent_data
                )
                recommendations.append(rec)
        
        # Sort by confidence
        recommendations.sort(key=lambda x: x.confidence, reverse=True)
        
        return recommendations
    
    async def _recommend_wildcard(
        self,
        current_gameweek: int,
        fixtures: List[Dict[str, Any]],
        manager_history: Dict[str, Any]
    ) -> Optional[ChipRecommendation]:
        """Generate wildcard recommendation"""
        # Check if in optimal window
        in_window = any(
            w[0] <= current_gameweek <= w[1]
            for w in self.optimal_windows['wildcard']
        )
        
        confidence = 0.5
        reasoning = []
        recommended_gw = current_gameweek
        
        # Check team issues (would need more data)
        recent_scores = [
            gw['points'] for gw in manager_history.get('current', [])[-5:]
        ]
        if recent_scores:
            avg_recent = statistics.mean(recent_scores)
            if avg_recent < 40:
                confidence += 0.2
                reasoning.append("Recent poor performance")
        
        # Check fixture swings
        if current_gameweek in [4, 5, 6]:
            confidence += 0.2
            reasoning.append("Early season template emerging")
        elif current_gameweek in [19, 20]:
            confidence += 0.1
            reasoning.append("Mid-season fixture swing")
        
        if not reasoning:
            reasoning.append("Save for better opportunity")
            confidence = 0.2
        
        return ChipRecommendation(
            chip_name='wildcard',
            recommended_gameweek=recommended_gw,
            confidence=confidence,
            reasoning=reasoning,
            expected_benefit=15.0,  # Estimate
            risk_level='medium',
            h2h_context={}
        )
    
    async def _recommend_bench_boost(
        self,
        current_gameweek: int,
        fixtures: List[Dict[str, Any]],
        bootstrap_data: Optional[Dict[str, Any]]
    ) -> Optional[ChipRecommendation]:
        """Generate bench boost recommendation"""
        confidence = 0.3
        reasoning = []
        
        # Check for double gameweeks
        # Simplified - would need actual DGW data
        if current_gameweek >= 35:
            confidence += 0.4
            reasoning.append("Potential double gameweek")
        
        # Check bench strength (would need current team data)
        if current_gameweek < 30:
            confidence = 0.2
            reasoning = ["Save for double gameweek"]
        
        return ChipRecommendation(
            chip_name='bboost',
            recommended_gameweek=37,  # Typical DGW
            confidence=confidence,
            reasoning=reasoning,
            expected_benefit=18.0,
            risk_level='low' if confidence > 0.6 else 'medium',
            h2h_context={}
        )
    
    async def _recommend_free_hit(
        self,
        current_gameweek: int,
        fixtures: List[Dict[str, Any]]
    ) -> Optional[ChipRecommendation]:
        """Generate free hit recommendation"""
        confidence = 0.3
        reasoning = []
        
        # Check for blank gameweeks
        # Simplified - would need actual BGW data
        if current_gameweek in [18, 29, 30, 31]:
            confidence += 0.5
            reasoning.append("Blank gameweek opportunity")
        
        # Check for extreme fixture swing
        # Would need to analyze fixtures properly
        
        if not reasoning:
            reasoning = ["Save for blank gameweek"]
            confidence = 0.2
        
        return ChipRecommendation(
            chip_name='freehit',
            recommended_gameweek=29,  # Typical BGW
            confidence=confidence,
            reasoning=reasoning,
            expected_benefit=12.0,
            risk_level='medium',
            h2h_context={}
        )
    
    async def _recommend_triple_captain(
        self,
        current_gameweek: int,
        fixtures: List[Dict[str, Any]],
        bootstrap_data: Optional[Dict[str, Any]]
    ) -> Optional[ChipRecommendation]:
        """Generate triple captain recommendation"""
        confidence = 0.3
        reasoning = []
        
        # Check for double gameweeks
        if current_gameweek >= 36:
            confidence += 0.4
            reasoning.append("Double gameweek for premiums")
        
        # Check for standout fixtures
        # Would need to identify premium players with great fixtures
        
        if current_gameweek < 30:
            confidence = 0.2
            reasoning = ["Save for double gameweek"]
        
        return ChipRecommendation(
            chip_name='3xc',
            recommended_gameweek=37,
            confidence=confidence,
            reasoning=reasoning,
            expected_benefit=25.0,  # Assuming 15-point captain
            risk_level='high',  # High variance
            h2h_context={}
        )
    
    async def _get_h2h_context(
        self,
        current_gameweek: int,
        h2h_history: Optional[List[Dict[str, Any]]],
        opponent_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get H2H context for chip decisions"""
        context = {
            'current_position': 'unknown',
            'games_behind': 0,
            'opponent_chips': [],
            'must_win': False
        }
        
        if not h2h_history:
            return context
        
        # Calculate current standings
        wins = sum(1 for m in h2h_history if m.get('points_winner') == m.get('entry_1_entry'))
        losses = sum(1 for m in h2h_history if m.get('points_winner') == m.get('entry_2_entry'))
        
        if wins > losses:
            context['current_position'] = 'leading'
        elif losses > wins:
            context['current_position'] = 'trailing'
            context['games_behind'] = losses - wins
        else:
            context['current_position'] = 'tied'
        
        # Check if late season must-win
        remaining_games = 38 - current_gameweek
        if context['games_behind'] >= remaining_games - 2:
            context['must_win'] = True
        
        # Get opponent chips if available
        if opponent_data:
            context['opponent_chips'] = [
                c['name'] for c in opponent_data.get('chips', [])
            ]
        
        return context
    
    async def _analyze_upcoming_opportunities(
        self,
        remaining_chips: List[str],
        fixtures: List[Dict[str, Any]],
        current_gameweek: int
    ) -> List[Dict[str, Any]]:
        """Analyze upcoming opportunities for chip usage"""
        opportunities = []
        
        # Check next 10 gameweeks
        for gw in range(current_gameweek, min(39, current_gameweek + 10)):
            gw_opportunities = []
            
            # Check for DGW/BGW (simplified)
            if gw in [29, 30, 31]:
                gw_opportunities.append({
                    'type': 'blank_gameweek',
                    'suitable_chips': ['freehit'],
                    'confidence': 0.8
                })
            elif gw in [35, 36, 37]:
                gw_opportunities.append({
                    'type': 'double_gameweek',
                    'suitable_chips': ['bboost', '3xc'],
                    'confidence': 0.7
                })
            
            # Check for fixture swings
            # Would need detailed fixture analysis
            
            if gw_opportunities:
                opportunities.append({
                    'gameweek': gw,
                    'opportunities': gw_opportunities
                })
        
        return opportunities
    
    async def _compare_to_optimal_strategy(
        self,
        chip_analyses: List[ChipAnalysis],
        current_gameweek: int
    ) -> Dict[str, Any]:
        """Compare actual usage to optimal strategy"""
        comparison = {
            'timing_accuracy': 0,
            'missed_opportunities': [],
            'suboptimal_usage': []
        }
        
        if not chip_analyses:
            return comparison
        
        # Check timing accuracy
        perfect_timings = sum(1 for ca in chip_analyses if ca.timing_quality == 'perfect')
        good_timings = sum(1 for ca in chip_analyses if ca.timing_quality == 'good')
        
        comparison['timing_accuracy'] = (
            (perfect_timings * 1.0 + good_timings * 0.7) / len(chip_analyses)
        )
        
        # Check for suboptimal usage
        for ca in chip_analyses:
            if ca.timing_quality in ['suboptimal', 'poor']:
                comparison['suboptimal_usage'].append({
                    'chip': ca.chip_name,
                    'gameweek': ca.gameweek_used,
                    'issue': f"{ca.timing_quality} timing"
                })
        
        # Check for missed opportunities
        # Simplified - would need historical fixture data
        if not any(ca.chip_name == 'bboost' for ca in chip_analyses):
            if current_gameweek > 37:
                comparison['missed_opportunities'].append({
                    'chip': 'bboost',
                    'gameweek': 37,
                    'reason': 'Likely double gameweek'
                })
        
        return comparison
    
    async def _generate_insights(
        self,
        strategy: ChipStrategy,
        chip_analyses: List[ChipAnalysis],
        recommendations: List[ChipRecommendation]
    ) -> List[str]:
        """Generate insights about chip strategy"""
        insights = []
        
        # Success insights
        if strategy.avg_chip_success > 7:
            insights.append("Excellent chip timing and execution")
        elif strategy.avg_chip_success < 4:
            insights.append("Chip usage needs improvement")
        
        # Timing insights
        if strategy.preferred_timing == 'reactive':
            insights.append("Tendency to use chips reactively rather than planned")
        elif strategy.planning_quality > 7:
            insights.append("Well-planned chip strategy")
        
        # H2H insights
        if strategy.h2h_chip_success_rate > 0.7:
            insights.append("Chips often decisive in H2H victories")
        elif strategy.h2h_chip_success_rate < 0.3:
            insights.append("Chips not translating to H2H wins")
        
        # Remaining chips
        if len(strategy.chips_remaining) == 0:
            insights.append("All chips used - no safety net remaining")
        elif len(strategy.chips_remaining) >= 3 and recommendations:
            top_rec = recommendations[0]
            if top_rec.confidence > 0.7:
                insights.append(f"Strong opportunity for {top_rec.chip_name}")
        
        # Best/worst usage
        if strategy.best_chip_usage:
            insights.append(
                f"Best chip: {strategy.best_chip_usage.chip_name} "
                f"in GW{strategy.best_chip_usage.gameweek_used} "
                f"({strategy.best_chip_usage.points_gained:+.0f} pts)"
            )
        
        return insights[:5]
    
    def _serialize_strategy(self, strategy: ChipStrategy) -> Dict[str, Any]:
        """Serialize chip strategy to dict"""
        return {
            "chips_used": strategy.chips_used,
            "chips_remaining": strategy.chips_remaining,
            "performance": {
                "avg_success": round(strategy.avg_chip_success, 1),
                "h2h_success_rate": round(strategy.h2h_chip_success_rate, 2)
            },
            "behavior": {
                "preferred_timing": strategy.preferred_timing,
                "planning_quality": round(strategy.planning_quality, 1)
            }
        }
    
    def _serialize_chip_analysis(self, analysis: ChipAnalysis) -> Dict[str, Any]:
        """Serialize chip analysis to dict"""
        return {
            "chip": analysis.chip_name,
            "gameweek": analysis.gameweek_used,
            "performance": {
                "points_gained": round(analysis.points_gained, 1),
                "success_rating": round(analysis.success_rating, 1),
                "timing": analysis.timing_quality
            },
            "h2h_impact": analysis.h2h_impact
        }
    
    def _serialize_recommendation(self, rec: ChipRecommendation) -> Dict[str, Any]:
        """Serialize chip recommendation to dict"""
        return {
            "chip": rec.chip_name,
            "recommended_gameweek": rec.recommended_gameweek,
            "confidence": round(rec.confidence, 2),
            "reasoning": rec.reasoning,
            "expected_benefit": round(rec.expected_benefit, 1),
            "risk_level": rec.risk_level,
            "h2h_context": rec.h2h_context
        }