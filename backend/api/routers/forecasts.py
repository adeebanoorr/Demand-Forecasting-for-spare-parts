from fastapi import APIRouter, HTTPException, Depends
from backend.api.schemas import ForecastResponse, ComparisonResponse, MSTLEntry, AggregateForecastEntry
from backend.api.settings import settings
import pandas as pd
import traceback
from typing import List, Optional
from pathlib import Path

router = APIRouter(prefix="/forecast", tags=["Forecasts"])

def _fetch_forecast_data(item_code: str, model_name: str):
    lookup_code = item_code.rstrip('.')
    actual_model = str(model_name)
    val_file = None
    
    try:
        if model_name.lower() == "best":
            val_summary_path = settings.BASE_DIR / "all_validation" / "validation_summary_metrics.csv"
            if val_summary_path.exists():
                val_summary = pd.read_csv(val_summary_path)
                val_summary["Item_Code"] = val_summary["Item_Code"].str.rstrip('.')
                match = val_summary[val_summary["Item_Code"] == lookup_code]
                
                if len(match) > 0:
                    actual_model = str(match["Model"].iloc[0])
                    folders = ["all_validation", "classic_ml_validation", "autosarima_validation"]
                    for folder in folders:
                        dir_path = settings.BASE_DIR / folder
                        if not dir_path.exists(): continue
                        hits = list(dir_path.glob(f"{lookup_code}*_{actual_model}_*.csv"))
                        if not hits:
                            hits = list(dir_path.glob(f"{lookup_code}*validation_vs_actual.csv"))
                        if hits:
                            val_file = hits[0]
                            break
        
        elif model_name.lower() == "best_ml":
            actual_model = "Best Classical ML"
            dir_path = settings.BASE_DIR / "classic_ml_validation"
            if dir_path.exists():
                hits = list(dir_path.glob(f"{lookup_code}*validation_vs_actual.csv"))
                if hits: val_file = hits[0]
            
        elif model_name.lower() == "auto_sarima":
            actual_model = "Auto SARIMA"
            dir_path = settings.BASE_DIR / "autosarima_validation"
            if dir_path.exists():
                hits = list(dir_path.glob(f"{lookup_code}*validation_vs_actual.csv"))
                if hits: val_file = hits[0]
            
        elif model_name.lower() == "best_ts":
            ts_path = settings.BASE_DIR / "baseline_comparison" / "item_comparison_rmse_score.csv"
            if ts_path.exists():
                ts_df = pd.read_csv(ts_path)
                ts_df["Item_Code"] = ts_df["Item_Code"].str.rstrip('.')
                match = ts_df[ts_df["Item_Code"] == lookup_code]
                
                if len(match) > 0:
                    row_data = match.iloc[0].to_dict()
                    item_only = {k: v for k, v in row_data.items() if k != "Item_Code" and isinstance(v, (int, float))}
                    best_col = min(item_only, key=item_only.get) if item_only else "Prophet"
                    actual_model = str(best_col)
                    hits = list((settings.BASE_DIR / "all_validation").glob(f"{lookup_code}*_{actual_model}_*.csv"))
                    if hits: val_file = hits[0]
        
        else:
            actual_model = str(model_name)
            search_name = model_name.replace(" ", "")
            patterns = [
                (settings.BASE_DIR / "all_validation", f"{lookup_code}*_{search_name}_*.csv"),
                (settings.BASE_DIR / "all_validation" / "variants", f"{lookup_code}_validation_{search_name}.csv"),
                (settings.BASE_DIR / "classic_ml_validation" / "variants", f"{lookup_code}_validation_{search_name}.csv"),
            ]
            for v_dir, pattern in patterns:
                if v_dir.exists():
                    hits = list(v_dir.glob(pattern))
                    if hits:
                        val_file = hits[0]
                        break
        
        if val_file is None:
             for code in [lookup_code, item_code]:
                 forecast_dir = settings.BASE_DIR / "all_forecast"
                 if forecast_dir.exists():
                     hits = list(forecast_dir.glob(f"{code}*_final_forecast.csv"))
                     if hits:
                         val_file = hits[0]
                         break
                         
        if not val_file or not val_file.exists():
             return None
             
        df = pd.read_csv(val_file)
        df = df.loc[:, ~df.columns.duplicated()].copy()
        
        col_map = {
            "week": ["Week", "Week_Index", "Date", "week"],
            "forecast": ["Forecast_Qty", "Predicted_Qty", "forecast"],
            "actual": ["Actual_Qty", "actual"],
            "ci_lower": ["CI95_Lower", "CI_Lower", "CI80_Lower", "ci_lower"],
            "ci_upper": ["CI95_Upper", "CI_Upper", "CI80_Upper", "ci_upper"]
        }
        
        data = []
        for _, row_series in df.iterrows():
            row = row_series.to_dict()
            entry = {}
            for target, sources in col_map.items():
                val = None
                for src in sources:
                    if src in row:
                        val = row[src]
                        break
                if target == "week":
                    entry[target] = str(val) if val is not None else "N/A"
                else:
                    entry[target] = float(val) if val is not None and pd.notnull(val) else None
            data.append(entry)
        return {"model": actual_model, "data": data}
    except Exception as e:
        print(f"Error fetching {model_name} for {item_code}: {e}")
        return None

@router.get("/aggregate", response_model=List[AggregateForecastEntry])
def get_portfolio_forecast():
    """Get summarized forecast data across all items in the portfolio."""
    try:
        forecast_dir = settings.BASE_DIR / "all_forecast"
        if not forecast_dir.exists():
            return []
        files = list(forecast_dir.glob("*_final_forecast.csv"))
        agg_forecast = [0.0] * 12
        week_labels = [None] * 12
        for f in files:
            df = pd.read_csv(f)
            f_col = next((c for c in ["Forecast_Qty", "Predicted_Qty", "forecast", "forecast_qty"] if c in df.columns), None)
            w_col = next((c for c in ["Week", "Week_Index", "Date", "week", "Week_End"] if c in df.columns), None)
            if f_col:
                for idx, row in df.iterrows():
                    if idx < 12:
                        qty = float(row[f_col]) if pd.notnull(row[f_col]) else 0.0
                        agg_forecast[idx] += qty
                        if week_labels[idx] is None and w_col:
                            week_labels[idx] = str(row[w_col])
        result = [{"week": week_labels[i] if week_labels[i] else f"Week {i+1}", "forecast": round(agg_forecast[i], 2)} for i in range(12)]
        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comparison/{item_code:path}", response_model=ComparisonResponse)
def get_forecast_comparison(item_code: str):
    """Fetch comparative forecast data across Champion, Best ML, and Trend-Seasonal models."""
    try:
        champion = _fetch_forecast_data(item_code, "Best")
        ml = _fetch_forecast_data(item_code, "Best_ML")
        ts = _fetch_forecast_data(item_code, "Best_TS")
        
        if not champion and not ml and not ts:
            raise HTTPException(status_code=404, detail=f"No forecast data available for {item_code}")
            
        base = champion or ml or ts
        merged = []
        for i, entry in enumerate(base['data']):
            week_entry = {
                "week": entry['week'],
                "actual": entry['actual'],
                "champion": champion['data'][i]['forecast'] if champion and i < len(champion['data']) else None,
                "ml": ml['data'][i]['forecast'] if (ml and i < len(ml['data'])) else None,
                "ts": ts['data'][i]['forecast'] if (ts and i < len(ts['data'])) else None
            }
            if champion and i < len(champion['data']):
                week_entry["ci_lower"] = champion['data'][i].get("ci_lower")
                week_entry["ci_upper"] = champion['data'][i].get("ci_upper")
                
            merged.append(week_entry)
            
        return {
            "item": item_code,
            "models": {
                "champion": champion['model'] if champion else "Champion",
                "ml": ml['model'] if ml else "Best ML",
                "ts": ts['model'] if ts else "Best TS"
            },
            "data": merged
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mstl/{item_code:path}", response_model=List[MSTLEntry])
def get_mstl(item_code: str):
    """Compute and return MSTL (Multiple Seasonal-Trend decomposition) components."""
    from statsmodels.tsa.seasonal import MSTL
    try:
        data_path = settings.BASE_DIR / "data_preparation" / "train_dataset.csv"
        if not data_path.exists():
             raise HTTPException(status_code=404, detail="Dataset not found")
        
        df = pd.read_csv(data_path, parse_dates=["OA_DATE"])
        lookup_code = item_code.rstrip('.')
        df["ITEM_CODE"] = df["ITEM_CODE"].str.rstrip('.')
        df = df[df["ITEM_CODE"] == lookup_code].copy()
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data for item {item_code}")
        
        weekly = df.set_index("OA_DATE").resample("W")["QTY"].sum()
        full_idx = pd.date_range(weekly.index.min(), weekly.index.max(), freq="W")
        weekly = weekly.reindex(full_idx, fill_value=0)
        weekly.index.name = "week"
        weekly = weekly.reset_index()
        
        if len(weekly) < 8:
            raise HTTPException(status_code=422, detail="Not enough data for decomposition")
        
        n = len(weekly)
        period = 52 if n >= 104 else (26 if n >= 52 else max(4, n // 4))
        try:
            mstl = MSTL(weekly["QTY"], periods=[period]).fit()
        except Exception:
            period = max(4, n // 6)
            mstl = MSTL(weekly["QTY"], periods=[period]).fit()
            
        seasonal_raw = mstl.seasonal
        seasonal_vals = seasonal_raw.iloc[:, 0].round(2) if isinstance(seasonal_raw, pd.DataFrame) else seasonal_raw.round(2)
        
        result = pd.DataFrame({
            "week": weekly["week"].dt.strftime("%Y-%m-%d"),
            "observed": weekly["QTY"].round(2),
            "trend": mstl.trend.round(2),
            "seasonal": seasonal_vals,
            "residual": mstl.resid.round(2),
        })
        return result.to_dict(orient="records")
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{item_code:path}/{model_name}", response_model=ForecastResponse)
def get_forecast(item_code: str, model_name: str):
    """Retrieve detailed forecast data for a specific item code and forecasting model."""
    res = _fetch_forecast_data(item_code, model_name)
    if not res:
        raise HTTPException(status_code=404, detail=f"Forecast not found for {item_code}")
    return res
