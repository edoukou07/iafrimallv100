import logging
from functools import lru_cache
from app.config import get_settings
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService
from app.services.cache_service import CacheService
from app.services.search_service import SearchService

logger = logging.getLogger(__name__)

# Global instances
_embedding_service = None
_qdrant_service = None
_cache_service = None
_search_service = None

def initialize_services():
    """Initialize all services - DO NOT initialize embedding service at startup"""
    global _embedding_service, _qdrant_service, _cache_service, _search_service
    
    settings = get_settings()
    
    logger.info("Initializing services...")
    
    # DO NOT initialize embedding service here - it's lazy loaded
    # _embedding_service will be loaded on first use
    
    # DO NOT initialize Qdrant service at startup - use lazy loading
    # This prevents timeouts when Qdrant container is still starting
    _qdrant_service = None
    
    # Initialize cache service
    # Use redis_url if provided, otherwise use host:port
    if settings.redis_url:
        logger.info(f"Using Redis URL: {settings.redis_url[:30]}...")
        _cache_service = CacheService.from_url(
            url=settings.redis_url,
            ttl=settings.cache_ttl
        )
    else:
        _cache_service = CacheService(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password if settings.redis_password else None,
            ttl=settings.cache_ttl
        )
    
    # Initialize search service (will lazy-load embedding and qdrant services when needed)
    _search_service = SearchService(
        embedding_service=None,  # Will be loaded lazily
        qdrant_service=None,  # Will be loaded lazily
        cache_service=_cache_service,
        top_k=settings.top_k
    )
    
    logger.info("All services initialized successfully (embedding and Qdrant services will load on first use)")

def get_search_service() -> SearchService:
    """Get search service instance"""
    global _search_service
    
    if _search_service is None:
        initialize_services()
    
    return _search_service

def get_embedding_service() -> EmbeddingService:
    """Get embedding service instance - lazy loading on first use"""
    global _embedding_service
    
    if _embedding_service is None:
        logger.info("Loading CLIP embedding service on first use...")
        settings = get_settings()
        _embedding_service = EmbeddingService(model_name=settings.model_name)
        logger.info("CLIP embedding service loaded successfully")
    
    return _embedding_service

def get_qdrant_service() -> QdrantService:
    """Get Qdrant service instance - lazy loading on first use"""
    global _qdrant_service
    
    if _qdrant_service is None:
        logger.info("Loading Qdrant service on first use...")
        settings = get_settings()
        _qdrant_service = QdrantService(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            collection_name=settings.qdrant_collection_name,
            vector_size=settings.embedding_dim,
            api_key=settings.qdrant_api_key
        )
        logger.info("Qdrant service loaded successfully")
    
    return _qdrant_service

def get_cache_service() -> CacheService:
    """Get cache service instance"""
    global _cache_service
    
    if _cache_service is None:
        initialize_services()
    
    return _cache_service
