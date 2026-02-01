"""
Batch Qdrant Service - Named Vectors Support.

Handles Qdrant operations with named vectors:
- text_vector: 512d CLIP text embedding
- image_vector: 512d CLIP image embedding

This allows searching by text OR image and finding the same products.
"""

import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, 
    VectorParams, 
    PointStruct,
    NamedVector,
    VectorsConfig,
    SearchRequest,
    NamedSparseVector
)

logger = logging.getLogger(__name__)

# Vector dimensions
TEXT_VECTOR_DIM = 512
IMAGE_VECTOR_DIM = 512


class BatchQdrantService:
    """
    Qdrant service with named vectors support.
    
    Collection structure:
    - Vectors:
        - text_vector: 512d (CLIP text)
        - image_vector: 512d (CLIP image)
    - Payload: product metadata
    """
    
    _instance = None
    _client = None
    _collection_name = "products_v2"  # New collection with named vectors
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Qdrant client with named vectors collection."""
        try:
            qdrant_host = os.getenv("QDRANT_HOST", "20.238.104.13")
            qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
            
            logger.info(f"Initializing Qdrant (named vectors) at {qdrant_host}:{qdrant_port}")
            
            self._client = QdrantClient(
                host=qdrant_host,
                port=qdrant_port,
                prefer_grpc=False,
                https=False,
                timeout=30.0
            )
            
            self._ensure_collection_exists()
            logger.info(f"✅ Qdrant initialized with named vectors collection: {self._collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {e}")
            raise
    
    def _ensure_collection_exists(self):
        """Create collection with named vectors if not exists."""
        try:
            collections = self._client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self._collection_name not in collection_names:
                logger.info(f"Creating collection with named vectors: {self._collection_name}")
                
                # Create collection with named vectors
                self._client.create_collection(
                    collection_name=self._collection_name,
                    vectors_config={
                        "text_vector": VectorParams(
                            size=TEXT_VECTOR_DIM,
                            distance=Distance.COSINE
                        ),
                        "image_vector": VectorParams(
                            size=IMAGE_VECTOR_DIM,
                            distance=Distance.COSINE
                        )
                    }
                )
                
                logger.info(f"✓ Collection '{self._collection_name}' created with named vectors")
            else:
                logger.info(f"Collection '{self._collection_name}' already exists")
                
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise
    
    def index_product_with_named_vectors(
        self,
        product_id: str,
        text_vector: Optional[List[float]],
        image_vector: Optional[List[float]],
        payload: Dict[str, Any]
    ) -> bool:
        """
        Index a product with named vectors.
        
        Args:
            product_id: Unique product ID
            text_vector: 512d text embedding (or None)
            image_vector: 512d image embedding (or None)
            payload: Product metadata
            
        Returns:
            True if successful
        """
        try:
            # Generate Qdrant point ID
            qdrant_id = hash(product_id) % (2**63)
            
            # Build vectors dict (only include non-None vectors)
            vectors = {}
            if text_vector is not None and len(text_vector) == TEXT_VECTOR_DIM:
                vectors["text_vector"] = text_vector
            if image_vector is not None and len(image_vector) == IMAGE_VECTOR_DIM:
                vectors["image_vector"] = image_vector
            
            if not vectors:
                logger.error(f"Product {product_id}: No valid vectors to index")
                return False
            
            # Create point with named vectors
            point = PointStruct(
                id=qdrant_id,
                vector=vectors,
                payload={
                    "product_id": product_id,
                    **payload
                }
            )
            
            # Upsert to Qdrant
            self._client.upsert(
                collection_name=self._collection_name,
                points=[point]
            )
            
            logger.debug(
                f"Product {product_id} indexed with vectors: "
                f"text={'✓' if 'text_vector' in vectors else '✗'}, "
                f"image={'✓' if 'image_vector' in vectors else '✗'}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to index product {product_id}: {e}")
            return False
    
    def search_by_text(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = 0.3
    ) -> List[Dict]:
        """
        Search using text vector.
        
        Args:
            query_vector: 512d text query embedding
            limit: Max results
            score_threshold: Minimum similarity score
            
        Returns:
            List of search results
        """
        try:
            results = self._client.search(
                collection_name=self._collection_name,
                query_vector=NamedVector(
                    name="text_vector",
                    vector=query_vector
                ),
                limit=limit,
                score_threshold=score_threshold
            )
            
            return self._format_results(results)
            
        except Exception as e:
            logger.error(f"Text search failed: {e}")
            return []
    
    def search_by_image(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = 0.2
    ) -> List[Dict]:
        """
        Search using image vector.
        
        Args:
            query_vector: 512d image query embedding
            limit: Max results
            score_threshold: Minimum similarity score
            
        Returns:
            List of search results
        """
        try:
            results = self._client.search(
                collection_name=self._collection_name,
                query_vector=NamedVector(
                    name="image_vector",
                    vector=query_vector
                ),
                limit=limit,
                score_threshold=score_threshold
            )
            
            return self._format_results(results)
            
        except Exception as e:
            logger.error(f"Image search failed: {e}")
            return []
    
    def search_hybrid(
        self,
        text_vector: Optional[List[float]] = None,
        image_vector: Optional[List[float]] = None,
        limit: int = 10,
        text_weight: float = 0.5,
        image_weight: float = 0.5
    ) -> List[Dict]:
        """
        Hybrid search combining text and image vectors.
        
        Uses reciprocal rank fusion (RRF) to combine results.
        
        Args:
            text_vector: 512d text embedding (optional)
            image_vector: 512d image embedding (optional)
            limit: Max results
            text_weight: Weight for text results (0-1)
            image_weight: Weight for image results (0-1)
            
        Returns:
            List of fused search results
        """
        try:
            text_results = []
            image_results = []
            
            # Search with text vector
            if text_vector:
                text_results = self.search_by_text(text_vector, limit=limit * 2)
            
            # Search with image vector
            if image_vector:
                image_results = self.search_by_image(image_vector, limit=limit * 2)
            
            # Combine with weighted scores
            combined = {}
            
            for i, result in enumerate(text_results):
                product_id = result["id"]
                # RRF score
                rrf_score = text_weight / (i + 60)  # k=60 is common for RRF
                combined[product_id] = {
                    **result,
                    "score": rrf_score,
                    "text_score": result["score"],
                    "text_rank": i + 1
                }
            
            for i, result in enumerate(image_results):
                product_id = result["id"]
                rrf_score = image_weight / (i + 60)
                
                if product_id in combined:
                    combined[product_id]["score"] += rrf_score
                    combined[product_id]["image_score"] = result["score"]
                    combined[product_id]["image_rank"] = i + 1
                else:
                    combined[product_id] = {
                        **result,
                        "score": rrf_score,
                        "image_score": result["score"],
                        "image_rank": i + 1
                    }
            
            # Sort by combined score
            sorted_results = sorted(
                combined.values(),
                key=lambda x: x["score"],
                reverse=True
            )
            
            return sorted_results[:limit]
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []
    
    def _format_results(self, results) -> List[Dict]:
        """Format Qdrant results to standard format."""
        formatted = []
        for point in results:
            payload = point.payload
            formatted.append({
                "id": payload.get("product_id"),
                "score": point.score,
                "metadata": {
                    "title": payload.get("title"),
                    "description": payload.get("description"),
                    "price": payload.get("price"),
                    "sale_price": payload.get("sale_price"),
                    "currency": payload.get("currency"),
                    "category_name": payload.get("category_name"),
                    "provider_name": payload.get("provider_name"),
                    "image_url": payload.get("image_url"),
                    "tags": payload.get("tags", []),
                    "has_text_embedding": payload.get("has_text_embedding", False),
                    "has_image_embedding": payload.get("has_image_embedding", False)
                }
            })
        return formatted
    
    def get_collection_stats(self) -> Dict:
        """Get collection statistics."""
        try:
            info = self._client.get_collection(self._collection_name)
            return {
                "name": self._collection_name,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "vector_config": {
                    "text_vector": f"{TEXT_VECTOR_DIM}d CLIP",
                    "image_vector": f"{IMAGE_VECTOR_DIM}d CLIP"
                },
                "status": info.status
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}
    
    def health_check(self) -> bool:
        """Check Qdrant health."""
        try:
            self._client.get_collections()
            return True
        except:
            return False
    
    def delete_product(self, product_id: str) -> bool:
        """Delete a product from the collection."""
        try:
            qdrant_id = hash(product_id) % (2**63)
            self._client.delete(
                collection_name=self._collection_name,
                points_selector=[qdrant_id]
            )
            logger.info(f"Product {product_id} deleted")
            return True
        except Exception as e:
            logger.error(f"Failed to delete product {product_id}: {e}")
            return False
    
    def list_all_products(
        self,
        limit: int = 100,
        offset: Optional[int] = None
    ) -> Dict:
        """
        List all indexed products with pagination using scroll.
        
        Args:
            limit: Number of products to return per page
            offset: Offset point ID for pagination (None for first page)
            
        Returns:
            Dict with products list and next_offset for pagination
        """
        try:
            # Use scroll to retrieve all points
            points, next_offset = self._client.scroll(
                collection_name=self._collection_name,
                limit=limit,
                offset=offset,
                with_payload=True,
                with_vectors=False  # Don't return vectors to save bandwidth
            )
            
            products = []
            for point in points:
                payload = point.payload
                products.append({
                    "id": payload.get("product_id"),
                    "qdrant_id": point.id,
                    "title": payload.get("title"),
                    "description": payload.get("description"),
                    "short_description": payload.get("short_description"),
                    "price": payload.get("price"),
                    "sale_price": payload.get("sale_price"),
                    "currency": payload.get("currency", "XOF"),
                    "category_name": payload.get("category_name"),
                    "category_id": payload.get("category_id"),
                    "provider_name": payload.get("provider_name"),
                    "provider_id": payload.get("provider_id"),
                    "image_url": payload.get("image_url"),
                    "images": payload.get("images", []),
                    "tags": payload.get("tags", []),
                    "attributes": payload.get("attributes", {}),
                    "has_text_embedding": payload.get("has_text_embedding", False),
                    "has_image_embedding": payload.get("has_image_embedding", False),
                    "indexed_at": payload.get("indexed_at")
                })
            
            return {
                "products": products,
                "count": len(products),
                "next_offset": next_offset,
                "has_more": next_offset is not None
            }
            
        except Exception as e:
            logger.error(f"Failed to list products: {e}")
            return {
                "products": [],
                "count": 0,
                "next_offset": None,
                "has_more": False,
                "error": str(e)
            }
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """
        Get a single product by its ID.
        
        Args:
            product_id: The product ID
            
        Returns:
            Product dict or None if not found
        """
        try:
            # Search by product_id in payload using scroll with filter
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            points, _ = self._client.scroll(
                collection_name=self._collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="product_id",
                            match=MatchValue(value=product_id)
                        )
                    ]
                ),
                limit=1,
                with_payload=True,
                with_vectors=False
            )
            
            if not points:
                return None
            
            point = points[0]
            payload = point.payload
            
            return {
                "id": payload.get("product_id"),
                "qdrant_id": point.id,
                "title": payload.get("title"),
                "description": payload.get("description"),
                "short_description": payload.get("short_description"),
                "price": payload.get("price"),
                "sale_price": payload.get("sale_price"),
                "currency": payload.get("currency", "XOF"),
                "category_name": payload.get("category_name"),
                "category_id": payload.get("category_id"),
                "provider_name": payload.get("provider_name"),
                "provider_id": payload.get("provider_id"),
                "image_url": payload.get("image_url"),
                "images": payload.get("images", []),
                "tags": payload.get("tags", []),
                "attributes": payload.get("attributes", {}),
                "has_text_embedding": payload.get("has_text_embedding", False),
                "has_image_embedding": payload.get("has_image_embedding", False),
                "indexed_at": payload.get("indexed_at")
            }
            
        except Exception as e:
            logger.error(f"Failed to get product {product_id}: {e}")
            return None


# Singleton
_batch_qdrant_service: Optional[BatchQdrantService] = None


def get_batch_qdrant_service() -> BatchQdrantService:
    """Get singleton batch Qdrant service."""
    global _batch_qdrant_service
    if _batch_qdrant_service is None:
        _batch_qdrant_service = BatchQdrantService()
    return _batch_qdrant_service
