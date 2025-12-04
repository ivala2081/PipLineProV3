"""
Unit tests for input sanitizer utilities
"""
import pytest
from app.utils.input_sanitizer import (
    sanitize_client_name,
    sanitize_company_name,
    sanitize_notes,
    validate_currency,
    validate_psp_name,
    validate_payment_method,
    validate_category
)


@pytest.mark.unit
class TestSanitizeClientName:
    """Test client name sanitization"""
    
    def test_sanitize_client_name_basic(self):
        """Test basic client name sanitization"""
        result = sanitize_client_name("Test Client")
        assert result == "Test Client"
    
    def test_sanitize_client_name_whitespace(self):
        """Test whitespace trimming"""
        result = sanitize_client_name("  Test Client  ")
        assert result == "Test Client"
    
    def test_sanitize_client_name_empty(self):
        """Test empty string handling"""
        result = sanitize_client_name("")
        assert result is None
    
    def test_sanitize_client_name_special_chars(self):
        """Test special character handling"""
        result = sanitize_client_name("Client & Co.")
        assert "&" in result or result == "Client Co."


@pytest.mark.unit
class TestSanitizeCompanyName:
    """Test company name sanitization"""
    
    def test_sanitize_company_name_basic(self):
        """Test basic company name sanitization"""
        result = sanitize_company_name("Test Company")
        assert result == "Test Company"
    
    def test_sanitize_company_name_whitespace(self):
        """Test whitespace trimming"""
        result = sanitize_company_name("  Company  ")
        assert result == "Company"


@pytest.mark.unit
class TestSanitizeNotes:
    """Test notes sanitization"""
    
    def test_sanitize_notes_basic(self):
        """Test basic notes sanitization"""
        result = sanitize_notes("Test notes")
        assert result == "Test notes"
    
    def test_sanitize_notes_html(self):
        """Test HTML tag removal"""
        result = sanitize_notes("<script>alert('xss')</script>Test")
        assert "<script>" not in result
        assert "Test" in result


@pytest.mark.unit
class TestValidateCurrency:
    """Test currency validation"""
    
    def test_validate_currency_valid(self):
        """Test valid currency"""
        assert validate_currency("TRY") is True
        assert validate_currency("USD") is True
        assert validate_currency("EUR") is True
    
    def test_validate_currency_invalid(self):
        """Test invalid currency"""
        assert validate_currency("INVALID") is False
        assert validate_currency("") is False
    
    def test_validate_currency_case_insensitive(self):
        """Test case insensitive validation"""
        assert validate_currency("try") is True
        assert validate_currency("usd") is True


@pytest.mark.unit
class TestValidatePSPName:
    """Test PSP name validation"""
    
    def test_validate_psp_name_valid(self):
        """Test valid PSP name"""
        assert validate_psp_name("SIPAY") is True
        assert validate_psp_name("Test PSP") is True
        assert validate_psp_name("Test-PSP") is True
        assert validate_psp_name("Test_PSP") is True
    
    def test_validate_psp_name_empty(self):
        """Test empty PSP name (optional)"""
        assert validate_psp_name("") is True  # PSP is optional
    
    def test_validate_psp_name_invalid(self):
        """Test invalid PSP name"""
        assert validate_psp_name("A") is False  # Too short
        assert validate_psp_name("X" * 51) is False  # Too long


@pytest.mark.unit
class TestValidatePaymentMethod:
    """Test payment method validation"""
    
    def test_validate_payment_method_valid(self):
        """Test valid payment method"""
        assert validate_payment_method("KK") is True
        assert validate_payment_method("H") is True
        assert validate_payment_method("EFT") is True
    
    def test_validate_payment_method_empty(self):
        """Test empty payment method (optional)"""
        assert validate_payment_method("") is True  # Payment method is optional
    
    def test_validate_payment_method_custom(self):
        """Test custom payment method"""
        assert validate_payment_method("Custom Method") is True  # Length <= 20


@pytest.mark.unit
class TestValidateCategory:
    """Test category validation"""
    
    def test_validate_category_valid(self):
        """Test valid category"""
        assert validate_category("DEP") is True
        assert validate_category("WD") is True
        assert validate_category("DEPOSIT") is True
    
    def test_validate_category_invalid(self):
        """Test invalid category"""
        assert validate_category("INVALID") is False
        assert validate_category("") is False

