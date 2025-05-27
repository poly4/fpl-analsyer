from fastapi import APIRouter, Depends, HTTPException
from app.services.live_data import LiveDataService

router = APIRouter()

@router.get("/gameweek/{gameweek}")
async def get_live_gameweek_data(gameweek: int, live_data_service: LiveDataService = Depends()):
    """Fetches live data for a specific gameweek."""
    # TODO: Implement fetching and returning live data using LiveDataService
    data = await live_data_service.get_live_gameweek_data(gameweek)
    if not data:
        raise HTTPException(status_code=404, detail=f"Live data not found for gameweek {gameweek}")
    return data

# Add other live data related endpoints as needed