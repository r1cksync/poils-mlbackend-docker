from pydantic import BaseModel, Field, validator
from typing import Optional, List


class OCRRequest(BaseModel):
    """Base OCR request model"""
    preprocess: bool = Field(
        default=True,
        description="Apply image preprocessing for better OCR accuracy"
    )
    max_length: int = Field(
        default=512,
        ge=64,
        le=1024,
        description="Maximum length of extracted text"
    )


class OCRURLRequest(OCRRequest):
    """Request model for OCR from image URL"""
    image_url: str = Field(
        ...,
        description="URL of the image to process",
        min_length=1
    )
    
    @validator('image_url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class OCRBase64Request(OCRRequest):
    """Request model for OCR from base64 image"""
    image_base64: str = Field(
        ...,
        description="Base64 encoded image data",
        min_length=1
    )


class ImageInfo(BaseModel):
    """Image metadata"""
    width: int
    height: int
    mode: str
    format: str


class OCRResponse(BaseModel):
    """OCR response model"""
    success: bool = Field(
        default=True,
        description="Whether the operation was successful"
    )
    text: str = Field(
        ...,
        description="Extracted Hindi text from the image"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score of the extraction"
    )
    processing_time: float = Field(
        ...,
        description="Time taken to process the image in seconds"
    )
    image_info: Optional[ImageInfo] = Field(
        default=None,
        description="Metadata about the processed image"
    )
    device: Optional[str] = Field(
        default=None,
        description="Device used for inference (cpu/cuda)"
    )


class OCRBatchResponse(BaseModel):
    """Batch OCR response model"""
    success: bool = True
    results: List[OCRResponse]
    total_images: int
    total_time: float


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str = Field(
        ...,
        description="Error message"
    )
    detail: Optional[str] = Field(
        default=None,
        description="Detailed error information"
    )


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    model_loaded: bool
    model_name: str
    version: str
