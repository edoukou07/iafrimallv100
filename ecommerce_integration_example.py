"""
Integration client example for e-commerce API
Shows how to integrate Image Search API with your main e-commerce backend
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from typing import Optional
import logging

# Import the search client
from client import ImageSearchClient

logger = logging.getLogger(__name__)

# Initialize client
search_client = ImageSearchClient(base_url="http://localhost:8000")

# Your main e-commerce FastAPI app
app = FastAPI(title="E-commerce API with Image Search")

# ============= Search Endpoints =============

@app.get("/products/search-similar")
async def search_similar_products(
    image_url: str,
    top_k: int = 10,
    category: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None
):
    """
    Get products similar to a given image
    
    Usage:
    GET /products/search-similar?image_url=https://example.com/image.jpg&top_k=10
    """
    try:
        # Check if search service is healthy
        health = search_client.health_check()
        if health.get("status") != "healthy":
            raise HTTPException(status_code=503, detail="Search service unavailable")
        
        # Perform search
        results = search_client.search_by_image(
            image_url=image_url,
            top_k=top_k,
            category=category,
            price_min=price_min,
            price_max=price_max
        )
        
        return results
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products/search-text")
async def search_by_description(
    query: str,
    top_k: int = 10,
    category: Optional[str] = None
):
    """
    Search for products by text description
    
    Usage:
    GET /products/search-text?query=red%20cotton%20shirt&top_k=10
    """
    try:
        results = search_client.search_by_text(
            query=query,
            top_k=top_k,
            category=category
        )
        return results
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============= Product Management Endpoints =============

@app.post("/products")
async def create_product(
    product_data: dict,
    background_tasks: BackgroundTasks
):
    """
    Create a new product and index it for search
    
    Example payload:
    {
        "id": "prod_123",
        "name": "Red T-Shirt",
        "description": "Beautiful red cotton t-shirt",
        "image_url": "https://example.com/image.jpg",
        "category": "clothing",
        "price": 29.99,
        "attributes": {"color": "red", "size": "M"}
    }
    """
    try:
        # 1. Save product to your database
        # product = db.save_product(product_data)
        
        # 2. Index product in search service (background task)
        background_tasks.add_task(
            search_client.index_product,
            product_id=product_data["id"],
            name=product_data["name"],
            description=product_data["description"],
            image_url=product_data["image_url"],
            category=product_data["category"],
            price=product_data["price"],
            attributes=product_data.get("attributes")
        )
        
        return {
            "status": "success",
            "message": "Product created and indexed",
            "product_id": product_data["id"]
        }
    except Exception as e:
        logger.error(f"Product creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/products/{product_id}")
async def update_product(product_id: str, product_data: dict, background_tasks: BackgroundTasks):
    """
    Update product and re-index for search
    """
    try:
        # 1. Update product in database
        # product = db.update_product(product_id, product_data)
        
        # 2. Re-index product
        background_tasks.add_task(
            search_client.index_product,
            product_id=product_id,
            **product_data
        )
        
        return {
            "status": "success",
            "message": "Product updated and re-indexed"
        }
    except Exception as e:
        logger.error(f"Product update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============= Health and Status Endpoints =============

@app.get("/search-service/health")
async def search_service_health():
    """Check if image search service is healthy"""
    return search_client.health_check()

@app.get("/search-service/stats")
async def search_service_stats():
    """Get search service statistics"""
    try:
        return search_client.get_collection_info()
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============= Frontend Integration Example =============

@app.get("/api/recommendations/{product_id}")
async def get_product_recommendations(product_id: str, limit: int = 6):
    """
    Get product recommendations based on current product image
    
    Usage: GET /api/recommendations/prod_123?limit=6
    
    Frontend usage:
    fetch('/api/recommendations/prod_123?limit=6')
      .then(res => res.json())
      .then(data => displayRecommendations(data.results))
    """
    try:
        # 1. Get current product from DB
        # product = db.get_product(product_id)
        
        # 2. Find similar products
        # results = search_client.search_by_image(product.image_url, top_k=limit)
        
        # Mock response
        return {
            "product_id": product_id,
            "recommendations": [
                # Will contain similar products
            ]
        }
    except Exception as e:
        logger.error(f"Recommendations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
