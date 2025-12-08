"""
Real-time analytics service for PipLinePro
"""
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
import threading
from app import db
from app.models.transaction import Transaction
from app.models.financial import PspTrack, PSPAllocation
from sqlalchemy import func, text

logger = logging.getLogger(__name__)

class RealTimeAnalyticsService:
    """
    Real-time analytics service for live dashboard updates
    """
    
    def __init__(self):
        self._metrics_cache = {}
        self._cache_lock = threading.RLock()
        self._cache_ttl = 30  # 30 seconds cache
        self._last_update = 0
        
        # Real-time data streams
        self._transaction_stream = deque(maxlen=1000)  # Last 1000 transactions
        self._revenue_stream = deque(maxlen=1440)  # Last 24 hours (1-minute intervals)
        self._psp_performance = defaultdict(lambda: deque(maxlen=100))
        
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time analytics metrics"""
        current_time = time.time()
        
        with self._cache_lock:
            # Check if cache is still valid
            if current_time - self._last_update < self._cache_ttl and self._metrics_cache:
                return self._metrics_cache
            
            # Update metrics
            self._update_real_time_metrics()
            self._last_update = current_time
            
            return self._metrics_cache
    
    def _update_real_time_metrics(self):
        """Update real-time metrics from database"""
        try:
            now = datetime.now(timezone.utc)
            today = now.date()
            current_hour = now.hour
            
            # Get today's transactions
            today_transactions = db.session.query(Transaction).filter(
                Transaction.date == today
            ).all()
            
            # Calculate real-time metrics
            metrics = {
                'timestamp': now.isoformat(),
                'today': {
                    'total_transactions': len(today_transactions),
                    'total_revenue': sum(float(t.amount) for t in today_transactions),
                    'average_transaction': 0,
                    'hourly_breakdown': self._get_hourly_breakdown(today_transactions),
                    'psp_breakdown': self._get_psp_breakdown(today_transactions),
                    'currency_breakdown': self._get_currency_breakdown(today_transactions)
                },
                'recent_activity': {
                    'last_hour_transactions': self._get_last_hour_count(),
                    'last_5_minutes': self._get_recent_transactions(5),
                    'active_psps': self._get_active_psps(),
                    'top_clients': self._get_top_clients_today()
                },
                'performance': {
                    'response_time_avg': self._get_avg_response_time(),
                    'error_rate': self._get_error_rate(),
                    'cache_hit_rate': self._get_cache_hit_rate(),
                    'database_connections': self._get_db_connection_count()
                },
                'alerts': self._get_active_alerts(),
                'trends': self._calculate_trends()
            }
            
            # Calculate average transaction
            if metrics['today']['total_transactions'] > 0:
                metrics['today']['average_transaction'] = (
                    metrics['today']['total_revenue'] / metrics['today']['total_transactions']
                )
            
            self._metrics_cache = metrics
            
        except Exception as e:
            logger.error(f"Error updating real-time metrics: {e}")
            self._metrics_cache = {'error': str(e), 'timestamp': datetime.now(timezone.utc).isoformat()}
    
    def _get_hourly_breakdown(self, transactions: List[Transaction]) -> List[Dict[str, Any]]:
        """Get hourly breakdown of transactions"""
        hourly_data = defaultdict(lambda: {'count': 0, 'amount': 0.0})
        
        for transaction in transactions:
            hour = transaction.created_at.hour if transaction.created_at else 0
            hourly_data[hour]['count'] += 1
            hourly_data[hour]['amount'] += float(transaction.amount)
        
        return [
            {
                'hour': hour,
                'transactions': data['count'],
                'revenue': data['amount']
            }
            for hour, data in sorted(hourly_data.items())
        ]
    
    def _get_psp_breakdown(self, transactions: List[Transaction]) -> List[Dict[str, Any]]:
        """Get PSP breakdown for today"""
        psp_data = defaultdict(lambda: {'count': 0, 'amount': 0.0})
        
        for transaction in transactions:
            if transaction.psp:
                psp_data[transaction.psp]['count'] += 1
                psp_data[transaction.psp]['amount'] += float(transaction.amount)
        
        total_amount = sum(data['amount'] for data in psp_data.values())
        
        return [
            {
                'psp': psp,
                'transactions': data['count'],
                'revenue': data['amount'],
                'percentage': (data['amount'] / total_amount * 100) if total_amount > 0 else 0
            }
            for psp, data in sorted(psp_data.items(), key=lambda x: x[1]['amount'], reverse=True)
        ]
    
    def _get_currency_breakdown(self, transactions: List[Transaction]) -> List[Dict[str, Any]]:
        """Get currency breakdown for today"""
        currency_data = defaultdict(lambda: {'count': 0, 'amount': 0.0})
        
        for transaction in transactions:
            currency = transaction.currency or 'TRY'
            currency_data[currency]['count'] += 1
            currency_data[currency]['amount'] += float(transaction.amount)
        
        return [
            {
                'currency': currency,
                'transactions': data['count'],
                'revenue': data['amount']
            }
            for currency, data in sorted(currency_data.items(), key=lambda x: x[1]['amount'], reverse=True)
        ]
    
    def _get_last_hour_count(self) -> int:
        """Get transaction count for last hour"""
        try:
            one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
            count = db.session.query(Transaction).filter(
                Transaction.created_at >= one_hour_ago
            ).count()
            return count
        except Exception as e:
            logger.error(f"Error getting last hour count: {e}")
            return 0
    
    def _get_recent_transactions(self, minutes: int) -> List[Dict[str, Any]]:
        """Get recent transactions within specified minutes"""
        try:
            time_threshold = datetime.now(timezone.utc) - timedelta(minutes=minutes)
            transactions = db.session.query(Transaction).filter(
                Transaction.created_at >= time_threshold
            ).order_by(Transaction.created_at.desc()).limit(10).all()
            
            return [
                {
                    'id': t.id,
                    'amount': float(t.amount),
                    'currency': t.currency,
                    'psp': t.psp,
                    'client_name': t.client_name,
                    'created_at': t.created_at.isoformat() if t.created_at else None
                }
                for t in transactions
            ]
        except Exception as e:
            logger.error(f"Error getting recent transactions: {e}")
            return []
    
    def _get_active_psps(self) -> List[str]:
        """Get list of active PSPs today"""
        try:
            today = datetime.now(timezone.utc).date()
            psps = db.session.query(Transaction.psp).filter(
                Transaction.date == today,
                Transaction.psp.isnot(None),
                Transaction.psp != ''
            ).distinct().all()
            
            return [psp[0] for psp in psps if psp[0]]
        except Exception as e:
            logger.error(f"Error getting active PSPs: {e}")
            return []
    
    def _get_top_clients_today(self) -> List[Dict[str, Any]]:
        """Get top clients by transaction count today"""
        try:
            today = datetime.now(timezone.utc).date()
            client_stats = db.session.query(
                Transaction.client_name,
                func.count(Transaction.id).label('transaction_count'),
                func.sum(Transaction.amount).label('total_amount')
            ).filter(
                Transaction.date == today,
                Transaction.client_name.isnot(None),
                Transaction.client_name != ''
            ).group_by(Transaction.client_name).order_by(
                func.count(Transaction.id).desc()
            ).limit(5).all()
            
            return [
                {
                    'client_name': stat.client_name,
                    'transaction_count': stat.transaction_count,
                    'total_amount': float(stat.total_amount)
                }
                for stat in client_stats
            ]
        except Exception as e:
            logger.error(f"Error getting top clients: {e}")
            return []
    
    def _get_avg_response_time(self) -> float:
        """Get average API response time (mock data for now)"""
        # This would typically come from monitoring middleware
        return 0.15  # 150ms average
    
    def _get_error_rate(self) -> float:
        """Get current error rate percentage"""
        # This would typically come from error tracking
        return 0.1  # 0.1% error rate
    
    def _get_cache_hit_rate(self) -> float:
        """Get cache hit rate percentage"""
        # This would come from cache service metrics
        return 85.5  # 85.5% cache hit rate
    
    def _get_db_connection_count(self) -> int:
        """Get current database connection count"""
        # This would come from database pool metrics
        return 5  # 5 active connections
    
    def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active system alerts"""
        alerts = []
        
        # Check for high error rate
        if self._get_error_rate() > 5.0:
            alerts.append({
                'type': 'error_rate',
                'severity': 'high',
                'message': 'High error rate detected',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        
        # Check for low cache hit rate
        if self._get_cache_hit_rate() < 70.0:
            alerts.append({
                'type': 'cache_performance',
                'severity': 'medium',
                'message': 'Low cache hit rate',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        
        # Check for high response time
        if self._get_avg_response_time() > 1.0:
            alerts.append({
                'type': 'performance',
                'severity': 'medium',
                'message': 'High response time detected',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        
        return alerts
    
    def _calculate_trends(self) -> Dict[str, Any]:
        """Calculate trend data"""
        try:
            now = datetime.now(timezone.utc)
            yesterday = now - timedelta(days=1)
            week_ago = now - timedelta(days=7)
            
            # Today vs Yesterday
            today_count = db.session.query(Transaction).filter(
                Transaction.date == now.date()
            ).count()
            
            yesterday_count = db.session.query(Transaction).filter(
                Transaction.date == yesterday.date()
            ).count()
            
            # This week vs Last week
            this_week_start = now - timedelta(days=now.weekday())
            last_week_start = this_week_start - timedelta(days=7)
            last_week_end = this_week_start - timedelta(days=1)
            
            this_week_count = db.session.query(Transaction).filter(
                Transaction.date >= this_week_start.date()
            ).count()
            
            last_week_count = db.session.query(Transaction).filter(
                Transaction.date >= last_week_start.date(),
                Transaction.date <= last_week_end.date()
            ).count()
            
            return {
                'daily_change': {
                    'transactions': self._calculate_percentage_change(today_count, yesterday_count),
                    'direction': 'up' if today_count > yesterday_count else 'down'
                },
                'weekly_change': {
                    'transactions': self._calculate_percentage_change(this_week_count, last_week_count),
                    'direction': 'up' if this_week_count > last_week_count else 'down'
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating trends: {e}")
            return {
                'daily_change': {'transactions': 0, 'direction': 'stable'},
                'weekly_change': {'transactions': 0, 'direction': 'stable'}
            }
    
    def _calculate_percentage_change(self, current: int, previous: int) -> float:
        """Calculate percentage change between two values"""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return ((current - previous) / previous) * 100
    
    def get_psp_performance_stream(self, psp_name: str) -> List[Dict[str, Any]]:
        """Get real-time performance stream for a specific PSP"""
        try:
            # Get recent transactions for this PSP
            recent_transactions = db.session.query(Transaction).filter(
                Transaction.psp == psp_name,
                Transaction.created_at >= datetime.now(timezone.utc) - timedelta(hours=24)
            ).order_by(Transaction.created_at.desc()).limit(100).all()
            
            return [
                {
                    'timestamp': t.created_at.isoformat() if t.created_at else None,
                    'amount': float(t.amount),
                    'currency': t.currency,
                    'client_name': t.client_name
                }
                for t in recent_transactions
            ]
        except Exception as e:
            logger.error(f"Error getting PSP performance stream: {e}")
            return []
    
    def get_revenue_stream(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get revenue stream for the last N hours"""
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=hours)
            
            # Get hourly revenue data
            hourly_revenue = db.session.query(
                func.date_trunc('hour', Transaction.created_at).label('hour'),
                func.count(Transaction.id).label('transaction_count'),
                func.sum(Transaction.amount).label('total_amount')
            ).filter(
                Transaction.created_at >= start_time,
                Transaction.created_at <= end_time
            ).group_by(
                func.date_trunc('hour', Transaction.created_at)
            ).order_by('hour').all()
            
            return [
                {
                    'hour': row.hour.isoformat() if row.hour else None,
                    'transaction_count': row.transaction_count,
                    'revenue': float(row.total_amount) if row.total_amount else 0.0
                }
                for row in hourly_revenue
            ]
        except Exception as e:
            logger.error(f"Error getting revenue stream: {e}")
            return []

# Global real-time analytics service
real_time_analytics = RealTimeAnalyticsService()

def get_real_time_analytics() -> RealTimeAnalyticsService:
    """Get the global real-time analytics service"""
    return real_time_analytics
