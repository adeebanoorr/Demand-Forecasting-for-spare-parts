import pandas as pd
import os
import sys

def clean_chatbot_data():
    """
    Cleans the raw spare parts despatch details and saves it for the chatbot.
    """
    # Paths
    # Current script is in chatbot/
    # Raw data is in ../data/raw/
    raw_path = os.path.join("..", "data", "raw", "KPC___Despatch_Details_260924.csv")
    output_path = os.path.join("backend", "spare_parts_data.csv")

    if not os.path.exists(raw_path):
        # Try XLSX if CSV not found (some environments might have one or the other)
        raw_path = os.path.join("..", "data", "raw", "KPC___Despatch_Details_260924.xlsx")
        if not os.path.exists(raw_path):
            print(f"Error: Raw data not found at {raw_path}")
            return

    print(f"Loading raw data from: {raw_path}")
    if raw_path.endswith('.csv'):
        df = pd.read_csv(raw_path)
    else:
        df = pd.read_excel(raw_path)

    print(f"Initial row count: {len(df)}")
    print(f"Columns found in raw data: {list(df.columns)}")
    # Strip whitespace from column names
    df.columns = [c.strip() for c in df.columns]

    # 1. basic Column rename/normalization if needed
    # The agent expects: ITEM_CODE, ITEM_DESCRIPTION, MODEL, QTY, UNIT_PRICE, 
    # BASIC_VALUE, TAX_VALUE, GROSS_VALUE, REGION, INV_DATE, PROMISE_DATE, 
    # SCHEDULE_SHIP, INVNO, CUSTOMER_NAME
    
    # Precise mapping based on observed raw CSV headers
    mapping = {
        'ITEM CODE': 'ITEM_CODE',
        'ITEM DESCRIPTION': 'ITEM_DESCRIPTION',
        'INV.NO.': 'INVNO',
        'INV DATE': 'INV_DATE',
        'P.M. DATE': 'PROMISE_DATE',
        'SCHEDULE SHIP': 'SCHEDULE_SHIP',
        'CUST NAME': 'CUSTOMER_NAME',
        'BASIC VALUE IN FC': 'BASIC_VALUE',
        'GROSS VALUE IN FC': 'GROSS_VALUE',
        'UNIT PRICE': 'UNIT_PRICE',
        'TAX VALUE': 'TAX_VALUE'
    }
    
    # Apply mapping only for existing columns
    df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})

    # Ensure critical columns exist even if not renamed
    if 'ITEM_CODE' not in df.columns and 'ITEM CODE' in df.columns:
        df['ITEM_CODE'] = df['ITEM CODE']
    if 'CUSTOMER_NAME' not in df.columns and 'CUST NAME' in df.columns:
        df['CUSTOMER_NAME'] = df['CUST NAME']

    # 2. Date Cleaning
    print("Converting dates...")
    date_cols = ['INV_DATE', 'PROMISE_DATE', 'SCHEDULE_SHIP']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # 3. Numeric Cleaning
    print("Cleaning numeric columns...")
    num_cols = ["QTY", "BASIC_VALUE", "GROSS_VALUE", "UNIT_PRICE", "TAX_VALUE"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # 4. Text Cleaning (The "Clean" columns agent.py creates on-the-fly, but better to have them here)
    print("Cleaning text columns...")
    if 'ITEM_CODE' in df.columns:
        df["ITEM_CODE_CLEAN"] = df["ITEM_CODE"].astype(str).str.replace(".", "", regex=False).str.strip()
    
    if 'MODEL' in df.columns:
        df["MODEL_CLEAN"]  = df["MODEL"].astype(str).str.strip().str.lower()
    
    if 'REGION' in df.columns:
        df["REGION_CLEAN"] = df["REGION"].astype(str).str.strip().str.lower()
    
    if 'CUSTOMER_NAME' in df.columns:
        df["CUSTOMER_NAME_CLEAN"] = df["CUSTOMER_NAME"].astype(str).str.strip().str.lower().str.replace(r"\s+", " ", regex=True)

    # 5. Performance Metrics (Pre-calculate for the agent)
    print("Calculating performance metrics...")
    if 'INV_DATE' in df.columns and 'PROMISE_DATE' in df.columns:
        df["delayed"] = (df["INV_DATE"] > df["PROMISE_DATE"]).astype(int)
        df["DELAY_DAYS"] = (df["INV_DATE"] - df["PROMISE_DATE"]).dt.days.clip(lower=0)
        df["on_time"] = (df["INV_DATE"] <= df["PROMISE_DATE"]).astype(int)
        df["is_on_time"] = df["on_time"]

    # 6. Time Dimensions
    if 'INV_DATE' in df.columns:
        df["YEAR"] = df["INV_DATE"].dt.year
        df["QUARTER"] = df["INV_DATE"].dt.quarter
        df["MONTH"] = df["INV_DATE"].dt.month
        df["MONTH_NAME"] = df["INV_DATE"].dt.month_name()

    # Drop rows without critical info
    df = df.dropna(subset=['INV_DATE', 'QTY', 'ITEM_CODE'])

    # Save to CSV
    print(f"Saving cleaned data to: {output_path}")
    df.to_csv(output_path, index=False)
    print(f"Done! Final row count: {len(df)}")

if __name__ == "__main__":
    clean_chatbot_data()
