from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from ..services.live_data import LiveDataService
from ..models.manager import ManagerProfile, GameweekPerformance, ChipUsage
from ..models.h2h_league import H2HMatch, H2HLeagueEntry, H2HLeagueStandings

class H2HAnalyzer:
    """Core service for analyzing head-to-head battles between FPL managers."""
    
    def __init__(self, live_data_service: LiveDataService):
        """
        Initialize the H2H Analyzer.
        
        Args:
            live_data_service: Service for fetching live FPL data
        """
        self.live_data_service = live_data_service
        self._bootstrap_cache = None
        self._chip_multipliers = {
            'bboost': 1.0,  # Bench boost - no multiplier, just adds bench points
            'freehit': 1.0,  # Free hit - no multiplier
            '3xc': 3.0,      # Triple captain
            'wildcard': 1.0  # Wildcard - no multiplier
        }

    async def get_bootstrap_static(self) -> Dict[str, Any]:
        """Get cached bootstrap data with player and team information."""
        if not self._bootstrap_cache:
            self._bootstrap_cache = await self.live_data_service.get_bootstrap_static()
        return self._bootstrap_cache
    
    async def get_bootstrap_data(self) -> Dict[str, Any]:
        """Alias for get_bootstrap_static for backward compatibility."""
        return await self.get_bootstrap_static()

    async def analyze_battle(self, manager1_id: int, manager2_id: int, gameweek: int) -> Dict[str, Any]:
        """
        Analyzes an H2H battle between two managers for a specific gameweek.
        
        Args:
            manager1_id: First manager's ID
            manager2_id: Second manager's ID
            gameweek: Gameweek number to analyze
            
        Returns:
            Dict containing battle analysis with scores, differentials, and details
        """
        # Fetch all required data concurrently for better performance
        live_data = await self.live_data_service.get_live_gameweek_data(gameweek)
        
        # Fetch both managers' data
        manager1_picks = await self.live_data_service.get_manager_picks(manager1_id, gameweek)
        manager2_picks = await self.live_data_service.get_manager_picks(manager2_id, gameweek)
        
        manager1_info = await self.live_data_service.get_manager_info(manager1_id)
        manager2_info = await self.live_data_service.get_manager_info(manager2_id)
        
        # Calculate live scores with chip effects
        manager1_score = await self._calculate_live_score(manager1_picks, live_data, gameweek)
        manager2_score = await self._calculate_live_score(manager2_picks, live_data, gameweek)
        
        # Get differentials with detailed information
        differentials = await self._get_differentials_with_details(
            manager1_picks, manager2_picks, live_data, manager1_id, manager2_id
        )
        
        # Calculate point swing contribution for each differential
        point_swings = self._calculate_point_swings(differentials)
        
        # Get chip usage
        manager1_chip = manager1_picks.get('active_chip')
        manager2_chip = manager2_picks.get('active_chip')
        
        # Build comprehensive battle analysis
        return {
            "gameweek": gameweek,
            "timestamp": datetime.utcnow().isoformat(),
            "manager1": {
                "id": manager1_id,
                "name": manager1_info.get('name', ''),
                "player_name": f"{manager1_info.get('player_first_name', '')} {manager1_info.get('player_last_name', '')}".strip(),
                "score": manager1_score,
                "chip": manager1_chip,
                "formation": await self._get_formation(manager1_picks),
                "captain": await self._get_captain_info(manager1_picks, live_data),
                "bench_points": self._calculate_bench_points(manager1_picks, live_data)
            },
            "manager2": {
                "id": manager2_id,
                "name": manager2_info.get('name', ''),
                "player_name": f"{manager2_info.get('player_first_name', '')} {manager2_info.get('player_last_name', '')}".strip(),
                "score": manager2_score,
                "chip": manager2_chip,
                "formation": await self._get_formation(manager2_picks),
                "captain": await self._get_captain_info(manager2_picks, live_data),
                "bench_points": self._calculate_bench_points(manager2_picks, live_data)
            },
            "differentials": differentials,
            "point_swings": point_swings,
            "score_difference": manager1_score['total'] - manager2_score['total'],
            "leader": manager1_id if manager1_score['total'] > manager2_score['total'] else manager2_id,
            "is_tied": manager1_score['total'] == manager2_score['total']
        }

    async def _calculate_live_score(self, picks_data: Dict[str, Any], live_data: Dict[str, Any], gameweek: int) -> Dict[str, Any]:
        """
        Calculate live score for a manager with chip effects.
        
        Args:
            picks_data: Manager's picks data
            live_data: Live gameweek data
            gameweek: Current gameweek number
            
        Returns:
            Dict with total score, breakdown, and chip information
        """
        if not picks_data or 'picks' not in picks_data:
            return {"total": 0, "breakdown": [], "bench_breakdown": [], "error": "No picks data"}
            
        total_score = 0
        starting_xi_score = 0
        bench_score = 0
        player_scores = []
        bench_scores = []
        
        # Get live player data and bootstrap for additional info
        elements = live_data.get('elements', [])
        bootstrap = await self.get_bootstrap_data()
        players_dict = {p['id']: p for p in bootstrap.get('elements', [])}
        
        active_chip = picks_data.get('active_chip')
        
        for pick in picks_data.get('picks', []):
            player_id = pick['element']
            multiplier = pick['multiplier']
            position = pick['position']
            
            # Find player in live data
            player_live = next((p for p in elements if p['id'] == player_id), None)
            player_info = players_dict.get(player_id, {})
            
            if player_live:
                # Get player points
                player_points = player_live.get('stats', {}).get('total_points', 0)
                
                # Apply triple captain multiplier if active
                if active_chip == '3xc' and pick.get('is_captain', False):
                    multiplier = 3
                
                actual_points = player_points * multiplier
                
                player_data = {
                    "player_id": player_id,
                    "web_name": player_info.get('web_name', 'Unknown'),
                    "position": position,
                    "points": player_points,
                    "multiplier": multiplier,
                    "actual_points": actual_points,
                    "is_captain": pick.get('is_captain', False),
                    "is_vice_captain": pick.get('is_vice_captain', False),
                    "minutes": player_live.get('stats', {}).get('minutes', 0)
                }
                
                # Determine if player is in starting XI or on bench
                if position <= 11:
                    starting_xi_score += actual_points
                    player_scores.append(player_data)
                else:
                    bench_score += player_points  # Bench points aren't multiplied
                    bench_scores.append(player_data)
        
        # Apply bench boost if active
        if active_chip == 'bboost':
            total_score = starting_xi_score + bench_score
        else:
            total_score = starting_xi_score
        
        return {
            "total": total_score,
            "starting_xi_score": starting_xi_score,
            "bench_score": bench_score,
            "breakdown": sorted(player_scores, key=lambda x: x['position']),
            "bench_breakdown": sorted(bench_scores, key=lambda x: x['position']),
            "chip": active_chip,
            "chip_active": active_chip is not None
        }

    async def _get_differentials(self, picks1: Dict[str, Any], picks2: Dict[str, Any], live_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get player differentials between two managers."""
        if not picks1 or not picks2:
            return []
            
        # Get player IDs for each manager
        players1 = {p['element'] for p in picks1.get('picks', [])}
        players2 = {p['element'] for p in picks2.get('picks', [])}
        
        # Find differentials
        only_manager1 = players1 - players2
        only_manager2 = players2 - players1
        
        differentials = []
        elements = live_data.get('elements', [])
        
        # Process manager1's unique players
        for player_id in only_manager1:
            player_live = next((p for p in elements if p['id'] == player_id), None)
            if player_live:
                differentials.append({
                    "player_id": player_id,
                    "owned_by": "manager1",
                    "points": player_live.get('stats', {}).get('total_points', 0)
                })
        
        # Process manager2's unique players  
        for player_id in only_manager2:
            player_live = next((p for p in elements if p['id'] == player_id), None)
            if player_live:
                differentials.append({
                    "player_id": player_id,
                    "owned_by": "manager2",
                    "points": player_live.get('stats', {}).get('total_points', 0)
                })
        
        return sorted(differentials, key=lambda x: x['points'], reverse=True)

    async def _get_differentials_with_details(self, picks1: Dict[str, Any], picks2: Dict[str, Any], 
                                            live_data: Dict[str, Any], manager1_id: int, manager2_id: int) -> List[Dict[str, Any]]:
        """
        Get detailed differential analysis between two managers.
        
        Args:
            picks1: First manager's picks
            picks2: Second manager's picks
            live_data: Live gameweek data
            manager1_id: First manager's ID
            manager2_id: Second manager's ID
            
        Returns:
            List of differentials with detailed player information
        """
        if not picks1 or not picks2:
            return []
            
        # Get bootstrap data for player details
        bootstrap = await self.get_bootstrap_data()
        players_dict = {p['id']: p for p in bootstrap.get('elements', [])}
        teams_dict = {t['id']: t for t in bootstrap.get('teams', [])}
        positions = {1: 'GKP', 2: 'DEF', 3: 'MID', 4: 'FWD'}
        
        # Create dictionaries of players with their captaincy status
        players1_dict = {p['element']: p for p in picks1.get('picks', []) if p['position'] <= 11}
        players2_dict = {p['element']: p for p in picks2.get('picks', []) if p['position'] <= 11}
        
        # Get player IDs for each manager (starting XI only)
        players1 = set(players1_dict.keys())
        players2 = set(players2_dict.keys())
        
        # Find differentials
        only_manager1 = players1 - players2
        only_manager2 = players2 - players1
        common_players = players1 & players2
        
        differentials = []
        elements = live_data.get('elements', [])
        
        # Process manager1's unique players
        for player_id in only_manager1:
            player_live = next((p for p in elements if p['id'] == player_id), None)
            player_info = players_dict.get(player_id, {})
            if player_live and player_info:
                team_info = teams_dict.get(player_info.get('team', 0), {})
                pick_info = players1_dict[player_id]
                points = player_live.get('stats', {}).get('total_points', 0)
                
                # Apply captaincy multiplier
                if pick_info.get('is_captain'):
                    if picks1.get('active_chip') == '3xc':
                        points *= 3
                    else:
                        points *= 2
                
                differentials.append({
                    "player_id": player_id,
                    "owner": manager1_id,
                    "name": player_info.get('web_name', 'Unknown'),
                    "team": team_info.get('short_name', 'Unknown'),
                    "position": positions.get(player_info.get('element_type', 0), 'Unknown'),
                    "points": points,
                    "is_captain": pick_info.get('is_captain', False),
                    "ownership": player_info.get('selected_by_percent', 0),
                    "price": player_info.get('now_cost', 0) / 10,
                    "minutes": player_live.get('stats', {}).get('minutes', 0)
                })
        
        # Process manager2's unique players  
        for player_id in only_manager2:
            player_live = next((p for p in elements if p['id'] == player_id), None)
            player_info = players_dict.get(player_id, {})
            if player_live and player_info:
                team_info = teams_dict.get(player_info.get('team', 0), {})
                pick_info = players2_dict[player_id]
                points = player_live.get('stats', {}).get('total_points', 0)
                
                # Apply captaincy multiplier
                if pick_info.get('is_captain'):
                    if picks2.get('active_chip') == '3xc':
                        points *= 3
                    else:
                        points *= 2
                
                differentials.append({
                    "player_id": player_id,
                    "owner": manager2_id,
                    "name": player_info.get('web_name', 'Unknown'),
                    "team": team_info.get('short_name', 'Unknown'),
                    "position": positions.get(player_info.get('element_type', 0), 'Unknown'),
                    "points": points,
                    "is_captain": pick_info.get('is_captain', False),
                    "ownership": player_info.get('selected_by_percent', 0),
                    "price": player_info.get('now_cost', 0) / 10,
                    "minutes": player_live.get('stats', {}).get('minutes', 0)
                })
        
        # Check for captain differentials (same player but different captaincy)
        for player_id in common_players:
            pick1 = players1_dict[player_id]
            pick2 = players2_dict[player_id]
            
            if pick1.get('is_captain') != pick2.get('is_captain'):
                player_live = next((p for p in elements if p['id'] == player_id), None)
                player_info = players_dict.get(player_id, {})
                if player_live and player_info:
                    team_info = teams_dict.get(player_info.get('team', 0), {})
                    base_points = player_live.get('stats', {}).get('total_points', 0)
                    
                    differentials.append({
                        "player_id": player_id,
                        "owner": manager1_id if pick1.get('is_captain') else manager2_id,
                        "name": player_info.get('web_name', 'Unknown'),
                        "team": team_info.get('short_name', 'Unknown'),
                        "position": positions.get(player_info.get('element_type', 0), 'Unknown'),
                        "points": base_points,  # Base points for comparison
                        "is_captain": True,
                        "is_captain_differential": True,
                        "ownership": player_info.get('selected_by_percent', 0),
                        "price": player_info.get('now_cost', 0) / 10,
                        "minutes": player_live.get('stats', {}).get('minutes', 0)
                    })
        
        return sorted(differentials, key=lambda x: abs(x['points']), reverse=True)

    async def _get_recent_transfers(self, manager_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent transfers for a manager."""
        try:
            history = await self.live_data_service.get_manager_history(manager_id)
            bootstrap = await self.get_bootstrap_data()
            players_dict = {p['id']: p for p in bootstrap.get('elements', [])}
            
            transfers = []
            for transfer in history.get('current', [])[-limit:]:
                if 'event_transfers' in transfer and transfer['event_transfers'] > 0:
                    # Note: Actual transfer details would need a separate API call
                    # This is a simplified version
                    transfers.append({
                        "gameweek": transfer.get('event', 0),
                        "transfers_made": transfer.get('event_transfers', 0),
                        "points_hit": transfer.get('event_transfers_cost', 0)
                    })
            
            return transfers
        except:
            return []

    def _calculate_point_swings(self, differentials: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate Point Swing Contribution (PSC) for each differential.
        
        Args:
            differentials: List of differential players
            
        Returns:
            Dict with PSC analysis
        """
        if not differentials:
            return {
                "manager1_total_swing": 0,
                "manager2_total_swing": 0,
                "net_swing": 0,
                "biggest_positive_swing": None,
                "biggest_negative_swing": None,
                "swing_players": 0
            }
        
        # Group differentials by owner to handle multiple managers
        swings_by_owner = {}
        biggest_positive_swing = None
        biggest_negative_swing = None
        
        for diff in differentials:
            points = diff['points']
            owner = diff['owner']
            
            # Initialize if not seen
            if owner not in swings_by_owner:
                swings_by_owner[owner] = 0
            
            # Add to owner's swing
            swings_by_owner[owner] += points
            
            # Track biggest swings
            if not biggest_positive_swing or points > biggest_positive_swing.get('points', 0):
                biggest_positive_swing = diff
            
        # Get the two managers (should only be 2 in H2H)
        owners = list(swings_by_owner.keys())
        manager1_id = owners[0] if owners else None
        manager2_id = owners[1] if len(owners) > 1 else None
        
        manager1_swing = swings_by_owner.get(manager1_id, 0) if manager1_id else 0
        manager2_swing = swings_by_owner.get(manager2_id, 0) if manager2_id else 0
        
        return {
            "manager1_total_swing": manager1_swing,
            "manager2_total_swing": manager2_swing,
            "net_swing": abs(manager1_swing - manager2_swing),
            "biggest_positive_swing": biggest_positive_swing,
            "biggest_negative_swing": biggest_negative_swing,
            "swing_players": len(differentials)
        }
    
    async def _get_formation(self, picks_data: Dict[str, Any]) -> str:
        """
        Determine formation from picks data.
        
        Args:
            picks_data: Manager's picks data
            
        Returns:
            Formation string (e.g., "3-4-3")
        """
        if not picks_data or 'picks' not in picks_data:
            return "Unknown"
        
        # Get bootstrap data to map player IDs to positions
        bootstrap = await self.get_bootstrap_data()
        players_dict = {p['id']: p for p in bootstrap.get('elements', [])}
        
        position_counts = {1: 0, 2: 0, 3: 0, 4: 0}  # GKP, DEF, MID, FWD
        
        for pick in picks_data.get('picks', []):
            if pick['position'] <= 11:  # Starting XI only
                player_id = pick['element']
                player_info = players_dict.get(player_id, {})
                element_type = player_info.get('element_type', 0)
                if element_type in position_counts:
                    position_counts[element_type] += 1
        
        # Format as DEF-MID-FWD (excluding GKP)
        return f"{position_counts[2]}-{position_counts[3]}-{position_counts[4]}"
    
    async def _get_captain_info(self, picks_data: Dict[str, Any], live_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get captain information with points.
        
        Args:
            picks_data: Manager's picks data
            live_data: Live gameweek data
            
        Returns:
            Dict with captain details
        """
        if not picks_data or 'picks' not in picks_data:
            return {"name": "Unknown", "points": 0}
        
        bootstrap = await self.get_bootstrap_data()
        players_dict = {p['id']: p for p in bootstrap.get('elements', [])}
        elements = live_data.get('elements', [])
        
        for pick in picks_data.get('picks', []):
            if pick.get('is_captain'):
                player_id = pick['element']
                player_info = players_dict.get(player_id, {})
                player_live = next((p for p in elements if p['id'] == player_id), None)
                
                if player_info and player_live:
                    return {
                        "id": player_id,
                        "name": player_info.get('web_name', 'Unknown'),
                        "points": player_live.get('stats', {}).get('total_points', 0),
                        "multiplier": 3 if picks_data.get('active_chip') == '3xc' else 2
                    }
        
        return {"name": "Unknown", "points": 0}
    
    def _calculate_bench_points(self, picks_data: Dict[str, Any], live_data: Dict[str, Any]) -> int:
        """
        Calculate total bench points.
        
        Args:
            picks_data: Manager's picks data
            live_data: Live gameweek data
            
        Returns:
            Total bench points
        """
        if not picks_data or 'picks' not in picks_data:
            return 0
        
        bench_points = 0
        elements = live_data.get('elements', [])
        
        for pick in picks_data.get('picks', []):
            if pick['position'] > 11:  # Bench players
                player_id = pick['element']
                player_live = next((p for p in elements if p['id'] == player_id), None)
                if player_live:
                    bench_points += player_live.get('stats', {}).get('total_points', 0)
        
        return bench_points

    async def get_h2h_matches(self, league_id: int, gameweek: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get H2H matches for a league from the FPL API.
        
        Args:
            league_id: H2H league ID
            gameweek: Optional gameweek filter
            
        Returns:
            List of H2H match dictionaries
        """
        all_matches = []
        page = 1
        
        # Fetch all pages of matches
        while True:
            try:
                url = f"leagues-h2h-matches/league/{league_id}/"
                if page > 1:
                    url += f"?page={page}"
                    
                data = await self.live_data_service._fetch_data_with_caching(url)
                
                if not data or 'results' not in data:
                    break
                    
                matches = data.get('results', [])
                
                # Filter by gameweek if specified
                if gameweek:
                    matches = [m for m in matches if m.get('event') == gameweek]
                    
                all_matches.extend(matches)
                
                # Check if there are more pages
                if not data.get('has_next', False) or gameweek:
                    break
                    
                page += 1
                
            except Exception as e:
                print(f"Error fetching H2H matches page {page}: {e}")
                break
                
        return all_matches

    async def get_current_h2h_match(self, league_id: int, manager1_id: int, manager2_id: int, gameweek: int) -> Optional[Dict[str, Any]]:
        """
        Get the current H2H match between two managers in a specific gameweek.
        
        Args:
            league_id: H2H league ID
            manager1_id: First manager's ID
            manager2_id: Second manager's ID
            gameweek: Gameweek number
            
        Returns:
            H2H match data if found, None otherwise
        """
        matches = await self.get_h2h_matches(league_id, gameweek)
        
        # Find the match between these two managers
        for match in matches:
            entry_1 = match.get('entry_1_entry')
            entry_2 = match.get('entry_2_entry')
            
            if (entry_1 == manager1_id and entry_2 == manager2_id) or \
               (entry_1 == manager2_id and entry_2 == manager1_id):
                return match
                
        return None

    async def get_h2h_standings(self, league_id: int) -> Dict[str, Any]:
        """
        Get H2H league standings.
        
        Args:
            league_id: H2H league ID
            
        Returns:
            Dict with league and standings data from FPL API
        """
        return await self.live_data_service.get_h2h_standings(league_id)