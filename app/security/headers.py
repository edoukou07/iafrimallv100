"""
Security headers middleware and utilities
"""

import logging
from fastapi.requests import Request
from fastapi.responses import Response

logger = logging.getLogger(__name__)


def get_security_headers() -> dict:
    """
    Get security headers to prevent common attacks
    
    Returns:
        Dictionary of security headers
    """
    return {
        # Prevent clickjacking
        "X-Frame-Options": "DENY",
        
        # Prevent MIME type sniffing
        "X-Content-Type-Options": "nosniff",
        
        # Enable XSS protection (for older browsers)
        "X-XSS-Protection": "1; mode=block",
        
        # Referrer policy
        "Referrer-Policy": "strict-origin-when-cross-origin",
        
        # Permissions policy (Feature policy replacement)
        "Permissions-Policy": (
            "accelerometer=(), camera=(), geolocation=(), "
            "gyroscope=(), magnetometer=(), microphone=(), "
            "payment=(), usb=()"
        ),
        
        # Content Security Policy (strict)
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        ),
        
        # Strict Transport Security (for HTTPS)
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
        
        # Disable caching for sensitive data
        "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
    }


class SecurityHeadersMiddleware:
    """Middleware to add security headers to all responses"""
    
    def __init__(self, app):
        self.app = app
        self.headers = get_security_headers()
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                # Add security headers
                headers = list(message.get("headers", []))
                for header_name, header_value in self.headers.items():
                    # Remove existing header if present
                    headers = [
                        (name, value) for name, value in headers
                        if name.decode() != header_name
                    ]
                    # Add new header
                    headers.append((
                        header_name.encode(),
                        header_value.encode()
                    ))
                message["headers"] = headers
            
            await send(message)
        
        await self.app(scope, receive, send_with_headers)


def add_security_headers(response: Response) -> Response:
    """Add security headers to response"""
    for header_name, header_value in get_security_headers().items():
        response.headers[header_name] = header_value
    return response
