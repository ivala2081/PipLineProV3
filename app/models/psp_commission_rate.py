"""
PSP Commission Rate models for PipLine Treasury System
Handles time-based commission rate changes
"""
from app import db
from sqlalchemy.orm import validates
from datetime import datetime, timezone, date
from decimal import Decimal, InvalidOperation

class PSPCommissionRate(db.Model):
    """PSP Commission Rate model for storing time-based commission rate changes"""
    __tablename__ = 'psp_commission_rate'
    
    id = db.Column(db.Integer, primary_key=True)
    psp_name = db.Column(db.String(100), nullable=False)
    commission_rate = db.Column(db.Numeric(5, 4), nullable=False)  # 0.15 = 15%
    effective_from = db.Column(db.Date, nullable=False)  # When this rate becomes effective
    effective_until = db.Column(db.Date, nullable=True)  # When this rate expires (NULL = current)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Database constraints and indexes
    __table_args__ = (
        db.Index('idx_psp_commission_rate_psp', 'psp_name'),
        db.Index('idx_psp_commission_rate_effective_from', 'effective_from'),
        db.Index('idx_psp_commission_rate_effective_until', 'effective_until'),
        db.Index('idx_psp_commission_rate_psp_effective', 'psp_name', 'effective_from'),
        db.Index('idx_psp_commission_rate_active', 'is_active'),
    )
    
    @validates('psp_name')
    def validate_psp_name(self, key, value):
        """Validate PSP name"""
        if not value or len(value.strip()) == 0:
            raise ValueError('PSP name cannot be empty')
        return value.strip()
    
    @validates('commission_rate')
    def validate_commission_rate(self, key, value):
        """Validate commission rate"""
        try:
            rate = Decimal(str(value))
            if rate < 0:
                raise ValueError('Commission rate cannot be negative')
            if rate > 1:
                raise ValueError('Commission rate cannot exceed 100% (1.0)')
            return rate
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f'Invalid commission rate: {e}')
    
    @validates('effective_from')
    def validate_effective_from(self, key, value):
        """Validate effective from date"""
        if not isinstance(value, date):
            raise ValueError('Effective from must be a date')
        return value
    
    @validates('effective_until')
    def validate_effective_until(self, key, value):
        """Validate effective until date"""
        if value is not None:
            if not isinstance(value, date):
                raise ValueError('Effective until must be a date')
            if hasattr(self, 'effective_from') and self.effective_from and value <= self.effective_from:
                raise ValueError('Effective until must be after effective from')
        return value
    
    @classmethod
    def get_rate_for_date(cls, psp_name: str, target_date: date) -> Decimal:
        """Get the commission rate for a specific PSP on a specific date"""
        # Find the active rate for the PSP on the target date
        rate_record = cls.query.filter(
            cls.psp_name == psp_name,
            cls.is_active == True,
            cls.effective_from <= target_date,
            db.or_(
                cls.effective_until.is_(None),  # No end date (current rate)
                cls.effective_until >= target_date  # End date is after target date
            )
        ).order_by(cls.effective_from.desc()).first()
        
        if rate_record:
            return rate_record.commission_rate
        
        # If no specific rate found, return 0 (no commission)
        return Decimal('0.0')
    
    @classmethod
    def get_current_rate(cls, psp_name: str) -> Decimal:
        """Get the current commission rate for a PSP"""
        return cls.get_rate_for_date(psp_name, date.today())
    
    @classmethod
    def get_rate_history(cls, psp_name: str) -> list:
        """Get the complete rate history for a PSP"""
        return cls.query.filter(
            cls.psp_name == psp_name,
            cls.is_active == True
        ).order_by(cls.effective_from.asc()).all()
    
    @classmethod
    def set_new_rate(cls, psp_name: str, new_rate: Decimal, effective_from: date, effective_until: date = None):
        """Set a new commission rate for a PSP"""
        # Close any current rate that overlaps
        cls.query.filter(
            cls.psp_name == psp_name,
            cls.is_active == True,
            cls.effective_until.is_(None)  # Current rate (no end date)
        ).update({'effective_until': effective_from})
        
        # Create new rate record
        new_rate_record = cls(
            psp_name=psp_name,
            commission_rate=new_rate,
            effective_from=effective_from,
            effective_until=effective_until
        )
        db.session.add(new_rate_record)
        db.session.commit()
        
        return new_rate_record
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'psp_name': self.psp_name,
            'commission_rate': float(self.commission_rate) if self.commission_rate else 0.0,
            'commission_rate_percent': float(self.commission_rate * 100) if self.commission_rate else 0.0,
            'effective_from': self.effective_from.isoformat() if self.effective_from else None,
            'effective_until': self.effective_until.isoformat() if self.effective_until else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<PSPCommissionRate {self.psp_name}:{self.commission_rate}% from {self.effective_from}>'
