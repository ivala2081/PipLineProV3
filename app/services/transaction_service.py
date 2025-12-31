"""
Transaction Service
Business logic for transaction operations

This service handles all transaction-related business logic, including:
- Creating, updating, and deleting transactions
- Calculating commissions and net amounts
- Retrieving transactions with various filters
- Generating dashboard statistics
"""
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timezone
from decimal import Decimal
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.user_repository import UserRepository
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.transaction import Transaction
from app.utils.constants import TransactionCategory, Currency
from app.utils.unified_logger import get_logger
from app.utils.type_hints_helper import JsonDict, OptionalInt, OptionalDate

logger = get_logger(__name__)


class TransactionService:
    """Service for transaction business logic"""
    
    def __init__(self):
        self.transaction_repo = TransactionRepository()
        self.user_repo = UserRepository()
    
    def create_transaction(
        self,
        client_name: str,
        amount: Decimal,
        category: str,
        date: date,
        currency: str = Currency.TRY.value,
        payment_method: Optional[str] = None,
        psp: Optional[str] = None,
        company: Optional[str] = None,
        notes: Optional[str] = None,
        created_by: OptionalInt = None,
        organization_id: OptionalInt = None
    ) -> 'Transaction':
        """
        Create a new transaction
        
        Args:
            client_name: Client name
            amount: Transaction amount
            category: Transaction category (DEP or WD)
            date: Transaction date
            currency: Currency code
            payment_method: Payment method
            psp: Payment Service Provider
            company: Company name
            notes: Additional notes
            created_by: User ID who created the transaction
            organization_id: Organization ID
        
        Returns:
            Created transaction
        """
        # Validate category
        if not TransactionCategory.is_valid(category):
            raise ValueError(f"Invalid category: {category}. Must be DEP or WD")
        
        # Calculate commission (5% default, can be customized)
        commission_rate = Decimal('0.05')
        commission = amount * commission_rate
        net_amount = amount - commission
        
        # Create transaction
        transaction = self.transaction_repo.create(
            client_name=client_name,
            amount=amount,
            category=category,
            date=date,
            currency=currency,
            payment_method=payment_method,
            psp=psp,
            company=company,
            notes=notes,
            commission=commission,
            net_amount=net_amount,
            created_by=created_by,
            organization_id=organization_id,
            created_at=datetime.now(timezone.utc)
        )
        
        logger.info(f"Transaction created: {transaction.id} for client {client_name}")
        return transaction
    
    def update_transaction(
        self,
        transaction_id: int,
        **kwargs
    ) -> 'Transaction':
        """
        Update a transaction
        
        Args:
            transaction_id: Transaction ID
            **kwargs: Fields to update
        
        Returns:
            Updated transaction
        """
        transaction = self.transaction_repo.get_by_id(transaction_id)
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")
        
        # Recalculate commission if amount changed
        if 'amount' in kwargs:
            amount = Decimal(str(kwargs['amount']))
            commission_rate = Decimal('0.05')
            kwargs['commission'] = amount * commission_rate
            kwargs['net_amount'] = amount - kwargs['commission']
        
        updated = self.transaction_repo.update(transaction, **kwargs)
        logger.info(f"Transaction updated: {transaction_id}")
        return updated
    
    def delete_transaction(self, transaction_id: int) -> bool:
        """
        Delete a transaction
        
        Args:
            transaction_id: Transaction ID
        
        Returns:
            True if deleted successfully
        """
        success = self.transaction_repo.delete_by_id(transaction_id)
        if success:
            logger.info(f"Transaction deleted: {transaction_id}")
        return success
    
    def get_transactions_by_date_range(
        self,
        start_date: date,
        end_date: date,
        organization_id: OptionalInt = None
    ) -> List['Transaction']:
        """
        Get transactions in date range
        
        Args:
            start_date: Start date
            end_date: End date
            organization_id: Optional organization filter
        
        Returns:
            List of transactions
        """
        return self.transaction_repo.find_by_date_range(
            start_date,
            end_date,
            organization_id
        )
    
    def get_dashboard_stats(
        self,
        days: int = 30,
        organization_id: OptionalInt = None
    ) -> JsonDict:
        """
        Get dashboard statistics
        
        Args:
            days: Number of days to look back
            organization_id: Optional organization filter
        
        Returns:
            Dictionary with statistics
        """
        end_date = date.today()
        start_date = date.fromordinal(end_date.toordinal() - days)
        
        total_amount = self.transaction_repo.get_total_amount(
            start_date=start_date,
            end_date=end_date,
            organization_id=organization_id
        )
        
        deposit_amount = self.transaction_repo.get_total_amount(
            start_date=start_date,
            end_date=end_date,
            category=TransactionCategory.DEPOSIT.value,
            organization_id=organization_id
        )
        
        withdrawal_amount = self.transaction_repo.get_total_amount(
            start_date=start_date,
            end_date=end_date,
            category=TransactionCategory.WITHDRAWAL.value,
            organization_id=organization_id
        )
        
        total_count = self.transaction_repo.get_transaction_count(
            start_date=start_date,
            end_date=end_date,
            organization_id=organization_id
        )
        
        return {
            'total_amount': float(total_amount),
            'deposit_amount': float(deposit_amount),
            'withdrawal_amount': float(withdrawal_amount),
            'transaction_count': total_count,
            'period_days': days,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }
    
    @staticmethod
    def calculate_commission_based_on_total_deposits(total_deposits: Decimal, psp: str) -> Decimal:
        """
        Calculate commission based on total deposits for a PSP
        
        Args:
            total_deposits: Total deposit amount for the PSP
            psp: Payment Service Provider name
        
        Returns:
            Commission amount as Decimal
        """
        # Tether is company's own KASA, so no commission calculations
        if psp and psp.upper() == 'TETHER':
            return Decimal('0')
        
        # Get commission rate from PSP options
        try:
            from app.models.config import Option
            psp_option = Option.query.filter_by(
                field_name='psp',
                value=psp,
                is_active=True
            ).first()
            
            if psp_option and psp_option.commission_rate is not None:
                # commission_rate is stored as decimal (0.025 for 2.5%)
                # Convert to percentage for calculation: multiply by 100, then divide by 100
                # This is equivalent to: total_deposits * commission_rate
                commission_rate_percent = float(psp_option.commission_rate) * 100
                commission = total_deposits * Decimal(str(commission_rate_percent / 100))
                return commission
            else:
                # No commission rate found
                return Decimal('0')
        except Exception as e:
            logger.error(f"Error calculating commission for PSP {psp}: {e}")
            return Decimal('0')