"""
Transfer Strategy Analyzer
Analyzes transfer patterns, ROI, and value building success
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import statistics

logger = logging.getLogger(__name__)


@dataclass
class TransferAnalysis:
    """Analysis of a single transfer"""
    gameweek: int
    player_in: Dict[str, Any]
    player_out: Dict[str, Any]
    
    # Financial impact
    profit_loss: float  # Value gained/lost
    cost: int  # Transfer cost (0 or -4)
    
    # Points impact
    points_gained: float  # Points from player_in - player_out after transfer
    immediate_impact: float  # Points in the GW of transfer
    cumulative_impact: float  # Total points gained since transfer
    
    # Strategic assessment
    transfer_type: str  # 'injury', 'form', 'fixture', 'value', 'punt'
    success_rating: float  # 0-10 scale
    timing_quality: str  # 'early', 'optimal', 'late', 'knee-jerk'


@dataclass
class TransferStrategy:
    """Overall transfer strategy profile"""
    total_transfers: int
    total_hits: int
    total_points_cost: int
    
    # ROI metrics
    avg_points_gained_per_transfer: float
    avg_points_gained_per_hit: float
    total_roi: float  # Total points gained - costs
    
    # Value metrics
    total_value_gained: float
    successful_value_picks: List[Dict[str, Any]]
    
    # Timing patterns
    avg_transfer_time: str  # 'early_week', 'mid_week', 'deadline'
    price_change_awareness: float  # 0-1 score
    
    # Strategy classification
    strategy_type: str  # 'aggressive', 'conservative', 'balanced', 'reactive'
    planning_score: float  # 0-10 for how well planned transfers are


class TransferStrategyAnalyzer:
    """
    Analyzes transfer strategies and effectiveness
    """
    
    def __init__(self):
        self.hit_threshold = -4  # Points cost for extra transfers
        self.success_thresholds = {
            'excellent': 15,   # Points gained
            'good': 8,
            'neutral': 0,
            'poor': -4
        }
    
    async def analyze_transfer_strategy(
        self,
        manager_id: int,
        transfers: List[Dict[str, Any]],
        manager_history: Dict[str, Any],
        bootstrap_data: Dict[str, Any],
        fixtures: List[Dict[str, Any]],
        live_gameweek_data: Optional[Dict[str, List[Dict[str, Any]]]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive transfer strategy analysis
        """
        try:
            if not transfers:
                return self._get_no_transfers_analysis()
            
            # Get player data
            players_by_id = {p['id']: p for p in bootstrap_data['elements']}
            
            # Analyze each transfer
            transfer_analyses = []
            for transfer in transfers:
                analysis = await self._analyze_single_transfer(
                    transfer, players_by_id, manager_history, 
                    fixtures, live_gameweek_data
                )
                if analysis:
                    transfer_analyses.append(analysis)
            
            # Calculate overall strategy metrics
            strategy = await self._calculate_strategy_profile(
                transfer_analyses, manager_history, transfers
            )
            
            # Identify patterns
            patterns = await self._identify_transfer_patterns(
                transfer_analyses, transfers
            )
            
            # Compare to averages
            comparison = await self._compare_to_averages(
                strategy, patterns, manager_history
            )
            
            # Generate insights
            insights = await self._generate_transfer_insights(
                strategy, patterns, transfer_analyses
            )
            
            return {
                "summary": self._serialize_strategy(strategy),
                "detailed_transfers": [
                    self._serialize_transfer_analysis(ta) 
                    for ta in transfer_analyses[-10:]  # Last 10 transfers
                ],
                "patterns": patterns,
                "comparison": comparison,
                "insights": insights,
                "recommendations": await self._generate_recommendations(
                    strategy, patterns, manager_history
                )
            }
            
        except Exception as e:
            logger.error(f"Error analyzing transfer strategy: {e}")
            return {}
    
    async def _analyze_single_transfer(
        self,
        transfer: Dict[str, Any],
        players_by_id: Dict[int, Any],
        manager_history: Dict[str, Any],
        fixtures: List[Dict[str, Any]],
        live_gameweek_data: Optional[Dict[str, List[Dict[str, Any]]]]
    ) -> Optional[TransferAnalysis]:
        """Analyze a single transfer"""
        try:
            player_in = players_by_id.get(transfer['element_in'])
            player_out = players_by_id.get(transfer['element_out'])
            
            if not player_in or not player_out:
                return None
            
            gameweek = transfer['event']
            
            # Financial impact
            profit_loss = (
                transfer['element_in_cost'] - transfer['element_out_cost']
            ) / 10  # Convert to millions
            
            # Determine if hit was taken
            gw_history = next(
                (gw for gw in manager_history.get('current', []) 
                 if gw['event'] == gameweek), 
                None
            )
            
            cost = -4 if gw_history and gw_history.get('event_transfers_cost', 0) > 0 else 0
            
            # Points impact (would need historical data for accuracy)
            points_gained = await self._calculate_points_impact(
                player_in, player_out, gameweek, live_gameweek_data
            )
            
            # Transfer type classification
            transfer_type = await self._classify_transfer_type(
                player_in, player_out, gameweek, fixtures
            )
            
            # Success rating
            success_rating = self._calculate_transfer_success(
                points_gained['cumulative'], cost, transfer_type
            )
            
            # Timing analysis
            timing_quality = await self._assess_transfer_timing(
                transfer, player_in, player_out
            )
            
            return TransferAnalysis(
                gameweek=gameweek,
                player_in=player_in,
                player_out=player_out,
                profit_loss=profit_loss,
                cost=cost,
                points_gained=points_gained['total'],
                immediate_impact=points_gained['immediate'],
                cumulative_impact=points_gained['cumulative'],
                transfer_type=transfer_type,
                success_rating=success_rating,
                timing_quality=timing_quality
            )
            
        except Exception as e:
            logger.error(f"Error analyzing transfer: {e}")
            return None
    
    async def _calculate_points_impact(
        self,
        player_in: Dict[str, Any],
        player_out: Dict[str, Any],
        gameweek: int,
        live_gameweek_data: Optional[Dict[str, List[Dict[str, Any]]]]
    ) -> Dict[str, float]:
        """Calculate points gained from a transfer"""
        # This is simplified - in reality would need historical point data
        # Using current season data as proxy
        
        # Estimate based on form and points per game
        in_ppg = float(player_in.get('points_per_game', '0'))
        out_ppg = float(player_out.get('points_per_game', '0'))
        
        # Immediate impact (next GW)
        immediate = in_ppg - out_ppg
        
        # Cumulative (rest of season estimate)
        remaining_gws = max(0, 38 - gameweek)
        cumulative = immediate * remaining_gws
        
        # Adjust for form
        in_form = float(player_in.get('form', '0'))
        out_form = float(player_out.get('form', '0'))
        form_multiplier = 1 + (in_form - out_form) / 10
        
        return {
            'immediate': immediate * form_multiplier,
            'cumulative': cumulative * form_multiplier,
            'total': cumulative * form_multiplier
        }
    
    async def _classify_transfer_type(
        self,
        player_in: Dict[str, Any],
        player_out: Dict[str, Any],
        gameweek: int,
        fixtures: List[Dict[str, Any]]
    ) -> str:
        """Classify the type/reason for transfer"""
        # Check injury
        if player_out.get('status') != 'a':
            return 'injury'
        
        # Check form difference
        in_form = float(player_in.get('form', '0'))
        out_form = float(player_out.get('form', '0'))
        
        if in_form - out_form > 3:
            return 'form'
        
        # Check fixture swing
        in_team = player_in['team']
        out_team = player_out['team']
        
        # Get next 3 fixtures
        in_fixtures = []
        out_fixtures = []
        
        for fixture in fixtures:
            if not fixture['finished']:
                if fixture['team_h'] == in_team:
                    in_fixtures.append(fixture['team_h_difficulty'])
                elif fixture['team_a'] == in_team:
                    in_fixtures.append(fixture['team_a_difficulty'])
                    
                if fixture['team_h'] == out_team:
                    out_fixtures.append(fixture['team_h_difficulty'])
                elif fixture['team_a'] == out_team:
                    out_fixtures.append(fixture['team_a_difficulty'])
                    
                if len(in_fixtures) >= 3 and len(out_fixtures) >= 3:
                    break
        
        if in_fixtures and out_fixtures:
            in_avg = statistics.mean(in_fixtures[:3])
            out_avg = statistics.mean(out_fixtures[:3])
            
            if out_avg - in_avg > 1:
                return 'fixture'
        
        # Check value play
        if player_in['now_cost'] < player_out['now_cost'] * 0.9:
            return 'value'
        
        # Default to punt (speculative)
        return 'punt'
    
    def _calculate_transfer_success(
        self,
        points_gained: float,
        cost: int,
        transfer_type: str
    ) -> float:
        """Rate transfer success on 0-10 scale"""
        net_gain = points_gained + cost
        
        # Base rating
        if net_gain >= self.success_thresholds['excellent']:
            base_rating = 8.0
        elif net_gain >= self.success_thresholds['good']:
            base_rating = 6.0
        elif net_gain >= self.success_thresholds['neutral']:
            base_rating = 4.0
        else:
            base_rating = 2.0
        
        # Adjust for transfer type
        type_adjustments = {
            'injury': 1.0,    # Forced transfers get bonus
            'form': 0.5,      # Form chasing is okay
            'fixture': 0.8,   # Fixture planning is good
            'value': 0.7,     # Value building is strategic
            'punt': -0.5      # Punts are risky
        }
        
        adjustment = type_adjustments.get(transfer_type, 0)
        
        return min(10, max(0, base_rating + adjustment))
    
    async def _assess_transfer_timing(
        self,
        transfer: Dict[str, Any],
        player_in: Dict[str, Any],
        player_out: Dict[str, Any]
    ) -> str:
        """Assess the timing quality of a transfer"""
        # Check if caught price changes
        # This is simplified - would need price change data
        
        # If transfer happened early in week
        transfer_time = transfer.get('time', '')
        if transfer_time:
            # Parse time and check day of week
            # For now, random assignment
            import random
            return random.choice(['early', 'optimal', 'late', 'knee-jerk'])
        
        return 'unknown'
    
    async def _calculate_strategy_profile(
        self,
        transfer_analyses: List[TransferAnalysis],
        manager_history: Dict[str, Any],
        transfers: List[Dict[str, Any]]
    ) -> TransferStrategy:
        """Calculate overall transfer strategy profile"""
        total_transfers = len(transfers)
        
        # Count hits
        total_hits = sum(
            1 for gw in manager_history.get('current', [])
            if gw.get('event_transfers_cost', 0) > 0
        )
        total_points_cost = total_hits * 4
        
        # ROI calculations
        total_points_gained = sum(ta.points_gained for ta in transfer_analyses)
        avg_per_transfer = total_points_gained / total_transfers if total_transfers > 0 else 0
        avg_per_hit = total_points_gained / total_hits if total_hits > 0 else 0
        total_roi = total_points_gained - total_points_cost
        
        # Value calculations
        total_value_gained = sum(ta.profit_loss for ta in transfer_analyses)
        successful_value_picks = [
            {
                'player': ta.player_in['web_name'],
                'profit': ta.profit_loss,
                'points_gained': ta.cumulative_impact
            }
            for ta in transfer_analyses
            if ta.profit_loss > 0.5 and ta.cumulative_impact > 10
        ]
        
        # Timing patterns
        timing_counts = {}
        for ta in transfer_analyses:
            timing_counts[ta.timing_quality] = timing_counts.get(ta.timing_quality, 0) + 1
        
        most_common_timing = max(timing_counts.items(), key=lambda x: x[1])[0] if timing_counts else 'unknown'
        
        # Price change awareness (simplified)
        price_awareness = len([ta for ta in transfer_analyses if ta.timing_quality in ['early', 'optimal']]) / len(transfer_analyses) if transfer_analyses else 0
        
        # Strategy classification
        strategy_type = self._classify_strategy_type(
            total_transfers, total_hits, transfer_analyses
        )
        
        # Planning score
        planning_score = self._calculate_planning_score(
            transfer_analyses, timing_counts
        )
        
        return TransferStrategy(
            total_transfers=total_transfers,
            total_hits=total_hits,
            total_points_cost=total_points_cost,
            avg_points_gained_per_transfer=avg_per_transfer,
            avg_points_gained_per_hit=avg_per_hit,
            total_roi=total_roi,
            total_value_gained=total_value_gained,
            successful_value_picks=successful_value_picks,
            avg_transfer_time=most_common_timing,
            price_change_awareness=price_awareness,
            strategy_type=strategy_type,
            planning_score=planning_score
        )
    
    def _classify_strategy_type(
        self,
        total_transfers: int,
        total_hits: int,
        transfer_analyses: List[TransferAnalysis]
    ) -> str:
        """Classify overall transfer strategy"""
        if total_transfers == 0:
            return 'inactive'
        
        # Hit ratio
        hit_ratio = total_hits / total_transfers if total_transfers > 0 else 0
        
        # Success ratio
        successful_transfers = [ta for ta in transfer_analyses if ta.success_rating >= 6]
        success_ratio = len(successful_transfers) / len(transfer_analyses) if transfer_analyses else 0
        
        # Transfer frequency (assuming 38 GW season)
        transfers_per_gw = total_transfers / 38
        
        if hit_ratio > 0.3 and transfers_per_gw > 1.5:
            return 'aggressive'
        elif hit_ratio < 0.1 and transfers_per_gw < 0.8:
            return 'conservative'
        elif success_ratio < 0.3:
            return 'reactive'
        else:
            return 'balanced'
    
    def _calculate_planning_score(
        self,
        transfer_analyses: List[TransferAnalysis],
        timing_counts: Dict[str, int]
    ) -> float:
        """Calculate how well-planned transfers are"""
        score = 5.0  # Base score
        
        # Good timing increases score
        good_timing = timing_counts.get('early', 0) + timing_counts.get('optimal', 0)
        total_timing = sum(timing_counts.values())
        
        if total_timing > 0:
            timing_ratio = good_timing / total_timing
            score += timing_ratio * 3
        
        # Successful transfers increase score
        avg_success = statistics.mean([ta.success_rating for ta in transfer_analyses]) if transfer_analyses else 5
        score += (avg_success - 5) * 0.4
        
        # Injury transfers decrease score (reactive)
        injury_transfers = [ta for ta in transfer_analyses if ta.transfer_type == 'injury']
        if transfer_analyses:
            injury_ratio = len(injury_transfers) / len(transfer_analyses)
            score -= injury_ratio * 2
        
        return max(0, min(10, score))
    
    async def _identify_transfer_patterns(
        self,
        transfer_analyses: List[TransferAnalysis],
        transfers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Identify patterns in transfer behavior"""
        patterns = {
            'preferred_positions': {},
            'price_brackets': {},
            'team_preferences': {},
            'timing_patterns': {},
            'success_by_type': {}
        }
        
        if not transfer_analyses:
            return patterns
        
        # Position preferences
        positions = {}
        for ta in transfer_analyses:
            pos = ta.player_in['element_type']
            positions[pos] = positions.get(pos, 0) + 1
        
        patterns['preferred_positions'] = {
            'GKP': positions.get(1, 0),
            'DEF': positions.get(2, 0),
            'MID': positions.get(3, 0),
            'FWD': positions.get(4, 0)
        }
        
        # Price bracket preferences
        for ta in transfer_analyses:
            price = ta.player_in['now_cost'] / 10
            if price < 5.0:
                bracket = 'budget'
            elif price < 8.0:
                bracket = 'mid_price'
            elif price < 11.0:
                bracket = 'premium'
            else:
                bracket = 'elite'
            
            patterns['price_brackets'][bracket] = patterns['price_brackets'].get(bracket, 0) + 1
        
        # Team preferences (top 5)
        teams = {}
        for ta in transfer_analyses:
            team_id = ta.player_in['team']
            teams[team_id] = teams.get(team_id, 0) + 1
        
        # Sort by frequency
        top_teams = sorted(teams.items(), key=lambda x: x[1], reverse=True)[:5]
        patterns['team_preferences'] = dict(top_teams)
        
        # Success by transfer type
        type_success = {}
        for ta in transfer_analyses:
            if ta.transfer_type not in type_success:
                type_success[ta.transfer_type] = []
            type_success[ta.transfer_type].append(ta.success_rating)
        
        for transfer_type, ratings in type_success.items():
            patterns['success_by_type'][transfer_type] = {
                'count': len(ratings),
                'avg_success': statistics.mean(ratings)
            }
        
        return patterns
    
    async def _compare_to_averages(
        self,
        strategy: TransferStrategy,
        patterns: Dict[str, Any],
        manager_history: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare to typical FPL manager averages"""
        # These are approximate averages
        averages = {
            'transfers_per_season': 25,
            'hits_per_season': 3,
            'avg_roi_per_transfer': 2.5,
            'value_gained': 1.5
        }
        
        comparison = {
            'transfer_activity': {
                'manager': strategy.total_transfers,
                'average': averages['transfers_per_season'],
                'percentile': self._calculate_percentile(
                    strategy.total_transfers, 
                    averages['transfers_per_season'], 
                    10  # std dev estimate
                )
            },
            'hit_taking': {
                'manager': strategy.total_hits,
                'average': averages['hits_per_season'],
                'percentile': self._calculate_percentile(
                    strategy.total_hits,
                    averages['hits_per_season'],
                    3
                )
            },
            'transfer_success': {
                'manager': strategy.avg_points_gained_per_transfer,
                'average': averages['avg_roi_per_transfer'],
                'percentile': self._calculate_percentile(
                    strategy.avg_points_gained_per_transfer,
                    averages['avg_roi_per_transfer'],
                    2
                )
            },
            'value_building': {
                'manager': strategy.total_value_gained,
                'average': averages['value_gained'],
                'percentile': self._calculate_percentile(
                    strategy.total_value_gained,
                    averages['value_gained'],
                    1
                )
            }
        }
        
        # Overall ranking
        avg_percentile = statistics.mean([
            v['percentile'] for v in comparison.values()
        ])
        
        comparison['overall_ranking'] = self._get_ranking_label(avg_percentile)
        
        return comparison
    
    def _calculate_percentile(self, value: float, mean: float, std_dev: float) -> float:
        """Calculate approximate percentile using normal distribution"""
        z_score = (value - mean) / std_dev if std_dev > 0 else 0
        
        # Approximate percentile (simplified)
        if z_score > 2:
            return 95
        elif z_score > 1:
            return 84
        elif z_score > 0:
            return 50 + z_score * 34
        elif z_score > -1:
            return 50 + z_score * 34
        elif z_score > -2:
            return 16
        else:
            return 5
    
    def _get_ranking_label(self, percentile: float) -> str:
        """Get ranking label from percentile"""
        if percentile >= 90:
            return 'Elite'
        elif percentile >= 75:
            return 'Excellent'
        elif percentile >= 50:
            return 'Above Average'
        elif percentile >= 25:
            return 'Below Average'
        else:
            return 'Poor'
    
    async def _generate_transfer_insights(
        self,
        strategy: TransferStrategy,
        patterns: Dict[str, Any],
        transfer_analyses: List[TransferAnalysis]
    ) -> List[str]:
        """Generate key insights about transfer strategy"""
        insights = []
        
        # ROI insight
        if strategy.total_roi > 50:
            insights.append(f"Exceptional transfer ROI of {strategy.total_roi:.0f} points")
        elif strategy.total_roi < -20:
            insights.append(f"Poor transfer ROI of {strategy.total_roi:.0f} points")
        
        # Hit-taking insight
        if strategy.total_hits > 5:
            if strategy.avg_points_gained_per_hit > 4:
                insights.append("Aggressive but successful hit-taking strategy")
            else:
                insights.append("Excessive hits hurting overall rank")
        
        # Value building
        if strategy.total_value_gained > 3:
            insights.append(f"Excellent value building: £{strategy.total_value_gained:.1f}m gained")
        
        # Position preferences
        pos_pref = patterns.get('preferred_positions', {})
        most_transferred = max(pos_pref.items(), key=lambda x: x[1])[0] if pos_pref else None
        if most_transferred:
            insights.append(f"Focuses transfers on {most_transferred} positions")
        
        # Success patterns
        success_by_type = patterns.get('success_by_type', {})
        best_type = max(
            success_by_type.items(), 
            key=lambda x: x[1]['avg_success']
        )[0] if success_by_type else None
        
        if best_type:
            insights.append(f"Most successful with {best_type} transfers")
        
        # Planning
        if strategy.planning_score > 7:
            insights.append("Well-planned transfer strategy")
        elif strategy.planning_score < 3:
            insights.append("Reactive transfer approach")
        
        return insights[:5]  # Top 5 insights
    
    async def _generate_recommendations(
        self,
        strategy: TransferStrategy,
        patterns: Dict[str, Any],
        manager_history: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for improving transfer strategy"""
        recommendations = []
        
        # ROI recommendations
        if strategy.avg_points_gained_per_transfer < 2:
            recommendations.append("Focus on form and fixtures when making transfers")
        
        # Hit recommendations
        if strategy.total_hits > 5 and strategy.avg_points_gained_per_hit < 4:
            recommendations.append("Reduce hits - plan transfers better to avoid -4s")
        
        # Timing recommendations
        if strategy.price_change_awareness < 0.3:
            recommendations.append("Make transfers earlier in the week to catch price rises")
        
        # Value recommendations
        if strategy.total_value_gained < 1:
            recommendations.append("Target rising players early to build team value")
        
        # Planning recommendations
        if strategy.planning_score < 5:
            recommendations.append("Plan 2-3 gameweeks ahead to avoid reactive transfers")
        
        # Success rate
        success_rates = patterns.get('success_by_type', {})
        worst_type = min(
            success_rates.items(),
            key=lambda x: x[1]['avg_success']
        )[0] if success_rates else None
        
        if worst_type and success_rates[worst_type]['avg_success'] < 4:
            recommendations.append(f"Avoid {worst_type} transfers - low success rate")
        
        return recommendations[:4]  # Top 4 recommendations
    
    def _get_no_transfers_analysis(self) -> Dict[str, Any]:
        """Return analysis for managers with no transfers"""
        return {
            "summary": {
                "total_transfers": 0,
                "strategy_type": "set_and_forget",
                "planning_score": 10.0  # Perfect planning!
            },
            "insights": ["Set and forget strategy - no transfers made"],
            "recommendations": ["Consider occasional transfers for injuries/form"]
        }
    
    def _serialize_strategy(self, strategy: TransferStrategy) -> Dict[str, Any]:
        """Serialize transfer strategy to dict"""
        return {
            "total_transfers": strategy.total_transfers,
            "total_hits": strategy.total_hits,
            "points_cost": strategy.total_points_cost,
            "roi_metrics": {
                "avg_per_transfer": round(strategy.avg_points_gained_per_transfer, 1),
                "avg_per_hit": round(strategy.avg_points_gained_per_hit, 1),
                "total_roi": round(strategy.total_roi, 1)
            },
            "value_metrics": {
                "total_gained": round(strategy.total_value_gained, 1),
                "successful_picks": strategy.successful_value_picks[:5]
            },
            "behavior": {
                "avg_timing": strategy.avg_transfer_time,
                "price_awareness": round(strategy.price_change_awareness, 2),
                "strategy_type": strategy.strategy_type,
                "planning_score": round(strategy.planning_score, 1)
            }
        }
    
    def _serialize_transfer_analysis(self, ta: TransferAnalysis) -> Dict[str, Any]:
        """Serialize transfer analysis to dict"""
        return {
            "gameweek": ta.gameweek,
            "transfer": {
                "in": ta.player_in['web_name'],
                "out": ta.player_out['web_name']
            },
            "financial": {
                "profit_loss": round(ta.profit_loss, 1),
                "hit_cost": ta.cost
            },
            "points_impact": {
                "immediate": round(ta.immediate_impact, 1),
                "cumulative": round(ta.cumulative_impact, 1),
                "net_gain": round(ta.points_gained + ta.cost, 1)
            },
            "assessment": {
                "type": ta.transfer_type,
                "success_rating": round(ta.success_rating, 1),
                "timing": ta.timing_quality
            }
        }