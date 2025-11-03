from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Environment
    environment: str = "development"
    debug: bool = True
    
    # API
    api_title: str = "Image Search API"
    api_version: str = "1.0.0"
    api_description: str = "CLIP-powered image search for e-commerce"
    
    # Qdrant
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    qdrant_api_key: str = "your-api-key-here"
    qdrant_collection_name: str = "products"
    
    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: str = ""
    
    # Model
    model_name: str = "openai/clip-vit-base-patch32"
    embedding_dim: int = 512
    top_k: int = 10
    
    # Cache
    cache_ttl: int = 3600
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()
