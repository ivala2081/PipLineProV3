"""
PipLinePro - Treasury Management System
Main application entry point
"""
import os
import sys
from pathlib import Path

# Configure logging level early (using unified logger)
import logging

# Load environment variables from .env files
try:
    from dotenv import load_dotenv
    # Load environment-specific .env file first
    env_file = Path('.env.development') if os.getenv('FLASK_ENV') == 'development' else Path('.env')
    if env_file.exists():
        load_dotenv(env_file)
        print(f"Environment variables loaded from {env_file}")
    elif Path('.env').exists():
        load_dotenv('.env')
        print("Environment variables loaded from .env")

    else:
        print("INFO: No .env file found, using system environment variables")
except ImportError:
    print("INFO: python-dotenv not available, using system environment variables")

# Configure logging level based on environment
# In production, default to WARNING to reduce verbosity
default_log_level = 'WARNING' if os.getenv('FLASK_ENV') == 'production' else 'INFO'
log_level = os.getenv('LOG_LEVEL', default_log_level)
numeric_level = getattr(logging, log_level.upper(), logging.WARNING if os.getenv('FLASK_ENV') == 'production' else logging.INFO)
logging.basicConfig(level=numeric_level)
print(f"Logging level set to: {log_level}")

def setup_development_environment():
    """Set up development environment variables"""
    # Set development environment
    os.environ['FLASK_ENV'] = 'development'
    os.environ['DEBUG'] = 'True'
    
    # SECRET_KEY should NEVER be hardcoded in production
    # For development only, use a generated key or require it in .env
    if not os.environ.get('SECRET_KEY'):
        # Generate a development key on the fly
        import secrets
        dev_key = secrets.token_urlsafe(32)
        print(f"WARNING: Using auto-generated development SECRET_KEY")
        print(f"IMPORTANT: Set SECRET_KEY in .env for production use!")
        os.environ['SECRET_KEY'] = dev_key
    
    # Disable Redis for development unless explicitly enabled
    if not os.environ.get('REDIS_ENABLED'):
        os.environ['REDIS_ENABLED'] = 'false'
    
    # Database URL is now handled by config.py
    # No need to override here
    
    print("Development environment configured")

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import flask
        import sqlalchemy
        import flask_login
        import flask_wtf
        print("All required dependencies are installed")
        return True
    except ImportError as e:
        print(f"ERROR: Missing dependency: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        return False

def create_directories():
    """Create necessary directories"""
    directories = ['logs', 'static/uploads', 'backups']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    print("Directories created")

def main():
    """Main application startup function"""
    print("Starting PipLinePro...")
    
    # Set up environment
    setup_development_environment()
    
    # Validate environment variables BEFORE starting
    print("\n" + "="*70)
    print("Validating environment variables...")
    print("="*70)
    from app.utils.env_validator import validate_environment
    
    # Get current environment
    current_env = os.getenv('FLASK_ENV', 'development')
    
    # Validate environment variables
    # In development, show warnings but don't fail
    # In production, fail if required vars are missing
    fail_on_error = (current_env == 'production')
    is_valid, errors, warnings = validate_environment(current_env, fail_on_error=fail_on_error)
    
    if errors:
        print("WARNING - Environment validation errors:")
        for error in errors:
            print(f"  {error}")
    
    if warnings:
        print("\nWARNING - Environment validation warnings:")
        for warning in warnings:
            print(f"  {warning}")
    
    if is_valid:
        print("OK - Environment validation passed!")
    else:
        print("WARNING - Environment has issues but continuing in development mode")
    
    print("="*70 + "\n")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Import and run the app
    try:
        from app import create_app, db
        from werkzeug.security import generate_password_hash
        
        app = create_app()
        
        print("Application created successfully")
        
        # Initialize Sentry error tracking
        try:
            from app.utils.sentry_config import init_sentry
            if init_sentry(app):
                print("OK - Sentry error tracking initialized")
            else:
                print("INFO - Sentry error tracking not configured (set SENTRY_DSN to enable)")
        except Exception as e:
            print(f"WARNING - Failed to initialize Sentry: {e}")
        
        # Disable verbose loggers
        try:
            # Suppress SQLAlchemy logs
            logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
            logging.getLogger('sqlalchemy.dialects').setLevel(logging.ERROR)
            logging.getLogger('sqlalchemy.pool').setLevel(logging.ERROR)
            logging.getLogger('sqlalchemy.orm').setLevel(logging.ERROR)
            
            # Suppress Flask logs
            logging.getLogger('werkzeug').setLevel(logging.WARNING)
            logging.getLogger('flask.app').setLevel(logging.WARNING)
            
            # Suppress other noisy loggers
            logging.getLogger('urllib3').setLevel(logging.WARNING)
            logging.getLogger('requests').setLevel(logging.WARNING)
            logging.getLogger('yfinance').setLevel(logging.CRITICAL)
            
            print("Verbose loggers suppressed")
        except Exception as e:
            print(f"WARNING: Could not configure logging: {e}")
        
        # Initialize database optimization
        with app.app_context():
            try:
                # Try enhanced unified database service first
                try:
                    from app.services.unified_database_service import UnifiedDatabaseService
                    # UnifiedDatabaseService creates indexes on initialization or via static method
                    # Check if it has the method we need
                    if hasattr(UnifiedDatabaseService, 'create_performance_indexes'):
                        result = UnifiedDatabaseService.create_performance_indexes()
                        if isinstance(result, int):
                            app.logger.info(f"Database optimization completed: {result} indexes created")
                        else:
                            app.logger.info("Database optimization completed")
                except ImportError:
                    # Fallback to legacy service if unified service not available
                    from app.services.database_optimization_service import DatabaseOptimizationService
                    result = DatabaseOptimizationService.create_performance_indexes()
                    if isinstance(result, int):
                        app.logger.info(f"Database optimization completed: {result} indexes created")
                    else:
                        app.logger.info("Database optimization completed")
            except Exception as e:
                app.logger.error(f"Failed to initialize database optimization: {e}")
        
        # Database initialization - controlled by environment variable
        # Set INIT_DB=true to enable database initialization (development only)
        if os.environ.get('INIT_DB', 'false').lower() == 'true' and os.environ.get('FLASK_ENV') != 'production':
            app.logger.info("Database initialization enabled for development")
            with app.app_context():
                try:
                    db.create_all()
                    app.logger.info("Database tables created successfully")
                    
                    # Create default category options (WD and DEP)
                    from app.models.config import Option
                    default_categories = ['WD', 'DEP']
                    for category in default_categories:
                        existing_category = Option.query.filter_by(
                            field_name='category', 
                            value=category, 
                            is_active=True
                        ).first()
                        if not existing_category:
                            category_option = Option(
                                field_name='category',
                                value=category
                            )
                            db.session.add(category_option)
                            app.logger.info(f"Default category '{category}' created")
                    
                    db.session.commit()
                    app.logger.info("Default category options created successfully")
                    
                    # Create default admin user if it doesn't exist - SECURE VERSION
                    from app.models.user import User
                    admin_user = User.query.filter_by(username='admin').first()
                    if not admin_user:
                        # Check if admin credentials are provided via environment variables
                        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
                        admin_password = os.environ.get('ADMIN_PASSWORD')
                        
                        if not admin_password:
                            # Generate a secure random password if not provided
                            import secrets
                            import string
                            admin_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
                            app.logger.warning(f"WARNING: No ADMIN_PASSWORD set. Generated temporary password: {admin_password}")
                            app.logger.warning("IMPORTANT: Change this password immediately after first login!")
                        
                        admin_user = User()
                        admin_user.username = admin_username
                        admin_user.password = generate_password_hash(admin_password)
                        admin_user.role = 'admin'
                        admin_user.email = os.environ.get('ADMIN_EMAIL', 'admin@pipeline.com')
                        admin_user.password_changed_at = None  # Force password change on first login
                        db.session.add(admin_user)
                        db.session.commit()
                        app.logger.info(f"Admin user '{admin_username}' created")
                        
                        if not os.environ.get('ADMIN_PASSWORD'):
                            app.logger.warning(f"TEMPORARY PASSWORD: {admin_password}")
                            app.logger.warning("CHANGE THIS PASSWORD IMMEDIATELY AFTER LOGIN!")
                    else:
                        # Check if admin password needs to be changed (first login)
                        if admin_user.password_changed_at is None:
                            app.logger.warning("Admin user exists but password change required on first login")
                except Exception as e:
                    app.logger.error(f"Database initialization failed: {str(e)}")
        else:
            app.logger.info("Database initialization disabled - use Flask-Migrate for database management")
        
        # Register Flask CLI commands for migrations
        from app.cli_commands import register_cli_commands
        register_cli_commands(app)
        
        print("Starting development server...")
        print("Access the application at: http://127.0.0.1:5000")
        print("Debug mode is enabled")
        print("Press Ctrl+C to stop the server")
        print()
        print("Available Flask CLI commands:")
        print("  flask db init          - Initialize migration repository")
        print("  flask db migrate       - Create new migration")
        print("  flask db upgrade      - Apply migrations")
        print("  flask db downgrade    - Rollback migration")
        print("  flask db current      - Show current migration")
        print("  flask db history      - Show migration history")
        print()
        
        # Windows'ta use_reloader bazen sorun cikariyor, bu yuzden False yapiyoruz
        # Eger reloader istiyorsaniz, use_reloader=True yapabilirsiniz
        import platform
        use_reloader = platform.system() != 'Windows'
        
        # Get debug mode from environment variable (default: False for production)
        debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'
        
        # Only enable debug in development environment
        if os.getenv('FLASK_ENV') == 'production':
            debug_mode = False
            use_reloader = False
        
        app.run(
            host='0.0.0.0',  # Bind to all interfaces to allow external access
            port=5000,
            debug=debug_mode,
            use_reloader=use_reloader and debug_mode  # Only use reloader in debug mode
        )
        
    except Exception as e:
        print(f"ERROR: Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()