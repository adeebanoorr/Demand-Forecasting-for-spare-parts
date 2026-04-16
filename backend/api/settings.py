from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List
from pydantic import field_validator
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

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value):
        # Accept Render-style string env vars such as "*" or
        # comma-separated origins in addition to JSON arrays.
        if isinstance(value, str):
            raw = value.strip()
            if raw == "*":
                return ["*"]
            if raw.startswith("[") and raw.endswith("]"):
                return value
            return [origin.strip() for origin in raw.split(",") if origin.strip()]
        return value

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

settings = Settings()
