"""
Commission Rate Service for PipLine Treasury System
Handles time-based commission rate retrieval and management
"""
from datetime import date
from decimal import Decimal
from app.models.psp_commission_rate import PSPCommissionRate
from app.models.config import Option
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

class CommissionRateService:
    """Service for managing PSP commission rates"""
    
    # In-memory cache for commission rates (PSP + date -> rate)
    # Cache 1000 most recent rate lookups
    _rate_cache = {}
    
    @staticmethod
    def get_commission_rate(psp_name: str, target_date: date = None) -> Decimal:
        """
        Get commission rate for a PSP on a specific date (with caching)
        
        Args:
            psp_name: Name of the PSP
            target_date: Date to get rate for (defaults to today)
            
        Returns:
            Commission rate as decimal (0.15 = 15%)
        """
        if target_date is None:
            target_date = date.today()
        
        # Check cache first
        cache_key = f"{psp_name}:{target_date.isoformat()}"
        if cache_key in CommissionRateService._rate_cache:
            return CommissionRateService._rate_cache[cache_key]
        
        try:
            # First try the new time-based system
            rate = PSPCommissionRate.get_rate_for_date(psp_name, target_date)
            if rate > 0:
                logger.debug(f"Found time-based rate for {psp_name} on {target_date}: {rate}")
                # Cache the result
                CommissionRateService._rate_cache[cache_key] = rate
                # Limit cache size to prevent memory issues
                if len(CommissionRateService._rate_cache) > 1000:
                    # Remove oldest 200 entries
                    keys_to_remove = list(CommissionRateService._rate_cache.keys())[:200]
                    for key in keys_to_remove:
                        del CommissionRateService._rate_cache[key]
                return rate
        except Exception as e:
            logger.warning(f"Error getting time-based rate for {psp_name}: {e}")
        
        # Fallback to old system for backward compatibility
        try:
            from app.models.config import Option
            psp_option = Option.query.filter_by(
                field_name='psp',
                value=psp_name,
                is_active=True
            ).first()
            
            if psp_option and psp_option.commission_rate is not None:
                rate = psp_option.commission_rate
                logger.debug(f"Found legacy rate for {psp_name}: {rate}")
                # Cache the result
                CommissionRateService._rate_cache[cache_key] = rate
                return rate
        except Exception as e:
            logger.warning(f"Error getting legacy rate for {psp_name}: {e}")
        
        # No rate found - cache zero
        logger.warning(f"No commission rate found for {psp_name} on {target_date}")
        zero_rate = Decimal('0.0')
        CommissionRateService._rate_cache[cache_key] = zero_rate
        return zero_rate
    
    @staticmethod
    def get_commission_rate_percentage(psp_name: str, target_date: date = None) -> float:
        """
        Get commission rate as percentage for a PSP on a specific date
        
        Args:
            psp_name: Name of the PSP
            target_date: Date to get rate for (defaults to today)
            
        Returns:
            Commission rate as percentage (15.0 = 15%)
        """
        rate = CommissionRateService.get_commission_rate(psp_name, target_date)
        return float(rate * 100)
    
    @staticmethod
    def set_commission_rate(psp_name: str, new_rate: Decimal, effective_from: date, effective_until: date = None):
        """
        Set a new commission rate for a PSP
        
        Args:
            psp_name: Name of the PSP
            new_rate: New commission rate as decimal (0.15 = 15%)
            effective_from: When this rate becomes effective
            effective_until: When this rate expires (None = current)
        """
        try:
            rate_record = PSPCommissionRate.set_new_rate(
                psp_name=psp_name,
                new_rate=new_rate,
                effective_from=effective_from,
                effective_until=effective_until
            )
            logger.info(f"Set new commission rate for {psp_name}: {new_rate} from {effective_from}")
            
            # Clear cache for this PSP to force refresh
            CommissionRateService.clear_psp_cache(psp_name)
            
            return rate_record
        except Exception as e:
            logger.error(f"Error setting commission rate for {psp_name}: {e}")
            raise
    
    @staticmethod
    def clear_psp_cache(psp_name: str = None):
        """Clear cache for a specific PSP or all PSPs"""
        if psp_name:
            # Remove all cache entries for this PSP
            keys_to_remove = [k for k in CommissionRateService._rate_cache.keys() if k.startswith(f"{psp_name}:")]
            for key in keys_to_remove:
                del CommissionRateService._rate_cache[key]
            logger.info(f"Cleared commission rate cache for {psp_name}")
        else:
            # Clear entire cache
            CommissionRateService._rate_cache.clear()
            logger.info("Cleared entire commission rate cache")
    
    @staticmethod
    def get_rate_history(psp_name: str):
        """
        Get commission rate history for a PSP
        
        Args:
            psp_name: Name of the PSP
            
        Returns:
            List of rate records
        """
        try:
            return PSPCommissionRate.get_rate_history(psp_name)
        except Exception as e:
            logger.error(f"Error getting rate history for {psp_name}: {e}")
            return []
    
    @staticmethod
    def migrate_legacy_rates():
        """
        Migrate legacy commission rates to time-based system
        This should be run once during system upgrade
        """
        try:
            from app.models.config import Option
            
            # Get all PSP options with commission rates
            psp_options = Option.query.filter_by(
                field_name='psp', 
                is_active=True
            ).filter(Option.commission_rate.isnot(None)).all()
            
            migrated_count = 0
            for option in psp_options:
                # Check if already migrated
                existing = PSPCommissionRate.query.filter_by(psp_name=option.value).first()
                if existing:
                    continue
                
                # Create rate record
                effective_from = option.created_at.date() if option.created_at else date(2024, 1, 1)
                
                PSPCommissionRate(
                    psp_name=option.value,
                    commission_rate=option.commission_rate,
                    effective_from=effective_from,
                    effective_until=None,
                    is_active=True
                )
                migrated_count += 1
            
            logger.info(f"Migrated {migrated_count} legacy commission rates")
            return migrated_count
            
        except Exception as e:
            logger.error(f"Error migrating legacy rates: {e}")
            raise
