"""
Automated Currency Fixer Service
Automatically detects and fixes currency-related issues in the system
"""

import logging
from datetime import datetime, timezone, date
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Optional, Tuple
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.models.transaction import Transaction
from app.models.config import ExchangeRate
# Use enhanced exchange rate service (legacy service deprecated)
from app.services.enhanced_exchange_rate_service import enhanced_exchange_service as exchange_rate_service

logger = logging.getLogger(__name__)

class CurrencyFixerService:
    """Service to automatically detect and fix currency issues"""
    
    # Standard currency mappings
    CURRENCY_STANDARDS = {
        'TL': 'TRY',      # Standardize to TRY
        'TRY': 'TRY',
        'USD': 'USD',
        'EUR': 'EUR',
        'GBP': 'GBP',
        '₺': 'TRY',       # Symbol to code
        '$': 'USD',
        '€': 'EUR',
        '£': 'GBP',
    }
    
    def __init__(self):
        self.fixed_transactions = 0
        self.errors = []
        self.report = {}
    
    def run_full_currency_audit_and_fix(self) -> Dict:
        """
        Run a complete currency audit and fix all issues
        Returns a detailed report of what was fixed
        """
        logger.info("🔧 Starting comprehensive currency audit and fix...")
        
        self.report = {
            'start_time': datetime.now().isoformat(),
            'issues_found': {},
            'fixes_applied': {},
            'transactions_processed': 0,
            'errors': []
        }
        
        try:
            # Step 1: Standardize currency codes
            self._standardize_currency_codes()
            
            # Step 2: Fix missing TRY amounts
            self._fix_missing_try_amounts()
            
            # Step 3: Validate and fix exchange rates
            self._validate_and_fix_exchange_rates()
            
            # Step 4: Fix inconsistent conversions
            self._fix_inconsistent_conversions()
            
            # Step 5: Validate all calculations
            self._validate_calculations()
            
            self.report['end_time'] = datetime.now().isoformat()
            self.report['status'] = 'completed'
            
            logger.info(f"Currency audit completed. Fixed {self.fixed_transactions} transactions.")
            
        except Exception as e:
            logger.error(f"Currency audit failed: {e}")
            self.report['status'] = 'failed'
            self.report['error'] = str(e)
        
        return self.report
    
    def _standardize_currency_codes(self):
        """Standardize all currency codes to proper ISO format"""
        logger.info("🔄 Standardizing currency codes...")
        
        try:
            # Get all transactions with non-standard currency codes
            transactions = Transaction.query.filter(
                Transaction.currency.in_(['TL', '₺', '$', '€', '£'])
            ).all()
            
            standardized_count = 0
            for transaction in transactions:
                old_currency = transaction.currency
                new_currency = self.CURRENCY_STANDARDS.get(old_currency, old_currency)
                
                if old_currency != new_currency:
                    transaction.currency = new_currency
                    standardized_count += 1
                    logger.debug(f"Standardized currency {old_currency} → {new_currency} for transaction {transaction.id}")
            
            if standardized_count > 0:
                db.session.commit()
                self.report['fixes_applied']['standardized_currencies'] = standardized_count
                logger.info(f"Standardized {standardized_count} currency codes")
            
        except Exception as e:
            logger.error(f"Error standardizing currency codes: {e}")
            self.errors.append(f"Currency standardization error: {e}")
    
    def _fix_missing_try_amounts(self):
        """Find and fix transactions missing TRY conversion amounts"""
        logger.info("🔄 Fixing missing TRY conversion amounts...")
        
        try:
            # Find USD/EUR transactions without TRY amounts
            transactions = Transaction.query.filter(
                Transaction.currency.in_(['USD', 'EUR']),
                Transaction.amount_try.is_(None)
            ).all()
            
            fixed_count = 0
            for transaction in transactions:
                # Try to get exchange rate for transaction date
                exchange_rate = self._get_exchange_rate_for_date(
                    transaction.currency, 
                    transaction.date
                )
                
                if exchange_rate:
                    # Calculate TRY amounts
                    transaction.amount_try = transaction.amount * exchange_rate
                    transaction.commission_try = transaction.commission * exchange_rate
                    transaction.net_amount_try = transaction.net_amount * exchange_rate
                    transaction.exchange_rate = exchange_rate
                    
                    fixed_count += 1
                    logger.debug(f"Fixed TRY amounts for transaction {transaction.id} using rate {exchange_rate}")
                else:
                    # Use current exchange rate as fallback
                    current_rate = exchange_rate_service.get_current_rate_from_api()
                    if current_rate:
                        rate_value = Decimal(str(current_rate['rate']))
                        transaction.amount_try = transaction.amount * rate_value
                        transaction.commission_try = transaction.commission * rate_value
                        transaction.net_amount_try = transaction.net_amount * rate_value
                        transaction.exchange_rate = rate_value
                        
                        fixed_count += 1
                        logger.debug(f"Fixed TRY amounts for transaction {transaction.id} using current rate {rate_value}")
            
            if fixed_count > 0:
                db.session.commit()
                self.report['fixes_applied']['missing_try_amounts'] = fixed_count
                logger.info(f"Fixed {fixed_count} transactions with missing TRY amounts")
                
        except Exception as e:
            logger.error(f"Error fixing missing TRY amounts: {e}")
            self.errors.append(f"TRY amounts fix error: {e}")
    
    def _validate_and_fix_exchange_rates(self):
        """Validate and fix invalid exchange rates"""
        logger.info("🔄 Validating and fixing exchange rates...")
        
        try:
            # Find transactions with suspicious exchange rates
            transactions = Transaction.query.filter(
                Transaction.currency.in_(['USD', 'EUR']),
                Transaction.exchange_rate.isnot(None)
            ).all()
            
            fixed_count = 0
            for transaction in transactions:
                # Check if exchange rate is reasonable (USD/TRY should be 25-50, EUR/TRY should be 30-55)
                rate = float(transaction.exchange_rate)
                is_invalid = False
                
                if transaction.currency == 'USD' and (rate < 25 or rate > 50):
                    is_invalid = True
                elif transaction.currency == 'EUR' and (rate < 30 or rate > 55):
                    is_invalid = True
                
                if is_invalid:
                    # Get correct exchange rate
                    correct_rate = self._get_exchange_rate_for_date(
                        transaction.currency, 
                        transaction.date
                    )
                    
                    if correct_rate:
                        old_rate = transaction.exchange_rate
                        transaction.exchange_rate = correct_rate
                        
                        # Recalculate TRY amounts
                        transaction.amount_try = transaction.amount * correct_rate
                        transaction.commission_try = transaction.commission * correct_rate
                        transaction.net_amount_try = transaction.net_amount * correct_rate
                        
                        fixed_count += 1
                        logger.debug(f"Fixed invalid exchange rate for transaction {transaction.id}: {old_rate} → {correct_rate}")
            
            if fixed_count > 0:
                db.session.commit()
                self.report['fixes_applied']['invalid_exchange_rates'] = fixed_count
                logger.info(f"Fixed {fixed_count} invalid exchange rates")
                
        except Exception as e:
            logger.error(f"Error validating exchange rates: {e}")
            self.errors.append(f"Exchange rate validation error: {e}")
    
    def _fix_inconsistent_conversions(self):
        """Fix inconsistent currency conversions"""
        logger.info("🔄 Fixing inconsistent currency conversions...")
        
        try:
            # Find transactions where calculated TRY amount doesn't match stored amount
            transactions = Transaction.query.filter(
                Transaction.currency.in_(['USD', 'EUR']),
                Transaction.amount_try.isnot(None),
                Transaction.exchange_rate.isnot(None)
            ).all()
            
            fixed_count = 0
            for transaction in transactions:
                # Calculate what TRY amount should be
                expected_try = transaction.amount * transaction.exchange_rate
                actual_try = transaction.amount_try
                
                # Allow 1% tolerance for rounding differences
                tolerance = expected_try * Decimal('0.01')
                
                if abs(expected_try - actual_try) > tolerance:
                    # Fix the inconsistency
                    transaction.amount_try = expected_try
                    transaction.commission_try = transaction.commission * transaction.exchange_rate
                    transaction.net_amount_try = transaction.net_amount * transaction.exchange_rate
                    
                    fixed_count += 1
                    logger.debug(f"Fixed inconsistent conversion for transaction {transaction.id}: {actual_try} → {expected_try}")
            
            if fixed_count > 0:
                db.session.commit()
                self.report['fixes_applied']['inconsistent_conversions'] = fixed_count
                logger.info(f"Fixed {fixed_count} inconsistent conversions")
                
        except Exception as e:
            logger.error(f"Error fixing inconsistent conversions: {e}")
            self.errors.append(f"Inconsistent conversions error: {e}")
    
    def _validate_calculations(self):
        """Validate that all financial calculations are correct"""
        logger.info("🔄 Validating financial calculations...")
        
        try:
            # Check net_amount = amount - commission for all transactions
            transactions = Transaction.query.all()
            
            fixed_count = 0
            for transaction in transactions:
                expected_net = transaction.amount - transaction.commission
                
                if abs(expected_net - transaction.net_amount) > Decimal('0.01'):
                    transaction.net_amount = expected_net
                    
                    # If it's a foreign currency, also fix TRY net amount
                    if transaction.currency in ['USD', 'EUR'] and transaction.exchange_rate:
                        transaction.net_amount_try = expected_net * transaction.exchange_rate
                    
                    fixed_count += 1
                    logger.debug(f"Fixed net amount calculation for transaction {transaction.id}")
            
            if fixed_count > 0:
                db.session.commit()
                self.report['fixes_applied']['calculation_errors'] = fixed_count
                logger.info(f"Fixed {fixed_count} calculation errors")
                
        except Exception as e:
            logger.error(f"Error validating calculations: {e}")
            self.errors.append(f"Calculation validation error: {e}")
    
    def _get_exchange_rate_for_date(self, currency: str, target_date: date) -> Optional[Decimal]:
        """Get exchange rate for a specific currency and date"""
        try:
            # First try to get from database
            exchange_rate_record = ExchangeRate.query.filter_by(date=target_date).first()
            
            if exchange_rate_record:
                if currency == 'USD':
                    return Decimal(str(exchange_rate_record.usd_to_tl))
                elif currency == 'EUR':
                    return Decimal(str(exchange_rate_record.eur_to_tl)) if exchange_rate_record.eur_to_tl else None
            
            # Fallback to exchange rate service
            rate_data = exchange_rate_service.get_or_fetch_rate(currency, target_date)
            if rate_data:
                return Decimal(str(rate_data))
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting exchange rate for {currency} on {target_date}: {e}")
            return None
    
    def get_currency_health_report(self) -> Dict:
        """Generate a health report for currency data"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'total_transactions': Transaction.query.count(),
                'by_currency': {},
                'issues': {
                    'missing_try_amounts': 0,
                    'invalid_exchange_rates': 0,
                    'non_standard_currencies': 0,
                    'calculation_errors': 0
                }
            }
            
            # Count by currency
            for currency in ['TRY', 'USD', 'EUR', 'TL']:
                count = Transaction.query.filter_by(currency=currency).count()
                if count > 0:
                    report['by_currency'][currency] = count
            
            # Count issues
            report['issues']['missing_try_amounts'] = Transaction.query.filter(
                Transaction.currency.in_(['USD', 'EUR']),
                Transaction.amount_try.is_(None)
            ).count()
            
            report['issues']['non_standard_currencies'] = Transaction.query.filter(
                Transaction.currency.in_(['TL', '₺', '$', '€', '£'])
            ).count()
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating currency health report: {e}")
            return {'error': str(e)}

# Global instance
currency_fixer_service = CurrencyFixerService()
