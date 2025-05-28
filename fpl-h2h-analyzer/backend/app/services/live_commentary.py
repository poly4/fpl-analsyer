"""
Live Commentary Engine for FPL H2H Battles

Generates natural language commentary for live events, tracking momentum shifts
and personalizing messages based on viewer perspective.
"""

import random
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime


class EventType(Enum):
    """Types of events that can occur during a match"""
    GOAL = "goal"
    ASSIST = "assist"
    CLEAN_SHEET = "clean_sheet"
    PENALTY_SAVE = "penalty_save"
    PENALTY_MISS = "penalty_miss"
    RED_CARD = "red_card"
    YELLOW_CARD = "yellow_card"
    OWN_GOAL = "own_goal"
    BONUS = "bonus"
    CAPTAIN_HAUL = "captain_haul"
    DIFFERENTIAL_SUCCESS = "differential_success"
    MOMENTUM_SHIFT = "momentum_shift"


class CommentaryTone(Enum):
    """Different tones for commentary based on event impact"""
    EXCITING = "exciting"
    SYMPATHETIC = "sympathetic"
    INFORMATIVE = "informative"
    DRAMATIC = "dramatic"
    HUMOROUS = "humorous"


class CommentaryEngine:
    """Generates contextual live commentary for H2H battles"""
    
    def __init__(self):
        self.momentum_threshold = 10  # Points difference for momentum shift
        self.recent_events = []  # Track recent events for context
        
    def generate_commentary(
        self,
        event_type: EventType,
        player_name: str,
        team: str,
        points: int,
        is_captain: bool,
        is_differential: bool,
        viewer_owns: bool,
        rival_owns: bool,
        viewer_score: int,
        rival_score: int,
        viewer_name: str,
        rival_name: str,
        additional_context: Optional[Dict] = None
    ) -> Dict[str, any]:
        """
        Generate commentary for a specific event
        
        Args:
            event_type: Type of event that occurred
            player_name: Name of the player involved
            team: Player's team
            points: Points scored from this event
            is_captain: Whether player is captained
            is_differential: Whether player is a differential pick
            viewer_owns: Whether viewer owns this player
            rival_owns: Whether rival owns this player
            viewer_score: Current viewer score
            rival_score: Current rival score
            viewer_name: Viewer's team name
            rival_name: Rival's team name
            additional_context: Any additional context for the event
            
        Returns:
            Dict containing commentary text, tone, and impact score
        """
        
        # Determine impact and tone
        impact_score = self._calculate_impact_score(
            event_type, points, is_captain, is_differential,
            viewer_owns, rival_owns, viewer_score, rival_score
        )
        
        tone = self._determine_tone(
            impact_score, viewer_owns, rival_owns, 
            viewer_score, rival_score
        )
        
        # Generate the commentary
        commentary = self._generate_text(
            event_type, player_name, team, points, is_captain,
            is_differential, viewer_owns, rival_owns,
            viewer_score, rival_score, viewer_name, rival_name,
            tone, additional_context
        )
        
        # Check for momentum shift
        momentum_commentary = self._check_momentum_shift(
            viewer_score, rival_score, viewer_name, rival_name
        )
        
        return {
            "commentary": commentary,
            "tone": tone.value,
            "impact_score": impact_score,
            "momentum_shift": momentum_commentary,
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_impact_score(
        self, event_type: EventType, points: int, is_captain: bool,
        is_differential: bool, viewer_owns: bool, rival_owns: bool,
        viewer_score: int, rival_score: int
    ) -> int:
        """Calculate the impact score of an event (0-100)"""
        
        base_scores = {
            EventType.GOAL: 40,
            EventType.ASSIST: 25,
            EventType.CLEAN_SHEET: 20,
            EventType.PENALTY_SAVE: 50,
            EventType.PENALTY_MISS: 30,
            EventType.RED_CARD: 40,
            EventType.YELLOW_CARD: 10,
            EventType.OWN_GOAL: 35,
            EventType.BONUS: 15,
            EventType.CAPTAIN_HAUL: 60,
            EventType.DIFFERENTIAL_SUCCESS: 45,
            EventType.MOMENTUM_SHIFT: 50
        }
        
        score = base_scores.get(event_type, 20)
        
        # Modifiers
        if is_captain:
            score *= 2
            
        if is_differential and viewer_owns and not rival_owns:
            score *= 1.5
            
        # Game state modifier
        score_diff = abs(viewer_score - rival_score)
        if score_diff < 5:  # Close game
            score *= 1.3
        elif score_diff > 20:  # Blowout
            score *= 0.7
            
        return min(100, int(score))
    
    def _determine_tone(
        self, impact_score: int, viewer_owns: bool, rival_owns: bool,
        viewer_score: int, rival_score: int
    ) -> CommentaryTone:
        """Determine the appropriate tone for commentary"""
        
        if impact_score > 70:
            return CommentaryTone.DRAMATIC
        
        if viewer_owns and not rival_owns:
            if viewer_score > rival_score:
                return CommentaryTone.EXCITING
            else:
                return CommentaryTone.DRAMATIC  # Comeback potential
                
        elif rival_owns and not viewer_owns:
            if viewer_score > rival_score:
                return CommentaryTone.INFORMATIVE
            else:
                return CommentaryTone.SYMPATHETIC
                
        elif viewer_owns and rival_owns:
            return CommentaryTone.INFORMATIVE
            
        else:  # Neither owns
            if impact_score > 40:
                return CommentaryTone.DRAMATIC
            else:
                return CommentaryTone.INFORMATIVE
    
    def _generate_text(
        self, event_type: EventType, player_name: str, team: str,
        points: int, is_captain: bool, is_differential: bool,
        viewer_owns: bool, rival_owns: bool, viewer_score: int,
        rival_score: int, viewer_name: str, rival_name: str,
        tone: CommentaryTone, additional_context: Optional[Dict] = None
    ) -> str:
        """Generate the actual commentary text"""
        
        templates = self._get_templates(event_type, tone)
        
        # Select appropriate template based on ownership
        if viewer_owns and rival_owns:
            template_key = "both_own"
        elif viewer_owns:
            template_key = "viewer_owns"
        elif rival_owns:
            template_key = "rival_owns"
        else:
            template_key = "neither_owns"
            
        templates_list = templates.get(template_key, templates.get("default", []))
        template = random.choice(templates_list) if templates_list else ""
        
        # Format the template
        captain_prefix = "Captain " if is_captain else ""
        differential_suffix = " (differential pick!)" if is_differential and viewer_owns and not rival_owns else ""
        
        score_diff = viewer_score - rival_score
        score_status = f"ahead by {score_diff}" if score_diff > 0 else f"behind by {-score_diff}" if score_diff < 0 else "level"
        
        return template.format(
            player=captain_prefix + player_name,
            team=team,
            points=points,
            viewer=viewer_name,
            rival=rival_name,
            score_status=score_status,
            viewer_score=viewer_score,
            rival_score=rival_score,
            differential=differential_suffix
        )
    
    def _get_templates(self, event_type: EventType, tone: CommentaryTone) -> Dict[str, List[str]]:
        """Get commentary templates based on event type and tone"""
        
        templates = {
            EventType.GOAL: {
                "viewer_owns": {
                    CommentaryTone.EXCITING: [
                        "🎯 {player} finds the net! That's {points} points for {viewer}!{differential}",
                        "⚡ GOAL! {player} scores and {viewer} extends their lead! Now {score_status}!",
                        "💥 {player} with a crucial goal! {viewer} pulling away!"
                    ],
                    CommentaryTone.DRAMATIC: [
                        "🔥 INCREDIBLE! {player} scores when it matters most! {viewer} is {score_status}!",
                        "🚨 GAME CHANGER! {player} finds the net! The momentum shifts!"
                    ]
                },
                "rival_owns": {
                    CommentaryTone.SYMPATHETIC: [
                        "😬 {rival}'s {player} scores... That's {points} points you're missing out on.",
                        "💔 Ouch! {player} scores for {rival}. The gap widens to {rival_score}-{viewer_score}."
                    ],
                    CommentaryTone.INFORMATIVE: [
                        "📊 {player} scores for {rival}. {points} points added to their tally.",
                        "⚽ Goal for {player}. {rival} benefits with {points} points."
                    ]
                },
                "both_own": {
                    CommentaryTone.INFORMATIVE: [
                        "⚽ {player} scores! Both teams benefit equally with {points} points.",
                        "📊 Shared joy as {player} nets one. No advantage gained."
                    ]
                }
            },
            EventType.CAPTAIN_HAUL: {
                "viewer_owns": {
                    CommentaryTone.DRAMATIC: [
                        "👑 CAPTAIN FANTASTIC! {player} is delivering a masterclass! {points} points and counting!",
                        "🌟 Your captain {player} is on fire! This could be the game-winner!"
                    ]
                },
                "rival_owns": {
                    CommentaryTone.SYMPATHETIC: [
                        "😱 Disaster! {rival}'s captain {player} is hauling with {points} points!",
                        "💀 {rival}'s captaincy choice paying off big time... {player} with {points} points!"
                    ]
                }
            },
            EventType.DIFFERENTIAL_SUCCESS: {
                "viewer_owns": {
                    CommentaryTone.EXCITING: [
                        "🎲 DIFFERENTIAL PAYS OFF! {player} rewards your faith with {points} points!",
                        "🔮 Genius pick! Your differential {player} delivers while {rival} watches!"
                    ]
                }
            },
            EventType.RED_CARD: {
                "viewer_owns": {
                    CommentaryTone.SYMPATHETIC: [
                        "🟥 Disaster! {player} sees red! That's -3 points for {viewer}...",
                        "😤 {player} sent off! Your team takes a hit."
                    ]
                },
                "rival_owns": {
                    CommentaryTone.EXCITING: [
                        "🟥 {rival}'s {player} gets a red card! Advantage {viewer}!",
                        "⚡ Drama! {player} sent off - {rival} loses points!"
                    ]
                }
            }
        }
        
        # Add more templates for other event types...
        
        return templates.get(event_type, {})
    
    def _check_momentum_shift(
        self, viewer_score: int, rival_score: int, 
        viewer_name: str, rival_name: str
    ) -> Optional[str]:
        """Check if there's been a momentum shift in the battle"""
        
        if not hasattr(self, '_last_score_diff'):
            self._last_score_diff = 0
            
        current_diff = viewer_score - rival_score
        diff_change = current_diff - self._last_score_diff
        
        momentum_text = None
        
        if abs(diff_change) >= self.momentum_threshold:
            if diff_change > 0:
                momentum_text = f"🔄 MOMENTUM SHIFT! {viewer_name} surges ahead!"
            else:
                momentum_text = f"🔄 MOMENTUM SHIFT! {rival_name} fights back!"
                
        self._last_score_diff = current_diff
        
        return momentum_text
    
    def generate_battle_summary(
        self, viewer_name: str, rival_name: str,
        viewer_score: int, rival_score: int,
        key_events: List[Dict]
    ) -> str:
        """Generate a summary of the battle so far"""
        
        score_diff = viewer_score - rival_score
        
        if score_diff > 20:
            status = f"{viewer_name} dominating"
        elif score_diff > 10:
            status = f"{viewer_name} in control"
        elif score_diff > 0:
            status = f"{viewer_name} narrowly ahead"
        elif score_diff == 0:
            status = "Dead heat"
        elif score_diff > -10:
            status = f"{rival_name} edging it"
        elif score_diff > -20:
            status = f"{rival_name} in command"
        else:
            status = f"{rival_name} cruising"
            
        # Find the most impactful event
        if key_events:
            top_event = max(key_events, key=lambda x: x.get('impact_score', 0))
            key_moment = f"Key moment: {top_event.get('commentary', '')}"
        else:
            key_moment = "A tense battle with everything still to play for!"
            
        return f"📊 Battle Status: {status} ({viewer_score}-{rival_score})\n{key_moment}"