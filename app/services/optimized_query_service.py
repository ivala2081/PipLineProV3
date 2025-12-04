"""
Optimized Query Service for PipLine Treasury System
Handles efficient database queries with caching, batching, and SQL aggregation
"""
import logging
import time
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import func, and_, or_, desc, asc, case, cast, Float, text
from sqlalchemy.orm import joinedload, selectinload
from collections import defaultdict
from decimal import Decimal
import json

from app import db
from app.models.transaction import Transaction
from app.models.user import User
from app.models.config import Option, UserSettings, ExchangeRate
from app.models.financial import PspTrack, DailyBalance
from app.services.monitoring_service import get_monitoring_service

logger = logging.getLogger(__name__)

class OptimizedQueryService:
    """Optimized query service with caching, batching, and SQL aggregation"""
    
    def __init__(self):
        self.monitoring = get_monitoring_service()
        self.cache_service = None  # Initialize lazily
    
    def _get_cache_service(self):
        """Get cache service with proper application context handling"""
        if self.cache_service is None:
            try:
                from app.services.enhanced_cache_service import cache_service as svc
                self.cache_service = svc
            except Exception as e:
                logger.warning(f"Cache service not available: {e}")
                self.cache_service = None
        return self.cache_service
    
    def _log_query_performance(self, query_name: str, start_time: float, query_count: int = 1):
        """Log query performance metrics"""
        execution_time = time.time() - start_time
        if execution_time > 1.0:  # Log slow queries
            logger.warning(f"Slow query detected: {query_name} took {execution_time:.3f}s ({query_count} queries)")
        else:
            logger.debug(f"Query {query_name} executed in {execution_time:.3f}s ({query_count} queries)")
    
    def get_dashboard_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive dashboard metrics in a single optimized query"""
        start_time = time.time()
        
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            prev_start_date = start_date - timedelta(days=days)
            
            # Single optimized query for current period metrics
            current_metrics = db.session.query(
                func.count(Transaction.id).label('transaction_count'),
                func.sum(Transaction.amount).label('total_amount'),
                func.sum(Transaction.commission).label('total_commission'),
                func.sum(Transaction.net_amount).label('total_net'),
                func.count(func.distinct(Transaction.client_name)).label('unique_clients'),
                func.avg(Transaction.amount).label('avg_amount'),
                func.max(Transaction.date).label('latest_date'),
                func.min(Transaction.date).label('earliest_date')
            ).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).first()
            
            # Single optimized query for previous period metrics
            prev_metrics = db.session.query(
                func.count(Transaction.id).label('transaction_count'),
                func.sum(Transaction.amount).label('total_amount'),
                func.sum(Transaction.net_amount).label('total_net')
            ).filter(
                Transaction.date >= prev_start_date,
                Transaction.date < start_date
            ).first()
            
            # Single optimized query for daily trend data
            daily_trends = db.session.query(
                Transaction.date,
                func.sum(Transaction.amount).label('daily_amount'),
                func.sum(Transaction.commission).label('daily_commission'),
                func.count(Transaction.id).label('daily_count')
            ).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(Transaction.date).order_by(Transaction.date).all()
            
            # Single optimized query for recent transactions
            recent_transactions = db.session.query(Transaction).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).order_by(desc(Transaction.date)).limit(10).all()
            
            # Calculate growth percentages
            current_total = current_metrics.total_amount or Decimal('0')
            prev_total = prev_metrics.total_amount or Decimal('0')
            amount_growth = ((current_total - prev_total) / prev_total * 100) if prev_total > 0 else 0
            
            # Prepare trend data
            dates = [str(trend.date) for trend in daily_trends]
            amounts = [float(trend.daily_amount) for trend in daily_trends]
            commissions = [float(trend.daily_commission) for trend in daily_trends]
            counts = [trend.daily_count for trend in daily_trends]
            
            result = {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                },
                'metrics': {
                    'total_amount': float(current_metrics.total_amount or 0),
                    'total_commission': float(current_metrics.total_commission or 0),
                    'total_net': float(current_metrics.total_net or 0),
                    'transaction_count': current_metrics.transaction_count or 0,
                    'unique_clients': current_metrics.unique_clients or 0,
                    'avg_amount': float(current_metrics.avg_amount or 0),
                    'amount_growth': float(amount_growth),
                    'count_growth': current_metrics.transaction_count - (prev_metrics.transaction_count or 0)
                },
                'trends': {
                    'dates': dates,
                    'amounts': amounts,
                    'commissions': commissions,
                    'counts': counts
                },
                'recent_transactions': recent_transactions  # Return actual Transaction objects
            }
            
            self._log_query_performance("get_dashboard_metrics", start_time, 4)
            return result
            
        except Exception as e:
            logger.error(f"Error in get_dashboard_metrics: {e}")
            raise
    
    def get_business_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive business analytics in optimized queries"""
        start_time = time.time()
        
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            # Single optimized query for all business metrics
            business_metrics = db.session.query(
                func.count(Transaction.id).label('transaction_count'),
                func.sum(Transaction.amount).label('total_revenue'),
                func.sum(Transaction.commission).label('total_commission'),
                func.sum(Transaction.net_amount).label('net_profit'),
                func.count(func.distinct(Transaction.client_name)).label('active_clients'),
                func.avg(Transaction.amount).label('avg_transaction_value'),
                func.max(Transaction.amount).label('max_transaction'),
                func.min(Transaction.amount).label('min_transaction')
            ).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).first()
            
            # Single optimized query for daily trends with moving averages
            daily_data = db.session.query(
                Transaction.date,
                func.sum(Transaction.amount).label('daily_revenue'),
                func.sum(Transaction.commission).label('daily_commission'),
                func.count(Transaction.id).label('daily_count'),
                func.count(func.distinct(Transaction.client_name)).label('daily_clients')
            ).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(Transaction.date).order_by(Transaction.date).all()
            
            # Single optimized query for PSP breakdown
            psp_breakdown = db.session.query(
                Transaction.psp,
                func.count(Transaction.id).label('transaction_count'),
                func.sum(Transaction.amount).label('total_amount'),
                func.sum(Transaction.commission).label('total_commission'),
                func.avg(Transaction.amount).label('avg_amount')
            ).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(Transaction.psp).order_by(desc(func.sum(Transaction.amount))).all()
            
            # Calculate derived metrics
            total_revenue = business_metrics.total_revenue or Decimal('0')
            net_profit = business_metrics.net_profit or Decimal('0')
            total_commission = business_metrics.total_commission or Decimal('0')
            
            profit_margin = (total_commission / total_revenue * 100) if total_revenue > 0 else 0
            avg_daily_revenue = total_revenue / days if days > 0 else 0
            cost_ratio = (total_commission / total_revenue * 100) if total_revenue > 0 else 0
            avg_transaction_value = float(business_metrics.avg_transaction_value or 0)
            transactions_per_day = business_metrics.transaction_count / days if days > 0 else 0
            
            # Calculate moving averages for trends
            dates = [str(daily.date) for daily in daily_data]
            amounts = [float(daily.daily_revenue) for daily in daily_data]
            commissions = [float(daily.daily_commission) for daily in daily_data]
            counts = [daily.daily_count for daily in daily_data]
            
            # Calculate 7-day moving average
            window = 7
            moving_averages = []
            for i in range(len(amounts)):
                start_idx = max(0, i - window + 1)
                window_amounts = amounts[start_idx:i + 1]
                avg = sum(window_amounts) / len(window_amounts) if window_amounts else 0
                moving_averages.append(avg)
            
            # Find peak revenue day
            peak_revenue_date = max(daily_data, key=lambda x: x.daily_revenue).date if daily_data else date.today()
            
            result = {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                },
                'metrics': {
                    'total_revenue': float(total_revenue),
                    'net_profit': float(net_profit),
                    'transaction_count': business_metrics.transaction_count or 0,
                    'active_clients': business_metrics.active_clients or 0,
                    'profit_margin': float(profit_margin),
                    'avg_daily_revenue': float(avg_daily_revenue),
                    'cost_ratio': float(cost_ratio),
                    'avg_transaction_value': avg_transaction_value,
                    'transactions_per_day': transactions_per_day,
                    'max_transaction': float(business_metrics.max_transaction or 0),
                    'min_transaction': float(business_metrics.min_transaction or 0),
                    'amount_stddev': 0.0  # SQLite doesn't support stddev, set to 0
                },
                'trends': {
                    'dates': dates,
                    'amounts': amounts,
                    'commissions': commissions,
                    'counts': counts,
                    'moving_averages': moving_averages
                },
                'psp_breakdown': [
                    {
                        'psp': psp.psp or 'Unknown',
                        'transaction_count': psp.transaction_count,
                        'total_amount': float(psp.total_amount or 0),
                        'total_commission': float(psp.total_commission or 0),
                        'avg_amount': float(psp.avg_amount or 0)
                    }
                    for psp in psp_breakdown
                ],
                'peak_revenue_date': peak_revenue_date.isoformat()
            }
            
            self._log_query_performance("get_business_analytics", start_time, 3)
            return result
            
        except Exception as e:
            logger.error(f"Error in get_business_analytics: {e}")
            raise
    
    def get_psp_track_data(self, days: int = 30) -> Dict[str, Any]:
        """Get optimized PSP track data"""
        start_time = time.time()
        
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            # Single optimized query for PSP track summary
            psp_summary = db.session.query(
                Transaction.psp,
                func.count(Transaction.id).label('transaction_count'),
                func.sum(Transaction.amount).label('total_amount'),
                func.sum(Transaction.commission).label('total_commission'),
                func.sum(Transaction.net_amount).label('total_net'),
                func.avg(Transaction.amount).label('avg_amount'),
                func.max(Transaction.date).label('latest_date'),
                func.min(Transaction.date).label('earliest_date')
            ).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(Transaction.psp).order_by(desc(func.sum(Transaction.amount))).all()
            
            # Single optimized query for daily PSP data
            daily_psp_data = db.session.query(
                Transaction.date,
                Transaction.psp,
                func.sum(Transaction.amount).label('daily_amount'),
                func.sum(Transaction.commission).label('daily_commission'),
                func.count(Transaction.id).label('daily_count')
            ).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(Transaction.date, Transaction.psp).order_by(Transaction.date).all()
            
            # Process summary data
            summary_data = []
            total_active_psps = 0
            total_allocation = Decimal('0')
            total_rollover = Decimal('0')
            
            for psp in psp_summary:
                if psp.psp:  # Skip null PSPs
                    total_active_psps += 1
                    total_allocation += psp.total_amount or Decimal('0')
                    
                    summary_data.append({
                        'psp': psp.psp,
                        'transaction_count': psp.transaction_count,
                        'total_amount': float(psp.total_amount or 0),
                        'total_commission': float(psp.total_commission or 0),
                        'total_net': float(psp.total_net or 0),
                        'avg_amount': float(psp.avg_amount or 0),
                        'latest_date': psp.latest_date.isoformat() if psp.latest_date else None,
                        'earliest_date': psp.earliest_date.isoformat() if psp.earliest_date else None,
                        'withdraw': 0,  # Default value for compatibility
                        'allocation': float(psp.total_amount or 0),
                        'rollover': 0  # Default value for compatibility
                    })
            
            # Process daily data
            daily_data = defaultdict(lambda: {
                'date': None,
                'psps': defaultdict(lambda: {
                    'amount': Decimal('0'),
                    'commission': Decimal('0'),
                    'count': 0
                })
            })
            
            for daily in daily_psp_data:
                daily_data[daily.date]['date'] = daily.date
                daily_data[daily.date]['psps'][daily.psp or 'Unknown'] = {
                    'amount': daily.daily_amount or Decimal('0'),
                    'commission': daily.daily_commission or Decimal('0'),
                    'count': daily.daily_count
                }
            
            # Convert to list format
            daily_list = []
            for date_obj, data in sorted(daily_data.items()):
                daily_entry = {
                    'date': date_obj.isoformat(),
                    'psps': {}
                }
                for psp, psp_data in data['psps'].items():
                    daily_entry['psps'][psp] = {
                        'amount': float(psp_data['amount']),
                        'commission': float(psp_data['commission']),
                        'count': psp_data['count']
                    }
                daily_list.append(daily_entry)
            
            result = {
                'summary_data': summary_data,
                'daily_data': daily_list,
                'overview_data': {
                    'total_active_psps': total_active_psps,
                    'total_allocation': float(total_allocation),
                    'total_rollover': float(total_rollover),
                    'avg_allocation': float(total_allocation / total_active_psps) if total_active_psps > 0 else 0,
                    'psps': {psp.psp: {
                        'total_amount': float(psp.total_amount or 0),
                        'transaction_count': psp.transaction_count,
                        'avg_amount': float(psp.avg_amount or 0)
                    } for psp in psp_summary if psp.psp}
                }
            }
            
            self._log_query_performance("get_psp_track_data", start_time, 2)
            return result
            
        except Exception as e:
            logger.error(f"Error in get_psp_track_data: {e}")
            raise
    
    def get_transaction_stats(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get comprehensive transaction statistics with optimized queries"""
        start_time = time.time()
        
        try:
            # Single optimized query for all statistics
            stats = db.session.query(
                func.count(Transaction.id).label('total_transactions'),
                func.sum(Transaction.amount).label('total_amount'),
                func.sum(Transaction.commission).label('total_commission'),
                func.sum(Transaction.net_amount).label('total_net'),
                func.avg(Transaction.amount).label('avg_amount'),
                func.avg(Transaction.commission).label('avg_commission'),
                func.count(func.distinct(Transaction.client_name)).label('unique_clients'),
                func.count(func.distinct(Transaction.psp)).label('unique_psps'),
                func.count(func.distinct(Transaction.currency)).label('unique_currencies')
            ).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).first()
            
            # Single optimized query for currency breakdown
            currency_stats = db.session.query(
                Transaction.currency,
                func.count(Transaction.id).label('count'),
                func.sum(Transaction.amount).label('total_amount'),
                func.avg(Transaction.amount).label('avg_amount')
            ).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(Transaction.currency).all()
            
            # Single optimized query for PSP breakdown
            psp_stats = db.session.query(
                Transaction.psp,
                func.count(Transaction.id).label('count'),
                func.sum(Transaction.amount).label('total_amount'),
                func.avg(Transaction.amount).label('avg_amount')
            ).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(Transaction.psp).all()
            
            # Single optimized query for daily trends
            daily_trends = db.session.query(
                Transaction.date,
                func.count(Transaction.id).label('count'),
                func.sum(Transaction.amount).label('amount'),
                func.sum(Transaction.commission).label('commission')
            ).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(Transaction.date).order_by(Transaction.date).all()
            
            result = {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'summary': {
                    'total_transactions': stats.total_transactions or 0,
                    'total_amount': float(stats.total_amount or 0),
                    'total_commission': float(stats.total_commission or 0),
                    'total_net': float(stats.total_net or 0),
                    'avg_amount': float(stats.avg_amount or 0),
                    'avg_commission': float(stats.avg_commission or 0),
                    'unique_clients': stats.unique_clients or 0,
                    'unique_psps': stats.unique_psps or 0,
                    'unique_currencies': stats.unique_currencies or 0
                },
                'currency_breakdown': [
                    {
                        'currency': stat.currency,
                        'count': stat.count,
                        'total_amount': float(stat.total_amount or 0),
                        'avg_amount': float(stat.avg_amount or 0)
                    }
                    for stat in currency_stats
                ],
                'psp_breakdown': [
                    {
                        'psp': stat.psp or 'Unknown',
                        'count': stat.count,
                        'total_amount': float(stat.total_amount or 0),
                        'avg_amount': float(stat.avg_amount or 0)
                    }
                    for stat in psp_stats
                ],
                'daily_trends': [
                    {
                        'date': trend.date.isoformat(),
                        'count': trend.count,
                        'amount': float(trend.amount or 0),
                        'commission': float(trend.commission or 0)
                    }
                    for trend in daily_trends
                ]
            }
            
            self._log_query_performance("get_transaction_stats", start_time, 4)
            return result
            
        except Exception as e:
            logger.error(f"Error in get_transaction_stats: {e}")
            raise
    
    def invalidate_cache(self, pattern: str = None):
        """Invalidate cache for specific patterns"""
        try:
            cache_service = self._get_cache_service()
            if cache_service:
                if pattern:
                    cache_service.invalidate_pattern(pattern)
                else:
                    # Invalidate all analytics cache
                    patterns = [
                        "dashboard_metrics",
                        "business_analytics", 
                        "psp_track_data",
                        "transaction_stats"
                    ]
                    for p in patterns:
                        cache_service.invalidate_pattern(p)
                logger.info(f"Cache invalidated for pattern: {pattern or 'all analytics'}")
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")

# Global instance
optimized_query_service = OptimizedQueryService() 