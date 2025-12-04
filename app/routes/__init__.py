"""
Routes package for PipLinePro Treasury Management System
"""

from .auth import auth_bp
from .transactions import transactions_bp
from .analytics import analytics_bp
from .settings import settings_bp
from .api import api_bp

__all__ = [
    'auth_bp',
    'transactions_bp', 
    'analytics_bp',
    'settings_bp',
    'api_bp'
] 