"""
Transaction routes blueprint
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response, current_app
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta, timezone
from sqlalchemy import func, extract, desc, and_, or_
import pandas as pd
from werkzeug.utils import secure_filename
import os
import csv
from io import StringIO
import json
from decimal import Decimal, InvalidOperation
from collections import defaultdict
import logging

from app import db
from app.models.transaction import Transaction
from app.models.config import Option
from app.utils.unified_error_handler import handle_errors, handle_api_errors
from app.utils.db_compat import ilike_compat
from app.services.decimal_float_fix_service import decimal_float_service
from app.services.datetime_fix_service import fix_template_data_dates

logger = logging.getLogger(__name__)

# Create blueprint
transactions_bp = Blueprint('transactions', __name__)

# Define Analytics class outside of route functions to avoid scope issues
class Analytics:
    def __init__(self, total_clients, active_clients, avg_transaction_value, top_client_volume):
        self.total_clients = total_clients
        self.active_clients = active_clients
        self.avg_transaction_value = avg_transaction_value
        self.top_client_volume = top_client_volume

# Define ClientStats class outside of route functions to avoid scope issues
class ClientStats:
    def __init__(self, total_clients, total_volume, avg_transaction, top_client):
        self.total_clients = total_clients
        self.total_volume = total_volume
        self.avg_transaction = avg_transaction
        self.top_client = top_client

# Main transactions route
@transactions_bp.route('/transactions')
@login_required
@handle_errors
def transactions_main():
    """Main transactions page with filtering and pagination"""
    # Get page and filters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    
    # Build filters from request parameters
    filters = {
        'date_from': request.args.get('date_from'),
        'date_to': request.args.get('date_to'),
        'client_name': request.args.get('client_name'),
        'psp': request.args.get('psp'),
        'category': request.args.get('category'),
        'currency': request.args.get('currency'),
        'payment_method': request.args.get('payment_method'),
        'company': request.args.get('company')
    }
    
    # Get transactions data with pagination and filters
    query = Transaction.query
    
    # Apply filters
    if filters.get('date_from'):
        query = query.filter(Transaction.date >= filters['date_from'])
    if filters.get('date_to'):
        query = query.filter(Transaction.date <= filters['date_to'])
    if filters.get('client_name'):
        query = query.filter(ilike_compat(Transaction.client_name, f"%{filters['client_name']}%"))
    if filters.get('psp'):
        query = query.filter(ilike_compat(Transaction.psp, f"%{filters['psp']}%"))
    if filters.get('category'):
        query = query.filter(ilike_compat(Transaction.category, f"%{filters['category']}%"))
    if filters.get('currency'):
        query = query.filter(ilike_compat(Transaction.currency, f"%{filters['currency']}%"))
    if filters.get('payment_method'):
        query = query.filter(ilike_compat(Transaction.payment_method, f"%{filters['payment_method']}%"))
    if filters.get('company'):
        query = query.filter(ilike_compat(Transaction.company, f"%{filters['company']}%"))
    
    # Get total count for pagination
    total_count = query.count()
    
    # Apply pagination
    transactions = query.order_by(Transaction.date.desc(), Transaction.created_at.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()
    
    # Calculate pagination info
    total_pages = (total_count + per_page - 1) // per_page
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total_count,
        'pages': total_pages,
        'has_next': page < total_pages,
        'has_prev': page > 1
    }
    
    # Get distinct values for filters
    psp_options = [r[0] for r in db.session.query(Transaction.psp).distinct().filter(Transaction.psp.isnot(None)).all()]
    category_options = [r[0] for r in db.session.query(Transaction.category).distinct().filter(Transaction.category.isnot(None)).all()]
    currency_options = [r[0] for r in db.session.query(Transaction.currency).distinct().filter(Transaction.currency.isnot(None)).all()]
    payment_method_options = [r[0] for r in db.session.query(Transaction.payment_method).distinct().filter(Transaction.payment_method.isnot(None)).all()]
    
    # Calculate summary statistics
    summary = {
        'total_transactions': total_count,
        'total_amount': sum(t.amount for t in transactions),
        'total_commission': sum(t.commission for t in transactions),
        'total_net': sum(t.net_amount for t in transactions)
    }
    
    # Redirect to React frontend instead of rendering HTML template
    from app.utils.frontend_helper import serve_frontend
    return serve_frontend('/transactions')

# Alias routes for compatibility
@transactions_bp.route('/transactions_old')
@login_required
def transactions_alias():
    return redirect(url_for('transactions.clients'))

@transactions_bp.route('/add_transaction')
@login_required
def add_transaction_alias():
    return redirect(url_for('transactions.add'))

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'xlsx', 'xls'}

def validate_input(data, field_type='string'):
    """Validate input data"""
    if not data:
        return False, f"{field_type} is required"
    
    if field_type == 'amount':
        try:
            amount = Decimal(str(data))
            if amount <= 0:
                return False, "Amount must be positive"
            return True, amount
        except (InvalidOperation, ValueError):
            return False, "Invalid amount format"
    
    elif field_type == 'date':
        try:
            if isinstance(data, str):
                date_obj = datetime.strptime(data, '%Y-%m-%d').date()
            else:
                date_obj = data
            return True, date_obj
        except ValueError:
            return False, "Invalid date format (YYYY-MM-DD)"
    
    elif field_type == 'decimal':
        try:
            decimal_val = Decimal(str(data))
            return True, decimal_val
        except (InvalidOperation, ValueError):
            return False, "Invalid decimal format"
    
    return True, data

def secure_filename_upload(file):
    """Generate secure filename for upload"""
    filename = secure_filename(file.filename)
    # Add timestamp to prevent conflicts
    name, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{name}_{timestamp}{ext}"

def log_audit(action, table_name, record_id, old_values=None, new_values=None):
    """Log audit trail"""
    try:
        from app.models.audit import AuditLog
        audit_log = AuditLog(
            user_id=current_user.id,
            action=action,
            table_name=table_name,
            record_id=record_id,
            old_values=json.dumps(old_values) if old_values else None,
            new_values=json.dumps(new_values) if new_values else None,
            ip_address=request.remote_addr
        )
        db.session.add(audit_log)
        db.session.commit()
    except Exception as e:
        logger.error(f"Failed to log audit: {str(e)}")
        db.session.rollback()

def calculate_commission(amount, psp, category=None):
    """Calculate commission based on PSP and category"""
    try:
        # IMPORTANT: WD (Withdraw) transactions have ZERO commission
        # Company doesn't pay commissions for withdrawals
        if category and category.upper() == 'WD':
            return Decimal('0')
        
        # Get commission rate from PSP options for DEP transactions
        option = Option.query.filter_by(
            field_name='psp',
            value=psp,
            is_active=True
        ).first()
        
        if option and option.commission_rate:
            commission = amount * option.commission_rate
            return commission
        else:
            # Default commission rate of 2.5% for DEP transactions
            return amount * Decimal('0.025')
    except Exception as e:
        logger.error(f"Error calculating commission: {str(e)}")
        return Decimal('0')

def apply_transaction_filters(query):
    """Apply filters to transaction query"""
    # Date range filter
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Transaction.date >= start_date_obj)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Transaction.date <= end_date_obj)
        except ValueError:
            pass
    
    # PSP filter
    psp_filter = request.args.get('psp')
    if psp_filter:
        query = query.filter(Transaction.psp == psp_filter)
    
    # Category filter
    category_filter = request.args.get('category')
    if category_filter:
        query = query.filter(Transaction.category == category_filter)
    
    # Currency filter
    currency_filter = request.args.get('currency')
    if currency_filter:
        query = query.filter(Transaction.currency == currency_filter)
    
    # Amount range filter
    min_amount = request.args.get('min_amount')
    max_amount = request.args.get('max_amount')
    
    if min_amount:
        try:
            min_amount_decimal = Decimal(min_amount)
            query = query.filter(Transaction.amount >= min_amount_decimal)
        except (InvalidOperation, ValueError):
            pass
    
    if max_amount:
        try:
            max_amount_decimal = Decimal(max_amount)
            query = query.filter(Transaction.amount <= max_amount_decimal)
        except (InvalidOperation, ValueError):
            pass
    
    return query

@transactions_bp.route('/add', methods=['GET', 'POST'])
@login_required
@handle_errors
def add_transaction():
    """Add new transaction"""
    if request.method == 'POST':
        try:
            # Validate required fields
            client_name = request.form.get('client_name', '').strip()
            if not client_name:
                flash('Client name is required.', 'error')
                from app.utils.frontend_helper import serve_frontend
                return serve_frontend('/add-transaction')
            
            # Validate amount
            amount_str = request.form.get('amount', '')
            is_valid, amount_result = validate_input(amount_str, 'amount')
            if not is_valid:
                flash(amount_result, 'error')
                from app.utils.frontend_helper import serve_frontend
                return serve_frontend('/add-transaction')
            amount = amount_result
            
            # Validate date
            date_str = request.form.get('date', '')
            is_valid, date_result = validate_input(date_str, 'date')
            if not is_valid:
                flash(date_result, 'error')
                from app.utils.frontend_helper import serve_frontend
                return serve_frontend('/add-transaction')
            transaction_date = date_result
            
            # Get other fields
            iban = request.form.get('iban', '').strip()
            payment_method = request.form.get('payment_method', '').strip()
            company_order = request.form.get('company_order', '').strip()
            category = request.form.get('category', '').strip()
            psp = request.form.get('psp', '').strip()
            notes = request.form.get('notes', '').strip()
            currency = request.form.get('currency', 'TL').strip()
            
            # Calculate commission
            commission = calculate_commission(amount, psp, category)
            net_amount = amount - commission
            
            # Create transaction using service (includes automatic PSP sync)
            from app.services.transaction_service import TransactionService
            
            transaction_data = {
                'client_name': client_name,
                'iban': iban,
                'payment_method': payment_method,
                'company_order': company_order,
                'date': transaction_date,
                'category': category,
                'amount': amount,
                'commission': commission,
                'net_amount': net_amount,
                'currency': currency,
                'psp': psp,
                'notes': notes
            }
            
            transaction = TransactionService.create_transaction(transaction_data, current_user.id)
            
            # Log audit
            log_audit('CREATE', 'transaction', transaction.id, None, transaction.to_dict())
            
            flash('Transaction added successfully!', 'success')
            return redirect(url_for('transactions.clients'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding transaction: {str(e)}")
            flash('Error adding transaction. Please try again.', 'error')
    
    # Get template variables for dropdowns from Option model
    from app.models.config import Option
    
    # Get options from Option model
    iban_options = Option.query.filter_by(field_name='iban', is_active=True).order_by(Option.value).all()
    ibans = [option.value for option in iban_options]
    
    payment_method_options = Option.query.filter_by(field_name='payment_method', is_active=True).order_by(Option.value).all()
    payment_methods = [option.value for option in payment_method_options]
    
    company_options = Option.query.filter_by(field_name='company_order', is_active=True).order_by(Option.value).all()
    companies = [option.value for option in company_options]
    
    currency_options = Option.query.filter_by(field_name='currency', is_active=True).order_by(Option.value).all()
    currencies = [option.value for option in currency_options]
    
    category_options = Option.query.filter_by(field_name='category', is_active=True).order_by(Option.value).all()
    categories = [option.value for option in category_options]
    
    # Get PSP options from database transactions (fixed values)
    from app.services.psp_options_service import PspOptionsService
    from app.services.company_options_service import CompanyOptionsService
    psps = PspOptionsService.get_psps_from_database()
    
    # Get Company options from database transactions (fixed values)
    companies = CompanyOptionsService.get_companies_from_database()
    
    # Fallback to existing transaction data if no options are configured
    if not ibans:
        ibans = db.session.query(Transaction.iban).distinct().filter(Transaction.iban.isnot(None)).all()
        ibans = [iban[0] for iban in ibans if iban[0]]
    
    if not payment_methods:
        payment_methods = db.session.query(Transaction.payment_method).distinct().filter(Transaction.payment_method.isnot(None)).all()
        payment_methods = [pm[0] for pm in payment_methods if pm[0]]
    
    if not companies:
        companies = db.session.query(Transaction.company_order).distinct().filter(Transaction.company_order.isnot(None)).all()
        companies = [comp[0] for comp in companies if comp[0]]
    
    if not currencies:
        currencies = db.session.query(Transaction.currency).distinct().filter(Transaction.currency.isnot(None)).all()
        currencies = [curr[0] for curr in currencies if curr[0]]
    
    if not categories:
        categories = db.session.query(Transaction.category).distinct().filter(Transaction.category.isnot(None)).all()
        categories = [cat[0] for cat in categories if cat[0]]
    
    if not psps:
        psps = db.session.query(Transaction.psp).distinct().filter(Transaction.psp.isnot(None)).all()
        psps = [psp[0] for psp in psps if psp[0]]
    
        return serve_frontend('/add-transaction')

@transactions_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@handle_errors
def edit_transaction(id):
    """Edit existing transaction"""
    transaction = Transaction.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Store old values for audit
            old_values = transaction.to_dict()
            
            # Validate required fields
            client_name = request.form.get('client_name', '').strip()
            if not client_name:
                flash('Client name is required.', 'error')
                from app.utils.frontend_helper import serve_frontend
                return serve_frontend(f'/transactions/{id}/edit')
            
            # Validate amount
            amount_str = request.form.get('amount', '')
            is_valid, amount_result = validate_input(amount_str, 'amount')
            if not is_valid:
                flash(amount_result, 'error')
                from app.utils.frontend_helper import serve_frontend
                return serve_frontend(f'/transactions/{id}/edit')
            amount = amount_result
            
            # Validate date
            date_str = request.form.get('date', '')
            is_valid, date_result = validate_input(date_str, 'date')
            if not is_valid:
                flash(date_result, 'error')
                from app.utils.frontend_helper import serve_frontend
                return serve_frontend(f'/transactions/{id}/edit')
            transaction_date = date_result
            
            # Get other fields
            iban = request.form.get('iban', '').strip()
            payment_method = request.form.get('payment_method', '').strip()
            company_order = request.form.get('company_order', '').strip()
            category = request.form.get('category', '').strip()
            psp = request.form.get('psp', '').strip()
            notes = request.form.get('notes', '').strip()
            currency = request.form.get('currency', 'TL').strip()
            
            # Calculate commission
            commission = calculate_commission(amount, psp, category)
            net_amount = amount - commission
            
            # Update transaction using service (includes automatic PSP sync)
            from app.services.transaction_service import TransactionService
            
            transaction_data = {
                'client_name': client_name,
                'iban': iban,
                'payment_method': payment_method,
                'company_order': company_order,
                'date': transaction_date,
                'category': category,
                'amount': amount,
                'commission': commission,
                'net_amount': net_amount,
                'currency': currency,
                'psp': psp,
                'notes': notes
            }
            
            transaction = TransactionService.update_transaction(transaction.id, transaction_data, current_user.id)
            
            # Log audit
            log_audit('UPDATE', 'transaction', transaction.id, old_values, transaction.to_dict())
            
            flash('Transaction updated successfully!', 'success')
            return redirect(url_for('transactions.clients'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating transaction: {str(e)}")
            flash('Error updating transaction. Please try again.', 'error')
    
    # Get template variables for dropdowns from Option model
    from app.models.config import Option
    
    # Get options from Option model
    iban_options = Option.query.filter_by(field_name='iban', is_active=True).order_by(Option.value).all()
    ibans = [option.value for option in iban_options]
    
    payment_method_options = Option.query.filter_by(field_name='payment_method', is_active=True).order_by(Option.value).all()
    payment_methods = [option.value for option in payment_method_options]
    
    company_options = Option.query.filter_by(field_name='company_order', is_active=True).order_by(Option.value).all()
    companies = [option.value for option in company_options]
    
    currency_options = Option.query.filter_by(field_name='currency', is_active=True).order_by(Option.value).all()
    currencies = [option.value for option in currency_options]
    
    category_options = Option.query.filter_by(field_name='category', is_active=True).order_by(Option.value).all()
    categories = [option.value for option in category_options]
    
    # Get PSP options from database transactions (fixed values)
    from app.services.psp_options_service import PspOptionsService
    from app.services.company_options_service import CompanyOptionsService
    psps = PspOptionsService.get_psps_from_database()
    
    # Get Company options from database transactions (fixed values)
    companies = CompanyOptionsService.get_companies_from_database()
    
    # Fallback to existing transaction data if no options are configured
    if not ibans:
        ibans = db.session.query(Transaction.iban).distinct().filter(Transaction.iban.isnot(None)).all()
        ibans = [iban[0] for iban in ibans if iban[0]]
    
    if not payment_methods:
        payment_methods = db.session.query(Transaction.payment_method).distinct().filter(Transaction.payment_method.isnot(None)).all()
        payment_methods = [pm[0] for pm in payment_methods if pm[0]]
    
    if not companies:
        companies = db.session.query(Transaction.company_order).distinct().filter(Transaction.company_order.isnot(None)).all()
        companies = [comp[0] for comp in companies if comp[0]]
    
    if not currencies:
        currencies = db.session.query(Transaction.currency).distinct().filter(Transaction.currency.isnot(None)).all()
        currencies = [curr[0] for curr in currencies if curr[0]]
    
    if not categories:
        categories = db.session.query(Transaction.category).distinct().filter(Transaction.category.isnot(None)).all()
        categories = [cat[0] for cat in categories if cat[0]]
    
    if not psps:
        psps = db.session.query(Transaction.psp).distinct().filter(Transaction.psp.isnot(None)).all()
        psps = [psp[0] for psp in psps if psp[0]]
    
    from app.utils.frontend_helper import serve_frontend
    return serve_frontend(f'/transactions/{id}/edit')

@transactions_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@handle_errors
def delete_transaction(id):
    """Delete transaction"""
    # Reduced logging verbosity - only log in debug mode or errors
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    transaction = Transaction.query.get_or_404(id)
    
    try:
        # Store old values for audit
        old_values = transaction.to_dict()
        
        # Delete transaction using service (includes automatic PSP sync)
        from app.services.transaction_service import TransactionService
        TransactionService.delete_transaction(transaction.id, current_user.id)
        
        # Only log successful deletions in debug mode
        if current_app.config.get('DEBUG', False):
            logger.debug(f"Transaction {id} deleted successfully")
        
        # Log audit (temporarily disabled for debugging)
        # try:
        #     log_audit('DELETE', 'transaction', id, old_values, None)
        # except Exception as audit_error:
        #     logger.error(f"Audit logging failed but transaction was deleted: {str(audit_error)}")
        
        if is_ajax:
            return jsonify({
                'success': True,
                'message': 'Transaction deleted successfully!',
                'redirect_url': url_for('transactions.clients')
            })
        else:
            flash('Transaction deleted successfully!', 'success')
            return redirect(url_for('transactions.clients'))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting transaction {id}: {str(e)}", exc_info=True)
        
        if is_ajax:
            return jsonify({
                'success': False,
                'message': 'Error deleting transaction. Please try again.'
            }), 500
        else:
            flash('Error deleting transaction. Please try again.', 'error')
            return redirect(url_for('transactions.clients'))



@transactions_bp.route('/api/delete/<int:id>', methods=['POST'])
@login_required
@handle_api_errors
def api_delete_transaction(id):
    """API delete transaction - bypasses CSRF for AJAX calls"""
    transaction = Transaction.query.get_or_404(id)
    
    try:
        # Store old values for audit
        old_values = transaction.to_dict()
        
        # Delete transaction using service (includes automatic PSP sync)
        from app.services.transaction_service import TransactionService
        TransactionService.delete_transaction(transaction.id, current_user.id)
        
        # Only log successful deletions in debug mode
        if current_app.config.get('DEBUG', False):
            logger.debug(f"Transaction {id} deleted via API")
        
        return jsonify({
            'success': True,
            'message': 'Transaction deleted successfully!',
            'redirect_url': url_for('transactions.clients')
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting transaction {id} via API: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error deleting transaction. Please try again.'
        }), 500

@transactions_bp.route('/api/sync-psp-track', methods=['POST'])
@login_required
def api_sync_psp_track():
    """Manual API endpoint to sync PSP Track data"""
    try:
        from app.services.data_sync_service import DataSyncService
        
        # Get current transaction count
        transaction_count = Transaction.query.count()
        
        # Sync PSP Track data
        DataSyncService.sync_psp_track_from_transactions()
        
        # Get new PSP Track count
        from app.models.financial import PspTrack
        psp_track_count = PspTrack.query.count()
        
        logger.info(f"Manual PSP Track sync: {transaction_count} transactions, {psp_track_count} PSP tracks")
        
        return jsonify({
            'success': True,
            'message': f'PSP Track synced successfully! Transactions: {transaction_count}, PSP Tracks: {psp_track_count}',
            'transaction_count': transaction_count,
            'psp_track_count': psp_track_count
        })
    except Exception as e:
        logger.error(f"Error in manual PSP Track sync: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error syncing PSP Track: {str(e)}'
        }), 500

@transactions_bp.route('/clients')
@login_required
@handle_errors
def clients():
    """Clients management page with tabs - PERFORMANCE OPTIMIZED"""
    # Get active tab
    active_tab = request.args.get('tab', 'overview')
    
    # Get page and filters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    
    # Build filters from request parameters
    filters = {
        'date_from': request.args.get('date_from'),
        'date_to': request.args.get('date_to'),
        'amount_min': request.args.get('amount_min') if request.args.get('amount_min') else None,
        'client': request.args.get('client'),
        'psp': request.args.get('psp'),
        'category': request.args.get('category'),
        'currency': request.args.get('currency'),
        'payment_method': request.args.get('payment_method'),
        'company_order': request.args.get('company')
    }
    
    # Use optimized service to get all data
    try:
        # page_data = performance_optimized_service.get_clients_page_data(page, per_page, filters)
        
        # Extract data from optimized service - temporarily disabled
        # transactions = page_data['transactions']
        # distinct_values = page_data['distinct_values']
        # pagination = page_data['pagination']
        # summary = page_data['summary']
        
        # Get transactions data with pagination and filters
        query = Transaction.query
        
        # Apply filters
        if filters.get('date_from'):
            query = query.filter(Transaction.date >= filters['date_from'])
        if filters.get('date_to'):
            query = query.filter(Transaction.date <= filters['date_to'])
        if filters.get('client'):
            query = query.filter(ilike_compat(Transaction.client_name, f"%{filters['client']}%"))
        if filters.get('psp'):
            query = query.filter(ilike_compat(Transaction.psp, f"%{filters['psp']}%"))
        if filters.get('category'):
            query = query.filter(ilike_compat(Transaction.category, f"%{filters['category']}%"))
        if filters.get('currency'):
            query = query.filter(ilike_compat(Transaction.currency, f"%{filters['currency']}%"))
        if filters.get('payment_method'):
            query = query.filter(ilike_compat(Transaction.payment_method, f"%{filters['payment_method']}%"))
        if filters.get('company_order'):
            query = query.filter(ilike_compat(Transaction.company, f"%{filters['company_order']}%"))
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination
        transactions = query.order_by(Transaction.date.desc(), Transaction.created_at.desc()).offset(
            (page - 1) * per_page
        ).limit(per_page).all()
        
        # Calculate pagination info
        total_pages = (total_count + per_page - 1) // per_page
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total_count,
            'pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
        
        # Get distinct values for filters
        distinct_values = {
            'payment_method': [r[0] for r in db.session.query(Transaction.payment_method).distinct().filter(Transaction.payment_method.isnot(None)).all()],
            'category': [r[0] for r in db.session.query(Transaction.category).distinct().filter(Transaction.category.isnot(None)).all()],
            'psp': [r[0] for r in db.session.query(Transaction.psp).distinct().filter(Transaction.psp.isnot(None)).all()],
            'company_order': [r[0] for r in db.session.query(Transaction.company).distinct().filter(Transaction.company.isnot(None)).all()],
            'currency': [r[0] for r in db.session.query(Transaction.currency).distinct().filter(Transaction.currency.isnot(None)).all()]
        }
        
        # Calculate summary statistics
        summary = {
            'total_transactions': total_count,
            'total_amount': sum(t.amount for t in transactions),
            'total_commission': sum(t.commission for t in transactions),
            'total_net': sum(t.net_amount for t in transactions)
        }
        
        # Get all unique clients (for overview tab) - OPTIMIZED QUERY
        clients_data = db.session.query(
            Transaction.client_name,
            func.count(Transaction.id).label('transaction_count'),
            func.sum(Transaction.amount).label('total_amount'),
            func.sum(Transaction.commission).label('commission'),
            func.sum(Transaction.net_amount).label('net_amount'),
            func.max(Transaction.date).label('last_transaction_date')
        ).filter(
            Transaction.client_name.isnot(None),
            Transaction.client_name != ''
        ).group_by(Transaction.client_name).all()
        
        # Format client data
        clients = []
        for client in clients_data:
            clients.append({
                'name': client.client_name,
                'transaction_count': client.transaction_count,
                'total_amount': float(client.total_amount or 0),
                'volume': float(client.total_amount or 0),  # Add volume property for template compatibility
                'commission': float(client.commission or 0),
                'net_amount': float(client.net_amount or 0),
                'last_transaction_date': client.last_transaction_date,
                'is_active': client.last_transaction_date and (datetime.now().date() - client.last_transaction_date).days < 30 if client.last_transaction_date else False
            })
        
        # Calculate client statistics
        total_clients = len(clients)
        total_volume = sum(c['total_amount'] for c in clients)
        avg_transaction = total_volume / sum(c['transaction_count'] for c in clients) if sum(c['transaction_count'] for c in clients) > 0 else 0
        top_client = max(clients, key=lambda x: x['total_amount'])['name'] if clients else 'N/A'
        
        # Create client_stats as an object for template access
        client_stats = ClientStats(total_clients, total_volume, avg_transaction, top_client)
        
        # Get chart data for overview
        client_chart_data = None
        if clients:
            top_10_clients = sorted(clients, key=lambda x: x['total_amount'], reverse=True)[:10]
            client_chart_data = {
                'labels': [c['name'] for c in top_10_clients],
                'volumes': [c['total_amount'] for c in top_10_clients],
                'net_amounts': [c['net_amount'] for c in top_10_clients]
            }
        
        # Get filter values for transactions tab
        filter_client = request.args.get('client', '')
        filter_payment = request.args.get('payment_method', '')
        filter_category = request.args.get('category', '')
        filter_psp = request.args.get('psp', '')
        filter_company = request.args.get('company', '')
        filter_currency = request.args.get('currency', '')
        
        # Get analytics data
        analytics = {
            'total_clients': total_clients,
            'active_clients': len([c for c in clients if c['is_active']]),
            'avg_transaction_value': avg_transaction,
        }
        
        # Calculate top client volume
        top_client_volume = max(c['total_amount'] for c in clients) if clients else 0
        
        analytics = Analytics(
            total_clients=analytics['total_clients'],
            active_clients=analytics['active_clients'],
            avg_transaction_value=analytics['avg_transaction_value'],
            top_client_volume=top_client_volume
        )
        
        # Get filter options from distinct values
        payment_methods = distinct_values.get('payment_method', [])
        categories = distinct_values.get('category', [])
        psps = distinct_values.get('psp', [])
        companies = distinct_values.get('company_order', [])
        currencies = distinct_values.get('currency', [])
        
        # Get available clients for filter
        available_clients = [c['name'] for c in clients]
        
        # Prepare chart data
        top_clients = sorted(clients, key=lambda x: x['total_amount'], reverse=True)[:5]
        recent_activity = transactions[:5] if transactions else []
        
        # Volume chart data
        volume_chart_data = {
            'labels': [c['name'] for c in top_clients],
            'volumes': [c['total_amount'] for c in top_clients]
        }
        
        # Distribution chart data (top 5 clients + others)
        if len(clients) > 5:
            top_5 = clients[:5]
            others_total = sum(c['total_amount'] for c in clients[5:])
            distribution_chart_data = {
                'labels': [c['name'] for c in top_5] + ['Others'],
                'values': [c['total_amount'] for c in top_5] + [others_total]
            }
        else:
            distribution_chart_data = {
                'labels': [c['name'] for c in clients],
                'values': [c['total_amount'] for c in clients]
            }
            
        # Chart data will be serialized by the template filters
        
        # Identify risk clients (inactive for more than 30 days)
        risk_clients = [c for c in clients if not c['is_active']]
        
        # Create opportunity clients (clients with high potential for growth)
        opportunity_clients = []
        for client in clients:
            if client['is_active'] and client['total_amount'] > 0:
                # Calculate potential based on transaction history
                avg_transaction = client['total_amount'] / client['transaction_count'] if client['transaction_count'] > 0 else 0
                potential_value = avg_transaction * 2  # Assume 2x potential
                
                opportunity_clients.append({
                    'client_name': client['name'],
                    'opportunity_description': f"High-value client with {client['transaction_count']} transactions",
                    'potential_value': potential_value
                })
        
        # Limit to top 3 opportunities
        opportunity_clients = sorted(opportunity_clients, key=lambda x: x['potential_value'], reverse=True)[:3]
            
    except Exception as e:
        logger.error(f"Error in clients page: {str(e)}")
        flash('Error loading clients data', 'error')
        from app.utils.frontend_helper import serve_frontend
        return serve_frontend('/clients')
    
    # Auto-fix all template data for JSON compatibility
    template_data = {
        'active_tab': active_tab,
        'clients': clients,
        'client_stats': client_stats,
        'client_chart_data': client_chart_data,
        'transactions': transactions,
        'pagination': pagination,
        'available_clients': available_clients,
        'selected_client': filters.get('client'),
        'filters': filters,
        'analytics': analytics,
        'top_clients': top_clients,
        'recent_activity': recent_activity,
        'volume_chart_data': volume_chart_data,
        'distribution_chart_data': distribution_chart_data,
        'filter_client': filter_client,
        'filter_payment': filter_payment,
        'filter_category': filter_category,
        'filter_psp': filter_psp,
        'filter_company': filter_company,
        'filter_currency': filter_currency,
        'payment_methods': payment_methods,
        'categories': categories,
        'psps': psps,
        'companies': companies,
        'currencies': currencies,
        'risk_clients': risk_clients,
        'opportunity_clients': opportunity_clients,
        'now': datetime.now()
    }
    
    # Apply automated JSON fixing to all template data
    safe_data = template_data
    
    # Apply datetime fixing to all template data
    safe_data = fix_template_data_dates(safe_data)
    
    from app.utils.frontend_helper import serve_frontend
    return serve_frontend('/clients')



@transactions_bp.route('/import', methods=['GET', 'POST'])
@login_required
@handle_errors
def import_transactions():
    """Import transactions from CSV/Excel file"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected.', 'error')
            from app.utils.frontend_helper import serve_frontend
            return serve_frontend('/import')
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected.', 'error')
            from app.utils.frontend_helper import serve_frontend
            return serve_frontend('/import')
        
        if not allowed_file(file.filename):
            flash('Invalid file type. Please upload CSV or Excel file.', 'error')
            from app.utils.frontend_helper import serve_frontend
            return serve_frontend('/import')
        
        try:
            # Read file
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            
            # Validate required columns
            required_columns = ['client_name', 'amount', 'date']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                flash(f'Missing required columns: {", ".join(missing_columns)}', 'error')
                from app.utils.frontend_helper import serve_frontend
                return serve_frontend('/import')
            
            # Process transactions
            success_count = 0
            error_count = 0
            
            for index, row in df.iterrows():
                try:
                    # Validate data
                    client_name = str(row['client_name']).strip()
                    if not client_name:
                        continue
                    
                    # Validate amount
                    amount_str = str(row['amount'])
                    is_valid, amount_result = validate_input(amount_str, 'amount')
                    if not is_valid:
                        error_count += 1
                        continue
                    amount = amount_result
                    
                    # Validate date
                    date_str = str(row['date'])
                    is_valid, date_result = validate_input(date_str, 'date')
                    if not is_valid:
                        error_count += 1
                        continue
                    transaction_date = date_result
                    
                    # Get other fields
                    iban = str(row.get('iban', '')).strip()
                    payment_method = str(row.get('payment_method', '')).strip()
                    company_order = str(row.get('company_order', '')).strip()
                    category = str(row.get('category', '')).strip()
                    psp = str(row.get('psp', '')).strip()
                    notes = str(row.get('notes', '')).strip()
                    currency = str(row.get('currency', 'TL')).strip()
                    
                    # Calculate commission
                    commission = calculate_commission(amount, psp, category)
                    net_amount = amount - commission
                    
                    # Create transaction using service (includes automatic PSP sync)
                    from app.services.transaction_service import TransactionService
                    
                    transaction_data = {
                        'client_name': client_name,
                        'iban': iban,
                        'payment_method': payment_method,
                        'company_order': company_order,
                        'date': transaction_date,
                        'category': category,
                        'amount': amount,
                        'commission': commission,
                        'net_amount': net_amount,
                        'currency': currency,
                        'psp': psp,
                        'notes': notes
                    }
                    
                    TransactionService.create_transaction(transaction_data, current_user.id)
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing row {index}: {str(e)}")
                    continue
            
            db.session.commit()
            
            # Invalidate cache after bulk import
            try:
                from app.services.query_service import QueryService
                QueryService.invalidate_transaction_cache()
                # Cache invalidation - no verbose logging needed
            except Exception as cache_error:
                logger.warning(f"Failed to invalidate cache after import: {cache_error}")
            
            flash(f'Import completed! {success_count} transactions imported, {error_count} errors.', 'success')
            return redirect(url_for('transactions.clients'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error importing transactions: {str(e)}")
            flash('Error importing transactions. Please check file format.', 'error')
            from app.utils.frontend_helper import serve_frontend
            return serve_frontend('/import')

@transactions_bp.route('/export')
@login_required
@handle_errors
def export_transactions():
    """Export transactions to CSV"""
    try:
        # Build query
        query = Transaction.query
        
        # Apply filters
        query = apply_transaction_filters(query)
        
        # Order by date (newest first)
        query = query.order_by(desc(Transaction.date))
        
        transactions = query.all()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Client Name', 'IBAN', 'Payment Method', 'Company Order',
            'Date', 'Category', 'Amount', 'Commission', 'Net Amount',
            'Currency', 'PSP', 'Notes', 'Created At'
        ])
        
        # Write data
        for transaction in transactions:
            writer.writerow([
                transaction.id,
                transaction.client_name,
                transaction.iban or '',
                transaction.payment_method or '',
                transaction.company_order or '',
                transaction.date.strftime('%Y-%m-%d'),
                transaction.category or '',
                float(transaction.amount),
                float(transaction.commission),
                float(transaction.net_amount),
                transaction.currency,
                transaction.psp or '',
                transaction.notes or '',
                transaction.created_at.strftime('%Y-%m-%d %H:%M:%S') if transaction.created_at else ''
            ])
        
        # Create response
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=transactions.csv'}
        )
        
    except Exception as e:
        logger.error(f"Error exporting transactions: {str(e)}")
        flash('Error exporting transactions.', 'error')
        return redirect(url_for('transactions.clients'))

@transactions_bp.route('/view/<int:transaction_id>')
@login_required
def view_transaction(transaction_id):
    """View transaction details page"""
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Get related transactions for this client
    related_transactions = Transaction.query.filter_by(
        client_name=transaction.client_name
    ).filter(
        Transaction.id != transaction_id
    ).order_by(desc(Transaction.date)).limit(5).all()
    
    from app.utils.frontend_helper import serve_frontend
    return serve_frontend(f'/transactions/{transaction_id}')

@transactions_bp.route('/daily_summary/<date>', methods=['GET', 'POST'])
@login_required
def daily_summary(date):
    """Show daily summary for a specific date"""
    try:
        # Parse date
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD format.', 'error')
            return redirect(url_for('transactions.clients'))
        
        # Check for force refresh parameter
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        if force_refresh:
            # Clear cache for this specific date
            try:
                from app.services.query_service import QueryService
                QueryService.invalidate_transaction_cache()
                logger.info(f"Cache cleared for daily summary refresh on {date}")
            except Exception as cache_error:
                logger.warning(f"Failed to clear cache for daily summary refresh: {cache_error}")
        
        # Handle USD rate update
        if request.method == 'POST':
            usd_rate = request.form.get('usd_rate')
            if usd_rate:
                try:
                    usd_rate = Decimal(str(usd_rate))
                    if usd_rate <= 0:
                        flash('USD rate must be positive.', 'error')
                    else:
                        # Update or create exchange rate for this date
                        from app.models.config import ExchangeRate
                        exchange_rate = ExchangeRate.query.filter_by(date=date_obj).first()
                        if exchange_rate:
                            exchange_rate.usd_to_tl = usd_rate
                        else:
                            exchange_rate = ExchangeRate(
                                date=date_obj,
                                usd_to_tl=usd_rate
                            )
                            db.session.add(exchange_rate)
                        
                        db.session.commit()
                        
                        # Invalidate cache after exchange rate update
                        try:
                            from app.services.query_service import QueryService
                            QueryService.invalidate_transaction_cache()
                            logger.info("Cache invalidated after USD rate update")
                        except Exception as cache_error:
                            logger.warning(f"Failed to invalidate cache after USD rate update: {cache_error}")
                        
                        flash('USD rate updated successfully!', 'success')
                        
                        # Redirect back to the same daily summary page to show updated data
                        return redirect(url_for('transactions.daily_summary', date=date))
                        
                except (ValueError, InvalidOperation):
                    flash('Invalid USD rate format.', 'error')
        
        # Get all transactions for the date
        transactions = Transaction.query.filter_by(date=date_obj).order_by(Transaction.created_at.desc()).all()
        
        # Allow viewing daily summary even without transactions (for setting USD rate)
        if not transactions:
            # Get exchange rate for this date
            from app.models.config import ExchangeRate
            exchange_rate = ExchangeRate.query.filter_by(date=date_obj).first()
            usd_rate = decimal_float_service.safe_decimal(exchange_rate.usd_to_tl) if exchange_rate and exchange_rate.usd_to_tl else None
            
            # Show empty summary with USD rate form
            summary_data = {
                'date': date_obj,
                'date_str': date_obj.strftime('%A, %B %d, %Y'),
                'usd_rate': float(usd_rate) if usd_rate else None,
                'total_amount_tl': 0.0,
                'total_amount_usd': 0.0,
                'total_commission_tl': 0.0,
                'total_commission_usd': 0.0,
                'total_net_tl': 0.0,
                'total_net_usd': 0.0,
                'transaction_count': 0,
                'unique_clients': 0,
                'psp_summary': [],
                'category_summary': [],
                'payment_method_summary': [],
                'transactions': []
            }
            
            from app.utils.frontend_helper import serve_frontend
            return serve_frontend(f'/summary/{date}')
        
        # Get exchange rate for this date
        from app.models.config import ExchangeRate
        exchange_rate = ExchangeRate.query.filter_by(date=date_obj).first()
        usd_rate = decimal_float_service.safe_decimal(exchange_rate.usd_to_tl) if exchange_rate and exchange_rate.usd_to_tl else None
        
        # Calculate summary statistics with USD conversion
        # Separate deposits and withdrawals for proper calculation
        total_deposits_tl = Decimal('0')
        total_withdrawals_tl = Decimal('0')
        total_deposits_usd = Decimal('0')
        total_withdrawals_usd = Decimal('0')
        total_commission_tl = Decimal('0')
        total_commission_usd = Decimal('0')
        total_net_tl = Decimal('0')
        total_net_usd = Decimal('0')
        
        for transaction in transactions:
            amount = decimal_float_service.safe_decimal(transaction.amount)
            commission = decimal_float_service.safe_decimal(transaction.commission)
            net_amount = decimal_float_service.safe_decimal(transaction.net_amount)
            
            # Determine if this is a deposit or withdrawal based on category and amount sign
            # Withdrawals may be stored as negative amounts, deposits as positive
            is_withdrawal = (
                transaction.category and transaction.category.upper() in ['WD', 'WITHDRAW', 'WITHDRAWAL']
            ) or (amount < 0)  # Also check if amount is negative
            
            if transaction.currency and transaction.currency.upper() == 'USD':
                if is_withdrawal:
                    # WD: add absolute value to withdrawals (amount might be negative)
                    total_withdrawals_usd += abs(amount)
                else:
                    # DEP: add to deposits (amount is positive)
                    total_deposits_usd += amount
                total_commission_usd += commission
                if is_withdrawal:
                    total_net_usd -= net_amount  # Subtract withdrawals from net balance
                else:
                    total_net_usd += net_amount  # Add deposits to net balance
                
                # Convert USD to TL for total calculations
                if usd_rate and usd_rate != Decimal('0'):
                    amount_tl = decimal_float_service.safe_multiply(amount, usd_rate, 'decimal')
                    commission_tl = decimal_float_service.safe_multiply(commission, usd_rate, 'decimal')
                    net_amount_tl = decimal_float_service.safe_multiply(net_amount, usd_rate, 'decimal')
                    
                    if is_withdrawal:
                        total_withdrawals_tl += abs(amount_tl)
                        total_net_tl -= net_amount_tl  # Subtract withdrawals from net balance
                    else:
                        total_deposits_tl += amount_tl
                        total_net_tl += net_amount_tl  # Add deposits to net balance
                    total_commission_tl += commission_tl
                else:
                    # Fallback to USD amount
                    if is_withdrawal:
                        total_withdrawals_tl += amount
                        total_net_tl -= net_amount  # Subtract withdrawals from net balance
                    else:
                        total_deposits_tl += amount
                        total_net_tl += net_amount  # Add deposits to net balance
                    total_commission_tl += commission
            else:
                # TL transactions
                if is_withdrawal:
                    total_withdrawals_tl += abs(amount)
                    total_net_tl -= net_amount  # Subtract withdrawals from net balance
                else:
                    total_deposits_tl += amount
                    total_net_tl += net_amount  # Add deposits to net balance
                total_commission_tl += commission
        
        # Calculate totals using DEP + (-WD) formula
        # Withdrawals are stored as positive amounts, but we treat them as negative in calculations
        total_amount_tl = total_deposits_tl - total_withdrawals_tl  # DEP + (-WD)
        total_amount_usd = total_deposits_usd - total_withdrawals_usd  # DEP + (-WD)
        
        # Calculate gross balance (deposits - withdrawals before commission)
        gross_balance_tl = total_deposits_tl - total_withdrawals_tl
        gross_balance_usd = total_deposits_usd - total_withdrawals_usd
        
        transaction_count = len(transactions)
        
        # Group by PSP
        psp_data = defaultdict(lambda: {
            'deposits_tl': Decimal('0'),
            'withdrawals_tl': Decimal('0'),
            'deposits_usd': Decimal('0'),
            'withdrawals_usd': Decimal('0'),
            'amount_tl': Decimal('0'),  # Total (deposits + withdrawals)
            'amount_usd': Decimal('0'),  # Total (deposits + withdrawals)
            'commission_tl': Decimal('0'),
            'commission_usd': Decimal('0'),
            'net_tl': Decimal('0'),
            'net_usd': Decimal('0'),
            'count': 0,
            'transactions': []
        })
        
        for transaction in transactions:
            psp = transaction.psp or 'Unknown'
            amount = decimal_float_service.safe_decimal(transaction.amount)
            commission = decimal_float_service.safe_decimal(transaction.commission)
            net_amount = decimal_float_service.safe_decimal(transaction.net_amount)
            
            # Determine if this is a deposit or withdrawal based on category and amount sign
            # Withdrawals may be stored as negative amounts, deposits as positive
            is_withdrawal = (
                transaction.category and transaction.category.upper() in ['WD', 'WITHDRAW', 'WITHDRAWAL']
            ) or (amount < 0)  # Also check if amount is negative
            
            if transaction.currency and transaction.currency.upper() == 'USD':
                if is_withdrawal:
                    psp_data[psp]['withdrawals_usd'] += amount
                    psp_data[psp]['amount_usd'] -= amount  # Subtract withdrawals from total
                else:
                    psp_data[psp]['deposits_usd'] += amount
                    psp_data[psp]['amount_usd'] += amount  # Add deposits to total
                psp_data[psp]['commission_usd'] += commission
                psp_data[psp]['net_usd'] += net_amount
                
                # Convert to TL for total calculations
                if usd_rate and usd_rate != Decimal('0'):
                    amount_tl = decimal_float_service.safe_multiply(amount, usd_rate, 'decimal')
                    commission_tl = decimal_float_service.safe_multiply(commission, usd_rate, 'decimal')
                    net_amount_tl = decimal_float_service.safe_multiply(net_amount, usd_rate, 'decimal')
                    
                    if is_withdrawal:
                        psp_data[psp]['withdrawals_tl'] += amount_tl
                        psp_data[psp]['amount_tl'] -= amount_tl  # Subtract withdrawals from total
                    else:
                        psp_data[psp]['deposits_tl'] += amount_tl
                        psp_data[psp]['amount_tl'] += amount_tl  # Add deposits to total
                    psp_data[psp]['commission_tl'] += commission_tl
                    psp_data[psp]['net_tl'] += net_amount_tl
                else:
                    # Fallback to USD amount
                    if is_withdrawal:
                        psp_data[psp]['withdrawals_tl'] += amount
                        psp_data[psp]['amount_tl'] -= amount  # Subtract withdrawals from total
                    else:
                        psp_data[psp]['deposits_tl'] += amount
                        psp_data[psp]['amount_tl'] += amount  # Add deposits to total
                    psp_data[psp]['commission_tl'] += commission
                    psp_data[psp]['net_tl'] += net_amount
            else:
                # TL transactions
                if is_withdrawal:
                    psp_data[psp]['withdrawals_tl'] += amount
                    psp_data[psp]['amount_tl'] -= amount  # Subtract withdrawals from total
                else:
                    psp_data[psp]['deposits_tl'] += amount
                    psp_data[psp]['amount_tl'] += amount  # Add deposits to total
                psp_data[psp]['commission_tl'] += commission
                psp_data[psp]['net_tl'] += net_amount
            psp_data[psp]['count'] += 1
            psp_data[psp]['transactions'].append(transaction)
        
        # Group by category
        category_data = defaultdict(lambda: {
            'amount_tl': Decimal('0'),
            'amount_usd': Decimal('0'),
            'commission_tl': Decimal('0'),
            'commission_usd': Decimal('0'),
            'net_tl': Decimal('0'),
            'net_usd': Decimal('0'),
            'count': 0
        })
        
        for transaction in transactions:
            category = transaction.category or 'Unknown'
            if transaction.currency and transaction.currency.upper() == 'USD':
                category_data[category]['amount_usd'] += decimal_float_service.safe_decimal(transaction.amount)
                category_data[category]['commission_usd'] += decimal_float_service.safe_decimal(transaction.commission)
                category_data[category]['net_usd'] += decimal_float_service.safe_decimal(transaction.net_amount)
                # Convert to TL for total calculations
                if usd_rate and usd_rate != Decimal('0'):
                    category_data[category]['amount_tl'] += decimal_float_service.safe_multiply(transaction.amount, usd_rate, 'decimal')
                    category_data[category]['commission_tl'] += decimal_float_service.safe_multiply(transaction.commission, usd_rate, 'decimal')
                    category_data[category]['net_tl'] += decimal_float_service.safe_multiply(transaction.net_amount, usd_rate, 'decimal')
                else:
                    category_data[category]['amount_tl'] += decimal_float_service.safe_decimal(transaction.amount)
                    category_data[category]['commission_tl'] += decimal_float_service.safe_decimal(transaction.commission)
                    category_data[category]['net_tl'] += decimal_float_service.safe_decimal(transaction.net_amount)
            else:
                category_data[category]['amount_tl'] += decimal_float_service.safe_decimal(transaction.amount)
                category_data[category]['commission_tl'] += decimal_float_service.safe_decimal(transaction.commission)
                category_data[category]['net_tl'] += decimal_float_service.safe_decimal(transaction.net_amount)
            category_data[category]['count'] += 1
        
        # Payment method data will be calculated later in the comprehensive calculation
        
        # Get unique clients
        unique_clients = len(set(t.client_name for t in transactions if t.client_name))
        
        # Format PSP data for template
        psp_summary = []
        for psp, data in psp_data.items():
            psp_summary.append({
                'name': psp,
                'deposits_tl': float(data['deposits_tl']),
                'withdrawals_tl': float(data['withdrawals_tl']),
                'deposits_usd': float(data['deposits_usd']),
                'withdrawals_usd': float(data['withdrawals_usd']),
                'gross_tl': float(data['amount_tl']),  # Gross total (deposits - withdrawals, before commission)
                'gross_usd': float(data['amount_usd']),  # Gross total (deposits - withdrawals, before commission)
                'amount_tl': float(data['amount_tl']),  # Keep for backward compatibility
                'amount_usd': float(data['amount_usd']),  # Keep for backward compatibility
                'commission_tl': float(data['commission_tl']),
                'commission_usd': float(data['commission_usd']),
                'net_tl': float(data['net_tl']),
                'net_usd': float(data['net_usd']),
                'count': data['count']
            })
        
        # Format category data for template
        category_summary = []
        for category, data in category_data.items():
            category_summary.append({
                'name': category,
                'gross_tl': float(data['amount_tl']),  # Gross amount (before commission)
                'gross_usd': float(data['amount_usd']),  # Gross amount (before commission)
                'amount_tl': float(data['amount_tl']),  # Keep for backward compatibility
                'amount_usd': float(data['amount_usd']),  # Keep for backward compatibility
                'commission_tl': float(data['commission_tl']),
                'commission_usd': float(data['commission_usd']),
                'net_tl': float(data['net_tl']),
                'net_usd': float(data['net_usd']),
                'count': data['count']
            })
        
        # Payment method summary will be created later in the comprehensive calculation
        payment_method_summary = []  # Initialize empty list
        
        # Sort by TL amount (descending)
        psp_summary.sort(key=lambda x: x['amount_tl'], reverse=True)
        category_summary.sort(key=lambda x: x['amount_tl'], reverse=True)
        # payment_method_summary will be sorted later in the comprehensive calculation
        
        summary_data = {
            'date': date_obj,
            'date_str': date_obj.strftime('%A, %B %d, %Y'),
            'usd_rate': float(usd_rate) if usd_rate else None,
            'total_deposits_tl': float(total_deposits_tl),
            'total_withdrawals_tl': float(total_withdrawals_tl),
            'total_deposits_usd': float(total_deposits_usd),
            'total_withdrawals_usd': float(total_withdrawals_usd),
            'total_amount_tl': float(total_amount_tl),  # Net total (deposits + withdrawals)
            'total_amount_usd': float(total_amount_usd),  # Net total (deposits + withdrawals)
            'total_commission_tl': float(total_commission_tl),
            'total_commission_usd': float(total_commission_usd),
            'total_net_tl': float(total_net_tl),
            'total_net_usd': float(total_net_usd),
            'gross_balance_tl': float(gross_balance_tl),
            'gross_balance_usd': float(gross_balance_usd),
            'transaction_count': transaction_count,
            'unique_clients': unique_clients,
            'psp_summary': psp_summary,
            'category_summary': category_summary,
            'payment_method_summary': payment_method_summary,
            'transactions': transactions
        }
        
        from app.utils.frontend_helper import serve_frontend
        return serve_frontend(f'/summary/{date}')
        
    except Exception as e:
        logger.error(f"Error in daily summary: {str(e)}")
        flash(f'Error loading daily summary for {date}: {str(e)}', 'error')
        # Instead of redirecting to clients, show an error page
        from app.utils.frontend_helper import serve_frontend
        return serve_frontend(f'/summary/{date}')

@transactions_bp.route('/api/<int:transaction_id>')
@login_required
def get_transaction_details(transaction_id):
    """Get transaction details via API"""
    transaction = Transaction.query.get_or_404(transaction_id)
    
    return jsonify({
        'id': transaction.id,
        'client_name': transaction.client_name,
        'iban': transaction.iban,
        'payment_method': transaction.payment_method,
        'company_order': transaction.company_order,
        'date': transaction.date.strftime('%Y-%m-%d'),
        'category': transaction.category,
        'amount': float(transaction.amount),
        'commission': float(transaction.commission),
        'net_amount': float(transaction.net_amount),
        'currency': transaction.currency,
        'psp': transaction.psp,
        'notes': transaction.notes,
        'created_at': transaction.created_at.strftime('%Y-%m-%d %H:%M:%S') if transaction.created_at else None
    })

@transactions_bp.route('/summary/<date>', methods=['GET', 'POST'])
@login_required
def summary_view(date):
    """Alternative summary route - DEFINITE SOLUTION"""
    try:
        return daily_summary(date)
    except Exception as e:
        logger.error(f"Error in summary_view for date {date}: {str(e)}")
        flash(f'Error loading summary for {date}: {str(e)}', 'error')
        # Instead of redirecting to clients, show an error page
        from app.utils.frontend_helper import serve_frontend
        return serve_frontend(f'/summary/{date}')

@transactions_bp.route('/api/summary/<date>')
@login_required
def api_summary(date):
    """API endpoint for summary data - MODAL SOLUTION"""
    try:
        # Parse date
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
        
        # Get all transactions for the date
        transactions = Transaction.query.filter_by(date=date_obj).order_by(Transaction.created_at.desc()).all()
        
        # Get exchange rate for this date
        from app.models.config import ExchangeRate
        exchange_rate = ExchangeRate.query.filter_by(date=date_obj).first()
        usd_rate = decimal_float_service.safe_decimal(exchange_rate.usd_to_tl) if exchange_rate and exchange_rate.usd_to_tl else None
        
        # Fallback: If no exchange rate found for this date, use current rate
        if usd_rate is None:
            # Use enhanced exchange rate service
            from app.services.enhanced_exchange_rate_service import enhanced_exchange_service as rate_service
            try:
                current_rate_value = rate_service.get_current_rate("USD", "TRY")
                if current_rate_value and current_rate_value > 0:
                    usd_rate = decimal_float_service.safe_decimal(current_rate_value)
                else:
                    usd_rate = Decimal('48.0')  # Final fallback
            except:
                usd_rate = Decimal('48.0')  # Final fallback rate
        
        # Calculate summary statistics with proper deposit/withdrawal separation
        total_deposits_tl = Decimal('0')
        total_withdrawals_tl = Decimal('0')
        total_deposits_usd = Decimal('0')
        total_withdrawals_usd = Decimal('0')
        total_commission_tl = Decimal('0')
        total_commission_usd = Decimal('0')
        total_net_tl = Decimal('0')
        total_net_usd = Decimal('0')
        
        for transaction in transactions:
            amount = decimal_float_service.safe_decimal(transaction.amount)
            commission = decimal_float_service.safe_decimal(transaction.commission)
            net_amount = decimal_float_service.safe_decimal(transaction.net_amount)
            
            # Determine if this is a deposit or withdrawal based on category and amount sign
            # Withdrawals may be stored as negative amounts, deposits as positive
            is_withdrawal = (
                transaction.category and transaction.category.upper() in ['WD', 'WITHDRAW', 'WITHDRAWAL']
            ) or (amount < 0)  # Also check if amount is negative
            
            if transaction.currency and transaction.currency.upper() == 'USD':
                if is_withdrawal:
                    total_withdrawals_usd += amount
                else:
                    total_deposits_usd += amount
                total_commission_usd += commission
                total_net_usd += net_amount
                
                # Convert USD to TL for total calculations
                transaction_rate = transaction.exchange_rate if transaction.exchange_rate else usd_rate
                
                if transaction_rate and transaction_rate != Decimal('0'):
                    amount_tl = decimal_float_service.safe_multiply(amount, transaction_rate, 'decimal')
                    commission_tl = decimal_float_service.safe_multiply(commission, transaction_rate, 'decimal')
                    net_amount_tl = decimal_float_service.safe_multiply(net_amount, transaction_rate, 'decimal')
                    
                    if is_withdrawal:
                        total_withdrawals_tl += abs(amount_tl)
                        total_net_tl -= net_amount_tl  # Subtract withdrawals from net balance
                    else:
                        total_deposits_tl += amount_tl
                        total_net_tl += net_amount_tl  # Add deposits to net balance
                    total_commission_tl += commission_tl
                else:
                    # Fallback to USD amount
                    if is_withdrawal:
                        total_withdrawals_tl += amount
                        total_net_tl -= net_amount  # Subtract withdrawals from net balance
                    else:
                        total_deposits_tl += amount
                        total_net_tl += net_amount  # Add deposits to net balance
                    total_commission_tl += commission
            else:
                # TL transactions
                if is_withdrawal:
                    total_withdrawals_tl += abs(amount)
                    total_net_tl -= net_amount  # Subtract withdrawals from net balance
                else:
                    total_deposits_tl += amount
                    total_net_tl += net_amount  # Add deposits to net balance
                total_commission_tl += commission
        
        # Calculate totals using DEP + (-WD) formula
        # Withdrawals are stored as positive amounts, but we treat them as negative in calculations
        total_amount_tl = total_deposits_tl - total_withdrawals_tl  # DEP + (-WD)
        total_amount_usd = total_deposits_usd - total_withdrawals_usd  # DEP + (-WD)
        
        # Debug logging (disabled for cleaner output)
        # print(f"🔍 Daily Summary Debug for {date}:")
        # print(f"  Deposits TL: {total_deposits_tl}")
        # print(f"  Withdrawals TL: {total_withdrawals_tl} (raw)")
        # print(f"  Withdrawals TL: {abs(total_withdrawals_tl)} (absolute)")
        # print(f"  Net TL: {total_net_tl} (Deposits - |Withdrawals|)")
        # print(f"  Expected: {total_deposits_tl} - {abs(total_withdrawals_tl)} = {total_deposits_tl - abs(total_withdrawals_tl)}")
        
        # Group by PSP
        psp_data = defaultdict(lambda: {
            'amount_tl': Decimal('0'),
            'amount_usd': Decimal('0'),
            'commission_tl': Decimal('0'),
            'commission_usd': Decimal('0'),
            'net_tl': Decimal('0'),
            'net_usd': Decimal('0'),
            'count': 0
        })
        
        # Group by Category
        category_data = defaultdict(lambda: {
            'amount_tl': Decimal('0'),
            'amount_usd': Decimal('0'),
            'commission_tl': Decimal('0'),
            'commission_usd': Decimal('0'),
            'net_tl': Decimal('0'),
            'net_usd': Decimal('0'),
            'count': 0
        })
        
        # Group by Payment Method (reinitialize to avoid conflicts with previous calculation)
        payment_method_data = defaultdict(lambda: {
            'amount_tl': Decimal('0'),        # Gross amounts in TL
            'amount_usd': Decimal('0'),       # Gross amounts in USD
            'commission_tl': Decimal('0'),
            'commission_usd': Decimal('0'),
            'net_tl': Decimal('0'),
            'net_usd': Decimal('0'),
            'count': 0
        })
        
        for transaction in transactions:
            psp = transaction.psp or 'Unknown'
            category = transaction.category or 'Unknown'
            payment_method = transaction.payment_method or 'Unknown'
            
            if transaction.currency and transaction.currency.upper() == 'USD':
                psp_data[psp]['amount_usd'] += decimal_float_service.safe_decimal(transaction.amount)
                psp_data[psp]['commission_usd'] += decimal_float_service.safe_decimal(transaction.commission)
                psp_data[psp]['net_usd'] += decimal_float_service.safe_decimal(transaction.net_amount)
                category_data[category]['amount_usd'] += decimal_float_service.safe_decimal(transaction.amount)
                category_data[category]['commission_usd'] += decimal_float_service.safe_decimal(transaction.commission)
                category_data[category]['net_usd'] += decimal_float_service.safe_decimal(transaction.net_amount)
                # Payment method: Use GROSS amount for gross calculation
                payment_method_data[payment_method]['amount_usd'] += decimal_float_service.safe_decimal(transaction.amount)
                payment_method_data[payment_method]['commission_usd'] += decimal_float_service.safe_decimal(transaction.commission)
                payment_method_data[payment_method]['net_usd'] += decimal_float_service.safe_decimal(transaction.net_amount)
                
                if usd_rate:
                    psp_data[psp]['amount_tl'] += decimal_float_service.safe_multiply(transaction.amount, usd_rate, 'decimal')
                    psp_data[psp]['commission_tl'] += decimal_float_service.safe_multiply(transaction.commission, usd_rate, 'decimal')
                    psp_data[psp]['net_tl'] += decimal_float_service.safe_multiply(transaction.net_amount, usd_rate, 'decimal')
                    category_data[category]['amount_tl'] += decimal_float_service.safe_multiply(transaction.amount, usd_rate, 'decimal')
                    category_data[category]['commission_tl'] += decimal_float_service.safe_multiply(transaction.commission, usd_rate, 'decimal')
                    category_data[category]['net_tl'] += decimal_float_service.safe_multiply(transaction.net_amount, usd_rate, 'decimal')
                    # Payment method: Use GROSS amount for gross calculation
                    payment_method_data[payment_method]['amount_tl'] += decimal_float_service.safe_multiply(transaction.amount, usd_rate, 'decimal')
                    payment_method_data[payment_method]['commission_tl'] += decimal_float_service.safe_multiply(transaction.commission, usd_rate, 'decimal')
                    payment_method_data[payment_method]['net_tl'] += decimal_float_service.safe_multiply(transaction.net_amount, usd_rate, 'decimal')
                else:
                    psp_data[psp]['amount_tl'] += decimal_float_service.safe_decimal(transaction.amount)
                    psp_data[psp]['commission_tl'] += decimal_float_service.safe_decimal(transaction.commission)
                    psp_data[psp]['net_tl'] += decimal_float_service.safe_decimal(transaction.net_amount)
                    category_data[category]['amount_tl'] += decimal_float_service.safe_decimal(transaction.amount)
                    category_data[category]['commission_tl'] += decimal_float_service.safe_decimal(transaction.commission)
                    category_data[category]['net_tl'] += decimal_float_service.safe_decimal(transaction.net_amount)
                    # Payment method: Use GROSS amount for gross calculation
                    payment_method_data[payment_method]['amount_tl'] += decimal_float_service.safe_decimal(transaction.amount)
                    payment_method_data[payment_method]['commission_tl'] += decimal_float_service.safe_decimal(transaction.commission)
                    payment_method_data[payment_method]['net_tl'] += decimal_float_service.safe_decimal(transaction.net_amount)
            else:
                psp_data[psp]['amount_tl'] += decimal_float_service.safe_decimal(transaction.amount)
                psp_data[psp]['commission_tl'] += decimal_float_service.safe_decimal(transaction.commission)
                psp_data[psp]['net_tl'] += decimal_float_service.safe_decimal(transaction.net_amount)
                category_data[category]['amount_tl'] += decimal_float_service.safe_decimal(transaction.amount)
                category_data[category]['commission_tl'] += decimal_float_service.safe_decimal(transaction.commission)
                category_data[category]['net_tl'] += decimal_float_service.safe_decimal(transaction.net_amount)
                # Payment method: Use GROSS amount for gross calculation
                payment_method_data[payment_method]['amount_tl'] += decimal_float_service.safe_decimal(transaction.amount)
                payment_method_data[payment_method]['commission_tl'] += decimal_float_service.safe_decimal(transaction.commission)
                payment_method_data[payment_method]['net_tl'] += decimal_float_service.safe_decimal(transaction.net_amount)
            
            psp_data[psp]['count'] += 1
            category_data[category]['count'] += 1
            payment_method_data[payment_method]['count'] += 1
        
        # NEW CALCULATION LOGIC (USD-first approach):
        # Step 1: Calculate net amounts for each currency (deposits - withdrawals)
        try_net = total_deposits_tl - total_withdrawals_tl
        usd_net = total_deposits_usd - total_withdrawals_usd
        
        # Step 2: Calculate USD Gross Balance FIRST
        # Formula: (TRY_net / rate) + USD_net
        if usd_rate and usd_rate != Decimal('0'):
            gross_balance_usd = decimal_float_service.safe_divide(try_net, usd_rate, 'decimal') + usd_net
        else:
            # Fallback if no rate available
            gross_balance_usd = usd_net
        
        # Step 3: Calculate TRY Gross Balance from USD
        # Formula: USD_gross * rate
        if usd_rate and usd_rate != Decimal('0'):
            gross_balance_tl = decimal_float_service.safe_multiply(gross_balance_usd, usd_rate, 'decimal')
        else:
            # Fallback if no rate available
            gross_balance_tl = try_net
        
        # Format data for JSON response
        summary_data = {
            'date': date,
            'date_str': date_obj.strftime('%A, %B %d, %Y'),
            'usd_rate': usd_rate,
            'total_amount_tl': float(total_amount_tl),
            'total_amount_usd': float(total_amount_usd),
            'total_commission_tl': float(total_commission_tl),
            'total_commission_usd': float(total_commission_usd),
            'total_net_tl': float(total_net_tl),
            'total_net_usd': float(total_net_usd),
            'gross_balance_tl': float(gross_balance_tl),
            'gross_balance_usd': float(gross_balance_usd),
            'total_deposits_tl': float(total_deposits_tl),
            'total_deposits_usd': float(total_deposits_usd),
            'total_withdrawals_tl': float(total_withdrawals_tl),
            'total_withdrawals_usd': float(total_withdrawals_usd),
            'transaction_count': len(transactions),
            'unique_clients': len(set(t.client_name for t in transactions if t.client_name)),
            'psp_summary': [
                {
                    'name': psp,
                    'gross_tl': float(data['amount_tl']),  # Gross amount (before commission)
                    'gross_usd': float(data['amount_usd']),  # Gross amount (before commission)
                    'amount_tl': float(data['amount_tl']),  # For backward compatibility
                    'amount_usd': float(data['amount_usd']),  # For backward compatibility
                    'commission_tl': float(data['commission_tl']),
                    'commission_usd': float(data['commission_usd']),
                    'net_tl': float(data['net_tl']),
                    'net_usd': float(data['net_usd']),
                    'count': data['count'],
                    # Special handling for Tether PSP - show USD as primary currency
                    'is_tether': psp.upper() == 'TETHER',
                    'primary_currency': 'USD' if psp.upper() == 'TETHER' else 'TRY'
                }
                for psp, data in psp_data.items()
            ],
            'category_summary': [
                {
                    'name': category,
                    'amount_tl': float(data['amount_tl']),
                    'amount_usd': float(data['amount_usd']),
                    'commission_tl': float(data['commission_tl']),
                    'commission_usd': float(data['commission_usd']),
                    'net_tl': float(data['net_tl']),
                    'net_usd': float(data['net_usd']),
                    'count': data['count']
                }
                for category, data in category_data.items()
            ],
            'payment_method_summary': [
                {
                    'name': payment_method,
                    'gross_tl': float(data['amount_tl']),  # Gross amount (before commission)
                    'gross_usd': float(data['amount_usd']),  # Gross amount (before commission)
                    'amount_tl': float(data['amount_tl']),  # For backward compatibility
                    'amount_usd': float(data['amount_usd']),  # For backward compatibility
                    'commission_tl': float(data['commission_tl']),
                    'commission_usd': float(data['commission_usd']),
                    'net_tl': float(data['net_tl']),
                    'net_usd': float(data['net_usd']),
                    'count': data['count']
                }
                for payment_method, data in payment_method_data.items()
            ],
            'transactions': [
                {
                    'id': t.id,
                    'client_name': t.client_name,
                    'amount': float(t.amount),
                    'commission': float(t.commission),
                    'net_amount': float(t.net_amount),
                    'currency': t.currency,
                    'psp': t.psp,
                    'category': t.category,
                    'payment_method': t.payment_method,
                    'notes': t.notes or ''
                }
                for t in transactions
            ]
        }
        
        return jsonify(summary_data)
        
    except Exception as e:
        logger.error(f"Error in API summary: {str(e)}")
        return jsonify({'error': 'Error loading summary data'}), 500


@transactions_bp.route('/api/summary/batch', methods=['GET'])
# @login_required  # Temporarily disabled for debugging
def api_summary_batch():
    """Batch API endpoint for multiple date summaries - PERFORMANCE SOLUTION"""
    try:
        # Get dates from query parameter (comma-separated)
        dates_param = request.args.get('dates', '')
        if not dates_param:
            return jsonify({'error': 'No dates provided'}), 400
        
        # Parse dates
        date_strings = [d.strip() for d in dates_param.split(',') if d.strip()]
        if not date_strings:
            return jsonify({'error': 'No valid dates provided'}), 400
        
        # Limit to reasonable batch size
        if len(date_strings) > 100:
            return jsonify({'error': 'Too many dates requested (max 100)'}), 400
        
        # Parse and validate all dates first
        date_objects = []
        for date_str in date_strings:
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                date_objects.append((date_str, date_obj))
            except ValueError:
                logger.warning(f"Invalid date format: {date_str}")
                continue
        
        if not date_objects:
            return jsonify({'error': 'No valid dates in request'}), 400
        
        # Get all transactions for all dates in one query (optimization)
        all_dates = [date_obj for _, date_obj in date_objects]
        all_transactions = Transaction.query.filter(Transaction.date.in_(all_dates)).all()
        
        # Group transactions by date
        transactions_by_date = defaultdict(list)
        for transaction in all_transactions:
            if transaction.date:
                transactions_by_date[transaction.date].append(transaction)
        
        # Daily KUR rates from KASA.xlsx (used as fallback when no USD transactions)
        from app.services.excel_import_service import ExcelImportService
        DAILY_KUR_RATES = ExcelImportService.DAILY_KUR_RATES
        
        # Build response for each date
        summaries = {}
        
        for date_str, date_obj in date_objects:
            transactions = transactions_by_date.get(date_obj, [])
            
            # Get exchange rate from USD transactions for this date (most accurate)
            usd_rate = None
            for t in transactions:
                if t.currency and t.currency.upper() == 'USD' and t.exchange_rate:
                    rate_value = decimal_float_service.safe_decimal(t.exchange_rate)
                    if rate_value and rate_value > 1:  # Valid rate
                        usd_rate = rate_value
                        break
            
            # Fallback 1: Use the daily KUR rates from KASA.xlsx
            if usd_rate is None and date_str in DAILY_KUR_RATES:
                usd_rate = DAILY_KUR_RATES[date_str]
            
            # Fallback 2: Try ExchangeRate table
            if usd_rate is None:
                from app.models.config import ExchangeRate
                exchange_rate = ExchangeRate.query.filter_by(date=date_obj).first()
                if exchange_rate and exchange_rate.usd_to_tl:
                    usd_rate = decimal_float_service.safe_decimal(exchange_rate.usd_to_tl)
            
            # Final fallback: Use a default rate (should rarely happen)
            if usd_rate is None:
                usd_rate = Decimal('42.0')  # Final fallback rate
            
            # Calculate summary statistics (same logic as single endpoint)
            total_deposits_tl = Decimal('0')
            total_withdrawals_tl = Decimal('0')
            total_deposits_usd = Decimal('0')
            total_withdrawals_usd = Decimal('0')
            total_commission_tl = Decimal('0')
            total_commission_usd = Decimal('0')
            total_net_tl = Decimal('0')
            total_net_usd = Decimal('0')
            
            for transaction in transactions:
                amount = decimal_float_service.safe_decimal(transaction.amount)
                commission = decimal_float_service.safe_decimal(transaction.commission)
                net_amount = decimal_float_service.safe_decimal(transaction.net_amount)
                
                is_withdrawal = (
                    transaction.category and transaction.category.upper() in ['WD', 'WITHDRAW', 'WITHDRAWAL']
                ) or (amount < 0)
                
                if transaction.currency and transaction.currency.upper() == 'USD':
                    if is_withdrawal:
                        total_withdrawals_usd += abs(amount)  # Store as positive value
                    else:
                        total_deposits_usd += amount
                    total_commission_usd += commission
                    total_net_usd += net_amount
                    
                    # NOTE: USD transactions are NOT converted to TRY for gross balance calculation
                    # They remain as USD and are used directly in the USD-first calculation
                else:
                    # TL transactions
                    if is_withdrawal:
                        total_withdrawals_tl += abs(amount)
                        total_net_tl -= net_amount
                    else:
                        total_deposits_tl += amount
                        total_net_tl += net_amount
                    total_commission_tl += commission
            
            # NEW CALCULATION LOGIC (USD-first approach):
            # Step 1: Calculate net amounts for each currency (deposits - withdrawals)
            try_net = total_deposits_tl - total_withdrawals_tl
            usd_net = total_deposits_usd - total_withdrawals_usd
            
            # DEBUG: Log calculation details for September 30th
            if date_str == '2025-09-30':
                print(f"🔍 DEBUG September 30th:")
                print(f"  Total Deposits TL: {total_deposits_tl}")
                print(f"  Total Withdrawals TL: {total_withdrawals_tl}")
                print(f"  Total Deposits USD: {total_deposits_usd}")
                print(f"  Total Withdrawals USD: {total_withdrawals_usd}")
                print(f"  TRY Net: {try_net}")
                print(f"  USD Net: {usd_net}")
                print(f"  Exchange Rate: {usd_rate}")
            
            # Step 2: Calculate USD Gross Balance FIRST
            # Formula: (TRY_net / rate) + USD_net
            if usd_rate and usd_rate != Decimal('0'):
                gross_balance_usd = decimal_float_service.safe_divide(try_net, usd_rate, 'decimal') + usd_net
            else:
                # Fallback if no rate available
                gross_balance_usd = usd_net
            
            # Step 3: Calculate TRY Gross Balance from USD
            # Formula: USD_gross * rate
            if usd_rate and usd_rate != Decimal('0'):
                gross_balance_tl = decimal_float_service.safe_multiply(gross_balance_usd, usd_rate, 'decimal')
            else:
                # Fallback if no rate available
                gross_balance_tl = try_net
            
            # DEBUG: Log final results for September 30th
            if date_str == '2025-09-30':
                print(f"  Calculated USD Gross: {gross_balance_usd}")
                print(f"  Calculated TRY Gross: {gross_balance_tl}")
            
            # Store summary for this date
            summaries[date_str] = {
                'date': date_str,
                'transaction_count': len(transactions),
                'total_deposits_tl': float(total_deposits_tl),
                'total_withdrawals_tl': float(abs(total_withdrawals_tl)),
                'total_deposits_usd': float(total_deposits_usd),
                'total_withdrawals_usd': float(abs(total_withdrawals_usd)),
                'total_commission_tl': float(total_commission_tl),
                'total_commission_usd': float(total_commission_usd),
                'gross_balance_tl': float(gross_balance_tl),
                'gross_balance_usd': float(gross_balance_usd),
                'total_net_tl': float(total_net_tl),
                'total_net_usd': float(total_net_usd),
                'exchange_rate': float(usd_rate) if usd_rate else None
            }
        
        return jsonify({
            'success': True,
            'summaries': summaries,
            'count': len(summaries)
        })
        
    except Exception as e:
        logger.error(f"Error in batch API summary: {str(e)}")
        return jsonify({'error': 'Error loading batch summary data'}), 500
