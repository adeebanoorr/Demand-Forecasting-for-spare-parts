import os
import sys
import pickle
import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.metrics import mean_squared_error, mean_absolute_error

# Ignore warnings
warnings.filterwarnings("ignore")

# -------------------------------------------------
# Configuration & Paths
# -------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

# Data Paths
DATA_PREP_DIR = PROJECT_ROOT / "data" / "processed" / "data_preparation"
TRAIN_PATH = DATA_PREP_DIR / "train_dataset.csv"
TEST_PATH = DATA_PREP_DIR / "test_dataset.csv"

# Model & Output Paths
MODEL_DIR = PROJECT_ROOT / "models" / "classic_ml"
VALIDATION_DIR = PROJECT_ROOT / "data" / "processed" / "classic_ml_validation"
FIG_DIR = PROJECT_ROOT / "reports" / "figures" / "classic_ml_validation"

# Create directories if they don't exist
for d in [VALIDATION_DIR, FIG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Constants
FORECAST_WEEKS = 12
LAGS = 12

# -------------------------------------------------
# Helper Functions
# -------------------------------------------------
def prepare_forecast_input(history, lags):
    """Prepare features for the next step prediction."""
    features = {}
    for i in range(1, lags + 1):
        features[f'lag_{i}'] = history[-i]
    return pd.DataFrame([features])

def smape(actual, predicted):
    """Symmetric Mean Absolute Percentage Error."""
    return 100 / len(actual) * np.sum(
        2 * np.abs(predicted - actual) /
        (np.abs(actual) + np.abs(predicted) + 1e-6)
    )

def evaluate_performance(actual, predicted):
    """Calculate RMSE, MAE, and SMAPE."""
    rmse = np.sqrt(mean_squared_error(actual, predicted))
    mae = mean_absolute_error(actual, predicted)
    error_smape = smape(actual, predicted)
    return rmse, mae, error_smape

# -------------------------------------------------
# Main Validation Pipeline
# -------------------------------------------------
def main():
    print("Loading datasets...")
    try:
        train_df = pd.read_csv(TRAIN_PATH)
        test_df = pd.read_csv(TEST_PATH)
    except FileNotFoundError:
        print(f"Error: Datasets not found in {DATA_PREP_DIR}. Run data_preparation.py first.")
        return

    # Date Conversion
    train_df["OA_DATE"] = pd.to_datetime(train_df["OA_DATE"], errors="coerce")
    test_df["OA_DATE"] = pd.to_datetime(test_df["OA_DATE"], errors="coerce")

    # Get list of models
    model_files = list(MODEL_DIR.glob("*_best_model.pkl"))
    if not model_files:
        print(f"No models found in {MODEL_DIR}. Run train_forecast_classic_ml.py first.")
        return

    validation_summary = []

    for model_path in model_files:
        item = model_path.name.replace("_best_model.pkl", "")
        print(f"\nProcessing Validation for Item: {item}")

        # 1. Load Model
        try:
            with open(model_path, "rb") as f:
                model = pickle.load(f)
        except Exception as e:
            print(f"Error loading model for {item}: {e}")
            continue

        # 2. Resample Data to Weekly
        # Training Data (to get the starting lags)
        item_train = train_df[train_df["ITEM_CODE"] == item].sort_values("OA_DATE")
        ts_train = item_train.set_index("OA_DATE")["QTY"].resample("W-MON").sum().fillna(0)
        
        # Test Data (Actuals)
        item_test = test_df[test_df["ITEM_CODE"] == item].sort_values("OA_DATE")
        last_train_date = ts_train.index[-1]
        
        # Forecast dates starting after last training date
        forecast_dates = pd.date_range(
            start=last_train_date + pd.Timedelta(weeks=1),
            periods=FORECAST_WEEKS,
            freq="W-MON"
        )
        
        # Resample test data to match forecast index
        ts_test_actual = (
            item_test.set_index("OA_DATE")["QTY"]
            .resample("W-MON")
            .sum()
            .reindex(forecast_dates, fill_value=0)
        )

        if len(ts_train) < LAGS:
            print(f"Skipping {item}: Insufficient training history for lags.")
            continue

        # 3. Recursive Forecasting for the 12-week test period
        forecasts = []
        current_history = list(ts_train.values)
        
        for _ in range(FORECAST_WEEKS):
            X_next = prepare_forecast_input(current_history, LAGS)
            y_next = model.predict(X_next)[0]
            y_next = max(0, int(round(y_next))) # Non-negative integer
            forecasts.append(y_next)
            current_history.append(y_next)

        # 4. Evaluate Performance
        rmse_val, mae_val, smape_val = evaluate_performance(ts_test_actual.values, forecasts)
        print(f"Validation Metrics -> RMSE: {rmse_val:.2f}, MAE: {mae_val:.2f}, SMAPE: {smape_val:.2f}%")

        validation_summary.append({
            "Item_Code": item,
            "RMSE": rmse_val,
            "MAE": mae_val,
            "SMAPE": smape_val
        })

        # 5. Save Validation CSV
        comparison_df = pd.DataFrame({
            "Date": forecast_dates,
            "Actual_Qty": ts_test_actual.values,
            "Forecast_Qty": forecasts
        })
        comparison_df.to_csv(VALIDATION_DIR / f"{item}_validation_vs_actual.csv", index=False)

        # 6. Plot Validation Result
        plt.figure(figsize=(14, 6))
        
        # Historical context (last 12 weeks of training)
        plt.plot(ts_train.index[-12:], ts_train.values[-12:], label="Historical (Last 12W)", color="#2c3e50", alpha=0.5)
        
        # Validation Period
        plt.plot(forecast_dates, ts_test_actual.values, label="Actual", color="#27ae60", marker="o", linewidth=2)
        plt.plot(forecast_dates, forecasts, label="Forecast (Classic ML)", color="#e67e22", marker="o", linestyle="--")
        
        plt.axvline(last_train_date, linestyle=":", color="gray")
        plt.title(f"Classic ML Validation: {item}\nRMSE: {rmse_val:.2f} | SMAPE: {smape_val:.2f}%", fontsize=14, fontweight='bold')
        plt.xlabel("Date", fontweight='bold')
        plt.ylabel("Quantity", fontweight='bold')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        plt.savefig(FIG_DIR / f"{item}_validation_plot.png", dpi=200)
        plt.close()

    # 7. Save Summary Table
    if validation_summary:
        summary_df = pd.DataFrame(validation_summary)
        summary_path = VALIDATION_DIR / "classic_ml_validation_summary.csv"
        summary_df.to_csv(summary_path, index=False)
        print(f"\nOverall Validation summary saved to: {summary_path}")
        print(summary_df)

    print("\n===== CLASSICAL ML VALIDATION COMPLETED =====")

if __name__ == "__main__":
    main()
