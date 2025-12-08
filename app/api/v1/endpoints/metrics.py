"""
Prometheus Metrics Endpoint
Exposes metrics in Prometheus format
"""
from flask import Blueprint, Response, current_app
from app.utils.prometheus_metrics import generate_latest

metrics_bp = Blueprint('metrics', __name__)


@metrics_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """
    Prometheus metrics endpoint
    
    Returns:
        Prometheus-formatted metrics
    """
    try:
        # Generate Prometheus metrics
        metrics_data = generate_latest()
        
        return Response(
            metrics_data,
            mimetype='text/plain; version=0.0.4; charset=utf-8'
        )
    except Exception as e:
        current_app.logger.error(f"Error generating metrics: {e}")
        return Response(
            f"# Error generating metrics: {e}\n",
            status=500,
            mimetype='text/plain'
        )


@metrics_bp.route('/metrics/health', methods=['GET'])
def metrics_health():
    """
    Health check for metrics endpoint
    
    Returns:
        JSON response with metrics health status
    """
    try:
        # Try to generate metrics to verify it works
        generate_latest()
        
        return {
            'status': 'healthy',
            'message': 'Metrics endpoint is working',
            'format': 'prometheus'
        }, 200
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': f'Metrics endpoint error: {str(e)}'
        }, 500

