"""
Response Optimization Utilities
Provides compression, caching headers, and response optimization
"""
import gzip
import json
import time
from typing import Any, Dict, Optional
from flask import Response, request, jsonify
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class ResponseOptimizer:
    """Advanced response optimization"""
    
    def __init__(self):
        self.compression_threshold = 1024  # Compress responses > 1KB
        self.cache_headers = {
            'analytics': 'public, max-age=300',  # 5 minutes
            'dashboard': 'public, max-age=180',  # 3 minutes
            'system': 'public, max-age=60',      # 1 minute
            'static': 'public, max-age=3600',    # 1 hour
        }
    
    def compress_response(self, data: Any, content_type: str = 'application/json') -> Response:
        """Compress response data if beneficial"""
        # Convert to JSON if needed
        if not isinstance(data, (str, bytes)):
            json_data = json.dumps(data, default=str)
        else:
            json_data = data
        
        # Check if compression is beneficial
        if len(json_data.encode('utf-8')) < self.compression_threshold:
            return Response(
                json_data,
                mimetype=content_type,
                headers={'Content-Length': str(len(json_data.encode('utf-8')))}
            )
        
        # Compress the data
        compressed_data = gzip.compress(json_data.encode('utf-8'))
        
        return Response(
            compressed_data,
            mimetype=content_type,
            headers={
                'Content-Encoding': 'gzip',
                'Content-Length': str(len(compressed_data)),
                'Vary': 'Accept-Encoding'
            }
        )
    
    def add_cache_headers(self, response: Response, cache_type: str = 'default') -> Response:
        """Add appropriate cache headers to response"""
        cache_header = self.cache_headers.get(cache_type, 'no-cache')
        
        # Add cache headers
        response.headers['Cache-Control'] = cache_header
        response.headers['ETag'] = f'"{int(time.time())}"'
        response.headers['Last-Modified'] = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime())
        
        return response
    
    def optimize_json_response(self, data: Any, cache_type: str = 'default', 
                             compress: bool = True) -> Response:
        """Create optimized JSON response with compression and caching"""
        response = self.compress_response(data) if compress else Response(
            json.dumps(data, default=str),
            mimetype='application/json'
        )
        
        return self.add_cache_headers(response, cache_type)
    
    def handle_conditional_request(self, etag: str = None, last_modified: str = None) -> Optional[Response]:
        """Handle conditional requests (304 Not Modified)"""
        if_none_match = request.headers.get('If-None-Match')
        if_modified_since = request.headers.get('If-Modified-Since')
        
        # Check ETag
        if etag and if_none_match and etag in if_none_match:
            return Response(status=304)
        
        # Check Last-Modified
        if last_modified and if_modified_since:
            try:
                last_modified_time = time.mktime(time.strptime(last_modified, '%a, %d %b %Y %H:%M:%S GMT'))
                if_modified_time = time.mktime(time.strptime(if_modified_since, '%a, %d %b %Y %H:%M:%S GMT'))
                
                if last_modified_time <= if_modified_time:
                    return Response(status=304)
            except ValueError:
                pass  # Invalid date format, continue with normal response
        
        return None

# Global response optimizer instance
response_optimizer = ResponseOptimizer()

def optimized_response(cache_type: str = 'default', compress: bool = True):
    """Decorator for optimized API responses"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                # Execute the function
                result = func(*args, **kwargs)
                
                # Handle conditional requests
                conditional_response = response_optimizer.handle_conditional_request()
                if conditional_response:
                    return conditional_response
                
                # Optimize the response
                if isinstance(result, tuple) and len(result) == 2:
                    # Handle (data, status_code) tuple
                    data, status_code = result
                    response = response_optimizer.optimize_json_response(data, cache_type, compress)
                    response.status_code = status_code
                    return response
                elif hasattr(result, 'json'):
                    # Handle Flask Response object
                    return response_optimizer.add_cache_headers(result, cache_type)
                else:
                    # Handle plain data
                    return response_optimizer.optimize_json_response(result, cache_type, compress)
                    
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"Error in optimized response for {func.__name__}: {e} (took {execution_time:.2f}s)")
                return jsonify({'error': str(e)}), 500
                
        return wrapper
    return decorator

# Export commonly used functions
__all__ = ['ResponseOptimizer', 'response_optimizer', 'optimized_response']
