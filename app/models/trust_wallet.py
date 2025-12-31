"""
Trust Wallet models for blockchain transaction tracking
"""
from app import db
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from sqlalchemy import func, and_, Index
from sqlalchemy.orm import validates
import json

class TrustWallet(db.Model):
    """Model for managing Trust wallet addresses"""
    __tablename__ = 'trust_wallets'
    
    id = db.Column(db.Integer, primary_key=True)
    wallet_address = db.Column(db.String(100), nullable=False, unique=True)
    wallet_name = db.Column(db.String(100), nullable=False)  # User-friendly name
    network = db.Column(db.String(20), nullable=False)  # ETH, BSC, TRC
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Last sync information
    last_sync_block = db.Column(db.Integer, default=0)
    last_sync_time = db.Column(db.DateTime)
    
    # Multi-tenancy
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('trust_wallets', lazy=True))
    transactions = db.relationship('TrustWalletTransaction', backref='wallet', lazy=True, cascade='all, delete-orphan')
    organization = db.relationship('Organization', backref=db.backref('trust_wallets', lazy=True))
    
    # Indexes
    __table_args__ = (
        Index('idx_trust_wallet_address', 'wallet_address'),
        Index('idx_trust_wallet_network', 'network'),
        Index('idx_trust_wallet_active', 'is_active'),
        Index('idx_trust_wallet_created_by', 'created_by'),
        Index('idx_trust_wallet_organization', 'organization_id'),
    )
    
    @validates('wallet_address')
    def validate_wallet_address(self, key, value):
        """Validate wallet address format"""
        if not value or len(value.strip()) == 0:
            raise ValueError('Wallet address cannot be empty')
        
        # Basic validation for different networks
        value = value.strip()
        if self.network == 'ETH':
            if not value.startswith('0x') or len(value) != 42:
                raise ValueError('Invalid Ethereum address format')
        elif self.network == 'BSC':
            if not value.startswith('0x') or len(value) != 42:
                raise ValueError('Invalid BSC address format')
        elif self.network == 'TRC':
            if not value.startswith('T') or len(value) != 34:
                raise ValueError('Invalid TRON address format')
        
        return value
    
    @validates('network')
    def validate_network(self, key, value):
        """Validate network type"""
        allowed_networks = ['ETH', 'BSC', 'TRC']
        if value not in allowed_networks:
            raise ValueError(f'Network must be one of: {allowed_networks}')
        return value
    
    def to_dict(self):
        """Convert wallet to dictionary"""
        return {
            'id': self.id,
            'wallet_address': self.wallet_address,
            'wallet_name': self.wallet_name,
            'network': self.network,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'last_sync_block': self.last_sync_block,
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'transaction_count': len(self.transactions) if self.transactions else 0
        }
    
    def __repr__(self):
        return f'<TrustWallet {self.id}: {self.wallet_name} ({self.network})>'


class TrustWalletTransaction(db.Model):
    """Model for Trust wallet blockchain transactions"""
    __tablename__ = 'trust_wallet_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('trust_wallets.id'), nullable=False)
    
    # Blockchain transaction details
    transaction_hash = db.Column(db.String(100), nullable=False, unique=True)
    block_number = db.Column(db.Integer, nullable=False)
    block_timestamp = db.Column(db.DateTime, nullable=False)
    
    # Address information
    from_address = db.Column(db.String(100), nullable=False)
    to_address = db.Column(db.String(100), nullable=False)
    
    # Token information
    token_symbol = db.Column(db.String(20), nullable=False)  # USDT, USDC, ETH, etc.
    token_name = db.Column(db.String(100))  # Full token name, e.g., "Tether USD"
    token_address = db.Column(db.String(100))  # Contract address for tokens
    token_amount = db.Column(db.Numeric(36, 18), nullable=False)  # High precision for crypto
    token_decimals = db.Column(db.Integer, default=18)
    
    # Transaction details
    transaction_type = db.Column(db.String(10), nullable=False)  # IN, OUT, INTERNAL
    gas_fee = db.Column(db.Numeric(36, 18), default=0)  # Network fee
    gas_fee_token = db.Column(db.String(20), default='ETH')  # Usually ETH for gas
    
    # Status and metadata
    status = db.Column(db.String(20), default='CONFIRMED')  # CONFIRMED, PENDING, FAILED
    confirmations = db.Column(db.Integer, default=0)
    network = db.Column(db.String(20), nullable=False)  # ETH, BSC, TRC
    
    # Exchange rate and TRY conversion
    exchange_rate = db.Column(db.Numeric(15, 4), nullable=True)
    amount_try = db.Column(db.Numeric(15, 2), nullable=True)
    gas_fee_try = db.Column(db.Numeric(15, 2), nullable=True)
    
    # Additional metadata
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Multi-tenancy
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_trust_tx_hash', 'transaction_hash'),
        Index('idx_trust_tx_wallet', 'wallet_id'),
        Index('idx_trust_tx_block', 'block_number'),
        Index('idx_trust_tx_timestamp', 'block_timestamp'),
        Index('idx_trust_tx_from', 'from_address'),
        Index('idx_trust_tx_to', 'to_address'),
        Index('idx_trust_tx_token', 'token_symbol'),
        Index('idx_trust_tx_type', 'transaction_type'),
        Index('idx_trust_tx_status', 'status'),
        Index('idx_trust_tx_network', 'network'),
        Index('idx_trust_tx_wallet_timestamp', 'wallet_id', 'block_timestamp'),
        Index('idx_trust_tx_wallet_token', 'wallet_id', 'token_symbol'),
        Index('idx_trust_tx_organization', 'organization_id'),
    )
    
    @validates('transaction_type')
    def validate_transaction_type(self, key, value):
        """Validate transaction type"""
        allowed_types = ['IN', 'OUT', 'INTERNAL']
        if value not in allowed_types:
            raise ValueError(f'Transaction type must be one of: {allowed_types}')
        return value
    
    @validates('status')
    def validate_status(self, key, value):
        """Validate transaction status"""
        allowed_statuses = ['CONFIRMED', 'PENDING', 'FAILED']
        if value not in allowed_statuses:
            raise ValueError(f'Status must be one of: {allowed_statuses}')
        return value
    
    @validates('token_amount')
    def validate_token_amount(self, key, value):
        """Validate token amount - Numeric(36, 18) allows 18 digits before decimal, 18 after"""
        try:
            amount = Decimal(str(value))
            if amount < 0:
                raise ValueError('Token amount cannot be negative')
            # Numeric(36, 18) means 36 total digits with 18 decimal places
            # Max value: 999999999999999999.999999999999999999 (18 digits before, 18 after)
            max_amount = Decimal('999999999999999999.999999999999999999')
            if amount > max_amount:
                raise ValueError('Token amount too large')
            return amount
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f'Invalid token amount: {e}')
    
    def calculate_try_amount(self, exchange_rate=None):
        """Calculate TRY equivalent amount with error handling"""
        try:
            if exchange_rate:
                self.exchange_rate = Decimal(str(exchange_rate))
            elif not self.exchange_rate:
                # Try to get current rate from ExchangeRate model
                try:
                    from app.models.exchange_rate import ExchangeRate
                    if self.token_symbol in ['USDT', 'USDC']:
                        # These are typically pegged to USD
                        current_rate = ExchangeRate.get_current_rate('USDTRY')
                        if current_rate:
                            self.exchange_rate = current_rate.rate
                        else:
                            self.exchange_rate = Decimal('48.0')  # Fallback
                    elif self.token_symbol == 'ETH':
                        # ETH to TRY rate (would need ETH/TRY pair)
                        current_rate = ExchangeRate.get_current_rate('ETHTRY')
                        if current_rate:
                            self.exchange_rate = current_rate.rate
                        else:
                            self.exchange_rate = Decimal('120000.0')  # Approximate fallback
                    else:
                        # For other tokens, use USD rate as approximation
                        current_rate = ExchangeRate.get_current_rate('USDTRY')
                        if current_rate:
                            self.exchange_rate = current_rate.rate
                        else:
                            self.exchange_rate = Decimal('48.0')
                except Exception as e:
                    # If database query fails, use default
                    import logging
                    logging.getLogger(__name__).warning(f"Failed to get exchange rate: {e}, using default")
                    self.exchange_rate = Decimal('48.0')
        except Exception as e:
            # Final fallback
            import logging
            logging.getLogger(__name__).warning(f"Error calculating TRY amount: {e}")
            self.exchange_rate = Decimal('48.0')
        
        # Calculate TRY amount
        if self.token_amount and self.exchange_rate:
            self.amount_try = self.token_amount * self.exchange_rate
        else:
            self.amount_try = Decimal('0')
        
        # Calculate gas fee in TRY
        if self.gas_fee and self.gas_fee_token == 'ETH':
            # Gas fee is usually in ETH
            gas_rate = ExchangeRate.get_current_rate('ETHTRY')
            if gas_rate:
                self.gas_fee_try = self.gas_fee * gas_rate.rate
            else:
                self.gas_fee_try = self.gas_fee * Decimal('120000.0')
    
    def to_dict(self):
        """Convert transaction to dictionary"""
        return {
            'id': self.id,
            'wallet_id': self.wallet_id,
            'transaction_hash': self.transaction_hash,
            'block_number': self.block_number,
            'block_timestamp': self.block_timestamp.isoformat() if self.block_timestamp else None,
            'from_address': self.from_address,
            'to_address': self.to_address,
            'token_symbol': self.token_symbol,
            'token_name': self.token_name,
            'token_address': self.token_address,
            'token_amount': float(self.token_amount) if self.token_amount else 0.0,
            'token_decimals': self.token_decimals,
            'transaction_type': self.transaction_type,
            'gas_fee': float(self.gas_fee) if self.gas_fee else 0.0,
            'gas_fee_token': self.gas_fee_token,
            'status': self.status,
            'confirmations': self.confirmations,
            'network': self.network,
            'exchange_rate': float(self.exchange_rate) if self.exchange_rate else None,
            'amount_try': float(self.amount_try) if self.amount_try else None,
            'gas_fee_try': float(self.gas_fee_try) if self.gas_fee_try else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def get_wallet_summary(cls, wallet_id, start_date=None, end_date=None):
        """Get summary statistics for a wallet"""
        query = cls.query.filter(cls.wallet_id == wallet_id)
        
        if start_date:
            query = query.filter(cls.block_timestamp >= start_date)
        if end_date:
            query = query.filter(cls.block_timestamp <= end_date)
        
        return query.with_entities(
            func.count(cls.id).label('transaction_count'),
            func.sum(cls.token_amount).label('total_amount'),
            func.sum(cls.amount_try).label('total_amount_try'),
            func.sum(cls.gas_fee).label('total_gas_fee'),
            func.sum(cls.gas_fee_try).label('total_gas_fee_try'),
            func.count(func.distinct(cls.token_symbol)).label('unique_tokens')
        ).first()
    
    @classmethod
    def get_token_summary(cls, wallet_id, token_symbol, start_date=None, end_date=None):
        """Get summary for specific token"""
        query = cls.query.filter(
            cls.wallet_id == wallet_id,
            cls.token_symbol == token_symbol
        )
        
        if start_date:
            query = query.filter(cls.block_timestamp >= start_date)
        if end_date:
            query = query.filter(cls.block_timestamp <= end_date)
        
        return query.with_entities(
            func.count(cls.id).label('transaction_count'),
            func.sum(cls.token_amount).label('total_amount'),
            func.sum(cls.amount_try).label('total_amount_try'),
            func.sum(case([(cls.transaction_type == 'IN', cls.token_amount)], else_=0)).label('total_in'),
            func.sum(case([(cls.transaction_type == 'OUT', cls.token_amount)], else_=0)).label('total_out')
        ).first()
    
    def __repr__(self):
        return f'<TrustWalletTransaction {self.id}: {self.token_symbol} {self.token_amount} ({self.transaction_type})>'
