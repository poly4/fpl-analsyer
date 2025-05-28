import asyncio
import logging
import time
import json
import hashlib
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import weakref
from collections import OrderedDict
import threading
import psutil
import gzip
import pickle

from app.services.redis_cache import RedisCache

logger = logging.getLogger(__name__)


class CacheLevel(str, Enum):
    """Cache level hierarchy"""
    MEMORY = "memory"
    REDIS = "redis"
    DATABASE = "database"
    CDN = "cdn"


class DataType(str, Enum):
    """Data types with different caching strategies"""
    LIVE_DATA = "live_data"
    FIXTURES = "fixtures"
    PLAYER_DATA = "player_data"
    HISTORICAL_DATA = "historical_data"
    BOOTSTRAP = "bootstrap"
    MANAGER_DATA = "manager_data"
    PREDICTIONS = "predictions"
    ANALYTICS = "analytics"


@dataclass
class CacheConfig:
    """Cache configuration for different data types"""
    memory_ttl: int  # seconds
    redis_ttl: int   # seconds
    max_memory_size: int  # MB
    compression: bool = False
    pre_warm: bool = False
    invalidation_events: List[str] = None


@dataclass
class CacheStats:
    """Cache performance statistics"""
    hits: int = 0
    misses: int = 0
    memory_usage: float = 0.0  # MB
    redis_usage: float = 0.0   # MB
    avg_response_time: float = 0.0  # ms
    hit_rate: float = 0.0


class LRUCache:
    """Thread-safe LRU cache with TTL support"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache = OrderedDict()
        self.lock = threading.RLock()
        self.stats = CacheStats()
        
    def _is_expired(self, entry: Dict) -> bool:
        """Check if cache entry is expired"""
        return time.time() > entry['expires_at']
        
    def _cleanup_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time > entry['expires_at']
        ]
        
        for key in expired_keys:
            del self.cache[key]
            
    def get(self, key: str) -> Any:
        """Get value from cache"""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                
                if self._is_expired(entry):
                    del self.cache[key]
                    self.stats.misses += 1
                    return None
                    
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.stats.hits += 1
                return entry['value']
            else:
                self.stats.misses += 1
                return None
                
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        with self.lock:
            ttl = ttl or self.default_ttl
            
            # Remove oldest items if at capacity
            while len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                
            self.cache[key] = {
                'value': value,
                'expires_at': time.time() + ttl,
                'size': self._estimate_size(value)
            }
            
            # Periodic cleanup
            if len(self.cache) % 100 == 0:
                self._cleanup_expired()
                
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        with self.lock:
            return self.cache.pop(key, None) is not None
            
    def clear(self) -> None:
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            
    def _estimate_size(self, value: Any) -> int:
        """Estimate size of cached value in bytes"""
        try:
            return len(pickle.dumps(value))
        except:
            return 1024  # Default estimate
            
    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        with self.lock:
            total_requests = self.stats.hits + self.stats.misses
            hit_rate = self.stats.hits / total_requests if total_requests > 0 else 0
            
            memory_usage = sum(
                entry.get('size', 0) for entry in self.cache.values()
            ) / (1024 * 1024)  # Convert to MB
            
            return CacheStats(
                hits=self.stats.hits,
                misses=self.stats.misses,
                memory_usage=memory_usage,
                hit_rate=hit_rate
            )


class CacheManager:
    """Multi-layer cache manager with intelligent invalidation"""
    
    def __init__(self, redis_cache: RedisCache):
        self.redis_cache = redis_cache
        
        # Cache configurations for different data types
        self.cache_configs = {
            DataType.LIVE_DATA: CacheConfig(
                memory_ttl=30,
                redis_ttl=60,
                max_memory_size=50,
                compression=True,
                pre_warm=True,
                invalidation_events=['match_start', 'goal', 'substitution']
            ),
            DataType.FIXTURES: CacheConfig(
                memory_ttl=3600,
                redis_ttl=86400,  # 24 hours
                max_memory_size=20,
                compression=False,
                pre_warm=True,
                invalidation_events=['deadline', 'fixture_update']
            ),
            DataType.PLAYER_DATA: CacheConfig(
                memory_ttl=7200,  # 2 hours
                redis_ttl=21600,  # 6 hours
                max_memory_size=100,
                compression=True,
                pre_warm=True,
                invalidation_events=['deadline', 'transfer_deadline']
            ),
            DataType.HISTORICAL_DATA: CacheConfig(
                memory_ttl=86400,  # 24 hours
                redis_ttl=604800,  # 1 week
                max_memory_size=200,
                compression=True,
                pre_warm=False,
                invalidation_events=[]
            ),
            DataType.BOOTSTRAP: CacheConfig(
                memory_ttl=3600,
                redis_ttl=7200,
                max_memory_size=30,
                compression=False,
                pre_warm=True,
                invalidation_events=['season_start', 'deadline']
            ),
            DataType.MANAGER_DATA: CacheConfig(
                memory_ttl=300,  # 5 minutes
                redis_ttl=1800,  # 30 minutes
                max_memory_size=50,
                compression=True,
                pre_warm=False,
                invalidation_events=['transfer', 'captain_change']
            ),
            DataType.PREDICTIONS: CacheConfig(
                memory_ttl=1800,  # 30 minutes
                redis_ttl=3600,   # 1 hour
                max_memory_size=100,
                compression=True,
                pre_warm=False,
                invalidation_events=['lineup_change', 'injury_update']
            ),
            DataType.ANALYTICS: CacheConfig(
                memory_ttl=3600,
                redis_ttl=86400,
                max_memory_size=150,
                compression=True,
                pre_warm=False,
                invalidation_events=['new_gameweek']
            )
        }
        
        # Initialize memory caches for each data type
        self.memory_caches = {}
        for data_type, config in self.cache_configs.items():
            self.memory_caches[data_type] = LRUCache(
                max_size=config.max_memory_size * 10,  # Approximate entries
                default_ttl=config.memory_ttl
            )
            
        # Cache warming tasks
        self.warming_tasks = set()
        
        # Performance monitoring
        self.request_times = []
        self.max_request_history = 1000
        
    async def get(
        self, 
        key: str, 
        data_type: DataType,
        fetch_func: Optional[Callable] = None,
        **fetch_kwargs
    ) -> Any:
        """Get data with multi-layer cache fallback"""
        start_time = time.time()
        
        try:
            # Layer 1: Memory cache
            memory_cache = self.memory_caches[data_type]
            value = memory_cache.get(key)
            
            if value is not None:
                self._record_request_time(time.time() - start_time, 'memory')
                return value
                
            # Layer 2: Redis cache
            config = self.cache_configs[data_type]
            redis_key = f"{data_type.value}:{key}"
            
            value = await self.redis_cache.get(redis_key)
            
            if value is not None:
                # Decompress if needed
                if config.compression and isinstance(value, bytes):
                    value = self._decompress(value)
                    
                # Warm memory cache
                memory_cache.set(key, value, config.memory_ttl)
                
                self._record_request_time(time.time() - start_time, 'redis')
                return value
                
            # Layer 3: Fetch from source
            if fetch_func:
                value = await fetch_func(**fetch_kwargs)
                
                if value is not None:
                    # Store in all cache layers
                    await self.set(key, value, data_type)
                    
                self._record_request_time(time.time() - start_time, 'source')
                return value
                
            return None
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            # Fallback to fetch function if available
            if fetch_func:
                try:
                    return await fetch_func(**fetch_kwargs)
                except Exception as fetch_error:
                    logger.error(f"Fetch function error: {fetch_error}")
            return None
            
    async def set(self, key: str, value: Any, data_type: DataType) -> None:
        """Set data in appropriate cache layers"""
        try:
            config = self.cache_configs[data_type]
            
            # Store in memory cache
            memory_cache = self.memory_caches[data_type]
            memory_cache.set(key, value, config.memory_ttl)
            
            # Store in Redis cache
            redis_key = f"{data_type.value}:{key}"
            
            # Compress if configured
            redis_value = value
            if config.compression:
                redis_value = self._compress(value)
                
            await self.redis_cache.set(redis_key, redis_value, config.redis_ttl)
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            
    async def delete(self, key: str, data_type: DataType) -> None:
        """Delete from all cache layers"""
        try:
            # Delete from memory cache
            memory_cache = self.memory_caches[data_type]
            memory_cache.delete(key)
            
            # Delete from Redis cache
            redis_key = f"{data_type.value}:{key}"
            await self.redis_cache.delete(redis_key)
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            
    async def invalidate_pattern(self, pattern: str, data_type: DataType) -> int:
        """Invalidate all keys matching pattern"""
        try:
            # Clear memory cache (simplified - clear all for this data type)
            memory_cache = self.memory_caches[data_type]
            memory_cache.clear()
            
            # Clear Redis cache with pattern
            redis_pattern = f"{data_type.value}:{pattern}"
            return await self.redis_cache.clear_pattern(redis_pattern)
            
        except Exception as e:
            logger.error(f"Cache invalidate pattern error: {e}")
            return 0
            
    async def invalidate_by_event(self, event: str) -> int:
        """Invalidate caches based on events"""
        total_invalidated = 0
        
        for data_type, config in self.cache_configs.items():
            if config.invalidation_events and event in config.invalidation_events:
                count = await self.invalidate_pattern("*", data_type)
                total_invalidated += count
                logger.info(f"Invalidated {count} entries for {data_type.value} due to event: {event}")
                
        return total_invalidated
        
    async def warm_cache(self, data_type: DataType, keys: List[str], fetch_func: Callable) -> None:
        """Pre-warm cache with frequently accessed data"""
        config = self.cache_configs[data_type]
        
        if not config.pre_warm:
            return
            
        logger.info(f"Warming cache for {data_type.value} with {len(keys)} keys")
        
        # Warm in batches to avoid overwhelming the system
        batch_size = 10
        for i in range(0, len(keys), batch_size):
            batch = keys[i:i + batch_size]
            
            # Create warming tasks
            tasks = [
                self._warm_single_key(key, data_type, fetch_func)
                for key in batch
            ]
            
            # Execute batch
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Small delay between batches
            await asyncio.sleep(0.1)
            
    async def _warm_single_key(self, key: str, data_type: DataType, fetch_func: Callable) -> None:
        """Warm a single cache key"""
        try:
            # Check if already cached
            if self.memory_caches[data_type].get(key) is not None:
                return
                
            # Fetch and cache
            value = await fetch_func(key)
            if value is not None:
                await self.set(key, value, data_type)
                
        except Exception as e:
            logger.warning(f"Cache warming failed for key {key}: {e}")
            
    def _compress(self, data: Any) -> bytes:
        """Compress data for storage"""
        try:
            serialized = pickle.dumps(data)
            return gzip.compress(serialized)
        except Exception as e:
            logger.warning(f"Compression failed: {e}")
            return pickle.dumps(data)
            
    def _decompress(self, data: bytes) -> Any:
        """Decompress data from storage"""
        try:
            decompressed = gzip.decompress(data)
            return pickle.loads(decompressed)
        except Exception as e:
            logger.warning(f"Decompression failed: {e}")
            return pickle.loads(data)
            
    def _record_request_time(self, duration: float, source: str) -> None:
        """Record request timing for monitoring"""
        self.request_times.append({
            'duration': duration * 1000,  # Convert to ms
            'source': source,
            'timestamp': time.time()
        })
        
        # Keep only recent requests
        if len(self.request_times) > self.max_request_history:
            self.request_times = self.request_times[-self.max_request_history:]
            
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache performance statistics"""
        stats = {
            'memory_caches': {},
            'redis_stats': {},
            'request_times': {
                'avg_memory': 0,
                'avg_redis': 0,
                'avg_source': 0,
                'total_requests': len(self.request_times)
            },
            'system_memory': psutil.virtual_memory().percent
        }
        
        # Memory cache stats
        for data_type, cache in self.memory_caches.items():
            stats['memory_caches'][data_type.value] = asdict(cache.get_stats())
            
        # Redis stats
        try:
            redis_info = await self.redis_cache.info()
            stats['redis_stats'] = {
                'used_memory': redis_info.get('used_memory_human', 'Unknown'),
                'connected_clients': redis_info.get('connected_clients', 0),
                'keyspace_hits': redis_info.get('keyspace_hits', 0),
                'keyspace_misses': redis_info.get('keyspace_misses', 0)
            }
        except Exception as e:
            logger.warning(f"Failed to get Redis stats: {e}")
            
        # Request timing stats
        if self.request_times:
            memory_times = [r['duration'] for r in self.request_times if r['source'] == 'memory']
            redis_times = [r['duration'] for r in self.request_times if r['source'] == 'redis']
            source_times = [r['duration'] for r in self.request_times if r['source'] == 'source']
            
            stats['request_times'].update({
                'avg_memory': sum(memory_times) / len(memory_times) if memory_times else 0,
                'avg_redis': sum(redis_times) / len(redis_times) if redis_times else 0,
                'avg_source': sum(source_times) / len(source_times) if source_times else 0
            })
            
        return stats
        
    async def optimize_memory_usage(self) -> None:
        """Optimize memory cache usage"""
        system_memory = psutil.virtual_memory()
        
        # If memory usage is high, reduce cache sizes
        if system_memory.percent > 80:
            logger.warning(f"High memory usage ({system_memory.percent}%), optimizing caches")
            
            for cache in self.memory_caches.values():
                # Clear least recently used items
                with cache.lock:
                    items_to_remove = len(cache.cache) // 4  # Remove 25%
                    for _ in range(items_to_remove):
                        if cache.cache:
                            oldest_key = next(iter(cache.cache))
                            del cache.cache[oldest_key]
                            
    async def health_check(self) -> Dict[str, bool]:
        """Perform health check on all cache layers"""
        health = {
            'memory_cache': True,
            'redis_cache': False
        }
        
        try:
            # Test Redis connection
            test_key = "health_check"
            await self.redis_cache.set(test_key, "ok", ttl=60)
            result = await self.redis_cache.get(test_key)
            health['redis_cache'] = result == "ok"
            await self.redis_cache.delete(test_key)
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            
        return health


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


async def get_cache_manager() -> CacheManager:
    """Get or create cache manager instance"""
    global _cache_manager
    
    if _cache_manager is None:
        from app.services.redis_cache import get_redis_cache
        redis_cache = await get_redis_cache()
        _cache_manager = CacheManager(redis_cache)
        
    return _cache_manager


async def warm_common_caches():
    """Warm frequently accessed cache entries"""
    cache_manager = await get_cache_manager()
    
    # Define common cache warming strategies
    warming_strategies = {
        DataType.BOOTSTRAP: {
            'keys': ['bootstrap_static'],
            'fetch_func': lambda key: None  # Would fetch from FPL API
        },
        DataType.FIXTURES: {
            'keys': [f'fixtures_gw_{gw}' for gw in range(1, 39)],
            'fetch_func': lambda key: None  # Would fetch fixtures
        }
    }
    
    # Execute warming for each data type
    warming_tasks = []
    for data_type, strategy in warming_strategies.items():
        task = cache_manager.warm_cache(
            data_type, 
            strategy['keys'], 
            strategy['fetch_func']
        )
        warming_tasks.append(task)
        
    await asyncio.gather(*warming_tasks, return_exceptions=True)
    logger.info("Cache warming completed")