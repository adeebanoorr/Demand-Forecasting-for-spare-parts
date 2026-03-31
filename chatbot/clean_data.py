import pandas as pd

# ---------- Load Excel ----------
file_path = r"D:\KPCL_SparePartConsumption_Project\kpcl_selected_item_forecasting\data\raw\KPC___Despatch_Details_260924.xlsx"

df = pd.read_excel(file_path)

print("Original shape:", df.shape)

# ---------- Clean Column Names ----------
df.columns = (
    df.columns
    .str.strip()
    .str.replace(" ", "_")
    .str.replace(".", "")
)

# ---------- Convert Dates ----------
date_cols = [
    "INV_DATE", "PM_DATE", "OA_DATE", "SCHEDULE_SHIP",
    "PROMISE_DATE", "CUST_PO_DATE", "GCDATE",
    "EWAY_BILL_DATE", "EWB_VALIDITY_DATE"
]

for col in date_cols:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

# ---------- Handle Missing Values ----------

# Drop rows where QTY is missing (critical column)
if "QTY" in df.columns:
    df = df.dropna(subset=["QTY"])

# Fill important categorical columns
fill_cols = ["REGION", "ITEM_CODE", "CUSTOMER_NAME"]

for col in fill_cols:
    if col in df.columns:
        df[col] = df[col].fillna("Unknown")

# Fill numeric columns with 0
num_cols = df.select_dtypes(include=['int64', 'float64']).columns
df[num_cols] = df[num_cols].fillna(0)

# ---------- Remove duplicates ----------
df = df.drop_duplicates()

print("Cleaned shape:", df.shape)

# ---------- Save as CSV ----------
output_path = r"D:\KPCL_SparePartConsumption_Project\kpcl_selected_item_forecasting\chatbot\kpcl_cleaned.csv"

df.to_csv(output_path, index=False)

print("Cleaned CSV saved at:", output_path)