"""
Sentry Error Tracking Configuration
Configures Sentry for error monitoring and performance tracking
"""
import os
import logging

logger = logging.getLogger(__name__)


def init_sentry(app=None):
    """
    Initialize Sentry error tracking
    
    Args:
        app: Flask application instance (optional)
    """
    sentry_dsn = os.getenv('SENTRY_DSN')
    
    if not sentry_dsn:
        logger.info("Sentry DSN not configured - error tracking disabled")
        return False
    
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        
        # Get environment settings
        environment = os.getenv('FLASK_ENV', 'development')
        release = os.getenv('APP_VERSION', 'unknown')
        
        # Configure logging integration
        sentry_logging = LoggingIntegration(
            level=logging.INFO,  # Capture info and above as breadcrumbs
            event_level=logging.ERROR  # Send errors as events
        )
        
        # Initialize Sentry
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[
                FlaskIntegration(),
                SqlalchemyIntegration(),
                sentry_logging,
            ],
            environment=environment,
            release=release,
            
            # Performance Monitoring
            traces_sample_rate=float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.1')),  # 10% of transactions
            
            # Error Sampling
            sample_rate=1.0,  # Capture 100% of errors
            
            # Additional options
            send_default_pii=False,  # Don't send personally identifiable information
            attach_stacktrace=True,
            max_breadcrumbs=50,
            
            # Before send hook to filter sensitive data
            before_send=before_send_filter,
            
            # Performance monitoring
            profiles_sample_rate=float(os.getenv('SENTRY_PROFILES_SAMPLE_RATE', '0.1')),
        )
        
        logger.info(f"Sentry initialized successfully for environment: {environment}")
        
        # Test Sentry connection (only in development)
        if environment == 'development' and os.getenv('SENTRY_TEST_ON_INIT', 'false').lower() == 'true':
            sentry_sdk.capture_message("Sentry test message - initialization successful", level="info")
            logger.info("Sentry test message sent")
        
        return True
        
    except ImportError:
        logger.warning(
            "Sentry SDK not installed. Install with: pip install sentry-sdk[flask]"
        )
        return False
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
        return False


def before_send_filter(event, hint):
    """
    Filter and sanitize events before sending to Sentry
    Remove sensitive data like passwords, tokens, etc.
    """
    # Filter out sensitive environment variables
    if 'server_name' in event:
        env_vars = event.get('contexts', {}).get('runtime', {}).get('environment', {})
        if env_vars:
            sensitive_keys = [
                'SECRET_KEY', 'JWT_SECRET_KEY', 'DATABASE_URL',
                'POSTGRES_PASSWORD', 'REDIS_PASSWORD', 'OPENAI_API_KEY',
                'AWS_SECRET_ACCESS_KEY', 'SENTRY_DSN', 'ADMIN_PASSWORD'
            ]
            for key in sensitive_keys:
                if key in env_vars:
                    env_vars[key] = '***FILTERED***'
    
    # Filter request data
    if 'request' in event:
        request = event['request']
        
        # Filter headers
        if 'headers' in request:
            sensitive_headers = ['Authorization', 'Cookie', 'X-Auth-Token']
            for header in sensitive_headers:
                if header in request['headers']:
                    request['headers'][header] = '***FILTERED***'
        
        # Filter query params and form data
        if 'data' in request and isinstance(request['data'], dict):
            sensitive_fields = ['password', 'token', 'secret', 'api_key', 'credit_card']
            for field in sensitive_fields:
                for key in list(request['data'].keys()):
                    if field in key.lower():
                        request['data'][key] = '***FILTERED***'
    
    # Filter exception context
    if 'exception' in event and 'values' in event['exception']:
        for exception in event['exception']['values']:
            if 'stacktrace' in exception:
                for frame in exception['stacktrace'].get('frames', []):
                    # Filter local variables
                    if 'vars' in frame:
                        sensitive_vars = ['password', 'token', 'secret', 'api_key']
                        for var_name in list(frame['vars'].keys()):
                            if any(s in var_name.lower() for s in sensitive_vars):
                                frame['vars'][var_name] = '***FILTERED***'
    
    return event


def capture_exception(error: Exception, context: dict = None):
    """
    Capture an exception and send to Sentry with additional context
    
    Args:
        error: Exception to capture
        context: Additional context dictionary
    """
    try:
        import sentry_sdk
        
        if context:
            with sentry_sdk.push_scope() as scope:
                for key, value in context.items():
                    scope.set_context(key, value)
                sentry_sdk.capture_exception(error)
        else:
            sentry_sdk.capture_exception(error)
    except ImportError:
        logger.debug("Sentry not available - exception not sent")
    except Exception as e:
        logger.error(f"Failed to capture exception in Sentry: {e}")


def capture_message(message: str, level: str = "info", context: dict = None):
    """
    Capture a message and send to Sentry
    
    Args:
        message: Message to capture
        level: Severity level (debug, info, warning, error, fatal)
        context: Additional context dictionary
    """
    try:
        import sentry_sdk
        
        if context:
            with sentry_sdk.push_scope() as scope:
                for key, value in context.items():
                    scope.set_context(key, value)
                sentry_sdk.capture_message(message, level=level)
        else:
            sentry_sdk.capture_message(message, level=level)
    except ImportError:
        logger.debug("Sentry not available - message not sent")
    except Exception as e:
        logger.error(f"Failed to capture message in Sentry: {e}")


def set_user_context(user_id: str = None, email: str = None, username: str = None):
    """
    Set user context for Sentry events
    
    Args:
        user_id: User ID
        email: User email (will be filtered if send_default_pii is False)
        username: Username
    """
    try:
        import sentry_sdk
        
        user_data = {}
        if user_id:
            user_data['id'] = user_id
        if email:
            user_data['email'] = email
        if username:
            user_data['username'] = username
        
        if user_data:
            sentry_sdk.set_user(user_data)
    except ImportError:
        pass
    except Exception as e:
        logger.error(f"Failed to set user context in Sentry: {e}")


def add_breadcrumb(message: str, category: str = "default", level: str = "info", data: dict = None):
    """
    Add a breadcrumb to track user actions leading to an error
    
    Args:
        message: Breadcrumb message
        category: Category (e.g., 'navigation', 'api', 'user-action')
        level: Severity level
        data: Additional data dictionary
    """
    try:
        import sentry_sdk
        
        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data or {}
        )
    except ImportError:
        pass
    except Exception as e:
        logger.error(f"Failed to add breadcrumb in Sentry: {e}")

