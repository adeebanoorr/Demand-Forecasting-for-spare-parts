import warnings
warnings.filterwarnings("ignore")

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error

# =================================================
# 0. PATHS & CONFIGURATION
# =================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

# Data directories as per template
DATA_DIR = PROJECT_ROOT / "data" / "processed" 
MODEL_DIR = PROJECT_ROOT / "models" / "all_forecast"

# Use existing test dataset
TEST_PATH = PROJECT_ROOT / "data" / "processed" / "data_preparation" / "test_dataset.csv"
TRAIN_PATH = PROJECT_ROOT / "data" / "processed" / "data_preparation" / "train_dataset.csv"

OUT_CSV_DIR = PROJECT_ROOT / "data" / "processed" / "all_validation"
OUT_FIG_DIR = PROJECT_ROOT / "reports" / "figures" / "all_validation"

OUT_CSV_DIR.mkdir(parents=True, exist_ok=True)
OUT_FIG_DIR.mkdir(parents=True, exist_ok=True)

FORECAST_WEEKS = 12

# =================================================
# 1. METRICS
# =================================================
def smape(actual, predicted):
    return 100 / len(actual) * np.sum(
        2 * np.abs(predicted - actual) /
        (np.abs(actual) + np.abs(predicted) + 1e-6)
    )

def rmse(actual, predicted):
    return np.sqrt(mean_squared_error(actual, predicted))

# =================================================
# 2. LOAD FUTURE ACTUALS DATA
# =================================================
print("Loading datasets...")
test_df = pd.read_csv(TEST_PATH)
train_df = pd.read_csv(TRAIN_PATH)

# Rename to match template logic if needed, but here we'll use ITEM_CODE
test_df["OA_DATE"] = pd.to_datetime(test_df["OA_DATE"], errors="coerce")
test_df = test_df.dropna(subset=["OA_DATE", "QTY"])

# =================================================
# 3. FORECAST vs ACTUAL (WITH CI WHERE POSSIBLE)
# =================================================
print("\n===== WEEKLY BEST MODEL: FORECAST vs ACTUAL (WITH CI) =====")

validation_summary = []

for model_file in sorted(MODEL_DIR.glob("*_weekly_best.pkl")):

    item_code = model_file.name.replace("_weekly_best.pkl", "")
    print(f"\nItem Code: {item_code}")
    print("-" * 60)

    # -------------------------------------------------
    # Load trained model
    # -------------------------------------------------
    with open(model_file, "rb") as f:
        saved_data = pickle.load(f)

    model = saved_data["model"]
    model_type = saved_data["type"]

    # -------------------------------------------------
    # Get training end date (to align forecast start)
    # -------------------------------------------------
    item_train = train_df[train_df["ITEM_CODE"] == item_code].copy()
    item_train["OA_DATE"] = pd.to_datetime(item_train["OA_DATE"], errors="coerce")
    ts_train = (
        item_train.set_index("OA_DATE")["QTY"]
        .resample("W-MON")
        .sum()
        .fillna(0)
    )
    last_train_date = ts_train.index[-1]

    # -------------------------------------------------
    # Forecast
    # -------------------------------------------------
    future_index = pd.date_range(
        start=last_train_date + pd.Timedelta(weeks=1),
        periods=FORECAST_WEEKS,
        freq="W-MON"
    )

    forecast_mean = None
    ci_80_lower = ci_80_upper = None
    ci_95_lower = ci_95_upper = None

    try:
        if model_type in ["AR", "MA", "ARIMA", "SARIMA"]:
            forecast_res = model.get_forecast(steps=FORECAST_WEEKS)
            forecast_mean = forecast_res.predicted_mean
            
            # Confidence Intervals
            ci_80 = forecast_res.conf_int(alpha=0.20)
            ci_95 = forecast_res.conf_int(alpha=0.05)

            ci_80_lower = np.maximum(np.round(ci_80.iloc[:, 0]), 0).astype(int)
            ci_80_upper = np.maximum(np.round(ci_80.iloc[:, 1]), 0).astype(int)
            ci_95_lower = np.maximum(np.round(ci_95.iloc[:, 0]), 0).astype(int)
            ci_95_upper = np.maximum(np.round(ci_95.iloc[:, 1]), 0).astype(int)

        elif model_type == "Prophet":
            # Prophet forecast
            future = model.make_future_dataframe(periods=FORECAST_WEEKS, freq='W-MON')
            forecast_all = model.predict(future)
            forecast_data = forecast_all.iloc[-FORECAST_WEEKS:]
            
            # Back-transform from log (Prophet Enhanced)
            forecast_mean = np.expm1(forecast_data["yhat"].values)
            
            # Prophet CIs (usually yhat_lower/yhat_upper at 95% if interval_width was 0.95)
            ci_95_lower = np.maximum(np.round(np.expm1(forecast_data["yhat_lower"].values)), 0).astype(int)
            ci_95_upper = np.maximum(np.round(np.expm1(forecast_data["yhat_upper"].values)), 0).astype(int)
            # 80% CI not explicitly returned unless multiple interval_widths are run, 
            # so we'll leave it as None for Prophet in this simplified template match

        if forecast_mean is not None:
            forecast_mean = np.maximum(np.round(forecast_mean), 0).astype(int)

    except Exception as e:
        print(f"Forecast failed for {item_code}: {e}")
        continue

    # -------------------------------------------------
    # Load FUTURE ACTUALS
    # -------------------------------------------------
    item_test = test_df[test_df["ITEM_CODE"] == item_code]

    actual_future = (
        item_test
        .set_index("OA_DATE")["QTY"]
        .resample("W-MON")
        .sum()
        .reindex(future_index, fill_value=0)
    ).values

    # Metrics
    score_rmse = rmse(actual_future, forecast_mean)
    score_smape = smape(actual_future, forecast_mean)
    print(f"   RMSE: {score_rmse:.2f} | SMAPE: {score_smape:.2f}%")

    validation_summary.append({
        "Item_Code": item_code,
        "Model": model_type,
        "RMSE": score_rmse,
        "SMAPE": score_smape
    })

    # -------------------------------------------------
    # Output table
    # -------------------------------------------------
    result_df = pd.DataFrame({
        "Week": future_index,
        "Forecast_Qty": forecast_mean,
        "Actual_Qty": actual_future
    })

    if ci_80_lower is not None:
        result_df["CI80_Lower"] = ci_80_lower
        result_df["CI80_Upper"] = ci_80_upper
    
    if ci_95_lower is not None:
        result_df["CI95_Lower"] = ci_95_lower
        result_df["CI95_Upper"] = ci_95_upper

    out_csv = OUT_CSV_DIR / f"{item_code}_{model_type}_forecast_vs_actual_12w.csv"
    result_df.to_csv(out_csv, index=False)
    print(f"Saved CSV → {out_csv.name}")

    # -------------------------------------------------
    # Plot: Forecast + CI + Actual
    # -------------------------------------------------
    plt.figure(figsize=(12, 5))

    plt.plot(
        future_index,
        forecast_mean,
        label="Forecast",
        color="red",
        marker="o",
        linewidth=2
    )

    plt.plot(
        future_index,
        actual_future,
        label="Actual",
        color="green",
        marker="o",
        linewidth=2
    )

    if ci_80_lower is not None:
        plt.fill_between(
            future_index,
            ci_80_lower,
            ci_80_upper,
            color="red",
            alpha=0.25,
            label="80% CI"
        )

    if ci_95_lower is not None:
        plt.fill_between(
            future_index,
            ci_95_lower,
            ci_95_upper,
            color="red",
            alpha=0.12,
            label="95% CI"
        )

    plt.axvline(last_train_date, linestyle=":", color="gray")
    plt.title(f"{item_code} | {model_type} | Forecast vs Actual (12 Weeks)\nRMSE: {score_rmse:.2f} | SMAPE: {score_smape:.2f}%")
    plt.xlabel("Week")
    plt.ylabel("Quantity")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()

    fig_path = OUT_FIG_DIR / f"{item_code}_{model_type}_forecast_vs_actual.png"
    plt.savefig(fig_path, dpi=300)
    plt.close()

# Save final summary
summary_df = pd.DataFrame(validation_summary)
summary_df.to_csv(OUT_CSV_DIR / "validation_summary_metrics.csv", index=False)
print("\nValidation Summary:")
print(summary_df)

print("\n===== WEEKLY BEST MODEL VALIDATION COMPLETED =====")
