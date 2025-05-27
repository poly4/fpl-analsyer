from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime
from collections import Counter, defaultdict
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PatternRecognition:
    """
    Service for analyzing historical patterns in FPL manager behavior and H2H matchups.
    Identifies transfer patterns, captaincy tendencies, form cycles, and H2H dynamics.
    """
    
    def __init__(self):
        """
        Initialize the Pattern Recognition service.
        
        Note: Can accept LiveDataService for fetching additional historical data.
        """
        logger.info("PatternRecognition initialized")
        
        # Pattern thresholds
        self.consistency_threshold = 0.7  # 70% consistency for a pattern
        self.form_streak_threshold = 3    # Minimum gameweeks for a streak
        self.hit_frequency_high = 0.3     # 30%+ hits = aggressive
        self.captain_differential_threshold = 0.2  # 20%+ differential captains
    
    async def analyze_manager_patterns(
        self,
        manager_id: int,
        manager_history: Dict[str, Any],
        transfer_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Analyze overall patterns for a manager combining multiple analyses.
        
        Args:
            manager_id: Manager ID
            manager_history: Manager's historical data
            transfer_history: Optional transfer history
            
        Returns:
            Dict with comprehensive pattern analysis
        """
        logger.info(f"Analyzing patterns for manager {manager_id}")
        
        # Get current season data
        current_season = manager_history.get('current', [])
        
        # Analyze different pattern types
        transfer_patterns = await self._analyze_transfer_patterns(
            manager_id, current_season, transfer_history
        )
        
        captaincy_patterns = self._analyze_captaincy_patterns_from_history(
            manager_id, current_season
        )
        
        form_patterns = self._analyze_form_patterns(
            manager_id, current_season
        )
        
        # Calculate consistency score
        consistency_score = self._calculate_consistency_score(current_season)
        
        # Identify key pattern
        key_pattern = self._identify_key_pattern(
            transfer_patterns, captaincy_patterns, form_patterns
        )
        
        return {
            "manager_id": manager_id,
            "transfer_patterns": transfer_patterns,
            "captaincy_patterns": captaincy_patterns,
            "form_patterns": form_patterns,
            "consistency_score": consistency_score,
            "key_pattern": key_pattern,
            "form_trajectory": form_patterns.get("current_trajectory", "stable"),
            "risk_profile": self._determine_risk_profile(
                transfer_patterns, captaincy_patterns
            )
        }
    
    async def _analyze_transfer_patterns(
        self,
        manager_id: int,
        season_history: List[Dict[str, Any]],
        transfer_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Analyze transfer patterns including frequency, timing, and hit-taking.
        
        Returns:
            Dict with transfer pattern analysis
        """
        total_gameweeks = len(season_history)
        if total_gameweeks == 0:
            return self._empty_transfer_patterns()
        
        # Analyze from gameweek history
        total_transfers = 0
        total_hits = 0
        hit_gameweeks = []
        transfer_costs = []
        
        for i, gw in enumerate(season_history):
            transfers = gw.get('event_transfers', 0)
            cost = gw.get('event_transfers_cost', 0)
            
            total_transfers += transfers
            if cost > 0:
                total_hits += 1
                hit_gameweeks.append(i + 1)
                transfer_costs.append(cost)
        
        # Calculate metrics
        avg_transfers_per_gw = total_transfers / total_gameweeks if total_gameweeks > 0 else 0
        hit_frequency = total_hits / total_gameweeks if total_gameweeks > 0 else 0
        avg_hit_cost = statistics.mean(transfer_costs) if transfer_costs else 0
        
        # Analyze hit-taking context
        hit_context = self._analyze_hit_context(season_history, hit_gameweeks)
        
        # Common patterns
        patterns = []
        if hit_frequency > self.hit_frequency_high:
            patterns.append("Aggressive hit-taker")
        elif hit_frequency < 0.1:
            patterns.append("Conservative - rarely takes hits")
        
        if hit_context.get("after_bad_gw_rate", 0) > 0.5:
            patterns.append("Reactive - takes hits after poor gameweeks")
        
        return {
            "average_transfers_per_gw": round(avg_transfers_per_gw, 2),
            "hit_analysis": {
                "total_hits_taken": total_hits,
                "hit_frequency": round(hit_frequency, 2),
                "average_hit_cost": avg_hit_cost,
                "total_points_spent": sum(transfer_costs),
                "hit_context": hit_context
            },
            "patterns": patterns,
            "transfer_style": self._classify_transfer_style(
                avg_transfers_per_gw, hit_frequency
            )
        }
    
    def _analyze_hit_context(
        self,
        season_history: List[Dict[str, Any]],
        hit_gameweeks: List[int]
    ) -> Dict[str, Any]:
        """Analyze the context in which hits are taken."""
        if not hit_gameweeks or len(season_history) < 2:
            return {"after_bad_gw_rate": 0, "pattern": "Insufficient data"}
        
        after_bad_gw = 0
        after_good_gw = 0
        
        # Define bad gameweek as below average
        scores = [gw.get('points', 0) for gw in season_history]
        avg_score = statistics.mean(scores) if scores else 50
        
        for hit_gw in hit_gameweeks:
            if hit_gw > 1:  # Can check previous gameweek
                prev_score = season_history[hit_gw - 2].get('points', 0)
                if prev_score < avg_score:
                    after_bad_gw += 1
                else:
                    after_good_gw += 1
        
        total_hits_with_context = after_bad_gw + after_good_gw
        after_bad_rate = after_bad_gw / total_hits_with_context if total_hits_with_context > 0 else 0
        
        pattern = "Reactive" if after_bad_rate > 0.6 else "Strategic"
        
        return {
            "after_bad_gw_rate": round(after_bad_rate, 2),
            "pattern": pattern,
            "hits_after_bad_gw": after_bad_gw,
            "hits_after_good_gw": after_good_gw
        }
    
    def _classify_transfer_style(
        self,
        avg_transfers: float,
        hit_frequency: float
    ) -> str:
        """Classify overall transfer style."""
        if avg_transfers > 1.5 and hit_frequency > 0.3:
            return "Very Active - Frequent transfers with hits"
        elif avg_transfers > 1.2:
            return "Active - Regular transfers"
        elif avg_transfers < 0.8:
            return "Passive - Minimal transfers"
        else:
            return "Balanced - Moderate transfer activity"
    
    def _analyze_captaincy_patterns_from_history(
        self,
        manager_id: int,
        season_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze captaincy patterns from season history.
        Note: Limited without detailed picks data.
        """
        # This is simplified - would need actual captain picks data
        captain_points = []
        total_points = []
        
        for gw in season_history:
            # Estimate captain contribution (very rough)
            gw_points = gw.get('points', 0)
            bench_points = gw.get('points_on_bench', 0)
            active_points = gw_points - bench_points
            
            # Rough estimate: captain contributes ~20-30% of points
            estimated_captain_points = active_points * 0.25
            captain_points.append(estimated_captain_points)
            total_points.append(gw_points)
        
        # Calculate metrics
        avg_captain_contribution = (
            sum(captain_points) / sum(total_points) 
            if sum(total_points) > 0 else 0
        )
        
        # Simplified risk profile
        risk_profile = "Moderate"  # Default without actual captain data
        
        return {
            "estimated_captain_contribution": round(avg_captain_contribution, 2),
            "risk_profile": risk_profile,
            "notes": "Limited analysis without detailed captain picks data"
        }
    
    def _analyze_form_patterns(
        self,
        manager_id: int,
        season_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze form cycles and patterns."""
        if len(season_history) < 3:
            return {
                "current_form": "Unknown",
                "current_trajectory": "Unknown",
                "patterns": []
            }
        
        # Get points history
        points = [gw.get('points', 0) for gw in season_history]
        
        # Calculate rolling averages
        window_size = min(5, len(points))
        if len(points) >= window_size:
            rolling_avg = self._calculate_rolling_average(points, window_size)
        else:
            rolling_avg = points
        
        # Analyze current form
        recent_points = points[-5:] if len(points) >= 5 else points
        season_avg = statistics.mean(points)
        recent_avg = statistics.mean(recent_points)
        
        # Determine form status
        if recent_avg > season_avg * 1.1:
            current_form = "Excellent"
        elif recent_avg > season_avg:
            current_form = "Good"
        elif recent_avg < season_avg * 0.9:
            current_form = "Poor"
        else:
            current_form = "Average"
        
        # Analyze trajectory
        if len(recent_points) >= 3:
            first_half = statistics.mean(recent_points[:len(recent_points)//2])
            second_half = statistics.mean(recent_points[len(recent_points)//2:])
            
            if second_half > first_half * 1.1:
                trajectory = "improving"
            elif second_half < first_half * 0.9:
                trajectory = "declining"
            else:
                trajectory = "stable"
        else:
            trajectory = "stable"
        
        # Find streaks
        good_streaks, bad_streaks = self._find_form_streaks(points, season_avg)
        
        return {
            "season_average": round(season_avg, 1),
            "recent_average": round(recent_avg, 1),
            "current_form": current_form,
            "current_trajectory": trajectory,
            "longest_good_streak": max(good_streaks) if good_streaks else 0,
            "longest_bad_streak": max(bad_streaks) if bad_streaks else 0,
            "volatility": round(statistics.stdev(points), 1) if len(points) > 1 else 0,
            "consistency_rating": self._calculate_form_consistency(points)
        }
    
    def _calculate_rolling_average(
        self,
        values: List[float],
        window: int
    ) -> List[float]:
        """Calculate rolling average."""
        rolling_avg = []
        for i in range(len(values) - window + 1):
            window_avg = statistics.mean(values[i:i + window])
            rolling_avg.append(window_avg)
        return rolling_avg
    
    def _find_form_streaks(
        self,
        points: List[float],
        average: float
    ) -> Tuple[List[int], List[int]]:
        """Find good and bad form streaks."""
        good_streaks = []
        bad_streaks = []
        current_good = 0
        current_bad = 0
        
        for point in points:
            if point > average:
                current_good += 1
                if current_bad > 0:
                    bad_streaks.append(current_bad)
                    current_bad = 0
            else:
                current_bad += 1
                if current_good > 0:
                    good_streaks.append(current_good)
                    current_good = 0
        
        # Add final streaks
        if current_good > 0:
            good_streaks.append(current_good)
        if current_bad > 0:
            bad_streaks.append(current_bad)
        
        return good_streaks, bad_streaks
    
    def _calculate_form_consistency(self, points: List[float]) -> str:
        """Calculate form consistency rating."""
        if len(points) < 2:
            return "Unknown"
        
        std_dev = statistics.stdev(points)
        mean = statistics.mean(points)
        cv = std_dev / mean if mean > 0 else 0  # Coefficient of variation
        
        if cv < 0.2:
            return "Very Consistent"
        elif cv < 0.3:
            return "Consistent"
        elif cv < 0.4:
            return "Moderate"
        else:
            return "Volatile"
    
    def _calculate_consistency_score(
        self,
        season_history: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall consistency score (0-100)."""
        if len(season_history) < 5:
            return 50.0  # Default for insufficient data
        
        points = [gw.get('points', 0) for gw in season_history]
        ranks = [gw.get('overall_rank', 0) for gw in season_history if gw.get('overall_rank')]
        
        # Points consistency (lower CV is better)
        points_cv = statistics.stdev(points) / statistics.mean(points) if statistics.mean(points) > 0 else 1
        points_score = max(0, 100 - (points_cv * 100))
        
        # Rank consistency (smaller rank changes are better)
        if len(ranks) > 1:
            rank_changes = [abs(ranks[i] - ranks[i-1]) for i in range(1, len(ranks))]
            avg_rank_change = statistics.mean(rank_changes)
            # Normalize (assume 100k change is bad, 10k is good)
            rank_score = max(0, 100 - (avg_rank_change / 1000))
        else:
            rank_score = 50
        
        # Combined score
        consistency_score = (points_score * 0.6 + rank_score * 0.4)
        
        return round(consistency_score, 1)
    
    def _identify_key_pattern(
        self,
        transfer_patterns: Dict[str, Any],
        captaincy_patterns: Dict[str, Any],
        form_patterns: Dict[str, Any]
    ) -> str:
        """Identify the most significant pattern for the manager."""
        key_patterns = []
        
        # Check transfer patterns
        if transfer_patterns.get("hit_analysis", {}).get("hit_frequency", 0) > 0.4:
            key_patterns.append("Heavy hit-taker - aggressive transfer strategy")
        
        # Check form patterns
        if form_patterns.get("current_trajectory") == "improving":
            key_patterns.append("On the rise - improving form trajectory")
        elif form_patterns.get("longest_good_streak", 0) >= 5:
            key_patterns.append("Streak player - capable of sustained excellence")
        
        # Check consistency
        if form_patterns.get("consistency_rating") == "Very Consistent":
            key_patterns.append("Mr. Reliable - very consistent performer")
        elif form_patterns.get("consistency_rating") == "Volatile":
            key_patterns.append("Boom or bust - highly volatile scores")
        
        # Return most relevant pattern
        return key_patterns[0] if key_patterns else "Balanced approach - no dominant pattern"
    
    def _determine_risk_profile(
        self,
        transfer_patterns: Dict[str, Any],
        captaincy_patterns: Dict[str, Any]
    ) -> str:
        """Determine overall risk profile."""
        risk_score = 0
        
        # Transfer risk
        hit_freq = transfer_patterns.get("hit_analysis", {}).get("hit_frequency", 0)
        if hit_freq > 0.3:
            risk_score += 2
        elif hit_freq > 0.15:
            risk_score += 1
        
        # Captaincy risk (limited data)
        captain_profile = captaincy_patterns.get("risk_profile", "Moderate")
        if captain_profile == "High":
            risk_score += 2
        elif captain_profile == "Low":
            risk_score -= 1
        
        # Classify
        if risk_score >= 3:
            return "High Risk"
        elif risk_score >= 1:
            return "Moderate Risk"
        else:
            return "Low Risk"
    
    async def analyze_h2h_patterns(
        self,
        manager1_id: int,
        manager2_id: int,
        historical_h2h_matches: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze patterns specific to H2H encounters between two managers.
        
        Args:
            manager1_id: First manager ID
            manager2_id: Second manager ID
            historical_h2h_matches: List of past H2H matches
            
        Returns:
            Dict with H2H pattern analysis
        """
        if not historical_h2h_matches:
            return {
                "manager1_id": manager1_id,
                "manager2_id": manager2_id,
                "matches_analyzed": 0,
                "h2h_record": {"manager1_wins": 0, "manager2_wins": 0, "draws": 0},
                "patterns": ["No historical H2H data available"],
                "trend": "Unknown"
            }
        
        # Analyze H2H record
        m1_wins = 0
        m2_wins = 0
        draws = 0
        m1_scores = []
        m2_scores = []
        score_differences = []
        
        for match in historical_h2h_matches:
            m1_score = match.get('manager1_score', 0)
            m2_score = match.get('manager2_score', 0)
            
            m1_scores.append(m1_score)
            m2_scores.append(m2_score)
            score_differences.append(m1_score - m2_score)
            
            if m1_score > m2_score:
                m1_wins += 1
            elif m2_score > m1_score:
                m2_wins += 1
            else:
                draws += 1
        
        # Calculate averages
        avg_m1_score = statistics.mean(m1_scores) if m1_scores else 0
        avg_m2_score = statistics.mean(m2_scores) if m2_scores else 0
        avg_margin = statistics.mean(score_differences) if score_differences else 0
        
        # Determine patterns
        patterns = []
        dominant_manager = None
        
        total_matches = len(historical_h2h_matches)
        if m1_wins / total_matches > 0.6:
            patterns.append(f"Manager {manager1_id} dominates this matchup")
            dominant_manager = manager1_id
        elif m2_wins / total_matches > 0.6:
            patterns.append(f"Manager {manager2_id} dominates this matchup")
            dominant_manager = manager2_id
        else:
            patterns.append("Evenly matched historically")
        
        # Check for trends
        recent_matches = historical_h2h_matches[-3:] if len(historical_h2h_matches) >= 3 else historical_h2h_matches
        recent_m1_wins = sum(1 for m in recent_matches if m.get('manager1_score', 0) > m.get('manager2_score', 0))
        recent_m2_wins = sum(1 for m in recent_matches if m.get('manager2_score', 0) > m.get('manager1_score', 0))
        
        if recent_m1_wins > recent_m2_wins:
            trend = f"Manager {manager1_id} trending upward"
        elif recent_m2_wins > recent_m1_wins:
            trend = f"Manager {manager2_id} trending upward"
        else:
            trend = "No clear recent trend"
        
        # Check for close matches
        close_matches = sum(1 for diff in score_differences if abs(diff) <= 5)
        if close_matches / total_matches > 0.5:
            patterns.append("Typically very close matches")
        
        return {
            "manager1_id": manager1_id,
            "manager2_id": manager2_id,
            "matches_analyzed": total_matches,
            "h2h_record": {
                "manager1_wins": m1_wins,
                "manager2_wins": m2_wins,
                "draws": draws
            },
            "average_scores": {
                "manager1": round(avg_m1_score, 1),
                "manager2": round(avg_m2_score, 1)
            },
            "average_margin": round(abs(avg_margin), 1),
            "dominant_manager": dominant_manager,
            "patterns": patterns,
            "trend": trend,
            "close_match_rate": round(close_matches / total_matches, 2) if total_matches > 0 else 0
        }
    
    def _empty_transfer_patterns(self) -> Dict[str, Any]:
        """Return empty transfer patterns structure."""
        return {
            "average_transfers_per_gw": 0,
            "hit_analysis": {
                "total_hits_taken": 0,
                "hit_frequency": 0,
                "average_hit_cost": 0,
                "total_points_spent": 0,
                "hit_context": {"after_bad_gw_rate": 0, "pattern": "No data"}
            },
            "patterns": [],
            "transfer_style": "Unknown"
        }