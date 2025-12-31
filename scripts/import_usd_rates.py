"""
Script to import USD exchange rates and update transactions
Imports rates for June-December 2025 and updates existing USD transactions
"""
import sys
import os
from datetime import date, datetime, timedelta
from decimal import Decimal

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.config import ExchangeRate
from app.models.transaction import Transaction
from app.services.yfinance_rate_service import YFinanceRateService
from app.utils.unified_logger import get_logger

logger = get_logger(__name__)

# USD rates provided by user
RATES_DATA = {
    # June 2025 (30 days: 01.06.2025 - 30.06.2025)
    '2025-06': [
        39.25, 39.25, 39.25, 39.25, 39.25, 39.25, 39.25, 39.25, 39.25, 39.25,
        39.33, 39.33, 39.33, 39.33, 39.33, 39.33, 39.50, 39.50, 39.50, 39.50,
        39.50, 39.70, 39.70, 39.70, 39.70, 39.85, 39.85, 39.85, 39.85, 39.85
    ],
    # July 2025 (31 days: 01.07.2025 - 31.07.2025)
    '2025-07': [
        39.85, 39.85, 39.85, 39.85, 39.85, 40.00, 40.00, 40.00, 40.00, 40.00,
        40.00, 40.00, 40.00, 40.00, 40.00, 40.00, 40.20, 40.20, 40.20, 40.20,
        40.20, 40.60, 40.60, 40.60, 40.60, 40.60, 40.60, 40.60, 40.60, 40.60,
        40.60
    ],
    # August 2025 (31 days: 01.08.2025 - 31.08.2025)
    '2025-08': [
        40.60, 40.60, 40.60, 40.60, 40.60, 40.60, 40.60, 40.60, 40.60, 40.60,
        40.60, 40.60, 40.60, 40.60, 40.60, 40.90, 40.90, 40.90, 40.90, 40.90,
        40.90, 41.00, 41.00, 41.00, 41.00, 41.00, 41.00, 41.00, 41.00, 41.00,
        41.00
    ],
    # September 2025 (30 days: 01.09.2025 - 30.09.2025)
    '2025-09': [
        41.20, 41.20, 41.20, 41.20, 41.20, 41.20, 41.20, 41.20, 41.20, 41.20,
        41.20, 41.20, 41.20, 41.20, 41.50, 41.50, 41.70, 41.70, 41.70, 41.70,
        41.70, 41.70, 41.70, 41.70, 41.70, 41.70, 41.70, 41.70, 41.70, 41.70
    ],
    # October 2025 (31 days: 01.10.2025 - 31.10.2025)
    '2025-10': [
        41.70, 41.70, 41.70, 41.70, 41.70, 41.70, 41.70, 41.70, 41.70, 41.70,
        41.70, 41.70, 42.00, 42.00, 42.00, 42.00, 42.00, 42.00, 42.00, 42.00,
        42.00, 42.05, 42.05, 42.05, 42.05, 42.05, 42.05, 42.05, 42.05, 42.05,
        42.05
    ],
    # November 2025 (30 days: 01.11.2025 - 30.11.2025)
    '2025-11': [
        42.20, 42.20, 42.20, 42.20, 42.20, 42.20, 42.20, 42.20, 42.20, 42.20,
        42.20, 42.20, 42.20, 42.60, 42.60, 42.60, 42.60, 42.60, 42.60, 42.60,
        42.60, 42.60, 42.60, 42.60, 42.60, 42.60, 42.60, 42.60, 42.60, 42.60
    ],
    # December 2025 (31 days: 01.12.2025 - 31.12.2025)
    '2025-12': [
        42.20, 42.20, 42.20, 42.20, 42.20, 42.20, 42.20, 42.20, 42.62, 42.58,
        42.62, 42.64, 42.20, 42.71, 42.71, 42.71, 42.71, 42.75, 42.75, 42.75,
        42.75, 42.75, 42.75, 42.75, 42.75, 42.75, 42.75, 42.75, 42.75, 42.75,
        42.75
    ]
}


def generate_dates_for_month(year, month):
    """Generate all dates for a given month"""
    dates = []
    start_date = date(year, month, 1)
    
    # Get last day of month
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)
    
    return dates


def import_rates():
    """Import all USD rates into the database"""
    app = create_app()
    
    with app.app_context():
        rates_imported = 0
        rates_updated = 0
        
        for month_key, rates in RATES_DATA.items():
            year, month = map(int, month_key.split('-'))
            dates = generate_dates_for_month(year, month)
            
            if len(dates) != len(rates):
                logger.warning(f"Mismatch: {month_key} has {len(dates)} dates but {len(rates)} rates")
                # Use the minimum to avoid index errors
                count = min(len(dates), len(rates))
                dates = dates[:count]
                rates = rates[:count]
            
            for day_date, rate_value in zip(dates, rates):
                try:
                    rate_decimal = Decimal(str(rate_value))
                    
                    # Check if rate already exists
                    existing_rate = ExchangeRate.query.filter_by(date=day_date).first()
                    
                    if existing_rate:
                        # Force update existing rate (even if marked as manual)
                        existing_rate.usd_to_tl = rate_decimal
                        existing_rate.is_manual = True  # Mark as manual since these are provided rates
                        existing_rate.updated_at = datetime.now()
                        rates_updated += 1
                        logger.info(f"Updated rate for {day_date}: {rate_decimal} (forced update)")
                    else:
                        # Create new rate
                        new_rate = ExchangeRate()
                        new_rate.date = day_date
                        new_rate.usd_to_tl = rate_decimal
                        new_rate.is_manual = True
                        db.session.add(new_rate)
                        rates_imported += 1
                        logger.info(f"Created rate for {day_date}: {rate_decimal}")
                    
                except Exception as e:
                    logger.error(f"Error processing rate for {day_date}: {e}")
                    continue
        
        try:
            db.session.commit()
            logger.info(f"Successfully imported {rates_imported} new rates and updated {rates_updated} existing rates")
            return rates_imported + rates_updated
        except Exception as e:
            logger.error(f"Error committing rates to database: {e}")
            db.session.rollback()
            return 0


def update_transactions():
    """Update existing USD transactions to use the correct exchange rates"""
    app = create_app()
    
    with app.app_context():
        transactions_updated = 0
        transactions_skipped = 0
        
        # Get all USD transactions in the date range
        start_date = date(2025, 6, 1)
        end_date = date(2025, 12, 31)
        
        usd_transactions = Transaction.query.filter(
            Transaction.currency == 'USD',
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).all()
        
        logger.info(f"Found {len(usd_transactions)} USD transactions to update")
        
        for transaction in usd_transactions:
            try:
                # Get the exchange rate for this transaction's date
                exchange_rate = ExchangeRate.query.filter_by(date=transaction.date).first()
                
                if not exchange_rate or not exchange_rate.usd_to_tl:
                    logger.warning(f"No exchange rate found for {transaction.date}, skipping transaction {transaction.id}")
                    transactions_skipped += 1
                    continue
                
                rate = Decimal(str(exchange_rate.usd_to_tl))
                
                # Update transaction exchange rate
                transaction.exchange_rate = rate
                
                # Manually recalculate TRY amounts (similar to calculate_try_amounts but using config ExchangeRate)
                if transaction.currency == 'USD' and rate:
                    transaction.amount_try = abs(transaction.amount) * rate
                    transaction.commission_try = abs(transaction.commission) * rate if transaction.commission else Decimal('0')
                    transaction.net_amount_try = abs(transaction.net_amount) * rate
                    
                    # Handle withdrawal signs correctly
                    if transaction.category == 'WD':
                        transaction.amount_try = -transaction.amount_try
                        transaction.net_amount_try = -transaction.net_amount_try
                
                transactions_updated += 1
                
                if transactions_updated % 100 == 0:
                    logger.info(f"Updated {transactions_updated} transactions...")
                    
            except Exception as e:
                logger.error(f"Error updating transaction {transaction.id}: {e}")
                transactions_skipped += 1
                continue
        
        try:
            db.session.commit()
            logger.info(f"Successfully updated {transactions_updated} transactions, skipped {transactions_skipped}")
            return transactions_updated
        except Exception as e:
            logger.error(f"Error committing transaction updates: {e}")
            db.session.rollback()
            return 0


def main():
    """Main function to import rates and update transactions"""
    import sys
    
    # Check for --yes flag to skip confirmation
    skip_confirmation = '--yes' in sys.argv or '-y' in sys.argv
    
    print("=" * 60)
    print("USD Exchange Rate Import Script")
    print("=" * 60)
    print("\nThis script will:")
    print("1. Import USD exchange rates for June-December 2025")
    print("2. Update existing USD transactions with correct rates")
    print()
    
    if not skip_confirmation:
        response = input("Do you want to continue? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("Aborted.")
            return
    
    print("\nStep 1: Importing exchange rates...")
    rates_count = import_rates()
    if rates_count > 0:
        print(f"[OK] Imported/updated {rates_count} exchange rates")
    else:
        print("[WARNING] No rates were imported/updated")
    
    print("\nStep 2: Updating transactions...")
    transactions_count = update_transactions()
    if transactions_count > 0:
        print(f"[OK] Updated {transactions_count} transactions")
    else:
        print("[WARNING] No transactions were updated")
    
    print("\n" + "=" * 60)
    print("Script completed successfully!")
    print("=" * 60)


if __name__ == '__main__':
    main()

