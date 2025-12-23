"""
User Management API Endpoints
Provides CRUD operations for User entities.
"""
from flask import Blueprint, request, jsonify, current_app, g
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash
import json

from app import db, limiter
from app.models.user import User
from app.models.organization import Organization
from app.services.audit_service import AuditService
from app.utils.unified_error_handler import handle_api_errors, ValidationError, AuthorizationError
from app.utils.unified_logger import get_logger
from functools import wraps

logger = get_logger(__name__)
users_api = Blueprint('users_api', __name__)


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.admin_level > 2:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


def can_manage_users():
    """Check if current user has permission to manage users."""
    # Super admins (level 0-1) can manage all users
    # Org admins (level 2) can manage users in their organization
    return current_user.is_authenticated and current_user.admin_level <= 2


def can_manage_user(user):
    """Check if current user can manage a specific user."""
    if not current_user.is_authenticated:
        return False
    
    # Super admins can manage anyone
    if current_user.admin_level <= 1:
        return True
    
    # Org admins can manage users in their organization
    if current_user.admin_level == 2:
        return user.organization_id == current_user.organization_id
    
    return False


@users_api.route('/', methods=['GET'])
@limiter.limit("60 per minute")
@login_required
@admin_required
@handle_api_errors
def get_users():
    """
    Get list of users.
    Super admins see all users.
    Org admins see only users in their organization.
    """
    if not can_manage_users():
        raise AuthorizationError("You do not have permission to view users.")
    
    query = User.query
    
    # Org admins can only see users in their organization
    if current_user.admin_level >= 2:
        query = query.filter_by(organization_id=current_user.organization_id)
    
    # Filters
    org_id = request.args.get('organization_id', type=int)
    if org_id and current_user.admin_level <= 1:
        query = query.filter_by(organization_id=org_id)
    
    is_active = request.args.get('is_active')
    if is_active is not None:
        is_active_bool = is_active.lower() in ['true', '1', 'yes']
        query = query.filter_by(is_active=is_active_bool)
    
    admin_level = request.args.get('admin_level', type=int)
    if admin_level is not None:
        query = query.filter_by(admin_level=admin_level)
    
    users = query.order_by(User.username).all()
    
    return jsonify({
        'success': True,
        'users': [user.to_dict() for user in users],
        'total': len(users)
    }), 200


@users_api.route('/<int:user_id>', methods=['GET'])
@limiter.limit("60 per minute")
@login_required
@admin_required
@handle_api_errors
def get_user(user_id):
    """Get details of a specific user."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if not can_manage_user(user):
        raise AuthorizationError("You do not have permission to view this user.")
    
    return jsonify({
        'success': True,
        'user': user.to_dict()
    }), 200


@users_api.route('/', methods=['POST'])
@limiter.limit("10 per minute")
@login_required
@admin_required
@handle_api_errors
def create_user():
    """Create a new user."""
    if not can_manage_users():
        raise AuthorizationError("You do not have permission to create users.")
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['username', 'password']
    for field in required_fields:
        if not data.get(field):
            raise ValidationError(f"{field} is required.")
    
    username = data.get('username').strip()
    email = data.get('email', '').strip() or None
    password = data.get('password')
    organization_id = data.get('organization_id', type=int)
    admin_level = data.get('admin_level', 3)  # Default to regular user
    is_active = data.get('is_active', True)
    
    # Validate username
    if len(username) < 3:
        raise ValidationError("Username must be at least 3 characters.")
    
    # Check if username already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        raise ValidationError(f"Username '{username}' already exists.")
    
    # Check if email already exists
    if email:
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            raise ValidationError(f"Email '{email}' already exists.")
    
    # Validate organization
    if organization_id:
        org = Organization.query.get(organization_id)
        if not org:
            raise ValidationError(f"Organization with ID {organization_id} not found.")
        
        # Org admins can only create users in their organization
        if current_user.admin_level >= 2 and organization_id != current_user.organization_id:
            raise AuthorizationError("You can only create users in your organization.")
        
        # Check organization user limit
        current_user_count = User.query.filter_by(organization_id=organization_id, is_active=True).count()
        if not org.can_add_user(current_user_count):
            raise ValidationError(f"Organization has reached maximum user limit ({org.max_users}).")
    else:
        # If no organization specified, use current user's organization (for org admins)
        if current_user.admin_level >= 2:
            organization_id = current_user.organization_id
    
    # Validate admin level
    # Org admins cannot create super admins
    if current_user.admin_level >= 2 and admin_level <= 1:
        raise AuthorizationError("You cannot create super admin users.")
    
    try:
        # Create user
        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            organization_id=organization_id,
            admin_level=admin_level,
            is_active=is_active,
            role=data.get('role', 'user')
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        AuditService.log_admin_action(
            AuditService.ACTION_CREATE,
            'User',
            new_user.id,
            new_values=new_user.to_dict()
        )
        
        logger.info(f"User created: {new_user.username} by user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'User created successfully',
            'user': new_user.to_dict()
        }), 201
        
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Integrity error creating user: {e}")
        raise ValidationError("User with this username or email already exists.")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating user: {e}", exc_info=True)
        return jsonify({'error': 'Failed to create user', 'details': str(e)}), 500


@users_api.route('/<int:user_id>', methods=['PUT'])
@limiter.limit("30 per minute")
@login_required
@admin_required
@handle_api_errors
def update_user(user_id):
    """Update an existing user."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if not can_manage_user(user):
        raise AuthorizationError("You do not have permission to update this user.")
    
    data = request.get_json()
    old_values = user.to_dict()
    
    try:
        # Update username
        if 'username' in data:
            new_username = data['username'].strip()
            if new_username != user.username:
                existing = User.query.filter_by(username=new_username).first()
                if existing:
                    raise ValidationError(f"Username '{new_username}' already exists.")
                user.username = new_username
        
        # Update email
        if 'email' in data:
            new_email = data['email'].strip() or None
            if new_email and new_email != user.email:
                existing = User.query.filter_by(email=new_email).first()
                if existing:
                    raise ValidationError(f"Email '{new_email}' already exists.")
                user.email = new_email
        
        # Update password
        if 'password' in data and data['password']:
            user.password = generate_password_hash(data['password'])
            user.password_changed_at = datetime.now(timezone.utc)
        
        # Update organization (super admins only)
        if 'organization_id' in data:
            if current_user.admin_level <= 1:
                new_org_id = data['organization_id']
                if new_org_id:
                    org = Organization.query.get(new_org_id)
                    if not org:
                        raise ValidationError(f"Organization with ID {new_org_id} not found.")
                user.organization_id = new_org_id
            else:
                raise AuthorizationError("Only super admins can change user organizations.")
        
        # Update admin level (super admins only)
        if 'admin_level' in data:
            if current_user.admin_level <= 1:
                user.admin_level = data['admin_level']
            else:
                raise AuthorizationError("Only super admins can change admin levels.")
        
        # Update role
        if 'role' in data:
            user.role = data['role']
        
        # Update is_active
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        db.session.commit()
        
        AuditService.log_admin_action(
            AuditService.ACTION_UPDATE,
            'User',
            user.id,
            old_values=old_values,
            new_values=user.to_dict()
        )
        
        logger.info(f"User updated: {user.username} by user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200
        
    except ValidationError as e:
        db.session.rollback()
        raise e
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating user: {e}", exc_info=True)
        return jsonify({'error': 'Failed to update user', 'details': str(e)}), 500


@users_api.route('/<int:user_id>', methods=['DELETE'])
@limiter.limit("10 per minute")
@login_required
@admin_required
@handle_api_errors
def delete_user(user_id):
    """Delete a user (soft delete - sets is_active=False)."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if not can_manage_user(user):
        raise AuthorizationError("You do not have permission to delete this user.")
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        raise ValidationError("You cannot delete your own account.")
    
    # Prevent org admins from deleting super admins
    if current_user.admin_level >= 2 and user.admin_level <= 1:
        raise AuthorizationError("You cannot delete super admin users.")
    
    try:
        old_values = user.to_dict()
        
        # Soft delete - just deactivate
        user.is_active = False
        db.session.commit()
        
        AuditService.log_admin_action(
            AuditService.ACTION_DELETE,
            'User',
            user.id,
            old_values=old_values
        )
        
        logger.info(f"User deleted (deactivated): {user.username} by user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'User deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting user: {e}", exc_info=True)
        return jsonify({'error': 'Failed to delete user', 'details': str(e)}), 500


@users_api.route('/<int:user_id>/activate', methods=['POST'])
@limiter.limit("10 per minute")
@login_required
@admin_required
@handle_api_errors
def activate_user(user_id):
    """Activate a deactivated user."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if not can_manage_user(user):
        raise AuthorizationError("You do not have permission to activate this user.")
    
    try:
        user.is_active = True
        user.failed_login_attempts = 0
        user.account_locked_until = None
        db.session.commit()
        
        logger.info(f"User activated: {user.username} by user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'User activated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error activating user: {e}", exc_info=True)
        return jsonify({'error': 'Failed to activate user', 'details': str(e)}), 500


@users_api.route('/stats', methods=['GET'])
@limiter.limit("30 per minute")
@login_required
@admin_required
@handle_api_errors
def get_user_stats():
    """Get user statistics."""
    if not can_manage_users():
        raise AuthorizationError("You do not have permission to view user statistics.")
    
    # Filter by organization for org admins
    query = User.query
    if current_user.admin_level >= 2:
        query = query.filter_by(organization_id=current_user.organization_id)
    
    total_users = query.count()
    active_users = query.filter_by(is_active=True).count()
    inactive_users = query.filter_by(is_active=False).count()
    
    # Count by admin level
    super_admins = query.filter(User.admin_level <= 1).count()
    org_admins = query.filter(User.admin_level == 2).count()
    regular_users = query.filter(User.admin_level > 2).count()
    
    # Count by organization (super admins only)
    by_organization = []
    if current_user.admin_level <= 1:
        orgs = Organization.query.all()
        for org in orgs:
            user_count = User.query.filter_by(organization_id=org.id).count()
            by_organization.append({
                'organization_id': org.id,
                'organization_name': org.name,
                'user_count': user_count,
                'max_users': org.max_users
            })
    
    return jsonify({
        'success': True,
        'stats': {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'super_admins': super_admins,
            'org_admins': org_admins,
            'regular_users': regular_users,
            'by_organization': by_organization
        }
    }), 200
