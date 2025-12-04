"""
CSRF Token Fix Service for PipLine Pro
Automatically handles CSRF token generation, validation, and error recovery
"""

import secrets
import logging
from typing import Optional, Dict, Any
from flask import current_app, request, session, has_app_context, has_request_context
from flask_wtf.csrf import generate_csrf, validate_csrf
from werkzeug.exceptions import BadRequest

# Decimal/Float type mismatch prevention
from app.services.decimal_float_fix_service import decimal_float_service


from app.utils.unified_logger import get_logger
logger = get_logger(__name__)

class CSRFFixService:
    """Service to handle CSRF token issues automatically"""
    
    def __init__(self):
        self.fallback_tokens = {}
        self.error_count = 0
        self.max_errors = 10
        self._csrf_enabled = True
    
    def generate_safe_csrf_token(self) -> str:
        """Generate a CSRF token with automatic fallback and proper session handling"""
        try:
            # Check if we're in a proper Flask context
            if not has_app_context():
                logger.warning("No Flask app context, using fallback token")
                return self._generate_fallback_token()
            
            # Ensure session is properly initialized
            self._ensure_session_initialized()
            
            # Try to generate a proper CSRF token using Flask-WTF
            token = generate_csrf()
            
            # Validate the token
            if token and len(token) > 10:
                # Store token in session to ensure it's available for validation
                if has_request_context():
                    session['csrf_token'] = token
                    session.modified = True
                    logger.debug("CSRF token stored in session successfully")
                
                logger.debug("CSRF token generated successfully")
                return token
            else:
                logger.warning("Generated CSRF token is invalid, using fallback")
                return self._generate_fallback_token()
                
        except Exception as e:
            logger.error(f"CSRF token generation failed: {str(e)}")
            return self._generate_fallback_token()
    
    def _ensure_session_initialized(self):
        """Ensure session is properly initialized for CSRF"""
        try:
            if has_request_context():
                # Initialize session if needed
                if 'csrf_token' not in session:
                    session['csrf_token'] = None
                    session.modified = True
                    logger.debug("Session initialized for CSRF")
                
                # Ensure session is marked as modified
                if not session.modified:
                    session.modified = True
                
                # Force session to be saved
                session.permanent = True
                session.modified = True
                    
        except Exception as e:
            logger.error(f"Failed to initialize session for CSRF: {str(e)}")
    
    def _generate_fallback_token(self) -> str:
        """Generate a fallback token when CSRF generation fails"""
        try:
            # Generate a cryptographically secure token
            token = secrets.token_urlsafe(32)
            
            # Only try to store in session if we have request context
            if has_request_context():
                if 'fallback_csrf_tokens' not in session:
                    session['fallback_csrf_tokens'] = {}
                
                session['fallback_csrf_tokens'][token] = True
                session.modified = True
                
                # Clean up old tokens (keep only last 10)
                tokens = list(session['fallback_csrf_tokens'].keys())
                if len(tokens) > 10:
                    for old_token in tokens[:-10]:
                        del session['fallback_csrf_tokens'][old_token]
            
            logger.info("Fallback CSRF token generated")
            return token
            
        except Exception as e:
            logger.error(f"Fallback token generation failed: {str(e)}")
            # Last resort: simple token
            return f"fallback_{secrets.token_hex(16)}"
    
    def validate_csrf_token(self, token: str) -> bool:
        """Validate CSRF token with fallback support"""
        if not token:
            return False
        
        try:
            # Try standard CSRF validation if we have proper context
            if has_app_context():
                validate_csrf(token)
                return True
            else:
                # Fall back to session validation
                return self._validate_fallback_token(token)
            
        except Exception as e:
            logger.debug(f"Standard CSRF validation failed: {str(e)}")
            
            # Try fallback validation
            return self._validate_fallback_token(token)
    
    def _validate_fallback_token(self, token: str) -> bool:
        """Validate fallback CSRF token"""
        try:
            if has_request_context() and 'fallback_csrf_tokens' in session:
                return token in session['fallback_csrf_tokens']
            return False
        except Exception as e:
            logger.error(f"Fallback token validation failed: {str(e)}")
            return False
    
    def get_csrf_token_for_template(self) -> str:
        """Get CSRF token for use in templates"""
        return self.generate_safe_csrf_token()
    
    def inject_csrf_headers(self, response) -> Any:
        """Inject CSRF headers into response"""
        try:
            token = self.generate_safe_csrf_token()
            response.headers['X-CSRF-Token'] = token
            return response
        except Exception as e:
            logger.error(f"Failed to inject CSRF headers: {str(e)}")
            return response
    
    def handle_csrf_error(self, error: Exception) -> Dict[str, Any]:
        """Handle CSRF errors gracefully"""
        self.error_count += 1
        
        if self.error_count > self.max_errors:
            logger.critical(f"Too many CSRF errors ({self.error_count}), disabling CSRF temporarily")
            self._csrf_enabled = False
            return {
                'error': 'CSRF protection temporarily disabled',
                'token': self._generate_fallback_token(),
                'disabled': True
            }
        
        logger.warning(f"CSRF error handled: {str(error)}")
        return {
            'error': 'CSRF validation failed',
            'token': self.generate_safe_csrf_token(),
            'disabled': False
        }
    
    def is_csrf_enabled(self) -> bool:
        """Check if CSRF protection is enabled"""
        return self._csrf_enabled
    
    def reset_error_count(self):
        """Reset error count to re-enable CSRF protection"""
        self.error_count = 0
        self._csrf_enabled = True
        logger.info("CSRF error count reset, protection re-enabled")

# Global instance
csrf_fix_service = CSRFFixService()

def get_csrf_token():
    """Global function for templates to get CSRF token"""
    return csrf_fix_service.get_csrf_token_for_template()

def validate_csrf_token_safe(token: str) -> bool:
    """Safe CSRF token validation"""
    return csrf_fix_service.validate_csrf_token(token)

def handle_csrf_error_safe(error: Exception) -> Dict[str, Any]:
    """Safe CSRF error handling"""
    return csrf_fix_service.handle_csrf_error(error)

def is_csrf_protection_enabled() -> bool:
    """Check if CSRF protection is currently enabled"""
    return csrf_fix_service.is_csrf_enabled() 