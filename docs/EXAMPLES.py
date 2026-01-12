"""
Exemples d'intégration avec l'Image Search API

Démonstration des cas d'usage courants pour e-commerce
"""

import requests
from typing import List, Dict

API_URL = "http://20.238.104.13:8000"


# ============================================================================
# 1. RECHERCHE TEXTE - Barre de recherche simple
# ============================================================================

def search_products(query: str, limit: int = 20) -> List[Dict]:
    """
    Intégration pour une barre de recherche.
    
    Usage:
        results = search_products("red shoes")
    """
    try:
        response = requests.post(
            f"{API_URL}/api/v1/search",
            json={"query": query, "limit": limit},
            timeout=15
        )
        response.raise_for_status()
        return response.json()["results"]
    except Exception as e:
        print(f"Search error: {e}")
        return []


# ============================================================================
# 2. RECHERCHE INVERSE D'IMAGE - Upload image, find similar
# ============================================================================

def reverse_image_search(image_file_path: str, limit: int = 10) -> List[Dict]:
    """
    Recherche inverse: client upload une image, cherche produits similaires.
    
    Usage:
        results = reverse_image_search("photo.jpg")
    """
    try:
        with open(image_file_path, 'rb') as f:
            files = {'file': f}
            data = {'limit': limit}
            response = requests.post(
                f"{API_URL}/api/v1/search-image",
                files=files,
                data=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()["results"]
    except Exception as e:
        print(f"Image search error: {e}")
        return []


# ============================================================================
# 3. RECHERCHE VOCALE - Audio search
# ============================================================================

def voice_search(audio_file_path: str, limit: int = 10) -> List[Dict]:
    """
    Recherche par voix: client parle, API transcrit et cherche.
    
    Formats acceptés: MP3, WAV, OGG, FLAC, M4A
    
    Usage:
        results = voice_search("search_audio.mp3")
    """
    try:
        with open(audio_file_path, 'rb') as f:
            files = {'file': f}
            data = {'limit': limit}
            response = requests.post(
                f"{API_URL}/api/v1/voice-search",
                files=files,
                data=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()["results"]
    except Exception as e:
        print(f"Voice search error: {e}")
        return []


# ============================================================================
# 4. AFFICHER LES RÉSULTATS
# ============================================================================

def display_search_results(results: List[Dict], max_items: int = 10):
    """Afficher les résultats de recherche."""
    if not results:
        print("❌ No results found")
        return
    
    print(f"\n✅ Found {len(results)} results:\n")
    
    for i, product in enumerate(results[:max_items], 1):
        metadata = product.get("metadata", {})
        score = product.get("score", 0)
        
        print(f"{i}. {metadata.get('name', 'N/A')}")
        print(f"   Score: {score:.2%}")
        print(f"   Price: ${metadata.get('price', 'N/A')}")
        print(f"   Category: {metadata.get('category', 'N/A')}")
        print(f"   URL: {metadata.get('url', 'N/A')}")
        print(f"   Image: {metadata.get('image_url', 'N/A')}")
        print()


# ============================================================================
# 5. INDEXER UN PRODUIT (avec embedding calculé par API)
# ============================================================================

def index_product_from_image(
    product_id: str,
    name: str,
    description: str,
    image_path: str,
    price: float = None,
    category: str = None,
    url: str = None
) -> bool:
    """
    Indexer un produit avec image.
    L'API calcule automatiquement l'embedding CLIP.
    
    Usage:
        success = index_product_from_image(
            product_id="123",
            name="Nike Red Shoes",
            description="High-performance running shoes",
            image_path="shoe.jpg",
            price=129.99,
            category="footwear",
            url="https://shop.com/products/shoe1"
        )
    """
    try:
        with open(image_path, 'rb') as f:
            files = {'file': f}
            data = {
                'product_id': product_id,
                'name': name,
                'description': description,
            }
            
            # Ajouter les métadonnées optionnelles
            if price is not None:
                data['price'] = price
            if category:
                data['category'] = category
            if url:
                data['url'] = url
            
            response = requests.post(
                f"{API_URL}/api/v1/index-product-with-image",
                files=files,
                data=data,
                timeout=60
            )
            response.raise_for_status()
            
            print(f"✅ Product '{name}' indexed successfully")
            return True
    
    except Exception as e:
        print(f"❌ Index error: {e}")
        return False


# ============================================================================
# 6. BULK INDEXING - Importer le catalogue
# ============================================================================

def bulk_index_products(products_list: List[Dict]) -> Dict[str, int]:
    """
    Indexer plusieurs produits en une passe.
    
    Chaque produit doit avoir: id, name, description, image_path, et optionnellement price, category, url
    
    Usage:
        products = [
            {
                "id": "1",
                "name": "Nike Shoes",
                "description": "Red running shoes",
                "image_path": "shoe1.jpg",
                "price": 99.99,
                "category": "footwear"
            },
            ...
        ]
        stats = bulk_index_products(products)
        print(f"Indexed: {stats['success']}, Failed: {stats['failed']}")
    """
    stats = {"success": 0, "failed": 0, "errors": []}
    
    for product in products_list:
        success = index_product_from_image(
            product_id=product.get("id"),
            name=product.get("name"),
            description=product.get("description"),
            image_path=product.get("image_path"),
            price=product.get("price"),
            category=product.get("category"),
            url=product.get("url")
        )
        
        if success:
            stats["success"] += 1
        else:
            stats["failed"] += 1
            stats["errors"].append(f"Product {product.get('id')}")
    
    return stats


# ============================================================================
# 7. VÉRIFIER LA SANTÉ DE L'API
# ============================================================================

def check_api_health() -> bool:
    """
    Vérifier que l'API est opérationnelle avant de l'utiliser.
    
    Usage:
        if check_api_health():
            results = search_products("shoes")
        else:
            print("API is down, please retry later")
    """
    try:
        response = requests.get(
            f"{API_URL}/api/v1/health",
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                print("✅ API is healthy")
                stats = data.get("qdrant", {}).get("stats", {})
                print(f"   Products indexed: {stats.get('points_count', 0)}")
                return True
        
        print("❌ API is not healthy")
        return False
    
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return False


# ============================================================================
# 8. RÉCUPÉRER LES STATISTIQUES
# ============================================================================

def get_api_stats() -> Dict:
    """
    Récupérer les statistiques de l'index.
    
    Returns:
        {
            "name": "products",
            "points_count": 1250,
            "vectors_count": 1250,
            "segment_count": 5
        }
    """
    try:
        response = requests.get(
            f"{API_URL}/api/v1/stats",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Stats error: {e}")
        return {}


# ============================================================================
# EXEMPLE D'UTILISATION COMPLÈTE
# ============================================================================

if __name__ == "__main__":
    # Vérifier la santé de l'API
    if not check_api_health():
        exit(1)
    
    # Exemple 1: Recherche texte
    print("\n" + "="*50)
    print("TEXT SEARCH")
    print("="*50)
    results = search_products("blue running shoes", limit=5)
    display_search_results(results)
    
    # Exemple 2: Vérifier les statistiques
    print("\n" + "="*50)
    print("API STATISTICS")
    print("="*50)
    stats = get_api_stats()
    print(f"Total products indexed: {stats.get('points_count', 0)}")
    print(f"Total vectors: {stats.get('vectors_count', 0)}")
    
    # Exemple 3: Recherche image (si image disponible)
    # print("\n" + "="*50)
    # print("REVERSE IMAGE SEARCH")
    # print("="*50)
    # results = reverse_image_search("product.jpg", limit=5)
    # display_search_results(results)
    
    # Exemple 4: Indexer un nouveau produit (si image disponible)
    # print("\n" + "="*50)
    # print("INDEX NEW PRODUCT")
    # print("="*50)
    # index_product_from_image(
    #     product_id="999",
    #     name="Adidas Blue Shoes",
    #     description="Comfortable blue athletic shoes",
    #     image_path="adidas_shoe.jpg",
    #     price=89.99,
    #     category="footwear",
    #     url="https://shop.com/products/adidas-shoe"
    # )
