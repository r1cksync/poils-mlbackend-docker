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
    # Use Microsoft TrOCR model (confirmed to work with Inference API)
    # This model works well for printed text and has some multilingual support
    # Alternative: "microsoft/trocr-base-handwritten" for handwritten text
    HUGGINGFACE_MODEL: str = os.getenv("HUGGINGFACE_MODEL", "microsoft/trocr-base-printed")
    # Use HF Serverless Inference API (free tier available)
    # Format: https://api-inference.huggingface.co/models/{model_id}
    # This works without authentication for public models (rate limited)
    # With authentication, gets higher rate limits
    HUGGINGFACE_API_URL: str = f"https://api-inference.huggingface.co/models/{os.getenv('HUGGINGFACE_MODEL', 'microsoft/trocr-base-printed')}"
    HUGGINGFACE_ROUTER_URL: str = HUGGINGFACE_API_URL
    
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
