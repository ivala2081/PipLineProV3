"""
Transactions API endpoints for Flask
"""
from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, text, case, and_
from datetime import datetime, timedelta, timezone
from app.models.transaction import Transaction
from app.models.financial import PspTrack
from app import db, limiter
from decimal import Decimal, InvalidOperation
import logging
import os
import json
from app.services.enhanced_cache_service import cache_service, cached
from app.services.unified_database_service import monitor_query_performance
from app.utils.unified_logger import get_logger
from app.utils.input_sanitizer import (
    sanitize_client_name, sanitize_company_name, sanitize_notes,
    validate_category, validate_currency, validate_psp_name, validate_payment_method
)
from app.utils.financial_utils import safe_decimal, safe_divide, to_float
from app.utils.permission_decorators import require_permission
from app.utils.db_compat import ilike_compat
from app.utils.api_response import success_response, error_response, paginated_response, ErrorCode
from app.utils.api_error_handler import handle_api_errors, ValidationError
from app.utils.unified_error_handler import DatabaseError, ResourceNotFoundError, ResourceNotFoundError
from app.utils.db_transaction import db_transaction
from app.utils.tenant_helpers import set_tenant_on_new_record, add_tenant_filter, validate_tenant_access

logger = logging.getLogger(__name__)
api_logger = get_logger('app.api.transactions')

transactions_api = Blueprint('transactions_api', __name__)

# CSRF protection is handled via @require_csrf decorator on critical endpoints
# GET requests are exempt, POST/PUT/DELETE require CSRF token in X-CSRFToken header
from app import csrf
csrf.exempt(transactions_api)  # Still exempt blueprint, but use @require_csrf on critical routes
from app.utils.csrf_decorator import require_csrf

@transactions_api.route("", methods=['POST'])
@transactions_api.route("/", methods=['POST'])
@limiter.limit("30 per minute, 500 per hour")  # Rate limiting for transaction creation
@login_required
@require_csrf
@handle_api_errors
def create_transaction():
    """Create a new transaction with standardized error handling"""
    # Enhanced authentication check
    if not current_user.is_authenticated:
        return jsonify(error_response(
            ErrorCode.AUTHENTICATION_ERROR.value,
            'Please log in to create transactions'
        )), 401
    
    # Log the request for debugging
    logger.info(f"Transaction creation request from user {current_user.username}")
    
    # Validate request content type
    if not request.is_json:
        return jsonify(error_response(
            ErrorCode.VALIDATION_ERROR.value,
            'Request must be JSON'
        )), 400
    
    data = request.get_json()
    
    # Sanitize and validate required fields
    client_name = sanitize_client_name(data.get('client_name', ''))
    if not client_name:
        raise ValidationError('Client name is required', field='client_name')
    
    # Validate amount
    amount_str = data.get('amount', '')
    try:
        amount = Decimal(str(amount_str))
        if amount <= 0:
            raise ValidationError('Amount must be positive', field='amount')
    except (InvalidOperation, ValueError) as e:
        raise ValidationError('Invalid amount format', field='amount', details={'value': amount_str})
    
    # Sanitize and validate other fields
    currency = validate_currency(data.get('currency', 'TL')) or 'TL'
    payment_method = validate_payment_method(data.get('payment_method', ''))
    
    # Category is required and must be valid
    category = validate_category(data.get('category', ''))
    if not category:
        raise ValidationError('Invalid or missing category. Must be DEP or WD', field='category')
    
    psp_raw = data.get('psp', '')
    logger.info(f"PSP value received from frontend: '{psp_raw}' (type: {type(psp_raw)}, repr: {repr(psp_raw)})")
    
    # Very simple handling - just strip whitespace, no validation
    # If PSP is provided and not empty after stripping, use it
    if psp_raw:
        psp = str(psp_raw).strip()
        # If it's empty after stripping, set to None
        if not psp:
            psp = None
        # Otherwise, use it as-is (very permissive - no validation)
    else:
        psp = None
    
    logger.info(f"PSP value after processing: '{psp}' (type: {type(psp)}, repr: {repr(psp)})")
    
    # Log a warning if we received a value but it became None
    if psp is None and psp_raw and str(psp_raw).strip():
        logger.error(f"ERROR: PSP value '{psp_raw}' became None after processing!")
    company = sanitize_company_name(data.get('company', ''))
    
    # Handle both 'description' and 'notes' fields for backward compatibility
    description = sanitize_notes(data.get('description', data.get('notes', '')))
    
    # Currency is already in correct format (TL, USD, EUR)
    
    # Handle both 'transaction_date' and 'date' fields for backward compatibility
    transaction_date_str = data.get('transaction_date', data.get('date', ''))
    
    # Parse transaction date
    try:
        if transaction_date_str:
            transaction_date = datetime.strptime(transaction_date_str, '%Y-%m-%d').date()
        else:
            transaction_date = datetime.now().date()
    except ValueError:
        raise ValidationError(
            'Invalid transaction date format. Use YYYY-MM-DD',
            field='transaction_date',
            details={'value': transaction_date_str}
        )
    
    # Check for manual commission override first
    use_manual_commission = data.get('use_manual_commission', False)
    manual_commission_rate = data.get('manual_commission_rate')
    
    # Calculate commission strictly based on PSP rate when available (no defaults)
    commission_rate: Decimal | None = None
    
    if use_manual_commission and manual_commission_rate is not None:
        # Use manual commission rate (convert percentage to decimal)
        commission_rate = Decimal(str(manual_commission_rate)) / Decimal('100')
        logger.info(f"Using manual commission rate: {manual_commission_rate}% (decimal: {commission_rate})")
    elif psp:
        try:
            from app.services.psp_options_service import PspOptionsService
            from app.services.company_options_service import CompanyOptionsService
            commission_rate = PspOptionsService.get_psp_commission_rate(psp)
            logger.info(f"Using PSP '{psp}' commission rate: {commission_rate}")
        except Exception as e:
            logger.warning(f"Error fetching PSP commission rate for '{psp}': {e}")

    # Calculate commission based on category
    if category == 'WD':
        # WD transactions always have 0 commission and should be stored as negative amounts
        commission = Decimal('0')
        amount = -amount  # Store withdrawal amounts as negative values
        logger.info(f"WD transaction - setting commission to 0 and amount to negative: {amount}")
    elif commission_rate is not None:
        # Calculate commission for DEP transactions
        commission = amount * commission_rate
        logger.info(f"Calculated commission: {commission} for amount: {amount}")
    else:
        commission = Decimal('0')
        logger.info(f"No commission rate available, setting commission to 0")
    net_amount = amount - commission

    # Handle TRY amount calculations
    exchange_rate_value = (
        data.get('exchange_rate')
        or data.get('usd_rate')
        or data.get('eur_rate')
    )

    exchange_rate_decimal = None
    amount_try = None
    commission_try = None
    net_amount_try = None

    if currency and currency.upper() in ('USD', 'EUR') and exchange_rate_value not in (None, ""):
        try:
            exchange_rate_decimal = Decimal(str(exchange_rate_value))
            if exchange_rate_decimal > 0:
                amount_try = (amount * exchange_rate_decimal)
                commission_try = (commission * exchange_rate_decimal)
                net_amount_try = (net_amount * exchange_rate_decimal)
        except (InvalidOperation, ValueError):
            # If provided exchange rate is invalid, keep TRY fields as None
            logger.warning("Invalid exchange rate provided; skipping TRY calculations")
    elif currency and currency.upper() == 'TL':
        # For TL transactions, TL amounts are the same as original amounts
        exchange_rate_decimal = Decimal('1.0')
        amount_try = amount
        commission_try = commission
        net_amount_try = net_amount
    
    # Create transaction using transaction helper
    # Keep PSP as-is (None or string) - don't convert to empty string
    logger.info(f"Creating transaction with PSP: '{psp}' (type: {type(psp)}, will be saved to database)")
    transaction_id = None
    with db_transaction() as session:
        transaction = Transaction(
            client_name=client_name,
            company=company,
            payment_method=payment_method,
            date=transaction_date,
            category=category,
            amount=amount,
            commission=commission,
            net_amount=net_amount,
            currency=currency,
            psp=psp,  # Use psp directly - can be None or string
            notes=description,
            created_by=current_user.id,
            # TRY amounts and exchange rate
            amount_try=amount_try,
            commission_try=commission_try,
            net_amount_try=net_amount_try,
            exchange_rate=exchange_rate_decimal
        )
        
        # Multi-tenancy: Set organization_id automatically
        set_tenant_on_new_record(transaction)
        
        session.add(transaction)
        session.flush()  # Ensure the transaction gets an ID
        transaction_id = transaction.id  # Save ID before commit
        # Transaction will auto-commit here
    
    # Force WAL checkpoint to ensure transaction is immediately visible (SQLite specific)
    try:
        db.session.execute(text("PRAGMA wal_checkpoint(FULL)"))
        db.session.commit()
    except Exception:
        # Ignore if not SQLite
        pass
    
    # Invalidate cache after transaction creation
    try:
        from app.services.query_service import QueryService
        QueryService.invalidate_transaction_cache()
        logger.info("Cache invalidated after API transaction creation")
    except Exception as cache_error:
        logger.warning(f"Failed to invalidate cache after API transaction creation: {cache_error}")
    
    # Reload transaction from database to ensure we have all fields
    transaction = Transaction.query.get(transaction_id)
    if not transaction:
        raise DatabaseError("Transaction was created but could not be retrieved")
    
    logger.info(f"Transaction {transaction_id} reloaded from database - PSP value: '{transaction.psp}'")
    
    # Prepare response data (backward compatible format for frontend)
    transaction_data = {
        'id': transaction.id,
        'client_name': transaction.client_name,
        'amount': float(transaction.amount),
        'commission': float(transaction.commission),
        'net_amount': float(transaction.net_amount),
        'currency': transaction.currency,
        'date': transaction.date.isoformat() if transaction.date else None
    }
    
    # Return standardized response with backward compatibility
    # Frontend expects 'success' and 'transaction' fields at root level
    response_data = success_response(
        data=transaction_data,
        meta={'message': 'Transaction created successfully'}
    )
    
    # Add backward compatibility fields for frontend
    response_data['success'] = True
    response_data['transaction'] = transaction_data
    response_data['message'] = 'Transaction created successfully'
    
    return jsonify(response_data), 201

@transactions_api.route("/debug/company-data")
@login_required
def debug_company_data():
    """Debug endpoint to check company data in database"""
    try:
        # Get sample transactions with company data
        sample_transactions = db.session.query(
            Transaction.client_name,
            Transaction.company,
            Transaction.created_at
        ).filter(
            Transaction.client_name.isnot(None),
            Transaction.client_name != ''
        ).order_by(Transaction.created_at.desc()).limit(10).all()
        
        result = []
        for t in sample_transactions:
            result.append({
                'client_name': t.client_name,
                'company': t.company,
                'created_at': t.created_at.isoformat() if t.created_at else None
            })
        
        return jsonify({
            'total_transactions': Transaction.query.count(),
            'transactions_with_company': db.session.query(Transaction.company).filter(
                Transaction.company.isnot(None),
                Transaction.company != ''
            ).count(),
            'sample_transactions': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@transactions_api.route("/clients")
@login_required
def get_clients():
    """Get clients data (grouped transactions by client) - Optimized with proper error handling"""
    try:
        api_logger.info(f"API Request: GET /clients")
        logger.info("Starting clients query...")
        
        # Add performance tracking
        import time
        start_time = time.time()
        
        # Get the ACTUAL total count of unique clients (without limit) for accurate summary
        actual_total_clients = db.session.query(
            func.count(func.distinct(Transaction.client_name))
        ).filter(
            Transaction.client_name.isnot(None),
            Transaction.client_name != ''
        ).scalar() or 0
        
        logger.info(f"Total unique clients in database: {actual_total_clients}")
        
        # Get transactions grouped by client with additional data including commission and company
        # First get the basic stats - use converted amounts (amount_try) for proper currency conversion
        client_stats = db.session.query(
            Transaction.client_name,
            func.count(Transaction.id).label('transaction_count'),
            # Use amount_try (converted to TRY) if available, otherwise fallback to amount
            func.sum(
                func.coalesce(Transaction.amount_try, Transaction.amount)
            ).label('total_amount'),
            # Use commission_try (converted to TRY) if available, otherwise fallback to commission
            func.sum(
                func.coalesce(Transaction.commission_try, Transaction.commission)
            ).label('total_commission'),
            # Calculate deposits separately (for Net Cash calculation)
            func.sum(
                case(
                    (func.upper(Transaction.category).in_(['DEP', 'DEPOSIT', 'INVESTMENT']),
                     func.abs(func.coalesce(Transaction.amount_try, Transaction.amount))),
                    else_=0
                )
            ).label('total_deposits'),
            # Calculate withdrawals separately (for Net Cash calculation)
            func.sum(
                case(
                    (func.upper(Transaction.category).in_(['WD', 'WITHDRAW', 'WITHDRAWAL']),
                     func.abs(func.coalesce(Transaction.amount_try, Transaction.amount))),
                    else_=0
                )
            ).label('total_withdrawals'),
            # For average, use converted amounts as well
            func.avg(
                func.coalesce(Transaction.amount_try, Transaction.amount)
            ).label('average_amount'),
            func.min(Transaction.created_at).label('first_transaction'),
            func.max(Transaction.created_at).label('last_transaction')
        ).filter(
            Transaction.client_name.isnot(None),
            Transaction.client_name != ''
        ).group_by(Transaction.client_name).limit(1000).all()  # Limit to 1000 clients for performance
        
        logger.info(f"Found {len(client_stats)} unique clients (limited to 1000 for performance)")
        
        # Get company data for all clients in ONE query (optimized - no N+1 problem)
        # Get all client names from our stats
        client_names = [client.client_name for client in client_stats]
        
        # Single query to get most recent company for ALL clients
        # Subquery to get the latest transaction ID for each client with a company
        latest_company_subquery = db.session.query(
            Transaction.client_name,
            func.max(Transaction.created_at).label('max_created_at')
        ).filter(
            Transaction.client_name.in_(client_names),
            Transaction.company.isnot(None),
            Transaction.company != ''
        ).group_by(Transaction.client_name).subquery()
        
        # Main query to get companies for these latest transactions
        company_data = db.session.query(
            Transaction.client_name,
            Transaction.company
        ).join(
            latest_company_subquery,
            and_(
                Transaction.client_name == latest_company_subquery.c.client_name,
                Transaction.created_at == latest_company_subquery.c.max_created_at
            )
        ).all()
        
        # Convert to dictionary for fast lookup
        client_companies = {row.client_name: row.company for row in company_data}
        logger.info(f"Found company data for {len(client_companies)} clients")
        
        # OPTIMIZATION: Use simpler queries to avoid SQLite compatibility issues
        # Get currencies and PSPs for each client
        client_metadata_dict = {}
        
        for client_name in client_names:
            try:
                # Get unique currencies for this client
                currency_query = db.session.query(Transaction.currency).filter(
                    Transaction.client_name == client_name,
                    Transaction.currency.isnot(None),
                    Transaction.currency != ''
                ).distinct().all()
                currencies = [row[0] for row in currency_query]
                
                # Get unique PSPs for this client
                psp_query = db.session.query(Transaction.psp).filter(
                    Transaction.client_name == client_name,
                    Transaction.psp.isnot(None),
                    Transaction.psp != ''
                ).distinct().all()
                psps = [row[0] for row in psp_query]
                
                client_metadata_dict[client_name] = {
                    'currencies': currencies,
                    'psps': psps
                }
            except Exception as e:
                logger.warning(f"Error getting metadata for client {client_name}: {str(e)}")
                client_metadata_dict[client_name] = {
                    'currencies': [],
                    'psps': []
                }
        
        # Get latest payment_method and category for each client in a single query
        latest_data_subquery = db.session.query(
            Transaction.client_name,
            func.max(Transaction.created_at).label('max_created_at')
        ).filter(
            Transaction.client_name.in_(client_names)
        ).group_by(Transaction.client_name).subquery()
        
        latest_transaction_data = db.session.query(
            Transaction.client_name,
            Transaction.payment_method,
            Transaction.category
        ).join(
            latest_data_subquery,
            and_(
                Transaction.client_name == latest_data_subquery.c.client_name,
                Transaction.created_at == latest_data_subquery.c.max_created_at
            )
        ).all()
        
        # Merge latest transaction data into metadata
        for row in latest_transaction_data:
            if row.client_name in client_metadata_dict:
                client_metadata_dict[row.client_name]['payment_method'] = row.payment_method
                client_metadata_dict[row.client_name]['category'] = row.category
        
        logger.info(f"Built metadata for {len(client_metadata_dict)} clients")
        
        clients_data = []
        for client in client_stats:
            try:
                # Fix: Ensure proper type conversion and handle NULL values
                total_amount = float(client.total_amount) if client.total_amount is not None else 0.0
                total_commission = float(client.total_commission) if client.total_commission is not None else 0.0
                total_deposits = float(client.total_deposits) if client.total_deposits is not None else 0.0
                total_withdrawals = float(client.total_withdrawals) if client.total_withdrawals is not None else 0.0
                
                # Calculate Net Cash = Deposits - Withdrawals (Cash Flow formula)
                net_cash = total_deposits - total_withdrawals
                
                # Get pre-calculated metadata for this client (from batch query above)
                metadata = client_metadata_dict.get(client.client_name, {})
                currencies = metadata.get('currencies', [])
                psps = metadata.get('psps', [])
                payment_method = metadata.get('payment_method')
                category = metadata.get('category')
                
                # Fix: Ensure all numeric values are properly converted
                avg_transaction = float(client.average_amount) if client.average_amount is not None else 0.0
                
                # Get company name from our dictionary
                company_name = client_companies.get(client.client_name)
                
                clients_data.append({
                    'client_name': client.client_name,
                    'company_name': company_name,  # Add company name to response
                    'payment_method': payment_method,
                    'category': category,
                    'total_amount': total_amount,
                    'total_commission': total_commission,
                    'total_deposits': total_deposits,
                    'total_withdrawals': total_withdrawals,
                    'total_net': net_cash,  # Now using Net Cash (Deposits - Withdrawals)
                    'transaction_count': client.transaction_count,
                    'first_transaction': client.first_transaction.isoformat() if client.first_transaction else None,
                    'last_transaction': client.last_transaction.isoformat() if client.last_transaction else None,
                    'currencies': currencies,
                    'psps': psps,
                    'avg_transaction': avg_transaction
                })
            except Exception as client_error:
                # Log individual client processing errors but continue
                logger.warning(f"Error processing client {client.client_name}: {str(client_error)}")
                continue
        
        # Sort by total amount descending
        clients_data.sort(key=lambda x: x['total_amount'], reverse=True)
        
        logger.info(f"Successfully built client data for {len(clients_data)} clients")
        
        # If no data found, try alternative method
        if len(clients_data) == 0:
            # No data from aggregation, trying alternative method
            try:
                # Get all unique client names
                unique_clients = db.session.query(Transaction.client_name).filter(
                    Transaction.client_name.isnot(None),
                    Transaction.client_name != ''
                ).distinct().all()
                
                # Found unique clients for alternative calculation
                
                for client_row in unique_clients:
                    client_name = client_row.client_name
                    if not client_name:
                        continue
                        
                    # Get all transactions for this client
                    client_transactions = Transaction.query.filter(
                        Transaction.client_name == client_name
                    ).all()
                    
                    if not client_transactions:
                        continue
                    
                    # Calculate manually using converted amounts (amount_try) for proper currency conversion
                    total_amount = sum(
                        float(t.amount_try) if t.amount_try is not None else float(t.amount) 
                        for t in client_transactions if (t.amount_try is not None or t.amount is not None)
                    )
                    total_commission = sum(
                        float(t.commission_try) if t.commission_try is not None else float(t.commission) 
                        for t in client_transactions if (t.commission_try is not None or t.commission is not None)
                    )
                    
                    # Calculate deposits and withdrawals separately for Net Cash formula
                    total_deposits = sum(
                        abs(float(t.amount_try) if t.amount_try is not None else float(t.amount))
                        for t in client_transactions 
                        if (t.amount_try is not None or t.amount is not None) and 
                           t.category and t.category.upper() in ['DEP', 'DEPOSIT', 'INVESTMENT']
                    )
                    total_withdrawals = sum(
                        abs(float(t.amount_try) if t.amount_try is not None else float(t.amount))
                        for t in client_transactions 
                        if (t.amount_try is not None or t.amount is not None) and 
                           t.category and t.category.upper() in ['WD', 'WITHDRAW', 'WITHDRAWAL']
                    )
                    
                    # Net Cash = Deposits - Withdrawals (Cash Flow formula)
                    net_cash = total_deposits - total_withdrawals
                    
                    # Alternative calculation for client data
                    
                    # Get other data
                    latest_transaction = max(client_transactions, key=lambda x: x.created_at if x.created_at else datetime.min)
                    
                    # Handle company name in fallback method
                    company_name = latest_transaction.company
                    if not company_name or company_name.strip() == '':
                        # Try to find any transaction with company data for this client
                        company_transaction = next((t for t in client_transactions if t.company and t.company.strip() != ''), None)
                        if company_transaction:
                            company_name = company_transaction.company
                        else:
                            company_name = None
                    
                    clients_data.append({
                        'client_name': client_name,
                        'company_name': company_name,  # Add company name from latest transaction
                        'payment_method': latest_transaction.payment_method,
                        'category': latest_transaction.category,
                        'total_amount': total_amount,
                        'total_commission': total_commission,
                        'total_deposits': total_deposits,
                        'total_withdrawals': total_withdrawals,
                        'total_net': net_cash,  # Now using Net Cash (Deposits - Withdrawals)
                        'transaction_count': len(client_transactions),
                        'first_transaction': min(t.created_at for t in client_transactions if t.created_at).isoformat() if any(t.created_at for t in client_transactions) else None,
                        'last_transaction': latest_transaction.created_at.isoformat() if latest_transaction.created_at else None,
                        'currencies': list(set(t.currency for t in client_transactions if t.currency)),
                        'psps': list(set(t.psp for t in client_transactions if t.psp)),
                        'avg_transaction': total_amount / len(client_transactions) if client_transactions else 0.0
                    })
                
                # Sort again
                clients_data.sort(key=lambda x: x['total_amount'], reverse=True)
                
            except Exception as fallback_error:
                # Fallback method failed, continuing with empty data
                pass
        
        # Calculate summary metrics for Client Insights cards
        from datetime import timedelta
        
        # New clients this month (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        new_clients_count = len([c for c in client_stats if c.first_transaction and c.first_transaction >= thirty_days_ago])
        
        # Average transaction value across all clients
        total_transactions = sum(c.transaction_count for c in client_stats)
        total_volume = sum(float(c.total_amount or 0) for c in client_stats)
        avg_transaction_value = total_volume / total_transactions if total_transactions > 0 else 0
        
        # Top client by volume
        top_by_volume = max(client_stats, key=lambda c: float(c.total_amount or 0)) if client_stats else None
        top_by_volume_data = {
            'client_name': top_by_volume.client_name if top_by_volume else None,
            'total_amount': float(top_by_volume.total_amount or 0) if top_by_volume else 0
        } if top_by_volume else None
        
        # Top client by commission
        top_by_commission = max(client_stats, key=lambda c: float(c.total_commission or 0)) if client_stats else None
        top_by_commission_data = {
            'client_name': top_by_commission.client_name if top_by_commission else None,
            'total_commission': float(top_by_commission.total_commission or 0) if top_by_commission else 0
        } if top_by_commission else None
        
        # Most active client (by transaction count)
        most_active = max(client_stats, key=lambda c: c.transaction_count) if client_stats else None
        most_active_data = {
            'client_name': most_active.client_name if most_active else None,
            'transaction_count': most_active.transaction_count if most_active else 0
        } if most_active else None
        
        # Multi-currency clients count
        multi_currency_count = len([c for c in client_metadata_dict.values() if len(c.get('currencies', [])) > 1])
        
        summary = {
            'total_clients': actual_total_clients,  # Use actual count, not limited result
            'new_clients_this_month': new_clients_count,
            'avg_transaction_value': avg_transaction_value,
            'multi_currency_count': multi_currency_count,
            'top_by_volume': top_by_volume_data,
            'top_by_commission': top_by_commission_data,
            'most_active': most_active_data,
            'total_transactions': total_transactions,
            'total_volume': total_volume
        }
        
        # Performance tracking completed
        elapsed_time = time.time() - start_time
        logger.info(f"Returning {len(clients_data)} clients successfully in {elapsed_time:.2f} seconds")
        
        return jsonify({
            'clients': clients_data,
            'summary': summary
        }), 200
        
    except Exception as e:
        # Performance tracking completed
            
        # Log error with full traceback for debugging
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Error in get_clients endpoint: {str(e)}")
        logger.error(f"Full traceback: {error_traceback}")
        api_logger.error(f"Error in get_clients: {str(e)}", user_id=current_user.id, context="get_clients")
        
        # Return empty array instead of error to prevent UI crashes
        return jsonify([]), 200

@transactions_api.route("/search-clients")
@login_required
def search_clients():
    """Search for clients by name - returns client information and transactions"""
    try:
        search_term = request.args.get('q', '').strip()
        
        if not search_term or len(search_term) < 2:
            return jsonify({
                'clients': [],
                'transactions': [],
                'message': 'Search term must be at least 2 characters'
            }), 200
        
        # Search for clients matching the search term (case insensitive)
        # Get unique client names that match
        matching_clients_query = db.session.query(
            Transaction.client_name
        ).filter(
            Transaction.client_name.isnot(None),
            Transaction.client_name != '',
            func.lower(Transaction.client_name).like(f'%{search_term.lower()}%')
        ).distinct().limit(20).all()
        
        client_names = [row[0] for row in matching_clients_query]
        
        if not client_names:
            return jsonify({
                'clients': [],
                'transactions': [],
                'message': f'No clients found matching "{search_term}"'
            }), 200
        
        # Get client statistics for matching clients
        client_stats = db.session.query(
            Transaction.client_name,
            func.count(Transaction.id).label('transaction_count'),
            func.sum(func.coalesce(Transaction.amount_try, Transaction.amount)).label('total_amount'),
            func.sum(func.coalesce(Transaction.commission_try, Transaction.commission)).label('total_commission'),
            func.min(Transaction.date).label('first_transaction'),
            func.max(Transaction.date).label('last_transaction')
        ).filter(
            Transaction.client_name.in_(client_names)
        ).group_by(Transaction.client_name).all()
        
        # Get recent transactions for these clients
        recent_transactions = db.session.query(Transaction).filter(
            Transaction.client_name.in_(client_names)
        ).order_by(Transaction.date.desc(), Transaction.created_at.desc()).limit(50).all()
        
        # Format client data
        clients_data = []
        for client in client_stats:
            clients_data.append({
                'client_name': client.client_name,
                'transaction_count': client.transaction_count,
                'total_amount': float(client.total_amount) if client.total_amount else 0.0,
                'total_commission': float(client.total_commission) if client.total_commission else 0.0,
                'first_transaction': client.first_transaction.strftime('%Y-%m-%d') if client.first_transaction else None,
                'last_transaction': client.last_transaction.strftime('%Y-%m-%d') if client.last_transaction else None,
            })
        
        # Format transaction data
        transactions_data = []
        for tx in recent_transactions:
            transactions_data.append({
                'id': tx.id,
                'client_name': tx.client_name,
                'date': tx.date.strftime('%Y-%m-%d') if tx.date else None,
                'amount': float(tx.amount) if tx.amount else 0.0,
                'currency': tx.currency,
                'category': tx.category,
                'psp': tx.psp,
                'payment_method': tx.payment_method,
                'commission': float(tx.commission) if tx.commission else 0.0,
                'net_amount': float(tx.net_amount) if tx.net_amount else 0.0,
            })
        
        return jsonify({
            'clients': clients_data,
            'transactions': transactions_data,
            'search_term': search_term,
            'total_clients': len(clients_data),
            'total_transactions': len(transactions_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error in search_clients endpoint: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'error': 'Failed to search clients',
            'clients': [],
            'transactions': []
        }), 500

@transactions_api.route("/client-details/<path:client_name>")
@login_required
def get_client_details(client_name):
    """Get comprehensive details for a specific client"""
    try:
        # Decode the client name from URL path
        from urllib.parse import unquote
        decoded_client_name = unquote(client_name)
        if not decoded_client_name:
            return jsonify({'error': 'Client name is required'}), 400
        
        # Get all transactions for this client
        client_transactions = db.session.query(Transaction).filter(
            Transaction.client_name == decoded_client_name
        ).order_by(Transaction.date.desc(), Transaction.created_at.desc()).all()
        
        if not client_transactions:
            return jsonify({
                'error': f'Client "{decoded_client_name}" not found',
                'client_name': decoded_client_name
            }), 404
        
        # Calculate comprehensive statistics
        total_amount = sum(float(tx.amount_try) if tx.amount_try else float(tx.amount or 0) for tx in client_transactions)
        total_commission = sum(float(tx.commission_try) if tx.commission_try else float(tx.commission or 0) for tx in client_transactions)
        total_net = sum(float(tx.net_amount or 0) for tx in client_transactions)
        
        # Calculate deposits and withdrawals
        deposits = sum(
            abs(float(tx.amount_try) if tx.amount_try else float(tx.amount or 0))
            for tx in client_transactions
            if tx.category and tx.category.upper() in ['DEP', 'DEPOSIT', 'INVESTMENT']
        )
        withdrawals = sum(
            abs(float(tx.amount_try) if tx.amount_try else float(tx.amount or 0))
            for tx in client_transactions
            if tx.category and tx.category.upper() in ['WD', 'WITHDRAW', 'WITHDRAWAL']
        )
        
        # Get unique values
        currencies = list(set(tx.currency for tx in client_transactions if tx.currency))
        psps = list(set(tx.psp for tx in client_transactions if tx.psp))
        payment_methods = list(set(tx.payment_method for tx in client_transactions if tx.payment_method))
        categories = list(set(tx.category for tx in client_transactions if tx.category))
        
        # Get company name (most recent)
        company_name = None
        for tx in client_transactions:
            if tx.company:
                company_name = tx.company
                break
        
        # Get date range
        dates = [tx.date for tx in client_transactions if tx.date]
        first_transaction = min(dates).strftime('%Y-%m-%d') if dates else None
        last_transaction = max(dates).strftime('%Y-%m-%d') if dates else None
        
        # Calculate average transaction
        avg_transaction = total_amount / len(client_transactions) if client_transactions else 0
        
        # Format transactions
        transactions_data = []
        for tx in client_transactions:
            transactions_data.append({
                'id': tx.id,
                'date': tx.date.strftime('%Y-%m-%d') if tx.date else None,
                'amount': float(tx.amount_try) if tx.amount_try else float(tx.amount or 0),
                'currency': tx.currency,
                'category': tx.category,
                'psp': tx.psp,
                'payment_method': tx.payment_method,
                'commission': float(tx.commission_try) if tx.commission_try else float(tx.commission or 0),
                'net_amount': float(tx.net_amount or 0),
                'company': tx.company,
                'notes': tx.notes,
            })
        
        return jsonify({
            'client_name': decoded_client_name,
            'company_name': company_name,
            'statistics': {
                'transaction_count': len(client_transactions),
                'total_amount': total_amount,
                'total_commission': total_commission,
                'total_net': total_net,
                'total_deposits': deposits,
                'total_withdrawals': withdrawals,
                'avg_transaction': avg_transaction,
                'first_transaction': first_transaction,
                'last_transaction': last_transaction,
            },
            'metadata': {
                'currencies': currencies,
                'psps': psps,
                'payment_methods': payment_methods,
                'categories': categories,
            },
            'transactions': transactions_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_client_details endpoint: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'error': 'Failed to fetch client details'
        }), 500

@transactions_api.route("/psp_summary_stats")
@login_required
@limiter.limit("20 per minute, 200 per hour")  # Dashboard endpoint - frequently accessed
def get_psp_summary_stats():
    """Get PSP summary statistics including allocations with caching"""
    try:
        api_logger.info(f"API Request: GET /psp_summary_stats")
        logger.info("Starting PSP summary stats query...")
        
        # Check cache first
        cache_key = f"psp_summary:{current_user.id}"
        cached_result = cache_service.get(cache_key)
        if cached_result is not None:
            api_logger.info(f"Cache get: {cache_key} (hit)")
            return jsonify(cached_result), 200
        
        # Get PSP statistics from actual transactions using TRY amounts
        # Calculate deposits and withdrawals separately, then compute net total
        # Use separate queries to avoid SQLAlchemy case function issues
        psp_stats = db.session.query(
            Transaction.psp,
            func.count(Transaction.id).label('transaction_count'),
            func.sum(func.coalesce(Transaction.amount_try, Transaction.amount)).label('total_amount_try'),
            func.avg(func.coalesce(Transaction.amount_try, Transaction.amount)).label('average_amount_try')
        ).filter(
            Transaction.psp.isnot(None),
            Transaction.psp != ''
        ).group_by(Transaction.psp).all()
        
        # Get deposits separately
        psp_deposits = db.session.query(
            Transaction.psp,
            func.sum(func.coalesce(Transaction.amount_try, Transaction.amount)).label('total_deposits_try')
        ).filter(
            Transaction.psp.isnot(None),
            Transaction.psp != '',
            func.upper(Transaction.category).in_(['DEP', 'DEPOSIT', 'INVESTMENT'])
        ).group_by(Transaction.psp).all()
        
        # Get withdrawals separately
        psp_withdrawals = db.session.query(
            Transaction.psp,
            func.sum(func.coalesce(Transaction.amount_try, Transaction.amount)).label('total_withdrawals_try')
        ).filter(
            Transaction.psp.isnot(None),
            Transaction.psp != '',
            func.upper(Transaction.category).in_(['WD', 'WITHDRAW', 'WITHDRAWAL'])
        ).group_by(Transaction.psp).all()
        
        # Get allocations from PSPAllocation table (if table exists)
        allocations_dict = {}
        try:
            from app.models.financial import PSPAllocation
            # Check if table exists before querying
            inspector = db.inspect(db.engine)
            table_names = inspector.get_table_names()
            
            if 'psp_allocation' in table_names:
                psp_allocations = db.session.query(
                    PSPAllocation.psp_name,
                    func.sum(PSPAllocation.allocation_amount).label('total_allocations')
                ).group_by(PSPAllocation.psp_name).all()
                
                allocations_dict = {psp.psp_name: float(psp.total_allocations) if psp.total_allocations else 0.0 for psp in psp_allocations}
            else:
                logger.warning("PSPAllocation table does not exist, skipping allocations")
                allocations_dict = {}
        except Exception as alloc_error:
            logger.warning(f"Error fetching PSP allocations: {alloc_error}, continuing without allocations")
            allocations_dict = {}
        
        # Create lookup dictionaries
        deposits_dict = {psp.psp: float(psp.total_deposits_try) if psp.total_deposits_try else 0.0 for psp in psp_deposits}
        withdrawals_dict = {psp.psp: float(psp.total_withdrawals_try) if psp.total_withdrawals_try else 0.0 for psp in psp_withdrawals}
        
        logger.info(f"PSP stats query completed, found {len(psp_stats)} PSPs")
        
        psp_data = []
        for psp in psp_stats:
            # Calculate net total: deposits - withdrawals using lookup dictionaries
            total_deposits = deposits_dict.get(psp.psp, 0.0)
            total_withdrawals = withdrawals_dict.get(psp.psp, 0.0)
            total_amount = total_deposits + total_withdrawals  # Net total (deposits + withdrawals, since withdrawals are negative)
            
            # Get total allocations for this PSP
            total_allocations = allocations_dict.get(psp.psp, 0.0)
            
            # Get the actual commission rate for this PSP from options (no defaults)
            commission_rate = None
            try:
                from app.models.config import Option
                psp_option = Option.query.filter_by(
                    field_name='psp',
                    value=psp.psp,
                    is_active=True
                ).first()
                
                if psp_option and psp_option.commission_rate is not None:
                    commission_rate = float(psp_option.commission_rate) * 100  # Convert to percentage
            except Exception:
                pass  # Skip if error occurs
            
            # Calculate commission based on total deposits only (not net total)
            # Tether is company's own KASA, so no commission calculations
            if psp.psp.upper() == 'TETHER':
                total_commission = 0.0
                total_net = total_amount
                total_allocations = 0.0  # No allocations for internal company KASA
                logger.info(f"Summary PSP {psp.psp}: internal company KASA, deposits={total_deposits}, commission=0")
            elif commission_rate is not None:
                total_commission = total_deposits * (commission_rate / 100)
                total_net = total_amount - total_commission
                logger.info(f"Summary PSP {psp.psp}: deposits={total_deposits}, rate={commission_rate}%, commission={total_commission}")
            else:
                total_commission = 0.0
                total_net = total_amount
                logger.info(f"Summary PSP {psp.psp}: no commission rate found, deposits={total_deposits}, commission=0")
            
            psp_data.append({
                'psp': psp.psp,
                'total_amount': total_amount,
                'total_deposits': total_deposits,
                'total_withdrawals': total_withdrawals,
                'total_commission': total_commission,
                'total_net': total_net,
                'total_allocations': total_allocations,
                'transaction_count': psp.transaction_count,
                'commission_rate': commission_rate
            })
        
        # Sort by total amount descending
        psp_data.sort(key=lambda x: x['total_amount'], reverse=True)
        
        logger.info(f"PSP summary stats completed successfully, returning {len(psp_data)} PSPs")
        
        # Cache the result
        cache_service.set(cache_key, psp_data, ttl=300)
        api_logger.info(f"Cache set: {cache_key} (miss)")
        
        # Invalidate cache to ensure fresh data
        try:
            from app.services.query_service import QueryService
            QueryService.invalidate_transaction_cache()
            logger.info("Cache invalidated after PSP summary stats")
        except Exception as cache_error:
            logger.warning(f"Failed to invalidate cache after PSP summary stats: {cache_error}")
        
        return jsonify(psp_data)
        
    except Exception as e:
        logger.error(f"Error in PSP summary stats: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return jsonify({
            'error': 'Failed to retrieve PSP summary statistics',
            'message': str(e)
        }), 500

@transactions_api.route("/psp_monthly_stats")
@login_required
def get_psp_monthly_stats():
    """Get PSP monthly statistics with date filtering and caching
    
    PHASE 1 OPTIMIZATION: Lazy loading support
    - include_daily=false: Returns only summary (faster)
    - include_daily=true: Returns full daily breakdown (default)
    """
    import time
    start_time = time.time()
    try:
        api_logger.info(f"API Request: GET /psp_monthly_stats")
        logger.info("Starting PSP monthly stats query...")
        
        # Get query parameters with validation
        year = request.args.get('year', datetime.now().year, type=int)
        month = request.args.get('month', datetime.now().month, type=int)
        
        # PHASE 1: Lazy loading - optionally exclude daily breakdown
        include_daily = request.args.get('include_daily', 'true').lower() == 'true'
        
        # Cache disabled for real-time data - kullanici her zaman guncel veri gormek istiyor
        # cache_key = f"pipeline:psp_monthly_stats:{year}:{month}"
        # cached_result = cache_service.get(cache_key)
        # if cached_result is not None:
        #     logger.info(f"CACHE HIT: Returning cached PSP monthly stats for {year}-{month:02d}")
        #     return jsonify(cached_result), 200
        
        # Validate year and month
        if not (1 <= month <= 12):
            return jsonify({'error': 'Invalid month. Must be between 1 and 12.'}), 400
        if year < 2020 or year > 2030:
            return jsonify({'error': 'Invalid year. Must be between 2020 and 2030.'}), 400
        
        logger.info(f"Fetching monthly stats for {year}-{month:02d}")
        
        # Calculate date range for the month
        try:
            start_date = datetime(year, month, 1).date()
            if month == 12:
                end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
        except ValueError as e:
            logger.error(f"Invalid date range: {e}")
            return jsonify({'error': 'Invalid date range'}), 400
        
        logger.info(f"Date range: {start_date} to {end_date}")
        
        # Get PSP statistics for the specific month
        # For Tether, use USD amounts; for others, use TRY amounts
        psp_stats = db.session.query(
            Transaction.psp,
            func.count(Transaction.id).label('transaction_count'),
            func.sum(
                case(
                    (func.upper(Transaction.psp) == 'TETHER', func.coalesce(Transaction.amount, 0)),
                    else_=func.coalesce(Transaction.amount_try, Transaction.amount)
                )
            ).label('total_amount'),
            func.avg(
                case(
                    (func.upper(Transaction.psp) == 'TETHER', func.coalesce(Transaction.amount, 0)),
                    else_=func.coalesce(Transaction.amount_try, Transaction.amount)
                )
            ).label('average_amount')
        ).filter(
            Transaction.psp.isnot(None),
            Transaction.psp != '',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).group_by(Transaction.psp).all()
        
        # Get PSPs with high DEVIR (>100) even if they have no transactions in this month
        # These PSPs need to be tracked due to their debt
        high_devir_psps = []
        try:
            from app.models.financial import PSPDevir
            # Get the most recent DEVIR for each PSP
            latest_devir_subquery = db.session.query(
                PSPDevir.psp_name,
                func.max(PSPDevir.date).label('latest_date')
            ).group_by(PSPDevir.psp_name).subquery()
            
            high_devir_psps = db.session.query(
                PSPDevir.psp_name,
                PSPDevir.devir_amount
            ).join(
                latest_devir_subquery,
                (PSPDevir.psp_name == latest_devir_subquery.c.psp_name) &
                (PSPDevir.date == latest_devir_subquery.c.latest_date)
            ).filter(
                PSPDevir.devir_amount > 100
            ).all()
            
            logger.info(f"Found {len(high_devir_psps)} PSPs with DEVIR > 100")
        except Exception as e:
            logger.warning(f"Failed to get high DEVIR PSPs: {e}")
            high_devir_psps = []
        
        # Get PSPs with any DEVIR history (rollovers from past months)
        try:
            from app.models.financial import PSPDevir
            # Get all PSPs that have any DEVIR records (indicating they had rollovers)
            psp_devir_history = db.session.query(PSPDevir.psp_name).distinct().all()
            psp_with_devir_history = {psp.psp_name for psp in psp_devir_history}
            logger.info(f"Found {len(psp_with_devir_history)} PSPs with DEVIR history: {sorted(psp_with_devir_history)}")
        except Exception as e:
            logger.warning(f"Failed to get PSPs with DEVIR history: {e}")
            psp_with_devir_history = set()
        
        # Get unique PSP names from transaction-based and high DEVIR PSPs
        transaction_psps = {psp.psp for psp in psp_stats}
        high_devir_psp_names = {psp.psp_name for psp in high_devir_psps}
        
        # Combine PSPs: those with DEVIR history + those with transactions + those with high DEVIR
        all_psp_names = psp_with_devir_history.union(transaction_psps).union(high_devir_psp_names)
        
        # Create a comprehensive PSP list with transaction data
        comprehensive_psp_stats = []
        for psp_name in all_psp_names:
            # Find transaction data for this PSP
            psp_transaction_data = next((psp for psp in psp_stats if psp.psp == psp_name), None)
            
            if psp_transaction_data:
                # PSP has transactions in this month
                comprehensive_psp_stats.append(psp_transaction_data)
            else:
                # PSP has no transactions but high DEVIR - create dummy entry
                from sqlalchemy import text
                dummy_psp = type('DummyPSP', (), {
                    'psp': psp_name,
                    'transaction_count': 0,
                    'total_amount': 0.0,
                    'average_amount': 0.0
                })()
                comprehensive_psp_stats.append(dummy_psp)
                logger.info(f"Added PSP {psp_name} with high DEVIR but no transactions")
        
        # Use the comprehensive PSP list
        psp_stats = comprehensive_psp_stats
        
        # Get deposits for the month
        # For Tether, use USD amounts; for others, use TRY amounts
        psp_deposits = db.session.query(
            Transaction.psp,
            func.sum(
                case(
                    (func.upper(Transaction.psp) == 'TETHER', func.coalesce(Transaction.amount, 0)),
                    else_=func.coalesce(Transaction.amount_try, Transaction.amount)
                )
            ).label('total_deposits')
        ).filter(
            Transaction.psp.isnot(None),
            Transaction.psp != '',
            func.upper(Transaction.category).in_(['DEP', 'DEPOSIT', 'INVESTMENT']),
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).group_by(Transaction.psp).all()
        
        # Get withdrawals for the month
        # For Tether, use USD amounts; for others, use TRY amounts
        psp_withdrawals = db.session.query(
            Transaction.psp,
            func.sum(
                case(
                    (func.upper(Transaction.psp) == 'TETHER', func.coalesce(Transaction.amount, 0)),
                    else_=func.coalesce(Transaction.amount_try, Transaction.amount)
                )
            ).label('total_withdrawals')
        ).filter(
            Transaction.psp.isnot(None),
            Transaction.psp != '',
            func.upper(Transaction.category).in_(['WD', 'WITHDRAW', 'WITHDRAWAL']),
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).group_by(Transaction.psp).all()
        
        # Get allocations for the month from PSPAllocation table
        try:
            from app.models.financial import PSPAllocation
            psp_allocations = db.session.query(
                PSPAllocation.psp_name,
                func.sum(PSPAllocation.allocation_amount).label('total_allocations')
            ).filter(
                PSPAllocation.date >= start_date,
                PSPAllocation.date <= end_date
            ).group_by(PSPAllocation.psp_name).all()
        except ImportError as e:
            logger.warning(f"PSPAllocation import failed: {e}. Using empty allocations.")
            psp_allocations = []
        except Exception as e:
            logger.warning(f"Error querying PSPAllocation: {e}. Using empty allocations.")
            psp_allocations = []
        
        # Create lookup dictionaries
        deposits_dict = {psp.psp: float(psp.total_deposits) if psp.total_deposits else 0.0 for psp in psp_deposits}
        withdrawals_dict = {psp.psp: float(psp.total_withdrawals) if psp.total_withdrawals else 0.0 for psp in psp_withdrawals}
        allocations_dict = {psp.psp_name: float(psp.total_allocations) if psp.total_allocations else 0.0 for psp in psp_allocations}
        
        # Load manual DEVIR overrides for first day of month only
        devir_overrides_cache = {}
        try:
            from app.models.financial import PSPDevir
            # Get all DEVIR overrides
            devir_overrides = PSPDevir.query.all()
            for override in devir_overrides:
                if override.psp_name not in devir_overrides_cache:
                    devir_overrides_cache[override.psp_name] = {}
                devir_overrides_cache[override.psp_name][override.date] = override.devir_amount
            logger.info(f"Loaded {len(devir_overrides)} DEVIR overrides for first day of month")
        except Exception as e:
            logger.warning(f"Failed to load DEVIR overrides: {e}")
            devir_overrides_cache = {}
        
        # BUG FIX: Pre-load manual KASA TOP overrides for the entire month
        # This prevents manually edited KASA TOP values from being lost during recalculation
        kasa_top_overrides_cache = {}
        try:
            from app.models.financial import PSPKasaTop
            # Get all KASA TOP overrides for the month being calculated
            kasa_top_overrides = PSPKasaTop.query.filter(
                PSPKasaTop.date >= start_date,
                PSPKasaTop.date <= end_date
            ).all()
            for override in kasa_top_overrides:
                if override.psp_name not in kasa_top_overrides_cache:
                    kasa_top_overrides_cache[override.psp_name] = {}
                kasa_top_overrides_cache[override.psp_name][override.date] = override.kasa_top_amount
            logger.info(f"Loaded {len(kasa_top_overrides)} KASA TOP overrides for {year}-{month:02d}")
        except Exception as e:
            logger.warning(f"Failed to load KASA TOP overrides: {e}")
            kasa_top_overrides_cache = {}
        
        calculated_devirs_to_store = []
        
        logger.info(f"Monthly PSP stats query completed, found {len(psp_stats)} PSPs")
        
        # PERFORMANCE OPTIMIZATION: Bulk query all PSP daily data at once instead of N+1 queries
        query_start = time.time()
        
        # Get ALL daily deposits for ALL PSPs in one query
        all_daily_deposits = db.session.query(
            Transaction.psp,
            Transaction.date,
            func.sum(
                case(
                    (func.upper(Transaction.psp) == 'TETHER', func.coalesce(Transaction.amount, 0)),
                    else_=func.coalesce(Transaction.amount_try, Transaction.amount)
                )
            ).label('daily_deposits'),
            func.count(Transaction.id).label('deposit_count')
        ).filter(
            Transaction.psp.in_([psp.psp for psp in psp_stats]),
            func.upper(Transaction.category).in_(['DEP', 'DEPOSIT', 'INVESTMENT']),
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).group_by(Transaction.psp, Transaction.date).all()
        
        # Get ALL daily withdrawals for ALL PSPs in one query
        all_daily_withdrawals = db.session.query(
            Transaction.psp,
            Transaction.date,
            func.sum(
                case(
                    (func.upper(Transaction.psp) == 'TETHER', func.coalesce(Transaction.amount, 0)),
                    else_=func.coalesce(Transaction.amount_try, Transaction.amount)
                )
            ).label('daily_withdrawals'),
            func.count(Transaction.id).label('withdrawal_count')
        ).filter(
            Transaction.psp.in_([psp.psp for psp in psp_stats]),
            func.upper(Transaction.category).in_(['WD', 'WITHDRAW', 'WITHDRAWAL']),
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).group_by(Transaction.psp, Transaction.date).all()
        
        # Get ALL daily totals for ALL PSPs in one query
        all_daily_totals = db.session.query(
            Transaction.psp,
            Transaction.date,
            func.sum(
                case(
                    (func.upper(Transaction.psp) == 'TETHER', func.coalesce(Transaction.amount, 0)),
                    else_=func.coalesce(Transaction.amount_try, Transaction.amount)
                )
            ).label('daily_total'),
            func.count(Transaction.id).label('transaction_count')
        ).filter(
            Transaction.psp.in_([psp.psp for psp in psp_stats]),
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).group_by(Transaction.psp, Transaction.date).all()
        
        # Get ALL daily allocations for ALL PSPs in one query
        all_daily_allocations = db.session.query(
            PSPAllocation.psp_name,
            PSPAllocation.date,
            func.sum(PSPAllocation.allocation_amount).label('daily_allocations')
        ).filter(
            PSPAllocation.psp_name.in_([psp.psp for psp in psp_stats]),
            PSPAllocation.date >= start_date,
            PSPAllocation.date <= end_date
        ).group_by(PSPAllocation.psp_name, PSPAllocation.date).all()
        
        query_time = time.time() - query_start
        logger.info(f"PERFORMANCE: Bulk queries completed in {query_time:.2f}s (4 queries instead of {len(psp_stats) * 4})")
        
        # Build lookup dictionaries for quick access
        deposits_lookup = {}
        for row in all_daily_deposits:
            if row.psp not in deposits_lookup:
                deposits_lookup[row.psp] = {}
            deposits_lookup[row.psp][row.date] = (float(row.daily_deposits) if row.daily_deposits else 0.0, row.deposit_count)
        
        withdrawals_lookup = {}
        for row in all_daily_withdrawals:
            if row.psp not in withdrawals_lookup:
                withdrawals_lookup[row.psp] = {}
            withdrawals_lookup[row.psp][row.date] = (float(row.daily_withdrawals) if row.daily_withdrawals else 0.0, row.withdrawal_count)
        
        totals_lookup = {}
        for row in all_daily_totals:
            if row.psp not in totals_lookup:
                totals_lookup[row.psp] = {}
            totals_lookup[row.psp][row.date] = (float(row.daily_total) if row.daily_total else 0.0, row.transaction_count)
        
        allocations_lookup = {}
        for row in all_daily_allocations:
            if row.psp_name not in allocations_lookup:
                allocations_lookup[row.psp_name] = {}
            allocations_lookup[row.psp_name][row.date] = float(row.daily_allocations) if row.daily_allocations else 0.0
        
        # PERFORMANCE OPTIMIZATION: Pre-load previous month's last day data for all PSPs
        # This eliminates N queries when calculating first day of month DEVIR
        prev_month_last_day = start_date - timedelta(days=1)
        prev_month_data_lookup = {}
        
        try:
            from app.models.financial import PSPDevir, PSPAllocation
            
            # Get previous day's DEVIR for all PSPs in one query
            prev_devirs = db.session.query(
                PSPDevir.psp_name,
                PSPDevir.devir_amount
            ).filter(
                PSPDevir.psp_name.in_([psp.psp for psp in psp_stats]),
                PSPDevir.date == prev_month_last_day
            ).all()
            
            # Get previous day's allocations for all PSPs in one query
            prev_allocations = db.session.query(
                PSPAllocation.psp_name,
                func.sum(PSPAllocation.allocation_amount).label('total_allocations')
            ).filter(
                PSPAllocation.psp_name.in_([psp.psp for psp in psp_stats]),
                PSPAllocation.date == prev_month_last_day
            ).group_by(PSPAllocation.psp_name).all()
            
            # Get previous day's transactions for all PSPs in one query
            prev_deposits = db.session.query(
                Transaction.psp,
                func.sum(
                    case(
                        (func.upper(Transaction.psp) == 'TETHER', func.coalesce(Transaction.amount, 0)),
                        else_=func.coalesce(Transaction.amount_try, Transaction.amount)
                    )
                ).label('deposits')
            ).filter(
                Transaction.psp.in_([psp.psp for psp in psp_stats]),
                func.upper(Transaction.category).in_(['DEP', 'DEPOSIT', 'INVESTMENT']),
                Transaction.date == prev_month_last_day
            ).group_by(Transaction.psp).all()
            
            prev_withdrawals = db.session.query(
                Transaction.psp,
                func.sum(
                    case(
                        (func.upper(Transaction.psp) == 'TETHER', func.coalesce(Transaction.amount, 0)),
                        else_=func.coalesce(Transaction.amount_try, Transaction.amount)
                    )
                ).label('withdrawals')
            ).filter(
                Transaction.psp.in_([psp.psp for psp in psp_stats]),
                func.upper(Transaction.category).in_(['WD', 'WITHDRAW', 'WITHDRAWAL']),
                Transaction.date == prev_month_last_day
            ).group_by(Transaction.psp).all()
            
            # Build lookup dictionary
            for psp in psp_stats:
                psp_name = psp.psp
                prev_devir = next((d.devir_amount for d in prev_devirs if d.psp_name == psp_name), 0.0)
                prev_alloc = next((a.total_allocations for a in prev_allocations if a.psp_name == psp_name), 0.0)
                prev_dep = next((d.deposits for d in prev_deposits if d.psp == psp_name), 0.0)
                prev_wd = next((w.withdrawals for w in prev_withdrawals if w.psp == psp_name), 0.0)
                
                # Calculate previous day's NET and KASA TOP
                from app.services.commission_rate_service import CommissionRateService
                prev_rate = CommissionRateService.get_commission_rate_percentage(psp_name, prev_month_last_day)
                prev_commission = float(prev_dep) * (prev_rate / 100) if prev_rate else 0.0
                prev_total = float(prev_dep) + float(prev_wd)
                prev_net = prev_total - prev_commission
                prev_kasa_top = prev_net + float(prev_devir)
                
                prev_month_data_lookup[psp_name] = {
                    'kasa_top': prev_kasa_top,
                    'tahs_tutari': float(prev_alloc) if prev_alloc else 0.0,
                    'devir': float(prev_devir)
                }
            
            logger.info(f"PERFORMANCE: Pre-loaded previous month data for {len(prev_month_data_lookup)} PSPs in bulk")
        except Exception as e:
            logger.warning(f"Could not pre-load previous month data: {e}")
            prev_month_data_lookup = {}
        
        # Get daily breakdown for each PSP using the lookup dictionaries
        daily_breakdown = {}
        for psp in psp_stats:
            # Use pre-built lookup dictionaries for this PSP (no more queries!)
            psp_deposits_by_date = deposits_lookup.get(psp.psp, {})
            psp_withdrawals_by_date = withdrawals_lookup.get(psp.psp, {})
            psp_totals_by_date = totals_lookup.get(psp.psp, {})
            psp_allocations_by_date = allocations_lookup.get(psp.psp, {})
            
            # Build daily breakdown
            daily_data = []
            
            # DEVIR FIX: Process ALL days in month to maintain DEVIR continuity
            # Previous optimization (only processing days with data) broke DEVIR chain
            # When a day has no transactions/allocations, DEVIR should carry forward
            # Formula: DEVIR = Previous Day KASA TOP - Previous Day TAHS TUTARI
            # This requires processing every day sequentially
            import calendar
            from datetime import date as date_class
            days_in_month = calendar.monthrange(year, month)[1]
            
            all_dates = set()
            # Add all days in the month to ensure DEVIR continuity
            for day in range(1, days_in_month + 1):
                all_dates.add(date_class(year, month, day))
            
            # Note: Response is cached for 60 seconds to maintain performance
            
            # Reduced logging - only log every 5th PSP
            if len(psp_stats) == 0 or (psp_stats.index(psp) % 5 == 0):
                logger.info(f"Processing all {len(all_dates)} days for {psp.psp} in {year}-{month:02d}")
            
            # Filter dates to only include those within the current month
            filtered_dates = [date for date in sorted(all_dates) if start_date <= date <= end_date]
            
            # Process dates in chronological order to ensure previous day data is available
            for date in sorted(filtered_dates):
                # Extract values from lookup dictionaries (tuples for deposits/withdrawals/totals)
                daily_deposits_data = psp_deposits_by_date.get(date, (0.0, 0))
                daily_deposits_amount = daily_deposits_data[0] if isinstance(daily_deposits_data, tuple) else daily_deposits_data
                
                daily_withdrawals_data = psp_withdrawals_by_date.get(date, (0.0, 0))
                daily_withdrawals_amount = daily_withdrawals_data[0] if isinstance(daily_withdrawals_data, tuple) else daily_withdrawals_data
                
                daily_totals_data = psp_totals_by_date.get(date, (0.0, 0))
                daily_total_amount = daily_totals_data[0] if isinstance(daily_totals_data, tuple) else daily_totals_data
                transaction_count = daily_totals_data[1] if isinstance(daily_totals_data, tuple) else 0
                
                daily_total = daily_deposits_amount + daily_withdrawals_amount  # deposits + withdrawals (since withdrawals are negative)
                daily_allocations = psp_allocations_by_date.get(date, 0.0)
                
                # Initialize daily_rollover to prevent UnboundLocalError
                daily_rollover = 0.0
                
                # OPTIMIZATION: Get commission rate once per PSP (cached), not per day
                commission_rate = None
                try:
                    from app.services.commission_rate_service import CommissionRateService
                    # Use cached rate lookup (much faster)
                    commission_rate = CommissionRateService.get_commission_rate_percentage(psp.psp, date)
                except Exception as e:
                    pass
                
                if commission_rate is not None:
                    daily_commission = daily_deposits_amount * (commission_rate / 100)
                    # FIXED: NET = TOPLAM - KOMISYON (deposits + withdrawals - commission)
                    # Commission is calculated from deposits only, but NET includes withdrawals
                    daily_net = daily_total - daily_commission
                else:
                    daily_commission = 0.0
                    daily_net = daily_total
                
                # Check if this is the first day of the month
                is_first_day_of_month = (date.day == 1)
                
                # KASA TOP calculation moved to after DEVIR calculation
                # This ensures we use current day NET + current day DEVIR
                
                # Calculate daily rollover (DEVİR = previous day KASA_TOP - previous day TAHS_TUTARI)
                # This applies to ALL days, including first day of month
                # For first day of month, we need to get previous month's last day KASA TOP
                # For subsequent days, DEVİR = previous day's KASA_TOP - previous day's TAHS_TUTARI
                
                # Initialize variables before if-else block
                previous_day_kasa_top = 0.0
                previous_day_tahs_tutari = 0.0
                
                # Check for manual override first (only for first day of month)
                if is_first_day_of_month and date in devir_overrides_cache.get(psp.psp, {}):
                    daily_rollover = float(devir_overrides_cache[psp.psp][date])
                else:
                    # For ALL days (including first day of month), calculate DEVIR from previous day
                    # This ensures continuity across month boundaries
                    # CORRECT FORMULA: DEVIR = PREVIOUS DAY KASA TOP - PREVIOUS DAY TAHS TUTARI
                    # Get previous day's KASA TOP and TAHS TUTARI (already initialized above)
                    
                    # Calculate previous day
                    previous_date = date - timedelta(days=1)
                    
                    # OPTIMIZATION: Use direct lookup instead of looping
                    # Check if we already processed this day in daily_data (faster than daily_breakdown)
                    if daily_data:
                        # Get last entry (most likely to be previous day)
                        last_entry = daily_data[-1]
                        last_date_str = last_entry.get('date')
                        try:
                            last_date = datetime.fromisoformat(last_date_str).date() if isinstance(last_date_str, str) else last_date_str
                            if last_date == previous_date:
                                previous_day_kasa_top = last_entry.get('kasa_top', 0.0)
                                previous_day_tahs_tutari = last_entry.get('tahs_tutari', 0.0)
                                # DEBUG: Log when previous day data is found
                                if psp.psp == "#61 CRYPPAY" and previous_day_kasa_top > 0:
                                    logger.info(f"🔍 Found previous day data for {psp.psp} on {previous_date}: KASA TOP = {previous_day_kasa_top:,.2f}")
                        except:
                            pass
                    
                    # If not found in daily breakdown, try to get from database
                    # This is especially important when previous day is in a different month
                    if previous_day_kasa_top == 0.0 and previous_day_tahs_tutari == 0.0:
                        # PERFORMANCE OPTIMIZATION: Check pre-loaded previous month data first
                        if previous_date == prev_month_last_day and psp.psp in prev_month_data_lookup:
                            prev_data = prev_month_data_lookup[psp.psp]
                            previous_day_kasa_top = prev_data['kasa_top']
                            previous_day_tahs_tutari = prev_data['tahs_tutari']
                        else:
                            # Fallback to database queries only if not in pre-loaded data
                            try:
                                # First, try to get previous day's KASA TOP from PSPKasaTop table if it exists
                                try:
                                    from app.models.financial import PSPKasaTop
                                    prev_kasa_top_record = PSPKasaTop.query.filter_by(
                                        psp_name=psp.psp,
                                        date=previous_date
                                    ).first()
                                    if prev_kasa_top_record:
                                        previous_day_kasa_top = float(prev_kasa_top_record.kasa_top_amount)
                                except ImportError:
                                    pass
                                
                                # If not found in PSPKasaTop, calculate from transactions
                                if previous_day_kasa_top == 0.0:
                                    # Get previous day's transactions
                                    prev_day_deposits = db.session.query(
                                        func.sum(
                                            case(
                                                (func.upper(Transaction.psp) == 'TETHER', func.coalesce(Transaction.amount, 0)),
                                                else_=func.coalesce(Transaction.amount_try, Transaction.amount)
                                            )
                                        )
                                    ).filter(
                                        Transaction.psp == psp.psp,
                                        func.upper(Transaction.category).in_(['DEP', 'DEPOSIT', 'INVESTMENT']),
                                        Transaction.date == previous_date
                                    ).scalar() or 0.0
                                    
                                    prev_day_withdrawals = db.session.query(
                                        func.sum(
                                            case(
                                                (func.upper(Transaction.psp) == 'TETHER', func.coalesce(Transaction.amount, 0)),
                                                else_=func.coalesce(Transaction.amount_try, Transaction.amount)
                                            )
                                        )
                                    ).filter(
                                        Transaction.psp == psp.psp,
                                        func.upper(Transaction.category).in_(['WD', 'WITHDRAW', 'WITHDRAWAL']),
                                        Transaction.date == previous_date
                                    ).scalar() or 0.0
                                    
                                    prev_day_total = float(prev_day_deposits) + float(prev_day_withdrawals)
                                    
                                    # Get commission rate for previous day
                                    from app.services.commission_rate_service import CommissionRateService
                                    prev_day_commission_rate = CommissionRateService.get_commission_rate_percentage(psp.psp, previous_date)
                                    prev_day_commission = float(prev_day_deposits) * (prev_day_commission_rate / 100) if prev_day_commission_rate else 0.0
                                    # FIXED: NET = TOPLAM - KOMISYON (deposits + withdrawals - commission)
                                    prev_day_net = prev_day_total - prev_day_commission
                                    
                                    # Get previous day's DEVIR
                                    try:
                                        from app.models.financial import PSPDevir
                                        prev_day_devir = PSPDevir.query.filter_by(
                                            psp_name=psp.psp,
                                            date=previous_date
                                        ).first()
                                        prev_day_devir_amount = float(prev_day_devir.devir_amount) if prev_day_devir else 0.0
                                    except:
                                        prev_day_devir_amount = 0.0
                                    
                                    # Calculate previous day's KASA TOP: NET + DEVIR
                                    previous_day_kasa_top = prev_day_net + prev_day_devir_amount
                                
                                # Get previous day's allocations (TAHS TUTARI)
                                try:
                                    from app.models.financial import PSPAllocation
                                    prev_day_allocations = db.session.query(
                                        func.sum(PSPAllocation.allocation_amount)
                                    ).filter(
                                        PSPAllocation.psp_name == psp.psp,
                                        PSPAllocation.date == previous_date
                                    ).scalar() or 0.0
                                except ImportError:
                                    prev_day_allocations = 0.0
                                
                                # Set previous_day_tahs_tutari from allocations
                                previous_day_tahs_tutari = float(prev_day_allocations) if prev_day_allocations else 0.0
                                
                            except Exception as e:
                                # Silent fallback - no logging for performance
                                previous_day_kasa_top = 0.0
                                previous_day_tahs_tutari = 0.0
                                
                                # Quick fallback: check last entry in daily_data only (already done above)
                                pass
                    
                    # Calculate DEVIR using previous day's values
                    # Ensure both values are floats to avoid type mismatch
                    previous_day_kasa_top_float = float(previous_day_kasa_top)
                    previous_day_tahs_tutari_float = float(previous_day_tahs_tutari)
                    daily_rollover = previous_day_kasa_top_float - previous_day_tahs_tutari_float
                    # Minimal logging - only first day of month
                    if is_first_day_of_month:
                        logger.info(f"DEVIR: {psp.psp} {date} = {daily_rollover:,.2f}")
                
                # Store the calculated DEVIR value for future use (batch operation)
                # Only store if it's not a manual override for first day of month
                # AND only if there are transactions for this day (avoid storing unnecessary devir records)
                # EXCEPTION: Always store last day of month to ensure continuity across months
                import calendar
                last_day_of_month = calendar.monthrange(date.year, date.month)[1]
                is_last_day_of_month = (date.day == last_day_of_month)
                is_manual_override = is_first_day_of_month and date in devir_overrides_cache.get(psp.psp, {})
                
                should_store_devir = (
                    not is_manual_override and 
                    (transaction_count > 0 or is_last_day_of_month)
                )
                
                if should_store_devir:
                    calculated_devirs_to_store.append({
                        'psp_name': psp.psp,
                        'date': date,
                        'devir_amount': daily_rollover
                    })
                
                # CORRECT FORMULA: KASA TOP = previous day KASA TOP + today's NET
                # TAHS TUTARI does NOT reduce KASA TOP on the same day
                # Instead, TAHS TUTARI affects next day's DEVIR calculation
                # Formula: KASA TOP = Previous KASA TOP + NET
                # Where: NET = Deposits - Withdrawals - Commission
                # And: DEVIR (for next day) = KASA TOP - TAHS TUTARI
                
                # Önceki gün KASA TOP değerini al (already initialized at line 1284)
                # Use the variable that was initialized before the if-else block
                # Ensure we use float to avoid any type issues
                previous_day_kasa_top_for_calc = float(previous_day_kasa_top) if previous_day_kasa_top is not None else 0.0
                
                # KASA TOP = önceki gün KASA TOP + bugün NET (TAHS TUTARI does NOT reduce KASA TOP)
                daily_kasa_top = previous_day_kasa_top_for_calc + daily_net
                
                # DEBUG: Log KASA TOP calculation for #61 CRYPPAY
                if psp.psp == "#61 CRYPPAY" and transaction_count > 0:
                    logger.info(f"🔍 KASA TOP DEBUG for {psp.psp} on {date}: "
                               f"Previous Day KASA TOP = {previous_day_kasa_top_for_calc:,.2f}, "
                               f"Today's NET = {daily_net:,.2f}, "
                               f"Calculated KASA TOP = {daily_kasa_top:,.2f}, "
                               f"Today's TAHS TUTARI = {daily_allocations:,.2f} (affects next day's DEVIR)")
                
                # BUG FIX: Check if there's a manual KASA TOP override for the current day
                # This ensures manually edited KASA TOP values are preserved during recalculation
                if date in kasa_top_overrides_cache.get(psp.psp, {}):
                    daily_kasa_top = float(kasa_top_overrides_cache[psp.psp][date])
                    # Only log on first occurrence to reduce noise
                    if date.day == 1 or transaction_count > 0:
                        logger.info(f"✅ Applied manual KASA TOP override for {psp.psp} on {date}: {daily_kasa_top:,.2f}")
                
                daily_data.append({
                    'date': date.isoformat(),
                    'yatimim': daily_deposits_amount,
                    'cekme': daily_withdrawals_amount,
                    'toplam': daily_total,
                    'komisyon': daily_commission,
                    'net': daily_net,
                    'tahs_tutari': daily_allocations,
                    'kasa_top': daily_kasa_top,
                    'devir': daily_rollover,
                    'transaction_count': transaction_count
                })
                
                daily_breakdown[psp.psp] = daily_data
        
        # Note: Summary rows will be added after all calculations are complete
        
        # Build PSP data for monthly summary (after daily breakdown is complete)
        psp_data = []
        for psp in psp_stats:
            # Calculate net total: deposits - withdrawals using lookup dictionaries
            total_deposits = deposits_dict.get(psp.psp, 0.0)
            total_withdrawals = withdrawals_dict.get(psp.psp, 0.0)
            total_amount = total_deposits + total_withdrawals  # Net total (deposits + withdrawals, since withdrawals are negative)
            
            # Get total allocations for this PSP in the month
            total_allocations = allocations_dict.get(psp.psp, 0.0)
            
            # Get the actual commission rate for this PSP using time-based system
            commission_rate = None
            try:
                from app.services.commission_rate_service import CommissionRateService
                # Get rate for the first day of the month being calculated
                target_date = datetime(year, month, 1).date()
                commission_rate = CommissionRateService.get_commission_rate_percentage(psp.psp, target_date)
            except Exception as e:
                logger.warning(f"Error getting commission rate for {psp.psp}: {e}")
                pass  # Skip if error occurs
            
            # Calculate commission based on total deposits only (not net total)
            # Tether is company's own KASA, so no commission calculations
            if psp.psp.upper() == 'TETHER':
                total_commission = 0.0
                total_net = total_amount
                total_allocations = 0.0  # No allocations for internal company KASA
                logger.info(f"Monthly PSP {psp.psp}: internal company KASA, deposits={total_deposits}, commission=0")
            elif commission_rate is not None and commission_rate > 0:
                total_commission = total_deposits * (commission_rate / 100)
                # FIXED: NET = TOPLAM - KOMISYON = (Deposits + Withdrawals) - Commission
                # Withdrawals are already negative, so total_amount = deposits + withdrawals (subtracts withdrawals)
                total_net = total_amount - total_commission
                logger.info(f"Monthly PSP {psp.psp}: deposits={total_deposits}, withdrawals={total_withdrawals}, rate={commission_rate}%, commission={total_commission}, net={total_net}")
            else:
                total_commission = 0.0
                total_net = total_amount
                logger.info(f"Monthly PSP {psp.psp}: no commission rate found, deposits={total_deposits}, commission=0")
            
            # Calculate opening and closing DEVIR
            # Tether is company's own KASA, so no allocations or devir calculations
            if psp.psp.upper() == 'TETHER':
                opening_devir = 0.0  # No devir for internal company KASA
                closing_devir = 0.0  # No devir for internal company KASA
                total_allocations = 0.0  # No allocations for internal company KASA
                kasa_top = total_net  # KASA TOP = NET for internal KASA (no rollover)
                logger.info(f"TETHER is internal KASA - no DEVIR/rollover calculations, KASA TOP = NET: {total_net}")
            else:
                # Get OPENING DEVIR (first day) and CLOSING DEVIR (last day) from daily breakdown
                opening_devir = 0.0
                closing_devir = 0.0
                
                try:
                    from app.models.financial import PSPDevir
                    
                    # Get opening and closing DEVIR from daily breakdown
                    if psp.psp in daily_breakdown and daily_breakdown[psp.psp]:
                        daily_data = daily_breakdown[psp.psp]
                        
                        # Get OPENING DEVIR (first day's DEVIR)
                        if len(daily_data) > 0:
                            first_day_data = daily_data[0]
                            if first_day_data.get('date') != 'MONTHLY_SUMMARY':
                                opening_devir = float(first_day_data.get('devir', 0.0))
                        
                        # Get CLOSING DEVIR (last day's DEVIR)
                        if len(daily_data) > 0:
                            last_day_data = daily_data[-1]
                            
                            # If the last entry is a summary row, get the second-to-last entry
                            if last_day_data.get('date') == 'MONTHLY_SUMMARY':
                                if len(daily_data) > 1:
                                    last_day_data = daily_data[-2]
                                else:
                                    last_day_data = None
                            
                            if last_day_data:
                                # Calculate CLOSING DEVIR: LAST KASA TOP - LAST TAHS TUTARI
                                kasa_top_value = last_day_data.get('kasa_top', 0.0)
                                tahs_tutari_value = last_day_data.get('tahs_tutari', 0.0)
                                
                                # Convert to float, handling both numeric and string values
                                if isinstance(kasa_top_value, str):
                                    import re
                                    numeric_match = re.search(r'[\d,]+\.?\d*', kasa_top_value.replace(',', ''))
                                    last_day_kasa_top = float(numeric_match.group()) if numeric_match else 0.0
                                else:
                                    last_day_kasa_top = float(kasa_top_value)
                                    
                                if isinstance(tahs_tutari_value, str):
                                    numeric_match = re.search(r'[\d,]+\.?\d*', tahs_tutari_value.replace(',', ''))
                                    last_day_tahs_tutari = float(numeric_match.group()) if numeric_match else 0.0
                                else:
                                    last_day_tahs_tutari = float(tahs_tutari_value)
                                
                                # Calculate CLOSING DEVIR using the formula: LAST KASA TOP - LAST TAHS TUTARI
                                closing_devir = last_day_kasa_top - last_day_tahs_tutari
                                logger.info(f"Calculated DEVIR for {psp.psp} in {year}-{month:02d}: OPENING={opening_devir:,.2f}, CLOSING={closing_devir:,.2f} (LAST KASA TOP {last_day_kasa_top:,.2f} - LAST TAHS TUTARI {last_day_tahs_tutari:,.2f})")
                        
                except Exception as e:
                    logger.warning(f"Could not get DEVIR for {psp.psp}: {e}")
                    # Continue with 0 values if fetch fails
                
                # Calculate KASA TOP using correct formula: DEVIR + NET
                # For monthly, use the last day's KASA TOP from daily breakdown
                kasa_top = total_net  # Default fallback
                
                # Get the last day's KASA TOP from the daily breakdown (calculated with correct formula)
                if psp.psp in daily_breakdown and daily_breakdown[psp.psp]:
                    last_day_kasa_top = daily_breakdown[psp.psp][-1].get('kasa_top', kasa_top)
                    kasa_top = last_day_kasa_top
                
                # KASA TOP is now calculated automatically using the formula: DEVIR + NET
                # No manual overrides needed - the formula is fixed
            
            # PHASE 1 OPTIMIZATION: Conditionally include daily breakdown
            psp_item = {
                'psp': psp.psp,
                'total_deposits': total_deposits,  # YATIRIM (deposits)
                'total_withdrawals': total_withdrawals,  # ÇEKME (withdrawals)
                'total_amount': total_amount,  # TOPLAM (deposits + withdrawals, withdrawals are negative)
                'total_commission': total_commission,  # KOMİSYON (commission)
                'total_net': total_net,  # NET (toplam - komisyon)
                'total_allocations': total_allocations,  # TAHS TUTARI (allocation amount)
                'closing_balance': kasa_top,  # KASA TOP (closing balance)
                'opening_balance': opening_devir,  # OPENING DEVİR (carryover from previous month)
                'closing_devir': closing_devir,  # CLOSING DEVİR (carryover to next month)
                'transaction_count': psp.transaction_count,
                'commission_rate': commission_rate,
                'month': month,
                'year': year,
                # Keep Turkish names for backward compatibility
                'yatimim': total_deposits,
                'cekme': total_withdrawals,
                'toplam': total_amount,
                'komisyon': total_commission,
                'net': total_net,
                'tahs_tutari': total_allocations,
                'kasa_top': kasa_top,
                'devir': opening_devir,  # DEVIR field shows OPENING balance (start of month)
            }
            
            # Only include daily breakdown if requested (saves ~60-70% payload size)
            if include_daily:
                psp_item['daily_breakdown'] = daily_breakdown.get(psp.psp, [])
            
            psp_data.append(psp_item)
        
        # Sort by total amount descending
        psp_data.sort(key=lambda x: x['toplam'], reverse=True)
        
        logger.info(f"Monthly PSP stats completed successfully, returning {len(psp_data)} PSPs")
        
        # PERFORMANCE OPTIMIZATION: Batch store calculated DEVIR values (only changed/new ones)
        if calculated_devirs_to_store:
            try:
                from app.models.financial import PSPDevir
                devir_store_start = time.time()
                
                # Get all existing DEVIR records for this period in one query
                psp_names = list(set([d['psp_name'] for d in calculated_devirs_to_store]))
                dates = list(set([d['date'] for d in calculated_devirs_to_store]))
                
                existing_devirs = PSPDevir.query.filter(
                    PSPDevir.psp_name.in_(psp_names),
                    PSPDevir.date.in_(dates)
                ).all()
                
                # Build lookup dictionary for existing records
                existing_dict = {(d.psp_name, d.date): d for d in existing_devirs}
                
                new_count = 0
                updated_count = 0
                unchanged_count = 0
                
                for devir_data in calculated_devirs_to_store:
                    key = (devir_data['psp_name'], devir_data['date'])
                    new_value = devir_data['devir_amount']
                    
                    if key not in existing_dict:
                        # Create new record
                        new_devir = PSPDevir(
                            psp_name=devir_data['psp_name'],
                            date=devir_data['date'],
                            devir_amount=new_value
                        )
                        db.session.add(new_devir)
                        new_count += 1
                    else:
                        # Only update if value changed significantly (> 0.01 difference)
                        existing = existing_dict[key]
                        old_value = float(existing.devir_amount)
                        if abs(old_value - new_value) > 0.01:
                            existing.devir_amount = new_value
                            updated_count += 1
                        else:
                            unchanged_count += 1
                
                db.session.commit()
                devir_store_time = time.time() - devir_store_start
                logger.info(f"PERFORMANCE: DEVIR storage completed in {devir_store_time:.2f}s - New: {new_count}, Updated: {updated_count}, Unchanged: {unchanged_count}")
            except Exception as e:
                logger.warning(f"Could not batch store DEVIR values: {e}")
                db.session.rollback()
        
        # Add monthly summary rows for each PSP after all calculations are complete
        for psp_data_item in psp_data:
            psp_name = psp_data_item['psp']
            if psp_name in daily_breakdown and daily_breakdown[psp_name]:
                daily_data = daily_breakdown[psp_name]
                last_day_data = daily_data[-1]  # Get the last day's data
                first_day_data = daily_data[0]  # Get the first day's data
                
                final_kasa_top = last_day_data['kasa_top']
                final_devir = last_day_data['devir']
                opening_devir = first_day_data['devir']  # Opening balance (DEVIR at start of month)
                
                # Calculate closing DEVIR (carryover to next month)
                # CLOSING DEVIR = Last Day KASA TOP - Last Day TAHS TUTARI
                last_day_tahs_tutari = last_day_data.get('tahs_tutari', 0.0)
                closing_devir = final_kasa_top - last_day_tahs_tutari
                
                # Add summary row
                summary_row = {
                    'date': 'MONTHLY_SUMMARY',
                    'yatimim': '---',
                    'cekme': '---', 
                    'toplam': '---',
                    'komisyon': '---',
                    'net': '---',
                    'tahs_tutari': '---',
                    'kasa_top': f'FINAL: {final_kasa_top:,.2f}',
                    'devir': f'OPENING: {opening_devir:,.2f} | CLOSING: {final_devir:,.2f}',
                    'transaction_count': '---',
                    'formulas': {
                        'kasa_top_formula': 'KASA TOP = CURRENT DAY DEVIR + CURRENT DAY NET',
                        'devir_formula': 'DEVIR = PREVIOUS DAY KASA TOP - PREVIOUS DAY TAHS TUTARI',
                        'devir_note': 'OPENING DEVIR = First day carryover from previous month, CLOSING DEVIR = Last day carryover to next month'
                    }
                }
                daily_data.append(summary_row)
                
                # Add final DEVIR row (carryover to next month)
                final_devir_row = {
                    'date': 'FINAL_DEVIR',
                    'yatimim': '',
                    'cekme': '', 
                    'toplam': '',
                    'komisyon': '',
                    'net': '',
                    'tahs_tutari': '',
                    'kasa_top': '',
                    'devir': f'{closing_devir:,.2f}',
                    'transaction_count': '',
                    'note': 'Carryover to next month'
                }
                daily_data.append(final_devir_row)
                
                daily_breakdown[psp_name] = daily_data
                
                # Update the PSP data with the modified daily breakdown
                psp_data_item['daily_breakdown'] = daily_data
        
        # Log total execution time
        total_time = time.time() - start_time
        logger.info(f"PERFORMANCE: Total PSP monthly stats execution time: {total_time:.2f}s for {len(psp_data)} PSPs and {len(calculated_devirs_to_store)} DEVIR calculations")
        
        # CONSOLIDATE PSPs: Merge multiple CRYPPAY accounts and other variants
        # This consolidates #61, #62, #70, #71, #72 CRYPPAY into single #61 CRYPPAY for reporting
        try:
            from app.utils.psp_utils import consolidate_psp_data
            original_psp_count = len(psp_data)
            psp_data = consolidate_psp_data(psp_data)
            if original_psp_count != len(psp_data):
                logger.info(f"PSP CONSOLIDATION: Consolidated {original_psp_count} PSPs into {len(psp_data)} PSPs")
        except Exception as e:
            logger.warning(f"PSP consolidation failed: {e}. Continuing with unconsolidated data.")
        
        # Prepare response
        response_data = {
            'data': psp_data,
            'month': month,
            'year': year,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'include_daily': include_daily,  # PHASE 1: Indicate if daily data included
            'performance': {
                'total_time': round(total_time, 2),
                'psp_count': len(psp_data),
                'cached': False  # Will be True if served from cache
            }
        }
        
        # Cache disabled for real-time data - kullanici her zaman guncel veri gormek istiyor
        # cache_service.set(cache_key, response_data, ttl=900)
        # logger.info(f"CACHE SET: Stored PSP monthly stats for {year}-{month:02d} (TTL: 900s)")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in PSP monthly stats: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return jsonify({
            'error': 'Failed to retrieve PSP monthly statistics',
            'message': str(e)
        }), 500

@transactions_api.route("/")
@handle_api_errors
def get_transactions():
    """Get all transactions with standardized response"""
    
    # Get query parameters
    from app.utils.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, MIN_PAGE_SIZE
    page = request.args.get('page', 1, type=int)
    # Enforce reasonable pagination limits for performance
    # UI should use pagination or summary endpoints for large datasets
    requested_per_page = request.args.get('per_page', DEFAULT_PAGE_SIZE, type=int)
    per_page = min(max(MIN_PAGE_SIZE, requested_per_page), MAX_PAGE_SIZE)  # Ensure within limits
    
    # Log warning if client requested more than max (helps identify code that needs updating)
    if requested_per_page > MAX_PAGE_SIZE:
        logger.warning(
            f"Client requested per_page={requested_per_page} but max is {MAX_PAGE_SIZE}. "
            f"Consider using pagination or summary endpoints for large datasets. "
            f"Request capped to {per_page}."
        )
    category = request.args.get('category')
    
    # Get filter parameters
    client = request.args.get('client')
    payment_method = request.args.get('payment_method')
    psp = request.args.get('psp')
    currency = request.args.get('currency')
    
    # Get date range filter parameters
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Get amount range filter parameters
    amount_min = request.args.get('amount_min', type=float)
    amount_max = request.args.get('amount_max', type=float)
    commission_min = request.args.get('commission_min', type=float)
    commission_max = request.args.get('commission_max', type=float)
    
    # Get sorting parameters
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    
    # Get search parameter
    search = request.args.get('search')
    
    # Log all query parameters for debugging
    logger.debug(f"Query parameters: page={page}, per_page={per_page}, category={category}, client={client}, payment_method={payment_method}, psp={psp}, currency={currency}, date_from={date_from}, date_to={date_to}, sort_by={sort_by}, sort_order={sort_order}")
    
    # Build query
    query = Transaction.query
    
    # Multi-tenancy: Apply organization filter
    query = add_tenant_filter(query, Transaction)
    
    # Log total transactions before any filters
    total_before_filters = query.count()
    logger.debug(f"Total transactions before filters: {total_before_filters}")
    
    if category:
        query = query.filter(Transaction.category == category)
        logger.info(f"Applied category filter: {category}")
    
    # Apply additional filters
    if client:
        query = query.filter(ilike_compat(Transaction.client_name, f'%{client}%'))
        logger.info(f"Applied client filter: {client}")
    
    if payment_method:
        query = query.filter(ilike_compat(Transaction.payment_method, f'%{payment_method}%'))
        logger.info(f"Applied payment_method filter: {payment_method}")
    
    if psp:
        query = query.filter(ilike_compat(Transaction.psp, f'%{psp}%'))
        logger.info(f"Applied psp filter: {psp}")
    
    if currency:
        query = query.filter(Transaction.currency == currency)
        logger.info(f"Applied currency filter: {currency}")
    
    # Apply date range filters
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Transaction.date >= date_from_obj)
            logger.info(f"Applied date_from filter: {date_from}")
        except ValueError:
            raise ValidationError(f'Invalid date_from format: {date_from}. Use YYYY-MM-DD', field='date_from')
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Transaction.date <= date_to_obj)
            logger.info(f"Applied date_to filter: {date_to}")
        except ValueError:
            raise ValidationError(f'Invalid date_to format: {date_to}. Use YYYY-MM-DD', field='date_to')
    
    # Apply amount range filters
    if amount_min is not None:
        query = query.filter(Transaction.amount >= amount_min)
        logger.info(f"Applied amount_min filter: {amount_min}")
    
    if amount_max is not None:
        query = query.filter(Transaction.amount <= amount_max)
        logger.info(f"Applied amount_max filter: {amount_max}")
    
    if commission_min is not None:
        query = query.filter(Transaction.commission >= commission_min)
        logger.info(f"Applied commission_min filter: {commission_min}")
    
    if commission_max is not None:
        query = query.filter(Transaction.commission <= commission_max)
        logger.info(f"Applied commission_max filter: {commission_max}")
    
    # Apply search filter (searches in client_name, company, notes)
    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                ilike_compat(Transaction.client_name, search_term),
                ilike_compat(Transaction.company, search_term),
                ilike_compat(Transaction.notes, search_term)
            )
        )
        logger.info(f"Applied search filter: {search}")
    
    # Log total transactions after all filters
    total_after_filters = query.count()
    logger.debug(f"Total transactions after filters: {total_after_filters}")
    
    # Paginate
    try:
        # Force WAL checkpoint to ensure we see latest transactions
        db.session.execute(text("PRAGMA wal_checkpoint(FULL)"))
        db.session.commit()
        
        # Add debugging to see what transactions are being returned
        total_count = query.count()
        logger.debug(f"Total transactions matching filters: {total_count}")
        
        # Determine sort column
        sort_column = Transaction.created_at  # Default
        if sort_by == 'date':
            sort_column = Transaction.date
        elif sort_by == 'amount':
            sort_column = Transaction.amount
        elif sort_by == 'commission':
            sort_column = Transaction.commission
        elif sort_by == 'client_name':
            sort_column = Transaction.client_name
        elif sort_by == 'category':
            sort_column = Transaction.category
        
        # Apply sort order
        if sort_order == 'asc':
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
        
        logger.info(f"Applied sorting: {sort_by} {sort_order} | Filtered count: {total_count} | Requesting page {page} with {per_page} per page")
        
        # Check what's in the pagination results
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Log the first 10 transactions in pagination to see what's being returned
        logger.debug(f"First 10 transactions in pagination:")
        for i, trans in enumerate(pagination.items[:10]):
            logger.debug(f"  {i+1}. ID={trans.id}, Client={trans.client_name}, Amount={trans.amount}, Date={trans.date}, Created={trans.created_at}")
        
        # Log date range of returned transactions
        if pagination.items:
            dates = [trans.date for trans in pagination.items if trans.date]
            if dates:
                logger.info(f"Returned transactions date range: {min(dates)} to {max(dates)} ({len(pagination.items)} transactions)")
        
        logger.debug(f"Returning {len(pagination.items)} transactions for page {page}")
        if pagination.items:
            latest_transaction = pagination.items[0]
            logger.debug(f"Latest transaction: ID={latest_transaction.id}, Client={latest_transaction.client_name}, Amount={latest_transaction.amount}, Created={latest_transaction.created_at}")
    except Exception as pagination_error:
        # Handle pagination error gracefully
        # Fallback to simple query without pagination (sorting already applied to query)
        transactions_data = query.all()
        pagination = type('obj', (object,), {
            'items': transactions_data,
            'total': len(transactions_data),
            'pages': 1
        })
    
    transactions = []
    for transaction in pagination.items:
        try:
            # Debug logging for specific transactions
            # Process special transactions without debug output
            
            # Calculate commission if not set, using PSP-specific rate but always 0 for WD
            if transaction.commission:
                commission = float(transaction.commission)
                net_amount = float(transaction.net_amount) if transaction.net_amount else float(transaction.amount) - commission
            else:
                # IMPORTANT: WD (Withdraw) transactions have ZERO commission
                if transaction.category and transaction.category.upper() == 'WD':
                    commission = 0.0
                    net_amount = float(transaction.amount)
                else:
                    # Try to get PSP-specific commission rate for non-WD transactions
                    commission_rate = None
                    if transaction.psp:
                        try:
                            from app.models.config import Option
                            psp_option = Option.query.filter_by(
                                field_name='psp',
                                value=transaction.psp,
                                is_active=True
                            ).first()
                            
                            if psp_option and psp_option.commission_rate is not None:
                                commission_rate = psp_option.commission_rate
                        except Exception:
                            pass  # Use 0 rate if error occurs
                    
                    if commission_rate is not None:
                        commission = float(transaction.amount) * float(commission_rate)
                        net_amount = float(transaction.amount) - commission
                    else:
                        commission = 0.0
                        net_amount = float(transaction.amount)
            
            # Ensure PSP is properly serialized (None becomes None, not empty string)
            psp_value = transaction.psp if transaction.psp else None
            logger.debug(f"Transaction {transaction.id} PSP value: {repr(psp_value)}")
            
            transactions.append({
                'id': transaction.id,
                'client_name': transaction.client_name,
                'company': transaction.company,
                'payment_method': transaction.payment_method,
                'category': transaction.category,
                'amount': float(transaction.amount),
                'commission': commission,
                'net_amount': net_amount,
                'currency': transaction.currency,
                'psp': psp_value,  # Use psp_value to ensure proper serialization
                'date': transaction.date.strftime('%Y-%m-%d') if transaction.date else None,
                'created_at': transaction.created_at.isoformat() if transaction.created_at else None,
                'notes': transaction.notes,
                'exchange_rate': float(transaction.exchange_rate) if transaction.exchange_rate else None,
                'amount_tl': float(transaction.amount_try) if transaction.amount_try else None,
                'commission_tl': float(transaction.commission_try) if transaction.commission_try else None,
                'net_amount_tl': float(transaction.net_amount_try) if transaction.net_amount_try else None
            })
        except Exception as transaction_error:
            # Skip problematic transaction but log the error
            logger.error(f"Error processing transaction ID {transaction.id}: {transaction_error}", exc_info=True)
            continue
    
    # Return processed transactions
    logger.info(f"Returning {len(transactions)} transactions (total in DB: {pagination.total})")
    if len(transactions) == 0 and pagination.total > 0:
        logger.warning(f"WARNING: pagination.total={pagination.total} but transactions array is empty!")
    
    return jsonify(paginated_response(
        items=transactions,
        page=page,
        per_page=per_page,
        total=pagination.total,
        meta={
            'message': 'Transactions retrieved successfully',
            'transactions': transactions,  # Backward compatibility
            'pages': pagination.pages  # Backward compatibility
        }
    )), 200

@transactions_api.route("/dropdown-options")
@login_required
def get_dropdown_options():
    """Get static dropdown options - fixed values that cannot be changed"""
    try:
        # Static dropdown options - these cannot be modified through the UI
        static_options = {
            'payment_method': [
                {'id': 1, 'value': 'Bank', 'commission_rate': None, 'created_at': None},
                {'id': 2, 'value': 'Credit card', 'commission_rate': None, 'created_at': None},
                {'id': 3, 'value': 'Tether', 'commission_rate': None, 'created_at': None}
            ],
            'currency': [
                {'id': 1, 'value': 'TL', 'commission_rate': None, 'created_at': None},
                {'id': 2, 'value': 'USD', 'commission_rate': None, 'created_at': None},
                {'id': 3, 'value': 'EUR', 'commission_rate': None, 'created_at': None}
            ],
            'currencies': [  # Add this for frontend compatibility
                {'id': 1, 'value': 'TL', 'commission_rate': None, 'created_at': None},
                {'id': 2, 'value': 'USD', 'commission_rate': None, 'created_at': None},
                {'id': 3, 'value': 'EUR', 'commission_rate': None, 'created_at': None}
            ],
            'category': [
                {'id': 1, 'value': 'DEP', 'commission_rate': None, 'created_at': None},
                {'id': 2, 'value': 'WD', 'commission_rate': None, 'created_at': None}
            ]
        }
        
        # Get PSP and Company options from database (Option model)
        from app.models.config import Option
        
        # Get PSP options from database
        psp_options_db = Option.query.filter_by(
            field_name='psp',
            is_active=True
        ).order_by(Option.value).all()
        
        static_options['psp'] = []
        for option in psp_options_db:
            static_options['psp'].append({
                'id': option.id,
                'value': option.value,
                'commission_rate': float(option.commission_rate) if option.commission_rate else None,
                'created_at': option.created_at.isoformat() if option.created_at else None
            })
        
        # Get Company options from database
        company_options_db = Option.query.filter_by(
            field_name='company',
            is_active=True
        ).order_by(Option.value).all()
        
        static_options['company'] = []
        for option in company_options_db:
            static_options['company'].append({
                'id': option.id,
                'value': option.value,
                'commission_rate': float(option.commission_rate) if option.commission_rate else None,
                'created_at': option.created_at.isoformat() if option.created_at else None
            })
        
        return jsonify(static_options)
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to retrieve dropdown options',
            'message': str(e)
        }), 500

@transactions_api.route("/dropdown-options", methods=['POST'])
@require_csrf
@login_required
@require_permission('transactions:manage_options')
def add_dropdown_option():
    """Add a new dropdown option (only for dynamic fields)"""
    # Import CSRF protection here to avoid circular imports
    from flask_wtf.csrf import validate_csrf
    from flask import request
    
    # Check if field is static (not modifiable)
    static_fields = ['payment_method', 'currency', 'category']
    data = request.get_json()
    field_name = data.get('field_name', '').lower()
    
    if field_name in static_fields:
        return jsonify({
            'error': 'Cannot modify static field',
            'message': f'The {field_name} field has fixed values and cannot be modified'
        }), 400
    
    # Validate CSRF token only if CSRF is enabled
    # If user is authenticated via session, we can be more lenient with CSRF
    # Session cookies already provide CSRF protection
    from flask import current_app
    from flask_login import current_user
    
    if current_app.config.get('WTF_CSRF_ENABLED', True) and not current_user.is_authenticated:
        try:
            csrf_token = request.headers.get('X-CSRFToken')
            if csrf_token:
                validate_csrf(csrf_token)
            else:
                return jsonify({
                    'error': 'CSRF token is required',
                    'message': 'Missing X-CSRFToken header'
                }), 400
        except Exception as e:
            return jsonify({
                'error': 'CSRF validation failed',
                'message': str(e)
            }), 400
    try:
        from app.models.config import Option
        from decimal import Decimal, InvalidOperation
        field_name = data.get('field_name', '').strip()
        value = data.get('value', '').strip()
        commission_rate = data.get('commission_rate')
        
        # Convert commission_rate to string if it's a number
        if commission_rate is not None:
            commission_rate = str(commission_rate).strip()
        
        if not field_name or not value:
            return jsonify({
                'error': 'Field name and value are required'
            }), 400
        
        # Validate commission rate if provided
        commission_decimal = None
        if commission_rate:
            try:
                commission_decimal = Decimal(commission_rate)
                if commission_decimal < 0 or commission_decimal > 1:
                    return jsonify({
                        'error': 'Commission rate must be between 0 and 1'
                    }), 400
            except (InvalidOperation, ValueError):
                return jsonify({
                    'error': 'Invalid commission rate format'
                }), 400
        
        # Commission rate is only required for PSP options
        if field_name == 'psp' and not commission_rate:
            return jsonify({
                'error': 'Commission rate is required for PSP options'
            }), 400
        
        # Check if option already exists
        existing = Option.query.filter_by(
            field_name=field_name,
            value=value,
            is_active=True
        ).first()
        
        if existing:
            return jsonify({
                'error': 'This option already exists'
            }), 400
        
        # Create new option
        option = Option(
            field_name=field_name,
            value=value,
            commission_rate=commission_decimal
        )
        
        db.session.add(option)
        db.session.commit()
        
        return jsonify({
            'message': 'Option added successfully',
            'option': {
                'id': option.id,
                'field_name': option.field_name,
                'value': option.value,
                'commission_rate': float(option.commission_rate) if option.commission_rate else None
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to add dropdown option',
            'message': str(e)
        }), 500

@transactions_api.route("/dropdown-options/<int:option_id>", methods=['PUT'])
@limiter.limit("30 per minute, 200 per hour")  # Rate limiting for configuration changes
@require_csrf
@login_required
@require_permission('transactions:manage_options')
def update_dropdown_option(option_id):
    """Update a dropdown option (only for dynamic fields)"""
    # Import CSRF protection here to avoid circular imports
    from flask_wtf.csrf import validate_csrf, generate_csrf
    from flask import request, session
    
    # Check if this option belongs to a static field
    try:
        from app.models.config import Option
        option = Option.query.get(option_id)
        if option and option.field_name.lower() in ['payment_method', 'currency', 'category']:
            return jsonify({
                'error': 'Cannot modify static field',
                'message': f'The {option.field_name} field has fixed values and cannot be modified'
            }), 400
    except Exception as e:
        pass  # Continue with validation if check fails
    
    # Validate CSRF token only if CSRF is enabled
    from flask import current_app
    from flask_login import current_user
    
    # If user is authenticated via session, we can be more lenient with CSRF
    # This is acceptable because session cookies already provide CSRF protection
    if current_app.config.get('WTF_CSRF_ENABLED', True) and not current_user.is_authenticated:
        csrf_token = request.headers.get('X-CSRFToken')
        
        if not csrf_token:
            return jsonify({
                'error': 'CSRF token is required',
                'message': 'Missing X-CSRFToken header'
            }), 400
        
        # Try multiple validation approaches
        token_valid = False
        
        # Method 1: Try Flask-WTF validation
        try:
            validate_csrf(csrf_token)
            token_valid = True
        except Exception as e:
            api_logger.debug(f"Flask-WTF validation failed: {str(e)}")
        
        # Method 2: Direct session comparison
        if not token_valid:
            session_token = session.get('csrf_token')
            if session_token and csrf_token == session_token:
                token_valid = True
                api_logger.debug("Token validated via direct session comparison")
        
        # Method 3: Generate new token and compare
        if not token_valid:
            try:
                new_token = generate_csrf()
                if csrf_token == new_token:
                    token_valid = True
                    api_logger.debug("Token validated via new token generation")
            except Exception as e:
                api_logger.debug(f"New token generation failed: {str(e)}")
        
        if not token_valid:
            api_logger.warning(f"CSRF validation failed for option {option_id}. Token: {csrf_token[:20] if csrf_token else 'None'}...")
            try:
                new_token = generate_csrf()
                return jsonify({
                    'error': 'CSRF validation failed',
                    'message': 'Security token validation failed. Please refresh the page and try again.',
                    'csrf_error': True,
                    'new_token': new_token
                }), 400
            except:
                return jsonify({
                    'error': 'CSRF validation failed',
                    'message': 'Security token validation failed. Please refresh the page and try again.',
                    'csrf_error': True
                }), 400
    try:
        from app.models.config import Option
        from decimal import Decimal, InvalidOperation
        
        option = Option.query.get(option_id)
        if not option:
            return jsonify({
                'error': 'Option not found'
            }), 404
        
        data = request.get_json()
        value = data.get('value', '').strip()
        commission_rate = data.get('commission_rate')
        
        # Debug logging
        api_logger.debug(f"Updating option {option_id}, field_name: {option.field_name}")
        api_logger.debug(f"Received value: '{value}', commission_rate: '{commission_rate}'")
        
        # Convert commission_rate to string if it's a number
        if commission_rate is not None:
            commission_rate = str(commission_rate).strip()
            # Convert empty string to None
            if not commission_rate:
                commission_rate = None
        
        if not value:
            return jsonify({
                'error': 'Value is required'
            }), 400
        
        # Validate commission rate if provided
        commission_decimal = None
        if commission_rate:
            try:
                commission_decimal = Decimal(commission_rate)
                if commission_decimal < 0 or commission_decimal > 1:
                    return jsonify({
                        'error': 'Commission rate must be between 0 and 1'
                    }), 400
            except (InvalidOperation, ValueError):
                return jsonify({
                    'error': 'Invalid commission rate format'
                }), 400
        
        # Commission rate is only required for PSP options
        if option.field_name == 'psp' and commission_rate is None:
            api_logger.debug("PSP option missing commission rate")
            return jsonify({
                'error': 'Commission rate is required for PSP options'
            }), 400
        
        # Check if option already exists (excluding current option)
        # Only check for duplicates if the value is actually changing
        if option.value != value:
            existing = Option.query.filter(
                Option.field_name == option.field_name,
                Option.value == value,
                Option.id != option_id,
                Option.is_active == True
            ).first()
            
            if existing:
                api_logger.debug(f"Duplicate option found: {existing.id}")
                return jsonify({
                    'error': f'An option with the value "{value}" already exists for {option.field_name} field'
                }), 400
        
        # Update option
        option.value = value
        option.commission_rate = commission_decimal
        
        db.session.commit()
        
        # IMPORTANT: If this is a PSP option and commission rate changed, 
        # update the time-based commission rate system as well
        if option.field_name == 'psp' and commission_decimal is not None:
            try:
                from app.services.commission_rate_service import CommissionRateService
                from datetime import date
                
                # Update the commission rate effective from today
                CommissionRateService.set_commission_rate(
                    psp_name=value,
                    new_rate=commission_decimal,
                    effective_from=date.today()
                )
                api_logger.info(f"Updated time-based commission rate for {value} to {commission_decimal}")
            except Exception as e:
                api_logger.error(f"Failed to update time-based commission rate: {e}")
                # Don't fail the request, just log the error
        
        # Refresh the option from database to ensure we have the latest data
        db.session.refresh(option)
        
        api_logger.info(f"Option {option_id} updated: value='{option.value}', commission_rate={option.commission_rate}")
        
        return jsonify({
            'message': 'Option updated successfully',
            'option': {
                'id': option.id,
                'field_name': option.field_name,
                'value': option.value,
                'commission_rate': float(option.commission_rate) if option.commission_rate else None
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to update dropdown option',
            'message': str(e)
        }), 500

@transactions_api.route("/dropdown-options/<int:option_id>", methods=['DELETE'])
@limiter.limit("20 per minute, 100 per hour")  # Rate limiting for deletions
@require_csrf
@login_required
@require_permission('transactions:manage_options')
def delete_dropdown_option(option_id):
    """Delete a dropdown option (only for dynamic fields)"""
    # Import CSRF protection here to avoid circular imports
    from flask_wtf.csrf import validate_csrf
    from flask import request
    from flask_login import current_user
    
    # Check if this option belongs to a static field
    try:
        from app.models.config import Option
        option = Option.query.get(option_id)
        if option and option.field_name.lower() in ['payment_method', 'currency', 'category']:
            return jsonify({
                'error': 'Cannot delete static field option',
                'message': f'The {option.field_name} field has fixed values and cannot be modified'
            }), 400
    except Exception as e:
        pass  # Continue with validation if check fails
    
    # Validate CSRF token only if CSRF is enabled
    # If user is authenticated via session, we can be more lenient with CSRF
    # Session cookies already provide CSRF protection
    from flask import current_app
    if current_app.config.get('WTF_CSRF_ENABLED', True) and not current_user.is_authenticated:
        try:
            csrf_token = request.headers.get('X-CSRFToken')
            if csrf_token:
                validate_csrf(csrf_token)
            else:
                return jsonify({
                    'error': 'CSRF token is required',
                    'message': 'Missing X-CSRFToken header'
                }), 400
        except Exception as e:
            return jsonify({
                'error': 'CSRF validation failed',
                'message': str(e)
            }), 400
    try:
        from app.models.config import Option
        
        option = Option.query.get(option_id)
        if not option:
            return jsonify({
                'error': 'Option not found'
            }), 404
        
        # Soft delete
        option.is_active = False
        db.session.commit()
        
        return jsonify({
            'message': 'Option deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to delete dropdown option',
            'message': str(e)
        }), 500

@transactions_api.route("/<int:transaction_id>", methods=['DELETE'])
@limiter.limit("20 per minute, 100 per hour")  # Rate limiting for deletions
@login_required
@handle_api_errors
def delete_transaction(transaction_id):
    """Delete a transaction - CSRF validation skipped for authenticated users"""
    # Enhanced authentication check
    if not current_user.is_authenticated:
        return jsonify(error_response(
            ErrorCode.AUTHENTICATION_ERROR.value,
            'Please log in to delete transactions'
        )), 401
    
    # Find the transaction
    logger.info(f"Attempting to delete transaction {transaction_id} by user {current_user.username}")
    transaction = Transaction.query.get(transaction_id)
    if not transaction:
        logger.warning(f"Transaction {transaction_id} not found for deletion by user {current_user.username}")
        # Check if transaction was recently deleted (might be a race condition)
        logger.info(f"Querying all transactions to verify: {Transaction.query.count()} total transactions exist")
        return jsonify({
            'error': 'Transaction not found',
            'message': f'Transaction with ID {transaction_id} does not exist'
        }), 404
    
    # Multi-tenancy: Validate access
    is_valid, error = validate_tenant_access(transaction, "transaction")
    if not is_valid:
        return error
    
    # Store transaction info for response
    transaction_info = {
        'id': transaction.id,
        'client_name': transaction.client_name,
        'amount': float(transaction.amount),
        'currency': transaction.currency,
        'date': transaction.date.isoformat() if transaction.date else None
    }
    
    # Delete transaction using service (includes automatic PSP sync)
    try:
        from app.services.transaction_service import TransactionService
        TransactionService.delete_transaction(transaction.id, current_user.id)
        
        logger.info(f"Transaction {transaction_id} deleted successfully by user {current_user.username}")
        
        return jsonify(success_response(
            data={
                'transaction': transaction_info
            },
            message='Transaction deleted successfully'
        )), 200
    except Exception as e:
        logger.error(f"Error deleting transaction {transaction_id}: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify(error_response(
            ErrorCode.INTERNAL_ERROR.value,
            f'Failed to delete transaction: {str(e)}'
        )), 500

@transactions_api.route("/<int:transaction_id>", methods=['GET'])
@login_required
def get_transaction(transaction_id):
    """Get a single transaction by ID"""
    try:
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return jsonify({
                'error': 'Transaction not found',
                'message': f'Transaction with ID {transaction_id} does not exist'
            }), 404
        
        # Convert to dictionary for JSON response
        transaction_data = {
            'id': transaction.id,
            'client_name': transaction.client_name,
            'company': transaction.company,
            'payment_method': transaction.payment_method,
            'category': transaction.category,
            'amount': float(transaction.amount),
            'commission': float(transaction.commission),
            'net_amount': float(transaction.net_amount),
            'currency': transaction.currency,
            'psp': transaction.psp,
            'notes': transaction.notes,
            'date': transaction.date.isoformat() if transaction.date else None,
            'created_at': transaction.created_at.isoformat() if transaction.created_at else None,
            'updated_at': transaction.updated_at.isoformat() if transaction.updated_at else None,
            # TL Amount fields for foreign currency transactions
            'amount_tl': float(transaction.amount_try) if transaction.amount_try else None,
            'commission_tl': float(transaction.commission_try) if transaction.commission_try else None,
            'net_amount_tl': float(transaction.net_amount_try) if transaction.net_amount_try else None,
            'exchange_rate': float(transaction.exchange_rate) if transaction.exchange_rate else None,
        }
        
        return jsonify({
            'status': 'success',
            'transaction': transaction_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting transaction {transaction_id}: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to retrieve transaction'
        }), 500

@transactions_api.route("/<int:transaction_id>", methods=['PUT'])
@limiter.limit("30 per minute, 500 per hour")  # Rate limiting for updates
@login_required
@require_csrf
def update_transaction(transaction_id):
    """Update an existing transaction"""
    try:
        # Enhanced authentication check
        if not current_user.is_authenticated:
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please log in to update transactions'
            }), 401
        
        # Log the request for debugging
        logger.info(f"Transaction update request from user {current_user.username} for transaction {transaction_id}")
        
        # Validate request content type
        if not request.is_json:
            return jsonify({
                'error': 'Invalid content type',
                'message': 'Request must be JSON'
            }), 400
        
        data = request.get_json()
        
        # Get the transaction to update
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return jsonify({
                'error': 'Transaction not found',
                'message': f'Transaction with ID {transaction_id} does not exist'
            }), 404
        
        # Multi-tenancy: Validate access
        is_valid, error = validate_tenant_access(transaction, "transaction")
        if not is_valid:
            return error
        
        # Validate required fields
        client_name = data.get('client_name', '').strip()
        if not client_name:
            return jsonify({
                'error': 'Client name is required'
            }), 400
        
        # Validate amount
        amount_str = data.get('amount', '')
        try:
            amount = Decimal(str(amount_str))
            if amount <= 0:
                return jsonify({
                    'error': 'Amount must be positive'
                }), 400
        except (InvalidOperation, ValueError):
            return jsonify({
                'error': 'Invalid amount format'
            }), 400
        
        # Get other fields
        currency = data.get('currency', 'TL').strip()
        payment_method = data.get('payment_method', '').strip()
        category = data.get('category', '').strip()
        psp = data.get('psp', '').strip()
        company = data.get('company', '').strip()
        notes = data.get('notes', '').strip()
        
        # Currency is already in correct format (TL, USD, EUR)
        
        # Handle both 'transaction_date' and 'date' fields for backward compatibility
        transaction_date_str = data.get('transaction_date', data.get('date', ''))
        
        # Parse transaction date
        try:
            if transaction_date_str:
                transaction_date = datetime.strptime(transaction_date_str, '%Y-%m-%d').date()
            else:
                transaction_date = datetime.now().date()
        except ValueError:
            return jsonify({
                'error': 'Invalid transaction date format. Use YYYY-MM-DD'
            }), 400
        
        # Check for manual commission override first
        use_manual_commission = data.get('use_manual_commission', False)
        manual_commission_rate = data.get('manual_commission_rate')
        
        # Calculate commission strictly based on PSP rate when available (no defaults)
        commission_rate: Decimal | None = None
        
        if use_manual_commission and manual_commission_rate is not None:
            # Use manual commission rate (convert percentage to decimal)
            commission_rate = Decimal(str(manual_commission_rate)) / Decimal('100')
            logger.info(f"Using manual commission rate: {manual_commission_rate}% (decimal: {commission_rate})")
        elif psp:
            try:
                from app.models.config import Option
                psp_option = Option.query.filter_by(
                    field_name='psp',
                    value=psp,
                    is_active=True
                ).first()
                if psp_option and psp_option.commission_rate:
                    commission_rate = psp_option.commission_rate
                    logger.info(f"Using PSP '{psp}' commission rate: {commission_rate}")
            except Exception as e:
                logger.warning(f"Error getting PSP commission rate: {e}")
        
        # Calculate commission based on category
        if category == 'WD':
            # WD transactions always have 0 commission
            commission = Decimal('0')
            logger.info(f"WD transaction - setting commission to 0 for amount: {amount}")
        elif commission_rate is not None:
            # Calculate commission for DEP transactions
            commission = amount * commission_rate
            logger.info(f"Calculated commission: {commission} for amount: {amount}")
        else:
            commission = Decimal('0')
            logger.info(f"No commission rate available, setting commission to 0")
        net_amount = amount - commission
        
        # Handle foreign currency calculations
        amount_try = None
        commission_try = None
        net_amount_try = None
        exchange_rate = None
        
        if currency in ['USD', 'EUR']:
            # Check for custom exchange rates from frontend
            custom_rate = None
            if currency == 'USD' and data.get('usd_rate'):
                try:
                    custom_rate = Decimal(str(data.get('usd_rate')))
                    logger.info(f"Using custom USD rate from frontend: {custom_rate}")
                except (InvalidOperation, ValueError):
                    logger.warning(f"Invalid custom USD rate provided: {data.get('usd_rate')}")
            elif currency == 'EUR' and data.get('eur_rate'):
                try:
                    custom_rate = Decimal(str(data.get('eur_rate')))
                    logger.info(f"Using custom EUR rate from frontend: {custom_rate}")
                except (InvalidOperation, ValueError):
                    logger.warning(f"Invalid custom EUR rate provided: {data.get('eur_rate')}")
            
            # Use custom rate if provided, otherwise get from database/service
            if custom_rate:
                exchange_rate = custom_rate
            else:
                # Get exchange rate from database for the transaction date
                try:
                    from app.models.exchange_rate import ExchangeRate
                    if currency == 'USD':
                        db_rate = ExchangeRate.get_current_rate('USDTRY')
                        if db_rate:
                            exchange_rate = db_rate.rate
                            logger.info(f"Using database USD rate: {exchange_rate}")
                        else:
                            # Fallback to a default rate
                            exchange_rate = Decimal('27.0')
                            logger.warning(f"No USD rate found, using fallback rate: {exchange_rate}")
                    elif currency == 'EUR':
                        # For EUR, use a default rate or similar logic
                        exchange_rate = Decimal('30.0')  # Approximate EUR/TRY rate
                        logger.warning(f"Using default EUR rate: {exchange_rate}")
                except Exception as e:
                    logger.error(f"Error getting exchange rate from database: {e}")
                    # Use default fallback rates
                    exchange_rate = Decimal('27.0') if currency == 'USD' else Decimal('30.0')
                    logger.warning(f"Using fallback rate for {currency}: {exchange_rate}")
                
            if exchange_rate:
                amount_try = amount * exchange_rate
                commission_try = commission * exchange_rate
                net_amount_try = net_amount * exchange_rate
                logger.info(f"Calculated TL amounts for {currency}: Amount={amount_try}, Commission={commission_try}, Net={net_amount_try}")
            else:
                logger.warning(f"Could not get exchange rate for {currency} on {transaction_date}")
        elif currency == 'TL':
            # For TL transactions, TL amounts are the same as original amounts
            exchange_rate = Decimal('1.0')
            amount_try = amount
            commission_try = commission
            net_amount_try = net_amount
            logger.info(f"Set TL amounts for TL transaction: Amount={amount_try}, Commission={commission_try}, Net={net_amount_try}")
        
        # Update transaction fields
        transaction.client_name = client_name
        transaction.company = company
        transaction.payment_method = payment_method
        transaction.category = category
        transaction.amount = amount
        transaction.commission = commission
        transaction.net_amount = net_amount
        transaction.currency = currency
        transaction.psp = psp
        transaction.notes = notes
        transaction.date = transaction_date
        transaction.updated_at = datetime.now(timezone.utc)
        
        # Update TRY amount fields
        transaction.amount_try = amount_try
        transaction.commission_try = commission_try
        transaction.net_amount_try = net_amount_try
        transaction.exchange_rate = exchange_rate
        
        # Save to database
        db.session.commit()
        
        # Save custom exchange rate after transaction update
        if currency in ['USD', 'EUR'] and custom_rate:
            try:
                from app.models.exchange_rate import ExchangeRate
                currency_pair = 'USDTRY' if currency == 'USD' else 'EURTRY'
                
                # Check if rate already exists for this date
                existing_rate = ExchangeRate.query.filter_by(
                    date=transaction_date,
                    currency_pair=currency_pair
                ).first()
                
                if existing_rate:
                    # Update existing rate
                    existing_rate.rate = custom_rate
                    existing_rate.updated_at = datetime.now(timezone.utc)
                    logger.info(f"Updated existing {currency} rate for {transaction_date} to {custom_rate}")
                else:
                    # Create new rate entry
                    new_rate = ExchangeRate(
                        currency_pair=currency_pair,
                        rate=custom_rate,
                        date=transaction_date,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                    db.session.add(new_rate)
                    logger.info(f"Created new {currency} rate for {transaction_date}: {custom_rate}")
                
                db.session.commit()
                logger.info(f"Exchange rate saved successfully for {currency}")
            except Exception as e:
                logger.error(f"Error saving custom exchange rate to database: {e}")
                # Don't fail the transaction update if rate saving fails
        
        logger.info(f"Transaction {transaction_id} updated successfully by user {current_user.username}")
        
        return jsonify({
            'status': 'success',
            'message': 'Transaction updated successfully',
            'transaction': {
                'id': transaction.id,
                'client_name': transaction.client_name,
                'company': transaction.company,
                'payment_method': transaction.payment_method,
                'category': transaction.category,
                'amount': float(transaction.amount),
                'commission': float(transaction.commission),
                'net_amount': float(transaction.net_amount),
                'currency': transaction.currency,
                'psp': transaction.psp,
                'notes': transaction.notes,
                'date': transaction.date.isoformat() if transaction.date else None,
                'updated_at': transaction.updated_at.isoformat() if transaction.updated_at else None,
                'amount_try': float(transaction.amount_try) if transaction.amount_try else None,
                'commission_try': float(transaction.commission_try) if transaction.commission_try else None,
                'net_amount_try': float(transaction.net_amount_try) if transaction.net_amount_try else None,
                'exchange_rate': float(transaction.exchange_rate) if transaction.exchange_rate else None,
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Error updating transaction {transaction_id}: {str(e)}")
        logger.error(f"Traceback: {error_traceback}")
        
        # Return detailed error in debug mode, generic message in production
        error_message = str(e) if current_app.config.get('DEBUG') else 'Failed to update transaction'
        return jsonify({
            'error': 'Internal server error',
            'message': error_message,
            'details': str(e) if current_app.config.get('DEBUG') else None
        }), 500

@transactions_api.route("/clients-by-date")
@login_required
def get_clients_by_date():
    """Get clients data grouped by transaction date"""
    try:
        # Get transactions grouped by client and date - use converted amounts for proper currency conversion
        client_date_stats = db.session.query(
            Transaction.client_name,
            Transaction.date,
            func.count(Transaction.id).label('transaction_count'),
            # Use amount_try (converted to TRY) if available, otherwise fallback to amount
            func.sum(
                func.coalesce(Transaction.amount_try, Transaction.amount)
            ).label('total_amount'),
            func.avg(
                func.coalesce(Transaction.amount_try, Transaction.amount)
            ).label('average_amount'),
            # Use commission_try (converted to TRY) if available, otherwise fallback to commission
            func.sum(
                func.coalesce(Transaction.commission_try, Transaction.commission)
            ).label('total_commission'),
            # Calculate deposits separately (for Net Cash calculation)
            func.sum(
                case(
                    (func.upper(Transaction.category).in_(['DEP', 'DEPOSIT', 'INVESTMENT']),
                     func.abs(func.coalesce(Transaction.amount_try, Transaction.amount))),
                    else_=0
                )
            ).label('total_deposits'),
            # Calculate withdrawals separately (for Net Cash calculation)
            func.sum(
                case(
                    (func.upper(Transaction.category).in_(['WD', 'WITHDRAW', 'WITHDRAWAL']),
                     func.abs(func.coalesce(Transaction.amount_try, Transaction.amount))),
                    else_=0
                )
            ).label('total_withdrawals')
        ).filter(
            Transaction.client_name.isnot(None),
            Transaction.client_name != ''
        ).group_by(Transaction.client_name, Transaction.date).all()
        
        # Group by date
        grouped_by_date = {}
        for stat in client_date_stats:
            date_str = stat.date.isoformat() if stat.date else None
            if date_str not in grouped_by_date:
                grouped_by_date[date_str] = []
            
            # Extract values from query results
            total_amount = float(stat.total_amount) if stat.total_amount else 0.0
            # Use actual commission from database or 0 if not available (no defaults)
            total_commission = float(stat.total_commission) if stat.total_commission else 0.0
            total_deposits = float(stat.total_deposits) if stat.total_deposits else 0.0
            total_withdrawals = float(stat.total_withdrawals) if stat.total_withdrawals else 0.0
            
            # Net Cash = Deposits - Withdrawals (Cash Flow formula)
            net_cash = total_deposits - total_withdrawals
            
            # Get additional client info
            latest_transaction = Transaction.query.filter(
                Transaction.client_name == stat.client_name
            ).order_by(Transaction.created_at.desc()).first()
            
            # Get currencies and PSPs for this client on this date
            date_transactions = Transaction.query.filter(
                Transaction.client_name == stat.client_name,
                Transaction.date == stat.date
            ).all()
            
            currencies = list(set([t.currency for t in date_transactions if t.currency]))
            psps = list(set([t.psp for t in date_transactions if t.psp]))
            
            grouped_by_date[date_str].append({
                'client_name': stat.client_name,
                'company_name': latest_transaction.company if latest_transaction else None,  # Add company name
                'payment_method': latest_transaction.payment_method if latest_transaction else None,
                'category': latest_transaction.category if latest_transaction else None,
                'date': date_str,
                'total_amount': total_amount,
                'total_commission': total_commission,
                'total_deposits': total_deposits,
                'total_withdrawals': total_withdrawals,
                'total_net': net_cash,  # Now using Net Cash (Deposits - Withdrawals)
                'transaction_count': stat.transaction_count,
                'avg_transaction': float(stat.average_amount) if stat.average_amount else 0.0,
                'currencies': currencies,
                'psps': psps
            })
        
        # Sort dates and clients within each date
        for date_str in grouped_by_date:
            grouped_by_date[date_str].sort(key=lambda x: x['total_amount'], reverse=True)
        
        # Convert to sorted list
        result = []
        for date_str in sorted(grouped_by_date.keys(), reverse=True):
            result.append({
                'date': date_str,
                'clients': grouped_by_date[date_str]
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to retrieve clients data by date',
            'message': str(e)
        }), 500

@transactions_api.route("/bulk-import", methods=['POST'])
@require_csrf
@login_required
@require_permission('transactions:bulk')
def bulk_import_transactions():
    """Bulk import transactions from CSV/Excel data with improved duplicate handling"""
    try:
        # Enhanced authentication check
        if not current_user.is_authenticated:
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please log in to import transactions'
            }), 401
        
        # Log the request for debugging
        logger.info(f"Bulk import request from user {current_user.username}")
        
        # Validate request content type
        if not request.is_json:
            return jsonify({
                'error': 'Invalid content type',
                'message': 'Request must be JSON'
            }), 400
        
        data = request.get_json()
        transactions_data = data.get('transactions', [])
        
        if not transactions_data or not isinstance(transactions_data, list):
            return jsonify({
                'error': 'Invalid data format',
                'message': 'transactions must be a non-empty array'
            }), 400
        
        if len(transactions_data) == 0:
            return jsonify({
                'error': 'No transactions to import',
                'message': 'transactions array is empty'
            }), 400
        
        # Limit to prevent abuse
        if len(transactions_data) > 1000:
            return jsonify({
                'error': 'Too many transactions',
                'message': 'Maximum 1000 transactions per import'
            }), 400
        
        successful_imports = 0
        failed_imports = 0
        skipped_duplicates = 0
        errors = []
        warnings = []
        
        # Track processed transactions to handle duplicates
        processed_transactions = set()
        
        for i, transaction_data in enumerate(transactions_data):
            try:
                # Enhanced debug logging for ALL transactions
                logger.info(f"Processing transaction row {i+1}: client='{transaction_data.get('client_name', '')}', amount='{transaction_data.get('amount', '')}', category='{transaction_data.get('category', '')}'")
                
                # Debug logging for specific transactions
                if transaction_data.get('client_name', '').strip() in ['TETHER ALIM', 'KUR FARKI MALİYETİ']:
                    logger.info(f"Processing special transaction row {i+1}: {transaction_data}")
                
                # Create a unique identifier for duplicate detection
                client_name = transaction_data.get('client_name', '').strip()
                amount = transaction_data.get('amount', '')
                date_str = transaction_data.get('date', '')
                
                # DISABLED: Duplicate detection for bulk imports
                # All rows from CSV will be imported without skipping
                # This ensures complete data import as requested by user
                
                # Get other fields for processing
                psp = transaction_data.get('psp', '').strip()
                payment_method = transaction_data.get('payment_method', '').strip()
                category = transaction_data.get('category', '').strip()
                company = transaction_data.get('company', '').strip()
                
                # Validate required fields with more flexible rules
                if not client_name:
                    # Try to generate a client name if missing
                    client_name = f"Unknown_Client_{i+1}"
                    warnings.append(f"Row {i+1}: Generated client name '{client_name}' for missing client")
                
                # Get other fields with improved defaults FIRST (before validation)
                currency = transaction_data.get('currency', 'TL').strip()
                notes = transaction_data.get('notes', '').strip()
                
                # Improved category handling - accept both DEP and WD
                if category:
                    category = category.strip().upper()
                    if category not in ['DEP', 'WD']:
                        # Try to map common variations
                        category_mapping = {
                            'DEPOSIT': 'DEP',
                            'WITHDRAW': 'WD',
                            'WITHDRAWAL': 'WD',
                            'ÇEKME': 'WD',
                            'YATIRMA': 'DEP'
                        }
                        if category in category_mapping:
                            category = category_mapping[category]
                            warnings.append(f"Row {i+1}: Mapped category '{category}' to '{category}'")
                        else:
                            # Default to DEP for unknown categories
                            category = 'DEP'
                            warnings.append(f"Row {i+1}: Unknown category '{category}', defaulting to 'DEP'")
                else:
                    # Default to DEP if no category specified
                    category = 'DEP'
                    warnings.append(f"Row {i+1}: No category specified, defaulting to 'DEP'")
                
                # Validate amount with more flexible rules (NOW category is defined)
                logger.info(f"Row {i+1}: Validating amount '{amount}' for category '{category}'")
                try:
                    amount_decimal = Decimal(str(amount))
                    logger.info(f"Row {i+1}: Amount parsed successfully: {amount_decimal}")
                    
                    # Allow negative amounts for WD (withdraw) transactions
                    if category == 'WD':
                        logger.info(f"Row {i+1}: Processing WD transaction with amount {amount_decimal}")
                        if amount_decimal == 0:
                            if client_name in ['TETHER ALIM', 'KUR FARKI MALİYETİ']:
                                logger.warning(f"Special transaction {client_name} has zero amount - this might be intentional")
                                warnings.append(f"Row {i+1}: Special transaction {client_name} has zero amount")
                            else:
                                logger.error(f"Row {i+1}: WD transaction cannot have zero amount for {client_name}")
                                errors.append(f"Row {i+1}: Amount cannot be zero for {client_name}")
                                failed_imports += 1
                                continue
                        # For WD transactions, negative amounts are valid (representing money going out)
                        elif amount_decimal > 0:
                            # Convert positive WD amounts to negative (money going out)
                            amount_decimal = -amount_decimal
                            logger.info(f"Row {i+1}: Converted positive WD amount {amount} to negative {amount_decimal}")
                    else:
                        # For DEP transactions, amounts must be positive
                        logger.info(f"Row {i+1}: Processing DEP transaction with amount {amount_decimal}")
                        if amount_decimal <= 0:
                            if client_name in ['TETHER ALIM', 'KUR FARKI MALİYETİ']:
                                logger.warning(f"Special transaction {client_name} has non-positive amount - this might be intentional")
                                warnings.append(f"Row {i+1}: Special transaction {client_name} has non-positive amount")
                            else:
                                logger.error(f"Row {i+1}: DEP transaction must have positive amount for {client_name}")
                                errors.append(f"Row {i+1}: DEP transactions must have positive amounts for {client_name}")
                                failed_imports += 1
                                continue
                        
                except (InvalidOperation, ValueError) as e:
                    logger.error(f"Row {i+1}: Amount parsing error: {e} for amount '{amount}'")
                    if client_name in ['TETHER ALIM', 'KUR FARKI MALİYETİ']:
                        logger.error(f"Special transaction {client_name} has invalid amount format: {amount}")
                        errors.append(f"Row {i+1}: Special transaction {client_name} has invalid amount format: {amount}")
                        failed_imports += 1
                        continue
                    else:
                        # Try to fix common amount format issues
                        try:
                            # Remove common non-numeric characters
                            cleaned_amount = str(amount).replace(',', '').replace('₺', '').replace('$', '').replace('€', '').strip()
                            amount_decimal = Decimal(cleaned_amount)
                            logger.info(f"Row {i+1}: Fixed amount format from '{amount}' to '{amount_decimal}'")
                        except (InvalidOperation, ValueError) as e2:
                            logger.error(f"Row {i+1}: Failed to fix amount format: {e2}")
                            errors.append(f"Row {i+1}: Invalid amount format '{amount}' for {client_name}")
                            failed_imports += 1
                            continue
                
                # Currency is already in correct format (TL, USD, EUR)
                
                # Parse transaction date with more flexible formats
                try:
                    if date_str:
                        # Handle multiple date formats
                        date_formats = ['%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']
                        transaction_date = None
                        
                        for date_format in date_formats:
                            try:
                                transaction_date = datetime.strptime(date_str, date_format).date()
                                break
                            except ValueError:
                                continue
                        
                        if not transaction_date:
                            # If all formats fail, use current date
                            transaction_date = datetime.now().date()
                            warnings.append(f"Row {i+1}: Invalid date format '{date_str}', using current date")
                    else:
                        transaction_date = datetime.now().date()
                        warnings.append(f"Row {i+1}: No date specified, using current date")
                except Exception as e:
                    transaction_date = datetime.now().date()
                    warnings.append(f"Row {i+1}: Date parsing error, using current date: {str(e)}")
                
                # Calculate commission and net amount with improved logic
                commission = transaction_data.get('commission', 0)
                net_amount = transaction_data.get('net_amount', 0)
                
                # If commission not provided or is 0, derive using PSP-specific rate when available
                if not commission or commission == 0:
                    commission_rate: Decimal | None = None
                    if psp:
                        try:
                            from app.models.config import Option
                            psp_option = Option.query.filter_by(
                                field_name='psp',
                                value=psp,
                                is_active=True
                            ).first()
                            if psp_option and psp_option.commission_rate is not None:
                                commission_rate = psp_option.commission_rate
                                logger.info(f"Using PSP '{psp}' commission rate: {commission_rate} for amount: {amount_decimal}")
                            else:
                                logger.warning(f"No commission rate found for PSP '{psp}'")
                        except Exception as e:
                            logger.warning(f"Error fetching PSP commission rate for '{psp}': {e}")
                    
                    if category == 'WD':
                        # WD transactions always have 0 commission and should be stored as negative amounts
                        commission = Decimal('0')
                        amount_decimal = -amount_decimal  # Store withdrawal amounts as negative values
                        logger.info(f"WD transaction - setting commission to 0 and amount to negative: {amount_decimal}")
                    elif commission_rate is not None:
                        # Calculate commission based on absolute amount for DEP transactions
                        commission = abs(amount_decimal) * commission_rate
                        logger.info(f"Calculated commission: {commission} for amount: {amount_decimal}")
                    else:
                        commission = Decimal('0')
                        logger.warning(f"No commission rate available for PSP '{psp}', setting commission to 0")
                
                # Always calculate net amount as amount - commission
                net_amount = amount_decimal - commission
                logger.info(f"Final values - Amount: {amount_decimal}, Commission: {commission}, Net: {net_amount}")
                
                # Add import timestamp to notes to distinguish from existing transactions
                import_note = f"Imported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                if notes:
                    notes = f"{notes} | {import_note}"
                else:
                    notes = import_note
                
                # Create transaction with improved data
                logger.info(f"Row {i+1}: Creating transaction object for {client_name} with amount {amount_decimal}")
                transaction = Transaction(
                    client_name=client_name,
                    company=company or 'Unknown',
                    payment_method=payment_method or 'Unknown',
                    category=category,
                    amount=amount_decimal,
                    commission=commission,
                    net_amount=net_amount,
                    currency=currency,
                    psp=psp or 'Unknown',
                    notes=notes,
                    date=transaction_date,
                    created_by=current_user.id,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                logger.info(f"Row {i+1}: Adding transaction to session")
                db.session.add(transaction)
                successful_imports += 1
                logger.info(f"Row {i+1}: Transaction added successfully, total successful: {successful_imports}")
                
                # DISABLED: No longer tracking processed transactions since duplicate detection is disabled
                # processed_transactions.add(duplicate_key)
                
            except Exception as e:
                logger.error(f"Row {i+1}: Exception during processing: {type(e).__name__}: {str(e)}")
                logger.error(f"Row {i+1}: Full error details: {e}")
                if hasattr(e, '__traceback__'):
                    import traceback
                    logger.error(f"Row {i+1}: Traceback: {traceback.format_exc()}")
                errors.append(f"Row {i+1}: {str(e)}")
                failed_imports += 1
                continue
        
        # Commit all successful transactions
        logger.info(f"Import processing complete. Attempting to commit {successful_imports} transactions to database")
        if successful_imports > 0:
            try:
                db.session.commit()
                logger.info(f"Successfully committed {successful_imports} transactions to database")
                
                # Invalidate cache after bulk import
                try:
                    from app.services.query_service import QueryService
                    QueryService.invalidate_transaction_cache()
                    logger.info("Cache invalidated after API bulk import")
                except Exception as cache_error:
                    logger.warning(f"Failed to invalidate cache after API bulk import: {cache_error}")
                    
            except Exception as commit_error:
                logger.error(f"Database commit failed: {commit_error}")
                db.session.rollback()
                return jsonify({
                    'error': 'Database commit failed',
                    'message': f'Import failed during database commit: {str(commit_error)}'
                }), 500
        else:
            logger.warning("No transactions to commit - all failed validation")
        
        # Prepare response with detailed information
        logger.info(f"Preparing response: {successful_imports} successful, {failed_imports} failed, 0 duplicates (duplicate detection disabled)")
        response_data = {
            'success': True,
            'message': f'Import completed: {successful_imports} successful, {failed_imports} failed (all CSV rows imported)',
            'data': {
                'total_rows': len(transactions_data),
                'successful_imports': successful_imports,
                'failed_imports': failed_imports,
                'skipped_duplicates': 0,  # Always 0 since duplicate detection is disabled
                'errors': errors[:20],  # Limit errors to first 20
                'warnings': warnings[:20]  # Limit warnings to first 20
            }
        }
        
        # Add summary statistics
        if successful_imports > 0:
            response_data['data']['summary'] = {
                'total_amount': sum(t.amount for t in db.session.query(Transaction).filter(
                    Transaction.created_by == current_user.id,
                    Transaction.created_at >= datetime.now() - timedelta(minutes=5)
                ).all()),
                'categories_imported': list(set(t.category for t in db.session.query(Transaction).filter(
                    Transaction.created_by == current_user.id,
                    Transaction.created_at >= datetime.now() - timedelta(minutes=5)
                ).all()))
            }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"CRITICAL ERROR in bulk import: {type(e).__name__}: {str(e)}")
        if hasattr(e, '__traceback__'):
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({
            'error': 'Internal server error',
            'message': f'Import failed: {str(e)}'
        }), 500

@transactions_api.route("/import-excel", methods=['POST'])
@require_csrf
@login_required
@require_permission('transactions:bulk')
def import_excel_transactions():
    """Import transactions from Excel file (kasa.xlsx format)"""
    try:
        # Authentication check
        if not current_user.is_authenticated:
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please log in to import transactions'
            }), 401
        
        logger.info(f"Excel import request from user {current_user.username}")
        
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                'error': 'No file provided',
                'message': 'Please upload an Excel file'
            }), 400
        
        file = request.files['file']
        
        # Check if filename is empty
        if file.filename == '':
            return jsonify({
                'error': 'No file selected',
                'message': 'Please select a file to upload'
            }), 400
        
        # Check file extension
        allowed_extensions = {'.xlsx', '.xls'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            return jsonify({
                'error': 'Invalid file type',
                'message': f'Please upload an Excel file (.xlsx or .xls)'
            }), 400
        
        # Get sheet names from request (optional)
        sheet_names = request.form.get('sheets')
        if sheet_names:
            try:
                sheet_names = json.loads(sheet_names)
            except:
                sheet_names = None
        
        # Save file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name
        
        try:
            # Import from Excel
            from app.services.excel_import_service import excel_import_service
            
            logger.info(f"Starting Excel import from file: {file.filename}")
            result = excel_import_service.import_from_excel(
                temp_file_path,
                sheet_names=sheet_names
            )
            
            logger.info(f"Excel import completed: {result['imported_count']} imported, {result['skipped_count']} skipped")
            
            return jsonify({
                'success': result['success'],
                'message': f'Successfully imported {result["imported_count"]} transactions',
                'data': {
                    'imported_count': result['imported_count'],
                    'skipped_count': result['skipped_count'],
                    'total_count': result.get('total_count', 0),
                    'sheets_processed': result.get('sheets_processed', 0),
                    'errors': result.get('errors', []),
                    'warnings': result.get('warnings', [])
                }
            }), 200 if result['success'] else 500
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
    except Exception as e:
        logger.error(f"Error in Excel import: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'message': f'Excel import failed: {str(e)}'
        }), 500

@transactions_api.route("/update-psp-from-kasa", methods=['POST'])
@require_csrf
@login_required
@require_permission('transactions:bulk')
def update_psp_from_kasa():
    """Update existing transactions' PSP field with KASA column values from Excel sheets"""
    try:
        # Authentication check
        if not current_user.is_authenticated:
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please log in to update transactions'
            }), 401
        
        logger.info(f"PSP update from KASA request from user {current_user.username}")
        
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                'error': 'No file provided',
                'message': 'Please upload an Excel file'
            }), 400
        
        file = request.files['file']
        
        # Check if filename is empty
        if file.filename == '':
            return jsonify({
                'error': 'No file selected',
                'message': 'Please select a file to upload'
            }), 400
        
        # Check file extension
        allowed_extensions = {'.xlsx', '.xls'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            return jsonify({
                'error': 'Invalid file type',
                'message': f'Please upload an Excel file (.xlsx or .xls)'
            }), 400
        
        # Get sheet names from request (optional)
        sheet_names = request.form.get('sheets')
        if sheet_names:
            try:
                sheet_names = json.loads(sheet_names)
            except:
                sheet_names = None
        
        # Save file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name
        
        try:
            # Update PSP from KASA
            from app.services.excel_import_service import excel_import_service
            
            logger.info(f"Starting PSP update from KASA column from file: {file.filename}")
            result = excel_import_service.update_psp_from_kasa(
                temp_file_path,
                sheet_names=sheet_names
            )
            
            logger.info(f"PSP update completed: {result['updated_count']} updated, {result['not_found_count']} not found")
            
            return jsonify({
                'success': result['success'],
                'message': f'Successfully updated {result["updated_count"]} transactions',
                'data': {
                    'updated_count': result['updated_count'],
                    'not_found_count': result['not_found_count'],
                    'sheets_processed': result.get('sheets_processed', 0),
                    'errors': result.get('errors', []),
                    'warnings': result.get('warnings', [])
                }
            }), 200 if result['success'] else 500
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
    except Exception as e:
        logger.error(f"Error in PSP update from KASA: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'message': f'PSP update failed: {str(e)}'
        }), 500

@transactions_api.route("/bulk-delete", methods=['POST'])
@require_csrf
@login_required
@require_permission('transactions:bulk')
def bulk_delete_transactions():
    """Bulk delete all transactions with confirmation code - clears all data and cache"""
    try:
        # Enhanced authentication check
        if not current_user.is_authenticated:
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please log in to delete transactions'
            }), 401
        
        # Log the request for debugging
        logger.info(f"Bulk delete request from user {current_user.username}")
        
        # Validate request content type
        if not request.is_json:
            return jsonify({
                'error': 'Invalid content type',
                'message': 'Request must be JSON'
            }), 400
        
        data = request.get_json()
        confirmation_code = data.get('confirmation_code', '').strip()
        
        # Validate confirmation code
        from flask import current_app
        expected_code = current_app.config.get('BULK_DELETE_CONFIRMATION_CODE', '4561')
        if confirmation_code != expected_code:
            return jsonify({
                'error': 'Invalid confirmation code',
                'message': 'Please enter the correct 4-digit confirmation code'
            }), 400
        
        # Get count of transactions before deletion
        transaction_count = Transaction.query.count()
        
        if transaction_count == 0:
            return jsonify({
                'error': 'No transactions to delete',
                'message': 'Database is already empty'
            }), 400
        
        # Import aggregate models
        from app.models.financial import PspTrack, DailyBalance, PSPAllocation, PSPDevir, PSPKasaTop, DailyNet
        
        # Count records in aggregate tables
        psp_track_count = PspTrack.query.count()
        daily_balance_count = DailyBalance.query.count()
        allocation_count = PSPAllocation.query.count()
        devir_count = PSPDevir.query.count()
        kasa_top_count = PSPKasaTop.query.count()
        daily_net_count = DailyNet.query.count()
        
        logger.info(f"Deleting data - Transactions: {transaction_count}, PspTrack: {psp_track_count}, "
                   f"DailyBalance: {daily_balance_count}, Allocations: {allocation_count}, "
                   f"Devir: {devir_count}, KasaTop: {kasa_top_count}, DailyNet: {daily_net_count}")
        
        # Delete all transactions and aggregate data
        Transaction.query.delete()
        PspTrack.query.delete()
        DailyBalance.query.delete()
        PSPAllocation.query.delete()
        PSPDevir.query.delete()
        PSPKasaTop.query.delete()
        DailyNet.query.delete()
        
        db.session.commit()
        
        # Clear all caches
        try:
            # Clear Redis cache if available
            if hasattr(current_app, 'redis_service') and current_app.redis_service:
                redis_service = current_app.redis_service
                if redis_service.is_connected():
                    # Clear all dashboard and analytics cache patterns
                    cache_patterns = [
                        'consolidated_dashboard:*',
                        'dashboard_stats*',
                        'analytics:*',
                        'commission:*',
                        'transaction:*',
                        'psp:*',
                        'daily:*'
                    ]
                    for pattern in cache_patterns:
                        try:
                            # Get keys matching pattern
                            keys = redis_service.redis_client.keys(pattern)
                            if keys:
                                redis_service.redis_client.delete(*keys)
                                logger.info(f"Cleared {len(keys)} cache keys for pattern: {pattern}")
                        except Exception as cache_error:
                            logger.warning(f"Failed to clear cache pattern {pattern}: {cache_error}")
                    
                    logger.info("✅ All Redis cache cleared successfully")
            
            # Clear query service cache
            from app.services.query_service import QueryService
            if hasattr(QueryService, 'invalidate_transaction_cache'):
                QueryService.invalidate_transaction_cache()
                logger.info("✅ Query service cache invalidated")
            
            # Clear enhanced cache service if available
            try:
                from app.services.enhanced_cache_service import cache_service
                if hasattr(cache_service, 'clear_all'):
                    cache_service.clear_all()
                    logger.info("✅ Enhanced cache service cleared")
            except ImportError:
                pass
                
        except Exception as cache_error:
            logger.warning(f"Cache clear warning (non-critical): {cache_error}")
        
        total_deleted = (transaction_count + psp_track_count + daily_balance_count + 
                        allocation_count + devir_count + kasa_top_count + daily_net_count)
        
        logger.info(f"✅ Successfully deleted {total_deleted} total records and cleared all caches by user {current_user.username}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted all data ({total_deleted} records) and cleared cache',
            'data': {
                'deleted_count': transaction_count,
                'total_deleted': total_deleted,
                'aggregate_tables_cleared': {
                    'psp_track': psp_track_count,
                    'daily_balance': daily_balance_count,
                    'psp_allocation': allocation_count,
                    'psp_devir': devir_count,
                    'psp_kasa_top': kasa_top_count,
                    'daily_net': daily_net_count
                },
                'cache_cleared': True
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in bulk delete: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': f'Bulk delete failed: {str(e)}'
        }), 500
