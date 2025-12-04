"""
Color Enhancement Routes
=======================

This module provides Flask routes for the color enhancement service,
allowing users to analyze and improve color contrast issues through
the web interface.

Features:
- Color analysis dashboard
- Real-time contrast checking
- Improvement suggestions
- Professional color palette management
- Automated fixes application
"""

from flask import Blueprint, redirect, jsonify, request, current_app
from flask_login import login_required, current_user
import logging

from app.services.color_enhancement_service import get_color_service, initialize_color_service

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
color_enhancement_bp = Blueprint('color_enhancement', __name__, url_prefix='/color-enhancement')

@color_enhancement_bp.route('/')
@login_required
def color_dashboard():
    """Color enhancement dashboard."""
    try:
        # Initialize color service
        color_service = get_color_service()
        
        # Get analysis report
        report = color_service.get_analysis_report()
        
        return redirect('http://localhost:3000/color-enhancement')
    except Exception as e:
        logger.error(f"Error in color dashboard: {e}")
        return redirect('http://localhost:3000/color-enhancement')

@color_enhancement_bp.route('/analyze', methods=['POST'])
@login_required
def analyze_colors():
    """Analyze application colors and return results."""
    try:
        color_service = get_color_service()
        results = color_service.analyze_application_colors()
        
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception as e:
        logger.error(f"Error analyzing colors: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@color_enhancement_bp.route('/improvements', methods=['GET'])
@login_required
def get_improvements():
    """Get CSS improvements for detected issues."""
    try:
        color_service = get_color_service()
        css_improvements = color_service.generate_css_improvements()
        
        return jsonify({
            'success': True,
            'css': css_improvements
        })
    except Exception as e:
        logger.error(f"Error getting improvements: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@color_enhancement_bp.route('/apply-improvements', methods=['POST'])
@login_required
def apply_improvements():
    """Apply color improvements automatically."""
    try:
        color_service = get_color_service()
        success = color_service.apply_improvements_automatically()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Improvements applied successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to apply improvements'
            }), 500
    except Exception as e:
        logger.error(f"Error applying improvements: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@color_enhancement_bp.route('/test-contrast', methods=['POST'])
@login_required
def test_contrast():
    """Test contrast ratio for specific color combinations."""
    try:
        data = request.get_json()
        foreground = data.get('foreground')
        background = data.get('background')
        element_type = data.get('element_type', 'text')
        
        if not foreground or not background:
            return jsonify({
                'success': False,
                'error': 'Foreground and background colors are required'
            }), 400
        
        color_service = get_color_service()
        analyzer = color_service.analyzer
        
        # Calculate contrast ratio
        contrast_ratio = analyzer.calculate_contrast_ratio(foreground, background)
        aa_passed, aaa_passed = analyzer.check_wcag_compliance(contrast_ratio, element_type)
        
        # Get suggestions if needed
        suggested_fg = None
        suggested_bg = None
        if not aa_passed:
            suggested_fg, suggested_bg = analyzer.suggest_better_colors(
                foreground, background, element_type
            )
        
        return jsonify({
            'success': True,
            'data': {
                'contrast_ratio': contrast_ratio,
                'wcag_aa_passed': aa_passed,
                'wcag_aaa_passed': aaa_passed,
                'suggested_foreground': suggested_fg,
                'suggested_background': suggested_bg
            }
        })
    except Exception as e:
        logger.error(f"Error testing contrast: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@color_enhancement_bp.route('/professional-palette', methods=['GET'])
@login_required
def get_professional_palette():
    """Get the professional color palette."""
    try:
        color_service = get_color_service()
        palette = color_service.analyzer.PROFESSIONAL_COLORS
        
        return jsonify({
            'success': True,
            'data': palette
        })
    except Exception as e:
        logger.error(f"Error getting professional palette: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@color_enhancement_bp.route('/report', methods=['GET'])
@login_required
def get_report():
    """Get detailed analysis report."""
    try:
        color_service = get_color_service()
        report = color_service.get_analysis_report()
        
        return jsonify({
            'success': True,
            'data': report
        })
    except Exception as e:
        logger.error(f"Error getting report: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Register blueprint with app
def init_color_enhancement_routes(app):
    """Initialize color enhancement routes with the Flask app."""
    app.register_blueprint(color_enhancement_bp)
    logger.info("Color enhancement routes registered") 