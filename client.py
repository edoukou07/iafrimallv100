"""
Example client for integrating with your e-commerce API
"""

import requests
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ImageSearchClient:
    """Client for Image Search API"""
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
    
    def search_by_image(self, 
                       image_url: str,
                       top_k: int = 10,
                       category: Optional[str] = None,
                       price_min: Optional[float] = None,
                       price_max: Optional[float] = None) -> Dict:
        """
        Search for similar products by image URL
        
        Args:
            image_url: URL of the image to search
            top_k: Number of results to return
            category: Optional category filter
            price_min: Minimum price filter
            price_max: Maximum price filter
        
        Returns:
            Search results with products
        """
        payload = {
            "image_url": image_url,
            "top_k": top_k
        }
        
        if category:
            payload["category_filter"] = category
        if price_min is not None:
            payload["price_min"] = price_min
        if price_max is not None:
            payload["price_max"] = price_max
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/search",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Search by image failed: {e}")
            raise
    
    def search_by_text(self,
                      query: str,
                      top_k: int = 10,
                      category: Optional[str] = None,
                      price_min: Optional[float] = None,
                      price_max: Optional[float] = None) -> Dict:
        """
        Search for similar products by text query
        
        Args:
            query: Text description to search
            top_k: Number of results to return
            category: Optional category filter
            price_min: Minimum price filter
            price_max: Maximum price filter
        
        Returns:
            Search results with products
        """
        payload = {
            "text_query": query,
            "top_k": top_k
        }
        
        if category:
            payload["category_filter"] = category
        if price_min is not None:
            payload["price_min"] = price_min
        if price_max is not None:
            payload["price_max"] = price_max
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/search",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Search by text failed: {e}")
            raise
    
    def index_product(self,
                     product_id: str,
                     name: str,
                     description: str,
                     image_url: str,
                     category: str,
                     price: float,
                     attributes: Optional[Dict] = None) -> Dict:
        """
        Index a product for searching
        
        Args:
            product_id: Unique product ID
            name: Product name
            description: Product description
            image_url: Product image URL
            category: Product category
            price: Product price
            attributes: Optional product attributes
        
        Returns:
            Indexing result
        """
        payload = {
            "id": product_id,
            "name": name,
            "description": description,
            "image_url": image_url,
            "category": category,
            "price": price
        }
        
        if attributes:
            payload["attributes"] = attributes
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/index-product",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Product indexing failed: {e}")
            raise
    
    def health_check(self) -> Dict:
        """Check API health status"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/health",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy"}
    
    def get_collection_info(self) -> Dict:
        """Get collection statistics"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/collections",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Get collection info failed: {e}")
            raise


# Example usage with FastAPI e-commerce API
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/search", tags=["search"])
search_client = ImageSearchClient()

@router.get("/similar")
async def get_similar_products(image_url: str, top_k: int = 10, category: str = None):
    """
    Get products similar to the provided image
    
    Integrate with your e-commerce API like this:
    
    Example: GET /search/similar?image_url=https://example.com/image.jpg&top_k=10
    """
    try:
        results = search_client.search_by_image(
            image_url=image_url,
            top_k=top_k,
            category=category
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/index")
async def index_new_product(product: Dict):
    """
    Index a new product for searching
    
    Use this when adding products to your catalog
    """
    try:
        result = search_client.index_product(
            product_id=product["id"],
            name=product["name"],
            description=product["description"],
            image_url=product["image_url"],
            category=product["category"],
            price=product["price"],
            attributes=product.get("attributes")
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
