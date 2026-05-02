"""
Application configuration
"""
from typing import List
import json
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "AI Money Brain"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # OpenAI (optional — app works without it, AI categorization just skips)
    OPENAI_API_KEY: str = ""

    # CORS — accepts wildcard "*", JSON list, comma-separated, or single string
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from various string formats."""
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                # JSON-formatted list like '["url1", "url2"]'
                return json.loads(v)
            elif "," in v:
                # Comma-separated like "url1,url2"
                return [i.strip() for i in v.split(",")]
            else:
                # Single value like "*" or "https://example.com"
                return [v]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
