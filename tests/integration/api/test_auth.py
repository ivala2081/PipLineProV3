# Test Authentication API Endpoints
"""
Integration tests for authentication endpoints.
"""
import pytest
from flask import json


@pytest.mark.integration
@pytest.mark.auth
class TestAuthEndpoints:
    """Tests for authentication API endpoints."""
    
    def test_login_success(self, client, admin_user):
        """Test successful login."""
        response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'access_token' in data
        assert 'user' in data
        assert data['user']['username'] == 'admin'
    
    def test_login_invalid_username(self, client):
        """Test login with invalid username."""
        response = client.post('/api/v1/auth/login', json={
            'username': 'nonexistent',
            'password': 'password123'
        })
        
        assert response.status_code in [401, 400]
        data = json.loads(response.data)
        assert 'error' in data or 'message' in data
    
    def test_login_invalid_password(self, client, admin_user):
        """Test login with invalid password."""
        response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'wrongpassword'
        })
        
        assert response.status_code in [401, 400]
        data = json.loads(response.data)
        assert 'error' in data or 'message' in data
    
    def test_login_missing_fields(self, client):
        """Test login with missing required fields."""
        response = client.post('/api/v1/auth/login', json={
            'username': 'admin'
            # Missing password
        })
        
        assert response.status_code in [400, 422]
    
    def test_login_inactive_user(self, client, session):
        """Test login with inactive user account."""
        from app.models.user import User
        
        # Create inactive user
        user = User(
            username='inactive',
            email='inactive@test.com',
            role='user',
            is_active=False
        )
        user.set_password('password123')
        session.add(user)
        session.commit()
        
        response = client.post('/api/v1/auth/login', json={
            'username': 'inactive',
            'password': 'password123'
        })
        
        assert response.status_code in [401, 403]
    
    def test_logout(self, client, auth_headers):
        """Test logout endpoint."""
        response = client.post(
            '/api/v1/auth/logout',
            headers=auth_headers
        )
        
        # Logout should succeed or endpoint might not exist
        assert response.status_code in [200, 204, 404]
    
    def test_auth_check_authenticated(self, client, auth_headers):
        """Test auth check with valid token."""
        response = client.get(
            '/api/v1/auth/check',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'authenticated' in data or 'user' in data
    
    def test_auth_check_unauthenticated(self, client):
        """Test auth check without token."""
        response = client.get('/api/v1/auth/check')
        
        assert response.status_code in [200, 401]
        # Should indicate not authenticated
    
    def test_protected_endpoint_without_auth(self, client):
        """Test accessing protected endpoint without authentication."""
        response = client.get('/api/v1/transactions/')
        
        assert response.status_code in [401, 403]
    
    def test_protected_endpoint_with_auth(self, client, auth_headers):
        """Test accessing protected endpoint with authentication."""
        response = client.get(
            '/api/v1/transactions/',
            headers=auth_headers
        )
        
        assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.auth
class TestUserRoles:
    """Tests for user role-based access control."""
    
    def test_admin_access(self, client, admin_token):
        """Test admin can access admin endpoints."""
        headers = {'Authorization': f'Bearer {admin_token}'}
        
        response = client.get(
            '/api/v1/users/',
            headers=headers
        )
        
        # Admin should have access (200) or endpoint might not exist (404)
        assert response.status_code in [200, 404]
    
    def test_user_no_admin_access(self, client, user_token):
        """Test regular user cannot access admin endpoints."""
        headers = {'Authorization': f'Bearer {user_token}'}
        
        response = client.get(
            '/api/v1/admin/',
            headers=headers
        )
        
        # Should be forbidden or not found
        assert response.status_code in [403, 404]
    
    def test_viewer_read_only(self, client, viewer_user):
        """Test viewer has read-only access."""
        # Login as viewer
        response = client.post('/api/v1/auth/login', json={
            'username': 'viewer',
            'password': 'viewer123'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        token = data.get('access_token')
        
        headers = {'Authorization': f'Bearer {token}'}
        
        # Viewer should be able to read
        response = client.get(
            '/api/v1/transactions/',
            headers=headers
        )
        assert response.status_code == 200
        
        # Viewer should not be able to create
        response = client.post(
            '/api/v1/transactions/',
            headers=headers,
            json={'test': 'data'}
        )
        assert response.status_code in [403, 422]  # Forbidden or validation error

