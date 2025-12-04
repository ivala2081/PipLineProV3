"""
Database Query Optimization Utilities
Provides optimized database queries and connection management
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import text, func, and_, or_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from app import db
import time

logger = logging.getLogger(__name__)

class QueryOptimizer:
    """Advanced database query optimization"""
    
    def __init__(self):
        self.query_cache = {}
        self.performance_stats = {
            'total_queries': 0,
            'slow_queries': 0,
            'cache_hits': 0,
            'avg_query_time': 0
        }
    
    @contextmanager
    def optimized_session(self):
        """Context manager for optimized database sessions"""
        session = db.session
        try:
            # Configure session for optimal performance
            session.execute(text("PRAGMA journal_mode=WAL"))  # SQLite WAL mode
            session.execute(text("PRAGMA synchronous=NORMAL"))  # Faster writes
            session.execute(text("PRAGMA cache_size=10000"))  # Larger cache
            session.execute(text("PRAGMA temp_store=MEMORY"))  # In-memory temp tables
            
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def execute_optimized_query(self, query: str, params: Dict = None, cache_key: str = None) -> List[Dict]:
        """Execute query with optimization and caching"""
        start_time = time.time()
        
        # Check cache first
        if cache_key and cache_key in self.query_cache:
            self.performance_stats['cache_hits'] += 1
            logger.debug(f"Query cache HIT for key: {cache_key}")
            return self.query_cache[cache_key]
        
        try:
            with self.optimized_session() as session:
                # Use prepared statements for better performance
                result = session.execute(text(query), params or {})
                
                # Convert to list of dictionaries
                columns = result.keys()
                data = [dict(zip(columns, row)) for row in result.fetchall()]
                
                # Cache the result
                if cache_key:
                    self.query_cache[cache_key] = data
                
                # Update performance stats
                execution_time = time.time() - start_time
                self.performance_stats['total_queries'] += 1
                self.performance_stats['avg_query_time'] = (
                    (self.performance_stats['avg_query_time'] * (self.performance_stats['total_queries'] - 1) + execution_time) 
                    / self.performance_stats['total_queries']
                )
                
                if execution_time > 1.0:
                    self.performance_stats['slow_queries'] += 1
                    logger.warning(f"Slow query detected: {execution_time:.2f}s - {query[:100]}...")
                
                logger.debug(f"Query executed in {execution_time:.3f}s")
                return data
                
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise
    
    def get_transaction_stats_optimized(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Optimized transaction statistics query"""
        cache_key = f"transaction_stats_{start_date}_{end_date}"
        
        # Build optimized query
        where_clause = ""
        params = {}
        
        if start_date and end_date:
            where_clause = "WHERE date BETWEEN :start_date AND :end_date"
            params = {'start_date': start_date, 'end_date': end_date}
        
        query = f"""
        SELECT 
            COUNT(*) as total_transactions,
            SUM(amount) as total_revenue,
            AVG(amount) as avg_transaction,
            COUNT(DISTINCT client_name) as unique_clients,
            COUNT(DISTINCT psp) as unique_psps,
            COUNT(DISTINCT company) as unique_companies,
            MIN(amount) as min_amount,
            MAX(amount) as max_amount,
            COUNT(CASE WHEN amount > 10000 THEN 1 END) as large_transactions
        FROM "transaction" 
        {where_clause}
        """
        
        result = self.execute_optimized_query(query, params, cache_key)
        return result[0] if result else {}
    
    def get_daily_revenue_optimized(self, days: int = 30) -> List[Dict[str, Any]]:
        """Optimized daily revenue query with proper indexing"""
        cache_key = f"daily_revenue_{days}"
        
        query = """
        SELECT 
            date,
            COUNT(*) as transaction_count,
            SUM(amount) as daily_revenue,
            AVG(amount) as avg_transaction,
            COUNT(DISTINCT client_name) as unique_clients
        FROM "transaction" 
        WHERE date >= date('now', '-{} days')
        GROUP BY date 
        ORDER BY date DESC
        """.format(days)
        
        return self.execute_optimized_query(query, cache_key=cache_key)
    
    def get_psp_performance_optimized(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """Optimized PSP performance query"""
        cache_key = f"psp_performance_{start_date}_{end_date}"
        
        where_clause = ""
        params = {}
        
        if start_date and end_date:
            where_clause = "WHERE date BETWEEN :start_date AND :end_date"
            params = {'start_date': start_date, 'end_date': end_date}
        
        query = f"""
        SELECT 
            psp,
            COUNT(*) as transaction_count,
            SUM(amount) as total_volume,
            AVG(amount) as avg_transaction,
            COUNT(DISTINCT client_name) as unique_clients,
            COUNT(DISTINCT company) as unique_companies
        FROM "transaction" 
        {where_clause}
        GROUP BY psp 
        ORDER BY total_volume DESC
        """
        
        return self.execute_optimized_query(query, params, cache_key)
    
    def get_client_analytics_optimized(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Optimized client analytics query"""
        cache_key = f"client_analytics_{start_date}_{end_date}"
        
        where_clause = ""
        params = {}
        
        if start_date and end_date:
            where_clause = "WHERE date BETWEEN :start_date AND :end_date"
            params = {'start_date': start_date, 'end_date': end_date}
        
        # Top clients by volume
        top_clients_query = f"""
        SELECT 
            client_name,
            COUNT(*) as transaction_count,
            SUM(amount) as total_volume,
            AVG(amount) as avg_transaction,
            COUNT(DISTINCT psp) as psp_count
        FROM "transaction" 
        {where_clause}
        GROUP BY client_name 
        ORDER BY total_volume DESC 
        LIMIT 10
        """
        
        # Client distribution
        distribution_query = f"""
        SELECT 
            CASE 
                WHEN SUM(amount) > 100000 THEN 'High Value'
                WHEN SUM(amount) > 10000 THEN 'Medium Value'
                ELSE 'Low Value'
            END as segment,
            COUNT(*) as client_count,
            SUM(amount) as total_volume
        FROM "transaction" 
        {where_clause}
        GROUP BY client_name
        """
        
        top_clients = self.execute_optimized_query(top_clients_query, params)
        distribution = self.execute_optimized_query(distribution_query, params)
        
        return {
            'top_clients': top_clients,
            'distribution': distribution,
            'cache_key': cache_key
        }
    
    def clear_query_cache(self, pattern: str = None):
        """Clear query cache"""
        if pattern:
            keys_to_remove = [key for key in self.query_cache.keys() if pattern in key]
            for key in keys_to_remove:
                del self.query_cache[key]
            logger.info(f"Cleared {len(keys_to_remove)} cached queries matching pattern: {pattern}")
        else:
            self.query_cache.clear()
            logger.info("All query cache cleared")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get query performance statistics"""
        return {
            **self.performance_stats,
            'cache_size': len(self.query_cache),
            'cache_hit_rate': (self.performance_stats['cache_hits'] / max(self.performance_stats['total_queries'], 1)) * 100
        }

# Global query optimizer instance
query_optimizer = QueryOptimizer()

# Export commonly used functions
__all__ = ['QueryOptimizer', 'query_optimizer']
