"""
Tenant Helper Functions
Utilities for multi-tenancy support in API endpoints
"""
from flask import g
from app.middleware.tenant_middleware import (
    get_current_organization_id,
    set_organization_on_create,
    filter_by_organization,
    is_super_admin
)


def add_tenant_filter(query, model_class):
    """
    Add organization filter to a query if model supports multi-tenancy.
    
    Usage:
        query = Transaction.query
        query = add_tenant_filter(query, Transaction)
        transactions = query.all()
    """
    return filter_by_organization(query, model_class)


def set_tenant_on_new_record(model_instance):
    """
    Set organization_id on a new model instance.
    
    Usage:
        transaction = Transaction(...)
        set_tenant_on_new_record(transaction)
        db.session.add(transaction)
    """
    set_organization_on_create(model_instance)


def get_tenant_id():
    """Get current tenant/organization ID"""
    return get_current_organization_id()


def is_cross_tenant_allowed():
    """Check if current user can access data across tenants"""
    return is_super_admin()


def validate_tenant_access(resource, resource_name="resource"):
    """
    Validate that a resource belongs to the current organization.
    Returns (is_valid, error_response_tuple or None)
    
    Usage:
        transaction = Transaction.query.get(transaction_id)
        is_valid, error = validate_tenant_access(transaction, "transaction")
        if not is_valid:
            return error
    """
    if not resource:
        from flask import jsonify
        return False, (jsonify({'error': f'{resource_name.capitalize()} not found'}), 404)
    
    # Skip validation for super admins
    if is_cross_tenant_allowed():
        return True, None
    
    # Check if resource has organization_id
    if not hasattr(resource, 'organization_id'):
        # Resource doesn't support multi-tenancy, allow access
        return True, None
    
    current_org_id = get_tenant_id()
    resource_org_id = getattr(resource, 'organization_id', None)
    
    if resource_org_id and resource_org_id != current_org_id:
        from flask import jsonify
        return False, (jsonify({
            'error': 'Access denied',
            'message': f'This {resource_name} belongs to a different organization'
        }), 403)
    
    return True, None


def get_tenant_context_info():
    """
    Get current tenant context information for logging/debugging.
    
    Returns:
        dict: {
            'organization_id': int or None,
            'is_super_admin': bool,
            'has_tenant_context': bool
        }
    """
    org_id = get_tenant_id()
    return {
        'organization_id': org_id,
        'is_super_admin': is_cross_tenant_allowed(),
        'has_tenant_context': org_id is not None
    }

