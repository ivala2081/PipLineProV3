"""
Comprehensive Health Check Service for PipLinePro
Provides unified health checking with dependency monitoring
"""
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
import psutil
import os

from app.utils.unified_logger import get_logger

logger = get_logger("HealthCheck")


class HealthStatus(str, Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class DependencyCheck:
    """Individual dependency health check"""
    
    def __init__(self, name: str, check_func, critical: bool = True, timeout: float = 5.0):
        self.name = name
        self.check_func = check_func
        self.critical = critical
        self.timeout = timeout
        self.last_check: Optional[datetime] = None
        self.last_status: Optional[HealthStatus] = None
        self.last_error: Optional[str] = None
    
    def check(self) -> Tuple[HealthStatus, Optional[str], Dict[str, Any]]:
        """Run health check with timeout"""
        start_time = time.time()
        details: Dict[str, Any] = {}
        
        try:
            # Run check with timeout
            result = self.check_func()
            
            # Handle different return types
            if isinstance(result, tuple):
                status, error, extra_details = result
                details.update(extra_details or {})
            elif isinstance(result, dict):
                status = result.get('status', HealthStatus.HEALTHY)
                error = result.get('error')
                details.update({k: v for k, v in result.items() if k not in ['status', 'error']})
            else:
                status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                error = None
            
            elapsed = time.time() - start_time
            
            # Check timeout
            if elapsed > self.timeout:
                status = HealthStatus.DEGRADED
                error = f"Check timed out after {self.timeout}s"
            
            self.last_check = datetime.now(timezone.utc)
            self.last_status = status
            self.last_error = error
            details['response_time_ms'] = round(elapsed * 1000, 2)
            
            return status, error, details
            
        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = str(e)
            self.last_check = datetime.now(timezone.utc)
            self.last_status = HealthStatus.UNHEALTHY
            self.last_error = error_msg
            details['response_time_ms'] = round(elapsed * 1000, 2)
            
            return HealthStatus.UNHEALTHY, error_msg, details


class HealthCheckService:
    """Comprehensive health check service"""
    
    def __init__(self):
        self.dependencies: List[DependencyCheck] = []
        self._setup_default_checks()
    
    def _setup_default_checks(self):
        """Setup default health checks"""
        # Database check
        self.register_dependency(
            "database",
            self._check_database,
            critical=True,
            timeout=5.0
        )
        
        # Redis check (optional)
        self.register_dependency(
            "redis",
            self._check_redis,
            critical=False,
            timeout=2.0
        )
        
        # Disk space check
        self.register_dependency(
            "disk",
            self._check_disk_space,
            critical=True,
            timeout=1.0
        )
        
        # Memory check
        self.register_dependency(
            "memory",
            self._check_memory,
            critical=True,
            timeout=0.5
        )
    
    def register_dependency(
        self,
        name: str,
        check_func,
        critical: bool = True,
        timeout: float = 5.0
    ):
        """Register a dependency health check"""
        check = DependencyCheck(name, check_func, critical, timeout)
        self.dependencies.append(check)
        logger.info(f"Registered health check: {name} (critical={critical})")
    
    def _check_database(self) -> Tuple[HealthStatus, Optional[str], Dict[str, Any]]:
        """Check database connectivity"""
        try:
            from flask import current_app
            from app import db
            from sqlalchemy import text
            
            # Check if we have app context
            try:
                app = current_app._get_current_object()
            except RuntimeError:
                # No app context, return unhealthy
                return HealthStatus.UNHEALTHY, "No application context", {}
            
            start_time = time.time()
            try:
                # Try to execute a simple query
                result = db.session.execute(text('SELECT 1'))
                db.session.commit()  # Ensure transaction is committed
                elapsed = time.time() - start_time
            except Exception as db_error:
                # Rollback on error
                try:
                    db.session.rollback()
                except:
                    pass
                elapsed = time.time() - start_time
                return HealthStatus.UNHEALTHY, str(db_error), {
                    'response_time_ms': round(elapsed * 1000, 2)
                }
            
            # Check connection pool stats if available
            pool_stats = {}
            try:
                if hasattr(db, 'engine') and hasattr(db.engine, 'pool'):
                    pool = db.engine.pool
                    pool_stats = {
                        'pool_size': pool.size(),
                        'checked_in': pool.checkedin(),
                        'checked_out': pool.checkedout(),
                        'overflow': pool.overflow(),
                    }
            except Exception:
                pass
            
            return HealthStatus.HEALTHY, None, {
                'response_time_ms': round(elapsed * 1000, 2),
                'pool_stats': pool_stats
            }
            
        except Exception as e:
            logger.error(f"Database health check error: {str(e)}", exc_info=True)
            return HealthStatus.UNHEALTHY, str(e), {}
    
    def _check_redis(self) -> Tuple[HealthStatus, Optional[str], Dict[str, Any]]:
        """Check Redis connectivity"""
        try:
            from app import redis_client
            from app.config import Config
            
            # Check if Redis is enabled
            if not Config.REDIS_ENABLED:
                return HealthStatus.UNKNOWN, "Redis disabled", {}
            
            if not redis_client:
                return HealthStatus.UNKNOWN, "Redis not configured", {}
            
            start_time = time.time()
            redis_client.ping()
            elapsed = time.time() - start_time
            
            # Get Redis info
            info = {}
            try:
                redis_info = redis_client.info()
                info = {
                    'connected_clients': redis_info.get('connected_clients', 0),
                    'used_memory_mb': round(redis_info.get('used_memory', 0) / (1024 * 1024), 2),
                    'keyspace': redis_info.get('db0', {}),
                }
            except Exception:
                pass
            
            return HealthStatus.HEALTHY, None, {
                'response_time_ms': round(elapsed * 1000, 2),
                'info': info
            }
            
        except ImportError:
            return HealthStatus.UNKNOWN, "Redis not available", {}
        except Exception as e:
            return HealthStatus.UNHEALTHY, str(e), {}
    
    def _check_disk_space(self) -> Tuple[HealthStatus, Optional[str], Dict[str, Any]]:
        """Check disk space"""
        try:
            disk = psutil.disk_usage('/')
            percent_used = disk.percent
            free_gb = disk.free / (1024 ** 3)
            
            # Warn if disk is > 80% full
            if percent_used > 90:
                status = HealthStatus.UNHEALTHY
                error = f"Disk usage critical: {percent_used}%"
            elif percent_used > 80:
                status = HealthStatus.DEGRADED
                error = f"Disk usage high: {percent_used}%"
            else:
                status = HealthStatus.HEALTHY
                error = None
            
            return status, error, {
                'percent_used': round(percent_used, 2),
                'free_gb': round(free_gb, 2),
                'total_gb': round(disk.total / (1024 ** 3), 2),
            }
            
        except Exception as e:
            return HealthStatus.UNHEALTHY, str(e), {}
    
    def _check_memory(self) -> Tuple[HealthStatus, Optional[str], Dict[str, Any]]:
        """Check memory usage"""
        try:
            memory = psutil.virtual_memory()
            percent_used = memory.percent
            
            # Warn if memory is > 85% used
            if percent_used > 95:
                status = HealthStatus.UNHEALTHY
                error = f"Memory usage critical: {percent_used}%"
            elif percent_used > 85:
                status = HealthStatus.DEGRADED
                error = f"Memory usage high: {percent_used}%"
            else:
                status = HealthStatus.HEALTHY
                error = None
            
            # Get process memory if available
            process_memory = {}
            try:
                process = psutil.Process()
                process_memory = {
                    'rss_mb': round(process.memory_info().rss / (1024 ** 2), 2),
                    'percent': process.memory_percent(),
                }
            except Exception:
                pass
            
            return status, error, {
                'percent_used': round(percent_used, 2),
                'available_gb': round(memory.available / (1024 ** 3), 2),
                'total_gb': round(memory.total / (1024 ** 3), 2),
                'process': process_memory
            }
            
        except Exception as e:
            return HealthStatus.UNHEALTHY, str(e), {}
    
    def check_all(self) -> Dict[str, Any]:
        """Run all health checks"""
        overall_status = HealthStatus.HEALTHY
        checks = {}
        critical_failures = []
        
        for dep in self.dependencies:
            status, error, details = dep.check()
            
            checks[dep.name] = {
                'status': status.value,
                'critical': dep.critical,
                'error': error,
                'details': details,
                'last_check': dep.last_check.isoformat() if dep.last_check else None
            }
            
            # Update overall status
            if status == HealthStatus.UNHEALTHY:
                if dep.critical:
                    overall_status = HealthStatus.UNHEALTHY
                    critical_failures.append(dep.name)
                elif overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
            elif status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED
        
        return {
            'status': overall_status.value,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'service': 'PipLinePro',
            'version': '1.0.0',
            'checks': checks,
            'critical_failures': critical_failures
        }
    
    def check_basic(self) -> Dict[str, Any]:
        """Basic health check - only critical dependencies"""
        overall_status = HealthStatus.HEALTHY
        checks = {}
        
        for dep in self.dependencies:
            if not dep.critical:
                continue
            
            status, error, details = dep.check()
            
            checks[dep.name] = {
                'status': status.value,
                'error': error
            }
            
            if status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
        
        return {
            'status': overall_status.value,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'checks': checks
        }
    
    def check_readiness(self) -> Tuple[Dict[str, Any], int]:
        """Kubernetes readiness probe - checks if ready to serve traffic"""
        result = self.check_basic()
        
        # Return 503 if any critical dependency is unhealthy
        if result['status'] == HealthStatus.UNHEALTHY.value:
            return result, 503
        
        return result, 200
    
    def check_liveness(self) -> Tuple[Dict[str, Any], int]:
        """Kubernetes liveness probe - checks if application is alive"""
        return {
            'status': HealthStatus.HEALTHY.value,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }, 200


# Global health check service instance
health_check_service = HealthCheckService()

