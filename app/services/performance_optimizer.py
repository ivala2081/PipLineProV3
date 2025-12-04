"""
Performance Optimization Service
Provides comprehensive performance optimization including caching, query optimization, and resource management
"""
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import request, current_app, g

from app.utils.unified_logger import get_logger
from app.services.monitoring_service import get_monitoring_service

logger = get_logger("PerformanceOptimizer")


class PerformanceOptimizer:
    """Comprehensive performance optimization service"""
    
    def __init__(self):
        self.response_times: Dict[str, List[float]] = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.query_optimizations = 0
    
    def track_response_time(self, endpoint: str, duration: float):
        """Track response time for an endpoint"""
        if endpoint not in self.response_times:
            self.response_times[endpoint] = []
        
        self.response_times[endpoint].append(duration)
        
        # Keep only last 1000 measurements
        if len(self.response_times[endpoint]) > 1000:
            self.response_times[endpoint] = self.response_times[endpoint][-1000:]
        
        # Record metric for monitoring
        monitoring_service = get_monitoring_service()
        monitoring_service.record_metric(f'api.response_time.{endpoint}', duration)
        
        # Alert on slow responses
        if duration > 2.0:
            from app.services.monitoring_service import AlertLevel
            monitoring_service.create_alert(
                "Slow API Response",
                f"Endpoint {endpoint} took {duration:.2f}s to respond",
                AlertLevel.WARNING,
                "performance.api",
                {'endpoint': endpoint, 'duration': duration}
            )
    
    def cache_decorator(self, ttl: int = 300, key_func=None):
        """Decorator for caching function results"""
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = f"{f.__name__}:{str(args)}:{str(kwargs)}"
                
                # Try to get from cache
                try:
                    from app.services.enhanced_cache_service import cache_service
                    cached = cache_service.get(cache_key)
                    if cached is not None:
                        self.cache_hits += 1
                        return cached
                except Exception as e:
                    logger.debug(f"Cache get error: {e}")
                
                # Cache miss - execute function
                self.cache_misses += 1
                result = f(*args, **kwargs)
                
                # Store in cache
                try:
                    from app.services.enhanced_cache_service import cache_service
                    cache_service.set(cache_key, result, ttl=ttl)
                except Exception as e:
                    logger.debug(f"Cache set error: {e}")
                
                return result
            return wrapper
        return decorator
    
    def performance_decorator(self, endpoint: Optional[str] = None):
        """Decorator for tracking endpoint performance"""
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                endpoint_name = endpoint or request.endpoint or f.__name__
                
                try:
                    result = f(*args, **kwargs)
                    
                    # Track response time
                    duration = time.time() - start_time
                    self.track_response_time(endpoint_name, duration)
                    
                    # Add performance header
                    if hasattr(g, 'response') and g.response:
                        g.response.headers['X-Response-Time'] = f"{duration:.3f}s"
                    
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    self.track_response_time(f"{endpoint_name}_error", duration)
                    raise
            return wrapper
        return decorator
    
    def optimize_query(self, query, **kwargs):
        """Optimize database query"""
        # This is a placeholder - actual optimization would depend on SQLAlchemy version
        # and specific query patterns
        self.query_optimizations += 1
        return query
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        total_requests = sum(len(times) for times in self.response_times.values())
        total_time = sum(sum(times) for times in self.response_times.values())
        avg_response_time = total_time / max(total_requests, 1)
        
        cache_hit_rate = 0
        if self.cache_hits + self.cache_misses > 0:
            cache_hit_rate = (self.cache_hits / (self.cache_hits + self.cache_misses)) * 100
        
        # Get slowest endpoints
        slowest_endpoints = []
        for endpoint, times in self.response_times.items():
            if times:
                avg_time = sum(times) / len(times)
                max_time = max(times)
                slowest_endpoints.append({
                    'endpoint': endpoint,
                    'avg_time': avg_time,
                    'max_time': max_time,
                    'requests': len(times)
                })
        
        slowest_endpoints.sort(key=lambda x: x['avg_time'], reverse=True)
        
        return {
            'total_requests': total_requests,
            'avg_response_time': avg_response_time,
            'cache_stats': {
                'hits': self.cache_hits,
                'misses': self.cache_misses,
                'hit_rate': round(cache_hit_rate, 2)
            },
            'query_optimizations': self.query_optimizations,
            'slowest_endpoints': slowest_endpoints[:10],
            'endpoints_tracked': len(self.response_times),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def get_endpoint_stats(self, endpoint: str) -> Dict[str, Any]:
        """Get statistics for a specific endpoint"""
        if endpoint not in self.response_times:
            return {}
        
        times = self.response_times[endpoint]
        if not times:
            return {}
        
        return {
            'endpoint': endpoint,
            'requests': len(times),
            'avg_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times),
            'p95_time': sorted(times)[int(len(times) * 0.95)] if len(times) > 20 else max(times),
            'p99_time': sorted(times)[int(len(times) * 0.99)] if len(times) > 100 else max(times),
        }
    
    def recommend_optimizations(self) -> List[Dict[str, Any]]:
        """Recommend performance optimizations"""
        recommendations = []
        
        # Check cache hit rate
        stats = self.get_stats()
        cache_hit_rate = stats['cache_stats']['hit_rate']
        if cache_hit_rate < 50:
            recommendations.append({
                'type': 'cache',
                'priority': 'high',
                'message': f'Low cache hit rate ({cache_hit_rate:.1f}%). Consider increasing cache TTL or adding more caching.',
                'action': 'Review cache configuration and consider preloading frequently accessed data'
            })
        
        # Check slow endpoints
        slowest = stats['slowest_endpoints']
        for endpoint_stat in slowest[:5]:
            if endpoint_stat['avg_time'] > 1.0:
                recommendations.append({
                    'type': 'endpoint',
                    'priority': 'medium',
                    'message': f"Endpoint {endpoint_stat['endpoint']} has average response time of {endpoint_stat['avg_time']:.2f}s",
                    'action': f"Consider optimizing {endpoint_stat['endpoint']} - add caching, optimize queries, or add database indexes"
                })
        
        # Check response times
        if stats['avg_response_time'] > 0.5:
            recommendations.append({
                'type': 'general',
                'priority': 'high',
                'message': f'Average response time is {stats["avg_response_time"]:.2f}s. Consider general optimizations.',
                'action': 'Review database queries, add indexes, enable query caching, optimize serialization'
            })
        
        return recommendations


# Global instance
_performance_optimizer: Optional[PerformanceOptimizer] = None


def get_performance_optimizer() -> PerformanceOptimizer:
    """Get or create performance optimizer instance"""
    global _performance_optimizer
    
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizer()
    
    return _performance_optimizer


def init_performance_optimizer(app):
    """Initialize performance optimizer with Flask app"""
    optimizer = get_performance_optimizer()
    app.performance_optimizer = optimizer
    return optimizer

