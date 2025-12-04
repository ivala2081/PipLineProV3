"""
Integration tests for exchange rates API endpoints
"""
import pytest
from app import create_app
from app.models.config import ExchangeRate
from decimal import Decimal
from datetime import date


@pytest.mark.integration
@pytest.mark.database
class TestExchangeRatesAPI:
    """Test exchange rates API endpoints"""
    
    def test_get_current_rates(self, client, admin_user, session):
        """Test getting current exchange rates"""
        # Create test exchange rate
        rate = ExchangeRate(
            currency='USD',
            rate=Decimal('30.5000'),
            date=date.today()
        )
        session.add(rate)
        session.commit()
        
        # Login
        client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        response = client.get('/api/v1/exchange-rates/current')
        
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data or isinstance(data, dict)
    
    def test_get_rates_history(self, client, admin_user, session):
        """Test getting exchange rate history"""
        # Create test rates
        for i in range(3):
            rate = ExchangeRate(
                currency='USD',
                rate=Decimal(f'30.{5000+i}'),
                date=date.today()
            )
            session.add(rate)
        session.commit()
        
        # Login
        client.post('/api/v1/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        
        response = client.get('/api/v1/exchange-rates/history?currency=USD')
        
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data or isinstance(data, list)

