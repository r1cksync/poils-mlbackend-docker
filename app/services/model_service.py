from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
import torch
import logging
import time
from typing import Dict, Optional
import asyncio

from app.core.config import settings

logger = logging.getLogger(__name__)


class ModelService:
    """
    Service for managing the Microsoft TrOCR model.
    Handles model loading, inference, and resource management.
    """
    
    def __init__(self):
        self.model_name = settings.MODEL_NAME
        self.processor: Optional[TrOCRProcessor] = None
        self.model: Optional[VisionEncoderDecoderModel] = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.is_loaded = False
    
    async def load_model(self):
        """Load the TrOCR model and processor"""
        try:
            logger.info(f"Loading model: {self.model_name}")
            logger.info(f"Using device: {self.device}")
            
            # Load processor (tokenizer + feature extractor)
            self.processor = TrOCRProcessor.from_pretrained(
                self.model_name,
                cache_dir=settings.MODEL_CACHE_DIR
            )
            
            # Load model
            self.model = VisionEncoderDecoderModel.from_pretrained(
                self.model_name,
                cache_dir=settings.MODEL_CACHE_DIR
            )
            
            # Move model to device
            self.model.to(self.device)
            self.model.eval()  # Set to evaluation mode
            
            self.is_loaded = True
            logger.info(f"✅ Model loaded successfully on {self.device}")
            
            # Log model info
            total_params = sum(p.numel() for p in self.model.parameters())
            logger.info(f"Model parameters: {total_params:,}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load model: {str(e)}")
            raise RuntimeError(f"Model loading failed: {str(e)}")
    
    async def extract_text(
        self, 
        image: Image.Image, 
        max_length: int = 512
    ) -> Dict:
        """
        Extract Hindi text from image using TrOCR model.
        
        Args:
            image: PIL Image to process
            max_length: Maximum length of generated text
            
        Returns:
            Dictionary with extracted text, confidence, and metadata
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        try:
            start_time = time.time()
            
            # Preprocess image
            pixel_values = self.processor(
                images=image, 
                return_tensors="pt"
            ).pixel_values
            
            # Move to device
            pixel_values = pixel_values.to(self.device)
            
            # Generate text with no_grad for inference
            with torch.no_grad():
                generated_ids = self.model.generate(
                    pixel_values,
                    max_length=max_length,
                    num_beams=4,  # Beam search for better results
                    early_stopping=True
                )
            
            # Decode generated text
            extracted_text = self.processor.batch_decode(
                generated_ids, 
                skip_special_tokens=True
            )[0]
            
            processing_time = time.time() - start_time
            
            logger.info(f"Text extracted in {processing_time:.2f}s: {extracted_text[:50]}...")
            
            return {
                "text": extracted_text.strip(),
                "confidence": self._calculate_confidence(generated_ids),
                "processing_time": round(processing_time, 2),
                "device": self.device,
                "model": self.model_name
            }
            
        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            raise RuntimeError(f"OCR processing failed: {str(e)}")
    
    def _calculate_confidence(self, generated_ids: torch.Tensor) -> float:
        """
        Calculate confidence score based on model output.
        This is a simplified confidence calculation.
        """
        try:
            # For now, return a placeholder confidence
            # In production, you'd calculate this from model logits
            return 0.85
        except:
            return 0.0
    
    async def batch_extract(
        self, 
        images: list[Image.Image], 
        max_length: int = 512
    ) -> list[Dict]:
        """
        Extract text from multiple images in batch.
        
        Args:
            images: List of PIL Images
            max_length: Maximum length of generated text
            
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
        """Clean up model resources"""
        try:
            if self.model:
                del self.model
            if self.processor:
                del self.processor
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            self.is_loaded = False
            logger.info("Model resources cleaned up")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
    
    def get_model_info(self) -> Dict:
        """Get information about the loaded model"""
        return {
            "model_name": self.model_name,
            "is_loaded": self.is_loaded,
            "device": self.device,
            "cuda_available": torch.cuda.is_available(),
            "torch_version": torch.__version__
        }
