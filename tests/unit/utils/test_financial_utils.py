# Test Financial Utilities
"""
Unit tests for financial calculation utilities.
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from app.utils.financial_utils import (
    calculate_commission,
    calculate_net_amount,
    format_currency,
    convert_currency,
    calculate_daily_summary
)


@pytest.mark.unit
@pytest.mark.financial
class TestFinancialCalculations:
    """Tests for financial calculation functions."""
    
    def test_calculate_commission_percentage(self):
        """Test commission calculation with percentage."""
        amount = Decimal('1000.00')
        rate = Decimal('2.5')  # 2.5%
        
        commission = calculate_commission(amount, rate, 'percentage')
        
        assert commission == Decimal('25.00')
    
    def test_calculate_commission_fixed(self):
        """Test commission calculation with fixed amount."""
        amount = Decimal('1000.00')
        rate = Decimal('10.00')
        
        commission = calculate_commission(amount, rate, 'fixed')
        
        assert commission == Decimal('10.00')
    
    def test_calculate_commission_zero_amount(self):
        """Test commission calculation with zero amount."""
        amount = Decimal('0.00')
        rate = Decimal('2.5')
        
        commission = calculate_commission(amount, rate, 'percentage')
        
        assert commission == Decimal('0.00')
    
    def test_calculate_net_amount_deposit(self):
        """Test net amount calculation for deposit."""
        gross_amount = Decimal('1000.00')
        commission = Decimal('25.00')
        
        net = calculate_net_amount(gross_amount, commission, 'deposit')
        
        # For deposits: net = gross - commission
        assert net == Decimal('975.00')
    
    def test_calculate_net_amount_withdrawal(self):
        """Test net amount calculation for withdrawal."""
        gross_amount = Decimal('1000.00')
        commission = Decimal('25.00')
        
        net = calculate_net_amount(gross_amount, commission, 'withdrawal')
        
        # For withdrawals: net = gross + commission
        assert net == Decimal('1025.00')
    
    def test_format_currency_try(self):
        """Test TRY currency formatting."""
        amount = Decimal('1234.56')
        
        formatted = format_currency(amount, 'TRY')
        
        assert '1,234.56' in formatted or '1.234,56' in formatted
        assert '₺' in formatted or 'TRY' in formatted
    
    def test_format_currency_usd(self):
        """Test USD currency formatting."""
        amount = Decimal('1234.56')
        
        formatted = format_currency(amount, 'USD')
        
        assert '1,234.56' in formatted or '1.234,56' in formatted
        assert '$' in formatted or 'USD' in formatted
    
    def test_convert_currency(self):
        """Test currency conversion."""
        amount = Decimal('100.00')
        rate = Decimal('30.50')
        
        # Convert USD to TRY
        converted = convert_currency(amount, 'USD', 'TRY', rate)
        
        assert converted == Decimal('3050.00')
    
    def test_convert_currency_same(self):
        """Test currency conversion with same currencies."""
        amount = Decimal('100.00')
        
        # Convert TRY to TRY (should return same amount)
        converted = convert_currency(amount, 'TRY', 'TRY', Decimal('1.0'))
        
        assert converted == amount
    
    def test_convert_currency_inverse(self):
        """Test inverse currency conversion."""
        amount = Decimal('3050.00')
        rate = Decimal('30.50')
        
        # Convert TRY to USD
        converted = convert_currency(amount, 'TRY', 'USD', rate)
        
        assert converted == Decimal('100.00')


@pytest.mark.unit
@pytest.mark.financial
class TestDailySummary:
    """Tests for daily summary calculations."""
    
    def test_calculate_daily_summary_empty(self):
        """Test daily summary with no transactions."""
        transactions = []
        
        summary = calculate_daily_summary(transactions, datetime.now().date())
        
        assert summary['total_deposits'] == Decimal('0.00')
        assert summary['total_withdrawals'] == Decimal('0.00')
        assert summary['net_amount'] == Decimal('0.00')
    
    def test_calculate_daily_summary_deposits_only(self, multiple_transactions):
        """Test daily summary with only deposits."""
        # Filter deposit transactions
        deposits = [t for t in multiple_transactions if t.type == 'deposit']
        
        summary = calculate_daily_summary(deposits, datetime.now().date())
        
        assert summary['total_deposits'] > Decimal('0.00')
        assert summary['total_withdrawals'] == Decimal('0.00')
        assert summary['net_amount'] == summary['total_deposits']
    
    def test_calculate_daily_summary_mixed(self, multiple_transactions):
        """Test daily summary with mixed transaction types."""
        summary = calculate_daily_summary(
            multiple_transactions,
            datetime.now().date()
        )
        
        assert 'total_deposits' in summary
        assert 'total_withdrawals' in summary
        assert 'net_amount' in summary
        assert isinstance(summary['total_deposits'], Decimal)

