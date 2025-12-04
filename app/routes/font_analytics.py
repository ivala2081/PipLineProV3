"""
Font Analytics Routes for PipLine Pro
Provides font performance insights, recommendations, and optimization tools
"""

from flask import Blueprint, jsonify, request, redirect, current_app
from app.services.font_optimization_service import FontOptimizationService
import logging

# Decimal/Float type mismatch prevention
from app.services.decimal_float_fix_service import decimal_float_service


logger = logging.getLogger(__name__)

font_analytics_bp = Blueprint('font_analytics', __name__, url_prefix='/font-analytics')

# Initialize font optimization service
font_service = FontOptimizationService()

@font_analytics_bp.route('/')
def font_analytics_dashboard():
    """Main font analytics dashboard"""
    try:
        stats = font_service.get_font_performance_stats()
        recommendations = font_service.get_font_recommendations()
        loading_strategy = font_service.get_font_loading_strategy()
        service_stats = font_service.get_service_stats()
        
        return redirect('http://localhost:3000/font-analytics')
    except Exception as e:
        logger.error(f"Error loading font analytics dashboard: {e}")
        return jsonify({"error": "Failed to load font analytics"}), 500

@font_analytics_bp.route('/api/stats')
def get_font_stats():
    """Get font performance statistics"""
    try:
        stats = font_service.get_font_performance_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting font stats: {e}")
        return jsonify({"error": "Failed to get font statistics"}), 500

@font_analytics_bp.route('/api/recommendations')
def get_font_recommendations():
    """Get font recommendations"""
    try:
        use_case = request.args.get('use_case')
        recommendations = font_service.get_font_recommendations(use_case)
        return jsonify(recommendations)
    except Exception as e:
        logger.error(f"Error getting font recommendations: {e}")
        return jsonify({"error": "Failed to get font recommendations"}), 500

@font_analytics_bp.route('/api/accessibility/<font_family>')
def get_font_accessibility(font_family):
    """Get accessibility analysis for a specific font"""
    try:
        accessibility = font_service.analyze_font_accessibility(font_family)
        return jsonify(accessibility)
    except Exception as e:
        logger.error(f"Error analyzing font accessibility: {e}")
        return jsonify({"error": "Failed to analyze font accessibility"}), 500

@font_analytics_bp.route('/api/loading-strategy')
def get_loading_strategy():
    """Get font loading strategy recommendations"""
    try:
        strategy = font_service.get_font_loading_strategy()
        return jsonify(strategy)
    except Exception as e:
        logger.error(f"Error getting loading strategy: {e}")
        return jsonify({"error": "Failed to get loading strategy"}), 500

@font_analytics_bp.route('/api/generate-css')
def generate_optimized_css():
    """Generate optimized font CSS"""
    try:
        optimize = request.args.get('optimize', 'true').lower() == 'true'
        css = font_service.generate_font_css(optimize_performance=optimize)
        return jsonify({
            "css": css,
            "optimized": optimize,
            "size_bytes": len(css.encode('utf-8'))
        })
    except Exception as e:
        logger.error(f"Error generating CSS: {e}")
        return jsonify({"error": "Failed to generate CSS"}), 500

@font_analytics_bp.route('/api/record-usage', methods=['POST'])
def record_font_usage():
    """Record font usage for analytics"""
    try:
        data = request.get_json()
        font_family = data.get('font_family')
        font_weight = data.get('font_weight', 400)
        load_time = data.get('load_time', 0.0)
        
        if not font_family:
            return jsonify({"error": "font_family is required"}), 400
        
        font_service.record_font_usage(font_family, font_weight, load_time)
        return jsonify({"success": True, "message": "Font usage recorded"})
    except Exception as e:
        logger.error(f"Error recording font usage: {e}")
        return jsonify({"error": "Failed to record font usage"}), 500

@font_analytics_bp.route('/api/cleanup', methods=['POST'])
def cleanup_old_metrics():
    """Clean up old font metrics"""
    try:
        days = request.json.get('days', 30) if request.is_json else 30
        font_service.cleanup_old_metrics(days)
        return jsonify({"success": True, "message": f"Cleaned up metrics older than {days} days"})
    except Exception as e:
        logger.error(f"Error cleaning up metrics: {e}")
        return jsonify({"error": "Failed to cleanup metrics"}), 500

@font_analytics_bp.route('/api/service-stats')
def get_service_stats():
    """Get font optimization service statistics"""
    try:
        stats = font_service.get_service_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting service stats: {e}")
        return jsonify({"error": "Failed to get service statistics"}), 500

@font_analytics_bp.route('/preview')
def font_preview():
    """Interactive font preview and testing page"""
    try:
        recommendations = font_service.get_font_recommendations()
        accessibility_data = {
            "Inter": font_service.analyze_font_accessibility("Inter"),
            "SF Mono": font_service.analyze_font_accessibility("SF Mono")
        }
        
        return redirect('http://localhost:3000/font-preview')
    except Exception as e:
        logger.error(f"Error loading font preview: {e}")
        return jsonify({"error": "Failed to load font preview"}), 500

@font_analytics_bp.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        return jsonify({
            "status": "healthy",
            "service": "Font Analytics",
            "metrics_count": len(font_service.font_metrics),
            "recommendations_count": len(font_service.recommendations)
        })
    except Exception as e:
        logger.error(f"Font analytics health check failed: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500 