"""
Enhanced Error Response System
Provides standardized, user-friendly error responses with detailed context
"""
import logging
import traceback
import uuid
import time
from datetime import datetime
from flask import jsonify, request, g
from functools import wraps
from typing import Optional, Dict, Any
from collections.abc import Callable

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base class for API errors with enhanced context"""
    
    def __init__(self, message: str, status_code: int = 500, 
                 details: Optional[Dict[str, Any]] = None,
                 user_message: Optional[str] = None):
        """
        Initialize API error with context.
        
        Args:
            message: Technical error message (for logs)
            status_code: HTTP status code
            details: Additional error details
            user_message: User-friendly message (if different from technical message)
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.user_message = user_message or message
        self.error_id = str(uuid.uuid4())
        self.timestamp = datetime.utcnow().isoformat()


class ValidationError(APIError):
    """Validation error (400)"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message, 
            status_code=400,
            details=details,
            user_message=f"Validation error: {message}"
        )


class AuthenticationError(APIError):
    """Authentication error (401)"""
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message,
            status_code=401,
            user_message="Please log in to access this resource"
        )


class AuthorizationError(APIError):
    """Authorization error (403)"""
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message,
            status_code=403,
            user_message="You don't have permission to access this resource"
        )


class NotFoundError(APIError):
    """Resource not found error (404)"""
    def __init__(self, resource: str, resource_id: Any = None):
        message = f"{resource} not found"
        if resource_id:
            message += f": {resource_id}"
        super().__init__(
            message,
            status_code=404,
            user_message=f"The requested {resource.lower()} was not found"
        )


class ConflictError(APIError):
    """Conflict error (409) - e.g., duplicate entry"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message,
            status_code=409,
            details=details,
            user_message=f"Conflict: {message}"
        )


class DatabaseError(APIError):
    """Database error (500)"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message,
            status_code=500,
            details=details,
            user_message="A database error occurred. Please try again later."
        )


def create_error_response(error: Exception, include_traceback: bool = False) -> tuple:
    """
    Create a standardized error response from any exception.
    
    Args:
        error: The exception to convert
        include_traceback: Whether to include traceback (only in development)
    
    Returns:
        tuple: (json_response, status_code)
    """
    # Generate request ID if not already present
    request_id = getattr(g, 'request_id', str(uuid.uuid4()))
    
    # Handle known API errors
    if isinstance(error, APIError):
        response = {
            'error': {
                'id': error.error_id,
                'message': error.user_message,
                'technical_message': error.message,
                'details': error.details,
                'timestamp': error.timestamp,
                'request_id': request_id
            }
        }
        status_code = error.status_code
        
        # Log the error with full context
        logger.error(
            f"API Error [{error.error_id}]: {error.message}",
            extra={
                'error_id': error.error_id,
                'status_code': status_code,
                'request_id': request_id,
                'details': error.details,
                'endpoint': request.endpoint if hasattr(request, 'endpoint') else 'unknown'
            }
        )
    else:
        # Handle unexpected errors
        error_id = str(uuid.uuid4())
        response = {
            'error': {
                'id': error_id,
                'message': 'An unexpected error occurred',
                'technical_message': str(error),
                'timestamp': datetime.utcnow().isoformat(),
                'request_id': request_id
            }
        }
        status_code = 500
        
        # Log unexpected errors with traceback
        logger.error(
            f"Unexpected error [{error_id}]: {str(error)}",
            extra={
                'error_id': error_id,
                'error_type': type(error).__name__,
                'request_id': request_id,
                'traceback': traceback.format_exc()
            },
            exc_info=True
        )
    
    # Add traceback in development mode
    if include_traceback and hasattr(request, 'environ'):
        is_development = request.environ.get('FLASK_ENV') != 'production'
        if is_development:
            response['error']['traceback'] = traceback.format_exc()
    
    return jsonify(response), status_code


def api_error_handler(func: Callable) -> Callable:
    """
    Decorator to handle errors in API endpoints with standardized responses.
    
    Usage:
        @api_error_handler
        def my_endpoint():
            # Your code here
            if something_wrong:
                raise ValidationError("Invalid input")
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except APIError as e:
            return create_error_response(e)
        except Exception as e:
            return create_error_response(e, include_traceback=True)
    return wrapper


def add_request_id():
    """
    Middleware to add unique request ID to each request.
    Call this in Flask before_request.
    """
    g.request_id = str(uuid.uuid4())
    g.request_start_time = time.time()


def log_request_completion():
    """
    Middleware to log request completion.
    Call this in Flask after_request.
    """
    if hasattr(g, 'request_start_time'):
        elapsed_time = time.time() - g.request_start_time
        request_id = getattr(g, 'request_id', 'unknown')
        
        logger.info(
            f"Request completed: {request.method} {request.path}",
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.path,
                'status_code': getattr(g, 'response_status', 200),
                'elapsed_time': round(elapsed_time, 3)
            }
        )


def create_success_response(data: Any, message: Optional[str] = None, 
                           status_code: int = 200) -> tuple:
    """
    Create a standardized success response.
    
    Args:
        data: The data to return
        message: Optional success message
        status_code: HTTP status code (default: 200)
    
    Returns:
        tuple: (json_response, status_code)
    
    Example:
        return create_success_response(
            data={'clients': clients_list},
            message='Clients retrieved successfully'
        )
    """
    response = {
        'success': True,
        'data': data,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if message:
        response['message'] = message
    
    if hasattr(g, 'request_id'):
        response['request_id'] = g.request_id
    
    return jsonify(response), status_code


def validate_required_fields(data: Dict, required_fields: list) -> None:
    """
    Validate that required fields are present in request data.
    
    Args:
        data: Request data dictionary
        required_fields: List of required field names
    
    Raises:
        ValidationError: If any required field is missing
    
    Example:
        validate_required_fields(request.json, ['client_name', 'amount'])
    """
    missing_fields = []
    
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationError(
            f"Missing required fields: {', '.join(missing_fields)}",
            details={'missing_fields': missing_fields}
        )


def validate_field_types(data: Dict, field_types: Dict[str, type]) -> None:
    """
    Validate that fields have the correct type.
    
    Args:
        data: Request data dictionary
        field_types: Dictionary mapping field names to expected types
    
    Raises:
        ValidationError: If any field has wrong type
    
    Example:
        validate_field_types(
            request.json, 
            {'amount': (int, float), 'client_name': str}
        )
    """
    type_errors = []
    
    for field, expected_type in field_types.items():
        if field in data and data[field] is not None:
            if not isinstance(data[field], expected_type):
                type_errors.append(
                    f"{field} must be {expected_type.__name__}, got {type(data[field]).__name__}"
                )
    
    if type_errors:
        raise ValidationError(
            "Field type validation failed",
            details={'type_errors': type_errors}
        )


# Export commonly used functions
__all__ = [
    'APIError',
    'ValidationError',
    'AuthenticationError',
    'AuthorizationError',
    'NotFoundError',
    'ConflictError',
    'DatabaseError',
    'create_error_response',
    'api_error_handler',
    'add_request_id',
    'log_request_completion',
    'create_success_response',
    'validate_required_fields',
    'validate_field_types',
]

