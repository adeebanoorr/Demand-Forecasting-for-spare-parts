import warnings
warnings.filterwarnings("ignore")

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib
import pickle
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from prophet import Prophet

# -------------------------------------------------
# 0. Project root & Mapping
# -------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

# Comparison path
COMPARISON_PATH = PROJECT_ROOT / "data" / "processed" / "baseline_comparison" / "item_comparison_rmse_score.csv"

def get_champion_models():
    """Load champion models from the comparison results."""
    if not COMPARISON_PATH.exists():
        print(f"Warning: Comparison file {COMPARISON_PATH} not found. Using defaults.")
        # Fallback to a few known good ones if file missing
        return {
            "082.03.110.50.": "AR",
            "082.04.030.50.": "AR",
            "082.08.000.50.": "Prophet"
        }

    try:
        comp_df = pd.read_csv(COMPARISON_PATH, index_col="Item_Code")
        best_models = comp_df.idxmin(axis=1).to_dict()
        print(f"Loaded {len(best_models)} champion models from baseline comparison.")
        return best_models
    except Exception as e:
        print(f"Error loading comparison file: {e}")
        return {}

# -------------------------------------------------
# 1. Paths
# -------------------------------------------------
TRAIN_PATH = PROJECT_ROOT / "data" / "processed" / "data_preparation" / "train_dataset.csv"
TEST_PATH = PROJECT_ROOT / "data" / "processed" / "data_preparation" / "test_dataset.csv"

# Updated model directory as per validation template
MODEL_DIR = PROJECT_ROOT / "models" / "all_forecast"
FORECAST_DIR = PROJECT_ROOT / "data" / "processed" / "all_forecast"
FIG_DIR = PROJECT_ROOT / "reports" / "figures" / "all_forecast"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
FORECAST_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

FORECAST_WEEKS = 12

# -------------------------------------------------
# 2. Load Data
# -------------------------------------------------
print("Loading datasets...")
train_df = pd.read_csv(TRAIN_PATH)
test_df = pd.read_csv(TEST_PATH)

full_df = pd.concat([train_df, test_df], ignore_index=True)
full_df["OA_DATE"] = pd.to_datetime(full_df["OA_DATE"], errors="coerce")
full_df = full_df.dropna(subset=["OA_DATE", "QTY"])

# -------------------------------------------------
# 3. Main Pipeline loop
# -------------------------------------------------
best_models = get_champion_models()
print(f"Starting Training & Forecasting for {len(best_models)} items...")

for item_code, model_type in best_models.items():
    print(f"\n>>> Item: {item_code} | Using Model: {model_type}")
    
    item_df = full_df[full_df["ITEM_CODE"] == item_code].sort_values("OA_DATE")
    
    # Weekly Resampling (MON) as per validation template
    ts = (
        item_df.set_index("OA_DATE")["QTY"]
        .resample("W-MON")
        .sum()
        .fillna(0)
    )
    
    if len(ts) < 5:
        print(f"Skipping {item_code}: Insufficient data ({len(ts)} weeks).")
        continue

    forecast_index = pd.date_range(
        start=ts.index[-1] + pd.Timedelta(weeks=1),
        periods=FORECAST_WEEKS,
        freq="W-MON"
    )

    # --- A. Fit Model & Forecast ---
    model_obj = None
    forecast = None
    ci_80_lower = ci_80_upper = None
    ci_95_lower = ci_95_upper = None

    if model_type in ["AR", "MA", "ARMA", "ARIMA"]:
        # Identify order
        if model_type == "AR": order = (1,0,0)
        elif model_type == "MA": order = (0,0,1)
        elif model_type == "ARMA": order = (1,0,1)
        else: order = (1,1,1) # ARIMA

        model_obj = ARIMA(ts, order=order).fit()
        forecast_res = model_obj.get_forecast(FORECAST_WEEKS)
        forecast = forecast_res.predicted_mean
        
        # Confidence Intervals
        ci_80 = forecast_res.conf_int(alpha=0.20)
        ci_95 = forecast_res.conf_int(alpha=0.05)
        
        forecast = np.maximum(np.round(forecast), 0).astype(int)
        ci_80_lower = np.maximum(np.round(ci_80.iloc[:, 0]), 0).astype(int)
        ci_80_upper = np.maximum(np.round(ci_80.iloc[:, 1]), 0).astype(int)
        ci_95_lower = np.maximum(np.round(ci_95.iloc[:, 0]), 0).astype(int)
        ci_95_upper = np.maximum(np.round(ci_95.iloc[:, 1]), 0).astype(int)

    elif model_type == "SARIMA":
        model_obj = SARIMAX(
            ts, 
            order=(1, 1, 1), 
            seasonal_order=(0, 0, 0, 0),
            enforce_stationarity=False,
            enforce_invertibility=False
        ).fit(disp=False)
        forecast_res = model_obj.get_forecast(FORECAST_WEEKS)
        forecast = forecast_res.predicted_mean
        
        ci_80 = forecast_res.conf_int(alpha=0.20)
        ci_95 = forecast_res.conf_int(alpha=0.05)
        
        forecast = np.maximum(np.round(forecast), 0).astype(int)
        ci_80_lower = np.maximum(np.round(ci_80.iloc[:, 0]), 0).astype(int)
        ci_80_upper = np.maximum(np.round(ci_80.iloc[:, 1]), 0).astype(int)
        ci_95_lower = np.maximum(np.round(ci_95.iloc[:, 0]), 0).astype(int)
        ci_95_upper = np.maximum(np.round(ci_95.iloc[:, 1]), 0).astype(int)

    elif model_type == "Prophet":
        prophet_df = ts.reset_index()
        prophet_df.columns = ["ds", "y"]
        
        # Log transformation (Enhanced Prophet)
        prophet_df["y"] = np.log1p(prophet_df["y"])
        
        m = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            interval_width=0.95
        )
        # Add monthly seasonality
        m.add_seasonality(name='monthly', period=30.5, fourier_order=5)
        m.fit(prophet_df)
        model_obj = m
        
        future = m.make_future_dataframe(periods=FORECAST_WEEKS, freq='W-MON')
        forecast_all = m.predict(future)
        forecast_data = forecast_all.iloc[-FORECAST_WEEKS:]
        
        # Back-transform from log
        forecast = np.maximum(np.round(np.expm1(forecast_data["yhat"].values)), 0).astype(int)
        ci_95_lower = np.maximum(np.round(np.expm1(forecast_data["yhat_lower"].values)), 0).astype(int)
        ci_95_upper = np.maximum(np.round(np.expm1(forecast_data["yhat_upper"].values)), 0).astype(int)
        # 80% CI remains None for Prophet in this flow

    # --- B. Save Model as Dictionary (required by validation template) ---
    save_data = {
        "model": model_obj,
        "type": model_type
    }
    model_path = MODEL_DIR / f"{item_code}_weekly_best.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(save_data, f)

    # --- C. Save Forecast CSV ---
    forecast_df = pd.DataFrame({
        "Week_End": forecast_index,
        "Forecast_Qty": forecast
    })
    
    if ci_80_lower is not None:
        forecast_df["CI80_Lower"] = ci_80_lower
        forecast_df["CI80_Upper"] = ci_80_upper
    
    if ci_95_lower is not None:
        forecast_df["CI95_Lower"] = ci_95_lower
        forecast_df["CI95_Upper"] = ci_95_upper

    out_csv = FORECAST_DIR / f"{item_code}_final_forecast.csv"
    forecast_df.to_csv(out_csv, index=False)

    # --- D. Visualization ---
    plt.figure(figsize=(12, 6))
    plt.plot(ts.index, ts.values, label="Historical Actual", color="#2c3e50")
    plt.plot(forecast_index, forecast, label=f"Forecast ({model_type})", 
             marker="o", color="#e67e22", linestyle="--")
    
    # Shade Confidence Intervals
    if ci_95_lower is not None:
        plt.fill_between(
            forecast_index,
            ci_95_lower,
            ci_95_upper,
            color="#e67e22",
            alpha=0.15,
            label="95% Confidence Interval"
        )
    
    if ci_80_lower is not None:
        plt.fill_between(
            forecast_index,
            ci_80_lower,
            ci_80_upper,
            color="#e67e22",
            alpha=0.3,
            label="80% Confidence Interval"
        )
    
    plt.title(f"Final Forecast: {item_code} | Model: {model_type}", fontsize=14)
    plt.xlabel("Date")
    plt.ylabel("Quantity")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    
    fig_path = FIG_DIR / f"{item_code}_final_forecast.png"
    plt.savefig(fig_path, dpi=300)
    plt.close()

    print(f"   Done: Model saved, CSV saved, Plot saved.")

print("\n===== FINAL FORECAST PIPELINE COMPLETED =====")
