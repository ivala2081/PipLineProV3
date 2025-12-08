"""
Feature Flags System
Safe way to enable/disable features without code deployment
"""
import os
from typing import Dict, Any, Optional
from functools import wraps
from flask import current_app, jsonify

class FeatureFlags:
    """
    Centralized feature flags management
    Flags can be controlled via environment variables or runtime configuration
    """
    
    # Feature flags - default to False (disabled)
    # Set via environment variables: FEATURE_FLAG_NAME=true
    ENABLE_MICROSERVICES = os.getenv('ENABLE_MICROSERVICES', 'false').lower() == 'true'
    ENABLE_MULTI_TENANT = os.getenv('ENABLE_MULTI_TENANT', 'false').lower() == 'true'
    ENABLE_READ_REPLICAS = os.getenv('ENABLE_READ_REPLICAS', 'false').lower() == 'true'
    ENABLE_REDIS_CLUSTER = os.getenv('ENABLE_REDIS_CLUSTER', 'false').lower() == 'true'
    ENABLE_API_GATEWAY = os.getenv('ENABLE_API_GATEWAY', 'false').lower() == 'true'
    ENABLE_ENHANCED_MONITORING = os.getenv('ENABLE_ENHANCED_MONITORING', 'true').lower() == 'true'  # Default enabled
    ENABLE_PROMETHEUS_METRICS = os.getenv('ENABLE_PROMETHEUS_METRICS', 'true').lower() == 'true'  # Default enabled
    ENABLE_DISTRIBUTED_TRACING = os.getenv('ENABLE_DISTRIBUTED_TRACING', 'false').lower() == 'true'
    ENABLE_ADVANCED_CACHING = os.getenv('ENABLE_ADVANCED_CACHING', 'false').lower() == 'true'
    
    # Canary deployment flags (percentage-based)
    CANARY_MICROSERVICES_PERCENTAGE = int(os.getenv('CANARY_MICROSERVICES_PERCENTAGE', '0'))
    CANARY_MULTI_TENANT_PERCENTAGE = int(os.getenv('CANARY_MULTI_TENANT_PERCENTAGE', '0'))
    
    @classmethod
    def is_enabled(cls, flag_name: str) -> bool:
        """
        Check if a feature flag is enabled
        
        Args:
            flag_name: Name of the feature flag (e.g., 'ENABLE_MICROSERVICES')
            
        Returns:
            bool: True if enabled, False otherwise
        """
        return getattr(cls, flag_name, False)
    
    @classmethod
    def get_all_flags(cls) -> Dict[str, bool]:
        """Get all feature flags as dictionary"""
        flags = {}
        for attr_name in dir(cls):
            if attr_name.startswith('ENABLE_') or attr_name.startswith('CANARY_'):
                if not callable(getattr(cls, attr_name)) and not attr_name.startswith('__'):
                    flags[attr_name] = getattr(cls, attr_name)
        return flags
    
    @classmethod
    def is_canary_enabled(cls, flag_name: str, user_id: Optional[int] = None) -> bool:
        """
        Check if canary deployment is enabled for this user/request
        
        Args:
            flag_name: Name of the canary flag (e.g., 'CANARY_MICROSERVICES_PERCENTAGE')
            user_id: Optional user ID for consistent canary assignment
            
        Returns:
            bool: True if user should be in canary group
        """
        percentage = getattr(cls, flag_name, 0)
        if percentage == 0:
            return False
        
        # Use user_id for consistent assignment, or random if None
        if user_id:
            # Consistent assignment based on user_id
            return (user_id % 100) < percentage
        else:
            # Random assignment (for non-authenticated requests)
            import random
            return random.randint(0, 99) < percentage


def feature_flag_required(flag_name: str, fallback_handler=None):
    """
    Decorator to require a feature flag to be enabled
    
    Usage:
        @feature_flag_required('ENABLE_MICROSERVICES')
        def my_function():
            # This code only runs if ENABLE_MICROSERVICES is True
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not FeatureFlags.is_enabled(flag_name):
                if fallback_handler:
                    return fallback_handler(*args, **kwargs)
                return jsonify({
                    'error': 'Feature not enabled',
                    'feature': flag_name
                }), 403
            return func(*args, **kwargs)
        return wrapper
    return decorator


def feature_flag_or_default(flag_name: str, default_func):
    """
    Decorator to use feature flag with fallback to default function
    
    Usage:
        @feature_flag_or_default('ENABLE_READ_REPLICAS', use_primary_db)
        def get_database():
            return use_replica_db()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if FeatureFlags.is_enabled(flag_name):
                return func(*args, **kwargs)
            else:
                return default_func(*args, **kwargs)
        return wrapper
    return decorator

