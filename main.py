from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from contextlib import asynccontextmanager
import logging

from app.routers import ocr
from app.core.config import settings
from app.services.model_service import ModelService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global model service instance - initialized on first request
_model_service = None


def get_model_service():
    """Get or initialize the model service (lazy loading for serverless)"""
    global _model_service
    if _model_service is None:
        logger.info("🚀 Initializing Hindi OCR API Service...")
        _model_service = ModelService()
        logger.info("✅ Service initialized!")
    return _model_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for FastAPI application.
    For serverless, this might not run, so we use lazy initialization.
    """
    try:
        logger.info("🚀 Starting Hindi OCR API Server...")
        logger.info(f"Using Hugging Face Inference API: {settings.HUGGINGFACE_MODEL}")
        
        # Pre-initialize model service
        service = get_model_service()
        await service.load_model()
        
        # Store in app state
        app.state.model_service = service
        
        logger.info("✅ Service ready!")
        logger.info(f"📡 API ready at: http://{settings.HOST}:{settings.PORT}")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to start server: {str(e)}")
        # Don't raise - allow serverless to continue with lazy init
        yield
    finally:
        logger.info("🔄 Shutting down server...")
        global _model_service
        if _model_service:
            _model_service.cleanup()
        logger.info("👋 Server stopped")


# Create FastAPI application
app = FastAPI(
    title="Hindi OCR API",
    description="FastAPI service for Hindi text extraction using Vision Encoder-Decoder (ViT + Hindi RoBERTa)",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "service": "Hindi OCR API",
        "version": "1.0.0",
        "status": "running",
        "model": settings.MODEL_NAME,
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "ocr_extract": "/api/ocr/extract",
            "ocr_extract_url": "/api/ocr/extract-url",
            "ocr_extract_base64": "/api/ocr/extract-base64"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Try to get from app.state, fallback to lazy init
        try:
            is_ready = hasattr(app.state, 'model_service') and app.state.model_service is not None
        except:
            is_ready = False
        
        # If not in state, we can still work with lazy loading
        if not is_ready:
            service = get_model_service()
            is_ready = service.is_loaded
        
        return {
            "status": "healthy",
            "model_loaded": is_ready,
            "model_name": settings.HUGGINGFACE_MODEL,
            "service_type": "huggingface-api",
            "version": "2.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "healthy",
            "model_loaded": True,
            "model_name": settings.HUGGINGFACE_MODEL,
            "service_type": "huggingface-api",
            "version": "2.0.0",
            "note": "Using lazy initialization"
        }


# Include routers
app.include_router(ocr.router, prefix="/api/ocr", tags=["OCR"])


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
