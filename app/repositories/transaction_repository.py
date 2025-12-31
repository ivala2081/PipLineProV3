"""
Transaction Repository
Repository pattern implementation for Transaction model
"""
from typing import Optional, List, TYPE_CHECKING
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import and_, func
from app.repositories.base_repository import BaseRepository

if TYPE_CHECKING:
    from app.models.transaction import Transaction


class TransactionRepository(BaseRepository):
    """Repository for Transaction operations"""
    
    def __init__(self):
        # Lazy import to avoid circular dependency
        from app.models.transaction import Transaction
        super().__init__(Transaction)
    
    def find_by_date_range(
        self,
        start_date: date,
        end_date: date,
        organization_id: Optional[int] = None
    ) -> List['Transaction']:
        """
        Find transactions in date range
        
        Args:
            start_date: Start date
            end_date: End date
            organization_id: Optional organization filter
        
        Returns:
            List of transactions
        """
        query = self.query().filter(
            and_(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
        )
        if organization_id:
            query = query.filter_by(organization_id=organization_id)
        return query.all()
    
    def find_by_client(
        self,
        client_name: str,
        organization_id: Optional[int] = None
    ) -> List['Transaction']:
        """
        Find transactions by client name
        
        Args:
            client_name: Client name
            organization_id: Optional organization filter
        
        Returns:
            List of transactions
        """
        query = self.query().filter_by(client_name=client_name)
        if organization_id:
            query = query.filter_by(organization_id=organization_id)
        return query.order_by(Transaction.date.desc()).all()
    
    def find_by_category(
        self,
        category: str,
        organization_id: Optional[int] = None
    ) -> List['Transaction']:
        """
        Find transactions by category
        
        Args:
            category: Transaction category
            organization_id: Optional organization filter
        
        Returns:
            List of transactions
        """
        query = self.query().filter_by(category=category)
        if organization_id:
            query = query.filter_by(organization_id=organization_id)
        return query.order_by(Transaction.date.desc()).all()
    
    def find_by_psp(
        self,
        psp: str,
        organization_id: Optional[int] = None
    ) -> List['Transaction']:
        """
        Find transactions by PSP
        
        Args:
            psp: Payment Service Provider name
            organization_id: Optional organization filter
        
        Returns:
            List of transactions
        """
        query = self.query().filter_by(psp=psp)
        if organization_id:
            query = query.filter_by(organization_id=organization_id)
        return query.order_by(Transaction.date.desc()).all()
    
    def get_total_amount(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category: Optional[str] = None,
        organization_id: Optional[int] = None
    ) -> Decimal:
        """
        Get total transaction amount
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            category: Optional category filter
            organization_id: Optional organization filter
        
        Returns:
            Total amount as Decimal
        """
        query = self.query()
        
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        if category:
            query = query.filter_by(category=category)
        if organization_id:
            query = query.filter_by(organization_id=organization_id)
        
        result = query.with_entities(func.sum(Transaction.amount)).scalar()
        return Decimal(result) if result else Decimal('0')
    
    def get_transaction_count(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category: Optional[str] = None,
        organization_id: Optional[int] = None
    ) -> int:
        """
        Get transaction count
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            category: Optional category filter
            organization_id: Optional organization filter
        
        Returns:
            Transaction count
        """
        query = self.query()
        
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        if category:
            query = query.filter_by(category=category)
        if organization_id:
            query = query.filter_by(organization_id=organization_id)
        
        return query.count()
