"""
Organization API Endpoints
Manage organizations (tenants) for multi-tenancy support
"""
from flask import Blueprint, request, jsonify, g
from flask_login import login_required, current_user
from app import db, limiter
from app.models.organization import Organization
from app.models.user import User
from app.utils.unified_error_handler import handle_errors, ValidationError
from app.middleware.tenant_middleware import (
    get_current_organization_id, 
    get_current_organization,
    is_super_admin
)
import logging

logger = logging.getLogger(__name__)

organizations_api = Blueprint('organizations_api', __name__, url_prefix='/api/v1/organizations')


@organizations_api.route('', methods=['GET'])
@login_required
@limiter.limit("30 per minute")
@handle_errors
def list_organizations():
    """
    List organizations.
    - Super admins: see all organizations
    - Regular users: see only their organization
    """
    try:
        if is_super_admin():
            # Super admin can see all organizations
            organizations = Organization.query.filter_by(is_active=True).all()
        else:
            # Regular users can only see their organization
            org_id = get_current_organization_id()
            if org_id:
                organizations = Organization.query.filter_by(id=org_id, is_active=True).all()
            else:
                organizations = []
        
        return jsonify({
            'success': True,
            'organizations': [org.to_dict() for org in organizations],
            'count': len(organizations)
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing organizations: {e}")
        return jsonify({'error': 'Failed to list organizations'}), 500


@organizations_api.route('/<int:org_id>', methods=['GET'])
@login_required
@limiter.limit("60 per minute")
@handle_errors
def get_organization(org_id):
    """Get a specific organization"""
    try:
        # Check access
        current_org_id = get_current_organization_id()
        if not is_super_admin() and current_org_id != org_id:
            return jsonify({'error': 'Access denied'}), 403
        
        organization = Organization.query.get(org_id)
        if not organization:
            return jsonify({'error': 'Organization not found'}), 404
        
        # Get additional stats
        user_count = User.query.filter_by(organization_id=org_id, is_active=True).count()
        
        org_dict = organization.to_dict()
        org_dict['user_count'] = user_count
        
        return jsonify({
            'success': True,
            'organization': org_dict
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting organization {org_id}: {e}")
        return jsonify({'error': 'Failed to get organization'}), 500


@organizations_api.route('', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
@handle_errors
def create_organization():
    """
    Create a new organization.
    Only super admins can create organizations.
    """
    try:
        if not is_super_admin():
            return jsonify({'error': 'Only super admins can create organizations'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        name = data.get('name', '').strip()
        slug = data.get('slug', '').strip().lower()
        
        if not name:
            return jsonify({'error': 'Organization name is required'}), 400
        if not slug:
            # Generate slug from name
            import re
            slug = re.sub(r'[^a-z0-9-]', '-', name.lower())
            slug = re.sub(r'-+', '-', slug).strip('-')
        
        # Check if slug is unique
        existing = Organization.query.filter_by(slug=slug).first()
        if existing:
            return jsonify({'error': f'Organization with slug "{slug}" already exists'}), 400
        
        # Create organization
        organization = Organization(
            name=name,
            slug=slug,
            subscription_tier=data.get('subscription_tier', 'free'),
            max_users=data.get('max_users', 5),
            max_transactions_per_month=data.get('max_transactions_per_month', 1000),
            max_psp_connections=data.get('max_psp_connections', 3),
            contact_email=data.get('contact_email'),
            contact_phone=data.get('contact_phone'),
            country=data.get('country'),
            timezone=data.get('timezone', 'UTC'),
            is_active=data.get('is_active', True),  # Explicitly set is_active
        )
        
        db.session.add(organization)
        db.session.commit()
        
        logger.info(f"Organization created: {organization.name} (ID: {organization.id})")
        
        return jsonify({
            'success': True,
            'message': 'Organization created successfully',
            'organization': organization.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating organization: {e}")
        return jsonify({'error': 'Failed to create organization'}), 500


@organizations_api.route('/<int:org_id>', methods=['PUT'])
@login_required
@limiter.limit("20 per minute")
@handle_errors
def update_organization(org_id):
    """
    Update an organization.
    - Super admins: can update any organization
    - Org admins: can update their own organization (limited fields)
    """
    try:
        current_org_id = get_current_organization_id()
        
        # Check access
        if not is_super_admin() and current_org_id != org_id:
            return jsonify({'error': 'Access denied'}), 403
        
        organization = Organization.query.get(org_id)
        if not organization:
            return jsonify({'error': 'Organization not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Fields that only super admins can update
        super_admin_fields = [
            'subscription_tier', 'subscription_status', 'subscription_expires_at',
            'max_users', 'max_transactions_per_month', 'max_psp_connections',
            'is_active'
        ]
        
        # Fields that org admins can update
        org_admin_fields = [
            'name', 'logo_url', 'primary_color', 'contact_email', 
            'contact_phone', 'address', 'country', 'timezone', 'settings'
        ]
        
        allowed_fields = org_admin_fields
        if is_super_admin():
            allowed_fields = allowed_fields + super_admin_fields
        
        # Update allowed fields
        for field in allowed_fields:
            if field in data:
                setattr(organization, field, data[field])
        
        db.session.commit()
        
        logger.info(f"Organization updated: {organization.name} (ID: {organization.id})")
        
        return jsonify({
            'success': True,
            'message': 'Organization updated successfully',
            'organization': organization.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating organization {org_id}: {e}")
        return jsonify({'error': 'Failed to update organization'}), 500


@organizations_api.route('/<int:org_id>', methods=['DELETE'])
@login_required
@limiter.limit("5 per minute")
@handle_errors
def delete_organization(org_id):
    """
    Delete (deactivate) an organization.
    Only super admins can delete organizations.
    Note: This soft-deletes by setting is_active=False
    """
    try:
        if not is_super_admin():
            return jsonify({'error': 'Only super admins can delete organizations'}), 403
        
        # Prevent deleting the default organization
        if org_id == 1:
            return jsonify({'error': 'Cannot delete the default organization'}), 400
        
        organization = Organization.query.get(org_id)
        if not organization:
            return jsonify({'error': 'Organization not found'}), 404
        
        # Soft delete
        organization.is_active = False
        organization.subscription_status = 'cancelled'
        db.session.commit()
        
        logger.info(f"Organization deactivated: {organization.name} (ID: {organization.id})")
        
        return jsonify({
            'success': True,
            'message': 'Organization deactivated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting organization {org_id}: {e}")
        return jsonify({'error': 'Failed to delete organization'}), 500


@organizations_api.route('/current', methods=['GET'])
@login_required
@limiter.limit("60 per minute")
@handle_errors
def get_current_org():
    """Get the current user's organization"""
    try:
        organization = get_current_organization()
        if not organization:
            return jsonify({'error': 'No organization context'}), 404
        
        # Get usage stats
        from app.models.transaction import Transaction
        from app.models.financial import Expense
        from datetime import datetime
        
        current_month = datetime.now().strftime('%Y-%m')
        
        user_count = User.query.filter_by(
            organization_id=organization.id, 
            is_active=True
        ).count()
        
        # This month's transaction count
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        tx_count = Transaction.query.filter(
            Transaction.organization_id == organization.id,
            Transaction.created_at >= month_start
        ).count()
        
        org_dict = organization.to_dict()
        org_dict['usage'] = {
            'users': user_count,
            'users_limit': organization.max_users,
            'transactions_this_month': tx_count,
            'transactions_limit': organization.max_transactions_per_month,
        }
        
        return jsonify({
            'success': True,
            'organization': org_dict
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting current organization: {e}")
        return jsonify({'error': 'Failed to get organization'}), 500


@organizations_api.route('/<int:org_id>/users', methods=['GET'])
@login_required
@limiter.limit("30 per minute")
@handle_errors
def get_organization_users(org_id):
    """Get users in an organization"""
    try:
        current_org_id = get_current_organization_id()
        
        # Check access
        if not is_super_admin() and current_org_id != org_id:
            return jsonify({'error': 'Access denied'}), 403
        
        users = User.query.filter_by(organization_id=org_id, is_active=True).all()
        
        return jsonify({
            'success': True,
            'users': [user.to_dict() for user in users],
            'count': len(users)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting organization users: {e}")
        return jsonify({'error': 'Failed to get users'}), 500


@organizations_api.route('/<int:org_id>/stats', methods=['GET'])
@login_required
@limiter.limit("20 per minute")
@handle_errors
def get_organization_stats(org_id):
    """Get statistics for an organization"""
    try:
        current_org_id = get_current_organization_id()
        
        # Check access
        if not is_super_admin() and current_org_id != org_id:
            return jsonify({'error': 'Access denied'}), 403
        
        organization = Organization.query.get(org_id)
        if not organization:
            return jsonify({'error': 'Organization not found'}), 404
        
        from app.models.transaction import Transaction
        from app.models.financial import Expense
        from app.models.trust_wallet import TrustWallet
        from datetime import datetime
        from sqlalchemy import func
        
        # Get counts
        user_count = User.query.filter_by(organization_id=org_id, is_active=True).count()
        transaction_count = Transaction.query.filter_by(organization_id=org_id).count()
        expense_count = Expense.query.filter_by(organization_id=org_id).count()
        wallet_count = TrustWallet.query.filter_by(organization_id=org_id, is_active=True).count()
        
        # Get this month's stats
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        monthly_tx_count = Transaction.query.filter(
            Transaction.organization_id == org_id,
            Transaction.created_at >= month_start
        ).count()
        
        monthly_tx_volume = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.organization_id == org_id,
            Transaction.created_at >= month_start
        ).scalar() or 0
        
        return jsonify({
            'success': True,
            'stats': {
                'users': user_count,
                'transactions': transaction_count,
                'expenses': expense_count,
                'wallets': wallet_count,
                'monthly_transactions': monthly_tx_count,
                'monthly_volume': float(monthly_tx_volume),
                'limits': {
                    'max_users': organization.max_users,
                    'max_transactions_per_month': organization.max_transactions_per_month,
                    'max_psp_connections': organization.max_psp_connections
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting organization stats: {e}")
        return jsonify({'error': 'Failed to get stats'}), 500

