"""
Integrated Qdrant service - runs in-memory or in-process.
No need for separate Qdrant container/service.
Uses local storage directory for persistence.
"""
import os
import logging
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import json

logger = logging.getLogger(__name__)

class IntegratedQdrantService:
    """Qdrant service running in the same container."""
    
    _instance = None
    _client = None
    _collection_name = "products"
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Lazy initialization - don't connect until first use."""
        pass  # Don't connect at startup
    
    def _ensure_initialized(self):
        """Initialize client on first use (lazy loading)."""
        if self._initialized:
            return
        
        self._initialized = True
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Qdrant client connecting to remote server."""
        try:
            # Connect to remote Qdrant server instead of local storage
            qdrant_host = os.getenv("QDRANT_HOST", "qdrant")  # Default to docker service name
            qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
            
            logger.info(f"Initializing Qdrant connecting to remote server: {qdrant_host}:{qdrant_port}")
            
            # Initialize with remote server connection
            self._client = QdrantClient(
                host=qdrant_host,
                port=qdrant_port,
                prefer_grpc=False,  # Use HTTP for better compatibility
                https=False,
                timeout=60.0  # Increased timeout to 60 seconds
            )
            
            # Create collection if it doesn't exist
            self._ensure_collection_exists()
            
            # Log configuration
            self._log_memory_info()
            
            logger.info(f"✅ Qdrant initialized, connected to remote server at {qdrant_host}:{qdrant_port}")
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            raise
    
    def _log_memory_info(self):
        """Log memory and storage configuration."""
        try:
            # Get Qdrant info if available
            info = self._client.get_telemetry()
            logger.info("Qdrant Configuration:")
            logger.info("  ✓ Storage: Remote Qdrant Server")
            logger.info("  ✓ Communication: HTTP")
            logger.info("  ✓ Distance Metric: COSINE")
        except Exception as e:
            logger.warning(f"Could not retrieve telemetry: {e}")
    
    def _ensure_collection_exists(self):
        """Create collection if it doesn't exist."""
        try:
            collections = self._client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self._collection_name not in collection_names:
                logger.info(f"Creating collection: {self._collection_name}")
                self._client.create_collection(
                    collection_name=self._collection_name,
                    vectors_config=VectorParams(
                        size=512,  # CLIP vector dimension (openai/clip-vit-base-patch32)
                        distance=Distance.COSINE
                    )
                )
            else:
                logger.info(f"Collection '{self._collection_name}' already exists")
                
        except Exception as e:
            logger.error(f"Failed to ensure collection exists: {e}")
            raise
    
    def index_product(self, product_id: str, name: str, description: str, 
                     embedding: List[float], metadata: Dict = None) -> tuple:
        """Index a product with embedding. Returns (success: bool, qdrant_id: int or None)"""
        self._ensure_initialized()  # Lazy init
        try:
            # Combine name + description for better search
            full_text = f"{name} {description}"
            
            # Generate the Qdrant ID (same as what would be stored)
            qdrant_id = hash(product_id) % (2**63)  # Convert to positive int64
            
            point = PointStruct(
                id=qdrant_id,
                vector=embedding,
                payload={
                    "product_id": product_id,
                    "name": name,
                    "description": description,
                    "full_text": full_text,
                    **(metadata or {})
                }
            )
            
            self._client.upsert(
                collection_name=self._collection_name,
                points=[point]
            )
            
            logger.info(f"Indexed product: {product_id} with Qdrant ID: {qdrant_id}")
            return True, qdrant_id
            
        except Exception as e:
            logger.error(f"Failed to index product {product_id}: {e}")
            return False, None
    
    def search(self, query_vector: List[float], limit: int = 10, 
               score_threshold: float = 0.3, 
               category_filter: str = None, 
               min_score: float = None) -> List[Dict]:
        """
        Search for similar products with intelligent filtering.
        
        Args:
            query_vector: Query embedding vector
            limit: Max number of results to return
            score_threshold: Minimum similarity score (0.0-1.0, default 0.3 for better precision)
            category_filter: Optional category filter
            min_score: Alias for score_threshold (for backward compatibility)
        
        Returns:
            List of search results sorted by score
        """
        self._ensure_initialized()  # Lazy init
        
        try:
            # Use min_score if provided (backward compatibility)
            if min_score is not None:
                score_threshold = min_score
            
            # Fetch more results than limit to allow filtering
            fetch_limit = max(limit * 2, 50)
            
            results = self._client.search(
                collection_name=self._collection_name,
                query_vector=query_vector,
                limit=fetch_limit,
                score_threshold=score_threshold  # Intelligent threshold
            )
            
            search_results = []
            for scored_point in results:
                payload = scored_point.payload
                
                # Apply category filter if provided
                if category_filter:
                    product_category = payload.get("category", "").lower()
                    if category_filter.lower() not in product_category:
                        continue
                
                search_results.append({
                    "id": payload.get("product_id"),
                    "score": scored_point.score,
                    "metadata": {
                        "name": payload.get("name"),
                        "description": payload.get("description"),
                        "image_url": payload.get("image_url"),
                        "price": payload.get("price"),
                        "category": payload.get("category"),
                        "url": payload.get("url")
                    }
                })
                
                # Stop once we have enough results
                if len(search_results) >= limit:
                    break
            
            logger.info(f"Search returned {len(search_results)} results (threshold={score_threshold})")
            return search_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_collection_stats(self) -> Dict:
        """Get collection statistics."""
        self._ensure_initialized()  # Lazy init
        try:
            collection_info = self._client.get_collection(self._collection_name)
            return {
                "name": self._collection_name,
                "points_count": collection_info.points_count,
                "vectors_count": collection_info.vectors_count,
                "segment_count": getattr(collection_info, 'segments_count', 0)
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}
    
    def health_check(self) -> bool:
        """Check if Qdrant is healthy."""
        self._ensure_initialized()  # Lazy init
        try:
            self._client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False
    
    def clear_collection(self) -> bool:
        """Clear all data in collection (for testing)."""
        try:
            self._client.delete_collection(self._collection_name)
            self._ensure_collection_exists()
            logger.info("Collection cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            return False


# Singleton instance
_qdrant_service = None

def get_qdrant_service() -> IntegratedQdrantService:
    """Get singleton Qdrant service."""
    global _qdrant_service
    if _qdrant_service is None:
        _qdrant_service = IntegratedQdrantService()
    return _qdrant_service
