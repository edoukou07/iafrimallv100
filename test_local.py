#!/usr/bin/env python3
"""
Local testing script for Image Search API
Before deploying to Azure Container Apps
"""
import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class TestClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Test health endpoint"""
        print("\n🏥 Testing Health Check...")
        resp = self.session.get(f"{self.base_url}/api/v1/health")
        print(f"Status: {resp.status_code}")
        print(f"Response: {json.dumps(resp.json(), indent=2)}")
        return resp.json()
    
    def get_stats(self) -> Dict[str, Any]:
        """Test stats endpoint"""
        print("\n📊 Testing Stats Endpoint...")
        resp = self.session.get(f"{self.base_url}/api/v1/stats")
        print(f"Status: {resp.status_code}")
        print(f"Response: {json.dumps(resp.json(), indent=2)}")
        return resp.json()
    
    def embed_text(self, text: str) -> list:
        """Test text embedding"""
        print(f"\n🔤 Testing Text Embedding for: '{text}'...")
        resp = self.session.post(
            f"{self.base_url}/api/v1/embed",
            data={"text": text}
        )
        print(f"Status: {resp.status_code}")
        data = resp.json()
        print(f"Embedding dimension: {data.get('dimension')}")
        print(f"First 5 values: {data.get('embedding', [])[:5]}")
        return data.get('embedding', [])
    
    def index_product(self, product_id: str, name: str, description: str) -> bool:
        """Test product indexing"""
        print(f"\n📦 Indexing Product: {product_id}...")
        resp = self.session.post(
            f"{self.base_url}/api/v1/index-product",
            data={
                "product_id": product_id,
                "name": name,
                "description": description,
                "metadata": json.dumps({"brand": "Test Brand", "price": 99.99})
            }
        )
        print(f"Status: {resp.status_code}")
        print(f"Response: {json.dumps(resp.json(), indent=2)}")
        return resp.status_code == 200
    
    def search(self, query: str, limit: int = 5) -> list:
        """Test search"""
        print(f"\n🔍 Searching for: '{query}'...")
        resp = self.session.post(
            f"{self.base_url}/api/v1/search",
            json={"query": query, "limit": limit}
        )
        print(f"Status: {resp.status_code}")
        data = resp.json()
        print(f"Results found: {data.get('count')}")
        for i, result in enumerate(data.get('results', [])[:3], 1):
            print(f"  {i}. {result.get('metadata', {}).get('name')} (score: {result.get('score'):.3f})")
        return data.get('results', [])

def main():
    print("=" * 60)
    print("  Image Search API - Local Test Suite")
    print("=" * 60)
    
    client = TestClient(BASE_URL)
    
    try:
        # Test 1: Health check
        health = client.health_check()
        assert health.get('status') in ['healthy', 'degraded'], "Health check failed"
        
        # Test 2: Get stats
        stats = client.get_stats()
        assert 'collection' in stats, "Stats endpoint failed"
        
        # Test 3: Embed text
        embedding1 = client.embed_text("luxury handbag")
        assert len(embedding1) > 0, "Embedding failed"
        
        embedding2 = client.embed_text("premium leather bag")
        assert len(embedding2) > 0, "Embedding failed"
        
        # Test 4: Index products
        products = [
            ("prod_001", "Red Leather Handbag", "Premium red leather handbag with gold accents"),
            ("prod_002", "Blue Canvas Backpack", "Durable blue canvas backpack perfect for travel"),
            ("prod_003", "Black Wallet", "Classic black leather wallet with card slots"),
            ("prod_004", "Brown Suitcase", "Large brown suitcase for long trips"),
            ("prod_005", "Grey Shoulder Bag", "Stylish grey shoulder bag for everyday use"),
        ]
        
        for prod_id, name, desc in products:
            success = client.index_product(prod_id, name, desc)
            assert success, f"Failed to index {prod_id}"
        
        time.sleep(1)  # Wait for indexing
        
        # Test 5: Search
        results = client.search("red handbag", limit=5)
        assert len(results) > 0, "Search returned no results"
        
        # Test 6: Another search
        results = client.search("travel bag", limit=3)
        assert len(results) > 0, "Search returned no results"
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        print("\n🚀 Ready to deploy to Azure Container Apps!")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
