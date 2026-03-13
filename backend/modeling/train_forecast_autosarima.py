import sys
import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pickle
from pathlib import Path
from pmdarima import auto_arima

warnings.filterwarnings("ignore")

# -------------------------------------------------
# Configuration
# -------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

TRAIN_PATH = PROJECT_ROOT / "data" / "processed" / "data_preparation" / "train_dataset.csv"

MODEL_DIR = PROJECT_ROOT / "models" / "autosarima"
FORECAST_DIR = PROJECT_ROOT / "data" / "processed" / "autosarima_forecast"
FIG_DIR = PROJECT_ROOT / "reports" / "figures" / "autosarima_forecast"

for d in [MODEL_DIR, FORECAST_DIR, FIG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

FORECAST_WEEKS = 12
SEASONAL_PERIOD = 52  # Weekly seasonality

# -------------------------------------------------
# Main Pipeline
# -------------------------------------------------
def main():
    print("Loading training dataset...")
    df = pd.read_csv(TRAIN_PATH)

    df["OA_DATE"] = pd.to_datetime(df["OA_DATE"], errors="coerce")
    df = df.dropna(subset=["OA_DATE", "QTY"])

    item_codes = sorted(df["ITEM_CODE"].unique())
    print(f"Found {len(item_codes)} items.")

    for item in item_codes:
        print(f"\nProcessing Item: {item}")

        item_df = df[df["ITEM_CODE"] == item].sort_values("OA_DATE")

        ts = (
            item_df.set_index("OA_DATE")["QTY"]
            .resample("W-MON")
            .sum()
            .fillna(0)
        )

        if len(ts) < 10:
            print("Skipping — insufficient history")
            continue

        # -------------------------------
        # Train Auto-SARIMA
        # -------------------------------
        m = SEASONAL_PERIOD if len(ts) > 2 * SEASONAL_PERIOD else 1

        model = auto_arima(
            ts,
            seasonal=(m > 1),
            m=m,
            max_p=3, max_q=3,
            max_P=1, max_Q=1, max_D=1,
            stepwise=True,
            n_fits=30,
            suppress_warnings=True,
            error_action="ignore",
            trace=False
        )

        print(f"Best Model: {model.order} {model.seasonal_order}")

        # -------------------------------
        # Forecast 12 weeks ahead
        # -------------------------------
        forecast, conf_int = model.predict(
            n_periods=FORECAST_WEEKS,
            return_conf_int=True
        )

        forecast = np.maximum(np.round(forecast), 0).astype(int)

        future_dates = pd.date_range(
            start=ts.index[-1] + pd.Timedelta(weeks=1),
            periods=FORECAST_WEEKS,
            freq="W-MON"
        )

        forecast_df = pd.DataFrame({
            "Week_End": future_dates,
            "Forecast_Qty": forecast,
            "CI_Lower": np.maximum(np.round(conf_int[:, 0]), 0).astype(int),
            "CI_Upper": np.maximum(np.round(conf_int[:, 1]), 0).astype(int)
        })

        forecast_df.to_csv(FORECAST_DIR / f"{item}_forecast.csv", index=False)

        # -------------------------------
        # Save Model
        # -------------------------------
        with open(MODEL_DIR / f"{item}_autosarima.pkl", "wb") as f:
            pickle.dump(model, f, protocol=4)

        # -------------------------------
        # Plot
        # -------------------------------
        plt.figure(figsize=(14, 6))
        plt.plot(ts.index, ts.values, label="Historical")
        plt.plot(future_dates, forecast, label="Forecast", linestyle="--", marker="o")
        plt.fill_between(
            future_dates,
            forecast_df["CI_Lower"],
            forecast_df["CI_Upper"],
            alpha=0.2,
            label="Confidence Interval"
        )

        plt.axvline(ts.index[-1], linestyle=":", color="gray")
        plt.title(f"Auto-SARIMA Forecast — {item}")
        plt.xlabel("Week")
        plt.ylabel("Quantity")
        plt.legend()
        plt.grid(True, alpha=0.3)

        plt.savefig(FIG_DIR / f"{item}_forecast.png", dpi=200)
        plt.close()

    print("\n===== TRAINING + FORECASTING COMPLETED =====")


if __name__ == "__main__":
    main()