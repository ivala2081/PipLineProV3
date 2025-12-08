"""
Error Handling Service for PipLine Treasury System
Provides centralized error handling, logging, and monitoring
"""
import logging
import traceback
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from functools import wraps
from flask import request, current_app, g, jsonify
import psutil
import threading

logger = logging.getLogger(__name__)

class PipLineError(Exception):
    """Base exception class for PipLine application"""
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.details = details or {}
        self.timestamp = datetime.utcnow()

class DatabaseError(PipLineError):
    """Database-related errors"""
    def __init__(self, message: str, query: str = None, params: Dict = None):
        super().__init__(message, "DATABASE_ERROR", {
            "query": query,
            "params": params
        })

class ValidationError(PipLineError):
    """Data validation errors"""
    def __init__(self, message: str, field: str = None, value: Any = None):
        super().__init__(message, "VALIDATION_ERROR", {
            "field": field,
            "value": value
        })

class AuthenticationError(PipLineError):
    """Authentication and authorization errors"""
    def __init__(self, message: str, user_id: int = None, action: str = None):
        super().__init__(message, "AUTHENTICATION_ERROR", {
            "user_id": user_id,
            "action": action
        })

class BusinessLogicError(PipLineError):
    """Business logic and workflow errors"""
    def __init__(self, message: str, operation: str = None, context: Dict = None):
        super().__init__(message, "BUSINESS_LOGIC_ERROR", {
            "operation": operation,
            "context": context or {}
        })

class ErrorService:
    """Comprehensive error handling and monitoring service"""
    
    def __init__(self):
        """Initialize error service"""
        self.error_counts = {}
        self.performance_metrics = {}
        self.error_history = []
        self.max_history_size = 1000
        self._lock = threading.Lock()
    
    def log_error(self, error: Exception, context: Dict = None, severity: str = "ERROR"):
        """Log error with context and performance metrics"""
        error_info = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "severity": severity,
            "traceback": traceback.format_exc(),
            "context": context or {},
            "request_info": self._get_request_info(),
            "performance_metrics": self._get_performance_metrics()
        }
        
        # Log to file
        logger.error(f"Error: {error_info['error_message']}", extra=error_info)
        
        # Store in memory for monitoring
        with self._lock:
            self.error_history.append(error_info)
            if len(self.error_history) > self.max_history_size:
                self.error_history.pop(0)
            
            # Update error counts
            error_type = type(error).__name__
            self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
    
    def _get_request_info(self) -> Dict:
        """Get current request information"""
        try:
            return {
                "method": request.method,
                "url": request.url,
                "endpoint": request.endpoint,
                "user_agent": request.headers.get('User-Agent'),
                "ip": request.remote_addr,
                "user_id": getattr(g, 'user_id', None)
            }
        except RuntimeError:
            return {}
    
    def _get_performance_metrics(self) -> Dict:
        """Get current performance metrics"""
        try:
            process = psutil.Process()
            return {
                "cpu_percent": process.cpu_percent(),
                "memory_percent": process.memory_percent(),
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "thread_count": process.num_threads(),
                "open_files": len(process.open_files()),
                "connections": len(process.connections())
            }
        except Exception:
            return {}
    
    def handle_exception(self, error: Exception, context: Dict = None):
        """Handle and log exception with proper error response"""
        self.log_error(error, context)
        
        if isinstance(error, PipLineError):
            return jsonify({
                "error": error.message,
                "error_code": error.error_code,
                "details": error.details,
                "timestamp": error.timestamp.isoformat()
            }), 400
        else:
            return jsonify({
                "error": "Internal server error",
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }), 500
    
    def monitor_performance(self, operation: str):
        """Decorator to monitor function performance"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss
                
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    memory_used = psutil.Process().memory_info().rss - start_memory
                    
                    self._record_performance(operation, execution_time, memory_used, success=True)
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    memory_used = psutil.Process().memory_info().rss - start_memory
                    
                    self._record_performance(operation, execution_time, memory_used, success=False)
                    self.log_error(e, {"operation": operation})
                    raise
            return wrapper
        return decorator
    
    def _record_performance(self, operation: str, execution_time: float, memory_used: int, success: bool):
        """Record performance metrics"""
        with self._lock:
            if operation not in self.performance_metrics:
                self.performance_metrics[operation] = {
                    "total_calls": 0,
                    "successful_calls": 0,
                    "failed_calls": 0,
                    "total_time": 0,
                    "total_memory": 0,
                    "min_time": float('inf'),
                    "max_time": 0,
                    "avg_time": 0
                }
            
            metrics = self.performance_metrics[operation]
            metrics["total_calls"] += 1
            metrics["total_time"] += execution_time
            metrics["total_memory"] += memory_used
            
            if success:
                metrics["successful_calls"] += 1
            else:
                metrics["failed_calls"] += 1
            
            metrics["min_time"] = min(metrics["min_time"], execution_time)
            metrics["max_time"] = max(metrics["max_time"], execution_time)
            metrics["avg_time"] = metrics["total_time"] / metrics["total_calls"]
    
    def get_error_summary(self) -> Dict:
        """Get error summary for monitoring"""
        with self._lock:
            return {
                "total_errors": sum(self.error_counts.values()),
                "error_counts": self.error_counts.copy(),
                "recent_errors": self.error_history[-10:] if self.error_history else [],
                "performance_metrics": self.performance_metrics.copy()
            }
    
    def get_health_status(self) -> Dict:
        """Get application health status"""
        try:
            # Check database connectivity
            from app import db
            db.session.execute("SELECT 1")
            db_status = "healthy"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
        
        # Check memory usage
        process = psutil.Process()
        memory_percent = process.memory_percent()
        memory_status = "healthy" if memory_percent < 80 else "warning"
        
        # Check CPU usage
        cpu_percent = process.cpu_percent()
        cpu_status = "healthy" if cpu_percent < 80 else "warning"
        
        return {
            "status": "healthy" if all(s == "healthy" for s in [db_status, memory_status, cpu_status]) else "warning",
            "database": db_status,
            "memory": {
                "status": memory_status,
                "percent": memory_percent,
                "mb": process.memory_info().rss / 1024 / 1024
            },
            "cpu": {
                "status": cpu_status,
                "percent": cpu_percent
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def clear_history(self):
        """Clear error history and performance metrics"""
        with self._lock:
            self.error_history.clear()
            self.error_counts.clear()
            self.performance_metrics.clear()

# Global error service instance
error_service = ErrorService() 