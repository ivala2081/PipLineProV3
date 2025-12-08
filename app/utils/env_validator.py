"""
Environment Variable Validation Service
Validates required environment variables at application startup
"""
import os
import sys
from typing import Dict, List, Tuple, Optional
from enum import Enum


class EnvVarType(Enum):
    """Environment variable types"""
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    URL = "url"
    EMAIL = "email"


class EnvVarImportance(Enum):
    """Environment variable importance levels"""
    REQUIRED = "required"  # Must be set, app fails to start without it
    RECOMMENDED = "recommended"  # Should be set, warning if missing
    OPTIONAL = "optional"  # Nice to have


class EnvVar:
    """Environment variable definition"""
    def __init__(
        self,
        name: str,
        importance: EnvVarImportance,
        var_type: EnvVarType = EnvVarType.STRING,
        default: Optional[str] = None,
        description: str = "",
        environments: List[str] = None,  # ['development', 'production', 'testing']
        validator: Optional[callable] = None
    ):
        self.name = name
        self.importance = importance
        self.var_type = var_type
        self.default = default
        self.description = description
        self.environments = environments or ['development', 'production', 'testing']
        self.validator = validator


class EnvValidator:
    """Environment variable validator"""
    
    # Define all environment variables
    ENV_VARS = [
        # Core Application
        EnvVar(
            "FLASK_ENV",
            EnvVarImportance.REQUIRED,
            description="Application environment (development, production, testing)"
        ),
        EnvVar(
            "SECRET_KEY",
            EnvVarImportance.REQUIRED,
            description="Flask secret key for session encryption",
            environments=['production']
        ),
        EnvVar(
            "DEBUG",
            EnvVarImportance.OPTIONAL,
            EnvVarType.BOOLEAN,
            default="False",
            description="Enable debug mode (development only)"
        ),
        
        # Database Configuration
        EnvVar(
            "DATABASE_URL",
            EnvVarImportance.RECOMMENDED,
            EnvVarType.URL,
            description="Full database connection URL"
        ),
        EnvVar(
            "POSTGRES_HOST",
            EnvVarImportance.RECOMMENDED,
            description="PostgreSQL host (required for production)",
            environments=['production']
        ),
        EnvVar(
            "POSTGRES_PORT",
            EnvVarImportance.OPTIONAL,
            EnvVarType.INTEGER,
            default="5432",
            description="PostgreSQL port"
        ),
        EnvVar(
            "POSTGRES_DB",
            EnvVarImportance.RECOMMENDED,
            description="PostgreSQL database name",
            environments=['production']
        ),
        EnvVar(
            "POSTGRES_USER",
            EnvVarImportance.RECOMMENDED,
            description="PostgreSQL username",
            environments=['production']
        ),
        EnvVar(
            "POSTGRES_PASSWORD",
            EnvVarImportance.RECOMMENDED,
            description="PostgreSQL password",
            environments=['production']
        ),
        EnvVar(
            "POSTGRES_SSL_MODE",
            EnvVarImportance.OPTIONAL,
            default="prefer",
            description="PostgreSQL SSL mode (require, prefer, disable)"
        ),
        
        # Admin Configuration
        EnvVar(
            "ADMIN_USERNAME",
            EnvVarImportance.OPTIONAL,
            default="admin",
            description="Default admin username"
        ),
        EnvVar(
            "ADMIN_PASSWORD",
            EnvVarImportance.RECOMMENDED,
            description="Default admin password (set in production)",
            environments=['production']
        ),
        EnvVar(
            "ADMIN_EMAIL",
            EnvVarImportance.OPTIONAL,
            EnvVarType.EMAIL,
            default="admin@pipeline.com",
            description="Admin email address"
        ),
        
        # Redis Configuration
        EnvVar(
            "REDIS_ENABLED",
            EnvVarImportance.OPTIONAL,
            EnvVarType.BOOLEAN,
            default="false",
            description="Enable Redis for caching and rate limiting"
        ),
        EnvVar(
            "REDIS_URL",
            EnvVarImportance.OPTIONAL,
            EnvVarType.URL,
            description="Redis connection URL (required if REDIS_ENABLED=true)"
        ),
        EnvVar(
            "REDIS_HOST",
            EnvVarImportance.OPTIONAL,
            default="localhost",
            description="Redis host"
        ),
        EnvVar(
            "REDIS_PORT",
            EnvVarImportance.OPTIONAL,
            EnvVarType.INTEGER,
            default="6379",
            description="Redis port"
        ),
        EnvVar(
            "REDIS_PASSWORD",
            EnvVarImportance.OPTIONAL,
            description="Redis password (if authentication enabled)"
        ),
        
        # Security & Monitoring
        EnvVar(
            "SENTRY_DSN",
            EnvVarImportance.RECOMMENDED,
            EnvVarType.URL,
            description="Sentry DSN for error tracking",
            environments=['production']
        ),
        EnvVar(
            "JWT_SECRET_KEY",
            EnvVarImportance.RECOMMENDED,
            description="JWT secret key for API authentication",
            environments=['production']
        ),
        
        # Logging
        EnvVar(
            "LOG_LEVEL",
            EnvVarImportance.OPTIONAL,
            default="INFO",
            description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
        ),
        
        # CORS Configuration
        EnvVar(
            "CORS_ORIGINS",
            EnvVarImportance.RECOMMENDED,
            description="Comma-separated list of allowed CORS origins",
            environments=['production']
        ),
        
        # Backup Configuration
        EnvVar(
            "AWS_ACCESS_KEY_ID",
            EnvVarImportance.OPTIONAL,
            description="AWS access key for S3 backups"
        ),
        EnvVar(
            "AWS_SECRET_ACCESS_KEY",
            EnvVarImportance.OPTIONAL,
            description="AWS secret key for S3 backups"
        ),
        EnvVar(
            "AWS_REGION",
            EnvVarImportance.OPTIONAL,
            default="us-east-1",
            description="AWS region for S3 backups"
        ),
        EnvVar(
            "S3_BUCKET",
            EnvVarImportance.OPTIONAL,
            description="S3 bucket name for backups"
        ),
        
        # External Services
        EnvVar(
            "OPENAI_API_KEY",
            EnvVarImportance.OPTIONAL,
            description="OpenAI API key for AI features"
        ),
        EnvVar(
            "SLACK_WEBHOOK",
            EnvVarImportance.OPTIONAL,
            EnvVarType.URL,
            description="Slack webhook URL for notifications"
        ),
    ]
    
    @classmethod
    def validate(cls, environment: str = None, fail_on_error: bool = True) -> Tuple[bool, List[str], List[str]]:
        """
        Validate environment variables
        
        Args:
            environment: Current environment (development, production, testing)
            fail_on_error: If True, print errors and exit on validation failure
            
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        if environment is None:
            environment = os.getenv('FLASK_ENV')
            if not environment:
                # If FLASK_ENV is not set at all, default to development and warn
                environment = 'development'
                if fail_on_error:
                    print("INFO - FLASK_ENV not set, defaulting to 'development'")
        
        errors = []
        warnings = []
        
        for env_var in cls.ENV_VARS:
            # Skip if not applicable to current environment
            if environment not in env_var.environments:
                continue
            
            value = os.getenv(env_var.name)
            
            # Check if required variable is missing
            if env_var.importance == EnvVarImportance.REQUIRED and not value:
                errors.append(
                    f"REQUIRED: {env_var.name} is not set. {env_var.description}"
                )
                continue
            
            # Check if recommended variable is missing
            if env_var.importance == EnvVarImportance.RECOMMENDED and not value:
                warnings.append(
                    f"RECOMMENDED: {env_var.name} is not set. {env_var.description}"
                )
                continue
            
            # Validate value if present
            if value and env_var.validator:
                try:
                    if not env_var.validator(value):
                        errors.append(
                            f"INVALID: {env_var.name} has invalid value. {env_var.description}"
                        )
                except Exception as e:
                    errors.append(
                        f"VALIDATION ERROR: {env_var.name} - {str(e)}"
                    )
        
        # Additional contextual validations
        redis_enabled = os.getenv('REDIS_ENABLED', 'false').lower() == 'true'
        if redis_enabled and not os.getenv('REDIS_URL') and not os.getenv('REDIS_HOST'):
            errors.append(
                "REDIS_ENABLED is true but REDIS_URL or REDIS_HOST is not set"
            )
        
        # Check for insecure defaults in production
        if environment == 'production':
            secret_key = os.getenv('SECRET_KEY', '')
            if 'dev-secret' in secret_key.lower() or 'change' in secret_key.lower():
                errors.append(
                    "SECURITY: SECRET_KEY appears to be using a development/default value in production"
                )
            
            # Warn if using SQLite in production
            database_url = os.getenv('DATABASE_URL', '')
            if 'sqlite' in database_url.lower():
                warnings.append(
                    "PRODUCTION: Using SQLite database. PostgreSQL is recommended for production."
                )
        
        # Check for S3 backup configuration
        s3_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'S3_BUCKET']
        s3_set = [os.getenv(var) for var in s3_vars]
        if any(s3_set) and not all(s3_set):
            warnings.append(
                f"BACKUP: Partial S3 configuration detected. All of {', '.join(s3_vars)} should be set for S3 backups."
            )
        
        is_valid = len(errors) == 0
        
        if fail_on_error and not is_valid:
            print("\n" + "="*70)
            print("ENVIRONMENT VARIABLE VALIDATION FAILED")
            print("="*70)
            for error in errors:
                print(error)
            if warnings:
                print("\nWarnings:")
                for warning in warnings:
                    print(warning)
            print("\n" + "="*70)
            print("Please set the required environment variables and restart the application.")
            print("See env.example for reference.")
            print("="*70 + "\n")
            sys.exit(1)
        
        return is_valid, errors, warnings
    
    @classmethod
    def print_validation_report(cls, environment: str = None):
        """Print a detailed validation report"""
        if environment is None:
            environment = os.getenv('FLASK_ENV', 'development')
        
        is_valid, errors, warnings = cls.validate(environment, fail_on_error=False)
        
        print("\n" + "="*70)
        print(f"ENVIRONMENT VARIABLE VALIDATION REPORT - {environment.upper()}")
        print("="*70)
        
        if is_valid:
            print("OK - All required environment variables are set!")
        else:
            print(f"ERROR - Validation failed with {len(errors)} error(s)")
            for error in errors:
                print(f"  {error}")
        
        if warnings:
            print(f"\nWARNING - {len(warnings)} warning(s):")
            for warning in warnings:
                print(f"  {warning}")
        
        print("="*70 + "\n")
        
        return is_valid
    
    @classmethod
    def get_documentation(cls) -> Dict:
        """Generate documentation for all environment variables"""
        docs = {
            'required': [],
            'recommended': [],
            'optional': []
        }
        
        for env_var in cls.ENV_VARS:
            var_doc = {
                'name': env_var.name,
                'type': env_var.var_type.value,
                'default': env_var.default,
                'description': env_var.description,
                'environments': env_var.environments
            }
            
            if env_var.importance == EnvVarImportance.REQUIRED:
                docs['required'].append(var_doc)
            elif env_var.importance == EnvVarImportance.RECOMMENDED:
                docs['recommended'].append(var_doc)
            else:
                docs['optional'].append(var_doc)
        
        return docs


# Convenience function for quick validation
def validate_environment(environment: str = None, fail_on_error: bool = True):
    """Validate environment variables at application startup"""
    return EnvValidator.validate(environment, fail_on_error)


if __name__ == '__main__':
    # Run validation when called directly
    EnvValidator.print_validation_report()

