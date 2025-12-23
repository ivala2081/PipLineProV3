"""
Performance monitoring endpoints for PipLinePro
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import text
import logging
import time
import psutil
from datetime import datetime, timezone
from app.services.enhanced_cache_service import cache_service
from app.services.unified_database_service import get_unified_db_service as get_query_optimizer
from app.services.security_service import get_security_service
from app.utils.unified_logger import get_logger

logger = logging.getLogger(__name__)
api_logger = get_logger('app.api.performance')

performance_api = Blueprint('performance_api', __name__)

@performance_api.route('/metrics')
@login_required
def get_performance_metrics():
    """Get comprehensive performance metrics"""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Cache metrics
        cache_stats = cache_service.get_stats()
        
        # Query performance metrics
        query_optimizer = get_query_optimizer()
        query_stats = query_optimizer.get_query_stats()
        
        # Security metrics
        security_service = get_security_service()
        security_metrics = security_service.get_security_metrics()
        
        # Database performance
        try:
            from app.services.unified_database_service import UnifiedDatabaseService as DatabaseOptimizationService
            db_stats = DatabaseOptimizationService.get_database_stats()
        except Exception as e:
            logger.warning(f"Failed to get database stats: {e}")
            db_stats = {"error": str(e)}
        
        # Connection pool metrics
        pool_stats = {}
        try:
            from app.services.connection_pool_monitor import get_pool_monitor
            from app import db
            pool_monitor = get_pool_monitor(db.engine)
            if pool_monitor:
                pool_stats = pool_monitor.get_pool_stats()
        except Exception as e:
            logger.warning(f"Failed to get pool stats: {e}")
            pool_stats = {"error": str(e)}
        
        # Performance optimizer stats
        optimizer_stats = {}
        try:
            from app.services.performance_optimizer import get_performance_optimizer
            optimizer = get_performance_optimizer()
            optimizer_stats = optimizer.get_stats()
        except Exception as e:
            logger.warning(f"Failed to get optimizer stats: {e}")
            optimizer_stats = {"error": str(e)}
        
        metrics = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'memory_used_gb': round(memory.used / (1024**3), 2),
                'disk_percent': disk.percent,
                'disk_free_gb': round(disk.free / (1024**3), 2),
                'disk_used_gb': round(disk.used / (1024**3), 2)
            },
            'cache': cache_stats,
            'queries': query_stats,
            'security': security_metrics,
            'database': db_stats,
            'connection_pool': pool_stats,
            'performance': optimizer_stats
        }
        
        return jsonify(metrics), 200
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to retrieve performance metrics',
            'message': str(e)
        }), 500

@performance_api.route('/cache/stats')
@login_required
def get_cache_stats():
    """Get detailed cache statistics"""
    try:
        stats = cache_service.get_stats()
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to retrieve cache statistics',
            'message': str(e)
        }), 500

@performance_api.route('/cache/clear', methods=['POST'])
@login_required
def clear_cache():
    """Clear all cache entries"""
    try:
        success = cache_service.clear()
        
        if success:
            logger.info(f"Cache cleared by user {current_user.id}")
            return jsonify({'message': 'Cache cleared successfully'}), 200
        else:
            logger.warning("Cache clear operation failed")
            return jsonify({'error': 'Failed to clear cache'}), 500
        
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to clear cache',
            'message': str(e)
        }), 500

@performance_api.route('/queries/stats')
@login_required
def get_query_stats():
    """Get query performance statistics"""
    try:
        query_optimizer = get_query_optimizer()
        stats = query_optimizer.get_query_stats()
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error getting query stats: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to retrieve query statistics',
            'message': str(e)
        }), 500

@performance_api.route('/queries/optimize', methods=['POST'])
@login_required
def optimize_queries():
    """Run query optimization"""
    try:
        query_optimizer = get_query_optimizer()
        result = query_optimizer.optimize_transaction_queries()
        logger.info(f"Query optimization completed: {result} views created by user {current_user.id}")
        return jsonify({
            'message': 'Query optimization completed',
            'views_created': result
        }), 200
        
    except Exception as e:
        logger.error(f"Error optimizing queries: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to optimize queries',
            'message': str(e)
        }), 500

@performance_api.route('/security/metrics')
@login_required
def get_security_metrics():
    """Get security metrics"""
    try:
        security_service = get_security_service()
        metrics = security_service.get_security_metrics()
        return jsonify(metrics), 200
        
    except Exception as e:
        logger.error(f"Error getting security metrics: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to retrieve security metrics',
            'message': str(e)
        }), 500

@performance_api.route('/health')
@login_required
def get_health_status():
    """Get detailed health status"""
    try:
        # Check system health
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Determine health status
        health_status = "healthy"
        issues = []
        
        if cpu_percent > 80:
            health_status = "warning"
            issues.append(f"High CPU usage: {cpu_percent}%")
        
        if memory.percent > 85:
            health_status = "warning"
            issues.append(f"High memory usage: {memory.percent}%")
        
        if cpu_percent > 95 or memory.percent > 95:
            health_status = "critical"
        
        # Check cache health
        cache_stats = cache_service.get_stats()
        
        if not cache_stats.get('redis_available', False):
            issues.append("Redis cache not available")
        
        # Check database health
        try:
            from app import db
            db.session.execute('SELECT 1')
            db_status = "healthy"
        except Exception as e:
            db_status = "unhealthy"
            issues.append(f"Database error: {str(e)}")
            health_status = "critical"
        
        health_data = {
            'status': health_status,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'issues': issues,
            'components': {
                'database': db_status,
                'cache': 'healthy' if cache_stats.get('redis_available', False) else 'degraded',
                'system': health_status
            },
            'metrics': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'cache_entries': cache_stats.get('memory_cache_entries', 0)
            }
        }
        
        status_code = 200 if health_status == "healthy" else 503
        return jsonify(health_data), status_code
        
    except Exception as e:
        logger.error(f"Error getting health status: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': 'Failed to retrieve health status',
            'message': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500

@performance_api.route('/status')
@login_required
def get_status():
    """
    Get system status metrics (compatibility endpoint for System Monitor)
    Returns metrics in the format expected by frontend
    """
    try:
        # System metrics (reduced logging - only log errors)
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Cache metrics
        cache_stats = cache_service.get_stats()
        
        # Query performance metrics
        query_optimizer = get_query_optimizer()
        query_stats = query_optimizer.get_query_stats()
        
        # Database pool stats
        db_pool_stats = {}
        db_stats = {}
        try:
            db_stats = query_optimizer.get_database_stats()
            db_pool_stats = db_stats.get('connection_pool', {}) if isinstance(db_stats, dict) else {}
            
            # If connection_pool is not in db_stats, try to get it directly from the engine
            if not db_pool_stats or db_pool_stats.get('size', 0) == 0:
                try:
                    from app import db
                    pool = db.engine.pool
                    db_pool_stats = {
                        'size': pool.size(),
                        'checked_out': pool.checkedout(),
                        'checked_in': pool.checkedin(),
                        'overflow': pool.overflow(),
                    }
                    # Update db_stats with pool info
                    if isinstance(db_stats, dict):
                        db_stats['connection_pool'] = db_pool_stats
                except Exception as pool_error:
                    logger.debug(f"Could not get pool stats directly: {pool_error}")
        except Exception as e:
            logger.warning(f"Failed to get database pool stats: {e}")
            # Try to get pool stats directly as fallback
            try:
                from app import db
                pool = db.engine.pool
                db_pool_stats = {
                    'size': pool.size(),
                    'checked_out': pool.checkedout(),
                    'checked_in': pool.checkedin(),
                    'overflow': pool.overflow(),
                }
            except Exception as pool_error:
                logger.debug(f"Could not get pool stats as fallback: {pool_error}")
                db_pool_stats = {}
        
        # Calculate cache hit rate
        hits = cache_stats.get('hits', 0)
        misses = cache_stats.get('misses', 0)
        total_requests = hits + misses
        hit_rate = (hits / total_requests * 100) if total_requests > 0 else 0
        
        # Calculate application performance metrics from query stats
        total_queries = query_stats.get('total_queries', 0)
        error_count = query_stats.get('error_count', 0)
        avg_query_time = query_stats.get('avg_query_time', 0) or query_stats.get('average_query_time', 0)
        
        # Calculate requests per second (estimate based on queries per minute)
        # This is a rough estimate - in a real scenario, you'd track actual HTTP requests
        requests_per_second = round(total_queries / 60.0, 2) if total_queries > 0 else 0
        
        # Average response time in milliseconds (from query time or default)
        avg_response_time = round(avg_query_time * 1000, 2) if avg_query_time > 0 else 0
        
        # Error rate percentage
        error_rate = round((error_count / total_queries * 100), 2) if total_queries > 0 else 0
        
        # Build response matching frontend expectations
        response = {
            'timestamp': int(time.time()),  # Unix timestamp as frontend expects
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'memory_used_gb': round(memory.used / (1024**3), 2),
                'disk_free_gb': round(disk.free / (1024**3), 2),
                'disk_used_gb': round(disk.used / (1024**3), 2)
            },
            'cache': {
                'hit_rate': round(hit_rate, 2),
                'hits': hits,
                'misses': misses,
                'requests_per_second': requests_per_second,
                'avg_response_time': avg_response_time,
                'error_rate': error_rate,
                'redis_available': cache_stats.get('redis_available', False),
                'memory_cache_entries': cache_stats.get('memory_cache_entries', 0)
            },
            'database_pool': {
                'checked_out': db_pool_stats.get('checked_out', 0),
                'overflow': db_pool_stats.get('overflow', 0),
                'size': db_pool_stats.get('size', 0)
            },
            'queries': query_stats,
            'database': db_stats if isinstance(db_stats, dict) else {}
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to retrieve status',
            'message': str(e),
            'timestamp': int(time.time())
        }), 500

@performance_api.route('/system-status')
@login_required
def get_system_status():
    """
    Get overall system status (compatibility endpoint for System Monitor)
    Returns overall health status in the format expected by frontend
    """
    try:
        # Check system health
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Determine health status
        overall_status = "healthy"
        database_status = "healthy"
        cache_status = "healthy"
        api_status = "healthy"
        background_tasks_status = "healthy"
        
        if cpu_percent > 95 or memory.percent > 95:
            overall_status = "critical"
        elif cpu_percent > 80 or memory.percent > 85:
            overall_status = "warning"
        
        # Check cache health
        cache_stats = cache_service.get_stats()
        if not cache_stats.get('redis_available', False) and cache_stats.get('memory_cache_entries', 0) == 0:
            cache_status = "error"
        elif not cache_stats.get('redis_available', False):
            cache_status = "warning"
        
        # Check database health
        try:
            from app import db
            db.session.execute(text('SELECT 1'))
            database_status = "healthy"
        except Exception as e:
            database_status = "error"
            overall_status = "critical"
            logger.warning(f"Database health check failed: {e}")
        
        # API is healthy if we got here
        api_status = "healthy"
        
        # Background tasks - check if we have any monitoring running
        # For now, assume healthy (can be enhanced later)
        background_tasks_status = "healthy"
        
        response = {
            'overall': overall_status,
            'database': database_status,
            'cache': cache_status,
            'api': api_status,
            'background_tasks': background_tasks_status,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}", exc_info=True)
        return jsonify({
            'overall': 'error',
            'database': 'error',
            'cache': 'error',
            'api': 'error',
            'background_tasks': 'error',
            'error': 'Failed to retrieve system status',
            'message': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500

@performance_api.route('/alerts')
@login_required
def get_alerts():
    """
    Get performance alerts (compatibility endpoint for System Monitor)
    Returns alerts based on current system state
    Now uses centralized AlertingService
    """
    try:
        # Import alerting service (lightweight in-memory alert manager)
        from app.services.alerting_service import alerting_service, AlertLevel
        
        # Gather current system state
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get health status
        health_data = {
            'status': {
                'overall': 'healthy',
                'components': {}
            }
        }
        
        # Determine health from metrics
        if cpu_percent > 95 or memory.percent > 95:
            health_data['status']['overall'] = 'critical'
        elif cpu_percent > 80 or memory.percent > 85:
            health_data['status']['overall'] = 'warning'
        
        if cpu_percent > 95:
            health_data['status']['components']['cpu'] = 'critical'
        elif cpu_percent > 80:
            health_data['status']['components']['cpu'] = 'warning'
        
        if memory.percent > 95:
            health_data['status']['components']['memory'] = 'critical'
        elif memory.percent > 85:
            health_data['status']['components']['memory'] = 'warning'
        
        # Get cache stats
        cache_stats = cache_service.get_stats()
        
        # Get metrics for alerting
        metrics = {
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent
            }
        }
        
        # Calculate error rate (if available from query stats)
        query_optimizer = get_query_optimizer()
        query_stats = query_optimizer.get_query_stats()
        error_count = query_stats.get('error_count', 0)
        total_queries = query_stats.get('total_queries', 0)
        error_rate = (error_count / total_queries * 100) if total_queries > 0 else 0
        
        # Feed current metrics into alerting service (this app's AlertingService API)
        alerting_service.check_system_metrics({'system': metrics['system']})
        alerting_service.check_error_rate(error_count=error_count, total_requests=total_queries)

        # Recent alerts (return as "active" for UI; UI can choose to show latest N)
        recent_alerts = alerting_service.get_recent_alerts(limit=50)
        alert_stats = alerting_service.get_alert_stats()

        # Format alerts for frontend (match PerformanceAlert interface)
        formatted_alerts = []
        for alert in recent_alerts:
            # Map AlertLevel to frontend type and severity
            level_to_type = {
                AlertLevel.INFO: 'info',
                AlertLevel.WARNING: 'warning',
                AlertLevel.ERROR: 'error',
                AlertLevel.CRITICAL: 'error'
            }
            level_to_severity = {
                AlertLevel.INFO: 'low',
                AlertLevel.WARNING: 'medium',
                AlertLevel.ERROR: 'high',
                AlertLevel.CRITICAL: 'critical'
            }
            
            formatted_alert = {
                'id': f"alert_{alert.timestamp.timestamp()}_{hash(alert.message)}",
                'type': level_to_type.get(alert.level, 'info'),
                'message': f"{alert.title}: {alert.message}" if alert.title != alert.message else alert.message,
                'timestamp': alert.timestamp.isoformat(),
                'severity': level_to_severity.get(alert.level, 'low'),
                'resolved': False,
                'recommendations': alert.metadata.get('recommendations', []) if alert.metadata else [],
                'details': alert.metadata.get('details', {}) if alert.metadata else {}
            }
            formatted_alerts.append(formatted_alert)
        
        # Shape summary to match frontend expectations as much as possible
        alert_summary = {
            'total': alert_stats.get('total_alerts', 0),
            'by_severity': alert_stats.get('by_level', {}),
            'by_category': {}
        }
        
        return jsonify({
            'alerts': formatted_alerts,
            'summary': alert_summary,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}", exc_info=True)
        # Return empty alerts array in correct format instead of error
        return jsonify({
            'alerts': [],
            'summary': {
                'total': 0,
                'by_severity': {'critical': 0, 'error': 0, 'warning': 0, 'info': 0},
                'by_category': {}
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200  # Return 200 with empty alerts instead of 500


@performance_api.route('/optimization-recommendations')
@login_required
def get_optimization_recommendations():
    """
    Get optimization recommendations for Business Analytics.

    This endpoint is used by the frontend (`BusinessAnalytics.tsx`).
    It returns recommendations in the shape expected by the UI:
      - priority: low|medium|high|critical
      - component: cpu|memory|database|cache|system
      - message: human readable text
      - action: suggested action
    """
    try:
        from app.services.performance_monitor import performance_monitor

        raw_recs = performance_monitor.get_optimization_recommendations() or []

        # Normalize into UI shape
        mapped = []
        for rec in raw_recs:
            rec_type = (rec.get('type') or '').lower()
            priority = (rec.get('priority') or 'low').lower()
            title = rec.get('title') or 'Optimization Recommendation'
            description = rec.get('description') or ''

            # Map component from type
            component = 'system'
            if 'cpu' in rec_type:
                component = 'cpu'
            elif 'memory' in rec_type:
                component = 'memory'
            elif 'database' in rec_type:
                component = 'database'
            elif 'cache' in rec_type:
                component = 'cache'

            # Provide a compact UI message and action
            message = f"{title}: {description}".strip(': ').strip()
            action = description or 'Review recommendation details'

            mapped.append({
                'priority': priority,
                'component': component,
                'message': message,
                'action': action,
                'details': {
                    'impact': rec.get('impact'),
                    'effort': rec.get('effort'),
                    'type': rec.get('type'),
                }
            })

        # Fallback when monitor hasn't produced recommendations yet
        if not mapped:
            mapped = [{
                'priority': 'low',
                'component': 'system',
                'message': 'No optimization recommendations available yet.',
                'action': 'Continue monitoring system performance.',
                'details': {}
            }]

        return jsonify({
            'recommendations': mapped,
            'total': len(mapped),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error getting optimization recommendations: {str(e)}", exc_info=True)
        return jsonify({
            'recommendations': [],
            'total': 0,
            'error': 'Failed to retrieve optimization recommendations',
            'message': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500

@performance_api.route('/connection-pool/stats')
@login_required
def get_connection_pool_stats():
    """Get detailed connection pool statistics and health"""
    try:
        from app.services.connection_pool_monitor import get_pool_monitor
        from app import db
        
        pool_monitor = get_pool_monitor(db.engine)
        
        if not pool_monitor:
            return jsonify({
                'error': 'Connection pool monitor not initialized',
                'message': 'Pool monitoring may not be available'
            }), 503
        
        stats = pool_monitor.get_pool_stats()
        alerts = pool_monitor.get_alerts(limit=20)
        optimization = pool_monitor.optimize_pool_config()
        
        return jsonify({
            'pool_stats': stats,
            'recent_alerts': alerts,
            'optimization_suggestions': optimization,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting connection pool stats: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to retrieve connection pool statistics',
            'message': str(e)
        }), 500


@performance_api.route('/connection-pool/alerts')
@login_required
def get_connection_pool_alerts():
    """Get connection pool alerts and warnings"""
    try:
        from app.services.connection_pool_monitor import get_pool_monitor
        from app import db
        
        pool_monitor = get_pool_monitor(db.engine)
        
        if not pool_monitor:
            return jsonify({
                'alerts': [],
                'message': 'Connection pool monitor not initialized'
            }), 200
        
        limit = request.args.get('limit', 50, type=int)
        alerts = pool_monitor.get_alerts(limit=limit)
        
        return jsonify({
            'alerts': alerts,
            'count': len(alerts),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting pool alerts: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to retrieve pool alerts',
            'message': str(e)
        }), 500


@performance_api.route('/connection-pool/optimize')
@login_required
def get_pool_optimization_suggestions():
    """Get connection pool optimization suggestions"""
    try:
        from app.services.connection_pool_monitor import get_pool_monitor
        from app import db
        
        pool_monitor = get_pool_monitor(db.engine)
        
        if not pool_monitor:
            return jsonify({
                'error': 'Connection pool monitor not initialized',
                'message': 'Pool monitoring may not be available'
            }), 503
        
        suggestions = pool_monitor.optimize_pool_config()
        
        return jsonify({
            'optimization': suggestions,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting pool optimization: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to retrieve optimization suggestions',
            'message': str(e)
        }), 500


@performance_api.route('/database-optimization/create-index', methods=['POST'])
@login_required
def create_optimization_index():
    """
    Create a specific index from optimization recommendations
    Expects JSON: {"table": "table_name", "index": "index_name", "columns": ["col1", "col2"]}
    """
    try:
        data = request.get_json() or {}
        table_name = data.get('table')
        index_name = data.get('index')
        columns = data.get('columns', [])
        
        if not table_name or not index_name or not columns:
            return jsonify({
                'error': 'Missing required fields',
                'message': 'table, index, and columns are required'
            }), 400
        
        from app import db
        from sqlalchemy import text
        
        # Build CREATE INDEX statement
        columns_str = ', '.join(f'"{col}"' for col in columns)
        sql = f'CREATE INDEX IF NOT EXISTS {index_name} ON "{table_name}" ({columns_str})'
        
        try:
            db.session.execute(text(sql))
            db.session.commit()
            
            api_logger.info(f"Created index {index_name} on {table_name}({columns_str}) by user {current_user.id}")
            
            return jsonify({
                'success': True,
                'message': f'Index {index_name} created successfully',
                'index': {
                    'table': table_name,
                    'index': index_name,
                    'columns': columns
                },
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 200
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create index {index_name}: {e}")
            return jsonify({
                'success': False,
                'error': f'Failed to create index: {str(e)}',
                'message': str(e)
            }), 500
            
    except Exception as e:
        logger.error(f"Error creating index: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to create index',
            'message': str(e)
        }), 500


@performance_api.route('/database-optimization', methods=['GET', 'POST'])
@login_required
def database_optimization():
    """
    Run database optimization and return recommendations
    Returns results in the format expected by System Monitor frontend
    """
    try:
        
        recommendations = []
        
        # Get database stats and verify indexes
        query_optimizer_instance = get_query_optimizer()
        
        # Check for missing indexes
        try:
            from app.services.index_optimization_service import index_optimization_service
            index_recommendations = index_optimization_service.get_index_recommendations()
            
            # Add missing index recommendations
            for missing_idx in index_recommendations.get('missing_indexes', []):
                recommendations.append({
                    'type': 'warning' if missing_idx['priority'] == 'high' else 'info',
                    'component': 'database',
                    'message': f"Missing index: {missing_idx['index']} on {missing_idx['table']}",
                    'priority': missing_idx['priority'],
                    'action': f"Create index {missing_idx['index']} on columns {', '.join(missing_idx['columns'])}",
                    'details': {
                        'table': missing_idx['table'],
                        'index': missing_idx['index'],
                        'columns': missing_idx['columns'],
                        'suggestions': [
                            f"CREATE INDEX {missing_idx['index']} ON \"{missing_idx['table']}\" ({', '.join(missing_idx['columns'])})"
                        ]
                    }
                })
        except Exception as e:
            logger.debug(f"Index optimization check failed: {e}")
        db_stats = query_optimizer_instance.get_database_stats()
        
        # Check for large tables without proper indexes
        tables_to_check = ['transaction', 'psp_track', 'daily_balance', 'user']
        for table in tables_to_check:
            try:
                from app import db
                # Quote table name to handle reserved keywords like 'transaction'
                result = db.session.execute(text(f'SELECT COUNT(*) FROM "{table}"')).fetchone()
                row_count = result[0] if result else 0
                
                if row_count > 10000:
                    # Check if table has indexes
                    try:
                        indexes_result = db.session.execute(
                            text(f"SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND tbl_name='{table}'")
                        ).fetchone()
                        index_count = indexes_result[0] if indexes_result else 0
                        
                        if index_count < 2:  # At least should have primary key + one more
                            recommendations.append({
                                'type': 'warning',
                                'component': 'database',
                                'message': f'Large table "{table}" ({row_count:,} rows) may benefit from additional indexes',
                                'priority': 'medium' if row_count < 50000 else 'high',
                                'action': f'Consider adding indexes on frequently queried columns for table {table}',
                                'details': {
                                    'table': table,
                                    'row_count': row_count,
                                    'current_indexes': index_count,
                                    'suggestions': [
                                        'Review query patterns for this table',
                                        'Add indexes on frequently filtered/sorted columns',
                                        'Consider composite indexes for multi-column queries'
                                    ],
                                    'general_tips': [
                                        'Indexes improve SELECT performance but slow INSERT/UPDATE',
                                        'Focus on indexes for queries used in WHERE, JOIN, and ORDER BY clauses',
                                        'Monitor index usage to avoid unnecessary indexes'
                                    ]
                                }
                            })
                    except Exception as e:
                        logger.debug(f"Could not check indexes for {table}: {e}")
                        
            except Exception as e:
                logger.warning(f"Could not analyze table {table}: {e}")
                recommendations.append({
                    'type': 'error',
                    'component': 'database',
                    'message': f'Error analyzing table "{table}"',
                    'priority': 'low',
                    'action': f'Check database connection and table existence for {table}',
                    'details': {
                        'table': table,
                        'error': str(e),
                        'general_tips': ['Verify database connection', 'Check table schema']
                    }
                })
        
        # Check database size and suggest vacuum if needed
        try:
            from app import db
            size_result = db.session.execute(
                text("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            ).fetchone()
            db_size_bytes = size_result[0] if size_result else 0
            db_size_mb = db_size_bytes / (1024 * 1024)
            
            if db_size_mb > 100:  # If database > 100MB
                recommendations.append({
                    'type': 'info',
                    'component': 'database',
                    'message': f'Database size is {db_size_mb:.1f} MB - consider periodic VACUUM',
                    'priority': 'low',
                    'action': 'Run VACUUM to reclaim space and optimize database',
                    'details': {
                        'suggestions': [
                            'Schedule regular VACUUM operations for SQLite',
                            'Consider archiving old data if database continues to grow',
                            'Monitor database growth trends'
                        ],
                        'general_tips': [
                            'VACUUM reorganizes the database and reclaims unused space',
                            'Run during low-traffic periods',
                            'Regular VACUUM improves query performance'
                        ]
                    }
                })
        except Exception as e:
            logger.debug(f"Could not check database size: {e}")
        
        # Add success recommendation if no issues found
        if not recommendations:
            recommendations.append({
                'type': 'success',
                'component': 'database',
                'message': 'Database appears to be well-optimized',
                'priority': 'low',
                'action': 'Continue monitoring database performance',
                'details': {
                    'general_tips': [
                        'Regular monitoring helps catch performance issues early',
                        'Review slow query logs periodically',
                        'Keep database statistics up to date'
                    ]
                }
            })
        
        response = {
            'recommendations': recommendations,
            'total': len(recommendations),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        api_logger.info(f"Database optimization analysis completed: {len(recommendations)} recommendations (user: {current_user.id})")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error running database optimization: {str(e)}", exc_info=True)
        return jsonify({
            'recommendations': [{
                'type': 'error',
                'component': 'system',
                'message': f'Database optimization failed: {str(e)}',
                'priority': 'critical',
                'action': 'Check server logs and database connectivity',
                'details': {
                    'error': str(e),
                    'general_tips': [
                        'Verify database connection',
                        'Check application logs for details',
                        'Ensure database permissions are correct'
                    ]
                }
            }],
            'total': 1,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500