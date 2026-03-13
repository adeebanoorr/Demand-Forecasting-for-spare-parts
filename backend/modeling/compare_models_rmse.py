import warnings
import pickle
warnings.filterwarnings("ignore")

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from prophet import Prophet

# -------------------------------------------------
# 0. Project root
# -------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

# -------------------------------------------------
# 1. Paths
# -------------------------------------------------
TRAIN_PATH = PROJECT_ROOT / "data" / "processed" / "data_preparation" / "train_dataset.csv"
TEST_PATH = PROJECT_ROOT / "data" / "processed" / "data_preparation" / "test_dataset.csv"
FIG_DIR = PROJECT_ROOT / "reports" / "figures" / "baseline_comparison"
RESULTS_DIR = PROJECT_ROOT / "data" / "processed" / "baseline_comparison"

FIG_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# PERSISTENCE PATHS FOR VARIANTS
VAR_VALIDATION_DIR = PROJECT_ROOT / "data" / "processed" / "all_validation" / "variants"
VAR_MODEL_DIR = PROJECT_ROOT / "models" / "all_forecast" / "variants"

for d in [VAR_VALIDATION_DIR, VAR_MODEL_DIR]:
    d.mkdir(parents=True, exist_ok=True)

def save_variant(item_code, model_name, model_obj, test_index, test_actual, forecast_vals):
    """Helper to save model and its validation data."""
    # Save Model
    with open(VAR_MODEL_DIR / f"{item_code}_{model_name}_model.pkl", "wb") as f:
        pickle.dump(model_obj, f)
    
    # Save Validation vs Actual
    val_df = pd.DataFrame({
        "Date": test_index,
        "Actual_Qty": test_actual,
        "Predicted_Qty": forecast_vals
    })
    val_df.to_csv(VAR_VALIDATION_DIR / f"{item_code}_validation_{model_name}.csv", index=False)

# -------------------------------------------------
# 2. Helper: RMSE
# -------------------------------------------------
def rmse(y_true, y_pred):
    return np.sqrt(mean_squared_error(y_true, y_pred))

# -------------------------------------------------
# 3. Model comparison loop
# -------------------------------------------------
all_results = []
FORECAST_WEEKS = 12

print("Loading datasets...")
train_df = pd.read_csv(TRAIN_PATH)
test_df = pd.read_csv(TEST_PATH)

# Combine for easier processing per item
full_df = pd.concat([train_df, test_df], ignore_index=True)
full_df["OA_DATE"] = pd.to_datetime(full_df["OA_DATE"], errors="coerce")
full_df = full_df.dropna(subset=["OA_DATE", "QTY"])

item_codes = sorted(full_df["ITEM_CODE"].unique())
print(f"Found {len(item_codes)} items: {item_codes}")

for item_code in item_codes:
    print(f"\nProcessing Item: {item_code}")
    
    item_df = full_df[full_df["ITEM_CODE"] == item_code].sort_values("OA_DATE")
    
    # Resample to weekly (Sunday)
    ts = (
        item_df.set_index("OA_DATE")["QTY"]
        .resample("W-SUN")
        .sum()
        .fillna(0)
    )
    
    if len(ts) < FORECAST_WEEKS * 2:
        print(f"Insufficient data for {item_code}. Skipping.")
        continue
        
    train = ts.iloc[:-FORECAST_WEEKS]
    test = ts.iloc[-FORECAST_WEEKS:]
    
    results = {"Item_Code": item_code}
    
    # --- AR(1) ---
    try:
        ar_model = ARIMA(train, order=(1, 0, 0)).fit()
        ar_f = ar_model.forecast(FORECAST_WEEKS)
        results["AR"] = rmse(test, ar_f)
        save_variant(item_code, "AR", ar_model, test.index, test.values, ar_f)
    except Exception as e:
        print(f"AR error for {item_code}: {e}")
        results["AR"] = np.nan

    # --- MA(1) ---
    try:
        ma_model = ARIMA(train, order=(0, 0, 1)).fit()
        ma_f = ma_model.forecast(FORECAST_WEEKS)
        results["MA"] = rmse(test, ma_f)
        save_variant(item_code, "MA", ma_model, test.index, test.values, ma_f)
    except Exception as e:
        print(f"MA error for {item_code}: {e}")
        results["MA"] = np.nan

    # --- ARMA(1,1) ---
    try:
        arma_model = ARIMA(train, order=(1, 0, 1)).fit()
        arma_f = arma_model.forecast(FORECAST_WEEKS)
        results["ARMA"] = rmse(test, arma_f)
        save_variant(item_code, "ARMA", arma_model, test.index, test.values, arma_f)
    except Exception as e:
        print(f"ARMA error for {item_code}: {e}")
        results["ARMA"] = np.nan

    # --- ARIMA(1,1,1) ---
    try:
        arima_model = ARIMA(train, order=(1, 1, 1)).fit()
        arima_f = arima_model.forecast(FORECAST_WEEKS)
        results["ARIMA"] = rmse(test, arima_f)
        save_variant(item_code, "ARIMA", arima_model, test.index, test.values, arima_f)
    except Exception as e:
        print(f"ARIMA error for {item_code}: {e}")
        results["ARIMA"] = np.nan

    # --- SARIMA(1,1,1) ---
    try:
        sarima_model = SARIMAX(
            train,
            order=(1, 1, 1),
            seasonal_order=(0, 0, 0, 0),
            enforce_stationarity=False,
            enforce_invertibility=False
        ).fit(disp=False)
        sarima_f = sarima_model.forecast(FORECAST_WEEKS)
        results["SARIMA"] = rmse(test, sarima_f)
        save_variant(item_code, "SARIMA", sarima_model, test.index, test.values, sarima_f)
    except Exception as e:
        print(f"SARIMA error for {item_code}: {e}")
        results["SARIMA"] = np.nan

    # --- Prophet ---
    try:
        # Prepare Prophet data
        prophet_train = train.reset_index()
        prophet_train.columns = ["ds", "y"]
        
        # Initialize and fit model
        m = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            interval_width=0.95
        )
        m.fit(prophet_train)
        
        # Forecast
        future = m.make_future_dataframe(periods=FORECAST_WEEKS, freq='W-SUN')
        forecast_all = m.predict(future)
        prophet_forecast = forecast_all.iloc[-FORECAST_WEEKS:]["yhat"].values
        results["Prophet"] = rmse(test, prophet_forecast)
        save_variant(item_code, "Prophet", m, test.index, test.values, prophet_forecast)
    except Exception as e:
        print(f"Prophet error for {item_code}: {e}")
        results["Prophet"] = np.nan

    all_results.append(results)

# -------------------------------------------------
# 4. Results Table
# -------------------------------------------------
rmse_df = pd.DataFrame(all_results).set_index("Item_Code")
print("\nRMSE Score comparison (lower is better):\n")
print(rmse_df)

# Save results
results_csv = RESULTS_DIR / "item_comparison_rmse_score.csv"
rmse_df.to_csv(results_csv)
print(f"\nResults saved to: {results_csv}")

# -------------------------------------------------
# 5. Visualization
# -------------------------------------------------
plt.figure(figsize=(18, 9))

colors = {
    "AR": "#1f77b4",
    "MA": "#ff7f0e",
    "ARMA": "#2ca02c",
    "ARIMA": "#d62728",
    "SARIMA": "#9467bd",
    "Prophet": "#e377c2"  # Distinct pink for Prophet
}

# Plot each item
for idx, item in enumerate(rmse_df.index):
    row = rmse_df.loc[item]
    # Filter out NaNs to find best model
    valid_values = row.dropna()
    if valid_values.empty:
        continue
        
    best_model = valid_values.idxmin()

    for model in rmse_df.columns:
        val = row[model]
        if pd.isna(val):
            continue
            
        is_best = (model == best_model)
        
        plt.plot(
            idx,
            val,
            marker="o",
            color=colors[model] if is_best else "gray",
            alpha=1.0 if is_best else 0.3,
            markersize=12 if is_best else 7,
            zorder=3 if is_best else 2
        )
        
        # Add text label for the best model score
        if is_best:
            plt.text(
                idx, val, f" {val:.2f}\n({model})", 
                va='bottom', ha='left', 
                color=colors[model], fontweight='bold',
                fontsize=9
            )

# Draw connecting lines for each model
for model in rmse_df.columns:
    if model in colors:
        plt.plot(
            range(len(rmse_df)),
            rmse_df[model],
            linestyle="--",
            alpha=0.15,
            color=colors[model],
            label=model,
            zorder=1
        )

plt.xticks(range(len(rmse_df)), rmse_df.index, rotation=45, ha="right")
plt.xlabel("Item Code", fontsize=12)
plt.ylabel("RMSE (Weekly Quantity)", fontsize=12)
plt.title("Weekly RMSE Comparison: AR vs MA vs ARMA vs ARIMA vs SARIMA vs Prophet", fontsize=14, fontweight='bold')
plt.grid(axis="y", linestyle="--", alpha=0.4)

# Legend
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], marker="o", color=color,
           label=model, linestyle="", markersize=10)
    for model, color in colors.items()
]
plt.legend(handles=legend_elements, title="Model Type", loc="upper left", bbox_to_anchor=(1, 1))

# Save figure
fig_path = FIG_DIR / "item_comparison_rmse_score.png"
plt.tight_layout()
plt.savefig(fig_path, dpi=300)
plt.close()

print(f"Figure saved at: {fig_path}")

print("\n===== COMPARATIVE ANALYSIS (WITH PROPHET) COMPLETED =====")
