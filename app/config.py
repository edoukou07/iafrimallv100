"""Application configuration with security hardening"""

import logging
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional, List

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings with security defaults"""
    
    # ===== Environment & Debug =====
    environment: str = "development"  # development, staging, production
    debug: bool = False  # ⚠️ NEVER True in production
    
    # ===== API Configuration =====
    api_title: str = "Image Search API"
    api_version: str = "2.0.0"
    api_description: str = "CLIP-powered image search with security hardening"
    
    # ===== Security =====
    # JWT Secret Key (MUST be set in production)
    secret_key: str = "change-me-in-production-min-32-chars"
    jwt_algorithm: str = "HS256"
    access_token_expire_hours: int = 24
    
    # API Keys (for service-to-service auth)
    api_key: Optional[str] = None
    indexation_api_key: Optional[str] = None
    
    # CORS: Whitelist of allowed origins
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    cors_allow_credentials: bool = False  # Set to False when allow_origins=["*"]
    cors_allow_methods: List[str] = ["GET", "POST"]
    cors_allow_headers: List[str] = ["Content-Type", "Authorization"]
    
    # ===== Qdrant Configuration =====
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    qdrant_api_key: str = "change-me-in-production"  # MUST change in production
    qdrant_collection_name: str = "products"
    qdrant_timeout: float = 60.0
    qdrant_verify_ssl: bool = True
    
    # ===== Redis Configuration =====
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: str = "change-me-in-production"  # MUST set password in production
    redis_url: str = ""
    redis_ssl: bool = False
    
    # ===== Model Configuration =====
    model_name: str = "openai/clip-vit-base-patch32"
    embedding_dim: int = 512
    top_k: int = 10
    
    # ===== Cache Configuration =====
    cache_ttl: int = 3600  # 1 hour
    cache_enabled: bool = True
    
    # ===== File Upload Security =====
    max_upload_size_mb: int = 50
    allowed_image_extensions: List[str] = ["jpg", "jpeg", "png", "webp", "gif"]
    image_mime_types: List[str] = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    
    # ===== URL Validation (SSRF Prevention) =====
    allow_image_urls: bool = True
    image_url_whitelist: Optional[List[str]] = None  # e.g., ["example.com", "cdn.example.com"]
    max_image_url_timeout: int = 10  # seconds
    
    # ===== Rate Limiting =====
    rate_limit_enabled: bool = True
    rate_limit_public_search: int = 100      # requests per minute
    rate_limit_auth_search: int = 1000       # requests per minute
    rate_limit_auth_upload: int = 50         # requests per minute
    rate_limit_window: int = 60              # seconds
    
    # ===== Logging =====
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # ===== Request Size Limits =====
    max_body_size: int = 52428800  # 50 MB in bytes
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        # Validate on assignment
        validate_assignment = True
    
    def __init__(self, **data):
        """Initialize settings and validate security requirements"""
        super().__init__(**data)
        
        # Validate production settings
        if self.environment == "production":
            self._validate_production_settings()
    
    def _validate_production_settings(self):
        """Validate security settings for production"""
        errors = []
        
        # Check debug mode
        if self.debug:
            errors.append("DEBUG mode must be False in production")
        
        # Check secret key
        if self.secret_key == "change-me-in-production-min-32-chars":
            errors.append("SECRET_KEY must be changed in production")
        if len(self.secret_key) < 32:
            errors.append("SECRET_KEY must be at least 32 characters")
        
        # Check API keys
        if self.api_key and self.api_key == "change-me-in-production":
            errors.append("API_KEY must be changed in production")
        
        # Check Qdrant API key
        if self.qdrant_api_key == "change-me-in-production":
            errors.append("QDRANT_API_KEY must be changed in production")
        
        # Check Redis password
        if not self.redis_password or self.redis_password == "change-me-in-production":
            errors.append("REDIS_PASSWORD must be set in production")
        
        # Check CORS origins
        if "*" in self.cors_origins:
            logger.warning("CORS allows all origins in production - consider restricting")
        
        # Check SSL
        if not self.qdrant_verify_ssl:
            errors.append("QDRANT_VERIFY_SSL should be True in production")
        
        if errors:
            error_msg = "Production security validation failed:\n" + "\n".join(
                f"  ❌ {error}" for error in errors
            )
            logger.error(error_msg)
            if self.environment == "production":
                raise ValueError(error_msg)
    
    @property
    def redis_url_safe(self) -> str:
        """Get Redis URL with credentials (use with care)"""
        if self.redis_url:
            return self.redis_url
        
        password_part = f":{self.redis_password}@" if self.redis_password else ""
        protocol = "rediss" if self.redis_ssl else "redis"
        return f"{protocol}://{password_part}{self.redis_host}:{self.redis_port}/0"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance - use dependency injection in FastAPI"""
    return Settings()
