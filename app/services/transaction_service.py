"""
Transaction service for managing financial transactions
"""
from app import db
from app.models.transaction import Transaction
from app.models.financial import DailyBalance
from datetime import datetime, date
import logging
import pandas as pd
from decimal import Decimal

# Import enhanced exchange rate service (legacy service deprecated)
from app.services.enhanced_exchange_rate_service import enhanced_exchange_service as exchange_rate_service

# Import sync service if available
try:
    from app.services.data_sync_service import DataSyncService
    SYNC_AVAILABLE = True
except ImportError:
    SYNC_AVAILABLE = False

# Import PSP options service
from app.services.psp_options_service import PspOptionsService

# Import enhanced services
try:
    from app.services.event_service import event_service, EventType
    from app.services.enhanced_cache_service import cache_service
    ENHANCED_SERVICES_AVAILABLE = True
except ImportError:
    ENHANCED_SERVICES_AVAILABLE = False

logger = logging.getLogger(__name__)

def safe_float(value, default=0.0):
    """Safely convert value to float, handling None and invalid values"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

class TransactionService:
    """Service for managing transactions"""
    
    @staticmethod
    def create_transaction(data, user_id):
        """Create a new transaction with automatic exchange rate handling"""
        try:
            # Calculate commission if not provided
            if 'commission' not in data or data['commission'] is None:
                data['commission'] = TransactionService.calculate_commission(
                    data['amount'], data.get('psp'), data.get('category')
                )
            
            # Calculate net amount
            data['net_amount'] = data['amount'] - data['commission']
            
            # Create transaction
            transaction = Transaction(
                client_name=data['client_name'],
                amount=data['amount'],
                date=data['date'],
                currency=data.get('currency', 'TL'),
                psp=data.get('psp', ''),
                category=data.get('category', ''),
                payment_method=data.get('payment_method', ''),
                commission=data['commission'],
                net_amount=data['net_amount'],
                notes=data.get('notes', ''),
                created_by=user_id
            )
            
            # Handle exchange rate for foreign currency transactions
            if transaction.currency in ['USD', 'EUR']:
                try:
                    # Fetch exchange rate from yfinance
                    exchange_rate = exchange_rate_service.get_or_fetch_rate(
                        transaction.currency, transaction.date
                    )
                    
                    if exchange_rate:
                        # Calculate TL amounts
                        transaction.calculate_try_amounts(exchange_rate)
                        logger.info(f"Successfully calculated TL amounts for {transaction.currency} transaction using rate {exchange_rate}")
                    else:
                        logger.warning(f"Failed to fetch exchange rate for {transaction.currency} on {transaction.date}")
                        # Set TL amounts to None to indicate missing rate
                        transaction.amount_try = None
                        transaction.commission_try = None
                        transaction.net_amount_try = None
                        transaction.exchange_rate = None
                        
                except Exception as rate_error:
                    logger.error(f"Error handling exchange rate for transaction: {rate_error}")
                    # Set TL amounts to None to indicate error
                    transaction.amount_try = None
                    transaction.commission_try = None
                    transaction.net_amount_try = None
                    transaction.exchange_rate = None
            else:
                # For TL transactions, TL amounts are the same as original amounts
                transaction.calculate_try_amounts(Decimal('1.0'))
            
            db.session.add(transaction)
            db.session.commit()
            
            # Publish event for real-time updates
            if ENHANCED_SERVICES_AVAILABLE:
                try:
                    event_service.publish_event(
                        EventType.TRANSACTION_CREATED,
                        {
                            'transaction_id': transaction.id,
                            'client_name': transaction.client_name,
                            'amount': float(transaction.amount),
                            'currency': transaction.currency,
                            'psp': transaction.psp,
                            'category': transaction.category,
                            'user_id': user_id
                        },
                        source='transaction_service'
                    )
                except Exception as event_error:
                    logger.warning(f"Event publishing failed: {event_error}")
            
            # Update daily balance
            TransactionService.update_daily_balance(data['date'], data.get('psp', ''))
            
            # Sync PSP Track if available
            if SYNC_AVAILABLE:
                try:
                    DataSyncService.sync_psp_track_from_transactions()
                except Exception as sync_error:
                    logger.warning(f'PSP Track sync failed after transaction creation: {sync_error}')
            
            # Invalidate relevant caches after transaction creation
            if ENHANCED_SERVICES_AVAILABLE:
                try:
                    cache_service.invalidate_transaction_cache(transaction.id)
                    logger.info("Cache invalidated after transaction creation")
                except Exception as cache_error:
                    logger.warning(f"Cache invalidation failed: {cache_error}")
            else:
                try:
                    from app.services.query_service import QueryService
                    QueryService.invalidate_transaction_cache()
                    logger.info("Cache invalidated after transaction creation")
                except Exception as cache_error:
                    logger.warning(f"Failed to invalidate cache after transaction creation: {cache_error}")
            
            return transaction
            
        except Exception as e:
            logger.error(f'Error creating transaction: {e}')
            db.session.rollback()
            raise

    @staticmethod
    def update_transaction(transaction_id, data, user_id):
        """Update an existing transaction with automatic exchange rate handling"""
        try:
            transaction = Transaction.query.get(transaction_id)
            if not transaction:
                raise ValueError('Transaction not found')
            
            # Store original currency for comparison
            original_currency = transaction.currency
            
            # Update fields
            for key, value in data.items():
                if hasattr(transaction, key):
                    setattr(transaction, key, value)
            
            # Recalculate commission and net amount if amount changed
            if 'amount' in data:
                transaction.commission = TransactionService.calculate_commission(
                    data['amount'], data.get('psp', transaction.psp), data.get('category', transaction.category)
                )
                transaction.net_amount = data['amount'] - transaction.commission
            
            # Handle exchange rate if currency changed or is foreign currency
            if transaction.currency in ['USD', 'EUR']:
                try:
                    # Fetch exchange rate from yfinance
                    exchange_rate = exchange_rate_service.get_or_fetch_rate(
                        transaction.currency, transaction.date
                    )
                    
                    if exchange_rate:
                        # Calculate TL amounts
                        transaction.calculate_try_amounts(exchange_rate)
                        logger.info(f"Successfully updated TL amounts for {transaction.currency} transaction using rate {exchange_rate}")
                    else:
                        logger.warning(f"Failed to fetch exchange rate for {transaction.currency} on {transaction.date}")
                        # Set TL amounts to None to indicate missing rate
                        transaction.amount_try = None
                        transaction.commission_try = None
                        transaction.net_amount_try = None
                        transaction.exchange_rate = None
                        
                except Exception as rate_error:
                    logger.error(f"Error handling exchange rate for transaction update: {rate_error}")
                    # Set TL amounts to None to indicate error
                    transaction.amount_try = None
                    transaction.net_amount_try = None
                    transaction.exchange_rate = None
            else:
                # For TL transactions, TL amounts are the same as original amounts
                transaction.calculate_try_amounts(Decimal('1.0'))
            
            transaction.updated_at = datetime.now()
            db.session.commit()
            
            # Update daily balance
            TransactionService.update_daily_balance(transaction.date, transaction.psp)
            
            # Sync PSP Track if available
            if SYNC_AVAILABLE:
                try:
                    DataSyncService.sync_psp_track_from_transactions()
                except Exception as sync_error:
                    logger.warning(f'PSP Track sync failed after transaction update: {sync_error}')
            
            # Invalidate relevant caches after transaction update
            try:
                from app.services.query_service import QueryService
                QueryService.invalidate_transaction_cache()
                logger.info("Cache invalidated after transaction update")
            except Exception as cache_error:
                logger.warning(f"Failed to invalidate cache after transaction update: {cache_error}")
            
            return transaction
            
        except Exception as e:
            logger.error(f'Error updating transaction: {e}')
            db.session.rollback()
            raise

    @staticmethod
    def delete_transaction(transaction_id, user_id):
        """Delete a transaction"""
        try:
            transaction = Transaction.query.get(transaction_id)
            if not transaction:
                raise ValueError('Transaction not found')
            
            # Store date and PSP for balance update (handle None PSP)
            date_obj = transaction.date
            psp = transaction.psp if transaction.psp else ''
            
            logger.info(f"Deleting transaction {transaction_id} - Date: {date_obj}, PSP: {psp or 'N/A'}")
            
            db.session.delete(transaction)
            db.session.commit()
            
            # Update daily balance (this may fail but shouldn't prevent deletion)
            try:
                TransactionService.update_daily_balance(date_obj, psp)
            except Exception as balance_error:
                logger.warning(f'Failed to update daily balance after deletion: {balance_error}')
                # Don't raise - deletion was successful, balance update is secondary
            
            # Sync PSP Track if available
            if SYNC_AVAILABLE:
                try:
                    DataSyncService.sync_psp_track_from_transactions()
                except Exception as sync_error:
                    logger.warning(f'PSP Track sync failed after transaction deletion: {sync_error}')
            
            # Invalidate relevant caches after transaction deletion
            try:
                from app.services.query_service import QueryService
                QueryService.invalidate_transaction_cache()
                logger.info("Cache invalidated after transaction deletion")
            except Exception as cache_error:
                logger.warning(f"Failed to invalidate cache after transaction deletion: {cache_error}")
            
            return True
            
        except Exception as e:
            logger.error(f'Error deleting transaction {transaction_id}: {e}', exc_info=True)
            db.session.rollback()
            raise

    @staticmethod
    def calculate_commission(amount, psp=None, category=None):
        """Calculate commission based on PSP and category"""
        # IMPORTANT: WD (Withdraw) transactions have ZERO commission
        # Company doesn't pay commissions for withdrawals
        if category and category.upper() == 'WD':
            return Decimal('0')
        
        # Get commission rate from PSP service for DEP transactions
        try:
            if psp:
                commission_rate = PspOptionsService.get_psp_commission_rate(psp)
                commission = amount * commission_rate
                return round(commission, 2)
        except Exception as e:
            logger.warning(f"Error getting PSP commission rate: {e}")
        
        # Default commission rate of 2.5% for DEP transactions if no PSP rate found
        default_rate = Decimal('0.025')
        commission = amount * default_rate
        return round(commission, 2)

    @staticmethod
    def calculate_commission_based_on_total_deposits(psp_deposits, psp_name):
        """Calculate commission based on total deposits for a PSP (for ledger display)"""
        try:
            if not psp_deposits or psp_deposits <= 0:
                return Decimal('0')
            
            # Get commission rate from PSP service
            commission_rate = PspOptionsService.get_psp_commission_rate(psp_name)
            commission = psp_deposits * commission_rate
            return round(commission, 2)
        except Exception as e:
            logger.warning(f"Error calculating commission for PSP '{psp_name}': {e}")
            # Default commission rate of 2.5% if no PSP rate found
            default_rate = Decimal('0.025')
            commission = psp_deposits * default_rate
            return round(commission, 2)

    @staticmethod
    def get_exchange_rate(date_obj, currency='USD'):
        """Get exchange rate for a specific date and currency"""
        try:
            return exchange_rate_service.get_or_fetch_rate(currency, date_obj)
        except Exception as e:
            logger.error(f"Error getting exchange rate: {str(e)}")
            return None

    @staticmethod
    def update_daily_balance(date_obj, psp):
        """Update daily balance for a specific date and PSP"""
        try:
            # Handle None or empty PSP values
            if psp is None:
                psp = ''
            
            # Normalize PSP to string
            psp = str(psp) if psp else ''
            
            # Get all transactions for the date and PSP
            # Use filter with proper None handling
            if psp:
                transactions = Transaction.query.filter_by(date=date_obj, psp=psp).all()
            else:
                # Handle None/empty PSP - filter for transactions where PSP is None or empty
                from sqlalchemy import or_
                transactions = Transaction.query.filter(
                    Transaction.date == date_obj,
                    or_(Transaction.psp.is_(None), Transaction.psp == '')
                ).all()
            
            # Calculate totals
            total_inflow = sum(t.amount for t in transactions if t.category == 'DEP')
            total_outflow = sum(t.amount for t in transactions if t.category == 'WD')
            total_commission = sum(t.commission for t in transactions)
            net_amount = total_inflow - total_outflow - total_commission
            
            # Update or create daily balance
            if psp:
                daily_balance = DailyBalance.query.filter_by(date=date_obj, psp=psp).first()
            else:
                daily_balance = DailyBalance.query.filter_by(date=date_obj, psp='').first()
            
            if daily_balance:
                daily_balance.total_inflow = total_inflow
                daily_balance.total_outflow = total_outflow
                daily_balance.total_commission = total_commission
                daily_balance.net_amount = net_amount
                daily_balance.updated_at = datetime.now()
            else:
                daily_balance = DailyBalance(
                    date=date_obj,
                    psp=psp or '',  # Ensure PSP is not None
                    total_inflow=total_inflow,
                    total_outflow=total_outflow,
                    total_commission=total_commission,
                    net_amount=net_amount
                )
                db.session.add(daily_balance)
            
            db.session.commit()
            logger.info(f"Updated daily balance for {date_obj} - PSP: {psp or 'N/A'}, Net: {net_amount}")
            
        except Exception as e:
            logger.error(f'Error updating daily balance: {e}', exc_info=True)
            db.session.rollback()

    @staticmethod
    def import_transactions(file_data, user_id):
        """Import transactions from file"""
        try:
            # Read file data
            df = pd.read_excel(file_data) if file_data.endswith('.xlsx') else pd.read_csv(file_data)
            
            imported_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Prepare transaction data
                    transaction_data = {
                        'client_name': row.get('client_name', ''),
                        'amount': safe_float(row.get('amount', 0)),
                        'date': pd.to_datetime(row.get('date')).date(),
                        'currency': row.get('currency', 'TL'),
                        'psp': row.get('psp', ''),
                        'category': row.get('category', ''),
                        'payment_method': row.get('payment_method', ''),
                        'notes': row.get('notes', '')
                    }
                    
                    # Create transaction
                    TransactionService.create_transaction(transaction_data, user_id)
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
            
            return {
                'imported_count': imported_count,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f'Error importing transactions: {e}')
            raise

    @staticmethod
    def export_transactions(filters=None):
        """Export transactions with optional filters"""
        try:
            query = Transaction.query
            
            if filters:
                if filters.get('start_date'):
                    query = query.filter(Transaction.date >= filters['start_date'])
                if filters.get('end_date'):
                    query = query.filter(Transaction.date <= filters['end_date'])
                if filters.get('psp'):
                    query = query.filter(Transaction.psp == filters['psp'])
                if filters.get('category'):
                    query = query.filter(Transaction.category == filters['category'])
            
            transactions = query.all()
            
            # Convert to list of dictionaries
            export_data = []
            for transaction in transactions:
                export_data.append(transaction.to_dict())
            
            return export_data
            
        except Exception as e:
            logger.error(f'Error exporting transactions: {e}')
            raise

    @staticmethod
    def backfill_existing_transactions():
        """Backfill TL amounts for existing USD/EUR transactions and commissions for WD transactions"""
        try:
            # Get all USD and EUR transactions without TL amounts
            usd_eur_transactions = Transaction.query.filter(
                Transaction.currency.in_(['USD', 'EUR']),
                (Transaction.amount_try.is_(None) | Transaction.commission_try.is_(None) | Transaction.net_amount_try.is_(None))
            ).all()
            
            # Get all WD transactions with zero commission
            wd_transactions = Transaction.query.filter(
                Transaction.category == 'WD',
                (Transaction.commission == 0 or Transaction.commission == Decimal('0'))
            ).all()
            
            # Combine both lists
            transactions = usd_eur_transactions + wd_transactions
            
            updated_count = 0
            error_count = 0
            
            for transaction in transactions:
                try:
                    # Handle USD/EUR transactions (TL amounts)
                    if transaction.currency in ['USD', 'EUR']:
                        # Fetch exchange rate
                        exchange_rate = exchange_rate_service.get_or_fetch_rate(
                            transaction.currency, transaction.date
                        )
                        
                        if exchange_rate:
                            # Calculate TL amounts
                            transaction.calculate_try_amounts(exchange_rate)
                            updated_count += 1
                            logger.info(f"Backfilled TL amounts for transaction {transaction.id}")
                        else:
                            error_count += 1
                            logger.warning(f"Failed to fetch rate for transaction {transaction.id}")
                    
                    # Handle WD transactions (commissions)
                    if transaction.category == 'WD' and (transaction.commission == 0 or transaction.commission == Decimal('0')):
                        try:
                            from app.models.config import Option
                            psp_option = Option.query.filter_by(
                                field_name='psp',
                                value=transaction.psp,
                                is_active=True
                            ).first()
                            
                            # WD transactions always have 0 commission
                            commission = Decimal('0')
                            logger.info(f"WD transaction - setting commission to 0 for amount: {transaction.amount}")
                            
                            logger.info(f"Before update - Transaction {transaction.id}: commission={transaction.commission}, net_amount={transaction.net_amount}")
                            
                            transaction.commission = commission
                            transaction.net_amount = transaction.amount - commission
                            
                            logger.info(f"After update - Transaction {transaction.id}: commission={transaction.commission}, net_amount={transaction.net_amount}")
                            
                            updated_count += 1
                            logger.info(f"Backfilled commission for WD transaction {transaction.id}: {commission}")
                        except Exception as e:
                            logger.warning(f"Failed to backfill commission for transaction {transaction.id}: {e}")
                
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error backfilling transaction {transaction.id}: {e}")
            
            db.session.commit()
            
            logger.info(f"Backfill completed: {updated_count} updated, {error_count} errors")
            return {
                'updated_count': updated_count,
                'error_count': error_count
            }
            
        except Exception as e:
            logger.error(f"Error in backfill: {e}")
            db.session.rollback()
            raise 