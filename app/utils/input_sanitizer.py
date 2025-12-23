"""
Input Sanitization Utilities
Provides secure input sanitization and validation functions
"""

import re
import bleach
from typing import Optional


def sanitize_client_name(name: Optional[str]) -> Optional[str]:
    """
    Sanitize client name input
    - Remove dangerous characters
    - Trim whitespace
    - Limit length
    """
    if not name:
        return None
    
    # Clean and trim
    name = str(name).strip()
    
    # Remove HTML tags
    name = bleach.clean(name, tags=[], strip=True)
    
    # Limit length
    name = name[:255]
    
    return name if name else None


def sanitize_company_name(company: Optional[str]) -> Optional[str]:
    """Sanitize company name input"""
    if not company:
        return None
    
    company = str(company).strip()
    company = bleach.clean(company, tags=[], strip=True)
    company = company[:255]
    
    return company if company else None


def sanitize_notes(notes: Optional[str]) -> Optional[str]:
    """
    Sanitize notes/description input
    - Remove dangerous HTML
    - Allow basic formatting
    - Limit length
    """
    if not notes:
        return None
    
    notes = str(notes).strip()
    
    # Allow basic text, remove scripts and dangerous tags
    notes = bleach.clean(
        notes,
        tags=[],  # No HTML tags allowed
        strip=True
    )
    
    # Limit length
    notes = notes[:1000]
    
    return notes if notes else None


def validate_category(category: str) -> str:
    """
    Validate and normalize transaction category
    Allowed: DEP (Deposit), WD (Withdraw)
    Returns normalized category code ('DEP' or 'WD') or None if invalid
    """
    if not category:
        return None
    
    category_upper = str(category).upper().strip()
    
    # Normalize full names to codes
    if category_upper in ['DEPOSIT', 'DEP']:
        return 'DEP'
    elif category_upper in ['WITHDRAW', 'WD']:
        return 'WD'
    
    return None


def validate_currency(currency: str) -> str:
    """
    Validate and normalize currency code
    Allowed: TL (not TRY), USD, EUR, GBP, etc.
    Returns normalized currency code or None if invalid
    """
    if not currency:
        return None
    
    currency_upper = str(currency).upper().strip()
    
    # PipLine uses 'TL' instead of 'TRY'
    if currency_upper == 'TRY':
        currency_upper = 'TL'
    
    # Common currency codes (ISO 4217) + TL
    valid_currencies = [
        'TL', 'USD', 'EUR', 'GBP', 'JPY', 'CHF', 
        'CAD', 'AUD', 'NZD', 'CNY', 'INR', 'RUB',
        'BRL', 'ZAR', 'MXN', 'SGD', 'HKD', 'NOK',
        'SEK', 'DKK', 'PLN', 'THB', 'MYR', 'IDR'
    ]
    
    if currency_upper in valid_currencies:
        return currency_upper
    return None


def validate_psp_name(psp: Optional[str]) -> Optional[str]:
    """
    Validate and sanitize PSP (Payment Service Provider) name
    - Very permissive validation - only strips whitespace and limits length
    - Allows most characters to support various PSP naming conventions
    - Length 1-100 characters (increased from 50)
    Returns sanitized PSP name or None if invalid (None is valid for optional PSP)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if not psp:
        logger.debug("PSP validation: Empty/None value provided, returning None")
        return None  # PSP is optional
    
    psp_clean = str(psp).strip()
    
    # If after stripping it's empty, return None
    if not psp_clean:
        logger.debug("PSP validation: Value is empty after stripping, returning None")
        return None
    
    # Very permissive length check - allow up to 100 characters
    if len(psp_clean) < 1 or len(psp_clean) > 100:
        logger.warning(f"PSP validation: Length check failed for '{psp_clean}' (length: {len(psp_clean)})")
        return None
    
    # Very permissive validation - only block obviously dangerous characters
    # Allow most printable characters except control characters and null bytes
    # This allows #, spaces, Turkish characters, etc.
    if '\x00' in psp_clean:
        logger.warning(f"PSP validation: Null byte found in '{psp_clean}'")
        return None
    
    # Remove any control characters but keep the rest
    import string
    # Keep printable characters and common whitespace
    psp_clean = ''.join(char for char in psp_clean if char.isprintable() or char in string.whitespace)
    psp_clean = psp_clean.strip()
    
    if not psp_clean:
        logger.warning(f"PSP validation: After cleaning, value is empty")
        return None
    
    logger.debug(f"PSP validation: Successfully validated '{psp_clean}'")
    return psp_clean


def validate_payment_method(method: Optional[str]) -> str:
    """
    Validate and normalize payment method code
    Common methods: KK (Credit Card), H (Cash), EFT, etc.
    Returns normalized payment method or None if invalid (None is valid for optional method)
    """
    if not method:
        return None  # Payment method is optional
    
    method_upper = str(method).upper().strip()
    
    # Common payment method codes
    valid_methods = [
        'KK',      # Kredi Kartı (Credit Card)
        'H',       # Havale (Wire Transfer)
        'N',       # Nakit (Cash)
        'EFT',     # Electronic Fund Transfer
        'BANKA',   # Bank
        'TETHER',  # Tether
        'CRYPTO',  # Cryptocurrency
        'CHECK',   # Check
        'OTHER'    # Other
    ]
    
    # Return normalized method if valid, or allow custom methods up to 20 chars
    if method_upper in valid_methods or len(method_upper) <= 20:
        return method_upper
    return None


def sanitize_iban(iban: Optional[str]) -> Optional[str]:
    """
    Sanitize IBAN (International Bank Account Number)
    - Remove spaces and dashes
    - Convert to uppercase
    - Basic format validation
    """
    if not iban:
        return None
    
    iban = str(iban).strip()
    
    # Remove spaces and dashes
    iban = iban.replace(' ', '').replace('-', '')
    
    # Convert to uppercase
    iban = iban.upper()
    
    # Basic validation (should start with 2 letters, followed by digits)
    if not re.match(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]+$', iban):
        return None
    
    # Limit length (IBAN is typically 15-34 characters)
    if len(iban) < 15 or len(iban) > 34:
        return None
    
    return iban


def sanitize_generic_text(text: Optional[str], max_length: int = 255) -> Optional[str]:
    """
    Generic text sanitization
    - Remove HTML
    - Trim whitespace
    - Limit length
    """
    if not text:
        return None
    
    text = str(text).strip()
    text = bleach.clean(text, tags=[], strip=True)
    text = text[:max_length]
    
    return text if text else None


def validate_numeric_string(value: Optional[str]) -> bool:
    """
    Validate if string is a valid number
    """
    if not value:
        return False
    
    try:
        float(str(value).replace(',', ''))
        return True
    except (ValueError, TypeError):
        return False

