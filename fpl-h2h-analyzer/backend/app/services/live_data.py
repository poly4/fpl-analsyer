"""
FPL API Client Service with File-based Caching

This module provides the LiveDataService class, which handles all interactions
with the Fantasy Premier League API, including a file-based caching mechanism
to reduce API calls and improve performance.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlencode

import httpx

# Configure logging
logger = logging.getLogger(__name__)


class FPLException(Exception):
    """Base exception for FPL API related errors"""
    pass


class ManagerNotFoundException(FPLException):
    """Exception raised when a manager is not found"""
    pass


class LeagueNotFoundException(FPLException):
    """Exception raised when a league is not found"""
    pass


class APIRateLimitException(FPLException):
    """Exception raised when API rate limit is hit"""
    pass


class LiveDataService:
    """
    Service for fetching data from the Fantasy Premier League API with caching.
    
    This service implements a file-based caching mechanism to reduce API calls
    and improve performance. Cache files are stored in the .api_cache directory
    with a default TTL of 5 minutes.
    """
    
    def __init__(self, base_url: str = "https://fantasy.premierleague.com/api/"):
        """
        Initialize the LiveDataService.
        
        Args:
            base_url: Base URL for the FPL API (default: official FPL API)
        """
        self.base_url = base_url.rstrip('/') + '/'  # Ensure trailing slash
        self.cache_dir = ".api_cache"
        self.cache_ttl_seconds = 300  # 5 minutes
        
        # Create cache directory if it doesn't exist
        Path(self.cache_dir).mkdir(exist_ok=True)
        
        # Initialize HTTP client with appropriate headers
        self.client = httpx.AsyncClient(
            headers={
                'User-Agent': 'FPL-H2H-Analyzer/2.0 (https://github.com/yourusername/fpl-h2h-analyzer)',
                'Accept': 'application/json',
                'Accept-Language': 'en-GB,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            },
            timeout=30.0,
            follow_redirects=True
        )
        
        logger.info(f"LiveDataService initialized with base URL: {self.base_url}")
    
    def _generate_cache_key(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a unique cache key based on endpoint and parameters.
        
        Args:
            endpoint: API endpoint
            params: Optional query parameters
            
        Returns:
            Cache key string
        """
        # Clean endpoint for filename
        clean_endpoint = endpoint.strip('/').replace('/', '_').replace('{', '').replace('}', '')
        
        # Add sorted parameters to ensure consistent keys
        if params:
            sorted_params = sorted(params.items())
            param_str = '_'.join(f"{k}_{v}" for k, v in sorted_params)
            return f"{clean_endpoint}_{param_str}.json"
        
        return f"{clean_endpoint}.json"
    
    async def _fetch_data_with_caching(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch data from API with caching support.
        
        Args:
            endpoint: API endpoint to fetch
            params: Optional query parameters
            
        Returns:
            JSON response data or None if error
        """
        # Generate cache key and file path
        cache_key = self._generate_cache_key(endpoint, params)
        cache_path = Path(self.cache_dir) / cache_key
        
        # Check cache
        if cache_path.exists():
            # Check if cache is still valid
            file_age = time.time() - cache_path.stat().st_mtime
            if file_age < self.cache_ttl_seconds:
                try:
                    with open(cache_path, 'r') as f:
                        data = json.load(f)
                    logger.info(f"Cache hit for {endpoint} (age: {file_age:.1f}s)")
                    return data
                except json.JSONDecodeError:
                    logger.warning(f"Invalid cache file {cache_path}, will refetch")
            else:
                logger.info(f"Cache expired for {endpoint} (age: {file_age:.1f}s)")
        
        # Cache miss or expired - fetch from API
        try:
            # Construct full URL with proper trailing slash
            url = self.base_url + endpoint.strip('/')
            if not url.endswith('/'):
                url += '/'
            
            # Add query parameters if provided
            if params:
                url += '?' + urlencode(params)
            
            logger.info(f"Fetching from API: {url}")
            
            # Make the request
            response = await self.client.get(url)
            
            # Check for rate limiting
            if response.status_code == 429:
                logger.error(f"Rate limit hit for {url}")
                raise APIRateLimitException(f"Rate limit exceeded for {endpoint}")
            
            # Raise for other HTTP errors
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            
            # Save to cache
            try:
                with open(cache_path, 'w') as f:
                    json.dump(data, f, indent=2)
                logger.info(f"Cached response for {endpoint}")
            except IOError as e:
                logger.warning(f"Failed to cache response: {e}")
            
            return data
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                if 'manager' in endpoint or 'entry' in endpoint:
                    raise ManagerNotFoundException(f"Manager not found: {endpoint}")
                elif 'league' in endpoint:
                    raise LeagueNotFoundException(f"League not found: {endpoint}")
            logger.error(f"HTTP error fetching {endpoint}: {e}")
            return None
            
        except httpx.RequestError as e:
            logger.error(f"Request error fetching {endpoint}: {e}")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error fetching {endpoint}: {e}")
            return None
    
    async def get_bootstrap_static(self) -> Optional[Dict[str, Any]]:
        """
        Get bootstrap-static data containing players, teams, and general game data.
        
        Returns:
            Bootstrap static data or None if error
        """
        return await self._fetch_data_with_caching("bootstrap-static")
    
    async def get_manager_info(self, manager_id: int) -> Optional[Dict[str, Any]]:
        """
        Get manager profile information.
        
        Args:
            manager_id: FPL manager ID
            
        Returns:
            Manager info data or None if error
        """
        return await self._fetch_data_with_caching(f"entry/{manager_id}")
    
    async def get_manager_history(self, manager_id: int) -> Optional[Dict[str, Any]]:
        """
        Get manager's historical performance data.
        
        Args:
            manager_id: FPL manager ID
            
        Returns:
            Manager history data or None if error
        """
        return await self._fetch_data_with_caching(f"entry/{manager_id}/history")
    
    async def get_manager_picks(self, manager_id: int, gameweek: int) -> Optional[Dict[str, Any]]:
        """
        Get manager's team picks for a specific gameweek.
        
        Args:
            manager_id: FPL manager ID
            gameweek: Gameweek number
            
        Returns:
            Manager picks data or None if error
        """
        return await self._fetch_data_with_caching(f"entry/{manager_id}/event/{gameweek}/picks")
    
    async def get_h2h_league_standings(self, league_id: int, page: int = 1) -> Optional[Dict[str, Any]]:
        """
        Get H2H league standings.
        
        Args:
            league_id: H2H league ID
            page: Page number for paginated results (default: 1)
            
        Returns:
            H2H league standings data or None if error
        """
        params = {"page_standings": page}
        return await self._fetch_data_with_caching(f"leagues-h2h/{league_id}/standings", params)
    
    async def get_h2h_league_matches(self, league_id: int, page: int = 1) -> Optional[Dict[str, Any]]:
        """
        Get H2H league matches.
        
        Args:
            league_id: H2H league ID
            page: Page number for paginated results (default: 1)
            
        Returns:
            H2H league matches data or None if error
        """
        params = {"page": page}
        return await self._fetch_data_with_caching(f"leagues-h2h-matches/league/{league_id}", params)
    
    async def get_live_gameweek_data(self, gameweek: int) -> Optional[Dict[str, Any]]:
        """
        Get live gameweek data with player points and bonus.
        
        Args:
            gameweek: Gameweek number
            
        Returns:
            Live gameweek data or None if error
        """
        return await self._fetch_data_with_caching(f"event/{gameweek}/live")
    
    async def get_fixture_data(self, gameweek: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get fixture data, optionally filtered by gameweek.
        
        Args:
            gameweek: Optional gameweek number to filter fixtures
            
        Returns:
            Fixture data or None if error
        """
        params = {"event": gameweek} if gameweek else None
        return await self._fetch_data_with_caching("fixtures", params)
    
    async def get_current_gameweek(self) -> Optional[int]:
        """
        Get the current gameweek number.
        
        Returns:
            Current gameweek number or None if error
        """
        bootstrap_data = await self.get_bootstrap_static()
        if not bootstrap_data:
            logger.error("Failed to fetch bootstrap data for current gameweek")
            return None
        
        # Find the current gameweek
        events = bootstrap_data.get('events', [])
        for event in events:
            if event.get('is_current', False):
                return event.get('id')
        
        # If no current gameweek, find the latest finished one
        finished_events = [e for e in events if e.get('finished', False)]
        if finished_events:
            return max(finished_events, key=lambda e: e.get('id', 0)).get('id')
        
        logger.warning("Could not determine current gameweek")
        return None
    
    async def warm_cache(self, league_id: Optional[int] = None, manager_ids: Optional[List[int]] = None):
        """
        Pre-warm the cache with commonly used data.
        
        Args:
            league_id: Optional league ID to warm cache for
            manager_ids: Optional list of manager IDs to warm cache for
        """
        tasks = []
        
        # Always warm bootstrap data and current gameweek
        tasks.append(self.get_bootstrap_static())
        tasks.append(self.get_current_gameweek())
        
        # Warm league data if provided
        if league_id:
            tasks.append(self.get_h2h_league_standings(league_id))
            tasks.append(self.get_h2h_league_matches(league_id))
        
        # Warm manager data if provided
        if manager_ids:
            for manager_id in manager_ids:
                tasks.append(self.get_manager_info(manager_id))
                tasks.append(self.get_manager_history(manager_id))
        
        # Execute all warm-up tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if r is not None and not isinstance(r, Exception))
        logger.info(f"Cache warmed with {success_count}/{len(tasks)} successful fetches")
    
    async def clear_cache(self, older_than_seconds: Optional[int] = None):
        """
        Clear cache files, optionally only those older than specified seconds.
        
        Args:
            older_than_seconds: Only clear files older than this many seconds
        """
        cache_path = Path(self.cache_dir)
        current_time = time.time()
        cleared_count = 0
        
        for cache_file in cache_path.glob("*.json"):
            if older_than_seconds:
                file_age = current_time - cache_file.stat().st_mtime
                if file_age < older_than_seconds:
                    continue
            
            try:
                cache_file.unlink()
                cleared_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete cache file {cache_file}: {e}")
        
        logger.info(f"Cleared {cleared_count} cache files")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the FPL API connection.
        
        Returns:
            Health check status
        """
        try:
            start_time = time.time()
            data = await self._fetch_data_with_caching("bootstrap-static")
            elapsed = time.time() - start_time
            
            return {
                "healthy": data is not None,
                "response_time_ms": int(elapsed * 1000),
                "cache_size": len(list(Path(self.cache_dir).glob("*.json"))),
                "api_reachable": data is not None
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "cache_size": len(list(Path(self.cache_dir).glob("*.json"))),
                "api_reachable": False
            }
    
    async def get_fixtures(self, event: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get fixture data for a specific gameweek or all fixtures.
        
        Args:
            event: Optional gameweek number
            
        Returns:
            Fixture data or None if error
        """
        endpoint = "fixtures"
        params = {"event": event} if event else None
        return await self._fetch_data_with_caching(endpoint, params)

    async def get_manager_transfers(self, manager_id: int) -> Optional[Dict[str, Any]]:
        """
        Get manager's transfer history.
        
        Args:
            manager_id: FPL manager ID
            
        Returns:
            Transfer history data or None if error
        """
        return await self._fetch_data_with_caching(f"entry/{manager_id}/transfers")

    async def get_h2h_standings(self, league_id: int) -> Optional[Dict[str, Any]]:
        """
        Get H2H league standings.
        
        Args:
            league_id: H2H league ID
            
        Returns:
            H2H league standings data or None if error
        """
        return await self._fetch_data_with_caching(f"leagues-h2h/{league_id}/standings")

    async def get_h2h_matches(self, league_id: int, gameweek: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get H2H matches for a league.
        
        Args:
            league_id: H2H league ID
            gameweek: Optional gameweek filter
            
        Returns:
            List of H2H matches
        """
        params = {"event": gameweek} if gameweek else None
        data = await self._fetch_data_with_caching(f"leagues-h2h-matches/league/{league_id}", params)
        
        if data and "results" in data:
            return data["results"]
        return []

    async def invalidate_cache(self, pattern: Optional[str] = None):
        """Invalidate cache entries matching pattern."""
        cache_path = Path(self.cache_dir)
        if pattern:
            for cache_file in cache_path.glob(f"*{pattern}*"):
                try:
                    cache_file.unlink()
                    logger.info(f"Invalidated cache file: {cache_file}")
                except Exception as e:
                    logger.error(f"Error deleting cache file {cache_file}: {e}")
        else:
            # Clear all cache
            for cache_file in cache_path.glob("*.json"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.error(f"Error deleting cache file {cache_file}: {e}")

    async def warm_cache(self, league_id: int):
        """Pre-warm cache with frequently accessed data."""
        logger.info(f"Warming cache for league {league_id}")
        
        # Get current gameweek first
        bootstrap = await self.get_bootstrap_static()
        if bootstrap:
            current_gw = await self.get_current_gameweek()
            if current_gw:
                # Warm up common endpoints
                await self.get_h2h_standings(league_id)
                await self.get_h2h_matches(league_id, current_gw)
                await self.get_live_gameweek_data(current_gw)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        cache_path = Path(self.cache_dir)
        cache_files = list(cache_path.glob("*.json"))
        
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            "cache_dir": str(cache_path),
            "total_files": len(cache_files),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "oldest_file": min(cache_files, key=lambda f: f.stat().st_mtime).name if cache_files else None,
            "newest_file": max(cache_files, key=lambda f: f.stat().st_mtime).name if cache_files else None
        }

    async def close(self):
        """Close the HTTP client connection."""
        await self.client.aclose()
        logger.info("LiveDataService HTTP client closed")