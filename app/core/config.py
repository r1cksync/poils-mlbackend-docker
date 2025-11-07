from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings and configuration"""
    
    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", 8000))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Model configuration
    MODEL_NAME: str = os.getenv("MODEL_NAME", "surajp/trocr-base-hindi")
    MODEL_CACHE_DIR: str = os.getenv("MODEL_CACHE_DIR", "./model_cache")
    MAX_IMAGE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # CORS configuration
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://*.vercel.app",
        "https://*.netlify.app",
        "*"  # Allow all for development (restrict in production)
    ]
    
    # Image processing
    MAX_IMAGE_DIMENSION: int = 2048  # Max width/height for processing
    SUPPORTED_FORMATS: List[str] = ["image/jpeg", "image/png", "image/jpg", "application/pdf"]
    
    # Timeouts
    REQUEST_TIMEOUT: int = 60  # seconds
    MODEL_TIMEOUT: int = 30  # seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
