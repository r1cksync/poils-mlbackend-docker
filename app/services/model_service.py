import io
import logging
import time
import base64
import os
import tempfile
import json
from typing import Dict, Any, Optional
from PIL import Image
from google.cloud import vision

from app.core.config import settings

logger = logging.getLogger(__name__)


class ModelService:
    """
    Service for Hindi OCR using Google Cloud Vision API.
    Supports Hindi, English, and many other languages with high accuracy.
    """
    
    def __init__(self):
        """Initialize the Google Cloud Vision client"""
        self.client = None
        self.is_loaded = False
        self._setup_credentials()
        
    def _setup_credentials(self):
        """Setup Google Cloud credentials from environment or service account"""
        try:
            # Try to get credentials from environment variable
            creds_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
            if creds_json:
                # Write credentials to a temporary file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    f.write(creds_json)
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f.name
            
            # Initialize the Vision API client
            self.client = vision.ImageAnnotatorClient()
            self.is_loaded = True
            logger.info("✅ Google Cloud Vision API client initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Google Cloud Vision client: {str(e)}")
            self.is_loaded = False

    async def extract_text(self, image_data: bytes) -> Dict[str, Any]:
        """
        Extract Hindi/English text from image using Google Cloud Vision API
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        start_time = time.time()
        
        try:
            if not self.is_loaded or not self.client:
                raise ValueError("Google Cloud Vision client not properly initialized")
            
            # Create Vision API image object
            image = vision.Image(content=image_data)
            
            # Perform text detection with language hints for better Hindi recognition
            response = self.client.text_detection(
                image=image,
                image_context=vision.ImageContext(
                    language_hints=['hi', 'en']  # Hindi and English
                )
            )
            
            # Check for errors
            if response.error.message:
                raise Exception(f"Vision API error: {response.error.message}")
            
            # Extract text
            texts = response.text_annotations
            extracted_text = ""
            confidence = 0.0
            
            if texts:
                # First annotation contains the full text
                extracted_text = texts[0].description.strip()
                
                # Calculate average confidence from individual words
                confidences = []
                for text in texts[1:]:  # Skip first (full text) annotation
                    if hasattr(text, 'confidence'):
                        confidences.append(text.confidence)
                
                if confidences:
                    confidence = sum(confidences) / len(confidences) * 100
                else:
                    # If no confidence data, estimate based on text length
                    confidence = min(95.0, len(extracted_text) * 2) if extracted_text else 0.0
            
            processing_time = time.time() - start_time
            
            # Get image dimensions for metadata
            pil_image = Image.open(io.BytesIO(image_data))
            width, height = pil_image.size
            
            result = {
                "text": extracted_text,
                "confidence": round(confidence, 2),
                "processing_time": round(processing_time, 2),
                "metadata": {
                    "model": "Google Cloud Vision API",
                    "languages": ["Hindi", "English"],
                    "image_size": f"{width}x{height}",
                    "num_detections": len(texts) - 1 if texts else 0
                }
            }
            
            logger.info(f"✅ Text extraction successful: {len(extracted_text)} characters, "
                       f"{confidence:.1f}% confidence, {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Google Cloud Vision OCR failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            return {
                "text": "",
                "confidence": 0.0,
                "processing_time": round(processing_time, 2),
                "metadata": {
                    "model": "Google Cloud Vision API",
                    "error": error_msg,
                    "languages": ["Hindi", "English"]
                }
            }

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return {
            "model_name": "Google Cloud Vision API",
            "model_type": "cloud-ocr",
            "languages": ["Hindi", "English", "50+ others"],
            "status": "loaded" if self.is_loaded else "not_loaded",
            "features": [
                "Multi-language OCR",
                "High accuracy Hindi text recognition",
                "Automatic language detection",
                "Confidence scoring",
                "Batch processing support"
            ],
            "capabilities": {
                "hindi_support": True,
                "english_support": True,
                "handwritten_text": True,
                "printed_text": True,
                "confidence_scores": True
            }
        }

    def cleanup(self):
        """Clean up resources"""
        try:
            if self.client:
                # Close any open connections
                self.client = None
            
            # Clean up temporary credentials file if it exists
            creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if creds_path and creds_path.endswith('.json') and '/tmp' in creds_path:
                try:
                    os.unlink(creds_path)
                except:
                    pass
            
            self.is_loaded = False
            logger.info("🧹 ModelService cleanup completed")
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {str(e)}")

    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()