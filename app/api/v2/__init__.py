"""
API v2 Blueprint Registration
Enhanced API with comprehensive documentation and microservices support
"""
from flask import Blueprint

# Import endpoints conditionally to avoid import errors
try:
    from app.api.v2.endpoints import transactions
    TRANSACTIONS_AVAILABLE = True
except ImportError:
    TRANSACTIONS_AVAILABLE = False

try:
    from app.api.v2.endpoints import analytics
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False

try:
    from app.api.v2.endpoints import users
    USERS_AVAILABLE = True
except ImportError:
    USERS_AVAILABLE = False

try:
    from app.api.v2.endpoints import health
    HEALTH_AVAILABLE = True
except ImportError:
    HEALTH_AVAILABLE = False

try:
    from app.api.v2.endpoints import real_time
    REALTIME_AVAILABLE = True
except ImportError:
    REALTIME_AVAILABLE = False

try:
    from app.api.v2.endpoints import cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

try:
    from app.api.v2.endpoints import services
    SERVICES_AVAILABLE = True
except ImportError:
    SERVICES_AVAILABLE = False

try:
    from app.api.v2.endpoints import webhooks
    WEBHOOKS_AVAILABLE = True
except ImportError:
    WEBHOOKS_AVAILABLE = False

# Create the main API v2 blueprint
api_v2 = Blueprint('api_v2', __name__, url_prefix='/api/v2')

# Register endpoint blueprints conditionally
if TRANSACTIONS_AVAILABLE:
    api_v2.register_blueprint(transactions.transactions_api, url_prefix='/transactions')

if ANALYTICS_AVAILABLE:
    api_v2.register_blueprint(analytics.analytics_api, url_prefix='/analytics')

if USERS_AVAILABLE:
    api_v2.register_blueprint(users.users_api, url_prefix='/users')

if HEALTH_AVAILABLE:
    api_v2.register_blueprint(health.health_api, url_prefix='/health')

if REALTIME_AVAILABLE:
    api_v2.register_blueprint(real_time.real_time_api, url_prefix='/realtime')

if CACHE_AVAILABLE:
    api_v2.register_blueprint(cache.cache_api, url_prefix='/cache')

if SERVICES_AVAILABLE:
    api_v2.register_blueprint(services.services_api, url_prefix='/services')

if WEBHOOKS_AVAILABLE:
    api_v2.register_blueprint(webhooks.webhooks_api, url_prefix='/webhooks')

@api_v2.route("/")
def api_root():
    """API v2 root endpoint with comprehensive documentation"""
    return {
        'api_version': '2.0',
        'name': 'PipLinePro API v2',
        'description': 'Enhanced API with microservices support and real-time capabilities',
        'documentation': '/api/v2/docs',
        'endpoints': {
            'transactions': '/api/v2/transactions',
            'analytics': '/api/v2/analytics',
            'users': '/api/v2/users',
            'health': '/api/v2/health',
            'realtime': '/api/v2/realtime',
            'cache': '/api/v2/cache',
            'services': '/api/v2/services',
            'webhooks': '/api/v2/webhooks'
        },
        'features': [
            'Real-time WebSocket connections',
            'Event-driven architecture',
            'Advanced caching with Redis',
            'Microservices support',
            'Comprehensive monitoring',
            'Webhook integrations',
            'Rate limiting',
            'API versioning'
        ],
        'authentication': {
            'type': 'Bearer Token',
            'header': 'Authorization: Bearer <token>',
            'endpoint': '/api/v2/auth/token'
        },
        'rate_limits': {
            'default': '1000 requests per hour',
            'authenticated': '10000 requests per hour',
            'premium': '100000 requests per hour'
        }
    }

@api_v2.route("/docs")
def api_docs():
    """API documentation endpoint"""
    return {
        'title': 'PipLinePro API v2 Documentation',
        'version': '2.0.0',
        'description': 'Complete API documentation for PipLinePro v2',
        'sections': {
            'authentication': {
                'description': 'How to authenticate with the API',
                'endpoints': [
                    'POST /api/v2/auth/login',
                    'POST /api/v2/auth/refresh',
                    'POST /api/v2/auth/logout'
                ]
            },
            'transactions': {
                'description': 'Transaction management endpoints',
                'endpoints': [
                    'GET /api/v2/transactions',
                    'POST /api/v2/transactions',
                    'GET /api/v2/transactions/{id}',
                    'PUT /api/v2/transactions/{id}',
                    'DELETE /api/v2/transactions/{id}',
                    'GET /api/v2/transactions/bulk',
                    'POST /api/v2/transactions/bulk'
                ]
            },
            'analytics': {
                'description': 'Analytics and reporting endpoints',
                'endpoints': [
                    'GET /api/v2/analytics/dashboard',
                    'GET /api/v2/analytics/psp-summary',
                    'GET /api/v2/analytics/trends',
                    'GET /api/v2/analytics/reports'
                ]
            },
            'realtime': {
                'description': 'Real-time data streaming',
                'endpoints': [
                    'WebSocket /api/v2/realtime/connect',
                    'GET /api/v2/realtime/events',
                    'POST /api/v2/realtime/subscribe'
                ]
            },
            'webhooks': {
                'description': 'Webhook management',
                'endpoints': [
                    'GET /api/v2/webhooks',
                    'POST /api/v2/webhooks',
                    'GET /api/v2/webhooks/{id}',
                    'PUT /api/v2/webhooks/{id}',
                    'DELETE /api/v2/webhooks/{id}',
                    'POST /api/v2/webhooks/{id}/test'
                ]
            }
        },
        'examples': {
            'create_transaction': {
                'method': 'POST',
                'url': '/api/v2/transactions',
                'headers': {
                    'Authorization': 'Bearer <token>',
                    'Content-Type': 'application/json'
                },
                'body': {
                    'client_name': 'John Doe',
                    'amount': 1000.00,
                    'currency': 'TL',
                    'psp': 'STRIPE',
                    'category': 'DEP',
                    'date': '2024-01-15'
                }
            },
            'get_analytics': {
                'method': 'GET',
                'url': '/api/v2/analytics/dashboard?start_date=2024-01-01&end_date=2024-01-31',
                'headers': {
                    'Authorization': 'Bearer <token>'
                }
            }
        },
        'error_codes': {
            '400': 'Bad Request - Invalid input data',
            '401': 'Unauthorized - Invalid or missing authentication',
            '403': 'Forbidden - Insufficient permissions',
            '404': 'Not Found - Resource not found',
            '429': 'Too Many Requests - Rate limit exceeded',
            '500': 'Internal Server Error - Server error occurred'
        }
    }
