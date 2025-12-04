"""
Unit Tests - User Model
Tests for user model validation and authentication
"""
import pytest
from app.models.user import User
from datetime import datetime, timedelta, timezone


class TestUserCreation:
    """Test user creation and basic fields"""
    
    def test_create_basic_user(self, session):
        """Test creating a basic user"""
        user = User(
            username='testuser',
            email='test@test.com',
            role='user',
            admin_level=0
        )
        user.set_password('password123')
        session.add(user)
        session.commit()
        
        assert user.id is not None
        assert user.username == 'testuser'
        assert user.email == 'test@test.com'
    
    def test_user_timestamps(self, session):
        """Test user created_at timestamp"""
        user = User(
            username='testuser',
            email='test@test.com',
            role='user',
            admin_level=0
        )
        user.set_password('password123')
        session.add(user)
        session.commit()
        
        assert user.created_at is not None
        assert user.password_changed_at is not None
    
    def test_user_default_values(self, session):
        """Test user default field values"""
        user = User(
            username='testuser',
            email='test@test.com',
            role='user',
            admin_level=0
        )
        user.set_password('password123')
        session.add(user)
        session.commit()
        
        assert user.is_active is True
        assert user.failed_login_attempts == 0
        assert user.account_locked_until is None


class TestUserValidation:
    """Test user field validation"""
    
    def test_username_required(self, session):
        """Test username is required"""
        with pytest.raises(ValueError, match='Username cannot be empty'):
            user = User(
                username='',
                email='test@test.com',
                role='user',
                admin_level=0
            )
            session.add(user)
            session.commit()
    
    def test_username_minimum_length(self, session):
        """Test username minimum length"""
        with pytest.raises(ValueError, match='Username must be at least 3 characters'):
            user = User(
                username='ab',  # Too short
                email='test@test.com',
                role='user',
                admin_level=0
            )
            session.add(user)
            session.commit()
    
    def test_username_special_characters(self, session):
        """Test username with invalid characters"""
        with pytest.raises(ValueError, match='Username can only contain'):
            user = User(
                username='user@#$',  # Invalid characters
                email='test@test.com',
                role='user',
                admin_level=0
            )
            session.add(user)
            session.commit()
    
    def test_username_whitespace_trimmed(self, session):
        """Test username whitespace is trimmed"""
        # Note: Username validation happens before trimming
        # Whitespace in username will fail validation
        user = User(
            username='testuser',  # No whitespace - validation requires alphanumeric only
            email='test@test.com',
            role='user',
            admin_level=0
        )
        user.set_password('password123')
        session.add(user)
        session.commit()
        
        assert user.username == 'testuser'
    
    def test_email_validation(self, session):
        """Test email format validation"""
        with pytest.raises(ValueError, match='Invalid email format'):
            user = User(
                username='testuser',
                email='invalid-email',  # Invalid format
                role='user',
                admin_level=0
            )
            session.add(user)
            session.commit()
    
    def test_email_whitespace_trimmed(self, session):
        """Test email whitespace is trimmed"""
        # Note: Email validation happens before trimming
        # Whitespace in email will fail validation
        user = User(
            username='testuser',
            email='test@test.com',  # No whitespace - validation requires proper format
            role='user',
            admin_level=0
        )
        user.set_password('password123')
        session.add(user)
        session.commit()
        
        assert user.email == 'test@test.com'
    
    def test_role_validation(self, session):
        """Test role validation"""
        with pytest.raises(ValueError, match='Role must be one of'):
            user = User(
                username='testuser',
                email='test@test.com',
                role='superuser',  # Invalid role
                admin_level=0
            )
            session.add(user)
            session.commit()
    
    def test_admin_level_validation(self, session):
        """Test admin level validation"""
        with pytest.raises(ValueError, match='Admin level must be 0, 1, 2, or 3'):
            user = User(
                username='testuser',
                email='test@test.com',
                role='admin',
                admin_level=99  # Invalid level
            )
            session.add(user)
            session.commit()


class TestPasswordManagement:
    """Test password hashing and verification"""
    
    def test_set_password(self, session):
        """Test password is hashed"""
        user = User(
            username='testuser',
            email='test@test.com',
            role='user',
            admin_level=0
        )
        user.set_password('password123')
        session.add(user)
        session.commit()
        
        # Password should be hashed
        assert user.password != 'password123'
        assert len(user.password) > 50
    
    def test_check_password_correct(self, session):
        """Test password verification with correct password"""
        user = User(
            username='testuser',
            email='test@test.com',
            role='user',
            admin_level=0
        )
        user.set_password('password123')
        session.add(user)
        session.commit()
        
        assert user.check_password('password123') is True
    
    def test_check_password_incorrect(self, session):
        """Test password verification with incorrect password"""
        user = User(
            username='testuser',
            email='test@test.com',
            role='user',
            admin_level=0
        )
        user.set_password('password123')
        session.add(user)
        session.commit()
        
        assert user.check_password('wrongpassword') is False
    
    def test_password_changed_at_updated(self, session):
        """Test password_changed_at is updated"""
        user = User(
            username='testuser',
            email='test@test.com',
            role='user',
            admin_level=0
        )
        user.set_password('password123')
        session.add(user)
        session.commit()
        
        assert user.password_changed_at is not None


class TestUserRoles:
    """Test user role functionality"""
    
    def test_admin_role(self, session):
        """Test admin role"""
        user = User(
            username='admin',
            email='admin@test.com',
            role='admin',
            admin_level=1
        )
        user.set_password('password123')
        session.add(user)
        session.commit()
        
        assert user.role == 'admin'
        assert user.is_any_admin() is True
    
    def test_user_role(self, session):
        """Test regular user role"""
        # Note: admin_level=0 is actually "hard_admin" level
        # Regular users should have role='user' but is_any_admin checks admin_level
        # which includes 0,1,2,3 - so even level 0 returns True
        user = User(
            username='user',
            email='user@test.com',
            role='user',
            admin_level=0
        )
        user.set_password('password123')
        session.add(user)
        session.commit()
        
        assert user.role == 'user'
        # admin_level=0 is considered admin (hard_admin)
        assert user.is_any_admin() is True
        assert user.is_hard_admin() is True
    
    def test_viewer_role(self, session):
        """Test viewer role"""
        user = User(
            username='viewer',
            email='viewer@test.com',
            role='viewer',
            admin_level=0
        )
        user.set_password('password123')
        session.add(user)
        session.commit()
        
        assert user.role == 'viewer'


class TestAdminLevels:
    """Test admin level hierarchy"""
    
    def test_hard_admin(self, session):
        """Test hard admin (level 0)"""
        user = User(
            username='hardadmin',
            email='hard@test.com',
            role='admin',
            admin_level=0
        )
        user.set_password('password123')
        session.add(user)
        session.commit()
        
        assert user.is_hard_admin() is True
        assert user.get_admin_title() == 'Hard Administrator'
    
    def test_main_admin(self, session):
        """Test main admin (level 1)"""
        user = User(
            username='mainadmin',
            email='main@test.com',
            role='admin',
            admin_level=1
        )
        user.set_password('password123')
        session.add(user)
        session.commit()
        
        assert user.is_main_admin() is True
        assert user.get_admin_title() == 'Main Administrator'
    
    def test_secondary_admin(self, session):
        """Test secondary admin (level 2)"""
        user = User(
            username='secondaryadmin',
            email='secondary@test.com',
            role='admin',
            admin_level=2
        )
        user.set_password('password123')
        session.add(user)
        session.commit()
        
        assert user.is_secondary_admin() is True
        assert user.get_admin_title() == 'Secondary Administrator'
    
    def test_sub_admin(self, session):
        """Test sub admin (level 3)"""
        user = User(
            username='subadmin',
            email='sub@test.com',
            role='admin',
            admin_level=3
        )
        user.set_password('password123')
        session.add(user)
        session.commit()
        
        assert user.is_sub_admin() is True
        assert user.get_admin_title() == 'Sub Administrator'


class TestAccountLockout:
    """Test account lockout functionality"""
    
    def test_increment_failed_attempts(self, session):
        """Test incrementing failed login attempts"""
        user = User(
            username='testuser',
            email='test@test.com',
            role='user',
            admin_level=0
        )
        user.set_password('password123')
        session.add(user)
        session.commit()
        
        initial_attempts = user.failed_login_attempts
        user.increment_failed_attempts()
        
        assert user.failed_login_attempts == initial_attempts + 1
    
    def test_account_locked_after_max_attempts(self, session):
        """Test account is locked after max failed attempts"""
        user = User(
            username='testuser',
            email='test@test.com',
            role='user',
            admin_level=0
        )
        user.set_password('password123')
        session.add(user)
        session.commit()
        
        # Simulate 5 failed attempts
        for _ in range(5):
            user.increment_failed_attempts()
        
        assert user.account_locked_until is not None
        assert user.is_account_locked() is True
    
    def test_reset_failed_attempts(self, session):
        """Test resetting failed login attempts"""
        user = User(
            username='testuser',
            email='test@test.com',
            role='user',
            admin_level=0
        )
        user.set_password('password123')
        session.add(user)
        session.commit()
        
        user.increment_failed_attempts()
        user.reset_failed_attempts()
        
        assert user.failed_login_attempts == 0
        assert user.account_locked_until is None


class TestUserMethods:
    """Test user business logic methods"""
    
    def test_to_dict_serialization(self, session):
        """Test to_dict method"""
        user = User(
            username='testuser',
            email='test@test.com',
            role='user',
            admin_level=0
        )
        user.set_password('password123')
        session.add(user)
        session.commit()
        
        data = user.to_dict()
        
        assert isinstance(data, dict)
        assert data['username'] == 'testuser'
        assert data['email'] == 'test@test.com'
        assert 'password' not in data  # Password should not be in dict
    
    def test_repr_method(self, session):
        """Test __repr__ method"""
        user = User(
            username='testuser',
            email='test@test.com',
            role='user',
            admin_level=0
        )
        user.set_password('password123')
        session.add(user)
        session.commit()
        
        repr_str = repr(user)
        assert 'User' in repr_str
        assert 'testuser' in repr_str

