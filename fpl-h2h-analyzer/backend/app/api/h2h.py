from fastapi import APIRouter, Depends, HTTPException
from app.services.h2h_analyzer import H2HAnalyzer
from app.services.live_data import LiveDataService # Might need live data service here
from app.services.enhanced_h2h_analyzer import EnhancedH2HAnalyzer
from app.services.analytics.predictive_engine import PredictiveEngine
from app.services.live_data_v2 import LiveDataService as LiveDataV2

router = APIRouter()

@router.get("/battle/{manager1_id}/{manager2_id}")
async def get_h2h_battle_analysis(
    manager1_id: int,
    manager2_id: int,
    gameweek: int, # Assuming gameweek is a query parameter
    h2h_analyzer: H2HAnalyzer = Depends(),
    live_data_service: LiveDataService = Depends() # Inject LiveDataService if needed
):
    """Provides analysis for an H2H battle between two managers for a specific gameweek."""
    # TODO: Fetch necessary data (e.g., manager picks, live data) and perform analysis
    live_data = await live_data_service.get_live_gameweek_data(gameweek)
    if not live_data:
         raise HTTPException(status_code=404, detail=f"Live data not available for gameweek {gameweek}")

    analysis_results = await h2h_analyzer.analyze_battle(manager1_id, manager2_id, gameweek, live_data)

    if not analysis_results:
        raise HTTPException(status_code=404, detail="Analysis could not be generated")

    return analysis_results

# Add other H2H related endpoints as needed (e.g., differentials)

@router.get("/prediction/{manager1_id}/{manager2_id}")
async def get_h2h_prediction(
    manager1_id: int,
    manager2_id: int,
    gameweek: int = 38,
    live_data_service: LiveDataV2 = Depends()
):
    """Get enhanced H2H match prediction with ML-powered insights."""
    try:
        # Initialize prediction engine
        predictive_engine = PredictiveEngine()
        
        # Fetch all required data
        manager1_history = await live_data_service.get_manager_history(manager1_id)
        manager2_history = await live_data_service.get_manager_history(manager2_id)
        manager1_picks = await live_data_service.get_manager_picks(manager1_id, gameweek)
        manager2_picks = await live_data_service.get_manager_picks(manager2_id, gameweek)
        bootstrap_data = await live_data_service.get_bootstrap_static()
        fixtures = await live_data_service.get_fixtures(gameweek)
        
        if not all([manager1_history, manager2_history, manager1_picks, manager2_picks]):
            raise HTTPException(status_code=404, detail="Could not fetch required manager data")
        
        # Generate prediction
        prediction_result = await predictive_engine.predict_match_outcome(
            manager1_id=manager1_id,
            manager2_id=manager2_id,
            manager1_history=manager1_history,
            manager2_history=manager2_history,
            current_gw_picks_m1=manager1_picks,
            current_gw_picks_m2=manager2_picks,
            fixture_data=fixtures,
            gameweek=gameweek,
            bootstrap_data=bootstrap_data
        )
        
        return {
            "status": "success",
            "gameweek": gameweek,
            "managers": {
                "manager1_id": manager1_id,
                "manager2_id": manager2_id
            },
            "prediction": prediction_result,
            "generated_at": prediction_result.get("generated_at", "2025-05-30T07:40:00Z")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.get("/enhanced/{manager1_id}/{manager2_id}")
async def get_enhanced_h2h_analysis(
    manager1_id: int,
    manager2_id: int,
    gameweek: int = 38,
    enhanced_analyzer: EnhancedH2HAnalyzer = Depends()
):
    """Get comprehensive enhanced H2H analysis including predictions."""
    try:
        analysis_result = await enhanced_analyzer.analyze_battle_comprehensive(
            manager1_id, manager2_id, gameweek
        )
        
        if not analysis_result:
            raise HTTPException(status_code=404, detail="Enhanced analysis could not be generated")
            
        return analysis_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enhanced analysis failed: {str(e)}")