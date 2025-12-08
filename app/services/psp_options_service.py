"""
PSP Options Service
Handles fixed PSP options from database transactions
"""
import logging
from typing import List, Dict, Any
from decimal import Decimal
from app import db
from app.models.config import Option
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)

# Prevent duplicate logging by tracking logged operations
_logged_operations = set()

class PspOptionsService:
    """Service for managing fixed PSP options"""
    
    @staticmethod
    def get_psps_from_database() -> List[str]:
        """Get all unique PSPs from transaction database and option table"""
        try:
            # Get distinct PSPs from transactions
            psp_results = db.session.query(Transaction.psp).distinct().filter(
                Transaction.psp.isnot(None),
                Transaction.psp != ''
            ).order_by(Transaction.psp).all()
            
            transaction_psps = [result[0] for result in psp_results]
            
            # Get PSPs from option table (for historical data)
            option_results = db.session.query(Option.value).filter(
                Option.field_name == 'psp',
                Option.is_active == True
            ).distinct().order_by(Option.value).all()
            
            option_psps = [result[0] for result in option_results]
            
            # Combine and deduplicate
            all_psps = list(set(transaction_psps + option_psps))
            all_psps.sort()
            
            # Log only once per unique result set
            result_key = f"psps_{len(transaction_psps)}_{len(option_psps)}_{len(all_psps)}"
            if result_key not in _logged_operations:
                logger.info(f"Found {len(transaction_psps)} PSPs in transaction table: {transaction_psps}")
                logger.info(f"Found {len(option_psps)} PSPs in option table: {option_psps}")
                logger.info(f"Found {len(all_psps)} unique PSPs total: {all_psps}")
                _logged_operations.add(result_key)
            
            return all_psps
            
        except Exception as e:
            logger.error(f"Error getting PSPs from database: {e}")
            return []
    
    @staticmethod
    def create_fixed_psp_options() -> List[Dict[str, Any]]:
        """Create fixed PSP options with default commission rates"""
        psps = PspOptionsService.get_psps_from_database()
        
        # Remove duplicates while preserving order
        unique_psps = []
        seen = set()
        for psp in psps:
            if psp not in seen:
                unique_psps.append(psp)
                seen.add(psp)
        
        # Default commission rates for common PSPs (fallback only)
        default_rates = {
            'stripe': Decimal('0.029'),  # 2.9%
            'paypal': Decimal('0.034'),  # 3.4%
            'square': Decimal('0.026'),  # 2.6%
            'adyen': Decimal('0.025'),   # 2.5%
            'worldpay': Decimal('0.035'), # 3.5%
            'braintree': Decimal('0.029'), # 2.9%
            'authorize.net': Decimal('0.029'), # 2.9%
            'bank': Decimal('0.0'),      # 0% for bank transfers
            'cash': Decimal('0.0'),      # 0% for cash
            'crypto': Decimal('0.01'),   # 1% for crypto
            'wire': Decimal('0.0'),      # 0% for wire transfers
            # Business PSPs with specified rates
            '#60 cashpay': Decimal('0.08'),   # 8.0%
            '#61 cryppay': Decimal('0.075'),  # 7.5%
            '#62 cryppay': Decimal('0.075'),  # 7.5% - New PSP
            'atatp': Decimal('0.08'),         # 8.0%
            'cpo': Decimal('0.05'),           # 5.0%
            'cpo py kk': Decimal('0.11'),     # 11.0%
            'filbox kk': Decimal('0.12'),     # 12.0%
            'kuyumcu': Decimal('0.12'),       # 12.0%
            'sipay': Decimal('0.0015'),       # 0.15% - Updated rate
            'sipay-15': Decimal('0.0015'),    # 0.15% - Updated rate
            'tether': Decimal('0.0'),         # 0.0% - Company's internal KASA in USD
        }
        
        fixed_options = []
        for psp in unique_psps:
            # First try to get rate from database
            db_option = Option.query.filter_by(
                field_name='psp',
                value=psp,
                is_active=True
            ).first()
            
            if db_option and db_option.commission_rate is not None:
                commission_rate = db_option.commission_rate
            else:
                # Fallback to default rate based on PSP name
                psp_lower = psp.lower().strip()
                commission_rate = default_rates.get(psp_lower, Decimal('0.025'))  # Default 2.5%
            
            # Log commission rate only once per PSP
            rate_key = f"rate_{psp}_{commission_rate}"
            if rate_key not in _logged_operations:
                logger.info(f"Using default commission rate for '{psp}': {commission_rate}")
                _logged_operations.add(rate_key)
            
            fixed_options.append({
                'value': psp,
                'commission_rate': float(commission_rate),
                'is_fixed': True
            })
        
        # Log creation only once
        creation_key = f"created_psps_{len(fixed_options)}"
        if creation_key not in _logged_operations:
            logger.info(f"Created {len(fixed_options)} unique fixed PSP options")
            _logged_operations.add(creation_key)
        
        return fixed_options
    
    @staticmethod
    def get_psp_commission_rate(psp: str) -> Decimal:
        """Get commission rate for a specific PSP"""
        try:
            # First try to get rate from database
            db_option = Option.query.filter_by(
                field_name='psp',
                value=psp,
                is_active=True
            ).first()
            
            if db_option and db_option.commission_rate is not None:
                return db_option.commission_rate
            
            # Fallback to default rates
            default_rates = {
                'stripe': Decimal('0.029'),
                'paypal': Decimal('0.034'),
                'square': Decimal('0.026'),
                'adyen': Decimal('0.025'),
                'worldpay': Decimal('0.035'),
                'braintree': Decimal('0.029'),
                'authorize.net': Decimal('0.029'),
                'bank': Decimal('0.0'),
                'cash': Decimal('0.0'),
                'crypto': Decimal('0.01'),
                'wire': Decimal('0.0'),
                # Business PSPs with specified rates
                '#60 cashpay': Decimal('0.08'),   # 8.0%
                '#61 cryppay': Decimal('0.075'),  # 7.5%
                '#62 cryppay': Decimal('0.075'),  # 7.5% - New PSP
                'atatp': Decimal('0.08'),         # 8.0%
                'cpo': Decimal('0.05'),           # 5.0%
                'cpo py kk': Decimal('0.11'),     # 11.0%
                'filbox kk': Decimal('0.12'),     # 12.0%
                'kuyumcu': Decimal('0.12'),       # 12.0%
                'sipay': Decimal('0.0015'),       # 0.15% - Updated rate
                'sipay-15': Decimal('0.0015'),    # 0.15% - Updated rate
                'tether': Decimal('0.0'),         # 0.0% - Company's internal KASA in USD
            }
            
            psp_lower = psp.lower().strip()
            return default_rates.get(psp_lower, Decimal('0.025'))
            
        except Exception as e:
            logger.error(f"Error getting commission rate for PSP '{psp}': {e}")
            return Decimal('0.025')  # Default 2.5%
    
    @staticmethod
    def ensure_psp_options_exist():
        """Ensure PSP options exist in the database with proper commission rates"""
        try:
            psps = PspOptionsService.get_psps_from_database()
            
            for psp in psps:
                # Check if PSP option already exists
                existing_option = Option.query.filter_by(
                    field_name='psp', 
                    value=psp, 
                    is_active=True
                ).first()
                
                if not existing_option:
                    # Create new PSP option with default commission rate
                    commission_rate = PspOptionsService.get_psp_commission_rate(psp)
                    
                    new_option = Option(
                        field_name='psp',
                        value=psp,
                        commission_rate=commission_rate,
                        is_active=True
                    )
                    
                    db.session.add(new_option)
                    logger.info(f"Created PSP option: {psp} with rate {commission_rate}")
            
            db.session.commit()
            logger.info("PSP options ensured in database")
            
        except Exception as e:
            logger.error(f"Error ensuring PSP options: {e}")
            db.session.rollback()
