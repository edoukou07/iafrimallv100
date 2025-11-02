import logging
import time
from typing import List, Dict, Any, Optional
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService
from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)

class SearchService:
    """Main search service orchestrating embedding, vectordb, and caching"""
    
    def __init__(self, embedding_service: EmbeddingService, 
                 qdrant_service: QdrantService, 
                 cache_service: CacheService,
                 top_k: int = 10):
        self.embedding_service = embedding_service
        self.qdrant_service = qdrant_service
        self.cache_service = cache_service
        self.top_k = top_k
    
    def search_by_image_url(self, image_url: str, top_k: Optional[int] = None,
                           category_filter: Optional[str] = None,
                           price_min: Optional[float] = None,
                           price_max: Optional[float] = None) -> Dict[str, Any]:
        """Search for similar products by image URL"""
        start_time = time.time()
        top_k = top_k or self.top_k
        
        # Check cache
        cache_key = self.cache_service._generate_key("image_search", image_url)
        cached_result = self.cache_service.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            # Generate embedding
            logger.info(f"Generating embedding for image URL: {image_url}")
            embedding = self.embedding_service.embed_image_from_url(image_url)
            
            # Search in Qdrant
            logger.info(f"Searching for similar products in Qdrant")
            search_results = self.qdrant_service.search(embedding, top_k=top_k)
            
            # Filter results
            results = self._filter_and_format_results(
                search_results, 
                category_filter, 
                price_min, 
                price_max
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            response = {
                "query_type": "image",
                "top_k": top_k,
                "total_results": len(results),
                "results": results,
                "execution_time_ms": execution_time
            }
            
            # Cache result
            self.cache_service.set(cache_key, response)
            
            return response
        except Exception as e:
            logger.error(f"Error searching by image: {e}")
            raise
    
    def search_by_text(self, text_query: str, top_k: Optional[int] = None,
                      category_filter: Optional[str] = None,
                      price_min: Optional[float] = None,
                      price_max: Optional[float] = None) -> Dict[str, Any]:
        """Search for similar products by text query"""
        start_time = time.time()
        top_k = top_k or self.top_k
        
        # Check cache
        cache_key = self.cache_service._generate_key("text_search", text_query)
        cached_result = self.cache_service.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            # Generate embedding
            logger.info(f"Generating embedding for text: {text_query}")
            embedding = self.embedding_service.embed_text(text_query)
            
            # Search in Qdrant
            logger.info(f"Searching for similar products in Qdrant")
            search_results = self.qdrant_service.search(embedding, top_k=top_k)
            
            # Filter results
            results = self._filter_and_format_results(
                search_results, 
                category_filter, 
                price_min, 
                price_max
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            response = {
                "query_type": "text",
                "top_k": top_k,
                "total_results": len(results),
                "results": results,
                "execution_time_ms": execution_time
            }
            
            # Cache result
            self.cache_service.set(cache_key, response)
            
            return response
        except Exception as e:
            logger.error(f"Error searching by text: {e}")
            raise
    
    def _filter_and_format_results(self, search_results: List[Dict[str, Any]],
                                   category_filter: Optional[str] = None,
                                   price_min: Optional[float] = None,
                                   price_max: Optional[float] = None) -> List[Dict[str, Any]]:
        """Filter and format search results"""
        formatted_results = []
        
        for result in search_results:
            payload = result["payload"]
            
            # Apply category filter
            if category_filter and payload.get("category") != category_filter:
                continue
            
            # Apply price filters
            price = payload.get("price", 0)
            if price_min is not None and price < price_min:
                continue
            if price_max is not None and price > price_max:
                continue
            
            formatted_results.append({
                "product_id": payload.get("product_id"),
                "name": payload.get("name"),
                "description": payload.get("description"),
                "image_url": payload.get("image_url"),
                "price": payload.get("price"),
                "category": payload.get("category"),
                "similarity_score": result["score"]
            })
        
        return formatted_results
    
    def index_product(self, product_id: str, name: str, description: str,
                     image_url: str, category: str, price: float,
                     attributes: Optional[Dict[str, Any]] = None) -> bool:
        """Index a product with its embedding"""
        try:
            logger.info(f"Indexing product: {product_id}")
            
            # Generate embedding from image
            embedding = self.embedding_service.embed_image_from_url(image_url)
            
            # Upsert to Qdrant
            metadata = {
                "name": name,
                "description": description,
                "image_url": image_url,
                "category": category,
                "price": price,
                "attributes": attributes or {}
            }
            
            self.qdrant_service.upsert_product(product_id, embedding, metadata)
            
            logger.info(f"Product {product_id} indexed successfully")
            return True
        except Exception as e:
            logger.error(f"Error indexing product {product_id}: {e}")
            raise
    
    def index_batch(self, products: List[Dict[str, Any]]) -> int:
        """Batch index products"""
        try:
            logger.info(f"Batch indexing {len(products)} products")
            
            for product in products:
                # Generate embedding for each product
                embedding = self.embedding_service.embed_image_from_url(product["image_url"])
                product["embedding"] = embedding
            
            # Batch upsert
            self.qdrant_service.upsert_batch(products)
            
            logger.info(f"Successfully indexed {len(products)} products")
            return len(products)
        except Exception as e:
            logger.error(f"Error batch indexing: {e}")
            raise
