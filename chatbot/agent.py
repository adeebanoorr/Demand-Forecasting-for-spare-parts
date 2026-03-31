import pandas as pd
import re
import os
import datetime
import json
import hashlib
from collections import OrderedDict
from langchain_ollama import OllamaLLM
import guardrails as gd
from pydantic import BaseModel, Field

# =============================================================================
# CONFIG & LOAD
# =============================================================================
DEBUG = True
LOG_FILE = "chatbot_logs.txt"
CACHE_FILE = "chatbot_cache.json"
file_path = r"D:\KPCL_SparePartConsumption_Project\kpcl_selected_item_forecasting\chatbot\kpcl_cleaned.csv"

if not os.path.exists(file_path):
    print(f"Error: Dataset not found at {file_path}")
    exit()

df = pd.read_csv(file_path)

# Data Cleaning & Helpers
df['INV_DATE'] = pd.to_datetime(df['INV_DATE'], errors='coerce')
df['PROMISE_DATE'] = pd.to_datetime(df['PROMISE_DATE'], errors='coerce')
df['SCHEDULE_SHIP'] = pd.to_datetime(df['SCHEDULE_SHIP'], errors='coerce')

# Performance Optimization: Precompute YEAR to avoid repeated .dt calls
df["YEAR"] = df["INV_DATE"].dt.year

df["ITEM_CODE_CLEAN"] = df["ITEM_CODE"].astype(str).str.replace(".", "", regex=False).str.strip()
df["MODEL_CLEAN"]  = df["MODEL"].astype(str).str.strip().str.lower()
df["REGION_CLEAN"] = df["REGION"].astype(str).str.strip().str.lower()
df["CUSTOMER_NAME_CLEAN"] = df["CUSTOMER_NAME"].astype(str).str.strip().str.lower().str.replace(r"\s+", " ", regex=True)

ALLOWED_COLS = [
    "ITEM_CODE", "ITEM_DESCRIPTION", "MODEL", "QTY", "UNIT_PRICE",
    "BASIC_VALUE", "TAX_VALUE", "GROSS_VALUE", "REGION", "INV_DATE",
    "ITEM_CODE_CLEAN", "CUSTOMER_NAME_CLEAN", "MODEL_CLEAN", "REGION_CLEAN",
    "PROMISE_DATE", "SCHEDULE_SHIP", "on_time", "is_on_time", "delayed", "INVNO", "YEAR"
]

for col in ["QTY", "BASIC_VALUE", "GROSS_VALUE", "UNIT_PRICE", "TAX_VALUE"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Performance Optimization: Precompute unique values and split dictionaries
ALL_MODELS  = sorted(df["MODEL_CLEAN"].dropna().unique().tolist())
ALL_REGIONS = sorted(df["REGION_CLEAN"].dropna().unique().tolist())
ALL_CUSTOMERS = sorted(df["CUSTOMER_NAME_CLEAN"].dropna().unique().tolist())
ALL_YEARS   = sorted(df["YEAR"].dropna().unique().tolist())

DF_BY_YEAR   = {y: d for y, d in df.groupby("YEAR")}
DF_BY_REGION = {r: d for r, d in df.groupby("REGION_CLEAN")}
DF_BY_MODEL  = {m: d for m, d in df.groupby("MODEL_CLEAN")}
DF_BY_CUSTOMER = {c: d for c, d in df.groupby("CUSTOMER_NAME_CLEAN")}

# PRECOMPUTED AGGREGATES (Ultra Fast Path)
AGG = {
    "revenue_by_year": df.groupby("YEAR")["GROSS_VALUE"].sum().sort_values(ascending=False),
    "qty_by_region": df.groupby("REGION_CLEAN")["QTY"].sum().sort_values(ascending=False),
    "qty_by_model": df.groupby("MODEL_CLEAN")["QTY"].sum().sort_values(ascending=False),
    "revenue_by_region": df.groupby("REGION_CLEAN")["GROSS_VALUE"].sum().sort_values(ascending=False),
}

print(f"Data Loaded: {df.shape[0]:,} rows x {df.shape[1]} columns")

# Caching Logic
CACHE_LIMIT = 2000

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return OrderedDict(json.load(f))
        except: return OrderedDict()
    return OrderedDict()

def get_cache(key):
    if key in cache:
        cache.move_to_end(key)
        return cache[key]
    return None

def set_cache(key, value):
    cache[key] = value
    cache.move_to_end(key)
    if len(cache) > CACHE_LIMIT:
        cache.popitem(last=False)
    save_cache()

def save_cache():
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except: pass

cache = load_cache()
context = {"last_year": None, "last_region": None}

# =============================================================================
# UTILS
# =============================================================================
def log_event(query, raw_response, formatted_ans, error=None):
    with open(LOG_FILE, "a") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"\n[{timestamp}] Query: {query}\n")
        f.write(f"LLM Response:\n{raw_response}\n")
        if error: f.write(f"Error: {error}\n")
        else: f.write(f"Final Answer: {formatted_ans}\n")
        f.write("-" * 40 + "\n")

def restore_item_format(val):
    if isinstance(val, str) and val.isdigit():
        match = df[df["ITEM_CODE_CLEAN"] == val]
        if not match.empty:
            return match["ITEM_CODE"].iloc[0]
    return val

def guard_columns(code):
    # Context-aware regex: Only check strings that appear inside indexing brackets or specific pandas methods
    # df['col'], df[["col1", "col2"]], .loc[:, "col"], .groupby("col"), .sort_values("col")
    indexing_patterns = [
        r"\[\s*['\"]([a-zA-Z0-9_]+)['\"]\s*\]",
        r"\.loc\[.*?,?\s*['\"]([a-zA-Z0-9_]+)['\"]\s*\]",
        r"\.groupby\(\s*(?:\[\s*)?['\"]([a-zA-Z0-9_]+)['\"]",
        r"\.sort_values\(\s*(?:\[\s*)?['\"]([a-zA-Z0-9_]+)['\"]",
        r"\.rename\(columns=\{['\"]([a-zA-Z0-9_]+)['\"]"
    ]
    
    potential_cols = []
    for pattern in indexing_patterns:
        potential_cols.extend(re.findall(pattern, code))
    
    for c in potential_cols:
        if c.isdigit(): continue 
        if c not in ALLOWED_COLS:
            return False, f"Invalid column: {c}. Use ONLY: {', '.join(sorted(list(ALLOWED_COLS)))}"
    return True, None

def normalize_query(q):
    """
    Converts user input into a clean, structured form for better cache hits and LLM accuracy.
    Note: The normalized query is used as the PRIMARY CACHE KEY.
    """
    # 1. Basic Cleaning
    q = q.lower().strip().strip("?").strip("!")
    
    # 2. Punctuation Cleanup (Example: 2021,2022 -> 2021 2022)
    q = re.sub(r"[,\-]", " ", q)
    
    # 3. Remove standalone filler phrases (safer than global sub)
    fillers = [
        "please", "can you", "show me", "tell me", "what is", "what was", "what were", 
        "find", "search for", "give me", "list", "calculate", "details of", "information about",
        "could you", "i want to know", "thank you", "thanks", "i'm asking", "made"
    ]
    for f in fillers:
        q = re.sub(rf"\b{f}\b", "", q)
    
    # Special case: 'the/a/an' only at start or as standalone
    q = re.sub(r"^(the|a|an)\s+", "", q)
    q = re.sub(r"\s+(the|a|an)\b", " ", q)
    
    # 4. Standardize Metrics
    q = q.replace("gross value", "revenue").replace("earnings", "revenue").replace("sales value", "revenue")
    q = q.replace("quantity", "qty").replace("number of", "qty").replace("units", "qty")
    q = q.replace("unique invoice", "unique_invoices").replace("total unique invoices", "unique_invoices")
    
    # 5. Standardize Yearly breakdowns
    q = q.replace("every year", "by year").replace("each year", "by year").replace("annually", "by year")
    
    def region_replacer(match):
        preposition = match.group(1)
        word = match.group(2)
        if word in ALL_REGIONS: return f"region {word}"
        if word in ALL_MODELS: return f"model {word}"
        return f"{preposition} {word}"

    q = q.replace(" city", "").replace(" location", "").replace(" area", "")
    q = re.sub(r"\b(from|in|at|for)\s+(\d{4})\b", r"\2", q)
    q = re.sub(r"\b(from|in|at|for)\s+([a-z]{3,})\b", region_replacer, q)
    
    # 7. Final cleanup and conditional "total" prefix
    q = re.sub(r"\s+", " ", q).strip()
    
    # DONT add "total" if it's already structured or asking "which/who/list/top"
    if any(w in q for w in ["revenue", "qty", "unique_invoices"]):
        if not any(w in q for w in ["total", "top", "most", "least", "best", "avg", "average", "who", "which", "list", "by"]):
            q = "total " + q
            
    return q

def classify_query(q):
    """Categorizes queries using a scoring system for better intent detection."""
    q = q.lower().strip().strip(".")
    greeting_patterns = [
        r"\bhi\b", r"\bhello\b", r"\bhey\b", r"\bbye\b", r"\bexit\b", r"\bquit\b",
        r"\bthanks\b", r"\bthank you\b", r"\bgood morning\b", r"\bgood evening\b",
        r"\bhelp\b", r"\bhow can you help\b", r"\bwhat can you do\b"
    ]
    if any(re.search(p, q) for p in greeting_patterns):
        return "GREETING"
    
    # Intent Scoring
    score = {
        "agg":  sum(1 for w in ["total", "sum", "avg", "average", "revenue", "qty", "quantity", "value", "tax"] if w in q),
        "rank": sum(1 for w in ["top", "most", "least", "best", "highest", "lowest", "which", "who"] if w in q),
        "data": sum(1 for w in ["part", "item", "code", "model", "region", "customer", "invoice", "detail", "record", "dispatch"] if w in q)
    }
    
    # Domain keywords and year check
    if any(score.values()) or re.search(r"\b20\d{2}\b", q):
        if score["rank"] > score["agg"]: return "RANKING"
        if score["agg"] > 0: return "AGGREGATION"
        return "DATA_QUERY"
        
    return "OFF_TOPIC"

def extract_filters(q):
    """Centralized tool to pull year, region, model and customer from any query string."""
    filters = {"year": None, "region": None, "model": None, "customer": None}
    
    year_match = re.search(r"\b(20\d{2})\b", q)
    if year_match: filters["year"] = int(year_match.group(1))
    
    q_low = q.lower()
    for r in ALL_REGIONS:
        if re.search(rf"\b{re.escape(r)}\b", q_low) or f"'{r}'" in q_low:
            filters["region"] = r
            break
            
    for m in ALL_MODELS:
        if re.search(rf"\b{re.escape(m)}\b", q_low):
            filters["model"] = m
            break

    for c in ALL_CUSTOMERS:
        if c in q_low:
            filters["customer"] = c
            break
            
    if not filters["customer"]:
        for c in ALL_CUSTOMERS:
            # Check if a significant prefix of the customer name is mentioned (min 8 chars)
            # This handles "Gargi Engineering" matching "Gargi Engineering Enterprises..."
            prefix = c[:12] if len(c) > 12 else c
            if len(prefix) >= 8 and prefix in q_low:
                filters["customer"] = c
                break
            
    return filters

def update_context(q):
    f = extract_filters(q)
    if f["year"]: context["last_year"] = str(f["year"])
    if f["region"]: context["last_region"] = f["region"]

def apply_memory(q):
    """Returns rewritten query and extracted filters (applying context if needed)."""
    filters = {}
    q_low = q.lower()
    
    # 1. Handle Relative Years
    if "next year" in q_low and context["last_year"]:
        filters["year"] = int(context["last_year"]) + 1
    elif "previous year" in q_low and context["last_year"]:
        filters["year"] = int(context["last_year"]) - 1
    elif "this year" in q_low or "same year" in q_low:
        if context["last_year"]: filters["year"] = int(context["last_year"])
        
    # 2. Handle Region Memory
    if any(w in q_low for w in ["that region", "this region", "same region"]):
        if context["last_region"]: filters["region"] = context["last_region"]
        
    # 3. Handle General Context Fallback (if no explicit filters found in q)
    raw_filters = extract_filters(q)
    if not filters.get("year") and not raw_filters["year"] and context["last_year"]:
        if any(w in q_low for w in ["total", "how many", "revenue", "qty"]):
             filters["year"] = int(context["last_year"])
             
    if not filters.get("region") and not raw_filters["region"] and context["last_region"]:
        if any(w in q_low for w in ["total", "how many", "revenue", "qty"]):
            filters["region"] = context["last_region"]

    # Merge found filters with context-derived ones
    final_filters = {**raw_filters, **filters}
    return q, final_filters

def deterministic_handler(processed_q, filters):
    """Answers simple total/count/ranking queries using O(1) indexes and a Hybrid Path."""
    q_clean = processed_q.lower().strip()
    
    # Fast path: Priority Filter Logic
    target_df = df
    if filters.get("year") and filters["year"] in DF_BY_YEAR:
        target_df = DF_BY_YEAR[filters["year"]]
        
    if filters.get("customer") and filters["customer"] in DF_BY_CUSTOMER:
        if target_df is df: target_df = DF_BY_CUSTOMER[filters["customer"]]
        else: target_df = target_df[target_df["CUSTOMER_NAME_CLEAN"] == filters["customer"]]
        
    if filters.get("region") and filters["region"] in DF_BY_REGION:
        if target_df is df: target_df = DF_BY_REGION[filters["region"]]
        else: target_df = target_df[target_df["REGION_CLEAN"] == filters["region"]]
            
    if filters.get("model") and filters["model"] in DF_BY_MODEL:
        if target_df is df: target_df = DF_BY_MODEL[filters["model"]]
        else: target_df = target_df[target_df["MODEL_CLEAN"] == filters["model"]]

    # Hybrid Ranking (Handle simple "top 1" without template/LLM)
    if "top 1" in q_clean or "best" in q_clean or "highest" in q_clean:
        metric = "GROSS_VALUE" if "revenue" in q_clean else "QTY"
        
        if "item description" in q_clean or "description" in q_clean:
            return target_df.groupby("ITEM_DESCRIPTION")[metric].sum().idxmax()
        if "item" in q_clean or "code" in q_clean:
            return target_df.groupby("ITEM_CODE_CLEAN")[metric].sum().idxmax()
        if "customer" in q_clean:
            return target_df.groupby("CUSTOMER_NAME_CLEAN")[metric].sum().idxmax()
        if "region" in q_clean:
            return target_df.groupby("REGION_CLEAN")[metric].sum().idxmax()

    ranking_keywords = ["top", "most", "least"]
    # Only skip if it's a "Top N" (N > 1) which needs Template Layer
    if any(k in q_clean for k in ranking_keywords) and not re.search(r"top 1\b", q_clean): 
        return None
    
    confidence_msg = ""
    # Confidence Layer: Warning for tiny samples, but non-blocking
    if 0 < len(target_df) < 3:
        confidence_msg = f" (Note: Low Confidence - only {len(target_df)} record(s) found)"

    # Remove filters from query to find metric
    q_norm = q_clean
    if filters.get("year"): q_norm = q_norm.replace(str(filters["year"]), "")
    if filters.get("region"): q_norm = q_norm.replace(filters["region"], "")
    if filters.get("model"): q_norm = q_norm.replace(filters["model"], "")
    if filters.get("customer"): q_norm = q_norm.replace(filters["customer"], "")
    q_norm = re.sub(r"\s+", " ", q_norm).strip()

    metrics = {
        "revenue": lambda d: f"{d['GROSS_VALUE'].sum():,.2f}",
        "gross value": lambda d: f"{d['GROSS_VALUE'].sum():,.2f}",
        "quantity": lambda d: f"{d['QTY'].sum():,.0f}",
        "qty": lambda d: f"{d['QTY'].sum():,.0f}",
        "parts sold": lambda d: f"{d['QTY'].sum():,.0f}",
        "parts": lambda d: f"{d['QTY'].sum():,.0f}",
        "avg": lambda d: f"{d['QTY'].mean() if 'qty' in q_clean else d['GROSS_VALUE'].mean():,.2f}",
        "average": lambda d: f"{d['QTY'].mean() if 'qty' in q_clean else d['GROSS_VALUE'].mean():,.2f}",
        "efficiency": lambda d: f"{(d['INV_DATE'] <= d['PROMISE_DATE']).mean() * 100:.2f}%",
        "unique invoice": lambda d: f"{d['INVNO'].nunique():,}",
        "unique invoices": lambda d: f"{d['INVNO'].nunique():,}",
        "invoice": lambda d: f"{len(d):,}",
        "invoices": lambda d: f"{len(d):,}",
        "customer": lambda d: f"{d['CUSTOMER_NAME_CLEAN'].nunique():,}",
        "customers": lambda d: f"{d['CUSTOMER_NAME_CLEAN'].nunique():,}",
        "tax": lambda d: f"{d['TAX_VALUE'].sum():,.2f}"
    }
    
    for k, func in metrics.items():
        if re.search(rf"\b{re.escape(k)}\b", q_norm):
             res = func(target_df)
             return f"{res}{confidence_msg}"
    return None

def template_handler(q, filters=None):
    """Bypasses LLM for high-frequency structured patterns like 'top 5' or 'by year'."""
    q_clean = q.lower().strip()
    nums = re.findall(r"\d+", q_clean)
    n = int(nums[0]) if nums else 5
    
    # Apply context filters if provided
    temp_df = df
    if filters:
        if filters.get("year") and filters["year"] in DF_BY_YEAR:
            temp_df = DF_BY_YEAR[filters["year"]]
        if filters.get("customer") and filters["customer"] in DF_BY_CUSTOMER:
            if temp_df is df: temp_df = DF_BY_CUSTOMER[filters["customer"]]
            else: temp_df = temp_df[temp_df["CUSTOMER_NAME_CLEAN"] == filters["customer"]]
        if filters.get("region") and filters["region"] in DF_BY_REGION:
            if temp_df is df: temp_df = DF_BY_REGION[filters["region"]]
            else: temp_df = temp_df[temp_df["REGION_CLEAN"] == filters["region"]]
        if filters.get("model") and filters["model"] in DF_BY_MODEL:
            if temp_df is df: temp_df = DF_BY_MODEL[filters["model"]]
            else: temp_df = temp_df[temp_df["MODEL_CLEAN"] == filters["model"]]

    # Pattern 1: Ranking (Top N)
    if "top" in q_clean or "best" in q_clean or "highest" in q_clean:
        metric = "GROSS_VALUE" if "revenue" in q_clean else "QTY"
        if "item" in q_clean:
            col = "ITEM_DESCRIPTION" if "description" in q_clean else "ITEM_CODE_CLEAN"
            return temp_df.groupby(col)[metric].sum().nlargest(n).sort_values(ascending=False)
        if "customer" in q_clean:
            return temp_df.groupby("CUSTOMER_NAME_CLEAN")[metric].sum().nlargest(n).sort_values(ascending=False)
        if "region" in q_clean:
            return temp_df.groupby("REGION_CLEAN")[metric].sum().nlargest(n).sort_values(ascending=False)

    # Pattern 2: Category Breakdown
    if "by year" in q_clean: return temp_df.groupby("YEAR")["GROSS_VALUE" if "revenue" in q_clean else "QTY"].sum().sort_values(ascending=False)
    if "by region" in q_clean: return temp_df.groupby("REGION_CLEAN")["GROSS_VALUE" if "revenue" in q_clean else "QTY"].sum().sort_values(ascending=False)
    if "by model" in q_clean: return temp_df.groupby("MODEL_CLEAN")["GROSS_VALUE" if "revenue" in q_clean else "QTY"].sum().sort_values(ascending=False)

    # Pattern 3: On-Time / Delay Performance
    if "on time" in q_clean or "efficiency" in q_clean: return f"{(temp_df['INV_DATE'] <= temp_df['PROMISE_DATE']).mean() * 100:.2f}%"
    if "delayed" in q_clean: return f"{(temp_df['INV_DATE'] > temp_df['PROMISE_DATE']).mean() * 100:.2f}%"
    if "on day of promise" in q_clean or "on the day of promise" in q_clean:
        return f"{(temp_df['INV_DATE'] == temp_df['PROMISE_DATE']).mean() * 100:.2f}%"

    # Pattern 4: Correlation (Dispatch vs Qty)
    if "correlation" in q_clean or ("delay" in q_clean and "qty" in q_clean):
        corr = temp_df["QTY"].corr(temp_df["delayed"])
        return f"Correlation Coefficient: {corr:.4f} ({'Weak' if abs(corr) < 0.2 else 'Strong'} Relationship)"

    # Pattern 5: Small Fallbacks
    if "most sold item" in q_clean: return temp_df.groupby("ITEM_CODE_CLEAN")["QTY"].sum().idxmax()
    if "best region" in q_clean or "which region highest revenue" in q_clean:
        return temp_df.groupby("REGION_CLEAN")["GROSS_VALUE"].sum().idxmax()

    # Pattern 12: On-time dispatch %
    if "on time" in q_clean:
        return f"{(temp_df['INV_DATE'] <= temp_df['PROMISE_DATE']).mean() * 100:.2f}%"
        
    return None

# =============================================================================
# HYBRID GUARDRAILS (Phase 5)
# =============================================================================
class SparePartsAnalysis(BaseModel):
    plan: str = Field(description="Step-by-step logic for the analysis")
    python_code: str = Field(description="The executable pandas code that assigns the result to 'ans'")

# Initialize the Guard with the Pydantic schema
guard = gd.Guard.for_pydantic(output_class=SparePartsAnalysis)

# =============================================================================
# LLM & PROMPT
# =============================================================================
llm = OllamaLLM(model="mistral")

PROMPT_TEMPLATE = """You are a professional KPCL Data Analyst.

STRICT RULES:
1. ALWAYS provide a "Plan" (markdown comment) explaining your logic.
2. ALWAYS wrap Python code in <python>...</python> and assign ONLY the final result to `ans`.
3. NEVER add conversational filler (no "Hello", "Sure", "Here is the result"). 
4. NEVER mention Python, Pandas, Mistral, or any technical library names.
5. Filter for specific years ONLY if mentioned in the query.
6. "Total Number/Quantity" ALWAYS means `df['QTY'].sum()`. Use a simple filter: `df[df['col'] == 'val']['QTY'].sum()`.
7. "Total Invoices" (no 'unique' keyword) ALWAYS means `len(df)` (Total records).
8. "Total Unique Invoices" ALWAYS means `df['INVNO'].nunique()`.
9. "Most/Least sold" ALWAYS refers to the `.sum()` of the `QTY` column.
10. FOR MULTI-STEP QUERIES (e.g. "revenue of top item"): First find the ID, then filter for it, and FINALLY assign the value to `ans`.
11. ABSOLUTELY NEVER use `.map()` or string `.join()` on pandas Series.
12. ALWAYS ensure the FINAL numerical or string result is assigned to `ans` at the VERY LAST line.
13. To partial match models (e.g. "acr services"), use `.str.contains("acr-service", case=False)` on CLEAN columns.
14. 'On-Time Dispatch %' = `(df['INV_DATE'] <= df['PROMISE_DATE']).mean() * 100`.
15. Filter for specific years ONLY if mentioned. NEVER assume years from examples.
16. FOR "WHO" OR "WHICH" QUESTIONS: The final `ans` MUST be a category name (e.g., CUSTOMER_NAME_CLEAN or ITEM_CODE_CLEAN), NOT a numeric sum or value.
17. FOR "EVERY YEAR" OR "ANNUALLY": Use `df.groupby('YEAR')['GROSS_VALUE'].sum()` and return a dictionary or clean list.
18. NEVER return raw tuples like `('Name', 100)`. Assign ONLY the name or the primary metric requested to `ans`.

OUTPUT FORMAT:
ALWAYS return a valid JSON object matching this schema:
{{
  "plan": "your logic here",
  "python_code": "your code here"
}}

DATA SCHEMA:
- ITEM_CODE_CLEAN: Primary ID Number (use for 'code')
- ITEM_DESCRIPTION: Human-readable name (use for 'description')
- MODEL_CLEAN, REGION_CLEAN, CUSTOMER_NAME_CLEAN: Filter columns
- QTY, UNIT_PRICE, BASIC_VALUE, TAX_VALUE, GROSS_VALUE (Total Revenue)
- INVNO: Invoice number
- INV_DATE, PROMISE_DATE, YEAR: Dates/Years

EXPLICIT EXAMPLES:
- Q: what was the total revenue made by the most sold item
  A: {{
    "plan": "Find the item code with the highest sum of QTY, then calculate the total GROSS_VALUE for that specific item code.",
    "python_code": "top_id = df.groupby('ITEM_CODE_CLEAN')['QTY'].sum().idxmax()\nans = df[df['ITEM_CODE_CLEAN'] == top_id]['GROSS_VALUE'].sum()"
  }}

- Q: who is the top customer by quantity in 2024
  A: {{
    "plan": "Filter for 2024, group by CUSTOMER_NAME_CLEAN, sum QTY, and get the identity of the max.",
    "python_code": "df24 = df[df['YEAR'] == 2024]\nans = df24.groupby('CUSTOMER_NAME_CLEAN')['QTY'].sum().idxmax()"
  }}
- Q: revenue of the most sold item in 2023?
  A: {{
    "plan": "Find item code with highest sum QTY in 2023, then sum its GROSS_VALUE.",
    "python_code": "df23 = df[df['YEAR'] == 2023]\ntop_item = df23.groupby('ITEM_CODE_CLEAN')['QTY'].sum().idxmax()\nans = df23[df23['ITEM_CODE_CLEAN'] == top_item]['GROSS_VALUE'].sum()"
  }}
- Q: what is our On-Time Dispatch % for ahmedabad?
  A: {{
    "plan": "Filter for Ahmedabad, check INV_DATE <= PROMISE_DATE, return as percentage.",
    "python_code": "df_loc = df[df['REGION_CLEAN'] == 'ahmedabad']\nans = f'{{(df_loc[\"INV_DATE\"] <= df_loc[\"PROMISE_DATE\"]).mean() * 100:.2f}}%'"
  }}
- Q: which year has highest revenue?
  A: {{
    "plan": "Group by year, sum revenue, and find the year (index) with the max value.",
    "python_code": "ans = df.groupby('YEAR')['GROSS_VALUE'].sum().idxmax()"
  }}
- Q: total unique invoices in 2021 and 2022?
  A: {{
    "plan": "Combine years with OR (|) and brackets. Unique count of INVNO.",
    "python_code": "df_f = df[(df['YEAR'] == 2021) | (df['YEAR'] == 2022)]\nans = df_f['INVNO'].nunique()"
  }}

TYPE: {q_type}
{context_block}
{error_block}
Question: {question}
Output:"""

def build_prompt(question, history, q_type, context_block=""):
    error_block = ""
    if history:
        error_block = "\n# --- RALPH LOOP ERROR FEEDBACK ---\n"
        for i, (code, error) in enumerate(history):
            if "datetime64" in error: error_block += "# FIX: NEVER use .str on INV_DATE.\n"
            error_block += f"# Attempt {i+1} failed: {error}\n"
    return PROMPT_TEMPLATE.format(question=question, error_block=error_block, q_type=q_type, context_block=context_block)

# --- STRICT EXEC SANDBOX ---
# Blocks escalation to dangerous built-ins like eval() or getattr()
SAFE_GLOBALS = {
    "df": df,
    "pd": pd,
    "__builtins__": {} # Remove access to all standard built-ins by default
}

# Explicitly whitelist only safe logic functions
SAFE_LOCALS = {
    "len": len, "sum": sum, "max": max, "min": min, "abs": abs, "round": round,
    "range": range, "zip": zip, "enumerate": enumerate,
    "str": str, "int": int, "float": float, "bool": bool, "list": list, "dict": dict,
}

def extract_code(text):
    match = re.search(r"<python>(.*?)</python>", text, re.DOTALL)
    if match: return match.group(1).strip()
    return "\n".join([l for l in text.splitlines() if "=" in l or "df[" in l])

def run_code(code):
    if not code: return None, "No code provided."
    
    # Security: Blocks any import statement or file operations (open())
    # Also enforces column-level restrictions via the regex guard below.
    if "import" in code or "open(" in code: return None, "Security Violation."
    
    if "__" in code:
        return None, "Security Violation: dunder access blocked."

    forbidden = ["eval", "exec", "os.", "sys.", "subprocess", "lambda", "apply("]
    if any(f in code for f in forbidden):
        return None, "Security Violation: forbidden keyword detected."

    code = re.sub(r"df\[[\"\']ITEM_CODE[\"\']\]", "df[\"ITEM_CODE_CLEAN\"]", code)
    code = re.sub(r"\.ITEM_CODE\b", ".ITEM_CODE_CLEAN", code)
    ok, err = guard_columns(code)
    if not ok: return None, err
    
    # Run in strict sandbox
    current_locals = SAFE_LOCALS.copy()
    try:
        exec(code, SAFE_GLOBALS, current_locals)
        return current_locals.get("ans"), None
    except Exception as e: return None, str(e)

import hashlib

def ask_ai(q):
    start_time = datetime.datetime.now()
    MAX_EXEC_TIME = 5.0  # Increased for local latency
    
    # Step 1: Normalize Query (Layer Added)
    original_q = q
    
    # Intelligent Query Rewriting
    q_low = q.lower()
    if "highest revenue" in q_low:
        q = q.replace("highest revenue", "which has highest revenue")
    if "focus" in q_low or "better revenue" in q_low:
        if not any(w in q_low for w in ["best", "highest", "top"]):
            q = q + " best"
    if "dispatch delays" in q_low and "qty" in q_low:
        q = "correlation between qty and dispatch delays"
        
    q = normalize_query(q)
    if DEBUG and original_q.lower().strip() != q:
        print(f"  [Normalization]: '{original_q}' -> '{q}'")

    q_type = classify_query(q)
    
    if q_type == "GREETING": 
        return "KPCL Spare Parts Analyst ready. Please specify a metric, region, or time period."
    
    if q_type == "OFF_TOPIC":
        return "I am specialized only in KPCL spare parts analysis. Please ask questions related to invoices, revenue, quantities, or models!"

    update_context(q)
    processed_q, filters = apply_memory(q)
    
    # Hashed Cache Key (MD5) to prevent memory bloat
    intent_str = json.dumps({"q": processed_q, "f": filters}, sort_keys=True)
    cache_key = hashlib.md5(intent_str.encode()).hexdigest()
    
    # --- Correct Execution Order ---
    
    # Step 2: Deterministic Layer (FIRST)
    det_ans = deterministic_handler(processed_q, filters)
    if det_ans:
        if isinstance(det_ans, (int, float)) and det_ans == 0:
            det_ans = "No significant data found for this query."
        log_event(original_q, f"DETERMINISTIC (Norm: {q})\nFilters: {filters}", det_ans)
        set_cache(cache_key, det_ans)
        return det_ans
        
    # Step 3: Template Layer
    tpl_ans = template_handler(processed_q, filters)
    if tpl_ans is not None:
        formatted = ""
        if isinstance(tpl_ans, (pd.Series, pd.DataFrame)):
            formatted = "\n" + tpl_ans.head(10).to_markdown()
        else: formatted = str(tpl_ans)
        
        log_event(original_q, f"TEMPLATE (Norm: {q})\nFilters: {filters}", formatted)
        set_cache(cache_key, formatted)
        return formatted

    # Step 4: Cache (LAST)
    cached = get_cache(cache_key)
    if cached: return cached
    
    context_block = "# CONTEXT:\n"
    years = re.findall(r"\b(20\d{2})\b", processed_q)
    if len(years) > 1:
        y_filter = " | ".join([f"(df['INV_DATE'].dt.year == {y})" for y in years])
        context_block += f"# MULTI-YEAR FILTER: {y_filter}\n"
    
    found_codes = re.findall(r"[a-zA-Z\d\.]{5,}", q)
    if found_codes:
        context_block += "# - Found Item Codes (Cleaned):\n"
        for c in found_codes:
            if any(char.isdigit() for char in c):
                clean = c.replace(".", "").strip()
                context_block += f"#   - '{c}' -> use ITEM_CODE_CLEAN == '{clean}'\n"
    
    context_block += f"# - Available Models (MODEL_CLEAN): {ALL_MODELS}\n"
    context_block += f"# - Available Regions (REGION_CLEAN): {ALL_REGIONS}\n"
    history = []
    for attempt in range(1, 6):
        if (datetime.datetime.now() - start_time).total_seconds() > MAX_EXEC_TIME:
            return "Query took too long. Please simplify."
            
        prompt = build_prompt(processed_q, history, q_type, context_block)
        raw    = llm.invoke(prompt)
        
        # --- LAYER 1: STRUCTURAL GUARD (Guardrails AI) ---
        try:
            # In version 0.9.x, guard.parse returns a ValidationOutcome object
            outcome = guard.parse(raw)
            validated_output = outcome.validated_output
            
            if not validated_output:
                 history.append((raw, "Structural error: could not parse JSON schema."))
                 continue
                 
            # Extract code from the dictionary
            code = validated_output.get("python_code")
        except Exception as e:
            if DEBUG: print(f"  [Structural Guard Error]: {e}")
            history.append((raw, f"Format error: Please provide valid JSON with 'plan' and 'python_code' keys. {e}"))
            continue

        # --- LAYER 2: SECURITY & EXECUTION (Custom Sandbox) ---
        result, err = run_code(code)
        if err:
            if DEBUG: print(f"  [Attempt {attempt} Error]: {err}")
            # Smart Retry Feedback
            if "KeyError" in err:
                msg = f"Column error — check schema. {err}"
            elif "NoneType" in str(type(result)) and result is None:
                msg = "Result is empty — ensure filters are correct."
            else:
                msg = err
            history.append((raw, msg))
            continue
        final_ans = restore_item_format(result)
        
        if final_ans is None or (isinstance(final_ans, (int, float)) and final_ans == 0):
            return "No significant data found for this query."
        
        # Guard: Maximum Rows for DataFrames
        MAX_ROWS = 50
        if isinstance(final_ans, pd.DataFrame):
            final_ans = final_ans.head(MAX_ROWS)
        
        # Better formatting for various types
        if isinstance(final_ans, (pd.DataFrame, pd.Series, pd.Index)):
            if isinstance(final_ans, pd.DataFrame):
                formatted = "\n" + final_ans.head(10).to_markdown()
            else:
                formatted = ", ".join([str(x) for x in final_ans.tolist()])
        elif "numpy" in str(type(final_ans)) and hasattr(final_ans, "tolist"):
            items = final_ans.tolist()
            if isinstance(items, list):
                formatted = ", ".join([str(x) for x in items])
            else:
                formatted = str(items)
        elif isinstance(final_ans, dict):
            formatted = "\n" + "\n".join([f"- {k}: {v}" for k, v in final_ans.items()])
        elif isinstance(final_ans, (list, tuple)):
            formatted = ", ".join([str(x) for x in final_ans])
        elif isinstance(final_ans, float) or "float" in str(type(final_ans)):
            formatted = f"{float(final_ans):,.2f}"
        elif isinstance(final_ans, (int, complex)) or "int" in str(type(final_ans)):
            formatted = f"{int(final_ans):,}"
        else:
            formatted = str(final_ans)
        
        # Log include normalization info
        duration = (datetime.datetime.now() - start_time).total_seconds()
        log_event(original_q, f"{raw}\n[Normalized: {q}]\nExecution Time: {duration:.3f}s", formatted)
        cache[cache_key] = formatted
        save_cache()
        return formatted
    return "Data analysis failed. Please refine your query (e.g., check metrics or year formats)."

# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    print("\nKPCL Chatbot V12 (Final Polish) Ready! Type 'exit' to quit.\n" + "="*60)
    while True:
        try:
            inp = input("\nYou: ").strip()
            if not inp or inp.lower() in ["exit", "quit"]: break
            print(f"\nBot: {ask_ai(inp)}")
        except KeyboardInterrupt: break