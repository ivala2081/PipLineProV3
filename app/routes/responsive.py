"""
Responsive Automation Routes
Handles responsive design automation endpoints
"""

from flask import Blueprint, request, jsonify, redirect, current_app
from app.services.responsive_automation_service import responsive_automation_service
import logging
from datetime import datetime

# Decimal/Float type mismatch prevention
from app.services.decimal_float_fix_service import decimal_float_service


logger = logging.getLogger(__name__)

responsive_bp = Blueprint('responsive', __name__, url_prefix='/responsive')

@responsive_bp.route('/css/<int:viewport_width>')
def get_responsive_css(viewport_width):
    """
    Get responsive CSS for specific viewport width
    
    Args:
        viewport_width: Target viewport width in pixels
        
    Returns:
        CSS content with appropriate headers
    """
    try:
        css_content = responsive_automation_service.generate_responsive_css(viewport_width)
        
        if not css_content:
            return jsonify({'error': 'Failed to generate responsive CSS'}), 500
        
        response = current_app.response_class(
            css_content,
            status=200,
            mimetype='text/css'
        )
        
        # Add cache headers
        response.headers['Cache-Control'] = 'public, max-age=300'  # 5 minutes
        response.headers['Content-Type'] = 'text/css; charset=utf-8'
        
        return response
        
    except Exception as e:
        logger.error(f"Error serving responsive CSS: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@responsive_bp.route('/css')
def get_responsive_css_dynamic():
    """
    Get responsive CSS with dynamic viewport width from query parameter
    """
    try:
        viewport_width = request.args.get('width', 1200, type=int)
        
        # Validate viewport width
        if viewport_width < 320 or viewport_width > 2560:
            return jsonify({'error': 'Invalid viewport width'}), 400
        
        return get_responsive_css(viewport_width)
        
    except Exception as e:
        logger.error(f"Error serving dynamic responsive CSS: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@responsive_bp.route('/template/<template_name>')
def get_responsive_template(template_name):
    """
    Get responsive version of a template
    
    Args:
        template_name: Name of the template to process
        
    Returns:
        Processed template content
    """
    try:
        # Get context from query parameters
        context = {}
        for key, value in request.args.items():
            if key.startswith('ctx_'):
                context_key = key[4:]  # Remove 'ctx_' prefix
                context[context_key] = value
        
        # Generate responsive template
        template_content = responsive_automation_service.generate_responsive_template(
            template_name, context
        )
        
        if not template_content:
            return jsonify({'error': f'Template {template_name} not found'}), 404
        
        response = current_app.response_class(
            template_content,
            status=200,
            mimetype='text/html'
        )
        
        # Add cache headers
        response.headers['Cache-Control'] = 'public, max-age=600'  # 10 minutes
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        
        return response
        
    except Exception as e:
        logger.error(f"Error serving responsive template {template_name}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@responsive_bp.route('/config', methods=['GET'])
def get_responsive_config():
    """
    Get responsive configuration
    
    Returns:
        JSON configuration object
    """
    try:
        config = responsive_automation_service.get_responsive_config()
        return jsonify(config)
        
    except Exception as e:
        logger.error(f"Error getting responsive config: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@responsive_bp.route('/config', methods=['POST'])
def update_responsive_config():
    """
    Update responsive configuration
    
    Returns:
        Success status
    """
    try:
        config_data = request.get_json()
        
        if not config_data:
            return jsonify({'error': 'No configuration data provided'}), 400
        
        success = responsive_automation_service.update_responsive_config(config_data)
        
        if success:
            return jsonify({'message': 'Configuration updated successfully'})
        else:
            return jsonify({'error': 'Failed to update configuration'}), 500
            
    except Exception as e:
        logger.error(f"Error updating responsive config: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@responsive_bp.route('/stats')
def get_responsive_stats():
    """
    Get responsive automation statistics
    
    Returns:
        JSON statistics object
    """
    try:
        stats = responsive_automation_service.get_responsive_stats()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting responsive stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@responsive_bp.route('/cache/clear', methods=['POST'])
def clear_responsive_cache():
    """
    Clear responsive cache
    
    Returns:
        Success status
    """
    try:
        success = responsive_automation_service.cleanup_cache()
        
        if success:
            return jsonify({'message': 'Cache cleared successfully'})
        else:
            return jsonify({'error': 'Failed to clear cache'}), 500
            
    except Exception as e:
        logger.error(f"Error clearing responsive cache: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@responsive_bp.route('/preview')
def responsive_preview():
    """
    Preview responsive design with different viewport sizes
    
    Returns:
        HTML preview page
    """
    try:
        viewport_width = request.args.get('width', 1200, type=int)
        
        # Generate responsive CSS
        css_content = responsive_automation_service.generate_responsive_css(viewport_width)
        
        # Get responsive config
        config = responsive_automation_service.get_responsive_config()
        
        return redirect('http://localhost:3000/responsive')
        
    except Exception as e:
        logger.error(f"Error serving responsive preview: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@responsive_bp.route('/test')
def responsive_test():
    """
    Test responsive automation functionality
    
    Returns:
        Test results
    """
    try:
        test_results = {
            'css_generation': False,
            'template_processing': False,
            'config_management': False,
            'cache_management': False
        }
        
        # Test CSS generation
        try:
            css_content = responsive_automation_service.generate_responsive_css(1200)
            test_results['css_generation'] = bool(css_content)
        except Exception as e:
            logger.error(f"CSS generation test failed: {e}")
        
        # Test template processing
        try:
            template_content = responsive_automation_service.process_template_responsiveness(
                '<div class="card">Test</div>'
            )
            test_results['template_processing'] = bool(template_content)
        except Exception as e:
            logger.error(f"Template processing test failed: {e}")
        
        # Test config management
        try:
            config = responsive_automation_service.get_responsive_config()
            test_results['config_management'] = bool(config)
        except Exception as e:
            logger.error(f"Config management test failed: {e}")
        
        # Test cache management
        try:
            success = responsive_automation_service.cleanup_cache()
            test_results['cache_management'] = success
        except Exception as e:
            logger.error(f"Cache management test failed: {e}")
        
        return jsonify({
            'test_results': test_results,
            'all_passed': all(test_results.values()),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error running responsive tests: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@responsive_bp.route('/health')
def responsive_health():
    """
    Health check for responsive automation service
    
    Returns:
        Health status
    """
    try:
        stats = responsive_automation_service.get_responsive_stats()
        
        health_status = {
            'status': 'healthy',
            'service': 'responsive_automation',
            'timestamp': datetime.now().isoformat(),
            'stats': stats
        }
        
        return jsonify(health_status)
        
    except Exception as e:
        logger.error(f"Responsive health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'service': 'responsive_automation',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500 