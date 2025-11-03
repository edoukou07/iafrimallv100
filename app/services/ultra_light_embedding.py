"""
Ultra-lightweight embedding service using TF-IDF (scikit-learn).
No PyTorch, Transformers, or sentence-transformers dependencies.
Uses pre-computed embeddings from Qdrant + TF-IDF for search.
"""
import json
import hashlib
import numpy as np
from typing import List, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
import redis
import logging

logger = logging.getLogger(__name__)

class UltraLightEmbeddingService:
    """Generate and cache TF-IDF embeddings - no heavy ML models."""
    
    _instance = None
    _vectorizer = None
    _redis_client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._vectorizer is None:
            # TF-IDF vectorizer - very lightweight
            # max_features limits dimension to ~500
            self._vectorizer = TfidfVectorizer(
                max_features=500,
                ngram_range=(1, 2),
                min_df=1,
                max_df=1.0,
                lowercase=True,
                stop_words='english'
            )
            # Pre-fit with dummy data to initialize
            self._vectorizer.fit(['search query text'])
    
    @staticmethod
    def _get_redis():
        """Get Redis connection (cached)."""
        from app.config import get_settings
        settings = get_settings()
        if UltraLightEmbeddingService._redis_client is None:
            try:
                UltraLightEmbeddingService._redis_client = redis.Redis(
                    host=settings.redis_host,
                    port=int(settings.redis_port),
                    password=settings.redis_password,
                    ssl=False,  # Disable SSL for Docker Compose communication
                    decode_responses=False
                )
                UltraLightEmbeddingService._redis_client.ping()
            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                UltraLightEmbeddingService._redis_client = None
        return UltraLightEmbeddingService._redis_client
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for embedding."""
        return f"tfidf_embedding:{hashlib.md5(text.encode()).hexdigest()}"
    
    def embed(self, text: str) -> List[float]:
        """Get TF-IDF embedding for text, using cache if available."""
        cache_key = self._get_cache_key(text)
        redis_conn = self._get_redis()
        
        # Try to get from Redis cache
        if redis_conn:
            try:
                cached = redis_conn.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Redis cache get failed: {e}")
        
        # Generate TF-IDF embedding
        try:
            tfidf_vector = self._vectorizer.transform([text]).toarray()[0]
            embedding = tfidf_vector.tolist()
        except Exception as e:
            logger.error(f"TF-IDF embedding failed: {e}")
            # Fallback: return zero vector
            embedding = [0.0] * len(self._vectorizer.get_feature_names_out())
        
        # Store in Redis cache (24h TTL)
        if redis_conn:
            try:
                redis_conn.setex(
                    cache_key,
                    86400,  # 24 hours
                    json.dumps(embedding)
                )
            except Exception as e:
                logger.warning(f"Redis cache set failed: {e}")
        
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
            try:
                tfidf_vectors = self._vectorizer.transform(uncached_texts).toarray()
                
                for idx, vector in zip(uncached_indices, tfidf_vectors):
                    embedding_list = vector.tolist()
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
            except Exception as e:
                logger.error(f"Batch TF-IDF embedding failed: {e}")
        
        return results
    
    def similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts."""
        try:
            emb1 = np.array(self.embed(text1))
            emb2 = np.array(self.embed(text2))
            
            dot_product = np.dot(emb1, emb2)
            norm1 = np.linalg.norm(emb1)
            norm2 = np.linalg.norm(emb2)
            
            return float(dot_product / (norm1 * norm2 + 1e-8))
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            return 0.0
    
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return len(self._vectorizer.get_feature_names_out())


# Singleton instance
_embedding_service = None

def get_embedding_service() -> UltraLightEmbeddingService:
    """Get singleton embedding service."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = UltraLightEmbeddingService()
    return _embedding_service
