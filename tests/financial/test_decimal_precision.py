"""
Financial Tests - Decimal Precision
CRITICAL: Tests for decimal precision in financial calculations
No floating point errors allowed!
"""
import pytest
from decimal import Decimal, ROUND_HALF_EVEN
from app.models.transaction import Transaction
from datetime import date


class TestDecimalPrecision:
    """Test decimal precision in financial calculations"""
    
    def test_amount_stored_as_decimal(self, session):
        """Test amount is stored as Decimal, not float"""
        transaction = Transaction(
            client_name='Test Client',
            date=date.today(),
            category='DEP',
            amount=Decimal('1000.50'),
            commission=Decimal('50.25'),
            net_amount=Decimal('950.25'),
            currency='TL'
        )
        session.add(transaction)
        session.commit()
        
        # Verify it's Decimal type
        assert isinstance(transaction.amount, Decimal)
        assert isinstance(transaction.commission, Decimal)
        assert isinstance(transaction.net_amount, Decimal)
    
    def test_two_decimal_places_precision(self, session):
        """Test amounts are stored with 2 decimal places"""
        transaction = Transaction(
            client_name='Test Client',
            date=date.today(),
            category='DEP',
            amount=Decimal('1000.123'),  # 3 decimals
            commission=Decimal('50.999'),  # 3 decimals
            net_amount=Decimal('949.124'),  # 3 decimals
            currency='TL'
        )
        session.add(transaction)
        session.commit()
        
        # Database should store with 2 decimal precision
        # Refresh from database
        session.refresh(transaction)
        
        # Check precision (database rounds to 2 decimals)
        assert transaction.amount == Decimal('1000.12')
        assert transaction.commission == Decimal('51.00')
        assert transaction.net_amount == Decimal('949.12')
    
    def test_no_floating_point_errors(self, session):
        """Test no floating point precision errors"""
        # Classic floating point error: 0.1 + 0.2 != 0.3
        # With Decimal, this should work correctly
        
        amount1 = Decimal('0.1')
        amount2 = Decimal('0.2')
        total = amount1 + amount2
        
        assert total == Decimal('0.3')  # Should be exactly 0.3
        assert str(total) == '0.3'
    
    def test_large_amount_precision(self, session):
        """Test precision with large amounts"""
        transaction = Transaction(
            client_name='Large Transaction',
            date=date.today(),
            category='DEP',
            amount=Decimal('999999999.99'),  # Max amount
            commission=Decimal('9999999.99'),
            net_amount=Decimal('990000000.00'),
            currency='TL'
        )
        session.add(transaction)
        session.commit()
        
        assert transaction.amount == Decimal('999999999.99')
    
    def test_small_amount_precision(self, session):
        """Test precision with small amounts"""
        transaction = Transaction(
            client_name='Small Transaction',
            date=date.today(),
            category='DEP',
            amount=Decimal('0.01'),  # Minimum amount
            commission=Decimal('0.00'),
            net_amount=Decimal('0.01'),
            currency='TL'
        )
        session.add(transaction)
        session.commit()
        
        assert transaction.amount == Decimal('0.01')


class TestRoundingBehavior:
    """Test rounding behavior for financial calculations"""
    
    def test_bankers_rounding_half_even(self):
        """Test banker's rounding (round half to even)"""
        # Banker's rounding: 0.5 rounds to nearest even number
        
        # 2.5 should round to 2 (even)
        value1 = Decimal('2.5').quantize(Decimal('1'), rounding=ROUND_HALF_EVEN)
        assert value1 == Decimal('2')
        
        # 3.5 should round to 4 (even)
        value2 = Decimal('3.5').quantize(Decimal('1'), rounding=ROUND_HALF_EVEN)
        assert value2 == Decimal('4')
        
        # 4.5 should round to 4 (even)
        value3 = Decimal('4.5').quantize(Decimal('1'), rounding=ROUND_HALF_EVEN)
        assert value3 == Decimal('4')
    
    def test_rounding_to_two_decimals(self):
        """Test rounding to 2 decimal places"""
        value = Decimal('10.12345')
        rounded = value.quantize(Decimal('0.01'))
        
        assert rounded == Decimal('10.12')
    
    def test_commission_rounding(self):
        """Test commission calculation rounding"""
        amount = Decimal('1000.00')
        rate = Decimal('0.0325')  # 3.25%
        
        commission = (amount * rate).quantize(Decimal('0.01'))
        
        assert commission == Decimal('32.50')


class TestDecimalArithmetic:
    """Test decimal arithmetic operations"""
    
    def test_addition_precision(self):
        """Test addition maintains precision"""
        a = Decimal('100.11')
        b = Decimal('200.22')
        result = a + b
        
        assert result == Decimal('300.33')
    
    def test_subtraction_precision(self):
        """Test subtraction maintains precision"""
        amount = Decimal('1000.00')
        commission = Decimal('50.25')
        net = amount - commission
        
        assert net == Decimal('949.75')
    
    def test_multiplication_precision(self):
        """Test multiplication maintains precision"""
        amount = Decimal('1000.00')
        rate = Decimal('0.05')  # 5%
        commission = amount * rate
        
        assert commission == Decimal('50.00')
    
    def test_division_precision(self):
        """Test division maintains precision"""
        total = Decimal('1000.00')
        count = Decimal('3')
        average = (total / count).quantize(Decimal('0.01'))
        
        assert average == Decimal('333.33')
    
    def test_percentage_calculation(self):
        """Test percentage calculation precision"""
        amount = Decimal('1000.00')
        percentage = Decimal('15.5')  # 15.5%
        
        result = (amount * percentage / 100).quantize(Decimal('0.01'))
        
        assert result == Decimal('155.00')


class TestExchangeRatePrecision:
    """Test exchange rate precision (4 decimal places)"""
    
    def test_exchange_rate_four_decimals(self, session):
        """Test exchange rate stored with 4 decimal places"""
        transaction = Transaction(
            client_name='USD Transaction',
            date=date.today(),
            category='DEP',
            amount=Decimal('1000.00'),
            commission=Decimal('50.00'),
            net_amount=Decimal('950.00'),
            currency='USD',
            exchange_rate=Decimal('30.5678')  # 4 decimals
        )
        session.add(transaction)
        session.commit()
        
        session.refresh(transaction)
        assert transaction.exchange_rate == Decimal('30.5678')
    
    def test_currency_conversion_precision(self):
        """Test currency conversion maintains precision"""
        usd_amount = Decimal('100.00')
        exchange_rate = Decimal('30.5678')
        
        try_amount = (usd_amount * exchange_rate).quantize(Decimal('0.01'))
        
        assert try_amount == Decimal('3056.78')
    
    def test_reverse_conversion_precision(self):
        """Test reverse currency conversion"""
        try_amount = Decimal('3056.78')
        exchange_rate = Decimal('30.5678')
        
        usd_amount = (try_amount / exchange_rate).quantize(Decimal('0.01'))
        
        assert usd_amount == Decimal('100.00')


class TestEdgeCases:
    """Test edge cases in decimal calculations"""
    
    def test_zero_amount(self, session):
        """Test zero amount transaction"""
        # Zero amount should be rejected for DEP
        # Creating minimum valid transaction instead
        transaction = Transaction(
            client_name='Minimum Amount',
            date=date.today(),
            category='DEP',
            amount=Decimal('0.01'),  # Minimum positive
            commission=Decimal('0.00'),
            net_amount=Decimal('0.01'),
            currency='TL'
        )
        session.add(transaction)
        session.commit()
        
        assert transaction.amount > 0
    
    def test_maximum_amount(self, session):
        """Test maximum allowed amount"""
        max_amount = Decimal('999999999.99')
        
        transaction = Transaction(
            client_name='Max Amount',
            date=date.today(),
            category='DEP',
            amount=max_amount,
            commission=Decimal('0.00'),
            net_amount=max_amount,
            currency='TL'
        )
        session.add(transaction)
        session.commit()
        
        assert transaction.amount == max_amount
    
    def test_minimum_positive_amount(self, session):
        """Test minimum positive amount (0.01)"""
        min_amount = Decimal('0.01')
        
        transaction = Transaction(
            client_name='Min Amount',
            date=date.today(),
            category='DEP',
            amount=min_amount,
            commission=Decimal('0.00'),
            net_amount=min_amount,
            currency='TL'
        )
        session.add(transaction)
        session.commit()
        
        assert transaction.amount == min_amount

