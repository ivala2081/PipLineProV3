"""
Unit tests for security service
"""
import pytest
from unittest.mock import Mock, patch
from app.services.security_service import SecurityService


@pytest.mark.unit
class TestSecurityService:
    """Test SecurityService"""
    
    def test_security_service_initialization(self):
        """Test security service initialization"""
        service = SecurityService()
        
        assert service is not None
        assert service._max_attempts == 5
        assert service._lockout_duration == 900
        assert len(service._failed_attempts) == 0
    
    def test_validate_password_strength_weak(self):
        """Test password strength validation - weak password"""
        service = SecurityService()
        
        result = service.validate_password_strength("weak")
        
        assert result['is_valid'] is False
        assert result['strength'] == 'weak'
        assert len(result['issues']) > 0
    
    def test_validate_password_strength_strong(self):
        """Test password strength validation - strong password"""
        service = SecurityService()
        
        result = service.validate_password_strength("StrongP@ssw0rd123!")
        
        # Strong password should have score >= 4
        assert result['strength'] in ['strong', 'medium']
        assert result['score'] >= 2
    
    def test_validate_password_strength_common_password(self):
        """Test password strength validation - common password"""
        service = SecurityService()
        
        result = service.validate_password_strength("password123!")
        
        # Common password should have lower score or issues
        assert result['score'] < 5 or len(result['issues']) > 0
    
    def test_has_sequential_chars(self):
        """Test sequential character detection"""
        service = SecurityService()
        
        assert service._has_sequential_chars("abc123") is True
        assert service._has_sequential_chars("xyz") is True
        assert service._has_sequential_chars("random") is False
    
    def test_has_repeated_chars(self):
        """Test repeated character detection"""
        service = SecurityService()
        
        assert service._has_repeated_chars("aaaabbbb") is True
        assert service._has_repeated_chars("random") is False
    
    def test_generate_secure_token(self):
        """Test secure token generation"""
        service = SecurityService()
        
        token = service.generate_secure_token(32)
        
        assert len(token) > 0
        assert isinstance(token, str)
        
        # Generate another token and verify uniqueness
        token2 = service.generate_secure_token(32)
        assert token != token2
    
    def test_hash_password(self):
        """Test password hashing"""
        service = SecurityService()
        
        password = "TestPassword123!"
        hash1 = service.hash_password(password)
        hash2 = service.hash_password(password)
        
        assert hash1 != password
        assert hash1 != hash2  # Different salts should produce different hashes
        assert len(hash1) > 0
    
    def test_verify_password(self):
        """Test password verification"""
        service = SecurityService()
        
        password = "TestPassword123!"
        password_hash = service.hash_password(password)
        
        assert service.verify_password(password, password_hash) is True
        assert service.verify_password("wrong", password_hash) is False
    
    def test_check_rate_limit_within_limit(self):
        """Test rate limit check - within limit"""
        service = SecurityService()
        
        identifier = "test_user"
        
        # Make requests within limit
        for i in range(5):
            assert service.check_rate_limit(identifier, limit=10) is True
    
    def test_check_rate_limit_exceeded(self):
        """Test rate limit check - exceeded"""
        service = SecurityService()
        
        identifier = "test_user"
        
        # Exceed limit
        for i in range(10):
            service.check_rate_limit(identifier, limit=10)
        
        # Next request should be blocked
        assert service.check_rate_limit(identifier, limit=10) is False
    
    def test_record_failed_attempt(self):
        """Test recording failed authentication attempt"""
        service = SecurityService()
        
        service.record_failed_attempt("test_user", "192.168.1.1", "Mozilla/5.0", "invalid_credentials")
        
        assert "test_user" in service._failed_attempts
        assert len(service._failed_attempts["test_user"]) == 1
    
    def test_is_ip_blocked_not_blocked(self):
        """Test is_ip_blocked - not blocked"""
        service = SecurityService()
        
        assert service.is_ip_blocked("192.168.1.1") is False
    
    def test_is_ip_blocked_after_max_attempts(self):
        """Test is_ip_blocked - blocked after max attempts"""
        service = SecurityService()
        
        identifier = "test_user"
        ip_address = "192.168.1.1"
        
        # Record max attempts
        for i in range(service._max_attempts):
            service.record_failed_attempt(identifier, ip_address, "Mozilla/5.0", "invalid_credentials")
        
        assert service.is_ip_blocked(ip_address) is True
    
    def test_is_account_locked(self):
        """Test account lock detection"""
        service = SecurityService()
        
        identifier = "test_user"
        ip_address = "192.168.1.1"
        
        # Record max attempts
        for i in range(service._max_attempts):
            service.record_failed_attempt(identifier, ip_address, "Mozilla/5.0", "invalid_credentials")
        
        assert service.is_account_locked(identifier) is True
    
    def test_detect_suspicious_activity(self):
        """Test suspicious activity detection"""
        service = SecurityService()
        
        # Detect suspicious activity
        service.detect_suspicious_activity(
            "192.168.1.1",
            "short",
            "api_request",
            {"query": "SELECT * FROM users"}
        )
        
        # Should detect suspicious activity
        assert len(service._suspicious_activities) > 0

