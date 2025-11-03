"""
Image embedding service using OpenAI CLIP (ViT-B/32 model).
Multi-modal: Understands both images and text.
Outputs: 512-dimensional embeddings.

Architecture:
- Model: clip-vit-base-patch32 (ViT-B/32)
- Image Encoder: Vision Transformer
- Text Encoder: Text Transformer
- Embedding Dimension: 512
- Memory: ~350MB (optimized PyTorch 2.0.1)
- Performance: ~100-200ms per image (CPU), ~50ms (GPU)
"""
import logging
from typing import List, Optional, Union
import numpy as np
from PIL import Image
import io
import torch
import torchvision.transforms as transforms
from transformers import CLIPModel, CLIPProcessor

logger = logging.getLogger(__name__)

class ImageEmbeddingService:
    """Extract image and text embeddings using OpenAI CLIP (ViT-B/32)."""
    
    _instance = None
    _model = None
    _processor = None
    _device = None
    
    # CLIP Model Configuration
    MODEL_NAME = "openai/clip-vit-base-patch32"  # ViT-B/32: optimal for e-commerce
    EMBEDDING_DIMENSION = 512
    IMAGE_SIZE = 224
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._model is None:
            self._initialize_model()
    
    def _initialize_model(self):
        """Initialize CLIP ViT-B/32 model."""
        try:
            logger.info("🔄 Loading CLIP ViT-B/32 model...")
            
            # Determine device (GPU if available, else CPU)
            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            logger.info(f"   Device: {self._device}")
            
            # Load CLIP model (ViT-B/32)
            logger.info(f"   Model: {self.MODEL_NAME}")
            self._model = CLIPModel.from_pretrained(self.MODEL_NAME)
            self._processor = CLIPProcessor.from_pretrained(self.MODEL_NAME)
            
            # Move model to device
            self._model = self._model.to(self._device)
            self._model.eval()  # Set to evaluation mode
            
            logger.info(f"✅ CLIP ViT-B/32 loaded successfully")
            logger.info(f"   Embedding dimension: {self.EMBEDDING_DIMENSION}")
            logger.info(f"   Image size: {self.IMAGE_SIZE}x{self.IMAGE_SIZE}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load CLIP model: {e}")
            raise RuntimeError(f"CLIP model initialization failed: {e}")
    
    def embed_image(self, image_data: Union[bytes, Image.Image]) -> List[float]:
        """
        Generate CLIP embedding from image.
        
        Args:
            image_data: Image bytes or PIL Image object
            
        Returns:
            List of 512 floats (CLIP embedding)
        """
        try:
            # Convert bytes to PIL Image if needed
            if isinstance(image_data, bytes):
                image = Image.open(io.BytesIO(image_data)).convert("RGB")
            else:
                image = image_data.convert("RGB")
            
            # Process image
            inputs = self._processor(
                images=image,
                return_tensors="pt",
                padding=True
            )
            
            # Move inputs to device
            for key in inputs:
                if isinstance(inputs[key], torch.Tensor):
                    inputs[key] = inputs[key].to(self._device)
            
            # Get image embeddings
            with torch.no_grad():
                image_features = self._model.get_image_features(**inputs)
            
            # Normalize embeddings (important for similarity search)
            image_features = torch.nn.functional.normalize(image_features, p=2, dim=-1)
            
            # Convert to list
            embedding = image_features[0].cpu().numpy().tolist()
            
            logger.debug(f"Image embedding generated: {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"❌ Image embedding error: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate CLIP embedding from text.
        Useful for cross-modal search.
        
        Args:
            text: Text string (e.g., product description)
            
        Returns:
            List of 512 floats (CLIP embedding)
        """
        try:
            # Process text
            inputs = self._processor(
                text=text,
                return_tensors="pt",
                padding=True,
                truncation=True
            )
            
            # Move inputs to device
            for key in inputs:
                if isinstance(inputs[key], torch.Tensor):
                    inputs[key] = inputs[key].to(self._device)
            
            # Get text embeddings
            with torch.no_grad():
                text_features = self._model.get_text_features(**inputs)
            
            # Normalize embeddings
            text_features = torch.nn.functional.normalize(text_features, p=2, dim=-1)
            
            # Convert to list
            embedding = text_features[0].cpu().numpy().tolist()
            
            logger.debug(f"Text embedding generated: {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"❌ Text embedding error: {e}")
            raise
    
    def image_similarity(self, 
                        image1_data: Union[bytes, Image.Image],
                        image2_data: Union[bytes, Image.Image]) -> float:
        """
        Calculate similarity between two images using CLIP.
        
        Args:
            image1_data: First image (bytes or PIL Image)
            image2_data: Second image (bytes or PIL Image)
            
        Returns:
            Similarity score (0.0 to 1.0, higher = more similar)
        """
        try:
            embedding1 = np.array(self.embed_image(image1_data))
            embedding2 = np.array(self.embed_image(image2_data))
            
            # Cosine similarity (already normalized, so just dot product)
            similarity = float(np.dot(embedding1, embedding2))
            
            return similarity
            
        except Exception as e:
            logger.error(f"❌ Image similarity error: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """Return embedding dimension (512 for ViT-B/32)."""
        return self.EMBEDDING_DIMENSION
    
    def get_model_info(self) -> dict:
        """Return model information."""
        return {
            "model": self.MODEL_NAME,
            "architecture": "ViT-B/32 (Vision Transformer)",
            "embedding_dimension": self.EMBEDDING_DIMENSION,
            "device": str(self._device),
            "text_max_length": 77,
            "image_size": self.IMAGE_SIZE,
            "description": "Multi-modal CLIP model from OpenAI. Understands images and text in the same embedding space."
        }


# Singleton instance
_image_embedding_service = None


def get_image_embedding_service() -> ImageEmbeddingService:
    """Get or create singleton image embedding service."""
    global _image_embedding_service
    if _image_embedding_service is None:
        _image_embedding_service = ImageEmbeddingService()
    return _image_embedding_service

def get_image_embedding_service() -> ImageEmbeddingService:
    """Get singleton image embedding service."""
    global _image_embedding_service
    if _image_embedding_service is None:
        _image_embedding_service = ImageEmbeddingService()
    return _image_embedding_service
