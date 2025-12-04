"""
Connection Pool Optimization
Optimizes database connection pooling for better performance
"""
import logging
from typing import Dict, Any, Optional
from flask import current_app
from sqlalchemy import event, pool
from sqlalchemy.engine import Engine
from app import db

logger = logging.getLogger(__name__)


class ConnectionPoolOptimizer:
    """Optimize database connection pool settings"""
    
    @staticmethod
    def configure_pool(engine: Engine, config: Optional[Dict[str, Any]] = None):
        """
        Configure connection pool with optimal settings
        
        Args:
            engine: SQLAlchemy Engine
            config: Optional configuration overrides
        """
        if config is None:
            config = {}
        
        # Get pool settings from config or use defaults
        pool_size = config.get('pool_size', 10)
        max_overflow = config.get('max_overflow', 20)
        pool_timeout = config.get('pool_timeout', 30)
        pool_recycle = config.get('pool_recycle', 3600)
        pool_pre_ping = config.get('pool_pre_ping', True)
        
        # Update pool settings
        if hasattr(engine.pool, 'size'):
            engine.pool.size = pool_size
        if hasattr(engine.pool, '_max_overflow'):
            engine.pool._max_overflow = max_overflow
        if hasattr(engine.pool, '_timeout'):
            engine.pool._timeout = pool_timeout
        if hasattr(engine.pool, '_recycle'):
            engine.pool._recycle = pool_recycle
        if hasattr(engine.pool, '_pre_ping'):
            engine.pool._pre_ping = pool_pre_ping
        
        logger.info(
            f"Connection pool configured: size={pool_size}, "
            f"overflow={max_overflow}, timeout={pool_timeout}s, "
            f"recycle={pool_recycle}s, pre_ping={pool_pre_ping}"
        )
    
    @staticmethod
    def setup_pool_events(engine: Engine):
        """Setup event listeners for connection pool monitoring"""
        
        @event.listens_for(engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Log new connection"""
            logger.debug("New database connection established")
        
        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """Log connection checkout"""
            logger.debug("Connection checked out from pool")
        
        @event.listens_for(engine, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            """Log connection checkin"""
            logger.debug("Connection returned to pool")
        
        @event.listens_for(engine, "invalidate")
        def receive_invalidate(dbapi_conn, connection_record, exception):
            """Log connection invalidation"""
            logger.warning(f"Connection invalidated: {exception}")
        
        logger.info("Connection pool event listeners configured")
    
    @staticmethod
    def get_pool_stats(engine: Engine) -> Dict[str, Any]:
        """
        Get connection pool statistics
        
        Args:
            engine: SQLAlchemy Engine
        
        Returns:
            Dictionary with pool statistics
        """
        pool = engine.pool
        
        stats = {
            'size': getattr(pool, 'size', None),
            'checked_in': getattr(pool, '_checked_in', None),
            'checked_out': getattr(pool, '_checked_out', None),
            'overflow': getattr(pool, '_overflow', None),
            'invalid': getattr(pool, '_invalid', None),
        }
        
        # Calculate utilization
        if stats['size'] and stats['checked_out']:
            stats['utilization'] = (stats['checked_out'] / stats['size']) * 100
        else:
            stats['utilization'] = 0
        
        return stats
    
    @staticmethod
    def optimize_for_workload(engine: Engine, workload_type: str = 'mixed'):
        """
        Optimize pool settings based on workload type
        
        Args:
            engine: SQLAlchemy Engine
            workload_type: 'read_heavy', 'write_heavy', or 'mixed'
        """
        if workload_type == 'read_heavy':
            # More connections for read-heavy workloads
            config = {
                'pool_size': 20,
                'max_overflow': 30,
                'pool_timeout': 30,
            }
        elif workload_type == 'write_heavy':
            # Fewer connections but more overflow for write-heavy
            config = {
                'pool_size': 10,
                'max_overflow': 25,
                'pool_timeout': 20,
            }
        else:  # mixed
            # Balanced settings
            config = {
                'pool_size': 15,
                'max_overflow': 25,
                'pool_timeout': 30,
            }
        
        ConnectionPoolOptimizer.configure_pool(engine, config)
        logger.info(f"Pool optimized for {workload_type} workload")

