"""
Database Service Module for PipLine Treasury System
Handles database connections, monitoring, and optimization
"""
import os
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event, Engine, text
from sqlalchemy.exc import SQLAlchemyError
from flask import current_app
from collections import deque

# Import SQL security utilities
from app.utils.sql_security import SQLSecurityValidator, create_secure_executor, validate_and_execute_query

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service for database operations and monitoring"""
    
    def __init__(self, db: SQLAlchemy):
        self.db = db
        self.engine = db.engine
        self.slow_queries = deque(maxlen=100)  # Keep last 100 slow queries
        self.connection_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'failed_connections': 0,
            'slow_queries_count': 0
        }
        
        # Initialize secure executor
        self.secure_executor = create_secure_executor(db.session)
        
        # Set up event listeners for monitoring
        self._setup_event_listeners()
    
    def _setup_event_listeners(self):
        """Set up SQLAlchemy event listeners for monitoring"""
        
        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Log query start time"""
            context._query_start_time = time.time()
            context._query_statement = statement
            context._query_parameters = parameters
        
        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Log query execution time and slow queries"""
            execution_time = time.time() - getattr(context, '_query_start_time', time.time())
            
            # Log slow queries (taking more than 1 second)
            if execution_time > 1.0:
                self._log_slow_query(statement, parameters, execution_time)
            
            # Update connection stats
            self.connection_stats['total_connections'] += 1
            
            # Log query performance
            if current_app.config.get('DB_QUERY_LOGGING', False):
                logger.debug(f"Query executed in {execution_time:.3f}s: {statement[:100]}...")
        
        @event.listens_for(Engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            """Log successful connection"""
            self.connection_stats['active_connections'] += 1
            logger.debug("Database connection established")
        
        @event.listens_for(Engine, "close")
        def on_disconnect(dbapi_connection, connection_record):
            """Log connection close"""
            self.connection_stats['active_connections'] = max(0, self.connection_stats['active_connections'] - 1)
            logger.debug("Database connection closed")
    
    def _log_slow_query(self, statement: str, parameters: Any, execution_time: float):
        """Log slow query details"""
        self.connection_stats['slow_queries_count'] += 1
        
        query_info = {
            'statement': statement[:200] + '...' if len(statement) > 200 else statement,
            'parameters': str(parameters)[:100] + '...' if len(str(parameters)) > 100 else str(parameters),
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat()
        }
        
        self.slow_queries.append(query_info)
        
        logger.warning(f"Slow query detected ({execution_time:.3f}s): {statement[:100]}...")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get database connection statistics"""
        try:
            pool = self.engine.pool
            return {
                'total_connections': self.connection_stats['total_connections'],
                'active_connections': self.connection_stats['active_connections'],
                'failed_connections': self.connection_stats['failed_connections'],
                'slow_queries_count': self.connection_stats['slow_queries_count'],
                'pool_size': pool.size(),
                'pool_overflow': pool.overflow(),
                'pool_checked_in': pool.checkedin(),
                'pool_checked_out': pool.checkedout(),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting connection stats: {str(e)}")
            return {'error': str(e)}
    
    def get_slow_queries(self, limit: int = 50) -> list:
        """Get list of slow queries"""
        return list(self.slow_queries)[-limit:]
    
    def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        try:
            start_time = time.time()
            
            # SECURITY FIX: Use secure query execution
            result = validate_and_execute_query(self.db.session, 'SELECT 1')
            result.fetchone()  # Execute the query
            
            execution_time = time.time() - start_time
            
            health_status = {
                'status': 'healthy',
                'response_time': execution_time,
                'timestamp': datetime.now().isoformat()
            }
            
            # Check for potential issues
            if execution_time > 1.0:
                health_status['status'] = 'slow'
                health_status['warning'] = f'Connection test took {execution_time:.3f}s'
            
            overflow_count = getattr(self.engine.pool, 'overflow', lambda: 0)()
            if overflow_count > 10:
                health_status['status'] = 'warning'
                health_status['warning'] = f'High connection overflow: {overflow_count}'
            
            return health_status
            
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def execute_prepared_statement(self, statement: str, parameters: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a prepared statement with parameters"""
        try:
            # SECURITY FIX: Use the secure executor for all SQL operations
            return self.secure_executor.execute_safe_query(statement, parameters)
        except Exception as e:
            logger.error(f"Prepared statement execution failed: {str(e)}")
            raise
    
    def execute_safe_select(self, table: str, columns: Optional[List[str]] = None, 
                          where_clause: Optional[str] = None, 
                          parameters: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a safe SELECT query"""
        return self.secure_executor.execute_safe_select(table, columns, where_clause, parameters)
    
    def execute_safe_count(self, table: str, where_clause: Optional[str] = None,
                          parameters: Optional[Dict[str, Any]] = None) -> int:
        """Execute a safe COUNT query"""
        return self.secure_executor.execute_safe_count(table, where_clause, parameters)


# Global database service instance
database_service = None

def init_database_service(db: SQLAlchemy):
    """Initialize the database service"""
    global database_service
    database_service = DatabaseService(db)
    return database_service

def get_database_service() -> DatabaseService:
    """Get the database service instance"""
    global database_service
    if database_service is None:
        raise RuntimeError("Database service not initialized")
    return database_service

def get_db_connection():
    """Get a direct database connection for raw SQL operations"""
    import sqlite3
    from app import app
    
    # Get database URL from Flask app config
    database_url = app.config.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///instance/treasury_improved.db')
    
    # Convert SQLAlchemy URL to SQLite path
    if database_url.startswith('sqlite:///'):
        db_path = database_url.replace('sqlite:///', '')
        return sqlite3.connect(db_path)
    else:
        # For other databases, you might need different connection logic
        raise NotImplementedError(f"Direct connection not implemented for {database_url}") 