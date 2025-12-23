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


@database_api.route('/indexes', methods=['GET'])
@login_required
@require_any_admin
def get_index_status():
    """Get database index status and information"""
    try:
        from app import db
        from app.utils.db_compat import get_database_type
        from sqlalchemy import text, inspect
        
        db_type = get_database_type()
        indexes_info = []
        
        if db_type == 'sqlite':
            # SQLite: Query sqlite_master for indexes
            result = db.session.execute(text("""
                SELECT 
                    name as index_name,
                    tbl_name as table_name,
                    sql as index_sql
                FROM sqlite_master
                WHERE type = 'index' 
                AND name NOT LIKE 'sqlite_%'
                ORDER BY tbl_name, name
            """))
            
            for row in result:
                indexes_info.append({
                    'index_name': row.index_name,
                    'table_name': row.table_name,
                    'sql': row.index_sql,
                    'database_type': 'sqlite'
                })
        
        elif db_type in ['postgresql', 'postgres']:
            # PostgreSQL: Query pg_indexes
            result = db.session.execute(text("""
                SELECT 
                    indexname as index_name,
                    tablename as table_name,
                    indexdef as index_sql
                FROM pg_indexes
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname
            """))
            
            for row in result:
                indexes_info.append({
                    'index_name': row.index_name,
                    'table_name': row.table_name,
                    'sql': row.index_sql,
                    'database_type': 'postgresql'
                })
        
        elif db_type in ['mssql', 'sqlserver']:
            # SQL Server: Query sys.indexes
            result = db.session.execute(text("""
                SELECT 
                    i.name as index_name,
                    OBJECT_NAME(i.object_id) as table_name,
                    COL_NAME(ic.object_id, ic.column_id) as column_name,
                    i.type_desc as index_type
                FROM sys.indexes i
                INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
                WHERE i.object_id > 0
                AND i.is_primary_key = 0
                AND i.is_unique_constraint = 0
                ORDER BY OBJECT_NAME(i.object_id), i.name
            """))
            
            indexes_dict = {}
            for row in result:
                key = f"{row.table_name}_{row.index_name}"
                if key not in indexes_dict:
                    indexes_dict[key] = {
                        'index_name': row.index_name,
                        'table_name': row.table_name,
                        'index_type': row.index_type,
                        'columns': [],
                        'database_type': 'mssql'
                    }
                indexes_dict[key]['columns'].append(row.column_name)
            
            indexes_info = list(indexes_dict.values())
        
        # Count performance indexes
        performance_indexes = [
            idx for idx in indexes_info 
            if 'idx_transaction' in idx['index_name'].lower() or 'idx_' in idx['index_name'].lower()
        ]
        
        return jsonify({
            'status': 'success',
            'data': {
                'database_type': db_type,
                'total_indexes': len(indexes_info),
                'performance_indexes': len(performance_indexes),
                'indexes': indexes_info,
                'performance_indexes_detail': performance_indexes
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get index status: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get index status',
            'error': str(e)
        }), 500
