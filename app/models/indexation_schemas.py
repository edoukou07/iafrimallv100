"""
Schemas for batch indexation from Django backend.

Payload structure:
{
    "products": [...],
    "callbackUrl": "https://api.afrimall.com/api/v1/products/search/ai/indexation/callback",
    "batchId": "batch-1706470800000"
}
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime


class ProductImage(BaseModel):
    """Image associated with a product"""
    url: str = Field(..., description="URL complète de l'image")
    altText: Optional[str] = Field(None, description="Texte alternatif")
    isPrimary: bool = Field(False, description="Image principale")


class ProductCategory(BaseModel):
    """Product category"""
    id: str = Field(..., description="UUID de la catégorie")
    name: str = Field(..., description="Nom de la catégorie")
    slug: str = Field(..., description="Slug URL")


class ProductProvider(BaseModel):
    """Product vendor/provider"""
    id: str = Field(..., description="UUID du vendeur")
    storeName: Optional[str] = Field(None, description="Nom de la boutique")


class ProductAttribute(BaseModel):
    """Product attribute key-value pair"""
    name: str = Field(..., description="Nom de l'attribut")
    value: str = Field(..., description="Valeur de l'attribut")


class ProductToIndex(BaseModel):
    """
    Product to be indexed by AI server.
    Received from Django backend.
    """
    id: str = Field(..., description="UUID du produit")
    title: str = Field(..., description="Titre du produit")
    slug: str = Field(..., description="Slug URL")
    description: Optional[str] = Field(None, description="Description complète")
    shortDescription: Optional[str] = Field(None, description="Description courte")
    price: float = Field(..., description="Prix en FCFA")
    salePrice: Optional[float] = Field(None, description="Prix promotionnel")
    currency: str = Field("XOF", description="Devise")
    category: Optional[ProductCategory] = Field(None, description="Catégorie")
    provider: Optional[ProductProvider] = Field(None, description="Vendeur")
    attributes: List[ProductAttribute] = Field(default_factory=list, description="Attributs produit")
    tags: List[str] = Field(default_factory=list, description="Tags")
    seoTitle: Optional[str] = Field(None, description="Titre SEO")
    seoDescription: Optional[str] = Field(None, description="Description SEO")
    seoKeywords: List[str] = Field(default_factory=list, description="Mots-clés SEO")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Métadonnées JSON")
    images: List[ProductImage] = Field(default_factory=list, description="Images du produit")
    
    def get_primary_image_url(self) -> Optional[str]:
        """Get the primary image URL or first image if no primary"""
        for img in self.images:
            if img.isPrimary:
                return img.url
        return self.images[0].url if self.images else None
    
    def get_text_for_embedding(self) -> str:
        """
        Build rich text for embedding generation.
        Combines multiple fields for better semantic search.
        """
        parts = []
        
        # Title is most important
        if self.title:
            parts.append(self.title)
        
        # SEO Title (often optimized for search)
        if self.seoTitle:
            parts.append(self.seoTitle)
        
        # Short description for quick context
        if self.shortDescription:
            parts.append(self.shortDescription)
        
        # SEO Description (optimized summary)
        if self.seoDescription:
            parts.append(self.seoDescription)
        
        # Full description
        if self.description:
            parts.append(self.description)
        
        # Category name
        if self.category:
            parts.append(f"Catégorie: {self.category.name}")
        
        # Tags
        if self.tags:
            parts.append(f"Tags: {', '.join(self.tags)}")
        
        # Attributes
        for attr in self.attributes:
            parts.append(f"{attr.name}: {attr.value}")
        
        # SEO keywords
        if self.seoKeywords:
            parts.append(f"Mots-clés: {', '.join(self.seoKeywords)}")
        
        return " | ".join(parts)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "iPhone 15 Pro Max 256GB",
                "slug": "iphone-15-pro-max-256gb",
                "description": "Le dernier iPhone avec puce A17 Pro",
                "shortDescription": "iPhone 15 Pro Max",
                "price": 850000,
                "salePrice": 799000,
                "currency": "XOF",
                "category": {"id": "cat-001", "name": "Smartphones", "slug": "smartphones"},
                "provider": {"id": "vendor-001", "storeName": "TechStore"},
                "attributes": [{"name": "Couleur", "value": "Noir"}, {"name": "Stockage", "value": "256GB"}],
                "tags": ["apple", "iphone", "smartphone"],
                "images": [{"url": "https://example.com/iphone.jpg", "altText": "iPhone 15", "isPrimary": True}]
            }
        }


class BatchIndexationRequest(BaseModel):
    """
    Batch indexation request from Django backend.
    
    Sent to: POST /indexation/products
    """
    products: List[ProductToIndex] = Field(..., description="Liste des produits à indexer")
    callbackUrl: str = Field(..., description="URL de callback pour les résultats")
    batchId: str = Field(..., description="ID unique du batch")
    
    class Config:
        json_schema_extra = {
            "example": {
                "products": [],
                "callbackUrl": "https://api.afrimall.com/api/v1/products/search/ai/indexation/callback",
                "batchId": "batch-1706470800000"
            }
        }


class ProductIndexResult(BaseModel):
    """Result of indexing a single product"""
    id: str = Field(..., description="Product UUID")
    isIndexed: bool = Field(..., description="Whether indexing succeeded")
    errorMessage: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        # Exclude None values from JSON output
        json_encoders = {type(None): lambda v: None}
    
    def model_dump(self, **kwargs):
        """Override to exclude None errorMessage"""
        data = super().model_dump(**kwargs)
        if data.get("errorMessage") is None:
            del data["errorMessage"]
        return data


class BatchIndexationCallback(BaseModel):
    """
    Callback payload sent back to Django backend.
    
    Sent to: POST {callbackUrl}
    
    Format exact attendu par Django:
    {
        "batchId": "batch-1706470800000",
        "results": [
            { "id": "product-uuid-1", "isIndexed": true },
            { "id": "product-uuid-2", "isIndexed": true },
            { "id": "product-uuid-3", "isIndexed": false, "errorMessage": "Description trop courte" }
        ]
    }
    """
    batchId: str = Field(..., description="ID du batch traité")
    results: List[ProductIndexResult] = Field(..., description="Résultats par produit")
    
    class Config:
        json_schema_extra = {
            "example": {
                "batchId": "batch-1706470800000",
                "results": [
                    {"id": "product-uuid-1", "isIndexed": True},
                    {"id": "product-uuid-2", "isIndexed": True},
                    {"id": "product-uuid-3", "isIndexed": False, "errorMessage": "Description trop courte"}
                ]
            }
        }


class BatchIndexationResponse(BaseModel):
    """
    Immediate response to batch indexation request.
    Processing happens asynchronously.
    """
    status: str = Field(..., description="accepted | rejected")
    batchId: str = Field(..., description="ID du batch")
    productsReceived: int = Field(..., description="Nombre de produits reçus")
    message: str = Field(..., description="Message de statut")
    estimatedTimeSeconds: Optional[int] = Field(None, description="Temps estimé en secondes")
