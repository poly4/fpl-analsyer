"""
Enhanced FPL API Client Service with Rate Limiting
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

from .rate_limiter import (
    RateLimitedFPLClient, 
    RateLimitConfig, 
    RequestPriority,
    get_endpoint_priority
)

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
    Enhanced service for fetching data from the Fantasy Premier League API 
    with rate limiting and intelligent caching.
    """
    
    def __init__(
        self, 
        base_url: str = "https://fantasy.premierleague.com/api/",
        redis_client: Optional[Any] = None,
        rate_limit_config: Optional[RateLimitConfig] = None
    ):
        """
        Initialize the enhanced LiveDataService.
        
        Args:
            base_url: Base URL for the FPL API
            redis_client: Optional Redis client for metrics
            rate_limit_config: Optional rate limit configuration
        """
        self.base_url = base_url.rstrip('/') + '/'
        self.cache_dir = ".api_cache"
        self.redis_client = redis_client
        
        # Cache TTL based on endpoint priority
        self.cache_ttls = {
            RequestPriority.CRITICAL: 30,      # 30 seconds
            RequestPriority.HIGH: 3600,        # 1 hour
            RequestPriority.MEDIUM: 1800,      # 30 minutes
            RequestPriority.LOW: 7200,         # 2 hours
        }
        
        # Create cache directory
        Path(self.cache_dir).mkdir(exist_ok=True)
        
        # Initialize base HTTP client
        self.base_client = httpx.AsyncClient(
            headers={
                'User-Agent': 'FPL-H2H-Analyzer/3.0 (Rate Limited)',
                'Accept': 'application/json',
                'Accept-Language': 'en-GB,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            },
            timeout=30.0,
            follow_redirects=True
        )
        
        # Initialize rate-limited client
        self.client = RateLimitedFPLClient(
            base_client=self,  # Pass self as base client
            config=rate_limit_config,
            redis_client=redis_client
        )
        
        # Track initialization
        self._initialized = False
        logger.info(f"LiveDataServiceV2 initialized with rate limiting")
    
    async def initialize(self):
        """Initialize the service and start rate limiter"""
        if not self._initialized:
            await self.client.start()
            self._initialized = True
            
            # Warm critical caches
            await self._warm_critical_caches()
    
    async def close(self):
        """Clean up resources"""
        if self._initialized:
            await self.client.stop()
            await self.base_client.aclose()
            self._initialized = False
    
    def _generate_cache_key(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Generate a unique cache key"""
        clean_endpoint = endpoint.strip('/').replace('/', '_').replace('{', '').replace('}', '')
        
        if params:
            sorted_params = sorted(params.items())
            param_str = '_'.join(f"{k}_{v}" for k, v in sorted_params)
            return f"{clean_endpoint}_{param_str}.json"
        
        return f"{clean_endpoint}.json"
    
    def _get_cache_ttl(self, endpoint: str) -> int:
        """Get cache TTL based on endpoint priority"""
        priority = get_endpoint_priority(endpoint)
        return self.cache_ttls.get(priority, 300)  # Default 5 minutes
    
    async def _check_cache(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Check if valid cached data exists"""
        cache_key = self._generate_cache_key(endpoint, params)
        cache_path = Path(self.cache_dir) / cache_key
        
        if cache_path.exists():
            file_age = time.time() - cache_path.stat().st_mtime
            cache_ttl = self._get_cache_ttl(endpoint)
            
            if file_age < cache_ttl:
                try:
                    with open(cache_path, 'r') as f:
                        data = json.load(f)
                    logger.debug(f"Cache hit for {endpoint} (age: {file_age:.1f}s, TTL: {cache_ttl}s)")
                    return data
                except json.JSONDecodeError:
                    logger.warning(f"Invalid cache file {cache_path}")
        
        return None
    
    async def _save_cache(self, endpoint: str, data: Dict[str, Any], params: Optional[Dict[str, Any]] = None):
        """Save data to cache"""
        cache_key = self._generate_cache_key(endpoint, params)
        cache_path = Path(self.cache_dir) / cache_key
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(data, f, separators=(',', ':'))
            logger.debug(f"Cached response for {endpoint}")
        except Exception as e:
            logger.error(f"Error caching response: {e}")
    
    async def request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make HTTP request (called by rate limiter).
        This method is used by the RateLimitedFPLClient.
        """
        # Check cache first
        if method.upper() == 'GET':
            params = kwargs.get('params')
            cached_data = await self._check_cache(endpoint, params)
            if cached_data:
                return cached_data
        
        # Construct full URL
        url = self.base_url + endpoint.strip('/')
        if not url.endswith('/'):
            url += '/'
        
        # Make request
        response = await self.base_client.request(method, url, **kwargs)
        
        # Handle errors
        if response.status_code == 429:
            raise APIRateLimitException("Rate limit exceeded")
        
        response.raise_for_status()
        
        # Parse JSON
        data = response.json()
        
        # Cache successful GET requests
        if method.upper() == 'GET' and data:
            await self._save_cache(endpoint, data, kwargs.get('params'))
        
        return data
    
    async def _fetch_with_priority(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        priority: Optional[RequestPriority] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch data with rate limiting and priority.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            priority: Request priority (auto-detected if None)
            
        Returns:
            API response data
        """
        if not self._initialized:
            await self.initialize()
        
        # Auto-detect priority if not provided
        if priority is None:
            priority = get_endpoint_priority(endpoint)
        
        try:
            # Make rate-limited request
            data = await self.client.request(
                'GET',
                endpoint,
                priority=priority,
                params=params
            )
            return data
            
        except ManagerNotFoundException:
            raise
        except LeagueNotFoundException:
            raise
        except APIRateLimitException:
            raise
        except Exception as e:
            logger.error(f"Error fetching {endpoint}: {e}")
            return None
    
    # API Methods with rate limiting
    
    async def get_bootstrap_static(self) -> Optional[Dict[str, Any]]:
        """Get bootstrap-static data (HIGH priority)"""
        return await self._fetch_with_priority("bootstrap-static", priority=RequestPriority.HIGH)
    
    async def get_current_gameweek(self) -> Optional[int]:
        """Get current gameweek number (HIGH priority)"""
        data = await self.get_bootstrap_static()
        if data and 'events' in data:
            for event in data['events']:
                if event.get('is_current'):
                    return event.get('id')
        return None
    
    async def get_manager_info(self, manager_id: int) -> Optional[Dict[str, Any]]:
        """Get manager profile (MEDIUM priority)"""
        return await self._fetch_with_priority(f"entry/{manager_id}", priority=RequestPriority.MEDIUM)
    
    async def get_manager_history(self, manager_id: int) -> Optional[Dict[str, Any]]:
        """Get manager history (MEDIUM priority)"""
        return await self._fetch_with_priority(f"entry/{manager_id}/history", priority=RequestPriority.MEDIUM)
    
    async def get_manager_picks(self, manager_id: int, gameweek: int) -> Optional[Dict[str, Any]]:
        """Get manager picks for gameweek (MEDIUM priority)"""
        return await self._fetch_with_priority(
            f"entry/{manager_id}/event/{gameweek}/picks",
            priority=RequestPriority.MEDIUM
        )
    
    async def get_live_gameweek_data(self, gameweek: int) -> Optional[Dict[str, Any]]:
        """Get live gameweek data (CRITICAL priority during matches)"""
        # Check if matches are currently live
        bootstrap = await self.get_bootstrap_static()
        is_live = False
        
        if bootstrap and 'events' in bootstrap:
            for event in bootstrap['events']:
                if event.get('id') == gameweek and event.get('is_current'):
                    # Check if deadline passed and not finished
                    deadline = datetime.fromisoformat(event.get('deadline_time', '').replace('Z', '+00:00'))
                    is_live = datetime.now(deadline.tzinfo) > deadline and not event.get('finished')
                    break
        
        priority = RequestPriority.CRITICAL if is_live else RequestPriority.HIGH
        return await self._fetch_with_priority(f"event/{gameweek}/live", priority=priority)
    
    async def get_fixtures(self, gameweek: Optional[int] = None) -> Optional[List[Dict[str, Any]]]:
        """Get fixtures data (HIGH priority)"""
        params = {'event': gameweek} if gameweek else None
        return await self._fetch_with_priority("fixtures", params=params, priority=RequestPriority.HIGH)
    
    async def get_h2h_league_standings(self, league_id: int, page: int = 1) -> Optional[Dict[str, Any]]:
        """Get H2H league standings (MEDIUM priority)"""
        params = {'page_standings': page}
        return await self._fetch_with_priority(
            f"leagues-h2h/{league_id}/standings",
            params=params,
            priority=RequestPriority.MEDIUM
        )
    
    async def get_h2h_matches(self, league_id: int, page: int = 1) -> Optional[Dict[str, Any]]:
        """Get H2H matches (MEDIUM priority)"""
        params = {'page': page} if page > 1 else None
        return await self._fetch_with_priority(
            f"leagues-h2h-matches/league/{league_id}",
            params=params,
            priority=RequestPriority.MEDIUM
        )
    
    # New endpoints to implement
    
    async def get_element_summary(self, player_id: int) -> Optional[Dict[str, Any]]:
        """Get player summary across seasons (LOW priority)"""
        return await self._fetch_with_priority(
            f"element-summary/{player_id}",
            priority=RequestPriority.LOW
        )
    
    async def get_dream_team(self, gameweek: int) -> Optional[Dict[str, Any]]:
        """Get dream team for gameweek (LOW priority)"""
        return await self._fetch_with_priority(
            f"dream-team/{gameweek}",
            priority=RequestPriority.LOW
        )
    
    async def get_manager_transfers(self, manager_id: int) -> Optional[Dict[str, Any]]:
        """Get complete transfer history (MEDIUM priority)"""
        return await self._fetch_with_priority(
            f"entry/{manager_id}/transfers",
            priority=RequestPriority.MEDIUM
        )
    
    async def get_manager_transfers_latest(self, manager_id: int) -> Optional[Dict[str, Any]]:
        """Get latest transfers (MEDIUM priority)"""
        return await self._fetch_with_priority(
            f"entry/{manager_id}/transfers-latest",
            priority=RequestPriority.MEDIUM
        )
    
    async def get_event_status(self) -> Optional[Dict[str, Any]]:
        """Get bonus processing status (CRITICAL during bonus processing)"""
        return await self._fetch_with_priority(
            "event-status",
            priority=RequestPriority.CRITICAL
        )
    
    async def get_set_piece_notes(self) -> Optional[Dict[str, Any]]:
        """Get penalty and set piece takers (LOW priority)"""
        return await self._fetch_with_priority(
            "team/set-piece-notes",
            priority=RequestPriority.LOW
        )
    
    # Cache management
    
    async def _warm_critical_caches(self):
        """Warm critical caches on startup"""
        priority_endpoints = [
            ("bootstrap-static", RequestPriority.HIGH),
            ("fixtures", RequestPriority.HIGH),
        ]
        
        # Get current gameweek
        gw = await self.get_current_gameweek()
        if gw:
            priority_endpoints.append((f"event/{gw}/live", RequestPriority.HIGH))
        
        await self.client.warm_cache(priority_endpoints)
    
    async def warm_cache(self, league_id: Optional[int] = None, manager_ids: Optional[List[int]] = None):
        """
        Pre-warm the cache with commonly used data.
        
        Args:
            league_id: Optional league ID to warm cache for
            manager_ids: Optional list of manager IDs to warm cache for
        """
        # Warm critical caches first
        await self._warm_critical_caches()
        
        # If league_id provided, warm league-specific data
        if league_id:
            current_gw = await self.get_current_gameweek()
            if current_gw:
                # Warm league standings and matches
                await self.get_h2h_league_standings(league_id)
                await self.get_h2h_matches(league_id, current_gw)
        
        # If manager_ids provided, warm manager-specific data
        if manager_ids:
            for manager_id in manager_ids[:10]:  # Limit to 10 managers
                await self.get_manager_info(manager_id)
                await self.get_manager_history(manager_id)
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        cache_path = Path(self.cache_dir)
        cache_files = list(cache_path.glob("*.json"))
        
        total_size = sum(f.stat().st_size for f in cache_files) / (1024 * 1024)  # MB
        
        # Group by age
        now = time.time()
        age_groups = {
            'fresh': 0,      # < 1 minute
            'recent': 0,     # < 5 minutes
            'valid': 0,      # < TTL
            'expired': 0     # > TTL
        }
        
        for f in cache_files:
            age = now - f.stat().st_mtime
            if age < 60:
                age_groups['fresh'] += 1
            elif age < 300:
                age_groups['recent'] += 1
            elif age < 3600:  # Assume 1 hour max TTL
                age_groups['valid'] += 1
            else:
                age_groups['expired'] += 1
        
        return {
            'total_files': len(cache_files),
            'total_size_mb': round(total_size, 2),
            'age_distribution': age_groups,
            'cache_directory': str(cache_path.absolute())
        }
    
    async def invalidate_cache(self, pattern: Optional[str] = None):
        """Invalidate cache entries"""
        cache_path = Path(self.cache_dir)
        
        if pattern:
            # Remove files matching pattern
            removed = 0
            for f in cache_path.glob(f"*{pattern}*.json"):
                f.unlink()
                removed += 1
            logger.info(f"Removed {removed} cache files matching '{pattern}'")
        else:
            # Remove all cache files
            removed = 0
            for f in cache_path.glob("*.json"):
                f.unlink()
                removed += 1
            logger.info(f"Removed all {removed} cache files")
    
    # Monitoring
    
    async def get_rate_limit_metrics(self) -> Dict[str, Any]:
        """Get rate limiter metrics"""
        return self.client.get_metrics()
    
    @property
    def rate_limiter(self):
        """Access to the rate limiter client for metrics"""
        return self.client
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check with rate limit status"""
        try:
            # Try a lightweight request
            bootstrap = await self.get_bootstrap_static()
            metrics = await self.get_rate_limit_metrics()
            
            return {
                'healthy': True,
                'api_accessible': bootstrap is not None,
                'rate_limit_status': {
                    'available_tokens': metrics['available_tokens'],
                    'requests_per_minute': metrics['requests_per_minute'],
                    'consecutive_429s': metrics['consecutive_429s'],
                    'queue_size': metrics['current_queue_size']
                }
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }