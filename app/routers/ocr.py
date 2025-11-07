from fastapi import APIRouter, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse
import logging
import time
import aiohttp
import io

from app.models.schemas import (
    OCRResponse, OCRURLRequest, OCRBase64Request, 
    ErrorResponse, ImageInfo
)
from app.services.image_processor import ImageProcessor
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize image processor
image_processor = ImageProcessor(max_dimension=settings.MAX_IMAGE_DIMENSION)


@router.post(
    "/extract",
    response_model=OCRResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Extract text from uploaded image",
    description="Upload an image file (JPEG, PNG, PDF) and extract Hindi text using Microsoft TrOCR"
)
async def extract_text_from_upload(
    request: Request,
    image: UploadFile = File(..., description="Image file to process")
):
    """
    Extract Hindi text from an uploaded image file.
    
    Supports: JPEG, PNG, PDF
    Max size: 10MB
    """
    try:
        # Validate file size
        contents = await image.read()
        file_size = len(contents)
        
        if file_size > settings.MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.MAX_IMAGE_SIZE / 1024 / 1024}MB"
            )
        
        # Validate content type
        if image.content_type not in settings.SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format. Supported: {', '.join(settings.SUPPORTED_FORMATS)}"
            )
        
        logger.info(f"Processing uploaded file: {image.filename} ({file_size} bytes)")
        
        start_time = time.time()
        
        # Convert to PIL Image
        pil_image = image_processor.bytes_to_image(contents)
        
        # Get image info before processing
        original_info = image_processor.get_image_info(pil_image)
        
        # Prepare image for OCR
        processed_image = image_processor.prepare_image(pil_image, preprocess=True)
        
        # Get model service from app state
        model_service = request.app.state.model_service
        
        # Extract text
        result = await model_service.extract_text(processed_image)
        
        total_time = time.time() - start_time
        
        return OCRResponse(
            success=True,
            text=result["text"],
            confidence=result["confidence"],
            processing_time=round(total_time, 2),
            image_info=ImageInfo(**original_info),
            device=result.get("device")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR extraction failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"OCR processing failed: {str(e)}"
        )


@router.post(
    "/extract-url",
    response_model=OCRResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Extract text from image URL",
    description="Provide an image URL and extract Hindi text using Microsoft TrOCR"
)
async def extract_text_from_url(
    request: Request,
    ocr_request: OCRURLRequest
):
    """
    Extract Hindi text from an image URL.
    
    Downloads the image from the provided URL and processes it.
    """
    try:
        logger.info(f"Downloading image from URL: {ocr_request.image_url}")
        
        start_time = time.time()
        
        # Download image
        async with aiohttp.ClientSession() as session:
            async with session.get(
                ocr_request.image_url,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to download image: HTTP {response.status}"
                    )
                
                image_bytes = await response.read()
        
        # Validate size
        if len(image_bytes) > settings.MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Image too large. Maximum size: {settings.MAX_IMAGE_SIZE / 1024 / 1024}MB"
            )
        
        # Convert to PIL Image
        pil_image = image_processor.bytes_to_image(image_bytes)
        
        # Get image info
        original_info = image_processor.get_image_info(pil_image)
        
        # Prepare image
        processed_image = image_processor.prepare_image(
            pil_image, 
            preprocess=ocr_request.preprocess
        )
        
        # Get model service
        model_service = request.app.state.model_service
        
        # Extract text
        result = await model_service.extract_text(
            processed_image,
            max_length=ocr_request.max_length
        )
        
        total_time = time.time() - start_time
        
        return OCRResponse(
            success=True,
            text=result["text"],
            confidence=result["confidence"],
            processing_time=round(total_time, 2),
            image_info=ImageInfo(**original_info),
            device=result.get("device")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"URL OCR failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process image from URL: {str(e)}"
        )


@router.post(
    "/extract-base64",
    response_model=OCRResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Extract text from base64 image",
    description="Provide a base64 encoded image and extract Hindi text using Microsoft TrOCR"
)
async def extract_text_from_base64(
    request: Request,
    ocr_request: OCRBase64Request
):
    """
    Extract Hindi text from a base64 encoded image.
    
    Supports data URLs (data:image/jpeg;base64,...) or raw base64 strings.
    """
    try:
        logger.info("Processing base64 image")
        
        start_time = time.time()
        
        # Convert base64 to PIL Image
        pil_image = image_processor.base64_to_image(ocr_request.image_base64)
        
        # Get image info
        original_info = image_processor.get_image_info(pil_image)
        
        # Prepare image
        processed_image = image_processor.prepare_image(
            pil_image,
            preprocess=ocr_request.preprocess
        )
        
        # Get model service
        model_service = request.app.state.model_service
        
        # Extract text
        result = await model_service.extract_text(
            processed_image,
            max_length=ocr_request.max_length
        )
        
        total_time = time.time() - start_time
        
        return OCRResponse(
            success=True,
            text=result["text"],
            confidence=result["confidence"],
            processing_time=round(total_time, 2),
            image_info=ImageInfo(**original_info),
            device=result.get("device")
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Base64 OCR failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process base64 image: {str(e)}"
        )


@router.get(
    "/model-info",
    summary="Get model information",
    description="Get information about the loaded OCR model"
)
async def get_model_info(request: Request):
    """Get information about the loaded Microsoft TrOCR model"""
    try:
        model_service = request.app.state.model_service
        return model_service.get_model_info()
    except Exception as e:
        logger.error(f"Failed to get model info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get model information")
