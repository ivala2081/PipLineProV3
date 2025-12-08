"""
API Versioning Middleware
Adds versioning headers and deprecation warnings to API responses
"""
from flask import request, jsonify, make_response
from functools import wraps
from datetime import datetime

# API Version Information
API_VERSIONS = {
    'v1': {
        'status': 'stable',
        'sunset_date': None,  # No sunset date yet
        'description': 'Stable production API',
        'documentation': '/api/v1/docs'
    },
    'v2': {
        'status': 'beta',
        'sunset_date': None,
        'description': 'Beta API with microservices support',
        'documentation': '/api/v2/docs'
    },
    'legacy': {
        'status': 'deprecated',
        'sunset_date': '2026-01-01',  # Planned sunset date
        'description': 'Legacy routes - migrate to /api/v1 or /api/v2',
        'documentation': '/docs/API_VERSIONING.md'
    }
}

def get_api_version_from_path(path):
    """Determine API version from request path"""
    if path.startswith('/api/v2'):
        return 'v2'
    elif path.startswith('/api/v1'):
        return 'v1'
    elif path.startswith('/api/') or any(path.startswith(f'/{route}') for route in [
        'auth', 'transactions', 'analytics', 'settings', 'health', 
        'responsive', 'font-analytics', 'admin', 'exchange-rates'
    ]):
        return 'legacy'
    return None

def add_api_version_headers(response, version_info):
    """Add API versioning headers to response"""
    if not version_info:
        return response
    
    # Add standard API version headers
    response.headers['X-API-Version'] = version_info.get('version', 'unknown')
    response.headers['X-API-Status'] = version_info.get('status', 'stable')
    
    # Add deprecation warning if applicable
    if version_info['status'] == 'deprecated':
        sunset_date = version_info.get('sunset_date')
        if sunset_date:
            response.headers['Deprecation'] = 'true'
            response.headers['Sunset'] = sunset_date
            response.headers['Link'] = '</api/v1>; rel="successor-version"'
            response.headers['Warning'] = f'299 - "This API version is deprecated and will be removed on {sunset_date}. Please migrate to /api/v1"'
    
    # Add beta warning if applicable
    elif version_info['status'] == 'beta':
        response.headers['Warning'] = '299 - "This API version is in beta. Features may change without notice."'
    
    # Add documentation link
    if version_info.get('documentation'):
        response.headers['X-API-Documentation'] = version_info['documentation']
    
    return response

def create_api_versioning_middleware(app):
    """Create and register API versioning middleware"""
    
    @app.after_request
    def add_versioning_headers(response):
        """Add versioning headers to all API responses"""
        # Only add headers to API routes
        path = request.path
        
        # Determine API version
        api_version = get_api_version_from_path(path)
        
        if api_version and api_version in API_VERSIONS:
            version_config = API_VERSIONS[api_version]
            version_info = {
                'version': api_version,
                'status': version_config['status'],
                'sunset_date': version_config.get('sunset_date'),
                'documentation': version_config.get('documentation'),
                'description': version_config.get('description')
            }
            
            response = add_api_version_headers(response, version_info)
        
        return response
    
    # Add API versioning info endpoint
    @app.route('/api/versions')
    def api_versions():
        """Get information about all API versions"""
        return jsonify({
            'current_version': 'v1',
            'latest_version': 'v2',
            'supported_versions': ['v1', 'v2'],
            'versions': {
                'v1': {
                    'status': API_VERSIONS['v1']['status'],
                    'description': API_VERSIONS['v1']['description'],
                    'base_url': '/api/v1',
                    'documentation': API_VERSIONS['v1']['documentation'],
                    'sunset_date': API_VERSIONS['v1'].get('sunset_date'),
                    'features': [
                        'Stable production endpoints',
                        'Full CRUD operations',
                        'Analytics and reporting',
                        'Transaction management',
                        'User management',
                        'Exchange rate management'
                    ]
                },
                'v2': {
                    'status': API_VERSIONS['v2']['status'],
                    'description': API_VERSIONS['v2']['description'],
                    'base_url': '/api/v2',
                    'documentation': API_VERSIONS['v2']['documentation'],
                    'sunset_date': API_VERSIONS['v2'].get('sunset_date'),
                    'features': [
                        'Beta features',
                        'Real-time WebSocket support',
                        'Webhook integrations',
                        'Advanced caching',
                        'Microservices architecture',
                        'Event-driven design'
                    ]
                },
                'legacy': {
                    'status': API_VERSIONS['legacy']['status'],
                    'description': API_VERSIONS['legacy']['description'],
                    'base_url': '/',
                    'documentation': None,
                    'sunset_date': API_VERSIONS['legacy'].get('sunset_date'),
                    'migration_guide': 'Please migrate to /api/v1 for stable endpoints or /api/v2 for beta features'
                }
            },
            'migration': {
                'from_legacy_to_v1': {
                    'description': 'Migrate from legacy routes to API v1',
                    'examples': [
                        {'old': '/transactions', 'new': '/api/v1/transactions'},
                        {'old': '/analytics', 'new': '/api/v1/analytics'},
                        {'old': '/auth', 'new': '/api/v1/auth'}
                    ]
                },
                'from_v1_to_v2': {
                    'description': 'Upgrade to API v2 for new features',
                    'note': 'v2 is currently in beta. Use v1 for production workloads.',
                    'examples': [
                        {'v1': '/api/v1/transactions', 'v2': '/api/v2/transactions'},
                        {'v1': '/api/v1/analytics', 'v2': '/api/v2/analytics'}
                    ]
                }
            }
        })
    
    app.logger.info("API versioning middleware initialized")

