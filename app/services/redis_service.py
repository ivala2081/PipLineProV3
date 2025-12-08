"""
Redis Service for Advanced Caching and Session Management
"""
import redis
import json
import time
import logging
from typing import Any, Optional, Dict, List
from functools import wraps
from flask import current_app
from app.utils.unified_logger import get_logger

# Get logger instance
logger = logging.getLogger(__name__)

class RedisService:
    """Advanced Redis service for caching, sessions, and background tasks"""
    
    def __init__(self, app=None):
        self.app = app
        self.redis_client = None
        self.connected = False
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0
        }
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize Redis service with Flask app"""
        self.app = app
        
        try:
            # Check REDIS_ENABLED (support both boolean and string)
            redis_enabled = app.config.get('REDIS_ENABLED', False)
            if isinstance(redis_enabled, str):
                redis_enabled = redis_enabled.lower() == 'true'
            
            if redis_enabled:
                # Prefer REDIS_URL if available, otherwise use individual components
                redis_url = app.config.get('REDIS_URL')
                if redis_url:
                    self.redis_client = redis.from_url(
                        redis_url,
                        decode_responses=True,
                        socket_connect_timeout=5,
                        socket_timeout=5,
                        retry_on_timeout=True
                    )
                else:
                    # Fallback to individual config components
                    self.redis_client = redis.Redis(
                        host=app.config.get('REDIS_HOST', 'localhost'),
                        port=app.config.get('REDIS_PORT', 6379),
                        db=app.config.get('REDIS_DB', 0),
                        password=app.config.get('REDIS_PASSWORD'),
                        ssl=app.config.get('REDIS_SSL', False),
                        decode_responses=True,
                        socket_connect_timeout=5,
                        socket_timeout=5,
                        retry_on_timeout=True
                    )
                
                # Test connection
                self.redis_client.ping()
                self.connected = True
                logger.info("✅ Redis service initialized successfully")
                
            else:
                logger.info("⚠️ Redis disabled in configuration")
                
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}")
            self.connected = False
    
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        if not self.connected or not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except:
            self.connected = False
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from Redis cache"""
        if not self.is_connected():
            self.stats['misses'] += 1
            return default
        
        try:
            value = self.redis_client.get(key)
            if value is not None:
                self.stats['hits'] += 1
                return json.loads(value)
            else:
                self.stats['misses'] += 1
                return default
        except Exception as e:
            logging.error(f"Redis get error: {e}")
            self.stats['errors'] += 1
            return default
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in Redis cache"""
        if not self.is_connected():
            return False
        
        try:
            if ttl is None:
                ttl = current_app.config.get('REDIS_CACHE_TTL', 3600)
            
            serialized_value = json.dumps(value)
            result = self.redis_client.setex(key, ttl, serialized_value)
            self.stats['sets'] += 1
            return result
        except Exception as e:
            logging.error(f"Redis set error: {e}")
            self.stats['errors'] += 1
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from Redis cache"""
        if not self.is_connected():
            return False
        
        try:
            result = self.redis_client.delete(key)
            self.stats['deletes'] += 1
            return result > 0
        except Exception as e:
            logging.error(f"Redis delete error: {e}")
            self.stats['errors'] += 1
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        if not self.is_connected():
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logging.error(f"Redis exists error: {e}")
            self.stats['errors'] += 1
            return False
    
    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for key"""
        if not self.is_connected():
            return False
        
        try:
            return bool(self.redis_client.expire(key, ttl))
        except Exception as e:
            logging.error(f"Redis expire error: {e}")
            self.stats['errors'] += 1
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Redis service statistics"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'connected': self.is_connected(),
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'sets': self.stats['sets'],
            'deletes': self.stats['deletes'],
            'errors': self.stats['errors'],
            'total_requests': total_requests,
            'hit_rate': round(hit_rate, 2),
            'error_rate': round((self.stats['errors'] / total_requests * 100) if total_requests > 0 else 0, 2)
        }
    
    def clear_stats(self):
        """Clear statistics"""
        self.stats = {
            'hits': 0, 'misses': 0, 'sets': 0, 'deletes': 0, 'errors': 0
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for Redis service"""
        try:
            if not self.is_connected():
                return {
                    'status': 'disconnected',
                    'message': 'Redis service not available',
                    'timestamp': time.time()
                }
            
            # Test basic operations
            test_key = f"health_check_{int(time.time())}"
            test_value = {'test': True, 'timestamp': time.time()}
            
            # Test set
            set_result = self.set(test_key, test_value, 10)
            if not set_result:
                return {
                    'status': 'error',
                    'message': 'Redis set operation failed',
                    'timestamp': time.time()
                }
            
            # Test get
            retrieved_value = self.get(test_key)
            if retrieved_value != test_value:
                return {
                    'status': 'error',
                    'message': 'Redis get operation failed',
                    'timestamp': time.time()
                }
            
            # Test delete
            delete_result = self.delete(test_key)
            if not delete_result:
                return {
                    'status': 'error',
                    'message': 'Redis delete operation failed',
                    'timestamp': time.time()
                }
            
            return {
                'status': 'healthy',
                'message': 'All Redis operations working correctly',
                'timestamp': time.time(),
                'stats': self.get_stats()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Redis health check failed: {str(e)}',
                'timestamp': time.time()
            }

# Redis cache decorator
def redis_cache(ttl: int = None, key_prefix: str = ''):
    """Decorator for Redis caching"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            args_str = str(args)
            kwargs_str = str(sorted(kwargs.items()))
            combined_str = args_str + kwargs_str
            cache_key = f"{key_prefix}:{func.__name__}:{hash(combined_str)}"
            
            # Try to get from Redis cache
            redis_service = current_app.redis_service if hasattr(current_app, 'redis_service') else None
            
            if redis_service and redis_service.is_connected():
                cached_result = redis_service.get(cache_key)
                if cached_result is not None:
                    return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            
            if redis_service and redis_service.is_connected():
                redis_service.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

# Initialize Redis service
redis_service = RedisService()
