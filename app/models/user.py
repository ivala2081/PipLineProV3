"""
User model with authentication and security features
"""
from app import db
from flask_login import UserMixin
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import validates
import re

# Decimal/Float type mismatch prevention
from app.services.decimal_float_fix_service import decimal_float_service


class User(UserMixin, db.Model):
    """User model with enhanced security features"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'admin', 'user', 'viewer'
    admin_level = db.Column(db.Integer, default=0)  # 0=user, 1=main_admin, 2=secondary_admin, 3=sub_admin
    admin_permissions = db.Column(db.Text, nullable=True)  # JSON string of specific permissions
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Who created this admin
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)
    profile_picture = db.Column(db.String(255), nullable=True)  # Path to profile picture
    
    # Security fields
    last_login = db.Column(db.DateTime)
    failed_login_attempts = db.Column(db.Integer, default=0)
    account_locked_until = db.Column(db.DateTime)
    password_changed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    email = db.Column(db.String(120), unique=True, nullable=True)
    
    # Relationships
    created_admins = db.relationship('User', backref=db.backref('creator', remote_side=[id]))
    
    # Add cascade delete relationships for related models
    # These will be defined in the respective models, but we can add them here for clarity
    # audit_logs = db.relationship('AuditLog', backref='user', cascade='all, delete-orphan')
    # sessions = db.relationship('UserSession', backref='user', cascade='all, delete-orphan')
    # settings = db.relationship('UserSettings', backref='user', cascade='all, delete-orphan', uselist=False)
    # transactions = db.relationship('Transaction', backref='user', cascade='all, delete-orphan')
    # reconciliations = db.relationship('Reconciliation', backref='user', cascade='all, delete-orphan')
    
    # Database indexes for performance
    __table_args__ = (
        db.Index('idx_user_username', 'username'),
        db.Index('idx_user_email', 'email'),
        db.Index('idx_user_role', 'role'),
        db.Index('idx_user_is_active', 'is_active'),
        db.Index('idx_user_admin_level', 'admin_level'),
        # Composite indexes for common query patterns
        db.Index('idx_user_active_admin', 'is_active', 'admin_level'),
        db.Index('idx_user_role_active', 'role', 'is_active'),
    )
    
    @validates('username')
    def validate_username(self, key, value):
        """Validate username"""
        if not value or len(value.strip()) == 0:
            raise ValueError('Username cannot be empty')
        if len(value) < 3:
            raise ValueError('Username must be at least 3 characters')
        if len(value) > 80:
            raise ValueError('Username too long')
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return value.strip()
    
    @validates('email')
    def validate_email(self, key, value):
        """Validate email"""
        if value:
            if len(value) > 120:
                raise ValueError('Email too long')
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
                raise ValueError('Invalid email format')
        return value.strip() if value else None
    
    @validates('role')
    def validate_role(self, key, value):
        """Validate role"""
        allowed_roles = ['admin', 'user', 'viewer']
        if value not in allowed_roles:
            raise ValueError(f'Role must be one of: {allowed_roles}')
        return value
    
    @validates('admin_level')
    def validate_admin_level(self, key, value):
        """Validate admin level"""
        if value not in [0, 1, 2, 3]:
            raise ValueError('Admin level must be 0, 1, 2, or 3')
        return value
    
    def is_hard_admin(self):
        """Check if user is hard admin (level 0) - invisible in web interface"""
        return self.admin_level == 0
    
    def is_main_admin(self):
        """Check if user is main admin (level 1)"""
        return self.admin_level == 1
    
    def is_secondary_admin(self):
        """Check if user is secondary main admin (level 2)"""
        return self.admin_level == 2
    
    def is_sub_admin(self):
        """Check if user is sub admin (level 3)"""
        return self.admin_level == 3
    
    def is_any_admin(self):
        """Check if user is any type of admin"""
        return self.admin_level in [0, 1, 2, 3]
    
    def is_visible_admin(self):
        """Check if admin should be visible in web interface (excludes hard admin)"""
        return self.admin_level in [1, 2, 3]
    
    def can_manage_admin(self, target_admin_level):
        """Check if this admin can manage another admin of given level"""
        if self.admin_level == 0:  # Hard admin can manage all
            return True
        elif self.admin_level == 1:  # Main admin can manage all except hard admin
            return target_admin_level in [1, 2, 3]
        elif self.admin_level == 2:  # Secondary admin can manage sub-admins
            return target_admin_level == 3
        return False
    
    def get_admin_title(self):
        """Get admin title based on level"""
        if self.admin_level == 0:
            return "Hard Administrator"
        elif self.admin_level == 1:
            return "Main Administrator"
        elif self.admin_level == 2:
            return "Secondary Administrator"
        elif self.admin_level == 3:
            return "Sub Administrator"
        return "User"
    
    def get_permissions(self):
        """Get admin permissions as dictionary"""
        import json
        if self.admin_permissions:
            try:
                return json.loads(self.admin_permissions)
            except:
                return {}
        return {}
    
    def has_permission(self, permission):
        """Check if admin has specific permission"""
        if self.admin_level == 0:  # Hard admin has all permissions
            return True
        elif self.admin_level == 1:  # Main admin has all permissions except hard admin management
            return True
        elif self.admin_level == 2:  # Secondary admin has most permissions
            restricted_permissions = ['manage_main_admin', 'manage_hard_admin', 'system_config']
            return permission not in restricted_permissions
        else:  # Sub admin - check specific permissions
            permissions = self.get_permissions()
            return permissions.get(permission, False)
    
    def is_account_locked(self):
        """Check if account is locked"""
        if self.account_locked_until:
            # Handle both timezone-aware and timezone-naive datetimes
            lockout_time = self.account_locked_until
            if lockout_time.tzinfo is None:
                # Timezone-naive, assume UTC
                lockout_time = lockout_time.replace(tzinfo=timezone.utc)
            return datetime.now(timezone.utc) < lockout_time
        return False
    
    def increment_failed_attempts(self):
        """Increment failed login attempts"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            # Lock account for 30 minutes
            self.account_locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
    
    def reset_failed_attempts(self):
        """Reset failed login attempts"""
        self.failed_login_attempts = 0
        self.account_locked_until = None
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'admin_level': self.admin_level,
            'admin_title': self.get_admin_title(),
            'is_active': self.is_active,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'failed_login_attempts': self.failed_login_attempts,
            'account_locked_until': self.account_locked_until.isoformat() if self.account_locked_until else None,
            'created_by': self.created_by,
            'permissions': self.get_permissions()
        }
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def safe_delete(self):
        """Safely delete user and all related records"""
        from app.models.audit import AuditLog, UserSession
        from app.models.transaction import Transaction
        from app.models.financial import Reconciliation
        from app.models.config import UserSettings
        
        # Delete related records in the correct order
        
        # 1. Delete user sessions
        UserSession.query.filter_by(user_id=self.id).delete()
        
        # 2. Delete user settings
        UserSettings.query.filter_by(user_id=self.id).delete()
        
        # 3. Delete audit logs
        AuditLog.query.filter_by(user_id=self.id).delete()
        
        # 4. Delete reconciliations created by this user
        Reconciliation.query.filter_by(created_by=self.id).delete()
        
        # 5. Delete transactions created by this user
        Transaction.query.filter_by(created_by=self.id).delete()
        
        # 6. Finally delete the user
        db.session.delete(self)
    
    def set_password(self, password):
        """Set password hash"""
        from werkzeug.security import generate_password_hash
        self.password = generate_password_hash(password)
        self.password_changed_at = datetime.now(timezone.utc)
    
    def check_password(self, password):
        """Check password against hash"""
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password, password) 