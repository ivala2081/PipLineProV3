"""
Enhanced Transactions API endpoints for PipLinePro v2
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import logging

# Import services conditionally
try:
    from app.services.event_service import event_service, EventType
    EVENT_SERVICE_AVAILABLE = True
except ImportError:
    EVENT_SERVICE_AVAILABLE = False

try:
    from app.services.enhanced_cache_service import cache_service, CacheKey
    CACHE_SERVICE_AVAILABLE = True
except ImportError:
    CACHE_SERVICE_AVAILABLE = False

try:
    from app.services.microservice_service import TransactionServiceClient
    MICROSERVICE_SERVICE_AVAILABLE = True
except ImportError:
    MICROSERVICE_SERVICE_AVAILABLE = False

logger = logging.getLogger(__name__)

transactions_api = Blueprint('transactions_api', __name__)

# Temporarily disable CSRF protection for transactions API
from app import csrf
csrf.exempt(transactions_api)

@transactions_api.route("", methods=['GET'])
@login_required
def get_transactions():
    """Get transactions with enhanced caching and real-time updates"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        psp = request.args.get('psp')
        category = request.args.get('category')
        
        # Build filters
        filters = {}
        if psp:
            filters['psp'] = psp
        if category:
            filters['category'] = category
        
        # Try to get from cache first
        cached_result = None
        if CACHE_SERVICE_AVAILABLE:
            try:
                cache_key = CacheKey.transaction_list(filters, page, per_page)
                cached_result = cache_service.get(cache_key)
                
                if cached_result:
                    logger.info(f"Cache hit for transactions: {cache_key}")
                    return jsonify({
                        'status': 'success',
                        'data': cached_result,
                        'cached': True
                    })
            except Exception as e:
                logger.warning(f"Cache service error: {e}")
        
        # If not in cache, get from database
        from app.services.query_service import QueryService
        from datetime import datetime
        
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        
        result = QueryService.get_transactions_by_date_range(
            start_date=start_date_obj,
            end_date=end_date_obj,
            page=page,
            per_page=per_page,
            filters=filters
        )
        
        # Cache the result
        if CACHE_SERVICE_AVAILABLE:
            try:
                cache_key = CacheKey.transaction_list(filters, page, per_page)
                cache_service.set(cache_key, result, ttl=1800)  # 30 minutes
            except Exception as e:
                logger.warning(f"Cache service error: {e}")
        
        return jsonify({
            'status': 'success',
            'data': result,
            'cached': False
        })
        
    except Exception as e:
        logger.error(f"Error getting transactions: {e}")
        return jsonify({'error': 'Failed to get transactions'}), 500

@transactions_api.route("", methods=['POST'])
@login_required
def create_transaction():
    """Create a new transaction with event publishing"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['client_name', 'amount', 'currency']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create transaction (using existing service)
        from app.services.transaction_service import TransactionService
        from app.models.transaction import Transaction
        
        transaction = TransactionService.create_transaction(data, current_user.id)
        
        if transaction:
            # Publish event for real-time updates
            if EVENT_SERVICE_AVAILABLE:
                try:
                    event_service.publish_event(
                        EventType.TRANSACTION_CREATED,
                        {
                            'transaction_id': transaction.id,
                            'client_name': transaction.client_name,
                            'amount': float(transaction.amount),
                            'psp': transaction.psp,
                            'user_id': current_user.id
                        },
                        source='api_v2'
                    )
                except Exception as e:
                    logger.warning(f"Event service error: {e}")
            
            # Invalidate related cache
            if CACHE_SERVICE_AVAILABLE:
                try:
                    cache_service.invalidate_transaction_cache(transaction.id)
                except Exception as e:
                    logger.warning(f"Cache service error: {e}")
            
            return jsonify({
                'status': 'success',
                'data': {
                    'id': transaction.id,
                    'client_name': transaction.client_name,
                    'amount': float(transaction.amount),
                    'currency': transaction.currency,
                    'psp': transaction.psp,
                    'category': transaction.category,
                    'created_at': transaction.created_at.isoformat()
                },
                'message': 'Transaction created successfully'
            }), 201
        else:
            return jsonify({'error': 'Failed to create transaction'}), 500
            
    except Exception as e:
        logger.error(f"Error creating transaction: {e}")
        return jsonify({'error': 'Failed to create transaction'}), 500

@transactions_api.route('/<int:transaction_id>', methods=['GET'])
@login_required
def get_transaction(transaction_id):
    """Get a specific transaction"""
    try:
        # Try cache first
        cache_key = CacheKey.transaction_detail(transaction_id)
        cached_transaction = cache_service.get(cache_key)
        
        if cached_transaction:
            return jsonify({
                'status': 'success',
                'data': cached_transaction,
                'cached': True
            })
        
        # Get from database
        from app.models.transaction import Transaction
        transaction = Transaction.query.get_or_404(transaction_id)
        
        transaction_data = {
            'id': transaction.id,
            'client_name': transaction.client_name,
            'amount': float(transaction.amount),
            'currency': transaction.currency,
            'psp': transaction.psp,
            'category': transaction.category,
            'commission': float(transaction.commission),
            'net_amount': float(transaction.net_amount),
            'date': transaction.date.isoformat(),
            'created_at': transaction.created_at.isoformat(),
            'updated_at': transaction.updated_at.isoformat()
        }
        
        # Cache the result
        cache_service.set(cache_key, transaction_data, ttl=3600)  # 1 hour
        
        return jsonify({
            'status': 'success',
            'data': transaction_data,
            'cached': False
        })
        
    except Exception as e:
        logger.error(f"Error getting transaction {transaction_id}: {e}")
        return jsonify({'error': 'Failed to get transaction'}), 500

@transactions_api.route('/<int:transaction_id>', methods=['PUT'])
@login_required
def update_transaction(transaction_id):
    """Update a transaction"""
    try:
        data = request.get_json()
        
        # Update transaction
        from app.services.transaction_service import TransactionService
        success = TransactionService.update_transaction(transaction_id, data, current_user.id)
        
        if success:
            # Publish event
            event_service.publish_event(
                EventType.TRANSACTION_UPDATED,
                {
                    'transaction_id': transaction_id,
                    'user_id': current_user.id,
                    'changes': data
                },
                source='api_v2'
            )
            
            # Invalidate cache
            cache_service.invalidate_transaction_cache(transaction_id)
            
            return jsonify({
                'status': 'success',
                'message': 'Transaction updated successfully'
            })
        else:
            return jsonify({'error': 'Failed to update transaction'}), 500
            
    except Exception as e:
        logger.error(f"Error updating transaction {transaction_id}: {e}")
        return jsonify({'error': 'Failed to update transaction'}), 500

@transactions_api.route('/<int:transaction_id>', methods=['DELETE'])
@login_required
def delete_transaction(transaction_id):
    """Delete a transaction"""
    try:
        from app.models.transaction import Transaction
        from app import db
        
        transaction = Transaction.query.get_or_404(transaction_id)
        db.session.delete(transaction)
        db.session.commit()
        
        # Publish event
        event_service.publish_event(
            EventType.TRANSACTION_DELETED,
            {
                'transaction_id': transaction_id,
                'user_id': current_user.id
            },
            source='api_v2'
        )
        
        # Invalidate cache
        cache_service.invalidate_transaction_cache(transaction_id)
        
        return jsonify({
            'status': 'success',
            'message': 'Transaction deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting transaction {transaction_id}: {e}")
        return jsonify({'error': 'Failed to delete transaction'}), 500

@transactions_api.route('/bulk', methods=['POST'])
@login_required
def bulk_create_transactions():
    """Create multiple transactions in bulk"""
    try:
        data = request.get_json()
        transactions_data = data.get('transactions', [])
        
        if not transactions_data:
            return jsonify({'error': 'No transactions provided'}), 400
        
        created_transactions = []
        errors = []
        
        for i, transaction_data in enumerate(transactions_data):
            try:
                from app.services.transaction_service import TransactionService
                transaction = TransactionService.create_transaction(transaction_data, current_user.id)
                
                if transaction:
                    created_transactions.append({
                        'id': transaction.id,
                        'client_name': transaction.client_name,
                        'amount': float(transaction.amount)
                    })
                    
                    # Publish event for each transaction
                    event_service.publish_event(
                        EventType.TRANSACTION_CREATED,
                        {
                            'transaction_id': transaction.id,
                            'client_name': transaction.client_name,
                            'amount': float(transaction.amount),
                            'psp': transaction.psp,
                            'user_id': current_user.id,
                            'bulk_operation': True
                        },
                        source='api_v2'
                    )
                else:
                    errors.append(f'Transaction {i+1}: Failed to create')
                    
            except Exception as e:
                errors.append(f'Transaction {i+1}: {str(e)}')
        
        # Invalidate cache after bulk operation
        cache_service.invalidate_transaction_cache()
        
        return jsonify({
            'status': 'success',
            'created_count': len(created_transactions),
            'error_count': len(errors),
            'transactions': created_transactions,
            'errors': errors
        })
        
    except Exception as e:
        logger.error(f"Error in bulk transaction creation: {e}")
        return jsonify({'error': 'Failed to create bulk transactions'}), 500
