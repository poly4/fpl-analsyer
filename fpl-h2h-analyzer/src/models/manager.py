# Data models for FPL managers
# This file will define dataclasses for manager profiles and related stats.

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class GameweekPerformance:
    """Represents a manager's performance in a single gameweek."""
    event: int  # Gameweek number
    points: int
    total_points: int
    rank: Optional[int]
    rank_sort: Optional[int]
    overall_rank: Optional[int]
    bank: Optional[int] # Bank value in tenths of a million (e.g., 10 = £1.0m)
    value: Optional[int] # Team value in tenths of a million
    event_transfers: int
    event_transfers_cost: int
    points_on_bench: int
    chip_played: Optional[str] = None # e.g., 'bboost', '3xc', 'freehit', 'wildcard'

    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'GameweekPerformance':
        # Provide default values for potentially missing fields
        return cls(
            event=data.get('event', 0), # Assuming 0 is a safe default for event number if missing
            points=data.get('points', 0),
            total_points=data.get('total_points', 0),
            rank=data.get('rank'), # Optional, None is acceptable
            rank_sort=data.get('rank_sort'), # Optional, None is acceptable
            overall_rank=data.get('overall_rank'), # Optional, None is acceptable
            bank=data.get('bank'), # Optional, None is acceptable
            value=data.get('value'), # Optional, None is acceptable
            event_transfers=data.get('event_transfers', 0),
            event_transfers_cost=data.get('event_transfers_cost', 0),
            points_on_bench=data.get('points_on_bench', 0),
            chip_played=data.get('chip') # Optional, None is acceptable
        )

@dataclass
class PastSeasonPerformance:
    """Represents a manager's performance in a past FPL season."""
    season_name: str
    total_points: int
    rank: int

    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'PastSeasonPerformance':
        # Provide default values for potentially missing fields
        return cls(
            season_name=data.get('season_name', 'Unknown Season'), # Provide a default string
            total_points=data.get('total_points', 0),
            rank=data.get('rank', 0) # Assuming 0 is a safe default for rank if missing
        )

@dataclass
class ManagerPick:
    """Represents a single player pick by a manager for a gameweek."""
    element: int # Player ID
    position: int # Playing position
    multiplier: int # 0 for bench, 1 for starter, 2 for captain, 3 for triple captain
    is_captain: bool
    is_vice_captain: bool

    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'ManagerPick':
        return cls(
            element=data.get('element'),
            position=data.get('position'),
            multiplier=data.get('multiplier'),
            is_captain=data.get('is_captain'),
            is_vice_captain=data.get('is_vice_captain')
        )

@dataclass
class ManagerGameweekPicks:
    """Represents all of a manager's picks for a specific gameweek."""
    active_chip: Optional[str]
    automatic_subs: List[Dict[str, int]] # List of {'event_in': player_id, 'event_out': player_id}
    entry_history: Optional[GameweekPerformance]  # Make optional
    picks: List[ManagerPick]

    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'ManagerGameweekPicks':
        # Handle entry_history being None or missing
        entry_history = None
        if data.get('entry_history'):
            entry_history = GameweekPerformance.from_api_data(data['entry_history'])
            
        return cls(
            active_chip=data.get('active_chip'),
            automatic_subs=data.get('automatic_substitutions', []), # Provide default empty list
            entry_history=entry_history,
            picks=[ManagerPick.from_api_data(p) for p in data.get('picks', [])] # Provide default empty list
        )


@dataclass
class ManagerProfile:
    """Represents an FPL manager's profile and overall FPL status."""
    id: int
    name: str
    team_name: str
    started_event: int # Gameweek manager started playing
    overall_rank: Optional[int]
    overall_points: Optional[int] # This is usually part of league entry, not manager profile directly
    
    # From manager history API
    current_gameweek_history: List[GameweekPerformance] = field(default_factory=list)
    past_seasons: List[PastSeasonPerformance] = field(default_factory=list)
    chips_played: List[Dict[str, Any]] = field(default_factory=list) # Chips used this season

    # Populated separately
    # gameweek_picks: Dict[int, ManagerGameweekPicks] = field(default_factory=dict) # GW_num: Picks

    @classmethod
    def from_entry_api_data(cls, data: Dict[str, Any]) -> 'ManagerProfile':
        # Provide default values for potentially missing fields and handle name construction safely
        first_name = data.get('player_first_name', '')
        last_name = data.get('player_last_name', '')
        full_name = f"{first_name} {last_name}".strip()
        if not full_name:
             full_name = data.get('name', 'Unknown Manager') # Fallback to team name or default

        profile = cls(
            id=data.get('id', 0), # Assuming 0 is a safe default for ID if missing
            name=full_name,
            team_name=data.get('name', 'Unknown Team'), # Provide a default string
            started_event=data.get('started_event', 0), # Assuming 0 is a safe default if missing
            overall_rank=data.get('summary_overall_rank'), # Optional, None is acceptable
            overall_points=data.get('summary_overall_points') # Optional, None is acceptable
        )

        # If history data is included, update from it
        if 'current' in data:
            profile.current_gameweek_history = [
                GameweekPerformance.from_api_data(gw_data)
                for gw_data in data.get('current', [])
            ]
            # Update overall stats from latest gameweek if not set
            if profile.current_gameweek_history and not profile.overall_rank:
                latest = profile.current_gameweek_history[-1]
                profile.overall_rank = latest.overall_rank
                profile.overall_points = latest.total_points

        if 'past' in data:
            profile.past_seasons = [
                PastSeasonPerformance.from_api_data(season_data)
                for season_data in data.get('past', [])
            ]

        if 'chips' in data:
            profile.chips_played = data.get('chips', [])

        return profile

    def update_from_history_api_data(self, history_data: Dict[str, Any]):
        self.current_gameweek_history = [
            GameweekPerformance.from_api_data(gw_data) for gw_data in history_data.get('current', [])
        ]
        self.past_seasons = [
            PastSeasonPerformance.from_api_data(season_data) for season_data in history_data.get('past', [])
        ]
        self.chips_played = history_data.get('chips', [])

    def get_current_gameweek_performance(self, gameweek: int) -> Optional[GameweekPerformance]:
        for gw_perf in self.current_gameweek_history:
            if gw_perf.event == gameweek:
                return gw_perf
        return None

# Example Usage (for testing purposes)
if __name__ == "__main__":
    # Mock API data (simplified)
    mock_manager_entry_data = {
        "id": 12345,
        "player_first_name": "Test",
        "player_last_name": "Manager",
        "name": "Test FC",
        "started_event": 1,
        "summary_overall_rank": 1000,
        "summary_overall_pts": 2000
    }

    mock_manager_history_data = {
        "current": [
            {"event": 1, "points": 60, "total_points": 60, "overall_rank": 5000, "event_transfers": 0, "event_transfers_cost": 0, "points_on_bench": 5, "chip": None, "value": 1000, "bank": 0},
            {"event": 2, "points": 70, "total_points": 130, "overall_rank": 3000, "event_transfers": 1, "event_transfers_cost": 0, "points_on_bench": 10, "chip": "bboost", "value": 1005, "bank": 2}
        ],
        "past": [
            {"season_name": "2022/23", "total_points": 2200, "rank": 15000},
            {"season_name": "2021/22", "total_points": 2100, "rank": 25000}
        ],
        "chips": [
            {"name": "bboost", "time": "2023-08-20T10:00:00Z", "event": 2}
        ]
    }

    mock_manager_picks_data_gw2 = {
        "active_chip": "bboost",
        "automatic_substitutions": [],
        "entry_history": {"event": 2, "points": 70, "total_points": 130, "rank": 123, "overall_rank": 3000, "bank": 2, "value": 1005, "event_transfers": 1, "event_transfers_cost": 0, "points_on_bench": 10},
        "picks": [
            {"element": 101, "position": 1, "multiplier": 1, "is_captain": False, "is_vice_captain": False},
            {"element": 202, "position": 11, "multiplier": 2, "is_captain": True, "is_vice_captain": False},
            # ... more picks
        ]
    }

    manager = ManagerProfile.from_entry_api_data(mock_manager_entry_data)
    manager.update_from_history_api_data(mock_manager_history_data)

    print(f"Manager: {manager.name} ({manager.id}), Team: {manager.team_name}")
    print(f"Overall Rank: {manager.overall_rank}, Overall Points: {manager.overall_points}")
    
    print("\nPast Seasons:")
    for season in manager.past_seasons:
        print(f"  - {season.season_name}: Points: {season.total_points}, Rank: {season.rank}")

    print("\nCurrent Season Gameweeks:")
    for gw_perf in manager.current_gameweek_history:
        print(f"  - GW {gw_perf.event}: Points: {gw_perf.points}, Total: {gw_perf.total_points}, OR: {gw_perf.overall_rank}, Chip: {gw_perf.chip_played}")

    gw2_perf = manager.get_current_gameweek_performance(2)
    if gw2_perf:
        print(f"\nPerformance in GW2: {gw2_perf.points} points. Chip: {gw2_perf.chip_played}")

    print("\nChips Played:")
    for chip in manager.chips_played:
        print(f"  - {chip['name']} in GW {chip['event']}")

    # Example for ManagerGameweekPicks
    gw2_picks = ManagerGameweekPicks.from_api_data(mock_manager_picks_data_gw2)
    print(f"\nGW2 Picks for manager (example data):")
    print(f"  Active chip: {gw2_picks.active_chip}")
    print(f"  Points in GW2 (from picks data): {gw2_picks.entry_history.points}")
    if gw2_picks.picks:
        print(f"  Captain (Player ID): {[p.element for p in gw2_picks.picks if p.is_captain][0]}")

    print("\nDone with Manager model tests.")