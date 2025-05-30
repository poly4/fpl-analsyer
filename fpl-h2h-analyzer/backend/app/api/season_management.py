"""
API endpoints for season management and live features.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional, Any
import logging
from ..services.season_manager import SeasonManager, SeasonState, GameweekState
from ..services.live_data_v2 import LiveDataService
from ..websocket.live_updates import WebSocketManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/season", tags=["Season Management"])

# Global season manager instance (would be properly injected in production)
_season_manager: Optional[SeasonManager] = None
_websocket_manager: Optional[WebSocketManager] = None

def get_season_manager() -> SeasonManager:
    """Get or create season manager instance."""
    global _season_manager, _websocket_manager
    
    if _season_manager is None:
        live_data_service = LiveDataService()
        
        # Create WebSocket manager if not exists
        if _websocket_manager is None:
            _websocket_manager = WebSocketManager()
        
        _season_manager = SeasonManager(live_data_service, _websocket_manager)
    
    return _season_manager

def get_websocket_manager() -> WebSocketManager:
    """Get WebSocket manager instance."""
    global _websocket_manager
    
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    
    return _websocket_manager


@router.get("/status")
async def get_season_status(
    season_manager: SeasonManager = Depends(get_season_manager)
):
    """
    Get current season and gameweek status.
    
    Returns comprehensive information about the current season state,
    gameweek progress, and available features.
    """
    try:
        status = season_manager.get_status()
        season_info = season_manager.get_season_info()
        gameweek_info = season_manager.get_gameweek_info()
        
        return {
            "status": status,
            "season": {
                "id": season_info.id if season_info else None,
                "name": season_info.name if season_info else None,
                "state": season_info.state.value if season_info else "unknown",
                "current_gameweek": season_info.current_gameweek if season_info else 0,
                "total_gameweeks": season_info.total_gameweeks if season_info else 0,
                "start_date": season_info.start_date.isoformat() if season_info else None,
                "end_date": season_info.end_date.isoformat() if season_info else None,
                "active_chips": season_info.active_chips if season_info else [],
                "new_features": season_info.new_features if season_info else [],
                "rule_changes": season_info.rule_changes if season_info else []
            },
            "gameweek": {
                "id": gameweek_info.id if gameweek_info else 0,
                "name": gameweek_info.name if gameweek_info else None,
                "state": gameweek_info.state.value if gameweek_info else "unknown",
                "deadline_time": gameweek_info.deadline_time.isoformat() if gameweek_info else None,
                "fixtures_count": gameweek_info.fixtures_count if gameweek_info else 0,
                "finished_fixtures": gameweek_info.finished_fixtures if gameweek_info else 0,
                "average_score": gameweek_info.average_score if gameweek_info else None,
                "highest_score": gameweek_info.highest_score if gameweek_info else None,
                "most_captained": gameweek_info.most_captained if gameweek_info else None,
                "chip_plays": gameweek_info.chip_plays if gameweek_info else {}
            },
            "features": {
                "live_features_available": season_manager.is_live_features_enabled(),
                "live_tracking_active": status["features"]["live_tracking_active"],
                "price_tracking_active": status["features"]["price_change_tracking"],
                "websocket_available": _websocket_manager is not None
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting season status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/initialize")
async def initialize_season_manager(
    season_manager: SeasonManager = Depends(get_season_manager)
):
    """
    Initialize the season manager and start monitoring.
    
    This should be called once when the application starts to begin
    season monitoring and enable appropriate features.
    """
    try:
        success = await season_manager.initialize()
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to initialize season manager")
        
        status = season_manager.get_status()
        
        return {
            "message": "Season manager initialized successfully",
            "status": status
        }
        
    except Exception as e:
        logger.error(f"Error initializing season manager: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect-state")
async def detect_season_state(
    season_manager: SeasonManager = Depends(get_season_manager)
):
    """
    Manually trigger season state detection.
    
    Forces a refresh of the current season and gameweek state
    from the FPL API.
    """
    try:
        state = await season_manager.detect_season_state()
        
        return {
            "detected_state": state.value,
            "season_info": season_manager.get_season_info(),
            "gameweek_info": season_manager.get_gameweek_info(),
            "message": f"Season state detected as: {state.value}"
        }
        
    except Exception as e:
        logger.error(f"Error detecting season state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/live-features/enable")
async def enable_live_features(
    season_manager: SeasonManager = Depends(get_season_manager)
):
    """
    Manually enable live features.
    
    Enables live gameweek tracking, price change monitoring,
    and real-time updates during active seasons.
    """
    try:
        await season_manager.enable_live_features()
        
        return {
            "message": "Live features enabled",
            "live_features_enabled": season_manager.is_live_features_enabled(),
            "status": season_manager.get_status()["features"]
        }
        
    except Exception as e:
        logger.error(f"Error enabling live features: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/live-features/disable")
async def disable_live_features(
    season_manager: SeasonManager = Depends(get_season_manager)
):
    """
    Manually disable live features.
    
    Disables live tracking and real-time updates.
    Useful during off-season or for testing.
    """
    try:
        await season_manager.disable_live_features()
        
        return {
            "message": "Live features disabled",
            "live_features_enabled": season_manager.is_live_features_enabled(),
            "status": season_manager.get_status()["features"]
        }
        
    except Exception as e:
        logger.error(f"Error disabling live features: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gameweek/{gameweek_id}/status")
async def get_gameweek_status(
    gameweek_id: int,
    season_manager: SeasonManager = Depends(get_season_manager)
):
    """
    Get detailed status for a specific gameweek.
    
    Returns comprehensive information about the gameweek including
    fixtures, scores, and current state.
    """
    try:
        gameweek_info = season_manager.get_gameweek_info()
        
        if not gameweek_info or gameweek_info.id != gameweek_id:
            # Try to get info for requested gameweek (simplified implementation)
            return {
                "gameweek_id": gameweek_id,
                "error": "Gameweek not current or not available",
                "current_gameweek": gameweek_info.id if gameweek_info else None
            }
        
        return {
            "gameweek_id": gameweek_id,
            "name": gameweek_info.name,
            "state": gameweek_info.state.value,
            "deadline_time": gameweek_info.deadline_time.isoformat(),
            "fixtures": {
                "total": gameweek_info.fixtures_count,
                "finished": gameweek_info.finished_fixtures,
                "remaining": gameweek_info.fixtures_count - gameweek_info.finished_fixtures,
                "progress_percent": (gameweek_info.finished_fixtures / gameweek_info.fixtures_count * 100) if gameweek_info.fixtures_count > 0 else 0
            },
            "scores": {
                "average": gameweek_info.average_score,
                "highest": gameweek_info.highest_score
            },
            "popular_picks": {
                "most_captained": gameweek_info.most_captained,
                "most_transferred_in": gameweek_info.most_transferred_in
            },
            "chip_usage": gameweek_info.chip_plays,
            "is_live": gameweek_info.state == GameweekState.LIVE,
            "is_finished": gameweek_info.state in [GameweekState.COMPLETED, GameweekState.BONUS_AWARDED]
        }
        
    except Exception as e:
        logger.error(f"Error getting gameweek {gameweek_id} status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/websocket/status")
async def get_websocket_status(
    websocket_manager: WebSocketManager = Depends(get_websocket_manager)
):
    """
    Get WebSocket connection status and statistics.
    
    Returns information about active connections, rooms,
    and performance metrics.
    """
    try:
        stats = websocket_manager.get_statistics()
        health = websocket_manager.get_health_status()
        
        return {
            "websocket_available": True,
            "statistics": stats,
            "health": health,
            "room_management": {
                "total_rooms": stats["total_rooms"],
                "room_details": stats["room_details"]
            },
            "performance": {
                "average_latency_ms": stats["average_latency_ms"],
                "total_messages_sent": stats["total_messages_sent"],
                "total_messages_received": stats["total_messages_received"],
                "uptime_seconds": stats["uptime_seconds"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting WebSocket status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transition/new-season")
async def trigger_new_season_transition(
    season_manager: SeasonManager = Depends(get_season_manager)
):
    """
    Manually trigger new season transition.
    
    This is primarily for testing and administrative purposes.
    In production, season transitions should happen automatically.
    """
    try:
        await season_manager.handle_season_transition(SeasonState.PRE_SEASON)
        
        return {
            "message": "New season transition triggered",
            "new_state": SeasonState.PRE_SEASON.value,
            "status": season_manager.get_status()
        }
        
    except Exception as e:
        logger.error(f"Error triggering new season transition: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/features/availability")
async def get_feature_availability(
    season_manager: SeasonManager = Depends(get_season_manager)
):
    """
    Get availability of different features based on current season state.
    
    Returns which features are available and enabled based on
    the current season and gameweek state.
    """
    try:
        season_info = season_manager.get_season_info()
        gameweek_info = season_manager.get_gameweek_info()
        status = season_manager.get_status()
        
        # Determine feature availability
        features = {
            "live_tracking": {
                "available": season_info and season_info.state == SeasonState.ACTIVE,
                "enabled": status["features"]["live_tracking_active"],
                "description": "Real-time gameweek score tracking"
            },
            "price_tracking": {
                "available": season_info and season_info.state in [SeasonState.ACTIVE, SeasonState.PRE_SEASON],
                "enabled": status["features"]["price_change_tracking"],
                "description": "Player price change monitoring"
            },
            "websocket_updates": {
                "available": _websocket_manager is not None,
                "enabled": _websocket_manager is not None,
                "description": "Real-time WebSocket notifications"
            },
            "deadline_notifications": {
                "available": gameweek_info and gameweek_info.state in [GameweekState.DEADLINE_APPROACHING, GameweekState.SCHEDULED],
                "enabled": status["features"]["live_features_enabled"],
                "description": "Gameweek deadline reminders"
            },
            "live_scores": {
                "available": gameweek_info and gameweek_info.state == GameweekState.LIVE,
                "enabled": status["features"]["live_tracking_active"],
                "description": "Live player and match scores"
            },
            "h2h_tracking": {
                "available": True,  # Always available
                "enabled": True,
                "description": "Head-to-head battle tracking"
            },
            "advanced_analytics": {
                "available": True,  # Always available
                "enabled": True,
                "description": "Advanced performance metrics and insights"
            }
        }
        
        return {
            "season_state": season_info.state.value if season_info else "unknown",
            "gameweek_state": gameweek_info.state.value if gameweek_info else "unknown",
            "features": features,
            "summary": {
                "total_features": len(features),
                "available_features": sum(1 for f in features.values() if f["available"]),
                "enabled_features": sum(1 for f in features.values() if f["enabled"]),
                "live_features_active": any(f["enabled"] and "live" in f["description"].lower() for f in features.values())
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting feature availability: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_season_health(
    season_manager: SeasonManager = Depends(get_season_manager),
    websocket_manager: WebSocketManager = Depends(get_websocket_manager)
):
    """
    Get comprehensive health status of season management system.
    
    Returns health information for monitoring and alerting systems.
    """
    try:
        season_status = season_manager.get_status()
        ws_health = websocket_manager.get_health_status()
        
        # Determine overall health
        health_issues = []
        
        # Check season manager health
        if not season_status["tasks"]["season_monitor"]:
            health_issues.append("Season monitor task not running")
        
        # Check WebSocket health
        if ws_health["status"] != "healthy":
            health_issues.append(f"WebSocket manager status: {ws_health['status']}")
        
        # Check live features if season is active
        if (season_manager.is_season_active() and 
            not season_status["features"]["live_features_enabled"]):
            health_issues.append("Live features disabled during active season")
        
        overall_status = "healthy" if not health_issues else "degraded"
        
        return {
            "status": overall_status,
            "timestamp": season_status.get("last_updated"),
            "components": {
                "season_manager": {
                    "status": "healthy" if season_status["tasks"]["season_monitor"] else "unhealthy",
                    "season_state": season_status["season"]["state"],
                    "current_gameweek": season_status["season"]["current_gameweek"]
                },
                "websocket_manager": {
                    "status": ws_health["status"],
                    "active_connections": ws_health["active_connections"],
                    "utilization_percent": ws_health["utilization_percent"]
                },
                "live_features": {
                    "status": "enabled" if season_status["features"]["live_features_enabled"] else "disabled",
                    "tracking_active": season_status["features"]["live_tracking_active"],
                    "price_tracking": season_status["features"]["price_change_tracking"]
                }
            },
            "issues": health_issues,
            "metrics": {
                "active_websocket_connections": ws_health["active_connections"],
                "season_uptime": "unknown",  # Would track from initialization
                "background_tasks_running": sum(1 for task in season_status["tasks"].values() if task)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting season health: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": None
        }