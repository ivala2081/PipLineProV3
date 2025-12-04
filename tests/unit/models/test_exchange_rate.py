"""
Unit tests for ExchangeRate model
"""
import pytest
from datetime import date
from decimal import Decimal
from app.models.exchange_rate import ExchangeRate


@pytest.mark.unit
@pytest.mark.database
class TestExchangeRateModel:
    """Test ExchangeRate model"""
    
    def test_exchange_rate_creation(self, session):
        """Test creating exchange rate"""
        rate = ExchangeRate(
            currency_pair='USDTRY',
            rate=Decimal('34.50'),
            is_active=True
        )
        session.add(rate)
        session.commit()
        
        assert rate.currency_pair == 'USDTRY'
        assert rate.rate == Decimal('34.50')
        assert rate.is_active is True
    
    def test_exchange_rate_date(self, session):
        """Test exchange rate date"""
        test_date = date(2025, 1, 1)
        rate = ExchangeRate(
            currency_pair='EURTRY',
            rate=Decimal('37.20'),
            date_value=test_date,
            is_active=True
        )
        session.add(rate)
        session.commit()
        
        assert rate.date == test_date
    
    def test_exchange_rate_inactive(self, session):
        """Test inactive exchange rate"""
        rate = ExchangeRate(
            currency_pair='USDTRY',
            rate=Decimal('34.50'),
            is_active=False
        )
        session.add(rate)
        session.commit()
        
        assert rate.is_active is False
    
    def test_exchange_rate_source(self, session):
        """Test exchange rate source"""
        rate = ExchangeRate(
            currency_pair='USDTRY',
            rate=Decimal('34.50'),
            is_active=True,
            source='yfinance'
        )
        session.add(rate)
        session.commit()
        
        assert rate.source == 'yfinance'
    
    def test_exchange_rate_created_at(self, session):
        """Test exchange rate created_at timestamp"""
        rate = ExchangeRate(
            currency_pair='USDTRY',
            rate=Decimal('34.50'),
            is_active=True
        )
        session.add(rate)
        session.commit()
        
        assert rate.created_at is not None

