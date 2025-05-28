import asyncio
import time
import gzip
import brotli
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.types import ASGIApp
import weakref
from collections import defaultdict, deque
import threading

logger = logging.getLogger(__name__)


class RequestBatcher:
    """Batches similar requests to reduce load"""
    
    def __init__(self, batch_window_ms: int = 50, max_batch_size: int = 10):
        self.batch_window_ms = batch_window_ms
        self.max_batch_size = max_batch_size
        self.pending_batches = defaultdict(list)
        self.batch_futures = defaultdict(list)
        self.lock = threading.Lock()
        
    async def batch_request(self, key: str, request_func: Callable, *args, **kwargs) -> Any:
        """Add request to batch or execute immediately if batch is full"""
        
        # Create a future for this request
        future = asyncio.Future()
        
        with self.lock:
            batch_key = f"{key}_{hash(str(args))}"
            self.pending_batches[batch_key].append((request_func, args, kwargs))
            self.batch_futures[batch_key].append(future)
            
            # If batch is full, execute immediately
            if len(self.pending_batches[batch_key]) >= self.max_batch_size:
                asyncio.create_task(self._execute_batch(batch_key))
            else:
                # Schedule batch execution
                asyncio.create_task(self._schedule_batch_execution(batch_key))
                
        return await future
        
    async def _schedule_batch_execution(self, batch_key: str):
        """Schedule batch execution after window period"""
        await asyncio.sleep(self.batch_window_ms / 1000)
        await self._execute_batch(batch_key)
        
    async def _execute_batch(self, batch_key: str):
        """Execute all requests in a batch"""
        with self.lock:
            requests = self.pending_batches.pop(batch_key, [])
            futures = self.batch_futures.pop(batch_key, [])
            
        if not requests:
            return
            
        try:
            # Execute all requests in parallel
            tasks = []
            for request_func, args, kwargs in requests:
                task = asyncio.create_task(request_func(*args, **kwargs))
                tasks.append(task)
                
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Set results to futures
            for future, result in zip(futures, results):
                if isinstance(result, Exception):
                    future.set_exception(result)
                else:
                    future.set_result(result)
                    
        except Exception as e:
            # Set exception to all futures
            for future in futures:
                if not future.done():
                    future.set_exception(e)


class ResponseCompressor:
    """Advanced response compression with content-aware algorithms"""
    
    def __init__(self):
        self.compression_thresholds = {
            'application/json': 512,  # Compress JSON responses > 512 bytes
            'text/html': 1024,       # Compress HTML > 1KB
            'text/plain': 1024,      # Compress text > 1KB
            'application/javascript': 1024,
            'text/css': 1024
        }
        
    def should_compress(self, content_type: str, content_length: int) -> bool:
        """Determine if content should be compressed"""
        threshold = self.compression_thresholds.get(content_type, 2048)
        return content_length >= threshold
        
    def compress_content(self, content: bytes, accept_encoding: str) -> tuple[bytes, str]:
        """Compress content using best available algorithm"""
        
        # Prefer Brotli for better compression
        if 'br' in accept_encoding:
            try:
                compressed = brotli.compress(content, quality=4)
                return compressed, 'br'
            except Exception:
                pass
                
        # Fallback to gzip
        if 'gzip' in accept_encoding:
            try:
                compressed = gzip.compress(content, compresslevel=6)
                return compressed, 'gzip'
            except Exception:
                pass
                
        return content, 'identity'


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Comprehensive performance middleware"""
    
    def __init__(self, app: ASGIApp, enable_compression: bool = True, enable_batching: bool = True):
        super().__init__(app)
        self.enable_compression = enable_compression
        self.enable_batching = enable_batching
        
        # Components
        self.compressor = ResponseCompressor() if enable_compression else None
        self.batcher = RequestBatcher() if enable_batching else None
        
        # Performance tracking
        self.request_count = 0
        self.total_response_time = 0
        self.endpoint_stats = defaultdict(lambda: {'count': 0, 'total_time': 0})
        self.lock = threading.Lock()
        
        # Cache for compressed responses
        self.compression_cache = {}
        self.cache_max_size = 1000
        
    async def dispatch(self, request: Request, call_next) -> Response:
        """Main middleware dispatch"""
        start_time = time.time()
        
        try:
            # Extract endpoint for tracking
            endpoint = self._get_endpoint(request)
            
            # Process request
            response = await call_next(request)
            
            # Calculate response time
            response_time = (time.time() - start_time) * 1000  # ms
            
            # Track performance metrics
            self._track_performance(endpoint, response_time)
            
            # Optimize response
            if self.enable_compression:
                response = await self._optimize_response(request, response)
                
            # Add performance headers
            response.headers["X-Response-Time"] = f"{response_time:.2f}ms"
            response.headers["X-Request-ID"] = str(id(request))
            
            return response
            
        except Exception as e:
            logger.error(f"Error in performance middleware: {e}")
            # Return original response on error
            response_time = (time.time() - start_time) * 1000
            response = await call_next(request)
            response.headers["X-Response-Time"] = f"{response_time:.2f}ms"
            return response
            
    def _get_endpoint(self, request: Request) -> str:
        """Extract endpoint identifier from request"""
        method = request.method
        path = request.url.path
        
        # Normalize path by replacing IDs with placeholders
        normalized_path = path
        path_parts = path.split('/')
        
        for i, part in enumerate(path_parts):
            if part.isdigit():
                path_parts[i] = '{id}'
            elif len(part) == 36 and '-' in part:  # UUID
                path_parts[i] = '{uuid}'
                
        normalized_path = '/'.join(path_parts)
        return f"{method} {normalized_path}"
        
    def _track_performance(self, endpoint: str, response_time: float):
        """Track performance metrics"""
        with self.lock:
            self.request_count += 1
            self.total_response_time += response_time
            
            stats = self.endpoint_stats[endpoint]
            stats['count'] += 1
            stats['total_time'] += response_time
            
    async def _optimize_response(self, request: Request, response: Response) -> Response:
        """Optimize response with compression and caching"""
        
        # Skip compression for certain response types
        if (
            hasattr(response, 'status_code') and response.status_code != 200 or
            not hasattr(response, 'body') or
            response.headers.get('content-encoding')
        ):
            return response
            
        try:
            # Get response content
            if hasattr(response, 'body'):
                content = response.body
            else:
                content = b''
                
            if not content:
                return response
                
            content_type = response.headers.get('content-type', '').split(';')[0]
            content_length = len(content)
            
            # Check if compression is beneficial
            if not self.compressor.should_compress(content_type, content_length):
                return response
                
            # Get client's accepted encodings
            accept_encoding = request.headers.get('accept-encoding', '')
            
            # Check compression cache
            cache_key = f"{hash(content)}_{accept_encoding}"
            if cache_key in self.compression_cache:
                compressed_content, encoding = self.compression_cache[cache_key]
            else:
                # Compress content
                compressed_content, encoding = self.compressor.compress_content(
                    content, accept_encoding
                )
                
                # Cache compressed result
                if len(self.compression_cache) < self.cache_max_size:
                    self.compression_cache[cache_key] = (compressed_content, encoding)
                    
            # Update response
            if encoding != 'identity':
                response.headers['content-encoding'] = encoding
                response.headers['content-length'] = str(len(compressed_content))
                response.headers['vary'] = 'Accept-Encoding'
                
                # Create new response with compressed content
                if isinstance(response, JSONResponse):
                    # For JSON responses, we need to handle differently
                    new_response = Response(
                        content=compressed_content,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        media_type=response.media_type
                    )
                else:
                    new_response = Response(
                        content=compressed_content,
                        status_code=response.status_code,
                        headers=dict(response.headers)
                    )
                    
                return new_response
                
        except Exception as e:
            logger.warning(f"Failed to compress response: {e}")
            
        return response
        
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        with self.lock:
            if self.request_count == 0:
                return {
                    "total_requests": 0,
                    "avg_response_time": 0,
                    "endpoints": {}
                }
                
            endpoint_stats = {}
            for endpoint, stats in self.endpoint_stats.items():
                endpoint_stats[endpoint] = {
                    "count": stats['count'],
                    "avg_response_time": stats['total_time'] / stats['count'],
                    "total_time": stats['total_time']
                }
                
            return {
                "total_requests": self.request_count,
                "avg_response_time": self.total_response_time / self.request_count,
                "endpoints": endpoint_stats,
                "compression_cache_size": len(self.compression_cache)
            }


class CacheControlMiddleware(BaseHTTPMiddleware):
    """Intelligent cache control headers"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
        # Cache policies by endpoint pattern
        self.cache_policies = {
            'GET /api/bootstrap': {'max_age': 3600, 'public': True},      # 1 hour
            'GET /api/fixtures': {'max_age': 1800, 'public': True},       # 30 minutes
            'GET /api/player/{id}': {'max_age': 7200, 'public': True},    # 2 hours
            'GET /api/live/gw/{id}': {'max_age': 30, 'public': True},     # 30 seconds
            'GET /api/analytics': {'max_age': 900, 'public': True},       # 15 minutes
            'POST /api': {'no_cache': True},                              # No cache for POST
            'PUT /api': {'no_cache': True},                               # No cache for PUT
            'DELETE /api': {'no_cache': True},                            # No cache for DELETE
        }
        
    async def dispatch(self, request: Request, call_next) -> Response:
        """Add intelligent cache headers"""
        response = await call_next(request)
        
        # Don't add cache headers if already present
        if 'cache-control' in response.headers:
            return response
            
        endpoint = self._normalize_endpoint(request)
        policy = self._get_cache_policy(endpoint)
        
        if policy:
            cache_header = self._build_cache_header(policy)
            if cache_header:
                response.headers['cache-control'] = cache_header
                
                # Add ETag for GET requests
                if request.method == 'GET' and hasattr(response, 'body'):
                    etag = f'W/"{hash(response.body)}"'
                    response.headers['etag'] = etag
                    
        return response
        
    def _normalize_endpoint(self, request: Request) -> str:
        """Normalize endpoint for policy matching"""
        method = request.method
        path = request.url.path
        
        # Replace dynamic segments
        path_parts = path.split('/')
        for i, part in enumerate(path_parts):
            if part.isdigit():
                path_parts[i] = '{id}'
            elif len(part) == 36 and '-' in part:  # UUID
                path_parts[i] = '{id}'
                
        normalized_path = '/'.join(path_parts)
        return f"{method} {normalized_path}"
        
    def _get_cache_policy(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Get cache policy for endpoint"""
        # Try exact match first
        if endpoint in self.cache_policies:
            return self.cache_policies[endpoint]
            
        # Try pattern matching
        for pattern, policy in self.cache_policies.items():
            if self._matches_pattern(endpoint, pattern):
                return policy
                
        return None
        
    def _matches_pattern(self, endpoint: str, pattern: str) -> bool:
        """Check if endpoint matches pattern"""
        endpoint_parts = endpoint.split()
        pattern_parts = pattern.split()
        
        if len(endpoint_parts) != len(pattern_parts):
            return False
            
        method_match = endpoint_parts[0] == pattern_parts[0]
        path_match = self._path_matches(endpoint_parts[1], pattern_parts[1])
        
        return method_match and path_match
        
    def _path_matches(self, path: str, pattern: str) -> bool:
        """Check if path matches pattern with wildcards"""
        path_segments = path.split('/')
        pattern_segments = pattern.split('/')
        
        if len(path_segments) != len(pattern_segments):
            return False
            
        for path_seg, pattern_seg in zip(path_segments, pattern_segments):
            if pattern_seg.startswith('{') and pattern_seg.endswith('}'):
                continue  # Wildcard matches anything
            if path_seg != pattern_seg:
                return False
                
        return True
        
    def _build_cache_header(self, policy: Dict[str, Any]) -> Optional[str]:
        """Build cache-control header from policy"""
        if policy.get('no_cache'):
            return 'no-cache, no-store, must-revalidate'
            
        parts = []
        
        if policy.get('public'):
            parts.append('public')
        else:
            parts.append('private')
            
        if 'max_age' in policy:
            parts.append(f"max-age={policy['max_age']}")
            
        if policy.get('must_revalidate'):
            parts.append('must-revalidate')
            
        return ', '.join(parts) if parts else None


class HTTP2ServerPushMiddleware(BaseHTTPMiddleware):
    """HTTP/2 Server Push for critical resources"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
        # Define push resources for different pages
        self.push_resources = {
            '/': [
                {'path': '/static/css/main.css', 'as': 'style'},
                {'path': '/static/js/main.js', 'as': 'script'},
                {'path': '/api/bootstrap', 'as': 'fetch'}
            ],
            '/dashboard': [
                {'path': '/static/js/dashboard.js', 'as': 'script'},
                {'path': '/api/manager/current', 'as': 'fetch'}
            ]
        }
        
    async def dispatch(self, request: Request, call_next) -> Response:
        """Add HTTP/2 Server Push hints"""
        response = await call_next(request)
        
        # Only for HTML responses
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('text/html'):
            return response
            
        path = request.url.path
        resources = self.push_resources.get(path, [])
        
        if resources:
            link_headers = []
            for resource in resources:
                link_header = f"<{resource['path']}>; rel=preload; as={resource['as']}"
                link_headers.append(link_header)
                
            if link_headers:
                response.headers['link'] = ', '.join(link_headers)
                
        return response


def setup_performance_middleware(app):
    """Setup all performance middleware"""
    
    # Add middlewares in order (last added = first executed)
    app.add_middleware(HTTP2ServerPushMiddleware)
    app.add_middleware(CacheControlMiddleware)
    app.add_middleware(PerformanceMiddleware, enable_compression=True, enable_batching=True)
    
    # Add built-in Gzip middleware as fallback
    # app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    logger.info("Performance middleware configured")


# Global middleware instances for stats access
_performance_middleware = None


def get_middleware_stats() -> Dict[str, Any]:
    """Get performance statistics from middleware"""
    global _performance_middleware
    
    if _performance_middleware:
        return _performance_middleware.get_performance_stats()
    else:
        return {"error": "Performance middleware not initialized"}