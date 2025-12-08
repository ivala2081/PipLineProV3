"""
Configuration settings for PipLine Treasury System
"""
import os
import secrets
from datetime import timedelta

# Decimal/Float type mismatch prevention
from app.services.decimal_float_fix_service import decimal_float_service


class Config:
    """Base configuration class"""
    # Enhanced SECRET_KEY generation
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_urlsafe(64)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join('static', 'uploads')
    
    # Security settings
    BULK_DELETE_CONFIRMATION_CODE = os.environ.get('BULK_DELETE_CONFIRMATION_CODE', '4561')
    
    # Enhanced security settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)  # Extended session lifetime
    REMEMBER_COOKIE_DURATION = timedelta(days=30)  # Remember me cookie duration
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'  # Changed back to 'Lax' for better compatibility
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development, will be overridden per environment
    
    # CORS Configuration - Base settings
    CORS_ORIGINS = []  # To be set per environment
    CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS = ["Content-Type", "Authorization", "X-Requested-With", "X-CSRFToken", "Accept"]
    CORS_EXPOSE_HEADERS = ["Content-Type", "Authorization"]
    CORS_SUPPORTS_CREDENTIALS = True
    CORS_MAX_AGE = 600  # 10 minutes
    
    # Enhanced file upload security
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'jpg', 'jpeg', 'png'}
    
    # Enhanced rate limiting
    RATELIMIT_STORAGE_URL = "memory://"
    RATELIMIT_DEFAULT = "200 per day; 50 per hour; 10 per minute"
    RATELIMIT_STORAGE_OPTIONS = {
        'key_prefix': 'pipeline_ratelimit'
    }
    
    # Enhanced logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/pipeline.log'
    
    # Backup Configuration
    BACKUP_ENABLED = True
    BACKUP_RETENTION_DAYS = 30  # Keep backups for 30 days
    BACKUP_SCHEDULE_TIME = '23:59'  # Schedule time in 24-hour format (HH:MM) - Daily at 23:59 local time
    
    # Redis Configuration for Caching
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_CACHE_TTL = 300  # 5 minutes default cache TTL
    REDIS_SESSION_TTL = 14400  # 4 hours session TTL
    
    # JWT Configuration (UNUSED - Application uses Flask-Login sessions)
    # Kept for potential future JWT migration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or secrets.token_urlsafe(32)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Babel Configuration for Internationalization
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_DEFAULT_TIMEZONE = 'UTC'
    BABEL_TRANSLATION_DIRECTORIES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'babel', 'locale')
    LANGUAGES = {
        'en': 'English',
        'tr': 'Türkçe'
    }
    
    # PostgreSQL Configuration - Use environment variables only
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST')
    POSTGRES_PORT = os.environ.get('POSTGRES_PORT', '5432')
    POSTGRES_DB = os.environ.get('POSTGRES_DB')
    POSTGRES_USER = os.environ.get('POSTGRES_USER')
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
    POSTGRES_SSL_MODE = os.environ.get('POSTGRES_SSL_MODE', 'prefer')
    
    # MSSQL Configuration - Use environment variables only (optional, set DATABASE_TYPE=mssql to use)
    MSSQL_HOST = os.environ.get('MSSQL_HOST')
    MSSQL_PORT = os.environ.get('MSSQL_PORT', '1433')
    MSSQL_DB = os.environ.get('MSSQL_DB')
    MSSQL_USER = os.environ.get('MSSQL_USER')
    MSSQL_PASSWORD = os.environ.get('MSSQL_PASSWORD')
    MSSQL_DRIVER = os.environ.get('MSSQL_DRIVER', 'ODBC Driver 17 for SQL Server')
    MSSQL_ENCRYPT = os.environ.get('MSSQL_ENCRYPT', 'yes')
    MSSQL_TRUST_SERVER_CERT = os.environ.get('MSSQL_TRUST_SERVER_CERT', 'no')
    
    # Database engine options will be set per environment
    # Base configuration - no database-specific settings here
    
    # Database Query Logging
    DB_QUERY_LOGGING = False  # Set to True to log all SQL queries
    DB_SLOW_QUERY_THRESHOLD = 1.0  # Log queries taking longer than 1 second
    
    # Prepared Statements (enabled by default for security)
    SQLALCHEMY_USE_PREPARED_STATEMENTS = True
    
    # Database Backup Settings
    BACKUP_ENABLED = True
    BACKUP_RETENTION_DAYS = 30
    BACKUP_SCHEDULE_HOURS = 24  # Daily backups
    
    # Database Connection Monitoring
    DB_CONNECTION_MONITORING = True
    DB_HEALTH_CHECK_INTERVAL = 300  # 5 minutes
    
    # Enhanced Database Performance Monitoring
    DB_PERFORMANCE_MONITORING = True
    DB_SLOW_QUERY_THRESHOLD = 0.5  # 500ms threshold for slow queries
    DB_CONNECTION_POOL_MONITORING = True
    DB_QUERY_CACHE_ENABLED = True
    DB_QUERY_CACHE_TTL = 600  # 10 minutes cache TTL
    
    # Database Connection Pool Metrics
    DB_POOL_METRICS_ENABLED = True
    DB_POOL_CHECKOUT_TIMEOUT = 5  # 5 seconds max wait for connection
    DB_POOL_OVERFLOW_RECOVERY = True  # Automatically recover from overflow
    
    # Redis Configuration for Advanced Caching
    REDIS_ENABLED = False  # Disabled by default, enable per environment
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DB = 0
    REDIS_PASSWORD = None
    REDIS_SSL = False
    REDIS_CACHE_TTL = 3600  # 1 hour default cache TTL
    REDIS_SESSION_TTL = 28800  # 8 hours session TTL
    
    # Background Task Processing (Celery)
    # Celery uses Redis as both broker and result backend
    # Uses different Redis DBs to separate concerns:
    # - DB 1: Celery broker (task queue)
    # - DB 2: Celery results (task results)
    CELERY_ENABLED = True
    CELERY_BROKER_URL = 'redis://localhost:6379/1'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/2'
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TIMEZONE = 'UTC'
    CELERY_ENABLE_UTC = True
    CELERY_TASK_TRACK_STARTED = True
    CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
    CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
    
    # Enhanced Security Headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdn.socket.io; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; img-src 'self' data:; font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; connect-src 'self' https://cdn.socket.io; frame-ancestors 'none';",
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
        'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    # Password Security
    PASSWORD_MIN_LENGTH = 12
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_DIGITS = True
    PASSWORD_REQUIRE_SPECIAL = True
    
    # Session Security
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = 'instance/sessions'
    SESSION_FILE_THRESHOLD = 500
    
    # Login Security
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_LOCKOUT_DURATION = 900  # 15 minutes
    PASSWORD_RESET_EXPIRY = 3600  # 1 hour

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    
    # Database configuration - SQLite is now the default for easy setup
    @staticmethod
    def get_database_uri():
        """Get database URI based on environment variables - SQLite is default"""
        if os.environ.get('DATABASE_URL'):
            db_url = os.environ.get('DATABASE_URL')
            print(f"[DB Config] Using DATABASE_URL from environment: {db_url[:50]}...")
            return db_url
        
        # Check database type (default to SQLite for easy setup)
        # Strip whitespace to handle any formatting issues
        db_type = os.environ.get('DATABASE_TYPE', 'sqlite').strip().lower() if os.environ.get('DATABASE_TYPE') else 'sqlite'
        print(f"[DB Config] Detected DATABASE_TYPE: {db_type}")
        
        if db_type == 'mssql' or db_type == 'sqlserver':
            # Build MSSQL URI from components
            host = os.environ.get('MSSQL_HOST')
            port = os.environ.get('MSSQL_PORT', '1433')
            db = os.environ.get('MSSQL_DB')
            user = os.environ.get('MSSQL_USER')
            password = os.environ.get('MSSQL_PASSWORD')
            driver = os.environ.get('MSSQL_DRIVER', 'ODBC Driver 17 for SQL Server')
            encrypt = os.environ.get('MSSQL_ENCRYPT', 'yes')
            trust_cert = os.environ.get('MSSQL_TRUST_SERVER_CERT', 'no')
            
            # Validate required environment variables
            if not all([host, db, user, password]):
                # DevelopmentConfig: fallback to SQLite if MSSQL is not configured
                import warnings
                warnings.warn(
                    "MSSQL database type is selected but MSSQL credentials are not set. "
                    "Falling back to SQLite for development. "
                    "Set MSSQL_HOST, MSSQL_DB, MSSQL_USER, MSSQL_PASSWORD in .env to use MSSQL.",
                    UserWarning
                )
                _base_dir = os.path.dirname(os.path.abspath(__file__))
                _db_path = os.path.join(_base_dir, "instance", "treasury_fresh.db")
                _db_path_normalized = _db_path.replace(os.sep, '/')
                return f'sqlite:///{_db_path_normalized}'
            
            # Build MSSQL connection string for pyodbc
            # Pyodbc driver name: replace spaces with + (no curly braces in URL)
            from urllib.parse import quote_plus
            # Driver name: replace spaces with + for URL (pyodbc will handle it)
            driver_encoded = driver.replace(' ', '+')
            # Build connection string with proper encoding
            password_encoded = quote_plus(password)
            user_encoded = quote_plus(user)
            db_uri = f"mssql+pyodbc://{user_encoded}:{password_encoded}@{host}:{port}/{db}?driver={driver_encoded}&Encrypt={encrypt}&TrustServerCertificate={trust_cert}"
            print(f"[DB Config] Built MSSQL connection string: mssql+pyodbc://{user_encoded}:***@{host}:{port}/{db}")
            return db_uri
        elif db_type == 'postgresql' or db_type == 'postgres':
            # Build PostgreSQL URI from components
            host = os.environ.get('POSTGRES_HOST')
            port = os.environ.get('POSTGRES_PORT', '5432')
            db = os.environ.get('POSTGRES_DB')
            user = os.environ.get('POSTGRES_USER')
            password = os.environ.get('POSTGRES_PASSWORD')
            ssl_mode = os.environ.get('POSTGRES_SSL_MODE', 'prefer')
            
            # Validate required environment variables
            if not all([host, db, user, password]):
                missing_vars = []
                if not host: missing_vars.append('POSTGRES_HOST')
                if not db: missing_vars.append('POSTGRES_DB')
                if not user: missing_vars.append('POSTGRES_USER')
                if not password: missing_vars.append('POSTGRES_PASSWORD')
                raise ValueError(f"Missing required PostgreSQL environment variables: {', '.join(missing_vars)}")
            
            db_uri = f"postgresql://{user}:{password}@{host}:{port}/{db}?sslmode={ssl_mode}"
            print(f"[DB Config] Built PostgreSQL connection string: postgresql://{user}:***@{host}:{port}/{db}")
            return db_uri
        elif db_type == 'sqlite':
            # SQLite fallback (only if explicitly set)
            _base_dir = os.path.dirname(os.path.abspath(__file__))
            _db_path = os.path.join(_base_dir, "instance", "treasury_fresh.db")
            
            # Ensure database directory exists with proper permissions
            _db_dir = os.path.dirname(_db_path)
            if not os.path.exists(_db_dir):
                os.makedirs(_db_dir, mode=0o755, exist_ok=True)
            
            # Convert to forward slashes for SQLite URI
            _db_path_normalized = _db_path.replace(os.sep, '/')
            db_uri = f'sqlite:///{_db_path_normalized}'
            print(f"[DB Config] Using SQLite database: {_db_path_normalized}")
            return db_uri
        else:
            # Unknown database type - default to SQLite
            raise ValueError(f"Unknown DATABASE_TYPE: {db_type}. Supported types: mssql, postgresql, sqlite")
    
    # Get the absolute path to the database file
    _base_dir = os.path.dirname(os.path.abspath(__file__))
    _db_path = os.path.join(_base_dir, "instance", "treasury_fresh.db")
    
    # Ensure database directory exists with proper permissions
    _db_dir = os.path.dirname(_db_path)
    if not os.path.exists(_db_dir):
        os.makedirs(_db_dir, mode=0o755, exist_ok=True)
    
    # Convert to forward slashes for SQLite URI and set database URI
    _db_path_normalized = _db_path.replace(os.sep, '/')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or None  # Will be set after class definition
    
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development
    
    # CORS Configuration for Development - Allow React dev servers including network access
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173,http://192.168.56.1:5173,http://0.0.0.0:5173').split(',')
    
    # Development-specific settings
    LOG_LEVEL = 'INFO'  # Changed from DEBUG to reduce verbosity
    SQLALCHEMY_ECHO = False  # Changed from True to reduce SQL logging
    
    # Database settings - optimized per database type
    @staticmethod
    def get_engine_options():
        """Get engine options based on database type - SQLite is default"""
        db_type = os.environ.get('DATABASE_TYPE', 'sqlite').lower()
        
        if db_type == 'mssql' or db_type == 'sqlserver':
            # MSSQL-optimized settings
            return {
                'pool_size': 10,
                'pool_timeout': 30,
                'pool_recycle': 3600,
                'pool_pre_ping': True,
                'max_overflow': 20,
                'echo': False,
                'connect_args': {
                    'timeout': 30,
                    'autocommit': False
                }
            }
        elif db_type == 'postgresql' or db_type == 'postgres':
            # PostgreSQL-optimized settings
            return {
                'pool_size': 10,
                'pool_timeout': 30,
                'pool_recycle': 3600,
                'pool_pre_ping': True,
                'max_overflow': 20,
                'echo': False,
                'connect_args': {
                    'application_name': 'PipLinePro-Dev',
                    'options': '-c timezone=utc'
                }
            }
        else:
            # SQLite-specific database settings for development
            return {
                'connect_args': {
                    'check_same_thread': False,
                    'timeout': 60,
                    'isolation_level': None,
                },
                'pool_pre_ping': True,
                'pool_recycle': -1,
            }
    
    SQLALCHEMY_ENGINE_OPTIONS = None  # Will be set after class definition
    
    # Disable query logging in development to reduce verbosity
    DB_QUERY_LOGGING = False
    DB_SLOW_QUERY_THRESHOLD = 1.0  # Only log queries taking longer than 1 second
    
    # Relaxed security for development
    SESSION_COOKIE_SAMESITE = 'Lax'  # Allow cross-origin requests for React frontend
    SESSION_COOKIE_DOMAIN = None  # Allow localhost
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development
    
    # CSRF Configuration for development - more lenient
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 7200  # 2 hours for development
    WTF_CSRF_SSL_STRICT = False  # Don't require HTTPS in development
    
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdn.socket.io https://cdnjs.cloudflare.com https://cdn.datatables.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://cdn.datatables.net; img-src 'self' data:; font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; connect-src 'self' https://cdn.socket.io;",
    }
    
    # Development Redis settings (disabled by default)
    REDIS_ENABLED = False  # Disable Redis in development by default
    REDIS_URL = os.environ.get('REDIS_URL') or None  # Use in-memory cache if Redis not available

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    
    # CORS Configuration for Production - Restrictive, use environment variable
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',') if os.environ.get('CORS_ORIGINS') else []
    CORS_MAX_AGE = 3600  # 1 hour for production
    
    # Database configuration - SQLite is now the default database for production
    @staticmethod
    def get_database_uri():
        """Get database URI based on environment variables - SQLite is default"""
        if os.environ.get('DATABASE_URL'):
            return os.environ.get('DATABASE_URL')
        
        # Check database type (default to SQLite)
        # Strip whitespace to handle any formatting issues
        db_type = os.environ.get('DATABASE_TYPE', 'sqlite').strip().lower() if os.environ.get('DATABASE_TYPE') else 'sqlite'
        print(f"[DB Config] Production - Detected DATABASE_TYPE: {db_type}")
        
        if db_type == 'mssql' or db_type == 'sqlserver':
            # Build MSSQL URI from components
            host = os.environ.get('MSSQL_HOST')
            port = os.environ.get('MSSQL_PORT', '1433')
            db = os.environ.get('MSSQL_DB')
            user = os.environ.get('MSSQL_USER')
            password = os.environ.get('MSSQL_PASSWORD')
            driver = os.environ.get('MSSQL_DRIVER', 'ODBC Driver 17 for SQL Server')
            encrypt = os.environ.get('MSSQL_ENCRYPT', 'yes')
            trust_cert = os.environ.get('MSSQL_TRUST_SERVER_CERT', 'no')
            
            # Validate required environment variables
            if not all([host, db, user, password]):
                missing_vars = []
                if not host: missing_vars.append('MSSQL_HOST')
                if not db: missing_vars.append('MSSQL_DB')
                if not user: missing_vars.append('MSSQL_USER')
                if not password: missing_vars.append('MSSQL_PASSWORD')
                raise ValueError(f"Missing required MSSQL environment variables: {', '.join(missing_vars)}")
            
            # Build MSSQL connection string for pyodbc
            # Pyodbc driver name: replace spaces with + (no curly braces in URL)
            from urllib.parse import quote_plus
            # Driver name: replace spaces with + for URL (pyodbc will handle it)
            driver_encoded = driver.replace(' ', '+')
            # Build connection string with proper encoding
            password_encoded = quote_plus(password)
            user_encoded = quote_plus(user)
            db_uri = f"mssql+pyodbc://{user_encoded}:{password_encoded}@{host}:{port}/{db}?driver={driver_encoded}&Encrypt={encrypt}&TrustServerCertificate={trust_cert}"
            print(f"[DB Config] Production - Built MSSQL connection string: mssql+pyodbc://{user_encoded}:***@{host}:{port}/{db}")
            return db_uri
        elif db_type == 'postgresql' or db_type == 'postgres':
            # Build PostgreSQL URI from components
            host = os.environ.get('POSTGRES_HOST')
            port = os.environ.get('POSTGRES_PORT', '5432')
            db = os.environ.get('POSTGRES_DB')
            user = os.environ.get('POSTGRES_USER')
            password = os.environ.get('POSTGRES_PASSWORD')
            ssl_mode = os.environ.get('POSTGRES_SSL_MODE', 'prefer')
            
            # Validate required environment variables
            if not all([host, db, user, password]):
                missing_vars = []
                if not host: missing_vars.append('POSTGRES_HOST')
                if not db: missing_vars.append('POSTGRES_DB')
                if not user: missing_vars.append('POSTGRES_USER')
                if not password: missing_vars.append('POSTGRES_PASSWORD')
                raise ValueError(f"Missing required PostgreSQL environment variables: {', '.join(missing_vars)}")
            
            db_uri = f"postgresql://{user}:{password}@{host}:{port}/{db}?sslmode={ssl_mode}"
            print(f"[DB Config] Production - Built PostgreSQL connection string: postgresql://{user}:***@{host}:{port}/{db}")
            return db_uri
        elif db_type == 'sqlite':
            # SQLite for production - using treasury_fresh.db with all existing data
            _base_dir = os.path.dirname(os.path.abspath(__file__))
            _db_path = os.path.join(_base_dir, "instance", "treasury_fresh.db")
            _db_path_normalized = _db_path.replace(os.sep, '/')
            db_uri = f'sqlite:///{_db_path_normalized}'
            print(f"[DB Config] Production - Using SQLite database: {_db_path_normalized}")
            return db_uri
        else:
            # Unknown database type - default to SQLite
            raise ValueError(f"Unknown DATABASE_TYPE: {db_type}. Supported types: mssql, postgresql, sqlite")
    
    # Set default database URI - will be overridden by environment variables
    # Use lazy evaluation to avoid circular reference
    _base_dir_prod = os.path.dirname(os.path.abspath(__file__))
    _db_path_prod = os.path.join(_base_dir_prod, "instance", "treasury_fresh.db")
    _db_path_prod_normalized = _db_path_prod.replace(os.sep, '/')
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or None  # Will be set after class definition
    # Production security - Cookie settings
    SESSION_COOKIE_HTTPONLY = True  # Not accessible via JavaScript
    # SESSION_COOKIE_SECURE: Set based on environment (False for HTTP, True for HTTPS)
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    SESSION_COOKIE_SAMESITE = 'Lax'  # Lax for compatibility with HTTP
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)  # Extended session time
    
    # Redis for rate limiting and caching
    # Can be enabled/disabled via environment variable
    # When disabled, uses in-memory fallback for caching and rate limiting
    REDIS_ENABLED = os.environ.get('REDIS_ENABLED', 'false').lower() == 'true'
    
    # Build REDIS_URL from environment or components
    # Supports both REDIS_URL env var and individual component vars
    _redis_url = os.environ.get('REDIS_URL')
    if not _redis_url:
        # Build from components if REDIS_URL not provided
        _redis_host = os.environ.get('REDIS_HOST', 'localhost')
        _redis_port = os.environ.get('REDIS_PORT', '6379')
        _redis_db = os.environ.get('REDIS_DB', '0')
        _redis_password = os.environ.get('REDIS_PASSWORD')
        if _redis_password:
            _redis_url = f"redis://:{_redis_password}@{_redis_host}:{_redis_port}/{_redis_db}"
        else:
            _redis_url = f"redis://{_redis_host}:{_redis_port}/{_redis_db}"
    REDIS_URL = _redis_url
    
    # Use Redis for rate limiting if enabled, otherwise fallback to memory
    # Flask-Limiter will use this URL for distributed rate limiting
    RATELIMIT_STORAGE_URL = REDIS_URL if REDIS_ENABLED else "memory://"
    
    # Production logging - Windows compatible path
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'WARNING')
    LOG_FILE = 'logs/pipelinepro.log'
    
    # Production query performance monitoring
    DB_SLOW_QUERY_THRESHOLD = 2.0  # Log queries > 2 seconds
    DB_QUERY_PERFORMANCE_TRACKING = True  # Track all query metrics
    DB_QUERY_STATS_INTERVAL = 3600  # Log stats every hour
    
    # Production database settings - optimized for SQLite (default) or PostgreSQL/MSSQL
    @staticmethod
    def get_engine_options():
        """Get engine options based on database type - SQLite is default"""
        db_type = os.environ.get('DATABASE_TYPE', 'sqlite').lower()
        
        if db_type == 'mssql' or db_type == 'sqlserver':
            # MSSQL-optimized settings
            return {
                'pool_size': 20,
                'pool_timeout': 30,
                'pool_recycle': 3600,  # 1 hour
                'pool_pre_ping': True,
                'max_overflow': 30,
                'echo': False,
                'isolation_level': 'READ_COMMITTED',
                'connect_args': {
                    'timeout': 30,
                    'autocommit': False
                }
            }
        elif db_type == 'postgresql' or db_type == 'postgres':
            # PostgreSQL-optimized settings
            return {
                'pool_size': 20,
                'pool_timeout': 30,
                'pool_recycle': 3600,  # 1 hour
                'pool_pre_ping': True,
                'max_overflow': 30,
                'echo': False,
                'isolation_level': 'READ_COMMITTED',
                'connect_args': {
                    'application_name': 'PipLinePro',
                    'options': '-c timezone=utc'
                }
            }
        else:
            # SQLite-optimized settings for production
            return {
                'connect_args': {
                    'check_same_thread': False,
                    'timeout': 60,
                    'isolation_level': None,
                },
                'pool_pre_ping': True,
                'pool_recycle': -1,
            }
    
    SQLALCHEMY_ENGINE_OPTIONS = None  # Will be set after class definition
    
    # Disable query logging in production for performance
    DB_QUERY_LOGGING = False
    DB_SLOW_QUERY_THRESHOLD = 2.0  # Log queries taking longer than 2 seconds
    
    # Enhanced backup settings for production
    BACKUP_ENABLED = True
    BACKUP_RETENTION_DAYS = 90  # Keep backups for 3 months
    BACKUP_SCHEDULE_HOURS = 12  # Twice daily backups
    
    # Enhanced security headers for production
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdn.socket.io https://cdnjs.cloudflare.com https://cdn.datatables.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://cdn.datatables.net; img-src 'self' data:; font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; connect-src 'self' https://cdn.socket.io; frame-ancestors 'none'; object-src 'none'; base-uri 'self'; form-action 'self';",
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()',
        'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
        'X-Permitted-Cross-Domain-Policies': 'none',
        'X-Download-Options': 'noopen',
        'X-DNS-Prefetch-Control': 'off'
    }
    
    # Enhanced rate limiting for production
    RATELIMIT_DEFAULT = "1000 per day; 100 per hour; 20 per minute"
    RATELIMIT_LOGIN = "5 per minute"
    RATELIMIT_API = "100 per hour"
    
    # CSRF Protection (explicitly enabled in production)
    # CSRF is inherited from base Config, but explicitly set here for clarity
    WTF_CSRF_ENABLED = True  # MUST be True in production
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour token lifetime
    WTF_CSRF_SSL_STRICT = True  # Require HTTPS for CSRF tokens in production

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
    # CORS Configuration for Testing - Permissive for tests
    CORS_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']
    
    # Test-specific settings
    LOG_LEVEL = 'ERROR'
    
    # Testing database settings (SQLite doesn't support pooling)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'echo': False,
    }
    
    # Disable backup for testing
    BACKUP_ENABLED = False
    DB_CONNECTION_MONITORING = False
    
    # Relaxed security for testing
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # No Redis for testing (use in-memory cache)
    REDIS_URL = None

# Set ProductionConfig SQLALCHEMY_DATABASE_URI and SQLALCHEMY_ENGINE_OPTIONS after class is fully defined
# This avoids circular reference error
# Set ProductionConfig SQLALCHEMY_DATABASE_URI lazily - only when ProductionConfig is actually used
# This prevents errors during development when ProductionConfig is not needed
if not ProductionConfig.SQLALCHEMY_DATABASE_URI:
        try:
            ProductionConfig.SQLALCHEMY_DATABASE_URI = (
                os.environ.get('DATABASE_URL') or 
                ProductionConfig.get_database_uri() or 
                f'sqlite:///{ProductionConfig._db_path_prod_normalized}'
            )
        except ValueError as e:
            # Database configuration error - will fail when ProductionConfig is actually used
            # Don't set it now, let it fail when ProductionConfig is actually selected
            ProductionConfig.SQLALCHEMY_DATABASE_URI = None

if not ProductionConfig.SQLALCHEMY_ENGINE_OPTIONS:
    try:
        ProductionConfig.SQLALCHEMY_ENGINE_OPTIONS = ProductionConfig.get_engine_options()
    except Exception:
        # If engine options fail, use defaults
        ProductionConfig.SQLALCHEMY_ENGINE_OPTIONS = {}

# Set DevelopmentConfig SQLALCHEMY_DATABASE_URI and SQLALCHEMY_ENGINE_OPTIONS after class is fully defined
if not DevelopmentConfig.SQLALCHEMY_DATABASE_URI:
    DevelopmentConfig.SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL') or 
        DevelopmentConfig.get_database_uri()
    )

if not DevelopmentConfig.SQLALCHEMY_ENGINE_OPTIONS:
    DevelopmentConfig.SQLALCHEMY_ENGINE_OPTIONS = DevelopmentConfig.get_engine_options()

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 