"""
Exchange Rate Model
Stores currency exchange rates with timestamps for historical tracking
"""

from datetime import datetime, timezone, date
from decimal import Decimal
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Boolean, Index, Date
from app import db


class ExchangeRate(db.Model):
    """
    Exchange Rate Model for storing currency conversion rates
    
    Stores USD/TRY exchange rates with timestamps for:
    - Real-time rate updates from yfinance
    - Historical rate tracking
    - Transaction conversion calculations
    """
    
    __tablename__ = 'exchange_rates'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Date for this rate (can be nullable for compatibility)
    date = Column(Date, nullable=True)
    
    # Currency pair (e.g., 'USDTRY')
    currency_pair = Column(String(10), nullable=False, index=True)
    
    # Exchange rate (USD to TRY)
    rate = Column(Numeric(precision=10, scale=4), nullable=False)
    
    # Source of the rate (e.g., 'yfinance', 'manual', 'fallback')
    source = Column(String(50), nullable=False, default='yfinance')
    
    # Manual override fields (for compatibility with existing table)
    is_manual_override = Column(Boolean, nullable=False, default=False)
    override_reason = Column(String(200), nullable=True)
    data_quality = Column(String(50), nullable=False, default='closing_price')
    
    # Timestamp when rate was fetched/created
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Whether this is the current active rate
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Additional metadata
    bid_price = Column(Numeric(precision=10, scale=4), nullable=True)  # Buy price
    ask_price = Column(Numeric(precision=10, scale=4), nullable=True)  # Sell price
    volume = Column(Numeric(precision=15, scale=2), nullable=True)     # Trading volume
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_currency_pair_created', 'currency_pair', 'created_at'),
        Index('idx_currency_pair_active', 'currency_pair', 'is_active'),
        Index('idx_created_at', 'created_at'),
    )
    
    def __init__(self, currency_pair, rate, source='yfinance', is_active=True, 
                 bid_price=None, ask_price=None, volume=None, date_value=None):
        """
        Initialize ExchangeRate instance
        
        Args:
            currency_pair (str): Currency pair code (e.g., 'USDTRY')
            rate (Decimal): Exchange rate value
            source (str): Source of the rate data
            is_active (bool): Whether this is the current active rate
            bid_price (Decimal, optional): Bid price
            ask_price (Decimal, optional): Ask price
            volume (Decimal, optional): Trading volume
            date_value (date, optional): Date for this rate (defaults to today)
        """
        self.currency_pair = currency_pair
        self.rate = Decimal(str(rate))
        self.source = source
        self.is_active = is_active
        self.bid_price = Decimal(str(bid_price)) if bid_price else None
        self.ask_price = Decimal(str(ask_price)) if ask_price else None
        self.volume = Decimal(str(volume)) if volume else None
        self.date = date_value or date.today()
        self.is_manual_override = False
        self.data_quality = 'closing_price'
        self.created_at = datetime.now(timezone.utc)
    
    def __repr__(self):
        return f'<ExchangeRate {self.currency_pair}: {self.rate} ({self.source}, {self.created_at})>'
    
    def to_dict(self):
        """Convert ExchangeRate to dictionary for API responses"""
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'currency_pair': self.currency_pair,
            'rate': float(self.rate),
            'source': self.source,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active,
            'bid_price': float(self.bid_price) if self.bid_price else None,
            'ask_price': float(self.ask_price) if self.ask_price else None,
            'volume': float(self.volume) if self.volume else None,
            'is_manual_override': self.is_manual_override,
            'data_quality': self.data_quality,
        }
    
    @classmethod
    def get_current_rate(cls, currency_pair='USDTRY'):
        """
        Get the current active exchange rate for a currency pair
        
        Args:
            currency_pair (str): Currency pair code (default: 'USDTRY')
            
        Returns:
            ExchangeRate: Current active rate or None if not found
        """
        return cls.query.filter_by(
            currency_pair=currency_pair,
            is_active=True
        ).order_by(cls.created_at.desc()).first()
    
    @classmethod
    def get_rate_at_date(cls, date, currency_pair='USDTRY'):
        """
        Get the exchange rate for a specific date
        
        Args:
            date (datetime): Target date
            currency_pair (str): Currency pair code (default: 'USDTRY')
            
        Returns:
            ExchangeRate: Rate closest to the target date or None if not found
        """
        return cls.query.filter(
            cls.currency_pair == currency_pair,
            cls.created_at <= date
        ).order_by(cls.created_at.desc()).first()
    
    @classmethod
    def get_rate_history(cls, currency_pair='USDTRY', limit=100):
        """
        Get historical exchange rates for a currency pair
        
        Args:
            currency_pair (str): Currency pair code (default: 'USDTRY')
            limit (int): Number of records to return (default: 100)
            
        Returns:
            List[ExchangeRate]: Historical rates ordered by date (newest first)
        """
        return cls.query.filter_by(
            currency_pair=currency_pair
        ).order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def deactivate_old_rates(cls, currency_pair='USDTRY'):
        """
        Deactivate all old rates for a currency pair
        Used when setting a new active rate
        
        Args:
            currency_pair (str): Currency pair code (default: 'USDTRY')
        """
        cls.query.filter_by(
            currency_pair=currency_pair,
            is_active=True
        ).update({'is_active': False})
    
    @classmethod
    def create_new_rate(cls, rate, currency_pair='USDTRY', source='yfinance', 
                       bid_price=None, ask_price=None, volume=None):
        """
        Create a new exchange rate and deactivate old ones
        
        Args:
            rate (Decimal): New exchange rate
            currency_pair (str): Currency pair code (default: 'USDTRY')
            source (str): Source of the rate data (default: 'yfinance')
            bid_price (Decimal, optional): Bid price
            ask_price (Decimal, optional): Ask price
            volume (Decimal, optional): Trading volume
            
        Returns:
            ExchangeRate: Newly created rate instance
        """
        from app import db
        
        # Deactivate old rates
        cls.deactivate_old_rates(currency_pair)
        
        # Create new active rate
        new_rate = cls(
            currency_pair=currency_pair,
            rate=rate,
            source=source,
            is_active=True,
            bid_price=bid_price,
            ask_price=ask_price,
            volume=volume
        )
        
        db.session.add(new_rate)
        db.session.commit()
        
        return new_rate
    
    def convert_amount(self, amount_usd):
        """
        Convert USD amount to TRY using this exchange rate
        
        Args:
            amount_usd (Decimal): Amount in USD
            
        Returns:
            Decimal: Amount in TRY
        """
        return Decimal(str(amount_usd)) * self.rate
    
    def age_in_minutes(self):
        """
        Get the age of this rate in minutes
        
        Returns:
            int: Age in minutes
        """
        now = datetime.now(timezone.utc)
        
        # Ensure both datetimes have the same timezone awareness
        if self.created_at.tzinfo is None:
            # If created_at is naive, assume it's UTC
            created_at_utc = self.created_at.replace(tzinfo=timezone.utc)
        else:
            # If created_at is aware, convert to UTC
            created_at_utc = self.created_at.astimezone(timezone.utc)
        
        delta = now - created_at_utc
        return int(delta.total_seconds() / 60)
    
    def is_stale(self, max_age_minutes=15):
        """
        Check if this rate is stale (older than max_age_minutes)
        
        Args:
            max_age_minutes (int): Maximum age in minutes (default: 15)
            
        Returns:
            bool: True if rate is stale, False otherwise
        """
        return self.age_in_minutes() > max_age_minutes