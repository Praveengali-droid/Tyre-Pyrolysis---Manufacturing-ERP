"""
Configuration settings for the ERP backend.
Uses pydantic-settings for environment variable management.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = "sqlite:///./erp.db"
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS - include multiple ports in case one is in use
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173", 
        "http://localhost:5174", 
        "http://localhost:5175",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        # Railway production domains
        "https://*.railway.app",
        "https://*.up.railway.app",
    ]
    
    # App
    DEBUG: bool = True
    APP_NAME: str = "Tyre Pyrolysis ERP"
    VERSION: str = "3.0.0"
    
    # Indian Compliance
    DEFAULT_GST_RATE: float = 18.0  # Default GST rate for byproducts
    DEFAULT_ELECTRICITY_RATE: float = 8.50  # ₹/kWh average industrial rate
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
