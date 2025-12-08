"""
Financial Performance API Endpoints
Provides real transaction data for dashboard financial performance section
"""

from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from app import db, limiter
from app.models.transaction import Transaction
from app.models.config import ExchangeRate  # Use config.ExchangeRate for consistency with consolidated_dashboard
from app.services.historical_exchange_service import historical_exchange_service
from datetime import date, timedelta, datetime
from decimal import Decimal
import logging
import time
from functools import lru_cache

logger = logging.getLogger(__name__)

financial_performance_bp = Blueprint('financial_performance', __name__)

# Simple in-memory cache for financial performance data
_financial_performance_cache = {}
_cache_duration = 1800  # 30 minutes cache (increased for better performance and to handle slow queries)

@financial_performance_bp.route("/clear-cache", methods=["POST"])
@login_required
def clear_financial_performance_cache():
    """Clear the financial performance cache - useful for debugging/testing"""
    global _financial_performance_cache
    cache_keys_count = len(_financial_performance_cache)
    _financial_performance_cache.clear()
    logger.info(f"Financial performance cache cleared ({cache_keys_count} entries removed)")
    return jsonify({
        "success": True,
        "message": f"Cache cleared ({cache_keys_count} entries removed)",
        "cleared_entries": cache_keys_count
    })

def normalize_payment_method(payment_method):
    """Normalize payment method to standard categories
    
    CRITICAL: This function must be consistent across all endpoints.
    Payment methods are normalized to: BANK, CC, TETHER, or OTHER
    """
    if not payment_method:
        return 'OTHER'
    
    # Convert to string and normalize
    pm_str = str(payment_method).strip()
    if not pm_str:
        return 'OTHER'
    
    pm_lower = pm_str.lower()
    
    # Bank variations (includes IBAN transfers)
    if any(keyword in pm_lower for keyword in ['bank', 'banka', 'havale', 'eft', 'wire', 'transfer', 'iban']):
        return 'BANK'
    
    # Credit card variations
    if any(keyword in pm_lower for keyword in ['kk', 'credit', 'card', 'kredi', 'visa', 'mastercard', 'amex']):
        return 'CC'
    
    # Tether variations (company's internal KASA in USD)
    if any(keyword in pm_lower for keyword in ['tether', 'usdt', 'crypto', 'kasa']):
        return 'TETHER'
    
    # Default
    return 'OTHER'

def calculate_financial_metrics(start_date, end_date):
    """Calculate financial metrics for a given date range using SQL aggregates for performance
    
    CRITICAL FIX: Handles both transactions WITH and WITHOUT TRY amounts.
    For transactions without TRY amounts, converts them using current exchange rate.
    This ensures ALL transactions are included in calculations.
    """
    from sqlalchemy import func, and_, case
    
    logger.debug(f"Calculating financial metrics for {start_date} to {end_date}")
    
    # Get current exchange rate for converting transactions without TRY amounts
    # CRITICAL FIX: Use config.ExchangeRate (has usd_to_tl field) for consistency
    try:
        latest_rate = ExchangeRate.query.order_by(ExchangeRate.date.desc()).first()
        exchange_rate = float(latest_rate.usd_to_tl) if latest_rate and latest_rate.usd_to_tl else 48.0
    except:
        exchange_rate = 48.0
    
    # Get EUR rate if available
    try:
        latest_rate = ExchangeRate.query.order_by(ExchangeRate.date.desc()).first()
        eur_rate = float(latest_rate.eur_to_tl) if latest_rate and latest_rate.eur_to_tl else (exchange_rate * 1.08)
    except:
        eur_rate = exchange_rate * 1.08
    
    # Query 1: Transactions WITH TRY amounts (already converted)
    # CRITICAL: Use amount_try (gross) for deposits/withdrawals, net_amount_try for net calculations
    # CRITICAL FIX: Also get original amount and exchange_rate for Tether transactions
    query_with_try = db.session.query(
        Transaction.payment_method,
        Transaction.currency,
        Transaction.category,
        func.sum(func.abs(Transaction.amount_try)).label('total_amount'),  # Gross amount in TL
        func.sum(func.abs(Transaction.net_amount_try)).label('total_net_amount'),  # Net amount in TL
        func.sum(func.abs(func.coalesce(Transaction.commission_try, Transaction.commission))).label('total_commission'),
        func.count(Transaction.id).label('count'),
        func.sum(func.abs(Transaction.amount)).label('total_original_amount'),  # Original amount for Tether
        func.avg(Transaction.exchange_rate).label('avg_exchange_rate'),  # Average exchange rate for conversion back
        func.min(Transaction.exchange_rate).label('min_exchange_rate'),  # Min rate as fallback
        func.max(Transaction.exchange_rate).label('max_exchange_rate')  # Max rate as fallback
    ).filter(
        Transaction.date >= start_date,
        Transaction.date <= end_date,
        Transaction.amount_try.isnot(None)  # Only transactions with TRY amounts
    ).group_by(
        Transaction.payment_method,
        Transaction.currency,
        Transaction.category
    ).all()
    
    # Query 2: Transactions WITHOUT TRY amounts (need conversion)
    query_without_try = db.session.query(
        Transaction.payment_method,
        Transaction.currency,
        Transaction.category,
        Transaction.amount,
        Transaction.net_amount,
        Transaction.commission
    ).filter(
        Transaction.date >= start_date,
        Transaction.date <= end_date,
        Transaction.amount_try.is_(None)
    ).all()
    
    # Initialize totals - all amounts will be in TL
    gross_totals = {'BANK': {'USD': Decimal('0'), 'TL': Decimal('0'), 'count': 0},
                    'CC': {'USD': Decimal('0'), 'TL': Decimal('0'), 'count': 0},
                    'TETHER': {'USD': Decimal('0'), 'TL': Decimal('0'), 'count': 0},
                    'OTHER': {'USD': Decimal('0'), 'TL': Decimal('0'), 'count': 0}}
    
    net_totals = {'BANK': {'USD': Decimal('0'), 'TL': Decimal('0'), 'count': 0},
                  'CC': {'USD': Decimal('0'), 'TL': Decimal('0'), 'count': 0},
                  'TETHER': {'USD': Decimal('0'), 'TL': Decimal('0'), 'count': 0},
                  'OTHER': {'USD': Decimal('0'), 'TL': Decimal('0'), 'count': 0}}
    
    commission_totals = {'BANK': {'USD': Decimal('0'), 'TL': Decimal('0')},
                        'CC': {'USD': Decimal('0'), 'TL': Decimal('0')},
                        'TETHER': {'USD': Decimal('0'), 'TL': Decimal('0')},
                        'OTHER': {'USD': Decimal('0'), 'TL': Decimal('0')}}
    
    deposit_totals = {'BANK': {'USD': Decimal('0'), 'TL': Decimal('0')},
                     'CC': {'USD': Decimal('0'), 'TL': Decimal('0')},
                     'TETHER': {'USD': Decimal('0'), 'TL': Decimal('0')},
                     'OTHER': {'USD': Decimal('0'), 'TL': Decimal('0')}}
    
    withdrawal_totals = {'BANK': {'USD': Decimal('0'), 'TL': Decimal('0')},
                        'CC': {'USD': Decimal('0'), 'TL': Decimal('0')},
                        'TETHER': {'USD': Decimal('0'), 'TL': Decimal('0')},
                        'OTHER': {'USD': Decimal('0'), 'TL': Decimal('0')}}
    
    total_transactions = 0
    
    # Process transactions WITH TRY amounts (already converted)
    for row in query_with_try:
            payment_method = normalize_payment_method(row.payment_method)
            currency = (row.currency or 'TL').upper()
            count = row.count or 0
            
            # CRITICAL FIX: Tether transactions should always stay in USD, regardless of currency field
            # Some Tether transactions might have currency='TL' but should still be treated as USD
            if payment_method == 'TETHER':
                # Tether stays in USD - prefer original amount (should be in USD), fallback to converting amount_try
                # First, try to use original amount (should be in USD for Tether)
                original_amount = Decimal(str(row.total_original_amount or 0))
                
                # Try multiple fallbacks for exchange rate
                avg_rate = None
                if row.avg_exchange_rate is not None:
                    avg_rate = float(row.avg_exchange_rate)
                elif row.min_exchange_rate is not None:
                    avg_rate = float(row.min_exchange_rate)
                elif row.max_exchange_rate is not None:
                    avg_rate = float(row.max_exchange_rate)
                else:
                    avg_rate = exchange_rate
                
                # CRITICAL: If original_amount is 0, it might be because amount values are negative or zero
                # Try to get actual Tether amounts by querying individual transactions
                if original_amount == 0 and row.total_amount and row.total_amount > 0:
                    # Original amount is 0 but amount_try exists - convert back to USD
                    if avg_rate and avg_rate > 0:
                        amount_usd = Decimal(str(row.total_amount or 0)) / Decimal(str(avg_rate))
                        net_amount_usd = Decimal(str(row.total_net_amount or 0)) / Decimal(str(avg_rate))
                        commission_usd = Decimal(str(row.total_commission or 0)) / Decimal(str(avg_rate))
                    elif exchange_rate > 0:
                        # Use current exchange rate as last resort
                        amount_usd = Decimal(str(row.total_amount or 0)) / Decimal(str(exchange_rate))
                        net_amount_usd = Decimal(str(row.total_net_amount or 0)) / Decimal(str(exchange_rate))
                        commission_usd = Decimal(str(row.total_commission or 0)) / Decimal(str(exchange_rate))
                    else:
                        amount_usd = Decimal('0')
                        net_amount_usd = Decimal('0')
                        commission_usd = Decimal('0')
                elif original_amount > 0:
                    # Use original amount (should be in USD for Tether)
                    amount_usd = original_amount
                    # Calculate net_amount_usd: if we have net_amount_try, convert it back
                    if row.total_net_amount and avg_rate and avg_rate > 0:
                        net_amount_usd = Decimal(str(row.total_net_amount or 0)) / Decimal(str(avg_rate))
                    else:
                        # Estimate: net = gross - commission
                        net_amount_usd = amount_usd - Decimal(str(row.total_commission or 0)) / Decimal(str(avg_rate)) if avg_rate and avg_rate > 0 else amount_usd
                    commission_usd = Decimal(str(row.total_commission or 0)) / Decimal(str(avg_rate)) if avg_rate and avg_rate > 0 else Decimal('0')
                elif avg_rate and avg_rate > 0:
                    # Fallback: convert amount_try back to USD
                    amount_usd = Decimal(str(row.total_amount or 0)) / Decimal(str(avg_rate))
                    net_amount_usd = Decimal(str(row.total_net_amount or 0)) / Decimal(str(avg_rate))
                    commission_usd = Decimal(str(row.total_commission or 0)) / Decimal(str(avg_rate))
                else:
                    # Last resort: use current exchange rate
                    if exchange_rate > 0:
                        amount_usd = Decimal(str(row.total_amount or 0)) / Decimal(str(exchange_rate))
                        net_amount_usd = Decimal(str(row.total_net_amount or 0)) / Decimal(str(exchange_rate))
                        commission_usd = Decimal(str(row.total_commission or 0)) / Decimal(str(exchange_rate))
                    else:
                        amount_usd = Decimal('0')
                        net_amount_usd = Decimal('0')
                        commission_usd = Decimal('0')
                
                # Debug logging for Tether transactions
                logger.warning(f"🔍 Tether transaction: payment_method={row.payment_method}, currency={currency}, count={count}, "
                           f"amount_try={row.total_amount}, original_amount={original_amount}, "
                           f"avg_rate={avg_rate}, exchange_rate={exchange_rate}, amount_usd={amount_usd}, net_amount_usd={net_amount_usd}")
                
                total_transactions += count
                
                # Add to USD totals for Tether
                gross_totals[payment_method]['USD'] += amount_usd
                net_totals[payment_method]['USD'] += net_amount_usd
                gross_totals[payment_method]['count'] += count
                net_totals[payment_method]['count'] += count
                
                commission_totals[payment_method]['USD'] += commission_usd
                
                # Categorize as deposit or withdrawal (in USD for Tether)
                if row.category == 'DEP':
                    deposit_totals[payment_method]['USD'] += amount_usd
                elif row.category == 'WD':
                    withdrawal_totals[payment_method]['USD'] += amount_usd
            else:
                # Non-Tether transactions: use TL amounts as before
                # CRITICAL FIX: Use amount_try (gross) for deposits/withdrawals, net_amount_try for net totals
                amount_tl = Decimal(str(row.total_amount or 0))  # This is amount_try (gross)
                net_amount_tl = Decimal(str(row.total_net_amount or 0))  # This is net_amount_try (net)
                commission_tl = Decimal(str(row.total_commission or 0))
                
                total_transactions += count
                
                # Add to TL totals (use gross for gross_totals, net for net_totals)
                gross_totals[payment_method]['TL'] += amount_tl
                net_totals[payment_method]['TL'] += net_amount_tl
                gross_totals[payment_method]['count'] += count
                net_totals[payment_method]['count'] += count
                
                commission_totals[payment_method]['TL'] += commission_tl
                
                # Categorize as deposit or withdrawal (use gross amount - amount_try)
                if row.category == 'DEP':
                    deposit_totals[payment_method]['TL'] += amount_tl
                elif row.category == 'WD':
                    # WD transactions: amount_try is already negative, but we want positive withdrawal amount
                    withdrawal_totals[payment_method]['TL'] += amount_tl
    
    # Process transactions WITHOUT TRY amounts (convert on the fly)
    for txn in query_without_try:
        payment_method = normalize_payment_method(txn.payment_method)
        currency = (txn.currency or 'TL').upper()
        
        # CRITICAL: Tether transactions should remain in USD (company's internal KASA)
        # Other USD transactions should be converted to TL
        if payment_method == 'TETHER' and currency == 'USD':
            # Tether stays in USD - don't convert
            amount_usd = Decimal(str(abs(txn.amount or 0)))
            net_amount_usd = Decimal(str(abs(txn.net_amount or 0)))
            commission_usd = Decimal(str(abs(txn.commission or 0)))
            
            total_transactions += 1
            
            # Add to USD totals for Tether
            gross_totals[payment_method]['USD'] += amount_usd
            net_totals[payment_method]['USD'] += net_amount_usd
            gross_totals[payment_method]['count'] += 1
            net_totals[payment_method]['count'] += 1
            
            commission_totals[payment_method]['USD'] += commission_usd
            
            # Categorize as deposit or withdrawal (in USD for Tether)
            if txn.category == 'DEP':
                deposit_totals[payment_method]['USD'] += amount_usd
            elif txn.category == 'WD':
                withdrawal_totals[payment_method]['USD'] += amount_usd
        else:
            # Convert to TL based on currency for non-Tether transactions
            if currency == 'USD':
                amount_tl = Decimal(str(abs(txn.amount or 0))) * Decimal(str(exchange_rate))
                net_amount_tl = Decimal(str(abs(txn.net_amount or 0))) * Decimal(str(exchange_rate))
                commission_tl = Decimal(str(abs(txn.commission or 0))) * Decimal(str(exchange_rate))
            elif currency == 'EUR':
                amount_tl = Decimal(str(abs(txn.amount or 0))) * Decimal(str(eur_rate))
                net_amount_tl = Decimal(str(abs(txn.net_amount or 0))) * Decimal(str(eur_rate))
                commission_tl = Decimal(str(abs(txn.commission or 0))) * Decimal(str(eur_rate))
            else:
                # Assume TL
                amount_tl = Decimal(str(abs(txn.amount or 0)))
                net_amount_tl = Decimal(str(abs(txn.net_amount or 0)))
                commission_tl = Decimal(str(abs(txn.commission or 0)))
            
            total_transactions += 1
            
            # Add to TL totals
            gross_totals[payment_method]['TL'] += amount_tl
            net_totals[payment_method]['TL'] += net_amount_tl
            gross_totals[payment_method]['count'] += 1
            net_totals[payment_method]['count'] += 1
            
            commission_totals[payment_method]['TL'] += commission_tl
            
            # Categorize as deposit or withdrawal
            if txn.category == 'DEP':
                deposit_totals[payment_method]['TL'] += amount_tl
            elif txn.category == 'WD':
                withdrawal_totals[payment_method]['TL'] += amount_tl
    
    logger.debug(f"Financial metrics calculated: {total_transactions} total transactions (with TRY: {len(query_with_try)}, without TRY: {len(query_without_try)})")
    
    return {
        'gross_amounts': gross_totals,
        'net_amounts': net_totals,
        'commissions': commission_totals,
        'deposits': deposit_totals,
        'withdrawals': withdrawal_totals,
        'total_transactions': total_transactions
    }

def calculate_financial_metrics_with_daily_conversion(start_date, end_date):
    """Calculate financial metrics - using simplified approach for performance"""
    logger.info(f"Calculating financial metrics (simplified) for {start_date} to {end_date}")
    
    # Use the simple aggregate function to avoid timeouts
    result = calculate_financial_metrics(start_date, end_date)
    
    # For daily_converted_usd, use a simple calculation with current rate
    # CRITICAL FIX: Use config.ExchangeRate (has usd_to_tl field)
    try:
        latest_rate = ExchangeRate.query.order_by(ExchangeRate.date.desc()).first()
        rate = float(latest_rate.usd_to_tl) if latest_rate and latest_rate.usd_to_tl else 48.0
    except:
        rate = 48.0
    
    # Calculate simple daily converted USD
    bank_usd = result['net_amounts']['BANK']['USD']
    bank_tl = result['net_amounts']['BANK']['TL']
    cc_usd = result['net_amounts']['CC']['USD']
    cc_tl = result['net_amounts']['CC']['TL']
    tether_usd = result['net_amounts']['TETHER']['USD']
    
    daily_converted_usd = bank_usd + (bank_tl / Decimal(str(rate))) + cc_usd + (cc_tl / Decimal(str(rate))) + tether_usd
    
    result['daily_converted_usd'] = daily_converted_usd
    return result

@financial_performance_bp.route('/financial-performance', methods=['GET'])
@limiter.limit("20 per minute, 200 per hour")  # Dashboard endpoint - moderate frequency
@login_required  # Add login requirement for security
def get_financial_performance():
    """Get financial performance data for dashboard - optimized with caching"""
    start_time = time.time()
    try:
        # Get time range and view type from query parameters
        time_range = request.args.get('range', '30d')
        view_type = request.args.get('view', 'net')  # 'gross' or 'net'
        
        # Check cache first
        cache_key = f"financial_performance_{time_range}"
        current_time = time.time()
        
        if cache_key in _financial_performance_cache:
            cached_data, timestamp = _financial_performance_cache[cache_key]
            if current_time - timestamp < _cache_duration:
                logger.debug(f"Returning cached financial performance data for {time_range}")
                return jsonify(cached_data)
        
        # Calculate date range
        end_date = date.today()
        
        if time_range == 'daily':
            start_date = end_date
        elif time_range == '7d':
            start_date = end_date - timedelta(days=7)
        elif time_range == '30d':
            start_date = end_date - timedelta(days=30)
        elif time_range == '90d':
            start_date = end_date - timedelta(days=90)
        elif time_range == 'monthly':
            start_date = end_date.replace(day=1)
        elif time_range == 'annual':
            start_date = end_date.replace(month=1, day=1)
        else:  # 'all'
            # Get actual data range from database for 'all'
            latest_transaction = Transaction.query.order_by(Transaction.date.desc()).first()
            earliest_transaction = Transaction.query.order_by(Transaction.date.asc()).first()
            
            if latest_transaction and earliest_transaction:
                # Use the actual range of data in database
                start_date = earliest_transaction.date
                end_date = latest_transaction.date  # Update end_date to use last transaction date
            else:
                # Fallback to 90 days if no data
                start_date = end_date - timedelta(days=90)
        
        # Get historical exchange rates for accurate calculations
        # CRITICAL FIX: Use config.ExchangeRate (has usd_to_tl field)
        try:
            # Get current rate for fallback
            latest_rate = ExchangeRate.query.order_by(ExchangeRate.date.desc()).first()
            current_exchange_rate = float(latest_rate.usd_to_tl) if latest_rate and latest_rate.usd_to_tl else 48.0
        except Exception:
            current_exchange_rate = 48.0
        
        # Calculate different time periods
        # Get the actual data range from the database
        latest_transaction = Transaction.query.order_by(Transaction.date.desc()).first()
        earliest_transaction = Transaction.query.order_by(Transaction.date.asc()).first()
        
        if latest_transaction and earliest_transaction:
            data_end_date = latest_transaction.date
            data_start_date = earliest_transaction.date
        else:
            # Fallback to today if no data
            data_end_date = date.today()
            data_start_date = date.today()
        
        # Daily metrics (last available day with transactions) - use simple calculation
        # Use the last transaction date, not necessarily today
        daily_end = data_end_date
        daily_start = daily_end
        logger.info(f"Daily metrics date range: {daily_start} to {daily_end}")
        daily_metrics = calculate_financial_metrics(daily_start, daily_end)
        
        # Monthly metrics (last available month with transactions) - use simple calculation for performance
        # Use the month of the last transaction, not necessarily this month
        monthly_end = data_end_date
        monthly_start = monthly_end.replace(day=1)
        logger.info(f"Monthly metrics date range: {monthly_start} to {monthly_end}")
        monthly_metrics = calculate_financial_metrics(monthly_start, monthly_end)
        
        # Annual metrics (year of last transaction with available data) - use simple calculation for performance
        # Use the year of the last transaction, not necessarily this year
        annual_end = data_end_date
        annual_start = annual_end.replace(month=1, day=1)
        logger.info(f"Annual metrics date range: {annual_start} to {annual_end}")
        annual_metrics = calculate_financial_metrics(annual_start, annual_end)
        
        # Get historical exchange rates for accurate Conv calculations
        try:
            # Daily rate (for the last transaction day)
            daily_rate = historical_exchange_service.get_daily_rate(daily_end)
            logger.info(f"Using daily rate for {daily_end}: {daily_rate}")
            
            # Monthly average rate (for the month with the last transaction)
            monthly_rate = historical_exchange_service.get_monthly_average_rate(
                monthly_end.year, monthly_end.month
            )
            logger.info(f"Using monthly average rate for {monthly_end.year}-{monthly_end.month:02d}: {monthly_rate}")
            
            # Annual average rate (for the year with the last transaction)
            annual_rate = historical_exchange_service.get_monthly_average_rate(
                annual_end.year, 1  # January average as proxy for annual
            )
            logger.info(f"Using annual rate for {annual_end.year}: {annual_rate}")
            
        except Exception as e:
            logger.error(f"Error fetching historical rates: {e}")
            # Fallback to current rate
            daily_rate = monthly_rate = annual_rate = current_exchange_rate
        
        # Calculate Conv (Conversion) totals - Total revenue in USD
        def calculate_conv_total(metrics, rate):
            """Calculate total revenue in USD by converting TL amounts to USD"""
            # Use amounts based on view type for Conv calculation
            amounts_key = 'gross_amounts' if view_type == 'gross' else 'net_amounts'
            amounts = metrics[amounts_key]
            bank_usd = float(amounts['BANK']['USD'])
            bank_tl_to_usd = float(amounts['BANK']['TL']) / rate
            cc_usd = float(amounts['CC']['USD'])
            cc_tl_to_usd = float(amounts['CC']['TL']) / rate
            tether_usd = float(amounts['TETHER']['USD'])
            
            total_usd = bank_usd + bank_tl_to_usd + cc_usd + cc_tl_to_usd + tether_usd
            logger.debug(f"Conv calculation ({view_type}): Bank USD={bank_usd}, Bank TL->USD={bank_tl_to_usd}, CC USD={cc_usd}, CC TL->USD={cc_tl_to_usd}, Tether USD={tether_usd}, Total={total_usd}")
            return total_usd
        
        # Calculate Conv totals for each period
        # Daily: use simple calculation with single rate
        daily_conv_usd = calculate_conv_total(daily_metrics, daily_rate)
        
        # Monthly and Annual: calculate based on view type (more accurate)
        monthly_conv_usd = calculate_conv_total(monthly_metrics, monthly_rate)
        annual_conv_usd = calculate_conv_total(annual_metrics, annual_rate)
        
        logger.debug(f"Conv calculations - Daily: {daily_conv_usd}, Monthly: {monthly_conv_usd}, Annual: {annual_conv_usd}")
        
        # Helper function to format period data
        def format_period_data(metrics, conv_usd):
            # Choose amounts based on view type
            amounts_key = 'gross_amounts' if view_type == 'gross' else 'net_amounts'
            amounts = metrics[amounts_key]
            
            return {
                'total_bank_usd': float(amounts['BANK']['USD']),
                'total_bank_tl': float(amounts['BANK']['TL']),
                'total_cc_usd': float(amounts['CC']['USD']),
                'total_cc_tl': float(amounts['CC']['TL']),
                'total_tether_usd': float(amounts['TETHER']['USD']),
                'total_tether_tl': float(amounts['TETHER']['TL']),
                'conv_usd': conv_usd,
                'conv_tl': 0.0,   # Conv is always in USD
                'total_transactions': metrics['total_transactions'],
                'bank_count': amounts['BANK']['count'],
                'cc_count': amounts['CC']['count'],
                'tether_count': amounts['TETHER']['count'],
                # Deposit totals
                'total_deposits_usd': float(metrics['deposits']['BANK']['USD'] + metrics['deposits']['CC']['USD'] + metrics['deposits']['TETHER']['USD']),
                'total_deposits_tl': float(metrics['deposits']['BANK']['TL'] + metrics['deposits']['CC']['TL'] + metrics['deposits']['TETHER']['TL']),
                # Withdrawal totals
                'total_withdrawals_usd': float(metrics['withdrawals']['BANK']['USD'] + metrics['withdrawals']['CC']['USD'] + metrics['withdrawals']['TETHER']['USD']),
                'total_withdrawals_tl': float(metrics['withdrawals']['BANK']['TL'] + metrics['withdrawals']['CC']['TL'] + metrics['withdrawals']['TETHER']['TL']),
                # Net cash (deposits - withdrawals)
                'net_cash_usd': float(metrics['deposits']['BANK']['USD'] + metrics['deposits']['CC']['USD'] + metrics['deposits']['TETHER']['USD']) - float(metrics['withdrawals']['BANK']['USD'] + metrics['withdrawals']['CC']['USD'] + metrics['withdrawals']['TETHER']['USD']),
                'net_cash_tl': float(metrics['deposits']['BANK']['TL'] + metrics['deposits']['CC']['TL'] + metrics['deposits']['TETHER']['TL']) - float(metrics['withdrawals']['BANK']['TL'] + metrics['withdrawals']['CC']['TL'] + metrics['withdrawals']['TETHER']['TL']),
                # Commission totals (always shown)
                'commission_bank_usd': float(metrics['commissions']['BANK']['USD']),
                'commission_bank_tl': float(metrics['commissions']['BANK']['TL']),
                'commission_cc_usd': float(metrics['commissions']['CC']['USD']),
                'commission_cc_tl': float(metrics['commissions']['CC']['TL']),
                'commission_tether_usd': float(metrics['commissions']['TETHER']['USD']),
                'commission_tether_tl': float(metrics['commissions']['TETHER']['TL']),
                'total_commission_usd': float(metrics['commissions']['BANK']['USD'] + metrics['commissions']['CC']['USD'] + metrics['commissions']['TETHER']['USD']),
                'total_commission_tl': float(metrics['commissions']['BANK']['TL'] + metrics['commissions']['CC']['TL'] + metrics['commissions']['TETHER']['TL'])
            }
        
        # Format response
        response_data = {
            'success': True,
            'data': {
                'daily': format_period_data(daily_metrics, daily_conv_usd),
                'monthly': format_period_data(monthly_metrics, monthly_conv_usd),
                'annual': format_period_data(annual_metrics, annual_conv_usd),
                'exchange_rate': current_exchange_rate,
                'historical_rates': {
                    'daily_rate': daily_rate,
                    'monthly_rate': monthly_rate,
                    'annual_rate': annual_rate
                },
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'range': time_range,
                    'view_type': view_type
                }
            }
        }
        
        elapsed_time = time.time() - start_time
        logger.info(f"Financial performance data retrieved for range {time_range}: Daily={daily_metrics.get('total_transactions', 0)}, Monthly={monthly_metrics.get('total_transactions', 0)}, Annual={annual_metrics.get('total_transactions', 0)} transactions (took {elapsed_time:.2f}s)")
        
        # Cache the response
        _financial_performance_cache[cache_key] = (response_data, current_time)
        
        return jsonify(response_data)
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Error retrieving financial performance data after {elapsed_time:.2f}s: {str(e)}", exc_info=True)
        # Return partial error response - don't expose full error in production
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve financial performance data',
            'message': str(e) if current_app.config.get('DEBUG') else 'Internal server error'
        }), 500

@financial_performance_bp.route('/financial-performance/daily', methods=['GET'])
def get_daily_financial_performance():
    """Get daily financial performance data for a specific date"""
    try:
        # Get date from query parameters
        date_str = request.args.get('date')
        
        if date_str:
            # Parse the specific date
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid date format. Use YYYY-MM-DD'
                }), 400
        else:
            # Default to today
            target_date = date.today()
        
        logger.info(f"Daily endpoint called for {target_date}")
        
        # Calculate metrics for the specific date
        metrics = calculate_financial_metrics(target_date, target_date)
        
        logger.info(f"Daily metrics calculated: Bank TL={metrics['net_amounts']['BANK']['TL']}, CC TL={metrics['net_amounts']['CC']['TL']}, Tether USD={metrics['net_amounts']['TETHER']['USD']}")
        
        # Get historical exchange rate for the specific date
        try:
            exchange_rate = historical_exchange_service.get_daily_rate(target_date)
            logger.debug(f"Using historical rate for {target_date}: {exchange_rate}")
        except Exception as e:
            logger.error(f"Error fetching historical rate for {target_date}: {e}")
            # Fallback to current rate
            # CRITICAL FIX: Use config.ExchangeRate (has usd_to_tl field)
            try:
                latest_rate = ExchangeRate.query.order_by(ExchangeRate.date.desc()).first()
                exchange_rate = float(latest_rate.usd_to_tl) if latest_rate and latest_rate.usd_to_tl else 48.0
            except Exception:
                exchange_rate = 48.0
        
        # Calculate Conv total
        def calculate_conv_total(metrics, rate):
            """Calculate total revenue in USD by converting TL amounts to USD"""
            # Use net amounts for Conv calculation (after commission)
            amounts = metrics['net_amounts']
            bank_usd = float(amounts['BANK']['USD'])
            bank_tl_to_usd = float(amounts['BANK']['TL']) / rate
            cc_usd = float(amounts['CC']['USD'])
            cc_tl_to_usd = float(amounts['CC']['TL']) / rate
            tether_usd = float(amounts['TETHER']['USD'])
            
            total_usd = bank_usd + bank_tl_to_usd + cc_usd + cc_tl_to_usd + tether_usd
            return total_usd
        
        conv_usd = calculate_conv_total(metrics, exchange_rate)
        
        # Format response - use net amounts by default for daily endpoint
        net_amounts = metrics['net_amounts']
        response_data = {
            'success': True,
            'data': {
                'total_bank_usd': float(net_amounts['BANK']['USD']),
                'total_bank_tl': float(net_amounts['BANK']['TL']),
                'total_cc_usd': float(net_amounts['CC']['USD']),
                'total_cc_tl': float(net_amounts['CC']['TL']),
                'total_tether_usd': float(net_amounts['TETHER']['USD']),
                'total_tether_tl': float(net_amounts['TETHER']['TL']),
                'conv_usd': conv_usd,
                'conv_tl': 0.0,
                'total_transactions': metrics['total_transactions'],
                'bank_count': net_amounts['BANK']['count'],
                'cc_count': net_amounts['CC']['count'],
                'tether_count': net_amounts['TETHER']['count'],
                # Deposit totals
                'total_deposits_usd': float(metrics['deposits']['BANK']['USD'] + metrics['deposits']['CC']['USD'] + metrics['deposits']['TETHER']['USD']),
                'total_deposits_tl': float(metrics['deposits']['BANK']['TL'] + metrics['deposits']['CC']['TL'] + metrics['deposits']['TETHER']['TL']),
                # Withdrawal totals
                'total_withdrawals_usd': float(metrics['withdrawals']['BANK']['USD'] + metrics['withdrawals']['CC']['USD'] + metrics['withdrawals']['TETHER']['USD']),
                'total_withdrawals_tl': float(metrics['withdrawals']['BANK']['TL'] + metrics['withdrawals']['CC']['TL'] + metrics['withdrawals']['TETHER']['TL']),
                # Net cash (deposits - withdrawals)
                'net_cash_usd': float(metrics['deposits']['BANK']['USD'] + metrics['deposits']['CC']['USD'] + metrics['deposits']['TETHER']['USD']) - float(metrics['withdrawals']['BANK']['USD'] + metrics['withdrawals']['CC']['USD'] + metrics['withdrawals']['TETHER']['USD']),
                'net_cash_tl': float(metrics['deposits']['BANK']['TL'] + metrics['deposits']['CC']['TL'] + metrics['deposits']['TETHER']['TL']) - float(metrics['withdrawals']['BANK']['TL'] + metrics['withdrawals']['CC']['TL'] + metrics['withdrawals']['TETHER']['TL']),
                'exchange_rate': exchange_rate,
                'period': {
                    'date': target_date.isoformat(),
                    'year': target_date.year,
                    'month': target_date.month,
                    'day': target_date.day
                }
            }
        }
        
        logger.info(f"Daily financial performance data retrieved for {target_date}: {metrics['total_transactions']} transactions")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error retrieving daily financial performance data: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve daily financial performance data',
            'message': str(e)
        }), 500

# Removed duplicate route - using the one with year/month parameters below

@financial_performance_bp.route('/financial-performance/annual', methods=['GET'])
def get_annual_financial_performance():
    """Get annual financial performance data"""
    return get_financial_performance_with_range('annual')

def get_financial_performance_with_range(time_range):
    """Helper function to get financial performance for specific range"""
    try:
        # Calculate date range
        end_date = date.today()
        
        if time_range == 'daily':
            start_date = end_date
        elif time_range == 'monthly':
            start_date = end_date.replace(day=1)
        elif time_range == 'annual':
            start_date = end_date.replace(month=1, day=1)
        else:
            start_date = end_date - timedelta(days=30)
        
        # Calculate metrics
        metrics = calculate_financial_metrics(start_date, end_date)
        
        # Get current exchange rate
        # CRITICAL FIX: Use config.ExchangeRate (has usd_to_tl field)
        try:
            latest_rate = ExchangeRate.query.order_by(ExchangeRate.date.desc()).first()
            exchange_rate = float(latest_rate.usd_to_tl) if latest_rate and latest_rate.usd_to_tl else 48.0
        except Exception:
            exchange_rate = 48.0
        
        # Format response
        response_data = {
            'success': True,
            'data': {
                'total_bank_usd': float(metrics['net_amounts']['BANK']['USD']),
                'total_bank_tl': float(metrics['net_amounts']['BANK']['TL']),
                'total_cc_usd': float(metrics['net_amounts']['CC']['USD']),
                'total_cc_tl': float(metrics['net_amounts']['CC']['TL']),
                'total_tether_usd': float(metrics['net_amounts']['TETHER']['USD']),
                'total_tether_tl': float(metrics['net_amounts']['TETHER']['TL']),
                'conv_usd': 0.0,
                'conv_tl': 0.0,
                'total_transactions': metrics['total_transactions'],
                'bank_count': metrics['net_amounts']['BANK']['count'],
                'cc_count': metrics['net_amounts']['CC']['count'],
                'tether_count': metrics['net_amounts']['TETHER']['count'],
                'exchange_rate': exchange_rate,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'range': time_range
                }
            }
        }
        
        logger.info(f"{time_range.capitalize()} financial performance data retrieved: {metrics['total_transactions']} transactions")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error retrieving {time_range} financial performance data: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve {time_range} financial performance data',
            'message': str(e)
        }), 500

@financial_performance_bp.route('/financial-performance/monthly', methods=['GET'])
def get_monthly_financial_performance_by_date():
    """Get monthly financial performance data for a specific month"""
    try:
        # Get year, month, and view parameters from query parameters
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        view_type = request.args.get('view', default='net', type=str)
        
        if not year or not month:
            return jsonify({
                'success': False,
                'error': 'Year and month parameters are required'
            }), 400
        
        # Validate month
        if month < 1 or month > 12:
            return jsonify({
                'success': False,
                'error': 'Month must be between 1 and 12'
            }), 400
        
        # Calculate date range for the specific month
        start_date = date(year, month, 1)
        
        # Get last day of the month
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        logger.info(f"Monthly endpoint called for {year}-{month:02d}: {start_date} to {end_date}")
        
        # Calculate metrics for the specific month using daily conversion
        metrics = calculate_financial_metrics_with_daily_conversion(start_date, end_date)
        
        logger.info(f"Monthly metrics calculated: Bank TL={metrics['net_amounts']['BANK']['TL']}, CC TL={metrics['net_amounts']['CC']['TL']}, Tether USD={metrics['net_amounts']['TETHER']['USD']}")
        
        # Calculate Conv based on view type
        amounts_for_conv = metrics['gross_amounts'] if view_type == 'gross' else metrics['net_amounts']
        # Use historical exchange rate service to get average rate for the month
        try:
            monthly_rate = historical_exchange_service.get_monthly_average_rate(year, month)
        except Exception:
            monthly_rate = 48.0
        
        conv_usd = float(amounts_for_conv['BANK']['USD']) + float(amounts_for_conv['BANK']['TL']) / monthly_rate + \
                   float(amounts_for_conv['CC']['USD']) + float(amounts_for_conv['CC']['TL']) / monthly_rate + \
                   float(amounts_for_conv['TETHER']['USD'])
        logger.info(f"Monthly Conv using view_type {view_type}: {conv_usd} USD")
        
        # Format response - use amounts based on view type
        amounts_key = 'gross_amounts' if view_type == 'gross' else 'net_amounts'
        amounts = metrics[amounts_key]
        response_data = {
            'success': True,
            'data': {
                'total_bank_usd': float(amounts['BANK']['USD']),
                'total_bank_tl': float(amounts['BANK']['TL']),
                'total_cc_usd': float(amounts['CC']['USD']),
                'total_cc_tl': float(amounts['CC']['TL']),
                'total_tether_usd': float(amounts['TETHER']['USD']),
                'total_tether_tl': float(amounts['TETHER']['TL']),
                'conv_usd': conv_usd,
                'conv_tl': 0.0,
                'total_transactions': metrics['total_transactions'],
                'bank_count': amounts['BANK']['count'],
                'cc_count': amounts['CC']['count'],
                'tether_count': amounts['TETHER']['count'],
                # Deposit totals
                'total_deposits_usd': float(metrics['deposits']['BANK']['USD'] + metrics['deposits']['CC']['USD'] + metrics['deposits']['TETHER']['USD']),
                'total_deposits_tl': float(metrics['deposits']['BANK']['TL'] + metrics['deposits']['CC']['TL'] + metrics['deposits']['TETHER']['TL']),
                # Withdrawal totals
                'total_withdrawals_usd': float(metrics['withdrawals']['BANK']['USD'] + metrics['withdrawals']['CC']['USD'] + metrics['withdrawals']['TETHER']['USD']),
                'total_withdrawals_tl': float(metrics['withdrawals']['BANK']['TL'] + metrics['withdrawals']['CC']['TL'] + metrics['withdrawals']['TETHER']['TL']),
                # Net cash (deposits - withdrawals)
                'net_cash_usd': float(metrics['deposits']['BANK']['USD'] + metrics['deposits']['CC']['USD'] + metrics['deposits']['TETHER']['USD']) - float(metrics['withdrawals']['BANK']['USD'] + metrics['withdrawals']['CC']['USD'] + metrics['withdrawals']['TETHER']['USD']),
                'net_cash_tl': float(metrics['deposits']['BANK']['TL'] + metrics['deposits']['CC']['TL'] + metrics['deposits']['TETHER']['TL']) - float(metrics['withdrawals']['BANK']['TL'] + metrics['withdrawals']['CC']['TL'] + metrics['withdrawals']['TETHER']['TL']),
                'exchange_rate': 0.0,  # Not used with daily conversion
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'year': year,
                    'month': month
                }
            }
        }
        
        logger.info(f"Monthly financial performance data retrieved for {year}-{month:02d}: {metrics['total_transactions']} transactions")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error retrieving monthly financial performance data: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve monthly financial performance data',
            'message': str(e)
        }), 500
