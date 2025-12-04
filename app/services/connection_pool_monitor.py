"""
Enhanced Database Connection Pool Monitoring Service
Provides comprehensive monitoring and optimization for database connections
"""
import logging
import threading
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from collections import deque
from sqlalchemy import event, Engine
from sqlalchemy.pool import Pool

from app.utils.unified_logger import get_logger

logger = get_logger("DBPoolMonitor")


class ConnectionPoolMonitor:
    """Comprehensive database connection pool monitoring service"""
    
    def __init__(self, engine: Engine):
        self.engine = engine
        self.pool: Optional[Pool] = None
        self.metrics_history: deque = deque(maxlen=1000)  # Keep last 1000 measurements
        self.alerts: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        self.start_time = datetime.now(timezone.utc)
        
        # Initialize pool reference
        try:
            self.pool = engine.pool
            self._setup_event_listeners()
        except Exception as e:
            logger.error(f"Failed to initialize connection pool monitor: {e}")
    
    def _setup_event_listeners(self):
        """Setup SQLAlchemy event listeners for connection tracking"""
        if not self.pool:
            return
        
        @event.listens_for(self.engine, "connect")
        def on_connect(dbapi_conn, connection_record):
            """Track new connections"""
            with self.lock:
                self._record_event("connect", {
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
        
        @event.listens_for(self.engine, "checkout")
        def on_checkout(dbapi_conn, connection_record, connection_proxy):
            """Track connection checkout"""
            checkout_time = time.time()
            connection_record._checkout_time = checkout_time
            
            with self.lock:
                self._record_event("checkout", {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "checkout_time": checkout_time
                })
        
        @event.listens_for(self.engine, "checkin")
        def on_checkin(dbapi_conn, connection_record):
            """Track connection checkin"""
            with self.lock:
                checkout_time = getattr(connection_record, '_checkout_time', None)
                duration = None
                if checkout_time:
                    duration = time.time() - checkout_time
                
                self._record_event("checkin", {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "duration": duration
                })
        
        @event.listens_for(self.engine, "invalidate")
        def on_invalidate(dbapi_conn, connection_record, exception):
            """Track connection invalidation"""
            with self.lock:
                self._record_event("invalidate", {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "exception": str(exception) if exception else None
                })
                self._check_pool_health()
        
        logger.info("Database connection pool event listeners initialized")
    
    def _record_event(self, event_type: str, data: Dict[str, Any]):
        """Record an event for monitoring"""
        # Keep minimal event history
        if len(self.metrics_history) >= 1000:
            self.metrics_history.popleft()
        
        self.metrics_history.append({
            "event_type": event_type,
            **data
        })
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get current connection pool statistics"""
        if not self.pool:
            return {
                "error": "Pool not available",
                "status": "unavailable"
            }
        
        try:
            pool_size = self.pool.size()
            checked_in = self.pool.checkedin()
            checked_out = self.pool.checkedout()
            overflow = getattr(self.pool, 'overflow', 0)
            invalid = getattr(self.pool, 'invalid', 0)
            
            total_connections = pool_size + overflow
            active_connections = checked_out
            idle_connections = checked_in
            
            # Calculate usage percentage
            usage_percent = 0
            if total_connections > 0:
                usage_percent = (active_connections / total_connections) * 100
            
            # Calculate utilization
            utilization = 0
            if pool_size > 0:
                utilization = (checked_out / pool_size) * 100
            
            # Get pool configuration
            max_overflow = getattr(self.pool, '_max_overflow', 0)
            pool_timeout = getattr(self.pool, '_timeout', None)
            
            stats = {
                "pool_size": pool_size,
                "max_overflow": max_overflow,
                "checked_in": checked_in,
                "checked_out": checked_out,
                "overflow": overflow,
                "invalid": invalid,
                "total_connections": total_connections,
                "active_connections": active_connections,
                "idle_connections": idle_connections,
                "usage_percent": round(usage_percent, 2),
                "utilization_percent": round(utilization, 2),
                "pool_timeout": pool_timeout,
                "status": self._get_pool_status(usage_percent, overflow, invalid),
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "uptime_seconds": (datetime.now(timezone.utc) - self.start_time).total_seconds()
            }
            
            # Add health checks
            stats["health"] = self._check_pool_health()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting pool stats: {e}")
            return {
                "error": str(e),
                "status": "error"
            }
    
    def _get_pool_status(self, usage_percent: float, overflow: int, invalid: int) -> str:
        """Determine pool health status"""
        if invalid > 0:
            return "degraded"
        if overflow > 0:
            return "warning"
        if usage_percent > 90:
            return "warning"
        if usage_percent > 80:
            return "healthy"
        return "healthy"
    
    def _check_pool_health(self) -> Dict[str, Any]:
        """Check pool health and generate alerts"""
        if not self.pool:
            return {"status": "unavailable"}
        
        try:
            pool_size = self.pool.size()
            checked_out = self.pool.checkedout()
            overflow = getattr(self.pool, 'overflow', 0)
            invalid = getattr(self.pool, 'invalid', 0)
            
            issues = []
            warnings = []
            
            # Check for invalid connections
            if invalid > 0:
                issues.append(f"{invalid} invalid connection(s) in pool")
            
            # Check for overflow
            if overflow > 0:
                warnings.append(f"Pool overflow: {overflow} connections")
            
            # Check utilization
            if pool_size > 0:
                utilization = (checked_out / pool_size) * 100
                if utilization > 90:
                    issues.append(f"High pool utilization: {utilization:.1f}%")
                elif utilization > 80:
                    warnings.append(f"Pool utilization high: {utilization:.1f}%")
            
            # Check for connection leaks (checkouts without checkins)
            recent_events = [e for e in list(self.metrics_history)[-100:] if e.get("event_type") in ["checkout", "checkin"]]
            checkouts = sum(1 for e in recent_events if e.get("event_type") == "checkout")
            checkins = sum(1 for e in recent_events if e.get("event_type") == "checkin")
            
            if checkouts - checkins > 10:
                warnings.append(f"Potential connection leak detected: {checkouts - checkins} unreturned connections")
            
            health = {
                "status": "healthy" if not issues else "degraded",
                "issues": issues,
                "warnings": warnings,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Store alerts
            if issues or warnings:
                self.alerts.append({
                    **health,
                    "pool_stats": {
                        "pool_size": pool_size,
                        "checked_out": checked_out,
                        "overflow": overflow,
                        "invalid": invalid
                    }
                })
                
                # Keep only last 100 alerts
                if len(self.alerts) > 100:
                    self.alerts.pop(0)
            
            return health
            
        except Exception as e:
            logger.error(f"Error checking pool health: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_recent_metrics(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get recent pool metrics"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        
        recent = []
        for metric in self.metrics_history:
            metric_time = datetime.fromisoformat(metric.get("timestamp", ""))
            if metric_time >= cutoff_time:
                recent.append(metric)
        
        return recent
    
    def get_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        return list(self.alerts[-limit:])
    
    def optimize_pool_config(self) -> Dict[str, Any]:
        """Analyze pool usage and suggest optimizations"""
        if not self.pool:
            return {"error": "Pool not available"}
        
        stats = self.get_pool_stats()
        suggestions = []
        
        current_size = stats.get("pool_size", 0)
        max_overflow = stats.get("max_overflow", 0)
        utilization = stats.get("utilization_percent", 0)
        overflow_count = stats.get("overflow", 0)
        
        # Suggest pool size adjustments
        if utilization > 85:
            suggested_size = int(current_size * 1.2)
            suggestions.append({
                "type": "increase_pool_size",
                "current": current_size,
                "suggested": suggested_size,
                "reason": f"High utilization ({utilization:.1f}%)"
            })
        elif utilization < 30 and current_size > 5:
            suggested_size = max(5, int(current_size * 0.8))
            suggestions.append({
                "type": "decrease_pool_size",
                "current": current_size,
                "suggested": suggested_size,
                "reason": f"Low utilization ({utilization:.1f}%)"
            })
        
        # Suggest overflow adjustments
        if overflow_count > 0:
            suggested_overflow = max_overflow + 5
            suggestions.append({
                "type": "increase_max_overflow",
                "current": max_overflow,
                "suggested": suggested_overflow,
                "reason": f"Frequent overflow ({overflow_count} connections)"
            })
        
        return {
            "current_config": {
                "pool_size": current_size,
                "max_overflow": max_overflow
            },
            "utilization": utilization,
            "suggestions": suggestions,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def reset_metrics(self):
        """Reset all metrics and alerts"""
        with self.lock:
            self.metrics_history.clear()
            self.alerts.clear()
            self.start_time = datetime.now(timezone.utc)
        logger.info("Connection pool metrics reset")


# Global pool monitor instance
_pool_monitor: Optional[ConnectionPoolMonitor] = None


def get_pool_monitor(engine: Optional[Engine] = None) -> Optional[ConnectionPoolMonitor]:
    """Get or create connection pool monitor instance"""
    global _pool_monitor
    
    if _pool_monitor is None and engine:
        _pool_monitor = ConnectionPoolMonitor(engine)
    
    return _pool_monitor


def initialize_pool_monitoring(engine: Engine):
    """Initialize connection pool monitoring"""
    global _pool_monitor
    _pool_monitor = ConnectionPoolMonitor(engine)
    logger.info("Connection pool monitoring initialized")
    return _pool_monitor

