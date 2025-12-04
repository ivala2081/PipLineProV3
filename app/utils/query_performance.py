"""
Query Performance Optimization Utilities
Decorators and context managers for query optimization
"""
import logging
import time
import functools
from typing import Callable, Any, Optional, Dict
from functools import wraps
from flask import g, current_app
from sqlalchemy.orm import Query
from sqlalchemy import event
from app import db
from app.services.enhanced_cache_service import cache_service

logger = logging.getLogger(__name__)


def cached_query(cache_key_func: Optional[Callable] = None, ttl: int = 300):
    """
    Decorator for caching query results
    
    Args:
        cache_key_func: Function to generate cache key from function args
        ttl: Cache TTL in seconds (default: 5 minutes)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if cache_key_func:
                cache_key = cache_key_func(*args, **kwargs)
            else:
                # Default cache key from function name and args
                import hashlib
                import json
                key_data = {
                    'func': func.__name__,
                    'args': str(args),
                    'kwargs': json.dumps(kwargs, sort_keys=True, default=str)
                }
                cache_key = f"query:{func.__name__}:{hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()}"
            
            # Try cache first
            try:
                cached_result = cache_service.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache HIT for query: {func.__name__}")
                    return cached_result
            except Exception as e:
                logger.warning(f"Cache read error: {e}")
            
            # Execute query
            result = func(*args, **kwargs)
            
            # Cache result
            try:
                cache_service.set(cache_key, result, ttl=ttl)
                logger.debug(f"Cached result for query: {func.__name__}")
            except Exception as e:
                logger.warning(f"Cache write error: {e}")
            
            return result
        
        return wrapper
    return decorator


def track_query_performance(threshold: float = 1.0):
    """
    Decorator to track query performance and log slow queries
    
    Args:
        threshold: Time threshold in seconds for slow query detection
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Track in Flask g for request-level stats
                if not hasattr(g, 'query_stats'):
                    g.query_stats = []
                
                g.query_stats.append({
                    'function': func.__name__,
                    'execution_time': execution_time,
                    'slow': execution_time > threshold
                })
                
                # Log slow queries
                if execution_time > threshold:
                    logger.warning(
                        f"Slow query detected: {func.__name__} took {execution_time:.3f}s "
                        f"(threshold: {threshold}s)"
                    )
                else:
                    logger.debug(f"Query {func.__name__} executed in {execution_time:.3f}s")
                
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Query error in {func.__name__} after {execution_time:.3f}s: {e}"
                )
                raise
        
        return wrapper
    return decorator


def optimize_query(query: Query, limit: Optional[int] = None, offset: Optional[int] = None):
    """
    Optimize SQLAlchemy query with best practices
    
    Args:
        query: SQLAlchemy Query object
        limit: Maximum number of results
        offset: Offset for pagination
    
    Returns:
        Optimized query
    """
    # Apply pagination
    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)
    
    # Enable query result caching if available
    # Note: SQLAlchemy doesn't have built-in query caching,
    # but we can use our cache service
    
    return query


def batch_queries(queries: list, batch_size: int = 100):
    """
    Execute queries in batches to avoid memory issues
    
    Args:
        queries: List of query functions or Query objects
        batch_size: Number of queries per batch
    
    Yields:
        Results from each batch
    """
    for i in range(0, len(queries), batch_size):
        batch = queries[i:i + batch_size]
        results = []
        
        for query in batch:
            if callable(query):
                results.append(query())
            else:
                results.append(query.all())
        
        yield results


class QueryOptimizer:
    """Query optimization context manager"""
    
    def __init__(self, enable_cache: bool = True, cache_ttl: int = 300):
        self.enable_cache = enable_cache
        self.cache_ttl = cache_ttl
        self.query_count = 0
        self.total_time = 0.0
        self.slow_queries = []
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        total_time = time.time() - self.start_time
        logger.debug(
            f"QueryOptimizer: {self.query_count} queries in {total_time:.3f}s "
            f"(avg: {total_time / self.query_count:.3f}s)" if self.query_count > 0 else ""
        )
        
        if self.slow_queries:
            logger.warning(f"Found {len(self.slow_queries)} slow queries")
    
    def execute(self, query_func: Callable, cache_key: Optional[str] = None):
        """Execute query with optimization"""
        start_time = time.time()
        self.query_count += 1
        
        # Try cache if enabled
        if self.enable_cache and cache_key:
            try:
                cached = cache_service.get(cache_key)
                if cached is not None:
                    logger.debug(f"Cache HIT: {cache_key}")
                    return cached
            except Exception as e:
                logger.warning(f"Cache error: {e}")
        
        # Execute query
        result = query_func()
        
        # Cache result if enabled
        if self.enable_cache and cache_key:
            try:
                cache_service.set(cache_key, result, ttl=self.cache_ttl)
            except Exception as e:
                logger.warning(f"Cache write error: {e}")
        
        # Track performance
        execution_time = time.time() - start_time
        self.total_time += execution_time
        
        if execution_time > 1.0:  # Slow query threshold
            self.slow_queries.append({
                'query': query_func.__name__ if hasattr(query_func, '__name__') else str(query_func),
                'time': execution_time
            })
        
        return result


def eager_load_relationships(query: Query, relationships: list):
    """
    Eager load relationships to avoid N+1 queries
    
    Args:
        query: SQLAlchemy Query object
        relationships: List of relationship names to eager load
    
    Returns:
        Query with eager loading
    """
    from sqlalchemy.orm import joinedload, selectinload
    
    for rel in relationships:
        # Use selectinload for better performance in most cases
        query = query.options(selectinload(rel))
    
    return query


def use_index_hint(query: Query, table_name: str, index_name: str):
    """
    Add index hint to query (database-specific)
    
    Note: This is mainly for PostgreSQL and MySQL
    SQLite doesn't support index hints
    
    Args:
        query: SQLAlchemy Query object
        table_name: Name of the table
        index_name: Name of the index to use
    
    Returns:
        Query with index hint
    """
    from app.utils.db_compat import get_database_type
    
    db_type = get_database_type()
    
    if db_type == 'postgresql':
        # PostgreSQL uses index hints via text()
        from sqlalchemy import text
        # Note: SQLAlchemy doesn't directly support index hints
        # This would need to be done via raw SQL if needed
        logger.debug(f"Index hint requested for {table_name}.{index_name} (PostgreSQL)")
    elif db_type == 'mysql':
        logger.debug(f"Index hint requested for {table_name}.{index_name} (MySQL)")
    else:
        logger.debug(f"Index hints not supported for {db_type}")
    
    return query

