import os
import sys
import pickle
import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ML Models
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error

# Ignore warnings
warnings.filterwarnings("ignore")

# -------------------------------------------------
# Configuration & Paths
# -------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

# Use full datasets for training if available, otherwise just train_dataset
TRAIN_PATH = PROJECT_ROOT / "data" / "processed" / "data_preparation" / "train_dataset.csv"
TEST_PATH = PROJECT_ROOT / "data" / "processed" / "data_preparation" / "test_dataset.csv"

# Output Paths
MODEL_DIR = PROJECT_ROOT / "models" / "classic_ml"
FORECAST_DIR = PROJECT_ROOT / "data" / "processed" / "classic_ml_forecast"
FIG_DIR = PROJECT_ROOT / "reports" / "figures" / "classic_ml_forecast"

# Create directories
for d in [MODEL_DIR, FORECAST_DIR, FIG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Constants
FORECAST_WEEKS = 12
LAGS = 12

# -------------------------------------------------
# CHAMPION MODEL MAPPING
# -------------------------------------------------
COMPARISON_PATH = PROJECT_ROOT / "data" / "processed" / "classic_ml_comparison" / "classic_ml_rmse_comparison.csv"

def get_champion_models():
    """Load champion models from the comparison results."""
    if not COMPARISON_PATH.exists():
        print(f"Warning: Comparison file {COMPARISON_PATH} not found. Using defaults.")
        return {}

    try:
        comp_df = pd.read_csv(COMPARISON_PATH, index_col="Item_Code")
        # For each item, find the column name with the minimum value
        best_models = comp_df.idxmin(axis=1).to_dict()
        print(f"Loaded {len(best_models)} champion models from comparison results.")
        return best_models
    except Exception as e:
        print(f"Error loading comparison file: {e}")
        return {}

# -------------------------------------------------
# Feature Engineering
# -------------------------------------------------
def create_lag_features(df, lags):
    """Create lag features for time series."""
    df_lags = df.copy()
    for i in range(1, lags + 1):
        df_lags[f'lag_{i}'] = df_lags['QTY'].shift(i)
    return df_lags.dropna()

def prepare_forecast_input(history, lags):
    """Prepare features for the next step prediction."""
    features = {}
    for i in range(1, lags + 1):
        features[f'lag_{i}'] = history[-i]
    return pd.DataFrame([features])

def get_model_instance(model_name):
    """Initialize the specific model instance."""
    if model_name == "LinearRegression":
        return LinearRegression()
    elif model_name == "RandomForest":
        return RandomForestRegressor(n_estimators=100, random_state=42)
    elif model_name == "GradientBoosting":
        return GradientBoostingRegressor(n_estimators=100, random_state=42)
    elif model_name == "XGBoost":
        return XGBRegressor(n_estimators=100, random_state=42)
    else:
        return LinearRegression() # Default

# -------------------------------------------------
# Main Pipeline
# -------------------------------------------------
def main():
    print("Loading datasets...")
    
    # 0. Load Champion Models
    champion_mapping = get_champion_models()

    try:
        # Load both to get full history
        train_df = pd.read_csv(TRAIN_PATH)
        # Check if test file exists to include it in "Full Data Training"
        if TEST_PATH.exists():
            test_df = pd.read_csv(TEST_PATH)
            df = pd.concat([train_df, test_df], ignore_index=True)
            print("Training on Combined Dataset (Train + Test).")
        else:
            df = train_df
            print("Training on Train Dataset only.")
    except FileNotFoundError:
        print(f"Error: Datasets not found. Run data_preparation.py first.")
        return

    df["OA_DATE"] = pd.to_datetime(df["OA_DATE"], errors="coerce")
    df = df.dropna(subset=["OA_DATE", "QTY"])

    item_codes = sorted(df["ITEM_CODE"].unique())
    print(f"Found {len(item_codes)} items.")

    for item in item_codes:
        model_type = champion_mapping.get(item, "LinearRegression")
        print(f"\n>>> Processing Item: {item} | Selected Champion: {model_type}")
        
        # 1. Resample to Weekly
        item_df = df[df["ITEM_CODE"] == item].sort_values("OA_DATE")
        ts = item_df.set_index("OA_DATE")["QTY"].resample("W-MON").sum().fillna(0).reset_index()
        
        if len(ts) < LAGS + 1:
            print(f"Skipping {item}: Not enough data for lags.")
            continue

        # 2. Create Lags
        ts_lags = create_lag_features(ts, LAGS)
        X = ts_lags.drop(columns=["OA_DATE", "QTY"])
        y = ts_lags["QTY"]
        
        # 3. Initialize and Fit Champion Model
        model = get_model_instance(model_type)
        model.fit(X, y)
        
        # 4. Fitted Values for Plotting
        ts_lags['Fitted'] = np.maximum(np.round(model.predict(X)), 0).astype(int)
        
        # 5. Recursive Forecasting
        forecasts = []
        current_history = list(ts['QTY'].values)
        
        for _ in range(FORECAST_WEEKS):
            X_next = prepare_forecast_input(current_history, LAGS)
            y_next = model.predict(X_next)[0]
            y_next = max(0, int(round(y_next)))
            forecasts.append(y_next)
            current_history.append(y_next)
            
        # 6. Save Model
        with open(MODEL_DIR / f"{item}_best_model.pkl", "wb") as f:
            pickle.dump(model, f)
            
        # 7. Save Forecast CSV
        future_dates = pd.date_range(
            start=ts['OA_DATE'].iloc[-1] + pd.Timedelta(weeks=1),
            periods=FORECAST_WEEKS,
            freq="W-MON"
        )
        forecast_df = pd.DataFrame({
            "Week_End": future_dates,
            "Forecast_Qty": forecasts
        })
        forecast_df.to_csv(FORECAST_DIR / f"{item}_forecast_classic.csv", index=False)
        
        # 8. Visualization
        plt.figure(figsize=(14, 6))
        
        # Historical
        plt.plot(ts['OA_DATE'], ts['QTY'], label="Historical Actual", color="#2c3e50", alpha=0.6)
        
        # Fitted
        plt.plot(ts_lags['OA_DATE'], ts_lags['Fitted'], label=f"Fitted ({model_type})", color="#27ae60", linestyle=":")
        
        # Forecast
        plt.plot(future_dates, forecasts, label="Future Forecast (12W)", color="#e67e22", marker="o", linestyle="--")
        
        plt.axvline(ts['OA_DATE'].iloc[-1], color="gray", linestyle=":", alpha=0.5)
        plt.title(f"Champion ML Forecast: {item} | Model: {model_type}", fontsize=14, fontweight='bold')
        plt.xlabel("Date")
        plt.ylabel("Quantity")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        plt.savefig(FIG_DIR / f"{item}_forecast_classic.png", dpi=200)
        plt.close()

    print("\n===== CHAMPION ML PIPELINE COMPLETED =====")

if __name__ == "__main__":
    main()
