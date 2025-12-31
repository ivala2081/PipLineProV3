"""
CSRF Token Service
Provides token-based CSRF protection for API endpoints
"""
import hmac
import hashlib
import time
from typing import Optional
from flask import request, session, current_app
from app.utils.unified_logger import get_logger

logger = get_logger(__name__)


class CSRFTokenService:
    """
    Service for generating and validating CSRF tokens
    """
    
    @staticmethod
    def generate_token(user_id: Optional[int] = None) -> str:
        """
        Generate a CSRF token
        
        Args:
            user_id: Optional user ID for user-specific tokens
        
        Returns:
            CSRF token string
        """
        secret = current_app.config.get('SECRET_KEY', 'default-secret')
        timestamp = str(int(time.time()))
        
        # Include user ID if available
        if user_id:
            data = f"{user_id}:{timestamp}"
        else:
            data = f"anonymous:{timestamp}"
        
        # Generate HMAC token
        token = hmac.new(
            secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return token
    
    @staticmethod
    def validate_token(token: str, user_id: Optional[int] = None, max_age: int = 3600) -> bool:
        """
        Validate a CSRF token
        
        Args:
            token: Token to validate
            user_id: Optional user ID for user-specific validation
            max_age: Maximum age of token in seconds
        
        Returns:
            True if token is valid, False otherwise
        """
        if not token:
            return False
        
        secret = current_app.config.get('SECRET_KEY', 'default-secret')
        current_time = int(time.time())
        
        # Check tokens for the last hour
        for i in range(max_age):
            timestamp = str(current_time - i)
            
            if user_id:
                data = f"{user_id}:{timestamp}"
            else:
                data = f"anonymous:{timestamp}"
            
            expected_token = hmac.new(
                secret.encode(),
                data.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if hmac.compare_digest(token, expected_token):
                return True
        
        return False
    
    @staticmethod
    def get_token_from_request() -> Optional[str]:
        """
        Get CSRF token from request
        
        Checks headers (X-CSRFToken, X-CSRF-Token) and form data
        
        Returns:
            CSRF token or None
        """
        # Check headers first
        token = request.headers.get('X-CSRFToken') or request.headers.get('X-CSRF-Token')
        
        # Check form data
        if not token and request.is_json:
            data = request.get_json(silent=True)
            if data:
                token = data.get('csrf_token') or data.get('_csrf_token')
        
        # Check session
        if not token:
            token = session.get('csrf_token')
        
        return token
    
    @staticmethod
    def require_csrf_token(f):
        """
        Decorator to require CSRF token for API endpoints
        
        Usage:
            @csrf_token_service.require_csrf_token
            @login_required
            def create_transaction():
                ...
        """
        from functools import wraps
        from flask import jsonify
        from flask_login import current_user
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip CSRF for GET, HEAD, OPTIONS
            if request.method in ('GET', 'HEAD', 'OPTIONS'):
                return f(*args, **kwargs)
            
            # Get token from request
            token = CSRFTokenService.get_token_from_request()
            
            if not token:
                return jsonify({
                    'error': 'CSRF token missing',
                    'message': 'CSRF token is required for this request'
                }), 403
            
            # Validate token
            user_id = current_user.id if current_user.is_authenticated else None
            if not CSRFTokenService.validate_token(token, user_id):
                return jsonify({
                    'error': 'CSRF token invalid',
                    'message': 'CSRF token is invalid or expired'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function


# Global CSRF token service instance
csrf_token_service = CSRFTokenService()


def get_csrf_token() -> str:
    """
    Get or generate CSRF token for current session
    
    Returns:
        CSRF token string
    """
    from flask_login import current_user
    
    # Check if token exists in session
    token = session.get('csrf_token')
    if token:
        return token
    
    # Generate new token
    user_id = current_user.id if current_user.is_authenticated else None
    token = csrf_token_service.generate_token(user_id)
    session['csrf_token'] = token
    
    return token

