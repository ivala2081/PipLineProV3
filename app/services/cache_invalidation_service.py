"""
Cache Invalidation Service
Implements cache tags and invalidation strategy
"""
from typing import Set, List, Dict, Any, Optional
from functools import wraps
from app.services.enhanced_cache_service import cache_service
from app.utils.unified_logger import get_logger

logger = get_logger(__name__)


class CacheTag:
    """Cache tag constants"""
    TRANSACTION = "transaction"
    USER = "user"
    ORGANIZATION = "organization"
    DASHBOARD = "dashboard"
    ANALYTICS = "analytics"
    EXCHANGE_RATE = "exchange_rate"
    PSP = "psp"
    CLIENT = "client"


class CacheInvalidationService:
    """
    Service for managing cache invalidation with tags
    """
    
    def __init__(self):
        self._tag_to_keys: Dict[str, Set[str]] = {}
        self._key_to_tags: Dict[str, Set[str]] = {}
    
    def tag_cache_key(self, key: str, tags: List[str]):
        """
        Tag a cache key with one or more tags
        
        Args:
            key: Cache key
            tags: List of tags to associate with the key
        """
        for tag in tags:
            if tag not in self._tag_to_keys:
                self._tag_to_keys[tag] = set()
            self._tag_to_keys[tag].add(key)
        
        if key not in self._key_to_tags:
            self._key_to_tags[key] = set()
        self._key_to_tags[key].update(tags)
    
    def invalidate_by_tag(self, tag: str) -> int:
        """
        Invalidate all cache keys with a specific tag
        
        Args:
            tag: Tag to invalidate
        
        Returns:
            Number of keys invalidated
        """
        if tag not in self._tag_to_keys:
            return 0
        
        keys_to_invalidate = list(self._tag_to_keys[tag])
        invalidated_count = 0
        
        for key in keys_to_invalidate:
            try:
                cache_service.delete(key)
                invalidated_count += 1
            except Exception as e:
                logger.warning(f"Failed to invalidate cache key {key}: {e}")
        
        # Clean up tag mappings
        del self._tag_to_keys[tag]
        for key in keys_to_invalidate:
            if key in self._key_to_tags:
                self._key_to_tags[key].discard(tag)
                if not self._key_to_tags[key]:
                    del self._key_to_tags[key]
        
        logger.info(f"Invalidated {invalidated_count} cache keys for tag '{tag}'")
        return invalidated_count
    
    def invalidate_by_tags(self, tags: List[str]) -> int:
        """
        Invalidate cache keys with any of the specified tags
        
        Args:
            tags: List of tags to invalidate
        
        Returns:
            Total number of keys invalidated
        """
        total_invalidated = 0
        for tag in tags:
            total_invalidated += self.invalidate_by_tag(tag)
        return total_invalidated
    
    def invalidate_key(self, key: str):
        """
        Invalidate a specific cache key
        
        Args:
            key: Cache key to invalidate
        """
        try:
            cache_service.delete(key)
            # Clean up tag mappings
            if key in self._key_to_tags:
                tags = self._key_to_tags[key].copy()
                for tag in tags:
                    if tag in self._tag_to_keys:
                        self._tag_to_keys[tag].discard(key)
                        if not self._tag_to_keys[tag]:
                            del self._tag_to_keys[tag]
                del self._key_to_tags[key]
        except Exception as e:
            logger.warning(f"Failed to invalidate cache key {key}: {e}")
    
    def get_tagged_keys(self, tag: str) -> Set[str]:
        """
        Get all cache keys with a specific tag
        
        Args:
            tag: Tag to query
        
        Returns:
            Set of cache keys
        """
        return self._tag_to_keys.get(tag, set()).copy()
    
    def get_tags_for_key(self, key: str) -> Set[str]:
        """
        Get all tags for a specific cache key
        
        Args:
            key: Cache key to query
        
        Returns:
            Set of tags
        """
        return self._key_to_tags.get(key, set()).copy()
    
    def clear_all_tags(self):
        """Clear all tag mappings"""
        self._tag_to_keys.clear()
        self._key_to_tags.clear()
        logger.info("All cache tags cleared")


# Global cache invalidation service instance
cache_invalidation_service = CacheInvalidationService()


def cached_with_tags(tags: List[str], ttl: int = 300):
    """
    Decorator to cache function results with tags
    
    Args:
        tags: List of cache tags
        ttl: Time to live in seconds
    
    Usage:
        @cached_with_tags([CacheTag.TRANSACTION, CacheTag.DASHBOARD], ttl=600)
        def get_transactions():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            import hashlib
            import json
            
            key_parts = [func.__name__]
            if args:
                key_parts.append(str(hash(str(args))))
            if kwargs:
                key_parts.append(str(hash(json.dumps(kwargs, sort_keys=True))))
            
            cache_key = f"{func.__module__}:{':'.join(key_parts)}"
            
            # Try to get from cache
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache with tags
            cache_service.set(cache_key, result, ttl=ttl)
            cache_invalidation_service.tag_cache_key(cache_key, tags)
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache_on_change(tags: List[str]):
    """
    Decorator to invalidate cache when a function modifies data
    
    Args:
        tags: Tags to invalidate after function execution
    
    Usage:
        @invalidate_cache_on_change([CacheTag.TRANSACTION])
        def create_transaction():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Execute function
            result = func(*args, **kwargs)
            
            # Invalidate cache tags
            cache_invalidation_service.invalidate_by_tags(tags)
            
            return result
        
        return wrapper
    return decorator

