"""
Tenant Middleware for Multi-Tenancy Support
Automatically sets and enforces organization context for all requests
"""
import logging
from functools import wraps
from flask import g, request, current_app
from flask_login import current_user

logger = logging.getLogger(__name__)


class TenantMiddleware:
    """
    Middleware to handle multi-tenancy context.
    
    This middleware:
    1. Sets the current organization context (g.organization_id) for authenticated users
    2. Provides decorators for enforcing tenant isolation in views
    3. Provides query filters for automatic tenant filtering
    """
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the middleware with the Flask app"""
        self.app = app
        
        # Register before_request handler
        app.before_request(self._set_tenant_context)
        
        # Register after_request handler for logging
        app.after_request(self._log_tenant_context)
        
        logger.info("Tenant middleware initialized")
    
    def _set_tenant_context(self):
        """
        Set the tenant context for the current request.
        Called before each request.
        """
        # Default: no organization context
        g.organization_id = None
        g.organization = None
        g.is_super_admin = False
        
        # Skip for static files and health checks
        if request.path.startswith('/static') or request.path.startswith('/api/v1/health'):
            return
        
        # Check if user is authenticated
        if current_user and current_user.is_authenticated:
            try:
                # Get organization from user
                org_id = getattr(current_user, 'organization_id', None)
                
                if org_id:
                    g.organization_id = org_id
                    
                    # Optionally load full organization object
                    # Only if needed for the request (lazy loading)
                    # g.organization = current_user.organization
                    
                    # Check if user is super admin (can access all orgs)
                    # Super admins have admin_level 0 or 1
                    admin_level = getattr(current_user, 'admin_level', None)
                    if admin_level in [0, 1]:
                        g.is_super_admin = True
                        
                        # Check for organization override header (for super admins)
                        override_org = request.headers.get('X-Organization-ID')
                        if override_org:
                            try:
                                g.organization_id = int(override_org)
                                logger.debug(f"Super admin overriding org to {g.organization_id}")
                            except ValueError:
                                pass
                else:
                    # User has no organization - assign to default (ID: 1)
                    # This handles legacy users created before multi-tenancy
                    g.organization_id = 1
                    logger.debug(f"User {current_user.id} has no org, using default (1)")
                    
            except Exception as e:
                logger.warning(f"Error setting tenant context: {e}")
                g.organization_id = 1  # Fallback to default
    
    def _log_tenant_context(self, response):
        """Log tenant context after request (for debugging)"""
        if current_app.debug and g.get('organization_id'):
            logger.debug(f"Request completed for org {g.organization_id}")
        return response


def get_current_organization_id():
    """
    Get the current organization ID from the request context.
    Returns None if not in a request context or no organization is set.
    """
    return getattr(g, 'organization_id', None)


def get_current_organization():
    """
    Get the current organization object from the request context.
    Lazy loads the organization if not already loaded.
    """
    if not hasattr(g, 'organization') or g.organization is None:
        org_id = get_current_organization_id()
        if org_id:
            from app.models.organization import Organization
            g.organization = Organization.query.get(org_id)
    return getattr(g, 'organization', None)


def is_super_admin():
    """Check if current user is a super admin (can access all organizations)"""
    return getattr(g, 'is_super_admin', False)


def require_organization(f):
    """
    Decorator to require organization context for a view.
    Returns 403 if no organization context is set.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not get_current_organization_id():
            from flask import jsonify
            return jsonify({
                'error': 'Organization context required',
                'message': 'This endpoint requires an organization context'
            }), 403
        return f(*args, **kwargs)
    return decorated_function


def require_same_organization(model_class, id_param='id'):
    """
    Decorator to ensure the requested resource belongs to the current organization.
    
    Usage:
        @require_same_organization(Transaction, 'transaction_id')
        def get_transaction(transaction_id):
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            org_id = get_current_organization_id()
            if not org_id:
                from flask import jsonify
                return jsonify({'error': 'Organization context required'}), 403
            
            # Get the resource ID from kwargs
            resource_id = kwargs.get(id_param)
            if resource_id:
                # Check if resource belongs to current organization
                resource = model_class.query.get(resource_id)
                if resource:
                    resource_org = getattr(resource, 'organization_id', None)
                    if resource_org and resource_org != org_id and not is_super_admin():
                        from flask import jsonify
                        return jsonify({
                            'error': 'Access denied',
                            'message': 'This resource belongs to a different organization'
                        }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def filter_by_organization(query, model_class=None):
    """
    Add organization filter to a SQLAlchemy query.
    
    Usage:
        query = Transaction.query
        query = filter_by_organization(query, Transaction)
        transactions = query.all()
    
    Or with explicit model:
        query = db.session.query(Transaction).join(...)
        query = filter_by_organization(query, Transaction)
    """
    org_id = get_current_organization_id()
    
    # If super admin and no specific org requested, return unfiltered
    if is_super_admin() and not org_id:
        return query
    
    # If no org context, use default org (1)
    if not org_id:
        org_id = 1
    
    # Apply filter
    if model_class:
        if hasattr(model_class, 'organization_id'):
            return query.filter(model_class.organization_id == org_id)
    
    return query


def set_organization_on_create(model_instance):
    """
    Set organization_id on a new model instance before saving.
    
    Usage:
        transaction = Transaction(...)
        set_organization_on_create(transaction)
        db.session.add(transaction)
    """
    org_id = get_current_organization_id()
    if org_id and hasattr(model_instance, 'organization_id'):
        model_instance.organization_id = org_id
    elif hasattr(model_instance, 'organization_id'):
        # Default to org 1 if no context
        model_instance.organization_id = 1


class TenantQuery:
    """
    Mixin for models to automatically filter by organization.
    
    Usage in model:
        class Transaction(db.Model, TenantQuery):
            ...
        
        # Then in views:
        transactions = Transaction.query_for_tenant().all()
    """
    
    @classmethod
    def query_for_tenant(cls):
        """Get query filtered by current organization"""
        from app import db
        query = db.session.query(cls)
        return filter_by_organization(query, cls)
    
    @classmethod
    def get_for_tenant(cls, id):
        """Get a single record by ID, ensuring it belongs to current organization"""
        org_id = get_current_organization_id()
        query = cls.query.filter_by(id=id)
        
        if hasattr(cls, 'organization_id') and org_id and not is_super_admin():
            query = query.filter_by(organization_id=org_id)
        
        return query.first()


# Convenience function for API endpoints
def tenant_filter(model_class):
    """
    Get a filter dict for the current organization.
    
    Usage:
        transactions = Transaction.query.filter_by(**tenant_filter(Transaction)).all()
    """
    org_id = get_current_organization_id()
    
    if hasattr(model_class, 'organization_id') and org_id:
        return {'organization_id': org_id}
    
    return {}


# Initialize singleton
tenant_middleware = TenantMiddleware()

