from pydantic_settings import BaseSettings
from pathlib import Path
import os

class Settings(BaseSettings):
    # App Information
    APP_TITLE: str = "KPCL Spare Parts Forecasting API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Advanced forecasting and analytics API for KPCL spare parts demand."
    
    # Environment
    PORT: int = 8000
    DEBUG: bool = False
    
    # Path Configuration (Assuming relative to backend/api/)
    BASE_DIR: Path = Path(__file__).resolve().parents[2] / "data" / "processed"
    STATIC_DIR: Path = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    
    # Security
    # Keep this as plain string so env parsing never crashes on Render.
    # Examples: "*", "https://a.com,https://b.com", '["https://a.com"]'
    ALLOWED_ORIGINS: str = "*"

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

settings = Settings()
