"""
Database Management API endpoints
Provides database health monitoring, backup management, and maintenance operations
"""

from flask import Blueprint, jsonify, request, send_file
from flask_login import login_required, current_user
import os
import sqlite3
import subprocess
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import logging

from app import db
from app.utils.permission_decorators import require_main_admin
from flask import jsonify

logger = logging.getLogger(__name__)

database_management_bp = Blueprint('database_management', __name__)

# Helper functions for responses
def success_response(data, status_code=200):
    """Create a success response"""
    return jsonify({"success": True, "data": data}), status_code

def error_response(message, status_code=400):
    """Create an error response"""
    return jsonify({"success": False, "error": message}), status_code

@database_management_bp.route('/health', methods=['GET'])
@login_required
@require_main_admin
def get_database_health():
    """Get comprehensive database health information"""
    try:
        db_path = "instance/treasury_improved.db"
        
        if not os.path.exists(db_path):
            return error_response("Database file not found", 404)
        
        # Get file information
        file_size = os.path.getsize(db_path) / (1024 * 1024)  # MB
        last_modified = datetime.fromtimestamp(os.path.getmtime(db_path))
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check integrity
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()[0]
        
        # Get table counts
        tables = {
            'user': 'Users',
            '"transaction"': 'Transactions',
            'exchange_rate': 'Exchange Rates',
            'psp_commission_rate': 'PSP Commission Rates',
            'psp_devir': 'PSP Devir Records',
            'psp_kasa_top': 'PSP Kasa Top Records',
            'audit_log': 'Audit Logs'
        }
        
        table_stats = {}
        total_records = 0
        for table, name in tables.items():
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                total_records += count
                table_stats[name] = count
            except sqlite3.OperationalError:
                table_stats[name] = 0
        
        # Get performance metrics
        cursor.execute("PRAGMA page_count")
        page_count = cursor.fetchone()[0]
        cursor.execute("PRAGMA page_size")
        page_size = cursor.fetchone()[0]
        db_size = (page_count * page_size) / (1024 * 1024)
        
        cursor.execute("PRAGMA freelist_count")
        free_pages = cursor.fetchone()[0]
        fragmentation = (free_pages / page_count * 100) if page_count > 0 else 0
        
        conn.close()
        
        # Determine health status
        health_status = "healthy"
        if fragmentation > 20:
            health_status = "warning"
        elif integrity != "ok":
            health_status = "critical"
        
        return success_response({
            'status': health_status,
            'file_info': {
                'path': db_path,
                'size_mb': round(file_size, 2),
                'last_modified': last_modified.isoformat()
            },
            'integrity': integrity,
            'statistics': {
                'tables': table_stats,
                'total_records': total_records,
                'database_size_mb': round(db_size, 2),
                'fragmentation_percent': round(fragmentation, 2)
            },
            'recommendations': {
                'optimize': fragmentation > 10,
                'backup': True,
                'message': 'Database is healthy' if health_status == 'healthy' else 'Consider optimization'
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting database health: {e}")
        return error_response(f"Error getting database health: {str(e)}", 500)

@database_management_bp.route('/backups', methods=['GET'])
@login_required
@require_main_admin
def list_backups():
    """List all available database backups"""
    try:
        backup_dir = "backups"
        
        if not os.path.exists(backup_dir):
            return success_response({
                'backups': [],
                'total_count': 0,
                'total_size_mb': 0
            })
        
        backups = []
        total_size = 0
        
        for filename in os.listdir(backup_dir):
            if filename.startswith("treasury_backup_") and filename.endswith(".db"):
                filepath = os.path.join(backup_dir, filename)
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                modified = datetime.fromtimestamp(os.path.getmtime(filepath))
                age_days = (datetime.now() - modified).days
                
                # Determine status
                if age_days == 0:
                    status = "fresh"
                elif age_days < 7:
                    status = "recent"
                elif age_days < 30:
                    status = "old"
                else:
                    status = "very_old"
                
                backups.append({
                    'filename': filename,
                    'size_mb': round(size_mb, 2),
                    'created_at': modified.isoformat(),
                    'age_days': age_days,
                    'status': status
                })
                total_size += size_mb
        
        # Sort by date (newest first)
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        
        return success_response({
            'backups': backups,
            'total_count': len(backups),
            'total_size_mb': round(total_size, 2),
            'latest_backup': backups[0] if backups else None
        })
        
    except Exception as e:
        logger.error(f"Error listing backups: {e}")
        return error_response(f"Error listing backups: {str(e)}", 500)

@database_management_bp.route('/backup', methods=['POST'])
@login_required
@require_main_admin
def create_backup():
    """Create a new database backup"""
    try:
        # Run backup script
        result = subprocess.run(
            ['python', 'backup_sqlite.py'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # Get the newly created backup
            backup_dir = "backups"
            if os.path.exists(backup_dir):
                backups = [f for f in os.listdir(backup_dir) 
                          if f.startswith("treasury_backup_") and f.endswith(".db")]
                if backups:
                    latest_backup = max(backups)
                    backup_path = os.path.join(backup_dir, latest_backup)
                    size_mb = os.path.getsize(backup_path) / (1024 * 1024)
                    
                    logger.info(f"Backup created successfully: {latest_backup}")
                    return success_response({
                        'message': 'Backup created successfully',
                        'filename': latest_backup,
                        'size_mb': round(size_mb, 2),
                        'created_at': datetime.now().isoformat()
                    })
            
            return success_response({'message': 'Backup created successfully'})
        else:
            logger.error(f"Backup failed: {result.stderr}")
            return error_response(f"Backup failed: {result.stderr}", 500)
            
    except subprocess.TimeoutExpired:
        return error_response("Backup operation timed out", 500)
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return error_response(f"Error creating backup: {str(e)}", 500)

@database_management_bp.route('/optimize', methods=['POST'])
@login_required
@require_main_admin
def optimize_database():
    """Optimize database (VACUUM operation)"""
    try:
        db_path = "instance/treasury_improved.db"
        
        if not os.path.exists(db_path):
            return error_response("Database file not found", 404)
        
        # Create backup before optimization
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        backup_filename = f"pre_optimize_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        shutil.copy2(db_path, backup_path)
        
        # Perform VACUUM
        conn = sqlite3.connect(db_path)
        conn.execute("VACUUM")
        conn.close()
        
        logger.info("Database optimized successfully")
        return success_response({
            'message': 'Database optimized successfully',
            'backup_created': backup_filename
        })
        
    except Exception as e:
        logger.error(f"Error optimizing database: {e}")
        return error_response(f"Error optimizing database: {str(e)}", 500)

@database_management_bp.route('/system-status', methods=['GET'])
@login_required
@require_main_admin
def get_system_status():
    """Get overall system status including disk space and multi-user readiness"""
    try:
        # Get disk space
        import shutil as disk_util
        total, used, free = disk_util.disk_usage(".")
        disk_info = {
            'total_gb': round(total / (1024**3), 2),
            'used_gb': round(used / (1024**3), 2),
            'free_gb': round(free / (1024**3), 2),
            'usage_percent': round((used / total) * 100, 1)
        }
        
        # Determine disk status
        if disk_info['free_gb'] < 1:
            disk_status = "critical"
        elif disk_info['free_gb'] < 5:
            disk_status = "warning"
        else:
            disk_status = "healthy"
        
        # Get database type
        db_url = os.getenv('DATABASE_URL', 'sqlite:///instance/treasury_improved.db')
        db_type = 'sqlite' if 'sqlite' in db_url else 'postgresql' if 'postgresql' in db_url else 'unknown'
        
        # Multi-user readiness
        if db_type == 'sqlite':
            multi_user_status = {
                'ready': False,
                'max_recommended_users': 3,
                'current_type': 'SQLite',
                'recommendation': 'Suitable for 1-3 concurrent users. Migrate to PostgreSQL for 5+ users.'
            }
        else:
            multi_user_status = {
                'ready': True,
                'max_recommended_users': 'unlimited',
                'current_type': 'PostgreSQL',
                'recommendation': 'Database supports unlimited concurrent users.'
            }
        
        return success_response({
            'disk_space': disk_info,
            'disk_status': disk_status,
            'database_type': db_type,
            'multi_user': multi_user_status,
            'overall_status': 'healthy' if disk_status == 'healthy' else disk_status
        })
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return error_response(f"Error getting system status: {str(e)}", 500)

@database_management_bp.route('/download-backup/<filename>', methods=['GET'])
@login_required
@require_main_admin
def download_backup(filename):
    """Download a specific backup file"""
    try:
        # Validate filename
        if not filename.startswith("treasury_backup_") and not filename.startswith("pre_optimize_backup_"):
            return error_response("Invalid backup filename", 400)
        
        backup_path = os.path.join("backups", filename)
        
        if not os.path.exists(backup_path):
            return error_response("Backup file not found", 404)
        
        return send_file(
            backup_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/x-sqlite3'
        )
        
    except Exception as e:
        logger.error(f"Error downloading backup: {e}")
        return error_response(f"Error downloading backup: {str(e)}", 500)

@database_management_bp.route('/delete-backup/<filename>', methods=['DELETE'])
@login_required
@require_main_admin
def delete_backup(filename):
    """Delete a specific backup file"""
    try:
        # Validate filename
        if not filename.startswith("treasury_backup_") and not filename.startswith("pre_optimize_backup_"):
            return error_response("Invalid backup filename", 400)
        
        backup_path = os.path.join("backups", filename)
        
        if not os.path.exists(backup_path):
            return error_response("Backup file not found", 404)
        
        # Don't allow deleting the most recent backup
        backup_dir = "backups"
        backups = sorted([f for f in os.listdir(backup_dir) 
                         if f.startswith("treasury_backup_") and f.endswith(".db")])
        
        if len(backups) == 1 and filename == backups[0]:
            return error_response("Cannot delete the only backup", 400)
        
        os.remove(backup_path)
        logger.info(f"Backup deleted: {filename}")
        
        return success_response({'message': f'Backup {filename} deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting backup: {e}")
        return error_response(f"Error deleting backup: {str(e)}", 500)
