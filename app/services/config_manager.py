"""
Centralized Configuration Management Service
Provides unified configuration access, validation, and management
"""
import os
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from datetime import datetime, timezone
from flask import current_app

from app.utils.unified_logger import get_logger

logger = get_logger("ConfigManager")


class ConfigCategory(str, Enum):
    """Configuration categories"""
    SECURITY = "security"
    DATABASE = "database"
    CACHE = "cache"
    LOGGING = "logging"
    PERFORMANCE = "performance"
    FEATURE = "feature"
    INTEGRATION = "integration"
    UI = "ui"


class ConfigValidationError(Exception):
    """Configuration validation error"""
    pass


class ConfigManager:
    """Centralized configuration management service"""
    
    def __init__(self, app=None):
        self.app = app
        self._config_cache: Dict[str, Any] = {}
        self._validators: Dict[str, Callable] = {}
        self._watchers: Dict[str, List[Callable]] = {}
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize configuration manager with Flask app"""
        self.app = app
        
        # Register built-in validators
        self._register_validators()
        
        logger.info("Configuration Manager initialized")
    
    def _register_validators(self):
        """Register built-in configuration validators"""
        
        def validate_positive_int(value: Any) -> bool:
            """Validate positive integer"""
            try:
                return isinstance(value, int) and value > 0
            except (ValueError, TypeError):
                return False
        
        def validate_port(value: Any) -> bool:
            """Validate port number"""
            return validate_positive_int(value) and 1 <= value <= 65535
        
        def validate_timeout(value: Any) -> bool:
            """Validate timeout value"""
            return validate_positive_int(value) and value <= 3600
        
        def validate_url(value: Any) -> bool:
            """Validate URL"""
            if not isinstance(value, str):
                return False
            return value.startswith(('http://', 'https://', 'redis://', 'postgresql://'))
        
        def validate_boolean(value: Any) -> bool:
            """Validate boolean"""
            return isinstance(value, bool)
        
        def validate_secret_key(value: Any) -> bool:
            """Validate secret key"""
            return isinstance(value, str) and len(value) >= 32
        
        # Register validators
        self._validators = {
            'port': validate_port,
            'timeout': validate_timeout,
            'url': validate_url,
            'boolean': validate_boolean,
            'secret_key': validate_secret_key,
            'positive_int': validate_positive_int
        }
    
    def get(self, key: str, default: Any = None, category: Optional[ConfigCategory] = None) -> Any:
        """Get configuration value"""
        try:
            # Try app config first
            if self.app:
                value = self.app.config.get(key, default)
            else:
                value = os.environ.get(key, default)
            
            # Cache the value
            cache_key = f"{category.value}_{key}" if category else key
            self._config_cache[cache_key] = value
            
            return value
        except Exception as e:
            logger.warning(f"Error getting config '{key}': {e}")
            return default
    
    def set(self, key: str, value: Any, validate: bool = True, category: Optional[ConfigCategory] = None):
        """Set configuration value (runtime-safe configurations only)"""
        if not self.app:
            raise RuntimeError("ConfigManager not initialized with Flask app")
        
        # Validate if requested
        if validate:
            self._validate_value(key, value, category)
        
        # Update app config
        self.app.config[key] = value
        
        # Update cache
        cache_key = f"{category.value}_{key}" if category else key
        self._config_cache[cache_key] = value
        
        # Notify watchers
        self._notify_watchers(key, value)
        
        logger.info(f"Configuration updated: {key}")
    
    def get_all(self, category: Optional[ConfigCategory] = None) -> Dict[str, Any]:
        """Get all configuration values, optionally filtered by category"""
        if not self.app:
            return {}
        
        config = {}
        
        # Get category-specific config keys
        category_prefixes = {
            ConfigCategory.SECURITY: ['SECRET_KEY', 'SESSION_', 'CSRF_', 'CORS_', 'AUTH_'],
            ConfigCategory.DATABASE: ['SQLALCHEMY_', 'DB_', 'POSTGRES_'],
            ConfigCategory.CACHE: ['REDIS_', 'CACHE_'],
            ConfigCategory.LOGGING: ['LOG_'],
            ConfigCategory.PERFORMANCE: ['POOL_', 'PERFORMANCE_'],
            ConfigCategory.FEATURE: ['FEATURE_', 'ENABLE_'],
        }
        
        if category and category in category_prefixes:
            prefixes = category_prefixes[category]
            for key in self.app.config:
                if any(key.startswith(prefix) for prefix in prefixes):
                    config[key] = self.app.config[key]
        else:
            config = dict(self.app.config)
        
        return config
    
    def validate(self, key: str, value: Any, category: Optional[ConfigCategory] = None) -> bool:
        """Validate configuration value"""
        try:
            self._validate_value(key, value, category)
            return True
        except ConfigValidationError:
            return False
    
    def _validate_value(self, key: str, value: Any, category: Optional[ConfigCategory] = None):
        """Internal validation"""
        # Port validation
        if 'PORT' in key.upper():
            if not self._validators['port'](value):
                raise ConfigValidationError(f"Invalid port value: {value}")
        
        # URL validation
        elif 'URL' in key.upper() or '_URL' in key.upper():
            if value and not self._validators['url'](value):
                raise ConfigValidationError(f"Invalid URL value: {value}")
        
        # Timeout validation
        elif 'TIMEOUT' in key.upper():
            if not self._validators['timeout'](value):
                raise ConfigValidationError(f"Invalid timeout value: {value}")
        
        # Secret key validation
        elif 'SECRET_KEY' in key.upper():
            if not self._validators['secret_key'](value):
                raise ConfigValidationError(f"Secret key must be at least 32 characters")
        
        # Boolean validation
        elif isinstance(value, bool):
            if not self._validators['boolean'](value):
                raise ConfigValidationError(f"Invalid boolean value: {value}")
    
    def watch(self, key: str, callback: Callable[[str, Any], None]):
        """Watch for configuration changes"""
        if key not in self._watchers:
            self._watchers[key] = []
        self._watchers[key].append(callback)
    
    def _notify_watchers(self, key: str, value: Any):
        """Notify watchers of configuration changes"""
        if key in self._watchers:
            for callback in self._watchers[key]:
                try:
                    callback(key, value)
                except Exception as e:
                    logger.error(f"Error in config watcher callback: {e}")
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return {
            'database_url': self.get('SQLALCHEMY_DATABASE_URI', ''),
            'pool_size': self.get('SQLALCHEMY_ENGINE_OPTIONS', {}).get('pool_size', 5),
            'max_overflow': self.get('SQLALCHEMY_ENGINE_OPTIONS', {}).get('max_overflow', 10),
            'pool_timeout': self.get('SQLALCHEMY_ENGINE_OPTIONS', {}).get('pool_timeout', 30),
            'pool_recycle': self.get('SQLALCHEMY_ENGINE_OPTIONS', {}).get('pool_recycle', 3600),
            'query_logging': self.get('DB_QUERY_LOGGING', False),
            'slow_query_threshold': self.get('DB_SLOW_QUERY_THRESHOLD', 1.0),
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        return {
            'secret_key_set': bool(self.get('SECRET_KEY')),
            'session_lifetime_hours': self.get('PERMANENT_SESSION_LIFETIME').total_seconds() / 3600 if self.get('PERMANENT_SESSION_LIFETIME') else 8,
            'session_cookie_secure': self.get('SESSION_COOKIE_SECURE', False),
            'session_cookie_httponly': self.get('SESSION_COOKIE_HTTPONLY', True),
            'session_cookie_samesite': self.get('SESSION_COOKIE_SAMESITE', 'Lax'),
            'csrf_enabled': self.get('WTF_CSRF_ENABLED', True),
            'cors_origins': self.get('CORS_ORIGINS', []),
            'max_content_length': self.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024),
        }
    
    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration"""
        return {
            'redis_enabled': self.get('REDIS_ENABLED', False),
            'redis_url': self.get('REDIS_URL', ''),
            'cache_ttl': self.get('REDIS_CACHE_TTL', 300),
            'session_ttl': self.get('REDIS_SESSION_TTL', 14400),
        }
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration"""
        return {
            'pool_size': self.get('SQLALCHEMY_ENGINE_OPTIONS', {}).get('pool_size', 5),
            'max_overflow': self.get('SQLALCHEMY_ENGINE_OPTIONS', {}).get('max_overflow', 10),
            'query_logging': self.get('DB_QUERY_LOGGING', False),
            'slow_query_threshold': self.get('DB_SLOW_QUERY_THRESHOLD', 1.0),
            'monitoring_enabled': self.get('DB_CONNECTION_MONITORING', True),
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            'level': self.get('LOG_LEVEL', 'INFO'),
            'file': self.get('LOG_FILE', 'logs/pipeline.log'),
            'json_format': self.get('LOG_JSON_FORMAT', False),
        }
    
    def get_feature_flags(self) -> Dict[str, bool]:
        """Get feature flags"""
        return {
            'backup_enabled': self.get('BACKUP_ENABLED', True),
            'redis_enabled': self.get('REDIS_ENABLED', False),
            'query_logging': self.get('DB_QUERY_LOGGING', False),
            'connection_monitoring': self.get('DB_CONNECTION_MONITORING', True),
            'performance_monitoring': self.get('DB_PERFORMANCE_MONITORING', True),
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        return {
            'environment': self.get('FLASK_ENV', 'development'),
            'debug': self.get('DEBUG', False),
            'database': self.get_database_config(),
            'security': self.get_security_config(),
            'cache': self.get_cache_config(),
            'performance': self.get_performance_config(),
            'logging': self.get_logging_config(),
            'features': self.get_feature_flags(),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def reload(self):
        """Reload configuration from environment"""
        # Clear cache
        self._config_cache.clear()
        
        # Reload from environment variables
        if self.app:
            from config import config
            env = os.environ.get('FLASK_ENV', 'development')
            config_name = 'production' if env == 'production' else ('testing' if env == 'testing' else 'development')
            self.app.config.from_object(config[config_name])
        
        logger.info("Configuration reloaded")
    
    def export(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Export configuration (excluding secrets by default)"""
        config = self.get_all()
        
        if not include_secrets:
            # Filter out sensitive values
            sensitive_keys = ['SECRET_KEY', 'PASSWORD', 'TOKEN', 'API_KEY', 'PRIVATE_KEY']
            filtered_config = {}
            for key, value in config.items():
                if any(sensitive in key.upper() for sensitive in sensitive_keys):
                    filtered_config[key] = '***REDACTED***'
                else:
                    filtered_config[key] = value
            return filtered_config
        
        return config


# Global instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager(app=None) -> ConfigManager:
    """Get or create configuration manager instance"""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigManager(app)
    
    return _config_manager


def init_config_manager(app):
    """Initialize configuration manager with Flask app"""
    return get_config_manager(app).init_app(app)

