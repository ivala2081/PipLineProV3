"""
Admin Section Permissions Routes for PipLine Treasury System
Allows main admin to configure which sections are accessible to different admin levels
"""
from flask import Blueprint, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
import json
import logging

from app import db
from app.models.config import AdminSectionPermission
from app.services.admin_permission_service import admin_permission_service
from app.utils.permission_decorators import require_main_admin
from app.utils.unified_error_handler import handle_errors, handle_api_errors
from app.utils.unified_logger import get_logger, log_function_call as performance_log

# Configure logging
logger = get_logger(__name__)

# Create blueprint
admin_permissions_bp = Blueprint('admin_permissions', __name__)

@admin_permissions_bp.route('/admin/permissions/sections')
@login_required
@require_main_admin
@handle_errors
@performance_log
def admin_section_permissions():
    """Admin section permissions management page"""
    try:
        # Get all section permissions
        sections = admin_permission_service.get_all_sections()
        
        return redirect('http://localhost:3000/admin/permissions')
        
    except Exception as e:
        logger.error(f"Error in admin section permissions view: {str(e)}")
        flash('Error loading section permissions page.', 'error')
        return redirect(url_for('admin_management.admin_management'))

@admin_permissions_bp.route('/admin/permissions/sections/initialize', methods=['POST'])
@login_required
@require_main_admin
@handle_errors
@performance_log
def initialize_section_permissions():
    """Initialize default section permissions"""
    try:
        success = admin_permission_service.initialize_default_sections()
        
        if success:
            flash('Default section permissions initialized successfully.', 'success')
        else:
            flash('Error initializing section permissions.', 'error')
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error initializing section permissions: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_permissions_bp.route('/admin/permissions/sections/update', methods=['POST'])
@login_required
@require_main_admin
@handle_errors
@performance_log
def update_section_permissions():
    """Update section permissions"""
    try:
        data = request.get_json()
        
        if not data or 'sections' not in data:
            return jsonify({'success': False, 'error': 'Invalid data provided'}), 400
        
        sections_data = data['sections']
        success = admin_permission_service.update_multiple_sections(sections_data)
        
        if success:
            flash('Section permissions updated successfully.', 'success')
        else:
            flash('Error updating section permissions.', 'error')
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error updating section permissions: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_permissions_bp.route('/admin/permissions/sections/<int:section_id>', methods=['PUT'])
@login_required
@require_main_admin
@handle_errors
@performance_log
def update_single_section_permission(section_id):
    """Update single section permission"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'Invalid data provided'}), 400
        
        success = admin_permission_service.update_section_permissions(section_id, data)
        
        if success:
            flash('Section permission updated successfully.', 'success')
        else:
            flash('Error updating section permission.', 'error')
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error updating single section permission: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_permissions_bp.route('/admin/permissions/sections/create', methods=['POST'])
@login_required
@require_main_admin
@handle_errors
@performance_log
def create_custom_section():
    """Create a custom section permission"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['section_name', 'section_display_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        # Check if section already exists
        existing = AdminSectionPermission.query.filter_by(
            section_name=data['section_name']
        ).first()
        
        if existing:
            return jsonify({'success': False, 'error': 'Section with this name already exists'}), 400
        
        # Set default permissions
        section_data = {
            'section_name': data['section_name'],
            'section_display_name': data['section_display_name'],
            'section_description': data.get('section_description', ''),
            'main_admin_access': data.get('main_admin_access', True),
            'secondary_admin_access': data.get('secondary_admin_access', False),
            'sub_admin_access': data.get('sub_admin_access', False)
        }
        
        success = admin_permission_service.create_custom_section(section_data)
        
        if success:
            flash('Custom section created successfully.', 'success')
        else:
            flash('Error creating custom section.', 'error')
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error creating custom section: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_permissions_bp.route('/admin/permissions/sections/<int:section_id>', methods=['DELETE'])
@login_required
@require_main_admin
@handle_errors
@performance_log
def delete_section_permission(section_id):
    """Delete a section permission"""
    try:
        success = admin_permission_service.delete_section(section_id)
        
        if success:
            flash('Section permission deleted successfully.', 'success')
        else:
            flash('Error deleting section permission.', 'error')
        
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Error deleting section permission: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_permissions_bp.route('/admin/permissions/sections/check/<section_name>')
@login_required
@handle_errors
@performance_log
def check_section_access(section_name):
    """Check if current user can access a specific section"""
    try:
        if not current_user.is_any_admin():
            return jsonify({'can_access': False, 'reason': 'Not an administrator'})
        
        can_access = admin_permission_service.can_access_section(
            current_user.admin_level, 
            section_name
        )
        
        return jsonify({
            'can_access': can_access,
            'admin_level': current_user.admin_level,
            'section_name': section_name
        })
        
    except Exception as e:
        logger.error(f"Error checking section access: {str(e)}")
        return jsonify({'can_access': False, 'error': str(e)}), 500

@admin_permissions_bp.route('/admin/permissions/sections/user-sections')
@login_required
@handle_errors
@performance_log
def get_user_accessible_sections():
    """Get sections accessible to current user"""
    try:
        accessible_sections = admin_permission_service.get_accessible_sections_for_user(current_user)
        
        return jsonify({
            'success': True,
            'sections': accessible_sections,
            'admin_level': current_user.admin_level
        })
        
    except Exception as e:
        logger.error(f"Error getting user accessible sections: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_permissions_bp.route('/admin/permissions/sections/preview/<int:admin_level>')
@login_required
@require_main_admin
@handle_errors
@performance_log
def preview_admin_level_sections(admin_level):
    """Preview sections accessible to a specific admin level"""
    try:
        if admin_level not in [1, 2, 3]:
            return jsonify({'success': False, 'error': 'Invalid admin level'}), 400
        
        sections = admin_permission_service.get_sections_for_admin_level(admin_level)
        
        return jsonify({
            'success': True,
            'sections': sections,
            'admin_level': admin_level
        })
        
    except Exception as e:
        logger.error(f"Error previewing admin level sections: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500 