"""
Admin management routes for managing admin permissions and hierarchy
"""
from flask import Blueprint, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone
import json
import logging

from app import db
from app.models.user import User
from app.utils.permission_decorators import (
    require_main_admin, require_secondary_admin_or_higher, require_any_admin,
    can_manage_user, get_manageable_admin_levels, get_available_permissions
)
from app.utils.unified_error_handler import handle_errors, handle_api_errors
from app.utils.unified_logger import get_logger, log_function_call as performance_log

# Configure logging
logger = get_logger(__name__)

# Create blueprint
admin_management_bp = Blueprint('admin_management', __name__)

@admin_management_bp.route('/admin/management')
@login_required
@require_any_admin
@handle_errors
@performance_log
def admin_management():
    """Admin management dashboard"""
    try:
        # Get all visible admins (exclude hard admins - level 0)
        admins = User.query.filter(User.admin_level > 0).order_by(User.admin_level, User.username).all()
        
        # Get manageable admin levels for current user
        manageable_levels = get_manageable_admin_levels(current_user.admin_level)
        
        # Get available permissions
        available_permissions = get_available_permissions()
        
        from app.utils.frontend_helper import serve_frontend
        return serve_frontend('/admin/management')
    except Exception as e:
        logger.error(f"Error in admin management view: {str(e)}")
        flash('Error loading admin management page.', 'error')
        return redirect(url_for('settings.settings'))

@admin_management_bp.route('/admin/create', methods=['GET', 'POST'])
@login_required
@require_secondary_admin_or_higher
@handle_errors
@performance_log
def create_admin():
    """Create new admin"""
    if request.method == 'GET':
        # Return available data for the modal
        manageable_levels = get_manageable_admin_levels(current_user.admin_level)
        available_permissions = get_available_permissions()
        
        return jsonify({
            'success': True, 
            'manageable_levels': manageable_levels,
            'available_permissions': available_permissions
        })
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'password', 'email', 'admin_level']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate admin level
        admin_level = int(data['admin_level'])
        manageable_levels = get_manageable_admin_levels(current_user.admin_level)
        if admin_level not in manageable_levels:
            return jsonify({'error': 'You cannot create an admin of this level'}), 403
        
        # Check if username already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        # Check if email already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create new admin
        new_admin = User(
            username=data['username'],
            password=generate_password_hash(data['password']),
            email=data['email'],
            role='admin',
            admin_level=admin_level,
            created_by=current_user.id,
            is_active=True
        )
        
        # Set permissions for sub-admin
        if admin_level == 3:
            permissions = data.get('permissions', {})
            new_admin.admin_permissions = json.dumps(permissions)
        
        db.session.add(new_admin)
        db.session.commit()
        
        # Log admin creation
        from app.services.audit_service import audit_service
        audit_service.log_admin_creation(new_admin)
        
        logger.info(f"Admin {new_admin.username} created by {current_user.username}")
        return jsonify({'success': True, 'message': 'Admin created successfully'})
        
    except Exception as e:
        logger.error(f"Error creating admin: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Error creating admin'}), 500

@admin_management_bp.route('/admin/<int:admin_id>/edit', methods=['GET', 'POST'])
@login_required
@require_any_admin
@handle_errors
@performance_log
def edit_admin(admin_id):
    """Edit admin"""
    admin = User.query.get_or_404(admin_id)
    
    # Check if current user can manage this admin
    if not can_manage_user(admin):
        flash('You cannot manage this admin.', 'error')
        return redirect(url_for('admin_management.admin_management'))
    
    if request.method == 'GET':
        # Return admin data as JSON for the modal
        admin_data = {
            'id': admin.id,
            'username': admin.username,
            'email': admin.email,
            'admin_level': admin.admin_level,
            'is_active': admin.is_active,
            'permissions': admin.get_permissions()
        }
        
        return jsonify({'success': True, 'admin': admin_data})
    
    try:
        data = request.get_json()
        
        # Capture old values for audit logging
        old_values = {
            'username': admin.username,
            'email': admin.email,
            'admin_level': admin.admin_level,
            'is_active': admin.is_active,
            'permissions': admin.get_permissions()
        }
        old_level = admin.admin_level
        old_permissions = admin.get_permissions()
        
        # Update username if provided and different
        if data.get('username') and data['username'] != admin.username:
            # Check if username already exists
            if User.query.filter_by(username=data['username']).filter(User.id != admin_id).first():
                return jsonify({'error': 'Username already exists'}), 400
            admin.username = data['username']
        
        # Update email if provided and different
        if data.get('email') and data['email'] != admin.email:
            if User.query.filter_by(email=data['email']).filter(User.id != admin_id).first():
                return jsonify({'error': 'Email already exists'}), 400
            admin.email = data['email']
        
        # Update admin level (only if current user can manage this level)
        if data.get('admin_level'):
            new_level = int(data['admin_level'])
            manageable_levels = get_manageable_admin_levels(current_user.admin_level)
            if new_level not in manageable_levels:
                return jsonify({'error': 'You cannot set this admin level'}), 403
            if new_level != old_level:
                # Admin level changed - will be logged separately
                admin.admin_level = new_level
        
        # Update permissions for sub-admin
        new_permissions = old_permissions
        if admin.admin_level == 3:
            new_permissions = data.get('permissions', {})
            admin.admin_permissions = json.dumps(new_permissions)
        
        # Update password if provided
        if data.get('password'):
            admin.password = generate_password_hash(data['password'])
            admin.password_changed_at = datetime.now(timezone.utc)
            # Log password change separately
            from app.services.audit_service import audit_service
            audit_service.log_admin_action(
                action=audit_service.ACTION_USER_PASSWORD_CHANGE,
                table_name='user',
                record_id=admin.id,
                additional_info={'changed_by_admin': current_user.username}
            )
        
        db.session.commit()
        
        # Log admin changes
        from app.services.audit_service import audit_service
        # Log admin level change separately if it changed
        if data.get('admin_level') and int(data['admin_level']) != old_level:
            audit_service.log_admin_level_change(admin, old_level, admin.admin_level)
        
        # Log permission change separately if permissions changed
        if admin.admin_level == 3 and new_permissions != old_permissions:
            audit_service.log_permission_change(admin, old_permissions, new_permissions)
        
        # Log general admin update
        audit_service.log_admin_update(admin, old_values)
        
        logger.info(f"Admin {admin.username} updated by {current_user.username}")
        return jsonify({'success': True, 'message': 'Admin updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating admin: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Error updating admin'}), 500

@admin_management_bp.route('/admin/<int:admin_id>/delete', methods=['POST'])
@login_required
@require_any_admin
@handle_errors
@performance_log
def delete_admin(admin_id):
    """Delete admin"""
    try:
        admin = User.query.get_or_404(admin_id)
        
        # Check if current user can manage this admin
        if not can_manage_user(admin):
            return jsonify({'error': 'You cannot manage this admin'}), 403
        
        # Prevent self-deletion
        if admin.id == current_user.id:
            return jsonify({'error': 'You cannot delete your own account'}), 400
        
        # Prevent deletion of main admin by secondary admin
        if current_user.admin_level == 2 and admin.admin_level == 1:
            return jsonify({'error': 'Secondary admin cannot delete main admin'}), 403
        
        # Check for related records that would prevent deletion
        from app.models.audit import AuditLog, UserSession
        from app.models.transaction import Transaction
        from app.models.financial import Reconciliation
        from app.models.config import UserSettings
        
        # Check if admin has created other admins
        created_admins = User.query.filter_by(created_by=admin.id).count()
        if created_admins > 0:
            return jsonify({'error': f'Cannot delete admin. This admin has created {created_admins} other admin(s). Please reassign or delete them first.'}), 400
        
        # Check if admin has created transactions
        transaction_count = Transaction.query.filter_by(created_by=admin.id).count()
        if transaction_count > 0:
            return jsonify({'error': f'Cannot delete admin. This admin has created {transaction_count} transaction(s). Please reassign or delete them first.'}), 400
        
        # Log admin deletion before deletion
        from app.services.audit_service import audit_service
        audit_service.log_admin_deletion(admin)
        
        # Check if admin has audit logs
        audit_count = AuditLog.query.filter_by(user_id=admin.id).count()
        if audit_count > 0:
            return jsonify({'error': f'Cannot delete admin. This admin has {audit_count} audit log(s). Please contact system administrator.'}), 400
        
        # Check if admin has reconciliations
        reconciliation_count = Reconciliation.query.filter_by(created_by=admin.id).count()
        if reconciliation_count > 0:
            return jsonify({'error': f'Cannot delete admin. This admin has created {reconciliation_count} reconciliation(s). Please reassign or delete them first.'}), 400
        
        username = admin.username
        
        # Use the safe_delete method to properly handle all related records
        admin.safe_delete()
        
        # Commit all changes
        db.session.commit()
        
        logger.info(f"Admin {username} deleted by {current_user.username}")
        return jsonify({'success': True, 'message': 'Admin deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting admin: {str(e)}")
        db.session.rollback()
        
        # Provide more specific error messages
        if "FOREIGN KEY constraint failed" in str(e):
            return jsonify({'error': 'Cannot delete admin due to existing related records. Please contact system administrator.'}), 400
        elif "UNIQUE constraint failed" in str(e):
            return jsonify({'error': 'Cannot delete admin due to database constraints. Please contact system administrator.'}), 400
        elif "NOT NULL constraint failed" in str(e):
            return jsonify({'error': 'Cannot delete admin due to database constraint issues. Please contact system administrator.'}), 400
        else:
            return jsonify({'error': 'Error deleting admin. Please try again or contact system administrator.'}), 500

@admin_management_bp.route('/admin/<int:admin_id>/toggle_status', methods=['POST'])
@login_required
@require_any_admin
@handle_errors
@performance_log
def toggle_admin_status(admin_id):
    """Toggle admin active status"""
    try:
        admin = User.query.get_or_404(admin_id)
        
        # Check if current user can manage this admin
        if not can_manage_user(admin):
            return jsonify({'error': 'You cannot manage this admin'}), 403
        
        # Prevent self-deactivation
        if admin.id == current_user.id:
            return jsonify({'error': 'You cannot deactivate your own account'}), 400
        
        old_status = admin.is_active
        admin.is_active = not admin.is_active
        db.session.commit()
        
        # Log admin status change
        from app.services.audit_service import audit_service
        audit_service.log_admin_status_change(admin, admin.is_active)
        
        status = 'activated' if admin.is_active else 'deactivated'
        logger.info(f"Admin {admin.username} {status} by {current_user.username}")
        
        return jsonify({
            'success': True, 
            'message': f'Admin {status} successfully',
            'is_active': admin.is_active
        })
        
    except Exception as e:
        logger.error(f"Error toggling admin status: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Error updating admin status'}), 500

@admin_management_bp.route('/admin/permissions')
@login_required
@require_any_admin
@handle_errors
def get_permissions():
    """Get available permissions"""
    try:
        available_permissions = get_available_permissions()
        return jsonify({'permissions': available_permissions})
    except Exception as e:
        logger.error(f"Error getting permissions: {str(e)}")
        return jsonify({'error': 'Error getting permissions'}), 500 