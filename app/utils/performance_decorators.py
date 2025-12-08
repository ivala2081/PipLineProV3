"""
Performance Decorators
Reusable decorators for performance optimization
"""
import logging
import time
import functools
from typing import Callable, Any, Optional
from flask import g, request
from app.services.enhanced_cache_service import cache_service

logger = logging.getLogger(__name__)


def cache_result(ttl: int = 300, key_func: Optional[Callable] = None):
    """
    Cache function result with TTL
    
    Args:
        ttl: Time to live in seconds
        key_func: Optional function to generate cache key from args
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                import hashlib
                import json
                key_data = {
                    'func': func.__name__,
                    'args': str(args),
                    'kwargs': json.dumps(kwargs, sort_keys=True, default=str)
                }
                cache_key = f"cache:{func.__name__}:{hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()}"
            
            # Try cache
            try:
                cached = cache_service.get(cache_key)
                if cached is not None:
                    logger.debug(f"Cache HIT: {func.__name__}")
                    return cached
            except Exception:
                pass
            
            # Execute and cache
            result = func(*args, **kwargs)
            
            try:
                cache_service.set(cache_key, result, ttl=ttl)
            except Exception:
                pass
            
            return result
        
        return wrapper
    return decorator


def track_performance(threshold: float = 1.0):
    """
    Track function execution time
    
    Args:
        threshold: Time threshold in seconds for warning
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                
                # Track in Flask g
                if not hasattr(g, 'performance_metrics'):
                    g.performance_metrics = []
                
                g.performance_metrics.append({
                    'function': func.__name__,
                    'duration': duration,
                    'slow': duration > threshold
                })
                
                if duration > threshold:
                    logger.warning(f"Slow function: {func.__name__} took {duration:.3f}s")
                
                return result
            except Exception as e:
                duration = time.time() - start
                logger.error(f"Error in {func.__name__} after {duration:.3f}s: {e}")
                raise
        
        return wrapper
    return decorator


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Retry function on failure with exponential backoff
    
    Args:
        max_retries: Maximum number of retries
        delay: Initial delay in seconds
        backoff: Backoff multiplier
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"{func.__name__} failed after {max_retries + 1} attempts")
            
            raise last_exception
        
        return wrapper
    return decorator


def batch_process(batch_size: int = 100):
    """
    Process items in batches
    
    Args:
        batch_size: Number of items per batch
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(items: list, *args, **kwargs):
            results = []
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                batch_results = func(batch, *args, **kwargs)
                results.extend(batch_results if isinstance(batch_results, list) else [batch_results])
            return results
        
        return wrapper
    return decorator

