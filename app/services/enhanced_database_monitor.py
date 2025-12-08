"""
Enhanced Database Monitoring Service for PipLinePro
Provides comprehensive database monitoring, query tracking, and performance analysis
"""
import time
import threading
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict, deque
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
import psutil

from app.utils.unified_logger import get_enhanced_logger, PerformanceLogger

# Import enhanced connection pool monitor
from app.services.connection_pool_monitor import ConnectionPoolMonitor, initialize_pool_monitoring

class DatabaseQueryTracker:
    """Tracks database queries with detailed performance metrics"""
    
    def __init__(self, max_queries: int = 1000):
        self.queries = deque(maxlen=max_queries)
        self.slow_queries = deque(maxlen=100)
        self.query_stats = defaultdict(int)
        self.total_execution_time = 0.0
        self.slow_query_threshold = 1.0  # seconds
        self.lock = threading.Lock()
    
    def add_query(self, query: str, params: tuple, duration: float, 
                  stack_trace: str = None, error: Exception = None):
        """Add a query to the tracker"""
        query_info = {
            'timestamp': datetime.now(timezone.utc),
            'query': query,
            'params': params,
            'duration': duration,
            'stack_trace': stack_trace,
            'error': str(error) if error else None,
            'error_type': type(error).__name__ if error else None
        }
        
        with self.lock:
            self.queries.append(query_info)
            self.query_stats[query] += 1
            self.total_execution_time += duration
            
            # Track slow queries
            if duration > self.slow_query_threshold:
                self.slow_queries.append(query_info)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database query statistics"""
        with self.lock:
            total_queries = len(self.queries)
            avg_time = self.total_execution_time / total_queries if total_queries > 0 else 0
            
            return {
                'total_queries': total_queries,
                'total_execution_time': self.total_execution_time,
                'average_execution_time': avg_time,
                'slow_queries_count': len(self.slow_queries),
                'slow_query_threshold': self.slow_query_threshold,
                'most_frequent_queries': dict(sorted(
                    self.query_stats.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:10])
            }
    
    def get_slow_queries(self) -> List[Dict[str, Any]]:
        """Get list of slow queries"""
        with self.lock:
            return list(self.slow_queries)
    
    def get_recent_queries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent queries"""
        with self.lock:
            return list(self.queries)[-limit:]

class DatabaseConnectionMonitor:
    """Monitors database connection pool and performance"""
    
    def __init__(self, engine: Engine):
        self.engine = engine
        self.connection_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'idle_connections': 0,
            'connection_errors': 0,
            'last_check': None
        }
        self.lock = threading.Lock()
    
    def update_stats(self):
        """Update connection pool statistics"""
        try:
            pool = self.engine.pool
            with self.lock:
                self.connection_stats.update({
                    'total_connections': pool.size(),
                    'active_connections': pool.checkedin(),
                    'idle_connections': pool.checkedout(),
                    'last_check': datetime.now(timezone.utc)
                })
        except Exception as e:
            with self.lock:
                self.connection_stats['connection_errors'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        with self.lock:
            return self.connection_stats.copy()

class EnhancedDatabaseMonitor:
    """Enhanced database monitoring service"""
    
    def __init__(self, app=None):
        self.app = app
        self.logger = get_enhanced_logger("DatabaseMonitor")
        self.query_tracker = DatabaseQueryTracker()
        self.connection_monitor = None
        self.monitoring_active = False
        self.monitor_thread = None
        self.stats_interval = 300  # seconds (changed from 60 to 300)
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the database monitor with Flask app"""
        self.app = app
        # Access the engine through the app context
        with app.app_context():
            from app import db
            self.engine = db.engine
            self.connection_monitor = DatabaseConnectionMonitor(self.engine)
            
            # Initialize enhanced connection pool monitoring
            try:
                self.pool_monitor = initialize_pool_monitoring(self.engine)
                self.logger.info("Enhanced connection pool monitoring initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize pool monitoring: {e}")
                self.pool_monitor = None
        
        # Set up SQLAlchemy event listeners
        self._setup_event_listeners()
        
        # Start monitoring
        self.start_monitoring()
        
        self.logger.info("Enhanced Database Monitor initialized")
    
    def _setup_event_listeners(self):
        """Set up SQLAlchemy event listeners for query tracking"""
        
        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Track query start time"""
            context._query_start_time = time.time()
            context._query_statement = statement
            context._query_parameters = parameters
        
        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Track query completion and log performance"""
            duration = time.time() - getattr(context, '_query_start_time', time.time())
            
            # Get stack trace for debugging
            import traceback
            stack_trace = ''.join(traceback.format_stack()[:-2])  # Exclude SQLAlchemy internals
            
            # Track the query
            self.query_tracker.add_query(statement, parameters, duration, stack_trace)
            
            # Log query performance
            self.logger.log_database_query(
                query=statement,
                params=parameters,
                duration=duration,
                slow_query_threshold=self.query_tracker.slow_query_threshold
            )
        
        @event.listens_for(Engine, "handle_error")
        def handle_error(exception_context):
            """Track database errors"""
            # Handle different SQLAlchemy versions
            try:
                # Try newer SQLAlchemy version (2.0+)
                error = exception_context.original
            except AttributeError:
                try:
                    # Try older SQLAlchemy version
                    error = exception_context.exception
                except AttributeError:
                    # Fallback to the context itself
                    error = exception_context
            
            statement = getattr(exception_context, 'statement', 'Unknown')
            parameters = getattr(exception_context, 'parameters', None)
            
            self.logger.log_exception(error, {
                'database_error': True,
                'statement': statement,
                'parameters': parameters,
                'error_type': type(error).__name__
            })
    
    def start_monitoring(self):
        """Start the database monitoring service"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("Database monitoring started")
    
    def stop_monitoring(self):
        """Stop the database monitoring service"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        self.logger.info("Database monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Update connection statistics
                if self.connection_monitor:
                    self.connection_monitor.update_stats()
                
                # Log periodic statistics
                self._log_periodic_stats()
                
                # Sleep for the monitoring interval
                time.sleep(self.stats_interval)
                
            except Exception as e:
                self.logger.log_exception(e, {'monitoring_loop': True})
                time.sleep(10)  # Wait before retrying
    
    def _log_periodic_stats(self):
        """Log periodic database statistics"""
        try:
            # Get query statistics
            query_stats = self.query_tracker.get_stats()
            
            # Get connection statistics
            conn_stats = self.connection_monitor.get_stats() if self.connection_monitor else {}
            
            # Get system memory usage
            memory_info = psutil.virtual_memory()
            
            # Log only essential statistics to reduce log volume
            self.logger.log_performance_metrics(
                operation="database_periodic_stats",
                duration=0,  # Not applicable for periodic stats
                additional_metrics={
                    'query_stats': {
                        'total_queries': query_stats.get('total_queries', 0),
                        'total_execution_time': query_stats.get('total_execution_time', 0.0),
                        'average_execution_time': query_stats.get('average_execution_time', 0.0),
                        'slow_queries_count': query_stats.get('slow_queries_count', 0)
                    },
                    'connection_stats': {
                        'total_connections': conn_stats.get('total_connections', 0),
                        'active_connections': conn_stats.get('active_connections', 0),
                        'connection_errors': conn_stats.get('connection_errors', 0)
                    },
                    'system_memory': {
                        'total_gb': memory_info.total / (1024**3),
                        'available_gb': memory_info.available / (1024**3),
                        'percent_used': memory_info.percent
                    }
                }
            )
            
        except Exception as e:
            self.logger.log_exception(e, {'periodic_stats': True})
    
    def get_database_health(self) -> Dict[str, Any]:
        """Get comprehensive database health information"""
        try:
            # Test database connectivity
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                connectivity_ok = result.fetchone()[0] == 1
            
            # Get statistics
            query_stats = self.query_tracker.get_stats()
            conn_stats = self.connection_monitor.get_stats() if self.connection_monitor else {}
            
            # Get enhanced pool statistics if available
            pool_stats = {}
            if self.pool_monitor:
                pool_stats = self.pool_monitor.get_pool_stats()
            
            # Calculate health metrics
            avg_query_time = query_stats.get('average_execution_time', 0)
            slow_query_ratio = (query_stats.get('slow_queries_count', 0) / 
                              max(query_stats.get('total_queries', 1), 1))
            
            # Determine health status
            if avg_query_time < 0.1 and slow_query_ratio < 0.05:
                health_status = "EXCELLENT"
            elif avg_query_time < 0.5 and slow_query_ratio < 0.1:
                health_status = "GOOD"
            elif avg_query_time < 1.0 and slow_query_ratio < 0.2:
                health_status = "FAIR"
            else:
                health_status = "POOR"
            
            return {
                'status': health_status,
                'connectivity': connectivity_ok,
                'query_performance': {
                    'average_query_time': avg_query_time,
                    'slow_query_ratio': slow_query_ratio,
                    'total_queries': query_stats.get('total_queries', 0),
                    'slow_queries': query_stats.get('slow_queries_count', 0)
                },
                'connection_pool': conn_stats,
                'pool_monitor': pool_stats,
                'recommendations': self._get_recommendations(avg_query_time, slow_query_ratio)
            }
            
        except Exception as e:
            self.logger.log_exception(e, {'health_check': True})
            return {
                'status': 'ERROR',
                'connectivity': False,
                'error': str(e)
            }
    
    def _get_recommendations(self, avg_query_time: float, slow_query_ratio: float) -> List[str]:
        """Get recommendations based on performance metrics"""
        recommendations = []
        
        if avg_query_time > 1.0:
            recommendations.append("Consider optimizing slow queries or adding database indexes")
        
        if slow_query_ratio > 0.1:
            recommendations.append("High number of slow queries detected - review query performance")
        
        if avg_query_time > 0.5:
            recommendations.append("Consider implementing query caching for frequently executed queries")
        
        if not recommendations:
            recommendations.append("Database performance is within acceptable parameters")
        
        return recommendations
    
    def get_slow_queries_report(self) -> Dict[str, Any]:
        """Get detailed report of slow queries"""
        slow_queries = self.query_tracker.get_slow_queries()
        
        # Group slow queries by pattern
        query_patterns = defaultdict(list)
        for query_info in slow_queries:
            # Create a simplified pattern for grouping
            pattern = self._simplify_query_pattern(query_info['query'])
            query_patterns[pattern].append(query_info)
        
        # Analyze patterns
        pattern_analysis = {}
        for pattern, queries in query_patterns.items():
            total_time = sum(q['duration'] for q in queries)
            avg_time = total_time / len(queries)
            max_time = max(q['duration'] for q in queries)
            
            pattern_analysis[pattern] = {
                'count': len(queries),
                'total_time': total_time,
                'average_time': avg_time,
                'max_time': max_time,
                'recent_occurrences': [
                    {
                        'timestamp': q['timestamp'].isoformat(),
                        'duration': q['duration'],
                        'params': q['params']
                    }
                    for q in queries[-5:]  # Last 5 occurrences
                ]
            }
        
        return {
            'total_slow_queries': len(slow_queries),
            'patterns': pattern_analysis,
            'threshold_seconds': self.query_tracker.slow_query_threshold
        }
    
    def _simplify_query_pattern(self, query: str) -> str:
        """Simplify query for pattern matching"""
        # Remove specific values and keep structure
        import re
        
        # Replace numbers with placeholders
        query = re.sub(r'\b\d+\b', 'N', query)
        
        # Replace quoted strings with placeholders
        query = re.sub(r"'[^']*'", "'S'", query)
        query = re.sub(r'"[^"]*"', '"S"', query)
        
        # Normalize whitespace
        query = re.sub(r'\s+', ' ', query).strip()
        
        return query
    
    def set_slow_query_threshold(self, threshold: float):
        """Set the slow query threshold in seconds"""
        self.query_tracker.slow_query_threshold = threshold
        self.logger.info(f"Slow query threshold set to {threshold} seconds")
    
    def clear_query_history(self):
        """Clear query history"""
        self.query_tracker.queries.clear()
        self.query_tracker.slow_queries.clear()
        self.query_tracker.query_stats.clear()
        self.query_tracker.total_execution_time = 0.0
        
        self.logger.info("Query history cleared")

# Global instance
database_monitor = EnhancedDatabaseMonitor()

def init_database_monitor(app):
    """Initialize database monitor with Flask app"""
    database_monitor.init_app(app)
    return database_monitor 