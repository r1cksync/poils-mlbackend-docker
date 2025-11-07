from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings and configuration"""
    
    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", 8000))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Hugging Face API configuration
    HUGGINGFACE_API_KEY: str = os.getenv("HUGGINGFACE_API_KEY", "")
    HUGGINGFACE_MODEL: str = os.getenv("HUGGINGFACE_MODEL", "microsoft/trocr-base-printed")
    HUGGINGFACE_API_URL: str = f"https://api-inference.huggingface.co/models/{os.getenv('HUGGINGFACE_MODEL', 'microsoft/trocr-base-printed')}"
    # New HF Router URL (replaces deprecated api-inference endpoint)
    HUGGINGFACE_ROUTER_URL: str = f"https://router.huggingface.co/hf-inference/models/{os.getenv('HUGGINGFACE_MODEL', 'microsoft/trocr-base-printed')}"
    
    # Image processing
    MAX_IMAGE_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_IMAGE_DIMENSION: int = 2048  # Max width/height for processing
    SUPPORTED_FORMATS: List[str] = ["image/jpeg", "image/png", "image/jpg"]
    
    # CORS configuration
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://*.vercel.app",
        "https://*.netlify.app",
        "*"  # Allow all for development (restrict in production)
    ]
    
    # Timeouts
    REQUEST_TIMEOUT: int = 60  # seconds
    API_TIMEOUT: int = 30  # seconds for Hugging Face API
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
