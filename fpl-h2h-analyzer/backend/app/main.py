from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import redis.asyncio as redis
import os
import json
import asyncio
import uuid
from typing import Optional, List, Dict, Any

from .services.live_data_v2 import LiveDataService
from .services.h2h_analyzer import H2HAnalyzer
from .services.enhanced_h2h_analyzer import EnhancedH2HAnalyzer
from .services.analytics import DifferentialAnalyzer, PredictiveEngine, ChipAnalyzer, PatternRecognition
from .services.advanced_analytics import AdvancedAnalyticsService
from .services.report_generator import ReportGenerator
from .services.cache import CacheService
from .websocket.live_updates import WebSocketManager, MessageType, WebSocketMessage, generate_h2h_room_id, generate_league_room_id, generate_live_room_id
from .config import TARGET_LEAGUE_ID
import logging

logger = logging.getLogger(__name__)

# Global instances
live_data_service = None
h2h_analyzer = None
enhanced_h2h_analyzer = None
differential_analyzer = None
predictive_engine = None
chip_analyzer = None
pattern_recognizer = None
advanced_analytics = None
report_generator = None
redis_client = None
cache_service = None
websocket_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global live_data_service, h2h_analyzer, enhanced_h2h_analyzer, differential_analyzer, predictive_engine, chip_analyzer, pattern_recognizer, advanced_analytics, report_generator, redis_client, cache_service, websocket_manager
    
    try:
        # Initialize Redis connection
        redis_client = await redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        
        # Initialize cache service with Redis
        cache_service = CacheService(redis_client)
        
        # Initialize WebSocket manager
        websocket_manager = WebSocketManager(max_connections=1000, heartbeat_interval=30)
        await websocket_manager.start_background_tasks()
        
        # Initialize services with rate limiting
        live_data_service = LiveDataService()
        h2h_analyzer = H2HAnalyzer(live_data_service)
        
        # Initialize analytics services
        differential_analyzer = DifferentialAnalyzer()
        predictive_engine = PredictiveEngine()
        chip_analyzer = ChipAnalyzer()
        pattern_recognizer = PatternRecognition()
        
        # Initialize enhanced analyzer with all analytics services
        enhanced_h2h_analyzer = EnhancedH2HAnalyzer(
            h2h_analyzer=h2h_analyzer,
            differential_analyzer=differential_analyzer,
            predictive_engine=predictive_engine,
            chip_analyzer=chip_analyzer,
            pattern_recognition=pattern_recognizer,
            live_data_service=live_data_service
        )
        
        # Initialize advanced analytics service
        advanced_analytics = AdvancedAnalyticsService(live_data_service)
        
        # Initialize report generator
        report_generator = ReportGenerator(
            live_data_service=live_data_service,
            h2h_analyzer=h2h_analyzer,
            enhanced_h2h_analyzer=enhanced_h2h_analyzer
        )
        
        # Warm cache for better performance
        current_gw = await live_data_service.get_current_gameweek()
        await live_data_service.warm_cache(league_id=TARGET_LEAGUE_ID)
        
        print(f"✅ FPL Nexus backend started successfully")
        print(f"🔴 Redis: {os.getenv('REDIS_URL', 'redis://localhost:6379')}")
        print(f"🎯 Current Gameweek: {current_gw}")
        print(f"🔌 WebSocket Manager: {websocket_manager.max_connections} max connections")
        
    except Exception as e:
        print(f"❌ Failed to start services: {e}")
        raise
    
    yield
    
    # Shutdown
    print("🛑 Shutting down FPL Nexus backend...")
    
    if websocket_manager:
        await websocket_manager.stop_background_tasks()
    
    if live_data_service:
        await live_data_service.close()
    
    if cache_service:
        await cache_service.close()
    
    if redis_client:
        await redis_client.close()
    
    print("✅ Shutdown complete")

app = FastAPI(lifespan=lifespan)

# CORS configuration
origins = [
    "http://localhost:3000",
    "http://localhost:5173",  # Vite dev server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    """Enhanced health check with service status"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": asyncio.get_event_loop().time(),
            "services": {}
        }
        
        # Check live data service
        if live_data_service:
            live_health = await live_data_service.health_check()
            health_status["services"]["live_data"] = live_health
            if not live_health["healthy"]:
                health_status["status"] = "degraded"
        
        # Check cache service
        if cache_service:
            cache_health = await cache_service.health_check()
            health_status["services"]["cache"] = cache_health
            if not cache_health["healthy"]:
                health_status["status"] = "degraded"
        
        # Check WebSocket manager
        if websocket_manager:
            ws_health = websocket_manager.get_health_status()
            health_status["services"]["websocket"] = ws_health
            if ws_health["status"] != "healthy":
                health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": asyncio.get_event_loop().time()
        }

@app.get("/api/test/rate-limiter")
async def test_rate_limiter():
    """Test if rate limiter is initialized"""
    try:
        has_rate_limiter = hasattr(live_data_service, 'rate_limiter') if live_data_service else False
        rate_limiter_type = type(live_data_service.rate_limiter).__name__ if has_rate_limiter else None
        
        result = {
            "live_data_service_exists": live_data_service is not None,
            "has_rate_limiter": has_rate_limiter,
            "rate_limiter_type": rate_limiter_type
        }
        
        if has_rate_limiter:
            try:
                metrics = live_data_service.rate_limiter.get_metrics()
                result["metrics"] = metrics
            except Exception as e:
                result["metrics_error"] = str(e)
                
        return result
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}

@app.get("/api/test/analytics")
async def test_analytics():
    """Test analytics initialization"""
    try:
        result = {
            "enhanced_analyzer": enhanced_h2h_analyzer is not None,
            "differential_analyzer": enhanced_h2h_analyzer.differential_analyzer is not None if enhanced_h2h_analyzer else False,
            "predictive_engine": enhanced_h2h_analyzer.predictive_engine is not None if enhanced_h2h_analyzer else False,
            "chip_analyzer": enhanced_h2h_analyzer.chip_analyzer is not None if enhanced_h2h_analyzer else False,
            "pattern_recognizer": enhanced_h2h_analyzer.pattern_recognition is not None if enhanced_h2h_analyzer else False
        }
        
        # Try fetching some data
        if enhanced_h2h_analyzer:
            try:
                data = await enhanced_h2h_analyzer._fetch_battle_data(3356830, 3531308, 38)
                result["data_fetch"] = {
                    "manager1_info": "id" in data.get("manager1_info", {}),
                    "manager2_info": "id" in data.get("manager2_info", {}),
                    "manager1_picks": "picks" in data.get("manager1_picks", {}),
                    "manager2_picks": "picks" in data.get("manager2_picks", {}),
                    "manager1_history": "current" in data.get("manager1_history", {}),
                    "manager2_history": "current" in data.get("manager2_history", {}),
                }
            except KeyError as e:
                result["data_fetch_error"] = f"KeyError: {e}"
                import traceback
                result["traceback"] = traceback.format_exc()
            except Exception as e:
                result["data_fetch_error"] = str(e)
                result["error_type"] = type(e).__name__
                
        return result
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}

@app.get("/api/gameweek/current")
async def get_current_gameweek():
    """Get the current gameweek."""
    try:
        gw = await live_data_service.get_current_gameweek()
        return {"gameweek": gw}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/league/{league_id}/overview")
async def get_league_overview(league_id: int):
    """Get league overview including standings and basic info."""
    try:
        # Get the full standings data with league info
        standings_data = await h2h_analyzer.get_h2h_standings(league_id)
        current_gw = await live_data_service.get_current_gameweek()
        
        return {
            "league_id": league_id,
            "current_gameweek": current_gw,
            "standings": standings_data  # Return the full API response with league info and standings
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/websocket/broadcast/{room_id}")
async def broadcast_message(room_id: str, message_type: str, data: dict):
    """Manually broadcast a message to a WebSocket room (for testing/admin)"""
    if not websocket_manager:
        raise HTTPException(status_code=503, detail="WebSocket service unavailable")
    
    try:
        message = WebSocketMessage(
            type=MessageType(message_type),
            data=data
        )
        
        sent_count = await websocket_manager.broadcast_to_room(room_id, message)
        
        return {
            "message": f"Broadcasted to room {room_id}",
            "recipients": sent_count,
            "message_type": message_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/h2h/live-battles/{league_id}")
async def get_live_battles(league_id: int, gameweek: Optional[int] = None):
    """Get live H2H battles for a league."""
    try:
        # Get current gameweek if not specified
        if gameweek is None:
            current_gw_data = await live_data_service.get_current_gameweek()
            # Handle end of season - cap at GW38
            gameweek = min(current_gw_data, 38) if isinstance(current_gw_data, int) else 38
            
        logger.info(f"Fetching H2H battles for league {league_id}, gameweek {gameweek}")
        
        # Get H2H matches for the gameweek
        matches = await h2h_analyzer.get_h2h_matches(league_id, gameweek)
        
        # If no matches found for current gameweek, try the previous one
        if not matches and gameweek > 1:
            logger.info(f"No matches found for GW{gameweek}, trying GW{gameweek-1}")
            gameweek = gameweek - 1
            matches = await h2h_analyzer.get_h2h_matches(league_id, gameweek)
        
        # Get live data for the gameweek
        live_data = await live_data_service.get_live_gameweek_data(gameweek)
        
        # Process each match to add live scores
        live_battles = []
        for match in matches:
            # Calculate live scores for both managers
            manager1_id = match.get('entry_1_entry')
            manager2_id = match.get('entry_2_entry')
            
            if manager1_id and manager2_id:
                try:
                    # Get picks for both managers
                    picks1 = await live_data_service.get_manager_picks(manager1_id, gameweek)
                    picks2 = await live_data_service.get_manager_picks(manager2_id, gameweek)
                    
                    # Calculate live scores
                    score1 = await h2h_analyzer._calculate_live_score(picks1, live_data)
                    score2 = await h2h_analyzer._calculate_live_score(picks2, live_data)
                    
                    live_battles.append({
                        "match_id": match.get('id'),
                        "gameweek": gameweek,
                        "manager1": {
                            "id": manager1_id,
                            "name": match.get('entry_1_name'),
                            "player_name": match.get('entry_1_player_name'),
                            "score": score1.get('total', 0),
                            "chip": score1.get('chip')
                        },
                        "manager2": {
                            "id": manager2_id,
                            "name": match.get('entry_2_name'),
                            "player_name": match.get('entry_2_player_name'),
                            "score": score2.get('total', 0),
                            "chip": score2.get('chip')
                        },
                        "completed": match.get('finished', False)
                    })
                except Exception as e:
                    print(f"Error processing match {match.get('id')}: {e}")
                    # For completed matches, use the final scores from the API
                    is_completed = gameweek < 38 or match.get('finished', False)
                    live_battles.append({
                        "match_id": match.get('id'),
                        "gameweek": gameweek,
                        "manager1": {
                            "id": manager1_id,
                            "name": match.get('entry_1_name'),
                            "player_name": match.get('entry_1_player_name'),
                            "score": match.get('entry_1_points', 0)
                        },
                        "manager2": {
                            "id": manager2_id,
                            "name": match.get('entry_2_name'), 
                            "player_name": match.get('entry_2_player_name'),
                            "score": match.get('entry_2_points', 0)
                        },
                        "completed": is_completed
                    })
        
        return {
            "gameweek": gameweek,
            "league_id": league_id,
            "battles": live_battles
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/h2h/battle/{manager1_id}/{manager2_id}")
async def get_h2h_battle_details(manager1_id: int, manager2_id: int, gameweek: Optional[int] = None):
    """Get detailed H2H battle analysis between two managers."""
    try:
        if gameweek is None:
            gameweek = await live_data_service.get_current_gameweek()
            
        analysis = await h2h_analyzer.analyze_battle(manager1_id, manager2_id, gameweek)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/connect")
async def websocket_connect(websocket: WebSocket):
    """Main WebSocket endpoint for real-time updates"""
    client_id = str(uuid.uuid4())
    
    if not websocket_manager:
        await websocket.close(code=1011, reason="WebSocket service unavailable")
        return
    
    # Connect client to WebSocket manager
    connected = await websocket_manager.connect(websocket, client_id)
    if not connected:
        return
    
    try:
        # Handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                await websocket_manager.handle_client_message(client_id, data)
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"Error handling message from {client_id}: {e}")
                break
                
    except Exception as e:
        print(f"WebSocket error for client {client_id}: {e}")
    finally:
        await websocket_manager.disconnect(client_id)

@app.websocket("/ws/h2h-battle/{manager1_id}/{manager2_id}")
async def websocket_h2h_battle(websocket: WebSocket, manager1_id: int, manager2_id: int):
    """Legacy WebSocket endpoint for H2H battles (backwards compatibility)"""
    client_id = f"h2h_{manager1_id}_{manager2_id}_{uuid.uuid4().hex[:8]}"
    
    if not websocket_manager:
        await websocket.close(code=1011, reason="WebSocket service unavailable")
        return
    
    # Connect client
    connected = await websocket_manager.connect(websocket, client_id)
    if not connected:
        return
    
    try:
        # Subscribe to H2H room
        room_id = generate_h2h_room_id(str(manager1_id), str(manager2_id))
        await websocket_manager.subscribe_to_room(client_id, room_id)
        
        # Get current gameweek and subscribe to live updates
        current_gw = await live_data_service.get_current_gameweek()
        live_room_id = generate_live_room_id(current_gw)
        await websocket_manager.subscribe_to_room(client_id, live_room_id)
        
        # Send initial battle data
        try:
            analysis = await h2h_analyzer.analyze_battle(manager1_id, manager2_id, current_gw)
            initial_message = WebSocketMessage(
                type=MessageType.H2H_UPDATE,
                data={
                    "gameweek": current_gw,
                    "manager1": {
                        "id": manager1_id,
                        "score": analysis["manager1"]["score"]["total"],
                        "name": analysis["manager1"]["name"]
                    },
                    "manager2": {
                        "id": manager2_id,
                        "score": analysis["manager2"]["score"]["total"],
                        "name": analysis["manager2"]["name"]
                    },
                    "differentials": analysis["differentials"][:5],
                    "timestamp": asyncio.get_event_loop().time()
                },
                client_id=client_id
            )
            await websocket_manager.send_to_client(client_id, initial_message)
        except Exception as e:
            print(f"Error sending initial H2H data: {e}")
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                await websocket_manager.handle_client_message(client_id, data)
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"Error in H2H WebSocket: {e}")
                break
                
    finally:
        await websocket_manager.disconnect(client_id)

@app.get("/api/manager/{manager_id}")
async def get_manager_info(manager_id: int):
    """Get manager information."""
    try:
        data = await live_data_service.get_manager_info(manager_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/manager/{manager_id}/history")
async def get_manager_history(manager_id: int):
    """Get manager history."""
    try:
        data = await live_data_service.get_manager_history(manager_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/manager/{manager_id}/transfers")
async def get_manager_transfers(manager_id: int):
    """Get complete transfer history for a manager."""
    try:
        data = await live_data_service.get_manager_transfers(manager_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/manager/{manager_id}/transfers/latest")
async def get_manager_transfers_latest(manager_id: int):
    """Get latest transfers for a manager."""
    try:
        data = await live_data_service.get_manager_transfers_latest(manager_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/manager/{manager_id}/cup")
async def get_manager_cup(manager_id: int):
    """Get manager's cup status."""
    try:
        data = await live_data_service.get_manager_cup(manager_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/player/{player_id}/summary")
async def get_element_summary(player_id: int):
    """Get detailed player information including history."""
    try:
        data = await live_data_service.get_element_summary(player_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dream-team/{gameweek}")
async def get_dream_team(gameweek: int):
    """Get the dream team for a specific gameweek."""
    try:
        data = await live_data_service.get_dream_team(gameweek)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/set-piece-notes")
async def get_set_piece_notes():
    """Get penalty and set piece taker information."""
    try:
        data = await live_data_service.get_set_piece_notes()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/event-status")
async def get_event_status():
    """Get current event/bonus processing status."""
    try:
        data = await live_data_service.get_event_status()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/league/classic/{league_id}/standings")
async def get_classic_league_standings(
    league_id: int,
    page_standings: int = 1,
    page_new_entries: int = 1
):
    """Get classic league standings with pagination."""
    try:
        data = await live_data_service.get_classic_league_standings(
            league_id, page_standings, page_new_entries
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/league/{league_id}/entries-and-h2h-matches")
async def get_league_entries_and_h2h_matches(league_id: int):
    """Get all league entries and H2H matches."""
    try:
        data = await live_data_service.get_league_entries_and_h2h_matches(league_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/websocket/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    if not websocket_manager:
        raise HTTPException(status_code=503, detail="WebSocket service unavailable")
    
    try:
        stats = websocket_manager.get_statistics()
        health = websocket_manager.get_health_status()
        
        return {
            "statistics": stats,
            "health": health,
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cache/invalidate")
async def invalidate_cache(pattern: Optional[str] = None):
    """Invalidate cache entries"""
    try:
        if live_data_service:
            await live_data_service.invalidate_cache(pattern)
            return {"message": f"Cache invalidated", "pattern": pattern}
        else:
            raise HTTPException(status_code=503, detail="Cache service unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cache/warm")
async def warm_cache(league_id: Optional[int] = None):
    """Warm cache with frequently accessed data"""
    try:
        if live_data_service:
            await live_data_service.warm_cache(league_id=league_id or TARGET_LEAGUE_ID)
            return {"message": "Cache warming completed", "league_id": league_id}
        else:
            raise HTTPException(status_code=503, detail="Cache service unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cache/stats")
async def get_cache_stats():
    """Get cache performance statistics"""
    try:
        if live_data_service:
            stats = live_data_service.get_cache_stats()
            return stats
        else:
            raise HTTPException(status_code=503, detail="Cache service unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rate-limiter/metrics")
async def get_rate_limiter_metrics():
    """Get rate limiter metrics and status"""
    try:
        if live_data_service and hasattr(live_data_service, 'rate_limiter'):
            metrics = live_data_service.rate_limiter.get_metrics()
            return metrics
        else:
            raise HTTPException(status_code=503, detail="Rate limiter not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Analytics Endpoints

@app.get("/api/analytics/h2h/comprehensive/{manager1_id}/{manager2_id}")
async def get_comprehensive_h2h_analysis(
    manager1_id: int,
    manager2_id: int,
    gameweek: Optional[int] = None,
    include_predictions: bool = True,
    include_patterns: bool = True
):
    """Get comprehensive H2H analysis with all analytics"""
    try:
        logger.info(f"Starting comprehensive analysis for {manager1_id} vs {manager2_id}")
        
        if not enhanced_h2h_analyzer:
            raise HTTPException(status_code=503, detail="Analytics service not initialized")
        
        logger.info("Enhanced analyzer available, calling analyze_battle_comprehensive")
            
        if gameweek is None:
            gameweek = await live_data_service.get_current_gameweek()
            
        analysis = await enhanced_h2h_analyzer.analyze_battle_comprehensive(
            manager1_id,
            manager2_id,
            gameweek
        )
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Could not generate analysis")
        
        # Return the analysis directly as it's already a dict
        return analysis
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"ERROR in comprehensive H2H analysis: {e}")
        print(f"Full traceback:\n{tb}")
        logger.error(f"Error in comprehensive H2H analysis: {e}")
        logger.error(f"Traceback: {tb}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/h2h/differential/{manager1_id}/{manager2_id}")
async def get_differential_analysis(
    manager1_id: int,
    manager2_id: int,
    gameweek: Optional[int] = None
):
    """Get quick differential analysis"""
    try:
        if not enhanced_h2h_analyzer:
            raise HTTPException(status_code=503, detail="Analytics service not initialized")
            
        # Get differential analysis from enhanced analyzer
        if gameweek is None:
            gameweek = await live_data_service.get_current_gameweek()
            
        comprehensive = await enhanced_h2h_analyzer.analyze_battle_comprehensive(
            manager1_id,
            manager2_id,
            gameweek
        )
        
        # Extract differential analysis
        if comprehensive and 'differential_analysis' in comprehensive:
            return comprehensive['differential_analysis']
        else:
            # Fallback to direct differential analyzer
            if enhanced_h2h_analyzer.differential_analyzer:
                bootstrap_data = await live_data_service.get_bootstrap_static()
                live_data = await live_data_service.get_live_gameweek_data(gameweek)
                manager1_picks = await live_data_service.get_manager_picks(manager1_id, gameweek)
                manager2_picks = await live_data_service.get_manager_picks(manager2_id, gameweek)
                
                return await enhanced_h2h_analyzer.differential_analyzer.analyze_differentials(
                    manager1_picks,
                    manager2_picks,
                    live_data,
                    bootstrap_data,
                    manager1_id,
                    manager2_id,
                    gameweek
                )
            else:
                raise HTTPException(status_code=503, detail="Differential analyzer not available")
    except Exception as e:
        logger.error(f"Error in differential analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/h2h/prediction/{manager1_id}/{manager2_id}")
async def get_h2h_prediction(
    manager1_id: int,
    manager2_id: int,
    gameweek: Optional[int] = None
):
    """Get H2H match prediction"""
    try:
        if not enhanced_h2h_analyzer or not enhanced_h2h_analyzer.predictive_engine:
            raise HTTPException(status_code=503, detail="Predictive engine not initialized")
            
        if gameweek is None:
            gameweek = await live_data_service.get_current_gameweek()
            
        # Fetch required data
        manager1_picks = await live_data_service.get_manager_picks(manager1_id, gameweek)
        manager2_picks = await live_data_service.get_manager_picks(manager2_id, gameweek)
        
        # Generate prediction using predict_match_outcome
        manager1_history = await live_data_service.get_manager_history(manager1_id)
        manager2_history = await live_data_service.get_manager_history(manager2_id)
        fixtures = await live_data_service.get_fixtures()
        
        prediction = await enhanced_h2h_analyzer.predictive_engine.predict_match_outcome(
            manager1_id,
            manager2_id,
            manager1_history,
            manager2_history,
            manager1_picks,
            manager2_picks,
            fixtures,
            gameweek
        )
        
        return prediction
    except Exception as e:
        logger.error(f"Error in H2H prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/chip-strategy/{manager_id}")
async def get_chip_strategy(
    manager_id: int,
    opponent_id: Optional[int] = None,
    horizon: int = 10
):
    """Get chip usage strategy analysis"""
    try:
        if not enhanced_h2h_analyzer or not enhanced_h2h_analyzer.chip_analyzer:
            raise HTTPException(status_code=503, detail="Chip analyzer not initialized")
            
        # Fetch required data
        manager_info = await live_data_service.get_manager_info(manager_id)
        manager_history = await live_data_service.get_manager_history(manager_id)
        current_gw = await live_data_service.get_current_gameweek()
        manager_picks = await live_data_service.get_manager_picks(manager_id, current_gw)
        
        opponent_data = None
        if opponent_id:
            opponent_data = await live_data_service.get_manager_info(opponent_id)
            
        # Get chip recommendations
        fixtures = await live_data_service.get_fixtures()
        bootstrap_data = await live_data_service.get_bootstrap_static()
        
        h2h_context = None
        if opponent_id:
            opponent_picks = await live_data_service.get_manager_picks(opponent_id, current_gw)
            # Create H2H context
            h2h_context = {
                "is_leading": False,  # Would need actual scores
                "score_difference": 0,  # Would need actual scores
                "opponent_chip": opponent_picks.get('active_chip') if opponent_picks else None
            }
        
        recommendations = await enhanced_h2h_analyzer.chip_analyzer.get_chip_recommendations(
            manager_id,
            manager_history,
            fixtures,
            current_gw,
            h2h_context,
            bootstrap_data,
            manager_picks
        )
        
        return recommendations
    except Exception as e:
        logger.error(f"Error in chip strategy analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/patterns/manager/{manager_id}")
async def get_manager_patterns(
    manager_id: int
):
    """Get historical patterns for a manager"""
    try:
        if not enhanced_h2h_analyzer or not enhanced_h2h_analyzer.pattern_recognition:
            raise HTTPException(status_code=503, detail="Pattern recognizer not initialized")
            
        # Fetch manager history
        manager_history = await live_data_service.get_manager_history(manager_id)
        
        # Analyze patterns
        patterns = await enhanced_h2h_analyzer.pattern_recognition.analyze_manager_patterns(
            manager_id,
            manager_history
        )
        
        # Patterns is returned as a dict, not an object with attributes
        return patterns
    except Exception as e:
        logger.error(f"Error in pattern analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/visualization/h2h/{manager1_id}/{manager2_id}")
async def get_h2h_visualization_data(
    manager1_id: int,
    manager2_id: int,
    gameweek: Optional[int] = None
):
    """Get data formatted for visualization"""
    try:
        if not enhanced_h2h_analyzer:
            raise HTTPException(status_code=503, detail="Analytics service not initialized")
            
        if gameweek is None:
            gameweek = await live_data_service.get_current_gameweek()
            
        # Get comprehensive analysis
        analysis = await enhanced_h2h_analyzer.analyze_battle_comprehensive(
            manager1_id,
            manager2_id,
            gameweek
        )
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Could not generate analysis")
        
        # Extract data from the dictionary structure
        meta = analysis.get("meta", {})
        core = analysis.get("core_analysis", {})
        differential = analysis.get("differential_analysis", {})
        prediction = analysis.get("prediction", {})
        summary = analysis.get("summary", {})
        
        # Format for visualization
        viz_data = {
            "overview": {
                "gameweek": meta.get("gameweek", gameweek),
                "manager1": {
                    "id": manager1_id,
                    "name": core.get("manager1", {}).get("name", "Unknown"),
                    "score": core.get("manager1", {}).get("score", {}).get("total", 0)
                },
                "manager2": {
                    "id": manager2_id,
                    "name": core.get("manager2", {}).get("name", "Unknown"),
                    "score": core.get("manager2", {}).get("score", {}).get("total", 0)
                },
                "advantage_score": summary.get("advantage_score", 0),
                "confidence": summary.get("confidence_level", 0)
            },
            "differentials": {
                "unique_to_m1": [
                    {
                        "player_name": p.get("name", "Unknown"),
                        "team": p.get("team", "Unknown"),
                        "position": p.get("position", "Unknown"),
                        "points": p.get("live_points", 0),
                        "strategic_value": p.get("strategic_value", 0),
                        "risk_score": p.get("risk_score", 0),
                        "reward_score": p.get("reward_score", 0)
                    } for p in differential.get("manager1_differentials", [])[:10]
                ],
                "unique_to_m2": [
                    {
                        "player_name": p.get("name", "Unknown"),
                        "team": p.get("team", "Unknown"),
                        "position": p.get("position", "Unknown"),
                        "points": p.get("live_points", 0),
                        "strategic_value": p.get("strategic_value", 0),
                        "risk_score": p.get("risk_score", 0),
                        "reward_score": p.get("reward_score", 0)
                    } for p in differential.get("manager2_differentials", [])[:10]
                ],
                "captain_differential": {
                    "exists": differential.get("captain_analysis", {}).get("same_captain", True) == False,
                    "swing_potential": differential.get("captain_analysis", {}).get("net_captain_advantage", 0)
                }
            },
            "predictions": {
                "win_probabilities": {
                    "manager1": prediction.get("manager1_win_probability", 0.5),
                    "manager2": prediction.get("manager2_win_probability", 0.5),
                    "draw": prediction.get("draw_probability", 0)
                } if prediction else {
                    "manager1": 0.5,
                    "manager2": 0.5,
                    "draw": 0
                },
                "expected_scores": {
                    "manager1": {
                        "total": prediction.get("manager1_expected_points", 0),
                        "confidence_interval": prediction.get("margin_confidence_interval_95", [0, 0])
                    },
                    "manager2": {
                        "total": prediction.get("manager2_expected_points", 0),
                        "confidence_interval": prediction.get("margin_confidence_interval_95", [0, 0])
                    }
                } if prediction else None
            },
            "insights": {
                "key_insights": summary.get("key_insights", [])[:5],
                "decisive_players": prediction.get("decisive_players_m1", []) + prediction.get("decisive_players_m2", [])
            },
            "metrics": {
                "score_difference": core.get("score_difference", 0),
                "total_psc_swing": differential.get("total_psc_swing", {}).get("net_advantage", 0),
                "differentials_count": len(core.get("differentials", []))
            }
        }
        
        return viz_data
    except Exception as e:
        logger.error(f"Error generating visualization data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/report/generate/h2h/{manager1_id}/{manager2_id}")
async def generate_h2h_report(
    manager1_id: int,
    manager2_id: int,
    league_id: int = TARGET_LEAGUE_ID,
    format: str = "json"
):
    """Generate H2H season report in specified format."""
    try:
        if not report_generator:
            raise HTTPException(status_code=503, detail="Report generator not initialized")
        
        # Validate format
        if format not in ["json", "csv", "pdf"]:
            raise HTTPException(status_code=400, detail="Invalid format. Must be json, csv, or pdf")
        
        # Generate report
        result = await report_generator.generate_h2h_season_report(
            manager1_id=manager1_id,
            manager2_id=manager2_id,
            league_id=league_id,
            output_format=format
        )
        
        # For JSON format, return the data directly
        if format == "json":
            return result["data"]
        
        # For other formats, return file info
        return {
            "status": "success",
            "file_path": result["file_path"],
            "format": format,
            "message": f"Report generated successfully. File saved at: {result['file_path']}"
        }
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/report/download/{file_path:path}")
async def download_report(file_path: str):
    """Download a generated report file."""
    try:
        from fastapi.responses import FileResponse
        import os
        
        # Security: ensure file is in reports directory
        full_path = os.path.abspath(file_path)
        reports_dir = os.path.abspath("reports")
        
        if not full_path.startswith(reports_dir):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="Report file not found")
        
        return FileResponse(
            path=full_path,
            filename=os.path.basename(full_path),
            media_type="application/octet-stream"
        )
        
    except Exception as e:
        logger.error(f"Error downloading report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Advanced Analytics Endpoints

@app.get("/api/analytics/v2/h2h/comprehensive/{manager1_id}/{manager2_id}")
async def get_comprehensive_h2h_analysis_v2(
    manager1_id: int,
    manager2_id: int,
    gameweek: Optional[int] = None,
    include_predictions: bool = True,
    include_patterns: bool = True,
    include_live: bool = True
):
    """
    Get comprehensive H2H analysis using all advanced analytics modules.
    Includes differential impact, historical patterns, predictions, transfer analysis,
    chip strategy, and live tracking.
    """
    try:
        if not advanced_analytics:
            raise HTTPException(status_code=503, detail="Advanced analytics service not initialized")
        
        analysis = await advanced_analytics.get_comprehensive_h2h_analysis(
            manager1_id,
            manager2_id,
            gameweek,
            include_predictions,
            include_patterns,
            include_live
        )
        
        return analysis
    except Exception as e:
        logger.error(f"Error in comprehensive H2H analysis v2: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/v2/differential-impact/{manager1_id}/{manager2_id}")
async def get_differential_impact_analysis(
    manager1_id: int,
    manager2_id: int,
    gameweek: Optional[int] = None
):
    """Get differential impact analysis between two managers."""
    try:
        if not advanced_analytics:
            raise HTTPException(status_code=503, detail="Advanced analytics service not initialized")
        
        analysis = await advanced_analytics.get_differential_analysis(
            manager1_id,
            manager2_id,
            gameweek
        )
        
        return analysis
    except Exception as e:
        logger.error(f"Error in differential impact analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/v2/transfer-roi/{manager_id}")
async def get_transfer_roi_analysis(manager_id: int):
    """Get comprehensive transfer ROI analysis for a manager."""
    try:
        if not advanced_analytics:
            raise HTTPException(status_code=503, detail="Advanced analytics service not initialized")
        
        analysis = await advanced_analytics.get_transfer_roi_analysis(manager_id)
        
        return analysis
    except Exception as e:
        logger.error(f"Error in transfer ROI analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/v2/live-match/{manager1_id}/{manager2_id}")
async def get_live_match_state(
    manager1_id: int,
    manager2_id: int,
    gameweek: Optional[int] = None
):
    """Get current live match state with provisional bonus and projections."""
    try:
        if not advanced_analytics:
            raise HTTPException(status_code=503, detail="Advanced analytics service not initialized")
        
        state = await advanced_analytics.get_live_match_state(
            manager1_id,
            manager2_id,
            gameweek
        )
        
        return state
    except Exception as e:
        logger.error(f"Error getting live match state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/analytics/live-tracking/{manager1_id}/{manager2_id}")
async def websocket_live_tracking(
    websocket: WebSocket,
    manager1_id: int,
    manager2_id: int
):
    """WebSocket endpoint for continuous live match tracking."""
    await websocket.accept()
    tracking_id = None
    
    try:
        # Define callback to send updates
        async def send_update(track_id: str):
            try:
                state = await advanced_analytics.get_live_match_state(
                    manager1_id,
                    manager2_id
                )
                await websocket.send_json({
                    "type": "live_update",
                    "data": state
                })
            except Exception as e:
                logger.error(f"Error sending live update: {e}")
        
        # Start tracking
        tracking_id = await advanced_analytics.start_live_tracking(
            manager1_id,
            manager2_id,
            send_update
        )
        
        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                break
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if tracking_id:
            await advanced_analytics.stop_live_tracking(tracking_id)
        try:
            await websocket.close()
        except:
            pass
