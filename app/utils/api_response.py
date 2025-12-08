"""
Unified API response envelope helper.
All API endpoints should return: { data, error, meta }
"""
from typing import Any, Dict, Optional
from enum import Enum


class ErrorCode(Enum):
    """Standard error codes for API responses"""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    DATABASE_ERROR = "DATABASE_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    RATE_LIMIT_ERROR = "RATE_LIMIT_ERROR"
    INVALID_REQUEST = "INVALID_REQUEST"


def make_response(
    data: Any = None,
    error: Optional[Dict[str, Any]] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a unified response envelope.
    - data: payload (object, list, or None)
    - error: { code, message, details } or None
    - meta: pagination or contextual info
    
    Returns:
        Dict containing 'data', 'error', and 'meta' keys
    """
    return {
        'data': data,
        'error': error or None,
        'meta': meta or None,
    }


def success_response(data: Any = None, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Helper function for success responses.
    
    Args:
        data: Response data payload
        meta: Optional metadata (message, pagination, etc.)
    
    Returns:
        Standardized success response
    """
    return make_response(data=data, error=None, meta=meta)


def error_response(
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 400
) -> Dict[str, Any]:
    """
    Helper function for error responses.
    
    Args:
        code: Error code (use ErrorCode enum values)
        message: User-friendly error message
        details: Optional error details
        status_code: HTTP status code
    
    Returns:
        Standardized error response
    """
    error_dict = {
        'code': code,
        'message': message,
    }
    
    if details:
        error_dict['details'] = details
    
    return make_response(
        data=None,
        error=error_dict,
        meta={'status_code': status_code}
    )


def paginated_response(
    items: list,
    page: int,
    per_page: int,
    total: int,
    meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Helper function for paginated responses.
    
    Args:
        items: List of items for current page
        page: Current page number
        per_page: Items per page
        total: Total number of items
        meta: Additional metadata
    
    Returns:
        Standardized paginated response
    """
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    
    pagination_meta = {
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'prev_page': page - 1 if page > 1 else None,
            'next_page': page + 1 if page < total_pages else None
        }
    }
    
    if meta:
        pagination_meta.update(meta)
    
    return make_response(
        data=items,
        error=None,
        meta=pagination_meta
    )


__all__ = [
    'make_response',
    'success_response',
    'error_response',
    'paginated_response',
    'ErrorCode'
]


