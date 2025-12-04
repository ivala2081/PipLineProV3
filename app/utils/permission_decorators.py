"""
Permission decorators for role-based access control
"""
from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user
from app.utils.unified_error_handler import AuthorizationError

def require_admin_level(required_level):
    """Decorator to require specific admin level"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            if not current_user.is_any_admin():
                flash('Access denied. Admin privileges required.', 'error')
                abort(403)
            
            if current_user.admin_level > required_level:
                flash('Access denied. Higher admin level required.', 'error')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_permission(permission):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            if not current_user.has_permission(permission):
                flash(f'Access denied. Permission "{permission}" required.', 'error')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_section_access(section_name):
    """Decorator to require access to specific section"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            # Check section access using admin permission service
            try:
                from app.services.admin_permission_service import admin_permission_service
                can_access = admin_permission_service.can_access_section(
                    current_user.admin_level, 
                    section_name
                )
                
                if not can_access:
                    flash(f'Access denied. You do not have permission to access "{section_name}".', 'error')
                    abort(403)
                
            except Exception as e:
                # If permission service fails, fall back to admin level check
                if not current_user.is_any_admin():
                    flash('Access denied. Administrator privileges required.', 'error')
                    abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_hard_admin(f):
    """Decorator to require hard admin (level 0)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        if not current_user.is_hard_admin():
            flash('Access denied. Hard administrator privileges required.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def require_main_admin(f):
    """Decorator to require main admin (level 1)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        if not current_user.is_main_admin():
            flash('Access denied. Main administrator privileges required.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def require_secondary_admin_or_higher(f):
    """Decorator to require secondary admin (level 2) or higher"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        if current_user.admin_level not in [0, 1, 2]:
            flash('Access denied. Secondary administrator or higher privileges required.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def require_any_admin(f):
    """Decorator to require any admin level"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        if not current_user.is_any_admin():
            flash('Access denied. Administrator privileges required.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def can_manage_user(target_user):
    """Check if current user can manage target user"""
    if not current_user.is_authenticated:
        return False
    
    # Hard admin can manage everyone
    if current_user.is_hard_admin():
        return True
    
    # Main admin can manage everyone except hard admin
    if current_user.is_main_admin():
        return target_user.admin_level > 0
    
    # Secondary admin can manage sub-admins and regular users
    if current_user.is_secondary_admin():
        return target_user.admin_level in [0, 3]
    
    # Sub admin can only manage regular users
    if current_user.is_sub_admin():
        return target_user.admin_level == 0
    
    return False

def get_manageable_admin_levels(current_admin_level):
    """Get admin levels that current admin can manage"""
    if current_admin_level == 0:  # Hard admin
        return [1, 2, 3]  # Can manage all visible admins
    elif current_admin_level == 1:  # Main admin
        return [2, 3]  # Can manage secondary and sub admins
    elif current_admin_level == 2:  # Secondary admin
        return [3]  # Can only manage sub admins
    else:
        return []  # Sub admin can't manage other admins

def get_available_permissions():
    """Get all available permissions for admin management"""
    return {
        'user_management': 'Manage users and their accounts',
        'transaction_management': 'Manage transactions and financial data',
        'system_settings': 'Access and modify system settings',
        'backup_restore': 'Perform backup and restore operations',
        'audit_logs': 'View audit logs and security events',
        'reports_analytics': 'Generate reports and view analytics',
        'dropdown_management': 'Manage form dropdown options',
        'exchange_rates': 'Manage exchange rates',
        'admin_management': 'Manage other administrators',
        'system_config': 'Advanced system configuration',
        'database_management': 'Database operations and maintenance'
    } 