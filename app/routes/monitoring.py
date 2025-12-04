"""
Monitoring and Metrics Endpoints
Provides health checks, metrics, and monitoring data
"""
from flask import Blueprint, jsonify, request, Response
from prometheus_flask_exporter import PrometheusMetrics
import psutil
import os
import time
import re
from datetime import datetime
from flask_login import login_required, current_user
from functools import wraps
from app.utils.feature_flags import FeatureFlags
from app.utils.prometheus_metrics import (
    get_metrics, update_system_metrics, 
    track_transaction, track_psp_commission
)


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

monitoring_bp = Blueprint('monitoring_enhanced', __name__, url_prefix='/api/v1/monitoring')


# Health check endpoint (no auth required)
@monitoring_bp.route('/health', methods=['GET'])
def health_check():
    """
    Basic health check endpoint
    Returns 200 if application is running
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'PipLinePro'
    }), 200


@monitoring_bp.route('/health/detailed', methods=['GET'])
@admin_required
def detailed_health_check():
    """
    Detailed health check with database and system info
    Requires admin authentication
    """
    from app import db
    
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'PipLinePro',
        'checks': {}
    }
    
    # Database check
    try:
        db.session.execute('SELECT 1')
        health_status['checks']['database'] = {
            'status': 'healthy',
            'response_time_ms': 0  # Could measure actual time
        }
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
    
    # System resources
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_status['checks']['system'] = {
            'status': 'healthy',
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_mb': memory.available / (1024 * 1024),
            'disk_percent': disk.percent,
            'disk_free_gb': disk.free / (1024 * 1024 * 1024)
        }
        
        # Warn if resources are high
        if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
            health_status['status'] = 'degraded'
            health_status['checks']['system']['warning'] = 'High resource usage'
            
    except Exception as e:
        health_status['checks']['system'] = {
            'status': 'unknown',
            'error': str(e)
        }
    
    # Environment info
    health_status['environment'] = {
        'flask_env': os.getenv('FLASK_ENV', 'unknown'),
        'debug': os.getenv('DEBUG', 'false'),
        'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
    }
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code


@monitoring_bp.route('/metrics/prometheus', methods=['GET'])
def prometheus_metrics():
    """
    Prometheus metrics endpoint
    No authentication required (Prometheus needs to scrape this)
    """
    if not FeatureFlags.ENABLE_PROMETHEUS_METRICS:
        return jsonify({'error': 'Prometheus metrics disabled'}), 404
    
    # Update system metrics before scraping
    update_system_metrics()
    
    # Return Prometheus format
    return Response(
        get_metrics(),
        mimetype='text/plain; version=0.0.4; charset=utf-8'
    )


@monitoring_bp.route('/metrics/system', methods=['GET'])
@admin_required
def system_metrics():
    """
    Get current system metrics
    Requires admin authentication
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Network stats (if available)
        try:
            net_io = psutil.net_io_counters()
            network_stats = {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }
        except:
            network_stats = None
        
        # Process info
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info()
        
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'cpu': {
                'percent': cpu_percent,
                'count': cpu_count,
                'per_cpu': psutil.cpu_percent(interval=0.1, percpu=True)
            },
            'memory': {
                'total_mb': memory.total / (1024 * 1024),
                'available_mb': memory.available / (1024 * 1024),
                'used_mb': memory.used / (1024 * 1024),
                'percent': memory.percent
            },
            'disk': {
                'total_gb': disk.total / (1024 * 1024 * 1024),
                'used_gb': disk.used / (1024 * 1024 * 1024),
                'free_gb': disk.free / (1024 * 1024 * 1024),
                'percent': disk.percent
            },
            'process': {
                'memory_mb': process_memory.rss / (1024 * 1024),
                'cpu_percent': process.cpu_percent(interval=0.1)
            }
        }
        
        if network_stats:
            metrics['network'] = network_stats
        
        return jsonify(metrics), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/metrics/database', methods=['GET'])
@admin_required
def database_metrics():
    """
    Get database metrics and connection pool info
    Requires admin authentication
    """
    from app import db
    from sqlalchemy import inspect, text
    
    try:
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'database': {}
        }
        
        # Get database type
        database_url = str(db.engine.url)
        if 'postgresql' in database_url:
            db_type = 'postgresql'
        elif 'sqlite' in database_url:
            db_type = 'sqlite'
        else:
            db_type = 'unknown'
        
        metrics['database']['type'] = db_type
        
        # Connection pool info
        pool = db.engine.pool
        metrics['database']['pool'] = {
            'size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'total_connections': pool.size() + pool.overflow()
        }
        
        # Table counts
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        metrics['database']['tables'] = len(tables)
        
        # Get row counts for main tables
        table_stats = {}
        for table in ['transactions', 'users', 'exchange_rates', 'audit_logs']:
            try:
                if table in tables:
                    result = db.session.execute(text(f'SELECT COUNT(*) FROM {table}'))
                    count = result.scalar()
                    table_stats[table] = count
            except:
                pass
        
        metrics['database']['table_stats'] = table_stats
        
        # Database size (PostgreSQL only)
        if db_type == 'postgresql':
            try:
                result = db.session.execute(text("SELECT pg_database_size(current_database())"))
                size_bytes = result.scalar()
                metrics['database']['size_mb'] = round(size_bytes / (1024 * 1024), 2)
            except:
                pass
        
        return jsonify(metrics), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/metrics/application', methods=['GET'])
@admin_required
def application_metrics():
    """
    Get application-specific metrics
    Requires admin authentication
    """
    try:
        from app.services.error_service import error_service
        
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'application': {
                'name': 'PipLinePro',
                'version': os.getenv('APP_VERSION', 'unknown'),
                'environment': os.getenv('FLASK_ENV', 'unknown')
            }
        }
        
        # Error stats
        if error_service:
            metrics['errors'] = {
                'total_tracked': len(error_service.error_history),
                'error_counts': error_service.error_counts
            }
        
        # Cache stats (if available)
        try:
            from app import advanced_cache
            cache_stats = advanced_cache.get_stats()
            metrics['cache'] = cache_stats
        except:
            pass
        
        # Uptime
        try:
            with open('logs/app_start_time.txt', 'r') as f:
                start_time = float(f.read().strip())
                uptime_seconds = time.time() - start_time
                metrics['application']['uptime_seconds'] = round(uptime_seconds, 2)
                metrics['application']['uptime_hours'] = round(uptime_seconds / 3600, 2)
        except:
            pass
        
        return jsonify(metrics), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/backups', methods=['GET'])
@admin_required
def list_backups():
    """
    List all available backups
    Requires admin authentication
    """
    try:
        from app.services.backup_service import get_backup_service
        
        backup_service = get_backup_service()
        backups = backup_service.list_backups()
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'count': len(backups),
            'backups': backups
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/backups/create', methods=['POST'])
@admin_required
def create_backup():
    """
    Create a new backup
    Requires admin authentication
    """
    try:
        from app.services.backup_service import get_backup_service
        from flask import current_app
        
        backup_service = get_backup_service(current_app)
        database_url = current_app.config.get('SQLALCHEMY_DATABASE_URI')
        
        success, message, backup_path = backup_service.create_backup(database_url)
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'backup_path': backup_path,
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def setup_prometheus_metrics(app):
    """
    Setup Prometheus metrics for the Flask app
    Call this during app initialization
    """
    try:
        # Check feature flag
        if not FeatureFlags.ENABLE_PROMETHEUS_METRICS:
            app.logger.info("Prometheus metrics disabled via feature flag")
            return None
        
        # Check if PrometheusMetrics is already initialized
        if hasattr(app, 'prometheus_metrics'):
            app.logger.info("Prometheus metrics already initialized")
            return app.prometheus_metrics
        
        metrics = PrometheusMetrics(app, path=None)  # Don't auto-register /metrics endpoint
        
        # Note: PrometheusMetrics already creates app_info metric automatically
        # We don't need to create it again to avoid duplicate metric error
        
        # Exclude health check from metrics (too noisy)
        # Prometheus expects regex patterns, not plain strings
        try:
            if hasattr(metrics, 'excluded_paths'):
                if metrics.excluded_paths is None:
                    metrics.excluded_paths = []
                if isinstance(metrics.excluded_paths, list):
                    # Convert string paths to regex patterns if needed
                    health_path_pattern = re.compile(r'/api/v1/monitoring/health')
                    # Check if pattern already exists (as regex or string)
                    pattern_exists = any(
                        (isinstance(p, re.Pattern) and p.pattern == health_path_pattern.pattern) or
                        (isinstance(p, str) and p == '/api/v1/monitoring/health')
                        for p in metrics.excluded_paths
                    )
                    if not pattern_exists:
                        metrics.excluded_paths.append(health_path_pattern)
        except (AttributeError, TypeError) as e:
            # If excluded_paths doesn't exist or isn't modifiable, skip
            app.logger.debug(f"Could not modify excluded_paths: {e}")
        
        # Store metrics instance on app
        app.prometheus_metrics = metrics
        
        # Note: app_info is already created by PrometheusMetrics
        # We can set it if needed, but it's optional
        # The prometheus_flask_exporter handles app_info automatically
        
        app.logger.info("Prometheus metrics enabled")
        return metrics
    except Exception as e:
        app.logger.warning(f"Failed to setup Prometheus metrics: {e}")
        return None

