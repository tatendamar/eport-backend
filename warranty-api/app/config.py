"""
Configuration settings for the Warranty Register API.
Uses pydantic-settings for environment variable management.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database settings
    database_url: str = "postgresql://warranty_user:warranty_pass@db:5432/warranty_db"
    
    # JWT Settings for API authentication
    secret_key: str = "your-super-secret-key-change-in-production-minimum-32-chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # API Settings
    api_title: str = "Warranty Register API"
    api_version: str = "1.0.0"
    api_description: str = "API for registering device warranties"
    
    # Security
    api_key: str = "warranty-api-key-change-this"
    allowed_origins: str = "*"
    
    # App settings
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
