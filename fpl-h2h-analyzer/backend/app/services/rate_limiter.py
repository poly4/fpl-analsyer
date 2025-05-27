"""
Comprehensive Rate Limiting System for FPL API
Implements token bucket algorithm with exponential backoff
"""

import asyncio
import time
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from enum import Enum
import json

logger = logging.getLogger(__name__)


class RequestPriority(Enum):
    """Priority levels for API requests"""
    CRITICAL = 1  # Live data during matches (30s cache)
    HIGH = 2      # Bootstrap-static, fixtures (1 hour cache)
    MEDIUM = 3    # Manager history (30 min cache)
    LOW = 4       # Player details (2 hour cache)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiter"""
    tokens_per_minute: int = 90
    burst_capacity: int = 10
    refill_rate: float = 1.5  # tokens per second (90/60)
    max_retries: int = 5
    initial_backoff: float = 1.0
    max_backoff: float = 32.0
    backoff_multiplier: float = 2.0


@dataclass
class RequestMetrics:
    """Metrics for monitoring rate limit performance"""
    total_requests: int = 0
    successful_requests: int = 0
    rate_limited_requests: int = 0
    failed_requests: int = 0
    total_wait_time: float = 0.0
    queue_lengths: List[int] = field(default_factory=list)
    last_reset: datetime = field(default_factory=datetime.now)


class TokenBucket:
    """Token bucket implementation for rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> float:
        """
        Acquire tokens from the bucket.
        Returns wait time if tokens not immediately available.
        """
        async with self._lock:
            # Refill tokens based on time elapsed
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return 0.0
            else:
                # Calculate wait time
                deficit = tokens - self.tokens
                wait_time = deficit / self.refill_rate
                return wait_time
    
    @property
    def available_tokens(self) -> float:
        """Get current available tokens"""
        now = time.monotonic()
        elapsed = now - self.last_refill
        return min(self.capacity, self.tokens + elapsed * self.refill_rate)


class PriorityQueue:
    """Priority queue for requests"""
    
    def __init__(self):
        self.queues: Dict[RequestPriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in RequestPriority
        }
    
    async def put(self, item: Any, priority: RequestPriority):
        """Add item to queue with given priority"""
        await self.queues[priority].put(item)
    
    async def get(self) -> Any:
        """Get highest priority item from queue"""
        for priority in sorted(RequestPriority, key=lambda x: x.value):
            queue = self.queues[priority]
            if not queue.empty():
                return await queue.get()
        
        # If all queues empty, wait on highest priority queue
        return await self.queues[RequestPriority.CRITICAL].get()
    
    def total_size(self) -> int:
        """Get total items across all queues"""
        return sum(queue.qsize() for queue in self.queues.values())
    
    def get_sizes(self) -> Dict[str, int]:
        """Get size of each priority queue"""
        return {
            priority.name: queue.qsize() 
            for priority, queue in self.queues.items()
        }


class RateLimitedFPLClient:
    """
    Rate-limited FPL API client with token bucket algorithm,
    exponential backoff, and request prioritization.
    """
    
    def __init__(
        self, 
        base_client: Any,  # The underlying FPL client
        config: Optional[RateLimitConfig] = None,
        redis_client: Optional[Any] = None
    ):
        self.base_client = base_client
        self.config = config or RateLimitConfig()
        self.redis_client = redis_client
        
        # Initialize token bucket
        self.token_bucket = TokenBucket(
            capacity=self.config.tokens_per_minute + self.config.burst_capacity,
            refill_rate=self.config.refill_rate
        )
        
        # Initialize request queue
        self.request_queue = PriorityQueue()
        self.processing = False
        
        # Metrics
        self.metrics = RequestMetrics()
        
        # Request processor task
        self._processor_task = None
        
        # Backoff state
        self.consecutive_429s = 0
        self.last_429_time = None
    
    async def start(self):
        """Start the request processor"""
        if not self.processing:
            self.processing = True
            self._processor_task = asyncio.create_task(self._process_requests())
            logger.info("Rate limiter started")
    
    async def stop(self):
        """Stop the request processor"""
        self.processing = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        logger.info("Rate limiter stopped")
    
    async def request(
        self,
        method: str,
        endpoint: str,
        priority: RequestPriority = RequestPriority.MEDIUM,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make a rate-limited request to the FPL API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            priority: Request priority
            **kwargs: Additional arguments for the request
            
        Returns:
            API response data
        """
        # Create request future
        future = asyncio.Future()
        
        # Queue request
        await self.request_queue.put({
            'method': method,
            'endpoint': endpoint,
            'kwargs': kwargs,
            'future': future,
            'priority': priority,
            'retry_count': 0,
            'created_at': time.time()
        }, priority)
        
        # Update metrics
        self.metrics.total_requests += 1
        self.metrics.queue_lengths.append(self.request_queue.total_size())
        
        # Wait for result
        return await future
    
    async def _process_requests(self):
        """Process requests from the queue"""
        logger.info("Request processor started")
        
        while self.processing:
            try:
                # Get next request from queue
                request = await asyncio.wait_for(
                    self.request_queue.get(),
                    timeout=1.0
                )
                
                # Wait for token
                wait_time = await self.token_bucket.acquire()
                if wait_time > 0:
                    logger.debug(f"Waiting {wait_time:.2f}s for rate limit token")
                    await asyncio.sleep(wait_time)
                    self.metrics.total_wait_time += wait_time
                
                # Process request
                await self._execute_request(request)
                
            except asyncio.TimeoutError:
                # No requests in queue
                continue
            except Exception as e:
                logger.error(f"Error in request processor: {e}")
    
    async def _execute_request(self, request: Dict[str, Any]):
        """Execute a single request with retry logic"""
        method = request['method']
        endpoint = request['endpoint']
        kwargs = request['kwargs']
        future = request['future']
        retry_count = request['retry_count']
        
        try:
            # Make the actual request
            if hasattr(self.base_client, method):
                response = await getattr(self.base_client, method)(endpoint, **kwargs)
            else:
                # Fallback to generic request method
                response = await self.base_client.request(method, endpoint, **kwargs)
            
            # Success - reset backoff
            self.consecutive_429s = 0
            self.metrics.successful_requests += 1
            
            # Set result
            future.set_result(response)
            
        except Exception as e:
            # Check if it's a 429 error
            if self._is_rate_limit_error(e):
                await self._handle_rate_limit(request, e)
            else:
                # Other error - set exception
                self.metrics.failed_requests += 1
                future.set_exception(e)
    
    def _is_rate_limit_error(self, error: Exception) -> bool:
        """Check if error is a rate limit (429) error"""
        error_str = str(error).lower()
        return '429' in error_str or 'rate limit' in error_str
    
    async def _handle_rate_limit(self, request: Dict[str, Any], error: Exception):
        """Handle rate limit error with exponential backoff"""
        self.consecutive_429s += 1
        self.metrics.rate_limited_requests += 1
        self.last_429_time = time.time()
        
        retry_count = request['retry_count']
        
        if retry_count >= self.config.max_retries:
            # Max retries exceeded
            logger.error(f"Max retries exceeded for {request['endpoint']}")
            request['future'].set_exception(error)
            return
        
        # Calculate backoff time
        backoff = min(
            self.config.initial_backoff * (self.config.backoff_multiplier ** retry_count),
            self.config.max_backoff
        )
        
        logger.warning(
            f"Rate limited on {request['endpoint']}. "
            f"Retry {retry_count + 1}/{self.config.max_retries} after {backoff}s"
        )
        
        # Update request for retry
        request['retry_count'] += 1
        
        # Wait and requeue
        await asyncio.sleep(backoff)
        await self.request_queue.put(request, request['priority'])
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        uptime = (datetime.now() - self.metrics.last_reset).total_seconds()
        
        return {
            'total_requests': self.metrics.total_requests,
            'successful_requests': self.metrics.successful_requests,
            'rate_limited_requests': self.metrics.rate_limited_requests,
            'failed_requests': self.metrics.failed_requests,
            'success_rate': (
                self.metrics.successful_requests / self.metrics.total_requests 
                if self.metrics.total_requests > 0 else 0
            ),
            'average_wait_time': (
                self.metrics.total_wait_time / self.metrics.total_requests
                if self.metrics.total_requests > 0 else 0
            ),
            'current_queue_size': self.request_queue.total_size(),
            'queue_sizes_by_priority': self.request_queue.get_sizes(),
            'available_tokens': self.token_bucket.available_tokens,
            'token_capacity': self.token_bucket.capacity,
            'requests_per_minute': (
                self.metrics.total_requests / (uptime / 60)
                if uptime > 0 else 0
            ),
            'consecutive_429s': self.consecutive_429s,
            'uptime_seconds': uptime
        }
    
    async def warm_cache(self, priority_endpoints: List[tuple]):
        """
        Warm cache with priority endpoints.
        
        Args:
            priority_endpoints: List of (endpoint, priority) tuples
        """
        tasks = []
        for endpoint, priority in priority_endpoints:
            task = self.request('GET', endpoint, priority=priority)
            tasks.append(task)
        
        # Execute with controlled concurrency
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        logger.info(f"Cache warming completed: {success_count}/{len(tasks)} successful")
    
    async def save_metrics_to_redis(self):
        """Save metrics to Redis for monitoring"""
        if self.redis_client:
            metrics = self.get_metrics()
            await self.redis_client.setex(
                'rate_limiter:metrics',
                300,  # 5 minute TTL
                json.dumps(metrics)
            )


# Endpoint priority mappings
ENDPOINT_PRIORITIES = {
    '/event/*/live/': RequestPriority.CRITICAL,
    '/bootstrap-static/': RequestPriority.HIGH,
    '/fixtures/': RequestPriority.HIGH,
    '/entry/*/history/': RequestPriority.MEDIUM,
    '/entry/*/event/*/picks/': RequestPriority.MEDIUM,
    '/element-summary/*/': RequestPriority.LOW,
    '/dream-team/*/': RequestPriority.LOW,
}


def get_endpoint_priority(endpoint: str) -> RequestPriority:
    """Determine priority for an endpoint"""
    for pattern, priority in ENDPOINT_PRIORITIES.items():
        if pattern.replace('*', '') in endpoint:
            return priority
    return RequestPriority.MEDIUM