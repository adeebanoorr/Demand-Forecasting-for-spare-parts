import pandas as pd
import os
from statsmodels.tsa.seasonal import MSTL
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Project root resolution
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

# Load dataset
file_path = PROJECT_ROOT / "data" / "processed" / "data_preparation" / "train_dataset.csv"

# Output folder
output_dir = PROJECT_ROOT / "reports" / "figures" / "mstl_analysis"
os.makedirs(output_dir, exist_ok=True)

print("Loading processed dataset...")
df = pd.read_csv(file_path)

df['OA_DATE'] = pd.to_datetime(df['OA_DATE'])

# Monthly aggregation
monthly = (
    df.groupby([
        "ITEM_CODE",
        pd.Grouper(key="OA_DATE", freq="ME")
    ])["QTY"]
    .sum()
    .reset_index()
)

# Output dir handled above

print("Running MSTL per item...")

for item, data in monthly.groupby("ITEM_CODE"):

    ts = data.set_index("OA_DATE")["QTY"].asfreq("ME").fillna(0)
    n = len(ts)

    if n < 6:
        print(f"Skipping {item} (too few data points: {n})")
        continue

    # Choose VALID seasonal period
    if n >= 24:
        period = 12
    elif n >= 12:
        period = 6
    elif n >= 8:
        period = 3
    else:
        period = 2

    # Ensure period < n/2
    if period >= n / 2:
        period = int(n / 2) - 1

    if period < 2:
        print(f"Skipping {item} (cannot determine valid seasonal period)")
        continue

    print(f"Running MSTL for {item} | Observations: {n} | Period: {period}")

    mstl = MSTL(ts, periods=[period])
    result = mstl.fit()

    # Custom Plotting for better aesthetics
    fig, axes = plt.subplots(4, 1, figsize=(12, 14), sharex=True, facecolor='white')
    
    # Define colors
    colors = {
        'observed': '#2c3e50',  # Dark Blue
        'trend': '#e74c3c',     # Red
        'seasonal': '#27ae60',  # Green
        'residual': '#7f8c8d'   # Grey
    }

    # 1. Observed
    axes[0].plot(result.observed, color=colors['observed'], label='Observed', linewidth=1.5, marker='o', markersize=4, alpha=0.8)
    axes[0].set_ylabel('Observed', fontweight='bold')
    axes[0].set_title(f"MSTL Decomposition — Item {item}", fontsize=16, fontweight='bold', pad=20)
    axes[0].grid(True, linestyle='--', alpha=0.6)

    # 2. Trend
    axes[1].plot(result.trend, color=colors['trend'], label='Trend', linewidth=2)
    axes[1].set_ylabel('Trend', fontweight='bold')
    axes[1].grid(True, linestyle='--', alpha=0.6)

    # 3. Seasonal
    axes[2].plot(result.seasonal, color=colors['seasonal'], label='Seasonal', linewidth=1.5)
    axes[2].set_ylabel('Seasonal', fontweight='bold')
    axes[2].grid(True, linestyle='--', alpha=0.6)

    # 4. Residual
    axes[3].scatter(result.resid.index, result.resid, color=colors['residual'], label='Residual', s=15, alpha=0.6)
    axes[3].axhline(0, color='black', linestyle='-', linewidth=0.8)
    axes[3].set_ylabel('Residual', fontweight='bold')
    axes[3].grid(True, linestyle='--', alpha=0.6)

    # Common formatting
    for ax in axes:
        ax.set_facecolor('white')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.tick_params(axis='both', which='major', labelsize=10)

    plt.xlabel('Date', fontweight='bold')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    plot_path = os.path.join(output_dir, f"MSTL_{item}.png")
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()

print("\nAll MSTL analyses completed.")