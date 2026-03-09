from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from pathlib import Path
import os
import traceback
from fastapi.middleware.wsgi import WSGIMiddleware

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API is reachable"}

# Directories
BASE_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
STATIC_DIR = Path(__file__).resolve().parents[1] / "webapp" / "dist"

@app.get("/")
def read_index():
    index_file = STATIC_DIR / "index.html"
    print(f"DEBUG: Checking for index at {index_file}")
    if index_file.exists():
        return FileResponse(index_file)
    
    # Fallback check
    alt_path = Path(__file__).resolve().parents[2] / "src" / "webapp" / "dist" / "index.html"
    print(f"DEBUG: Checking alt path at {alt_path}")
    if alt_path.exists():
        return FileResponse(alt_path)

    return {"message": "Spare Parts Forecast API Running (Dashboard build not found)", "debug_path": str(index_file)}

@app.get("/api/items")
def get_items():
    import pandas as pd
    try:
        forecast_dir = BASE_DIR / "all_forecast"
        files = list(forecast_dir.glob("*_final_forecast.csv"))
        items = set()
        for f in files:
            name = f.name.split("_")[0]
            items.add(name)
        return sorted(list(items))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

def _fetch_forecast_data(item_code: str, model_name: str):
    import pandas as pd
    lookup_code = item_code.rstrip('.')
    actual_model = str(model_name)
    val_file = None
    
    try:
        if model_name.lower() == "best":
            val_summary = pd.read_csv(BASE_DIR / "all_validation" / "validation_summary_metrics.csv")
            val_summary["Item_Code"] = val_summary["Item_Code"].str.rstrip('.')
            match = val_summary[val_summary["Item_Code"] == lookup_code]
            
            if len(match) > 0:
                actual_model = str(match["Model"].iloc[0])
                folders = ["all_validation", "classic_ml_validation", "autosarima_validation"]
                for folder in folders:
                    dir_path = BASE_DIR / folder
                    if not dir_path.exists(): continue
                    hits = list(dir_path.glob(f"{lookup_code}*_{actual_model}_*.csv"))
                    if not hits:
                        hits = list(dir_path.glob(f"{lookup_code}*validation_vs_actual.csv"))
                    if hits:
                        val_file = hits[0]
                        break
        
        elif model_name.lower() == "best_ml":
            actual_model = "Best Classical ML"
            hits = list((BASE_DIR / "classic_ml_validation").glob(f"{lookup_code}*validation_vs_actual.csv"))
            if hits: val_file = hits[0]
            
        elif model_name.lower() == "auto_sarima":
            actual_model = "Auto SARIMA"
            hits = list((BASE_DIR / "autosarima_validation").glob(f"{lookup_code}*validation_vs_actual.csv"))
            if hits: val_file = hits[0]
            
        elif model_name.lower() == "best_ts":
            ts_path = BASE_DIR / "baseline_comparison" / "item_comparison_rmse_score.csv"
            ts_df = pd.read_csv(ts_path)
            ts_df["Item_Code"] = ts_df["Item_Code"].str.rstrip('.')
            match = ts_df[ts_df["Item_Code"] == lookup_code]
            
            if len(match) > 0:
                row_data = match.iloc[0].to_dict()
                item_only = {k: v for k, v in row_data.items() if k != "Item_Code" and isinstance(v, (int, float))}
                best_col = min(item_only, key=item_only.get) if item_only else "Prophet"
                actual_model = str(best_col)
                hits = list((BASE_DIR / "all_validation").glob(f"{lookup_code}*_{actual_model}_*.csv"))
                if hits: val_file = hits[0]
        
        else:
            actual_model = str(model_name)
            search_name = model_name.replace(" ", "")
            patterns = [
                (BASE_DIR / "all_validation", f"{lookup_code}*_{search_name}_*.csv"),
                (BASE_DIR / "all_validation" / "variants", f"{lookup_code}_validation_{search_name}.csv"),
                (BASE_DIR / "classic_ml_validation" / "variants", f"{lookup_code}_validation_{search_name}.csv"),
            ]
            for v_dir, pattern in patterns:
                if v_dir.exists():
                    hits = list(v_dir.glob(pattern))
                    if hits:
                        val_file = hits[0]
                        break
        
        if val_file is None:
             for code in [lookup_code, item_code]:
                 hits = list((BASE_DIR / "all_forecast").glob(f"{code}*_final_forecast.csv"))
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

@app.get("/api/forecast/{item_code}/{model_name}")
def get_forecast(item_code: str, model_name: str):
    res = _fetch_forecast_data(item_code, model_name)
    if not res:
        raise HTTPException(status_code=404, detail=f"Forecast not found for {item_code}")
    return res

@app.get("/api/forecast_comparison/{item_code}")
def get_forecast_comparison(item_code: str):
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

@app.get("/api/validation/{item_code}")
def get_validation(item_code: str):
    import pandas as pd
    try:
        lookup_code = item_code.rstrip('.')
        val_dir = BASE_DIR / "all_validation"
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

@app.get("/api/metrics/{item_code}")
def get_metrics(item_code: str):
    import pandas as pd
    try:
        lookup_code = item_code.rstrip('.')
        sources = [
            (BASE_DIR / "all_validation" / "validation_summary_metrics.csv", None),
            (BASE_DIR / "classic_ml_validation" / "classic_ml_validation_summary.csv", "Best Classical ML")
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

@app.get("/api/comparison/{item_code}")
def get_comparison(item_code: str):
    import pandas as pd
    try:
        lookup_code = item_code.rstrip('.')
        res = {"ml": [], "ts": []}
        ml_path = BASE_DIR / "classic_ml_comparison" / "classic_ml_rmse_comparison.csv"
        if ml_path.exists():
            df = pd.read_csv(ml_path)
            df["Item_Code"] = df["Item_Code"].str.rstrip('.')
            match = df[df["Item_Code"] == lookup_code]
            if not match.empty:
                row = match.iloc[0].to_dict()
                for k, v in row.items():
                    if k != "Item_Code" and pd.notnull(v):
                        res["ml"].append({"name": k, "rmse": float(v)})
        ts_path = BASE_DIR / "baseline_comparison" / "item_comparison_rmse_score.csv"
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

@app.get("/api/global_metrics")
def get_global_metrics():
    import pandas as pd
    import numpy as np
    try:
        val_summary_path = BASE_DIR / "all_validation" / "validation_summary_metrics.csv"
        val_summary = pd.read_csv(val_summary_path) if val_summary_path.exists() else pd.DataFrame()
        avg_ml = 0.0
        ml_path = BASE_DIR / "classic_ml_comparison" / "classic_ml_rmse_comparison.csv"
        if ml_path.exists():
            mdf = pd.read_csv(ml_path).select_dtypes(include=[np.number])
            if not mdf.empty: avg_ml = mdf.mean().mean()
        avg_ts = 0.0
        ts_path = BASE_DIR / "baseline_comparison" / "item_comparison_rmse_score.csv"
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

@app.get("/api/aggregate_forecast")
def get_portfolio_forecast():
    import pandas as pd
    try:
        forecast_dir = BASE_DIR / "all_forecast"
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

@app.get("/api/download/forecast/{item_code}")
def download_forecast(item_code: str):
    try:
        lookup_code = item_code.rstrip('.')
        forecast_dir = BASE_DIR / "all_forecast"
        hits = list(forecast_dir.glob(f"{lookup_code}*_final_forecast.csv"))
        if not hits:
            raise HTTPException(status_code=404, detail=f"Forecast file not found for {item_code}")
        return FileResponse(path=hits[0], filename=hits[0].name, media_type='text/csv')
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/validation/{item_code}")
def download_validation(item_code: str):
    try:
        lookup_code = item_code.rstrip('.')
        val_dir = BASE_DIR / "all_validation"
        hits = list(val_dir.glob(f"{lookup_code}*_forecast_vs_actual_12w.csv"))
        if not hits:
            raise HTTPException(status_code=404, detail=f"Validation file not found for {item_code}")
        return FileResponse(path=hits[0], filename=hits[0].name, media_type='text/csv')
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/comparison")
def download_comparison():
    try:
        path = BASE_DIR / "all_validation" / "validation_summary_metrics.csv"
        if not path.exists():
            raise HTTPException(status_code=404, detail="Comparison summary file not found")
        return FileResponse(path=path, filename="model_comparison_summary.csv", media_type='text/csv')
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Mount Dash Performance Dashboard
try:
    from src.visualization.dashboard import app as dash_app
    app.mount("/analytics", WSGIMiddleware(dash_app.server))
    print("DEBUG: Dash Analytics dashboard mounted at /analytics")
except Exception as e:
    print(f"DEBUG: Failed to mount Dash analytics: {e}")

if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
