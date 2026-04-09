from fastapi import FastAPI, HTTPException, Depends, Security, status, Request, BackgroundTasks
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import uvicorn
import os
import sys
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chatbot-api")

# Ensure the parent directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from agent import ask_ai
except ImportError as e:
    logger.error(f"Error importing ask_ai: {e}")
    def ask_ai(q):
        return {"answer": f"Error: Agent not found. {e}", "metadata": {"type": "error"}}

# --- SECURITY ---
API_KEY = "spareparts-analyst-2026" # In production, use env variable
API_KEY_NAME = "access_token"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_KEY:
        return api_key
    # For now, we'll allow missing keys for local UI compatibility, 
    # but validate if present. 
    if api_key and api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    return api_key

# --- MODELS ---
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=2, json_schema_extra={"example": "What was the revenue in 2023?"})

class ResponseMetadata(BaseModel):
    type: str
    latency_ms: float
    filters: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    status: str = "success"
    metadata: ResponseMetadata

# --- APP SETUP ---
app = FastAPI(
    title="Enterprise Chatbot API",
    description="Advanced Analytics API for Spare Parts Forecasting",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- GLOBAL ERROR HANDLING ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "An internal server error occurred.",
            "detail": str(exc) if os.getenv("DEBUG") else "Internal Server Error"
        }
    )

# --- BACKGROUND TASKS ---
def log_analytics(query: str, response_type: str):
    # Simulate a database write or heavy logging
    time.sleep(0.1) 
    logger.info(f"Analytics: Query='{query}' Type='{response_type}'")

# --- ROUTES ---
@app.post("/ask", response_model=QueryResponse)
async def ask(
    request: QueryRequest, 
    background_tasks: BackgroundTasks,
    api_key: str = Depends(get_api_key)
):
    try:
        # The agent now returns a dict with 'answer' and 'metadata'
        result = ask_ai(request.query)
        
        # Add background task for logging
        background_tasks.add_task(log_analytics, request.query, result['metadata'].get('type'))
        
        return QueryResponse(
            answer=result["answer"],
            metadata=ResponseMetadata(**result["metadata"])
        )
    except Exception as e:
        logger.error(f"Error in /ask: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {
        "status": "operational",
        "timestamp": time.time(),
        "version": "2.0.0"
    }

if __name__ == "__main__":
    uvicorn.run("chatbot_api:app", host="0.0.0.0", port=8001, reload=True)
