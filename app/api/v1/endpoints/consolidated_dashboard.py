"""
Consolidated Dashboard API endpoint
Returns all dashboard data in a single optimized request
"""
from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from app import db, limiter
from app.models.transaction import Transaction
from app.models.financial import PspTrack
from sqlalchemy import func, and_, case
from datetime import datetime, timedelta
import logging
from app.services.enhanced_cache_service import cache_service
from app.utils.unified_logger import get_logger, PerformanceLogger
from app.utils.api_response import make_response

logger = logging.getLogger(__name__)
api_logger = get_logger('app.api.consolidated_dashboard')

consolidated_dashboard_api = Blueprint('consolidated_dashboard_api', __name__)

def normalize_payment_method(payment_method):
    """Normalize payment method to standard categories - consistent with financial_performance.py"""
    if not payment_method:
        return 'OTHER'
    
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
    
    # Tether variations
    if any(keyword in pm_lower for keyword in ['tether', 'usdt', 'crypto', 'kasa']):
        return 'TETHER'
    
    return 'OTHER'

# Temporarily disable CSRF protection
import os
from app import csrf
# Exempt CSRF only in non-production environments
if os.environ.get('FLASK_ENV') != 'production':
    csrf.exempt(consolidated_dashboard_api)

@consolidated_dashboard_api.route("/dashboard/consolidated")
# @login_required  # Temporarily disabled for debugging
@limiter.limit("15 per minute, 300 per hour")  # Dashboard endpoint - frequently accessed
def get_consolidated_dashboard():
    """Get all dashboard data in a single optimized request"""
    import time as time_module
    query_start_time = time_module.time()
    
    try:
        # Reduced logging verbosity - only log in debug mode or for errors
        time_range = request.args.get('range', 'all')
        now = datetime.now()  # Define now at the start for use throughout the function
        
        # CRITICAL FIX: Check cache but allow bypass with query parameter
        bypass_cache = request.args.get('_t') is not None  # Cache buster query parameter
        user_id = current_user.id if current_user.is_authenticated else 'anonymous'
        cache_key = f"consolidated_dashboard:{user_id}:{time_range}"
        
        if not bypass_cache:
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Returning cached consolidated dashboard for user {user_id}")
                # Return legacy raw JSON shape for frontend compatibility
                return jsonify(cached_result), 200
        
        # Build date filter based on time range
        date_filter = None
        chart_limit_days = 135  # Default for 'all'
        
        if time_range != 'all':
            if time_range == '7d':
                date_filter = now - timedelta(days=7)
                chart_limit_days = 7
            elif time_range == '30d':
                date_filter = now - timedelta(days=30)
                chart_limit_days = 30
            elif time_range == '90d':
                date_filter = now - timedelta(days=90)
                chart_limit_days = 90
            elif time_range == '6m':
                date_filter = now - timedelta(days=180)
                chart_limit_days = 180
            elif time_range == '1y':
                date_filter = now - timedelta(days=365)
                chart_limit_days = 365
        
        # Build base query with date filter
        # CRITICAL FIX: Use Transaction.date (transaction date) not created_at (record creation date)
        base_query = db.session.query(Transaction)
        if date_filter:
            base_query = base_query.filter(Transaction.date >= date_filter.date() if hasattr(date_filter, 'date') else date_filter)
        
        # CRITICAL FIX: Get current exchange rate FIRST before any calculations
        # This prevents currency mixing bugs
        from app.models.config import ExchangeRate
        exchange_rate_cache_key = "latest_exchange_rate"
        cached_rate = cache_service.get(exchange_rate_cache_key)
        
        if cached_rate:
            exchange_rate = cached_rate
        else:
            try:
                latest_rate = ExchangeRate.query.order_by(ExchangeRate.date.desc()).first()
                exchange_rate = float(latest_rate.usd_to_tl) if latest_rate and latest_rate.usd_to_tl else 48.0
                # Cache exchange rate for 5 minutes to ensure consistency
                cache_service.set(exchange_rate_cache_key, exchange_rate, 300)
            except:
                exchange_rate = 48.0
                cache_service.set(exchange_rate_cache_key, exchange_rate, 300)
        
        # Query 1: Get basic stats - FIXED to avoid currency mixing
        query_1_start = time_module.time()
        
        # DEBUG: Log that we're using the FIXED calculation
        logger.warning(f"🔧 Using FIXED currency conversion logic (v2.0)")
        
        # For total_revenue and total_commission, we need to handle NULL net_amount_try properly
        # Step 1: Sum all transactions that HAVE net_amount_try (already in TL)
        stats_with_try = base_query.filter(Transaction.net_amount_try.isnot(None)).with_entities(
            func.count(Transaction.id).label('count_with_try'),
            func.sum(Transaction.net_amount_try).label('revenue_with_try'),
            func.sum(func.coalesce(Transaction.commission_try, Transaction.commission)).label('commission_with_try')
        ).first()
        
        # Step 2: Get transactions WITHOUT net_amount_try and convert them
        transactions_without_try = base_query.filter(Transaction.net_amount_try.is_(None)).with_entities(
            Transaction.id,
            Transaction.net_amount,
            Transaction.commission,
            Transaction.currency
        ).all()
        
        # Convert missing TRY amounts using current exchange rate
        revenue_without_try = 0.0
        commission_without_try = 0.0
        count_without_try = len(transactions_without_try)
        
        for txn in transactions_without_try:
            # Convert to TL if needed
            if txn.currency and txn.currency.upper() == 'USD':
                revenue_without_try += float(txn.net_amount or 0) * exchange_rate
                commission_without_try += float(txn.commission or 0) * exchange_rate
            elif txn.currency and txn.currency.upper() == 'EUR':
                # Get EUR rate if available, otherwise estimate from USD rate
                try:
                    latest_rate = ExchangeRate.query.order_by(ExchangeRate.date.desc()).first()
                    eur_rate = float(latest_rate.eur_to_tl) if latest_rate and latest_rate.eur_to_tl else (exchange_rate * 1.08)
                except:
                    eur_rate = exchange_rate * 1.08
                revenue_without_try += float(txn.net_amount or 0) * eur_rate
                commission_without_try += float(txn.commission or 0) * eur_rate
            else:
                # Assume TL if currency is not specified or is TL
                revenue_without_try += float(txn.net_amount or 0)
                commission_without_try += float(txn.commission or 0)
        
        # Combine both parts
        total_transactions = (stats_with_try.count_with_try or 0) + count_without_try
        total_revenue = float(stats_with_try.revenue_with_try or 0) + revenue_without_try
        total_commission = float(stats_with_try.commission_with_try or 0) + commission_without_try
        
        query_1_time = (time_module.time() - query_1_start) * 1000
        logger.debug(f"Stats query: {query_1_time:.2f}ms")
        
        # Calculate actual deposits and withdrawals for accurate net cash - FIXED
        # CRITICAL FIX: Use amount_try (gross amount) not net_amount_try for deposits/withdrawals
        deposits_base = base_query.filter(Transaction.category == 'DEP')
        withdrawals_base = base_query.filter(Transaction.category == 'WD')
        
        # Deposits with amount_try (gross amount in TL)
        deposits_with_try = deposits_base.filter(Transaction.amount_try.isnot(None)).with_entities(
            func.sum(func.abs(Transaction.amount_try))
        ).scalar() or 0
        
        # Deposits without amount_try - convert manually
        deposits_without_try_txns = deposits_base.filter(Transaction.amount_try.is_(None)).with_entities(
            Transaction.amount,
            Transaction.currency
        ).all()
        
        deposits_without_try = 0.0
        for txn in deposits_without_try_txns:
            amount = abs(float(txn.amount or 0))
            if txn.currency and txn.currency.upper() == 'USD':
                deposits_without_try += amount * exchange_rate
            elif txn.currency and txn.currency.upper() == 'EUR':
                try:
                    latest_rate = ExchangeRate.query.order_by(ExchangeRate.date.desc()).first()
                    eur_rate = float(latest_rate.eur_to_tl) if latest_rate and latest_rate.eur_to_tl else (exchange_rate * 1.08)
                except:
                    eur_rate = exchange_rate * 1.08
                deposits_without_try += amount * eur_rate
            else:
                deposits_without_try += amount
        
        total_deposits = float(deposits_with_try) + deposits_without_try
        
        # Withdrawals with amount_try (gross amount in TL, withdrawals are negative so use abs)
        withdrawals_with_try = withdrawals_base.filter(Transaction.amount_try.isnot(None)).with_entities(
            func.sum(func.abs(Transaction.amount_try))
        ).scalar() or 0
        
        # Withdrawals without amount_try - convert manually
        withdrawals_without_try_txns = withdrawals_base.filter(Transaction.amount_try.is_(None)).with_entities(
            Transaction.amount,
            Transaction.currency
        ).all()
        
        withdrawals_without_try = 0.0
        for txn in withdrawals_without_try_txns:
            # WD transactions have negative amounts, so use abs to get positive withdrawal amount
            amount = abs(float(txn.amount or 0))
            if txn.currency and txn.currency.upper() == 'USD':
                withdrawals_without_try += amount * exchange_rate
            elif txn.currency and txn.currency.upper() == 'EUR':
                try:
                    latest_rate = ExchangeRate.query.order_by(ExchangeRate.date.desc()).first()
                    eur_rate = float(latest_rate.eur_to_tl) if latest_rate and latest_rate.eur_to_tl else (exchange_rate * 1.08)
                except:
                    eur_rate = exchange_rate * 1.08
                withdrawals_without_try += amount * eur_rate
            else:
                withdrawals_without_try += amount
        
        total_withdrawals = float(withdrawals_with_try) + withdrawals_without_try
        
        # Net cash is deposits - withdrawals (both now properly converted to TL)
        net_cash_tl = total_deposits - total_withdrawals
        
        # Calculate USD equivalent using the exchange rate we fetched earlier
        annual_net_cash_usd = net_cash_tl / exchange_rate if exchange_rate > 0 else 0
        
        # Calculate USD equivalents for deposits and withdrawals separately
        total_deposits_usd = total_deposits / exchange_rate if exchange_rate > 0 else 0
        total_withdrawals_usd = total_withdrawals / exchange_rate if exchange_rate > 0 else 0
        
        logger.debug(f"Net cash calculation: Deposits={total_deposits}, Withdrawals={total_withdrawals}, Net Cash TL={net_cash_tl}, Net Cash USD={annual_net_cash_usd}, Rate={exchange_rate}")
        
        # CRITICAL FIX: Calculate payment method breakdown for Annual (all time)
        # Get all transactions with payment method information
        # CRITICAL FIX: Also get exchange_rate for Tether transactions
        payment_method_query = base_query.filter(Transaction.payment_method.isnot(None)).with_entities(
            Transaction.payment_method,
            Transaction.amount_try,
            Transaction.amount,
            Transaction.net_amount_try,
            Transaction.net_amount,
            Transaction.currency,
            Transaction.category,
            Transaction.exchange_rate
        ).all()
        
        # Helper function to process transactions and calculate payment method totals
        def calculate_payment_method_totals(transactions):
            bank_tl = 0.0
            bank_usd = 0.0
            bank_count = 0
            cc_tl = 0.0
            cc_usd = 0.0
            cc_count = 0
            tether_tl = 0.0
            tether_usd = 0.0
            tether_count = 0
            deposits_tl = 0.0
            deposits_usd = 0.0
            withdrawals_tl = 0.0
            withdrawals_usd = 0.0
            
            for txn in transactions:
                payment_method = normalize_payment_method(txn.payment_method)
                currency = (txn.currency or 'TL').upper()
                
                # CRITICAL FIX: Tether transactions should always stay in USD, regardless of currency field
                if payment_method == 'TETHER':
                    # Tether stays in USD - prefer original amount (should be in USD), fallback to converting amount_try
                    original_amount = abs(float(txn.amount or 0))
                    
                    if original_amount > 0:
                        # Use original amount (should be in USD for Tether)
                        amount_usd = original_amount
                        if txn.net_amount:
                            net_amount_usd = abs(float(txn.net_amount or 0))
                        else:
                            # Estimate: net = gross - commission
                            txn_rate = float(txn.exchange_rate or exchange_rate) if txn.exchange_rate else exchange_rate
                            commission_usd = abs(float(txn.commission or 0)) / txn_rate if txn_rate > 0 else 0
                            net_amount_usd = amount_usd - commission_usd
                        amount_tl = 0.0  # Tether doesn't use TL
                        net_amount_tl = 0.0
                    elif txn.amount_try is not None:
                        # Convert amount_try back to USD using exchange_rate
                        txn_rate = float(txn.exchange_rate or exchange_rate) if txn.exchange_rate else exchange_rate
                        if txn_rate > 0:
                            amount_usd = abs(float(txn.amount_try or 0)) / txn_rate
                            net_amount_usd = abs(float(txn.net_amount_try or 0)) / txn_rate if txn.net_amount_try is not None else amount_usd
                        else:
                            # Last resort: use current exchange rate
                            amount_usd = abs(float(txn.amount_try or 0)) / exchange_rate if exchange_rate > 0 else 0
                            net_amount_usd = abs(float(txn.net_amount_try or 0)) / exchange_rate if exchange_rate > 0 and txn.net_amount_try else amount_usd
                        amount_tl = 0.0
                        net_amount_tl = 0.0
                    else:
                        # No data available
                        amount_usd = 0.0
                        net_amount_usd = 0.0
                        amount_tl = 0.0
                        net_amount_tl = 0.0
                else:
                    # Non-Tether transactions: determine amounts - prefer amount_try if available
                    if txn.amount_try is not None:
                        amount_tl = float(txn.amount_try or 0)
                        net_amount_tl = float(txn.net_amount_try or 0) if txn.net_amount_try is not None else amount_tl
                        amount_usd = amount_tl / exchange_rate if exchange_rate > 0 else 0
                    else:
                        # Convert based on currency
                        amount = float(txn.amount or 0)
                        net_amount = float(txn.net_amount or 0) if txn.net_amount else amount
                        if currency == 'USD':
                            amount_tl = amount * exchange_rate
                            net_amount_tl = net_amount * exchange_rate
                            amount_usd = amount
                        elif currency == 'EUR':
                            try:
                                latest_rate = ExchangeRate.query.order_by(ExchangeRate.date.desc()).first()
                                eur_rate = float(latest_rate.eur_to_tl) if latest_rate and latest_rate.eur_to_tl else (exchange_rate * 1.08)
                            except:
                                eur_rate = exchange_rate * 1.08
                            amount_tl = amount * eur_rate
                            net_amount_tl = net_amount * eur_rate
                            amount_usd = amount_tl / exchange_rate if exchange_rate > 0 else 0
                        else:
                            amount_tl = amount
                            net_amount_tl = net_amount
                            amount_usd = amount_tl / exchange_rate if exchange_rate > 0 else 0
                
                # Use net_amount for payment method calculations (after commission)
                amount_to_add_tl = abs(net_amount_tl)
                amount_to_add_usd = abs(net_amount_usd) if payment_method == 'TETHER' and currency == 'USD' else abs(amount_usd)
                
                # Use gross amount for deposits/withdrawals
                gross_amount_tl = abs(amount_tl)
                if payment_method == 'TETHER' and currency == 'USD':
                    gross_amount_usd = abs(amount_usd)  # Tether uses USD directly
                else:
                    gross_amount_usd = abs(amount_usd) if currency == 'USD' else (gross_amount_tl / exchange_rate if exchange_rate > 0 else 0)
                
                # Add to appropriate payment method totals
                if payment_method == 'BANK':
                    bank_tl += amount_to_add_tl
                    bank_usd += amount_to_add_usd
                    bank_count += 1
                elif payment_method == 'CC':
                    cc_tl += amount_to_add_tl
                    cc_usd += amount_to_add_usd
                    cc_count += 1
                elif payment_method == 'TETHER':
                    # Tether always uses USD
                    tether_usd += amount_to_add_usd
                    tether_count += 1
                
                # Track deposits and withdrawals
                if txn.category == 'DEP':
                    deposits_tl += gross_amount_tl
                    deposits_usd += gross_amount_usd
                elif txn.category == 'WD':
                    withdrawals_tl += gross_amount_tl
                    withdrawals_usd += gross_amount_usd
            
            # Calculate Conv (conversion) - sum of all payment methods in USD
            conv_usd = bank_usd + cc_usd + tether_usd
            
            return {
                'bank_tl': bank_tl, 'bank_usd': bank_usd, 'bank_count': bank_count,
                'cc_tl': cc_tl, 'cc_usd': cc_usd, 'cc_count': cc_count,
                'tether_tl': tether_tl, 'tether_usd': tether_usd, 'tether_count': tether_count,
                'conv_usd': conv_usd,
                'deposits_tl': deposits_tl, 'deposits_usd': deposits_usd,
                'withdrawals_tl': withdrawals_tl, 'withdrawals_usd': withdrawals_usd,
                'net_cash_tl': deposits_tl - withdrawals_tl,
                'net_cash_usd': deposits_usd - withdrawals_usd
            }
        
        # Calculate Annual totals (all transactions in base_query)
        annual_totals = calculate_payment_method_totals(payment_method_query)
        
        # Update annual totals with calculated deposits/withdrawals (already calculated above)
        annual_totals['deposits_tl'] = total_deposits
        annual_totals['deposits_usd'] = total_deposits_usd
        annual_totals['withdrawals_tl'] = total_withdrawals
        annual_totals['withdrawals_usd'] = total_withdrawals_usd
        annual_totals['net_cash_tl'] = net_cash_tl
        annual_totals['net_cash_usd'] = annual_net_cash_usd
        
        # Calculate Daily totals (today's transactions)
        today = now.date()
        daily_query = db.session.query(Transaction).filter(
            Transaction.date == today,
            Transaction.payment_method.isnot(None)
        ).with_entities(
            Transaction.payment_method,
            Transaction.amount_try,
            Transaction.amount,
            Transaction.net_amount_try,
            Transaction.net_amount,
            Transaction.currency,
            Transaction.category
        ).all()
        daily_totals = calculate_payment_method_totals(daily_query)
        
        # Calculate Monthly totals (this month's transactions)
        month_start = today.replace(day=1)
        monthly_query = db.session.query(Transaction).filter(
            Transaction.date >= month_start,
            Transaction.date <= today,
            Transaction.payment_method.isnot(None)
        ).with_entities(
            Transaction.payment_method,
            Transaction.amount_try,
            Transaction.amount,
            Transaction.net_amount_try,
            Transaction.net_amount,
            Transaction.currency,
            Transaction.category
        ).all()
        monthly_totals = calculate_payment_method_totals(monthly_query)
        
        # CRITICAL FIX: Also calculate daily and monthly deposits/withdrawals separately
        # Daily deposits and withdrawals
        daily_deposits_base = db.session.query(Transaction).filter(
            Transaction.date == today,
            Transaction.category == 'DEP'
        )
        daily_deposits_with_try = daily_deposits_base.filter(Transaction.amount_try.isnot(None)).with_entities(
            func.sum(func.abs(Transaction.amount_try))
        ).scalar() or 0
        daily_deposits_without_try_txns = daily_deposits_base.filter(Transaction.amount_try.is_(None)).with_entities(
            Transaction.amount,
            Transaction.currency
        ).all()
        daily_deposits_without_try = 0.0
        for txn in daily_deposits_without_try_txns:
            amount = abs(float(txn.amount or 0))
            if txn.currency and txn.currency.upper() == 'USD':
                daily_deposits_without_try += amount * exchange_rate
            elif txn.currency and txn.currency.upper() == 'EUR':
                try:
                    latest_rate = ExchangeRate.query.order_by(ExchangeRate.date.desc()).first()
                    eur_rate = float(latest_rate.eur_to_tl) if latest_rate and latest_rate.eur_to_tl else (exchange_rate * 1.08)
                except:
                    eur_rate = exchange_rate * 1.08
                daily_deposits_without_try += amount * eur_rate
            else:
                daily_deposits_without_try += amount
        daily_total_deposits = float(daily_deposits_with_try) + daily_deposits_without_try
        
        daily_withdrawals_base = db.session.query(Transaction).filter(
            Transaction.date == today,
            Transaction.category == 'WD'
        )
        daily_withdrawals_with_try = daily_withdrawals_base.filter(Transaction.amount_try.isnot(None)).with_entities(
            func.sum(func.abs(Transaction.amount_try))
        ).scalar() or 0
        daily_withdrawals_without_try_txns = daily_withdrawals_base.filter(Transaction.amount_try.is_(None)).with_entities(
            Transaction.amount,
            Transaction.currency
        ).all()
        daily_withdrawals_without_try = 0.0
        for txn in daily_withdrawals_without_try_txns:
            amount = abs(float(txn.amount or 0))
            if txn.currency and txn.currency.upper() == 'USD':
                daily_withdrawals_without_try += amount * exchange_rate
            elif txn.currency and txn.currency.upper() == 'EUR':
                try:
                    latest_rate = ExchangeRate.query.order_by(ExchangeRate.date.desc()).first()
                    eur_rate = float(latest_rate.eur_to_tl) if latest_rate and latest_rate.eur_to_tl else (exchange_rate * 1.08)
                except:
                    eur_rate = exchange_rate * 1.08
                daily_withdrawals_without_try += amount * eur_rate
            else:
                daily_withdrawals_without_try += amount
        daily_total_withdrawals = float(daily_withdrawals_with_try) + daily_withdrawals_without_try
        
        # Monthly deposits and withdrawals
        monthly_deposits_base = db.session.query(Transaction).filter(
            Transaction.date >= month_start,
            Transaction.date <= today,
            Transaction.category == 'DEP'
        )
        monthly_deposits_with_try = monthly_deposits_base.filter(Transaction.amount_try.isnot(None)).with_entities(
            func.sum(func.abs(Transaction.amount_try))
        ).scalar() or 0
        monthly_deposits_without_try_txns = monthly_deposits_base.filter(Transaction.amount_try.is_(None)).with_entities(
            Transaction.amount,
            Transaction.currency
        ).all()
        monthly_deposits_without_try = 0.0
        for txn in monthly_deposits_without_try_txns:
            amount = abs(float(txn.amount or 0))
            if txn.currency and txn.currency.upper() == 'USD':
                monthly_deposits_without_try += amount * exchange_rate
            elif txn.currency and txn.currency.upper() == 'EUR':
                try:
                    latest_rate = ExchangeRate.query.order_by(ExchangeRate.date.desc()).first()
                    eur_rate = float(latest_rate.eur_to_tl) if latest_rate and latest_rate.eur_to_tl else (exchange_rate * 1.08)
                except:
                    eur_rate = exchange_rate * 1.08
                monthly_deposits_without_try += amount * eur_rate
            else:
                monthly_deposits_without_try += amount
        monthly_total_deposits = float(monthly_deposits_with_try) + monthly_deposits_without_try
        
        monthly_withdrawals_base = db.session.query(Transaction).filter(
            Transaction.date >= month_start,
            Transaction.date <= today,
            Transaction.category == 'WD'
        )
        monthly_withdrawals_with_try = monthly_withdrawals_base.filter(Transaction.amount_try.isnot(None)).with_entities(
            func.sum(func.abs(Transaction.amount_try))
        ).scalar() or 0
        monthly_withdrawals_without_try_txns = monthly_withdrawals_base.filter(Transaction.amount_try.is_(None)).with_entities(
            Transaction.amount,
            Transaction.currency
        ).all()
        monthly_withdrawals_without_try = 0.0
        for txn in monthly_withdrawals_without_try_txns:
            amount = abs(float(txn.amount or 0))
            if txn.currency and txn.currency.upper() == 'USD':
                monthly_withdrawals_without_try += amount * exchange_rate
            elif txn.currency and txn.currency.upper() == 'EUR':
                try:
                    latest_rate = ExchangeRate.query.order_by(ExchangeRate.date.desc()).first()
                    eur_rate = float(latest_rate.eur_to_tl) if latest_rate and latest_rate.eur_to_tl else (exchange_rate * 1.08)
                except:
                    eur_rate = exchange_rate * 1.08
                monthly_withdrawals_without_try += amount * eur_rate
            else:
                monthly_withdrawals_without_try += amount
        monthly_total_withdrawals = float(monthly_withdrawals_with_try) + monthly_withdrawals_without_try
        
        # Update daily and monthly totals with calculated deposits/withdrawals
        daily_totals['deposits_tl'] = daily_total_deposits
        daily_totals['deposits_usd'] = daily_total_deposits / exchange_rate if exchange_rate > 0 else 0
        daily_totals['withdrawals_tl'] = daily_total_withdrawals
        daily_totals['withdrawals_usd'] = daily_total_withdrawals / exchange_rate if exchange_rate > 0 else 0
        daily_totals['net_cash_tl'] = daily_total_deposits - daily_total_withdrawals
        daily_totals['net_cash_usd'] = (daily_total_deposits - daily_total_withdrawals) / exchange_rate if exchange_rate > 0 else 0
        
        monthly_totals['deposits_tl'] = monthly_total_deposits
        monthly_totals['deposits_usd'] = monthly_total_deposits / exchange_rate if exchange_rate > 0 else 0
        monthly_totals['withdrawals_tl'] = monthly_total_withdrawals
        monthly_totals['withdrawals_usd'] = monthly_total_withdrawals / exchange_rate if exchange_rate > 0 else 0
        monthly_totals['net_cash_tl'] = monthly_total_deposits - monthly_total_withdrawals
        monthly_totals['net_cash_usd'] = (monthly_total_deposits - monthly_total_withdrawals) / exchange_rate if exchange_rate > 0 else 0
        
        logger.debug(f"Annual payment method breakdown: BANK TL={annual_totals['bank_tl']}, CC TL={annual_totals['cc_tl']}, TETHER USD={annual_totals['tether_usd']}")
        logger.debug(f"Daily payment method breakdown: BANK TL={daily_totals['bank_tl']}, CC TL={daily_totals['cc_tl']}, TETHER USD={daily_totals['tether_usd']}")
        logger.debug(f"Monthly payment method breakdown: BANK TL={monthly_totals['bank_tl']}, CC TL={monthly_totals['cc_tl']}, TETHER USD={monthly_totals['tether_usd']}")
        
        # Query 2: Get active clients count separately for better performance
        query_2_start = time_module.time()
        active_clients_count = base_query.with_entities(
            func.count(func.distinct(Transaction.client_name)).label('active_clients')
        ).scalar() or 0
        query_2_time = (time_module.time() - query_2_start) * 1000
        logger.debug(f"Active clients query: {query_2_time:.2f}ms")
        
        # Query 3: PSP summary - FIXED to handle all currencies
        query_3_start = time_module.time()
        
        # Get PSP stats with proper currency handling - include ALL transactions
        psp_transactions = base_query.filter(
            Transaction.psp.isnot(None),
            Transaction.psp != ''
        ).with_entities(
            Transaction.psp,
            Transaction.amount_try,
            Transaction.amount,
            Transaction.currency
        ).all()
        
        # Aggregate PSP stats manually to handle currency conversion
        psp_stats_dict = {}
        for row in psp_transactions:
            psp = row.psp
            if psp not in psp_stats_dict:
                psp_stats_dict[psp] = {'count': 0, 'total_amount': 0.0}
            
            psp_stats_dict[psp]['count'] += 1
            
            if row.amount_try is not None:
                psp_stats_dict[psp]['total_amount'] += float(row.amount_try or 0)
            else:
                amount = float(row.amount or 0)
                if row.currency and row.currency.upper() == 'USD':
                    psp_stats_dict[psp]['total_amount'] += amount * exchange_rate
                elif row.currency and row.currency.upper() == 'EUR':
                    try:
                        latest_rate = ExchangeRate.query.order_by(ExchangeRate.date.desc()).first()
                        eur_rate = float(latest_rate.eur_to_tl) if latest_rate and latest_rate.eur_to_tl else (exchange_rate * 1.08)
                    except:
                        eur_rate = exchange_rate * 1.08
                    psp_stats_dict[psp]['total_amount'] += amount * eur_rate
                else:
                    psp_stats_dict[psp]['total_amount'] += amount
        
        # Convert to list and sort
        from collections import namedtuple
        PSPStat = namedtuple('PSPStat', ['psp', 'transaction_count', 'total_amount'])
        psp_stats = [
            PSPStat(psp=psp, transaction_count=data['count'], total_amount=data['total_amount'])
            for psp, data in sorted(psp_stats_dict.items(), key=lambda x: x[1]['total_amount'], reverse=True)
        ][:10]
        query_3_time = (time_module.time() - query_3_start) * 1000
        logger.debug(f"PSP stats query: {query_3_time:.2f}ms")
        
        # Query 4: Calculate chart date range based on time_range  
        query_4_start = time_module.time()
        if time_range == '7d':
            chart_start_date = now - timedelta(days=7)
        elif time_range == '30d':
            chart_start_date = now - timedelta(days=30)
        elif time_range == '90d':
            chart_start_date = now - timedelta(days=90)
        else:  # 'all' - limit to 135 days for performance
            # Instead of querying earliest transaction (slow), use fixed limit
            chart_start_date = now - timedelta(days=min(chart_limit_days, 135))
        
        # Get daily net cash data - CRITICAL FIX: Use deposits - withdrawals, not net_amount_try
        # Net cash = deposits - withdrawals (cash flow), not revenue
        chart_date_filter = chart_start_date.date() if hasattr(chart_start_date, 'date') else chart_start_date
        
        # Get daily deposits
        daily_deposits_query = base_query.filter(
            Transaction.date >= chart_date_filter,
            Transaction.category == 'DEP'
        ).with_entities(
            Transaction.date.label('date'),
            Transaction.amount_try,
            Transaction.amount,
            Transaction.currency
        ).order_by(Transaction.date).all()
        
        # Get daily withdrawals
        daily_withdrawals_query = base_query.filter(
            Transaction.date >= chart_date_filter,
            Transaction.category == 'WD'
        ).with_entities(
            Transaction.date.label('date'),
            Transaction.amount_try,
            Transaction.amount,
            Transaction.currency
        ).order_by(Transaction.date).all()
        
        # Process deposits by date
        daily_deposits_dict = {}
        for row in daily_deposits_query:
            date_str = row.date.strftime('%Y-%m-%d') if hasattr(row.date, 'strftime') else str(row.date)
            if row.amount_try is not None:
                deposit_value = abs(float(row.amount_try or 0))
            else:
                amount = abs(float(row.amount or 0))
                if row.currency and row.currency.upper() == 'USD':
                    deposit_value = amount * exchange_rate
                elif row.currency and row.currency.upper() == 'EUR':
                    try:
                        latest_rate = ExchangeRate.query.order_by(ExchangeRate.date.desc()).first()
                        eur_rate = float(latest_rate.eur_to_tl) if latest_rate and latest_rate.eur_to_tl else (exchange_rate * 1.08)
                    except:
                        eur_rate = exchange_rate * 1.08
                    deposit_value = amount * eur_rate
                else:
                    deposit_value = amount
            daily_deposits_dict[date_str] = daily_deposits_dict.get(date_str, 0) + deposit_value
        
        # Process withdrawals by date
        daily_withdrawals_dict = {}
        for row in daily_withdrawals_query:
            date_str = row.date.strftime('%Y-%m-%d') if hasattr(row.date, 'strftime') else str(row.date)
            if row.amount_try is not None:
                withdrawal_value = abs(float(row.amount_try or 0))
            else:
                amount = abs(float(row.amount or 0))
                if row.currency and row.currency.upper() == 'USD':
                    withdrawal_value = amount * exchange_rate
                elif row.currency and row.currency.upper() == 'EUR':
                    try:
                        latest_rate = ExchangeRate.query.order_by(ExchangeRate.date.desc()).first()
                        eur_rate = float(latest_rate.eur_to_tl) if latest_rate and latest_rate.eur_to_tl else (exchange_rate * 1.08)
                    except:
                        eur_rate = exchange_rate * 1.08
                    withdrawal_value = amount * eur_rate
                else:
                    withdrawal_value = amount
            daily_withdrawals_dict[date_str] = daily_withdrawals_dict.get(date_str, 0) + withdrawal_value
        
        # Calculate net cash per day (deposits - withdrawals)
        daily_revenue_dict = {}
        all_dates = set(daily_deposits_dict.keys()) | set(daily_withdrawals_dict.keys())
        for date_str in all_dates:
            deposits = daily_deposits_dict.get(date_str, 0)
            withdrawals = daily_withdrawals_dict.get(date_str, 0)
            daily_revenue_dict[date_str] = deposits - withdrawals
        query_4_time = (time_module.time() - query_4_start) * 1000
        logger.debug(f"Chart data query: {query_4_time:.2f}ms")
        # Removed verbose logging - only log slow queries
        
        # Debug: Log sample data
        if daily_revenue_dict:
            sample_dates = list(daily_revenue_dict.keys())[:3]
            for date_str in sample_dates:
                logger.debug(f"Sample day: {date_str} -> net_cash={daily_revenue_dict[date_str]}")
        
        # Fill in missing dates with zero values
        processing_start = time_module.time()
        daily_revenue = []
        current_date = chart_start_date.date() if hasattr(chart_start_date, 'date') else chart_start_date
        end_date = now.date()
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            net_cash_value = daily_revenue_dict.get(date_str, 0)
            daily_revenue.append({
                'date': date_str,
                'amount': net_cash_value,  # Keep 'amount' for backwards compatibility
                'net_cash': net_cash_value  # Also provide as 'net_cash' for clarity
            })
            current_date += timedelta(days=1)
        
        processing_time = (time_module.time() - processing_start) * 1000
        logger.debug(f"Chart data processing: {processing_time:.2f}ms")
        logger.debug(f"Chart data: {len(daily_revenue)} days from {daily_revenue[0]['date'] if daily_revenue else 'N/A'} to {daily_revenue[-1]['date'] if daily_revenue else 'N/A'}")
        
        # Log first few days for debugging
        if daily_revenue:
            sample_days = daily_revenue[:5]
            logger.debug(f"Sample chart data (first 5 days): {sample_days}")
        
        # Calculate previous period stats for change comparison
        prev_period_start = None
        prev_period_end = None
        if date_filter:
            # date_filter is a datetime, convert to date for calculation
            filter_date = date_filter.date() if hasattr(date_filter, 'date') else date_filter
            period_duration = (now.date() - filter_date).days
            prev_period_end = filter_date
            prev_period_start = filter_date - timedelta(days=period_duration)
        else:
            # For 'all' range, compare with last 30 days
            prev_period_end = (now - timedelta(days=30)).date()
            prev_period_start = (now - timedelta(days=60)).date()
        
        # Get previous period stats
        prev_base_query = db.session.query(Transaction)
        if prev_period_start and prev_period_end:
            prev_base_query = prev_base_query.filter(
                Transaction.date >= prev_period_start,
                Transaction.date < prev_period_end
            )
        
        # Previous period revenue
        prev_stats_with_try = prev_base_query.filter(Transaction.net_amount_try.isnot(None)).with_entities(
            func.count(Transaction.id).label('count_with_try'),
            func.sum(Transaction.net_amount_try).label('revenue_with_try')
        ).first()
        
        prev_transactions_without_try = prev_base_query.filter(Transaction.net_amount_try.is_(None)).with_entities(
            Transaction.net_amount,
            Transaction.currency
        ).all()
        
        prev_revenue_without_try = 0.0
        for txn in prev_transactions_without_try:
            if txn.currency and txn.currency.upper() == 'USD':
                prev_revenue_without_try += float(txn.net_amount or 0) * exchange_rate
            elif txn.currency and txn.currency.upper() == 'EUR':
                try:
                    latest_rate = ExchangeRate.query.order_by(ExchangeRate.date.desc()).first()
                    eur_rate = float(latest_rate.eur_to_tl) if latest_rate and latest_rate.eur_to_tl else (exchange_rate * 1.08)
                except:
                    eur_rate = exchange_rate * 1.08
                prev_revenue_without_try += float(txn.net_amount or 0) * eur_rate
            else:
                prev_revenue_without_try += float(txn.net_amount or 0)
        
        prev_total_revenue = float(prev_stats_with_try.revenue_with_try or 0) + prev_revenue_without_try
        prev_total_transactions = (prev_stats_with_try.count_with_try or 0) + len(prev_transactions_without_try)
        prev_active_clients = prev_base_query.with_entities(
            func.count(func.distinct(Transaction.client_name))
        ).scalar() or 0
        
        # Calculate previous period net cash (deposits - withdrawals)
        prev_deposits_base = prev_base_query.filter(Transaction.category == 'DEP')
        prev_deposits_with_try = prev_deposits_base.filter(Transaction.amount_try.isnot(None)).with_entities(
            func.sum(func.abs(Transaction.amount_try))
        ).scalar() or 0
        
        prev_deposits_without_try_txns = prev_deposits_base.filter(Transaction.amount_try.is_(None)).with_entities(
            Transaction.amount,
            Transaction.currency
        ).all()
        
        prev_deposits_without_try = 0.0
        for txn in prev_deposits_without_try_txns:
            amount = abs(float(txn.amount or 0))
            if txn.currency and txn.currency.upper() == 'USD':
                prev_deposits_without_try += amount * exchange_rate
            elif txn.currency and txn.currency.upper() == 'EUR':
                try:
                    latest_rate = ExchangeRate.query.order_by(ExchangeRate.date.desc()).first()
                    eur_rate = float(latest_rate.eur_to_tl) if latest_rate and latest_rate.eur_to_tl else (exchange_rate * 1.08)
                except:
                    eur_rate = exchange_rate * 1.08
                prev_deposits_without_try += amount * eur_rate
            else:
                prev_deposits_without_try += amount
        
        prev_total_deposits = float(prev_deposits_with_try) + prev_deposits_without_try
        
        prev_withdrawals_base = prev_base_query.filter(Transaction.category == 'WD')
        prev_withdrawals_with_try = prev_withdrawals_base.filter(Transaction.amount_try.isnot(None)).with_entities(
            func.sum(func.abs(Transaction.amount_try))
        ).scalar() or 0
        
        prev_withdrawals_without_try_txns = prev_withdrawals_base.filter(Transaction.amount_try.is_(None)).with_entities(
            Transaction.amount,
            Transaction.currency
        ).all()
        
        prev_withdrawals_without_try = 0.0
        for txn in prev_withdrawals_without_try_txns:
            amount = abs(float(txn.amount or 0))
            if txn.currency and txn.currency.upper() == 'USD':
                prev_withdrawals_without_try += amount * exchange_rate
            elif txn.currency and txn.currency.upper() == 'EUR':
                try:
                    latest_rate = ExchangeRate.query.order_by(ExchangeRate.date.desc()).first()
                    eur_rate = float(latest_rate.eur_to_tl) if latest_rate and latest_rate.eur_to_tl else (exchange_rate * 1.08)
                except:
                    eur_rate = exchange_rate * 1.08
                prev_withdrawals_without_try += amount * eur_rate
            else:
                prev_withdrawals_without_try += amount
        
        prev_total_withdrawals = float(prev_withdrawals_with_try) + prev_withdrawals_without_try
        prev_net_cash = prev_total_deposits - prev_total_withdrawals
        
        # Calculate percentage changes
        def safe_percentage_change(current, previous):
            # Her iki deger de 0 ise, degisim yok (0%)
            if current == 0 and previous == 0:
                return 0.0
            # Onceki donem 0 ama su anki donem > 0 ise, sonsuz artis yerine 0% dondur
            # (cunku gercek bir karsilastirma yapilamaz)
            if previous == 0:
                return 0.0
            # Normal hesaplama: ((current - previous) / previous) * 100
            return ((current - previous) / previous) * 100
        
        # Debug: Log values for troubleshooting
        logger.debug(f"Change calculation - Current: revenue={total_revenue}, transactions={total_transactions}, clients={active_clients_count}, net_cash={net_cash_tl}")
        logger.debug(f"Change calculation - Previous: revenue={prev_total_revenue}, transactions={prev_total_transactions}, clients={prev_active_clients}, net_cash={prev_net_cash}")
        
        revenue_change = safe_percentage_change(total_revenue, prev_total_revenue)
        transactions_change = safe_percentage_change(total_transactions, prev_total_transactions)
        clients_change = safe_percentage_change(active_clients_count, prev_active_clients)
        net_cash_change = safe_percentage_change(net_cash_tl, prev_net_cash)
        
        # Debug: Log calculated changes
        logger.debug(f"Calculated changes - revenue={revenue_change}%, transactions={transactions_change}%, clients={clients_change}%, net_cash={net_cash_change}%")
        
        # Growth rate is revenue change
        growth_rate_value = revenue_change
        growth_rate_change = 0.0  # Growth rate change would need previous growth rate, default to 0
        
        # Format change strings
        def format_change(change_value):
            sign = '+' if change_value >= 0 else ''
            return f"{sign}{change_value:.1f}%"
        
        # Calculate daily, weekly, monthly, annual revenue from daily_revenue chart data
        # Daily revenue = last day's net cash (use amount as fallback)
        if daily_revenue and len(daily_revenue) > 0:
            last_day = daily_revenue[-1]
            daily_revenue_value = float(last_day.get('net_cash', last_day.get('amount', 0)))
        else:
            daily_revenue_value = 0.0
        
        # Weekly revenue = sum of last 7 days
        if daily_revenue and len(daily_revenue) >= 7:
            weekly_revenue_value = sum(float(day.get('net_cash', day.get('amount', 0))) for day in daily_revenue[-7:])
        elif daily_revenue:
            weekly_revenue_value = sum(float(day.get('net_cash', day.get('amount', 0))) for day in daily_revenue)
        else:
            weekly_revenue_value = 0.0
        
        # Monthly revenue = sum of last 30 days
        if daily_revenue and len(daily_revenue) >= 30:
            monthly_revenue_value = sum(float(day.get('net_cash', day.get('amount', 0))) for day in daily_revenue[-30:])
        elif daily_revenue:
            monthly_revenue_value = sum(float(day.get('net_cash', day.get('amount', 0))) for day in daily_revenue)
        else:
            monthly_revenue_value = 0.0
        
        # Annual revenue = total net cash (all time)
        annual_revenue_value = float(net_cash_tl)
        
        # Build response (annual_net_cash_usd already calculated above)
        
        # Format values - ensure proper formatting for zero values
        total_revenue_formatted = f"₺{float(total_revenue or 0):,.0f}" if (total_revenue or 0) != 0 else "₺0"
        total_transactions_formatted = f"{int(total_transactions or 0):,}" if (total_transactions or 0) != 0 else "0"
        active_clients_formatted = f"{int(active_clients_count or 0):,}" if (active_clients_count or 0) != 0 else "0"
        net_cash_formatted = f"₺{float(net_cash_tl or 0):,.0f}" if (net_cash_tl or 0) != 0 else "₺0"
        
        response_data = {
            'stats': {
                'total_revenue': {
                    'value': total_revenue_formatted,
                    'change': format_change(revenue_change),
                    'changeType': 'positive' if revenue_change >= 0 else 'negative'
                },
                'total_transactions': {
                    'value': total_transactions_formatted,
                    'change': format_change(transactions_change),
                    'changeType': 'positive' if transactions_change >= 0 else 'negative'
                },
                'active_clients': {
                    'value': active_clients_formatted,
                    'change': format_change(clients_change),
                    'changeType': 'positive' if clients_change >= 0 else 'negative'
                },
                'growth_rate': {
                    'value': f"{growth_rate_value:.1f}%",
                    'change': format_change(growth_rate_change),
                    'changeType': 'positive' if growth_rate_change >= 0 else 'negative'
                },
                'net_cash': {
                    'value': net_cash_formatted,
                    'change': format_change(net_cash_change),
                    'changeType': 'positive' if net_cash_change >= 0 else 'negative'
                }
            },
            'psp_summary': [
                {
                    'psp': row.psp,
                    'transaction_count': row.transaction_count,
                    'total_amount': float(row.total_amount),
                    'commission_rate': 7.5,  # Default rate
                    'commission': float(row.total_amount) * 0.075
                }
                for row in psp_stats
            ],
            'chart_data': {
                'daily_revenue': daily_revenue  # Already formatted with date strings and amounts
            },
            'exchange_rates': {
                'USD_TRY': exchange_rate,  # CRITICAL FIX: Use cached rate for consistency
                'last_updated': datetime.now().isoformat()
            },
            'commission_analytics': {
                'total_commission': float(total_commission or 0),
                'average_rate': 7.5,
                'top_psp': psp_stats[0].psp if psp_stats else None
            },
            # CRITICAL FIX: Add summary object that frontend expects
            'summary': {
                'net_cash': float(net_cash_tl),
                'total_net': float(total_revenue),  # Legacy field for backward compatibility
                'transaction_count': total_transactions or 0,
                'active_clients': active_clients_count or 0,
                'total_commission': float(total_commission or 0),
                'total_revenue': float(total_revenue or 0),
                'daily_revenue': float(daily_revenue_value),
                'weekly_revenue': float(weekly_revenue_value),
                'monthly_revenue': float(monthly_revenue_value),
                'annual_revenue': float(annual_revenue_value),
                'total_deposits': float(total_deposits),
                'total_withdrawals': float(total_withdrawals)
            },
            # Add financial performance data structure for frontend compatibility
            # CRITICAL FIX: Use REAL calculated values for daily, monthly, and annual (not estimates)
            'financial_performance': {
                'annual': {
                    'net_cash_tl': float(annual_totals['net_cash_tl']),
                    'net_cash_usd': float(annual_totals['net_cash_usd']),
                    'total_deposits_tl': float(annual_totals['deposits_tl']),
                    'total_deposits_usd': float(annual_totals['deposits_usd']),
                    'total_withdrawals_tl': float(annual_totals['withdrawals_tl']),
                    'total_withdrawals_usd': float(annual_totals['withdrawals_usd']),
                    'total_transactions': total_transactions or 0,
                    # Payment method breakdown
                    'total_bank_tl': float(annual_totals['bank_tl']),
                    'total_bank_usd': float(annual_totals['bank_usd']),
                    'total_cc_tl': float(annual_totals['cc_tl']),
                    'total_cc_usd': float(annual_totals['cc_usd']),
                    'total_tether_tl': float(annual_totals['tether_tl']),
                    'total_tether_usd': float(annual_totals['tether_usd']),
                    'conv_usd': float(annual_totals['conv_usd']),
                    'conv_tl': 0.0,  # Conv is always in USD
                    'bank_count': annual_totals['bank_count'],
                    'cc_count': annual_totals['cc_count'],
                    'tether_count': annual_totals['tether_count']
                },
                'monthly': {
                    'net_cash_tl': float(monthly_totals['net_cash_tl']),
                    'net_cash_usd': float(monthly_totals['net_cash_usd']),
                    'total_deposits_tl': float(monthly_totals['deposits_tl']),
                    'total_deposits_usd': float(monthly_totals['deposits_usd']),
                    'total_withdrawals_tl': float(monthly_totals['withdrawals_tl']),
                    'total_withdrawals_usd': float(monthly_totals['withdrawals_usd']),
                    'total_transactions': len(monthly_query),
                    # Payment method breakdown (REAL monthly data)
                    'total_bank_tl': float(monthly_totals['bank_tl']),
                    'total_bank_usd': float(monthly_totals['bank_usd']),
                    'total_cc_tl': float(monthly_totals['cc_tl']),
                    'total_cc_usd': float(monthly_totals['cc_usd']),
                    'total_tether_tl': float(monthly_totals['tether_tl']),
                    'total_tether_usd': float(monthly_totals['tether_usd']),
                    'conv_usd': float(monthly_totals['conv_usd']),
                    'conv_tl': 0.0,
                    'bank_count': monthly_totals['bank_count'],
                    'cc_count': monthly_totals['cc_count'],
                    'tether_count': monthly_totals['tether_count']
                },
                'daily': {
                    'net_cash_tl': float(daily_totals['net_cash_tl']),
                    'net_cash_usd': float(daily_totals['net_cash_usd']),
                    'total_deposits_tl': float(daily_totals['deposits_tl']),
                    'total_deposits_usd': float(daily_totals['deposits_usd']),
                    'total_withdrawals_tl': float(daily_totals['withdrawals_tl']),
                    'total_withdrawals_usd': float(daily_totals['withdrawals_usd']),
                    'total_transactions': len(daily_query),
                    # Payment method breakdown (REAL daily data)
                    'total_bank_tl': float(daily_totals['bank_tl']),
                    'total_bank_usd': float(daily_totals['bank_usd']),
                    'total_cc_tl': float(daily_totals['cc_tl']),
                    'total_cc_usd': float(daily_totals['cc_usd']),
                    'total_tether_tl': float(daily_totals['tether_tl']),
                    'total_tether_usd': float(daily_totals['tether_usd']),
                    'conv_usd': float(daily_totals['conv_usd']),
                    'conv_tl': 0.0,
                    'bank_count': daily_totals['bank_count'],
                    'cc_count': daily_totals['cc_count'],
                    'tether_count': daily_totals['tether_count']
                }
            }
        }
        
        # Cache result for 120 seconds (2 minutes) for better performance
        cache_service.set(cache_key, response_data, 120)
        
        # Log only slow requests (>2s) or in debug mode
        total_time = (time_module.time() - query_start_time) * 1000
        if total_time > 2000:
            logger.warning(f"Slow consolidated dashboard query: {total_time:.2f}ms (Query1: {query_1_time:.2f}ms, Query2: {query_2_time:.2f}ms, Query3: {query_3_time:.2f}ms, Query4: {query_4_time:.2f}ms, Processing: {processing_time:.2f}ms)")
        elif current_app.config.get('DEBUG', False):
            logger.debug(f"Consolidated dashboard: {total_time:.2f}ms")
        # Structured performance log
        api_logger.log_performance('consolidated_dashboard', total_time / 1000.0, {
            'range': time_range,
            'q1_ms': round(query_1_time, 2),
            'q2_ms': round(query_2_time, 2),
            'q3_ms': round(query_3_time, 2),
            'q4_ms': round(query_4_time, 2),
            'processing_ms': round(processing_time, 2),
        })
        
        # Support optional envelope for gradual migration
        if request.args.get('envelope') in ('1', 'true', 'True'):
            from app.utils.api_response import make_response
            return jsonify(make_response(data=response_data)), 200
        # Default: legacy raw JSON shape for current frontend
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error in consolidated dashboard: {str(e)}", exc_info=True)
        
        # Return legacy error structure expected by existing frontend
        return jsonify({
            'error': 'Failed to retrieve consolidated dashboard data',
            'message': str(e)
        }), 500
