"""
Integration tests for analytics API endpoints
"""
import pytest


@pytest.mark.integration
@pytest.mark.analytics
class TestAnalyticsAPI:
    """Test analytics API endpoints"""
    
    def test_get_dashboard_stats(self, client, admin_user):
        """Test getting dashboard statistics"""
        # Login
        client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        response = client.get('/api/v1/analytics/dashboard/stats')
        
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data or isinstance(data, dict)
    
    def test_get_dashboard_stats_with_range(self, client, admin_user):
        """Test getting dashboard stats with time range"""
        # Login
        client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        response = client.get('/api/v1/analytics/dashboard/stats?range=month')
        
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data or isinstance(data, dict)
    
    def test_get_system_performance(self, client, admin_user):
        """Test getting system performance"""
        # Login
        client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        response = client.get('/api/v1/analytics/system/performance')
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, dict)

