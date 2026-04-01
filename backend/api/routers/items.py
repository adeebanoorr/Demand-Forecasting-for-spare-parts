from fastapi import APIRouter, HTTPException, Depends
from backend.api.schemas import HealthCheck
from backend.api.settings import settings
import pandas as pd
import traceback
from typing import List

router = APIRouter(prefix="/items", tags=["Items"])

@router.get("/health", response_model=HealthCheck)
def health_check():
    """Check if the API service is alive and healthy."""
    return {"status": "ok", "message": "API is reachable"}

@router.get("", response_model=List[str])
def get_items():
    """Retrieve a list of all item codes that have forecast data available."""
    try:
        forecast_dir = settings.BASE_DIR / "all_forecast"
        if not forecast_dir.exists():
            return []
        files = list(forecast_dir.glob("*_final_forecast.csv"))
        items = set()
        for f in files:
            name = f.name.split("_")[0]
            items.add(name)
        return sorted(list(items))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
