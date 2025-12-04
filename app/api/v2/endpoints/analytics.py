"""
Enhanced Analytics API endpoints for PipLinePro v2
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.services.enhanced_cache_service import cache_service, CacheKey
from app.services.event_service import event_service, EventType
import logging

logger = logging.getLogger(__name__)

analytics_api = Blueprint('analytics_api', __name__)

# Temporarily disable CSRF protection for analytics API
from app import csrf
csrf.exempt(analytics_api)

@analytics_api.route('/dashboard', methods=['GET'])
@login_required
def get_dashboard_stats():
    """Get dashboard analytics with caching"""
    try:
        # Try cache first
        cache_key = CacheKey.analytics_dashboard(current_user.id)
        cached_stats = cache_service.get(cache_key)
        
        if cached_stats:
            return jsonify({
                'status': 'success',
                'data': cached_stats,
                'cached': True
            })
        
        # Get fresh data
        from app.services.psp_analytics_service import PspAnalyticsService
        from app.models.transaction import Transaction
        from app import db
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        # Get basic stats
        total_transactions = db.session.query(func.count(Transaction.id)).scalar()
        total_amount = db.session.query(func.sum(Transaction.amount)).scalar() or 0
        avg_transaction = db.session.query(func.avg(Transaction.amount)).scalar() or 0
        
        # Get PSP summary
        psp_stats = PspAnalyticsService.get_psp_summary_stats()
        
        # Get recent trends (last 7 days)
        week_ago = datetime.now().date() - timedelta(days=7)
        recent_transactions = db.session.query(func.count(Transaction.id)).filter(
            Transaction.date >= week_ago
        ).scalar()
        
        dashboard_data = {
            'total_transactions': total_transactions,
            'total_amount': float(total_amount),
            'avg_transaction': float(avg_transaction),
            'recent_transactions': recent_transactions,
            'psp_stats': psp_stats,
            'last_updated': datetime.now().isoformat()
        }
        
        # Cache the result
        cache_service.set(cache_key, dashboard_data, ttl=1800)  # 30 minutes
        
        return jsonify({
            'status': 'success',
            'data': dashboard_data,
            'cached': False
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return jsonify({'error': 'Failed to get dashboard stats'}), 500

@analytics_api.route('/psp-summary', methods=['GET'])
@login_required
def get_psp_summary():
    """Get PSP summary analytics"""
    try:
        date = request.args.get('date')
        cache_key = CacheKey.psp_summary(date)
        cached_summary = cache_service.get(cache_key)
        
        if cached_summary:
            return jsonify({
                'status': 'success',
                'data': cached_summary,
                'cached': True
            })
        
        # Get fresh PSP summary
        from app.services.psp_analytics_service import PspAnalyticsService
        summary_data = PspAnalyticsService.get_psp_summary_stats()
        
        # Cache the result
        cache_service.set(cache_key, summary_data, ttl=3600)  # 1 hour
        
        return jsonify({
            'status': 'success',
            'data': summary_data,
            'cached': False
        })
        
    except Exception as e:
        logger.error(f"Error getting PSP summary: {e}")
        return jsonify({'error': 'Failed to get PSP summary'}), 500

@analytics_api.route('/trends', methods=['GET'])
@login_required
def get_trends():
    """Get transaction trends over time"""
    try:
        days = request.args.get('days', 30, type=int)
        
        from app.models.transaction import Transaction
        from app import db
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        # Get daily transaction trends
        start_date = datetime.now().date() - timedelta(days=days)
        
        trends = db.session.query(
            Transaction.date,
            func.count(Transaction.id).label('count'),
            func.sum(Transaction.amount).label('total_amount'),
            func.avg(Transaction.amount).label('avg_amount')
        ).filter(
            Transaction.date >= start_date
        ).group_by(Transaction.date).order_by(Transaction.date).all()
        
        trends_data = [
            {
                'date': trend.date.isoformat(),
                'count': trend.count,
                'total_amount': float(trend.total_amount or 0),
                'avg_amount': float(trend.avg_amount or 0)
            }
            for trend in trends
        ]
        
        return jsonify({
            'status': 'success',
            'data': {
                'trends': trends_data,
                'period_days': days,
                'start_date': start_date.isoformat(),
                'end_date': datetime.now().date().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting trends: {e}")
        return jsonify({'error': 'Failed to get trends'}), 500

@analytics_api.route('/reports', methods=['GET'])
@login_required
def get_reports():
    """Get various analytics reports"""
    try:
        report_type = request.args.get('type', 'summary')
        
        if report_type == 'summary':
            # Get summary report
            from app.services.psp_analytics_service import PspAnalyticsService
            report_data = PspAnalyticsService.get_psp_summary_stats()
            
        elif report_type == 'detailed':
            # Get detailed report
            from app.models.transaction import Transaction
            from app import db
            from sqlalchemy import func
            
            report_data = {
                'total_transactions': db.session.query(func.count(Transaction.id)).scalar(),
                'total_amount': float(db.session.query(func.sum(Transaction.amount)).scalar() or 0),
                'avg_transaction': float(db.session.query(func.avg(Transaction.amount)).scalar() or 0),
                'unique_clients': db.session.query(func.count(func.distinct(Transaction.client_name))).scalar(),
                'psp_breakdown': db.session.query(
                    Transaction.psp,
                    func.count(Transaction.id).label('count'),
                    func.sum(Transaction.amount).label('total')
                ).group_by(Transaction.psp).all()
            }
            
        else:
            return jsonify({'error': 'Invalid report type'}), 400
        
        return jsonify({
            'status': 'success',
            'data': report_data,
            'report_type': report_type
        })
        
    except Exception as e:
        logger.error(f"Error getting reports: {e}")
        return jsonify({'error': 'Failed to get reports'}), 500
