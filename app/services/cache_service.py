import logging
import json
import hashlib
from typing import Optional, Any
import redis

logger = logging.getLogger(__name__)

class CacheService:
    """Service for Redis caching"""
    
    def __init__(self, host: str, port: int, password: Optional[str] = None, ttl: int = 3600):
        """Initialize Redis client"""
        self.host = host
        self.port = port
        self.ttl = ttl
        
        logger.info(f"Connecting to Redis at {host}:{port}")
        
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            password=password,
            decode_responses=True,
            socket_connect_timeout=5
        )
        
        # Test connection
        try:
            self.redis_client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Error connecting to Redis: {e}")
            self.redis_client = None
    
    def _generate_key(self, prefix: str, data: str) -> str:
        """Generate cache key using hash"""
        hash_obj = hashlib.md5(data.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if not self.redis_client:
                return None
            
            value = self.redis_client.get(key)
            if value:
                logger.debug(f"Cache hit for key: {key}")
                return json.loads(value)
            
            logger.debug(f"Cache miss for key: {key}")
            return None
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        try:
            if not self.redis_client:
                return False
            
            ttl = ttl or self.ttl
            self.redis_client.setex(
                key,
                ttl,
                json.dumps(value)
            )
            logger.debug(f"Cache set for key: {key} with TTL: {ttl}s")
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            if not self.redis_client:
                return False
            
            self.redis_client.delete(key)
            logger.debug(f"Cache deleted for key: {key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        try:
            if not self.redis_client:
                return 0
            
            keys = self.redis_client.keys(pattern)
            if keys:
                count = self.redis_client.delete(*keys)
                logger.debug(f"Cache cleared {count} keys matching pattern: {pattern}")
                return count
            return 0
        except Exception as e:
            logger.error(f"Error clearing cache pattern: {e}")
            return 0
    
    def health_check(self) -> bool:
        """Check if Redis is healthy"""
        try:
            if not self.redis_client:
                return False
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False    
    @classmethod
    def from_url(cls, url: str, ttl: int = 3600):
        """Create CacheService from Redis URL (e.g., redis://:password@host:port?ssl=True)"""
        logger.info(f"Connecting to Redis from URL: {url[:30]}...")
        
        redis_client = redis.from_url(url, decode_responses=True, socket_connect_timeout=5)
        
        # Create instance and set redis_client
        instance = cls.__new__(cls)
        instance.redis_client = redis_client
        instance.ttl = ttl
        instance.host = "redis-url"
        instance.port = 0
        
        # Test connection
        try:
            redis_client.ping()
            logger.info("Connected to Redis successfully via URL")
        except Exception as e:
            logger.error(f"Error connecting to Redis via URL: {e}")
            instance.redis_client = None
        
        return instance