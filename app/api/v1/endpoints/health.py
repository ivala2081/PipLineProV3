"""
Health check endpoints for PipLinePro
Uses unified health check service for comprehensive monitoring
Standardized response format
"""
from flask import Blueprint, jsonify
from datetime import datetime, timezone
import logging

from app.services.health_check_service import health_check_service
from app.utils.api_response import success_response, error_response, ErrorCode
from app.utils.api_error_handler import handle_api_errors

logger = logging.getLogger(__name__)

health_api = Blueprint('health_api', __name__)


@health_api.route('/health')
@health_api.route('/')
@handle_api_errors
def health_check():
    """Basic health check endpoint"""
    from flask import has_app_context
    
    # Check if we have app context
    if not has_app_context():
        return jsonify(error_response(
            ErrorCode.INTERNAL_ERROR.value,
            'No application context',
            details={'checks': {'service': {'status': 'unhealthy', 'error': 'Application not initialized'}}}
        )), 503
    
    result = health_check_service.check_basic()
    status_code = 200 if result['status'] == 'healthy' else 503
    
    # Wrap in standardized format
    if result['status'] == 'healthy':
        return jsonify(success_response(
            data=result,
            meta={'timestamp': datetime.now(timezone.utc).isoformat()}
        )), status_code
    else:
        return jsonify(error_response(
            ErrorCode.INTERNAL_ERROR.value,
            result.get('error', 'Service unhealthy'),
            details=result.get('checks', {})
        )), status_code


@health_api.route('/health/detailed')
@handle_api_errors
def detailed_health_check():
    """Detailed health check with all dependencies and system metrics"""
    result = health_check_service.check_all()
    
    # Add CPU metrics
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.1)
        result['system'] = {
            'cpu_percent': cpu_percent,
        }
    except Exception:
        pass
    
    status_code = 200 if result['status'] == 'healthy' else 503
    
    if result['status'] == 'healthy':
        return jsonify(success_response(
            data=result,
            meta={'timestamp': datetime.now(timezone.utc).isoformat()}
        )), status_code
    else:
        return jsonify(error_response(
            ErrorCode.INTERNAL_ERROR.value,
            result.get('error', 'Service unhealthy'),
            details=result
        )), status_code


@health_api.route('/health/ready')
@handle_api_errors
def readiness_check():
    """Kubernetes readiness probe - checks if ready to serve traffic"""
    result, status_code = health_check_service.check_readiness()
    
    if status_code == 200:
        return jsonify(success_response(
            data=result,
            meta={'timestamp': datetime.now(timezone.utc).isoformat()}
        )), status_code
    else:
        return jsonify(error_response(
            ErrorCode.INTERNAL_ERROR.value,
            result.get('error', 'Service not ready'),
            details=result
        )), status_code


@health_api.route('/health/live')
@handle_api_errors
def liveness_check():
    """Kubernetes liveness probe - checks if application is alive"""
    result, status_code = health_check_service.check_liveness()
    
    return jsonify(success_response(
        data=result,
        meta={'timestamp': datetime.now(timezone.utc).isoformat()}
    )), status_code