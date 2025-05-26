"""
Comprehensive tests for the CacheService implementation.
"""

import asyncio
import json
import pytest
import redis.asyncio as redis
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.cache import CacheService, CacheKeyBuilder


@pytest.fixture
async def mock_redis():
    """Create a mock Redis client."""
    mock_client = AsyncMock(spec=redis.Redis)
    return mock_client


@pytest.fixture
async def cache_service(mock_redis):
    """Create a CacheService instance with mock Redis."""
    return CacheService(mock_redis, key_prefix="test")


@pytest.fixture
async def real_redis():
    """Create a real Redis client for integration tests."""
    try:
        client = redis.from_url("redis://localhost:6379", decode_responses=False)
        await client.ping()
        yield client
        await client.close()
    except Exception:
        pytest.skip("Redis not available for integration tests")


class TestCacheService:
    """Test suite for CacheService functionality."""

    async def test_init(self, mock_redis):
        """Test CacheService initialization."""
        cache = CacheService(mock_redis, key_prefix="custom")
        assert cache.redis == mock_redis
        assert cache.key_prefix == "custom"
        assert cache._connection_healthy is True

    def test_make_key(self, cache_service):
        """Test cache key generation."""
        key = cache_service._make_key("test_key")
        assert key == "test:test_key"

    def test_serialize_value(self, cache_service):
        """Test value serialization."""
        # String value
        assert cache_service._serialize_value("test") == "test"
        
        # Dict value
        data = {"key": "value", "number": 42}
        serialized = cache_service._serialize_value(data)
        assert json.loads(serialized) == data
        
        # List value
        data = [1, 2, 3]
        serialized = cache_service._serialize_value(data)
        assert json.loads(serialized) == data

    def test_deserialize_value(self, cache_service):
        """Test value deserialization."""
        # None value
        assert cache_service._deserialize_value(None) is None
        
        # String value
        assert cache_service._deserialize_value(b"test") == "test"
        
        # JSON value
        data = {"key": "value"}
        json_bytes = json.dumps(data).encode('utf-8')
        assert cache_service._deserialize_value(json_bytes) == data
        
        # Invalid JSON fallback to string
        assert cache_service._deserialize_value(b"invalid json") == "invalid json"

    async def test_get_success(self, cache_service, mock_redis):
        """Test successful cache get operation."""
        mock_redis.get.return_value = b'{"test": "data"}'
        
        result = await cache_service.get("test_key")
        
        assert result == {"test": "data"}
        mock_redis.get.assert_called_once_with("test:test_key")

    async def test_get_miss(self, cache_service, mock_redis):
        """Test cache miss (key not found)."""
        mock_redis.get.return_value = None
        
        result = await cache_service.get("missing_key")
        
        assert result is None
        mock_redis.get.assert_called_once_with("test:missing_key")

    async def test_get_error(self, cache_service, mock_redis):
        """Test cache get with Redis error."""
        mock_redis.get.side_effect = Exception("Redis connection error")
        mock_redis.ping = AsyncMock(side_effect=Exception("Connection failed"))
        
        result = await cache_service.get("test_key")
        
        assert result is None
        assert cache_service._connection_healthy is False

    async def test_set_success(self, cache_service, mock_redis):
        """Test successful cache set operation."""
        mock_redis.set.return_value = True
        
        result = await cache_service.set("test_key", {"data": "value"}, ttl=300)
        
        assert result is True
        mock_redis.set.assert_called_once_with(
            "test:test_key", 
            '{"data": "value"}', 
            ex=300
        )

    async def test_set_default_ttl(self, cache_service, mock_redis):
        """Test cache set with default TTL."""
        mock_redis.set.return_value = True
        
        result = await cache_service.set("test_key", "value")
        
        assert result is True
        mock_redis.set.assert_called_once_with(
            "test:test_key", 
            "value", 
            ex=CacheService.DEFAULT_TTL
        )

    async def test_set_error(self, cache_service, mock_redis):
        """Test cache set with Redis error."""
        mock_redis.set.side_effect = Exception("Redis error")
        mock_redis.ping = AsyncMock(side_effect=Exception("Connection failed"))
        
        result = await cache_service.set("test_key", "value")
        
        assert result is False
        assert cache_service._connection_healthy is False

    async def test_delete_success(self, cache_service, mock_redis):
        """Test successful cache delete operation."""
        mock_redis.delete.return_value = 1
        
        result = await cache_service.delete("test_key")
        
        assert result is True
        mock_redis.delete.assert_called_once_with("test:test_key")

    async def test_delete_not_found(self, cache_service, mock_redis):
        """Test cache delete when key doesn't exist."""
        mock_redis.delete.return_value = 0
        
        result = await cache_service.delete("missing_key")
        
        assert result is False
        mock_redis.delete.assert_called_once_with("test:missing_key")

    async def test_exists_true(self, cache_service, mock_redis):
        """Test exists check for existing key."""
        mock_redis.exists.return_value = 1
        
        result = await cache_service.exists("test_key")
        
        assert result is True
        mock_redis.exists.assert_called_once_with("test:test_key")

    async def test_exists_false(self, cache_service, mock_redis):
        """Test exists check for non-existing key."""
        mock_redis.exists.return_value = 0
        
        result = await cache_service.exists("missing_key")
        
        assert result is False
        mock_redis.exists.assert_called_once_with("test:missing_key")

    async def test_clear_with_pattern(self, cache_service, mock_redis):
        """Test cache clear with specific pattern."""
        mock_redis.keys.return_value = ["test:key1", "test:key2"]
        mock_redis.delete.return_value = 2
        
        result = await cache_service.clear("key*")
        
        assert result == 2
        mock_redis.keys.assert_called_once_with("test:key*")
        mock_redis.delete.assert_called_once_with("test:key1", "test:key2")

    async def test_clear_all(self, cache_service, mock_redis):
        """Test cache clear all keys."""
        mock_redis.keys.return_value = ["test:key1", "test:key2", "test:key3"]
        mock_redis.delete.return_value = 3
        
        result = await cache_service.clear()
        
        assert result == 3
        mock_redis.keys.assert_called_once_with("test:*")
        mock_redis.delete.assert_called_once_with("test:key1", "test:key2", "test:key3")

    async def test_get_ttl_exists(self, cache_service, mock_redis):
        """Test TTL retrieval for existing key."""
        mock_redis.ttl.return_value = 300
        
        result = await cache_service.get_ttl("test_key")
        
        assert result == 300
        mock_redis.ttl.assert_called_once_with("test:test_key")

    async def test_get_ttl_no_expiry(self, cache_service, mock_redis):
        """Test TTL retrieval for key without expiry."""
        mock_redis.ttl.return_value = -1
        
        result = await cache_service.get_ttl("test_key")
        
        assert result is None

    async def test_get_ttl_not_exists(self, cache_service, mock_redis):
        """Test TTL retrieval for non-existing key."""
        mock_redis.ttl.return_value = -2
        
        result = await cache_service.get_ttl("missing_key")
        
        assert result is None

    async def test_expire_success(self, cache_service, mock_redis):
        """Test setting expiry for existing key."""
        mock_redis.expire.return_value = True
        
        result = await cache_service.expire("test_key", 600)
        
        assert result is True
        mock_redis.expire.assert_called_once_with("test:test_key", 600)

    async def test_expire_not_exists(self, cache_service, mock_redis):
        """Test setting expiry for non-existing key."""
        mock_redis.expire.return_value = False
        
        result = await cache_service.expire("missing_key", 600)
        
        assert result is False

    async def test_mget_success(self, cache_service, mock_redis):
        """Test multiple get operation."""
        mock_redis.mget.return_value = [b'"value1"', None, b'"value3"']
        
        result = await cache_service.mget(["key1", "key2", "key3"])
        
        assert result == ["value1", None, "value3"]
        mock_redis.mget.assert_called_once_with(["test:key1", "test:key2", "test:key3"])

    async def test_mset_success(self, cache_service, mock_redis):
        """Test multiple set operation."""
        mock_redis.mset.return_value = True
        mock_redis.expire = AsyncMock(return_value=True)
        
        mapping = {"key1": "value1", "key2": {"data": "value2"}}
        result = await cache_service.mset(mapping, ttl=300)
        
        assert result is True
        expected_mapping = {
            "test:key1": "value1",
            "test:key2": '{"data": "value2"}'
        }
        mock_redis.mset.assert_called_once_with(expected_mapping)
        
        # Check that expire was called for each key
        assert mock_redis.expire.call_count == 2

    async def test_get_stats_success(self, cache_service, mock_redis):
        """Test cache statistics retrieval."""
        mock_info = {
            "used_memory_human": "1.5M",
            "connected_clients": 10,
            "total_commands_processed": 1000,
            "keyspace_hits": 800,
            "keyspace_misses": 200
        }
        mock_redis.info.return_value = mock_info
        
        result = await cache_service.get_stats()
        
        assert result["used_memory"] == "1.5M"
        assert result["connected_clients"] == 10
        assert result["hit_rate"] == 80.0
        assert result["connection_healthy"] is True

    async def test_health_check_success(self, cache_service, mock_redis):
        """Test successful health check."""
        mock_redis.ping = AsyncMock()
        cache_service.set = AsyncMock(return_value=True)
        cache_service.get = AsyncMock(return_value={"timestamp": "test"})
        cache_service.delete = AsyncMock(return_value=True)
        
        result = await cache_service.health_check()
        
        assert result["healthy"] is True
        assert "timestamp" in result
        assert all(check["status"] == "pass" for check in result["checks"].values())

    async def test_health_check_failure(self, cache_service, mock_redis):
        """Test health check with Redis failure."""
        mock_redis.ping.side_effect = Exception("Connection failed")
        
        result = await cache_service.health_check()
        
        assert result["healthy"] is False
        assert "error" in result["checks"]["connection"]


class TestCacheKeyBuilder:
    """Test suite for CacheKeyBuilder utility."""

    def test_fpl_endpoint_basic(self):
        """Test FPL endpoint key building."""
        key = CacheKeyBuilder.fpl_endpoint("bootstrap-static/")
        assert key == "fpl_api:bootstrap-static_"

    def test_fpl_endpoint_with_params(self):
        """Test FPL endpoint key building with parameters."""
        params = {"event": 38, "page": 1}
        key = CacheKeyBuilder.fpl_endpoint("matches", params)
        assert key == "fpl_api:matches:event_38_page_1"

    def test_manager_data(self):
        """Test manager data key building."""
        key = CacheKeyBuilder.manager_data(12345, "history")
        assert key == "manager:12345:history"

    def test_league_data(self):
        """Test league data key building."""
        key = CacheKeyBuilder.league_data(620117, "standings")
        assert key == "league:620117:standings"

    def test_gameweek_data(self):
        """Test gameweek data key building."""
        key = CacheKeyBuilder.gameweek_data(38, "fixtures")
        assert key == "gameweek:38:fixtures"

    def test_live_data(self):
        """Test live data key building."""
        key = CacheKeyBuilder.live_data(38)
        assert key == "live:38"


class TestCacheServiceIntegration:
    """Integration tests with real Redis instance."""

    async def test_full_workflow(self, real_redis):
        """Test complete cache workflow with real Redis."""
        cache = CacheService(real_redis, key_prefix="integration_test")
        
        try:
            # Clear any existing test data
            await cache.clear()
            
            # Test basic operations
            test_data = {"test": "data", "number": 42}
            
            # Set data
            result = await cache.set("test_key", test_data, ttl=60)
            assert result is True
            
            # Get data
            retrieved = await cache.get("test_key")
            assert retrieved == test_data
            
            # Check existence
            exists = await cache.exists("test_key")
            assert exists is True
            
            # Check TTL
            ttl = await cache.get_ttl("test_key")
            assert ttl > 0 and ttl <= 60
            
            # Update TTL
            expire_result = await cache.expire("test_key", 120)
            assert expire_result is True
            
            # Verify new TTL
            new_ttl = await cache.get_ttl("test_key")
            assert new_ttl > 60
            
            # Test batch operations
            batch_data = {"key1": "value1", "key2": {"nested": "data"}}
            mset_result = await cache.mset(batch_data, ttl=30)
            assert mset_result is True
            
            # Get batch data
            batch_retrieved = await cache.mget(["key1", "key2", "nonexistent"])
            assert batch_retrieved[0] == "value1"
            assert batch_retrieved[1] == {"nested": "data"}
            assert batch_retrieved[2] is None
            
            # Health check
            health = await cache.health_check()
            assert health["healthy"] is True
            
            # Get stats
            stats = await cache.get_stats()
            assert stats["connection_healthy"] is True
            assert "hit_rate" in stats
            
            # Delete data
            delete_result = await cache.delete("test_key")
            assert delete_result is True
            
            # Verify deletion
            deleted_data = await cache.get("test_key")
            assert deleted_data is None
            
        finally:
            # Clean up
            await cache.clear()

    async def test_error_handling(self, real_redis):
        """Test error handling with real Redis."""
        cache = CacheService(real_redis, key_prefix="error_test")
        
        # Test operations on non-existent keys
        result = await cache.delete("nonexistent")
        assert result is False
        
        result = await cache.expire("nonexistent", 60)
        assert result is False
        
        exists = await cache.exists("nonexistent")
        assert exists is False
        
        ttl = await cache.get_ttl("nonexistent")
        assert ttl is None


# Performance benchmarks
class TestCachePerformance:
    """Performance tests for cache operations."""

    async def test_get_set_performance(self, real_redis):
        """Benchmark get/set operations."""
        cache = CacheService(real_redis, key_prefix="perf_test")
        
        try:
            # Warm up
            await cache.set("warmup", "data")
            await cache.get("warmup")
            
            # Benchmark SET operations
            import time
            start_time = time.time()
            
            for i in range(100):
                await cache.set(f"perf_key_{i}", {"data": f"value_{i}"}, ttl=60)
            
            set_time = time.time() - start_time
            
            # Benchmark GET operations
            start_time = time.time()
            
            for i in range(100):
                await cache.get(f"perf_key_{i}")
            
            get_time = time.time() - start_time
            
            # Performance assertions (adjust based on environment)
            assert set_time < 2.0, f"SET operations too slow: {set_time:.3f}s"
            assert get_time < 1.0, f"GET operations too slow: {get_time:.3f}s"
            
            print(f"SET performance: {100/set_time:.1f} ops/sec")
            print(f"GET performance: {100/get_time:.1f} ops/sec")
            
        finally:
            await cache.clear()

    async def test_batch_performance(self, real_redis):
        """Benchmark batch operations."""
        cache = CacheService(real_redis, key_prefix="batch_perf")
        
        try:
            # Prepare test data
            batch_data = {f"batch_key_{i}": f"value_{i}" for i in range(100)}
            batch_keys = list(batch_data.keys())
            
            # Benchmark MSET
            import time
            start_time = time.time()
            await cache.mset(batch_data, ttl=60)
            mset_time = time.time() - start_time
            
            # Benchmark MGET
            start_time = time.time()
            await cache.mget(batch_keys)
            mget_time = time.time() - start_time
            
            # Performance assertions
            assert mset_time < 1.0, f"MSET too slow: {mset_time:.3f}s"
            assert mget_time < 0.5, f"MGET too slow: {mget_time:.3f}s"
            
            print(f"MSET performance: {100/mset_time:.1f} ops/sec")
            print(f"MGET performance: {100/mget_time:.1f} ops/sec")
            
        finally:
            await cache.clear()


if __name__ == "__main__":
    # Run basic tests
    asyncio.run(pytest.main([__file__, "-v"]))