from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import redis.asyncio as redis
import os
import json
import asyncio
import uuid
from typing import Optional, List, Dict, Any

from .services.live_data import LiveDataService
from .services.h2h_analyzer import H2HAnalyzer
from .services.enhanced_h2h_analyzer import EnhancedH2HAnalyzer
from .services.analytics import DifferentialAnalyzer, PredictiveEngine, ChipAnalyzer, PatternRecognition
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
redis_client = None
cache_service = None
websocket_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global live_data_service, h2h_analyzer, enhanced_h2h_analyzer, differential_analyzer, predictive_engine, chip_analyzer, pattern_recognizer, redis_client, cache_service, websocket_manager
    
    try:
        # Initialize Redis connection
        redis_client = await redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        
        # Initialize cache service with Redis
        cache_service = CacheService(redis_client)
        
        # Initialize WebSocket manager
        websocket_manager = WebSocketManager(max_connections=1000, heartbeat_interval=30)
        await websocket_manager.start_background_tasks()
        
        # Initialize services
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
            gameweek = await live_data_service.get_current_gameweek()
        
        # Get H2H matches for the gameweek
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
                    # Add match with original scores if live calculation fails
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
                        "completed": match.get('finished', False),
                        "error": "Live scores unavailable"
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
            
        analysis = await enhanced_h2h_analyzer.get_quick_differential_analysis(
            manager1_id,
            manager2_id,
            gameweek
        )
        
        return analysis
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
        
        # Generate prediction
        prediction = enhanced_h2h_analyzer.predictive_engine.predict_h2h_match(
            manager1_picks,
            manager2_picks,
            gameweek
        )
        
        return {
            "gameweek": gameweek,
            "win_probability": {
                "manager1": prediction.win_probability_m1,
                "manager2": prediction.win_probability_m2,
                "draw": prediction.draw_probability
            },
            "expected_scores": {
                "manager1": prediction.manager1_prediction.expected_total_points,
                "manager2": prediction.manager2_prediction.expected_total_points
            },
            "expected_margin": prediction.expected_margin,
            "confidence_level": prediction.confidence_level,
            "decisive_players": [
                {
                    "player": p[0].player_name,
                    "expected_points": p[0].expected_points,
                    "impact_score": p[1]
                } for p in prediction.decisive_players[:5]
            ]
        }
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
            
        # Analyze chip strategy
        strategy = await enhanced_h2h_analyzer.chip_analyzer.analyze_chip_strategy(
            manager_info,
            manager_history,
            manager_picks,
            opponent_data,
            horizon
        )
        
        # Get summary
        summary = enhanced_h2h_analyzer.chip_analyzer.get_chip_summary(strategy) if hasattr(enhanced_h2h_analyzer.chip_analyzer, 'get_chip_summary') else None
        
        return {
            "manager_id": manager_id,
            "current_gameweek": current_gw,
            "chips_available": {k.value: v for k, v in strategy.chips_available.items()},
            "chips_used": {k.value: v for k, v in strategy.chips_used.items()},
            "immediate_recommendation": {
                "chip": strategy.immediate_recommendation.chip_type.value,
                "gameweek": strategy.immediate_recommendation.recommended_gameweek,
                "expected_gain": strategy.immediate_recommendation.expected_gain,
                "confidence": strategy.immediate_recommendation.confidence_score,
                "reasons": strategy.immediate_recommendation.reasons
            } if strategy.immediate_recommendation else None,
            "future_recommendations": [
                {
                    "chip": rec.chip_type.value,
                    "gameweek": rec.recommended_gameweek,
                    "expected_gain": rec.expected_gain
                } for rec in strategy.future_recommendations
            ],
            "summary": summary
        }
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
        
        return {
            "manager_id": manager_id,
            "transfer_patterns": {
                "avg_transfers_per_gw": patterns.avg_transfers_per_gw,
                "hit_frequency": patterns.hit_frequency,
                "avg_hit_size": patterns.avg_hit_size
            },
            "captain_patterns": {
                "consistency": patterns.captain_consistency,
                "risk_profile": patterns.captain_risk_profile,
                "differential_rate": patterns.differential_captain_rate
            },
            "performance_patterns": {
                "consistency_score": patterns.consistency_score,
                "clutch_performance": patterns.clutch_performance,
                "strong_periods": patterns.strong_periods,
                "weak_periods": patterns.weak_periods
            },
            "h2h_patterns": {
                "record": patterns.h2h_record,
                "avg_margin_win": patterns.avg_margin_win,
                "avg_margin_loss": patterns.avg_margin_loss,
                "comeback_rate": patterns.comeback_rate
            }
        }
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
            
        # Get comprehensive analysis
        analysis = await enhanced_h2h_analyzer.analyze_battle_comprehensive(
            manager1_id,
            manager2_id,
            gameweek,
            include_predictions=True,
            include_patterns=False
        )
        
        # Format for visualization
        viz_data = {
            "overview": {
                "gameweek": analysis.gameweek,
                "manager1": {
                    "id": manager1_id,
                    "name": analysis.manager1_name,
                    "score": analysis.current_scores["manager1"]["total"]
                },
                "manager2": {
                    "id": manager2_id,
                    "name": analysis.manager2_name,
                    "score": analysis.current_scores["manager2"]["total"]
                },
                "advantage_score": analysis.advantage_score,
                "confidence": analysis.confidence_level
            },
            "differentials": {
                "unique_to_m1": [
                    {
                        "player_name": p.player_name,
                        "team": p.team_name,
                        "position": p.position,
                        "points": p.current_points,
                        "strategic_value": p.strategic_value,
                        "risk_score": p.risk_score,
                        "reward_score": p.reward_score
                    } for p in analysis.differential_analysis.unique_to_manager1[:10]
                ],
                "unique_to_m2": [
                    {
                        "player_name": p.player_name,
                        "team": p.team_name,
                        "position": p.position,
                        "points": p.current_points,
                        "strategic_value": p.strategic_value,
                        "risk_score": p.risk_score,
                        "reward_score": p.reward_score
                    } for p in analysis.differential_analysis.unique_to_manager2[:10]
                ],
                "captain_differential": {
                    "exists": analysis.differential_analysis.captain_differential is not None,
                    "swing_potential": analysis.differential_analysis.captain_swing_potential
                }
            },
            "predictions": {
                "win_probabilities": {
                    "manager1": analysis.prediction.win_probability_m1,
                    "manager2": analysis.prediction.win_probability_m2,
                    "draw": analysis.prediction.draw_probability
                } if analysis.prediction else None,
                "expected_scores": {
                    "manager1": {
                        "total": analysis.prediction.manager1_prediction.expected_total_points,
                        "confidence_interval": analysis.prediction.manager1_prediction.confidence_interval
                    },
                    "manager2": {
                        "total": analysis.prediction.manager2_prediction.expected_total_points,
                        "confidence_interval": analysis.prediction.manager2_prediction.confidence_interval
                    }
                } if analysis.prediction else None
            },
            "insights": {
                "battlegrounds": analysis.key_battlegrounds[:5],
                "opportunities": analysis.opportunity_windows[:5],
                "risks": analysis.risk_assessment["key_risks"][:5] if "key_risks" in analysis.risk_assessment else []
            },
            "metrics": {
                "volatility_index": analysis.volatility_index,
                "strategic_complexity": analysis.strategic_complexity,
                "defensive_coverage": analysis.differential_analysis.defensive_coverage
            }
        }
        
        return viz_data
    except Exception as e:
        logger.error(f"Error generating visualization data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
