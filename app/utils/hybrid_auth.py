"""
Hybrid Authentication Decorator
Supports both session-based (Flask-Login) and JWT token-based authentication
This provides a fallback when session cookies fail due to CORS or domain issues
"""
from functools import wraps
from flask import request, jsonify, current_app
from flask_login import current_user, login_user
from app.models.user import User
from app.utils.unified_logger import get_logger

logger = get_logger(__name__)

def hybrid_auth_required(f):
    """
    Decorator that allows authentication via either:
    1. Session cookies (Flask-Login) - primary method
    2. JWT tokens (Authorization header) - fallback method
    
    This ensures API endpoints work even if session cookies fail.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First, try JWT token authentication (works even if cookies fail)
        jwt_user = None
        try:
            from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
            
            # Check for JWT token in Authorization header
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                try:
                    verify_jwt_in_request(optional=True)  # Optional - don't fail if no JWT
                    user_id = get_jwt_identity()
                    if user_id:
                        jwt_user = User.query.get(user_id)
                        if jwt_user and jwt_user.is_active:
                            logger.info(f"JWT authentication successful for user {jwt_user.username} on {request.path}")
                            # Set as current_user for Flask-Login compatibility
                            login_user(jwt_user, remember=False)
                            return f(*args, **kwargs)
                except Exception as jwt_error:
                    logger.debug(f"JWT verification failed (expected if no token): {str(jwt_error)}")
        except ImportError:
            logger.debug("JWT not available, using session only")
        except Exception as jwt_check_error:
            logger.debug(f"JWT check error: {str(jwt_check_error)}")
        
        # Fallback to session-based authentication (Flask-Login)
        if not current_user.is_authenticated:
            logger.warning(f"Authentication required for {request.path} - no valid session or JWT token")
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please log in to access this endpoint'
            }), 401
        
        # User is authenticated via session
        logger.debug(f"Session authentication successful for user {current_user.username} on {request.path}")
        return f(*args, **kwargs)
    
    return decorated_function

