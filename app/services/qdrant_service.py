import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, Range

logger = logging.getLogger(__name__)

class QdrantService:
    """Service for Qdrant vector database operations"""
    
    def __init__(self, host: str, port: int, collection_name: str, vector_size: int, api_key: Optional[str] = None):
        """Initialize Qdrant client"""
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.client = None
        self._initialized = False
        
        logger.info(f"Connecting to Qdrant at {host}:{port}")
        
        try:
            self.client = QdrantClient(host=host, port=port, api_key=api_key, timeout=5.0)
            self._initialize_collection()
            self._initialized = True
            logger.info(f"Connected to Qdrant successfully")
        except Exception as e:
            logger.warning(f"Could not connect to Qdrant at startup: {e}. Will retry on first request.")
            # Don't raise - allow app to start, will retry on first request
    
    def _ensure_connected(self):
        """Ensure connection to Qdrant (retry logic)"""
        if self._initialized:
            return
        
        try:
            self.client = QdrantClient(host=self.host, port=self.port, timeout=5.0)
            self._initialize_collection()
            self._initialized = True
            logger.info(f"Successfully connected to Qdrant")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise
    
    def _initialize_collection(self):
        """Initialize collection if it doesn't exist"""
        if not self.client:
            raise Exception("Qdrant client not initialized")
        
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
                )
                logger.info(f"Collection {self.collection_name} created successfully")
            else:
                logger.info(f"Collection {self.collection_name} already exists")
        except Exception as e:
            logger.error(f"Error initializing collection: {e}")
            raise
    
    def upsert_product(self, product_id: str, embedding: List[float], metadata: Dict[str, Any]):
        """Upsert product with embedding and metadata"""
        try:
            point = PointStruct(
                id=hash(product_id) % (10 ** 8),  # Convert ID to positive integer
                vector=embedding,
                payload={
                    "product_id": product_id,
                    **metadata
                }
            )
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            logger.info(f"Product {product_id} upserted to Qdrant")
        except Exception as e:
            logger.error(f"Error upserting product {product_id}: {e}")
            raise
    
    def upsert_batch(self, products: List[Dict[str, Any]]):
        """Batch upsert products"""
        try:
            points = []
            for product in products:
                point = PointStruct(
                    id=hash(product["product_id"]) % (10 ** 8),
                    vector=product["embedding"],
                    payload={
                        "product_id": product["product_id"],
                        "name": product.get("name", ""),
                        "description": product.get("description", ""),
                        "image_url": product.get("image_url", ""),
                        "category": product.get("category", ""),
                        "price": product.get("price", 0),
                        "attributes": product.get("attributes", {}),
                    }
                )
                points.append(point)
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Batch upserted {len(products)} products")
        except Exception as e:
            logger.error(f"Error in batch upsert: {e}")
            raise
    
    def search(self, embedding: List[float], top_k: int = 10, 
               filters: Optional[Filter] = None) -> List[Dict[str, Any]]:
        """Search for similar products"""
        self._ensure_connected()
        
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=embedding,
                query_filter=filters,
                limit=top_k,
                with_payload=True
            )
            
            search_results = []
            for result in results:
                search_results.append({
                    "score": result.score,
                    "payload": result.payload
                })
            
            logger.info(f"Search completed, found {len(search_results)} results")
            return search_results
        except Exception as e:
            logger.error(f"Error searching: {e}")
            raise
    
    def delete_product(self, product_id: str):
        """Delete product from collection"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[hash(product_id) % (10 ** 8)]
            )
            logger.info(f"Product {product_id} deleted from Qdrant")
        except Exception as e:
            logger.error(f"Error deleting product {product_id}: {e}")
            raise
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": info.config.collection_name,
                "vectors_count": info.points_count,
                "vector_size": self.vector_size,
                "distance": "cosine"
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            raise
    
    def health_check(self) -> bool:
        """Check if Qdrant is healthy"""
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False
