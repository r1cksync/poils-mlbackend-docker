import cv2
import numpy as np
import pytesseract
from PIL import Image
import io
import logging
import time
from typing import Dict
import base64

from app.core.config import settings

logger = logging.getLogger(__name__)


class ModelService:
    """
    Service for Hindi OCR using Tesseract OCR.
    Supports Hindi, English, and many other languages.
    """
    
    def __init__(self):
        # Use Tesseract OCR for reliable Hindi text recognition
        self.model_name = "Tesseract OCR (Hindi + English)"
        self.is_loaded = True
        
        # Configure Tesseract for Hindi and English
        self.tesseract_config = r'--oem 3 --psm 6 -l hin+eng'
        
        # Verify Tesseract installation
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract version: {version}")
        except Exception as e:
            logger.warning(f"Tesseract not found locally: {e}")
    
    async def load_model(self):
        """
        No model loading needed - Tesseract is ready to use.
        This method exists for compatibility with the original interface.
        """
        logger.info(f"✅ Using Tesseract OCR Engine")
        logger.info(f"Languages: Hindi (hin) + English (eng)")
        logger.info(f"Config: {self.tesseract_config}")
        
        self.is_loaded = True
    
    async def extract_text(
        self, 
        image: Image.Image, 
        max_length: int = 512
    ) -> Dict:
        """
        Extract Hindi/English text from image using Tesseract OCR.
        
        Args:
            image: PIL Image to process
            max_length: Not used with Tesseract, kept for compatibility
            
        Returns:
            Dictionary with extracted text and metadata
        """
        if not self.is_loaded:
            raise RuntimeError("Service not initialized. Call load_model() first.")
        
        try:
            start_time = time.time()
            
            # Convert PIL to OpenCV format for preprocessing
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Preprocess image for better OCR results
            # Convert to grayscale
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # Apply threshold to get better contrast
            _, threshold = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Convert back to PIL Image for Tesseract
            processed_image = Image.fromarray(threshold)
            
            logger.info(f"Processing image with Tesseract OCR (Hindi + English)")
            
            # Extract text using Tesseract
            try:
                # Try with Hindi + English
                extracted_text = pytesseract.image_to_string(
                    processed_image, 
                    config=self.tesseract_config,
                    timeout=30
                )
                
                # Get confidence scores
                data = pytesseract.image_to_data(
                    processed_image,
                    config=self.tesseract_config,
                    output_type=pytesseract.Output.DICT
                )
                
                # Calculate average confidence
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                
            except Exception as tesseract_error:
                logger.warning(f"Hindi OCR failed: {tesseract_error}. Trying English only...")
                # Fallback to English only
                extracted_text = pytesseract.image_to_string(
                    processed_image,
                    config=r'--oem 3 --psm 6 -l eng'
                )
                avg_confidence = 75  # Default confidence for English fallback
            
            processing_time = time.time() - start_time
            
            # Clean up the text
            cleaned_text = extracted_text.strip()
            
            logger.info(f"✅ Text extracted in {processing_time:.2f}s")
            logger.info(f"Extracted text: '{cleaned_text[:100]}...'")
            logger.info(f"Confidence: {avg_confidence:.1f}%")
            
            return {
                "text": cleaned_text,
                "confidence": round(avg_confidence / 100, 2),  # Convert to 0-1 scale
                "processing_time": round(processing_time, 2),
                "device": "local-tesseract",
                "model": self.model_name
            }
            
        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            return {
                "text": "",
                "confidence": 0.0,
                "processing_time": time.time() - start_time,
                "device": "local-tesseract",
                "model": self.model_name,
                "error": f"OCR failed: {str(e)}"
            }
    
    async def batch_extract(
        self, 
        images: list[Image.Image], 
        max_length: int = 512
    ) -> list[Dict]:
        """
        Extract text from multiple images in batch.
        
        Args:
            images: List of PIL Images
            max_length: Not used with API
            
        Returns:
            List of extraction results
        """
        results = []
        
        for idx, image in enumerate(images):
            try:
                logger.info(f"Processing image {idx + 1}/{len(images)}")
                result = await self.extract_text(image, max_length)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process image {idx + 1}: {str(e)}")
                results.append({
                    "text": "",
                    "error": str(e),
                    "processing_time": 0,
                    "confidence": 0.0
                })
        
        return results
    
    def cleanup(self):
        """Clean up resources (nothing to clean for API service)"""
        logger.info("API service cleanup - no resources to free")
        self.is_loaded = False
    
    def get_model_info(self) -> Dict:
        """Get information about the Tesseract OCR service"""
        try:
            version = pytesseract.get_tesseract_version()
            version_str = str(version)
        except:
            version_str = "Unknown"
            
        return {
            "model_name": self.model_name,
            "is_loaded": self.is_loaded,
            "service_type": "tesseract-ocr",
            "version": version_str,
            "languages": "Hindi (hin) + English (eng)",
            "has_api_key": False,  # Tesseract doesn't need API key
            "rate_limit": "No limits (local processing)"
        }
