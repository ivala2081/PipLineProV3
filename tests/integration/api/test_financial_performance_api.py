"""
Integration tests for financial performance API
"""
import pytest


@pytest.mark.integration
@pytest.mark.financial
class TestFinancialPerformanceAPI:
    """Test financial performance API endpoints"""
    
    def test_get_financial_performance(self, client, admin_user):
        """Test getting financial performance"""
        # Login
        client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        response = client.get('/api/v1/financial-performance/')
        
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data or isinstance(data, dict)
    
    def test_get_financial_performance_with_date_range(self, client, admin_user):
        """Test getting financial performance with date range"""
        # Login
        client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        response = client.get('/api/v1/financial-performance/?start_date=2025-01-01&end_date=2025-01-31')
        
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data or isinstance(data, dict)
    
    def test_get_psp_performance(self, client, admin_user):
        """Test getting PSP performance"""
        # Login
        client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        response = client.get('/api/v1/financial-performance/psp')
        
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data or isinstance(data, dict)

