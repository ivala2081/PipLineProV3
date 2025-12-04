"""
Request Tracing Middleware
Adds correlation IDs and request tracing for distributed systems
"""
import uuid
import time
import logging
from functools import wraps
from typing import Callable, Optional
from flask import request, g, current_app
from app.utils.prometheus_metrics import http_request_total, http_request_duration

logger = logging.getLogger(__name__)


def generate_request_id() -> str:
    """Generate unique request ID"""
    return str(uuid.uuid4())


def get_request_id() -> Optional[str]:
    """Get current request ID from Flask g"""
    return getattr(g, 'request_id', None)


def set_request_id(request_id: str):
    """Set request ID in Flask g"""
    g.request_id = request_id
    # Also set in request object for logging
    request.request_id = request_id


def request_tracing_middleware(app):
    """
    Flask middleware for request tracing
    
    Adds:
    - request_id: Unique identifier for each request
    - request_start_time: Request start timestamp
    - request_metrics: Performance metrics
    """
    
    @app.before_request
    def before_request():
        # Generate or get request ID from headers
        request_id = request.headers.get('X-Request-ID') or generate_request_id()
        set_request_id(request_id)
        
        # Store request start time
        g.request_start_time = time.time()
        
        # Initialize request metrics
        g.request_metrics = {
            'query_count': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'slow_queries': [],
        }
        
        # Log request start
        logger.info(
            f"Request started: {request.method} {request.path}",
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.path,
                'remote_addr': request.remote_addr,
            }
        )
    
    @app.after_request
    def after_request(response):
        # Calculate request duration
        if hasattr(g, 'request_start_time'):
            duration = time.time() - g.request_start_time
            
            # Add request ID to response headers
            request_id = get_request_id()
            if request_id:
                response.headers['X-Request-ID'] = request_id
            
            # Record Prometheus metrics
            try:
                endpoint = request.endpoint or 'unknown'
                http_request_total.labels(
                    method=request.method,
                    endpoint=endpoint,
                    status=response.status_code
                ).inc()
                
                http_request_duration.labels(
                    method=request.method,
                    endpoint=endpoint
                ).observe(duration)
            except Exception as e:
                logger.warning(f"Failed to record Prometheus metrics: {e}")
            
            # Log request completion
            log_level = logging.INFO
            if duration > 2.0:  # Slow request
                log_level = logging.WARNING
            
            logger.log(
                log_level,
                f"Request completed: {request.method} {request.path} - {response.status_code} - {duration:.3f}s",
                extra={
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'duration': duration,
                    'query_count': getattr(g, 'request_metrics', {}).get('query_count', 0),
                }
            )
        
        return response
    
    @app.teardown_request
    def teardown_request(exception):
        # Cleanup request-specific data
        if hasattr(g, 'request_id'):
            delattr(g, 'request_id')
        if hasattr(g, 'request_start_time'):
            delattr(g, 'request_start_time')
        if hasattr(g, 'request_metrics'):
            delattr(g, 'request_metrics')


def trace_function(func_name: Optional[str] = None):
    """
    Decorator to trace function execution with request ID
    
    Args:
        func_name: Optional function name override
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            request_id = get_request_id()
            func_name_actual = func_name or func.__name__
            
            start_time = time.time()
            logger.debug(
                f"Function call: {func_name_actual}",
                extra={'request_id': request_id, 'function': func_name_actual}
            )
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                if duration > 1.0:  # Slow function
                    logger.warning(
                        f"Slow function: {func_name_actual} took {duration:.3f}s",
                        extra={
                            'request_id': request_id,
                            'function': func_name_actual,
                            'duration': duration
                        }
                    )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Function error: {func_name_actual} failed after {duration:.3f}s: {e}",
                    extra={
                        'request_id': request_id,
                        'function': func_name_actual,
                        'duration': duration,
                        'error': str(e)
                    },
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator

