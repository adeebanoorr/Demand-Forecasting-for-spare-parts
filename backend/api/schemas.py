from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict

# --- Core Schemas ---

class HealthCheck(BaseModel):
    status: str = "ok"
    message: str = "API is reachable"

# --- Forecast Schemas ---

class ForecastEntry(BaseModel):
    week: str
    forecast: Optional[float] = None
    actual: Optional[float] = None
    ci_lower: Optional[float] = None
    ci_upper: Optional[float] = None

class ForecastResponse(BaseModel):
    model: str
    data: List[ForecastEntry]

class AggregateForecastEntry(BaseModel):
    week: str
    forecast: float

# --- Comparison Schemas ---

class ModelTypes(BaseModel):
    champion: str
    ml: str
    ts: str

class ComparisonEntry(BaseModel):
    week: str
    actual: Optional[float] = None
    champion: Optional[float] = None
    ml: Optional[float] = None
    ts: Optional[float] = None
    ci_lower: Optional[float] = None
    ci_upper: Optional[float] = None

class ComparisonResponse(BaseModel):
    item: str
    models: ModelTypes
    data: List[ComparisonEntry]

# --- Validation Schemas ---

class ValidationEntry(BaseModel):
    week: str
    forecast: Optional[float] = None
    actual: Optional[float] = None
    ci_lower: Optional[float] = None
    ci_upper: Optional[float] = None

class ValidationResponse(BaseModel):
    item_code: str
    data: List[ValidationEntry]

# --- Metric Schemas ---

class MetricResponse(BaseModel):
    champion: str
    rmse: float
    mae: float
    smape: Union[float, str]

class RMSEComparisonEntry(BaseModel):
    name: str
    rmse: float

class FullComparisonResponse(BaseModel):
    ml: List[RMSEComparisonEntry]
    ts: List[RMSEComparisonEntry]

class GlobalMetricsResponse(BaseModel):
    total_items: int
    best_mode_type: str
    avg_rmse_ml: float
    avg_rmse_ts: float

# --- MSTL Schemas ---

class MSTLEntry(BaseModel):
    week: str
    observed: float
    trend: float
    seasonal: float
    residual: float

# --- Error Schemas ---

class ErrorResponse(BaseModel):
    detail: str
    traceback: Optional[str] = None
