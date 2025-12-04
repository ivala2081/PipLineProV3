"""
API routes blueprint
"""
from flask import Blueprint, request, jsonify, Response
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta, timezone
from sqlalchemy import func, extract, desc, and_, or_
import json
from decimal import Decimal
from collections import defaultdict
import logging

from app import db
from app.models.transaction import Transaction
from app.models.user import User
from app.models.config import Option
from app.models.config import ExchangeRate
from app.models.financial import PspTrack, DailyBalance
from app.utils.unified_error_handler import (
    handle_api_errors, validate_request_data, validate_numeric_field, validate_date_field,
    PipLineError, ValidationError, ResourceNotFoundError, DatabaseError,
    log_error, safe_execute
)
from app.utils.unified_logger import get_logger, log_function_call as performance_log
from app.utils.db_compat import ilike_compat

# Configure logging
logger = get_logger(__name__)

# Create blueprint
api_bp = Blueprint('api', __name__)

# Import strategy functions
from app.api.v1.endpoints.strategy import (
    implement_strategy, get_strategy_status, deactivate_strategy
)

@api_bp.route('/api/csrf-token')
@login_required
def get_csrf_token():
    """Get CSRF token for forms"""
    from flask_wtf.csrf import generate_csrf
    try:
        token = generate_csrf()
        return jsonify({'csrf_token': token})
    except Exception as e:
        logger.error(f"Error generating CSRF token: {str(e)}")
        # Try to generate a new session-based token
        try:
            from flask import session
            if 'csrf_token' not in session:
                session['csrf_token'] = generate_csrf()
            return jsonify({'csrf_token': session['csrf_token']})
        except Exception as e2:
            logger.error(f"Error generating session CSRF token: {str(e2)}")
            return jsonify({'error': 'Could not generate CSRF token'}), 500

@api_bp.route('/api/transaction/<int:transaction_id>')
@login_required
@handle_api_errors
@performance_log
def get_transaction_details(transaction_id):
    """Get transaction details via API"""
    transaction = Transaction.query.get_or_404(transaction_id)
    
    return jsonify({
        'id': transaction.id,
        'client_name': transaction.client_name,
        'iban': getattr(transaction, 'iban', ''),  # Safe access - field may not exist
        'payment_method': transaction.payment_method,
        'company_order': getattr(transaction, 'company_order', ''),  # Safe access
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

@api_bp.route('/api/psp_summary_stats')
@login_required
@handle_api_errors
@performance_log
def api_psp_summary_stats():
    """Get PSP summary statistics"""
    # Get date range - if days is 0 or not specified, get all transactions
    days = request.args.get('days')
    if days is None or days == '0':
        # Get all transactions
        transactions = Transaction.query.filter(Transaction.psp.isnot(None)).all()
    else:
        days = validate_numeric_field(days, 'days', min_value=1, max_value=365)
        end_date = date.today()
        start_date = end_date - timedelta(days=int(days))
        
        # Get transactions in date range
        transactions = Transaction.query.filter(
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.psp.isnot(None)
        ).all()
    
    # Group by PSP
    psp_data = defaultdict(lambda: {
        'total_amount': Decimal('0'),
        'total_commission': Decimal('0'),
        'total_net': Decimal('0'),
        'transaction_count': 0
    })
    
    for transaction in transactions:
        psp = transaction.psp or 'Unknown'
        psp_data[psp]['total_amount'] += transaction.amount
        psp_data[psp]['total_commission'] += transaction.commission
        psp_data[psp]['total_net'] += transaction.net_amount
        psp_data[psp]['transaction_count'] += 1
    
    # Format response
    result = []
    for psp, data in psp_data.items():
        result.append({
            'psp': psp,
            'total_amount': float(data['total_amount']),
            'total_commission': float(data['total_commission']),
            'total_net': float(data['total_net']),
            'transaction_count': data['transaction_count'],
            'commission_rate': float(data['total_commission'] / data['total_amount'] * 100) if data['total_amount'] > 0 else 0
        })
    
    return jsonify(result)

@api_bp.route('/api/export_psp_data', methods=['POST'])
@login_required
def api_export_psp_data():
    """Export PSP data"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        psp_filter = data.get('psp')
        
        # Build query
        query = Transaction.query
        
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(Transaction.date >= start_date_obj)
            except ValueError:
                return jsonify({'error': 'Invalid start date format'}), 400
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(Transaction.date <= end_date_obj)
            except ValueError:
                return jsonify({'error': 'Invalid end date format'}), 400
        
        if psp_filter:
            query = query.filter(Transaction.psp == psp_filter)
        
        transactions = query.order_by(Transaction.date).all()
        
        # Format data for export
        export_data = []
        for transaction in transactions:
            export_data.append({
                'date': transaction.date.strftime('%Y-%m-%d'),
                'client_name': transaction.client_name,
                'psp': transaction.psp or '',
                'amount': float(transaction.amount),
                'commission': float(transaction.commission),
                'net_amount': float(transaction.net_amount),
                'category': transaction.category or '',
                'payment_method': transaction.payment_method or '',
                'currency': transaction.currency
            })
        
        return jsonify({
            'success': True,
            'data': export_data,
            'count': len(export_data)
        })
        
    except Exception as e:
        logger.error(f"Error exporting PSP data: {str(e)}")
        return jsonify({'error': 'Failed to export PSP data'}), 500

@api_bp.route('/api/check_exchange_rates')
@login_required
def api_check_exchange_rates():
    """Check exchange rates for a date range"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'error': 'Start date and end date are required'}), 400
        
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
        
        # Get exchange rates in range
        rates = ExchangeRate.query.filter(
            ExchangeRate.date >= start_date_obj,
            ExchangeRate.date <= end_date_obj
        ).order_by(ExchangeRate.date).all()
        
        # Check for missing dates
        missing_dates = []
        current_date = start_date_obj
        while current_date <= end_date_obj:
            rate_exists = any(rate.date == current_date for rate in rates)
            if not rate_exists:
                missing_dates.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
        
        # Format response
        result = {
            'rates': [
                {
                    'date': rate.date.strftime('%Y-%m-%d'),
                    'usd_to_tl': float(rate.usd_to_tl) if rate.usd_to_tl else None,
                    'eur_to_tl': float(rate.eur_to_tl) if rate.eur_to_tl else None
                }
                for rate in rates
            ],
            'missing_dates': missing_dates,
            'total_dates': len(missing_dates) + len(rates),
            'available_dates': len(rates),
            'missing_count': len(missing_dates)
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error checking exchange rates: {str(e)}")
        return jsonify({'error': 'Failed to check exchange rates'}), 500

@api_bp.route('/api/check_currencies_on_date')
@login_required
def api_check_currencies_on_date():
    """Check currencies available on a specific date"""
    try:
        check_date = request.args.get('date')
        if not check_date:
            return jsonify({'error': 'Date parameter is required'}), 400
        
        try:
            date_obj = datetime.strptime(check_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
        
        # Get exchange rate for the date
        rate = ExchangeRate.query.filter_by(date=date_obj).first()
        
        if rate:
            result = {
                'date': check_date,
                'available': True,
                'usd_to_tl': float(rate.usd_to_tl) if rate.usd_to_tl else None,
                'eur_to_tl': float(rate.eur_to_tl) if rate.eur_to_tl else None,
                'currencies': []
            }
            
            if rate.usd_to_tl:
                result['currencies'].append('USD')
            if rate.eur_to_tl:
                result['currencies'].append('EUR')
            
            return jsonify(result)
        else:
            return jsonify({
                'date': check_date,
                'available': False,
                'currencies': []
            })
        
    except Exception as e:
        logger.error(f"Error checking currencies on date: {str(e)}")
        return jsonify({'error': 'Failed to check currencies'}), 500

@api_bp.route('/api/psp_details/<date>/<psp>')
@login_required
def api_psp_details(date, psp):
    """Get detailed PSP information for a specific date"""
    try:
        # Parse date
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
        
        # Get transactions for the PSP on the date
        transactions = Transaction.query.filter(
            Transaction.date == date_obj,
            Transaction.psp == psp
        ).all()
        
        # Calculate totals
        total_amount = sum(t.amount for t in transactions)
        total_commission = sum(t.commission for t in transactions)
        total_net = sum(t.net_amount for t in transactions)
        
        # Get daily balance if exists
        daily_balance = DailyBalance.query.filter_by(
            date=date_obj,
            psp=psp
        ).first()
        
        # Format response
        result = {
            'date': date,
            'psp': psp,
            'transaction_count': len(transactions),
            'total_amount': float(total_amount),
            'total_commission': float(total_commission),
            'total_net': float(total_net),
            'transactions': [
                {
                    'id': t.id,
                    'client_name': t.client_name,
                    'amount': float(t.amount),
                    'commission': float(t.commission),
                    'net_amount': float(t.net_amount),
                    'category': t.category,
                    'payment_method': t.payment_method
                }
                for t in transactions
            ]
        }
        
        if daily_balance:
            result['daily_balance'] = {
                'opening_balance': float(daily_balance.opening_balance),
                'total_inflow': float(daily_balance.total_inflow),
                'total_outflow': float(daily_balance.total_outflow),
                'total_commission': float(daily_balance.total_commission),
                'net_amount': float(daily_balance.net_amount),
                'closing_balance': float(daily_balance.closing_balance),
                'allocation': float(daily_balance.allocation) if daily_balance.allocation else None
            }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting PSP details: {str(e)}")
        return jsonify({'error': 'Failed to get PSP details'}), 500

@api_bp.route('/api/validate_exchange_rates')
@login_required
def api_validate_exchange_rates():
    """Validate exchange rates for a date range"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'error': 'Start date and end date are required'}), 400
        
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
        
        # Get exchange rates in range
        rates = ExchangeRate.query.filter(
            ExchangeRate.date >= start_date_obj,
            ExchangeRate.date <= end_date_obj
        ).order_by(ExchangeRate.date).all()
        
        # Validate each rate
        validation_results = []
        for rate in rates:
            issues = []
            
            if not rate.usd_to_tl or rate.usd_to_tl <= 0:
                issues.append('Invalid USD exchange rate')
            
            if rate.eur_to_tl and rate.eur_to_tl <= 0:
                issues.append('Invalid EUR exchange rate')
            
            # Check for reasonable ranges (USD should be around 30-35 TL)
            if rate.usd_to_tl and (rate.usd_to_tl < 10 or rate.usd_to_tl > 100):
                issues.append('USD rate seems unrealistic')
            
            if rate.eur_to_tl and (rate.eur_to_tl < 10 or rate.eur_to_tl > 150):
                issues.append('EUR rate seems unrealistic')
            
            validation_results.append({
                'date': rate.date.strftime('%Y-%m-%d'),
                'usd_to_tl': float(rate.usd_to_tl) if rate.usd_to_tl else None,
                'eur_to_tl': float(rate.eur_to_tl) if rate.eur_to_tl else None,
                'valid': len(issues) == 0,
                'issues': issues
            })
        
        return jsonify({
            'validation_results': validation_results,
            'total_rates': len(validation_results),
            'valid_rates': len([r for r in validation_results if r['valid']]),
            'invalid_rates': len([r for r in validation_results if not r['valid']])
        })
        
    except Exception as e:
        logger.error(f"Error validating exchange rates: {str(e)}")
        return jsonify({'error': 'Failed to validate exchange rates'}), 500

@api_bp.route('/api/debug_day_summary/<date>')
@login_required
def api_debug_day_summary(date):
    """Debug day summary for troubleshooting"""
    try:
        # Parse date
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
        
        # Get all transactions for the date
        transactions = Transaction.query.filter_by(date=date_obj).all()
        
        # Get exchange rate for the date
        exchange_rate = ExchangeRate.query.filter_by(date=date_obj).first()
        
        # Get daily balances for the date
        daily_balances = DailyBalance.query.filter_by(date=date_obj).all()
        
        # Calculate totals by PSP
        psp_totals = defaultdict(lambda: {
            'amount': Decimal('0'),
            'commission': Decimal('0'),
            'net': Decimal('0'),
            'count': 0
        })
        
        for transaction in transactions:
            psp = transaction.psp or 'Unknown'
            psp_totals[psp]['amount'] += transaction.amount
            psp_totals[psp]['commission'] += transaction.commission
            psp_totals[psp]['net'] += transaction.net_amount
            psp_totals[psp]['count'] += 1
        
        # Format response
        result = {
            'date': date,
            'total_transactions': len(transactions),
            'total_amount': float(sum(t.amount for t in transactions)),
            'total_commission': float(sum(t.commission for t in transactions)),
            'total_net': float(sum(t.net_amount for t in transactions)),
            'exchange_rate': {
                'usd_to_tl': float(exchange_rate.usd_to_tl) if exchange_rate and exchange_rate.usd_to_tl else None,
                'eur_to_tl': float(exchange_rate.eur_to_tl) if exchange_rate and exchange_rate.eur_to_tl else None
            } if exchange_rate else None,
            'psp_totals': {
                psp: {
                    'amount': float(data['amount']),
                    'commission': float(data['commission']),
                    'net': float(data['net']),
                    'count': data['count']
                }
                for psp, data in psp_totals.items()
            },
            'daily_balances': [
                {
                    'psp': balance.psp,
                    'opening_balance': float(balance.opening_balance),
                    'total_inflow': float(balance.total_inflow),
                    'total_outflow': float(balance.total_outflow),
                    'total_commission': float(balance.total_commission),
                    'net_amount': float(balance.net_amount),
                    'closing_balance': float(balance.closing_balance),
                    'allocation': float(balance.allocation) if balance.allocation else None
                }
                for balance in daily_balances
            ],
            'transactions': [
                {
                    'id': t.id,
                    'client_name': t.client_name,
                    'psp': t.psp,
                    'amount': float(t.amount),
                    'commission': float(t.commission),
                    'net_amount': float(t.net_amount),
                    'category': t.category,
                    'payment_method': t.payment_method
                }
                for t in transactions
            ]
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in debug day summary: {str(e)}")
        return jsonify({'error': 'Failed to get debug day summary'}), 500

@api_bp.route('/api/mark_as_paid/<date>/<psp>', methods=['POST'])
@login_required
def api_mark_as_paid(date, psp):
    """Mark PSP as paid for a specific date"""
    try:
        # Parse date
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
        
        # Get or create daily balance
        daily_balance = DailyBalance.query.filter_by(
            date=date_obj,
            psp=psp
        ).first()
        
        if not daily_balance:
            return jsonify({'error': 'No daily balance found for this date and PSP'}), 404
        
        # Update paid status
        data = request.get_json()
        if data and 'paid' in data:
            daily_balance.is_paid = data['paid']
            db.session.commit()
            
            return jsonify({
                'success': True,
                'date': date,
                'psp': psp,
                'paid': daily_balance.is_paid
            })
        else:
            return jsonify({'error': 'Paid status is required'}), 400
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error marking as paid: {str(e)}")
        return jsonify({'error': 'Failed to mark as paid'}), 500 

@api_bp.route('/api/psp-allocations', methods=['POST'])
@login_required
def api_psp_allocations():
    """Update PSP allocation amounts"""
    try:
        data = request.get_json()
        
        # Debug logging
        logger.info(f"Received PSP allocation data: {data}")
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        date_str = data.get('date')
        psp = data.get('psp')
        allocation = data.get('allocation')
        
        logger.info(f"Parsed fields - date: {date_str}, psp: {psp}, allocation: {allocation}")
        
        if not all([date_str, psp, allocation is not None]):
            missing_fields = []
            if not date_str: missing_fields.append('date')
            if not psp: missing_fields.append('psp')
            if allocation is None: missing_fields.append('allocation')
            return jsonify({'success': False, 'message': f'Missing required fields: {missing_fields}'}), 400
        
        # Parse date
        try:
            allocation_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format'}), 400
        
        # Convert allocation to Decimal
        try:
            allocation_amount = Decimal(str(allocation)) if allocation else Decimal('0')
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Invalid allocation amount'}), 400
        
        # Find or create PSP track record
        psp_track = PspTrack.query.filter_by(
            date=allocation_date,
            psp_name=psp
        ).first()
        
        if psp_track:
            # Update existing record
            psp_track.allocation = allocation_amount
            psp_track.updated_at = datetime.now()
        else:
            # Create new record
            psp_track = PspTrack(
                date=allocation_date,
                psp_name=psp,
                allocation=allocation_amount,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.session.add(psp_track)
        
        # Commit changes
        db.session.commit()
        
        logger.info(f"Updated PSP allocation: {psp} on {date_str} = {allocation_amount}")
        
        return jsonify({
            'success': True,
            'message': 'Allocation updated successfully',
            'data': {
                'date': date_str,
                'psp': psp,
                'allocation': float(allocation_amount)
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating PSP allocation: {str(e)}")
        return jsonify({'success': False, 'message': f'Failed to update allocation: {str(e)}'}), 500

@api_bp.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
    
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'database': db_status,
        'version': '1.0.0'
    }) 

@api_bp.route('/api/dashboard/stats')
@login_required
@handle_api_errors
@performance_log
def api_dashboard_stats():
    """Get dashboard statistics for React frontend"""
    try:
        from datetime import datetime, date, timedelta
        from sqlalchemy import func, desc
        from app.models.transaction import Transaction
        from app.models.user import User
        
        # Get date range - if no date filter, get all-time data
        days_filter = request.args.get('days')
        if days_filter is None or days_filter == '0':
            # Get all-time data
            revenue_query = db.session.query(
                func.sum(Transaction.amount).label('total_amount'),
                func.sum(Transaction.commission).label('total_commission'),
                func.sum(Transaction.net_amount).label('total_net')
            ).first()
            
            transaction_count = Transaction.query.count()
            active_clients = db.session.query(
                func.count(func.distinct(Transaction.client_name))
            ).scalar() or 0
        else:
            # Get date range (last N days)
            days = int(days_filter)
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            # Total revenue (last N days)
            revenue_query = db.session.query(
                func.sum(Transaction.amount).label('total_amount'),
                func.sum(Transaction.commission).label('total_commission'),
                func.sum(Transaction.net_amount).label('total_net')
            ).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).first()
            
            # Total transactions (last N days)
            transaction_count = Transaction.query.filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).count()
            
            # Active clients (unique clients in last N days)
            active_clients = db.session.query(
                func.count(func.distinct(Transaction.client_name))
            ).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).scalar() or 0
        
        total_revenue = float(revenue_query.total_amount or 0)
        total_commission = float(revenue_query.total_commission or 0)
        total_net = float(revenue_query.total_net or 0)
        
        # Growth rate calculation
        if days_filter is None or days_filter == '0':
            # For all-time data, growth rate is 0
            growth_rate = 0
        else:
            # Growth rate (compare with previous period)
            prev_start_date = start_date - timedelta(days=days)
            prev_revenue_query = db.session.query(
                func.sum(Transaction.amount).label('total_amount')
            ).filter(
                Transaction.date >= prev_start_date,
                Transaction.date < start_date
            ).first()
            
            prev_revenue = float(prev_revenue_query.total_amount or 0)
            growth_rate = 0
            if prev_revenue > 0:
                growth_rate = ((total_revenue - prev_revenue) / prev_revenue) * 100
        
        # Recent transactions (last 10)
        recent_transactions = Transaction.query.order_by(
            desc(Transaction.created_at)
        ).limit(10).all()
        
        recent_transactions_data = []
        for transaction in recent_transactions:
            recent_transactions_data.append({
                'id': transaction.id,
                'client_name': transaction.client_name,
                'amount': float(transaction.amount),
                'currency': transaction.currency,
                'date': transaction.date.strftime('%Y-%m-%d'),
                'status': 'completed',  # You can add status field to your model
                'created_at': transaction.created_at.strftime('%Y-%m-%d %H:%M:%S') if transaction.created_at else None
            })
        
        return jsonify({
            'stats': {
                'total_revenue': {
                    'value': f"${total_revenue:,.2f}",
                    'change': f"{growth_rate:+.1f}%",
                    'changeType': 'positive' if growth_rate >= 0 else 'negative'
                },
                'total_transactions': {
                    'value': f"{transaction_count:,}",
                    'change': '+180.1%',  # You can calculate this dynamically
                    'changeType': 'positive'
                },
                'active_clients': {
                    'value': f"{active_clients:,}",
                    'change': '+19%',  # You can calculate this dynamically
                    'changeType': 'positive'
                },
                'growth_rate': {
                    'value': f"{growth_rate:+.2f}%",
                    'change': '+4.75%',  # You can calculate this dynamically
                    'changeType': 'positive' if growth_rate >= 0 else 'negative'
                }
            },
            'recent_transactions': recent_transactions_data,
            'summary': {
                'total_revenue': total_revenue,
                'total_commission': total_commission,
                'total_net': total_net,
                'transaction_count': transaction_count,
                'active_clients': active_clients,
                'growth_rate': growth_rate
            }
        })
        
    except Exception as e:
        logger.error(f"Error in dashboard stats API: {str(e)}")
        return jsonify({'error': 'Failed to fetch dashboard statistics'}), 500

@api_bp.route('/api/transactions')
@login_required
@handle_api_errors
@performance_log
def api_transactions_list():
    """Get transactions list for React frontend"""
    try:
        from datetime import datetime, date, timedelta
        from sqlalchemy import desc
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        client_name = request.args.get('client_name')
        psp = request.args.get('psp')
        category = request.args.get('category')
        
        # Build query
        query = Transaction.query
        
        # Apply filters
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
                
        if client_name:
            query = query.filter(ilike_compat(Transaction.client_name, f'%{client_name}%'))
            
        if psp:
            query = query.filter(ilike_compat(Transaction.psp, f'%{psp}%'))
            
        if category:
            query = query.filter(Transaction.category == category)
        
        # Order by created_at desc
        query = query.order_by(desc(Transaction.created_at))
        
        # Paginate
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        transactions_data = []
        for transaction in pagination.items:
            transactions_data.append({
                'id': transaction.id,
                'client_name': transaction.client_name,
                'iban': getattr(transaction, 'iban', ''),  # Safe access - field may not exist
                'payment_method': transaction.payment_method,
                'company_order': getattr(transaction, 'company_order', ''),  # Safe access
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
        
        return jsonify({
            'transactions': transactions_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Error in transactions list API: {str(e)}")
        return jsonify({'error': 'Failed to fetch transactions'}), 500

@api_bp.route('/api/analytics/overview')
@login_required
@handle_api_errors
@performance_log
def api_analytics_overview():
    """Get analytics overview for React frontend"""
    try:
        from datetime import datetime, date, timedelta
        from sqlalchemy import func, desc
        from collections import defaultdict
        
        # Get date range (last 30 days)
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        # Get transactions in date range
        transactions = Transaction.query.filter(
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).all()
        
        # Group by PSP
        psp_data = defaultdict(lambda: {
            'total_amount': 0.0,
            'total_commission': 0.0,
            'total_net': 0.0,
            'transaction_count': 0
        })
        
        # Group by category
        category_data = defaultdict(lambda: {
            'total_amount': 0.0,
            'total_commission': 0.0,
            'total_net': 0.0,
            'transaction_count': 0
        })
        
        # Group by client
        client_data = defaultdict(lambda: {
            'total_amount': 0.0,
            'total_commission': 0.0,
            'total_net': 0.0,
            'transaction_count': 0
        })
        
        # Process transactions
        for transaction in transactions:
            amount = float(transaction.amount)
            commission = float(transaction.commission)
            net_amount = float(transaction.net_amount)
            
            # PSP data
            psp_data[transaction.psp]['total_amount'] += amount
            psp_data[transaction.psp]['total_commission'] += commission
            psp_data[transaction.psp]['total_net'] += net_amount
            psp_data[transaction.psp]['transaction_count'] += 1
            
            # Category data
            category_data[transaction.category]['total_amount'] += amount
            category_data[transaction.category]['total_commission'] += commission
            category_data[transaction.category]['total_net'] += net_amount
            category_data[transaction.category]['transaction_count'] += 1
            
            # Client data
            client_data[transaction.client_name]['total_amount'] += amount
            client_data[transaction.client_name]['total_commission'] += commission
            client_data[transaction.client_name]['total_net'] += net_amount
            client_data[transaction.client_name]['transaction_count'] += 1
        
        # Convert to lists and sort
        psp_summary = [
            {
                'psp': psp,
                'total_amount': data['total_amount'],
                'total_commission': data['total_commission'],
                'total_net': data['total_net'],
                'transaction_count': data['transaction_count']
            }
            for psp, data in psp_data.items()
        ]
        psp_summary.sort(key=lambda x: x['total_amount'], reverse=True)
        
        category_summary = [
            {
                'category': category,
                'total_amount': data['total_amount'],
                'total_commission': data['total_commission'],
                'total_net': data['total_net'],
                'transaction_count': data['transaction_count']
            }
            for category, data in category_data.items()
        ]
        category_summary.sort(key=lambda x: x['total_amount'], reverse=True)
        
        client_summary = [
            {
                'client_name': client,
                'total_amount': data['total_amount'],
                'total_commission': data['total_commission'],
                'total_net': data['total_net'],
                'transaction_count': data['transaction_count']
            }
            for client, data in client_data.items()
        ]
        client_summary.sort(key=lambda x: x['total_amount'], reverse=True)
        
        return jsonify({
            'psp_summary': psp_summary,
            'category_summary': category_summary,
            'client_summary': client_summary,
            'date_range': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            }
        })
        
    except Exception as e:
        logger.error(f"Error in analytics overview API: {str(e)}")
        return jsonify({'error': 'Failed to fetch analytics data'}), 500

@api_bp.route('/api/clients')
@login_required
@handle_api_errors
@performance_log
def api_clients_list():
    """Get clients list for React frontend"""
    try:
        from sqlalchemy import func, desc
        from collections import defaultdict
        
        # Get all transactions
        transactions = Transaction.query.all()
        
        # Group by client
        client_data = defaultdict(lambda: {
            'total_amount': 0.0,
            'total_commission': 0.0,
            'total_net': 0.0,
            'transaction_count': 0,
            'first_transaction': None,
            'last_transaction': None,
            'currencies': set(),
            'psps': set()
        })
        
        # Process transactions
        for transaction in transactions:
            client = client_data[transaction.client_name]
            client['total_amount'] += float(transaction.amount)
            client['total_commission'] += float(transaction.commission)
            client['total_net'] += float(transaction.net_amount)
            client['transaction_count'] += 1
            client['currencies'].add(transaction.currency)
            client['psps'].add(transaction.psp)
            
            if not client['first_transaction'] or transaction.date < client['first_transaction']:
                client['first_transaction'] = transaction.date
            if not client['last_transaction'] or transaction.date > client['last_transaction']:
                client['last_transaction'] = transaction.date
        
        # Convert to list and format
        clients_list = []
        for client_name, data in client_data.items():
            clients_list.append({
                'client_name': client_name,
                'total_amount': data['total_amount'],
                'total_commission': data['total_commission'],
                'total_net': data['total_net'],
                'transaction_count': data['transaction_count'],
                'first_transaction': data['first_transaction'].strftime('%Y-%m-%d') if data['first_transaction'] else None,
                'last_transaction': data['last_transaction'].strftime('%Y-%m-%d') if data['last_transaction'] else None,
                'currencies': list(data['currencies']),
                'psps': list(data['psps']),
                'avg_transaction': data['total_amount'] / data['transaction_count'] if data['transaction_count'] > 0 else 0
            })
        
        # Sort by total amount
        clients_list.sort(key=lambda x: x['total_amount'], reverse=True)
        
        return jsonify({
            'clients': clients_list,
            'total_clients': len(clients_list)
        })
        
    except Exception as e:
        logger.error(f"Error in clients list API: {str(e)}")
        return jsonify({'error': 'Failed to fetch clients data'}), 500

# Strategy Implementation Routes
@api_bp.route('/api/strategy/implement', methods=['POST'])
@login_required
def api_implement_strategy():
    """Implement a revenue optimization strategy"""
    return implement_strategy()

@api_bp.route('/api/strategy/status', methods=['GET'])
@login_required
def api_get_strategy_status():
    """Get status of all implemented strategies"""
    return get_strategy_status()

@api_bp.route('/api/strategy/deactivate', methods=['POST'])
@login_required
def api_deactivate_strategy():
    """Deactivate a strategy"""
    return deactivate_strategy() 