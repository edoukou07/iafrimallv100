"""
Indexation Routes - Receives batch indexation requests from Django backend.

Endpoints:
- POST /indexation/products - Receive batch of products to index
- GET /indexation/health - Check indexation service health
- GET /indexation/stats - Get indexation statistics
"""

import os
import logging
import asyncio
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, BackgroundTasks, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models.indexation_schemas import (
    BatchIndexationRequest,
    BatchIndexationResponse,
    BatchIndexationCallback
)
from app.services.batch_indexation_service import get_batch_indexation_service
from app.services.batch_qdrant_service import get_batch_qdrant_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/indexation", tags=["Indexation"])

# Security (optional API key validation)
security = HTTPBearer(auto_error=False)


def verify_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> bool:
    """
    Verify API key from Authorization header.
    If AI_INDEXATION_API_KEY is not set, authentication is skipped.
    """
    expected_key = os.getenv("AI_INDEXATION_API_KEY", "")
    
    # If no API key configured, skip auth
    if not expected_key:
        return True
    
    # Check credentials
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    if credentials.credentials != expected_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    return True


async def process_batch_background(
    request: BatchIndexationRequest,
    callback_url: str
):
    """
    Background task to process batch and send callback.
    
    This runs asynchronously after the API returns 202 Accepted.
    """
    try:
        service = get_batch_indexation_service()
        
        # Process all products
        callback = await service.process_batch(request)
        
        # Send callback to Django backend
        await service.send_callback(callback_url, callback)
        
    except Exception as e:
        logger.error(f"Background batch processing failed: {e}")
        
        # Try to send error callback
        try:
            error_callback = BatchIndexationCallback(
                batchId=request.batchId,
                results=[],
                totalProcessed=0,
                successCount=0,
                failureCount=len(request.products),
                processingTimeMs=0
            )
            service = get_batch_indexation_service()
            await service.send_callback(callback_url, error_callback)
        except:
            pass


@router.post(
    "/products",
    response_model=BatchIndexationResponse,
    status_code=202,
    summary="Index batch of products",
    description="""
    Receive a batch of products from Django backend for AI indexation.
    
    **Flow:**
    1. Django backend sends batch of products (max 500)
    2. API validates and accepts request (returns 202 immediately)
    3. Background worker processes each product:
       - Generate CLIP text embedding (512d)
       - Download and generate CLIP image embedding (512d)
       - Store in Qdrant with named vectors
    4. Send callback to Django with results
    
    **Named Vectors:**
    - `text_vector`: Based on title, description, tags, attributes
    - `image_vector`: Based on primary product image
    
    **Callback:**
    Results are sent to `callbackUrl` with success/failure per product.
    """
)
async def index_products_batch(
    request: BatchIndexationRequest,
    background_tasks: BackgroundTasks,
    authorized: bool = Depends(verify_api_key)
):
    """
    Index a batch of products from Django backend.
    
    Processing happens asynchronously - returns immediately with 202 Accepted.
    Results are sent via callback to the provided URL.
    """
    try:
        # Validate request
        if not request.products:
            raise HTTPException(status_code=400, detail="No products provided")
        
        if len(request.products) > 500:
            raise HTTPException(
                status_code=400, 
                detail=f"Batch too large: {len(request.products)} products (max 500)"
            )
        
        if not request.callbackUrl:
            raise HTTPException(status_code=400, detail="callbackUrl is required")
        
        if not request.batchId:
            raise HTTPException(status_code=400, detail="batchId is required")
        
        logger.info(
            f"📦 Received batch {request.batchId}: "
            f"{len(request.products)} products, "
            f"callback: {request.callbackUrl}"
        )
        
        # Estimate processing time (~2-5 seconds per product)
        estimated_time = len(request.products) * 3
        
        # Start background processing
        background_tasks.add_task(
            process_batch_background,
            request,
            request.callbackUrl
        )
        
        return BatchIndexationResponse(
            status="accepted",
            batchId=request.batchId,
            productsReceived=len(request.products),
            message=f"Batch {request.batchId} accepted for processing. Results will be sent to callback URL.",
            estimatedTimeSeconds=estimated_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing batch request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/products/sync",
    response_model=BatchIndexationCallback,
    summary="Index batch synchronously (for testing)",
    description="Process batch synchronously and return results directly. Use for testing only."
)
async def index_products_sync(
    request: BatchIndexationRequest,
    authorized: bool = Depends(verify_api_key)
):
    """
    Index products synchronously (blocking).
    
    Use this for testing - production should use async endpoint.
    """
    try:
        if len(request.products) > 50:
            raise HTTPException(
                status_code=400,
                detail="Sync endpoint limited to 50 products. Use /products for larger batches."
            )
        
        service = get_batch_indexation_service()
        callback = await service.process_batch(request)
        
        return callback
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sync indexation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/health",
    summary="Indexation service health",
    description="Check health of indexation service and Qdrant connection."
)
async def indexation_health():
    """Check indexation service health."""
    try:
        qdrant = get_batch_qdrant_service()
        qdrant_ok = qdrant.health_check()
        
        return {
            "status": "healthy" if qdrant_ok else "degraded",
            "service": "Batch Indexation Service",
            "qdrant": {
                "connected": qdrant_ok,
                "collection": "products_v2"
            },
            "vectors": {
                "text_vector": "512d CLIP",
                "image_vector": "512d CLIP"
            }
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get(
    "/stats",
    summary="Indexation statistics",
    description="Get statistics about indexed products."
)
async def indexation_stats():
    """Get indexation statistics."""
    try:
        qdrant = get_batch_qdrant_service()
        stats = qdrant.get_collection_stats()
        
        return {
            "collection": stats,
            "service": "Batch Indexation Service",
            "embedding_config": {
                "text_model": "CLIP (openai/clip-vit-base-patch32)",
                "text_dimension": 512,
                "image_model": "CLIP (openai/clip-vit-base-patch32)",
                "image_dimension": 512
            }
        }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/products/{product_id}",
    summary="Delete product from index",
    description="Remove a product from the vector index."
)
async def delete_product(
    product_id: str,
    authorized: bool = Depends(verify_api_key)
):
    """Delete a product from the index."""
    try:
        qdrant = get_batch_qdrant_service()
        success = qdrant.delete_product(product_id)
        
        if success:
            return {"status": "deleted", "product_id": product_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete product")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/products",
    summary="List all indexed products",
    description="Retrieve all products indexed in Qdrant with pagination."
)
async def list_products(
    limit: int = 50,
    offset: int = None
):
    """
    List all indexed products with their metadata.
    
    Use offset from response to get next page.
    """
    try:
        qdrant = get_batch_qdrant_service()
        result = qdrant.list_all_products(limit=limit, offset=offset)
        
        return {
            "status": "success",
            "data": result["products"],
            "count": result["count"],
            "next_offset": result["next_offset"],
            "has_more": result["has_more"]
        }
        
    except Exception as e:
        logger.error(f"List products error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/products/{product_id}",
    summary="Get product by ID",
    description="Retrieve a single indexed product by its ID."
)
async def get_product(product_id: str):
    """Get a single product from the index."""
    try:
        qdrant = get_batch_qdrant_service()
        product = qdrant.get_product_by_id(product_id)
        
        if product:
            return {"status": "success", "data": product}
        else:
            raise HTTPException(status_code=404, detail="Product not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get product error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
