"""
Security Tests - Authorization
Critical tests for role-based access control (RBAC)
"""
import pytest
from app.models.user import User


class TestRoleBasedAccess:
    """Test role-based access control"""
    
    def test_admin_role_validation(self, session):
        """Test admin role is properly set"""
        admin = User(
            username='admin_test',
            email='admin_test@test.com',
            role='admin',
            admin_level=1
        )
        admin.set_password('password123')
        session.add(admin)
        session.commit()
        
        assert admin.role == 'admin'
        assert admin.admin_level == 1
    
    def test_user_role_validation(self, session):
        """Test user role is properly set"""
        user = User(
            username='user_test',
            email='user_test@test.com',
            role='user',
            admin_level=0
        )
        user.set_password('password123')
        session.add(user)
        session.commit()
        
        assert user.role == 'user'
        assert user.admin_level == 0
    
    def test_viewer_role_validation(self, session):
        """Test viewer role is properly set"""
        viewer = User(
            username='viewer_test',
            email='viewer_test@test.com',
            role='viewer',
            admin_level=0
        )
        viewer.set_password('password123')
        session.add(viewer)
        session.commit()
        
        assert viewer.role == 'viewer'
        assert viewer.admin_level == 0
    
    def test_invalid_role_rejected(self, session):
        """Test invalid role is rejected"""
        with pytest.raises(ValueError, match='Role must be one of'):
            user = User(
                username='invalid_role',
                email='invalid@test.com',
                role='superuser',  # Invalid role
                admin_level=0
            )
            user.set_password('password123')
            session.add(user)
            session.commit()


class TestAdminLevels:
    """Test admin level hierarchy"""
    
    def test_main_admin_level(self, session):
        """Test main admin (level 1)"""
        admin = User(
            username='main_admin',
            email='main@test.com',
            role='admin',
            admin_level=1
        )
        admin.set_password('password123')
        session.add(admin)
        session.commit()
        
        assert admin.admin_level == 1
        assert not admin.is_hard_admin()
    
    def test_hard_admin_level(self, session):
        """Test hard admin (level 0) - invisible in web"""
        hard_admin = User(
            username='hard_admin',
            email='hard@test.com',
            role='admin',
            admin_level=0
        )
        hard_admin.set_password('password123')
        session.add(hard_admin)
        session.commit()
        
        assert hard_admin.admin_level == 0
        assert hard_admin.is_hard_admin()
    
    def test_secondary_admin_level(self, session):
        """Test secondary admin (level 2)"""
        secondary_admin = User(
            username='secondary_admin',
            email='secondary@test.com',
            role='admin',
            admin_level=2
        )
        secondary_admin.set_password('password123')
        session.add(secondary_admin)
        session.commit()
        
        assert secondary_admin.admin_level == 2
    
    def test_sub_admin_level(self, session):
        """Test sub admin (level 3)"""
        sub_admin = User(
            username='sub_admin',
            email='sub@test.com',
            role='admin',
            admin_level=3
        )
        sub_admin.set_password('password123')
        session.add(sub_admin)
        session.commit()
        
        assert sub_admin.admin_level == 3
    
    def test_invalid_admin_level_rejected(self, session):
        """Test invalid admin level is rejected"""
        with pytest.raises(ValueError, match='Admin level must be 0, 1, 2, or 3'):
            user = User(
                username='invalid_level',
                email='invalid_level@test.com',
                role='admin',
                admin_level=99  # Invalid level
            )
            user.set_password('password123')
            session.add(user)
            session.commit()


class TestPermissionChecks:
    """Test permission checking methods"""
    
    def test_is_hard_admin_method(self, session):
        """Test is_hard_admin() method"""
        hard_admin = User(
            username='hard',
            email='hard@test.com',
            role='admin',
            admin_level=0
        )
        hard_admin.set_password('password123')
        session.add(hard_admin)
        
        regular_admin = User(
            username='regular',
            email='regular@test.com',
            role='admin',
            admin_level=1
        )
        regular_admin.set_password('password123')
        session.add(regular_admin)
        
        session.commit()
        
        assert hard_admin.is_hard_admin() is True
        assert regular_admin.is_hard_admin() is False
    
    def test_admin_can_create_users(self, session):
        """Test admin can create other users"""
        creator_admin = User(
            username='creator',
            email='creator@test.com',
            role='admin',
            admin_level=1
        )
        creator_admin.set_password('password123')
        session.add(creator_admin)
        session.commit()
        
        # Create user by admin
        new_user = User(
            username='created_user',
            email='created@test.com',
            role='user',
            admin_level=0,
            created_by=creator_admin.id
        )
        new_user.set_password('password123')
        session.add(new_user)
        session.commit()
        
        assert new_user.created_by == creator_admin.id
        assert new_user.creator.username == 'creator'


class TestAPIEndpointAccess:
    """Test API endpoint access based on roles"""
    
    def test_admin_can_access_admin_endpoints(self, client, admin_user):
        """Test admin can access admin-only endpoints"""
        # Login as admin
        response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        assert response.status_code == 200
        
        # Try to access admin endpoint (example: user management)
        # Note: Adjust endpoint based on actual implementation
        response = client.get('/api/v1/users/')
        # Should not be 403 Forbidden for admin
        assert response.status_code != 403
    
    def test_regular_user_cannot_access_admin_endpoints(self, client, regular_user):
        """Test regular user cannot access admin-only endpoints"""
        # Login as regular user
        response = client.post('/api/v1/auth/login', json={
            'username': 'user',
            'password': 'user123'
        })
        assert response.status_code == 200
        
        # Try to access admin endpoint
        response = client.get('/api/v1/users/')
        # Should be 403 Forbidden or 401 Unauthorized
        assert response.status_code in [401, 403]
    
    def test_unauthenticated_user_cannot_access_protected_endpoints(self, client):
        """Test unauthenticated user cannot access protected endpoints"""
        # Try to access protected endpoint without login
        response = client.get('/api/v1/transactions/')
        assert response.status_code in [401, 403]

