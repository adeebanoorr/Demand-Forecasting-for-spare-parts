import pandas as pd
import re
import os
import datetime
import json
import hashlib
from collections import OrderedDict
from openai import OpenAI
import guardrails as gd
from pydantic import BaseModel, Field
from dotenv import load_dotenv
# LangGraph & Checkpointing
from typing import Annotated, TypedDict, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

# Load secrets from .env file
load_dotenv()

# =============================================================================
# OBSERVABILITY (LangSmith)
# =============================================================================
if os.getenv("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "PartsAnalyst-Chatbot-NVIDIA"
    print("LangSmith Tracing Enabled.")
else:
    print("LangSmith Tracing Disabled (Missing API Key).")

# =============================================================================
# CONFIG & LOAD
# =============================================================================
DEBUG = True
LOG_FILE = "chatbot_logs.txt"
CACHE_FILE = "chatbot_cache.json"
# Adjusted path to point to backend's data
file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "spare_parts_data.csv"))

if not os.path.exists(file_path):
    print(f"Error: Dataset not found at {file_path}")
    exit()

df = pd.read_csv(file_path)

# Data Normalization: Strip and upper column names, replace spaces with underscores, and drop duplicates
df.columns = [c.strip().upper().replace(' ', '_') for c in df.columns]
df = df.loc[:, ~df.columns.duplicated()]

# Data Cleaning & Helpers
df['INV_DATE'] = pd.to_datetime(df['INV_DATE'], errors='coerce')
df['PROMISE_DATE'] = pd.to_datetime(df['PROMISE_DATE'], errors='coerce')
df['SCHEDULE_SHIP'] = pd.to_datetime(df['SCHEDULE_SHIP'], errors='coerce')

# Performance Optimization: Precompute YEAR, QUARTER, MONTH & MONTH_NAME
df["YEAR"] = df["INV_DATE"].dt.year
df["QUARTER"] = df["INV_DATE"].dt.quarter
df["MONTH"] = df["INV_DATE"].dt.month
df["MONTH_NAME"] = df["INV_DATE"].dt.month_name()

# Dispatch Performance Columns
df["delayed"] = (df["INV_DATE"] > df["PROMISE_DATE"]).astype(int)
df["DELAY_DAYS"] = (df["INV_DATE"] - df["PROMISE_DATE"]).dt.days.clip(lower=0)
df["on_time"] = (df["INV_DATE"] <= df["PROMISE_DATE"]).astype(int)
df["is_on_time"] = df["on_time"]

df["ITEM_CODE_CLEAN"] = df["ITEM_CODE"].astype(str).str.replace(".", "", regex=False).str.strip()
df["MODEL_CLEAN"]  = df["MODEL"].astype(str).str.strip().str.lower()
df["REGION_CLEAN"] = df["REGION"].astype(str).str.strip().str.lower()
df["CUSTOMER_NAME_CLEAN"] = df["CUSTOMER_NAME"].astype(str).str.strip().str.lower().str.replace(r"\s+", " ", regex=True)

ALLOWED_COLS = [
    "ITEM_CODE", "ITEM_DESCRIPTION", "MODEL", "QTY", "UNIT_PRICE",
    "BASIC_VALUE", "TAX_VALUE", "GROSS_VALUE", "REGION", "INV_DATE",
    "ITEM_CODE_CLEAN", "CUSTOMER_NAME_CLEAN", "MODEL_CLEAN", "REGION_CLEAN",
    "PROMISE_DATE", "SCHEDULE_SHIP", "on_time", "is_on_time", "delayed", 
    "INVNO", "YEAR", "QUARTER", "MONTH", "MONTH_NAME", "DELAY_DAYS"
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

# --- LANGGRAPH POSTGRESSAVER (LTM + STM) ---
DB_URL = os.getenv("DATABASE_URL", "sqlite:///chatbot_memory.db")

class AnalystState(TypedDict):
    messages: Annotated[List[BaseMessage], "The conversation messages"]
    summary: str
    filters: dict
    last_intent: str

DB_PATH = os.path.join(os.path.dirname(__file__), "chatbot_memory.sqlite")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
checkpointer = SqliteSaver(conn)

context = {"last_year": None, "last_region": None, "last_model": None, "last_customer": None, "last_query": "", "last_intent": None}

def log_to_file(session_id, user_q, ai_ans):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"\n[{timestamp}] SESSION: {session_id}\nUSER: {user_q}\nBOT: {ai_ans}\n" + "-"*50 + "\n"
    try:
        with open("chatbot_history_backup.txt", "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Logging Error: {e}")

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

def guard_columns(code):
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
    
    multi_match = re.findall(r"\[\s*\[(.*?)\]\s*\]", code)
    for match in multi_match:
        items = [i.strip().strip("'").strip('"') for i in match.split(",")]
        potential_cols.extend(items)

    for c in potential_cols:
        if c.lower() in ["true", "false"]: 
            return False, f"Logical error: {c} used as column name. Ensure boolean filters use single brackets: df[df['col'] == True]"
        if not c or c.isdigit(): continue 
        if c not in ALLOWED_COLS:
            return False, f"Invalid column: {c}. Use ONLY: {', '.join(sorted(list(ALLOWED_COLS)))}"
    return True, None

def normalize_query(q):
    # Mirrors original behavior...
    q = q.lower().replace(" w r t ", " by ").replace(" wrt ", " by ").strip().strip("?").strip("!")
    q = re.sub(r"[,\-]", " ", q)
    fillers = ["please", "can you", "show me", "tell me", "what is", "what was", "what were", 
               "find", "search for", "give me", "list", "calculate", "details of", "information about",
               "could you", "i want to know", "thank you", "thanks", "i'm asking", "made", "resp", "respectively"]
    for f in fillers:
        q = re.sub(rf"\b{f}\b", "", q)
    q = q.replace("breakdown of", "by").replace("list all", "by")
    q = q.replace("each", "by").replace("every", "by").replace("across", "by")
    
    if "last year" in q:
        if context["last_year"]: q = q.replace("last year", str(int(context["last_year"]) - 1))
        else: q = q.replace("last year", "2024")
    if "this year" in q: q = q.replace("this year", "2024")
    if "year before last" in q: q = q.replace("year before last", "2022")
    
    q = re.sub(r"^(the|a|an)\s+", "", q)
    q = re.sub(r"\s+(the|a|an)\b", " ", q)
    
    q = q.replace("gross value", "revenue").replace("earnings", "revenue")
    q = q.replace("sales value", "revenue").replace("billing", "revenue")
    q = q.replace("quantity", "qty").replace("number of", "qty").replace("units", "qty")
    q = q.replace("unique invoice", "unique_invoices").replace("total unique invoices", "unique_invoices")
    q = q.replace("stability", "stable").replace("consistency", "stable")
    
    q = q.replace("every year", "by year").replace("each year", "by year").replace("annually", "by year")
    q = q.replace("every quarter", "by quarter").replace("each quarter", "by quarter").replace("quarterly", "by quarter")
    q = q.replace("across quarters", "by quarter").replace("per quarter", "by quarter")
    
    def region_replacer(match):
        preposition = match.group(1)
        word = match.group(2)
        if word in ALL_REGIONS: return f"region {word}"
        if word in ALL_MODELS: return f"model {word}"
        return f"{preposition} {word}"

    q = q.replace(" city", " region").replace(" location", " region").replace(" area", " region")
    if "most customer" in q: q = q.replace("most customer", "most unique_customers")
    if "least customer" in q or "lowest customer" in q or "count of customer" in q:
        q = q.replace("least customer", "least unique_customers").replace("lowest customer", "least unique_customers").replace("count of customer", "unique_customers")

    q = q.replace(" dispatch %", " dispatch_utility").replace(" dispatch rate", " dispatch_utility")
    q = q.replace(" dispatch performance", " dispatch_utility").replace(" on-time dispatch", " dispatch_utility").replace(" on time dispatch", " dispatch_utility")
    q = q.replace(" unique item code", " unique item").replace("unique item codes", "unique item").replace("unique items", "unique item")
    q = q.replace("unique customers", "unique customer").replace("unique regions", "unique region")
    q = re.sub(r"\b(from|in|at|for)\s+(\d{4})\b", r"\2", q)
    q = re.sub(r"\b(from|in|at|for)\s+([a-z]{3,})\b", region_replacer, q)
    
    q = re.sub(r"\s+", " ", q).strip()
    if any(w in q for w in ["revenue", "qty", "unique_invoices", "count", "number"]):
        if not any(w in q for w in ["total", "top", "most", "least", "best", "avg", "average", "who", "which", "list", "by", "how many", "ratio", "show"]):
            q = "total " + q
    return q

def classify_query(q):
    q = q.lower().strip().strip(".")
    greeting_patterns = [r"\bhi\b", r"\bhello\b", r"\bhey\b", r"\bbye\b", r"\bexit\b", r"\bquit\b", r"\bthanks\b", r"\bthank you\b", r"\bgood morning\b", r"\bgood evening\b", r"\bhelp\b", r"\bhow can you help\b", r"\bwhat can you do\b"]
    if any(re.search(p, q) for p in greeting_patterns): return "GREETING"
    
    score = {
        "agg":  sum(1 for w in ["total", "sum", "avg", "average", "revenue", "qty", "quantity", "value", "tax", "ratio", "count"] if w in q),
        "rank": sum(1 for w in ["top", "most", "least", "best", "highest", "lowest", "which", "who"] if w in q),
        "data": sum(1 for w in ["part", "item", "code", "model", "region", "customer", "invoice", "detail", "record", "dispatch", "different"] if w in q)
    }
    if any(score.values()) or re.search(r"\b20\d{2}\b", q):
        if score["rank"] > score["agg"]: return "RANKING"
        if score["agg"] > 0: return "AGGREGATION"
        return "DATA_QUERY"
    if any(w in q for w in ["them", "those", "it", "these", "name", "list", "show"]):
        if context.get("last_intent") in ["AGGREGATION", "RANKING", "DATA_QUERY"]: return "DATA_QUERY"
    return "OFF_TOPIC"

def intent_safety(q):
    q_low = q.lower().strip()
    forbidden_intent = ["delete", "remove", "drop", "wipe", "clear", "modify", "update", "change", "hide", "truncate", "reset", "erase"]
    if any(w in q_low for w in ["column", "dataset", "table", "csv", "df", "data"]):
         if any(w in q_low for w in forbidden_intent):
             return False, "I cannot modify or delete data. I am a read-only analysis tool."
    return True, None

def extract_filters(q):
    filters = {"year": None, "region": None, "model": None, "customer": None, "years": []}
    range_match = re.findall(r"\b(20\d{2})\b", q)
    if len(range_match) > 1:
        y_start, y_end = int(min(range_match)), int(max(range_match))
        filters["years"] = list(range(y_start, y_end + 1))
        filters["year"] = y_start
    elif range_match:
        filters["year"] = int(range_match[0])
        filters["years"] = [int(range_match[0])]
    
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
            prefix = c[:12] if len(c) > 12 else c
            if len(prefix) >= 8 and prefix in q_low:
                filters["customer"] = c
                break
    return filters

def update_context(q):
    f = extract_filters(q)
    if f["year"]: context["last_year"] = str(f["year"])
    if f["region"]: context["last_region"] = f["region"]
    if f["model"]: context["last_model"] = f["model"]
    if f["customer"]: context["last_customer"] = f["customer"]
    context["last_query"] = q

def apply_memory(q):
    filters = {}
    q_low = q.lower()
    if "next year" in q_low and context["last_year"]: filters["year"] = int(context["last_year"]) + 1
    elif "previous year" in q_low and context["last_year"]: filters["year"] = int(context["last_year"]) - 1
    elif "this year" in q_low or "same year" in q_low:
        if context["last_year"]: filters["year"] = int(context["last_year"])
        
    if any(w in q_low for w in ["that region", "this region", "same region"]):
        if context["last_region"]: filters["region"] = context["last_region"]
        
    raw_filters = extract_filters(q)
    if "total" in q_low or "grand" in q_low or "all years" in q_low:
        return q, raw_filters

    if not filters.get("year") and not raw_filters["year"] and context["last_year"]:
        if any(w in q_low for w in ["total", "how many", "revenue", "qty"]):
             if "year" not in q_low: filters["year"] = int(context["last_year"])
             
    if not filters.get("region") and not raw_filters["region"] and context["last_region"]:
        if any(w in q_low for w in ["total", "how many", "revenue", "qty"]):
            if "region" not in q_low: filters["region"] = context["last_region"]

    if any(w in q_low for w in ["them", "those", "it", "these", "about"]):
        last_q = context.get("last_query", "").lower()
        if "model" in last_q or "type" in last_q: q = q + " models"
        elif "region" in last_q or "where" in last_q: q = q + " regions"
        elif "customer" in last_q or "who" in last_q: q = q + " customers"
        if "revenue" in last_q and "revenue" not in q_low: q = q + " revenue"
        elif "qty" in last_q and "qty" not in q_low: q = q + " qty"
        elif "dispatch" in last_q and "dispatch" not in q_low: q = q + " dispatch performance"

    final_filters = {**raw_filters, **filters}
    return q, final_filters

def deterministic_handler(processed_q, filters):
    q_low = processed_q.lower().strip()
    is_max = any(w in q_low for w in ["best", "highest", "top", "most"])
    is_min = any(w in q_low for w in ["worst", "lowest", "least", "min"])
    
    breakdown_keywords = ["by", "each", "every", "across", "breakdown", "per", "monthly", "yearly", "quarterly", "respective"]
    if any(k in q_low for k in breakdown_keywords): return None
    
    if any(w in q_low for w in ["which year", "what year", "year was that"]) and context["last_year"]: return f"The analysis was for the year {context['last_year']}."
    if any(w in q_low for w in ["which region", "what region", "region was that"]) and context["last_region"]: return f"The analysis was for {context['last_region']} region."
    if any(w in q_low for w in ["which model", "what model", "model was that"]) and context["last_model"]: return f"The analysis was for {context['last_model']}."
    if any(w in q_low for w in ["who was", "which customer", "what customer"]) and context["last_customer"]: return f"The customer was {context['last_customer']}."

    target_df = df
    if filters.get("years"): target_df = df[df["YEAR"].isin(filters["years"])]
    elif filters.get("year"):
        if filters["year"] in DF_BY_YEAR: target_df = DF_BY_YEAR[filters["year"]]
        else: return f"No records found for year {filters['year']}."
            
    if filters.get("region"):
        if filters["region"] in DF_BY_REGION: target_df = target_df[target_df["REGION_CLEAN"] == filters["region"]]
        else: return f"No records found for region {filters['region']}."

    if filters.get("model") and "ratio" not in q_low and "list" not in q_low and "all" not in q_low:
        if filters["model"] in DF_BY_MODEL: target_df = target_df[target_df["MODEL_CLEAN"] == filters["model"]]
        else: return f"No records found for model {filters['model']}."

    if "ratio" in q_low:
        raw_parts = re.findall(r"(acr[\-\s]spares|acr[\-\s]service|no[\-\s]sales[\-\s]credit)", q_low)
        parts = []
        for p in raw_parts:
            norm = p.replace("-", " ").replace("  ", " ").strip()
            for m in ALL_MODELS:
                if m.replace("-", " ").replace("  ", " ").strip() == norm:
                    if m not in parts: parts.append(m)
                    break
            
        if len(parts) >= 2:
            counts = {p: len(target_df[target_df["MODEL_CLEAN"] == p]) for p in parts}
            valid_counts = [v for v in counts.values() if v > 0]
            if valid_counts:
                ref = min(valid_counts)
                ratio_str = " : ".join([f"{v/ref:.2f}" for v in counts.values()])
                label_str = " : ".join(parts)
                answer = f"Ratio ({label_str}) = {ratio_str}"
                if filters.get("year"): answer += f" in {filters['year']}"
                if any(w in q_low for w in ["name", "identify", "tell me", "what are"]): answer += f"\nModels: {', '.join(ALL_MODELS)}"
                return answer
        elif len(parts) == 1 and ("other" in q_low or "rest" in q_low):
            p1 = parts[0]
            c1 = len(target_df[target_df["MODEL_CLEAN"] == p1])
            c2 = len(target_df[target_df["MODEL_CLEAN"] != p1])
            if c2 > 0:
                answer = f"Ratio of {p1} vs all others is {c1/c2:.2f}:1"
                if filters.get("year"): answer += f" in {filters['year']}"
                return answer

    if any(w in q_low for w in ["list", "what are", "different", "show all", "name", "identify", "tell me"]) and not any(w in q_low for w in ["top", "most", "highest", "lowest"]):
        if "model" in q_low: return ", ".join(ALL_MODELS)
        if "region" in q_low: return ", ".join(ALL_REGIONS)

    if any(w in q_low for w in ["how many", "count unique", "unique count", "count of all"]):
        if "model" in q_low: return f"{target_df['MODEL_CLEAN'].nunique():,}"
        if "region" in q_low: return f"{target_df['REGION_CLEAN'].nunique():,}"
        if "customer" in q_low: return f"{target_df['CUSTOMER_NAME_CLEAN'].nunique():,}"
        if "item" in q_low or "part" in q_low: return f"{target_df['ITEM_CODE_CLEAN'].nunique():,}"

    if any(w in q_low for w in ["total count", "count of", "number of", "how many"]):
        if filters.get("model"): return f"{len(target_df[target_df['MODEL_CLEAN'] == filters['model']]):,} records found for {filters['model']}"
        if filters.get("region"): return f"{len(target_df[target_df['REGION_CLEAN'] == filters['region']]):,} records found for {filters['region']}"
        if filters.get("customer"): return f"{len(target_df[target_df['CUSTOMER_NAME_CLEAN'] == filters['customer']]):,} records found for {filters['customer']}"
        if "model" in q_low: return f"{len(target_df):,}"

    if "unique customer" in q_low and "region" in q_low:
        valid_regions = target_df[~target_df["REGION_CLEAN"].isin(["default collector", None])]
        if not valid_regions.empty:
            func = "idxmin" if is_min else "idxmax"
            res = getattr(valid_regions.groupby("REGION_CLEAN")["CUSTOMER_NAME_CLEAN"].nunique(), func)()
            return res.upper()
            
    if filters.get("customer") and filters["customer"] in DF_BY_CUSTOMER: target_df = target_df[target_df["CUSTOMER_NAME_CLEAN"] == filters["customer"]]

    if "growth" in q_low and "highest" not in q_low:
        metric_col = "GROSS_VALUE" if "revenue" in q_low else "QTY"
        y_curr = filters.get("year") or ALL_YEARS[-1]
        y_prev = y_curr - 1
        if y_curr in DF_BY_YEAR and y_prev in DF_BY_YEAR:
            val_curr = DF_BY_YEAR[y_curr][metric_col].sum()
            val_prev = DF_BY_YEAR[y_prev][metric_col].sum()
            if val_prev > 0: return f"{((val_curr - val_prev) / val_prev) * 100:,.2f}% Growth ({y_curr} vs {y_prev})"

    if "difference" in q_low and (is_max and is_min):
        metric = "GROSS_VALUE" if "revenue" in q_low else "QTY"
        rank_metric = "QTY" if "sold" in q_low or "qty" in q_low else metric
        group_col = "ITEM_CODE_CLEAN" if "item" in q_low else "CUSTOMER_NAME_CLEAN"
        if "region" in q_low: group_col = "REGION_CLEAN"
        if "model" in q_low: group_col = "MODEL_CLEAN"
        
        agg = target_df.groupby(group_col).agg({metric: "sum", rank_metric: "sum"})
        if not agg.empty:
            i_max, i_min = agg[rank_metric].idxmax(), agg[rank_metric].idxmin()
            diff = agg.loc[i_max, metric] - agg.loc[i_min, metric]
            return f"Difference in {metric} between most and least {group_col.split('_')[0].strip().lower()} (ranked by {rank_metric}): {diff:,.2f}"

    if (is_max or is_min) and not any(w in q_low for w in ["top 2", "top 3", "top 5", "top 10"]):
        metric = "GROSS_VALUE" if "revenue" in q_low else "QTY"
        func = "idxmax" if is_max else "idxmin"
        if "region" in q_low or "city" in q_low: return getattr(target_df.groupby("REGION_CLEAN")[metric].sum(), func)()
        if "model" in q_low: return getattr(target_df.groupby("MODEL_CLEAN")[metric].sum(), func)()
        if "customer" in q_low: return getattr(target_df.groupby("CUSTOMER_NAME_CLEAN")[metric].sum(), func)()
        if "item" in q_low: return getattr(target_df.groupby("ITEM_DESCRIPTION" if "description" in q_low else "ITEM_CODE_CLEAN")[metric].sum(), func)()
        if "year" in q_low: return str(int(getattr(target_df.groupby("YEAR")[metric].sum(), func)()))

    if "unique" in q_low:
        if "item" in q_low: return f"{target_df['ITEM_CODE_CLEAN'].nunique():,}"
        if "customer" in q_low: return f"{target_df['CUSTOMER_NAME_CLEAN'].nunique():,}"
        if "model" in q_low: return f"{target_df['MODEL_CLEAN'].nunique():,}"
        if "region" in q_low: return f"{target_df['REGION_CLEAN'].nunique():,}"
        if "invoice" in q_low: return f"{target_df['INVNO'].nunique():,}"

    if "dispatch_utility" in q_low or "on-time" in q_low:
        if not target_df.empty:
            rate = (target_df["on_time"].sum() / len(target_df)) * 100
            region_str = f" for {filters['region'].upper()}" if filters.get("region") else ""
            year_str = f" in {filters['year']}" if filters.get("year") else ""
            return f"{rate:,.2f}% On-Time Dispatch Rate{region_str}{year_str}"
        return "No dispatch data found."

    if not any(k in q_low for k in ["top", "most", "least"]) or "top 1" in q_low:
        q_metric = q_low
        if filters.get("year"): q_metric = q_metric.replace(str(filters["year"]), "")
        if filters.get("model"): q_metric = q_metric.replace(filters["model"], "")
        if filters.get("region"): q_metric = q_metric.replace(filters["region"], "")
        if filters.get("customer"): q_metric = q_metric.replace(filters["customer"], "")
        
        metrics = {
            "revenue": lambda d: f"{d['GROSS_VALUE'].sum():,.2f}",
            "gross value": lambda d: f"{d['GROSS_VALUE'].sum():,.2f}",
            "qty": lambda d: f"{d['QTY'].sum():,.0f}",
            "quantity": lambda d: f"{d['QTY'].sum():,.0f}",
            "invoices": lambda d: f"{len(d):,}",
            "parts": lambda d: f"{d['QTY'].sum():,.0f}",
            "tax": lambda d: f"{d['TAX_VALUE'].sum():,.2f}"
        }
        for k, func in metrics.items():
            if re.search(rf"\b{re.escape(k)}\b", q_metric): return func(target_df)

    return None

def template_handler(q, filters=None):
    q_clean = q.lower().strip()
    nums = re.findall(r"\d+", q_clean)
    n = int(nums[0]) if nums else 10
    if any(q_clean.startswith(w) for w in ["who", "which"]) and not nums: n = 1
    
    temp_df = df
    if filters:
        if filters.get("years"): temp_df = df[df["YEAR"].isin(filters["years"])]
        elif filters.get("year") and filters["year"] in DF_BY_YEAR: temp_df = DF_BY_YEAR[filters["year"]]
        if filters.get("customer") and filters["customer"] in DF_BY_CUSTOMER: temp_df = temp_df[temp_df["CUSTOMER_NAME_CLEAN"] == filters["customer"]]
        if filters.get("region") and filters["region"] in DF_BY_REGION: temp_df = temp_df[temp_df["REGION_CLEAN"] == filters["region"]]
        if filters.get("model") and filters["model"] in DF_BY_MODEL: temp_df = temp_df[temp_df["MODEL_CLEAN"] == filters["model"]]

    is_bottom = any(k in q_clean for k in ["bottom", "worst", "lowest", "least"])
    if "top" in q_clean or "best" in q_clean or "highest" in q_clean or is_bottom:
        metric, agg = "QTY", "sum"
        if "revenue" in q_clean or "value" in q_clean or "sales" in q_clean: metric, agg = "GROSS_VALUE", "sum"
        elif "tax" in q_clean: metric, agg = "TAX_VALUE", "sum"
        elif "delayed" in q_clean or "delay" in q_clean: metric, agg = "delayed", "mean"
        elif "dispatch" in q_clean or "performance" in q_clean: metric, agg = "on_time", "mean"
        
        group_col = None
        if "model" in q_clean: group_col = "MODEL_CLEAN"
        elif "item" in q_clean or "part" in q_clean: group_col = "ITEM_DESCRIPTION" if "description" in q_clean else "ITEM_CODE_CLEAN"
        elif "customer" in q_clean and not ("count" in q_clean or "unique" in q_clean): group_col = "CUSTOMER_NAME_CLEAN"
        elif "region" in q_clean: group_col = "REGION_CLEAN"
        elif "year" in q_clean: group_col = "YEAR"
        elif "unique" in q_clean and "customer" in q_clean: group_col = "REGION_CLEAN"

        if group_col:
            grouped = temp_df.groupby(group_col)
            if "unique" in q_clean and "customer" in q_clean: metric, agg = "CUSTOMER_NAME_CLEAN", "nunique"
            if metric in ["on_time", "delayed"]:
                res = grouped[metric].agg(agg) * 100
                res = res.sort_values(ascending=is_bottom).head(n)
                res.name = "Rate (%)"
                return res.apply(lambda x: f"{x:.2f}%")
            
            res = grouped[metric].agg(agg)
            return res.nsmallest(n).sort_values(ascending=True) if is_bottom else res.nlargest(n).sort_values(ascending=False)

    if "stable" in q_clean:
        metric = "GROSS_VALUE" if "revenue" in q_clean else "QTY"
        group_col = "REGION_CLEAN" if "region" in q_clean else "MODEL_CLEAN"
        pivot_col = "QUARTER" if "quarter" in q_clean else "MONTH"
        
        matrix = temp_df.groupby([group_col, pivot_col])[metric].sum().unstack()
        if matrix.empty: return "Not enough multi-period data for stability analysis."
        return (matrix.std(axis=1) / matrix.mean(axis=1)).dropna().sort_values().head(3)

    if "by year" in q_clean: return temp_df.groupby("YEAR")["GROSS_VALUE" if "revenue" in q_clean else "QTY"].sum().sort_values(ascending=False)
    if "by quarter" in q_clean: return temp_df.groupby("QUARTER")["GROSS_VALUE" if "revenue" in q_clean else "QTY"].sum()
    if "by region" in q_clean: return temp_df.groupby("REGION_CLEAN")["GROSS_VALUE" if "revenue" in q_clean else "QTY"].sum().sort_values(ascending=False)
    if "by model" in q_clean: return temp_df.groupby("MODEL_CLEAN")["GROSS_VALUE" if "revenue" in q_clean else "QTY"].sum().sort_values(ascending=False)

    if "on time" in q_clean or "efficiency" in q_clean: return f"{(temp_df['INV_DATE'] <= temp_df['PROMISE_DATE']).mean() * 100:.2f}%"
    if "delayed" in q_clean: return f"{(temp_df['INV_DATE'] > temp_df['PROMISE_DATE']).mean() * 100:.2f}%"
    if "on day of promise" in q_clean or "on the day of promise" in q_clean: return f"{(temp_df['INV_DATE'] == temp_df['PROMISE_DATE']).mean() * 100:.2f}%"

    if "correlation" in q_clean or ("delay" in q_clean and "qty" in q_clean):
        corr = temp_df["QTY"].corr(temp_df["delayed"])
        return f"Correlation Coefficient: {corr:.4f} ({'Weak' if abs(corr) < 0.2 else 'Strong'} Relationship)"

    if "most sold item" in q_clean: return temp_df.groupby("ITEM_CODE_CLEAN")["QTY"].sum().idxmax()
    
    if "highest growth" in q_clean or "best growth" in q_clean:
        metric = "GROSS_VALUE" if "revenue" in q_clean else "QTY"
        y_curr = ALL_YEARS[-1]
        y_prev = y_curr - 1
        if y_curr in DF_BY_YEAR and y_prev in DF_BY_YEAR:
            curr_agg = DF_BY_YEAR[y_curr].groupby("REGION_CLEAN" if "region" in q_clean else "MODEL_CLEAN")[metric].sum()
            prev_agg = DF_BY_YEAR[y_prev].groupby("REGION_CLEAN" if "region" in q_clean else "MODEL_CLEAN")[metric].sum()
            return ((curr_agg - prev_agg) / prev_agg).dropna().nlargest(3)

    if "worst dispatch" in q_clean or "highest delay" in q_clean or ("bottom" in q_clean and "dispatch" in q_clean):
        col = "REGION_CLEAN" if "region" in q_clean else "CUSTOMER_NAME_CLEAN"
        delays = temp_df.groupby(col)["delayed"].mean().nlargest(3) * 100
        delays.name = "Delay %"
        return delays.apply(lambda x: f"{x:.2f}%")

    if "best dispatch" in q_clean or "top" in q_clean and "dispatch" in q_clean:
        col = "REGION_CLEAN" if "region" in q_clean else "CUSTOMER_NAME_CLEAN"
        on_time = temp_df.groupby(col)["on_time"].mean().nlargest(3) * 100
        on_time.name = "On-Time %"
        return on_time.apply(lambda x: f"{x:.2f}%")

    if "best region" in q_clean or "which region highest revenue" in q_clean: return temp_df.groupby("REGION_CLEAN")["GROSS_VALUE"].sum().idxmax()

    if "on time" in q_clean: return f"{(temp_df['INV_DATE'] <= temp_df['PROMISE_DATE']).mean() * 100:.2f}%"
        
    return None

# =============================================================================
# HYBRID GUARDRAILS (Phase 5)
# =============================================================================
class SparePartsAnalysis(BaseModel):
    plan: str = Field(description="Step-by-step logic for the analysis")
    python_code: str = Field(description="The executable pandas code that assigns the result to 'ans'")

guard = gd.Guard.for_pydantic(output_class=SparePartsAnalysis)

# =============================================================================
# LLM & PROMPT (NVIDIA integration)
# =============================================================================
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
nvidia_client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_API_KEY
)

class NvidiaLLM:
    def invoke(self, prompt: str) -> str:
        response = nvidia_client.chat.completions.create(
            model="meta/llama-3.1-70b-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=1024
        )
        return response.choices[0].message.content

llm = NvidiaLLM()

PROMPT_TEMPLATE = """You are a Clinical Data Analyst for Spare Parts.
Your goal is to provide 100% accurate pandas code based on the user's natural language query.

STRICT PERSONA RULES:
1. NEVER use technical jargon.
2. NEVER add conversational filler.
3. ONLY return the analysis result.

STRICT EXECUTION RULES:
1. "Plan": Concise markdown comment explaining analytical steps.
2. "Python Code": Valid pandas code wrapped in <python>...</python>. 
3. Assign the final result to the variable `ans`.
4. FOR "WHICH" OR "WHO" QUESTIONS: `ans` MUST be the identity (e.g., 'mumbai'), NOT the numeric value. Use `.idxmax()` or `.idxmin()`.
5. "Revenue" or "Billing" always means `GROSS_VALUE`.

DATA SCHEMA:
- ITEM_CODE_CLEAN: Primary ID Number
- ITEM_DESCRIPTION: Human-readable name
- MODEL_CLEAN, REGION_CLEAN, CUSTOMER_NAME_CLEAN: Filter columns
- QTY, UNIT_PRICE, BASIC_VALUE, TAX_VALUE, GROSS_VALUE (Total Revenue)
- YEAR, MONTH_NAME: Date dimensions

FEW-SHOT EXAMPLES:
Question: "Which year had highest revenue?"
Plan: // Group by YEAR, sum GROSS_VALUE, find idxmax
Python Code: <python>ans = df.groupby('YEAR')['GROSS_VALUE'].sum().idxmax()</python>

Question: "top 3 regions by qty in 2023"
Plan: // Filter for 2023, group by REGION_CLEAN, sum QTY, take top 3
Python Code: <python>ans = df[df['YEAR'] == 2023].groupby('REGION_CLEAN')['QTY'].sum().nlargest(3)</python>

Question: "what are the different models"
Plan: // Get unique values from MODEL_CLEAN
Python Code: <python>ans = df['MODEL_CLEAN'].unique()</python>

Question: "total count of acr spares"
Plan: // Filter for 'acr spares' and return row count
Python Code: <python>ans = len(df[df['MODEL_CLEAN'] == 'acr spares'])</python>

Question: "which city has the most customers"
Plan: // Group by REGION_CLEAN, count unique CUSTOMER_NAME_CLEAN, find idxmax
Python Code: <python>ans = df.groupby('REGION_CLEAN')['CUSTOMER_NAME_CLEAN'].nunique().idxmax()</python>

Question: "bottom 3 spare parts by quantity"
Plan: // Group by ITEM_CODE_CLEAN, sum QTY, take bottom 3
Python Code: <python>ans = df.groupby('ITEM_CODE_CLEAN')['QTY'].sum().nsmallest(3)</python>

Question: "What is our On-Time Dispatch % for Ahmedabad?"
Plan: // Filter for regional data, calculate sum of on_time / count, format as %
Python Code: <python>ans = f"{(df[df['REGION_CLEAN'] == 'ahmedabad']['on_time'].sum() / len(df[df['REGION_CLEAN'] == 'ahmedabad'])) * 100:,.2f}%"</python>

Question: {question}
{history_block}
Output:"""

def build_prompt(question, error_feedback, q_type, context_block="", messages=None, summary=""):
    error_block = ""
    history_block = ""
    if summary: history_block += f"\n# CONVERSATION SUMMARY (older turns):\n{summary}\n"
    if messages:
        history_block += "\n# RECENT CONVERSATION HISTORY:\n"
        for msg in messages[-6:]:
            role = "User" if msg.type == "human" else "AI"
            content = msg.content
            content_clean = content.split("|")[0][:100] + "..." if "|" in content else content[:100]
            history_block += f"{role}: {content_clean}\n"

    if error_feedback:
        error_block = "\n# --- RALPH LOOP ERROR FEEDBACK ---\n"
        for i, (code, error) in enumerate(error_feedback):
            if "datetime64" in error: error_block += "# FIX: NEVER use .str on INV_DATE.\n"
            error_block += f"# Attempt {i+1} failed: {error}\n"

    return PROMPT_TEMPLATE.format(question=question, error_block=error_block, q_type=q_type, context_block=context_block, history_block=history_block)

SAFE_GLOBALS = {"df": df, "pd": pd, "__builtins__": {}}
SAFE_LOCALS = {"len": len, "sum": sum, "max": max, "min": min, "abs": abs, "round": round, "range": range, "zip": zip, "enumerate": enumerate, "str": str, "int": int, "float": float, "bool": bool, "list": list, "dict": dict}

def extract_code(text):
    match = re.search(r"<python>(.*?)</python>", text, re.DOTALL)
    if match: return match.group(1).strip()
    return "\n".join([l for l in text.splitlines() if "=" in l or "df[" in l])

def run_code(code):
    if not code: return None, "No code provided."
    if "import" in code or "open(" in code: return None, "Security Violation."
    if "__" in code: return None, "Security Violation: dunder access blocked."
    forbidden = ["eval", "exec", "os.", "sys.", "subprocess", "lambda", "apply(", "drop(", "dropna", "fillna", "replace(", "pop(", "truncate(", "del ", "update(", "insert(", "remove(", "inplace=True"]
    if any(f in code for f in forbidden): return None, "Security Violation: destructive or forbidden operation detected."

    code = re.sub(r"df\[[\"\']ITEM_CODE[\"\']\]", "df[\"ITEM_CODE_CLEAN\"]", code)
    code = re.sub(r"\.ITEM_CODE\b", ".ITEM_CODE_CLEAN", code)
    ok, err = guard_columns(code)
    if not ok: return None, err
    
    current_locals = SAFE_LOCALS.copy()
    try:
        exec(code, SAFE_GLOBALS, current_locals)
        return current_locals.get("ans"), None
    except Exception as e: return None, str(e)

TRIM_THRESHOLD = 8
TRIM_KEEP = 4

def summarize_messages(state: AnalystState) -> dict:
    messages = state.get("messages", [])
    existing_summary = state.get("summary", "")
    if len(messages) <= TRIM_THRESHOLD: return {}
    to_summarize = messages[:-TRIM_KEEP]
    transcript = ""
    for msg in to_summarize:
        role = "User" if msg.type == "human" else "AI"
        transcript += f"{role}: {msg.content[:200]}\n"
    summary_prompt = f"You are summarizing a data analysis conversation.\nExisting summary: {existing_summary or '(none yet)'}\nNew conversation turns to add:\n{transcript}\nWrite a concise 3-5 sentence summary focusing on the KEY analytical topics, data filters (year/region/model), and important findings. Be factual, not conversational."
    try:
        new_summary = llm.invoke(summary_prompt)
        print(f"[CONTEXT] Trimmed {len(to_summarize)} messages. Summary updated.")
        return {"messages": messages[-TRIM_KEEP:], "summary": new_summary}
    except Exception as e:
        print(f"[CONTEXT] Summarization failed: {e}")
        return {}

def analyst_node(state: AnalystState):
    messages = state["messages"]
    last_msg = messages[-1].content
    summary = state.get("summary", "")
    
    q = normalize_query(last_msg)
    q_type = classify_query(q)

    safe, msg = intent_safety(last_msg)
    if not safe: return {"messages": [AIMessage(content=msg)], "filters": {}, "last_intent": "security_blocked"}
    if q_type == "GREETING": return {"messages": [AIMessage(content="Spare Parts Analyst ready.")], "filters": {}, "last_intent": "greeting"}
    if q_type == "OFF_TOPIC": return {"messages": [AIMessage(content="I am specialized only in spare parts analysis.")], "filters": {}, "last_intent": "off_topic"}

    processed_q, filters = apply_memory(q)
    update_context(processed_q)

    det_ans = deterministic_handler(processed_q, filters)
    if det_ans: return {"messages": [AIMessage(content=det_ans)], "filters": filters, "last_intent": "deterministic"}

    tpl_ans = template_handler(processed_q, filters)
    if tpl_ans is not None:
        formatted = "\n" + tpl_ans.to_markdown(tablefmt="github") if isinstance(tpl_ans, (pd.Series, pd.DataFrame)) else str(tpl_ans)
        return {"messages": [AIMessage(content=formatted)], "filters": filters, "last_intent": "template"}

    context_block = f"# YEAR FILTER: {filters.get('year')}\n# REGION: {filters.get('region')}\n"
    error_feedback = []
    for attempt in range(1, 4):
        prompt = build_prompt(processed_q, error_feedback, q_type, context_block, messages, summary=summary)
        raw = llm.invoke(prompt)
        try:
            outcome = guard.parse(raw)
            code = outcome.validated_output.get("python_code")
            result, err = run_code(code)
            if err:
                error_feedback.append((raw, err))
                continue
            return {"messages": [AIMessage(content=str(result))], "filters": filters, "last_intent": "llm_generated"}
        except: continue

    return {"messages": [AIMessage(content="I couldn't compute that. Try rephrasing or ask a simpler version.")], "filters": {}, "last_intent": "error"}

builder = StateGraph(AnalystState)
builder.add_node("summarize", summarize_messages)
builder.add_node("analyst", analyst_node)
builder.set_entry_point("summarize")
builder.add_edge("summarize", "analyst")
builder.set_finish_point("analyst")
analyst_app = builder.compile(checkpointer=checkpointer)

def ask_ai(q, session_id="default_user"):
    config = {"configurable": {"thread_id": session_id}}
    input_state = {"messages": [HumanMessage(content=q)]}
    try:
        output = analyst_app.invoke(input_state, config=config) if checkpointer else analyst_app.invoke(input_state)
        last_msg = output["messages"][-1].content
        metadata = {"type": output.get("last_intent"), "filters": output.get("filters"), "latency_ms": 0.0}
        log_to_file(session_id, q, last_msg)
        return {"answer": last_msg, "metadata": metadata}
    except Exception as e:
        return {"answer": f"Error: {e}", "metadata": {"type": "error", "latency_ms": 0.0}}

if __name__ == "__main__":
    print(f"\nNVIDIA API Analyst Bot Ready (model=meta/llama-3.1-70b-instruct)\n" + "="*40)
    while True:
        try:
            inp = input("\nYou: ").strip()
            if not inp or inp.lower() in ["exit", "quit"]: break
            result = ask_ai(inp)
            print(f"\nBot: {result['answer']}")
        except KeyboardInterrupt: break
