"""
Historical Exchange Rate Service
Fetches historical USD/TRY exchange rates with enhanced fallback mechanisms
"""

import yfinance as yf
import pandas as pd
from datetime import date, datetime, timedelta
from decimal import Decimal
import logging
from typing import Dict, Optional, Tuple
import time

# Import enhanced exchange rate service
from .enhanced_exchange_rate_service import enhanced_exchange_service

logger = logging.getLogger(__name__)

class HistoricalExchangeService:
    """Service for fetching historical exchange rates from Yahoo Finance"""
    
    def __init__(self):
        self.cache = {}  # Simple in-memory cache
        self.cache_duration = 300  # 5 minutes cache
    
    def get_historical_rate(self, target_date: date, symbol: str = "USDTRY=X") -> float:
        """
        Get exchange rate for a specific date
        
        Args:
            target_date: Date to get rate for
            symbol: Yahoo Finance symbol (default: USDTRY=X)
            
        Returns:
            Exchange rate as float
        """
        try:
            # Check cache first
            cache_key = f"{symbol}_{target_date.isoformat()}"
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if time.time() - timestamp < self.cache_duration:
                    logger.debug(f"Using cached rate for {target_date}: {cached_data}")
                    return cached_data
            
            # Try enhanced exchange service first
            if symbol == "USDTRY=X":
                rate = enhanced_exchange_service.get_historical_rate(target_date, "USD", "TRY")
                if rate and rate > 0:
                    self.cache[cache_key] = (rate, time.time())
                    logger.debug(f"Enhanced service rate for {target_date}: {rate}")
                    return rate
            
            # Fallback to Yahoo Finance
            rate = self._fetch_rate_from_yfinance(target_date, symbol)
            
            # Cache the result
            self.cache[cache_key] = (rate, time.time())
            
            logger.debug(f"Fetched rate for {target_date}: {rate}")
            return rate
            
        except Exception as e:
            logger.error(f"Error fetching rate for {target_date}: {e}")
            # Return fallback rate
            return 48.0
    
    def get_historical_rates_range(self, start_date: date, end_date: date, symbol: str = "USDTRY=X") -> Dict[str, float]:
        """
        Get exchange rates for a date range
        
        Args:
            start_date: Start date
            end_date: End date
            symbol: Yahoo Finance symbol
            
        Returns:
            Dictionary with date strings as keys and rates as values
        """
        try:
            # Check if we have cached data for the entire range
            cache_key = f"{symbol}_{start_date.isoformat()}_{end_date.isoformat()}"
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if time.time() - timestamp < self.cache_duration:
                    logger.debug(f"Using cached rates for range {start_date} to {end_date}")
                    return cached_data
            
            # Fetch from Yahoo Finance
            rates = self._fetch_rates_range_from_yfinance(start_date, end_date, symbol)
            
            # Cache the result
            self.cache[cache_key] = (rates, time.time())
            
            logger.debug(f"Fetched {len(rates)} rates for range {start_date} to {end_date}")
            return rates
            
        except Exception as e:
            logger.error(f"Error fetching rates for range {start_date} to {end_date}: {e}")
            # Return fallback rates
            return self._generate_fallback_rates(start_date, end_date)
    
    def _fetch_rate_from_yfinance(self, target_date: date, symbol: str) -> float:
        """Fetch single rate from Yahoo Finance"""
        try:
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Get data for the specific date (with some buffer for weekends/holidays)
            start = target_date - timedelta(days=5)
            end = target_date + timedelta(days=2)
            
            # Fetch historical data
            hist = ticker.history(start=start, end=end, interval="1d")
            
            if hist.empty:
                logger.warning(f"No data found for {symbol} on {target_date}")
                return 48.0
            
            # Find the closest available date
            available_dates = hist.index.date
            closest_date = min(available_dates, key=lambda x: abs((x - target_date).days))
            
            # Get the closing price (exchange rate)
            rate = float(hist.loc[hist.index.date == closest_date, 'Close'].iloc[0])
            
            logger.debug(f"Found rate for {closest_date} (target: {target_date}): {rate}")
            return rate
            
        except Exception as e:
            logger.error(f"Error fetching rate from yfinance: {e}")
            return 48.0
    
    def _fetch_rates_range_from_yfinance(self, start_date: date, end_date: date, symbol: str) -> Dict[str, float]:
        """Fetch rates for a date range from Yahoo Finance"""
        try:
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Add buffer for weekends/holidays
            start = start_date - timedelta(days=2)
            end = end_date + timedelta(days=2)
            
            # Fetch historical data
            hist = ticker.history(start=start, end=end, interval="1d")
            
            if hist.empty:
                logger.warning(f"No data found for {symbol} from {start_date} to {end_date}")
                return self._generate_fallback_rates(start_date, end_date)
            
            # Convert to dictionary
            rates = {}
            for date_idx, row in hist.iterrows():
                date_str = date_idx.date().isoformat()
                rates[date_str] = float(row['Close'])
            
            logger.debug(f"Fetched {len(rates)} rates from yfinance")
            return rates
            
        except Exception as e:
            logger.error(f"Error fetching rates range from yfinance: {e}")
            return self._generate_fallback_rates(start_date, end_date)
    
    def _generate_fallback_rates(self, start_date: date, end_date: date) -> Dict[str, float]:
        """Generate fallback rates when yfinance fails"""
        rates = {}
        current_date = start_date
        fallback_rate = 48.0
        
        while current_date <= end_date:
            rates[current_date.isoformat()] = fallback_rate
            current_date += timedelta(days=1)
        
        logger.warning(f"Using fallback rates ({fallback_rate}) for range {start_date} to {end_date}")
        return rates
    
    def get_daily_rate(self, target_date: date) -> float:
        """Get rate for a specific day (for daily calculations)"""
        # PRIORITY 1: Check database for manual rates first
        try:
            from app import db
            from sqlalchemy import text
            
            # Find the most recent rate on or before the target date
            query = text("""
                SELECT rate FROM exchange_rates 
                WHERE currency_pair = 'USDTRY' 
                AND date <= :target_date 
                AND is_active = 1
                ORDER BY date DESC 
                LIMIT 1
            """)
            
            result = db.session.execute(query, {'target_date': target_date}).fetchone()
            
            if result and result[0]:
                rate = float(result[0])
                logger.debug(f"Found database rate for {target_date}: {rate}")
                return rate
        except Exception as e:
            logger.warning(f"Could not fetch rate from database for {target_date}: {e}")
        
        # PRIORITY 2: Fallback to Yahoo Finance
        return self.get_historical_rate(target_date)
    
    def get_monthly_average_rate(self, year: int, month: int) -> float:
        """Get average rate for a specific month (for monthly calculations)"""
        try:
            # Try enhanced service first
            rate = enhanced_exchange_service.get_monthly_average_rate(year, month, "USD", "TRY")
            if rate and rate > 0:
                logger.debug(f"Enhanced service monthly average for {year}-{month:02d}: {rate}")
                return rate
            
            # Fallback to original method
            # Get first and last day of month
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
            
            # Get rates for the month
            rates = self.get_historical_rates_range(start_date, end_date)
            
            if not rates:
                return 48.0
            
            # Calculate average
            rate_values = list(rates.values())
            average_rate = sum(rate_values) / len(rate_values)
            
            logger.debug(f"Monthly average rate for {year}-{month:02d}: {average_rate}")
            return average_rate
            
        except Exception as e:
            logger.error(f"Error calculating monthly average rate: {e}")
            return 48.0
    
    def clear_cache(self):
        """Clear the cache"""
        self.cache.clear()
        logger.info("Exchange rate cache cleared")

# Global instance
historical_exchange_service = HistoricalExchangeService()
