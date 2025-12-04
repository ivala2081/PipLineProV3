"""
Transaction model with business logic and validation
"""
from app import db
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from sqlalchemy import func, and_
from sqlalchemy.orm import validates
import json

class Transaction(db.Model):
    """Transaction model with enhanced validation and business logic"""
    __tablename__ = 'transaction'  # Keep original name to match database
    
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100))
    payment_method = db.Column(db.String(50))

    date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(50))
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    commission = db.Column(db.Numeric(15, 2), default=0.0)
    net_amount = db.Column(db.Numeric(15, 2), nullable=False)
    currency = db.Column(db.String(10), default='TL')
    psp = db.Column(db.String(50))
    notes = db.Column(db.Text)
    
    # TL Amount fields for foreign currency transactions
    amount_try = db.Column(db.Numeric(15, 2), nullable=True)
    commission_try = db.Column(db.Numeric(15, 2), nullable=True)
    net_amount_try = db.Column(db.Numeric(15, 2), nullable=True)
    exchange_rate = db.Column(db.Numeric(10, 4), nullable=True)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Enhanced database indexes for performance optimization
    __table_args__ = (
        # Single column indexes for frequently queried fields
        db.Index('idx_transaction_date', 'date'),
        db.Index('idx_transaction_client', 'client_name'),
        db.Index('idx_transaction_company', 'company'),
        db.Index('idx_transaction_psp', 'psp'),
        db.Index('idx_transaction_category', 'category'),
        db.Index('idx_transaction_currency', 'currency'),
        db.Index('idx_transaction_created_at', 'created_at'),
        db.Index('idx_transaction_created_by', 'created_by'),
        
        # Composite indexes for common query patterns
        db.Index('idx_transaction_date_psp', 'date', 'psp'),
        db.Index('idx_transaction_date_category', 'date', 'category'),
        db.Index('idx_transaction_date_currency', 'date', 'currency'),
        db.Index('idx_transaction_psp_category', 'psp', 'category'),
        db.Index('idx_transaction_created_by_date', 'created_by', 'date'),
        
        # Multi-column indexes for complex queries
        db.Index('idx_transaction_date_psp_category', 'date', 'psp', 'category'),
        db.Index('idx_transaction_date_currency_psp', 'date', 'currency', 'psp'),
        
        # CRITICAL: Monthly stats query optimization - PSP + date + category together
        db.Index('idx_transaction_psp_date_category', 'psp', 'date', 'category'),
        
        # Partial indexes for active records (if supported by database)
        # Note: SQLite doesn't support partial indexes, but PostgreSQL does
    )
    
    # Relationships
    user = db.relationship('User', backref=db.backref('transactions', lazy=True))
    
    @validates('client_name')
    def validate_client_name(self, key, value):
        """Validate client name"""
        if not value or len(value.strip()) == 0:
            raise ValueError('Client name cannot be empty')
        if len(value) > 100:
            raise ValueError('Client name too long')
        return value.strip()
    
    @validates('amount')
    def validate_amount(self, key, value):
        """Validate amount - basit format kontrolu, category kontrolu endpoint'te yapilir"""
        try:
            amount = Decimal(str(value))
            # Sadece boyut kontrolu yap, category-specific kontroller endpoint'te
            if abs(amount) > 999999999.99:
                raise ValueError('Amount too large')
            # Sifir kontrolu - hem pozitif hem negatif degerlere izin ver
            if amount == 0:
                raise ValueError('Amount cannot be zero')
            return amount
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f'Invalid amount: {e}')
    
    @validates('commission')
    def validate_commission(self, key, value):
        """Validate commission - allow negative for WD transactions"""
        try:
            commission = Decimal(str(value))
            # Allow negative commissions (they will be validated in business logic)
            if commission > 999999999.99:
                raise ValueError('Commission too large')
            if commission < -999999999.99:
                raise ValueError('Commission too negative')
            return commission
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f'Invalid commission: {e}')
    
    @validates('net_amount')
    def validate_net_amount(self, key, value):
        """Validate net amount"""
        try:
            net_amount = Decimal(str(value))
            if net_amount > 999999999.99:
                raise ValueError('Net amount too large')
            return net_amount
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f'Invalid net amount: {e}')
    
    @validates('currency')
    def validate_currency(self, key, value):
        """Validate currency - only TL, USD, EUR allowed"""
        allowed_currencies = ['TL', 'USD', 'EUR']
        if value not in allowed_currencies:
            raise ValueError(f'Currency must be one of: {allowed_currencies}')
        return value
    
    @validates('category')
    def validate_category(self, key, value):
        """Validate category - only WD or DEP allowed"""
        if value:
            allowed_categories = ['WD', 'DEP']
            if value.upper() not in allowed_categories:
                raise ValueError(f'Category must be one of: {allowed_categories}')
            return value.upper()  # Normalize to uppercase
        return value
    
    def calculate_net_amount(self):
        """Calculate net amount based on amount and commission"""
        return self.amount - self.commission
    
    def calculate_try_amounts(self, exchange_rate=None):
        """Calculate TL amounts using exchange rate"""
        if self.currency == 'USD':
            if exchange_rate:
                # Use provided exchange rate
                self.exchange_rate = Decimal(str(exchange_rate))
            elif not self.exchange_rate:
                # Try to get current rate from ExchangeRate model
                from app.models.exchange_rate import ExchangeRate
                current_rate = ExchangeRate.get_current_rate('USDTRY')
                if current_rate:
                    self.exchange_rate = current_rate.rate
                else:
                    # No rate available - do NOT use arbitrary fallback
                    # Leave exchange_rate as None to indicate pending/missing rate
                    self.exchange_rate = None
                    # self.exchange_rate = Decimal('27.0')  # DANGEROUS FALLBACK REMOVED
            
            # Calculate TRY amounts ONLY if we have a valid exchange rate
            if self.exchange_rate:
                self.amount_try = abs(self.amount) * self.exchange_rate
                self.commission_try = abs(self.commission) * self.exchange_rate if self.commission else Decimal('0')
                self.net_amount_try = abs(self.net_amount) * self.exchange_rate
            else:
                # Reset TRY amounts if no rate available
                self.amount_try = None
                self.commission_try = None
                self.net_amount_try = None
            
            # Handle withdrawal signs correctly
            if self.category == 'WD':
                self.amount_try = -self.amount_try
                self.net_amount_try = -self.net_amount_try
                
        elif self.currency == 'EUR':
            # EUR conversion (future implementation)
            if exchange_rate:
                self.exchange_rate = Decimal(str(exchange_rate))
                self.amount_try = self.amount * self.exchange_rate
                self.commission_try = self.commission * self.exchange_rate if self.commission else Decimal('0')
                self.net_amount_try = self.net_amount * self.exchange_rate
        else:
            # For TL transactions, TL amounts are the same as original amounts
            self.exchange_rate = Decimal('1.0')
            self.amount_try = self.amount
            self.commission_try = self.commission
            self.net_amount_try = self.net_amount
    
    def update_exchange_rate(self, new_rate):
        """Update exchange rate and recalculate TRY amounts"""
        if self.currency == 'USD' and new_rate:
            self.exchange_rate = Decimal(str(new_rate))
            self.calculate_try_amounts(new_rate)
            return True
        return False
    
    def get_try_amount(self):
        """Get TRY equivalent amount (for metrics calculations)"""
        if self.amount_try is not None:
            return self.amount_try
        elif self.currency == 'TL':
            return self.amount
        else:
            # Fallback: calculate with current rate
            self.calculate_try_amounts()
            return self.amount_try or self.amount
    
    def get_try_net_amount(self):
        """Get TRY equivalent net amount (for metrics calculations)"""
        if self.net_amount_try is not None:
            return self.net_amount_try
        elif self.currency == 'TL':
            return self.net_amount
        else:
            # Fallback: calculate with current rate
            self.calculate_try_amounts()
            return self.net_amount_try or self.net_amount
    
    def to_dict(self):
        """Convert transaction to dictionary"""
        return {
            'id': self.id,
            'client_name': self.client_name,
            'company': self.company,
            'payment_method': self.payment_method,

            'date': self.date.isoformat() if self.date else None,
            'category': self.category,
            'amount': float(self.amount) if self.amount else 0.0,
            'commission': float(self.commission) if self.commission else 0.0,
            'net_amount': float(self.net_amount) if self.net_amount else 0.0,
            'currency': self.currency,
            'psp': self.psp,
            'notes': self.notes,
            'amount_try': float(self.amount_try) if self.amount_try else None,
            'commission_try': float(self.commission_try) if self.commission_try else None,
            'net_amount_try': float(self.net_amount_try) if self.net_amount_try else None,
            'exchange_rate': float(self.exchange_rate) if self.exchange_rate else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    @classmethod
    def get_daily_summary(cls, date_obj, psp=None):
        """Get daily summary for a specific date and PSP"""
        query = cls.query.filter(cls.date == date_obj)
        if psp:
            query = query.filter(cls.psp == psp)
        
        return query.with_entities(
            func.sum(cls.amount).label('total_amount'),
            func.sum(cls.commission).label('total_commission'),
            func.sum(cls.net_amount).label('total_net'),
            func.count(cls.id).label('transaction_count')
        ).first()
    
    @classmethod
    def get_psp_summary(cls, start_date, end_date, psp=None):
        """Get PSP summary for date range"""
        query = cls.query.filter(
            cls.date >= start_date,
            cls.date <= end_date
        )
        if psp:
            query = query.filter(cls.psp == psp)
        
        return query.with_entities(
            cls.psp,
            func.sum(cls.amount).label('total_amount'),
            func.sum(cls.commission).label('total_commission'),
            func.sum(cls.net_amount).label('total_net'),
            func.count(cls.id).label('transaction_count')
        ).group_by(cls.psp).all()
    
    def __repr__(self):
        return f'<Transaction {self.id}: {self.client_name} - {self.amount} {self.currency}>' 