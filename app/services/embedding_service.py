import logging
from typing import List
import torch
from PIL import Image
import io
import requests
import os
from transformers import CLIPProcessor, CLIPModel

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating CLIP embeddings from images and text"""
    
    def __init__(self, model_name: str = "sentence-transformers/clip-ViT-B-32"):
        """Initialize CLIP model and processor"""
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.processor = None
        
        # Skip model loading in local dev to avoid HuggingFace auth issues
        if os.getenv("ENVIRONMENT") != "development":
            logger.info(f"Loading CLIP model: {model_name} on device: {self.device}")
            try:
                self.model = CLIPModel.from_pretrained(model_name)
                self.processor = CLIPProcessor.from_pretrained(model_name)
                self.model.to(self.device)
                self.model.eval()
                logger.info(f"CLIP model loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load CLIP model: {e}. Using mock embeddings.")
                self.model = None
                self.processor = None
        else:
            logger.info(f"Development mode: Using mock embeddings (no model loaded)")
    
    def get_image_from_url(self, image_url: str) -> Image.Image:
        """Download and load image from URL"""
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            image = Image.open(io.BytesIO(response.content)).convert("RGB")
            return image
        except Exception as e:
            logger.error(f"Error loading image from URL {image_url}: {e}")
            raise
    
    def get_image_from_file(self, image_path: str) -> Image.Image:
        """Load image from local file"""
        try:
            image = Image.open(image_path).convert("RGB")
            return image
        except Exception as e:
            logger.error(f"Error loading image from file {image_path}: {e}")
            raise
    
    def embed_image(self, image: Image.Image) -> List[float]:
        """Generate embedding for image"""
        if self.model is None:
            # Return mock embedding for development
            import hashlib
            hash_val = hashlib.md5(str(image.tobytes()).encode()).digest()
            return [float(b) / 256.0 for b in hash_val[:512]]
        
        try:
            with torch.no_grad():
                inputs = self.processor(images=image, return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                image_features = self.model.get_image_features(**inputs)
                image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
                
                embedding = image_features[0].cpu().numpy().tolist()
                return embedding
        except Exception as e:
            logger.error(f"Error embedding image: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text"""
        if self.model is None:
            # Return mock embedding for development
            import hashlib
            hash_val = hashlib.md5(text.encode()).digest()
            return [float(b) / 256.0 for b in hash_val[:512]]
        
        try:
            with torch.no_grad():
                inputs = self.processor(text=text, return_tensors="pt", padding=True)
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                text_features = self.model.get_text_features(**inputs)
                text_features = text_features / text_features.norm(p=2, dim=-1, keepdim=True)
                
                embedding = text_features[0].cpu().numpy().tolist()
                return embedding
        except Exception as e:
            logger.error(f"Error embedding text: {e}")
            raise
    
    def embed_image_from_url(self, image_url: str) -> List[float]:
        """Generate embedding from image URL"""
        image = self.get_image_from_url(image_url)
        return self.embed_image(image)
    
    def embed_image_from_file(self, image_path: str) -> List[float]:
        """Generate embedding from image file"""
        image = self.get_image_from_file(image_path)
        return self.embed_image(image)
