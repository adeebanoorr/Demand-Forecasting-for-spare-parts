from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from backend.api.settings import settings
import traceback

router = APIRouter(prefix="/download", tags=["Downloads"])

@router.get("/forecast/{item_code}")
def download_forecast(item_code: str):
    """Download the final forecast CSV file for a specific item code."""
    try:
        lookup_code = item_code.rstrip('.')
        forecast_dir = settings.BASE_DIR / "all_forecast"
        if not forecast_dir.exists():
            raise HTTPException(status_code=404, detail="Forecast directory not found")
        
        hits = list(forecast_dir.glob(f"{lookup_code}*_final_forecast.csv"))
        if not hits:
            raise HTTPException(status_code=404, detail=f"Forecast file not found for {item_code}")
        
        return FileResponse(path=hits[0], filename=hits[0].name, media_type='text/csv')
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/validation/{item_code}")
def download_validation(item_code: str):
    """Download the 12-week validation comparison CSV file for a specific item code."""
    try:
        lookup_code = item_code.rstrip('.')
        val_dir = settings.BASE_DIR / "all_validation"
        if not val_dir.exists():
             raise HTTPException(status_code=404, detail="Validation directory not found")
             
        hits = list(val_dir.glob(f"{lookup_code}*_forecast_vs_actual_12w.csv"))
        if not hits:
            raise HTTPException(status_code=404, detail=f"Validation file not found for {item_code}")
        
        return FileResponse(path=hits[0], filename=hits[0].name, media_type='text/csv')
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comparison/summary")
def download_comparison():
    """Download the global validation summary metrics CSV file."""
    try:
        path = settings.BASE_DIR / "all_validation" / "validation_summary_metrics.csv"
        if not path.exists():
            raise HTTPException(status_code=404, detail="Comparison summary file not found")
        
        return FileResponse(path=path, filename="model_comparison_summary.csv", media_type='text/csv')
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
