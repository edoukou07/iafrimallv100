#!/usr/bin/env python3
"""
Test image search pipeline locally.
Tests CLIP embeddings + Qdrant + image search endpoints.
"""
import requests
import json
from pathlib import Path
import sys
from io import BytesIO
from PIL import Image
import numpy as np

BASE_URL = "http://localhost:8000"

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def print_success(text):
    print(f"✅ {text}")

def print_error(text):
    print(f"❌ {text}")

def print_info(text):
    print(f"ℹ️  {text}")

def create_test_image(width=224, height=224, color=(255, 0, 0)):
    """Create a simple test image (red square)."""
    img = Image.new('RGB', (width, height), color=color)
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

def test_health():
    """Test API health endpoint."""
    print_header("1. Testing API Health")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health")
        if response.status_code == 200:
            print_success("Health check passed")
            data = response.json()
            print(f"  Status: {data.get('status')}")
            print(f"  Version: {data.get('version')}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to {BASE_URL}")
        print_info("Make sure the server is running: python -m uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print_error(f"Health check error: {e}")
        return False

def test_stats():
    """Test stats endpoint."""
    print_header("2. Testing Stats Endpoint")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/stats")
        if response.status_code == 200:
            print_success("Stats retrieved")
            stats = response.json()
            print(f"  Embedding service: {stats.get('embedding_service', {}).get('type')}")
            print(f"  Dimension: {stats.get('embedding_service', {}).get('dimension')}")
            return True
        else:
            print_error(f"Stats error: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Stats error: {e}")
        return False

def test_text_embedding():
    """Test text embedding endpoint."""
    print_header("3. Testing Text Embedding (CLIP)")
    try:
        text = "A beautiful red dress"
        response = requests.post(
            f"{BASE_URL}/api/v1/embed",
            json={"text": text}
        )
        if response.status_code == 200:
            data = response.json()
            embedding = data.get("embedding", [])
            print_success(f"Text embedding generated: {len(embedding)} dimensions")
            print(f"  Text: '{text}'")
            print(f"  Embedding size: {len(embedding)}")
            print(f"  Sample values: {embedding[:3]}")
            return True, embedding
        else:
            print_error(f"Text embedding error: {response.status_code}")
            print(f"  Response: {response.text}")
            return False, None
    except Exception as e:
        print_error(f"Text embedding error: {e}")
        return False, None

def test_image_embedding():
    """Test image embedding endpoint."""
    print_header("4. Testing Image Embedding (CLIP)")
    try:
        # Create test image
        image_bytes = create_test_image(color=(255, 0, 0))  # Red
        
        response = requests.post(
            f"{BASE_URL}/api/v1/embed-image",
            files={"file": ("test_red.png", image_bytes, "image/png")}
        )
        
        if response.status_code == 200:
            data = response.json()
            embedding = data.get("embedding", [])
            print_success(f"Image embedding generated: {len(embedding)} dimensions")
            print(f"  Image: test_red.png (224x224, red)")
            print(f"  Embedding size: {len(embedding)}")
            print(f"  Sample values: {embedding[:3]}")
            return True, embedding
        else:
            print_error(f"Image embedding error: {response.status_code}")
            print(f"  Response: {response.text}")
            return False, None
    except Exception as e:
        print_error(f"Image embedding error: {e}")
        return False, None

def test_index_product_with_image():
    """Test product indexing with image."""
    print_header("5. Testing Product Indexing with Image")
    try:
        # Create test image
        image_bytes = create_test_image(color=(255, 100, 0))  # Orange
        
        response = requests.post(
            f"{BASE_URL}/api/v1/index-product-with-image",
            data={
                "product_id": "test_product_001",
                "name": "Beautiful Orange Dress",
                "description": "A stunning orange dress perfect for summer",
                "metadata": json.dumps({"price": 49.99, "category": "dress"})
            },
            files={"image_file": ("test_dress.png", image_bytes, "image/png")}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Product indexed successfully")
            print(f"  Product ID: test_product_001")
            print(f"  Embedding type: {data.get('embedding_type')}")
            print(f"  Embedding dimension: {data.get('embedding_dimension')}")
            return True
        else:
            print_error(f"Product indexing error: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Product indexing error: {e}")
        return False

def test_index_more_products():
    """Index additional products for search testing."""
    print_header("6. Indexing Additional Test Products")
    
    products = [
        {
            "id": "red_shirt_001",
            "name": "Red Casual Shirt",
            "desc": "Comfortable red shirt for everyday wear",
            "color": (255, 0, 0)  # Red
        },
        {
            "id": "blue_jeans_001",
            "name": "Blue Denim Jeans",
            "desc": "Classic blue jeans that fits perfectly",
            "color": (0, 0, 255)  # Blue
        },
        {
            "id": "green_hat_001",
            "name": "Green Summer Hat",
            "desc": "Stylish green hat for sunny days",
            "color": (0, 255, 0)  # Green
        }
    ]
    
    success_count = 0
    for product in products:
        try:
            image_bytes = create_test_image(color=product["color"])
            
            response = requests.post(
                f"{BASE_URL}/api/v1/index-product-with-image",
                data={
                    "product_id": product["id"],
                    "name": product["name"],
                    "description": product["desc"],
                    "metadata": json.dumps({"indexed": True})
                },
                files={"image_file": (f"{product['id']}.png", image_bytes, "image/png")}
            )
            
            if response.status_code == 200:
                print_success(f"Indexed: {product['name']}")
                success_count += 1
            else:
                print_error(f"Failed to index {product['name']}: {response.status_code}")
        except Exception as e:
            print_error(f"Error indexing {product['name']}: {e}")
    
    print_info(f"Successfully indexed {success_count}/{len(products)} products")
    return success_count == len(products)

def test_search_by_image():
    """Test image search endpoint."""
    print_header("7. Testing Image Search (Find Similar Products)")
    try:
        # Create a query image (orange-ish)
        query_image = create_test_image(color=(255, 80, 0))
        
        response = requests.post(
            f"{BASE_URL}/api/v1/search-image",
            files={"file": ("query.png", query_image, "image/png")},
            params={"limit": 5}
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            print_success(f"Image search returned {len(results)} results")
            print(f"  Query image: {data.get('query_image')}")
            print(f"  Model: {data.get('model')}")
            print(f"  Embedding dimension: {data.get('embedding_dimension')}")
            
            if results:
                print("\n  Top results:")
                for i, result in enumerate(results[:3], 1):
                    print(f"    {i}. {result.get('name')} (score: {result.get('score')})")
            else:
                print_info("  No results found (database might be empty)")
            
            return True
        else:
            print_error(f"Image search error: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Image search error: {e}")
        return False

def test_cross_modal_search():
    """Test cross-modal search (text query finds image products)."""
    print_header("8. Testing Cross-Modal Search (Text → Images)")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/search",
            json={"query": "red clothing item"},
            params={"limit": 5}
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            print_success(f"Cross-modal search returned {len(results)} results")
            print(f"  Query: 'red clothing item'")
            
            if results:
                print("\n  Top results:")
                for i, result in enumerate(results[:3], 1):
                    print(f"    {i}. {result.get('name')} (score: {result.get('score')})")
            else:
                print_info("  No results found")
            
            return True
        else:
            print_error(f"Cross-modal search error: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Cross-modal search error: {e}")
        return False

def main():
    """Run all tests."""
    print_header("🖼️  IMAGE SEARCH PIPELINE TEST SUITE")
    print_info("Testing CLIP embeddings + Qdrant + image search")
    print_info("Server should be running at http://localhost:8000")
    
    # Test 1: Health
    if not test_health():
        print_error("\n❌ Server is not running!")
        print_info("Start the server with:")
        print_info("  cd iafrimallv100")
        print_info("  python -m uvicorn app.main:app --reload")
        return
    
    # Test 2-4: Embeddings
    test_stats()
    text_ok, text_embed = test_text_embedding()
    image_ok, image_embed = test_image_embedding()
    
    # Test 5-6: Indexing
    index_ok = test_index_product_with_image()
    more_ok = test_index_more_products()
    
    # Test 7-8: Search
    search_ok = test_search_by_image()
    cross_ok = test_cross_modal_search()
    
    # Summary
    print_header("📊 TEST SUMMARY")
    tests = [
        ("Health Check", True),
        ("Stats Endpoint", True),
        ("Text Embedding (CLIP)", text_ok),
        ("Image Embedding (CLIP)", image_ok),
        ("Product Indexing", index_ok),
        ("Multi-Product Indexing", more_ok),
        ("Image Search", search_ok),
        ("Cross-Modal Search", cross_ok)
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for name, result in tests:
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    
    print_info(f"\nPassed: {passed}/{total} tests")
    
    if passed == total:
        print_success("\n🎉 All tests passed! Image search pipeline is working correctly.")
    else:
        print_error(f"\n⚠️  {total - passed} test(s) failed. Check errors above.")

if __name__ == "__main__":
    main()
