"""
Application Constants
Centralized location for all hardcoded values
"""
from typing import List, Dict

# Currency codes and symbols
CURRENCY_CODES: List[str] = ['TL', 'USD', 'EUR']
CURRENCY_SYMBOLS: Dict[str, str] = {
    'TL': '₺',
    'USD': '$',
    'EUR': '€',
    'TRY': '₺'  # Alternative code for Turkish Lira
}

# Transaction categories
TRANSACTION_CATEGORIES: List[str] = ['WD', 'DEP']
CATEGORY_LABELS: Dict[str, str] = {
    'WD': 'Withdraw',
    'DEP': 'Deposit'
}

# Payment methods (must match database codes)
PAYMENT_METHODS: List[str] = ['KK', 'NAKIT', 'HAVALE', 'EFT', 'OTHER']
PAYMENT_METHOD_LABELS: Dict[str, str] = {
    'KK': 'Credit Card',
    'NAKIT': 'Cash',
    'HAVALE': 'Wire Transfer',
    'EFT': 'Electronic Transfer',
    'OTHER': 'Other'
}

# Pagination defaults
DEFAULT_PAGE_SIZE: int = 50
MAX_PAGE_SIZE: int = 500
MIN_PAGE_SIZE: int = 1

# Date formats
DATE_FORMAT: str = '%Y-%m-%d'
DATETIME_FORMAT: str = '%Y-%m-%d %H:%M:%S'
ISO_DATE_FORMAT: str = '%Y-%m-%dT%H:%M:%S'

# Validation limits
MAX_CLIENT_NAME_LENGTH: int = 255
MAX_DESCRIPTION_LENGTH: int = 1000
MAX_AMOUNT: float = 999999999.99
MIN_AMOUNT: float = 0.01

# Rate limiting
DEFAULT_RATE_LIMIT: str = "200 per day; 50 per hour; 10 per minute"
API_RATE_LIMIT: str = "5000 per day; 1000 per hour; 200 per minute"

# Cache TTL (in seconds)
DEFAULT_CACHE_TTL: int = 3600  # 1 hour
SHORT_CACHE_TTL: int = 300     # 5 minutes
LONG_CACHE_TTL: int = 86400   # 24 hours

# File upload limits
MAX_FILE_SIZE: int = 16 * 1024 * 1024  # 16MB
ALLOWED_FILE_EXTENSIONS: List[str] = ['csv', 'xlsx', 'jpg', 'jpeg', 'png']

# Security
BULK_DELETE_CONFIRMATION_CODE: str = '4561'
SESSION_LIFETIME_HOURS: int = 8
REMEMBER_ME_DAYS: int = 30

# Exchange rate providers
EXCHANGE_RATE_PROVIDERS: List[str] = ['ExchangeRate-API', 'Fixer.io', 'CurrencyLayer']
DEFAULT_EXCHANGE_RATE_PROVIDER: str = 'ExchangeRate-API'

# Database
DEFAULT_DB_POOL_SIZE: int = 5
MAX_DB_POOL_OVERFLOW: int = 10

# Logging
DEFAULT_LOG_LEVEL: str = 'INFO'
PRODUCTION_LOG_LEVEL: str = 'WARNING'

# Analytics and Dashboard limits
MAX_REVENUE_TRENDS_DAYS: int = 365  # Maximum days for revenue trends charts
MAX_DASHBOARD_ITEMS: int = 100  # Maximum items to display in dashboard lists

