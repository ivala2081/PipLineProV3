"""
Extended integration tests for auth API
"""
import pytest


@pytest.mark.integration
@pytest.mark.auth
class TestAuthAPIExtended:
    """Extended tests for authentication API endpoints"""
    
    def test_login_success(self, client, admin_user):
        """Test successful login"""
        response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data or "token" in data or "access_token" in data
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'wrongpassword'
        })
        
        assert response.status_code in [401, 400]
        data = response.get_json()
        assert "error" in data or "message" in data
    
    def test_login_missing_fields(self, client):
        """Test login with missing fields"""
        response = client.post('/api/v1/auth/login', json={
            'username': 'admin'
        })
        
        assert response.status_code in [400, 422]
    
    def test_logout(self, client, admin_user):
        """Test logout"""
        # First login
        client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        # Then logout
        response = client.post('/api/v1/auth/logout')
        
        assert response.status_code in [200, 204]
    
    def test_get_current_user(self, client, admin_user):
        """Test getting current user"""
        # Login first
        client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        response = client.get('/api/v1/auth/me')
        
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data or "username" in data or "user" in data
    
    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without authentication"""
        response = client.get('/api/v1/auth/me')
        
        assert response.status_code in [401, 403]

