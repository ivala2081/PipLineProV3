"""
Input validation decorator and utilities
Provides consistent input validation across all endpoints

This module provides decorators and utilities for validating API input,
ensuring data integrity and security across all endpoints.
"""
from functools import wraps
from flask import request, jsonify
from typing import Callable, Dict, Any, List, Optional, Tuple
from app.utils.unified_error_handler import ValidationError
from app.utils.api_response import error_response, ErrorCode
from app.utils.type_hints_helper import JsonDict, OptionalStr


def validate_input(
    required_fields: Optional[List[str]] = None,
    optional_fields: Optional[List[str]] = None,
    field_validators: Optional[Dict[str, Callable]] = None,
    allow_empty: bool = False
) -> Callable:
    """
    Decorator to validate input data for API endpoints
    
    Args:
        required_fields: List of required field names
        optional_fields: List of optional field names (for documentation)
        field_validators: Dict mapping field names to validation functions
        allow_empty: Whether to allow empty request body
    
    Usage:
        @validate_input(
            required_fields=['client_name', 'amount', 'category'],
            field_validators={
                'amount': lambda x: float(x) > 0,
                'category': lambda x: x in ['DEP', 'WD']
            }
        )
        def create_transaction():
            data = request.get_json()
            # data is guaranteed to be valid here
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check content type
            if not request.is_json:
                return jsonify(error_response(
                    ErrorCode.VALIDATION_ERROR.value,
                    'Request must be JSON'
                )), 400
            
            # Get JSON data
            data = request.get_json(silent=True)
            
            if data is None:
                if not allow_empty:
                    return jsonify(error_response(
                        ErrorCode.VALIDATION_ERROR.value,
                        'Request body is required'
                    )), 400
                data = {}
            
            # Validate required fields
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data or data[field] is None]
                if missing_fields:
                    return jsonify(error_response(
                        ErrorCode.VALIDATION_ERROR.value,
                        f'Missing required fields: {", ".join(missing_fields)}'
                    )), 400
            
            # Validate field values using custom validators
            if field_validators:
                validation_errors = []
                for field, validator in field_validators.items():
                    if field in data:
                        try:
                            if not validator(data[field]):
                                validation_errors.append(f'{field}: validation failed')
                        except Exception as e:
                            validation_errors.append(f'{field}: {str(e)}')
                
                if validation_errors:
                    return jsonify(error_response(
                        ErrorCode.VALIDATION_ERROR.value,
                        f'Validation errors: {"; ".join(validation_errors)}'
                    )), 400
            
            # Attach validated data to request for easy access
            request.validated_data = data
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def validate_pagination(
    page: Optional[int] = None,
    per_page: Optional[int] = None
) -> Tuple[int, int]:
    """
    Validate and normalize pagination parameters
    
    Args:
        page: Page number (1-indexed)
        per_page: Items per page
    
    Returns:
        Tuple of (page, per_page) normalized values
    """
    from app.utils.constants import Defaults
    
    # Get from request args if not provided
    if page is None:
        try:
            page = int(request.args.get('page', 1))
        except (ValueError, TypeError):
            page = 1
    
    if per_page is None:
        try:
            per_page = int(request.args.get('per_page', Defaults.PAGE_SIZE))
        except (ValueError, TypeError):
            per_page = Defaults.PAGE_SIZE
    
    # Validate and normalize
    page = max(1, page)  # Minimum page is 1
    per_page = max(1, min(per_page, Defaults.MAX_PAGE_SIZE))  # Between 1 and max
    
    return page, per_page


def validate_date_range(
    start_date: OptionalStr = None,
    end_date: OptionalStr = None,
    max_days: int = 365
) -> Tuple[OptionalStr, OptionalStr]:
    """
    Validate date range parameters
    
    Args:
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        max_days: Maximum allowed days in range
    
    Returns:
        Tuple of validated (start_date, end_date)
    
    Raises:
        ValidationError: If dates are invalid or range exceeds max_days
    """
    from datetime import datetime
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            raise ValidationError('Invalid start_date format. Use YYYY-MM-DD', field='start_date')
    else:
        start_dt = None
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            raise ValidationError('Invalid end_date format. Use YYYY-MM-DD', field='end_date')
    else:
        end_dt = None
    
    # Validate range
    if start_dt and end_dt:
        if start_dt > end_dt:
            raise ValidationError('start_date must be before end_date', field='date_range')
        
        days_diff = (end_dt - start_dt).days
        if days_diff > max_days:
            raise ValidationError(
                f'Date range exceeds maximum of {max_days} days',
                field='date_range'
            )
    
    return start_date, end_date

