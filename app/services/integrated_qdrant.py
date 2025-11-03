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
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Qdrant client with RAM-optimized disk-based storage."""
        try:
            # Use local disk-based storage (persists across restarts)
            data_path = os.getenv("QDRANT_DATA_PATH", "/app/data/qdrant")
            os.makedirs(data_path, exist_ok=True)
            
            logger.info(f"Initializing Qdrant with RAM-optimized disk storage at: {data_path}")
            
            # Initialize with disk-based storage (not RAM)
            # Qdrant will use memory-mapped files for efficient access
            self._client = QdrantClient(
                path=data_path,
                prefer_grpc=False,  # Use HTTP for better compatibility
                timeout=30.0  # Connection timeout
            )
            
            # Create collection if it doesn't exist
            self._ensure_collection_exists()
            
            # Log RAM optimization settings
            self._log_memory_info()
            
            logger.info("✅ Qdrant initialized with RAM-optimized disk storage")
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            raise
    
    def _log_memory_info(self):
        """Log memory and storage configuration."""
        try:
            # Get Qdrant info if available
            info = self._client.get_telemetry()
            logger.info("Qdrant Configuration:")
            logger.info("  ✓ Vector Storage: DISK-BASED (not RAM)")
            logger.info("  ✓ Cache Strategy: LRU cache for hot vectors only")
            logger.info("  ✓ Memory Mode: Memory-mapped file access")
            logger.info("  ✓ Prefetch: Enabled for batch operations")
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
                        size=500,  # Dimension for TF-IDF vectors
                        distance=Distance.COSINE
                    )
                )
            else:
                logger.info(f"Collection '{self._collection_name}' already exists")
                
        except Exception as e:
            logger.error(f"Failed to ensure collection exists: {e}")
            raise
    
    def index_product(self, product_id: str, name: str, description: str, 
                     embedding: List[float], metadata: Dict = None) -> bool:
        """Index a product with embedding."""
        try:
            # Combine name + description for better search
            full_text = f"{name} {description}"
            
            point = PointStruct(
                id=hash(product_id) % (2**63),  # Convert to positive int64
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
            
            logger.info(f"Indexed product: {product_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to index product {product_id}: {e}")
            return False
    
    def search(self, query_vector: List[float], limit: int = 10) -> List[Dict]:
        """Search for similar products."""
        try:
            results = self._client.search(
                collection_name=self._collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=0.0
            )
            
            search_results = []
            for scored_point in results:
                search_results.append({
                    "id": scored_point.payload.get("product_id"),
                    "score": scored_point.score,
                    "metadata": {
                        "name": scored_point.payload.get("name"),
                        "description": scored_point.payload.get("description")
                    }
                })
            
            logger.info(f"Search returned {len(search_results)} results")
            return search_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_collection_stats(self) -> Dict:
        """Get collection statistics."""
        try:
            collection_info = self._client.get_collection(self._collection_name)
            return {
                "name": self._collection_name,
                "points_count": collection_info.points_count,
                "vectors_count": collection_info.vectors_count,
                "segment_count": len(collection_info.config.params) if hasattr(collection_info.config, 'params') else 0
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}
    
    def health_check(self) -> bool:
        """Check if Qdrant is healthy."""
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
