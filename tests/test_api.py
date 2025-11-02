import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestHealthEndpoint:
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "qdrant_connected" in data
        assert "redis_connected" in data
        assert "model_loaded" in data

class TestRootEndpoint:
    def test_root(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        assert "version" in data
        assert "docs" in data

class TestSearchEndpoint:
    def test_search_missing_query(self):
        """Test search with missing query"""
        response = client.post(
            "/api/v1/search",
            json={
                "top_k": 10
            }
        )
        assert response.status_code == 400
    
    def test_search_both_queries(self):
        """Test search with both image_url and text_query"""
        response = client.post(
            "/api/v1/search",
            json={
                "image_url": "https://example.com/image.jpg",
                "text_query": "test",
                "top_k": 10
            }
        )
        assert response.status_code == 400
