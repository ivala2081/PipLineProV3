"""
Database management API endpoints
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.services.unified_database_service import unified_db_service as db_optimization_service
from app.utils.permission_decorators import require_any_admin
import logging

logger = logging.getLogger(__name__)

database_api = Blueprint('database_api', __name__)


@database_api.route('/health', methods=['GET'])
@login_required
@require_any_admin
def database_health():
    """Get database health status"""
    try:
        health_info = db_optimization_service.get_database_health()
        return jsonify({
            'status': 'success',
            'data': health_info
        }), 200
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Database health check failed',
            'error': str(e)
        }), 500


@database_api.route('/tables', methods=['GET'])
@login_required
@require_any_admin
def database_tables():
    """Get database tables analysis"""
    try:
        tables_info = db_optimization_service.analyze_tables()
        return jsonify({
            'status': 'success',
            'data': tables_info
        }), 200
        
    except Exception as e:
        logger.error(f"Database tables analysis failed: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Database tables analysis failed',
            'error': str(e)
        }), 500


@database_api.route('/optimize', methods=['POST'])
@login_required
@require_any_admin
def optimize_database():
    """Safely optimize database (SQLite only)"""
    try:
        optimization_result = db_optimization_service.optimize_sqlite_safely()
        
        if 'error' in optimization_result:
            return jsonify({
                'status': 'error',
                'message': optimization_result['error']
            }), 400
        
        return jsonify({
            'status': 'success',
            'message': 'Database optimization completed',
            'data': optimization_result
        }), 200
        
    except Exception as e:
        logger.error(f"Database optimization failed: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Database optimization failed',
            'error': str(e)
        }), 500
