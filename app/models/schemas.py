from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Product(BaseModel):
    """Product model for database"""
    id: str
    name: str
    description: str
    image_url: str
    category: str
    price: float
    attributes: Optional[dict] = None
    embedding: Optional[List[float]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "prod_001",
                "name": "Red Shirt",
                "description": "Beautiful red cotton shirt",
                "image_url": "https://example.com/shirt.jpg",
                "category": "clothing",
                "price": 29.99,
                "attributes": {"color": "red", "size": "M"}
            }
        }

class SearchRequest(BaseModel):
    """Search request with image or text"""
    image_url: Optional[str] = None
    text_query: Optional[str] = None
    top_k: int = Field(default=10, ge=1, le=100)
    category_filter: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_url": "https://example.com/search-image.jpg",
                "top_k": 10,
                "category_filter": "clothing"
            }
        }

class SearchResult(BaseModel):
    """Single search result"""
    product_id: str
    name: str
    description: str
    image_url: str
    price: float
    category: str
    similarity_score: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "prod_001",
                "name": "Red Shirt",
                "description": "Beautiful red cotton shirt",
                "image_url": "https://example.com/shirt.jpg",
                "price": 29.99,
                "category": "clothing",
                "similarity_score": 0.95
            }
        }

class SearchResponse(BaseModel):
    """Search response with results"""
    query_type: str  # "image" or "text"
    top_k: int
    total_results: int
    results: List[SearchResult]
    execution_time_ms: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "query_type": "image",
                "top_k": 10,
                "total_results": 1,
                "results": [
                    {
                        "product_id": "prod_001",
                        "name": "Red Shirt",
                        "description": "Beautiful red cotton shirt",
                        "image_url": "https://example.com/shirt.jpg",
                        "price": 29.99,
                        "category": "clothing",
                        "similarity_score": 0.95
                    }
                ],
                "execution_time_ms": 245.5
            }
        }

class IndexProductRequest(BaseModel):
    """Request to index a product"""
    id: str
    name: str
    description: str
    image_url: str
    category: str
    price: float
    attributes: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "prod_001",
                "name": "Red Shirt",
                "description": "Beautiful red cotton shirt",
                "image_url": "https://example.com/shirt.jpg",
                "category": "clothing",
                "price": 29.99,
                "attributes": {"color": "red", "size": "M"}
            }
        }

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    qdrant_connected: bool
    redis_connected: bool
    model_loaded: bool
