"""
Data synchronization service to ensure PSP Track and Dashboard use transaction data
"""
from app import db
from app.models.transaction import Transaction
from app.models.financial import PspTrack
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging
import decimal

logger = logging.getLogger(__name__)

def safe_float(value, default=0.0):
    """Safely convert value to float, handling None and invalid values"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_decimal(value, default=Decimal('0')):
    """Safely convert value to Decimal, handling None and invalid values"""
    if value is None:
        return default
    try:
        return Decimal(str(value))
    except (ValueError, TypeError, decimal.InvalidOperation):
        return default

class DataSyncService:
    """Service to synchronize data between tables"""
    
    @staticmethod
    def sync_psp_track_from_transactions():
        """Sync PSP Track data from actual transactions, clearing old data first"""
        try:
            logger.info("Starting PSP Track sync from transactions...")
            
            # Ensure session is in a clean state
            try:
                db.session.rollback()
            except:
                pass  # Ignore if already rolled back
            
            # Get transaction count before sync
            transaction_count = Transaction.query.count()
            logger.info(f"Found {transaction_count} transactions to sync")
            
            # Clear all existing PSP Track data
            old_psp_count = PspTrack.query.count()
            PspTrack.query.delete()
            db.session.commit()
            logger.info(f"Cleared {old_psp_count} old PSP Track entries")

            # Get all transactions
            transactions = Transaction.query.all()
            
            # Group by date and PSP
            psp_data = {}
            skipped_negative = 0
            
            for transaction in transactions:
                # Skip negative amount transactions (refunds, chargebacks)
                if transaction.amount and safe_float(transaction.amount) < 0:
                    skipped_negative += 1
                    logger.warning(f"Skipping negative transaction {transaction.id}: {transaction.amount} TL")
                    continue
                    
                psp_name = transaction.psp or 'Unknown'
                key = (transaction.date, psp_name)
                
                if key not in psp_data:
                    psp_data[key] = {
                        'amount': Decimal('0'),
                        'commission_amount': Decimal('0'),
                        'difference': Decimal('0'),
                        'transaction_count': 0
                    }
                
                # Update totals using safe conversion
                safe_amount = safe_decimal(transaction.amount)
                safe_commission = safe_decimal(transaction.commission)
                
                psp_data[key]['amount'] += safe_amount
                psp_data[key]['commission_amount'] += safe_commission
                psp_data[key]['difference'] += (safe_amount - safe_commission)
                psp_data[key]['transaction_count'] += 1
            
            logger.info(f"Processed {len(transactions)} transactions into {len(psp_data)} PSP/date combinations")
            
            # Create new PSP Track entries
            for (date_obj, psp_name), data in psp_data.items():
                new_entry = PspTrack(
                    date=date_obj,
                    psp_name=psp_name,
                    amount=data['amount'],
                    commission_rate=Decimal('0.0'),
                    commission_amount=data['commission_amount'],
                    difference=data['difference']
                )
                db.session.add(new_entry)
            
            db.session.commit()
            logger.info(f"Successfully synced {len(psp_data)} PSP Track entries from transactions")
            if skipped_negative > 0:
                logger.info(f"Skipped {skipped_negative} negative transactions (refunds/chargebacks)")
            
            return True
            
        except Exception as e:
            logger.error(f"Error syncing PSP Track data: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            try:
                db.session.rollback()
            except:
                pass  # Ignore rollback errors
            return False
    
    @staticmethod
    def validate_data_consistency():
        """Validate that dashboard and PSP Track data are consistent"""
        try:
            # Get transaction totals
            transactions = Transaction.query.all()
            transaction_total = sum(t.amount for t in transactions)
            transaction_commission = sum(t.commission for t in transactions)
            
            # Get PSP Track totals
            psp_tracks = PspTrack.query.all()
            psp_total = sum(t.amount for t in psp_tracks)
            psp_commission = sum(t.commission_amount for t in psp_tracks)
            
            # Compare totals
            amount_diff = abs(transaction_total - psp_total)
            commission_diff = abs(transaction_commission - psp_commission)
            
            logger.info(f"Data consistency check:")
            logger.info(f"  Transaction total: {transaction_total}")
            logger.info(f"  PSP Track total: {psp_total}")
            logger.info(f"  Amount difference: {amount_diff}")
            logger.info(f"  Commission difference: {commission_diff}")
            
            return {
                'transaction_total': float(transaction_total),
                'psp_total': float(psp_total),
                'amount_difference': float(amount_diff),
                'commission_difference': float(commission_diff),
                'is_consistent': amount_diff < 0.01 and commission_diff < 0.01
            }
            
        except Exception as e:
            logger.error(f"Error validating data consistency: {str(e)}")
            return {'error': str(e)}