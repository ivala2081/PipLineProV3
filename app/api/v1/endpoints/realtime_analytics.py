"""
Real-time analytics endpoints for PipLinePro
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
import logging
from app.services.real_time_analytics_service import get_real_time_analytics
from app.utils.unified_logger import get_logger

logger = logging.getLogger(__name__)
api_logger = get_logger('app.api.realtime_analytics')

realtime_analytics_api = Blueprint('realtime_analytics_api', __name__)

@realtime_analytics_api.route('/metrics')
@login_required
def get_realtime_metrics():
    """Get real-time analytics metrics"""
    try:
        api_logger.info("API Request")
        
        analytics_service = get_real_time_analytics()
        metrics = analytics_service.get_real_time_metrics()
        
        api_logger.info("API Request")
        return jsonify(metrics), 200
        
    except Exception as e:
        logger.error(f"Error getting real-time metrics: {str(e)}")
        api_logger.info("API Request")
        return jsonify({
            'error': 'Failed to retrieve real-time metrics',
            'message': str(e)
        }), 500

@realtime_analytics_api.route('/dashboard')
@login_required
def get_realtime_dashboard():
    """Get real-time dashboard data"""
    try:
        api_logger.info("API Request")
        
        analytics_service = get_real_time_analytics()
        metrics = analytics_service.get_real_time_metrics()
        
        # Format for dashboard consumption
        dashboard_data = {
            'timestamp': metrics.get('timestamp'),
            'summary': {
                'total_transactions': metrics.get('today', {}).get('total_transactions', 0),
                'total_revenue': metrics.get('today', {}).get('total_revenue', 0),
                'average_transaction': metrics.get('today', {}).get('average_transaction', 0),
                'active_psps': len(metrics.get('recent_activity', {}).get('active_psps', [])),
                'alerts_count': len(metrics.get('alerts', []))
            },
            'charts': {
                'hourly_breakdown': metrics.get('today', {}).get('hourly_breakdown', []),
                'psp_breakdown': metrics.get('today', {}).get('psp_breakdown', []),
                'currency_breakdown': metrics.get('today', {}).get('currency_breakdown', [])
            },
            'recent_activity': metrics.get('recent_activity', {}),
            'performance': metrics.get('performance', {}),
            'alerts': metrics.get('alerts', []),
            'trends': metrics.get('trends', {})
        }
        
        api_logger.info("API Request")
        return jsonify(dashboard_data), 200
        
    except Exception as e:
        logger.error(f"Error getting real-time dashboard: {str(e)}")
        api_logger.info("API Request")
        return jsonify({
            'error': 'Failed to retrieve real-time dashboard',
            'message': str(e)
        }), 500

@realtime_analytics_api.route('/psp/<psp_name>/performance')
@login_required
def get_psp_performance(psp_name):
    """Get real-time performance data for a specific PSP"""
    try:
        api_logger.info("API Request")
        
        analytics_service = get_real_time_analytics()
        performance_data = analytics_service.get_psp_performance_stream(psp_name)
        
        api_logger.info("API Request")
        return jsonify({
            'psp_name': psp_name,
            'performance_data': performance_data,
            'count': len(performance_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting PSP performance: {str(e)}")
        api_logger.info("API Request")
        return jsonify({
            'error': 'Failed to retrieve PSP performance data',
            'message': str(e)
        }), 500

@realtime_analytics_api.route('/revenue/stream')
@login_required
def get_revenue_stream():
    """Get revenue stream data"""
    try:
        hours = request.args.get('hours', 24, type=int)
        hours = min(max(hours, 1), 168)  # Limit between 1 and 168 hours (1 week)
        
        api_logger.info("API Request")
        
        analytics_service = get_real_time_analytics()
        revenue_data = analytics_service.get_revenue_stream(hours)
        
        api_logger.info("API Request")
        return jsonify({
            'hours': hours,
            'revenue_stream': revenue_data,
            'data_points': len(revenue_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting revenue stream: {str(e)}")
        api_logger.info("API Request")
        return jsonify({
            'error': 'Failed to retrieve revenue stream',
            'message': str(e)
        }), 500

@realtime_analytics_api.route('/alerts')
@login_required
def get_active_alerts():
    """Get active system alerts"""
    try:
        api_logger.info("API Request")
        
        analytics_service = get_real_time_analytics()
        metrics = analytics_service.get_real_time_metrics()
        alerts = metrics.get('alerts', [])
        
        # Filter by severity if requested
        severity = request.args.get('severity')
        if severity:
            alerts = [alert for alert in alerts if alert.get('severity') == severity]
        
        api_logger.info("API Request")
        return jsonify({
            'alerts': alerts,
            'count': len(alerts),
            'severity_filter': severity
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        api_logger.info("API Request")
        return jsonify({
            'error': 'Failed to retrieve alerts',
            'message': str(e)
        }), 500

@realtime_analytics_api.route('/trends')
@login_required
def get_trends():
    """Get trend analysis data"""
    try:
        api_logger.info("API Request")
        
        analytics_service = get_real_time_analytics()
        metrics = analytics_service.get_real_time_metrics()
        trends = metrics.get('trends', {})
        
        api_logger.info("API Request")
        return jsonify(trends), 200
        
    except Exception as e:
        logger.error(f"Error getting trends: {str(e)}")
        api_logger.info("API Request")
        return jsonify({
            'error': 'Failed to retrieve trends',
            'message': str(e)
        }), 500

@realtime_analytics_api.route('/performance')
@login_required
def get_performance_metrics():
    """Get real-time performance metrics"""
    try:
        api_logger.info("API Request")
        
        analytics_service = get_real_time_analytics()
        metrics = analytics_service.get_real_time_metrics()
        performance = metrics.get('performance', {})
        
        api_logger.info("API Request")
        return jsonify(performance), 200
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        api_logger.info("API Request")
        return jsonify({
            'error': 'Failed to retrieve performance metrics',
            'message': str(e)
        }), 500

@realtime_analytics_api.route('/status')
@login_required
def get_service_status():
    """Get real-time analytics service status"""
    try:
        api_logger.info("API Request")
        
        analytics_service = get_real_time_analytics()
        metrics = analytics_service.get_real_time_metrics()
        
        # Determine service health
        alerts = metrics.get('alerts', [])
        error_rate = metrics.get('performance', {}).get('error_rate', 0)
        response_time = metrics.get('performance', {}).get('response_time_avg', 0)
        
        health_status = "healthy"
        if error_rate > 5.0 or response_time > 2.0:
            health_status = "degraded"
        if error_rate > 10.0 or response_time > 5.0:
            health_status = "unhealthy"
        
        status_data = {
            'service': 'real_time_analytics',
            'status': health_status,
            'timestamp': metrics.get('timestamp'),
            'metrics_available': bool(metrics.get('today')),
            'alerts_count': len(alerts),
            'error_rate': error_rate,
            'response_time': response_time,
            'last_update': metrics.get('timestamp')
        }
        
        status_code = 200 if health_status == "healthy" else 503
        api_logger.info("API Request")
        return jsonify(status_data), status_code
        
    except Exception as e:
        logger.error(f"Error getting service status: {str(e)}")
        api_logger.info("API Request")
        return jsonify({
            'service': 'real_time_analytics',
            'status': 'error',
            'error': str(e),
            'timestamp': None
        }), 500
