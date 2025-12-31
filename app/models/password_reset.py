"""
Password Reset Token Model
Stores secure password reset tokens with expiration
"""
from app import db
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import validates
import secrets

class PasswordResetToken(db.Model):
    """Password reset token model"""
    __tablename__ = 'password_reset_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 support
    
    # Relationships
    user = db.relationship('User', backref=db.backref('password_reset_tokens', lazy='dynamic'))
    
    __table_args__ = (
        db.Index('idx_password_reset_token_user_expires', 'user_id', 'expires_at'),
        db.Index('idx_password_reset_token_token', 'token'),
    )
    
    @classmethod
    def generate_token(cls, user_id: int, ip_address: str = None, expiry_hours: int = 1) -> 'PasswordResetToken':
        """
        Generate a new password reset token
        
        Args:
            user_id: User ID requesting password reset
            ip_address: IP address of the requester
            expiry_hours: Token expiration time in hours (default: 1 hour)
        
        Returns:
            PasswordResetToken instance
        """
        # Invalidate all existing tokens for this user
        cls.query.filter_by(user_id=user_id, used=False).update({'used': True})
        db.session.commit()
        
        # Generate secure token
        token = secrets.token_urlsafe(48)  # 64 characters when URL-safe encoded
        
        # Create new token
        reset_token = cls(
            user_id=user_id,
            token=token,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expiry_hours),
            ip_address=ip_address
        )
        
        db.session.add(reset_token)
        db.session.commit()
        
        return reset_token
    
    @classmethod
    def validate_token(cls, token: str) -> tuple:
        """
        Validate a password reset token
        
        Args:
            token: Token to validate
        
        Returns:
            Tuple of (is_valid, token_object, error_message)
        """
        reset_token = cls.query.filter_by(token=token, used=False).first()
        
        if not reset_token:
            return False, None, "Invalid or expired reset token"
        
        now = datetime.now(timezone.utc)
        expires_at = reset_token.expires_at
        if expires_at.tzinfo is None:
            # If expires_at is naive, make it timezone-aware
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if expires_at < now:
            # Mark as used
            reset_token.used = True
            db.session.commit()
            return False, None, "Reset token has expired"
        
        return True, reset_token, None
    
    def mark_as_used(self):
        """Mark token as used"""
        self.used = True
        db.session.commit()
    
    def is_valid(self) -> bool:
        """Check if token is still valid"""
        now = datetime.now(timezone.utc)
        if self.expires_at.tzinfo is None:
            # If expires_at is naive, make it timezone-aware
            expires_at = self.expires_at.replace(tzinfo=timezone.utc)
        else:
            expires_at = self.expires_at
        return not self.used and expires_at > now
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'used': self.used,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

