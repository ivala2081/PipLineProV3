"""
Query Service for PipLine Treasury System
Handles optimized database queries with caching and performance monitoring
"""
import logging
import time
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import func, and_, or_, desc, asc
from sqlalchemy.orm import joinedload, selectinload
from app import db
from app.models.transaction import Transaction
from app.models.user import User
from app.models.config import Option, UserSettings, ExchangeRate
from app.services.enhanced_cache_service import cache_service
from app.utils.db_compat import ilike_compat

# cache_invalidate helper function
def cache_invalidate(*patterns):
    for pattern in patterns:
        if pattern == 'all':
            cache_service.clear()
        else:
            cache_service.delete(pattern)

# Decimal/Float type mismatch prevention
from app.services.decimal_float_fix_service import decimal_float_service


logger = logging.getLogger(__name__)

class QueryService:
    """Optimized query service with caching and performance monitoring"""
    
    @staticmethod
    def _log_query_performance(query_name: str, start_time: float):
        """Log query performance metrics"""
        execution_time = time.time() - start_time
        if execution_time > 1.0:  # Log slow queries
            logger.warning(f"Slow query detected: {query_name} took {execution_time:.3f}s")
        else:
            logger.debug(f"Query {query_name} executed in {execution_time:.3f}s")
    
    @staticmethod
    def get_transactions_by_date_range(start_date: date, end_date: date, 
                                     page: int = 1, per_page: int = 50,
                                     filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get transactions by date range with pagination and caching"""
        start_time = time.time()
        
        try:
            query = Transaction.query.filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
            
            # Apply filters
            if filters:
                if filters.get('psp'):
                    query = query.filter(Transaction.psp == filters['psp'])
                if filters.get('category'):
                    query = query.filter(Transaction.category == filters['category'])
                if filters.get('currency'):
                    query = query.filter(Transaction.currency == filters['currency'])
                if filters.get('client_name'):
                    query = query.filter(ilike_compat(Transaction.client_name, f"%{filters['client_name']}%"))
            
            # Get total count for pagination
            total_count = query.count()
            
            # Apply pagination and ordering
            transactions = query.order_by(desc(Transaction.date), desc(Transaction.created_at))\
                               .offset((page - 1) * per_page)\
                               .limit(per_page)\
                               .all()
            
            # Convert to dictionaries
            transaction_list = [t.to_dict() for t in transactions]
            
            result = {
                'transactions': transaction_list,
                'total_count': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': (total_count + per_page - 1) // per_page
            }
            
            QueryService._log_query_performance("get_transactions_by_date_range", start_time)
            return result
            
        except Exception as e:
            logger.error(f"Error in get_transactions_by_date_range: {e}")
            raise
    
    @staticmethod
    def get_daily_summary(target_date: date, psp: str = None) -> Dict[str, Any]:
        """Get daily summary with caching"""
        start_time = time.time()
        
        try:
            summary = Transaction.get_daily_summary(target_date, psp)
            
            result = {
                'date': target_date.isoformat(),
                'psp': psp,
                'total_amount': float(summary.total_amount) if summary.total_amount else 0.0,
                'total_commission': float(summary.total_commission) if summary.total_commission else 0.0,
                'total_net': float(summary.total_net) if summary.total_net else 0.0,
                'transaction_count': summary.transaction_count or 0
            }
            
            QueryService._log_query_performance("get_daily_summary", start_time)
            return result
            
        except Exception as e:
            logger.error(f"Error in get_daily_summary: {e}")
            raise
    
    @staticmethod
    def get_psp_summary(start_date: date, end_date: date, psp: str = None) -> List[Dict[str, Any]]:
        """Get PSP summary with caching"""
        start_time = time.time()
        
        try:
            summaries = Transaction.get_psp_summary(start_date, end_date, psp)
            
            result = []
            for summary in summaries:
                result.append({
                    'psp': summary.psp,
                    'total_amount': float(summary.total_amount) if summary.total_amount else 0.0,
                    'total_commission': float(summary.total_commission) if summary.total_commission else 0.0,
                    'total_net': float(summary.total_net) if summary.total_net else 0.0,
                    'transaction_count': summary.transaction_count or 0
                })
            
            QueryService._log_query_performance("get_psp_summary", start_time)
            return result
            
        except Exception as e:
            logger.error(f"Error in get_psp_summary: {e}")
            raise
    
    @staticmethod
    def get_recent_transactions(limit: int = 10, user_id: int = None) -> List[Dict[str, Any]]:
        """Get recent transactions with caching"""
        start_time = time.time()
        
        try:
            query = Transaction.query.order_by(desc(Transaction.created_at))
            
            if user_id:
                query = query.filter(Transaction.created_by == user_id)
            
            transactions = query.limit(limit).all()
            result = [t.to_dict() for t in transactions]
            
            QueryService._log_query_performance("get_recent_transactions", start_time)
            return result
            
        except Exception as e:
            logger.error(f"Error in get_recent_transactions: {e}")
            raise
    
    @staticmethod
    def get_transaction_stats(start_date: date, end_date: date) -> Dict[str, Any]:
        """Get comprehensive transaction statistics"""
        start_time = time.time()
        
        try:
            # Get basic stats
            basic_stats = db.session.query(
                func.count(Transaction.id).label('total_transactions'),
                func.sum(Transaction.amount).label('total_amount'),
                func.sum(Transaction.commission).label('total_commission'),
                func.sum(Transaction.net_amount).label('total_net'),
                func.avg(Transaction.amount).label('avg_amount'),
                func.avg(Transaction.commission).label('avg_commission')
            ).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).first()
            
            # Get currency breakdown
            currency_stats = db.session.query(
                Transaction.currency,
                func.count(Transaction.id).label('count'),
                func.sum(Transaction.amount).label('total_amount')
            ).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(Transaction.currency).all()
            
            # Get PSP breakdown
            psp_stats = db.session.query(
                Transaction.psp,
                func.count(Transaction.id).label('count'),
                func.sum(Transaction.amount).label('total_amount')
            ).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(Transaction.psp).all()
            
            result = {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'summary': {
                    'total_transactions': basic_stats.total_transactions or 0,
                    'total_amount': float(basic_stats.total_amount) if basic_stats.total_amount else 0.0,
                    'total_commission': float(basic_stats.total_commission) if basic_stats.total_commission else 0.0,
                    'total_net': float(basic_stats.total_net) if basic_stats.total_net else 0.0,
                    'avg_amount': float(basic_stats.avg_amount) if basic_stats.avg_amount else 0.0,
                    'avg_commission': float(basic_stats.avg_commission) if basic_stats.avg_commission else 0.0
                },
                'currency_breakdown': [
                    {
                        'currency': stat.currency,
                        'count': stat.count,
                        'total_amount': float(stat.total_amount) if stat.total_amount else 0.0
                    }
                    for stat in currency_stats
                ],
                'psp_breakdown': [
                    {
                        'psp': stat.psp,
                        'count': stat.count,
                        'total_amount': float(stat.total_amount) if stat.total_amount else 0.0
                    }
                    for stat in psp_stats
                ]
            }
            
            QueryService._log_query_performance("get_transaction_stats", start_time)
            return result
            
        except Exception as e:
            logger.error(f"Error in get_transaction_stats: {e}")
            raise
    
    @staticmethod
    def invalidate_transaction_cache():
        """Invalidate all transaction-related cache entries"""
        patterns = [
            "transactions_by_date_range",
            "daily_summary", 
            "psp_summary",
            "recent_transactions",
            "transaction_stats"
        ]
        
        for pattern in patterns:
            cache_invalidate(pattern)
        
        logger.info(f"Invalidated transaction cache entries for patterns: {patterns}")
        return len(patterns) 