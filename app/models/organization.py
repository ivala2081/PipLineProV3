"""
Organization (Tenant) model for multi-tenancy support
This is the foundation for B2B SaaS - each customer company is an Organization
"""
from app import db
from datetime import datetime, timezone
from sqlalchemy.orm import validates
import re


class Organization(db.Model):
    """
    Organization model - represents a tenant/company in the multi-tenant system
    
    Each B2B customer will have one Organization record.
    All data (users, transactions, expenses, etc.) will be linked to an organization.
    """
    __tablename__ = 'organization'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic Info
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)  # URL-friendly identifier
    
    # Subscription & Billing
    subscription_tier = db.Column(db.String(20), default='free')  # 'free', 'starter', 'pro', 'enterprise'
    subscription_status = db.Column(db.String(20), default='active')  # 'active', 'suspended', 'cancelled'
    subscription_expires_at = db.Column(db.DateTime, nullable=True)
    
    # Limits based on subscription
    max_users = db.Column(db.Integer, default=1)
    max_transactions_per_month = db.Column(db.Integer, default=100)
    max_psp_connections = db.Column(db.Integer, default=1)
    
    # Organization Settings (JSON for flexibility)
    settings = db.Column(db.JSON, default=dict)
    
    # Branding (for white-label)
    logo_url = db.Column(db.String(255), nullable=True)
    primary_color = db.Column(db.String(7), nullable=True)  # Hex color
    
    # Contact Info
    contact_email = db.Column(db.String(120), nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    country = db.Column(db.String(50), nullable=True)
    timezone = db.Column(db.String(50), default='UTC')
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), 
                          onupdate=lambda: datetime.now(timezone.utc))
    
    # Database indexes for performance
    __table_args__ = (
        db.Index('idx_organization_slug', 'slug'),
        db.Index('idx_organization_is_active', 'is_active'),
        db.Index('idx_organization_subscription', 'subscription_tier', 'subscription_status'),
    )
    
    @validates('slug')
    def validate_slug(self, key, value):
        """Validate slug - only lowercase letters, numbers, and hyphens"""
        if not value or len(value.strip()) == 0:
            raise ValueError('Slug cannot be empty')
        if len(value) < 3:
            raise ValueError('Slug must be at least 3 characters')
        if len(value) > 50:
            raise ValueError('Slug too long')
        if not re.match(r'^[a-z0-9-]+$', value):
            raise ValueError('Slug can only contain lowercase letters, numbers, and hyphens')
        return value.strip().lower()
    
    @validates('name')
    def validate_name(self, key, value):
        """Validate organization name"""
        if not value or len(value.strip()) == 0:
            raise ValueError('Organization name cannot be empty')
        if len(value) > 100:
            raise ValueError('Organization name too long')
        return value.strip()
    
    @validates('subscription_tier')
    def validate_subscription_tier(self, key, value):
        """Validate subscription tier"""
        allowed_tiers = ['free', 'starter', 'pro', 'enterprise']
        if value not in allowed_tiers:
            raise ValueError(f'Subscription tier must be one of: {allowed_tiers}')
        return value
    
    def is_subscription_active(self):
        """Check if subscription is active and not expired"""
        if self.subscription_status != 'active':
            return False
        if self.subscription_expires_at:
            return datetime.now(timezone.utc) < self.subscription_expires_at
        return True
    
    def can_add_user(self, current_user_count):
        """Check if organization can add more users"""
        return current_user_count < self.max_users
    
    def can_add_transaction(self, current_month_count):
        """Check if organization can add more transactions this month"""
        return current_month_count < self.max_transactions_per_month
    
    def get_setting(self, key, default=None):
        """Get a setting value"""
        if self.settings:
            return self.settings.get(key, default)
        return default
    
    def set_setting(self, key, value):
        """Set a setting value"""
        if not self.settings:
            self.settings = {}
        self.settings[key] = value
    
    def to_dict(self):
        """Convert organization to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'subscription_tier': self.subscription_tier,
            'subscription_status': self.subscription_status,
            'subscription_expires_at': self.subscription_expires_at.isoformat() if self.subscription_expires_at else None,
            'max_users': self.max_users,
            'max_transactions_per_month': self.max_transactions_per_month,
            'max_psp_connections': self.max_psp_connections,
            'logo_url': self.logo_url,
            'primary_color': self.primary_color,
            'contact_email': self.contact_email,
            'country': self.country,
            'timezone': self.timezone,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Organization {self.name} ({self.slug})>'

