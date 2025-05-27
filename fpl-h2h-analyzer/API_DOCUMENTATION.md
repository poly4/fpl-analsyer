# FPL H2H Analyzer API Documentation

## Base URL
```
http://localhost:8000/api
```

## Authentication
Currently, the API does not require authentication for public league data. Some endpoints (marked with 🔒) require FPL authentication which is not yet implemented.

## Rate Limiting
- **Limit**: 90 requests per minute
- **Burst**: 10 additional requests
- **Algorithm**: Token bucket with priority queuing
- **Priority Levels**: CRITICAL > HIGH > MEDIUM > LOW

## Endpoints

### Core Endpoints

#### Health Check
```http
GET /health
```
Returns comprehensive health status of all services.

**Response**: 
```json
{
  "status": "healthy",
  "timestamp": 12345.678,
  "services": {
    "live_data": { "healthy": true, "response_time_ms": 18 },
    "cache": { "healthy": true, "ping": { "status": "pass" } },
    "websocket": { "status": "healthy", "active_connections": 5 }
  }
}
```

#### Current Gameweek
```http
GET /gameweek/current
```
Returns the current gameweek number.

**Response**: 
```json
{ "gameweek": 38 }
```

#### Rate Limiter Metrics
```http
GET /rate-limiter/metrics
```
Returns current rate limiter status and metrics.

**Response**:
```json
{
  "total_requests": 100,
  "successful_requests": 98,
  "rate_limited_requests": 2,
  "available_tokens": 85,
  "requests_per_minute": 45.2,
  "queue_sizes_by_priority": {
    "CRITICAL": 0,
    "HIGH": 1,
    "MEDIUM": 3,
    "LOW": 0
  }
}
```

### Manager Endpoints

#### Manager Info
```http
GET /manager/{manager_id}
```
Get basic manager information.

**Parameters**:
- `manager_id` (int): The manager's ID

**Response**: Manager object (see TypeScript interfaces)

#### Manager History
```http
GET /manager/{manager_id}/history
```
Get manager's season history including past seasons and chips used.

#### Manager Transfers
```http
GET /manager/{manager_id}/transfers
```
Get complete transfer history for a manager.

#### Latest Transfers
```http
GET /manager/{manager_id}/transfers/latest
```
Get only the latest gameweek transfers.

#### Manager Cup Status
```http
GET /manager/{manager_id}/cup
```
Get manager's FPL Cup status and matches.

### Player Endpoints

#### Player Summary
```http
GET /player/{player_id}/summary
```
Get detailed player information including:
- Season history
- Fixture list
- Past season performance

#### Dream Team
```http
GET /dream-team/{gameweek}
```
Get the highest scoring XI for a specific gameweek.

#### Set Piece Takers
```http
GET /set-piece-notes
```
Get penalty takers and set piece information for all teams.

### League Endpoints

#### H2H League Overview
```http
GET /league/{league_id}/overview
```
Get H2H league standings and basic info.

#### Classic League Standings
```http
GET /league/classic/{league_id}/standings
```
Get classic league standings with pagination.

**Query Parameters**:
- `page_standings` (int, default: 1): Page number for standings
- `page_new_entries` (int, default: 1): Page number for new entries

#### League Entries and H2H Matches
```http
GET /league/{league_id}/entries-and-h2h-matches
```
Get all league participants and their H2H matches.

#### Live H2H Battles
```http
GET /h2h/live-battles/{league_id}
```
Get live H2H match scores for current or specified gameweek.

**Query Parameters**:
- `gameweek` (int, optional): Specific gameweek (defaults to current)

### System Endpoints

#### Event Status
```http
GET /event-status
```
Get bonus processing status and league update information.
- **Priority**: CRITICAL during bonus processing
- **Cache**: 30 seconds

### H2H Analytics Endpoints

#### Comprehensive H2H Analysis
```http
GET /analytics/h2h/comprehensive/{manager1_id}/{manager2_id}
```
Get complete H2H analysis including:
- Differential analysis
- Predictions
- Historical patterns
- Chip strategies

**Query Parameters**:
- `gameweek` (int, optional): Specific gameweek
- `include_predictions` (bool, default: true)
- `include_patterns` (bool, default: true)

#### H2H Battle Details
```http
GET /h2h/battle/{manager1_id}/{manager2_id}
```
Get detailed battle analysis for current gameweek.

### Report Generation

#### Generate H2H Report
```http
POST /report/generate/h2h/{manager1_id}/{manager2_id}
```
Generate a comprehensive H2H report.

**Request Body**:
```json
{
  "league_id": 620117,
  "format": "pdf"  // Options: pdf, json, csv
}
```

#### Download Report
```http
GET /report/download/{file_path}
```
Download a previously generated report.

### WebSocket Endpoints

#### Main WebSocket Connection
```ws
WS /ws/connect
```
Main WebSocket for real-time updates.

**Message Types**:
- `SUBSCRIBE`: Subscribe to updates
- `UNSUBSCRIBE`: Unsubscribe from updates
- `HEARTBEAT`: Keep connection alive

**Subscription Rooms**:
- `league:{league_id}`: League updates
- `live:{gameweek}`: Live gameweek scores
- `h2h:{manager1_id}:{manager2_id}`: H2H battle updates

## Cache TTLs

| Endpoint Type | TTL | Description |
|--------------|-----|-------------|
| Live data | 30s | `/event/{id}/live`, `/event-status` |
| Volatile | 60s | Manager picks, latest transfers |
| Semi-static | 5m | League standings |
| Static | 30m | Bootstrap data, fixtures |
| Very static | 2h | Set piece notes, player history |

## Error Responses

All endpoints return standard error responses:

```json
{
  "detail": "Error message"
}
```

**Status Codes**:
- `200`: Success
- `404`: Resource not found
- `429`: Rate limited
- `500`: Internal server error
- `503`: Service unavailable

## TypeScript Integration

All response types are defined in `frontend/src/types/fpl-api.ts`.

Example usage:
```typescript
import { Manager, ManagerHistory } from '../types/fpl-api';
import { fplApiClient } from '../services/fpl-api-client';

const manager: Manager = await fplApiClient.getManagerInfo(123);
const history: ManagerHistory = await fplApiClient.getManagerHistory(123);
```

## Pagination

Large datasets support pagination:

```http
GET /league/classic/{league_id}/standings?page_standings=2
```

Helper methods automatically handle pagination:
- `get_all_h2h_matches(league_id)`: Gets all H2H matches
- `get_all_classic_league_standings(league_id)`: Gets all standings

## Not Yet Implemented

These endpoints require authentication (🔒):
- `GET /bootstrap-dynamic` - User's team value and bank
- `GET /me` - Current user's team
- `POST /transfers` - Make transfers

## Rate Limit Best Practices

1. Use appropriate priority levels:
   - CRITICAL: Live data during matches
   - HIGH: User-initiated requests
   - MEDIUM: Background updates
   - LOW: Static data refreshes

2. Implement client-side caching
3. Batch requests where possible
4. Monitor rate limit metrics via `/api/rate-limiter/metrics`