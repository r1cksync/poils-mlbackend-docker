import httpx
from huggingface_hub import InferenceClient
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
    Service for Hindi OCR using Hugging Face InferenceClient.
    Uses the new huggingface_hub library instead of deprecated API.
    """
    
    def __init__(self):
        # Use HF InferenceClient with the new API
        self.api_key = settings.HUGGINGFACE_API_KEY
        self.model_name = settings.HUGGINGFACE_MODEL
        self.is_loaded = True
        
        # Initialize InferenceClient
        self.client = InferenceClient(
            model=self.model_name,
            token=self.api_key if self.api_key and len(self.api_key) > 10 else None
        )
    
    async def load_model(self):
        """
        No model loading needed - using Hugging Face InferenceClient.
        This method exists for compatibility with the original interface.
        """
        logger.info(f"✅ Using Hugging Face InferenceClient")
        logger.info(f"Model: {self.model_name}")
        
        if not self.api_key or len(self.api_key) < 10:
            logger.warning("⚠️ No HUGGINGFACE_API_KEY provided - using free tier (rate limited)")
        else:
            logger.info("✅ API key configured")
        
        self.is_loaded = True
    
    async def extract_text(
        self, 
        image: Image.Image, 
        max_length: int = 512
    ) -> Dict:
        """
        Extract text from image using Hugging Face InferenceClient.
        
        Args:
            image: PIL Image to process
            max_length: Not used with API, kept for compatibility
            
        Returns:
            Dictionary with extracted text and metadata
        """
        if not self.is_loaded:
            raise RuntimeError("Service not initialized. Call load_model() first.")
        
        try:
            start_time = time.time()
            
            # Convert PIL Image to bytes
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            image_bytes = buffer.getvalue()
            
            logger.info(f"Sending request to Hugging Face InferenceClient ({len(image_bytes)} bytes)")
            
            # Use InferenceClient for image-to-text
            # Pass the raw bytes directly to the client
            try:
                result = self.client.image_to_text(image_bytes)
                logger.info(f"Raw result from InferenceClient: {result}")
            except Exception as client_error:
                logger.error(f"InferenceClient error: {str(client_error)}")
                # Fallback: try with PIL Image object
                result = self.client.image_to_text(image)
            
            # Extract text from response
            extracted_text = ""
            if isinstance(result, str):
                extracted_text = result
            elif isinstance(result, list) and len(result) > 0:
                # Result might be a list of dictionaries
                if isinstance(result[0], dict) and "generated_text" in result[0]:
                    extracted_text = result[0]["generated_text"]
                elif isinstance(result[0], str):
                    extracted_text = result[0]
            elif isinstance(result, dict) and "generated_text" in result:
                extracted_text = result["generated_text"]
            
            logger.info(f"Extracted text: '{extracted_text}'")
            
            processing_time = time.time() - start_time
            logger.info(f"✅ Text extracted in {processing_time:.2f}s: {extracted_text[:50]}...")
            
            return {
                "text": extracted_text.strip(),
                "confidence": 0.85,  # API doesn't provide confidence
                "processing_time": round(processing_time, 2),
                "device": "cloud-api",
                "model": self.model_name
            }
            
        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            # Return informative error
            return {
                "text": "",
                "confidence": 0.0,
                "processing_time": time.time() - start_time,
                "device": "cloud-api",
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
        """Get information about the InferenceClient service"""
        return {
            "model_name": self.model_name,
            "is_loaded": self.is_loaded,
            "service_type": "huggingface-inference-client",
            "client_type": "InferenceClient",
            "has_api_key": bool(self.api_key and len(self.api_key) > 10),
            "rate_limit": "Free tier (rate limited)" if not (self.api_key and len(self.api_key) > 10) else "Authenticated (higher limits)"
        }
