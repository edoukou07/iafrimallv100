"""
Rate limiting to prevent DoS and brute force attacks
"""

import logging
import time
from typing import Optional, Dict, Tuple
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    In-memory rate limiter
    
    Tracks requests per client (IP) or user (token)
    """
    
    def __init__(self):
        """Initialize rate limiter"""
        self.requests: Dict[str, list] = {}
    
    def is_allowed(
        self,
        identifier: str,
        max_requests: int = 100,
        window_seconds: int = 60
    ) -> Tuple[bool, Dict]:
        """
        Check if request is allowed
        
        Args:
            identifier: Client identifier (IP or user_id)
            max_requests: Max requests in time window
            window_seconds: Time window in seconds
        
        Returns:
            Tuple of (allowed: bool, info: dict with remaining requests)
        
        Raises:
            HTTPException: If rate limit exceeded
        """
        current_time = time.time()
        
        # Initialize identifier if not exist
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Remove old requests outside the window
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if current_time - req_time < window_seconds
        ]
        
        remaining = max_requests - len(self.requests[identifier])
        
        if len(self.requests[identifier]) >= max_requests:
            logger.warning(f"Rate limit exceeded for {identifier}")
            reset_time = int(self.requests[identifier][0]) + window_seconds
            raise HTTPException(
                status_code=429,
                detail=f"Too many requests. Try again after {reset_time}",
                headers={"Retry-After": str(reset_time - int(current_time))}
            )
        
        # Add current request
        self.requests[identifier].append(current_time)
        
        return True, {
            "remaining": remaining,
            "limit": max_requests,
            "reset_at": int(current_time) + window_seconds
        }
    
    def cleanup(self, window_seconds: int = 3600):
        """Remove old entries (run periodically)"""
        current_time = time.time()
        identifiers_to_delete = []
        
        for identifier, timestamps in self.requests.items():
            # Remove old timestamps
            self.requests[identifier] = [
                t for t in timestamps
                if current_time - t < window_seconds
            ]
            
            # Mark empty identifiers for deletion
            if not self.requests[identifier]:
                identifiers_to_delete.append(identifier)
        
        # Delete empty entries
        for identifier in identifiers_to_delete:
            del self.requests[identifier]
        
        logger.debug(f"Rate limiter cleanup: removed {len(identifiers_to_delete)} entries")


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create global rate limiter"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


class RateLimitConfig:
    """Rate limit configurations per endpoint type"""
    
    # Public endpoints (per IP)
    PUBLIC_SEARCH = {"max_requests": 100, "window_seconds": 60}      # 100 req/min
    PUBLIC_HEALTH = {"max_requests": 60, "window_seconds": 60}       # 60 req/min
    
    # Authenticated endpoints (per user)
    AUTH_SEARCH = {"max_requests": 1000, "window_seconds": 60}       # 1000 req/min
    AUTH_UPLOAD = {"max_requests": 50, "window_seconds": 60}         # 50 req/min
    AUTH_INDEXATION = {"max_requests": 100, "window_seconds": 60}    # 100 req/min
    
    # Strict endpoints
    AUTH_LOGIN = {"max_requests": 5, "window_seconds": 300}          # 5 req/5min
    AUTH_REGISTER = {"max_requests": 3, "window_seconds": 3600}      # 3 req/hour
