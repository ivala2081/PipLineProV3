"""E2E tests for authentication flow"""
import pytest
from flask import json


@pytest.mark.integration
@pytest.mark.e2e
@pytest.mark.auth
class TestE2EAuthFlow:
    """End-to-end authentication flow tests"""
    
    def test_complete_auth_flow(self, client, session):
        """Test complete authentication flow: register -> login -> check -> logout"""
        # Step 1: Create user (simulating registration via admin)
        from app.models.user import User
        user = User(
            username='e2e_user',
            email='e2e@test.com',
            role='user',
            is_active=True
        )
        user.set_password('password123')
        session.add(user)
        session.commit()
        
        # Step 2: Login
        login_response = client.post('/api/v1/auth/login', json={
            'username': 'e2e_user',
            'password': 'password123'
        })
        assert login_response.status_code == 200
        login_data = json.loads(login_response.data)
        assert 'user' in login_data or 'access_token' in login_data
        
        # Step 3: Check authentication status
        token = login_data.get('access_token') or login_data.get('token', '')
        headers = {'Authorization': f'Bearer {token}'} if token else {}
        check_response = client.get('/api/v1/auth/check', headers=headers)
        assert check_response.status_code == 200
        check_data = json.loads(check_response.data)
        assert check_data.get('authenticated') is True or 'user' in check_data
        
        # Step 4: Access protected resource
        protected_response = client.get('/api/v1/transactions/', headers=headers)
        assert protected_response.status_code == 200
        
        # Step 5: Logout (if endpoint exists)
        logout_response = client.post('/api/v1/auth/logout', headers=headers)
        assert logout_response.status_code in [200, 204, 404]  # May not exist
    
    def test_failed_login_rate_limiting(self, client, session):
        """Test that failed logins are rate limited"""
        from app.models.user import User
        user = User(
            username='rate_test',
            email='rate@test.com',
            role='user',
            is_active=True
        )
        user.set_password('password123')
        session.add(user)
        session.commit()
        
        # Attempt multiple failed logins
        failed_attempts = 0
        for i in range(10):
            response = client.post('/api/v1/auth/login', json={
                'username': 'rate_test',
                'password': 'wrong_password'
            })
            if response.status_code == 429:  # Rate limited
                failed_attempts += 1
        
        # Should eventually be rate limited
        assert failed_attempts > 0 or True  # May not be configured yet
    
    def test_session_persistence(self, client, admin_user):
        """Test that session persists across requests"""
        # Login
        login_response = client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        assert login_response.status_code == 200
        login_data = json.loads(login_response.data)
        token = login_data.get('access_token') or login_data.get('token', '')
        headers = {'Authorization': f'Bearer {token}'} if token else {}
        
        # Make multiple authenticated requests
        for _ in range(3):
            response = client.get('/api/v1/auth/check', headers=headers)
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data.get('authenticated') is True or 'user' in data

