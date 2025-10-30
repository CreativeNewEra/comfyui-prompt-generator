"""
Authentication and authorization utilities.

Handles admin request authorization with support for:
- API key authentication
- IP-based access control (loopback + allowlist)
- Proxy header support (optional)
"""

import secrets
import ipaddress
import logging

from app.config import config

logger = logging.getLogger(__name__)


def get_client_ip(req) -> str:
    """
    Return the best-effort client IP for the current request.

    Security note: Only trusts X-Forwarded-For if TRUST_PROXY_HEADERS is enabled.
    By default, uses req.remote_addr which cannot be spoofed by clients.

    Args:
        req: Flask request object

    Returns:
        str: Client IP address, or empty string if unable to determine
    """
    if not req:
        return ''

    # Only trust X-Forwarded-For if explicitly enabled (i.e., behind a trusted proxy)
    if config.TRUST_PROXY_HEADERS:
        forwarded_for = req.headers.get('X-Forwarded-For', '') if hasattr(req, 'headers') else ''
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()

    # Default to remote_addr which is set by the WSGI server and cannot be spoofed
    return getattr(req, 'remote_addr', '') or ''


def is_loopback_ip(ip: str) -> bool:
    """
    Return True if the provided IP address is a loopback/localhost address.

    Args:
        ip: IP address string (e.g., '127.0.0.1', '::1')

    Returns:
        bool: True if loopback, False otherwise
    """
    if not ip:
        return False

    try:
        return ipaddress.ip_address(ip).is_loopback
    except ValueError:
        return False


def authorize_admin_request(req):
    """
    Evaluate whether the incoming request may access admin-only endpoints.

    Authorization methods (in order of precedence):
    1. API key authentication (X-Admin-API-Key header or admin_api_key query param)
    2. IP-based access (loopback or in ADMIN_ALLOWED_IPS)

    Args:
        req: Flask request object

    Returns:
        tuple: (authorized: bool, client_ip: str, forwarded_for: str, reason: str)
    """
    client_ip = get_client_ip(req)
    forwarded_for = req.headers.get('X-Forwarded-For', '') if hasattr(req, 'headers') else ''

    # Check API key if configured
    if config.ADMIN_API_KEY:
        args = getattr(req, 'args', {})
        provided_key = (req.headers.get('X-Admin-API-Key') if hasattr(req, 'headers') else None) or args.get('admin_api_key')
        if provided_key and secrets.compare_digest(str(provided_key), str(config.ADMIN_API_KEY)):
            logger.info(f"Admin request authorized via API key from {client_ip}")
            return True, client_ip, forwarded_for, 'valid API key'
        return False, client_ip, forwarded_for, 'missing or invalid API key'

    # Check IP-based access
    if client_ip and (is_loopback_ip(client_ip) or client_ip in config.ADMIN_ALLOWED_IPS):
        logger.info(f"Admin request authorized via IP from {client_ip}")
        return True, client_ip, forwarded_for, 'allowed client IP'

    if not client_ip:
        logger.warning("Admin request denied: unable to determine client IP")
        return False, client_ip, forwarded_for, 'unable to determine client IP'

    logger.warning(f"Admin request denied: client IP {client_ip} not permitted")
    return False, client_ip, forwarded_for, 'client IP not permitted'
