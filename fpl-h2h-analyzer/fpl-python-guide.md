# FPL API Complete Implementation Guide for Python Monorepo

## FPL API Overview

The Fantasy Premier League API is an unofficial, publicly accessible API that powers the official FPL website. It provides comprehensive data about players, teams, leagues, fixtures, and manager statistics.

**Base URL:** `https://fantasy.premierleague.com/api/`

## Critical CORS Limitation

The FPL API does not include CORS headers, meaning:
* ❌ Cannot be called directly from browser JavaScript
* ❌ Will fail with CORS errors from React apps
* ✅ Works fine from backend servers, mobile apps, and tools like Postman
* ✅ Requires a backend proxy to serve frontend applications

## Python Libraries for FPL

### Official Python FPL Library
The recommended way to install fpl is via pip:
```bash
pip install fpl
```

This is an asynchronous Python wrapper for the Fantasy Premier League API that simplifies API interactions.

### Alternative Libraries
- **pandas-fpl**: For data analysis with pandas integration
- **fpl-data**: Provides data transformation utilities
- **fplcli**: Command-line interface for FPL

## Monorepo Architecture for FPL Project

### Recommended Python Monorepo Structure
```
fpl-monorepo/
├── backend/                  # FastAPI + Python API
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   └── middleware/
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── redis.py
│   │   ├── services/
│   │   │   ├── fpl_service.py
│   │   │   └── cache_service.py
│   │   └── models/
│   ├── tests/
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/                 # React + Vite + TypeScript
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── shared/                   # Shared Python utilities
│   ├── __init__.py
│   ├── models.py
│   └── constants.py
├── scripts/                  # Utility scripts
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
└── Makefile
```

## FastAPI Backend Proxy Setup

### 1. Core FastAPI Application
```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter

from app.api.routes import fpl_router
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    redis_client = redis.from_url(
        settings.REDIS_URL, 
        encoding="utf-8", 
        decode_responses=True
    )
    await FastAPILimiter.init(redis_client)
    yield
    # Shutdown
    await redis_client.close()

app = FastAPI(
    title="FPL API Proxy",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(fpl_router, prefix="/api")
```

### 2. Configuration Management
```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # API Settings
    FPL_BASE_URL: str = "https://fantasy.premierleague.com/api"
    
    # CORS Settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",  # Vite default
        "http://localhost:3000",
    ]
    
    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_SECOND: int = 2
    
    # Environment
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 3. FPL Service with Proxy and Rate Limiting
```python
# backend/app/services/fpl_service.py
import httpx
from fastapi import HTTPException
from typing import Optional, Dict, Any
import asyncio
from datetime import datetime, timedelta

class FPLRequestQueue:
    """Queue to handle FPL API rate limiting"""
    def __init__(self, delay: float = 1.5):
        self.queue: asyncio.Queue = asyncio.Queue()
        self.delay = delay
        self.last_request = datetime.min
        self._worker_task = None
    
    async def start(self):
        """Start the queue worker"""
        self._worker_task = asyncio.create_task(self._worker())
    
    async def stop(self):
        """Stop the queue worker"""
        if self._worker_task:
            self._worker_task.cancel()
    
    async def _worker(self):
        """Process requests from the queue"""
        while True:
            try:
                request_func, future = await self.queue.get()
                
                # Enforce rate limit
                now = datetime.now()
                time_since_last = (now - self.last_request).total_seconds()
                if time_since_last < self.delay:
                    await asyncio.sleep(self.delay - time_since_last)
                
                try:
                    result = await request_func()
                    future.set_result(result)
                except Exception as e:
                    future.set_exception(e)
                
                self.last_request = datetime.now()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Queue worker error: {e}")
    
    async def add_request(self, request_func):
        """Add a request to the queue"""
        future = asyncio.Future()
        await self.queue.put((request_func, future))
        return await future

class FPLService:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "FPL-Python-App/1.0"
            }
        )
        self.request_queue = FPLRequestQueue()
        
    async def __aenter__(self):
        await self.request_queue.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.request_queue.stop()
        await self.client.aclose()
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None):
        """Make a rate-limited request to FPL API"""
        async def request():
            url = f"{self.base_url}/{endpoint}"
            response = await self.client.get(url, params=params)
            
            if response.status_code == 429:
                raise HTTPException(
                    status_code=429,
                    detail="FPL API rate limit exceeded"
                )
            
            response.raise_for_status()
            return response.json()
        
        return await self.request_queue.add_request(request)
    
    async def get_bootstrap_static(self):
        """Get all players, teams, gameweeks data"""
        return await self._make_request("bootstrap-static/")
    
    async def get_fixtures(self, event_id: Optional[int] = None):
        """Get fixtures data"""
        params = {"event": event_id} if event_id else None
        return await self._make_request("fixtures/", params)
    
    async def get_player_summary(self, player_id: int):
        """Get detailed player data"""
        return await self._make_request(f"element-summary/{player_id}/")
    
    async def get_live_data(self, event_id: int):
        """Get live gameweek data"""
        return await self._make_request(f"event/{event_id}/live/")
    
    async def get_manager_data(self, manager_id: int):
        """Get manager team data"""
        return await self._make_request(f"entry/{manager_id}/")
    
    async def get_manager_history(self, manager_id: int):
        """Get manager history"""
        return await self._make_request(f"entry/{manager_id}/history/")
    
    async def get_league_standings(self, league_id: int):
        """Get classic league standings"""
        return await self._make_request(f"leagues-classic/{league_id}/standings/")
```

### 4. API Routes with Caching
```python
# backend/app/api/routes/fpl.py
from fastapi import APIRouter, Depends, Query
from fastapi_limiter.depends import RateLimiter
from typing import Optional
import json

from app.services.fpl_service import FPLService
from app.services.cache_service import CacheService
from app.core.config import settings

router = APIRouter(prefix="/fpl", tags=["FPL"])

# Dependency to get FPL service
async def get_fpl_service():
    async with FPLService(settings.FPL_BASE_URL) as service:
        yield service

# Dependency to get cache service
def get_cache_service():
    return CacheService()

@router.get(
    "/bootstrap-static",
    dependencies=[Depends(RateLimiter(times=10, seconds=60))]
)
async def get_bootstrap_static(
    fpl_service: FPLService = Depends(get_fpl_service),
    cache_service: CacheService = Depends(get_cache_service)
):
    """Get all players, teams, and gameweek data (cached for 1 hour)"""
    cache_key = "fpl:bootstrap-static"
    
    # Check cache
    cached_data = await cache_service.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    
    # Fetch from API
    data = await fpl_service.get_bootstrap_static()
    
    # Cache for 1 hour
    await cache_service.set(cache_key, json.dumps(data), expire=3600)
    
    return data

@router.get(
    "/fixtures",
    dependencies=[Depends(RateLimiter(times=20, seconds=60))]
)
async def get_fixtures(
    event_id: Optional[int] = Query(None),
    fpl_service: FPLService = Depends(get_fpl_service),
    cache_service: CacheService = Depends(get_cache_service)
):
    """Get fixtures data"""
    cache_key = f"fpl:fixtures:{event_id or 'all'}"
    
    # Check cache
    cached_data = await cache_service.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    
    # Fetch from API
    data = await fpl_service.get_fixtures(event_id)
    
    # Cache for 30 minutes
    await cache_service.set(cache_key, json.dumps(data), expire=1800)
    
    return data

@router.get(
    "/player/{player_id}",
    dependencies=[Depends(RateLimiter(times=30, seconds=60))]
)
async def get_player_summary(
    player_id: int,
    fpl_service: FPLService = Depends(get_fpl_service),
    cache_service: CacheService = Depends(get_cache_service)
):
    """Get detailed player data"""
    cache_key = f"fpl:player:{player_id}"
    
    # Check cache
    cached_data = await cache_service.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    
    # Fetch from API
    data = await fpl_service.get_player_summary(player_id)
    
    # Cache for 15 minutes
    await cache_service.set(cache_key, json.dumps(data), expire=900)
    
    return data

@router.get(
    "/live/{event_id}",
    dependencies=[Depends(RateLimiter(times=10, seconds=60))]
)
async def get_live_data(
    event_id: int,
    fpl_service: FPLService = Depends(get_fpl_service),
    cache_service: CacheService = Depends(get_cache_service)
):
    """Get live gameweek data"""
    cache_key = f"fpl:live:{event_id}"
    
    # Check cache (shorter TTL for live data)
    cached_data = await cache_service.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    
    # Fetch from API
    data = await fpl_service.get_live_data(event_id)
    
    # Cache for 1 minute (live data changes frequently)
    await cache_service.set(cache_key, json.dumps(data), expire=60)
    
    return data
```

### 5. Redis Cache Service
```python
# backend/app/services/cache_service.py
import redis.asyncio as redis
from typing import Optional
from app.core.config import settings

class CacheService:
    def __init__(self):
        self.redis_client = None
    
    async def connect(self):
        """Connect to Redis"""
        self.redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        if not self.redis_client:
            await self.connect()
        return await self.redis_client.get(key)
    
    async def set(self, key: str, value: str, expire: int = 300):
        """Set value in cache with expiration"""
        if not self.redis_client:
            await self.connect()
        await self.redis_client.set(key, value, ex=expire)
    
    async def delete(self, key: str):
        """Delete key from cache"""
        if not self.redis_client:
            await self.connect()
        await self.redis_client.delete(key)
```

## Using the Python FPL Library

### Basic Usage Example
```python
# scripts/fpl_analysis.py
import asyncio
from fpl import FPL

async def get_top_players():
    async with FPL() as fpl:
        # Get all players
        players = await fpl.get_players()
        
        # Sort by total points
        top_players = sorted(
            players, 
            key=lambda x: x.total_points, 
            reverse=True
        )[:10]
        
        for player in top_players:
            print(f"{player.web_name}: {player.total_points} points")

async def get_team_info(team_id):
    async with FPL() as fpl:
        # Get team information
        user = await fpl.get_user(team_id)
        print(f"Team: {user.name}")
        print(f"Overall Rank: {user.overall_rank}")
        
        # Get current team
        team = await user.get_team()
        print("\nCurrent Team:")
        for player in team:
            print(f"- {player.web_name}")

if __name__ == "__main__":
    asyncio.run(get_top_players())
```

## Docker Configuration

### Backend Dockerfile
```dockerfile
# docker/Dockerfile.backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .
COPY shared/ ./shared/

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose Configuration
```yaml
# docker/docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    build:
      context: ..
      dockerfile: docker/Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - ENVIRONMENT=development
    depends_on:
      - redis
    volumes:
      - ../backend:/app
      - ../shared:/app/shared
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ..
      dockerfile: docker/Dockerfile.frontend
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://localhost:8000
    volumes:
      - ../frontend:/app
      - /app/node_modules

volumes:
  redis_data:
```

## Rate Limiting Implementation

However it will start blocking us when we go above a couple of requests per second. To handle this:

### 1. Custom Rate Limiter Middleware
```python
# backend/app/middleware/rate_limiter.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import time
from collections import defaultdict
import asyncio

class CustomRateLimiter:
    def __init__(self, requests_per_second: float = 1.5):
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = defaultdict(float)
        self.lock = asyncio.Lock()
    
    async def __call__(self, request: Request, call_next):
        client_id = request.client.host
        
        async with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time[client_id]
            
            if time_since_last < self.min_interval:
                wait_time = self.min_interval - time_since_last
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": f"Rate limit exceeded. Retry after {wait_time:.2f} seconds"
                    },
                    headers={
                        "Retry-After": str(int(wait_time) + 1)
                    }
                )
            
            self.last_request_time[client_id] = current_time
        
        response = await call_next(request)
        return response
```

### 2. Using FastAPI-Limiter with Redis
FastAPI-Limiter is simple to use, which just provide a dependency RateLimiter:

```python
# backend/app/main.py (updated)
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter, WebSocketRateLimiter

# In your endpoint
@router.get(
    "/heavy-endpoint",
    dependencies=[Depends(RateLimiter(times=2, seconds=5))]
)
async def heavy_endpoint():
    """This endpoint allows 2 requests per 5 seconds"""
    return {"message": "Success"}

# For WebSocket support
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ratelimit = WebSocketRateLimiter(times=1, seconds=5)
    
    while True:
        try:
            data = await websocket.receive_text()
            await ratelimit(websocket, context_key=data)
            await websocket.send_text(f"Echo: {data}")
        except WebSocketRateLimitException:
            await websocket.send_text("Rate limit exceeded")
```

## Caching Strategies

### 1. Tiered Caching Strategy
```python
# backend/app/services/cache_strategy.py
from enum import Enum
from typing import Dict

class CacheTier(Enum):
    SHORT = 60          # 1 minute
    MEDIUM = 900        # 15 minutes
    LONG = 3600         # 1 hour
    VERY_LONG = 86400   # 24 hours

CACHE_STRATEGY: Dict[str, CacheTier] = {
    "bootstrap-static": CacheTier.LONG,      # Player data changes rarely
    "fixtures": CacheTier.MEDIUM,            # Fixture data moderate changes
    "live": CacheTier.SHORT,                 # Live data changes frequently
    "player-summary": CacheTier.MEDIUM,      # Player stats moderate changes
    "manager": CacheTier.LONG,               # Manager data stable
    "league-standings": CacheTier.MEDIUM,    # Standings update after matches
}
```

### 2. Cache Warming
```python
# backend/app/tasks/cache_warmer.py
import asyncio
from app.services.fpl_service import FPLService
from app.services.cache_service import CacheService

async def warm_cache():
    """Pre-populate cache with frequently accessed data"""
    async with FPLService(settings.FPL_BASE_URL) as fpl_service:
        cache_service = CacheService()
        await cache_service.connect()
        
        try:
            # Warm bootstrap-static (most accessed)
            print("Warming bootstrap-static cache...")
            data = await fpl_service.get_bootstrap_static()
            await cache_service.set(
                "fpl:bootstrap-static", 
                json.dumps(data), 
                expire=3600
            )
            
            # Warm current gameweek fixtures
            print("Warming fixtures cache...")
            fixtures = await fpl_service.get_fixtures()
            await cache_service.set(
                "fpl:fixtures:all", 
                json.dumps(fixtures), 
                expire=1800
            )
            
        finally:
            await cache_service.disconnect()

# Run cache warming on startup or schedule
if __name__ == "__main__":
    asyncio.run(warm_cache())
```

## Testing Strategy

### 1. Unit Tests with Pytest
```python
# backend/tests/test_fpl_service.py
import pytest
from unittest.mock import AsyncMock, patch
from app.services.fpl_service import FPLService

@pytest.mark.asyncio
async def test_get_bootstrap_static():
    """Test fetching bootstrap static data"""
    mock_response = {"players": [], "teams": []}
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=AsyncMock(return_value=mock_response)
        )
        
        async with FPLService("http://test.com") as service:
            result = await service.get_bootstrap_static()
            
        assert result == mock_response
        mock_get.assert_called_once()

@pytest.mark.asyncio
async def test_rate_limit_handling():
    """Test rate limit error handling"""
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.return_value = AsyncMock(status_code=429)
        
        async with FPLService("http://test.com") as service:
            with pytest.raises(HTTPException) as exc_info:
                await service.get_bootstrap_static()
            
        assert exc_info.value.status_code == 429
```

### 2. Integration Tests
```python
# backend/tests/test_api_integration.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_cors_headers():
    """Test CORS headers are properly set"""
    response = client.options(
        "/api/fpl/bootstrap-static",
        headers={"Origin": "http://localhost:5173"}
    )
    
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.headers["access-control-allow-credentials"] == "true"

def test_rate_limiting():
    """Test rate limiting works"""
    # Make multiple requests quickly
    responses = []
    for _ in range(15):
        response = client.get("/api/fpl/bootstrap-static")
        responses.append(response.status_code)
    
    # Should have some 429 responses
    assert 429 in responses
```

## Production Deployment

### 1. Environment Variables
```bash
# .env.production
ENVIRONMENT=production
FPL_BASE_URL=https://fantasy.premierleague.com/api
REDIS_URL=redis://redis:6379
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
RATE_LIMIT_PER_MINUTE=30
RATE_LIMIT_PER_SECOND=1
```

### 2. Gunicorn Configuration
```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
preload_app = True
accesslog = "-"
errorlog = "-"
```

### 3. Production Dockerfile
```dockerfile
# docker/Dockerfile.backend.prod
FROM python:3.11-slim as builder

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application
COPY backend/ .
COPY shared/ ./shared/

# Run with gunicorn
CMD ["gunicorn", "app.main:app", "-c", "gunicorn.conf.py"]
```

## Monitoring and Logging

### 1. Structured Logging
```python
# backend/app/core/logging.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        
        if hasattr(record, 'request_id'):
            log_obj['request_id'] = record.request_id
            
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_obj)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.handlers = [handler]
```

### 2. Request Tracking Middleware
```python
# backend/app/middleware/request_tracking.py
import uuid
import time
from fastapi import Request

async def request_tracking_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Add request ID to request state
    request.state.request_id = request_id
    
    # Log request
    logger.info(
        "Request started",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host
        }
    )
    
    response = await call_next(request)
    
    # Log response
    duration = time.time() - start_time
    logger.info(
        "Request completed",
        extra={
            "request_id": request_id,
            "status_code": response.status_code,
            "duration": duration
        }
    )
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    
    return response
```

## Summary

This Python implementation provides:

- ✅ **FastAPI backend proxy** to handle CORS issues
- ✅ **Python monorepo structure** for code organization
- ✅ **Asynchronous FPL library** integration
- ✅ **Redis-based caching** with tiered strategy
- ✅ **Rate limiting** implementation (both custom and library-based)
- ✅ **Docker configuration** for easy deployment
- ✅ **Comprehensive testing** strategy
- ✅ **Production-ready** configuration
- ✅ **Monitoring and logging** setup

The architecture handles the FPL API's constraints while providing a scalable, maintainable solution for building FPL applications with Python.