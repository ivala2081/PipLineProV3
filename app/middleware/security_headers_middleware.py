"""
Security Headers Middleware for PipLinePro
Adds important security headers to all HTTP responses
Uses configuration from config.py SECURITY_HEADERS for production settings
"""
from flask import request, current_app
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to all responses.
    
    This prevents common web vulnerabilities like:
    - Clickjacking (X-Frame-Options)
    - MIME sniffing (X-Content-Type-Options)
    - XSS (X-XSS-Protection)
    - Information leakage (X-Powered-By removal)
    - HTTPS enforcement (HSTS)
    - Content Security Policy (CSP)
    """
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the middleware with the Flask app"""
        app.after_request(self.add_security_headers)
        logger.info("Security headers middleware initialized")
    
    @staticmethod
    def add_security_headers(response):
        """
        Add security headers to the response.
        Uses SECURITY_HEADERS from config if available, otherwise uses sensible defaults.
        
        Headers added:
        - X-Frame-Options: Prevents clickjacking attacks
        - X-Content-Type-Options: Prevents MIME sniffing
        - X-XSS-Protection: Enables browser XSS protection
        - Strict-Transport-Security: Forces HTTPS (in production)
        - Content-Security-Policy: Controls what resources can be loaded
        - Referrer-Policy: Controls referrer information
        """
        try:
            # Get security headers from config (if available)
            security_headers = current_app.config.get('SECURITY_HEADERS', {})
            is_production = not current_app.config.get('DEBUG', False)
            
            # Use configured headers if available, otherwise use defaults
            # Only add headers that aren't already set
            
            # X-Frame-Options: Prevent clickjacking
            if 'X-Frame-Options' not in response.headers:
                response.headers['X-Frame-Options'] = security_headers.get(
                    'X-Frame-Options', 
                    'DENY' if is_production else 'SAMEORIGIN'
                )
            
            # X-Content-Type-Options: Prevent MIME sniffing
            if 'X-Content-Type-Options' not in response.headers:
                response.headers['X-Content-Type-Options'] = security_headers.get(
                    'X-Content-Type-Options',
                    'nosniff'
                )
            
            # X-XSS-Protection: Enable browser XSS protection
            if 'X-XSS-Protection' not in response.headers:
                response.headers['X-XSS-Protection'] = security_headers.get(
                    'X-XSS-Protection',
                    '1; mode=block'
                )
            
            # Referrer-Policy: Control referrer information
            if 'Referrer-Policy' not in response.headers:
                response.headers['Referrer-Policy'] = security_headers.get(
                    'Referrer-Policy',
                    'strict-origin-when-cross-origin'
                )
            
            # Permissions-Policy: Restrict browser features
            if 'Permissions-Policy' not in response.headers:
                response.headers['Permissions-Policy'] = security_headers.get(
                    'Permissions-Policy',
                    'geolocation=(), microphone=(), camera=()'
                )
            
            # Content-Security-Policy: Control resource loading
            if 'Content-Security-Policy' not in response.headers:
                csp = security_headers.get('Content-Security-Policy')
                if csp:
                    response.headers['Content-Security-Policy'] = csp
                elif is_production:
                    # Production default - more restrictive
                    response.headers['Content-Security-Policy'] = (
                        "default-src 'self'; "
                        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdn.socket.io; "
                        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                        "font-src 'self' https://fonts.gstatic.com; "
                        "img-src 'self' data:; "
                        "connect-src 'self' http://127.0.0.1:7242 https://cdn.socket.io; "
                        "frame-ancestors 'none'"
                    )
                else:
                    # Development default - more permissive (includes debug logging endpoint)
                    response.headers['Content-Security-Policy'] = (
                        "default-src 'self'; "
                        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                        "font-src 'self' https://fonts.gstatic.com; "
                        "img-src 'self' data: https:; "
                        "connect-src 'self' http://127.0.0.1:7242 https://query1.finance.yahoo.com; "
                        "frame-ancestors 'self'"
                    )
            
            # Strict-Transport-Security: Force HTTPS (only in production)
            if is_production and 'Strict-Transport-Security' not in response.headers:
                hsts = security_headers.get('Strict-Transport-Security')
                if hsts:
                    response.headers['Strict-Transport-Security'] = hsts
                else:
                    # Default HSTS: 1 year, include subdomains
                    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
            
            # Additional security headers from config
            additional_headers = [
                'X-Permitted-Cross-Domain-Policies',
                'X-Download-Options',
                'X-DNS-Prefetch-Control',
                'Cache-Control',
                'Pragma',
                'Expires'
            ]
            for header in additional_headers:
                if header not in response.headers and header in security_headers:
                    response.headers[header] = security_headers[header]
            
            # Remove server information disclosure
            response.headers.pop('Server', None)
            response.headers.pop('X-Powered-By', None)
            
        except RuntimeError:
            # Outside request context (during testing) - skip headers
            pass
        except Exception as e:
            logger.warning(f"Error setting security headers: {e}")
        
        # Add custom security header to identify our security middleware
        response.headers['X-Security-Headers'] = 'enabled'
        
        return response


def create_security_middleware(app):
    """
    Factory function to create and initialize security middleware.
    
    Args:
        app: Flask application instance
    
    Returns:
        SecurityHeadersMiddleware: Initialized middleware instance
    """
    middleware = SecurityHeadersMiddleware(app)
    logger.info("Security headers middleware created and initialized")
    return middleware

