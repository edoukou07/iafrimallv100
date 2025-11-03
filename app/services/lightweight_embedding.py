"""
Lightweight embedding service using sentence-transformers (no PyTorch/Transformers bloat).
Uses Redis cache to avoid recomputing embeddings.
"""
import json
import hashlib
import numpy as np
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import redis
import asyncio
from functools import lru_cache

class LightweightEmbeddingService:
    """Generate and cache embeddings efficiently."""
    
    _instance = None
    _model = None
    _redis_client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._model is None:
            # Using MiniLM (40MB vs 400MB for CLIP)
            self._model = SentenceTransformer('all-MiniLM-L6-v2')
    
    @staticmethod
    def _get_redis():
        """Get Redis connection (cached)."""
        from app.config import get_settings
        settings = get_settings()
        if LightweightEmbeddingService._redis_client is None:
            try:
                LightweightEmbeddingService._redis_client = redis.Redis(
                    host=settings.redis_host,
                    port=int(settings.redis_port),
                    password=settings.redis_password,
                    ssl=False,  # Disable SSL for Docker Compose communication
                    decode_responses=False
                )
                LightweightEmbeddingService._redis_client.ping()
            except Exception as e:
                print(f"Redis connection failed: {e}")
                LightweightEmbeddingService._redis_client = None
        return LightweightEmbeddingService._redis_client
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for embedding."""
        return f"embedding:{hashlib.md5(text.encode()).hexdigest()}"
    
    def embed(self, text: str) -> List[float]:
        """Get embedding for text, using cache if available."""
        cache_key = self._get_cache_key(text)
        redis_conn = self._get_redis()
        
        # Try to get from Redis cache
        if redis_conn:
            try:
                cached = redis_conn.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                print(f"Redis cache get failed: {e}")
        
        # Generate embedding
        embedding = self._model.encode(text).tolist()
        
        # Store in Redis cache (24h TTL)
        if redis_conn:
            try:
                redis_conn.setex(
                    cache_key,
                    86400,  # 24 hours
                    json.dumps(embedding)
                )
            except Exception as e:
                print(f"Redis cache set failed: {e}")
        
        return embedding
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts efficiently."""
        results = []
        redis_conn = self._get_redis()
        
        # Try batch cache first
        uncached_texts = []
        uncached_indices = []
        cache_keys = []
        
        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            cache_keys.append(cache_key)
            
            if redis_conn:
                try:
                    cached = redis_conn.get(cache_key)
                    if cached:
                        results.append(json.loads(cached))
                        continue
                except:
                    pass
            
            uncached_texts.append(text)
            uncached_indices.append(i)
            results.append(None)
        
        # Generate embeddings for uncached texts
        if uncached_texts:
            embeddings = self._model.encode(uncached_texts)
            
            for idx, embedding in zip(uncached_indices, embeddings):
                embedding_list = embedding.tolist()
                results[idx] = embedding_list
                
                # Cache it
                if redis_conn:
                    try:
                        redis_conn.setex(
                            cache_keys[idx],
                            86400,
                            json.dumps(embedding_list)
                        )
                    except:
                        pass
        
        return results
    
    def similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts."""
        emb1 = self.embed(text1)
        emb2 = self.embed(text2)
        
        # Cosine similarity
        emb1 = np.array(emb1)
        emb2 = np.array(emb2)
        
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        
        return float(dot_product / (norm1 * norm2 + 1e-8))


# Singleton instance
_embedding_service = None

def get_embedding_service() -> LightweightEmbeddingService:
    """Get singleton embedding service."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = LightweightEmbeddingService()
    return _embedding_service
