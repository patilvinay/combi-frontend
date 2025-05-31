from pydantic_settings import BaseSettings
from functools import lru_cache
import os
import secrets
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Settings(BaseSettings):
    # Application settings
    PROJECT_NAME: str = "IoT Time Series API"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 5050
    SECRET_KEY: str = "your-secret-key-here"  # Change this to a secure secret key in production
    
    # API settings
    API_V1_STR: str = "/api/v1"
    
    # Database settings
    DATABASE_URL: str = "postgresql://iotuser:iotpassword@localhost:5432/iotdb"
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    
    # Security settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    API_KEY: str = "Xj7Bq9Lp2Rt5Zk8Mn3Vx6Hs1"  # User-provided API key
    API_KEY_NAME: str = "X-API-Key"  # Header name for the API key
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"
        
        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            # This ensures that environment variables take precedence over .env file
            return env_settings, init_settings, file_secret_settings

    def __init__(self, **data):
        super().__init__(**data)
        
        # Generate a random SECRET_KEY if not set
        if self.SECRET_KEY == "your-secret-key-here" and not self.DEBUG:
            self.SECRET_KEY = secrets.token_urlsafe(32)

@lru_cache()
def get_settings() -> Settings:
    return Settings()

# Create settings instance
settings = get_settings()

# For backward compatibility
DATABASE_URL = settings.DATABASE_URL
