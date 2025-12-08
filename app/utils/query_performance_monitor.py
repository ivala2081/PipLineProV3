"""
Query Performance Monitoring
Automatically detects and logs slow database queries
"""
import logging
import time
from functools import wraps
from typing import Any
from collections.abc import Callable
from sqlalchemy import event
from sqlalchemy.engine import Engine
from datetime import datetime

logger = logging.getLogger(__name__)

# Configuration - will be overridden by Flask app config
SLOW_QUERY_THRESHOLD = 0.1  # 100ms - queries slower than this will be logged
VERY_SLOW_QUERY_THRESHOLD = 0.5  # 500ms - queries slower than this are critical

# Performance thresholds by environment
# Development: 100ms / 500ms (strict for early detection)
# Production: 1000ms / 2000ms (focus on critical issues)

# Statistics
query_stats = {
    'total_queries': 0,
    'slow_queries': 0,
    'very_slow_queries': 0,
    'total_time': 0.0,
    'slowest_query': {'time': 0.0, 'sql': '', 'timestamp': None}
}


class QueryPerformanceMonitor:
    """
    Monitor database query performance and log slow queries.
    """
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize query performance monitoring with Flask app"""
        # SQLAlchemy event listeners for query timing
        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Record query start time"""
            conn.info.setdefault('query_start_time', []).append(time.time())
        
        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Calculate and log query execution time"""
            try:
                total_time = time.time() - conn.info['query_start_time'].pop(-1)
                
                # Update statistics
                query_stats['total_queries'] += 1
                query_stats['total_time'] += total_time
                
                # Check if this is the slowest query
                if total_time > query_stats['slowest_query']['time']:
                    query_stats['slowest_query'] = {
                        'time': total_time,
                        'sql': statement[:200],  # First 200 chars
                        'timestamp': datetime.now().isoformat()
                    }
                
                # Log slow queries
                if total_time > VERY_SLOW_QUERY_THRESHOLD:
                    query_stats['very_slow_queries'] += 1
                    logger.warning(
                        f"VERY SLOW QUERY ({total_time:.3f}s): {statement[:200]}...",
                        extra={
                            'query_time': total_time,
                            'query': statement[:500],
                            'severity': 'critical'
                        }
                    )
                elif total_time > SLOW_QUERY_THRESHOLD:
                    query_stats['slow_queries'] += 1
                    logger.info(
                        f"Slow query ({total_time:.3f}s): {statement[:100]}...",
                        extra={
                            'query_time': total_time,
                            'query': statement[:500]
                        }
                    )
                
            except (IndexError, KeyError):
                # If timing data is missing, skip logging
                pass
        
        app.query_performance_monitor = self
        logger.info("Query performance monitoring initialized")
    
    @staticmethod
    def get_stats():
        """Get query performance statistics"""
        avg_time = query_stats['total_time'] / query_stats['total_queries'] if query_stats['total_queries'] > 0 else 0
        
        return {
            'total_queries': query_stats['total_queries'],
            'slow_queries': query_stats['slow_queries'],
            'very_slow_queries': query_stats['very_slow_queries'],
            'average_query_time': round(avg_time, 4),
            'total_query_time': round(query_stats['total_time'], 2),
            'slowest_query': query_stats['slowest_query'],
            'slow_query_percentage': round(
                (query_stats['slow_queries'] / query_stats['total_queries'] * 100) 
                if query_stats['total_queries'] > 0 else 0, 2
            )
        }
    
    @staticmethod
    def reset_stats():
        """Reset query statistics"""
        query_stats['total_queries'] = 0
        query_stats['slow_queries'] = 0
        query_stats['very_slow_queries'] = 0
        query_stats['total_time'] = 0.0
        query_stats['slowest_query'] = {'time': 0.0, 'sql': '', 'timestamp': None}
        logger.info("Query performance statistics reset")


def monitor_query_performance(threshold=SLOW_QUERY_THRESHOLD):
    """
    Decorator to monitor performance of a specific function that makes database queries.
    
    Args:
        threshold: Time threshold in seconds for logging (default: 0.1s)
    
    Example:
        @monitor_query_performance(threshold=0.2)
        def get_all_clients():
            return db.session.query(Client).all()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed_time = time.time() - start_time
                if elapsed_time > threshold:
                    logger.warning(
                        f"Slow operation: {func.__name__} took {elapsed_time:.3f}s",
                        extra={
                            'function': func.__name__,
                            'execution_time': elapsed_time,
                            'threshold': threshold
                        }
                    )
        return wrapper
    return decorator


# Create global instance
query_performance_monitor = QueryPerformanceMonitor()

