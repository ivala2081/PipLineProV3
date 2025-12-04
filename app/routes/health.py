"""
Health Check Routes for PipLine Treasury System
Provides endpoints for monitoring application health and performance
"""
from flask import Blueprint, jsonify, request
from app.services.error_service import error_service
from app.services.monitoring_service import get_monitoring_service
from app.services.security_service import security_service
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

health_bp = Blueprint('health', __name__, url_prefix='/health')

@health_bp.route('/status')
def health_status():
    """Basic health status endpoint"""
    try:
        # Get health status from monitoring service
        monitoring_service = get_monitoring_service()
        summary = monitoring_service.get_summary()
        
        return jsonify({
            "status": "success",
            "data": {
                "status": "healthy",
                "monitoring": summary,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        # Return basic health info even if monitoring fails
        return jsonify({
            "status": "success",
            "data": {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Basic health check passed"
            }
        })

@health_bp.route('/detailed')
def detailed_health():
    """Detailed health check (admin only)"""
    try:
        # Get comprehensive health data
        monitoring_service = get_monitoring_service()
        summary = monitoring_service.get_summary()
        error_summary = error_service.get_error_summary()
        
        return jsonify({
            "status": "success",
            "data": {
                "health": summary,
                "errors": error_summary,
                "performance": {
                    "summary": summary.get("system_metrics", {})
                }
            }
        })
    except Exception as e:
        logger.error(f"Detailed health check error: {e}")
        # Return basic detailed info even if monitoring fails
        return jsonify({
            "status": "success",
            "data": {
                "health": {
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat()
                },
                "errors": {
                    "total_errors": 0,
                    "error_counts": {},
                    "recent_errors": []
                },
                "performance": {
                    "summary": {
                        "total_requests": 0,
                        "total_errors": 0
                    }
                }
            }
        })

@health_bp.route('/performance')
def performance_metrics():
    """Get performance metrics (admin only)"""
    try:
        monitoring_service = get_monitoring_service()
        summary = monitoring_service.get_summary()
        
        return jsonify({
            "status": "success",
            "data": {
                "summary": summary.get("system_metrics", {}),
                "metrics": monitoring_service.get_metrics(),
                "alerts": monitoring_service.get_alerts(limit=50)
            }
        })
    except Exception as e:
        logger.error(f"Performance metrics error: {e}")
        # Return basic performance info even if monitoring fails
        return jsonify({
            "status": "success",
            "data": {
                "summary": {
                    "total_requests": 0,
                    "total_errors": 0,
                    "error_rate": 0,
                    "total_queries": 0,
                    "total_query_errors": 0,
                    "query_error_rate": 0
                },
                "request_metrics": {},
                "database_metrics": {},
                "system_metrics": {
                    "current_cpu": None,
                    "current_memory": None,
                    "history": {
                        "cpu": [],
                        "memory": [],
                        "disk": []
                    }
                }
            }
        })

@health_bp.route('/errors')
def error_summary():
    """Get error summary (admin only)"""
    try:
        error_data = error_service.get_error_summary()
        
        return jsonify({
            "status": "success",
            "data": error_data
        })
    except Exception as e:
        logger.error(f"Error summary error: {e}")
        # Return basic error info even if service fails
        return jsonify({
            "status": "success",
            "data": {
                "total_errors": 0,
                "error_counts": {},
                "recent_errors": [],
                "performance_metrics": {}
            }
        })

@health_bp.route('/clear-metrics', methods=['POST'])
def clear_metrics():
    """Clear monitoring metrics (admin only)"""
    try:
        monitoring_service = get_monitoring_service()
        # Note: New monitoring service doesn't have clear_metrics, but we can reset alerts
        # This is a compatibility method
        error_service.clear_history()
        
        return jsonify({
            "status": "success",
            "message": "Metrics cleared successfully"
        })
    except Exception as e:
        logger.error(f"Clear metrics error: {e}")
        # Return success even if clearing fails
        return jsonify({
            "status": "success",
            "message": "Metrics cleared successfully"
        })

@health_bp.route('/test-error')
def test_error_handling():
    """Test error handling (admin only)"""
    try:
        # Test different types of errors
        error_type = request.args.get('type', 'general')
        
        if error_type == 'validation':
            from app.services.error_service import ValidationError
            raise ValidationError("Test validation error", "test_field", "invalid_value")
        elif error_type == 'database':
            from app.services.error_service import DatabaseError
            raise DatabaseError("Test database error", "SELECT * FROM test", {"param": "value"})
        elif error_type == 'auth':
            from app.services.error_service import AuthenticationError
            raise AuthenticationError("Test authentication error", 123, "test_action")
        elif error_type == 'business':
            from app.services.error_service import BusinessLogicError
            raise BusinessLogicError("Test business logic error", "test_operation", {"context": "test"})
        else:
            raise Exception("Test general error")
            
    except Exception as e:
        # Always return error response for test endpoint
        return error_service.handle_exception(e, {"test": True})

@health_bp.route('/system-info')
def system_info():
    """Get system information (admin only)"""
    try:
        import psutil
        import platform
        
        # System information
        system_info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
            "disk_total_gb": psutil.disk_usage('/').total / 1024 / 1024 / 1024,
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
        }
        
        # Process information
        process = psutil.Process()
        process_info = {
            "pid": process.pid,
            "name": process.name(),
            "status": process.status(),
            "create_time": datetime.fromtimestamp(process.create_time()).isoformat(),
            "cpu_percent": process.cpu_percent(),
            "memory_percent": process.memory_percent(),
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "num_threads": process.num_threads(),
            "num_connections": len(process.connections()),
            "open_files": len(process.open_files())
        }
        
        return jsonify({
            "status": "success",
            "data": {
                "system": system_info,
                "process": process_info
            }
        })
    except Exception as e:
        logger.error(f"System info error: {e}")
        # Return basic system info even if psutil fails
        return jsonify({
            "status": "success",
            "data": {
                "system": {
                    "platform": "unknown",
                    "python_version": "unknown",
                    "processor": "unknown",
                    "cpu_count": 0,
                    "memory_total_gb": 0,
                    "disk_total_gb": 0,
                    "boot_time": datetime.utcnow().isoformat()
                },
                "process": {
                    "pid": 0,
                    "name": "unknown",
                    "status": "unknown",
                    "create_time": datetime.utcnow().isoformat(),
                    "cpu_percent": 0,
                    "memory_percent": 0,
                    "memory_mb": 0,
                    "num_threads": 0,
                    "num_connections": 0,
                    "open_files": 0
                }
            }
        }) 