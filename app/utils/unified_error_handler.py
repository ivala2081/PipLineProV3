"""
Unified Error Handling Module for PipLinePro
Consolidates all error handling implementations into a single, comprehensive system
"""
import logging
import traceback
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Union, Tuple, List
from functools import wraps
from flask import jsonify, request, current_app, g
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from decimal import InvalidOperation

from .unified_logger import get_enhanced_logger, PerformanceLogger

# Get enhanced logger - lazy initialization to avoid circular imports
logger = None

def _get_logger():
    """Get logger instance (lazy initialization)"""
    global logger
    if logger is None:
        logger = get_enhanced_logger("ErrorHandler")
    return logger


def _get_request_id() -> str:
    """Get or create request ID for correlation tracking"""
    if not hasattr(request, 'request_id'):
        request.request_id = str(uuid.uuid4())
    return request.request_id


class PipLineError(Exception):
    """
    Base exception class for PipLinePro application
    Combines features from all error handler implementations
    """
    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        retryable: bool = False
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.user_message = user_message or "An unexpected error occurred. Please try again."
        self.context = context or {}
        self.timestamp = datetime.now(timezone.utc)
        self.retryable = retryable
        self.request_id = _get_request_id() if request else None

    def to_dict(self, include_details: bool = False) -> Dict[str, Any]:
        """Convert error to dictionary for JSON serialization"""
        result = {
            'error': {
                'code': self.error_code,
                'message': self.user_message,
                'status_code': self.status_code,
                'timestamp': self.timestamp.isoformat(),
                'request_id': self.request_id
            }
        }
        
        # Include details in debug mode or if explicitly requested
        if include_details or (current_app and current_app.config.get('DEBUG', False)):
            result['error']['details'] = self.details
            result['error']['context'] = self.context
            result['error']['technical_message'] = self.message
        
        if self.retryable:
            result['error']['retryable'] = True
        
        return result


class ValidationError(PipLineError):
    """Exception for validation errors"""
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Any = None,
        validation_type: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details={
                "field": field,
                "value": str(value)[:100] if value is not None else None,  # Limit value length
                "validation_type": validation_type
            },
            user_message=f"Validation error: {message}"
        )


class AuthenticationError(PipLineError):
    """Exception for authentication errors"""
    def __init__(
        self,
        message: str = "Authentication required",
        auth_method: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401,
            details={
                "auth_method": auth_method,
                "ip_address": ip_address
            },
            user_message="Please log in to access this resource."
        )


class AuthorizationError(PipLineError):
    """Exception for authorization errors"""
    def __init__(
        self,
        message: str = "Insufficient permissions",
        resource: Optional[str] = None,
        action: Optional[str] = None,
        user_id: Optional[int] = None
    ):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403,
            details={
                "resource": resource,
                "action": action,
                "user_id": user_id
            },
            user_message="You don't have permission to perform this action."
        )


class ResourceNotFoundError(PipLineError):
    """Exception for resource not found errors"""
    def __init__(
        self,
        resource_type: str,
        resource_id: Any,
        search_criteria: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"{resource_type} with id {resource_id} not found",
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={
                "resource_type": resource_type,
                "resource_id": str(resource_id),
                "search_criteria": search_criteria
            },
            user_message=f"The requested {resource_type.lower()} was not found."
        )


class DatabaseError(PipLineError):
    """Exception for database errors"""
    def __init__(
        self,
        message: str,
        original_error: Optional[Exception] = None,
        operation: Optional[str] = None,
        table: Optional[str] = None,
        retryable: bool = True
    ):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=500,
            details={
                "original_error": str(original_error)[:500] if original_error else None,
                "operation": operation,
                "table": table,
                "error_type": type(original_error).__name__ if original_error else None
            },
            user_message="A database error occurred. Please try again later.",
            retryable=retryable
        )


class RateLimitError(PipLineError):
    """Exception for rate limiting errors"""
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            status_code=429,
            details={"retry_after": retry_after} if retry_after else {},
            user_message="Too many requests. Please try again later.",
            retryable=True
        )


class FileUploadError(PipLineError):
    """Exception for file upload errors"""
    def __init__(self, message: str, file_type: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="FILE_UPLOAD_ERROR",
            status_code=400,
            details={"file_type": file_type},
            user_message=f"File upload error: {message}"
        )


class JSONParsingError(PipLineError):
    """Exception for JSON parsing errors"""
    def __init__(self, message: str, data: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="JSON_PARSING_ERROR",
            status_code=400,
            details={"data_preview": data[:100] if data else None},
            user_message="Data format error. Please try again."
        )


class CSRFError(PipLineError):
    """Exception for CSRF token errors"""
    def __init__(self, message: str = "CSRF token validation failed"):
        super().__init__(
            message=message,
            error_code="CSRF_ERROR",
            status_code=400,
            user_message="Security validation failed. Please refresh the page and try again."
        )


class BusinessLogicError(PipLineError):
    """Exception for business logic errors"""
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="BUSINESS_LOGIC_ERROR",
            status_code=400,
            details={
                "operation": operation,
                "context": context or {}
            },
            user_message=message
        )


def log_error(error: Exception, context: Optional[Dict[str, Any]] = None, include_traceback: bool = True) -> None:
    """
    Log error with context information and correlation ID
    Combines features from all error handler implementations
    """
    error_context: Dict[str, Any] = context or {}
    
    # Add request context if available
    if request:
        error_context.update({
            'request_id': _get_request_id(),
            'request_method': request.method,
            'request_url': request.url,
            'request_path': request.path,
            'request_ip': request.remote_addr,
            'request_user_agent': request.headers.get('User-Agent', 'Unknown'),
            'request_referrer': request.headers.get('Referer'),
            'request_content_type': request.headers.get('Content-Type'),
            'request_content_length': request.content_length,
        })
        
        # Add user information if available
        if hasattr(g, 'user_id'):
            error_context['user_id'] = g.user_id
        elif hasattr(request, 'user_id'):
            error_context['user_id'] = request.user_id
        
        # Add form data (sanitized - exclude sensitive fields)
        if request.form:
            sanitized_form = {
                k: v for k, v in request.form.items()
                if k not in ['password', 'csrf_token', 'token', 'secret_key', 'api_key']
            }
            error_context['form_data'] = sanitized_form
        
        # Add query parameters
        if request.args:
            error_context['query_params'] = dict(request.args)
    
    # Add error-specific information
    if isinstance(error, PipLineError):
        error_context.update({
            'error_code': error.error_code,
            'error_details': error.details,
            'error_context': error.context,
            'retryable': error.retryable
        })
    
    # Add system information
    try:
        import psutil
        process = psutil.Process()
        error_context['system_info'] = {
            'memory_usage_mb': process.memory_info().rss / (1024 * 1024),
            'cpu_percent': process.cpu_percent(interval=0.1),
            'memory_percent': process.memory_percent(),
            'thread_count': process.num_threads()
        }
    except Exception:
        pass
    
    # Log with appropriate level
    log = _get_logger()
    if include_traceback:
        log.log_exception(error, error_context, include_traceback=True)
    else:
        log.error(f"{type(error).__name__}: {str(error)}", extra_data=error_context)


def handle_database_error(error: SQLAlchemyError, operation: str = "database operation") -> DatabaseError:
    """Handle database errors and return appropriate PipLineError"""
    error_details: Dict[str, Any] = {
        'operation': operation,
        'error_type': type(error).__name__,
        'error_message': str(error)
    }
    
    # Add specific details for different database error types
    if isinstance(error, IntegrityError):
        error_details['integrity_error'] = {
            'sql': getattr(error, 'statement', getattr(error, 'sql', 'Unknown')),
            'params': getattr(error, 'params', 'Unknown')
        }
        retryable = False  # Integrity errors are usually not retryable
    elif isinstance(error, OperationalError):
        error_details['operational_error'] = {
            'sql': getattr(error, 'statement', getattr(error, 'sql', 'Unknown')),
            'params': getattr(error, 'params', 'Unknown')
        }
        retryable = True  # Connection errors might be retryable
    else:
        retryable = True
    
    # Log the database error
    _get_logger().log_exception(error, error_details)
    
    return DatabaseError(
        message=f"Database error during {operation}: {str(error)}",
        original_error=error,
        operation=operation,
        retryable=retryable
    )


def handle_validation_error(error: Exception, field: Optional[str] = None) -> ValidationError:
    """Handle validation errors and return ValidationError"""
    if isinstance(error, InvalidOperation):
        return ValidationError(
            "Invalid numeric value provided",
            field=field,
            value=getattr(error, 'value', None),
            validation_type="numeric"
        )
    elif isinstance(error, ValueError):
        return ValidationError(
            str(error),
            field=field,
            validation_type="value"
        )
    else:
        return ValidationError(
            str(error),
            field=field,
            validation_type="generic"
        )


def create_error_response(
    error: PipLineError,
    request_format: Optional[str] = None
) -> Tuple[Union[str, Dict], int]:
    """
    Create appropriate error response based on request format
    Maintains backward compatibility with existing code
    """
    if not request_format and request:
        # Auto-detect format
        if request.path.startswith('/api/'):
            request_format = 'json'
        else:
            request_format = 'json' if request.headers.get('Accept') == 'application/json' else 'html'
    elif not request_format:
        request_format = 'json'
    
    error_dict = error.to_dict(
        include_details=(current_app and current_app.config.get('DEBUG', False))
    )
    
    if request_format == 'json':
        return jsonify(error_dict), error.status_code
    else:
        # For HTML requests, still return JSON (SPA pattern)
        return jsonify(error_dict), error.status_code


def handle_api_error(error: Exception) -> Tuple[Dict, int]:
    """Handle errors for API routes and return JSON response"""
    if isinstance(error, PipLineError):
        log_error(error, {'api_request': True})
        return create_error_response(error, 'json')
    else:
        # Convert unexpected errors to PipLineError
        pipeline_error = PipLineError(
            str(error),
            error_code="API_ERROR",
            status_code=500
        )
        log_error(pipeline_error, {'api_request': True})
        return create_error_response(pipeline_error, 'json')


def handle_web_error(error: Exception) -> Tuple[Dict, int]:
    """Handle errors for web routes and return HTML/JSON response"""
    if isinstance(error, PipLineError):
        log_error(error, {'web_request': True})
        return create_error_response(error, 'html')
    else:
        # Convert unexpected errors to PipLineError
        pipeline_error = PipLineError(
            str(error),
            error_code="WEB_ERROR",
            status_code=500
        )
        log_error(pipeline_error, {'web_request': True})
        return create_error_response(pipeline_error, 'html')


def safe_execute(func, *args, **kwargs):
    """Safely execute a function with comprehensive error handling"""
    try:
        return func(*args, **kwargs)
    except PipLineError:
        # Re-raise PipLineError as-is
        raise
    except SQLAlchemyError as e:
        # Handle database errors
        db_error = handle_database_error(e, f"function {func.__name__}")
        log_error(db_error, {"function": func.__name__})
        raise db_error
    except ValidationError as e:
        # Re-raise validation errors
        log_error(e, {"function": func.__name__})
        raise e
    except Exception as e:
        # Handle unexpected errors
        unexpected_error = PipLineError(
            f"Unexpected error in {func.__name__}: {str(e)}",
            error_code="UNEXPECTED_ERROR",
            status_code=500
        )
        log_error(unexpected_error, {"function": func.__name__, "original_error": str(e)})
        raise unexpected_error


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """Validate that required fields are present and not empty"""
    missing_fields = []
    
    for field in required_fields:
        if field not in data or data[field] is None or str(data[field]).strip() == '':
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationError(
            f"Missing required fields: {', '.join(missing_fields)}",
            field="required_fields",
            value=missing_fields,
            validation_type="missing_required"
        )


def validate_numeric_field(
    value: Any,
    field_name: str,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None
) -> float:
    """Validate and convert numeric field"""
    try:
        numeric_value = float(value)
        
        if min_value is not None and numeric_value < min_value:
            raise ValidationError(
                f"{field_name} must be at least {min_value}",
                field=field_name,
                value=numeric_value,
                validation_type="below_minimum"
            )
        
        if max_value is not None and numeric_value > max_value:
            raise ValidationError(
                f"{field_name} must be at most {max_value}",
                field=field_name,
                value=numeric_value,
                validation_type="above_maximum"
            )
        
        return numeric_value
    except (ValueError, TypeError):
        raise ValidationError(
            f"{field_name} must be a valid number",
            field=field_name,
            value=value,
            validation_type="invalid_type"
        )


def validate_date_field(date_string: str, field_name: str) -> datetime:
    """Validate and parse date field"""
    try:
        from datetime import datetime
        return datetime.strptime(date_string, '%Y-%m-%d')
    except ValueError:
        raise ValidationError(
            f"{field_name} must be a valid date in YYYY-MM-DD format",
            field=field_name,
            value=date_string,
            validation_type="invalid_date_format"
        )


# Route decorators for consistent error handling
def handle_errors(f):
    """Decorator to handle errors in web routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except PipLineError as e:
            log_error(e, {"route": f.__name__})
            return handle_web_error(e)
        except Exception as e:
            # Check if it's a CSRF error
            if "CSRF" in str(e) or "csrf" in str(e).lower():
                csrf_error = CSRFError(str(e))
                log_error(csrf_error, {"route": f.__name__, "original_error": str(e)})
                return handle_web_error(csrf_error)
            
            pipeline_error = PipLineError(
                f"Unexpected error in {f.__name__}: {str(e)}",
                error_code="ROUTE_ERROR",
                status_code=500
            )
            log_error(pipeline_error, {"route": f.__name__, "original_error": str(e)})
            return handle_web_error(pipeline_error)
    return decorated_function


def handle_api_errors(f):
    """Decorator to handle errors in API routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except PipLineError as e:
            log_error(e, {"api_route": f.__name__})
            return handle_api_error(e)
        except Exception as e:
            # Check if it's a CSRF error
            if "CSRF" in str(e) or "csrf" in str(e).lower():
                csrf_error = CSRFError(str(e))
                log_error(csrf_error, {"api_route": f.__name__, "original_error": str(e)})
                return handle_api_error(csrf_error)
            
            pipeline_error = PipLineError(
                f"Unexpected error in API {f.__name__}: {str(e)}",
                error_code="API_ROUTE_ERROR",
                status_code=500
            )
            log_error(pipeline_error, {"api_route": f.__name__, "original_error": str(e)})
            return handle_api_error(pipeline_error)
    return decorated_function


def validate_request_data(required_fields: Optional[List[str]] = None, optional_fields: Optional[List[str]] = None):
    """Decorator to validate request data"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get request data
                if request.method == 'GET':
                    data = request.args.to_dict()
                else:
                    data = request.get_json() or request.form.to_dict()
                
                # Validate required fields
                if required_fields:
                    validate_required_fields(data, required_fields)
                
                # Store validated data in request for use in route
                request.validated_data = data
                
                return f(*args, **kwargs)
            except ValidationError as e:
                log_error(e, {"route": f.__name__})
                if request.headers.get('Accept') == 'application/json':
                    return handle_api_error(e)
                else:
                    return handle_web_error(e)
        return decorated_function
    return decorator


def require_permissions(*permissions):
    """Decorator to check user permissions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                from flask_login import current_user
                
                if not current_user.is_authenticated:
                    raise AuthenticationError("Login required")
                
                # Check if user has required permissions
                user_permissions = getattr(current_user, 'permissions', [])
                if not all(perm in user_permissions for perm in permissions):
                    raise AuthorizationError(
                        f"Insufficient permissions. Required: {', '.join(permissions)}",
                        resource=f.__name__,
                        action="execute",
                        user_id=current_user.id if hasattr(current_user, 'id') else None
                    )
                
                return f(*args, **kwargs)
            except (AuthenticationError, AuthorizationError) as e:
                log_error(e, {"route": f.__name__})
                if request.headers.get('Accept') == 'application/json':
                    return handle_api_error(e)
                else:
                    return handle_web_error(e)
        return decorated_function
    return decorator


# Backward compatibility aliases
# These ensure existing code continues to work
EnhancedPipLineError = PipLineError
EnhancedValidationError = ValidationError
EnhancedAuthenticationError = AuthenticationError
EnhancedAuthorizationError = AuthorizationError
EnhancedResourceNotFoundError = ResourceNotFoundError
EnhancedDatabaseError = DatabaseError

