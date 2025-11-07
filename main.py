from fastapi import FastAPI, File, UploadFile, HTTPException
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

# Global model service instance
model_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for FastAPI application.
    Loads ML model on startup and cleans up on shutdown.
    """
    global model_service
    
    try:
        logger.info("🚀 Starting Hindi OCR API Server...")
        logger.info(f"Loading Indic-TrOCR model: {settings.MODEL_NAME}")
        
        # Initialize model service
        model_service = ModelService()
        await model_service.load_model()
        
        # Store in app state
        app.state.model_service = model_service
        
        logger.info("✅ Model loaded successfully!")
        logger.info(f"📡 API ready at: http://{settings.HOST}:{settings.PORT}")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to start server: {str(e)}")
        raise
    finally:
        logger.info("🔄 Shutting down server...")
        if model_service:
            model_service.cleanup()
        logger.info("👋 Server stopped")


# Create FastAPI application
app = FastAPI(
    title="Hindi OCR API",
    description="FastAPI service for Hindi text extraction using Indic-TrOCR model",
    version="1.0.0",
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
        is_ready = app.state.model_service is not None
        
        return {
            "status": "healthy" if is_ready else "starting",
            "model_loaded": is_ready,
            "model_name": settings.MODEL_NAME,
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")


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
