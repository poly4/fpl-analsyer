# Data models for H2H leagues
# This file will define dataclasses for H2H match results, league standings, and gameweek performance.

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

# Note: GameweekPerformance is in manager.py, if needed here, it would be imported.
# from .manager import ManagerProfile # If we need to link back to full manager profiles

@dataclass
class H2HLeagueEntry:
    """Represents a single manager's entry in an H2H league's standings."""
    id: int # League entry ID (distinct from manager ID)
    entry_id: int # Manager's FPL ID
    player_name: str # Manager's full name
    entry_name: str # Manager's team name
    rank: int
    last_rank: int
    rank_sort: int # Usually same as rank
    total: int # Total H2H points (e.g., 3 for a win, 1 for a draw)
    matches_played: int
    matches_won: int
    matches_drawn: int
    matches_lost: int
    points_for: int # Total FPL points scored by this manager in H2H matches
    # points_against: int # Not always directly available in standings, might need calculation from matches

    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'H2HLeagueEntry':
        return cls(
            id=data.get('id'),
            entry_id=data.get('entry'),
            player_name=data.get('player_name'),
            entry_name=data.get('entry_name'),
            rank=data.get('rank'),
            last_rank=data.get('last_rank'),
            rank_sort=data.get('rank_sort'),
            total=data.get('total'),
            matches_played=data.get('matches_played'),
            matches_won=data.get('matches_won'),
            matches_drawn=data.get('matches_drawn'),
            matches_lost=data.get('matches_lost'),
            points_for=data.get('points_for')
        )

@dataclass
class H2HMatch:
    """Represents a single H2H match between two managers in a gameweek."""
    id: int # Match ID
    event: int # Gameweek number
    league_id: int # The H2H league this match belongs to
    
    entry_1_entry: int # Manager 1's FPL ID
    entry_1_name: str # Manager 1's team name
    entry_1_player_name: str # Manager 1's player name
    entry_1_points: int # Manager 1's FPL points for this gameweek
    entry_1_win: int # 1 if won, 0 otherwise
    entry_1_draw: int # 1 if drawn, 0 otherwise
    entry_1_loss: int # 1 if lost, 0 otherwise

    entry_2_entry: int # Manager 2's FPL ID
    entry_2_name: str # Manager 2's team name
    entry_2_player_name: str # Manager 2's player name
    entry_2_points: int # Manager 2's FPL points for this gameweek
    entry_2_win: int # 1 if won, 0 otherwise
    entry_2_draw: int # 1 if drawn, 0 otherwise
    entry_2_loss: int # 1 if lost, 0 otherwise

    is_knockout: bool
    winner: Optional[int] # FPL ID of the winner, None if draw or not finished
    seed_value: Optional[str] # For cup matches

    @classmethod
    def from_api_data(cls, data: Dict[str, Any], league_id_override: Optional[int] = None) -> 'H2HMatch':
        # The league_id might not be in the match data itself, so allow override
        # It's often part of the parent structure when fetching matches for a league.
        return cls(
            id=data.get('id'),
            event=data.get('event'),
            league_id=league_id_override if league_id_override is not None else data.get('league'), # 'league' might be the field name
            
            entry_1_entry=data.get('entry_1_entry'),
            entry_1_name=data.get('entry_1_name'),
            entry_1_player_name=data.get('entry_1_player_name'),
            entry_1_points=data.get('entry_1_points'),
            entry_1_win=data.get('entry_1_win'),
            entry_1_draw=data.get('entry_1_draw'),
            entry_1_loss=data.get('entry_1_loss'),

            entry_2_entry=data.get('entry_2_entry'),
            entry_2_name=data.get('entry_2_name'),
            entry_2_player_name=data.get('entry_2_player_name'),
            entry_2_points=data.get('entry_2_points'),
            entry_2_win=data.get('entry_2_win'),
            entry_2_draw=data.get('entry_2_draw'),
            entry_2_loss=data.get('entry_2_loss'),

            is_knockout=data.get('is_knockout', False),
            winner=data.get('winner'),
            seed_value=data.get('seed_value')
        )

@dataclass
class H2HLeague:
    """Represents an FPL H2H league, including its standings and matches."""
    id: int
    name: str
    created: str # ISO date string
    closed: bool
    max_entries: Optional[int]
    league_type: str # e.g., 'x'
    scoring: str # e.g., 'h2h'
    admin_entry: Optional[int] # FPL ID of the admin
    start_event: int # Gameweek league starts
    # code_privacy: str # e.g., 'p' for private

    standings: List[H2HLeagueEntry] = field(default_factory=list)
    matches: Dict[int, List[H2HMatch]] = field(default_factory=dict) # Gameweek_num: List of matches

    @classmethod
    def from_standings_api_data(cls, data: Dict[str, Any]) -> 'H2HLeague':
        league_info = data.get('league', {})
        standings_results = data.get('standings', {}).get('results', [])
        
        league = cls(
            id=league_info.get('id'),
            name=league_info.get('name'),
            created=league_info.get('created'),
            closed=league_info.get('closed'),
            max_entries=league_info.get('max_entries'),
            league_type=league_info.get('league_type'),
            scoring=league_info.get('scoring'),
            admin_entry=league_info.get('admin_entry'),
            start_event=league_info.get('start_event')
            # code_privacy=league_info.get('code_privacy')
        )
        league.standings = [H2HLeagueEntry.from_api_data(s_data) for s_data in standings_results]
        return league

    def update_matches_from_api_data(self, matches_data: List[Dict[str, Any]]):
        """Updates or adds matches, organizing them by gameweek."""
        for match_api_data in matches_data:
            match = H2HMatch.from_api_data(match_api_data, league_id_override=self.id)
            if match.event not in self.matches:
                self.matches[match.event] = []
            # Avoid duplicate matches if called multiple times with overlapping data
            if not any(m.id == match.id for m in self.matches[match.event]):
                 self.matches[match.event].append(match)

    def get_manager_entry(self, manager_id: int) -> Optional[H2HLeagueEntry]:
        for entry in self.standings:
            if entry.entry_id == manager_id:
                return entry
        return None

    def get_matches_for_gameweek(self, gameweek: int) -> List[H2HMatch]:
        return self.matches.get(gameweek, [])

    def get_matches_for_manager(self, manager_id: int) -> List[H2HMatch]:
        manager_matches = []
        for gw_matches in self.matches.values():
            for match in gw_matches:
                if match.entry_1_entry == manager_id or match.entry_2_entry == manager_id:
                    manager_matches.append(match)
        return manager_matches

# Example Usage (for testing purposes)
if __name__ == "__main__":
    # Mock API data for H2H League Standings
    mock_h2h_standings_data = {
        "league": {
            "id": 12345, "name": "Test H2H League", "created": "2023-07-01T12:00:00Z",
            "closed": False, "max_entries": 20, "league_type": "x", "scoring": "h2h",
            "admin_entry": 101, "start_event": 1
        },
        "standings": {
            "has_next": False, "page": 1,
            "results": [
                {"id": 1, "entry": 101, "player_name": "Admin Manager", "entry_name": "Admin FC", "rank": 1, "last_rank": 1, "rank_sort": 1, "total": 6, "matches_played": 2, "matches_won": 2, "matches_drawn": 0, "matches_lost": 0, "points_for": 150},
                {"id": 2, "entry": 102, "player_name": "Rival Manager", "entry_name": "Rival Rovers", "rank": 2, "last_rank": 2, "rank_sort": 2, "total": 3, "matches_played": 2, "matches_won": 1, "matches_drawn": 0, "matches_lost": 1, "points_for": 120}
            ]
        }
    }

    # Mock API data for H2H Matches (for GW1)
    mock_h2h_matches_gw1_data = [
        {
            "id": 1001, "event": 1, "league": 12345,
            "entry_1_entry": 101, "entry_1_name": "Admin FC", "entry_1_player_name": "Admin Manager", "entry_1_points": 75, "entry_1_win": 1, "entry_1_draw": 0, "entry_1_loss": 0,
            "entry_2_entry": 102, "entry_2_name": "Rival Rovers", "entry_2_player_name": "Rival Manager", "entry_2_points": 60, "entry_2_win": 0, "entry_2_draw": 0, "entry_2_loss": 1,
            "is_knockout": False, "winner": 101
        }
        # ... more matches for GW1 if any
    ]
    # Mock API data for H2H Matches (for GW2)
    mock_h2h_matches_gw2_data = [
        {
            "id": 1002, "event": 2, "league": 12345,
            "entry_1_entry": 101, "entry_1_name": "Admin FC", "entry_1_player_name": "Admin Manager", "entry_1_points": 75, "entry_1_win": 1, "entry_1_draw": 0, "entry_1_loss": 0,
            "entry_2_entry": 103, "entry_2_name": "New Challenger", "entry_2_player_name": "Challenger Name", "entry_2_points": 70, "entry_2_win": 0, "entry_2_draw": 0, "entry_2_loss": 1,
            "is_knockout": False, "winner": 101
        },
         {
            "id": 1003, "event": 2, "league": 12345,
            "entry_1_entry": 102, "entry_1_name": "Rival Rovers", "entry_1_player_name": "Rival Manager", "entry_1_points": 60, "entry_1_win": 0, "entry_1_draw": 0, "entry_1_loss": 1,
            "entry_2_entry": 104, "entry_2_name": "Another Team", "entry_2_player_name": "Another Player", "entry_2_points": 65, "entry_2_win": 1, "entry_2_draw": 0, "entry_2_loss": 0,
            "is_knockout": False, "winner": 104
        }
    ]

    league = H2HLeague.from_standings_api_data(mock_h2h_standings_data)
    print(f"League: {league.name} (ID: {league.id}), Admin ID: {league.admin_entry}")

    print("\nStandings:")
    for entry in league.standings:
        print(f"  - {entry.rank}. {entry.entry_name} ({entry.player_name}) - Points: {entry.total}, W: {entry.matches_won} D: {entry.matches_drawn} L: {entry.matches_lost}, PF: {entry.points_for}")

    league.update_matches_from_api_data(mock_h2h_matches_gw1_data)
    league.update_matches_from_api_data(mock_h2h_matches_gw2_data)

    print("\nMatches in GW1:")
    for match in league.get_matches_for_gameweek(1):
        print(f"  - {match.entry_1_name} ({match.entry_1_points}) vs {match.entry_2_name} ({match.entry_2_points}). Winner: {match.winner}")

    print("\nMatches in GW2:")
    for match in league.get_matches_for_gameweek(2):
        print(f"  - {match.entry_1_name} ({match.entry_1_points}) vs {match.entry_2_name} ({match.entry_2_points}). Winner: {match.winner}")

    rival_manager_id = 102
    print(f"\nMatches for Manager ID {rival_manager_id} ({league.get_manager_entry(rival_manager_id).entry_name if league.get_manager_entry(rival_manager_id) else 'N/A'}):")
    for match in league.get_matches_for_manager(rival_manager_id):
        opponent_id = match.entry_1_entry if match.entry_2_entry == rival_manager_id else match.entry_2_entry
        opponent_name = match.entry_1_name if match.entry_2_entry == rival_manager_id else match.entry_2_name
        print(f"  - GW{match.event}: vs {opponent_name} (ID: {opponent_id}). Result: {'Win' if (match.entry_1_entry == rival_manager_id and match.entry_1_win) or (match.entry_2_entry == rival_manager_id and match.entry_2_win) else ('Draw' if (match.entry_1_draw and match.entry_1_entry == rival_manager_id) or (match.entry_2_draw and match.entry_2_entry == rival_manager_id) else 'Loss')}")

    print("\nDone with H2H League model tests.")