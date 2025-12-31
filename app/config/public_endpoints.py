"""
Public API endpoints configuration
Endpoints that don't require authentication
"""
from typing import List

# Public endpoints that don't require authentication
PUBLIC_ENDPOINTS: List[str] = [
    '/api/v1/exchange-rates/current',
    '/api/v1/health/',
    '/api/v1/health',  # Without trailing slash
    '/api/health',  # Direct health check
]

def is_public_endpoint(path: str) -> bool:
    """
    Check if an endpoint is public (doesn't require authentication)
    
    Args:
        path: Request path to check
    
    Returns:
        True if endpoint is public, False otherwise
    """
    return any(path.startswith(endpoint) for endpoint in PUBLIC_ENDPOINTS)

