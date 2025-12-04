"""
Transaction Repository
Provides optimized database access for Transaction model
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from sqlalchemy import func, and_, or_, desc
from sqlalchemy.orm import joinedload
from decimal import Decimal

from app.models.transaction import Transaction
from app.repositories.base_repository import BaseRepository
from app.utils.db_compat import ilike_compat

logger = logging.getLogger(__name__)


class TransactionRepository(BaseRepository):
    """Repository for Transaction model with optimized queries"""
    
    def __init__(self):
        super().__init__(Transaction)
    
    def get_by_date_range(self, start_date: date, end_date: date, 
                          filters: Dict[str, Any] = None,
                          page: int = 1, per_page: int = 50) -> Dict[str, Any]:
        """
        Get transactions within a date range with pagination
        
        Args:
            start_date: Start date
            end_date: End date
            filters: Additional filters (psp, category, currency, etc.)
            page: Page number
            per_page: Records per page
            
        Returns:
            Dictionary with items and pagination info
        """
        try:
            query = self.session.query(Transaction).filter(
                and_(
                    Transaction.date >= start_date,
                    Transaction.date <= end_date
                )
            )
            
            # Apply additional filters
            if filters:
                if filters.get('psp'):
                    query = query.filter(Transaction.psp == filters['psp'])
                if filters.get('category'):
                    query = query.filter(Transaction.category == filters['category'])
                if filters.get('currency'):
                    query = query.filter(Transaction.currency == filters['currency'])
                if filters.get('client_name'):
                    query = query.filter(ilike_compat(Transaction.client_name, f"%{filters['client_name']}%"))
            
            # Order by date descending
            query = query.order_by(desc(Transaction.date), desc(Transaction.id))
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            offset = (page - 1) * per_page
            items = query.offset(offset).limit(per_page).all()
            
            # Calculate pagination info
            total_pages = (total + per_page - 1) // per_page if total > 0 else 1
            
            return {
                'items': items,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'total_pages': total_pages,
                    'has_prev': page > 1,
                    'has_next': page < total_pages
                }
            }
        except Exception as e:
            logger.error(f"Error getting transactions by date range: {e}")
            return {
                'items': [],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': 0,
                    'total_pages': 0,
                    'has_prev': False,
                    'has_next': False
                }
            }
    
    def get_summary_by_date(self, start_date: date, end_date: date,
                           group_by: str = 'date') -> List[Dict[str, Any]]:
        """
        Get transaction summary grouped by specified field
        
        Args:
            start_date: Start date
            end_date: End date
            group_by: Field to group by ('date', 'psp', 'category', 'currency')
            
        Returns:
            List of summary dictionaries
        """
        try:
            # Build the query based on group_by
            if group_by == 'date':
                query = self.session.query(
                    Transaction.date,
                    func.count(Transaction.id).label('count'),
                    func.sum(Transaction.amount).label('total_amount'),
                    func.sum(Transaction.commission).label('total_commission'),
                    func.sum(Transaction.net_amount).label('total_net')
                ).filter(
                    and_(
                        Transaction.date >= start_date,
                        Transaction.date <= end_date
                    )
                ).group_by(Transaction.date).order_by(Transaction.date)
            
            elif group_by == 'psp':
                query = self.session.query(
                    Transaction.psp,
                    func.count(Transaction.id).label('count'),
                    func.sum(Transaction.amount).label('total_amount'),
                    func.sum(Transaction.commission).label('total_commission'),
                    func.sum(Transaction.net_amount).label('total_net')
                ).filter(
                    and_(
                        Transaction.date >= start_date,
                        Transaction.date <= end_date,
                        Transaction.psp.isnot(None)
                    )
                ).group_by(Transaction.psp).order_by(desc('total_amount'))
            
            elif group_by == 'category':
                query = self.session.query(
                    Transaction.category,
                    func.count(Transaction.id).label('count'),
                    func.sum(Transaction.amount).label('total_amount'),
                    func.sum(Transaction.commission).label('total_commission'),
                    func.sum(Transaction.net_amount).label('total_net')
                ).filter(
                    and_(
                        Transaction.date >= start_date,
                        Transaction.date <= end_date
                    )
                ).group_by(Transaction.category).order_by(desc('total_amount'))
            
            else:
                return []
            
            results = query.all()
            
            # Convert to dictionaries
            return [
                {
                    group_by: getattr(row, group_by if group_by != 'date' else 'date'),
                    'count': row.count,
                    'total_amount': float(row.total_amount) if row.total_amount else 0,
                    'total_commission': float(row.total_commission) if row.total_commission else 0,
                    'total_net': float(row.total_net) if row.total_net else 0
                }
                for row in results
            ]
        except Exception as e:
            logger.error(f"Error getting transaction summary: {e}")
            return []
    
    def get_by_psp(self, psp: str, start_date: date = None, end_date: date = None) -> List[Transaction]:
        """
        Get all transactions for a specific PSP
        
        Args:
            psp: PSP name
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of transactions
        """
        try:
            query = self.session.query(Transaction).filter(Transaction.psp == psp)
            
            if start_date:
                query = query.filter(Transaction.date >= start_date)
            if end_date:
                query = query.filter(Transaction.date <= end_date)
            
            return query.order_by(desc(Transaction.date)).all()
        except Exception as e:
            logger.error(f"Error getting transactions by PSP: {e}")
            return []
    
    def get_total_by_category(self, category: str, start_date: date, end_date: date) -> Decimal:
        """
        Get total amount for a specific category in date range
        
        Args:
            category: Transaction category
            start_date: Start date
            end_date: End date
            
        Returns:
            Total amount
        """
        try:
            result = self.session.query(
                func.sum(Transaction.amount)
            ).filter(
                and_(
                    Transaction.category == category,
                    Transaction.date >= start_date,
                    Transaction.date <= end_date
                )
            ).scalar()
            
            return result if result else Decimal('0')
        except Exception as e:
            logger.error(f"Error getting total by category: {e}")
            return Decimal('0')
    
    def search(self, search_term: str, limit: int = 100) -> List[Transaction]:
        """
        Search transactions by client name, notes, or other text fields
        
        Args:
            search_term: Search term
            limit: Maximum number of results
            
        Returns:
            List of matching transactions
        """
        try:
            search_pattern = f"%{search_term}%"
            query = self.session.query(Transaction).filter(
                or_(
                    ilike_compat(Transaction.client_name, search_pattern),
                    ilike_compat(Transaction.notes, search_pattern),
                    ilike_compat(Transaction.company, search_pattern)
                )
            ).order_by(desc(Transaction.date)).limit(limit)
            
            return query.all()
        except Exception as e:
            logger.error(f"Error searching transactions: {e}")
            return []
    
    def bulk_create(self, transactions_data: List[Dict[str, Any]]) -> tuple[int, int]:
        """
        Bulk create transactions
        
        Args:
            transactions_data: List of transaction dictionaries
            
        Returns:
            Tuple of (success_count, failure_count)
        """
        success_count = 0
        failure_count = 0
        
        try:
            for data in transactions_data:
                try:
                    transaction = Transaction(**data)
                    self.session.add(transaction)
                    success_count += 1
                except Exception as e:
                    logger.error(f"Error creating transaction: {e}")
                    failure_count += 1
            
            self.session.commit()
            logger.info(f"Bulk created {success_count} transactions ({failure_count} failures)")
            return success_count, failure_count
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Bulk transaction creation failed: {e}")
            return 0, len(transactions_data)


# Global transaction repository instance
transaction_repository = TransactionRepository()

def get_transaction_repository() -> TransactionRepository:
    """Get the global transaction repository"""
    return transaction_repository

