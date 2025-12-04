"""
Extended unit tests for financial utilities
"""
import pytest
from decimal import Decimal, InvalidOperation
from app.utils.financial_utils import (
    safe_decimal,
    safe_divide,
    to_float
)


@pytest.mark.unit
@pytest.mark.financial
class TestSafeDecimal:
    """Test safe_decimal function"""
    
    def test_safe_decimal_string(self):
        """Test safe_decimal with string"""
        result = safe_decimal("100.50")
        assert result == Decimal("100.50")
    
    def test_safe_decimal_float(self):
        """Test safe_decimal with float"""
        result = safe_decimal(100.50)
        assert result == Decimal("100.50")
    
    def test_safe_decimal_decimal(self):
        """Test safe_decimal with Decimal"""
        value = Decimal("100.50")
        result = safe_decimal(value)
        assert result == value
    
    def test_safe_decimal_invalid(self):
        """Test safe_decimal with invalid input"""
        result = safe_decimal("invalid")
        assert result == Decimal("0")
    
    def test_safe_decimal_none(self):
        """Test safe_decimal with None"""
        result = safe_decimal(None)
        assert result == Decimal("0")
    
    def test_safe_decimal_empty_string(self):
        """Test safe_decimal with empty string"""
        result = safe_decimal("")
        assert result == Decimal("0")


@pytest.mark.unit
@pytest.mark.financial
class TestSafeDivide:
    """Test safe_divide function"""
    
    def test_safe_divide_normal(self):
        """Test safe_divide with normal division"""
        result = safe_divide(Decimal("100"), Decimal("2"))
        assert result == Decimal("50")
    
    def test_safe_divide_by_zero(self):
        """Test safe_divide by zero"""
        result = safe_divide(Decimal("100"), Decimal("0"))
        assert result == Decimal("0")
    
    def test_safe_divide_none_numerator(self):
        """Test safe_divide with None numerator"""
        result = safe_divide(None, Decimal("2"))
        assert result == Decimal("0")
    
    def test_safe_divide_none_denominator(self):
        """Test safe_divide with None denominator"""
        result = safe_divide(Decimal("100"), None)
        assert result == Decimal("0")
    
    def test_safe_divide_decimal_strings(self):
        """Test safe_divide with string inputs"""
        result = safe_divide("100", "2")
        assert result == Decimal("50")


@pytest.mark.unit
@pytest.mark.financial
class TestToFloat:
    """Test to_float function"""
    
    def test_to_float_decimal(self):
        """Test to_float with Decimal"""
        result = to_float(Decimal("100.50"))
        assert result == 100.50
    
    def test_to_float_string(self):
        """Test to_float with string"""
        result = to_float("100.50")
        assert result == 100.50
    
    def test_to_float_float(self):
        """Test to_float with float"""
        result = to_float(100.50)
        assert result == 100.50
    
    def test_to_float_none(self):
        """Test to_float with None"""
        result = to_float(None)
        assert result == 0.0
    
    def test_to_float_invalid(self):
        """Test to_float with invalid input"""
        result = to_float("invalid")
        assert result == 0.0

