"""
Enhanced Users API endpoints for PipLinePro v2
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import logging

logger = logging.getLogger(__name__)

users_api = Blueprint('users_api', __name__)

# Temporarily disable CSRF protection for users API
from app import csrf
csrf.exempt(users_api)

@users_api.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """Get current user profile"""
    try:
        return jsonify({
            'status': 'success',
            'data': {
                'id': current_user.id,
                'username': current_user.username,
                'email': current_user.email,
                'role': current_user.role,
                'admin_level': current_user.admin_level,
                'created_at': current_user.created_at.isoformat(),
                'last_login': current_user.last_login.isoformat() if current_user.last_login else None
            }
        })
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return jsonify({'error': 'Failed to get profile'}), 500

@users_api.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """Update current user profile"""
    try:
        data = request.get_json()
        
        # Update allowed fields
        if 'email' in data:
            current_user.email = data['email']
        
        from app import db
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Profile updated successfully'
        })
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        return jsonify({'error': 'Failed to update profile'}), 500

@users_api.route('/settings', methods=['GET'])
@login_required
def get_settings():
    """Get user settings"""
    try:
        from app.models.config import UserSettings
        
        settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        
        if settings:
            settings_data = settings.to_dict()
        else:
            settings_data = {
                'language': 'en',
                'timezone': 'UTC',
                'date_format': 'YYYY-MM-DD',
                'currency': 'TL',
                'notifications': True
            }
        
        return jsonify({
            'status': 'success',
            'data': settings_data
        })
    except Exception as e:
        logger.error(f"Error getting user settings: {e}")
        return jsonify({'error': 'Failed to get settings'}), 500

@users_api.route('/settings', methods=['PUT'])
@login_required
def update_settings():
    """Update user settings"""
    try:
        data = request.get_json()
        
        from app.models.config import UserSettings
        from app import db
        
        settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        
        if not settings:
            settings = UserSettings(user_id=current_user.id)
            db.session.add(settings)
        
        # Update settings
        for key, value in data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Settings updated successfully'
        })
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        return jsonify({'error': 'Failed to update settings'}), 500
