"""
JWT Token handling for API authentication
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)


class JWTHandler:
    """Handle JWT token creation and validation"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        """
        Initialize JWT handler
        
        Args:
            secret_key: Secret key for signing tokens
            algorithm: JWT algorithm (default: HS256)
        """
        if not secret_key or len(secret_key) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def create_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT token
        
        Args:
            data: Claims to encode in token
            expires_delta: Token expiration time
        
        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)
        
        to_encode.update({"exp": expire})
        
        try:
            encoded_jwt = jwt.encode(
                to_encode,
                self.secret_key,
                algorithm=self.algorithm
            )
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating token: {e}")
            raise HTTPException(status_code=500, detail="Error creating token")
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token to verify
        
        Returns:
            Decoded token claims
        
        Raises:
            HTTPException: If token is invalid or expired
        """
        credentials_exception = HTTPException(
            status_code=401,
            detail="Invalid or expired credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            raise credentials_exception


# Global JWT handler (will be initialized in main)
_jwt_handler: Optional[JWTHandler] = None


def initialize_jwt_handler(secret_key: str) -> JWTHandler:
    """Initialize global JWT handler"""
    global _jwt_handler
    _jwt_handler = JWTHandler(secret_key)
    return _jwt_handler


def get_jwt_handler() -> JWTHandler:
    """Get global JWT handler"""
    if _jwt_handler is None:
        raise RuntimeError("JWT handler not initialized")
    return _jwt_handler


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create access token"""
    handler = get_jwt_handler()
    return handler.create_token(data, expires_delta)


def verify_token(token: str) -> Dict[str, Any]:
    """Verify token"""
    handler = get_jwt_handler()
    return handler.verify_token(token)


# Security scheme
security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security_scheme),
) -> Dict[str, Any]:
    """
    Dependency to get current user from token
    
    Usage:
        @router.get("/protected")
        async def protected(user = Depends(get_current_user)):
            return {"user_id": user["sub"]}
    """
    token = credentials.credentials
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
