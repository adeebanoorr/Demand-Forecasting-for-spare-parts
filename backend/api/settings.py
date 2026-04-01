from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List
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
    ALLOWED_ORIGINS: List[str] = ["*"]

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

settings = Settings()
