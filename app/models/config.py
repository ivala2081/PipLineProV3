"""
Configuration models for PipLine Treasury System
"""
from app import db
from sqlalchemy.orm import validates
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

# Decimal/Float type mismatch prevention
from app.services.decimal_float_fix_service import decimal_float_service

class Option(db.Model):
    """Configurable dropdown options"""
    __tablename__ = 'option'
    
    id = db.Column(db.Integer, primary_key=True)
    field_name = db.Column(db.String(50), nullable=False)
    value = db.Column(db.String(100), nullable=False)
    commission_rate = db.Column(db.Numeric(5, 4), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Database indexes for performance
    __table_args__ = (
        db.Index('idx_option_field_name', 'field_name'),
        db.Index('idx_option_is_active', 'is_active'),
    )
    
    @validates('field_name')
    def validate_field_name(self, key, value):
        """Validate field name"""
        allowed_fields = ['psp', 'category', 'payment_method', 'company', 'currency']
        if value not in allowed_fields:
            raise ValueError(f'Field name must be one of: {allowed_fields}')
        return value
    
    @validates('commission_rate')
    def validate_commission_rate(self, key, value):
        """Validate commission rate"""
        if value is not None:
            try:
                rate = Decimal(str(value))
                if rate < 0 or rate > 1:
                    raise ValueError('Commission rate must be between 0 and 1')
                return rate
            except (InvalidOperation, ValueError) as e:
                raise ValueError(f'Invalid commission rate: {e}')
        return value
    
    def to_dict(self):
        """Convert option to dictionary"""
        return {
            'id': self.id,
            'field_name': self.field_name,
            'value': self.value,
            'commission_rate': float(self.commission_rate) if self.commission_rate else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Option {self.field_name}:{self.value}>'

class ExchangeRate(db.Model):
    """Daily exchange rates"""
    __tablename__ = 'exchange_rate'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False)
    usd_to_tl = db.Column(db.Numeric(10, 4), nullable=False)
    eur_to_tl = db.Column(db.Numeric(10, 4), nullable=True)
    is_manual = db.Column(db.Boolean, default=False, nullable=False)  # Track if rate was manually edited
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Database indexes for performance
    __table_args__ = (
        db.Index('idx_exchange_rate_date', 'date'),
    )
    
    @validates('usd_to_tl')
    def validate_usd_to_tl(self, key, value):
        """Validate USD to TL rate"""
        if value is not None:
            try:
                rate = Decimal(str(value))
                if rate <= 0:
                    raise ValueError('Exchange rate must be positive')
                return rate
            except (InvalidOperation, ValueError) as e:
                raise ValueError(f'Invalid USD to TL rate: {e}')
        return value
    
    @validates('eur_to_tl')
    def validate_eur_to_tl(self, key, value):
        """Validate EUR to TL rate"""
        if value is not None:
            try:
                rate = Decimal(str(value))
                if rate <= 0:
                    raise ValueError('Exchange rate must be positive')
                return rate
            except (InvalidOperation, ValueError) as e:
                raise ValueError(f'Invalid EUR to TL rate: {e}')
        return value
    
    def to_dict(self):
        """Convert exchange rate to dictionary"""
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'usd_to_tl': float(self.usd_to_tl) if self.usd_to_tl else None,
            'eur_to_tl': float(self.eur_to_tl) if self.eur_to_tl else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<ExchangeRate {self.date}: USD={self.usd_to_tl}, EUR={self.eur_to_tl}>'

class UserSettings(db.Model):
    """User preferences and settings"""
    __tablename__ = 'user_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    language = db.Column(db.String(20), default='en')
    landing_page = db.Column(db.String(50), default='dashboard')
    table_page_size = db.Column(db.Integer, default=25)
    table_density = db.Column(db.String(20), default='comfortable')
    font_size = db.Column(db.String(20), default='medium')
    color_scheme = db.Column(db.String(20), default='default')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = db.relationship('User', backref=db.backref('settings', uselist=False))
    
    @validates('language')
    def validate_language(self, key, value):
        """Validate language"""
        allowed_languages = ['en', 'tr']
        if value not in allowed_languages:
            raise ValueError(f'Language must be one of: {allowed_languages}')
        return value
    
    @validates('landing_page')
    def validate_landing_page(self, key, value):
        """Validate landing page"""
        allowed_pages = ['dashboard', 'transactions', 'summary', 'analytics']
        if value not in allowed_pages:
            raise ValueError(f'Landing page must be one of: {allowed_pages}')
        return value
    
    @validates('table_density')
    def validate_table_density(self, key, value):
        """Validate table density"""
        allowed_densities = ['compact', 'comfortable', 'spacious']
        if value not in allowed_densities:
            raise ValueError(f'Table density must be one of: {allowed_densities}')
        return value
    
    @validates('font_size')
    def validate_font_size(self, key, value):
        """Validate font size"""
        allowed_sizes = ['small', 'medium', 'large']
        if value not in allowed_sizes:
            raise ValueError(f'Font size must be one of: {allowed_sizes}')
        return value
    
    @validates('color_scheme')
    def validate_color_scheme(self, key, value):
        """Validate color scheme"""
        allowed_schemes = ['default', 'blue', 'green', 'red', 'purple', 'orange', 'teal', 'pink', 'brown', 'business']
        if value not in allowed_schemes:
            raise ValueError(f'Color scheme must be one of: {allowed_schemes}')
        return value
    
    def to_dict(self):
        """Convert user settings to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'language': self.language,
            'landing_page': self.landing_page,
            'table_page_size': self.table_page_size,
            'table_density': self.table_density,
            'font_size': self.font_size,
            'color_scheme': self.color_scheme,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<UserSettings {self.user_id}:{self.color_scheme}>'

class AdminSectionPermission(db.Model):
    """Admin section permissions - controls which sections are accessible to different admin levels"""
    __tablename__ = 'admin_section_permission'
    
    id = db.Column(db.Integer, primary_key=True)
    section_name = db.Column(db.String(100), nullable=False, unique=True)
    section_display_name = db.Column(db.String(100), nullable=False)
    section_description = db.Column(db.Text, nullable=True)
    main_admin_access = db.Column(db.Boolean, default=True)  # Main admin always has access
    secondary_admin_access = db.Column(db.Boolean, default=True)  # Secondary admin access
    sub_admin_access = db.Column(db.Boolean, default=False)  # Sub admin access
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Database indexes for performance
    __table_args__ = (
        db.Index('idx_admin_section_name', 'section_name'),
        db.Index('idx_admin_section_active', 'is_active'),
    )
    
    @validates('section_name')
    def validate_section_name(self, key, value):
        """Validate section name"""
        if not value or len(value.strip()) == 0:
            raise ValueError('Section name cannot be empty')
        if len(value) > 100:
            raise ValueError('Section name too long')
        return value.strip()
    
    @validates('section_display_name')
    def validate_section_display_name(self, key, value):
        """Validate section display name"""
        if not value or len(value.strip()) == 0:
            raise ValueError('Section display name cannot be empty')
        if len(value) > 100:
            raise ValueError('Section display name too long')
        return value.strip()
    
    def to_dict(self):
        """Convert section permission to dictionary"""
        return {
            'id': self.id,
            'section_name': self.section_name,
            'section_display_name': self.section_display_name,
            'section_description': self.section_description,
            'main_admin_access': self.main_admin_access,
            'secondary_admin_access': self.secondary_admin_access,
            'sub_admin_access': self.sub_admin_access,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def has_access_for_level(self, admin_level):
        """Check if this section is accessible for given admin level"""
        if admin_level == 1:  # Main admin
            return self.main_admin_access
        elif admin_level == 2:  # Secondary admin
            return self.secondary_admin_access
        elif admin_level == 3:  # Sub admin
            return self.sub_admin_access
        return False
    
    def __repr__(self):
        return f'<AdminSectionPermission {self.section_name}:{self.section_display_name}>' 