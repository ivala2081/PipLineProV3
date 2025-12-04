"""
Exchange Rate API endpoints
Handles currency conversion, rate management, and real-time updates
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.utils.permission_decorators import require_permission
from datetime import datetime, date
from decimal import Decimal
import logging

from app.models.exchange_rate import ExchangeRate
from app.models.transaction import Transaction
# Use enhanced exchange rate service (legacy service deprecated)
from app.services.enhanced_exchange_rate_service import enhanced_exchange_service as exchange_rate_service
from app import db, limiter
import uuid
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# Create blueprint
exchange_rates_bp = Blueprint('exchange_rates', __name__)


@exchange_rates_bp.route('/current', methods=['GET'])
def get_current_rate():
    """
    Get current USD/TRY exchange rate
    
    Priority:
    1. Manual exchange_rate table for today
    2. Enhanced service (API)
    
    Returns:
        JSON: Current rate data with metadata
    """
    try:
        # Önce database'den bugünün manuel kurunu kontrol et
        from app.models.config import ExchangeRate as ManualExchangeRate
        from datetime import date
        
        today = date.today()
        manual_rate = ManualExchangeRate.query.filter_by(date=today).first()
        
        if manual_rate and manual_rate.usd_to_tl:
            # Manuel kur bulundu
            return jsonify({
                'success': True,
                'rate': {
                    'rate': float(manual_rate.usd_to_tl),
                    'currency_pair': 'USD/TRY',
                    'source': 'manual',
                    'is_fallback': False,
                    'is_manual': True,
                    'date': today.isoformat()
                },
                'is_stale': False,
                'age_minutes': 0,
                'message': 'Manual rate for today'
            })
        
        # Manuel kur yoksa servis'ten çek
        current_rate = exchange_rate_service.get_current_rate("USD", "TRY")
        
        if not current_rate:
            return jsonify({
                'success': False,
                'message': 'No current exchange rate available',
                'rate': None
            }), 404
        
        # Enhanced service returns a float. Provide a minimal, consistent payload.
        return jsonify({
            'success': True,
            'rate': {
                'rate': float(current_rate),
                'currency_pair': 'USD/TRY',
                'source': 'enhanced_multi_provider',
                'is_fallback': False,
                'is_manual': False
            },
            'is_stale': False,
            'age_minutes': None,
            'message': 'Current rate from API'
        })
        
    except Exception as e:
        logger.error(f"Error getting current rate: {e}")
        return jsonify({
            'success': False,
            'message': f'Error fetching current rate: {str(e)}'
        }), 500


@exchange_rates_bp.route('/rates', methods=['GET'])
@limiter.limit("60 per minute, 1000 per hour")  # More generous rate limits for exchange rates
def get_exchange_rates():
    """
    Get current exchange rates for multiple currencies
    
    Returns:
        JSON: Current rates for USD/TRY and EUR/TRY
    """
    try:
        # Get USD/TRY rate
        usd_rate = exchange_rate_service.get_current_rate("USD", "TRY")
        
        # Get EUR/TRY rate
        eur_rate = exchange_rate_service.get_current_rate("EUR", "TRY")
        
        rates = {}
        
        if usd_rate:
            rates['USD_TRY'] = {
                'rate': float(usd_rate),
                'currency_pair': 'USD/TRY',
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'is_stale': False,
                'age_minutes': None,
                'rate_source': 'enhanced_multi_provider',
                'is_fallback': False
            }
        
        if eur_rate:
            rates['EUR_TRY'] = {
                'rate': float(eur_rate),
                'currency_pair': 'EUR/TRY',
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'is_stale': False,
                'age_minutes': None,
                'rate_source': 'enhanced_multi_provider',
                'is_fallback': False
            }
        
        return jsonify({
            'success': True,
            'rates': rates,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting exchange rates: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get exchange rates',
            'error': str(e)
        }), 500


@exchange_rates_bp.route('/update', methods=['POST'])
@login_required
@require_permission('rates:update')
def force_rate_update():
    """
    Force an immediate exchange rate update from yfinance
    
    Returns:
        JSON: Update result and new rate data
    """
    try:
        logger.info("Force updating exchange rate via API")
        
        success = exchange_rate_service.force_update()
        
        if success:
            current_rate = exchange_rate_service.get_current_rate("USD", "TRY")
            return jsonify({
                'success': True,
                'message': 'Exchange rate updated successfully',
                'rate': {
                    'rate': float(current_rate) if current_rate else None,
                    'currency_pair': 'USD/TRY',
                    'source': 'enhanced_multi_provider',
                    'is_fallback': False
                } if current_rate else None
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to update exchange rate'
            }), 500
            
    except Exception as e:
        logger.error(f"Error forcing rate update: {e}")
        return jsonify({
            'success': False,
            'message': f'Error updating rate: {str(e)}'
        }), 500


@exchange_rates_bp.route('/history', methods=['GET'])
@login_required
def get_rate_history():
    """
    Get historical exchange rate data
    
    Query parameters:
        - limit: Number of records to return (default: 50, max: 200)
        - currency_pair: Currency pair (default: USDTRY)
    
    Returns:
        JSON: List of historical rates
    """
    try:
        limit = min(int(request.args.get('limit', 50)), 200)  # Cap at 200
        currency_pair = request.args.get('currency_pair', 'USDTRY')
        
        rates = ExchangeRate.get_rate_history(currency_pair, limit)
        
        return jsonify({
            'success': True,
            'rates': [rate.to_dict() for rate in rates],
            'count': len(rates)
        })
        
    except Exception as e:
        logger.error(f"Error getting rate history: {e}")
        return jsonify({
            'success': False,
            'message': f'Error fetching rate history: {str(e)}'
        }), 500


@exchange_rates_bp.route('/convert', methods=['POST'])
@login_required
def convert_currency():
    """
    Convert amount between currencies
    
    Request body:
        {
            "amount": 100.0,
            "from_currency": "USD",
            "to_currency": "TRY",
            "rate": 27.5 (optional - uses current rate if not provided)
        }
    
    Returns:
        JSON: Conversion result
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        amount = data.get('amount')
        from_currency = data.get('from_currency', 'USD')
        to_currency = data.get('to_currency', 'TRY')
        custom_rate = data.get('rate')
        
        if amount is None:
            return jsonify({
                'success': False,
                'message': 'Amount is required'
            }), 400
        
        # Convert amount to Decimal
        amount_decimal = Decimal(str(amount))
        
        # Handle USD to TRY conversion
        if from_currency == 'USD' and to_currency == 'TRY':
            if custom_rate:
                rate = Decimal(str(custom_rate))
                converted_amount = amount_decimal * rate
                rate_source = 'custom'
            else:
                current_rate = exchange_rate_service.get_current_rate("USD", "TRY")
                rate = Decimal(str(current_rate)) if current_rate else Decimal('42.02')
                converted_amount = amount_decimal * rate
                rate_source = 'enhanced_multi_provider' if current_rate else 'fallback'
        
        # Handle TRY to USD conversion
        elif from_currency == 'TRY' and to_currency == 'USD':
            if custom_rate:
                rate = Decimal(str(custom_rate))
                converted_amount = amount_decimal / rate
                rate_source = 'custom'
            else:
                current_rate = exchange_rate_service.get_current_rate("USD", "TRY")
                rate = Decimal(str(current_rate)) if current_rate else Decimal('42.02')
                converted_amount = amount_decimal / rate
                rate_source = 'enhanced_multi_provider' if current_rate else 'fallback'
        
        else:
            return jsonify({
                'success': False,
                'message': f'Conversion from {from_currency} to {to_currency} not supported'
            }), 400
        
        return jsonify({
            'success': True,
            'original_amount': float(amount_decimal),
            'converted_amount': float(converted_amount),
            'from_currency': from_currency,
            'to_currency': to_currency,
            'exchange_rate': float(rate),
            'rate_source': rate_source
        })
        
    except Exception as e:
        logger.error(f"Error converting currency: {e}")
        return jsonify({
            'success': False,
            'message': f'Error converting currency: {str(e)}'
        }), 500


@exchange_rates_bp.route('/transactions/update-rates', methods=['POST'])
@login_required
@require_permission('rates:update')
def update_transaction_rates():
    """
    Update exchange rates for transactions on a specific date
    
    Request body:
        {
            "date": "2025-08-31",
            "rate": 27.5,
            "currency": "USD" (optional, defaults to USD)
        }
    
    Returns:
        JSON: Update result with count of affected transactions
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        date_str = data.get('date')
        new_rate = data.get('rate')
        currency = data.get('currency', 'USD')
        
        if not date_str or not new_rate:
            return jsonify({
                'success': False,
                'message': 'Date and rate are required'
            }), 400
        
        # Parse date
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        new_rate_decimal = Decimal(str(new_rate))
        
        # Find transactions for the date with the specified currency
        transactions = Transaction.query.filter(
            Transaction.date == target_date,
            Transaction.currency == currency
        ).all()
        
        if not transactions:
            return jsonify({
                'success': False,
                'message': f'No {currency} transactions found for {date_str}'
            }), 404
        
        # Update each transaction's exchange rate
        updated_count = 0
        for transaction in transactions:
            if transaction.update_exchange_rate(new_rate_decimal):
                updated_count += 1
        
        # Save changes
        db.session.commit()
        
        logger.info(f"Updated exchange rates for {updated_count} transactions on {date_str}")
        
        return jsonify({
            'success': True,
            'message': f'Updated exchange rates for {updated_count} transactions',
            'updated_count': updated_count,
            'total_found': len(transactions),
            'date': date_str,
            'rate': float(new_rate_decimal),
            'currency': currency
        })
        
    except Exception as e:
        logger.error(f"Error updating transaction rates: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating transaction rates: {str(e)}'
        }), 500


@exchange_rates_bp.route('/transactions/usd-summary', methods=['GET'])
@login_required
def get_usd_transaction_summary():
    """
    Get summary of USD transactions grouped by date
    
    Query parameters:
        - start_date: Start date (YYYY-MM-DD, optional)
        - end_date: End date (YYYY-MM-DD, optional)
    
    Returns:
        JSON: USD transaction summary by date
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query
        query = Transaction.query.filter(Transaction.currency == 'USD')
        
        if start_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Transaction.date >= start_date_obj)
        
        if end_date:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Transaction.date <= end_date_obj)
        
        # Group by date
        from sqlalchemy import func
        results = query.with_entities(
            Transaction.date,
            func.count(Transaction.id).label('transaction_count'),
            func.sum(Transaction.amount).label('total_usd'),
            func.avg(Transaction.exchange_rate).label('avg_rate'),
            func.min(Transaction.exchange_rate).label('min_rate'),
            func.max(Transaction.exchange_rate).label('max_rate')
        ).group_by(Transaction.date).order_by(Transaction.date.desc()).all()
        
        summary = []
        for result in results:
            summary.append({
                'date': result.date.isoformat(),
                'transaction_count': result.transaction_count,
                'total_usd': float(result.total_usd) if result.total_usd else 0.0,
                'avg_rate': float(result.avg_rate) if result.avg_rate else None,
                'min_rate': float(result.min_rate) if result.min_rate else None,
                'max_rate': float(result.max_rate) if result.max_rate else None
            })
        
        return jsonify({
            'success': True,
            'summary': summary,
            'total_dates': len(summary)
        })
        
    except Exception as e:
        logger.error(f"Error getting USD transaction summary: {e}")
        return jsonify({
            'success': False,
            'message': f'Error getting USD summary: {str(e)}'
        }), 500


@exchange_rates_bp.route('/status', methods=['GET'])
@login_required
def get_exchange_service_status():
    """
    Get status of the exchange rate service
    
    Returns:
        JSON: Service status and current rate info
    """
    try:
        current_rate = exchange_rate_service.get_current_rate("USD", "TRY")
        is_stale = exchange_rate_service.is_rate_stale()
        
        status = {
            'service_running': exchange_rate_service.is_running,
            'current_rate_available': current_rate is not None,
            'rate_is_stale': is_stale,
            'last_update': current_rate.created_at.isoformat() if current_rate else None,
            'rate_value': float(current_rate.rate) if current_rate else None,
            'rate_source': current_rate.source if current_rate else None,
            'update_interval_minutes': exchange_rate_service.update_interval / 60
        }
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        logger.error(f"Error getting service status: {e}")
        return jsonify({
            'success': False,
            'message': f'Error getting service status: {str(e)}'
        }), 500


# Global variable to store notifications (in production, use Redis or database)
_notifications = []


@exchange_rates_bp.route('/notifications', methods=['GET'])
@login_required
def get_notifications():
    """
    Get exchange rate notifications
    
    Returns:
        JSON: List of notifications
    """
    try:
        # Generate sample notifications based on current rate changes
        current_rate = exchange_rate_service.get_current_rate("USD", "TRY")
        
        if current_rate:
            # Get rate from 24 hours ago for comparison
            yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
            previous_rate = ExchangeRate.get_rate_at_date('USDTRY', yesterday.strftime('%Y-%m-%d'))
            
            notifications = []
            
            if previous_rate:
                change_percent = ((current_rate['rate'] - previous_rate) / previous_rate) * 100
                
                # Generate notification if change is significant (>0.5%)
                if abs(change_percent) > 0.5:
                    notification_type = 'increase' if change_percent > 0 else 'decrease'
                    
                    notification = {
                        'id': str(uuid.uuid4()),
                        'type': notification_type,
                        'title': f'USD/TRY Rate {notification_type.title()}',
                        'message': f'Exchange rate has {"increased" if change_percent > 0 else "decreased"} by {abs(change_percent):.2f}% in the last 24 hours',
                        'currentRate': current_rate['rate'],
                        'previousRate': previous_rate,
                        'changePercent': change_percent,
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'isRead': False
                    }
                    notifications.append(notification)
                
                # Check for high volatility (>2% change)
                if abs(change_percent) > 2.0:
                    volatility_notification = {
                        'id': str(uuid.uuid4()),
                        'type': 'volatility',
                        'title': 'High Volatility Alert',
                        'message': f'USD/TRY rate showing high volatility with {abs(change_percent):.2f}% change. Consider reviewing your USD transactions.',
                        'currentRate': current_rate['rate'],
                        'previousRate': previous_rate,
                        'changePercent': change_percent,
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'isRead': False
                    }
                    notifications.append(volatility_notification)
            
            # Add any stored notifications
            notifications.extend(_notifications)
            
            return jsonify({
                'success': True,
                'notifications': notifications
            })
        
        return jsonify({
            'success': True,
            'notifications': _notifications
        })
        
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return jsonify({
            'success': False,
            'message': f'Error getting notifications: {str(e)}'
        }), 500


@exchange_rates_bp.route('/notifications/<notification_id>/read', methods=['PUT'])
@login_required
def mark_notification_read(notification_id):
    """
    Mark a notification as read
    
    Args:
        notification_id: ID of the notification to mark as read
        
    Returns:
        JSON: Success status
    """
    try:
        # In a real implementation, update the notification in the database
        # For now, we'll just return success
        
        return jsonify({
            'success': True,
            'message': 'Notification marked as read'
        })
        
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        return jsonify({
            'success': False,
            'message': f'Error marking notification as read: {str(e)}'
        }), 500


@exchange_rates_bp.route('/notifications/read-all', methods=['PUT'])
@login_required
def mark_all_notifications_read():
    """
    Mark all notifications as read
    
    Returns:
        JSON: Success status
    """
    try:
        # In a real implementation, update all notifications in the database
        # For now, we'll just return success
        
        return jsonify({
            'success': True,
            'message': 'All notifications marked as read'
        })
        
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        return jsonify({
            'success': False,
            'message': f'Error marking all notifications as read: {str(e)}'
        }), 500


@exchange_rates_bp.route('/notifications/<notification_id>', methods=['DELETE'])
@login_required
def dismiss_notification(notification_id):
    """
    Dismiss a notification
    
    Args:
        notification_id: ID of the notification to dismiss
        
    Returns:
        JSON: Success status
    """
    try:
        # Remove notification from global list
        global _notifications
        _notifications = [n for n in _notifications if n.get('id') != notification_id]
        
        return jsonify({
            'success': True,
            'message': 'Notification dismissed'
        })
        
    except Exception as e:
        logger.error(f"Error dismissing notification: {e}")
        return jsonify({
            'success': False,
            'message': f'Error dismissing notification: {str(e)}'
        }), 500
