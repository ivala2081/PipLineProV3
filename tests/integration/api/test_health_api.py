"""
Integration tests for health API endpoints
"""
import pytest
from app import create_app


@pytest.mark.integration
class TestHealthAPI:
    """Test health check API endpoints"""
    
    def test_health_check_endpoint(self, client):
        """Test basic health check endpoint"""
        response = client.get('/api/v1/health/')
        
        assert response.status_code in [200, 503]
        data = response.get_json()
        assert "data" in data or "status" in data
    
    def test_health_check_detailed_endpoint(self, client, admin_user):
        """Test detailed health check endpoint"""
        # Login first
        client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        response = client.get('/api/v1/health/detailed')
        
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data or "status" in data
    
    def test_health_check_ready_endpoint(self, client):
        """Test readiness check endpoint"""
        response = client.get('/api/v1/health/ready')
        
        assert response.status_code in [200, 503]
    
    def test_health_check_live_endpoint(self, client):
        """Test liveness check endpoint"""
        response = client.get('/api/v1/health/live')
        
        assert response.status_code in [200, 503]

