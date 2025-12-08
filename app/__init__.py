"""
PipLine Treasury System - Application Factory
"""
# Configure comprehensive logging to reduce verbosity FIRST - before any imports
import logging
import sys
import os

# Add the app directory to the Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Completely silence SQLAlchemy logging
logging.getLogger('sqlalchemy.engine').disabled = True
logging.getLogger('sqlalchemy.pool').disabled = True
logging.getLogger('sqlalchemy.dialects').disabled = True
logging.getLogger('sqlalchemy.orm').disabled = True
logging.getLogger('sqlalchemy').disabled = True

# Reduce werkzeug logging
logging.getLogger('werkzeug').setLevel(logging.WARNING)

# Reduce other verbose loggers
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('flask_limiter').setLevel(logging.WARNING)

from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import CSRFProtect
from flask_babel import Babel, get_locale, gettext, ngettext
from flask_cors import CORS
from flask_compress import Compress
from datetime import timedelta
import os
import traceback
import time

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
socketio = SocketIO()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["5000 per day", "1000 per hour", "200 per minute"],
    # storage_uri will be set from config during init_app()
    storage_options={"cluster": False}
)
csrf = CSRFProtect()
babel = Babel()
compress = Compress()

# Legacy in-memory cache for backward compatibility
# NOTE: Use enhanced_cache_service for new code
class AdvancedCache:
    """Simple in-memory cache - compatibility wrapper"""
    def __init__(self):
        self._cache = {}
        self._stats = {'hits': 0, 'misses': 0, 'sets': 0, 'deletes': 0, 'total_requests': 0}
    
    def get(self, key, default=None):
        """Get value from cache"""
        self._stats['total_requests'] += 1
        if key in self._cache:
            value, expiry = self._cache[key]
            if time.time() < expiry:
                self._stats['hits'] += 1
                return value
            del self._cache[key]
        self._stats['misses'] += 1
        return default
    
    def set(self, key, value, ttl=300):
        """Set value in cache with TTL"""
        self._cache[key] = (value, time.time() + ttl)
        self._stats['sets'] += 1
    
    def delete(self, key):
        """Delete key from cache"""
        if key in self._cache:
            del self._cache[key]
            self._stats['deletes'] += 1
    
    def clear(self):
        """Clear all cache"""
        self._cache.clear()
        self._stats = {'hits': 0, 'misses': 0, 'sets': 0, 'deletes': 0, 'total_requests': 0}
    
    def get_stats(self):
        """Get cache statistics"""
        total = self._stats['hits'] + self._stats['misses']
        hit_rate = (self._stats['hits'] / total * 100) if total > 0 else 0
        return {
            'hits': self._stats['hits'],
            'misses': self._stats['misses'],
            'sets': self._stats['sets'],
            'deletes': self._stats['deletes'],
            'total_requests': self._stats['total_requests'],
            'hit_rate': round(hit_rate, 2),
            'cache_size': len(self._cache),
            'max_size': 1000
        }

# Initialize legacy cache
advanced_cache = AdvancedCache()

# Pagination utilities
class PaginationHelper:
    """Helper class for API pagination"""
    
    @staticmethod
    def paginate_query(query, page=1, per_page=25, max_per_page=100):
        """Paginate a SQLAlchemy query safely"""
        # Ensure page is valid
        page = max(1, page)
        per_page = min(max(1, per_page), max_per_page)
        
        # Get total count
        total = query.count()
        
        # Calculate pagination info
        total_pages = (total + per_page - 1) // per_page
        page = min(page, total_pages) if total_pages > 0 else 1
        
        # Get paginated results
        offset = (page - 1) * per_page
        items = query.offset(offset).limit(per_page).all()
        
        return {
            'items': items,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages,
                'has_prev': page > 1,
                'has_next': page < total_pages,
                'prev_page': page - 1 if page > 1 else None,
                'next_page': page + 1 if page < total_pages else None
            }
        }
    
    @staticmethod
    def create_pagination_links(base_url, page, total_pages, per_page):
        """Create pagination links for API responses"""
        links = {
            'first': f"{base_url}?page=1&per_page={per_page}",
            'last': f"{base_url}?page={total_pages}&per_page={per_page}" if total_pages > 0 else None,
            'self': f"{base_url}?page={page}&per_page={per_page}",
            'prev': f"{base_url}?page={page-1}&per_page={per_page}" if page > 1 else None,
            'next': f"{base_url}?page={page+1}&per_page={per_page}" if page < total_pages else None
        }
        
        # Remove None values
        return {k: v for k, v in links.items() if v is not None}

def create_app(config_name=None):
    """Application factory pattern"""
    # Set template folder to the templates directory in the project root
    # Use absolute path to ensure templates are found regardless of app root path
    template_dir = os.path.abspath('templates')
    static_dir = os.path.abspath('static')
    # Set template and static folders
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    
    # Check if we're in development mode for simplified logging
    is_development = (os.environ.get('FLASK_ENV') == 'development' or 
                     os.environ.get('DEBUG') == 'True' or 
                     app.config.get('DEBUG', False))
    
    # Load configuration - automatically select based on environment
    from config import config
    
    if config_name is None:
        # Auto-select config based on environment
        if os.environ.get('FLASK_ENV') == 'production':
            config_name = 'production'
        elif os.environ.get('FLASK_ENV') == 'testing':
            config_name = 'testing'
        else:
            config_name = 'development'
    
    app.config.from_object(config[config_name])
    
    # Disable trailing slash redirects to prevent 308 redirects
    # This ensures /api/v1/health and /api/v1/health/ both work without redirects
    app.url_map.strict_slashes = False
    
    # Initialize CORS for React frontend - Using config-based settings
    cors_origins = app.config.get('CORS_ORIGINS', [])
    CORS(app, 
         resources={r"/api/*": {
             "origins": cors_origins,
             "methods": app.config.get('CORS_METHODS', ["GET", "POST", "PUT", "DELETE", "OPTIONS"]),
             "allow_headers": app.config.get('CORS_ALLOW_HEADERS', ["Content-Type", "Authorization"]),
             "expose_headers": app.config.get('CORS_EXPOSE_HEADERS', ["Content-Type", "Authorization"]),
             "supports_credentials": app.config.get('CORS_SUPPORTS_CREDENTIALS', True),
             "max_age": app.config.get('CORS_MAX_AGE', 600)
         }}
    )
    
    # Log CORS configuration for debugging
    app.logger.info(f"CORS enabled for origins: {cors_origins}")
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')
    
    # Configure rate limiter storage from config
    storage_uri = app.config.get('RATELIMIT_STORAGE_URL', 'memory://')
    limiter.storage_uri = storage_uri
    limiter.init_app(app)
    csrf.init_app(app)
    
    # PHASE 1 OPTIMIZATION: Enhanced compression settings
    compress.init_app(app)
    app.config['COMPRESS_MIMETYPES'] = [
        'text/html', 'text/css', 'text/xml', 
        'application/json', 'application/javascript',
        'text/javascript', 'application/xml'
    ]
    app.config['COMPRESS_LEVEL'] = 6  # Balance between speed and compression
    app.config['COMPRESS_MIN_SIZE'] = 500  # Only compress responses > 500 bytes
    
    # Initialize security headers middleware
    from app.middleware.security_headers_middleware import create_security_middleware
    security_middleware = create_security_middleware(app)
    app.security_middleware = security_middleware
    
    # Initialize API versioning middleware
    from app.middleware.api_versioning_middleware import create_api_versioning_middleware
    create_api_versioning_middleware(app)
    
    # Initialize query performance monitoring
    from app.utils.query_performance_monitor import QueryPerformanceMonitor
    query_monitor = QueryPerformanceMonitor(app)
    app.query_performance_monitor = query_monitor
    
    # Initialize request tracing middleware (enhanced request ID tracking)
    from app.middleware.request_tracing import request_tracing_middleware
    request_tracing_middleware(app)
    
    # Initialize distributed tracing
    from app.utils.distributed_tracing import TraceManager
    @app.before_request
    def init_trace_context():
        """Initialize trace context for each request"""
        TraceManager.create_trace_context()
    
    # Add request ID tracking middleware (legacy support)
    from app.utils.enhanced_error_responses import add_request_id, log_request_completion
    
    @app.after_request
    def after_request_handler(response):
        """Log request completion"""
        try:
            from flask import g
            g.response_status = response.status_code
            log_request_completion()
        except:
            pass  # Don't break the response if logging fails
        return response
    
    # Add advanced cache to app context
    app.advanced_cache = advanced_cache
    
    # Initialize Redis service
    from app.services.redis_service import redis_service
    redis_service.init_app(app)
    app.redis_service = redis_service
    
    # Initialize background task service
    from app.services.background_service import background_task_service
    background_task_service.init_app(app)
    app.background_task_service = background_task_service
    
    # Initialize enhanced services
    from app.services.event_service import event_service
    from app.services.enhanced_cache_service import cache_service
    from app.services.microservice_service import microservice_service
    from app.services.real_time_service import init_real_time_service
    
    # Initialize configuration manager
    from app.services.config_manager import init_config_manager
    init_config_manager(app)
    
    # Initialize monitoring and alerting service
    from app.services.monitoring_service import get_monitoring_service
    monitoring_service = get_monitoring_service()
    # Start monitoring after app is fully initialized
    monitoring_service.start_monitoring()
    app.monitoring_service = monitoring_service
    
    # Initialize enhanced rate limiting service
    from app.services.rate_limit_service import init_rate_limit_service
    rate_limit_service = init_rate_limit_service(limiter)
    app.rate_limit_service = rate_limit_service
    
    # Initialize performance optimizer
    from app.services.performance_optimizer import init_performance_optimizer
    init_performance_optimizer(app)
    
    # Initialize real-time service with SocketIO
    real_time_service = init_real_time_service(socketio, event_service)
    app.real_time_service = real_time_service
    app.event_service = event_service
    app.cache_service = cache_service
    app.microservice_service = microservice_service
    
    # Performance monitoring context
    @app.context_processor
    def inject_performance_data():
        """Inject performance data into template context"""
        return {
            'cache_stats': advanced_cache.get_stats(),
            'redis_stats': redis_service.get_stats() if redis_service.is_connected() else {},
            'background_stats': background_task_service.get_queue_stats() if background_task_service.is_connected() else {},
            'db_pool_size': db.engine.pool.size() if hasattr(db.engine, 'pool') else 0,
            'db_pool_checked_in': db.engine.pool.checkedin() if hasattr(db.engine, 'pool') else 0,
            'db_pool_checked_out': db.engine.pool.checkedout() if hasattr(db.engine, 'pool') else 0,
        }
    
    # Configure session for cross-origin requests in development
    if app.config.get('DEBUG', False):
        app.config['SESSION_COOKIE_DOMAIN'] = None  # Allow localhost
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Allow cross-origin requests for React frontend
        app.config['SESSION_COOKIE_SECURE'] = False  # Allow HTTP in development
        app.config['SESSION_COOKIE_HTTPONLY'] = True  # Keep HTTPOnly for security, CSRF tokens are handled via API
        app.config['SESSION_COOKIE_PATH'] = '/'  # Ensure cookie is set for all paths
        # Default session lifetime (overridden per-session in auth.py based on remember_me)
        # Regular login: 8 hours, Remember me: 30 days
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
        
        # Enhanced session configuration for React frontend
        app.config['SESSION_REFRESH_EACH_REQUEST'] = True  # Refresh session on each request
        app.config['SESSION_COOKIE_NAME'] = 'pipelinepro_session'  # Custom session cookie name
        # SESSION_COOKIE_MAX_AGE is now set dynamically per session in auth.py based on remember_me
        
        # Limit session cookie size by ensuring filesystem session storage is used
        # Flask-Session stores session data server-side, only session ID goes in cookie
        app.config['SESSION_TYPE'] = 'filesystem'
        app.config['SESSION_FILE_DIR'] = 'instance/sessions'
        app.config['SESSION_FILE_THRESHOLD'] = 500
        app.config['SESSION_FILE_MODE'] = 0o600  # Secure file permissions
        
        # CSRF protection configuration
        # Disable CSRF only in development and testing, keep enabled in production
        is_dev_or_test = (
            app.config.get('DEBUG', False) or 
            app.config.get('TESTING', False) or
            os.environ.get('FLASK_ENV') in ('development', 'testing')
        )
        if is_dev_or_test and not app.config.get('WTF_CSRF_ENABLED', True):
            # Only disable if explicitly configured in development/testing config
            # Production always has CSRF enabled
            app.config['WTF_CSRF_ENABLED'] = False
            app.logger.info("CSRF protection disabled for development/testing environment")
        else:
            # Ensure CSRF is enabled in production (respects config setting)
            csrf_enabled = app.config.get('WTF_CSRF_ENABLED', True)
            if csrf_enabled:
                app.logger.info("CSRF protection enabled")
    
    # Initialize security service
    # from app.services.security_service import security_service
    # security_service.init_app(app)
    
    # Initialize error handling and monitoring services
    # from app.services.error_service import error_service
    # from app.services.monitoring_service import monitoring_service
    
    # Start monitoring
    # monitoring_service.start_monitoring()
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Configure remember me functionality
    login_manager.remember_cookie_duration = timedelta(days=30)
    login_manager.remember_cookie_secure = False  # Set to True in production
    login_manager.remember_cookie_httponly = True
    login_manager.remember_cookie_samesite = 'Lax'  # Allow cross-origin in development
    
    # Custom unauthorized handler for API endpoints
    @login_manager.unauthorized_handler
    def unauthorized():
        """Handle unauthorized access - return JSON for API endpoints, redirect for web pages"""
        from flask import request, jsonify
        
        # Public API endpoints that don't require authentication
        public_endpoints = [
            '/api/v1/exchange-rates/current',
            '/api/v1/health/',
        ]
        
        # Check if this is a public endpoint
        for public_endpoint in public_endpoints:
            if request.path.startswith(public_endpoint):
                # Let the request proceed without authentication
                return None
        
        # Check if this is an API request
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please log in to access this endpoint'
            }), 401
        else:
            # For web pages, redirect to login
            return redirect(url_for('auth.login'))
    
    # Configure user loader
    @login_manager.user_loader
    def load_user(user_id):
        """Load user for Flask-Login"""
        from app.models.user import User
        try:
            user = User.query.get(int(user_id))
            if user and user.is_active:
                return user
            else:
                return None
        except Exception as e:
            logger = get_logger("UserLoader")
            logger.error(f"Error loading user {user_id}: {str(e)}")
            return None
    
    # ============================================================================
    # BLUEPRINT REGISTRATION
    # ============================================================================
    
    # Register legacy routes (for backward compatibility with old frontend)
    # These routes are deprecated and will be removed in a future version
    from app.routes.auth import auth_bp
    from app.routes.transactions import transactions_bp
    from app.routes.analytics import analytics_bp
    from app.routes.api import api_bp
    from app.routes.settings import settings_bp
    from app.routes.health import health_bp
    from app.routes.responsive import responsive_bp
    from app.routes.font_analytics import font_analytics_bp
    from app.routes.admin_management import admin_management_bp
    from app.routes.admin_permissions import admin_permissions_bp
    from app.routes.color_enhancement import init_color_enhancement_routes
    from app.routes.exchange_rates import exchange_rates_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(responsive_bp)
    app.register_blueprint(font_analytics_bp)
    app.register_blueprint(admin_management_bp)
    app.register_blueprint(admin_permissions_bp)
    app.register_blueprint(exchange_rates_bp)
    
    # Register modern API blueprints
    # API v1 - Stable, production-ready endpoints (all endpoints registered via api_v1.__init__)
    from app.api.v1 import api_v1
    app.register_blueprint(api_v1)
    
    # API v2 - Beta/Experimental features (new architecture with microservices support)
    from app.api.v2 import api_v2
    app.register_blueprint(api_v2)
    
    # Register standalone API endpoints (not included in api_v1 main blueprint)
    # These are registered separately because they have special URL patterns or were added later
    from app.api.v1.endpoints.auth import auth_api
    from app.api.v1.endpoints.consolidated_dashboard import consolidated_dashboard_api
    from app.api.v1.endpoints.commission_rates import commission_rates_api
    from app.api.v1.endpoints.performance import performance_api
    from app.api.v1.endpoints.monitoring import monitoring_api
    from app.api.v1.endpoints.system_stats import system_stats_api
    from app.api.v1.endpoints.financial_performance import financial_performance_bp
    from app.api.v1.endpoints.notifications import notifications_api
    from app.api.v1.endpoints.accounting import accounting_api
    
    app.register_blueprint(auth_api, url_prefix='/api/v1/auth')
    app.register_blueprint(consolidated_dashboard_api, url_prefix='/api/v1')
    app.register_blueprint(commission_rates_api, url_prefix='/api/v1/commission-rates')
    app.register_blueprint(performance_api, url_prefix='/api/v1/performance')
    app.register_blueprint(monitoring_api, url_prefix='/api/v1')
    app.register_blueprint(system_stats_api, url_prefix='/api/v1/system')
    app.register_blueprint(financial_performance_bp, url_prefix='/api/v1')
    app.register_blueprint(notifications_api, url_prefix='/api/v1')
    app.register_blueprint(accounting_api, url_prefix='/api/v1/accounting')
    
    # Register enhanced monitoring & metrics endpoints
    from app.routes.monitoring import monitoring_bp, setup_prometheus_metrics
    app.register_blueprint(monitoring_bp)
    
    # Initialize alerting service
    try:
        from app.services.alerting_service import alerting_service
        app.alerting_service = alerting_service
        app.logger.info("Alerting service initialized")
    except Exception as e:
        app.logger.error(f"Failed to initialize alerting service: {e}")
    
    # Initialize metrics collector
    try:
        from app.utils.metrics_collector import metrics_collector
        app.metrics_collector = metrics_collector
        app.logger.info("Metrics collector initialized")
    except Exception as e:
        app.logger.error(f"Failed to initialize metrics collector: {e}")
    
    # Setup Prometheus metrics (if available)
    setup_prometheus_metrics(app)
    
    # Initialize color enhancement routes
    init_color_enhancement_routes(app)
    
    # Unified logging system
    from app.utils.unified_logger import setup_logging, get_logger
    enhanced_logger = setup_logging(app)
    enhanced_logger.info("Unified logging system enabled")
    
    # Error handling (always enabled)
    # Using unified_error_handler (already imported in routes)
    
    # Serve React frontend (production) or redirect to dev server (development)
    from flask import send_from_directory
    
    # Get the frontend build directory
    frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'dist')
    if not os.path.exists(frontend_dist):
        frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'dist_prod')
    
    @app.route('/')
    def root():
        """Root route - serve React frontend or redirect to login"""
        from flask_login import current_user
        
        # Check if frontend build exists
        index_path = os.path.join(frontend_dist, 'index.html')
        if os.path.exists(index_path):
            # Serve React frontend with proper headers
            response = send_from_directory(frontend_dist, 'index.html')
            # Ensure proper content type
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
            # Disable caching for index.html to ensure fresh content
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response
        else:
            # Fallback: redirect to login API
            return redirect('/api/v1/docs/')
    
    @app.route('/<path:path>')
    def serve_frontend(path):
        """Serve React frontend static files"""
        # Check if file exists in frontend build
        file_path = os.path.join(frontend_dist, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_from_directory(frontend_dist, path)
        else:
            # For SPA routing, serve index.html for non-API routes
            if not path.startswith('api/'):
                index_path = os.path.join(frontend_dist, 'index.html')
                if os.path.exists(index_path):
                    return send_from_directory(frontend_dist, 'index.html')
            # Return 404 for missing files
            return jsonify({'error': 'Not found'}), 404
    
    # Note: format_number filter is now registered in template_helpers.py
    
    # Note: strftime filter is now registered in template_helpers.py as 'safe_strftime'
    
    # Register context processors
    @app.context_processor
    def inject_csrf_token():
        """Inject CSRF token function into templates - ENHANCED VERSION"""
        from app.services.csrf_fix_service import get_csrf_token
        
        # Return the function directly for template use
        return {'csrf_token': get_csrf_token}
    
    @app.context_processor
    def inject_user_settings():
        """Inject user settings into templates"""
        from flask_login import current_user
        if current_user and current_user.is_authenticated:
            from app.models.config import UserSettings
            user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
            return dict(user_settings=user_settings)
        return dict(user_settings=None)
    
    @app.context_processor
    def inject_translation_functions():
        """Inject translation functions into templates"""
        return dict(
            _=gettext,
            ngettext=ngettext,
            get_locale=get_locale
        )
    
    @app.context_processor
    def inject_now():
        """Inject current datetime into templates"""
        from datetime import datetime
        return dict(now=datetime.now())
    
    @app.context_processor
    def inject_float():
        """Inject float function into templates"""
        return dict(float=float)
    
    @app.context_processor
    def inject_math_functions():
        """Inject math functions into templates"""
        import math
        return dict(
            abs=abs,
            round=round,
            min=min,
            max=max,
            sum=sum
        )
    
    @app.context_processor
    def track_current_page():
        """Track the current page in session for reload functionality"""
        from flask import session, request
        from flask_login import current_user
        
        # Only track pages for authenticated users
        if current_user and current_user.is_authenticated:
            # Get the current request path
            current_path = request.path
            
            # Don't track certain paths (static files, API endpoints, etc.)
            excluded_paths = ['/static/', '/api/', '/health/', '/favicon.ico']
            should_track = True
            
            for excluded in excluded_paths:
                if current_path.startswith(excluded):
                    should_track = False
                    break
            
            # Store the current page in session if it should be tracked
            if should_track and current_path != '/':
                session['current_page'] = current_path
        
        return {}
    
    # Configure template filters for safe numeric operations
    from app.utils.template_helpers import (
        legacy_ultimate_tojson, safe_template_data, safe_compare, safe_float, 
        safe_decimal, format_number, format_currency, safe_multiply, 
        safe_add, safe_subtract, safe_divide
    )
    
    @app.template_filter('ultimate_tojson')
    def ultimate_tojson(obj):
        return legacy_ultimate_tojson(obj)
    
    @app.template_filter('safe_template_data')
    def safe_template_data_filter(data):
        return safe_template_data(data)
    
    @app.template_filter('safe_compare')
    def safe_compare_filter(value, operator, compare_value):
        return safe_compare(value, operator, compare_value)
    
    @app.template_filter('safe_float')
    def safe_float_filter(value):
        return safe_float(value)
    
    @app.template_filter('safe_decimal')
    def safe_decimal_filter(value):
        return safe_decimal(value)
    
    @app.template_filter('format_number')
    def format_number_filter(value, decimal_places=2):
        return format_number(value, decimal_places)
    
    @app.template_filter('format_currency')
    def format_currency_filter(value, currency="₺", decimal_places=2):
        return format_currency(value, currency, decimal_places)
    
    @app.template_filter('safe_multiply')
    def safe_multiply_filter(value1, value2, result_type="float"):
        return safe_multiply(value1, value2, result_type)
    
    @app.template_filter('safe_add')
    def safe_add_filter(value1, value2, result_type="float"):
        return safe_add(value1, value2, result_type)
    
    @app.template_filter('safe_subtract')
    def safe_subtract_filter(value1, value2, result_type="float"):
        return safe_subtract(value1, value2, result_type)
    
    @app.template_filter('safe_divide')
    def safe_divide_filter(value1, value2, result_type="float"):
        return safe_divide(value1, value2, result_type)
    
    @app.template_filter('format_date')
    def format_date_filter(value, format_str="%Y-%m-%d"):
        """Format date value"""
        try:
            if value is None:
                return 'N/A'
            if isinstance(value, str):
                from datetime import datetime
                # Try to parse the string date
                try:
                    date_obj = datetime.strptime(value, '%Y-%m-%d')
                    return date_obj.strftime(format_str)
                except ValueError:
                    return value
            elif hasattr(value, 'strftime'):
                return value.strftime(format_str)
            else:
                return str(value)
        except Exception:
            return 'N/A'
    
    # Babel locale selector
    def get_locale():
        """Get the locale for the current request"""
        from flask_login import current_user
        if current_user and current_user.is_authenticated:
            from app.models.config import UserSettings
            user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
            if user_settings and user_settings.language:
                return user_settings.language
        return 'en'  # Default to English
    
    # Initialize Babel with locale selector
    babel.init_app(app, locale_selector=get_locale)
    
    # Request timing and logging middleware
    import time
    
    @app.before_request
    def before_request():
        """Log request start and store start time"""
        request.start_time = time.time()
        
        # Generate unique request ID for tracking
        import uuid
        request.request_id = str(uuid.uuid4())
        
        # Ensure session is properly initialized
        from flask import session
        if 'csrf_token' not in session:
            # Initialize session if needed
            session.permanent = True
        
        # Skip logging for static files and excluded paths
        excluded_paths = ['/static/', '/health/', '/favicon.ico', '/robots.txt', '/sitemap.xml']
        should_log = True
        
        for excluded in excluded_paths:
            if request.path.startswith(excluded):
                should_log = False
                break
        
        # Only log non-static requests (skip in development for cleaner output)
        if should_log and request.method not in ['OPTIONS', 'HEAD'] and not is_development:
            enhanced_logger = get_logger("RequestHandler")
            enhanced_logger.info(f"Request started: {request.method} {request.path}", {
                'request_id': request.request_id,
                'operation': 'request_start'
            })

    @app.after_request
    def after_request(response):
        """Log request completion and add security headers"""
        # Calculate request duration
        duration = time.time() - getattr(request, 'start_time', time.time())
        
        # Skip logging for static files and excluded paths
        excluded_paths = ['/static/', '/health/', '/favicon.ico', '/robots.txt', '/sitemap.xml']
        should_log = True
        
        for excluded in excluded_paths:
            if request.path.startswith(excluded):
                should_log = False
                break
        
        # Only log non-static requests and slow requests (skip in development for cleaner output)
        if should_log and request.method not in ['OPTIONS', 'HEAD'] and not is_development:
            # Only log if request took more than 100ms or had an error
            if duration > 0.1 or response.status_code >= 400:
                enhanced_logger = get_logger("RequestHandler")
                enhanced_logger.log_performance(
                    operation=f"HTTP {response.status_code}",
                    duration=duration,
                    extra_data={
                        'request_id': getattr(request, 'request_id', 'Unknown'),
                        'method': request.method,
                        'url': request.path,  # Use path instead of full URL
                        'status_code': response.status_code
                    }
                )
        
        # Add security headers
        security_headers = app.config.get('SECURITY_HEADERS', {})
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response
    
    # ============================================================================
    # STANDARDIZED ERROR HANDLERS
    # ============================================================================
    from app.utils.unified_error_handler import (
        PipLineError, ValidationError, AuthenticationError, AuthorizationError,
        ResourceNotFoundError, DatabaseError, RateLimitError, FileUploadError,
        CSRFError, BusinessLogicError,
        log_error, handle_api_error, handle_web_error, create_error_response
    )
    from werkzeug.exceptions import HTTPException
    
    @app.errorhandler(PipLineError)
    def handle_pipeline_error(error):
        """Standardized handler for PipLineError exceptions"""
        log_error(error, {"global_handler": True})
        if request.path.startswith('/api/'):
            return handle_api_error(error)
        else:
            return handle_web_error(error)
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Standardized 404 handler"""
        if request.path.startswith('/api/'):
            not_found = ResourceNotFoundError(
                resource_type="Resource",
                resource_id=request.path
            )
            return handle_api_error(not_found)
        else:
            from app.utils.api_response import make_response
            return jsonify(make_response(
                data=None,
                error={'code': 'NOT_FOUND', 'message': 'The requested resource was not found'}
            )), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Standardized 500 handler"""
        db.session.rollback()
        pipeline_error = PipLineError(
            "Internal server error",
            error_code="INTERNAL_SERVER_ERROR",
            status_code=500
        )
        log_error(pipeline_error, {"global_handler": True, "original_error": str(error)})
        if request.path.startswith('/api/'):
            return handle_api_error(pipeline_error)
        else:
            return handle_web_error(pipeline_error)

    @app.errorhandler(403)
    def forbidden_error(error):
        """Standardized 403 handler"""
        auth_error = AuthorizationError(
            "Access to this resource is forbidden",
            resource=request.path
        )
        log_error(auth_error, {"global_handler": True})
        if request.path.startswith('/api/'):
            return handle_api_error(auth_error)
        else:
            return handle_web_error(auth_error)

    @app.errorhandler(401)
    def unauthorized_error(error):
        """Standardized 401 handler"""
        auth_error = AuthenticationError(
            "Authentication required",
            ip_address=request.remote_addr if request else None
        )
        log_error(auth_error, {"global_handler": True})
        if request.path.startswith('/api/'):
            return handle_api_error(auth_error)
        else:
            return handle_web_error(auth_error)

    @app.errorhandler(429)
    def rate_limit_error(error):
        """Standardized 429 handler"""
        rate_error = RateLimitError(
            "Rate limit exceeded",
            retry_after=getattr(error, 'retry_after', None)
        )
        log_error(rate_error, {"global_handler": True})
        if request.path.startswith('/api/'):
            response, status = handle_api_error(rate_error)
            if rate_error.details.get('retry_after'):
                response.headers['Retry-After'] = str(rate_error.details['retry_after'])
            return response, status
        else:
            return handle_web_error(rate_error)
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Standardized handler for Werkzeug HTTP exceptions"""
        if request.path.startswith('/api/'):
            pipeline_error = PipLineError(
                error.description or "HTTP error occurred",
                error_code=f"HTTP_{error.code}",
                status_code=error.code
            )
            log_error(pipeline_error, {"global_handler": True, "http_exception": True})
            return handle_api_error(pipeline_error)
        else:
            return error
    
    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        """Catch-all handler for unhandled exceptions"""
        db.session.rollback()
        
        # Check if it's a CSRF error
        if "CSRF" in str(error) or "csrf" in str(error).lower():
            csrf_error = CSRFError(str(error))
            log_error(csrf_error, {"global_handler": True, "original_error": str(error)})
            if request.path.startswith('/api/'):
                return handle_api_error(csrf_error)
            else:
                return handle_web_error(csrf_error)
        
        # Convert to PipLineError
        pipeline_error = PipLineError(
            f"Unexpected error: {str(error)}",
            error_code="UNEXPECTED_ERROR",
            status_code=500
        )
        log_error(pipeline_error, {"global_handler": True, "original_error": str(error), "error_type": type(error).__name__})
        
        if request.path.startswith('/api/'):
            return handle_api_error(pipeline_error)
        else:
            return handle_web_error(pipeline_error)
        from app.utils.api_response import make_response
        return jsonify(make_response(
            data=None,
            error={'code': getattr(error, 'error_code', 'PIPELINE_ERROR'), 'message': str(error)}
        )), 400

    # CSRF Error Handler - Enhanced
    @app.errorhandler(400)
    def handle_csrf_error(error):
        """Handle CSRF errors automatically"""
        from app.services.csrf_fix_service import handle_csrf_error_safe, is_csrf_protection_enabled
        from app.utils.unified_logger import get_logger
        from flask import jsonify
        
        # Get logger
        logger = get_logger("CSRFHandler")
        
        # Check if this is a CSRF error
        if hasattr(error, 'description') and 'CSRF' in str(error.description):
            logger.warning(f"CSRF error detected: {error.description}")
            
            # Handle the CSRF error
            result = handle_csrf_error_safe(error)
            
            # Check if this is an API request
            if request.path.startswith('/api/'):
                if result.get('disabled', False):
                    # CSRF protection temporarily disabled
                    logger.warning("CSRF protection temporarily disabled due to repeated errors")
                    return jsonify({
                        'error': 'CSRF protection temporarily disabled',
                        'message': 'Please try again in a few moments',
                        'csrf_disabled': True
                    }), 200
                
                # Return JSON response for API requests
                return jsonify({
                    'error': 'CSRF validation failed',
                    'message': 'Security token is invalid or expired. Please refresh the page and try again.',
                    'csrf_error': True,
                    'new_token': result.get('token', '')
                }), 400
            
            # For web requests, return JSON response
            if result.get('disabled', False):
                # CSRF protection temporarily disabled
                logger.warning("CSRF protection temporarily disabled due to repeated errors")
                return jsonify({
                    'error': 'CSRF Protection Disabled',
                    'message': result.get('error', 'CSRF protection disabled')
                }), 200
            
            # Return a JSON error response with new token
            return jsonify({
                'error': 'CSRF Validation Failed',
                'message': result.get('error', 'CSRF validation failed'),
                'new_token': result.get('token', '')
            }), 400
        
        # Handle other 400 errors
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Bad request',
                'message': str(error) if hasattr(error, 'description') else 'Invalid request'
            }), 400
        
        return render_template('errors/400.html', error=error), 400

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle unexpected errors with unified logging and better error messages"""
        from flask import jsonify
        from app.utils.unified_logger import get_logger
        import traceback
        
        error_logger = get_logger("ErrorHandler")
        error_logger.error(f"Unexpected error: {type(error).__name__}: {error}")
        
        # Detect external service errors (yfinance, API calls, etc.)
        error_str = str(error).lower()
        is_external_service_error = any([
            'yfinance' in error_str,
            'yahoo' in error_str,
            '429' in error_str,  # Rate limit
            '503' in error_str,  # Service unavailable
            '502' in error_str,  # Bad gateway
            'timeout' in error_str,
            'connection' in error_str
        ])
        
        # Check if this is a CSRF-related error
        if 'CSRF' in str(error) or 'csrf' in str(error).lower():
            from app.services.csrf_fix_service import handle_csrf_error_safe

            result = handle_csrf_error_safe(error)
            
            # Check if this is an API request
            if request.path.startswith('/api/'):
                return jsonify({
                    'error': 'CSRF error occurred',
                    'message': 'Security token validation failed. Please refresh the page and try again.',
                    'csrf_error': True,
                    'new_token': result.get('token', '')
                }), 400
            
            return render_template('errors/csrf_error.html', 
                                 error=result.get('error', 'CSRF error occurred'),
                                 new_token=result.get('token', '')), 400
        
        # Handle external service errors (yfinance, APIs) with graceful fallback
        if is_external_service_error:
            user_message = "External service temporarily unavailable. Using cached data."
            error_logger.warning(f"External service error (using fallback): {type(error).__name__}: {error}")
            
            if request.path.startswith('/api/'):
                return jsonify({
                    'error': 'Service temporarily unavailable',
                    'message': user_message,
                    'retry_after': 60  # seconds
                }), 503
            
            return jsonify({'error': 'Service Error', 'message': user_message}), 503
        
        # Handle database errors
        if 'database' in error_str or 'sql' in error_str:
            user_message = "Database connection issue. Please try again."
            if request.path.startswith('/api/'):
                return jsonify({
                    'error': 'Database error',
                    'message': user_message
                }), 500
        
        # Handle other unexpected errors
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred. Please try again.'
            }), 500
        
        return jsonify({'error': 'Internal Server Error', 'message': 'An unexpected error occurred'}), 500
    
    # Initialize Exchange Rate Service for automatic updates
    try:
        # Use enhanced exchange rate service (legacy service deprecated)
        from app.services.enhanced_exchange_rate_service import enhanced_exchange_service
        enhanced_exchange_service.start_auto_update(app)
        app.logger.info("Exchange rate auto-update service started (using enhanced multi-provider service)")
    except Exception as e:
        app.logger.error(f"Failed to start exchange rate service: {e}")

    # Initialize CLI commands
    try:
        from app.cli_commands import register_cli_commands
        register_cli_commands(app)
        app.logger.info("CLI commands initialized")
    except Exception as e:
        app.logger.error(f"Failed to initialize CLI commands: {e}")

    # Initialize Unified Database Service
    try:
        from app.services.unified_database_service import unified_db_service
        with app.app_context():
            # create_performance_indexes is a static method that returns an integer
            indexes_created = unified_db_service.create_performance_indexes()
            if indexes_created > 0:
                app.logger.info(f"Database optimization completed: {indexes_created} indexes created")
            else:
                app.logger.info(f"Database optimization completed with no new indexes")
    except Exception as e:
        app.logger.error(f"Failed to initialize database optimization: {e}")
    
    # Optimize connection pool
    try:
        from app.utils.connection_pool_optimizer import ConnectionPoolOptimizer
        with app.app_context():
            # Get workload type from config (default: mixed)
            workload_type = app.config.get('DB_WORKLOAD_TYPE', 'mixed')
            ConnectionPoolOptimizer.optimize_for_workload(db.engine, workload_type)
            ConnectionPoolOptimizer.setup_pool_events(db.engine)
            app.logger.info("Connection pool optimized and monitoring enabled")
    except Exception as e:
        app.logger.error(f"Failed to optimize connection pool: {e}")

    # Initialize system monitoring
    try:
        from app.services.system_monitoring_service import get_system_monitor
        with app.app_context():
            system_monitor = get_system_monitor()
            system_monitor.start_monitoring(interval=60)  # Monitor every minute
            app.logger.info("System monitoring initialized")
    except Exception as e:
        app.logger.error(f"Failed to initialize system monitoring: {e}")
    
    # Initialize feature flags
    try:
        from app.utils.feature_flags import FeatureFlags
        flags = FeatureFlags.get_all_flags()
        app.logger.info(f"Feature flags initialized: {flags}")
    except Exception as e:
        app.logger.warning(f"Failed to initialize feature flags: {e}")
    
    # Initialize Prometheus metrics updater (periodic system metrics update)
    try:
        from app.utils.feature_flags import FeatureFlags
        if FeatureFlags.ENABLE_PROMETHEUS_METRICS:
            try:
                import threading
                from app.utils.prometheus_metrics import update_system_metrics
                
                def update_metrics_periodically():
                    """Update system metrics every 30 seconds"""
                    while True:
                        try:
                            with app.app_context():
                                update_system_metrics()
                            time.sleep(30)
                        except Exception as e:
                            app.logger.error(f"Error updating metrics: {e}")
                            time.sleep(30)
                
                metrics_thread = threading.Thread(target=update_metrics_periodically, daemon=True)
                metrics_thread.start()
                app.logger.info("Prometheus metrics updater started")
            except Exception as e:
                app.logger.warning(f"Failed to start Prometheus metrics updater: {e}")
    except ImportError:
        app.logger.debug("Feature flags not available, skipping Prometheus metrics updater")

    # Initialize scalability services
    try:
        from app.services.scalability_service import get_scalability_service
        with app.app_context():
            scalability_service = get_scalability_service()
            scalability_service.start_services()
            app.logger.info("Scalability services initialized")
    except Exception as e:
        app.logger.error(f"Failed to initialize scalability services: {e}")

    # Initialize scheduled backup service
    if app.config.get('BACKUP_ENABLED', True):
        try:
            from app.services.scheduled_backup_service import scheduled_backup_service
            scheduled_backup_service.init_app(app)
            scheduled_backup_service.start()
            next_backup = scheduled_backup_service.get_next_backup_time()
            if next_backup:
                app.logger.info(f"Scheduled backup service initialized - Next backup: {next_backup}")
            else:
                app.logger.info("Scheduled backup service initialized - Check schedule configuration")
        except Exception as e:
            app.logger.error(f"Failed to initialize scheduled backup service: {e}")

    return app 