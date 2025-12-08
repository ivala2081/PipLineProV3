"""
Enhanced Health API endpoints for PipLinePro v2
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

# Import services conditionally
try:
    from app.services.enhanced_cache_service import cache_service
    CACHE_SERVICE_AVAILABLE = True
except ImportError:
    CACHE_SERVICE_AVAILABLE = False

try:
    from app.services.event_service import event_service
    EVENT_SERVICE_AVAILABLE = True
except ImportError:
    EVENT_SERVICE_AVAILABLE = False

try:
    from app.services.microservice_service import microservice_service
    MICROSERVICE_SERVICE_AVAILABLE = True
except ImportError:
    MICROSERVICE_SERVICE_AVAILABLE = False

logger = logging.getLogger(__name__)

health_api = Blueprint('health_api', __name__)

# Temporarily disable CSRF protection for health API
from app import csrf
csrf.exempt(health_api)

@health_api.route('/', methods=['GET'])
def health_check():
    """Comprehensive health check"""
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0',
            'services': {}
        }
        
        # Check database
        try:
            from app import db
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            health_status['services']['database'] = 'healthy'
        except Exception as e:
            health_status['services']['database'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'unhealthy'
        
        # Check Redis/cache
        if CACHE_SERVICE_AVAILABLE:
            try:
                cache_stats = cache_service.get_stats()
                health_status['services']['cache'] = 'healthy'
                health_status['cache_stats'] = cache_stats
            except Exception as e:
                health_status['services']['cache'] = f'unhealthy: {str(e)}'
        else:
            health_status['services']['cache'] = 'not available'
        
        # Check event service
        if EVENT_SERVICE_AVAILABLE:
            try:
                stream_info = event_service.get_stream_info()
                health_status['services']['events'] = 'healthy'
                health_status['event_stream'] = stream_info
            except Exception as e:
                health_status['services']['events'] = f'unhealthy: {str(e)}'
        else:
            health_status['services']['events'] = 'not available'
        
        # Check microservices
        if MICROSERVICE_SERVICE_AVAILABLE:
            try:
                service_stats = microservice_service.get_service_stats()
                health_status['services']['microservices'] = 'healthy'
                health_status['service_stats'] = service_stats
            except Exception as e:
                health_status['services']['microservices'] = f'unhealthy: {str(e)}'
        else:
            health_status['services']['microservices'] = 'not available'
        
        return jsonify(health_status)
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@health_api.route('/detailed', methods=['GET'])
def detailed_health():
    """Detailed health check with metrics"""
    try:
        from datetime import datetime
        from app import db
        import psutil
        
        detailed_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'system': {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent
            },
            'database': {
                'pool_size': db.engine.pool.size() if hasattr(db.engine, 'pool') else 0,
                'checked_in': db.engine.pool.checkedin() if hasattr(db.engine, 'pool') else 0,
                'checked_out': db.engine.pool.checkedout() if hasattr(db.engine, 'pool') else 0
            },
            'cache': cache_service.get_stats() if CACHE_SERVICE_AVAILABLE else {},
            'events': event_service.get_stream_info() if EVENT_SERVICE_AVAILABLE else {},
            'services': microservice_service.get_service_stats() if MICROSERVICE_SERVICE_AVAILABLE else {}
        }
        
        return jsonify(detailed_status)
        
    except Exception as e:
        logger.error(f"Error in detailed health check: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500
