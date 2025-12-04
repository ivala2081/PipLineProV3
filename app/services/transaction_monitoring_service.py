"""
Automated Transaction Calculation Monitoring Service
Continuously monitors transaction calculations and alerts on discrepancies
"""

import logging
import threading
import time
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
import json

from app import db
from app.models.transaction import Transaction
from app.models.exchange_rate import ExchangeRate
from app.services.decimal_float_fix_service import decimal_float_service
# Use enhanced exchange rate service (legacy service deprecated)
from app.services.enhanced_exchange_rate_service import EnhancedExchangeRateService as ExchangeRateService

logger = logging.getLogger(__name__)

@dataclass
class CalculationAlert:
    """Alert for calculation discrepancy"""
    transaction_id: int
    field_name: str
    expected_value: Decimal
    actual_value: Decimal
    difference: Decimal
    percentage_diff: float
    currency: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    timestamp: datetime
    description: str

@dataclass
class MonitoringStats:
    """Monitoring statistics"""
    total_checks: int
    alerts_generated: int
    last_check_time: datetime
    uptime_seconds: float
    average_check_duration: float
    currency_breakdown: Dict[str, int]

class TransactionMonitoringService:
    """Automated transaction calculation monitoring service"""
    
    def __init__(self, check_interval: int = 300):  # 5 minutes default
        self.check_interval = check_interval
        self.is_running = False
        self.monitoring_thread = None
        self.alerts: List[CalculationAlert] = []
        self.stats = MonitoringStats(
            total_checks=0,
            alerts_generated=0,
            last_check_time=datetime.now(),
            uptime_seconds=0.0,
            average_check_duration=0.0,
            currency_breakdown={}
        )
        
        # Alert thresholds
        self.thresholds = {
            'low': Decimal('0.01'),      # 1 cent
            'medium': Decimal('1.00'),   # 1 TL
            'high': Decimal('10.00'),    # 10 TL
            'critical': Decimal('100.00') # 100 TL
        }
        
        # Commission rates for verification
        self.commission_rates = {
            'iyzico': Decimal('0.025'),  # 2.5%
            'paytr': Decimal('0.02'),    # 2%
            'stripe': Decimal('0.029'),  # 2.9%
            'default': Decimal('0.015')  # 1.5%
        }
        
        # Exchange rate service
        self.exchange_rate_service = ExchangeRateService()
        
        # Alert callbacks
        self.alert_callbacks: List[Callable[[CalculationAlert], None]] = []
        
        # Last checked transaction IDs to avoid duplicate alerts
        self.last_checked_transactions = set()
        
        # Service initialization - no verbose logging needed
    
    def start_monitoring(self):
        """Start the monitoring service"""
        if self.is_running:
            logger.warning("Monitoring service is already running")
            return
        
        self.is_running = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        # Monitoring started - only log errors
    
    def stop_monitoring(self):
        """Stop the monitoring service"""
        if not self.is_running:
            logger.warning("Monitoring service is not running")
            return
        
        self.is_running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        logger.info("Transaction monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        start_time = datetime.now()
        
        while self.is_running:
            try:
                check_start = datetime.now()
                
                # Perform calculation check
                self._check_calculations()
                
                # Update statistics
                check_duration = (datetime.now() - check_start).total_seconds()
                self.stats.total_checks += 1
                self.stats.last_check_time = datetime.now()
                self.stats.uptime_seconds = (datetime.now() - start_time).total_seconds()
                
                # Update average check duration
                if self.stats.total_checks == 1:
                    self.stats.average_check_duration = check_duration
                else:
                    self.stats.average_check_duration = (
                        (self.stats.average_check_duration * (self.stats.total_checks - 1) + check_duration) 
                        / self.stats.total_checks
                    )
                
                logger.debug(f"✅ Calculation check completed in {check_duration:.2f}s")
                
                # Wait for next check
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def _check_calculations(self):
        """Check all transaction calculations"""
        try:
            # Get recent transactions (last 24 hours)
            yesterday = date.today() - timedelta(days=1)
            recent_transactions = Transaction.query.filter(
                Transaction.date >= yesterday
            ).all()
            
            logger.debug(f"🔍 Checking {len(recent_transactions)} recent transactions")
            
            for transaction in recent_transactions:
                # Skip if already checked recently
                if transaction.id in self.last_checked_transactions:
                    continue
                
                # Check transaction calculations
                alerts = self._check_transaction(transaction)
                
                # Add alerts
                for alert in alerts:
                    self.alerts.append(alert)
                    self.stats.alerts_generated += 1
                    
                    # Trigger alert callbacks
                    for callback in self.alert_callbacks:
                        try:
                            callback(alert)
                        except Exception as e:
                            logger.error(f"Error in alert callback: {e}")
                
                # Mark as checked
                self.last_checked_transactions.add(transaction.id)
            
            # Clean up old checked transactions (keep last 1000)
            if len(self.last_checked_transactions) > 1000:
                self.last_checked_transactions = set(list(self.last_checked_transactions)[-1000:])
            
            # Clean up old alerts (keep last 100)
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-100:]
            
        except Exception as e:
            logger.error(f"❌ Error checking calculations: {e}")
    
    def _check_transaction(self, transaction: Transaction) -> List[CalculationAlert]:
        """Check calculations for a single transaction"""
        alerts = []
        
        try:
            # Get exchange rate
            exchange_rate = self._get_exchange_rate(transaction.date, transaction.currency)
            
            # Check commission calculation
            commission_alert = self._check_commission(transaction, exchange_rate)
            if commission_alert:
                alerts.append(commission_alert)
            
            # Check net amount calculation
            net_amount_alert = self._check_net_amount(transaction, exchange_rate)
            if net_amount_alert:
                alerts.append(net_amount_alert)
            
            # Check amount validation
            amount_alert = self._check_amount_validation(transaction)
            if amount_alert:
                alerts.append(amount_alert)
            
            # Check currency conversion (if applicable)
            if transaction.currency and transaction.currency.upper() != 'TL':
                conversion_alert = self._check_currency_conversion(transaction, exchange_rate)
                if conversion_alert:
                    alerts.append(conversion_alert)
            
        except Exception as e:
            logger.error(f"❌ Error checking transaction #{transaction.id}: {e}")
            
            # Create critical alert for checking errors
            alerts.append(CalculationAlert(
                transaction_id=transaction.id,
                field_name='verification_error',
                expected_value=Decimal('0'),
                actual_value=Decimal('0'),
                difference=Decimal('0'),
                percentage_diff=0.0,
                currency=transaction.currency or 'TL',
                severity='critical',
                timestamp=datetime.now(),
                description=f"Error verifying transaction: {e}"
            ))
        
        return alerts
    
    def _check_commission(self, transaction: Transaction, exchange_rate: Optional[Decimal]) -> Optional[CalculationAlert]:
        """Check commission calculation"""
        expected_commission = self._calculate_expected_commission(transaction)
        actual_commission = decimal_float_service.safe_decimal(transaction.commission)
        
        difference = abs(expected_commission - actual_commission)
        
        if difference > self.thresholds['low']:
            percentage_diff = (difference / expected_commission * 100) if expected_commission > 0 else 0
            severity = self._determine_severity(difference)
            
            return CalculationAlert(
                transaction_id=transaction.id,
                field_name='commission',
                expected_value=expected_commission,
                actual_value=actual_commission,
                difference=difference,
                percentage_diff=float(percentage_diff),
                currency=transaction.currency or 'TL',
                severity=severity,
                timestamp=datetime.now(),
                description=f"Commission calculation discrepancy: expected {expected_commission}, got {actual_commission}"
            )
        
        return None
    
    def _check_net_amount(self, transaction: Transaction, exchange_rate: Optional[Decimal]) -> Optional[CalculationAlert]:
        """Check net amount calculation"""
        expected_net = decimal_float_service.safe_decimal(transaction.amount) - decimal_float_service.safe_decimal(transaction.commission)
        actual_net = decimal_float_service.safe_decimal(transaction.net_amount)
        
        difference = abs(expected_net - actual_net)
        
        if difference > self.thresholds['low']:
            percentage_diff = (difference / expected_net * 100) if expected_net > 0 else 0
            severity = self._determine_severity(difference)
            
            return CalculationAlert(
                transaction_id=transaction.id,
                field_name='net_amount',
                expected_value=expected_net,
                actual_value=actual_net,
                difference=difference,
                percentage_diff=float(percentage_diff),
                currency=transaction.currency or 'TL',
                severity=severity,
                timestamp=datetime.now(),
                description=f"Net amount calculation discrepancy: expected {expected_net}, got {actual_net}"
            )
        
        return None
    
    def _check_amount_validation(self, transaction: Transaction) -> Optional[CalculationAlert]:
        """Check amount validation"""
        amount = decimal_float_service.safe_decimal(transaction.amount)
        
        # Check if amount is positive
        if amount <= 0:
            return CalculationAlert(
                transaction_id=transaction.id,
                field_name='amount_validation',
                expected_value=amount,
                actual_value=amount,
                difference=Decimal('0'),
                percentage_diff=0.0,
                currency=transaction.currency or 'TL',
                severity='critical',
                timestamp=datetime.now(),
                description=f"Invalid amount: {amount} (must be positive)"
            )
        
        # Check if amount is within limits
        if amount > Decimal('999999999.99'):
            return CalculationAlert(
                transaction_id=transaction.id,
                field_name='amount_validation',
                expected_value=amount,
                actual_value=amount,
                difference=Decimal('0'),
                percentage_diff=0.0,
                currency=transaction.currency or 'TL',
                severity='high',
                timestamp=datetime.now(),
                description=f"Amount exceeds limit: {amount} (max: 999,999,999.99)"
            )
        
        return None
    
    def _check_currency_conversion(self, transaction: Transaction, exchange_rate: Optional[Decimal]) -> Optional[CalculationAlert]:
        """Check currency conversion calculations"""
        if not exchange_rate or exchange_rate == 0:
            return CalculationAlert(
                transaction_id=transaction.id,
                field_name='currency_conversion',
                expected_value=Decimal('0'),
                actual_value=Decimal('0'),
                difference=Decimal('0'),
                percentage_diff=0.0,
                currency=transaction.currency or 'TL',
                severity='medium',
                timestamp=datetime.now(),
                description=f"Missing exchange rate for {transaction.currency} on {transaction.date}"
            )
        
        return None
    
    def _calculate_expected_commission(self, transaction: Transaction) -> Decimal:
        """Calculate expected commission based on business rules"""
        amount = decimal_float_service.safe_decimal(transaction.amount)
        
        # WD (Withdraw) transactions have ZERO commission
        if transaction.category and transaction.category.upper() == 'WD':
            return Decimal('0')
        
        # Get commission rate based on PSP
        psp = transaction.psp or 'default'
        commission_rate = self.commission_rates.get(psp.lower(), self.commission_rates['default'])
        
        expected_commission = decimal_float_service.safe_multiply(amount, commission_rate, 'decimal')
        return expected_commission.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def _get_exchange_rate(self, transaction_date: date, currency: str) -> Optional[Decimal]:
        """Get exchange rate for the transaction date and currency"""
        if not currency or currency.upper() == 'TL':
            return None
        
        try:
            # Get exchange rate from database
            exchange_rate = ExchangeRate.query.filter_by(
                date=transaction_date
            ).first()
            
            if exchange_rate:
                if currency.upper() == 'USD':
                    return decimal_float_service.safe_decimal(exchange_rate.usd_to_tl)
                elif currency.upper() == 'EUR':
                    return decimal_float_service.safe_decimal(exchange_rate.eur_to_tl)
                elif currency.upper() == 'GBP':
                    return decimal_float_service.safe_decimal(exchange_rate.gbp_to_tl)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting exchange rate for {currency} on {transaction_date}: {e}")
            return None
    
    def _determine_severity(self, difference: Decimal) -> str:
        """Determine alert severity based on difference amount"""
        if difference >= self.thresholds['critical']:
            return 'critical'
        elif difference >= self.thresholds['high']:
            return 'high'
        elif difference >= self.thresholds['medium']:
            return 'medium'
        else:
            return 'low'
    
    def add_alert_callback(self, callback: Callable[[CalculationAlert], None]):
        """Add a callback function to be called when alerts are generated"""
        self.alert_callbacks.append(callback)
        logger.info(f"Added alert callback: {callback.__name__}")
    
    def get_alerts(self, severity: Optional[str] = None, limit: int = 50) -> List[CalculationAlert]:
        """Get recent alerts, optionally filtered by severity"""
        alerts = self.alerts
        
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        
        return alerts[-limit:] if limit else alerts
    
    def get_stats(self) -> MonitoringStats:
        """Get monitoring statistics"""
        return self.stats
    
    def get_alert_summary(self) -> Dict[str, int]:
        """Get summary of alerts by severity"""
        summary = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        
        for alert in self.alerts:
            summary[alert.severity] += 1
        
        return summary
    
    def clear_alerts(self):
        """Clear all alerts"""
        self.alerts.clear()
        logger.info("Cleared all alerts")
    
    def export_alerts(self, filename: str = None) -> str:
        """Export alerts to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'transaction_alerts_{timestamp}.json'
        
        alert_data = []
        for alert in self.alerts:
            alert_data.append({
                'transaction_id': alert.transaction_id,
                'field_name': alert.field_name,
                'expected_value': float(alert.expected_value),
                'actual_value': float(alert.actual_value),
                'difference': float(alert.difference),
                'percentage_diff': alert.percentage_diff,
                'currency': alert.currency,
                'severity': alert.severity,
                'timestamp': alert.timestamp.isoformat(),
                'description': alert.description
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(alert_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(alert_data)} alerts to {filename}")
        return filename

# Global monitoring service instance
transaction_monitor = TransactionMonitoringService()

def start_transaction_monitoring():
    """Start the global transaction monitoring service"""
    transaction_monitor.start_monitoring()

def stop_transaction_monitoring():
    """Stop the global transaction monitoring service"""
    transaction_monitor.stop_monitoring()

def get_transaction_monitor():
    """Get the global transaction monitoring service instance"""
    return transaction_monitor
