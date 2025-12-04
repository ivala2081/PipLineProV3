"""
Integration tests for performance API endpoints
"""
import pytest


@pytest.mark.integration
class TestPerformanceAPI:
    """Test performance API endpoints"""
    
    def test_get_performance_metrics(self, client, admin_user):
        """Test getting performance metrics"""
        # Login
        client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        response = client.get('/api/v1/performance/metrics')
        
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data or isinstance(data, dict)
    
    def test_get_cache_stats(self, client, admin_user):
        """Test getting cache statistics"""
        # Login
        client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        response = client.get('/api/v1/performance/cache/stats')
        
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data or isinstance(data, dict)
    
    def test_clear_cache(self, client, admin_user):
        """Test clearing cache"""
        # Login
        client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        response = client.post('/api/v1/performance/cache/clear')
        
        assert response.status_code in [200, 201]
        data = response.get_json()
        assert "data" in data or "message" in data or "success" in data

