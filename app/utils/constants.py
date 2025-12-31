"""
Application-wide constants
Centralized location for magic strings and configuration values
"""
from enum import Enum


class TransactionCategory(str, Enum):
    """Transaction category constants"""
    DEPOSIT = "DEP"
    WITHDRAWAL = "WD"
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Check if value is a valid category"""
        return value in [cls.DEPOSIT.value, cls.WITHDRAWAL.value]
    
    @classmethod
    def get_all(cls) -> list[str]:
        """Get all valid category values"""
        return [cls.DEPOSIT.value, cls.WITHDRAWAL.value]


class Currency(str, Enum):
    """Currency constants"""
    TRY = "TL"  # Turkish Lira
    USD = "USD"  # US Dollar
    EUR = "EUR"  # Euro
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Check if value is a valid currency"""
        return value in [cls.TRY.value, cls.USD.value, cls.EUR.value]
    
    @classmethod
    def get_all(cls) -> list[str]:
        """Get all valid currency values"""
        return [cls.TRY.value, cls.USD.value, cls.EUR.value]


class UserRole(str, Enum):
    """User role constants"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    MANAGER = "manager"
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Check if value is a valid role"""
        return value in [cls.ADMIN.value, cls.USER.value, cls.VIEWER.value, cls.MANAGER.value]
    
    @classmethod
    def get_all(cls) -> list[str]:
        """Get all valid role values"""
        return [cls.ADMIN.value, cls.USER.value, cls.VIEWER.value, cls.MANAGER.value]


class AdminLevel(int, Enum):
    """Admin level constants"""
    USER = 0
    MAIN_ADMIN = 1
    SECONDARY_ADMIN = 2
    SUB_ADMIN = 3
    
    @classmethod
    def is_valid(cls, value: int) -> bool:
        """Check if value is a valid admin level"""
        return value in [cls.USER.value, cls.MAIN_ADMIN.value, cls.SECONDARY_ADMIN.value, cls.SUB_ADMIN.value]


# Payment method constants (common values)
class PaymentMethod:
    """Payment method constants"""
    BANK = "BANK"
    CREDIT_CARD = "KK"  # Kredi Kartı
    TETHER = "TETHER"
    USDT = "USDT"
    CASH = "CASH"
    
    @classmethod
    def get_common_methods(cls) -> list[str]:
        """Get common payment methods"""
        return [cls.BANK, cls.CREDIT_CARD, cls.TETHER, cls.USDT, cls.CASH]


# PSP (Payment Service Provider) common names
class PSP:
    """PSP constants"""
    # Common PSP names - add more as needed
    @classmethod
    def get_common_psps(cls) -> list[str]:
        """Get common PSP names"""
        return []  # Will be populated from database


# Default values
class Defaults:
    """Default configuration values"""
    PAGE_SIZE = 25
    MAX_PAGE_SIZE = 100
    DEFAULT_CURRENCY = Currency.TRY.value
    DEFAULT_CATEGORY = TransactionCategory.DEPOSIT.value
    SESSION_TIMEOUT_HOURS = 8
    REMEMBER_ME_DAYS = 30


# API Response codes
class ApiResponseCode:
    """API response code constants"""
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    RATE_LIMIT_ERROR = "RATE_LIMIT_ERROR"


# File upload constants
class FileUpload:
    """File upload constants"""
    MAX_FILE_SIZE_MB = 16
    MAX_IMAGE_SIZE_MB = 5
    MAX_EXCEL_SIZE_MB = 10
    MAX_CSV_SIZE_MB = 5
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'jpg', 'jpeg', 'png', 'gif'}


# Cache TTL constants (in seconds)
class CacheTTL:
    """Cache time-to-live constants"""
    SHORT = 60  # 1 minute
    MEDIUM = 300  # 5 minutes
    LONG = 3600  # 1 hour
    VERY_LONG = 86400  # 24 hours
    EXCHANGE_RATE = 300  # 5 minutes for exchange rates
    DASHBOARD = 60  # 1 minute for dashboard data


# Rate limiting constants
class RateLimit:
    """Rate limiting constants"""
    DEFAULT = "200 per day; 50 per hour; 10 per minute"
    LOGIN = "5 per minute"
    API = "100 per hour"
    TRANSACTION_CREATE = "30 per minute; 500 per hour"


# Database constants
class Database:
    """Database-related constants"""
    SLOW_QUERY_THRESHOLD = 1.0  # seconds
    QUERY_TIMEOUT = 30  # seconds
    CONNECTION_POOL_SIZE = 10
    MAX_OVERFLOW = 20


# Dashboard and Analytics Constants
MAX_REVENUE_TRENDS_DAYS = 365  # Maximum days for revenue trends
MAX_DASHBOARD_ITEMS = 100  # Maximum items in dashboard queries

# Pagination Constants
DEFAULT_PAGE_SIZE = 25  # Default page size for pagination
MAX_PAGE_SIZE = 100  # Maximum page size allowed
MIN_PAGE_SIZE = 1  # Minimum page size allowed
