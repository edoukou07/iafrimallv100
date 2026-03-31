import logging
from typing import List, Optional
import torch
from PIL import Image
import io
import requests
import os
from transformers import CLIPProcessor, CLIPModel
from app.security.validators import validate_image_url, validate_file_size
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmbeddingService:
    """Service for generating CLIP embeddings from images and text"""
    
    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
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
    
    def get_image_from_url(
        self,
        image_url: str,
        allowed_domains: Optional[List[str]] = None,
        timeout: int = 10
    ) -> Image.Image:
        """
        Download and load image from URL with SSRF prevention
        
        Args:
            image_url: URL to download image from
            allowed_domains: Optional whitelist of allowed domains
            timeout: Request timeout in seconds
        
        Returns:
            PIL Image object
        
        Raises:
            HTTPException: If URL is invalid or unsafe
        """
        # Validate URL for SSRF attacks
        validate_image_url(image_url, allowed_domains)
        
        try:
            # Get whitelisted domains from config if not provided
            if allowed_domains is None and settings.image_url_whitelist:
                allowed_domains = settings.image_url_whitelist
            
            # Use settings timeout if available
            timeout = settings.max_image_url_timeout or timeout
            
            logger.info(f"Downloading image from: {image_url}")
            response = requests.get(
                image_url,
                timeout=timeout,
                verify=True,  # Always verify SSL certificates
                allow_redirects=False  # Prevent redirect attacks
            )
            response.raise_for_status()
            
            # Validate content length before processing
            content_length = response.headers.get("content-length")
            if content_length:
                content_length = int(content_length)
                validate_file_size(content_length, settings.max_upload_size_mb)
            
            # Verify MIME type
            content_type = response.headers.get("content-type", "").lower()
            if not any(mime in content_type for mime in ["image/", "application/octet-stream"]):
                logger.warning(f"Unexpected content-type: {content_type}")
                raise ValueError(f"Invalid content type: {content_type}")
            
            image = Image.open(io.BytesIO(response.content)).convert("RGB")
            logger.debug(f"Image loaded successfully from {image_url}")
            return image
            
        except Exception as e:
            logger.error(f"Error loading image from URL {image_url}: {e}")
            raise
    
    def get_image_from_file(self, image_path: str) -> Image.Image:
        """
        Load image from local file
        
        Args:
            image_path: Path to image file
        
        Returns:
            PIL Image object
        """
        try:
            # Validate path doesn't contain directory traversal
            if ".." in image_path:
                raise ValueError("Directory traversal not allowed")
            
            logger.debug(f"Loading image from file: {image_path}")
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
        """Generate embedding for text (max 77 tokens for CLIP)"""
        if self.model is None:
            # Return mock embedding for development
            import hashlib
            hash_val = hashlib.md5(text.encode()).digest()
            return [float(b) / 256.0 for b in hash_val[:512]]
        
        try:
            with torch.no_grad():
                # CLIP has max 77 tokens - truncate and pad
                inputs = self.processor(
                    text=text, 
                    return_tensors="pt", 
                    padding=True,
                    truncation=True,
                    max_length=77
                )
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                text_features = self.model.get_text_features(**inputs)
                text_features = text_features / text_features.norm(p=2, dim=-1, keepdim=True)
                
                embedding = text_features[0].cpu().numpy().tolist()
                return embedding
        except Exception as e:
            logger.error(f"Error embedding text: {e}")
            raise
    
    def embed_image_from_url(
        self,
        image_url: str,
        allowed_domains: Optional[List[str]] = None
    ) -> List[float]:
        """Generate embedding from image URL with security validation"""
        image = self.get_image_from_url(image_url, allowed_domains)
    
    def embed_image_from_file(self, image_path: str) -> List[float]:
        """Generate embedding from image file"""
        image = self.get_image_from_file(image_path)
        return self.embed_image(image)
    
    def get_dimension(self) -> int:
        """Return the dimension of embeddings (512 for CLIP)"""
        return 512
