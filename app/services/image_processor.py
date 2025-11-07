from PIL import Image
import io
import base64
import logging
from typing import Tuple, Optional
import cv2
import numpy as np
from pdf2image import convert_from_bytes

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Image preprocessing and utilities for OCR"""
    
    def __init__(self, max_dimension: int = 2048):
        self.max_dimension = max_dimension
    
    @staticmethod
    def validate_image(image_bytes: bytes) -> bool:
        """Validate if bytes represent a valid image"""
        try:
            Image.open(io.BytesIO(image_bytes))
            return True
        except Exception as e:
            logger.error(f"Invalid image: {str(e)}")
            return False
    
    @staticmethod
    def bytes_to_image(image_bytes: bytes) -> Image.Image:
        """Convert bytes to PIL Image"""
        try:
            return Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            logger.error(f"Failed to convert bytes to image: {str(e)}")
            raise ValueError("Invalid image data")
    
    @staticmethod
    def base64_to_image(base64_string: str) -> Image.Image:
        """Convert base64 string to PIL Image"""
        try:
            # Remove data URL prefix if present
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            image_bytes = base64.b64decode(base64_string)
            return Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            logger.error(f"Failed to convert base64 to image: {str(e)}")
            raise ValueError("Invalid base64 image data")
    
    @staticmethod
    def pdf_to_images(pdf_bytes: bytes) -> list[Image.Image]:
        """Convert PDF to list of PIL Images"""
        try:
            images = convert_from_bytes(pdf_bytes)
            logger.info(f"Converted PDF to {len(images)} images")
            return images
        except Exception as e:
            logger.error(f"Failed to convert PDF: {str(e)}")
            raise ValueError("Invalid PDF file")
    
    def resize_image(self, image: Image.Image) -> Image.Image:
        """Resize image if it exceeds max dimensions"""
        width, height = image.size
        
        if width <= self.max_dimension and height <= self.max_dimension:
            return image
        
        # Calculate new dimensions maintaining aspect ratio
        if width > height:
            new_width = self.max_dimension
            new_height = int(height * (self.max_dimension / width))
        else:
            new_height = self.max_dimension
            new_width = int(width * (self.max_dimension / height))
        
        logger.info(f"Resizing image from {width}x{height} to {new_width}x{new_height}")
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    @staticmethod
    def preprocess_for_ocr(image: Image.Image) -> Image.Image:
        """
        Preprocess image to improve OCR accuracy.
        Applies grayscale conversion, contrast enhancement, and noise reduction.
        """
        try:
            # Convert PIL to OpenCV
            img_array = np.array(image)
            
            # Convert to grayscale if colored
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # Apply adaptive thresholding for better text contrast
            processed = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Denoise
            processed = cv2.fastNlMeansDenoising(processed, None, 10, 7, 21)
            
            # Convert back to PIL
            return Image.fromarray(processed)
            
        except Exception as e:
            logger.warning(f"Preprocessing failed, using original image: {str(e)}")
            return image
    
    def prepare_image(self, image: Image.Image, preprocess: bool = True) -> Image.Image:
        """
        Complete image preparation pipeline.
        Converts to RGB, resizes, and optionally preprocesses.
        """
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large
            image = self.resize_image(image)
            
            # Apply OCR preprocessing
            if preprocess:
                image = self.preprocess_for_ocr(image)
            
            return image
            
        except Exception as e:
            logger.error(f"Image preparation failed: {str(e)}")
            raise
    
    @staticmethod
    def get_image_info(image: Image.Image) -> dict:
        """Extract image metadata"""
        return {
            "width": image.width,
            "height": image.height,
            "mode": image.mode,
            "format": image.format if hasattr(image, 'format') else "Unknown"
        }
