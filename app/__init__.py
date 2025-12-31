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
from flask_jwt_extended import JWTManager
from datetime import timedelta
import os
import traceback
import time
import signal
import atexit

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
jwt = JWTManager()  # JWT for token-based authentication (fallback for cookie issues)

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
    
    # SECURITY: Validate CORS origins in production
    is_production = os.environ.get('FLASK_ENV') == 'production'
    if is_production:
        if not cors_origins or len(cors_origins) == 0:
            app.logger.warning(
                "CORS_ORIGINS is empty in production! This may cause CORS errors. "
                "Set CORS_ORIGINS environment variable with your frontend domain(s)."
            )
        else:
            # Validate that origins are proper URLs
            from urllib.parse import urlparse
            invalid_origins = []
            for origin in cors_origins:
                parsed = urlparse(origin)
                if not parsed.scheme or not parsed.netloc:
                    invalid_origins.append(origin)
            
            if invalid_origins:
                app.logger.error(
                    f"Invalid CORS origins detected: {invalid_origins}. "
                    "CORS origins must be valid URLs (e.g., https://example.com)."
                )
                # In production, fail if invalid origins are detected
                raise ValueError(f"Invalid CORS origins: {invalid_origins}")
    
    CORS(app, 
         resources={r"/api/*": {
             "origins": cors_origins,
             "methods": app.config.get('CORS_METHODS', ["GET", "POST", "PUT", "DELETE", "OPTIONS"]),
             "allow_headers": app.config.get('CORS_ALLOW_HEADERS', ["Content-Type", "Authorization", "X-Requested-With", "X-CSRFToken", "Accept"]),
             "expose_headers": app.config.get('CORS_EXPOSE_HEADERS', ["Content-Type", "Authorization", "Set-Cookie"]),
             "supports_credentials": app.config.get('CORS_SUPPORTS_CREDENTIALS', True),
             "max_age": app.config.get('CORS_MAX_AGE', 3600),
             "send_wildcard": False,
             "always_send": True
         }}
    )
    
    # Log CORS configuration for debugging
    app.logger.info(f"CORS enabled for origins: {cors_origins}")
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')
    jwt.init_app(app)  # Initialize JWT for token-based authentication
    
    # Initialize Flask-Session BEFORE other extensions that might use sessions
    try:
        from flask_session import Session
        sess = Session()
        sess.init_app(app)
        app.logger.info("Flask-Session initialized successfully")
    except ImportError:
        app.logger.warning("Flask-Session not available, using default Flask session")
    
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
    
    # Initialize tenant middleware for multi-tenancy support
    from app.middleware.tenant_middleware import tenant_middleware
    tenant_middleware.init_app(app)
    app.tenant_middleware = tenant_middleware
    
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
        # Return minimal stats to avoid any potential errors during template rendering
        # The full performance data is available via API endpoints
        try:
            cache_stats = {}
            redis_stats = {}
            background_stats = {}
            pool_size = 0
            pool_checkedin = 0
            pool_checkedout = 0
            
            # Safely get cache stats
            try:
                cache_stats = advanced_cache.get_stats() if advanced_cache else {}
            except Exception:
                pass
            
            # Safely get redis stats (only if connected)
            try:
                if redis_service and redis_service.is_connected():
                    redis_stats = redis_service.get_stats()
            except Exception:
                pass
            
            # Skip background_task_service.get_queue_stats() as it can be slow/fail
            # This data is available via the performance API endpoint
            
            # Safely get pool stats
            try:
                if hasattr(db.engine, 'pool'):
                    pool = db.engine.pool
                    if hasattr(pool, 'size') and callable(pool.size):
                        pool_size = pool.size()
                    if hasattr(pool, 'checkedin') and callable(pool.checkedin):
                        pool_checkedin = pool.checkedin()
                    if hasattr(pool, 'checkedout') and callable(pool.checkedout):
                        pool_checkedout = pool.checkedout()
            except Exception:
                pass
            
            return {
                'cache_stats': cache_stats,
                'redis_stats': redis_stats,
                'background_stats': background_stats,
                'db_pool_size': pool_size,
                'db_pool_checked_in': pool_checkedin,
                'db_pool_checked_out': pool_checkedout,
            }
        except Exception:
            # If there's any error, return empty stats
            return {
                'cache_stats': {},
                'redis_stats': {},
                'background_stats': {},
                'db_pool_size': 0,
                'db_pool_checked_in': 0,
                'db_pool_checked_out': 0,
            }
    
    # Configure session for cross-origin requests (both development and production)
    # CRITICAL: These settings must be set for both dev and production
    is_https = app.config.get('SESSION_COOKIE_SECURE', False)
    
    # Session cookie settings - apply to all environments
    app.config['SESSION_COOKIE_DOMAIN'] = None  # None allows all domains (set specific domain if needed)
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Lax allows same-site and top-level navigation
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Keep HTTPOnly for security
    app.config['SESSION_COOKIE_PATH'] = '/'  # Ensure cookie is set for all paths
    app.config['SESSION_COOKIE_NAME'] = 'pipelinepro_session'  # Custom session cookie name
    
    # Default session lifetime (overridden per-session in auth.py based on remember_me)
    # Regular login: 8 hours, Remember me: 30 days
    if 'PERMANENT_SESSION_LIFETIME' not in app.config:
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
    
    # Enhanced session configuration for React frontend
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True  # Refresh session on each request
    
    # Ensure session directory exists for filesystem sessions
    if app.config.get('SESSION_TYPE') == 'filesystem':
        import pathlib
        session_dir = pathlib.Path(app.config.get('SESSION_FILE_DIR', 'instance/sessions'))
        session_dir.mkdir(parents=True, exist_ok=True)
        app.logger.info(f"Session directory: {session_dir}")
        
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
    
    # Initialize and start monitoring service in production
    try:
        from app.services.monitoring_service import get_monitoring_service
        monitoring_service = get_monitoring_service()
        # Start monitoring with 60 second interval (production-optimized)
        monitoring_service.start_monitoring(interval=60)
        app.logger.info("Production monitoring service started")
    except Exception as e:
        app.logger.warning(f"Failed to start monitoring service: {e}")
    
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
        from app.config.public_endpoints import is_public_endpoint
        
        # Check if this is a public endpoint
        if is_public_endpoint(request.path):
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
            # Try to convert to int, but handle UUID strings gracefully
            try:
                user_id_int = int(user_id)
                user = User.query.get(user_id_int)
            except (ValueError, TypeError):
                # If conversion fails, it might be a UUID or other format
                # Try to query by username or other identifier
                logger = get_logger("UserLoader")
                logger.warning(f"User ID {user_id} is not an integer, attempting alternative lookup")
                user = User.query.filter_by(username=str(user_id)).first()
                if not user:
                    # Try as string ID if your User model supports it
                    user = User.query.filter_by(id=user_id).first()
            
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
    from app.api.v1.endpoints.debug_clients import debug_clients_bp
    
    app.register_blueprint(auth_api, url_prefix='/api/v1/auth')
    app.register_blueprint(consolidated_dashboard_api, url_prefix='/api/v1')
    app.register_blueprint(commission_rates_api, url_prefix='/api/v1/commission-rates')
    app.register_blueprint(performance_api, url_prefix='/api/v1/performance')
    app.register_blueprint(monitoring_api, url_prefix='/api/v1')
    app.register_blueprint(system_stats_api, url_prefix='/api/v1/system')
    app.register_blueprint(financial_performance_bp, url_prefix='/api/v1')
    app.register_blueprint(notifications_api, url_prefix='/api/v1')
    app.register_blueprint(accounting_api, url_prefix='/api/v1/accounting')
    app.register_blueprint(debug_clients_bp, url_prefix='/api/v1')
    
    # Register enhanced monitoring & metrics endpoints
    from app.routes.monitoring import monitoring_bp, setup_prometheus_metrics
    app.register_blueprint(monitoring_bp)
    
    # Production optimization: Direct /api/health endpoint to fix 404 errors
    # Some monitoring tools don't follow redirects, so we provide direct response
    @app.route('/api/health', methods=['GET', 'HEAD'], strict_slashes=False)
    def direct_health_check():
        """Direct health check endpoint for monitoring tools that don't follow redirects"""
        try:
            from app.services.health_check_service import health_check_service
            from datetime import datetime, timezone
            
            result = health_check_service.check_basic()
            status_code = 200 if result.get('status') == 'healthy' else 503
            
            return jsonify({
                'status': result.get('status', 'healthy'),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'service': 'PipLinePro',
                'checks': result.get('checks', {})
            }), status_code
        except Exception as e:
            # Fallback response if health check service fails
            from datetime import datetime, timezone
            app.logger.error(f"Health check error: {e}")
            return jsonify({
                'status': 'unhealthy',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'service': 'PipLinePro',
                'error': str(e)
            }), 503
    
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
    # Check dist_new first (current build output), then dist, then dist_prod as fallback
    base_dir = os.path.dirname(os.path.dirname(__file__))
    frontend_dist = os.path.join(base_dir, 'frontend', 'dist_new')
    if not os.path.exists(frontend_dist):
        frontend_dist = os.path.join(base_dir, 'frontend', 'dist')
    if not os.path.exists(frontend_dist):
        frontend_dist = os.path.join(base_dir, 'frontend', 'dist_prod')
    
    # Log which directory is being used
    app.logger.info(f"Serving frontend from: {frontend_dist}")
    
    @app.route('/')
    def root():
        """Root route - serve React frontend or redirect to login"""
        try:
            # Check if frontend build exists
            app.logger.info(f"Root route called! frontend_dist={frontend_dist}")
            index_path = os.path.join(frontend_dist, 'index.html')
            app.logger.info(f"Root route: checking index at {index_path}")
            exists = os.path.exists(index_path)
            app.logger.info(f"Index exists: {exists}")
            if exists:
                app.logger.info("Serving index.html")
                # Serve React frontend with proper headers
                with open(index_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                from flask import make_response
                response = make_response(content)
                # Ensure proper content type
                response.headers['Content-Type'] = 'text/html; charset=utf-8'
                # Disable caching for index.html to ensure fresh content
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
                app.logger.info("Returning index.html response")
                return response
            else:
                # Fallback: redirect to login API
                app.logger.warning(f"Index.html not found at {index_path}, redirecting to docs")
                return redirect('/api/v1/docs/')
        except Exception as e:
            app.logger.error(f"Error in root route: {type(e).__name__}: {e}")
            import traceback
            app.logger.error(traceback.format_exc())
            raise
    
    # Explicit route for JS chunks to ensure proper serving
    @app.route('/js/<path:filename>')
    def serve_js_chunk(filename):
        """Serve JavaScript chunks with proper headers"""
        import time
        start_time = time.time()
        request_id = f"js_{int(time.time() * 1000)}"
        
        # Get base_dir for fallback
        base_dir_local = os.path.dirname(os.path.dirname(__file__))
        current_frontend_dist = frontend_dist
        
        app.logger.info(f"[{request_id}] ========== JS CHUNK REQUEST START ==========")
        app.logger.info(f"[{request_id}] Requested filename: {filename}")
        app.logger.info(f"[{request_id}] Frontend dist directory: {current_frontend_dist}")
        app.logger.info(f"[{request_id}] Request headers: {dict(request.headers)}")
        app.logger.info(f"[{request_id}] Request method: {request.method}")
        app.logger.info(f"[{request_id}] Request URL: {request.url}")
        app.logger.info(f"[{request_id}] Request remote_addr: {request.remote_addr}")
        
        js_path = os.path.join(current_frontend_dist, 'js', filename)
        app.logger.info(f"[{request_id}] Full JS path: {js_path}")
        app.logger.info(f"[{request_id}] Path exists: {os.path.exists(js_path)}")
        app.logger.info(f"[{request_id}] Path is file: {os.path.isfile(js_path) if os.path.exists(js_path) else 'N/A'}")
        
        # Fallback: check dist if not found in dist_new
        if not os.path.exists(js_path) or not os.path.isfile(js_path):
            dist_fallback = os.path.join(base_dir_local, 'frontend', 'dist', 'js', filename)
            if os.path.exists(dist_fallback) and os.path.isfile(dist_fallback):
                app.logger.info(f"[{request_id}] Using fallback path: {dist_fallback}")
                js_path = dist_fallback
                current_frontend_dist = os.path.join(base_dir_local, 'frontend', 'dist')
        
        if os.path.exists(js_path) and os.path.isfile(js_path):
            try:
                file_size = os.path.getsize(js_path)
                app.logger.info(f"[{request_id}] File size: {file_size} bytes")
                
                response = send_from_directory(os.path.join(current_frontend_dist, 'js'), filename)
                response.headers['Content-Type'] = 'application/javascript; charset=utf-8'
                response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
                # Add CORS headers for module loading
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
                
                elapsed = time.time() - start_time
                app.logger.info(f"[{request_id}] ✅ SUCCESS - Serving file in {elapsed:.3f}s")
                app.logger.info(f"[{request_id}] Response status: {response.status_code}")
                app.logger.info(f"[{request_id}] Response headers: {dict(response.headers)}")
                app.logger.info(f"[{request_id}] ========== JS CHUNK REQUEST END ==========")
                return response
            except Exception as e:
                elapsed = time.time() - start_time
                app.logger.error(f"[{request_id}] ❌ ERROR serving file after {elapsed:.3f}s: {str(e)}", exc_info=True)
                app.logger.info(f"[{request_id}] ========== JS CHUNK REQUEST END (ERROR) ==========")
                return jsonify({'error': f'Error serving JS chunk: {str(e)}'}), 500
        
        # File not found - log directory contents
        js_dir = os.path.join(current_frontend_dist, 'js')
        app.logger.error(f"[{request_id}] ❌ JS chunk not found: {filename}")
        app.logger.error(f"[{request_id}] JS directory exists: {os.path.exists(js_dir)}")
        if os.path.exists(js_dir):
            try:
                files_in_js_dir = os.listdir(js_dir)
                app.logger.error(f"[{request_id}] Files in js directory ({len(files_in_js_dir)}): {files_in_js_dir}")
                # Check for similar filenames
                matching_files = [f for f in files_in_js_dir if 'accounting' in f.lower() or filename.split('-')[0] in f]
                if matching_files:
                    app.logger.error(f"[{request_id}] Similar files found: {matching_files}")
            except Exception as e:
                app.logger.error(f"[{request_id}] Error listing js directory: {e}")
        
        app.logger.info(f"[{request_id}] ========== JS CHUNK REQUEST END (404) ==========")
        return jsonify({'error': f'JS chunk not found: {filename}', 'request_id': request_id}), 404
    
    # Explicit route for CSS files
    @app.route('/css/<path:filename>')
    def serve_css(filename):
        """Serve CSS files with proper headers"""
        # Get base_dir for fallback
        base_dir_local = os.path.dirname(os.path.dirname(__file__))
        current_frontend_dist = frontend_dist
        
        css_path = os.path.join(current_frontend_dist, 'css', filename)
        # Fallback: check dist if not found in dist_new
        if not os.path.exists(css_path) or not os.path.isfile(css_path):
            dist_fallback = os.path.join(base_dir_local, 'frontend', 'dist', 'css', filename)
            if os.path.exists(dist_fallback) and os.path.isfile(dist_fallback):
                app.logger.info(f"Using CSS fallback path: {dist_fallback}")
                css_path = dist_fallback
                current_frontend_dist = os.path.join(base_dir_local, 'frontend', 'dist')
            
        if os.path.exists(css_path) and os.path.isfile(css_path):
            response = send_from_directory(os.path.join(current_frontend_dist, 'css'), filename)
            response.headers['Content-Type'] = 'text/css; charset=utf-8'
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
            return response
        return jsonify({'error': f'CSS file not found: {filename}'}), 404
    
    @app.route('/<path:path>')
    def serve_frontend(path):
        """Serve React frontend static files"""
        # Skip API routes - they're handled by blueprints
        if path.startswith('api/'):
            return jsonify({'error': 'Not found'}), 404
        
        # Check if file exists in frontend build
        file_path = os.path.join(frontend_dist, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            response = send_from_directory(frontend_dist, path)
            # Set proper content type for JS modules
            if path.endswith('.js'):
                response.headers['Content-Type'] = 'application/javascript; charset=utf-8'
            elif path.endswith('.css'):
                response.headers['Content-Type'] = 'text/css; charset=utf-8'
            # Cache static assets (but not index.html)
            if path != 'index.html':
                response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
            return response
        else:
            # For SPA routing, serve index.html for non-API routes
            index_path = os.path.join(frontend_dist, 'index.html')
            if os.path.exists(index_path):
                response = send_from_directory(frontend_dist, 'index.html')
                # Disable caching for index.html
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
                return response
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
    
    # REMOVED: Duplicate Exception handler - handle_unexpected_error below is the active one
    # This handler was never called because Flask only uses the last registered handler

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
        # Import at the top to ensure availability
        from flask import jsonify, current_app, request
        from app.utils.unified_logger import get_logger
        import traceback
        
        # Rollback database session on error
        try:
            db.session.rollback()
        except Exception as rollback_error:
            pass
        
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
            else:
                # For web requests, return error response
                return jsonify({
                    'error': 'Database error',
                    'message': user_message
                }), 500
        
        # Handle other unexpected errors
        # SECURITY: Never expose internal error details in production
        try:
            is_debug = current_app.config.get('DEBUG', False)
        except (RuntimeError, AttributeError):
            # If current_app is not available (e.g., outside request context), default to False
            is_debug = False
        
        if request.path.startswith('/api/'):
            error_message = 'An unexpected error occurred. Please try again.'
            # Only include error details in debug mode
            if is_debug:
                error_message = f'An unexpected error occurred: {str(error)}'
            
            return jsonify({
                'error': 'Internal server error',
                'message': error_message
            }), 500
        
        # For web requests, never expose error details
        return jsonify({
            'error': 'Internal Server Error', 
            'message': 'An unexpected error occurred. Please contact support if this persists.'
        }), 500
    
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
            # Enable SQLite WAL mode persistently if using SQLite
            db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            if 'sqlite' in db_uri.lower():
                try:
                    from sqlalchemy import text
                    # Set WAL mode for SQLite (persists across connections)
                    db.session.execute(text("PRAGMA journal_mode=WAL"))
                    db.session.execute(text("PRAGMA synchronous=NORMAL"))
                    db.session.execute(text("PRAGMA cache_size=10000"))
                    db.session.commit()
                    app.logger.info("SQLite WAL mode enabled and configured")
                except Exception as wal_error:
                    app.logger.warning(f"Could not enable SQLite WAL mode: {wal_error}")
            
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
    
    # Add session timeout enforcement and request timeout middleware
    @app.before_request
    def enforce_session_timeout():
        """Enforce session timeout on all authenticated requests"""
        from flask import session, request, jsonify
        from flask_login import current_user
        from datetime import datetime, timezone
        import json
        
        # #region agent log
        try:
            with open(r'c:\PipLinePro\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"runtime","hypothesisId":"A","location":"app/__init__.py:1248","message":"Session timeout check started","data":{"is_authenticated":current_user.is_authenticated,"path":request.path},"timestamp":int(datetime.now().timestamp()*1000)}) + '\n')
        except: pass
        # #endregion
        
        # Enforce session timeout on all authenticated requests
        if current_user.is_authenticated:
            session_timeout = app.config.get('PERMANENT_SESSION_LIFETIME')
            # #region agent log
            try:
                with open(r'c:\PipLinePro\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"runtime","hypothesisId":"A","location":"app/__init__.py:1256","message":"Session timeout config","data":{"timeout_seconds":session_timeout.total_seconds() if session_timeout else None},"timestamp":int(datetime.now().timestamp()*1000)}) + '\n')
            except: pass
            # #endregion
            if session_timeout:
                session_created = session.get('_session_created')
                # #region agent log
                try:
                    with open(r'c:\PipLinePro\.cursor\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"runtime","hypothesisId":"A","location":"app/__init__.py:1261","message":"Session created time","data":{"session_created":str(session_created) if session_created else None},"timestamp":int(datetime.now().timestamp()*1000)}) + '\n')
                except: pass
                # #endregion
                if session_created:
                    try:
                        if isinstance(session_created, str):
                            session_created = datetime.fromisoformat(session_created.replace('Z', '+00:00'))
                        
                        if isinstance(session_created, datetime):
                            if session_created.tzinfo is None:
                                session_created = session_created.replace(tzinfo=timezone.utc)
                            
                            session_age = datetime.now(timezone.utc) - session_created
                            # #region agent log
                            try:
                                with open(r'c:\PipLinePro\.cursor\debug.log', 'a', encoding='utf-8') as f:
                                    f.write(json.dumps({"sessionId":"debug-session","runId":"runtime","hypothesisId":"A","location":"app/__init__.py:1274","message":"Session age calculated","data":{"session_age_seconds":session_age.total_seconds(),"timeout_seconds":session_timeout.total_seconds(),"is_expired":session_age > session_timeout},"timestamp":int(datetime.now().timestamp()*1000)}) + '\n')
                            except: pass
                            # #endregion
                            if session_age > session_timeout:
                                # Session expired - logout and return error
                                from flask_login import logout_user
                                logout_user()
                                # #region agent log
                                try:
                                    with open(r'c:\PipLinePro\.cursor\debug.log', 'a', encoding='utf-8') as f:
                                        f.write(json.dumps({"sessionId":"debug-session","runId":"runtime","hypothesisId":"A","location":"app/__init__.py:1282","message":"Session expired - user logged out","data":{"path":request.path},"timestamp":int(datetime.now().timestamp()*1000)}) + '\n')
                                except: pass
                                # #endregion
                                if request.path.startswith('/api/'):
                                    return jsonify({
                                        'error': 'Session expired',
                                        'message': 'Your session has expired. Please log in again.'
                                    }), 401
                                # For non-API requests, redirect handled by Flask-Login
                    except (ValueError, TypeError) as e:
                        app.logger.warning(f"Error checking session timeout: {e}")
                        # #region agent log
                        try:
                            with open(r'c:\PipLinePro\.cursor\debug.log', 'a', encoding='utf-8') as f:
                                f.write(json.dumps({"sessionId":"debug-session","runId":"runtime","hypothesisId":"A","location":"app/__init__.py:1293","message":"Session timeout check error","data":{"error":str(e)},"timestamp":int(datetime.now().timestamp()*1000)}) + '\n')
                        except: pass
                        # #endregion
                else:
                    # No session creation time - set it now
                    session['_session_created'] = datetime.now(timezone.utc).isoformat()
                    session.modified = True
                    # #region agent log
                    try:
                        with open(r'c:\PipLinePro\.cursor\debug.log', 'a', encoding='utf-8') as f:
                            f.write(json.dumps({"sessionId":"debug-session","runId":"runtime","hypothesisId":"A","location":"app/__init__.py:1300","message":"Session created time set","data":{"created_time":session['_session_created']},"timestamp":int(datetime.now().timestamp()*1000)}) + '\n')
                    except: pass
                    # #endregion
    
    # Add periodic connection pool monitoring
    try:
        import threading
        from app.utils.connection_pool_optimizer import ConnectionPoolOptimizer
        
        def monitor_connection_pool():
            """Periodically monitor connection pool and log warnings"""
            import json
            from datetime import datetime
            while True:
                try:
                    time.sleep(60)  # Check every minute
                    with app.app_context():
                        stats = ConnectionPoolOptimizer.get_pool_stats(db.engine)
                        utilization = stats.get('utilization', 0)
                        # #region agent log
                        try:
                            with open(r'c:\PipLinePro\.cursor\debug.log', 'a', encoding='utf-8') as f:
                                f.write(json.dumps({"sessionId":"debug-session","runId":"runtime","hypothesisId":"F","location":"app/__init__.py:1289","message":"Connection pool stats collected","data":{"pool_size":stats.get('size'),"checked_out":stats.get('checked_out'),"utilization":utilization},"timestamp":int(datetime.now().timestamp()*1000)}) + '\n')
                        except: pass
                        # #endregion
                        
                        # Warn if pool utilization is high
                        if utilization > 80:
                            app.logger.warning(
                                f"High connection pool utilization: {utilization:.1f}% - "
                                f"Size: {stats.get('size', 0)}, "
                                f"Checked out: {stats.get('checked_out', 0)}"
                            )
                except Exception as e:
                    app.logger.error(f"Error in connection pool monitoring: {e}")
                    # #region agent log
                    try:
                        with open(r'c:\PipLinePro\.cursor\debug.log', 'a', encoding='utf-8') as f:
                            f.write(json.dumps({"sessionId":"debug-session","runId":"runtime","hypothesisId":"F","location":"app/__init__.py:1304","message":"Connection pool monitoring error","data":{"error":str(e)},"timestamp":int(datetime.now().timestamp()*1000)}) + '\n')
                    except: pass
                    # #endregion
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_connection_pool, daemon=True)
        monitor_thread.start()
        app.logger.info("Connection pool monitoring started")
    except Exception as e:
        app.logger.warning(f"Could not start connection pool monitoring: {e}")

    return app 