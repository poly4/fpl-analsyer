"""
Historical Pattern Analyzer
Analyzes H2H history, patterns, and psychological edges
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import statistics

logger = logging.getLogger(__name__)


@dataclass
class H2HRecord:
    """Represents historical H2H record"""
    total_matches: int
    manager1_wins: int
    manager2_wins: int
    draws: int
    
    # Score statistics
    avg_margin: float
    biggest_m1_win: Tuple[int, int, int]  # (margin, m1_score, m2_score)
    biggest_m2_win: Tuple[int, int, int]
    
    # Streaks
    current_streak: Dict[str, Any]  # {type: 'win/loss/draw', count: N, manager: 'manager1/2'}
    longest_win_streak_m1: int
    longest_win_streak_m2: int
    
    # Recent form
    last_5_results: List[str]  # ['W', 'L', 'D'] from manager1 perspective
    recent_form_advantage: Optional[str]  # 'manager1', 'manager2', or None


@dataclass
class PatternInsight:
    """Represents a discovered pattern"""
    pattern_type: str
    description: str
    confidence: float  # 0-1
    impact: str  # 'high', 'medium', 'low'
    data: Dict[str, Any]


class HistoricalPatternAnalyzer:
    """
    Analyzes historical patterns between H2H opponents
    """
    
    def __init__(self):
        self.min_matches_for_patterns = 5
        self.psychological_weights = {
            'recent_form': 0.4,
            'head_to_head': 0.3,
            'momentum': 0.2,
            'consistency': 0.1
        }
    
    async def analyze_historical_patterns(
        self,
        manager1_id: int,
        manager2_id: int,
        h2h_history: List[Dict[str, Any]],
        manager1_season_history: Dict[str, Any],
        manager2_season_history: Dict[str, Any],
        current_gameweek: int
    ) -> Dict[str, Any]:
        """
        Comprehensive historical pattern analysis
        """
        try:
            # Get H2H record
            h2h_record = await self._calculate_h2h_record(
                h2h_history, manager1_id, manager2_id
            )
            
            # Analyze patterns
            patterns = await self._discover_patterns(
                h2h_history, manager1_id, manager2_id,
                manager1_season_history, manager2_season_history
            )
            
            # Calculate psychological edge
            psychological_analysis = await self._analyze_psychological_factors(
                h2h_record, patterns, 
                manager1_season_history, manager2_season_history,
                current_gameweek
            )
            
            # Chip usage patterns
            chip_analysis = await self._analyze_chip_patterns(
                manager1_season_history, manager2_season_history,
                h2h_history
            )
            
            # Performance patterns
            performance_patterns = await self._analyze_performance_patterns(
                manager1_season_history, manager2_season_history
            )
            
            return {
                "h2h_record": self._serialize_h2h_record(h2h_record),
                "discovered_patterns": [self._serialize_pattern(p) for p in patterns],
                "psychological_analysis": psychological_analysis,
                "chip_patterns": chip_analysis,
                "performance_patterns": performance_patterns,
                "matchup_summary": await self._generate_matchup_summary(
                    h2h_record, patterns, psychological_analysis
                )
            }
            
        except Exception as e:
            logger.error(f"Error analyzing historical patterns: {e}")
            return {}
    
    async def _calculate_h2h_record(
        self,
        h2h_history: List[Dict[str, Any]],
        manager1_id: int,
        manager2_id: int
    ) -> H2HRecord:
        """Calculate comprehensive H2H record"""
        if not h2h_history:
            return H2HRecord(
                total_matches=0, manager1_wins=0, manager2_wins=0, draws=0,
                avg_margin=0, biggest_m1_win=(0, 0, 0), biggest_m2_win=(0, 0, 0),
                current_streak={'type': None, 'count': 0, 'manager': None},
                longest_win_streak_m1=0, longest_win_streak_m2=0,
                last_5_results=[], recent_form_advantage=None
            )
        
        # Count results
        m1_wins = 0
        m2_wins = 0
        draws = 0
        margins = []
        biggest_m1_win = (0, 0, 0)
        biggest_m2_win = (0, 0, 0)
        
        # Sort by gameweek
        sorted_history = sorted(h2h_history, key=lambda x: x['event'])
        
        # Track streaks
        current_streak = {'type': None, 'count': 0, 'manager': None}
        m1_streak = 0
        m2_streak = 0
        max_m1_streak = 0
        max_m2_streak = 0
        
        last_5 = []
        
        for match in sorted_history:
            m1_score = match['entry_1_points'] if match['entry_1_entry'] == manager1_id else match['entry_2_points']
            m2_score = match['entry_2_points'] if match['entry_2_entry'] == manager2_id else match['entry_1_points']
            
            margin = m1_score - m2_score
            margins.append(abs(margin))
            
            if margin > 0:
                m1_wins += 1
                result = 'W'
                
                # Update streaks
                m1_streak += 1
                max_m1_streak = max(max_m1_streak, m1_streak)
                m2_streak = 0
                
                if margin > biggest_m1_win[0]:
                    biggest_m1_win = (margin, m1_score, m2_score)
                    
                # Update current streak
                if current_streak['type'] == 'win' and current_streak['manager'] == 'manager1':
                    current_streak['count'] += 1
                else:
                    current_streak = {'type': 'win', 'count': 1, 'manager': 'manager1'}
                    
            elif margin < 0:
                m2_wins += 1
                result = 'L'
                
                # Update streaks
                m2_streak += 1
                max_m2_streak = max(max_m2_streak, m2_streak)
                m1_streak = 0
                
                if abs(margin) > biggest_m2_win[0]:
                    biggest_m2_win = (abs(margin), m2_score, m1_score)
                    
                # Update current streak
                if current_streak['type'] == 'win' and current_streak['manager'] == 'manager2':
                    current_streak['count'] += 1
                else:
                    current_streak = {'type': 'win', 'count': 1, 'manager': 'manager2'}
                    
            else:
                draws += 1
                result = 'D'
                m1_streak = 0
                m2_streak = 0
                
                if current_streak['type'] == 'draw':
                    current_streak['count'] += 1
                else:
                    current_streak = {'type': 'draw', 'count': 1, 'manager': None}
            
            last_5.append(result)
        
        # Keep only last 5
        last_5 = last_5[-5:]
        
        # Determine recent form advantage
        recent_m1_wins = last_5.count('W')
        recent_m2_wins = last_5.count('L')
        
        if recent_m1_wins > recent_m2_wins:
            recent_form_advantage = 'manager1'
        elif recent_m2_wins > recent_m1_wins:
            recent_form_advantage = 'manager2'
        else:
            recent_form_advantage = None
        
        return H2HRecord(
            total_matches=len(h2h_history),
            manager1_wins=m1_wins,
            manager2_wins=m2_wins,
            draws=draws,
            avg_margin=statistics.mean(margins) if margins else 0,
            biggest_m1_win=biggest_m1_win,
            biggest_m2_win=biggest_m2_win,
            current_streak=current_streak,
            longest_win_streak_m1=max_m1_streak,
            longest_win_streak_m2=max_m2_streak,
            last_5_results=last_5,
            recent_form_advantage=recent_form_advantage
        )
    
    async def _discover_patterns(
        self,
        h2h_history: List[Dict[str, Any]],
        manager1_id: int,
        manager2_id: int,
        m1_season: Dict[str, Any],
        m2_season: Dict[str, Any]
    ) -> List[PatternInsight]:
        """Discover meaningful patterns in the data"""
        patterns = []
        
        if len(h2h_history) < self.min_matches_for_patterns:
            return patterns
        
        # Pattern 1: Home/Away performance
        home_away_pattern = await self._analyze_home_away_pattern(h2h_history)
        if home_away_pattern:
            patterns.append(home_away_pattern)
        
        # Pattern 2: Gameweek timing patterns
        timing_pattern = await self._analyze_timing_patterns(h2h_history, m1_season, m2_season)
        if timing_pattern:
            patterns.append(timing_pattern)
        
        # Pattern 3: Score clustering
        score_pattern = await self._analyze_score_patterns(h2h_history, manager1_id, manager2_id)
        if score_pattern:
            patterns.append(score_pattern)
        
        # Pattern 4: Momentum patterns
        momentum_pattern = await self._analyze_momentum_patterns(
            h2h_history, m1_season, m2_season
        )
        if momentum_pattern:
            patterns.append(momentum_pattern)
        
        # Pattern 5: Differential success patterns
        diff_pattern = await self._analyze_differential_patterns(h2h_history)
        if diff_pattern:
            patterns.append(diff_pattern)
        
        return patterns
    
    async def _analyze_home_away_pattern(
        self,
        h2h_history: List[Dict[str, Any]]
    ) -> Optional[PatternInsight]:
        """Analyze if there's a pattern in who goes first in matchups"""
        # In H2H, "entry_1" vs "entry_2" might show patterns
        entry1_scores = []
        entry2_scores = []
        
        for match in h2h_history:
            entry1_scores.append(match['entry_1_points'])
            entry2_scores.append(match['entry_2_points'])
        
        if len(entry1_scores) >= 5:
            avg_e1 = statistics.mean(entry1_scores)
            avg_e2 = statistics.mean(entry2_scores)
            
            if abs(avg_e1 - avg_e2) > 5:  # Significant difference
                return PatternInsight(
                    pattern_type="position_bias",
                    description=f"Entry 1 averages {avg_e1:.1f} vs Entry 2 {avg_e2:.1f}",
                    confidence=0.7,
                    impact="medium",
                    data={
                        "entry1_avg": avg_e1,
                        "entry2_avg": avg_e2,
                        "difference": avg_e1 - avg_e2
                    }
                )
        
        return None
    
    async def _analyze_timing_patterns(
        self,
        h2h_history: List[Dict[str, Any]],
        m1_season: Dict[str, Any],
        m2_season: Dict[str, Any]
    ) -> Optional[PatternInsight]:
        """Analyze performance patterns by gameweek ranges"""
        early_season = []  # GW 1-10
        mid_season = []    # GW 11-28
        late_season = []   # GW 29-38
        
        for match in h2h_history:
            gw = match['event']
            result = 1 if match.get('points_winner') == match['entry_1_entry'] else -1
            
            if gw <= 10:
                early_season.append(result)
            elif gw <= 28:
                mid_season.append(result)
            else:
                late_season.append(result)
        
        # Find strongest period
        periods = {
            'early': sum(early_season) if early_season else 0,
            'mid': sum(mid_season) if mid_season else 0,
            'late': sum(late_season) if late_season else 0
        }
        
        if max(abs(v) for v in periods.values()) >= 3:
            strongest = max(periods.items(), key=lambda x: abs(x[1]))
            return PatternInsight(
                pattern_type="seasonal_strength",
                description=f"Strongest in {strongest[0]} season",
                confidence=0.6,
                impact="medium",
                data=periods
            )
        
        return None
    
    async def _analyze_score_patterns(
        self,
        h2h_history: List[Dict[str, Any]],
        manager1_id: int,
        manager2_id: int
    ) -> Optional[PatternInsight]:
        """Analyze scoring patterns"""
        m1_scores = []
        m2_scores = []
        
        for match in h2h_history:
            if match['entry_1_entry'] == manager1_id:
                m1_scores.append(match['entry_1_points'])
                m2_scores.append(match['entry_2_points'])
            else:
                m1_scores.append(match['entry_2_points'])
                m2_scores.append(match['entry_1_points'])
        
        # Check for consistency
        m1_std = statistics.stdev(m1_scores) if len(m1_scores) > 1 else 0
        m2_std = statistics.stdev(m2_scores) if len(m2_scores) > 1 else 0
        
        if abs(m1_std - m2_std) > 10:
            more_consistent = "manager1" if m1_std < m2_std else "manager2"
            return PatternInsight(
                pattern_type="consistency_difference",
                description=f"{more_consistent} is more consistent",
                confidence=0.7,
                impact="high",
                data={
                    "manager1_std": m1_std,
                    "manager2_std": m2_std,
                    "difference": abs(m1_std - m2_std)
                }
            )
        
        return None
    
    async def _analyze_momentum_patterns(
        self,
        h2h_history: List[Dict[str, Any]],
        m1_season: Dict[str, Any],
        m2_season: Dict[str, Any]
    ) -> Optional[PatternInsight]:
        """Analyze momentum and form patterns"""
        # Look for patterns where one manager performs better after wins/losses
        momentum_data = {
            'after_win': {'m1': [], 'm2': []},
            'after_loss': {'m1': [], 'm2': []}
        }
        
        sorted_history = sorted(h2h_history, key=lambda x: x['event'])
        
        for i in range(1, len(sorted_history)):
            prev_match = sorted_history[i-1]
            curr_match = sorted_history[i]
            
            # Determine previous result
            m1_won_prev = (
                (prev_match['entry_1_entry'] == curr_match['entry_1_entry'] and 
                 prev_match['entry_1_points'] > prev_match['entry_2_points']) or
                (prev_match['entry_2_entry'] == curr_match['entry_1_entry'] and 
                 prev_match['entry_2_points'] > prev_match['entry_1_points'])
            )
            
            # Current performance
            m1_score = curr_match['entry_1_points']
            m2_score = curr_match['entry_2_points']
            
            if m1_won_prev:
                momentum_data['after_win']['m1'].append(m1_score)
                momentum_data['after_loss']['m2'].append(m2_score)
            else:
                momentum_data['after_loss']['m1'].append(m1_score)
                momentum_data['after_win']['m2'].append(m2_score)
        
        # Analyze momentum impact
        insights = []
        for manager in ['m1', 'm2']:
            if (len(momentum_data['after_win'][manager]) >= 3 and 
                len(momentum_data['after_loss'][manager]) >= 3):
                
                avg_after_win = statistics.mean(momentum_data['after_win'][manager])
                avg_after_loss = statistics.mean(momentum_data['after_loss'][manager])
                
                if abs(avg_after_win - avg_after_loss) > 8:
                    manager_name = 'manager1' if manager == 'm1' else 'manager2'
                    return PatternInsight(
                        pattern_type="momentum_dependent",
                        description=f"{manager_name} affected by previous results",
                        confidence=0.6,
                        impact="medium",
                        data={
                            "avg_after_win": avg_after_win,
                            "avg_after_loss": avg_after_loss,
                            "difference": avg_after_win - avg_after_loss
                        }
                    )
        
        return None
    
    async def _analyze_differential_patterns(
        self,
        h2h_history: List[Dict[str, Any]]
    ) -> Optional[PatternInsight]:
        """Analyze patterns in close vs comfortable wins"""
        close_matches = 0  # Within 10 points
        comfortable_matches = 0  # > 20 points
        
        for match in h2h_history:
            margin = abs(match['entry_1_points'] - match['entry_2_points'])
            
            if margin <= 10:
                close_matches += 1
            elif margin > 20:
                comfortable_matches += 1
        
        total = len(h2h_history)
        if total >= 5:
            close_pct = close_matches / total
            comfortable_pct = comfortable_matches / total
            
            if close_pct > 0.6:
                return PatternInsight(
                    pattern_type="match_closeness",
                    description="Matches tend to be very close",
                    confidence=0.8,
                    impact="high",
                    data={
                        "close_percentage": close_pct,
                        "avg_margin": statistics.mean([
                            abs(m['entry_1_points'] - m['entry_2_points']) 
                            for m in h2h_history
                        ])
                    }
                )
            elif comfortable_pct > 0.4:
                return PatternInsight(
                    pattern_type="match_volatility",
                    description="Matches tend to have large margins",
                    confidence=0.7,
                    impact="medium",
                    data={
                        "comfortable_percentage": comfortable_pct,
                        "avg_margin": statistics.mean([
                            abs(m['entry_1_points'] - m['entry_2_points']) 
                            for m in h2h_history
                        ])
                    }
                )
        
        return None
    
    async def _analyze_psychological_factors(
        self,
        h2h_record: H2HRecord,
        patterns: List[PatternInsight],
        m1_season: Dict[str, Any],
        m2_season: Dict[str, Any],
        current_gameweek: int
    ) -> Dict[str, Any]:
        """Calculate psychological edge factors"""
        factors = {}
        
        # Recent form weight
        recent_form_score = 0
        if h2h_record.recent_form_advantage == 'manager1':
            recent_form_score = 0.7
        elif h2h_record.recent_form_advantage == 'manager2':
            recent_form_score = -0.7
        
        # H2H dominance
        if h2h_record.total_matches > 0:
            win_rate_m1 = h2h_record.manager1_wins / h2h_record.total_matches
            dominance_score = (win_rate_m1 - 0.5) * 2  # -1 to 1 scale
        else:
            dominance_score = 0
        
        # Current streak impact
        streak_score = 0
        if h2h_record.current_streak['count'] >= 3:
            if h2h_record.current_streak['manager'] == 'manager1':
                streak_score = 0.5
            elif h2h_record.current_streak['manager'] == 'manager2':
                streak_score = -0.5
        
        # Overall season performance
        m1_current = m1_season.get('current', [])
        m2_current = m2_season.get('current', [])
        
        if m1_current and m2_current:
            # Compare recent gameweeks
            recent_gws = 5
            m1_recent_avg = statistics.mean([
                gw['points'] for gw in m1_current[-recent_gws:]
            ]) if len(m1_current) >= recent_gws else 50
            
            m2_recent_avg = statistics.mean([
                gw['points'] for gw in m2_current[-recent_gws:]
            ]) if len(m2_current) >= recent_gws else 50
            
            form_diff = (m1_recent_avg - m2_recent_avg) / 50  # Normalize
            form_score = max(-1, min(1, form_diff))
        else:
            form_score = 0
        
        # Calculate weighted psychological edge
        psychological_edge = (
            recent_form_score * self.psychological_weights['recent_form'] +
            dominance_score * self.psychological_weights['head_to_head'] +
            streak_score * self.psychological_weights['momentum'] +
            form_score * self.psychological_weights['consistency']
        )
        
        # Determine who has the edge
        if psychological_edge > 0.2:
            edge_holder = 'manager1'
            edge_strength = 'strong' if psychological_edge > 0.5 else 'slight'
        elif psychological_edge < -0.2:
            edge_holder = 'manager2'
            edge_strength = 'strong' if psychological_edge < -0.5 else 'slight'
        else:
            edge_holder = None
            edge_strength = 'neutral'
        
        return {
            "psychological_edge_score": round(psychological_edge, 3),
            "edge_holder": edge_holder,
            "edge_strength": edge_strength,
            "contributing_factors": {
                "recent_h2h_form": round(recent_form_score, 2),
                "historical_dominance": round(dominance_score, 2),
                "current_streak": round(streak_score, 2),
                "season_form": round(form_score, 2)
            },
            "confidence": self._calculate_confidence(h2h_record, patterns)
        }
    
    async def _analyze_chip_patterns(
        self,
        m1_season: Dict[str, Any],
        m2_season: Dict[str, Any],
        h2h_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze chip usage patterns"""
        m1_chips = m1_season.get('chips', [])
        m2_chips = m2_season.get('chips', [])
        
        # Categorize chip usage
        chip_categories = {
            'early': [],  # GW 1-10
            'mid': [],    # GW 11-28
            'late': []    # GW 29-38
        }
        
        for chip in m1_chips:
            gw = chip['event']
            if gw <= 10:
                chip_categories['early'].append(('manager1', chip['name']))
            elif gw <= 28:
                chip_categories['mid'].append(('manager1', chip['name']))
            else:
                chip_categories['late'].append(('manager1', chip['name']))
        
        for chip in m2_chips:
            gw = chip['event']
            if gw <= 10:
                chip_categories['early'].append(('manager2', chip['name']))
            elif gw <= 28:
                chip_categories['mid'].append(('manager2', chip['name']))
            else:
                chip_categories['late'].append(('manager2', chip['name']))
        
        # Analyze chip effectiveness in H2H context
        chip_effectiveness = {}
        for chip in m1_chips + m2_chips:
            # Find H2H match in that gameweek
            h2h_match = next(
                (m for m in h2h_history if m['event'] == chip['event']), 
                None
            )
            if h2h_match:
                manager = 'manager1' if chip in m1_chips else 'manager2'
                won = (
                    (manager == 'manager1' and h2h_match['entry_1_points'] > h2h_match['entry_2_points']) or
                    (manager == 'manager2' and h2h_match['entry_2_points'] > h2h_match['entry_1_points'])
                )
                
                if chip['name'] not in chip_effectiveness:
                    chip_effectiveness[chip['name']] = {'used': 0, 'won': 0}
                
                chip_effectiveness[chip['name']]['used'] += 1
                if won:
                    chip_effectiveness[chip['name']]['won'] += 1
        
        # Calculate success rates
        for chip_name, stats in chip_effectiveness.items():
            if stats['used'] > 0:
                stats['success_rate'] = stats['won'] / stats['used']
        
        return {
            "manager1_chips_used": [c['name'] for c in m1_chips],
            "manager2_chips_used": [c['name'] for c in m2_chips],
            "chip_timing_preference": {
                "manager1": self._determine_chip_timing_preference(m1_chips),
                "manager2": self._determine_chip_timing_preference(m2_chips)
            },
            "chip_effectiveness_h2h": chip_effectiveness,
            "remaining_chips": {
                "manager1": self._get_remaining_chips(m1_chips),
                "manager2": self._get_remaining_chips(m2_chips)
            }
        }
    
    async def _analyze_performance_patterns(
        self,
        m1_season: Dict[str, Any],
        m2_season: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze performance patterns throughout the season"""
        m1_current = m1_season.get('current', [])
        m2_current = m2_season.get('current', [])
        
        if not m1_current or not m2_current:
            return {}
        
        # Calculate rolling averages
        window = 5
        m1_rolling = []
        m2_rolling = []
        
        for i in range(window, len(m1_current)):
            m1_avg = statistics.mean([m1_current[j]['points'] for j in range(i-window, i)])
            m1_rolling.append(m1_avg)
        
        for i in range(window, len(m2_current)):
            m2_avg = statistics.mean([m2_current[j]['points'] for j in range(i-window, i)])
            m2_rolling.append(m2_avg)
        
        # Identify trends
        m1_trend = 'improving' if m1_rolling and m1_rolling[-1] > m1_rolling[0] else 'declining'
        m2_trend = 'improving' if m2_rolling and m2_rolling[-1] > m2_rolling[0] else 'declining'
        
        # Peak performance
        m1_peak = max([gw['points'] for gw in m1_current]) if m1_current else 0
        m2_peak = max([gw['points'] for gw in m2_current]) if m2_current else 0
        
        # Consistency (lower is better)
        m1_consistency = statistics.stdev([gw['points'] for gw in m1_current]) if len(m1_current) > 1 else 0
        m2_consistency = statistics.stdev([gw['points'] for gw in m2_current]) if len(m2_current) > 1 else 0
        
        return {
            "season_trends": {
                "manager1": m1_trend,
                "manager2": m2_trend
            },
            "peak_performance": {
                "manager1": m1_peak,
                "manager2": m2_peak
            },
            "consistency_score": {
                "manager1": round(100 - m1_consistency, 1),  # Convert to 0-100 scale
                "manager2": round(100 - m2_consistency, 1)
            },
            "current_form": {
                "manager1": m1_rolling[-1] if m1_rolling else 0,
                "manager2": m2_rolling[-1] if m2_rolling else 0
            }
        }
    
    async def _generate_matchup_summary(
        self,
        h2h_record: H2HRecord,
        patterns: List[PatternInsight],
        psychological_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a summary of the matchup dynamics"""
        key_factors = []
        
        # H2H dominance
        if h2h_record.total_matches >= 5:
            win_rate = h2h_record.manager1_wins / h2h_record.total_matches
            if win_rate > 0.65:
                key_factors.append("Manager 1 has historical dominance")
            elif win_rate < 0.35:
                key_factors.append("Manager 2 has historical dominance")
        
        # Current form
        if h2h_record.recent_form_advantage:
            key_factors.append(f"{h2h_record.recent_form_advantage} has better recent form")
        
        # Streaks
        if h2h_record.current_streak['count'] >= 3:
            key_factors.append(f"{h2h_record.current_streak['manager']} on {h2h_record.current_streak['count']}-match winning streak")
        
        # Key patterns
        high_impact_patterns = [p for p in patterns if p.impact == 'high']
        for pattern in high_impact_patterns[:2]:  # Top 2 patterns
            key_factors.append(pattern.description)
        
        return {
            "rivalry_intensity": self._calculate_rivalry_intensity(h2h_record),
            "predictability": self._calculate_predictability(h2h_record, patterns),
            "key_factors": key_factors,
            "recommended_focus": self._get_recommended_focus(patterns, psychological_analysis)
        }
    
    def _calculate_confidence(
        self,
        h2h_record: H2HRecord,
        patterns: List[PatternInsight]
    ) -> float:
        """Calculate confidence in psychological analysis"""
        base_confidence = min(0.5 + (h2h_record.total_matches * 0.05), 0.9)
        pattern_boost = len(patterns) * 0.05
        return min(base_confidence + pattern_boost, 0.95)
    
    def _determine_chip_timing_preference(self, chips: List[Dict[str, Any]]) -> str:
        """Determine if manager prefers early/mid/late chip usage"""
        if not chips:
            return "none_used"
        
        early = sum(1 for c in chips if c['event'] <= 10)
        mid = sum(1 for c in chips if 10 < c['event'] <= 28)
        late = sum(1 for c in chips if c['event'] > 28)
        
        if early > mid and early > late:
            return "early_user"
        elif late > early and late > mid:
            return "late_user"
        else:
            return "balanced"
    
    def _get_remaining_chips(self, used_chips: List[Dict[str, Any]]) -> List[str]:
        """Get list of remaining chips"""
        all_chips = {'wildcard', 'bboost', 'freehit', '3xc'}
        used = {c['name'] for c in used_chips}
        
        # Wildcard can be used twice
        if used.count('wildcard') < 2:
            remaining = list(all_chips - used)
            if 'wildcard' not in remaining and used.count('wildcard') == 1:
                remaining.append('wildcard')
        else:
            remaining = list(all_chips - used)
        
        return remaining
    
    def _calculate_rivalry_intensity(self, h2h_record: H2HRecord) -> str:
        """Calculate how intense the rivalry is"""
        if h2h_record.total_matches < 5:
            return "developing"
        
        # Check competitiveness
        total = h2h_record.total_matches
        close_ratio = max(h2h_record.manager1_wins, h2h_record.manager2_wins) / total
        
        if close_ratio < 0.6 and h2h_record.avg_margin < 15:
            return "intense"
        elif close_ratio > 0.75:
            return "one-sided"
        else:
            return "competitive"
    
    def _calculate_predictability(
        self,
        h2h_record: H2HRecord,
        patterns: List[PatternInsight]
    ) -> str:
        """Calculate how predictable the matchup is"""
        if h2h_record.total_matches < 3:
            return "unknown"
        
        # High confidence patterns make it more predictable
        high_conf_patterns = [p for p in patterns if p.confidence > 0.7]
        
        if len(high_conf_patterns) >= 2:
            return "predictable"
        elif h2h_record.draws / h2h_record.total_matches > 0.3:
            return "unpredictable"
        else:
            return "moderate"
    
    def _get_recommended_focus(
        self,
        patterns: List[PatternInsight],
        psychological_analysis: Dict[str, Any]
    ) -> List[str]:
        """Get recommended areas to focus on"""
        recommendations = []
        
        # Based on psychological edge
        if psychological_analysis['edge_holder']:
            if psychological_analysis['edge_strength'] == 'strong':
                recommendations.append("Leverage psychological advantage" if psychological_analysis['edge_holder'] == 'manager1' else "Overcome psychological deficit")
        
        # Based on patterns
        for pattern in patterns:
            if pattern.pattern_type == "consistency_difference":
                recommendations.append("Focus on consistent returns")
            elif pattern.pattern_type == "momentum_dependent":
                recommendations.append("Maintain positive momentum")
        
        return recommendations[:3]  # Top 3 recommendations
    
    def _serialize_h2h_record(self, record: H2HRecord) -> Dict[str, Any]:
        """Serialize H2H record to dict"""
        return {
            "total_matches": record.total_matches,
            "results": {
                "manager1_wins": record.manager1_wins,
                "manager2_wins": record.manager2_wins,
                "draws": record.draws
            },
            "statistics": {
                "average_margin": round(record.avg_margin, 1),
                "biggest_manager1_win": {
                    "margin": record.biggest_m1_win[0],
                    "score": f"{record.biggest_m1_win[1]}-{record.biggest_m1_win[2]}"
                },
                "biggest_manager2_win": {
                    "margin": record.biggest_m2_win[0],
                    "score": f"{record.biggest_m2_win[1]}-{record.biggest_m2_win[2]}"
                }
            },
            "streaks": {
                "current": record.current_streak,
                "longest_win_streak_manager1": record.longest_win_streak_m1,
                "longest_win_streak_manager2": record.longest_win_streak_m2
            },
            "recent_form": {
                "last_5_results": record.last_5_results,
                "advantage": record.recent_form_advantage
            }
        }
    
    def _serialize_pattern(self, pattern: PatternInsight) -> Dict[str, Any]:
        """Serialize pattern to dict"""
        return {
            "type": pattern.pattern_type,
            "description": pattern.description,
            "confidence": pattern.confidence,
            "impact": pattern.impact,
            "data": pattern.data
        }