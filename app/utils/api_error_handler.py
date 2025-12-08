"""
Unified API Error Handler Decorator
Provides automatic error handling for API endpoints with standardized responses
STANDARDIZED VERSION - Uses unified_error_handler as base
"""
from functools import wraps
from flask import jsonify, request, current_app
from app.utils.api_response import error_response, ErrorCode
from app.utils.unified_logger import get_logger
from app.utils.unified_error_handler import (
    PipLineError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    DatabaseError,
    RateLimitError,
    CSRFError,
    BusinessLogicError,
    log_error,
    handle_api_error
)
from app import db

logger = get_logger('APIErrorHandler')


def handle_api_errors(f):
    """
    STANDARDIZED decorator for unified API error handling.
    
    Automatically handles exceptions and returns standardized error responses.
    Ensures database rollback on errors.
    Uses unified_error_handler for consistent error handling across the application.
    
    Usage:
        @handle_api_errors
        @login_required
        def my_endpoint():
            # Your endpoint code here
            return jsonify(success_response(data=...))
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        
        except ValidationError as e:
            db.session.rollback()
            log_error(e, {"api_route": f.__name__})
            # Use unified error handler's response format
            error_dict = e.to_dict(include_details=current_app.config.get('DEBUG', False))
            return jsonify(error_dict), e.status_code
        
        except AuthenticationError as e:
            db.session.rollback()
            log_error(e, {"api_route": f.__name__})
            error_dict = e.to_dict(include_details=current_app.config.get('DEBUG', False))
            return jsonify(error_dict), e.status_code
        
        except AuthorizationError as e:
            db.session.rollback()
            log_error(e, {"api_route": f.__name__})
            error_dict = e.to_dict(include_details=current_app.config.get('DEBUG', False))
            return jsonify(error_dict), e.status_code
        
        except ResourceNotFoundError as e:
            db.session.rollback()
            log_error(e, {"api_route": f.__name__})
            error_dict = e.to_dict(include_details=current_app.config.get('DEBUG', False))
            return jsonify(error_dict), e.status_code
        
        except DatabaseError as e:
            db.session.rollback()
            log_error(e, {"api_route": f.__name__})
            error_dict = e.to_dict(include_details=current_app.config.get('DEBUG', False))
            return jsonify(error_dict), e.status_code
        
        except RateLimitError as e:
            db.session.rollback()
            log_error(e, {"api_route": f.__name__})
            error_dict = e.to_dict(include_details=current_app.config.get('DEBUG', False))
            # Add Retry-After header if available
            response = jsonify(error_dict)
            if e.details.get('retry_after'):
                response.headers['Retry-After'] = str(e.details['retry_after'])
            return response, e.status_code
        
        except CSRFError as e:
            db.session.rollback()
            log_error(e, {"api_route": f.__name__})
            error_dict = e.to_dict(include_details=current_app.config.get('DEBUG', False))
            return jsonify(error_dict), e.status_code
        
        except BusinessLogicError as e:
            db.session.rollback()
            log_error(e, {"api_route": f.__name__})
            error_dict = e.to_dict(include_details=current_app.config.get('DEBUG', False))
            return jsonify(error_dict), e.status_code
        
        except PipLineError as e:
            db.session.rollback()
            log_error(e, {"api_route": f.__name__})
            error_dict = e.to_dict(include_details=current_app.config.get('DEBUG', False))
            return jsonify(error_dict), e.status_code
        
        except ValueError as e:
            db.session.rollback()
            # Convert ValueError to ValidationError
            validation_error = ValidationError(
                str(e),
                validation_type="value"
            )
            log_error(validation_error, {"api_route": f.__name__, "original_error": str(e)})
            error_dict = validation_error.to_dict(include_details=current_app.config.get('DEBUG', False))
            return jsonify(error_dict), validation_error.status_code
        
        except Exception as e:
            db.session.rollback()
            # Log full error details for debugging
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"Unexpected error in {f.__name__}: {str(e)}")
            logger.error(f"Traceback: {error_traceback}")
            
            # Check if it's a CSRF error
            if "CSRF" in str(e) or "csrf" in str(e).lower():
                csrf_error = CSRFError(str(e))
                log_error(csrf_error, {"api_route": f.__name__, "original_error": str(e), "traceback": error_traceback})
                error_dict = csrf_error.to_dict(include_details=current_app.config.get('DEBUG', False))
                return jsonify(error_dict), csrf_error.status_code
            
            # Convert to PipLineError with more details in DEBUG mode
            error_message = f"Unexpected error in API {f.__name__}: {str(e)}"
            if current_app.config.get('DEBUG', False):
                error_message += f"\nTraceback: {error_traceback}"
            
            pipeline_error = PipLineError(
                error_message,
                error_code="API_ROUTE_ERROR",
                status_code=500
            )
            log_error(pipeline_error, {"api_route": f.__name__, "original_error": str(e), "traceback": error_traceback})
            error_dict = pipeline_error.to_dict(include_details=current_app.config.get('DEBUG', False))
            return jsonify(error_dict), pipeline_error.status_code
    
    return decorated_function

