"""
Audit and session models for security and tracking
"""
from app import db
from datetime import datetime, timezone
from sqlalchemy.orm import validates

class AuditLog(db.Model):
    """Audit log for tracking all changes"""
    __tablename__ = 'audit_log'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # 'CREATE', 'UPDATE', 'DELETE'
    table_name = db.Column(db.String(50), nullable=False)
    record_id = db.Column(db.Integer, nullable=False)
    old_values = db.Column(db.Text)  # JSON string of old values
    new_values = db.Column(db.Text)  # JSON string of new values
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    ip_address = db.Column(db.String(45))
    
    # Database indexes for performance
    __table_args__ = (
        db.Index('idx_audit_user_id', 'user_id'),
        db.Index('idx_audit_action', 'action'),
        db.Index('idx_audit_table', 'table_name'),
        db.Index('idx_audit_timestamp', 'timestamp'),
        db.Index('idx_audit_user_timestamp', 'user_id', 'timestamp'),  # Composite for user audit history queries
    )
    
    # Relationships
    user = db.relationship('User', backref=db.backref('audit_logs', lazy=True))
    
    @validates('action')
    def validate_action(self, key, value):
        """Validate action"""
        # Base actions
        allowed_actions = [
            'CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT',
            # Admin-specific actions
            'ADMIN_CREATE', 'ADMIN_UPDATE', 'ADMIN_DELETE',
            'ADMIN_PERMISSION_CHANGE', 'ADMIN_LEVEL_CHANGE',
            'ADMIN_ACTIVATE', 'ADMIN_DEACTIVATE',
            # User management actions
            'USER_PASSWORD_CHANGE', 'USER_ACCOUNT_LOCK', 'USER_ACCOUNT_UNLOCK',
            # System actions
            'SYSTEM_CONFIG_CHANGE', 'BACKUP_CREATE', 'BACKUP_RESTORE',
            'DATABASE_OPERATION', 'BULK_DELETE', 'IMPORT_DATA', 'EXPORT_DATA'
        ]
        if value not in allowed_actions:
            # Log warning but allow it (for backward compatibility and extensibility)
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Unknown action type in audit log: {value}. Allowing for backward compatibility.")
        return value
    
    def to_dict(self):
        """Convert audit log to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'table_name': self.table_name,
            'record_id': self.record_id,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'ip_address': self.ip_address
        }
    
    def __repr__(self):
        return f'<AuditLog {self.action} on {self.table_name}:{self.record_id}>'

class UserSession(db.Model):
    """User session tracking"""
    __tablename__ = 'user_session'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_token = db.Column(db.String(128), unique=True, nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_active = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)
    
    # Database indexes for performance
    __table_args__ = (
        db.Index('idx_session_user_id', 'user_id'),
        db.Index('idx_session_token', 'session_token'),
        db.Index('idx_session_is_active', 'is_active'),
        db.Index('idx_session_last_active', 'last_active'),
    )
    
    # Relationships
    user = db.relationship('User', backref=db.backref('sessions', lazy=True))
    
    def to_dict(self):
        """Convert session to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_token': self.session_token,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_active': self.last_active.isoformat() if self.last_active else None,
            'is_active': self.is_active
        }
    
    def __repr__(self):
        return f'<UserSession {self.user_id}:{self.session_token[:8]}...>'

class LoginAttempt(db.Model):
    """Login attempt tracking for security"""
    __tablename__ = 'login_attempt'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(255))
    success = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    failure_reason = db.Column(db.String(100))  # 'invalid_credentials', 'account_locked', etc.
    
    # Database indexes for performance
    __table_args__ = (
        db.Index('idx_login_username', 'username'),
        db.Index('idx_login_ip', 'ip_address'),
        db.Index('idx_login_success', 'success'),
        db.Index('idx_login_timestamp', 'timestamp'),
    )
    
    def to_dict(self):
        """Convert login attempt to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'success': self.success,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'failure_reason': self.failure_reason
        }
    
    def __repr__(self):
        return f'<LoginAttempt {self.username}:{"SUCCESS" if self.success else "FAILED"}>' 