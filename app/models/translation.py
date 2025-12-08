from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship, validates
from app import db


class TranslationKey(db.Model):
    """Translation keys for the application"""
    __tablename__ = 'translation_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    key_path = db.Column(db.String(255), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    context = db.Column(db.String(100), nullable=True)  # e.g., 'ui', 'email', 'notification'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    translations = relationship('Translation', back_populates='key', cascade='all, delete-orphan')
    
    @validates('key_path')
    def validate_key_path(self, key, value):
        """Validate translation key path"""
        if not value or '.' not in value:
            raise ValueError('Translation key must contain at least one dot (e.g., "common.loading")')
        return value


class Translation(db.Model):
    """Individual translations for each language"""
    __tablename__ = 'translations'
    
    id = db.Column(db.Integer, primary_key=True)
    key_id = db.Column(db.Integer, ForeignKey('translation_keys.id'), nullable=False)
    language_code = db.Column(db.String(10), nullable=False)
    translation_text = db.Column(db.Text, nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    is_auto_translated = db.Column(db.Boolean, default=False)
    confidence_score = db.Column(db.Float, default=0.0)  # For auto-translations
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    key = relationship('TranslationKey', back_populates='translations')
    
    # Composite unique constraint
    __table_args__ = (
        Index('idx_translation_key_language', 'key_id', 'language_code', unique=True),
    )
    
    @validates('language_code')
    def validate_language_code(self, key, value):
        """Validate language code"""
        allowed_languages = ['en', 'tr', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh', 'ar']
        if value not in allowed_languages:
            raise ValueError(f'Language code must be one of: {allowed_languages}')
        return value


class CustomDictionary(db.Model):
    """Custom dictionary for project-specific terms and expressions"""
    __tablename__ = 'custom_dictionary'
    
    id = db.Column(db.Integer, primary_key=True)
    source_language = db.Column(db.String(10), nullable=False)
    target_language = db.Column(db.String(10), nullable=False)
    source_term = db.Column(db.String(255), nullable=False)
    target_term = db.Column(db.String(255), nullable=False)
    context = db.Column(db.String(100), nullable=True)
    usage_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Composite unique constraint
    __table_args__ = (
        Index('idx_custom_dict_source_target', 'source_language', 'target_language', 'source_term', unique=True),
    )
    
    @validates('source_language', 'target_language')
    def validate_language_codes(self, key, value):
        """Validate language codes"""
        allowed_languages = ['en', 'tr', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh', 'ar']
        if value not in allowed_languages:
            raise ValueError(f'Language code must be one of: {allowed_languages}')
        return value


class TranslationMemory(db.Model):
    """Translation memory for storing previously used translations"""
    __tablename__ = 'translation_memory'
    
    id = db.Column(db.Integer, primary_key=True)
    source_language = db.Column(db.String(10), nullable=False)
    target_language = db.Column(db.String(10), nullable=False)
    source_text = db.Column(db.Text, nullable=False)
    target_text = db.Column(db.Text, nullable=False)
    context = db.Column(db.String(100), nullable=True)
    usage_count = db.Column(db.Integer, default=1)
    last_used = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Composite unique constraint
    __table_args__ = (
        Index('idx_translation_memory_source_target', 'source_language', 'target_language', 'source_text', unique=True),
    )


class TranslationLog(db.Model):
    """Log of translation operations for audit and analytics"""
    __tablename__ = 'translation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    operation_type = db.Column(db.String(50), nullable=False)  # 'create', 'update', 'delete', 'auto_translate'
    key_path = db.Column(db.String(255), nullable=True)
    source_language = db.Column(db.String(10), nullable=True)
    target_language = db.Column(db.String(10), nullable=True)
    user_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=True)
    details = db.Column(db.JSON, nullable=True)  # Additional operation details
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship('User', backref='translation_logs')


class TranslationSettings(db.Model):
    """Global translation settings and configuration"""
    __tablename__ = 'translation_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.JSON, nullable=False)
    description = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    @validates('setting_key')
    def validate_setting_key(self, key, value):
        """Validate setting key"""
        allowed_keys = [
            'supported_languages',
            'default_language',
            'auto_translation_enabled',
            'translation_provider',
            'quality_threshold',
            'backup_enabled',
            'sync_interval'
        ]
        if value not in allowed_keys:
            raise ValueError(f'Setting key must be one of: {allowed_keys}')
        return value
