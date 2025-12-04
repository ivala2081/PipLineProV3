"""
Unit tests for config manager
"""
import pytest
from unittest.mock import Mock, patch
from app.services.config_manager import ConfigManager, ConfigCategory, ConfigValidationError


@pytest.mark.unit
class TestConfigManager:
    """Test ConfigManager"""
    
    def test_config_manager_initialization(self):
        """Test config manager initialization"""
        manager = ConfigManager()
        
        assert manager is not None
        assert manager._config_cache == {}
        # Validators are registered only when init_app is called
        assert manager._validators == {}
    
    def test_config_manager_initialization_with_app(self, app):
        """Test config manager initialization with Flask app"""
        manager = ConfigManager(app=app)
        
        assert manager.app == app
    
    def test_get_config_from_app(self, app):
        """Test getting config value from app"""
        app.config['TEST_KEY'] = 'test_value'
        
        manager = ConfigManager(app=app)
        value = manager.get('TEST_KEY')
        
        assert value == 'test_value'
    
    def test_get_config_with_default(self, app):
        """Test getting config value with default"""
        manager = ConfigManager(app=app)
        value = manager.get('NON_EXISTENT_KEY', default='default_value')
        
        assert value == 'default_value'
    
    def test_get_config_with_category(self, app):
        """Test getting config value with category"""
        app.config['SECURITY_SECRET_KEY'] = 'secret'
        
        manager = ConfigManager(app=app)
        value = manager.get('SECRET_KEY', category=ConfigCategory.SECURITY)
        
        # Should try to find SECURITY_SECRET_KEY
        assert value is not None
    
    def test_set_config(self, app):
        """Test setting config value"""
        manager = ConfigManager(app=app)
        
        manager.set('TEST_KEY', 'test_value')
        
        assert app.config['TEST_KEY'] == 'test_value'
    
    def test_validate_positive_int(self, app):
        """Test positive integer validation"""
        manager = ConfigManager(app=app)
        
        validator = manager._validators.get('positive_int')
        assert validator is not None
        assert validator(5) is True
        assert validator(-5) is False
        assert validator(0) is False
        assert validator('not_int') is False
    
    def test_validate_port(self, app):
        """Test port validation"""
        manager = ConfigManager(app=app)
        
        validator = manager._validators.get('port')
        assert validator is not None
        assert validator(8080) is True
        assert validator(65535) is True
        assert validator(0) is False
        assert validator(65536) is False
    
    def test_validate_url(self, app):
        """Test URL validation"""
        manager = ConfigManager(app=app)
        
        validator = manager._validators.get('url')
        assert validator is not None
        assert validator('http://example.com') is True
        assert validator('https://example.com') is True
        assert validator('redis://localhost:6379') is True
        assert validator('not_a_url') is False
        assert validator(123) is False
    
    def test_validate_boolean(self, app):
        """Test boolean validation"""
        manager = ConfigManager(app=app)
        
        validator = manager._validators.get('boolean')
        assert validator is not None
        assert validator(True) is True
        assert validator(False) is True
        assert validator('true') is False
        assert validator(1) is False
    
    def test_validate_secret_key(self, app):
        """Test secret key validation"""
        manager = ConfigManager(app=app)
        
        validator = manager._validators.get('secret_key')
        assert validator is not None
        assert validator('a' * 32) is True
        assert validator('short') is False
        assert validator(123) is False
    
    def test_validators_registered_on_init(self, app):
        """Test that validators are registered when init_app is called"""
        manager = ConfigManager()
        manager.init_app(app)
        
        # Validators should be registered after init_app
        assert len(manager._validators) > 0
        assert 'port' in manager._validators
        assert 'url' in manager._validators
        assert 'boolean' in manager._validators
    
    def test_watch_config(self, app):
        """Test watching config changes"""
        manager = ConfigManager(app=app)
        
        callback_called = []
        
        def callback(key, old_value, new_value):
            callback_called.append((key, old_value, new_value))
        
        manager.watch('TEST_KEY', callback)
        
        manager.set('TEST_KEY', 'new_value')
        
        # Callback should be called (if implemented)
        # This is a basic test structure
    
    def test_get_all_config(self, app):
        """Test getting all config values"""
        app.config['KEY1'] = 'value1'
        app.config['KEY2'] = 'value2'
        
        manager = ConfigManager(app=app)
        all_config = manager.get_all()
        
        assert 'KEY1' in all_config
        assert 'KEY2' in all_config
        assert all_config['KEY1'] == 'value1'

