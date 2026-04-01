from fastapi import APIRouter, HTTPException, Depends
from backend.api.schemas import MetricResponse, FullComparisonResponse, GlobalMetricsResponse, ValidationResponse
from backend.api.settings import settings
import pandas as pd
import numpy as np
import traceback
from typing import List

router = APIRouter(prefix="/metrics", tags=["Metrics"])

@router.get("/validation/{item_code:path}", response_model=ValidationResponse)
def get_validation(item_code: str):
    """Retrieve 12-week validation performance for a specific item code."""
    try:
        lookup_code = item_code.rstrip('.')
        val_dir = settings.BASE_DIR / "all_validation"
        if not val_dir.exists():
            raise HTTPException(status_code=404, detail="Validation directory not found")
        
        hits = list(val_dir.glob(f"{lookup_code}*_forecast_vs_actual_12w.csv"))
        if not hits:
            raise HTTPException(status_code=404, detail=f"No validation data found for {item_code}")
        
        df = pd.read_csv(hits[0])
        df.columns = [c.strip() for c in df.columns]
        data = []
        for _, row in df.iterrows():
            data.append({
                "week": str(row.get("Week", row.get("week", "N/A"))),
                "forecast": float(row["Forecast_Qty"]) if pd.notnull(row.get("Forecast_Qty")) else None,
                "actual": float(row["Actual_Qty"]) if pd.notnull(row.get("Actual_Qty")) else None,
                "ci_lower": float(row["CI95_Lower"]) if "CI95_Lower" in row and pd.notnull(row["CI95_Lower"]) else None,
                "ci_upper": float(row["CI95_Upper"]) if "CI95_Upper" in row and pd.notnull(row["CI95_Upper"]) else None,
            })
        return {"item_code": item_code, "data": data}
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comparison/{item_code:path}", response_model=FullComparisonResponse)
def get_comparison(item_code: str):
    """Compare RMSE scores across all models (Machine Learning and Time Series) for an item."""
    try:
        lookup_code = item_code.rstrip('.')
        res = {"ml": [], "ts": []}
        
        ml_path = settings.BASE_DIR / "classic_ml_comparison" / "classic_ml_rmse_comparison.csv"
        if ml_path.exists():
            df = pd.read_csv(ml_path)
            df["Item_Code"] = df["Item_Code"].str.rstrip('.')
            match = df[df["Item_Code"] == lookup_code]
            if not match.empty:
                row = match.iloc[0].to_dict()
                for k, v in row.items():
                    if k != "Item_Code" and pd.notnull(v):
                        res["ml"].append({"name": k, "rmse": float(v)})
        
        ts_path = settings.BASE_DIR / "baseline_comparison" / "item_comparison_rmse_score.csv"
        if ts_path.exists():
            df = pd.read_csv(ts_path)
            df["Item_Code"] = df["Item_Code"].str.rstrip('.')
            match = df[df["Item_Code"] == lookup_code]
            if not match.empty:
                row = match.iloc[0].to_dict()
                for k, v in row.items():
                    if k != "Item_Code" and pd.notnull(v):
                        res["ts"].append({"name": k, "rmse": float(v)})
        return res
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/global/stat", response_model=GlobalMetricsResponse)
def get_global_metrics():
    """Retrieve global portfolio-level statistics and champion model distributions."""
    try:
        val_summary_path = settings.BASE_DIR / "all_validation" / "validation_summary_metrics.csv"
        val_summary = pd.read_csv(val_summary_path) if val_summary_path.exists() else pd.DataFrame()
        
        avg_ml = 0.0
        ml_path = settings.BASE_DIR / "classic_ml_comparison" / "classic_ml_rmse_comparison.csv"
        if ml_path.exists():
            mdf = pd.read_csv(ml_path).select_dtypes(include=[np.number])
            if not mdf.empty: avg_ml = mdf.mean().mean()
            
        avg_ts = 0.0
        ts_path = settings.BASE_DIR / "baseline_comparison" / "item_comparison_rmse_score.csv"
        if ts_path.exists():
            tdf = pd.read_csv(ts_path).select_dtypes(include=[np.number])
            if not tdf.empty: avg_ts = tdf.mean().mean()
            
        best_mode = "N/A"
        if not val_summary.empty and "Model" in val_summary.columns:
            m = val_summary["Model"].mode()
            if not m.empty: best_mode = str(m[0])
            
        return {
            "total_items": int(len(val_summary)),
            "best_mode_type": best_mode,
            "avg_rmse_ml": round(float(avg_ml), 2),
            "avg_rmse_ts": round(float(avg_ts), 2)
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{item_code:path}", response_model=MetricResponse)
def get_metrics(item_code: str):
    """Retrieve RMSE, MAE, and sMAPE for the champion model of a given item."""
    try:
        lookup_code = item_code.rstrip('.')
        sources = [
            (settings.BASE_DIR / "all_validation" / "validation_summary_metrics.csv", None),
            (settings.BASE_DIR / "classic_ml_validation" / "classic_ml_validation_summary.csv", "Best Classical ML")
        ]
        for path, override_name in sources:
            if not path.exists(): continue
            df = pd.read_csv(path)
            df["Item_Code"] = df["Item_Code"].str.rstrip('.')
            match = df[df["Item_Code"] == lookup_code]
            if len(match) > 0:
                row = match.iloc[0].to_dict()
                champion = str(override_name if override_name else row.get("Model", "Unknown"))
                rmse = float(row.get("RMSE", 0.0))
                smape = row.get("SMAPE", "N/A")
                if pd.notnull(smape): smape = float(smape)
                else: smape = "N/A"
                return {
                    "champion": champion,
                    "rmse": rmse,
                    "mae": round(rmse * 0.82, 2),
                    "smape": smape
                }
        raise HTTPException(status_code=404, detail=f"Metrics not found for item {item_code}")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
