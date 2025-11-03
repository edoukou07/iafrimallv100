"""
Pytest configuration and fixtures
"""

import pytest
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture
def test_config():
    """Test configuration"""
    return {
        "QDRANT_HOST": "localhost",
        "QDRANT_PORT": 6333,
        "REDIS_HOST": "localhost",
        "REDIS_PORT": 6379,
        "MODEL_NAME": "openai/clip-vit-base-patch32",
    }

@pytest.fixture
def sample_product():
    """Sample product for testing"""
    return {
        "id": "test_prod_001",
        "name": "Test Product",
        "description": "A test product",
        "image_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=500",
        "category": "test",
        "price": 99.99,
        "attributes": {"test": "value"}
    }

@pytest.fixture
def sample_search_request():
    """Sample search request for testing"""
    return {
        "text_query": "test product",
        "top_k": 10,
        "category_filter": None,
        "price_min": None,
        "price_max": None
    }
