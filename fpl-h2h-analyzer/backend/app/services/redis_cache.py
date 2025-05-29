import json
import logging
import pickle
from typing import Any, Optional, Union
from datetime import timedelta
import asyncio
import redis.asyncio as aioredis
from redis.exceptions import RedisError, ConnectionError

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache service with connection pooling and circuit breaker"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", max_connections: int = 50):
        self.redis_url = redis_url
        self.max_connections = max_connections
        self._pool: Optional[aioredis.ConnectionPool] = None
        self._client: Optional[aioredis.Redis] = None
        self._circuit_breaker_open = False
        self._failure_count = 0
        self._failure_threshold = 5
        self._retry_after = 30  # seconds
        self._last_failure_time = None
        
    async def connect(self):
        """Initialize Redis connection pool"""
        try:
            self._pool = aioredis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                decode_responses=False,  # We'll handle encoding/decoding
                socket_keepalive=True
            )
            self._client = aioredis.Redis(connection_pool=self._pool)
            
            # Test connection
            await self._client.ping()
            logger.info("Redis connection established")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
            
    async def disconnect(self):
        """Close Redis connection pool"""
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()
        logger.info("Redis connection closed")
        
    def _is_circuit_open(self) -> bool:
        """Check if circuit breaker is open"""
        if not self._circuit_breaker_open:
            return False
            
        # Check if retry time has passed
        if self._last_failure_time:
            import time
            if time.time() - self._last_failure_time > self._retry_after:
                self._circuit_breaker_open = False
                self._failure_count = 0
                logger.info("Circuit breaker closed, retrying Redis operations")
                return False
                
        return True
        
    def _handle_failure(self):
        """Handle Redis operation failure"""
        self._failure_count += 1
        
        if self._failure_count >= self._failure_threshold:
            import time
            self._circuit_breaker_open = True
            self._last_failure_time = time.time()
            logger.error(f"Circuit breaker opened after {self._failure_count} failures")
            
    def _handle_success(self):
        """Handle successful Redis operation"""
        self._failure_count = 0
        self._circuit_breaker_open = False
        
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        if self._is_circuit_open():
            return default
            
        try:
            if not self._client:
                return default
                
            value = await self._client.get(key)
            if value is None:
                return default
                
            # Try to deserialize as JSON first, then pickle
            try:
                result = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                result = pickle.loads(value)
                
            self._handle_success()
            return result
            
        except (RedisError, ConnectionError) as e:
            logger.error(f"Redis get error for key {key}: {e}")
            self._handle_failure()
            return default
        except Exception as e:
            logger.error(f"Unexpected error getting key {key}: {e}")
            return default
            
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set value in cache with optional TTL"""
        if self._is_circuit_open():
            return False
            
        try:
            if not self._client:
                return False
                
            # Serialize value
            try:
                serialized = json.dumps(value)
            except (TypeError, ValueError):
                # Fall back to pickle for complex objects
                serialized = pickle.dumps(value)
                
            # Convert timedelta to seconds
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
                
            # Set with or without TTL
            if ttl:
                await self._client.setex(key, ttl, serialized)
            else:
                await self._client.set(key, serialized)
                
            self._handle_success()
            return True
            
        except (RedisError, ConnectionError) as e:
            logger.error(f"Redis set error for key {key}: {e}")
            self._handle_failure()
            return False
        except Exception as e:
            logger.error(f"Unexpected error setting key {key}: {e}")
            return False
            
    async def delete(self, *keys: str) -> int:
        """Delete one or more keys"""
        if self._is_circuit_open() or not keys:
            return 0
            
        try:
            if not self._client:
                return 0
                
            result = await self._client.delete(*keys)
            self._handle_success()
            return result
            
        except (RedisError, ConnectionError) as e:
            logger.error(f"Redis delete error for keys {keys}: {e}")
            self._handle_failure()
            return 0
        except Exception as e:
            logger.error(f"Unexpected error deleting keys {keys}: {e}")
            return 0
            
    async def exists(self, *keys: str) -> int:
        """Check if keys exist"""
        if self._is_circuit_open() or not keys:
            return 0
            
        try:
            if not self._client:
                return 0
                
            result = await self._client.exists(*keys)
            self._handle_success()
            return result
            
        except (RedisError, ConnectionError) as e:
            logger.error(f"Redis exists error for keys {keys}: {e}")
            self._handle_failure()
            return 0
        except Exception as e:
            logger.error(f"Unexpected error checking keys {keys}: {e}")
            return 0
            
    async def expire(self, key: str, ttl: Union[int, timedelta]) -> bool:
        """Set expiration on a key"""
        if self._is_circuit_open():
            return False
            
        try:
            if not self._client:
                return False
                
            # Convert timedelta to seconds
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
                
            result = await self._client.expire(key, ttl)
            self._handle_success()
            return bool(result)
            
        except (RedisError, ConnectionError) as e:
            logger.error(f"Redis expire error for key {key}: {e}")
            self._handle_failure()
            return False
        except Exception as e:
            logger.error(f"Unexpected error expiring key {key}: {e}")
            return False
            
    async def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter"""
        if self._is_circuit_open():
            return None
            
        try:
            if not self._client:
                return None
                
            result = await self._client.incrby(key, amount)
            self._handle_success()
            return result
            
        except (RedisError, ConnectionError) as e:
            logger.error(f"Redis incr error for key {key}: {e}")
            self._handle_failure()
            return None
        except Exception as e:
            logger.error(f"Unexpected error incrementing key {key}: {e}")
            return None
            
    async def decr(self, key: str, amount: int = 1) -> Optional[int]:
        """Decrement a counter"""
        if self._is_circuit_open():
            return None
            
        try:
            if not self._client:
                return None
                
            result = await self._client.decrby(key, amount)
            self._handle_success()
            return result
            
        except (RedisError, ConnectionError) as e:
            logger.error(f"Redis decr error for key {key}: {e}")
            self._handle_failure()
            return None
        except Exception as e:
            logger.error(f"Unexpected error decrementing key {key}: {e}")
            return None
            
    async def lpush(self, key: str, *values: Any) -> Optional[int]:
        """Push values to the left of a list"""
        if self._is_circuit_open() or not values:
            return None
            
        try:
            if not self._client:
                return None
                
            # Serialize values
            serialized_values = []
            for value in values:
                try:
                    serialized = json.dumps(value)
                except (TypeError, ValueError):
                    serialized = pickle.dumps(value)
                serialized_values.append(serialized)
                
            result = await self._client.lpush(key, *serialized_values)
            self._handle_success()
            return result
            
        except (RedisError, ConnectionError) as e:
            logger.error(f"Redis lpush error for key {key}: {e}")
            self._handle_failure()
            return None
        except Exception as e:
            logger.error(f"Unexpected error pushing to list {key}: {e}")
            return None
            
    async def lrange(self, key: str, start: int, stop: int) -> list:
        """Get a range of values from a list"""
        if self._is_circuit_open():
            return []
            
        try:
            if not self._client:
                return []
                
            values = await self._client.lrange(key, start, stop)
            
            # Deserialize values
            result = []
            for value in values:
                try:
                    deserialized = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    deserialized = pickle.loads(value)
                result.append(deserialized)
                
            self._handle_success()
            return result
            
        except (RedisError, ConnectionError) as e:
            logger.error(f"Redis lrange error for key {key}: {e}")
            self._handle_failure()
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting list range {key}: {e}")
            return []
            
    async def ltrim(self, key: str, start: int, stop: int) -> bool:
        """Trim a list to the specified range"""
        if self._is_circuit_open():
            return False
            
        try:
            if not self._client:
                return False
                
            await self._client.ltrim(key, start, stop)
            self._handle_success()
            return True
            
        except (RedisError, ConnectionError) as e:
            logger.error(f"Redis ltrim error for key {key}: {e}")
            self._handle_failure()
            return False
        except Exception as e:
            logger.error(f"Unexpected error trimming list {key}: {e}")
            return False
            
    async def hset(self, key: str, field: str, value: Any) -> int:
        """Set a field in a hash"""
        if self._is_circuit_open():
            return 0
            
        try:
            if not self._client:
                return 0
                
            # Serialize value
            try:
                serialized = json.dumps(value)
            except (TypeError, ValueError):
                serialized = pickle.dumps(value)
                
            result = await self._client.hset(key, field, serialized)
            self._handle_success()
            return result
            
        except (RedisError, ConnectionError) as e:
            logger.error(f"Redis hset error for key {key}, field {field}: {e}")
            self._handle_failure()
            return 0
        except Exception as e:
            logger.error(f"Unexpected error setting hash field {key}.{field}: {e}")
            return 0
            
    async def hget(self, key: str, field: str, default: Any = None) -> Any:
        """Get a field from a hash"""
        if self._is_circuit_open():
            return default
            
        try:
            if not self._client:
                return default
                
            value = await self._client.hget(key, field)
            if value is None:
                return default
                
            # Deserialize value
            try:
                result = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                result = pickle.loads(value)
                
            self._handle_success()
            return result
            
        except (RedisError, ConnectionError) as e:
            logger.error(f"Redis hget error for key {key}, field {field}: {e}")
            self._handle_failure()
            return default
        except Exception as e:
            logger.error(f"Unexpected error getting hash field {key}.{field}: {e}")
            return default
            
    async def hgetall(self, key: str) -> dict:
        """Get all fields from a hash"""
        if self._is_circuit_open():
            return {}
            
        try:
            if not self._client:
                return {}
                
            data = await self._client.hgetall(key)
            
            # Deserialize values
            result = {}
            for field, value in data.items():
                try:
                    # Redis returns bytes, decode field name
                    field_str = field.decode() if isinstance(field, bytes) else field
                    
                    # Deserialize value
                    try:
                        deserialized = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        deserialized = pickle.loads(value)
                        
                    result[field_str] = deserialized
                except Exception as e:
                    logger.warning(f"Error deserializing hash field {field}: {e}")
                    
            self._handle_success()
            return result
            
        except (RedisError, ConnectionError) as e:
            logger.error(f"Redis hgetall error for key {key}: {e}")
            self._handle_failure()
            return {}
        except Exception as e:
            logger.error(f"Unexpected error getting hash {key}: {e}")
            return {}
            
    async def publish(self, channel: str, message: Any) -> int:
        """Publish a message to a channel"""
        if self._is_circuit_open():
            return 0
            
        try:
            if not self._client:
                return 0
                
            # Serialize message
            try:
                serialized = json.dumps(message)
            except (TypeError, ValueError):
                serialized = pickle.dumps(message)
                
            result = await self._client.publish(channel, serialized)
            self._handle_success()
            return result
            
        except (RedisError, ConnectionError) as e:
            logger.error(f"Redis publish error for channel {channel}: {e}")
            self._handle_failure()
            return 0
        except Exception as e:
            logger.error(f"Unexpected error publishing to channel {channel}: {e}")
            return 0
            
    async def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern"""
        if self._is_circuit_open():
            return 0
            
        try:
            if not self._client:
                return 0
                
            # Get all keys matching pattern
            keys = []
            async for key in self._client.scan_iter(match=pattern, count=100):
                keys.append(key)
                
            if not keys:
                return 0
                
            # Delete in batches
            deleted = 0
            batch_size = 100
            for i in range(0, len(keys), batch_size):
                batch = keys[i:i+batch_size]
                deleted += await self._client.delete(*batch)
                
            self._handle_success()
            return deleted
            
        except (RedisError, ConnectionError) as e:
            logger.error(f"Redis clear_pattern error for pattern {pattern}: {e}")
            self._handle_failure()
            return 0
        except Exception as e:
            logger.error(f"Unexpected error clearing pattern {pattern}: {e}")
            return 0
            
    async def get_keys(self, pattern: str = "*") -> list:
        """Get all keys matching a pattern"""
        if self._is_circuit_open():
            return []
            
        try:
            if not self._client:
                return []
                
            keys = []
            async for key in self._client.scan_iter(match=pattern, count=100):
                # Decode bytes to string
                key_str = key.decode() if isinstance(key, bytes) else key
                keys.append(key_str)
                
            self._handle_success()
            return keys
            
        except (RedisError, ConnectionError) as e:
            logger.error(f"Redis get_keys error for pattern {pattern}: {e}")
            self._handle_failure()
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting keys {pattern}: {e}")
            return []
            
    async def info(self) -> dict:
        """Get Redis server info"""
        if self._is_circuit_open():
            return {}
            
        try:
            if not self._client:
                return {}
                
            info_data = await self._client.info()
            self._handle_success()
            return info_data
            
        except (RedisError, ConnectionError) as e:
            logger.error(f"Redis info error: {e}")
            self._handle_failure()
            return {}
        except Exception as e:
            logger.error(f"Unexpected error getting Redis info: {e}")
            return {}


# Global cache instance
_redis_cache: Optional[RedisCache] = None


async def get_redis_cache() -> RedisCache:
    """Get or create Redis cache instance"""
    global _redis_cache
    
    if _redis_cache is None:
        import os
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        _redis_cache = RedisCache(redis_url)
        await _redis_cache.connect()
        
    return _redis_cache