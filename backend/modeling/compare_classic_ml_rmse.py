import os
import sys
import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pickle
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

# Data Paths
DATA_PREP_DIR = PROJECT_ROOT / "data" / "processed" / "data_preparation"
TRAIN_PATH = DATA_PREP_DIR / "train_dataset.csv"
TEST_PATH = DATA_PREP_DIR / "test_dataset.csv"

# Output Paths
RESULTS_DIR = PROJECT_ROOT / "data" / "processed" / "classic_ml_comparison"
FIG_DIR = PROJECT_ROOT / "reports" / "figures" / "classic_ml_comparison"

# PERSISTENCE PATHS FOR VARIANTS
VAR_VALIDATION_DIR = PROJECT_ROOT / "data" / "processed" / "classic_ml_validation" / "variants"
VAR_MODEL_DIR = PROJECT_ROOT / "models" / "classic_ml" / "variants"

# Create directories
for d in [RESULTS_DIR, FIG_DIR, VAR_VALIDATION_DIR, VAR_MODEL_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Constants
FORECAST_WEEKS = 12
LAGS = 12

# -------------------------------------------------
# Helper Functions
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

# -------------------------------------------------
# Main Pipeline
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
    
    # Preprocessing
    item_codes = sorted(train_df["ITEM_CODE"].unique())
    print(f"Found {len(item_codes)} items.")

    results = []

    for item in item_codes:
        print(f"\n>>> Comparing ML Models for Item: {item}")
        
        # 1. Weekly Resampling
        df_full = pd.concat([train_df, test_df], ignore_index=True)
        item_df = df_full[df_full["ITEM_CODE"] == item].sort_values("OA_DATE")
        ts = item_df.set_index("OA_DATE")["QTY"].resample("W-MON").sum().fillna(0).reset_index()
        
        if len(ts) < FORECAST_WEEKS + LAGS + 5:
            print(f"Skipping {item}: Insufficient data.")
            continue

        # Split for validation
        # ts_train contains all data up to the test period
        ts_train_val = ts.iloc[:-FORECAST_WEEKS]
        ts_test_val = ts.iloc[-FORECAST_WEEKS:]

        # Create Lags for training
        train_lags = create_lag_features(ts_train_val, LAGS)
        X_train = train_lags.drop(columns=["OA_DATE", "QTY"])
        y_train = train_lags["QTY"]
        
        # Models to compare
        models = {
            "LinearRegression": LinearRegression(),
            "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42),
            "GradientBoosting": GradientBoostingRegressor(n_estimators=100, random_state=42),
            "XGBoost": XGBRegressor(n_estimators=100, random_state=42)
        }
        
        item_scores = {"Item_Code": item}
        
        for name, model in models.items():
            # 2. Train Model
            model.fit(X_train, y_train)
            
            # 3. Recursive Forecast for the 12-week test period
            forecasts = []
            current_history = list(ts_train_val['QTY'].values)
            
            for _ in range(FORECAST_WEEKS):
                X_next = prepare_forecast_input(current_history, LAGS)
                y_next = model.predict(X_next)[0]
                y_next = max(0, y_next) # Non-negative
                forecasts.append(y_next)
                current_history.append(y_next)
                
            # 4. Compute RMSE against the actual test set
            rmse = np.sqrt(mean_squared_error(ts_test_val['QTY'], forecasts))
            item_scores[name] = rmse
            print(f"   {name}: RMSE = {rmse:.2f}")

            # 5. PERSIST VARIANT DATA (NEW)
            # Save Model
            with open(VAR_MODEL_DIR / f"{item}_{name}_model.pkl", "wb") as f:
                pickle.dump(model, f)
            
            # Save Validation vs Actual
            val_df = pd.DataFrame({
                "Date": ts_test_val['OA_DATE'].values,
                "Actual_Qty": ts_test_val['QTY'].values,
                "Predicted_Qty": forecasts
            })
            val_df.to_csv(VAR_VALIDATION_DIR / f"{item}_validation_{name}.csv", index=False)
            
        results.append(item_scores)

    # 5. Create Comparison DataFrame
    comparison_df = pd.DataFrame(results)
    comparison_df.set_index("Item_Code", inplace=True)
    
    # Save to CSV
    csv_path = RESULTS_DIR / "classic_ml_rmse_comparison.csv"
    comparison_df.to_csv(csv_path)
    print(f"\nComparison results saved to: {csv_path}")
    print(comparison_df)

    # 6. Visualization (Advanced Plotting to match requested style)
    plt.figure(figsize=(16, 8))
    
    model_names = comparison_df.columns.tolist()
    item_codes = comparison_df.index.tolist()
    x = np.arange(len(item_codes))
    
    # Color palette
    colors = plt.cm.tab10(np.linspace(0, 1, len(model_names)))
    model_to_color = dict(zip(model_names, colors))

    # 1. Plot background lines and points (grayed out)
    for model_name in model_names:
        plt.plot(x, comparison_df[model_name], color='lightgray', linestyle='--', alpha=0.3, zorder=1)
        plt.scatter(x, comparison_df[model_name], color='lightgray', s=30, alpha=0.5, zorder=2)

    # 2. Highlight Champions (Best model per item)
    for idx, item in enumerate(item_codes):
        # find best model for this item
        best_model = comparison_df.loc[item].idxmin()
        best_rmse = comparison_df.loc[item, best_model]
        
        # Plot large colored circle
        color = model_to_color[best_model]
        plt.scatter(idx, best_rmse, color=color, s=150, edgecolors='white', linewidth=1.5, zorder=4, label=best_model if idx == 0 else "")
        
        # Add text label
        plt.text(idx + 0.1, best_rmse, f"{best_rmse:.2f}\n({best_model})", 
                 color=color, fontsize=9, fontweight='bold', va='center')

    # Formatting
    plt.title("Weekly RMSE Comparison: Classical ML Models", fontsize=16, fontweight='bold', pad=20)
    plt.ylabel("RMSE (Weekly Quantity)", fontsize=12, fontweight='bold')
    plt.xlabel("Item Code", fontsize=12, fontweight='bold')
    plt.xticks(x, item_codes, rotation=45, ha='right')
    
    # Custom Legend
    from matplotlib.lines import Line2D
    legend_elements = [Line2D([0], [0], marker='o', color='w', label=m,
                              markerfacecolor=model_to_color[m], markersize=10) for m in model_names]
    plt.legend(handles=legend_elements, title="Model Type", loc='upper left', bbox_to_anchor=(1, 1))

    plt.grid(True, linestyle='--', alpha=0.3, zorder=0)
    plt.tight_layout()
    
    plot_path = FIG_DIR / "classic_ml_rmse_comparison_plot.png"
    plt.savefig(plot_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"Comparison plot saved to: {plot_path}")

    print("\n===== CLASSICAL ML COMPARISON COMPLETED =====")

if __name__ == "__main__":
    main()
