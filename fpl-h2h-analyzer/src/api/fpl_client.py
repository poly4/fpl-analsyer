# FPL API Client
# This file will contain the FPLAPIClient class for fetching data from the FPL API.

import requests
import time
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

from config import FPL_API_BASE_URL, CACHE_DIR, CACHE_EXPIRY_SECONDS

class FPLAPIClient:
    """Client to interact with the official FPL API."""

    def __init__(self, base_url: str = FPL_API_BASE_URL, cache_dir: str = CACHE_DIR, cache_expiry: int = CACHE_EXPIRY_SECONDS):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        })
        self.cache_dir = Path(cache_dir)
        self.cache_expiry = cache_expiry
        self._ensure_cache_dir_exists()

    def _ensure_cache_dir_exists(self):
        """Creates the cache directory if it doesn't exist."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Path:
        """Generates a unique cache file path for an endpoint and its parameters."""
        param_str = "_" + "_".join(f"{k}_{v}" for k, v in sorted(params.items())) if params else ""
        filename = f"{endpoint.replace('/', '_')}{param_str}.json"
        return self.cache_dir / filename

    def _read_from_cache(self, cache_path: Path) -> Optional[Dict[str, Any]]:
        """Reads data from cache if it exists and is not expired."""
        if cache_path.exists():
            try:
                file_mod_time = cache_path.stat().st_mtime
                if (time.time() - file_mod_time) < self.cache_expiry:
                    with open(cache_path, 'r') as f:
                        return json.load(f)
            except (IOError, json.JSONDecodeError) as e:
                print(f"Error reading from cache {cache_path}: {e}")
                return None
        return None

    def _write_to_cache(self, cache_path: Path, data: Dict[str, Any]):
        """Writes data to the cache."""
        try:
            with open(cache_path, 'w') as f:
                json.dump(data, f)
        except IOError as e:
            print(f"Error writing to cache {cache_path}: {e}")

    def _get_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Makes a GET request to the FPL API, utilizing cache."""
        # Ensure endpoint doesn't start with slash and base_url ends with slash
        endpoint = endpoint.lstrip('/')
        base_url = self.base_url
        if not base_url.endswith('/'):
            base_url += '/'

        # Ensure endpoint ends with trailing slash (CRITICAL for FPL API)
        if not endpoint.endswith('/') and '?' not in endpoint:
            endpoint += '/'

        url = f"{base_url}{endpoint}"
        cache_path = self._get_cache_path(endpoint, params)

        cached_data = self._read_from_cache(cache_path)
        if cached_data:
            # print(f"Cache hit for {url} with params {params}")
            return cached_data

        # print(f"Cache miss for {url} with params {params}. Fetching from API...")
        retries = 3
        for attempt in range(retries):
            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
                data = response.json()
                self._write_to_cache(cache_path, data)
                return data
            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt + 1}/{retries} failed for {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(2) # Wait before retrying
                else:
                    print(f"Max retries reached for {url}. Giving up.")
                    return None
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from {url}: {e}")
                return None
        return None # Should not be reached if retries > 0, but good practice

    def get_bootstrap_static(self) -> Optional[Dict[str, Any]]:
        """Fetches general FPL game data (players, teams, events, etc.)."""
        return self._get_request("bootstrap-static")

    def get_manager_info(self, manager_id: int) -> Optional[Dict[str, Any]]:
        """Fetches a specific manager's profile information."""
        data = self._get_request(f"entry/{manager_id}")
        if data:
            # The API doesn't return summary fields anymore, calculate them
            if 'current' in data:
                # Get latest gameweek data for overall rank/points
                current_gw = data['current'][-1] if data['current'] else None
                if current_gw:
                    data['summary_overall_rank'] = current_gw.get('overall_rank')
                    data['summary_overall_points'] = current_gw.get('total_points')
            return data
        return None

    def get_manager_history(self, manager_id: int) -> Optional[Dict[str, Any]]:
        """Fetches a manager's past seasons and current gameweek history."""
        return self._get_request(f"entry/{manager_id}/history")

    def get_manager_picks(self, manager_id: int, gameweek: int) -> Optional[Dict[str, Any]]:
        """Fetches a manager's team picks for a specific gameweek."""
        return self._get_request(f"entry/{manager_id}/event/{gameweek}/picks")

    def get_h2h_league_standings(self, league_id: int, page: int = 1) -> Optional[Dict[str, Any]]:
        """Fetches the H2H league standings. Supports pagination."""
        # The API endpoint for H2H standings might require page parameter for leagues with many teams
        # e.g. /api/leagues-h2h/{league_id}/standings/?page_standings={page}
        # For simplicity, assuming a direct endpoint, but this might need adjustment.
        # The official API seems to use `page_standings` for this.
        return self._get_request(f"leagues-h2h/{league_id}/standings", params={"page_standings": page})

    def get_h2h_league_matches(self, league_id: int, gameweek: Optional[int] = None, page: int = 1) -> Optional[Dict[str, Any]]:
        """
        Fetches H2H matches for a league with better error handling.
        """
        # First, let's try to get all matches without pagination
        all_results = []
        current_page = 1
        max_pages = 50  # Safety limit
        
        while current_page <= max_pages:
            params = {"page": current_page}
            if gameweek is not None:
                params["event"] = gameweek
                
            # Try the correct endpoint format
            data = self._get_request(f"leagues-h2h-matches/league/{league_id}", params=params)
            
            if not data:
                print(f"No data returned for H2H matches, league {league_id}, page {current_page}")
                break
                
            if 'results' in data:
                results = data['results']
                if not results:
                    print(f"No results in page {current_page}")
                    break
                    
                all_results.extend(results)
                print(f"Fetched {len(results)} matches from page {current_page}")
                
                # Check if there are more pages
                if not data.get('has_next', False):
                    break
            else:
                print(f"Unexpected response format: {list(data.keys())}")
                # Try to use the data as-is if it's a list
                if isinstance(data, list):
                    all_results.extend(data)
                break
                
            current_page += 1
        
        print(f"Total H2H matches fetched: {len(all_results)}")
        return {'results': all_results, 'has_next': False}

# Example Usage (for testing purposes)
if __name__ == "__main__":
    client = FPLAPIClient()

    print("Fetching bootstrap static data...")
    bootstrap_data = client.get_bootstrap_static()
    if bootstrap_data:
        print(f"Fetched {len(bootstrap_data.get('elements', []))} players.")
        # print(json.dumps(bootstrap_data, indent=2))

    # Replace with actual IDs for testing
    test_manager_id = 1 # Example manager ID
    test_league_id = 314 # Example Premier League H2H league ID (official overall league)
    # For a private league, you'd need its specific ID.
    # You can find this by inspecting network requests when viewing the league on the FPL site.

    print(f"\nFetching manager info for ID {test_manager_id}...")
    manager_info = client.get_manager_info(test_manager_id)
    if manager_info:
        print(f"Manager Name: {manager_info.get('player_first_name')} {manager_info.get('player_last_name')}")
        # print(json.dumps(manager_info, indent=2))

    print(f"\nFetching manager history for ID {test_manager_id}...")
    manager_history = client.get_manager_history(test_manager_id)
    if manager_history:
        print(f"Current points: {manager_history.get('current', [{}])[0].get('points')}")
        # print(json.dumps(manager_history, indent=2))

    # Assuming current gameweek is 1 for testing picks, adjust if needed
    # You'd typically get the current gameweek from bootstrap_data
    current_gw = 1 
    if bootstrap_data:
        for event in bootstrap_data.get('events', []):
            if event.get('is_current') is True:
                current_gw = event.get('id')
                break
    
    print(f"\nFetching manager picks for ID {test_manager_id} in GW {current_gw}...")
    manager_picks = client.get_manager_picks(test_manager_id, current_gw)
    if manager_picks:
        print(f"Captain ID: {manager_picks.get('captain')}, Vice-Captain ID: {manager_picks.get('vice_captain')}")
        # print(json.dumps(manager_picks, indent=2))

    print(f"\nFetching H2H league standings for league ID {test_league_id}...")
    league_standings = client.get_h2h_league_standings(test_league_id)
    if league_standings and league_standings.get('standings', {}).get('results'):
        print(f"League Name: {league_standings.get('league', {}).get('name')}")
        print(f"First manager in standings: {league_standings['standings']['results'][0]['entry_name']}")
        # print(json.dumps(league_standings, indent=2))
    elif league_standings:
        print(f"League standings for {test_league_id} fetched but might be empty or in unexpected format.")
        # print(json.dumps(league_standings, indent=2))
    else:
        print(f"Failed to fetch league standings for {test_league_id}.")

    print(f"\nFetching H2H league matches for league ID {test_league_id}, GW {current_gw}...")
    league_matches = client.get_h2h_league_matches(league_id=test_league_id, gameweek=current_gw)
    if league_matches and league_matches.get('results'):
        print(f"Found {len(league_matches['results'])} matches for GW {current_gw}.")
        # print(json.dumps(league_matches, indent=2))
    elif league_matches:
        print(f"League matches for {test_league_id} GW {current_gw} fetched but might be empty or in unexpected format.")
        # print(json.dumps(league_matches, indent=2))
    else:
        print(f"Failed to fetch league matches for {test_league_id} GW {current_gw}.")

    # Test caching by fetching again
    print("\nFetching bootstrap static data again (should be cached)...")
    bootstrap_data_cached = client.get_bootstrap_static()
    if bootstrap_data_cached:
        print(f"Fetched {len(bootstrap_data_cached.get('elements', []))} players (from cache).")

    print("\nDone with FPLAPIClient tests.")