import pandas as pd
import os
import sys
from pathlib import Path

# -------------------------------------------------
# 0. Configuration & Paths
# -------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_FILE_PATH = PROJECT_ROOT / "data" / "raw" / "KPC___Despatch_Details_260924.xlsx"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "data_preparation"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Priority item codes
PRIORITY_ITEMS = [
    "082.04.030.50.",
    "085.00.003.50.",
    "082.03.110.50.",
    "336.40.401.50.",
    "351.03.301.50.",
    "993.00.311.00.",
    "084.19.001.50.",
    "082.08.000.50."
]

# Column mapping (Original Name: New Name)
COLUMN_MAPPING = {
    "MODEL": "MODEL",
    "OA DATE": "OA_DATE",
    "ITEM CODE": "ITEM_CODE",
    "QTY": "QTY",
    "UNIT PRICE": "UNIT_PRICE",
    "BASIC VALUE": "BASIC_VALUE",
    "ITEM DESCRIPTION": "ITEM_DESCRIPTION"
}

# -------------------------------------------------
# 1. Load & Initial Cleanup
# -------------------------------------------------
print(f"Loading raw dataset from: {RAW_FILE_PATH.name}...")
try:
    df = pd.read_excel(RAW_FILE_PATH)
except Exception as e:
    print(f"Error loading Excel file: {e}")
    sys.exit(1)

print("Filtering for 'ACR SPARES' and priority items...")
# Robust filtering
df["MODEL_STR"] = df["MODEL"].astype(str).str.strip().str.upper()
df["ITEM_CODE_STR"] = df["ITEM CODE"].astype(str).str.strip()

df_filtered = df[
    (df["MODEL_STR"] == "ACR SPARES") &
    (df["ITEM_CODE_STR"].isin(PRIORITY_ITEMS))
].copy()

# Select and rename columns
df_filtered = df_filtered[list(COLUMN_MAPPING.keys())].rename(columns=COLUMN_MAPPING)

# Date conversion
df_filtered['OA_DATE'] = pd.to_datetime(df_filtered['OA_DATE'], errors='coerce')
df_filtered = df_filtered.dropna(subset=['OA_DATE', 'QTY'])

# -------------------------------------------------
# 2. Diagnostics (from data_cleaning.py)
# -------------------------------------------------
print("\n===== DATA DIAGNOSTICS =====")
print(f"Total Rows: {len(df_filtered)}")
print(f"Columns: {list(df_filtered.columns)}")

print("\nMissing Values:")
print(df_filtered.isnull().sum())

print("\nQTY Distribution:")
print(df_filtered["QTY"].describe())

neg_qty = (df_filtered["QTY"] < 0).sum()
print(f"Negative QTY values: {neg_qty}")

# -------------------------------------------------
# 3. Data Splitting (from dataset.py)
# -------------------------------------------------
print("\nSplitting data into Training and Testing sets...")
df_filtered = df_filtered.sort_values(by='OA_DATE').reset_index(drop=True)

# Training: Jan 2021 to Dec 2023
train_df = df_filtered[
    (df_filtered['OA_DATE'] >= '2021-01-01') & 
    (df_filtered['OA_DATE'] <= '2023-12-31')
]

# Testing: Jan 2024 onwards
test_df = df_filtered[
    (df_filtered['OA_DATE'] >= '2024-01-01')
]

# -------------------------------------------------
# 4. Save Outputs
# -------------------------------------------------
train_path = PROCESSED_DIR / "train_dataset.csv"
test_path = PROCESSED_DIR / "test_dataset.csv"

train_df.to_csv(train_path, index=False)
test_df.to_csv(test_path, index=False)

print(f"\n===== PREPARATION COMPLETE =====")
print(f"Training set: {train_path.name} ({len(train_df)} rows)")
print(f"Testing set:  {test_path.name}  ({len(test_df)} rows)")

print("\nSummary per Item Code (Total Rows):")
print(df_filtered['ITEM_CODE'].value_counts())
