import pandas as pd
import numpy as np

csv_path = r'D:\KPCL_SparePartConsumption_Project\kpcl_selected_item_forecasting\data\raw\KPC___Despatch_Details_260924.csv'

try:
    print(f"Loading {csv_path}...")
    df_raw = pd.read_csv(csv_path)
    print(f"RAW SHAPE: {df_raw.shape}")
    
    column_mapping = {
        'INV DATE': 'Date', 'REGION': 'Region', 'MODEL': 'Model',
        'CUSTOMER NAME': 'Customer', 'TRANSPORTER': 'Transporter',
        'ITEM DESCRIPTION': 'Item_Description', 'QTY': 'QTY',
        'UNIT PRICE': 'Unit_Price', 'GROSS VALUE': 'Gross_Value',
        'TAX VALUE': 'Tax', 'OA DATE': 'Order_Date', 'PROMISE DATE': 'Promise_Date'
    }
    df = df_raw.rename(columns=column_mapping)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Promise_Date'] = pd.to_datetime(df['Promise_Date'], errors='coerce')
    df['Order_Date'] = pd.to_datetime(df['Order_Date'], errors='coerce')
    
    print(f"SHAPE AFTER RENAME: {df.shape}")
    print("Sample Columns present:")
    print([c for c in ['Date', 'Region', 'Model', 'QTY'] if c in df.columns])
    print(df[['Date', 'Region', 'Model', 'QTY']].head())
    
    pre_drop = len(df)
    df = df.dropna(subset=['Date'])
    post_drop = len(df)
    print(f"ROWS DROPPED (MISSING DATE): {pre_drop - post_drop}")
    print(f"SHAPE AFTER DROPNA: {df.shape}")

except Exception as e:
    import traceback
    traceback.print_exc()
