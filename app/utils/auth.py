"""
Authentication utilities for the API

NOTE: This application uses Flask-Login session-based authentication.
JWT tokens are not used. Flask-Login manages sessions via cookies.

For API authentication, use Flask-Login's @login_required decorator
and access the current user via current_user from flask_login.
"""
from typing import Optional
from flask import request, session
from flask_login import current_user
from app.utils.unified_logger import get_logger

logger = get_logger(__name__)


def get_current_user_id() -> Optional[int]:
    """
    Get current user ID from Flask-Login session
    
    Returns:
        User ID if authenticated, None otherwise
    
    NOTE: This uses Flask-Login's current_user, not JWT tokens.
    The application uses session-based authentication via cookies.
    """
    try:
        if current_user.is_authenticated:
            return current_user.id
        return None
    except Exception as e:
        logger.debug(f"Error getting current user ID: {e}")
        return None


def get_session_token() -> Optional[str]:
    """
    Get session token from Flask session
    
    Returns:
        Session token string if present, None otherwise
    """
    return session.get('session_token')


def is_authenticated() -> bool:
    """
    Check if current request is authenticated
    
    Returns:
        True if user is authenticated, False otherwise
    """
    try:
        return current_user.is_authenticated
    except:
        return False 