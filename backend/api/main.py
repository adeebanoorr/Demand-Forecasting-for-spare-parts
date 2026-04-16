from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.wsgi import WSGIMiddleware
from contextlib import asynccontextmanager
import traceback
import os
import uvicorn

from backend.api.settings import settings
from backend.api.routers import items, forecasts, metrics, downloads
from backend.api.schemas import ErrorResponse

def parse_allowed_origins(origins_value: str):
    raw = (origins_value or "*").strip()
    if raw == "*":
        return ["*"]
    if raw.startswith("[") and raw.endswith("]"):
        # Minimal JSON-like list support without failing startup on bad input.
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [part.strip().strip('"').strip("'") for part in inner.split(",") if part.strip()]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print(f"INFO: Starting {settings.APP_TITLE} (v{settings.APP_VERSION})")
    print(f"INFO: Base Directory: {settings.BASE_DIR}")
    yield
    # Shutdown logic
    print(f"INFO: Shutting down {settings.APP_TITLE}")

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_allowed_origins(settings.ALLOWED_ORIGINS),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "path": request.url.path,
            "traceback": traceback.format_exc() if settings.DEBUG else None
        }
    )

# --- Routes ---

@app.get("/health", tags=["System"])
def health_check():
    """Root health check for the whole application."""
    return {"status": "ok", "message": "Spare Parts API is live"}

@app.get("/", tags=["System"])
def read_index():
    """Serve the primary frontend dashboard index file."""
    index_file = settings.STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "message": f"{settings.APP_TITLE} Running",
        "doc_path": "/docs",
        "frontend_status": "Build not found in static directory"
    }

# --- Include Modular Routers under /api/v1 ---
api_v1 = FastAPI() # Separate FastAPI instance for versioning is one way, but APIRouter is cleaner for simple projects

app.include_router(items.router, prefix="/api/v1")
app.include_router(forecasts.router, prefix="/api/v1")
app.include_router(metrics.router, prefix="/api/v1")
app.include_router(downloads.router, prefix="/api/v1")

# --- Legacy Compatibility / Aliases ---
# To avoid breaking the frontend immediately, we can also include them without the v1 prefix
app.include_router(items.router, prefix="/api", include_in_schema=False)
app.include_router(forecasts.router, prefix="/api", include_in_schema=False)
app.include_router(metrics.router, prefix="/api", include_in_schema=False)
app.include_router(downloads.router, prefix="/api", include_in_schema=False)

# --- Sub-applications & Static Files ---

# Mount Dash Performance Dashboard
try:
    from backend.visualization.dashboard import app as dash_app
    app.mount("/analytics", WSGIMiddleware(dash_app.server))
    print("DEBUG: Dash Analytics dashboard mounted at /analytics")
except Exception as e:
    print(f"DEBUG: Failed to mount Dash analytics: {e}")

# Static Files (React/Vite Build)
if settings.STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(settings.STATIC_DIR), html=True), name="static")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", settings.PORT))
    uvicorn.run(app, host="0.0.0.0", port=port)
