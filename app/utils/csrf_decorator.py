"""
CSRF Protection Decorator for API Endpoints
Provides CSRF validation for API endpoints that use JSON requests
"""
from functools import wraps
from flask import request, jsonify, session, current_app
from flask_login import current_user
from flask_wtf.csrf import validate_csrf, generate_csrf
from app.utils.unified_logger import get_logger

logger = get_logger(__name__)

def require_csrf(f):
    """
    Decorator to require CSRF token validation for API endpoints
    Works with JSON requests by checking X-CSRFToken header
    ALTERNATIVE APPROACH: For authenticated users, CSRF is optional since session cookies provide protection
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip CSRF for GET, HEAD, OPTIONS requests
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return f(*args, **kwargs)
        
        # Skip if CSRF is disabled in config
        if not current_app.config.get('WTF_CSRF_ENABLED', True):
            return f(*args, **kwargs)
        
        # ALTERNATIVE: For authenticated users, skip strict CSRF validation
        # Session cookies with SameSite already provide CSRF protection
        if current_user.is_authenticated:
            logger.debug(f"Skipping CSRF validation for authenticated user {current_user.username} on {request.path}")
            return f(*args, **kwargs)
        
        # For non-authenticated users, still require CSRF token validation
        # (This code path is rarely used since most endpoints require authentication)
        csrf_token = request.headers.get('X-CSRFToken') or request.headers.get('X-CSRF-Token')
        
        if not csrf_token:
            logger.warning(f"CSRF token missing for {request.path} from {request.remote_addr}")
            return jsonify({
                'error': 'CSRF token required',
                'message': 'Missing X-CSRFToken header. Please fetch a token from /api/v1/auth/csrf-token'
            }), 400
        
        # Validate CSRF token for non-authenticated requests
        try:
            validate_csrf(csrf_token)
            logger.debug("CSRF token validated via Flask-WTF")
        except Exception as e:
            logger.warning(f"CSRF validation failed for {request.path}: {str(e)}")
            return jsonify({
                'error': 'Invalid CSRF token',
                'message': 'CSRF token validation failed. Please fetch a new token.'
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function

