"""
Configuration Management API Endpoints
Provides API access to configuration settings and management
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from typing import Dict, Any
import logging

from app.services.config_manager import (
    get_config_manager, ConfigCategory, ConfigValidationError
)
from app.utils.unified_error_handler import handle_api_errors
from app.utils.unified_logger import get_logger

logger = get_logger("ConfigAPI")

config_api = Blueprint('config_api', __name__)


@config_api.route('/summary')
@login_required
@handle_api_errors
def get_config_summary():
    """Get configuration summary (non-sensitive settings only)"""
    try:
        config_manager = get_config_manager()
        summary = config_manager.get_summary()
        
        # Redact sensitive information
        if 'database' in summary:
            db_url = summary['database'].get('database_url', '')
            if db_url:
                # Redact credentials from URL
                if '@' in db_url:
                    summary['database']['database_url'] = '***REDACTED***'
        
        return jsonify({
            'success': True,
            'config': summary
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting config summary: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@config_api.route('/database')
@login_required
@handle_api_errors
def get_database_config():
    """Get database configuration"""
    try:
        config_manager = get_config_manager()
        db_config = config_manager.get_database_config()
        
        # Redact database URL
        if 'database_url' in db_config:
            db_config['database_url'] = '***REDACTED***'
        
        return jsonify({
            'success': True,
            'config': db_config
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting database config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@config_api.route('/security')
@login_required
@handle_api_errors
def get_security_config():
    """Get security configuration"""
    try:
        config_manager = get_config_manager()
        security_config = config_manager.get_security_config()
        
        return jsonify({
            'success': True,
            'config': security_config
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting security config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@config_api.route('/cache')
@login_required
@handle_api_errors
def get_cache_config():
    """Get cache configuration"""
    try:
        config_manager = get_config_manager()
        cache_config = config_manager.get_cache_config()
        
        return jsonify({
            'success': True,
            'config': cache_config
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting cache config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@config_api.route('/performance')
@login_required
@handle_api_errors
def get_performance_config():
    """Get performance configuration"""
    try:
        config_manager = get_config_manager()
        perf_config = config_manager.get_performance_config()
        
        return jsonify({
            'success': True,
            'config': perf_config
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting performance config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@config_api.route('/logging')
@login_required
@handle_api_errors
def get_logging_config():
    """Get logging configuration"""
    try:
        config_manager = get_config_manager()
        logging_config = config_manager.get_logging_config()
        
        return jsonify({
            'success': True,
            'config': logging_config
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting logging config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@config_api.route('/features')
@login_required
@handle_api_errors
def get_feature_flags():
    """Get feature flags"""
    try:
        config_manager = get_config_manager()
        features = config_manager.get_feature_flags()
        
        return jsonify({
            'success': True,
            'features': features
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting feature flags: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@config_api.route('/category/<category>')
@login_required
@handle_api_errors
def get_config_by_category(category: str):
    """Get configuration by category"""
    try:
        config_manager = get_config_manager()
        
        # Map string to enum
        category_map = {
            'security': ConfigCategory.SECURITY,
            'database': ConfigCategory.DATABASE,
            'cache': ConfigCategory.CACHE,
            'logging': ConfigCategory.LOGGING,
            'performance': ConfigCategory.PERFORMANCE,
            'feature': ConfigCategory.FEATURE,
            'integration': ConfigCategory.INTEGRATION,
            'ui': ConfigCategory.UI,
        }
        
        if category not in category_map:
            return jsonify({
                'success': False,
                'error': f'Invalid category: {category}'
            }), 400
        
        config_category = category_map[category]
        config_data = config_manager.get_all(category=config_category)
        
        # Redact sensitive information
        filtered_config = {}
        for key, value in config_data.items():
            if any(sensitive in key.upper() for sensitive in ['SECRET', 'PASSWORD', 'TOKEN', 'KEY']):
                filtered_config[key] = '***REDACTED***'
            else:
                filtered_config[key] = value
        
        return jsonify({
            'success': True,
            'category': category,
            'config': filtered_config
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting config by category: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@config_api.route('/validate', methods=['POST'])
@login_required
@handle_api_errors
def validate_config():
    """Validate configuration value"""
    try:
        data = request.get_json()
        key = data.get('key')
        value = data.get('value')
        category = data.get('category')
        
        if not key or value is None:
            return jsonify({
                'success': False,
                'error': 'Key and value are required'
            }), 400
        
        config_manager = get_config_manager()
        
        # Map category if provided
        config_category = None
        if category:
            category_map = {
                'security': ConfigCategory.SECURITY,
                'database': ConfigCategory.DATABASE,
                'cache': ConfigCategory.CACHE,
                'logging': ConfigCategory.LOGGING,
                'performance': ConfigCategory.PERFORMANCE,
            }
            config_category = category_map.get(category)
        
        is_valid = config_manager.validate(key, value, category=config_category)
        
        return jsonify({
            'success': True,
            'valid': is_valid,
            'key': key,
            'value': value
        }), 200
        
    except ConfigValidationError as e:
        return jsonify({
            'success': False,
            'valid': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error validating config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@config_api.route('/export')
@login_required
@handle_api_errors
def export_config():
    """Export configuration (excluding secrets)"""
    try:
        include_secrets = request.args.get('include_secrets', 'false').lower() == 'true'
        
        # Only allow admins to export with secrets
        if include_secrets and (not current_user.is_authenticated or current_user.role != 'admin'):
            return jsonify({
                'success': False,
                'error': 'Admin access required to export secrets'
            }), 403
        
        config_manager = get_config_manager()
        exported = config_manager.export(include_secrets=include_secrets)
        
        return jsonify({
            'success': True,
            'config': exported,
            'secrets_included': include_secrets
        }), 200
        
    except Exception as e:
        logger.error(f"Error exporting config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

