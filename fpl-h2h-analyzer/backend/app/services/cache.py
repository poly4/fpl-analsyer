"""
Redis-based caching service for FPL Nexus.

This module provides a comprehensive caching layer using Redis for improved
performance and scalability over file-based caching.
"""

import json
import logging
from typing import Any, Optional, Union, List
import redis.asyncio as redis
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CacheService:
    """
    Redis-based caching service with comprehensive error handling and connection management.
    
    Features:
    - Automatic JSON serialization/deserialization
    - Configurable TTL with intelligent defaults
    - Connection health monitoring
    - Graceful error handling with fallback options
    - Batch operations for performance
    """
    
    # Default TTL values in seconds
    DEFAULT_TTL = 300  # 5 minutes
    SHORT_TTL = 60     # 1 minute
    MEDIUM_TTL = 900   # 15 minutes
    LONG_TTL = 3600    # 1 hour
    VERY_LONG_TTL = 21600  # 6 hours
    DAILY_TTL = 86400  # 24 hours
    
    def __init__(self, redis_client: redis.Redis, key_prefix: str = "fpl_nexus"):
        """
        Initialize the cache service.
        
        Args:
            redis_client: Redis async client instance
            key_prefix: Prefix for all cache keys to avoid collisions
        """
        self.redis = redis_client
        self.key_prefix = key_prefix
        self._connection_healthy = True
        
    def _make_key(self, key: str) -> str:
        """Create a prefixed cache key."""
        return f"{self.key_prefix}:{key}"
        
    def _serialize_value(self, value: Any) -> str:
        """Serialize value to JSON string."""
        if isinstance(value, str):
            return value
        return json.dumps(value, default=str)
        
    def _deserialize_value(self, value: Optional[bytes]) -> Any:
        """Deserialize value from JSON string."""
        if value is None:
            return None
        try:
            value_str = value.decode('utf-8')
            # Try to parse as JSON, fallback to string if it fails
            try:
                return json.loads(value_str)
            except json.JSONDecodeError:
                return value_str
        except Exception as e:
            logger.warning(f"Failed to deserialize cache value: {e}")
            return None
            
    async def _check_connection(self) -> bool:
        """Check if Redis connection is healthy."""
        try:
            await self.redis.ping()
            self._connection_healthy = True
            return True
        except Exception as e:
            logger.error(f"Redis connection check failed: {e}")
            self._connection_healthy = False
            return False
            
    async def get(self, key: str) -> Any:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/error
        """
        try:
            cache_key = self._make_key(key)
            value = await self.redis.get(cache_key)
            result = self._deserialize_value(value)
            
            if result is not None:
                logger.debug(f"Cache HIT for key: {key}")
            else:
                logger.debug(f"Cache MISS for key: {key}")
                
            return result
        except Exception as e:
            logger.error(f"Cache GET error for key {key}: {e}")
            await self._check_connection()
            return None
            
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in cache with optional TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_key = self._make_key(key)
            serialized_value = self._serialize_value(value)
            
            if ttl is None:
                ttl = self.DEFAULT_TTL
                
            result = await self.redis.set(cache_key, serialized_value, ex=ttl)
            
            if result:
                logger.debug(f"Cache SET for key: {key} (TTL: {ttl}s)")
            else:
                logger.warning(f"Cache SET failed for key: {key}")
                
            return bool(result)
        except Exception as e:
            logger.error(f"Cache SET error for key {key}: {e}")
            await self._check_connection()
            return False
            
    async def delete(self, key: str) -> bool:
        """
        Delete a value from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if deleted, False if not found or error
        """
        try:
            cache_key = self._make_key(key)
            result = await self.redis.delete(cache_key)
            
            if result:
                logger.debug(f"Cache DELETE for key: {key}")
            else:
                logger.debug(f"Cache DELETE for key: {key} (not found)")
                
            return bool(result)
        except Exception as e:
            logger.error(f"Cache DELETE error for key {key}: {e}")
            await self._check_connection()
            return False
            
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.
        
        Args:
            key: Cache key to check
            
        Returns:
            True if exists, False otherwise
        """
        try:
            cache_key = self._make_key(key)
            result = await self.redis.exists(cache_key)
            return bool(result)
        except Exception as e:
            logger.error(f"Cache EXISTS error for key {key}: {e}")
            await self._check_connection()
            return False
            
    async def clear(self, pattern: Optional[str] = None) -> int:
        """
        Clear cache entries matching a pattern.
        
        Args:
            pattern: Key pattern to match (uses prefix if None)
            
        Returns:
            Number of keys deleted
        """
        try:
            if pattern is None:
                pattern = f"{self.key_prefix}:*"
            else:
                pattern = self._make_key(pattern)
                
            # Get all keys matching pattern
            keys = await self.redis.keys(pattern)
            
            if keys:
                result = await self.redis.delete(*keys)
                logger.info(f"Cache CLEAR: deleted {result} keys matching {pattern}")
                return result
            else:
                logger.debug(f"Cache CLEAR: no keys found matching {pattern}")
                return 0
                
        except Exception as e:
            logger.error(f"Cache CLEAR error for pattern {pattern}: {e}")
            await self._check_connection()
            return 0
            
    async def get_ttl(self, key: str) -> Optional[int]:
        """
        Get the TTL (time to live) for a key.
        
        Args:
            key: Cache key
            
        Returns:
            TTL in seconds, None if key doesn't exist or no TTL set
        """
        try:
            cache_key = self._make_key(key)
            ttl = await self.redis.ttl(cache_key)
            
            if ttl == -2:  # Key doesn't exist
                return None
            elif ttl == -1:  # Key exists but no TTL
                return None
            else:
                return ttl
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return None
            
    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set/update TTL for an existing key.
        
        Args:
            key: Cache key
            ttl: New TTL in seconds
            
        Returns:
            True if successful, False if key doesn't exist or error
        """
        try:
            cache_key = self._make_key(key)
            result = await self.redis.expire(cache_key, ttl)
            
            if result:
                logger.debug(f"Cache EXPIRE for key: {key} (TTL: {ttl}s)")
            else:
                logger.debug(f"Cache EXPIRE failed for key: {key} (key not found)")
                
            return bool(result)
        except Exception as e:
            logger.error(f"Cache EXPIRE error for key {key}: {e}")
            return False
            
    async def mget(self, keys: List[str]) -> List[Any]:
        """
        Get multiple values at once.
        
        Args:
            keys: List of cache keys
            
        Returns:
            List of values (None for missing keys)
        """
        try:
            cache_keys = [self._make_key(key) for key in keys]
            values = await self.redis.mget(cache_keys)
            
            results = []
            for i, value in enumerate(values):
                result = self._deserialize_value(value)
                results.append(result)
                
                if result is not None:
                    logger.debug(f"Cache MGET HIT for key: {keys[i]}")
                else:
                    logger.debug(f"Cache MGET MISS for key: {keys[i]}")
                    
            return results
        except Exception as e:
            logger.error(f"Cache MGET error for keys {keys}: {e}")
            return [None] * len(keys)
            
    async def mset(self, mapping: dict, ttl: Optional[int] = None) -> bool:
        """
        Set multiple key-value pairs at once.
        
        Args:
            mapping: Dictionary of key-value pairs
            ttl: TTL in seconds for all keys
            
        Returns:
            True if all operations successful
        """
        try:
            # Prepare the mapping with prefixed keys and serialized values
            cache_mapping = {}
            for key, value in mapping.items():
                cache_key = self._make_key(key)
                serialized_value = self._serialize_value(value)
                cache_mapping[cache_key] = serialized_value
                
            # Set all keys
            result = await self.redis.mset(cache_mapping)
            
            # Set TTL for all keys if specified
            if ttl is not None and result:
                for cache_key in cache_mapping.keys():
                    await self.redis.expire(cache_key, ttl)
                    
            if result:
                logger.debug(f"Cache MSET for {len(mapping)} keys (TTL: {ttl}s)")
            else:
                logger.warning(f"Cache MSET failed for {len(mapping)} keys")
                
            return bool(result)
        except Exception as e:
            logger.error(f"Cache MSET error: {e}")
            return False
            
    async def get_stats(self) -> dict:
        """
        Get cache statistics and health information.
        
        Returns:
            Dictionary with cache stats
        """
        try:
            info = await self.redis.info()
            return {
                "connection_healthy": self._connection_healthy,
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {
                "connection_healthy": False,
                "error": str(e)
            }
            
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage."""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)
        
    async def health_check(self) -> dict:
        """
        Perform a comprehensive health check.
        
        Returns:
            Health check results
        """
        health = {
            "healthy": False,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }
        
        try:
            # Test basic connectivity
            start_time = datetime.utcnow()
            await self.redis.ping()
            ping_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            health["checks"]["ping"] = {
                "status": "pass",
                "response_time_ms": round(ping_time, 2)
            }
            
            # Test read/write operations
            test_key = "health_check"
            test_value = {"timestamp": datetime.utcnow().isoformat()}
            
            # Test SET
            set_success = await self.set(test_key, test_value, ttl=60)
            health["checks"]["write"] = {
                "status": "pass" if set_success else "fail"
            }
            
            # Test GET
            retrieved_value = await self.get(test_key)
            read_success = retrieved_value is not None
            health["checks"]["read"] = {
                "status": "pass" if read_success else "fail"
            }
            
            # Test DELETE
            delete_success = await self.delete(test_key)
            health["checks"]["delete"] = {
                "status": "pass" if delete_success else "fail"
            }
            
            # Overall health
            all_checks_pass = all(
                check.get("status") == "pass" 
                for check in health["checks"].values()
            )
            health["healthy"] = all_checks_pass
            
        except Exception as e:
            health["checks"]["connection"] = {
                "status": "fail",
                "error": str(e)
            }
            logger.error(f"Cache health check failed: {e}")
            
        return health


class CacheKeyBuilder:
    """Helper class for building consistent cache keys."""
    
    @staticmethod
    def fpl_endpoint(endpoint: str, params: Optional[dict] = None) -> str:
        """Build cache key for FPL API endpoints."""
        key = f"fpl_api:{endpoint.replace('/', '_')}"
        if params:
            param_str = "_".join(f"{k}_{v}" for k, v in sorted(params.items()))
            key = f"{key}:{param_str}"
        return key
        
    @staticmethod
    def manager_data(manager_id: int, data_type: str) -> str:
        """Build cache key for manager-specific data."""
        return f"manager:{manager_id}:{data_type}"
        
    @staticmethod
    def league_data(league_id: int, data_type: str) -> str:
        """Build cache key for league-specific data."""
        return f"league:{league_id}:{data_type}"
        
    @staticmethod
    def gameweek_data(gameweek: int, data_type: str) -> str:
        """Build cache key for gameweek-specific data."""
        return f"gameweek:{gameweek}:{data_type}"
        
    @staticmethod
    def live_data(gameweek: int) -> str:
        """Build cache key for live gameweek data."""
        return f"live:{gameweek}"