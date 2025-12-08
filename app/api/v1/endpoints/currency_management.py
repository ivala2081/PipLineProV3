"""
Currency Management API endpoints
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
import logging

from app.services.currency_fixer_service import currency_fixer_service

logger = logging.getLogger(__name__)

currency_management_api = Blueprint('currency_management_api', __name__)

@currency_management_api.route('/health', methods=['GET'])
@login_required
def get_currency_health():
    """Get currency health status"""
    try:
        # Check if user has admin privileges
        if not hasattr(current_user, 'admin_level') or current_user.admin_level < 3:
            return jsonify({
                'error': 'Insufficient privileges',
                'message': 'Currency management requires admin level 3 or higher'
            }), 403
        
        logger.info(f"Currency health check requested by {current_user.username}")
        
        report = currency_fixer_service.get_currency_health_report()
        
        return jsonify({
            'success': True,
            'health_report': report
        })
        
    except Exception as e:
        logger.error(f"Error getting currency health: {e}")
        return jsonify({
            'error': 'Failed to get currency health',
            'message': str(e)
        }), 500

@currency_management_api.route('/fix', methods=['POST'])
@login_required
def fix_currencies():
    """Run automated currency fixes"""
    try:
        # Check if user has admin privileges
        if not hasattr(current_user, 'admin_level') or current_user.admin_level < 3:
            return jsonify({
                'error': 'Insufficient privileges',
                'message': 'Currency fixing requires admin level 3 or higher'
            }), 403
        
        data = request.get_json() or {}
        dry_run = data.get('dry_run', False)
        
        logger.info(f"Currency fix requested by {current_user.username} (dry_run: {dry_run})")
        
        if dry_run:
            # For dry run, just return the health report with what would be fixed
            health_report = currency_fixer_service.get_currency_health_report()
            return jsonify({
                'success': True,
                'dry_run': True,
                'message': 'Dry run completed - no changes made',
                'would_fix': health_report.get('issues', {}),
                'health_report': health_report
            })
        else:
            # Run actual fixes
            report = currency_fixer_service.run_full_currency_audit_and_fix()
            
            return jsonify({
                'success': True,
                'dry_run': False,
                'message': 'Currency fixes completed',
                'fix_report': report
            })
        
    except Exception as e:
        logger.error(f"Error fixing currencies: {e}")
        return jsonify({
            'error': 'Failed to fix currencies',
            'message': str(e)
        }), 500

@currency_management_api.route('/standardize', methods=['POST'])
@login_required
def standardize_currencies():
    """Standardize currency codes only"""
    try:
        # Check if user has admin privileges
        if not hasattr(current_user, 'admin_level') or current_user.admin_level < 2:
            return jsonify({
                'error': 'Insufficient privileges',
                'message': 'Currency standardization requires admin level 2 or higher'
            }), 403
        
        logger.info(f"Currency standardization requested by {current_user.username}")
        
        # Run just the standardization step
        fixer = currency_fixer_service
        fixer._standardize_currency_codes()
        
        return jsonify({
            'success': True,
            'message': 'Currency codes standardized successfully'
        })
        
    except Exception as e:
        logger.error(f"Error standardizing currencies: {e}")
        return jsonify({
            'error': 'Failed to standardize currencies',
            'message': str(e)
        }), 500
