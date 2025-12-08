"""
Yahoo Finance Exchange Rate Service
Fetches USD/TRY exchange rates from Yahoo Finance
"""
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
import yfinance as yf
from app import db
from app.models.config import ExchangeRate

logger = logging.getLogger(__name__)


class YFinanceRateService:
    """Service for fetching exchange rates from Yahoo Finance"""
    
    # Yahoo Finance ticker for USD/TRY
    USDTRY_TICKER = "USDTRY=X"
    
    @staticmethod
    def fetch_rate_for_date(target_date: date) -> Decimal:
        """
        Fetch USD/TRY exchange rate for a specific date from Yahoo Finance
        
        Args:
            target_date: The date to fetch the rate for
            
        Returns:
            Decimal: The USD/TRY exchange rate, or None if not available
        """
        try:
            logger.info(f"Fetching USD/TRY rate from yfinance for date: {target_date}")
            
            # Download data for the specific date (with a buffer)
            # yfinance needs a date range, so we fetch from target_date to next day
            end_date = target_date + timedelta(days=1)
            start_date = target_date
            
            ticker = yf.Ticker(YFinanceRateService.USDTRY_TICKER)
            data = ticker.history(start=start_date, end=end_date)
            
            if data.empty:
                # If no data for exact date, try getting the most recent available
                logger.warning(f"No data found for {target_date}, trying previous days...")
                start_date = target_date - timedelta(days=7)  # Look back up to 7 days
                data = ticker.history(start=start_date, end=end_date)
                
                if not data.empty:
                    # Get the last available rate
                    close_price = data['Close'].iloc[-1]
                    rate = Decimal(str(round(close_price, 4)))
                    logger.info(f"Using closest available rate: {rate} from {data.index[-1].date()}")
                    return rate
                else:
                    logger.error(f"No USD/TRY rate found for {target_date} even with 7-day lookback")
                    return None
            
            # Get the closing price for the target date
            close_price = data['Close'].iloc[0]
            rate = Decimal(str(round(close_price, 4)))
            
            logger.info(f"Successfully fetched USD/TRY rate for {target_date}: {rate}")
            return rate
            
        except Exception as e:
            logger.error(f"Error fetching rate from yfinance for {target_date}: {e}")
            return None
    
    @staticmethod
    def fetch_current_rate() -> Decimal:
        """
        Fetch the current/latest USD/TRY exchange rate
        
        Returns:
            Decimal: The current USD/TRY exchange rate
        """
        try:
            logger.info("Fetching current USD/TRY rate from yfinance")
            
            ticker = yf.Ticker(YFinanceRateService.USDTRY_TICKER)
            
            # Get the most recent data (last 2 days to ensure we get something)
            data = ticker.history(period="2d")
            
            if data.empty:
                logger.error("No current USD/TRY rate available from yfinance")
                return None
            
            # Get the most recent closing price
            close_price = data['Close'].iloc[-1]
            rate = Decimal(str(round(close_price, 4)))
            
            logger.info(f"Current USD/TRY rate: {rate}")
            return rate
            
        except Exception as e:
            logger.error(f"Error fetching current rate from yfinance: {e}")
            return None
    
    @staticmethod
    def fetch_rate_range(start_date: date, end_date: date) -> dict:
        """
        Fetch USD/TRY exchange rates for a date range
        
        Args:
            start_date: Start date of the range
            end_date: End date of the range
            
        Returns:
            dict: Dictionary mapping dates to rates {date: rate}
        """
        try:
            logger.info(f"Fetching USD/TRY rates from yfinance for range: {start_date} to {end_date}")
            
            # Add one day to end_date for yfinance (exclusive end)
            fetch_end_date = end_date + timedelta(days=1)
            
            ticker = yf.Ticker(YFinanceRateService.USDTRY_TICKER)
            data = ticker.history(start=start_date, end=fetch_end_date)
            
            if data.empty:
                logger.error(f"No USD/TRY rates found for range {start_date} to {end_date}")
                return {}
            
            # Convert to dictionary of {date: rate}
            rates = {}
            for index, row in data.iterrows():
                rate_date = index.date()
                close_price = row['Close']
                rate = Decimal(str(round(close_price, 4)))
                rates[rate_date] = rate
            
            logger.info(f"Successfully fetched {len(rates)} rates for date range")
            return rates
            
        except Exception as e:
            logger.error(f"Error fetching rate range from yfinance: {e}")
            return {}
    
    @staticmethod
    def update_database_rate(target_date: date, rate: Decimal, source: str = 'yfinance', force_update: bool = False) -> bool:
        """
        Update or create an exchange rate in the database
        
        Args:
            target_date: The date for the rate
            rate: The USD/TRY exchange rate
            source: The source of the rate (default: 'yfinance') - for logging only
            force_update: If True, update even if rate is manual (default: False)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if rate already exists
            existing_rate = ExchangeRate.query.filter_by(date=target_date).first()
            
            if existing_rate:
                # Check if this is a manual rate and we're not forcing update
                # Only skip if trying to auto-update a manually set rate
                if existing_rate.is_manual and not force_update and source != 'manual':
                    logger.info(f"Skipping update for {target_date}: rate is manually set (current: {existing_rate.usd_to_tl})")
                    return True  # Return True because it's not an error, just skipped
                
                # Update existing rate
                existing_rate.usd_to_tl = rate
                existing_rate.updated_at = datetime.now()
                # Set is_manual flag based on source
                if source == 'manual':
                    existing_rate.is_manual = True
                elif source == 'yfinance' and not force_update:
                    existing_rate.is_manual = False
                logger.info(f"Updated existing rate for {target_date}: {rate} (source: {source}, is_manual: {existing_rate.is_manual})")
            else:
                # Create new rate
                new_rate = ExchangeRate()
                new_rate.date = target_date
                new_rate.usd_to_tl = rate
                new_rate.is_manual = (source == 'manual')  # Set is_manual if source is manual
                db.session.add(new_rate)
                logger.info(f"Created new rate for {target_date}: {rate} (source: {source})")
            
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error updating database rate for {target_date}: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def fetch_and_save_rate(target_date: date) -> Decimal:
        """
        Fetch rate from yfinance and save it to the database
        
        Args:
            target_date: The date to fetch the rate for
            
        Returns:
            Decimal: The fetched and saved rate, or None if failed
        """
        # Fetch from yfinance
        rate = YFinanceRateService.fetch_rate_for_date(target_date)
        
        if rate:
            # Save to database
            if YFinanceRateService.update_database_rate(target_date, rate):
                return rate
        
        return None
    
    @staticmethod
    def fetch_and_save_range(start_date: date, end_date: date) -> int:
        """
        Fetch rates for a date range and save them to the database
        
        Args:
            start_date: Start date of the range
            end_date: End date of the range
            
        Returns:
            int: Number of rates successfully saved
        """
        rates = YFinanceRateService.fetch_rate_range(start_date, end_date)
        
        saved_count = 0
        for rate_date, rate in rates.items():
            if YFinanceRateService.update_database_rate(rate_date, rate):
                saved_count += 1
        
        logger.info(f"Saved {saved_count} out of {len(rates)} rates to database")
        return saved_count
    
    @staticmethod
    def auto_fill_missing_rates(days_back: int = 30) -> int:
        """
        Automatically fetch and fill missing exchange rates for recent dates
        
        Args:
            days_back: Number of days to look back (default: 30)
            
        Returns:
            int: Number of missing rates filled
        """
        try:
            logger.info(f"Auto-filling missing rates for last {days_back} days")
            
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)
            
            # Get all rates from yfinance for the period
            rates = YFinanceRateService.fetch_rate_range(start_date, end_date)
            
            if not rates:
                logger.warning("No rates fetched from yfinance")
                return 0
            
            # Check which dates are missing in database
            filled_count = 0
            for rate_date in rates.keys():
                existing_rate = ExchangeRate.query.filter_by(date=rate_date).first()
                
                if not existing_rate:
                    # Missing rate - save it
                    if YFinanceRateService.update_database_rate(rate_date, rates[rate_date]):
                        filled_count += 1
                        logger.info(f"Filled missing rate for {rate_date}: {rates[rate_date]}")
            
            logger.info(f"Auto-filled {filled_count} missing rates")
            return filled_count
            
        except Exception as e:
            logger.error(f"Error in auto-fill missing rates: {e}")
            return 0

