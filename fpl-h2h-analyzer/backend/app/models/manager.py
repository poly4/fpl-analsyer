"""
Manager-related data models for FPL H2H Analyzer.

This module defines dataclasses for representing FPL manager profiles
and their gameweek performance data.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class GameweekPerformance:
    """
    Represents a manager's performance in a single gameweek.
    
    Attributes:
        event: Gameweek number
        points: Points scored in this gameweek
        total_points: Cumulative total points up to this gameweek
        rank: Gameweek rank (optional)
        overall_rank: Overall rank after this gameweek (optional)
        bank: Money in bank (in tenths of millions)
        value: Team value (in tenths of millions)
        event_transfers: Number of transfers made
        event_transfers_cost: Points deducted for transfers
        points_on_bench: Points left on the bench
        chip_played: Chip used in this gameweek (optional)
    """
    event: int
    points: int
    total_points: int
    rank: Optional[int] = None
    overall_rank: Optional[int] = None
    bank: Optional[int] = None
    value: Optional[int] = None
    event_transfers: int = 0
    event_transfers_cost: int = 0
    points_on_bench: int = 0
    chip_played: Optional[str] = None


@dataclass
class ChipUsage:
    """
    Represents chip usage information.
    
    Attributes:
        name: Chip name (wildcard, bboost, 3xc, freehit)
        time: ISO timestamp when chip was played
        event: Gameweek when chip was played
    """
    name: str
    time: str
    event: int


@dataclass
class ManagerProfile:
    """
    Represents a complete FPL manager profile.
    
    Attributes:
        id: Manager's unique FPL ID
        name: Manager's full name
        team_name: Manager's team name
        overall_rank: Current overall rank (optional)
        overall_points: Current total points (optional)
        started_event: Gameweek when manager started playing
        favourite_team: ID of manager's favourite team
        player_region_name: Manager's region/country
        player_region_iso_code_short: Short ISO code for region
        current_gameweek: Current gameweek number
        gameweek_history: List of gameweek performances
        chips_used: List of chips used
        current_team_value: Current team value (optional)
        current_bank: Current money in bank (optional)
    """
    id: int
    name: str
    team_name: str
    overall_rank: Optional[int] = None
    overall_points: Optional[int] = None
    started_event: Optional[int] = None
    favourite_team: Optional[int] = None
    player_region_name: Optional[str] = None
    player_region_iso_code_short: Optional[str] = None
    current_gameweek: Optional[int] = None
    gameweek_history: List[GameweekPerformance] = field(default_factory=list)
    chips_used: List[ChipUsage] = field(default_factory=list)
    current_team_value: Optional[int] = None
    current_bank: Optional[int] = None
    
    @classmethod
    def from_api_response(cls, manager_data: Dict[str, Any], history_data: Optional[Dict[str, Any]] = None) -> 'ManagerProfile':
        """
        Create a ManagerProfile from FPL API response data.
        
        Args:
            manager_data: Response from /entry/{id}/ endpoint
            history_data: Response from /entry/{id}/history/ endpoint (optional)
            
        Returns:
            ManagerProfile instance
        """
        # Extract basic info
        profile = cls(
            id=manager_data['id'],
            name=f"{manager_data.get('player_first_name', '')} {manager_data.get('player_last_name', '')}".strip(),
            team_name=manager_data.get('name', 'Unknown Team'),
            overall_rank=manager_data.get('summary_overall_rank'),
            overall_points=manager_data.get('summary_overall_points'),
            started_event=manager_data.get('started_event'),
            favourite_team=manager_data.get('favourite_team'),
            player_region_name=manager_data.get('player_region_name'),
            player_region_iso_code_short=manager_data.get('player_region_iso_code_short'),
            current_gameweek=manager_data.get('current_event')
        )
        
        # Add history if provided
        if history_data:
            # Process gameweek history
            for gw_data in history_data.get('current', []):
                gw_perf = GameweekPerformance(
                    event=gw_data['event'],
                    points=gw_data['points'],
                    total_points=gw_data['total_points'],
                    rank=gw_data.get('rank'),
                    overall_rank=gw_data.get('overall_rank'),
                    bank=gw_data.get('bank'),
                    value=gw_data.get('value'),
                    event_transfers=gw_data.get('event_transfers', 0),
                    event_transfers_cost=gw_data.get('event_transfers_cost', 0),
                    points_on_bench=gw_data.get('points_on_bench', 0)
                )
                profile.gameweek_history.append(gw_perf)
            
            # Process chips used
            for chip_data in history_data.get('chips', []):
                chip = ChipUsage(
                    name=chip_data['name'],
                    time=chip_data['time'],
                    event=chip_data['event']
                )
                profile.chips_used.append(chip)
                
                # Also mark chip in gameweek history
                for gw in profile.gameweek_history:
                    if gw.event == chip_data['event']:
                        gw.chip_played = chip_data['name']
            
            # Set current values from latest gameweek
            if profile.gameweek_history:
                latest = profile.gameweek_history[-1]
                profile.current_team_value = latest.value
                profile.current_bank = latest.bank
        
        return profile
    
    def get_chips_available(self) -> Dict[str, bool]:
        """
        Get which chips are still available to use.
        
        Returns:
            Dictionary mapping chip names to availability
        """
        all_chips = {'wildcard': 2, 'bboost': 1, '3xc': 1, 'freehit': 1}
        used_chips = {}
        
        for chip in self.chips_used:
            chip_name = chip.name
            used_chips[chip_name] = used_chips.get(chip_name, 0) + 1
        
        available = {}
        for chip_name, allowed_count in all_chips.items():
            used_count = used_chips.get(chip_name, 0)
            available[chip_name] = used_count < allowed_count
        
        return available