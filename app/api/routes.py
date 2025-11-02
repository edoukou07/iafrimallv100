import logging
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from typing import Optional
from app.models.schemas import (
    SearchRequest, SearchResponse, IndexProductRequest,
    HealthResponse
)
from app.dependencies import get_search_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["search"])

@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest, search_service = None):
    """
    Search for similar products by image URL or text query
    
    - **image_url**: URL of the product image to search
    - **text_query**: Text description to search (alternative to image_url)
    - **top_k**: Number of results to return (1-100)
    - **category_filter**: Optional category to filter results
    - **price_min**: Minimum price filter
    - **price_max**: Maximum price filter
    """
    try:
        if not request.image_url and not request.text_query:
            raise HTTPException(
                status_code=400,
                detail="Either image_url or text_query must be provided"
            )
        
        if request.image_url and request.text_query:
            raise HTTPException(
                status_code=400,
                detail="Provide either image_url or text_query, not both"
            )
        
        search_service = get_search_service()
        
        if request.image_url:
            result = search_service.search_by_image_url(
                image_url=request.image_url,
                top_k=request.top_k,
                category_filter=request.category_filter,
                price_min=request.price_min,
                price_max=request.price_max
            )
        else:
            result = search_service.search_by_text(
                text_query=request.text_query,
                top_k=request.top_k,
                category_filter=request.category_filter,
                price_min=request.price_min,
                price_max=request.price_max
            )
        
        return SearchResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )

@router.post("/index-product")
async def index_product(request: IndexProductRequest):
    """
    Index a single product for searching
    
    - **id**: Product ID (unique)
    - **name**: Product name
    - **description**: Product description
    - **image_url**: Product image URL
    - **category**: Product category
    - **price**: Product price
    - **attributes**: Optional product attributes (JSON)
    """
    try:
        search_service = get_search_service()
        
        success = search_service.index_product(
            product_id=request.id,
            name=request.name,
            description=request.description,
            image_url=request.image_url,
            category=request.category,
            price=request.price,
            attributes=request.attributes
        )
        
        if success:
            return {
                "status": "success",
                "message": f"Product {request.id} indexed successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to index product")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Indexing error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Indexing failed: {str(e)}"
        )

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns status of:
    - API service
    - Qdrant vector database
    - Redis cache
    - CLIP model
    """
    try:
        search_service = get_search_service()
        
        qdrant_healthy = search_service.qdrant_service.health_check()
        redis_healthy = search_service.cache_service.health_check()
        model_loaded = search_service.embedding_service.model is not None
        
        status = "healthy" if (qdrant_healthy and redis_healthy and model_loaded) else "degraded"
        
        return HealthResponse(
            status=status,
            qdrant_connected=qdrant_healthy,
            redis_connected=redis_healthy,
            model_loaded=model_loaded
        )
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return HealthResponse(
            status="unhealthy",
            qdrant_connected=False,
            redis_connected=False,
            model_loaded=False
        )

@router.get("/collections")
async def get_collection_info():
    """Get Qdrant collection information"""
    try:
        search_service = get_search_service()
        info = search_service.qdrant_service.get_collection_info()
        return info
    except Exception as e:
        logger.error(f"Error getting collection info: {e}")
        raise HTTPException(status_code=500, detail=str(e))
