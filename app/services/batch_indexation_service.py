"""
Batch Indexation Service - Core processing logic.

Handles:
1. Processing batch of products from Django backend
2. Generating text embeddings (CLIP 512d)
3. Generating image embeddings (CLIP 512d) 
4. Storing in Qdrant with named vectors
5. Sending callback to Django backend

Named Vectors in Qdrant:
- "text_vector": 512d CLIP text embedding
- "image_vector": 512d CLIP image embedding
"""

import os
import logging
import asyncio
import httpx
import time
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime

from app.models.indexation_schemas import (
    ProductToIndex,
    BatchIndexationRequest,
    BatchIndexationCallback,
    ProductIndexResult
)

logger = logging.getLogger(__name__)


class BatchIndexationService:
    """
    Service for batch processing product indexation.
    
    Features:
    - Parallel embedding generation
    - Named vectors (text + image) in Qdrant
    - Automatic callback to Django backend
    - Error handling per product
    """
    
    def __init__(self):
        self._embedding_service = None
        self._image_service = None
        self._qdrant_service = None
        self._http_client = None
        
    def _get_embedding_service(self):
        """Lazy load embedding service"""
        if self._embedding_service is None:
            from app.services.embedding_service import EmbeddingService
            self._embedding_service = EmbeddingService()
        return self._embedding_service
    
    def _get_image_service(self):
        """Lazy load image embedding service"""
        if self._image_service is None:
            from app.services.image_embedding import get_image_embedding_service
            self._image_service = get_image_embedding_service()
        return self._image_service
    
    def _get_qdrant_service(self):
        """Lazy load Qdrant service"""
        if self._qdrant_service is None:
            from app.services.batch_qdrant_service import get_batch_qdrant_service
            self._qdrant_service = get_batch_qdrant_service()
        return self._qdrant_service
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client
    
    def _generate_text_embedding(self, product: ProductToIndex) -> Optional[List[float]]:
        """
        Generate CLIP text embedding for product.
        
        Args:
            product: Product with text fields
            
        Returns:
            512-dimensional embedding or None if failed
        """
        try:
            text = product.get_text_for_embedding()
            if not text or len(text.strip()) < 10:
                logger.warning(f"Product {product.id}: Text too short for embedding")
                return None
            
            embedding_service = self._get_embedding_service()
            embedding = embedding_service.embed_text(text)
            
            if embedding and len(embedding) == 512:
                logger.debug(f"Product {product.id}: Text embedding generated (512d)")
                return embedding
            else:
                logger.warning(f"Product {product.id}: Invalid text embedding dimension")
                return None
                
        except Exception as e:
            logger.error(f"Product {product.id}: Text embedding error: {e}")
            return None
    
    async def _download_image(self, url: str) -> Optional[bytes]:
        """Download image from URL"""
        try:
            client = await self._get_http_client()
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.warning(f"Failed to download image {url}: {e}")
            return None
    
    async def _generate_image_embedding(self, product: ProductToIndex) -> Optional[List[float]]:
        """
        Generate CLIP image embedding for product.
        
        Args:
            product: Product with images
            
        Returns:
            512-dimensional embedding or None if failed
        """
        try:
            image_url = product.get_primary_image_url()
            if not image_url:
                logger.debug(f"Product {product.id}: No image available")
                return None
            
            # Download image
            image_data = await self._download_image(image_url)
            if not image_data:
                logger.warning(f"Product {product.id}: Could not download image")
                return None
            
            # Generate embedding
            image_service = self._get_image_service()
            embedding = image_service.embed_image(image_data)
            
            if embedding and len(embedding) == 512:
                logger.debug(f"Product {product.id}: Image embedding generated (512d)")
                return embedding
            else:
                logger.warning(f"Product {product.id}: Invalid image embedding dimension")
                return None
                
        except Exception as e:
            logger.error(f"Product {product.id}: Image embedding error: {e}")
            return None
    
    async def _process_single_product(self, product: ProductToIndex) -> ProductIndexResult:
        """
        Process a single product: generate embeddings and index in Qdrant.
        
        Args:
            product: Product to process
            
        Returns:
            ProductIndexResult with success/failure info
        """
        text_embedding = None
        image_embedding = None
        error_message = None
        
        try:
            # Generate text embedding (sync - CLIP is CPU-bound)
            text_embedding = self._generate_text_embedding(product)
            
            # Generate image embedding (async - involves HTTP download)
            image_embedding = await self._generate_image_embedding(product)
            
            # Need at least one embedding
            if not text_embedding and not image_embedding:
                return ProductIndexResult(
                    id=product.id,
                    isIndexed=False,
                    errorMessage="Could not generate any embedding (text or image)"
                )
            
            # Build payload for Qdrant
            payload = {
                "product_id": product.id,
                "title": product.title,
                "slug": product.slug,
                "description": product.description,
                "short_description": product.shortDescription,
                "price": product.price,
                "sale_price": product.salePrice,
                "currency": product.currency,
                "category_id": product.category.id if product.category else None,
                "category_name": product.category.name if product.category else None,
                "category_slug": product.category.slug if product.category else None,
                "provider_id": product.provider.id if product.provider else None,
                "provider_name": product.provider.storeName if product.provider else None,
                "tags": product.tags,
                "attributes": [{"name": a.name, "value": a.value} for a in product.attributes],
                "seo_keywords": product.seoKeywords,
                "image_url": product.get_primary_image_url(),
                "has_text_embedding": text_embedding is not None,
                "has_image_embedding": image_embedding is not None,
                "indexed_at": datetime.now().isoformat(),
                "metadata": product.metadata
            }
            
            # Index in Qdrant with named vectors
            qdrant_service = self._get_qdrant_service()
            success = qdrant_service.index_product_with_named_vectors(
                product_id=product.id,
                text_vector=text_embedding,
                image_vector=image_embedding,
                payload=payload
            )
            
            if success:
                logger.info(f"✓ Product {product.id} indexed successfully")
                return ProductIndexResult(
                    id=product.id,
                    isIndexed=True
                )
            else:
                return ProductIndexResult(
                    id=product.id,
                    isIndexed=False,
                    errorMessage="Qdrant indexing failed"
                )
                
        except Exception as e:
            logger.error(f"✗ Product {product.id}: Processing error: {e}")
            return ProductIndexResult(
                id=product.id,
                isIndexed=False,
                errorMessage=str(e)
            )
    
    async def process_batch(self, request: BatchIndexationRequest) -> BatchIndexationCallback:
        """
        Process a batch of products.
        
        Args:
            request: BatchIndexationRequest with products list
            
        Returns:
            BatchIndexationCallback with results
        """
        start_time = time.time()
        logger.info(f"🚀 Starting batch {request.batchId} with {len(request.products)} products")
        
        results: List[ProductIndexResult] = []
        
        # Process products with limited concurrency
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent products
        
        async def process_with_semaphore(product: ProductToIndex) -> ProductIndexResult:
            async with semaphore:
                return await self._process_single_product(product)
        
        # Process all products concurrently (with limit)
        tasks = [process_with_semaphore(p) for p in request.products]
        results = await asyncio.gather(*tasks)
        
        # Calculate stats
        success_count = sum(1 for r in results if r.isIndexed)
        failure_count = len(results) - success_count
        processing_time_ms = (time.time() - start_time) * 1000
        
        callback = BatchIndexationCallback(
            batchId=request.batchId,
            results=results
        )
        
        logger.info(
            f"✅ Batch {request.batchId} completed: "
            f"{success_count}/{len(results)} success, "
            f"{processing_time_ms:.0f}ms"
        )
        
        return callback
    
    async def send_callback(self, callback_url: str, callback: BatchIndexationCallback) -> bool:
        """
        Send callback to Django backend.
        
        Args:
            callback_url: URL to POST callback to
            callback: Callback payload
            
        Returns:
            True if successful
        """
        try:
            client = await self._get_http_client()
            
            # Get API key from environment
            api_key = os.getenv("AI_INDEXATION_API_KEY", "")
            
            headers = {
                "Content-Type": "application/json"
            }
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            # Build callback payload (exclude None errorMessage)
            callback_data = {
                "batchId": callback.batchId,
                "results": []
            }
            for result in callback.results:
                result_dict = {"id": result.id, "isIndexed": result.isIndexed}
                if result.errorMessage is not None:
                    result_dict["errorMessage"] = result.errorMessage
                callback_data["results"].append(result_dict)
            
            response = await client.post(
                callback_url,
                json=callback_data,
                headers=headers
            )
            response.raise_for_status()
            
            logger.info(f"✓ Callback sent to {callback_url}: {response.status_code}")
            return True
            
        except Exception as e:
            logger.error(f"✗ Callback failed to {callback_url}: {e}")
            return False
    
    async def close(self):
        """Cleanup resources"""
        if self._http_client:
            await self._http_client.aclose()


# Singleton instance
_batch_service: Optional[BatchIndexationService] = None


def get_batch_indexation_service() -> BatchIndexationService:
    """Get singleton batch indexation service"""
    global _batch_service
    if _batch_service is None:
        _batch_service = BatchIndexationService()
    return _batch_service
