"""
Enhanced Cache Service for PipLinePro
Advanced Redis-based caching with intelligent invalidation and warming
"""
import json
import logging
import time
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union, Callable
from functools import wraps
import redis
from flask import current_app
from app.services.event_service import event_service, EventType

logger = logging.getLogger(__name__)

class CacheKey:
    """Cache key builder with namespacing"""
    
    @staticmethod
    def transaction_list(filters: Dict[str, Any] = None, page: int = 1, per_page: int = 50) -> str:
        """Generate cache key for transaction list"""
        key_data = {
            'type': 'transaction_list',
            'filters': filters or {},
            'page': page,
            'per_page': per_page
        }
        return f"pipeline:transactions:{hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()}"
    
    @staticmethod
    def transaction_detail(transaction_id: int) -> str:
        """Generate cache key for transaction detail"""
        return f"pipeline:transaction:{transaction_id}"
    
    @staticmethod
    def psp_summary(date: str = None) -> str:
        """Generate cache key for PSP summary"""
        date_key = date or datetime.now().strftime('%Y-%m-%d')
        return f"pipeline:psp_summary:{date_key}"
    
    @staticmethod
    def daily_balance(date: str, psp: str = None) -> str:
        """Generate cache key for daily balance"""
        if psp:
            return f"pipeline:daily_balance:{date}:{psp}"
        return f"pipeline:daily_balance:{date}"
    
    @staticmethod
    def analytics_dashboard(user_id: int = None) -> str:
        """Generate cache key for analytics dashboard"""
        if user_id:
            return f"pipeline:analytics:dashboard:{user_id}"
        return "pipeline:analytics:dashboard:global"
    
    @staticmethod
    def exchange_rate(currency: str, date: str = None) -> str:
        """Generate cache key for exchange rate"""
        date_key = date or datetime.now().strftime('%Y-%m-%d')
        return f"pipeline:exchange_rate:{currency}:{date_key}"
    
    @staticmethod
    def user_session(user_id: int) -> str:
        """Generate cache key for user session"""
        return f"pipeline:session:{user_id}"

class CacheStats:
    """Cache statistics tracking"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.invalidations = 0
        self.warm_ups = 0
    
    def hit_rate(self) -> float:
        """Calculate hit rate percentage"""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'sets': self.sets,
            'deletes': self.deletes,
            'invalidations': self.invalidations,
            'warm_ups': self.warm_ups,
            'hit_rate': self.hit_rate()
        }

class EnhancedCacheService:
    """Enhanced caching service with Redis backend and in-memory fallback"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self._redis_client = redis_client
        self._redis_initialized = False
        self.stats = CacheStats()
        self.default_ttl = 3600  # 1 hour
        self.namespace = "pipeline"
        
        # In-memory cache fallback when Redis is not available
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        
        # Cache warming strategies
        self.warming_strategies: Dict[str, Callable] = {}
        
        # Register cache warming strategies
        self._register_warming_strategies()
    
    @property
    def redis_client(self) -> Optional[redis.Redis]:
        """Lazy initialization of Redis client"""
        if not self._redis_initialized:
            self._redis_client = self._get_redis_client()
            self._redis_initialized = True
        return self._redis_client
    
    def _get_redis_client(self) -> Optional[redis.Redis]:
        """Get Redis client"""
        try:
            from flask import has_app_context
            if not has_app_context():
                return None
            
            redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
            redis_enabled = current_app.config.get('REDIS_ENABLED', False)
            if isinstance(redis_enabled, str):
                redis_enabled = redis_enabled.lower() == 'true'
            
            if not redis_enabled:
                return None
                
            return redis.from_url(redis_url, decode_responses=True)
        except Exception as e:
            logger.debug(f"Redis not available: {e}")
            return None
    
    def _register_warming_strategies(self):
        """Register cache warming strategies"""
        self.warming_strategies = {
            'transaction_list': self._warm_transaction_list,
            'psp_summary': self._warm_psp_summary,
            'analytics_dashboard': self._warm_analytics_dashboard,
            'exchange_rates': self._warm_exchange_rates
        }
    
    def _clean_expired_memory_cache(self):
        """Clean expired entries from memory cache"""
        current_time = time.time()
        expired_keys = [
            key for key, data in self._memory_cache.items()
            if data.get('expires_at', 0) < current_time
        ]
        for key in expired_keys:
            del self._memory_cache[key]
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (Redis with memory fallback)"""
        # Try Redis first
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value is not None:
                    self.stats.hits += 1
                    return json.loads(value)
            except Exception as e:
                logger.debug(f"Redis get error, falling back to memory: {e}")
        
        # Fallback to memory cache
        self._clean_expired_memory_cache()
        if key in self._memory_cache:
            cache_data = self._memory_cache[key]
            if cache_data.get('expires_at', 0) > time.time():
                self.stats.hits += 1
                return cache_data.get('value')
        
        self.stats.misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache (Redis with memory fallback)"""
        ttl = ttl or self.default_ttl
        
        # Try Redis first
        if self.redis_client:
            try:
                serialized_value = json.dumps(value, default=str)
                result = self.redis_client.setex(key, ttl, serialized_value)
                if result:
                    self.stats.sets += 1
                return result
            except Exception as e:
                logger.debug(f"Redis set error, falling back to memory: {e}")
        
        # Fallback to memory cache
        try:
            self._memory_cache[key] = {
                'value': value,
                'expires_at': time.time() + ttl
            }
            self.stats.sets += 1
            return True
        except Exception as e:
            logger.error(f"Error setting memory cache key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache (Redis with memory fallback)"""
        deleted = False
        
        # Try Redis first
        if self.redis_client:
            try:
                result = self.redis_client.delete(key)
                if result:
                    self.stats.deletes += 1
                    deleted = True
            except Exception as e:
                logger.debug(f"Redis delete error: {e}")
        
        # Also delete from memory cache
        if key in self._memory_cache:
            del self._memory_cache[key]
            if not deleted:
                self.stats.deletes += 1
            deleted = True
        
        return deleted
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        if not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                self.stats.invalidations += len(keys)
                
                # Publish invalidation event
                event_service.publish_event(
                    EventType.CACHE_INVALIDATED,
                    {'pattern': pattern, 'keys_count': len(keys)},
                    source='cache_service'
                )
                
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Error invalidating pattern {pattern}: {e}")
            return 0
    
    def invalidate_transaction_cache(self, transaction_id: Optional[int] = None):
        """Invalidate transaction-related cache"""
        patterns = [
            "pipeline:transactions:*",
            "pipeline:psp_summary:*",
            "pipeline:daily_balance:*",
            "pipeline:analytics:*"
        ]
        
        if transaction_id:
            patterns.append(f"pipeline:transaction:{transaction_id}")
        
        total_invalidated = 0
        for pattern in patterns:
            total_invalidated += self.invalidate_pattern(pattern)
        
        # Removed verbose cache invalidation logging - only log if errors occur
        return total_invalidated
    
    def warm_cache(self, strategy: str, **kwargs) -> bool:
        """Warm cache using specified strategy"""
        if strategy not in self.warming_strategies:
            logger.error(f"Unknown warming strategy: {strategy}")
            return False
        
        try:
            self.warming_strategies[strategy](**kwargs)
            self.stats.warm_ups += 1
            return True
        except Exception as e:
            logger.error(f"Error warming cache with strategy {strategy}: {e}")
            return False
    
    def _warm_transaction_list(self, **kwargs):
        """Warm transaction list cache"""
        from app.services.query_service import QueryService
        
        # Warm common transaction queries
        common_filters = [
            {},
            {'category': 'DEP'},
            {'category': 'WD'},
            {'psp': kwargs.get('psp')} if kwargs.get('psp') else None
        ]
        
        for filters in common_filters:
            if filters is None:
                continue
                
            for page in [1, 2]:  # Warm first 2 pages
                key = CacheKey.transaction_list(filters, page, 50)
                if not self.get(key):
                    transactions = QueryService.get_transactions_by_date_range(
                        start_date=kwargs.get('start_date'),
                        end_date=kwargs.get('end_date'),
                        page=page,
                        per_page=50,
                        filters=filters
                    )
                    self.set(key, transactions, ttl=1800)  # 30 minutes
    
    def _warm_psp_summary(self, **kwargs):
        """Warm PSP summary cache"""
        from app.services.psp_analytics_service import PspAnalyticsService
        
        # Warm current and recent PSP summaries
        dates = [
            datetime.now().strftime('%Y-%m-%d'),
            (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
            (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        ]
        
        for date in dates:
            key = CacheKey.psp_summary(date)
            if not self.get(key):
                # This would call the actual PSP summary service
                # summary_data = PspAnalyticsService.get_psp_summary(date)
                # self.set(key, summary_data, ttl=3600)
                pass
    
    def _warm_analytics_dashboard(self, **kwargs):
        """Warm analytics dashboard cache"""
        # Warm global and user-specific analytics
        keys = [
            CacheKey.analytics_dashboard(),
            CacheKey.analytics_dashboard(kwargs.get('user_id'))
        ]
        
        for key in keys:
            if not self.get(key):
                # This would call the actual analytics service
                # analytics_data = AnalyticsService.get_dashboard_data()
                # self.set(key, analytics_data, ttl=1800)
                pass
    
    def _warm_exchange_rates(self, **kwargs):
        """Warm exchange rates cache"""
        currencies = ['USD', 'EUR']
        dates = [
            datetime.now().strftime('%Y-%m-%d'),
            (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        ]
        
        for currency in currencies:
            for date in dates:
                key = CacheKey.exchange_rate(currency, date)
                if not self.get(key):
                    # This would call the actual exchange rate service
                    # rate = ExchangeRateService.get_rate(currency, date)
                    # self.set(key, rate, ttl=86400)  # 24 hours
                    pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = self.stats.to_dict()
        
        if self.redis_client:
            try:
                info = self.redis_client.info('memory')
                stats.update({
                    'redis_memory_used': info.get('used_memory_human'),
                    'redis_memory_peak': info.get('used_memory_peak_human'),
                    'redis_keyspace_hits': info.get('keyspace_hits', 0),
                    'redis_keyspace_misses': info.get('keyspace_misses', 0)
                })
            except Exception as e:
                logger.error(f"Error getting Redis info: {e}")
        
        return stats
    
    def clear_all(self) -> bool:
        """Clear all cache"""
        if not self.redis_client:
            return False
        
        try:
            keys = self.redis_client.keys(f"{self.namespace}:*")
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

# Global cache service instance
cache_service = EnhancedCacheService()

# Cache decorator for functions
def cached(ttl: int = 3600, key_func: Optional[Callable] = None):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                key_data = {
                    'func': func.__name__,
                    'args': args,
                    'kwargs': kwargs
                }
                cache_key = f"pipeline:func:{hashlib.md5(json.dumps(key_data, sort_keys=True, default=str).encode()).hexdigest()}"
            
            # Try to get from cache
            result = cache_service.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_service.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator
