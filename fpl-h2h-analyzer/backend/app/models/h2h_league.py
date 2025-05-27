"""
H2H League-related data models for FPL H2H Analyzer.

This module defines dataclasses for representing FPL H2H leagues,
matches, and standings data.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class H2HMatch:
    """
    Represents a single H2H match between two managers.
    
    Attributes:
        id: Unique match ID
        event: Gameweek number
        entry_1_entry: Manager ID for entry 1
        entry_1_name: Manager name for entry 1
        entry_1_points: Points scored by entry 1
        entry_2_entry: Manager ID for entry 2
        entry_2_name: Manager name for entry 2
        entry_2_points: Points scored by entry 2
        is_knockout: Whether this is a knockout match
        winner: Manager ID of the winner (None for draw)
        started: Whether the match has started
        finished: Whether the match has finished
    """
    id: int
    event: int
    entry_1_entry: int
    entry_1_name: str
    entry_1_points: int
    entry_2_entry: int
    entry_2_name: str
    entry_2_points: int
    is_knockout: bool = False
    winner: Optional[int] = None
    started: bool = True
    finished: bool = False
    
    @property
    def is_draw(self) -> bool:
        """Check if the match is a draw."""
        return self.finished and self.winner is None
    
    @property
    def margin(self) -> int:
        """Get the winning margin (absolute difference in points)."""
        return abs(self.entry_1_points - self.entry_2_points)
    
    def get_winner_name(self) -> Optional[str]:
        """Get the name of the winning manager."""
        if self.winner == self.entry_1_entry:
            return self.entry_1_name
        elif self.winner == self.entry_2_entry:
            return self.entry_2_name
        return None
    
    @classmethod
    def from_api_response(cls, match_data: Dict[str, Any]) -> 'H2HMatch':
        """
        Create an H2HMatch from FPL API response data.
        
        Args:
            match_data: Match data from API
            
        Returns:
            H2HMatch instance
        """
        # Determine winner
        winner = None
        if match_data.get('finished', False):
            if match_data['entry_1_points'] > match_data['entry_2_points']:
                winner = match_data['entry_1_entry']
            elif match_data['entry_2_points'] > match_data['entry_1_points']:
                winner = match_data['entry_2_entry']
        
        return cls(
            id=match_data['id'],
            event=match_data['event'],
            entry_1_entry=match_data['entry_1_entry'],
            entry_1_name=match_data.get('entry_1_player_name', 'Unknown'),
            entry_1_points=match_data['entry_1_points'],
            entry_2_entry=match_data['entry_2_entry'],
            entry_2_name=match_data.get('entry_2_player_name', 'Unknown'),
            entry_2_points=match_data['entry_2_points'],
            is_knockout=match_data.get('is_knockout', False),
            winner=winner,
            started=match_data.get('started', True),
            finished=match_data.get('finished', False)
        )


@dataclass
class H2HLeagueEntry:
    """
    Represents a manager's standing in an H2H league.
    
    Attributes:
        entry_id: Manager/Entry ID
        player_name: Manager's name
        entry_name: Team name
        rank: Current rank in the league
        last_rank: Previous rank
        rank_sort: Sort order for ranking
        total: Total H2H points (3 for win, 1 for draw)
        matches_played: Number of matches played
        matches_won: Number of matches won
        matches_drawn: Number of matches drawn
        matches_lost: Number of matches lost
        points_for: Total FPL points scored
    """
    entry_id: int
    player_name: str
    entry_name: str
    rank: int
    last_rank: int
    rank_sort: int
    total: int
    matches_played: int
    matches_won: int
    matches_drawn: int
    matches_lost: int
    points_for: int
    
    @property
    def win_percentage(self) -> float:
        """Calculate win percentage."""
        if self.matches_played == 0:
            return 0.0
        return (self.matches_won / self.matches_played) * 100
    
    @property
    def points_per_match(self) -> float:
        """Calculate average FPL points per match."""
        if self.matches_played == 0:
            return 0.0
        return self.points_for / self.matches_played
    
    @property
    def form_string(self) -> str:
        """Get a simple form representation (e.g., 'W-D-L')."""
        return f"{self.matches_won}W-{self.matches_drawn}D-{self.matches_lost}L"
    
    @classmethod
    def from_api_response(cls, entry_data: Dict[str, Any]) -> 'H2HLeagueEntry':
        """
        Create an H2HLeagueEntry from FPL API response data.
        
        Args:
            entry_data: Entry data from standings API
            
        Returns:
            H2HLeagueEntry instance
        """
        return cls(
            entry_id=entry_data['entry'],
            player_name=entry_data['player_name'],
            entry_name=entry_data['entry_name'],
            rank=entry_data['rank'],
            last_rank=entry_data['last_rank'],
            rank_sort=entry_data['rank_sort'],
            total=entry_data['total'],
            matches_played=entry_data.get('matches_played', 0),
            matches_won=entry_data.get('matches_won', 0),
            matches_drawn=entry_data.get('matches_drawn', 0),
            matches_lost=entry_data.get('matches_lost', 0),
            points_for=entry_data.get('points_for', 0)
        )


@dataclass
class H2HLeagueStandings:
    """
    Represents complete H2H league standings.
    
    Attributes:
        league: League metadata (id, name, created, etc.)
        standings: List of league entries
        has_next: Whether there are more pages of standings
        page: Current page number
        matches_next: Upcoming matches (optional)
        matches_this: Current gameweek matches (optional)
    """
    league: Dict[str, Any]
    standings: List[H2HLeagueEntry]
    has_next: bool = False
    page: int = 1
    matches_next: Optional[List[H2HMatch]] = field(default_factory=list)
    matches_this: Optional[List[H2HMatch]] = field(default_factory=list)
    
    @property
    def league_id(self) -> int:
        """Get the league ID."""
        return self.league.get('id', 0)
    
    @property
    def league_name(self) -> str:
        """Get the league name."""
        return self.league.get('name', 'Unknown League')
    
    @property
    def total_entries(self) -> int:
        """Get total number of entries in the league."""
        return len(self.standings)
    
    def get_entry_by_manager_id(self, manager_id: int) -> Optional[H2HLeagueEntry]:
        """Find a league entry by manager ID."""
        for entry in self.standings:
            if entry.entry_id == manager_id:
                return entry
        return None
    
    def get_top_entries(self, n: int = 5) -> List[H2HLeagueEntry]:
        """Get the top N entries by rank."""
        return sorted(self.standings, key=lambda x: x.rank)[:n]
    
    @classmethod
    def from_api_response(cls, standings_data: Dict[str, Any]) -> 'H2HLeagueStandings':
        """
        Create H2HLeagueStandings from FPL API response data.
        
        Args:
            standings_data: Response from league standings endpoint
            
        Returns:
            H2HLeagueStandings instance
        """
        # Parse standings entries
        standings = []
        for entry_data in standings_data.get('standings', {}).get('results', []):
            standings.append(H2HLeagueEntry.from_api_response(entry_data))
        
        # Parse matches if available
        matches_next = []
        for match_data in standings_data.get('matches_next', []):
            matches_next.append(H2HMatch.from_api_response(match_data))
        
        matches_this = []
        for match_data in standings_data.get('matches_this', []):
            matches_this.append(H2HMatch.from_api_response(match_data))
        
        return cls(
            league=standings_data.get('league', {}),
            standings=standings,
            has_next=standings_data.get('standings', {}).get('has_next', False),
            page=standings_data.get('standings', {}).get('page', 1),
            matches_next=matches_next if matches_next else None,
            matches_this=matches_this if matches_this else None
        )