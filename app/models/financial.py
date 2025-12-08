"""
Financial models for PipLine Treasury System
"""
from app import db
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from sqlalchemy.orm import validates

class PspTrack(db.Model):
    """PSP tracking model"""
    __tablename__ = 'psp_track'
    
    id = db.Column(db.Integer, primary_key=True)
    psp_name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=True)
    commission_rate = db.Column(db.Numeric(5, 4), nullable=True)
    commission_amount = db.Column(db.Numeric(15, 2), nullable=True)
    difference = db.Column(db.Numeric(15, 2), nullable=True)
    withdraw = db.Column(db.Numeric(15, 2), nullable=True)
    allocation = db.Column(db.Numeric(15, 2), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Database constraints and indexes
    __table_args__ = (
        db.Index('idx_psp_track_psp_name', 'psp_name'),
        db.Index('idx_psp_track_date', 'date'),
        db.Index('idx_psp_track_psp_date', 'psp_name', 'date'),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'psp_name': self.psp_name,
            'date': self.date.isoformat() if self.date else None,
            'amount': float(self.amount) if self.amount else 0.0,
            'commission_rate': float(self.commission_rate) if self.commission_rate else 0.0,
            'commission_amount': float(self.commission_amount) if self.commission_amount else 0.0,
            'difference': float(self.difference) if self.difference else 0.0,
            'withdraw': float(self.withdraw) if self.withdraw else 0.0,
            'allocation': float(self.allocation) if self.allocation else 0.0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<PspTrack {self.psp_name}:{self.date}:{self.amount}>'

class DailyBalance(db.Model):
    """Daily balance tracking model"""
    __tablename__ = 'daily_balance'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    psp = db.Column(db.String(50), nullable=False)
    opening_balance = db.Column(db.Numeric(15, 2), default=0.0)
    total_inflow = db.Column(db.Numeric(15, 2), default=0.0)
    total_outflow = db.Column(db.Numeric(15, 2), default=0.0)
    total_commission = db.Column(db.Numeric(15, 2), default=0.0)
    net_amount = db.Column(db.Numeric(15, 2), default=0.0)
    closing_balance = db.Column(db.Numeric(15, 2), default=0.0)
    allocation = db.Column(db.Numeric(15, 2), default=0.0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Database constraints and indexes
    __table_args__ = (
        db.UniqueConstraint('date', 'psp', name='uq_daily_balance_date_psp'),
        db.Index('idx_daily_balance_date', 'date'),
        db.Index('idx_daily_balance_psp', 'psp'),
        db.Index('idx_daily_balance_date_psp', 'date', 'psp'),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'psp': self.psp,
            'opening_balance': float(self.opening_balance) if self.opening_balance else 0.0,
            'total_inflow': float(self.total_inflow) if self.total_inflow else 0.0,
            'total_outflow': float(self.total_outflow) if self.total_outflow else 0.0,
            'total_commission': float(self.total_commission) if self.total_commission else 0.0,
            'net_amount': float(self.net_amount) if self.net_amount else 0.0,
            'closing_balance': float(self.closing_balance) if self.closing_balance else 0.0,
            'allocation': float(self.allocation) if self.allocation else 0.0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<DailyBalance {self.date}:{self.psp}:{self.net_amount}>'

class PSPAllocation(db.Model):
    """PSP allocation model for storing allocation data by date"""
    __tablename__ = 'psp_allocation'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    psp_name = db.Column(db.String(100), nullable=False)
    allocation_amount = db.Column(db.Numeric(15, 2), default=0.0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Composite unique constraint to ensure one allocation per PSP per date
    __table_args__ = (
        db.UniqueConstraint('date', 'psp_name', name='uq_psp_allocation_date_psp'),
        db.Index('idx_psp_allocation_date', 'date'),
        db.Index('idx_psp_allocation_psp', 'psp_name'),
        db.Index('idx_psp_allocation_date_psp', 'date', 'psp_name'),
    )
    
    @validates('allocation_amount')
    def validate_allocation_amount(self, key, value):
        """Validate allocation amount"""
        try:
            amount = Decimal(str(value))
            if amount < 0:
                raise ValueError('Allocation amount cannot be negative')
            if amount > 999999999.99:
                raise ValueError('Allocation amount too large')
            return amount
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f'Invalid allocation amount: {e}')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'psp_name': self.psp_name,
            'allocation_amount': float(self.allocation_amount) if self.allocation_amount else 0.0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<PSPAllocation {self.date}:{self.psp_name}:{self.allocation_amount}>'

class PSPDevir(db.Model):
    """PSP Devir (Transfer/Carryover) model for storing manual Devir overrides by date"""
    __tablename__ = 'psp_devir'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    psp_name = db.Column(db.String(100), nullable=False)
    devir_amount = db.Column(db.Numeric(15, 2), default=0.0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Composite unique constraint to ensure one Devir override per PSP per date
    __table_args__ = (
        db.UniqueConstraint('date', 'psp_name', name='uq_psp_devir_date_psp'),
        db.Index('idx_psp_devir_date', 'date'),
        db.Index('idx_psp_devir_psp', 'psp_name'),
        db.Index('idx_psp_devir_date_psp', 'date', 'psp_name'),
    )
    
    @validates('devir_amount')
    def validate_devir_amount(self, key, value):
        """Validate Devir amount"""
        try:
            amount = Decimal(str(value))
            if amount < -999999999.99:
                raise ValueError('Devir amount too small')
            if amount > 999999999.99:
                raise ValueError('Devir amount too large')
            return amount
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f'Invalid Devir amount: {e}')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'psp_name': self.psp_name,
            'devir_amount': float(self.devir_amount) if self.devir_amount else 0.0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<PSPDevir {self.date}:{self.psp_name}:{self.devir_amount}>'

class PSPKasaTop(db.Model):
    """PSP KASA TOP (Revenue) model for storing manual KASA TOP overrides by date"""
    __tablename__ = 'psp_kasa_top'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    psp_name = db.Column(db.String(100), nullable=False)
    kasa_top_amount = db.Column(db.Numeric(15, 2), default=0.0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Composite unique constraint to ensure one KASA TOP override per PSP per date
    __table_args__ = (
        db.UniqueConstraint('date', 'psp_name', name='uq_psp_kasa_top_date_psp'),
        db.Index('idx_psp_kasa_top_date', 'date'),
        db.Index('idx_psp_kasa_top_psp', 'psp_name'),
        db.Index('idx_psp_kasa_top_date_psp', 'date', 'psp_name'),
    )
    
    @validates('kasa_top_amount')
    def validate_kasa_top_amount(self, key, value):
        """Validate KASA TOP amount"""
        try:
            amount = Decimal(str(value))
            if amount < -999999999.99:
                raise ValueError('KASA TOP amount too small')
            if amount > 999999999.99:
                raise ValueError('KASA TOP amount too large')
            return amount
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f'Invalid KASA TOP amount: {e}')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'psp_name': self.psp_name,
            'kasa_top_amount': float(self.kasa_top_amount) if self.kasa_top_amount else 0.0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<PSPKasaTop {self.date}:{self.psp_name}:{self.kasa_top_amount}>' 

class DailyNet(db.Model):
    """Daily Net calculation model for Accounting → Net tab"""
    __tablename__ = 'daily_net'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)  # One net calculation per date
    net_cash_usd = db.Column(db.Numeric(15, 2), nullable=False, default=0.0)
    expenses_usd = db.Column(db.Numeric(15, 2), nullable=False, default=0.0)  # HARCAMALAR
    commissions_usd = db.Column(db.Numeric(15, 2), nullable=False, default=0.0)  # GIDERLER (KOMISYON)
    rollover_usd = db.Column(db.Numeric(15, 2), nullable=False, default=0.0)  # DEVREDEN TAHSILAT
    net_saglama_usd = db.Column(db.Numeric(15, 2), nullable=False, default=0.0)  # Calculated result
    
    # New fields for enhanced Net calculation
    onceki_kapanis_usd = db.Column(db.Numeric(15, 2), nullable=False, default=0.0)  # ÖNCEKİ KAPANIŞ (Previous Closing)
    company_cash_usd = db.Column(db.Numeric(15, 2), nullable=False, default=0.0)  # Company Cash (manual input)
    crypto_balance_usd = db.Column(db.Numeric(15, 2), nullable=False, default=0.0)  # Crypto Wallets Balance (auto-fetched)
    anlik_kasa_usd = db.Column(db.Numeric(15, 2), nullable=False, default=0.0)  # ANLIK KASA (Current Cash = Company Cash + Crypto Balance)
    anlik_kasa_manual = db.Column(db.Boolean, nullable=False, default=False)  # Flag to indicate if CURRENT CASH is manually overridden
    bekleyen_tahsilat_usd = db.Column(db.Numeric(15, 2), nullable=False, default=0.0)  # BEKLEYEN TAHSİLAT (Pending Collection)
    fark_usd = db.Column(db.Numeric(15, 2), nullable=False, default=0.0)  # FARK (Difference 1)
    fark_bottom_usd = db.Column(db.Numeric(15, 2), nullable=False, default=0.0)  # FARK bottom (Reconciliation Difference)
    
    notes = db.Column(db.Text, nullable=True)  # Optional notes
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Database constraints and indexes
    __table_args__ = (
        db.Index('idx_daily_net_date', 'date'),
        db.Index('idx_daily_net_created_by', 'created_by'),
    )
    
    @validates('net_cash_usd', 'expenses_usd', 'commissions_usd', 'rollover_usd', 'net_saglama_usd',
               'onceki_kapanis_usd', 'company_cash_usd', 'crypto_balance_usd', 'anlik_kasa_usd', 'bekleyen_tahsilat_usd', 'fark_usd', 'fark_bottom_usd')
    def validate_amounts(self, key, value):
        """Validate amount fields"""
        try:
            amount = Decimal(str(value))
            if amount < -999999999.99:
                raise ValueError(f'{key} amount too small')
            if amount > 999999999.99:
                raise ValueError(f'{key} amount too large')
            return amount
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f'Invalid {key}: {e}')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'net_cash_usd': float(self.net_cash_usd) if self.net_cash_usd else 0.0,
            'expenses_usd': float(self.expenses_usd) if self.expenses_usd else 0.0,
            'commissions_usd': float(self.commissions_usd) if self.commissions_usd else 0.0,
            'rollover_usd': float(self.rollover_usd) if self.rollover_usd else 0.0,
            'net_saglama_usd': float(self.net_saglama_usd) if self.net_saglama_usd else 0.0,
            'onceki_kapanis_usd': float(self.onceki_kapanis_usd) if self.onceki_kapanis_usd else 0.0,
            'company_cash_usd': float(self.company_cash_usd) if self.company_cash_usd else 0.0,
            'crypto_balance_usd': float(self.crypto_balance_usd) if self.crypto_balance_usd else 0.0,
            'anlik_kasa_usd': float(self.anlik_kasa_usd) if self.anlik_kasa_usd else 0.0,
            'anlik_kasa_manual': self.anlik_kasa_manual if self.anlik_kasa_manual else False,
            'bekleyen_tahsilat_usd': float(self.bekleyen_tahsilat_usd) if self.bekleyen_tahsilat_usd else 0.0,
            'fark_usd': float(self.fark_usd) if self.fark_usd else 0.0,
            'fark_bottom_usd': float(self.fark_bottom_usd) if self.fark_bottom_usd else 0.0,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    def __repr__(self):
        return f'<DailyNet {self.date}: NET_SAGLAMA={self.net_saglama_usd}>'