import httpx
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
    Service for Hindi OCR using Hugging Face Inference API.
    No local model loading required - uses cloud API instead.
    """
    
    def __init__(self):
        # Use new HF Router URL instead of deprecated api-inference
        self.api_url = settings.HUGGINGFACE_ROUTER_URL
        self.api_key = settings.HUGGINGFACE_API_KEY
        self.model_name = settings.HUGGINGFACE_MODEL
        self.is_loaded = True  # Always "loaded" since we use API
        
        # Only use API key if explicitly set and not empty
        # Some API keys may cause 410 errors with the inference API
        self.headers = {"Content-Type": "image/png"}
        if self.api_key and len(self.api_key) > 10:
            # Try with authorization first, will fallback to free tier on 403/410
            self.headers["Authorization"] = f"Bearer {self.api_key}"
    
    async def load_model(self):
        """
        No model loading needed - using Hugging Face Inference API.
        This method exists for compatibility with the original interface.
        """
        logger.info(f"✅ Using Hugging Face Inference API")
        logger.info(f"Model: {self.model_name}")
        logger.info(f"API: {self.api_url}")
        
        if not self.api_key:
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
        Extract Hindi text from image using Hugging Face Inference API.
        
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
            
            logger.info(f"Sending request to Hugging Face API ({len(image_bytes)} bytes)")
            
            # Call Hugging Face Inference API
            async with httpx.AsyncClient(timeout=settings.API_TIMEOUT) as client:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    data=image_bytes
                )
            
            # Handle response
            if response.status_code == 200:
                result = response.json()
                
                # Extract text from response
                # API returns: {"generated_text": "extracted text"}
                extracted_text = ""
                if isinstance(result, list) and len(result) > 0:
                    extracted_text = result[0].get("generated_text", "")
                elif isinstance(result, dict):
                    extracted_text = result.get("generated_text", "")
                
                processing_time = time.time() - start_time
                
                logger.info(f"✅ Text extracted in {processing_time:.2f}s: {extracted_text[:50]}...")
                
                return {
                    "text": extracted_text.strip(),
                    "confidence": 0.85,  # API doesn't provide confidence
                    "processing_time": round(processing_time, 2),
                    "device": "cloud-api",
                    "model": self.model_name
                }
            
            elif response.status_code == 403 or response.status_code == 410:
                # API key has insufficient permissions or endpoint deprecated with auth, try without auth
                logger.warning(f"Auth error ({response.status_code}), retrying without authentication (free tier)")
                
                async with httpx.AsyncClient(timeout=settings.API_timeout) as client:
                    retry_response = await client.post(
                        self.api_url,
                        headers={"Content-Type": "image/png"},
                        data=image_bytes
                    )
                
                if retry_response.status_code == 200:
                    result = retry_response.json()
                    extracted_text = ""
                    if isinstance(result, list) and len(result) > 0:
                        extracted_text = result[0].get("generated_text", "")
                    elif isinstance(result, dict):
                        extracted_text = result.get("generated_text", "")
                    
                    processing_time = time.time() - start_time
                    logger.info(f"✅ Text extracted (free tier) in {processing_time:.2f}s: {extracted_text[:50]}...")
                    
                    return {
                        "text": extracted_text.strip(),
                        "confidence": 0.85,
                        "processing_time": round(processing_time, 2),
                        "device": "cloud-api-free",
                        "model": self.model_name
                    }
                else:
                    error_msg = f"API request failed even without auth: {retry_response.status_code} - {retry_response.text[:200]}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
            
            elif response.status_code == 503:
                # Model is loading
                logger.warning("Model is loading on Hugging Face, please retry in a moment")
                return {
                    "text": "",
                    "confidence": 0.0,
                    "processing_time": time.time() - start_time,
                    "device": "cloud-api",
                    "model": self.model_name,
                    "error": "Model is loading, please retry in 20-30 seconds"
                }
            
            else:
                error_msg = f"API request failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
        except httpx.TimeoutException:
            logger.error("Request timeout - API took too long to respond")
            raise RuntimeError("Request timeout - please try again")
        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            raise RuntimeError(f"OCR processing failed: {str(e)}")
    
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
        """Get information about the API service"""
        return {
            "model_name": self.model_name,
            "is_loaded": self.is_loaded,
            "service_type": "huggingface-inference-api",
            "api_url": self.api_url,
            "has_api_key": bool(self.api_key),
            "rate_limit": "Free tier (no key)" if not self.api_key else "Authenticated"
        }
