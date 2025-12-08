from flask import Blueprint, request, jsonify
from app import db
from app.models.transaction import Transaction
from app.models.config import ExchangeRate
from app.services.decimal_float_fix_service import decimal_float_service
from app.utils.unified_logger import get_logger
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import func, and_

logger = get_logger(__name__)

bulk_rates_bp = Blueprint('bulk_rates', __name__)

@bulk_rates_bp.route('/bulk-rates/usd-dates', methods=['GET'])
def get_usd_transaction_dates():
    """Get all dates that have USD currency transactions"""
    try:
        # Get unique dates with USD transactions
        usd_dates = db.session.query(
            Transaction.date,
            func.count(Transaction.id).label('transaction_count'),
            func.sum(Transaction.amount).label('total_usd_amount')
        ).filter(
            and_(
                Transaction.currency == 'USD',
                Transaction.date.isnot(None)
            )
        ).group_by(Transaction.date).order_by(Transaction.date.desc()).all()
        
        result = []
        for date_obj, count, total_amount in usd_dates:
            # Get current exchange rate for this date
            current_rate = None
            exchange_rate = ExchangeRate.query.filter_by(date=date_obj).first()
            if exchange_rate and exchange_rate.usd_to_tl:
                current_rate = float(exchange_rate.usd_to_tl)
            
            result.append({
                'date': date_obj.isoformat() if date_obj else None,
                'transaction_count': count,
                'total_usd_amount': float(total_amount) if total_amount else 0,
                'current_rate': current_rate
            })
        
        return jsonify({
            'success': True,
            'usd_dates': result
        })
        
    except Exception as e:
        logger.error(f"Error fetching USD transaction dates: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch USD transaction dates'
        }), 500

@bulk_rates_bp.route('/bulk-rates/apply-usd-rate', methods=['POST'])
def apply_usd_rate():
    """Apply USD rate to all transactions on a specific date"""
    try:
        data = request.get_json()
        target_date = data.get('date')
        usd_rate = data.get('rate')
        
        if not target_date or not usd_rate:
            return jsonify({
                'success': False,
                'error': 'Date and rate are required'
            }), 400
        
        # Parse date
        try:
            date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }), 400
        
        # Validate rate
        try:
            rate_decimal = Decimal(str(usd_rate))
            if rate_decimal <= 0:
                return jsonify({
                    'success': False,
                    'error': 'Rate must be greater than 0'
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'Invalid rate format'
            }), 400
        
        # Get all USD transactions for this date
        usd_transactions = Transaction.query.filter(
            and_(
                Transaction.date == date_obj,
                Transaction.currency == 'USD'
            )
        ).all()
        
        if not usd_transactions:
            return jsonify({
                'success': False,
                'error': f'No USD transactions found for date {target_date}'
            }), 404
        
        # Update exchange rate for this date
        exchange_rate = ExchangeRate.query.filter_by(date=date_obj).first()
        if not exchange_rate:
            exchange_rate = ExchangeRate(date=date_obj)
            db.session.add(exchange_rate)
        
        exchange_rate.usd_to_tl = rate_decimal
        
        # Update all USD transactions for this date
        updated_count = 0
        for transaction in usd_transactions:
            # Update exchange rate
            transaction.exchange_rate = rate_decimal
            
            # Recalculate amount_try
            transaction.amount_try = decimal_float_service.safe_multiply(
                transaction.amount, 
                rate_decimal, 
                'decimal'
            )
            
            # Recalculate commission_try
            transaction.commission_try = decimal_float_service.safe_multiply(
                transaction.commission, 
                rate_decimal, 
                'decimal'
            )
            
            # Recalculate net_amount_try
            transaction.net_amount_try = decimal_float_service.safe_multiply(
                transaction.net_amount, 
                rate_decimal, 
                'decimal'
            )
            
            updated_count += 1
        
        # Commit all changes
        db.session.commit()
        
        logger.info(f"Applied USD rate {rate_decimal} to {updated_count} transactions on {target_date}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully applied rate {rate_decimal} to {updated_count} USD transactions on {target_date}',
            'updated_count': updated_count
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error applying USD rate: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to apply USD rate'
        }), 500

@bulk_rates_bp.route('/bulk-rates/apply-multiple-usd-rates', methods=['POST'])
def apply_multiple_usd_rates():
    """Apply multiple USD rates to different dates"""
    try:
        data = request.get_json()
        rates_data = data.get('rates', [])
        
        if not rates_data:
            return jsonify({
                'success': False,
                'error': 'Rates data is required'
            }), 400
        
        results = []
        total_updated = 0
        
        for rate_info in rates_data:
            target_date = rate_info.get('date')
            usd_rate = rate_info.get('rate')
            
            if not target_date or not usd_rate:
                results.append({
                    'date': target_date,
                    'success': False,
                    'error': 'Date and rate are required'
                })
                continue
            
            try:
                # Parse date
                date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
                
                # Validate rate
                rate_decimal = Decimal(str(usd_rate))
                if rate_decimal <= 0:
                    results.append({
                        'date': target_date,
                        'success': False,
                        'error': 'Rate must be greater than 0'
                    })
                    continue
                
                # Get USD transactions for this date
                usd_transactions = Transaction.query.filter(
                    and_(
                        Transaction.date == date_obj,
                        Transaction.currency == 'USD'
                    )
                ).all()
                
                if not usd_transactions:
                    results.append({
                        'date': target_date,
                        'success': False,
                        'error': f'No USD transactions found'
                    })
                    continue
                
                # Update exchange rate for this date
                exchange_rate = ExchangeRate.query.filter_by(date=date_obj).first()
                if not exchange_rate:
                    exchange_rate = ExchangeRate(date=date_obj)
                    db.session.add(exchange_rate)
                
                exchange_rate.usd_to_tl = rate_decimal
                
                # Update all USD transactions for this date
                updated_count = 0
                for transaction in usd_transactions:
                    transaction.exchange_rate = rate_decimal
                    transaction.amount_try = decimal_float_service.safe_multiply(
                        transaction.amount, rate_decimal, 'decimal'
                    )
                    transaction.commission_try = decimal_float_service.safe_multiply(
                        transaction.commission, rate_decimal, 'decimal'
                    )
                    transaction.net_amount_try = decimal_float_service.safe_multiply(
                        transaction.net_amount, rate_decimal, 'decimal'
                    )
                    updated_count += 1
                
                total_updated += updated_count
                results.append({
                    'date': target_date,
                    'success': True,
                    'updated_count': updated_count
                })
                
            except Exception as e:
                results.append({
                    'date': target_date,
                    'success': False,
                    'error': str(e)
                })
        
        # Commit all changes
        db.session.commit()
        
        logger.info(f"Applied multiple USD rates. Total updated: {total_updated}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully applied rates to {total_updated} USD transactions',
            'total_updated': total_updated,
            'results': results
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error applying multiple USD rates: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to apply multiple USD rates'
        }), 500
