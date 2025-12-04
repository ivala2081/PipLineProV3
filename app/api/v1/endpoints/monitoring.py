"""
Monitoring and Alerting API Endpoints
Provides API access to monitoring metrics and alerts
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from typing import Dict, Any, Optional
import logging

from app.services.monitoring_service import (
    get_monitoring_service, AlertLevel
)
from app.services.rate_limit_service import get_rate_limit_service
from app.utils.unified_error_handler import handle_api_errors
from app.utils.unified_logger import get_logger

logger = get_logger("MonitoringAPI")

monitoring_api = Blueprint('monitoring_api', __name__)


@monitoring_api.route('/summary')
@login_required
@handle_api_errors
def get_monitoring_summary():
    """Get monitoring summary"""
    try:
        monitoring_service = get_monitoring_service()
        summary = monitoring_service.get_summary()
        
        return jsonify({
            'success': True,
            'summary': summary
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting monitoring summary: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@monitoring_api.route('/alerts')
@login_required
@handle_api_errors
def get_alerts():
    """Get alerts"""
    try:
        monitoring_service = get_monitoring_service()
        
        level = request.args.get('level')
        source = request.args.get('source')
        limit = request.args.get('limit', 100, type=int)
        
        alert_level = None
        if level:
            try:
                alert_level = AlertLevel(level.lower())
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': f'Invalid alert level: {level}'
                }), 400
        
        alerts = monitoring_service.get_alerts(
            level=alert_level,
            source=source,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'alerts': alerts,
            'count': len(alerts)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@monitoring_api.route('/metrics')
@login_required
@handle_api_errors
def get_metrics():
    """Get metrics"""
    try:
        monitoring_service = get_monitoring_service()
        
        metric_name = request.args.get('name')
        limit = request.args.get('limit', type=int)
        
        metrics = monitoring_service.get_metrics(name=metric_name, limit=limit)
        
        return jsonify({
            'success': True,
            'metrics': metrics
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@monitoring_api.route('/rate-limits/stats')
@login_required
@handle_api_errors
def get_rate_limit_stats():
    """Get rate limiting statistics"""
    try:
        from app import limiter
        
        rate_limit_service = get_rate_limit_service(limiter)
        
        if not rate_limit_service:
            return jsonify({
                'success': False,
                'error': 'Rate limit service not initialized'
            }), 503
        
        stats = rate_limit_service.get_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting rate limit stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@monitoring_api.route('/rate-limits/violations')
@login_required
@handle_api_errors
def get_rate_limit_violations():
    """Get rate limit violations"""
    try:
        from app import limiter
        
        rate_limit_service = get_rate_limit_service(limiter)
        
        if not rate_limit_service:
            return jsonify({
                'success': False,
                'error': 'Rate limit service not initialized'
            }), 503
        
        limit = request.args.get('limit', 100, type=int)
        violations = rate_limit_service.get_violations(limit=limit)
        
        return jsonify({
            'success': True,
            'violations': violations,
            'count': len(violations)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting rate limit violations: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@monitoring_api.route('/rate-limits/violators')
@login_required
@handle_api_errors
def get_top_violators():
    """Get top rate limit violators"""
    try:
        from app import limiter
        
        rate_limit_service = get_rate_limit_service(limiter)
        
        if not rate_limit_service:
            return jsonify({
                'success': False,
                'error': 'Rate limit service not initialized'
            }), 503
        
        limit = request.args.get('limit', 10, type=int)
        violators = rate_limit_service.get_top_violators(limit=limit)
        
        return jsonify({
            'success': True,
            'violators': violators,
            'count': len(violators)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting top violators: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
