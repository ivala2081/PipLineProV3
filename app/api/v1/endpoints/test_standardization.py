"""
Test Endpoint for API Standardization
This endpoint is used to test the new standardized API response format
and error handling patterns before applying to production endpoints.
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.utils.api_response import (
    success_response,
    error_response,
    paginated_response,
    ErrorCode
)
from app.utils.api_error_handler import handle_api_errors
from app.utils.db_transaction import db_transaction
from app.utils.unified_logger import get_logger
from app import db
from app.models.transaction import Transaction
from datetime import datetime

logger = get_logger('TestStandardization')

test_api = Blueprint('test_api', __name__)

# Temporarily disable CSRF for testing
from app import csrf
csrf.exempt(test_api)


@test_api.route("/test/success")
@login_required
@handle_api_errors
def test_success_response():
    """
    Test endpoint for success response format.
    
    Returns:
        Standardized success response with data
    """
    test_data = {
        'message': 'Test successful',
        'user': current_user.username,
        'timestamp': datetime.now().isoformat()
    }
    
    return jsonify(success_response(
        data=test_data,
        meta={'message': 'This is a test endpoint'}
    )), 200


@test_api.route("/test/error-validation")
@login_required
@handle_api_errors
def test_validation_error():
    """
    Test endpoint for validation error handling.
    
    Query params:
        - force_error: If 'true', raises validation error
    """
    force_error = request.args.get('force_error', 'false').lower() == 'true'
    
    if force_error:
        from app.utils.unified_error_handler import ValidationError
        raise ValidationError("Test validation error", field="test_field")
    
    return jsonify(success_response(
        data={'message': 'No error forced'}
    )), 200


@test_api.route("/test/error-database")
@login_required
@handle_api_errors
def test_database_error():
    """
    Test endpoint for database error handling.
    
    Query params:
        - force_error: If 'true', raises database error
    """
    force_error = request.args.get('force_error', 'false').lower() == 'true'
    
    if force_error:
        # Simulate database error
        raise Exception("Simulated database error")
    
    return jsonify(success_response(
        data={'message': 'No database error forced'}
    )), 200


@test_api.route("/test/transaction")
@login_required
@handle_api_errors
def test_transaction_helper():
    """
    Test endpoint for database transaction helper.
    
    Query params:
        - create: If 'true', creates a test transaction
        - force_error: If 'true', forces error to test rollback
    """
    should_create = request.args.get('create', 'false').lower() == 'true'
    force_error = request.args.get('force_error', 'false').lower() == 'true'
    
    if not should_create:
        return jsonify(success_response(
            data={'message': 'Set create=true to test transaction'}
        )), 200
    
    try:
        with db_transaction() as session:
            # Test transaction creation
            test_transaction = Transaction(
                client_name='TEST_CLIENT',
                company='TEST_COMPANY',
                date=datetime.now().date(),
                category='DEP',
                amount=100.00,
                commission=5.00,
                net_amount=95.00,
                currency='TL',
                created_by=current_user.id
            )
            
            session.add(test_transaction)
            session.flush()  # Get ID before commit
            
            transaction_id = test_transaction.id
            
            if force_error:
                # Force error to test rollback
                raise Exception("Test rollback error")
            
            # Transaction will auto-commit here
        
        return jsonify(success_response(
            data={
                'message': 'Transaction created successfully',
                'transaction_id': transaction_id
            }
        )), 201
    
    except Exception as e:
        # Error handler decorator will catch this
        raise


@test_api.route("/test/pagination")
@login_required
@handle_api_errors
def test_pagination():
    """
    Test endpoint for paginated response format.
    
    Query params:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 10)
    """
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    # Simulate paginated data
    total_items = 100
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    items = [
        {'id': i, 'name': f'Item {i}'}
        for i in range(start_idx + 1, min(end_idx + 1, total_items + 1))
    ]
    
    return jsonify(paginated_response(
        items=items,
        page=page,
        per_page=per_page,
        total=total_items,
        meta={'message': 'Test pagination response'}
    )), 200


@test_api.route("/test/legacy-comparison")
@login_required
def test_legacy_comparison():
    """
    Test endpoint showing legacy vs new response format.
    
    Query params:
        - format: 'legacy' or 'new' (default: 'new')
    """
    response_format = request.args.get('format', 'new')
    
    test_data = {
        'message': 'Test data',
        'user': current_user.username
    }
    
    if response_format == 'legacy':
        # Legacy format (old way)
        return jsonify({
            'success': True,
            'data': test_data,
            'message': 'Legacy format response'
        }), 200
    else:
        # New standardized format
        return jsonify(success_response(
            data=test_data,
            meta={'message': 'New standardized format response'}
        )), 200

