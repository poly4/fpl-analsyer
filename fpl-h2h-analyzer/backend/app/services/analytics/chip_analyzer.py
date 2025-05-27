from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChipAnalyzer:
    """
    Service for analyzing and recommending optimal FPL chip usage strategies.
    Considers fixture difficulty, team form, and H2H context.
    """
    
    def __init__(self):
        """
        Initialize the Chip Analyzer.
        
        Note: Can accept LiveDataService and PredictiveEngine for enhanced analysis.
        """
        logger.info("ChipAnalyzer initialized")
        
        # Chip definitions
        self.chips = {
            'wildcard': {'name': 'Wildcard', 'code': 'wildcard'},
            'bboost': {'name': 'Bench Boost', 'code': 'bboost'},
            '3xc': {'name': 'Triple Captain', 'code': '3xc'},
            'freehit': {'name': 'Free Hit', 'code': 'freehit'}
        }
        
        # Strategic value thresholds
        self.dgw_threshold = 1.5  # Teams playing more than 1.5x games
        self.bgw_threshold = 0.5  # Teams playing less than 0.5x games
        self.fixture_swing_threshold = 2.0  # Average difficulty change threshold
        
    async def _get_available_chips(
        self,
        manager_id: int,
        manager_history: Dict[str, Any]
    ) -> List[str]:
        """
        Determine which chips are still available for the manager.
        
        Args:
            manager_id: Manager ID
            manager_history: Manager's historical data
            
        Returns:
            List of available chip codes
        """
        # Get chips used from history
        chips_used = set()
        
        # Check current season's chip usage
        current_season = manager_history.get('current', [])
        for gw_data in current_season:
            if gw_data.get('event_transfers_cost', 0) == 0 and gw_data.get('event_transfers', 0) > 1:
                # Likely a wildcard or free hit
                chips_used.add('wildcard')
            
            chip = gw_data.get('chip')
            if chip:
                chips_used.add(chip)
        
        # Check chips history
        chips_history = manager_history.get('chips', [])
        for chip_usage in chips_history:
            chip_name = chip_usage.get('name', '').lower()
            if 'wildcard' in chip_name:
                chips_used.add('wildcard')
            elif 'bench' in chip_name:
                chips_used.add('bboost')
            elif 'triple' in chip_name:
                chips_used.add('3xc')
            elif 'free' in chip_name:
                chips_used.add('freehit')
        
        # Determine available chips
        # Note: Typically get 2 wildcards per season (one per half)
        available = []
        
        # Check if first wildcard used
        wildcard_count = sum(1 for c in chips_history if 'wildcard' in c.get('name', '').lower())
        if wildcard_count < 2:
            available.append('wildcard')
        
        # Other chips are one per season
        if 'bboost' not in chips_used:
            available.append('bboost')
        if '3xc' not in chips_used:
            available.append('3xc')
        if 'freehit' not in chips_used:
            available.append('freehit')
        
        return available
    
    async def _estimate_bench_boost_value(
        self,
        manager_id: int,
        gameweek: int,
        manager_picks_data: Dict[str, Any],
        fixture_difficulties: Dict[int, float],
        bootstrap_data: Dict[str, Any]
    ) -> float:
        """
        Estimate the value of using Bench Boost chip.
        
        Args:
            manager_id: Manager ID
            gameweek: Target gameweek
            manager_picks_data: Current picks
            fixture_difficulties: Fixture difficulties by team
            bootstrap_data: Bootstrap static data
            
        Returns:
            Estimated point gain from Bench Boost
        """
        if not manager_picks_data or 'picks' not in manager_picks_data:
            return 0.0
        
        players = {p['id']: p for p in bootstrap_data.get('elements', [])}
        bench_value = 0.0
        
        # Calculate expected points for bench players
        for pick in manager_picks_data.get('picks', []):
            if pick['position'] > 11:  # Bench players
                player_id = pick['element']
                player = players.get(player_id, {})
                
                if not player:
                    continue
                
                # Get player's expected points based on form and fixture
                form = float(player.get('form', 0))
                team_id = player.get('team')
                fixture_diff = fixture_difficulties.get(team_id, 3)
                
                # Simple estimation: form adjusted by fixture difficulty
                fixture_multiplier = {
                    1: 1.3,   # Very easy
                    2: 1.15,  # Easy
                    3: 1.0,   # Average
                    4: 0.85,  # Hard
                    5: 0.7    # Very hard
                }.get(int(fixture_diff), 1.0)
                
                expected_points = form * fixture_multiplier
                
                # Reduce expectation for typically low-scoring positions
                position_type = player.get('element_type')
                if position_type == 1:  # GKP
                    expected_points *= 0.8
                
                bench_value += expected_points
        
        return round(bench_value, 1)
    
    async def _estimate_triple_captain_value(
        self,
        manager_id: int,
        gameweek: int,
        manager_picks_data: Dict[str, Any],
        fixture_difficulties: Dict[int, float],
        bootstrap_data: Dict[str, Any]
    ) -> float:
        """
        Estimate the value of using Triple Captain chip.
        
        Args:
            manager_id: Manager ID
            gameweek: Target gameweek
            manager_picks_data: Current picks
            fixture_difficulties: Fixture difficulties by team
            bootstrap_data: Bootstrap static data
            
        Returns:
            Estimated additional points from Triple Captain
        """
        if not manager_picks_data or 'picks' not in manager_picks_data:
            return 0.0
        
        players = {p['id']: p for p in bootstrap_data.get('elements', [])}
        
        # Find the captain
        captain_pick = None
        for pick in manager_picks_data.get('picks', []):
            if pick.get('is_captain'):
                captain_pick = pick
                break
        
        if not captain_pick:
            return 0.0
        
        player_id = captain_pick['element']
        player = players.get(player_id, {})
        
        if not player:
            return 0.0
        
        # Estimate captain's expected points
        form = float(player.get('form', 0))
        team_id = player.get('team')
        fixture_diff = fixture_difficulties.get(team_id, 3)
        
        # Fixture difficulty multiplier
        fixture_multiplier = {
            1: 1.4,   # Very easy - higher multiplier for captain
            2: 1.2,   # Easy
            3: 1.0,   # Average
            4: 0.8,   # Hard
            5: 0.6    # Very hard
        }.get(int(fixture_diff), 1.0)
        
        expected_captain_points = form * fixture_multiplier
        
        # Premium players tend to be more reliable captains
        if player.get('now_cost', 0) > 110:  # 11.0m+
            expected_captain_points *= 1.1
        
        # Penalty takers get a boost
        if player.get('penalties_order') == 1:
            expected_captain_points *= 1.15
        
        # Triple captain adds 1x the captain's score (from 2x to 3x)
        triple_captain_value = expected_captain_points
        
        return round(triple_captain_value, 1)
    
    async def get_chip_recommendations(
        self,
        manager_id: int,
        manager_history: Dict[str, Any],
        fixture_data: List[Dict[str, Any]],
        gameweek: int,
        h2h_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get strategic chip recommendations for a manager.
        
        Args:
            manager_id: Manager ID
            manager_history: Manager's historical data
            fixture_data: Fixture information
            gameweek: Current gameweek
            h2h_context: H2H specific context (opponent chip status, score difference)
            
        Returns:
            Dict with chip recommendations and analysis
        """
        logger.info(f"Generating chip recommendations for manager {manager_id}, GW{gameweek}")
        
        # Get available chips
        available_chips = await self._get_available_chips(manager_id, manager_history)
        
        if not available_chips:
            return {
                "manager_id": manager_id,
                "available_chips": [],
                "recommendations": [],
                "immediate_recommendation": None,
                "h2h_context_note": "All chips have been used"
            }
        
        recommendations = []
        
        # Analyze fixture landscape
        fixture_analysis = self._analyze_fixtures(fixture_data, gameweek)
        
        # Get current team data (simplified - would need actual picks data)
        # For now, we'll make recommendations based on general principles
        
        # Bench Boost recommendation
        if 'bboost' in available_chips:
            bb_recommendation = await self._analyze_bench_boost_opportunity(
                gameweek, fixture_analysis, h2h_context
            )
            if bb_recommendation:
                recommendations.append(bb_recommendation)
        
        # Triple Captain recommendation
        if '3xc' in available_chips:
            tc_recommendation = await self._analyze_triple_captain_opportunity(
                gameweek, fixture_analysis, h2h_context
            )
            if tc_recommendation:
                recommendations.append(tc_recommendation)
        
        # Free Hit recommendation
        if 'freehit' in available_chips:
            fh_recommendation = await self._analyze_free_hit_opportunity(
                gameweek, fixture_analysis, h2h_context
            )
            if fh_recommendation:
                recommendations.append(fh_recommendation)
        
        # Wildcard recommendation
        if 'wildcard' in available_chips:
            wc_recommendation = await self._analyze_wildcard_opportunity(
                gameweek, fixture_analysis, manager_history, h2h_context
            )
            if wc_recommendation:
                recommendations.append(wc_recommendation)
        
        # Sort by strategic value
        recommendations.sort(key=lambda x: x['strategic_value_score'], reverse=True)
        
        # Determine immediate recommendation
        immediate_rec = None
        if recommendations:
            top_rec = recommendations[0]
            if top_rec['strategic_value_score'] >= 4.0 and top_rec['gameweek_target'] == gameweek:
                immediate_rec = f"Use {top_rec['chip_name']} this gameweek"
        
        # H2H context notes
        h2h_notes = self._generate_h2h_notes(h2h_context, available_chips, recommendations)
        
        return {
            "manager_id": manager_id,
            "available_chips": available_chips,
            "recommendations": recommendations,
            "immediate_recommendation": immediate_rec,
            "h2h_context_note": h2h_notes,
            "fixture_outlook": fixture_analysis.get('summary', '')
        }
    
    def _analyze_fixtures(
        self,
        fixture_data: List[Dict[str, Any]],
        current_gameweek: int
    ) -> Dict[str, Any]:
        """Analyze fixture landscape for chip opportunities."""
        # Simplified fixture analysis
        # In reality, would parse fixture_data to identify DGWs, BGWs, fixture swings
        
        analysis = {
            "dgw_teams": [],  # Teams with double gameweeks
            "bgw_teams": [],  # Teams with blank gameweeks
            "easy_runs": [],  # Teams with easy fixture runs
            "hard_runs": [],  # Teams with difficult fixture runs
            "summary": ""
        }
        
        # Check for special gameweeks (simplified)
        # GW32-35 often have DGWs, GW33 often has BGW
        if 32 <= current_gameweek <= 35:
            analysis["dgw_teams"] = ["MCI", "CHE", "ARS"]  # Example
            analysis["summary"] = "Potential double gameweek opportunities"
        elif current_gameweek == 33:
            analysis["bgw_teams"] = ["LIV", "MUN", "TOT"]  # Example
            analysis["summary"] = "Blank gameweek for several teams"
        else:
            analysis["summary"] = "Standard gameweek fixtures"
        
        return analysis
    
    async def _analyze_bench_boost_opportunity(
        self,
        gameweek: int,
        fixture_analysis: Dict[str, Any],
        h2h_context: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Analyze Bench Boost opportunity."""
        strategic_value = 3.0  # Base value
        reasoning_parts = []
        
        # Check for double gameweek
        if fixture_analysis.get("dgw_teams"):
            strategic_value += 1.5
            reasoning_parts.append("Double gameweek opportunity")
        
        # H2H context
        if h2h_context:
            if h2h_context.get("is_leading") and h2h_context.get("score_difference", 0) < 10:
                strategic_value += 0.5
                reasoning_parts.append("Could extend narrow lead")
            elif not h2h_context.get("is_leading") and h2h_context.get("opponent_chip") == 'bboost':
                strategic_value += 1.0
                reasoning_parts.append("Counter opponent's Bench Boost")
        
        # End of season consideration
        if gameweek >= 35:
            strategic_value += 0.5
            reasoning_parts.append("Limited gameweeks remaining")
        
        if not reasoning_parts:
            reasoning_parts.append("Standard bench boost opportunity")
        
        return {
            "chip_name": "Bench Boost",
            "chip_code": "bboost",
            "gameweek_target": gameweek,
            "estimated_gain": 8.0,  # Simplified estimate
            "reasoning": "; ".join(reasoning_parts),
            "strategic_value_score": min(5.0, strategic_value)
        }
    
    async def _analyze_triple_captain_opportunity(
        self,
        gameweek: int,
        fixture_analysis: Dict[str, Any],
        h2h_context: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Analyze Triple Captain opportunity."""
        strategic_value = 3.0  # Base value
        reasoning_parts = []
        
        # Premium captain with easy fixture is ideal
        # This is simplified - would need actual fixture and player data
        if gameweek in [34, 35, 36, 37]:  # Often good fixture runs
            strategic_value += 1.0
            reasoning_parts.append("Premium captains have favorable fixtures")
        
        # Double gameweek for premium asset
        if fixture_analysis.get("dgw_teams"):
            strategic_value += 1.5
            reasoning_parts.append("Double gameweek for premium assets")
        
        # H2H context
        if h2h_context:
            if not h2h_context.get("is_leading"):
                strategic_value += 0.5
                reasoning_parts.append("Need to make up ground")
            
            if h2h_context.get("opponent_chip") == '3xc':
                strategic_value -= 0.5
                reasoning_parts.append("Opponent also using Triple Captain")
        
        if not reasoning_parts:
            reasoning_parts.append("Standard triple captain opportunity")
        
        return {
            "chip_name": "Triple Captain",
            "chip_code": "3xc",
            "gameweek_target": gameweek,
            "estimated_gain": 10.0,  # Simplified estimate
            "reasoning": "; ".join(reasoning_parts),
            "strategic_value_score": min(5.0, strategic_value)
        }
    
    async def _analyze_free_hit_opportunity(
        self,
        gameweek: int,
        fixture_analysis: Dict[str, Any],
        h2h_context: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Analyze Free Hit opportunity."""
        strategic_value = 2.5  # Base value (lower as it's more situational)
        reasoning_parts = []
        
        # Blank gameweek is prime Free Hit territory
        if fixture_analysis.get("bgw_teams"):
            strategic_value += 2.0
            reasoning_parts.append("Navigate blank gameweek")
        
        # Double gameweek with limited DGW players owned
        elif fixture_analysis.get("dgw_teams"):
            strategic_value += 1.0
            reasoning_parts.append("Target double gameweek players")
        
        # H2H desperation play
        if h2h_context and not h2h_context.get("is_leading"):
            score_diff = abs(h2h_context.get("score_difference", 0))
            if score_diff > 30:
                strategic_value += 1.0
                reasoning_parts.append("High-risk strategy needed in H2H")
        
        if not reasoning_parts:
            reasoning_parts.append("Save for blank/double gameweek")
            strategic_value = 2.0  # Lower value if no immediate need
        
        return {
            "chip_name": "Free Hit",
            "chip_code": "freehit",
            "gameweek_target": gameweek if strategic_value > 3.5 else "Future BGW/DGW",
            "estimated_gain": 15.0 if strategic_value > 3.5 else 0.0,
            "reasoning": "; ".join(reasoning_parts),
            "strategic_value_score": min(5.0, strategic_value)
        }
    
    async def _analyze_wildcard_opportunity(
        self,
        gameweek: int,
        fixture_analysis: Dict[str, Any],
        manager_history: Dict[str, Any],
        h2h_context: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Analyze Wildcard opportunity."""
        strategic_value = 3.0  # Base value
        reasoning_parts = []
        
        # Check team issues (simplified - would need actual team analysis)
        recent_scores = [gw.get('points', 0) for gw in manager_history.get('current', [])[-5:]]
        if recent_scores and sum(recent_scores) / len(recent_scores) < 45:
            strategic_value += 1.0
            reasoning_parts.append("Recent poor performance suggests team restructure needed")
        
        # Fixture swing opportunity
        if gameweek in [8, 9, 28, 29]:  # Common fixture swing points
            strategic_value += 1.0
            reasoning_parts.append("Major fixture swing opportunity")
        
        # Prepare for chip usage
        if gameweek <= 30:
            strategic_value += 0.5
            reasoning_parts.append("Set up team for future chip usage")
        
        # H2H context
        if h2h_context and not h2h_context.get("is_leading"):
            strategic_value += 0.5
            reasoning_parts.append("Fresh team could turn H2H fortunes")
        
        if not reasoning_parts:
            reasoning_parts.append("General team improvement opportunity")
        
        # Determine target gameweek range
        if strategic_value >= 4.0:
            target = f"GW{gameweek}"
        else:
            target = f"GW{gameweek+2}-GW{gameweek+4}"
        
        return {
            "chip_name": "Wildcard",
            "chip_code": "wildcard",
            "gameweek_target": target,
            "estimated_gain": 0.0,  # Hard to quantify
            "reasoning": "; ".join(reasoning_parts),
            "strategic_value_score": min(5.0, strategic_value)
        }
    
    def _generate_h2h_notes(
        self,
        h2h_context: Optional[Dict[str, Any]],
        available_chips: List[str],
        recommendations: List[Dict[str, Any]]
    ) -> str:
        """Generate H2H specific notes."""
        if not h2h_context:
            return "Consider H2H opponent's chip status when timing your chips"
        
        notes = []
        
        # Opponent chip status
        opp_chip = h2h_context.get("opponent_chip")
        if opp_chip:
            notes.append(f"Opponent has used {opp_chip} chip")
        
        # Score situation
        if h2h_context.get("is_leading"):
            diff = h2h_context.get("score_difference", 0)
            if diff < 10:
                notes.append("Small lead - chip could secure victory")
            else:
                notes.append("Comfortable lead - consider saving chips")
        else:
            diff = abs(h2h_context.get("score_difference", 0))
            if diff > 20:
                notes.append("Significant deficit - aggressive chip usage recommended")
            else:
                notes.append("Close match - chip timing crucial")
        
        return "; ".join(notes) if notes else "Chip usage could be decisive in this H2H battle"