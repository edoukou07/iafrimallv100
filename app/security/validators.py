"""
URL and input validators for SSRF prevention and security
"""

import logging
import ipaddress
from urllib.parse import urlparse
from typing import Optional
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class URLValidator:
    """Validates URLs to prevent SSRF attacks"""
    
    # Protocols de fichiers considérés comme dangereux
    DANGEROUS_SCHEMES = {
        "file", "ftp", "gopher", "ldap", "dict", "data", "jar", "jar!", "jndi"
    }
    
    # Domaines/IPs à blocquer (réseau privé)
    BLOCKED_DOMAINS = {
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "169.254.0.0",  # Link-local
    }
    
    # Domaines de métadonnées à blocquer (AWS, Azure, GCP, etc.)
    METADATA_DOMAINS = {
        "169.254.169.254",      # AWS metadata
        "metadata.google.internal",
        "metadata.alibabacloud.com",
        "100.100.100.200",       # Alibaba
    }
    
    @staticmethod
    def is_private_ip(ip_str: str) -> bool:
        """Check if IP is private/internal"""
        try:
            ip = ipaddress.ip_address(ip_str)
            return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
        except ValueError:
            return False
    
    @staticmethod
    def is_hostname_blocked(hostname: str) -> bool:
        """Check if hostname is in blocklist"""
        hostname_lower = hostname.lower()
        
        # Exact match
        if hostname_lower in URLValidator.BLOCKED_DOMAINS:
            return True
        
        # Check metadata domains
        if hostname_lower in URLValidator.METADATA_DOMAINS:
            return True
        
        # Multiple underscores (often bypass techniques)
        if hostname_lower.count("_") > 1:
            return True
        
        return False
    
    @classmethod
    def validate_url(cls, url: str, allowed_domains: Optional[list] = None) -> bool:
        """
        Validate URL for SSRF attacks
        
        Args:
            url: URL to validate
            allowed_domains: Optional whitelist of allowed domains
        
        Returns:
            True if URL is safe
        
        Raises:
            HTTPException: If URL is unsafe
        """
        if not url or not isinstance(url, str):
            raise HTTPException(status_code=400, detail="Invalid URL")
        
        url = url.strip()
        
        try:
            parsed = urlparse(url)
        except Exception as e:
            logger.warning(f"Failed to parse URL: {url} - {e}")
            raise HTTPException(status_code=400, detail="Invalid URL format")
        
        # Check scheme
        scheme = parsed.scheme.lower()
        if scheme in cls.DANGEROUS_SCHEMES:
            logger.warning(f"Dangerous scheme blocked: {scheme}")
            raise HTTPException(status_code=403, detail=f"Scheme '{scheme}' not allowed")
        
        if scheme not in {"http", "https"}:
            logger.warning(f"Unsupported scheme: {scheme}")
            raise HTTPException(status_code=400, detail="Only HTTP/HTTPS allowed")
        
        # Get hostname
        hostname = parsed.hostname
        if not hostname:
            raise HTTPException(status_code=400, detail="Invalid URL: no hostname")
        
        # Check if hostname is blocked
        if cls.is_hostname_blocked(hostname):
            logger.warning(f"Blocked hostname: {hostname}")
            raise HTTPException(status_code=403, detail="Access to this host is forbidden")
        
        # Check if IP is private
        if cls.is_private_ip(hostname):
            logger.warning(f"Private IP blocked: {hostname}")
            raise HTTPException(status_code=403, detail="Access to private networks forbidden")
        
        # Check whitelist if provided
        if allowed_domains and hostname not in allowed_domains:
            logger.warning(f"Domain not in whitelist: {hostname}")
            raise HTTPException(status_code=403, detail="Domain not allowed")
        
        return True


def validate_image_url(image_url: str, allowed_domains: Optional[list] = None) -> str:
    """
    Validate image URL before downloading
    
    Args:
        image_url: URL of image
        allowed_domains: Optional whitelist of allowed domains
    
    Returns:
        Validated URL
    
    Raises:
        HTTPException: If URL is unsafe
    """
    URLValidator.validate_url(image_url, allowed_domains)
    return image_url


def validate_file_size(content_length: int, max_size_mb: int = 50) -> bool:
    """
    Validate file size to prevent DoS
    
    Args:
        content_length: Size in bytes
        max_size_mb: Maximum allowed size in MB
    
    Returns:
        True if size is acceptable
    
    Raises:
        HTTPException: If size exceeds limit
    """
    max_bytes = max_size_mb * 1024 * 1024
    if content_length > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {max_size_mb}MB"
        )
    return True
