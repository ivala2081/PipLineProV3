"""
Enhanced AI Assistant Service for PipLinePro
Provides comprehensive READ-ONLY access to all project sections except security parts

SECURITY NOTE: This service has READ-ONLY access to the database.
No INSERT, UPDATE, or DELETE operations are permitted.
All database queries use SELECT statements only.
"""

import os
import json
import asyncio
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, desc, and_, or_, text
from sqlalchemy.orm import Session
from openai import OpenAI

from app import db
from app.models.transaction import Transaction
from app.models.user import User
from app.models.config import ExchangeRate, Option
from app.models.financial import PspTrack, DailyBalance, PSPAllocation
from app.models.audit import AuditLog
from app.utils.unified_logger import get_logger
from app.services.chatgpt_service import ChatGPTService
from app.utils.db_compat import extract_compat

logger = get_logger(__name__)


def read_only_query(func):
    """
    Decorator to ensure database operations are read-only.
    Prevents any write operations (INSERT, UPDATE, DELETE) from being executed.
    """
    def wrapper(*args, **kwargs):
        try:
            # Execute the query function
            result = func(*args, **kwargs)
            
            # Ensure session doesn't have any pending changes
            if db.session.dirty or db.session.new or db.session.deleted:
                logger.error(f"READ-ONLY VIOLATION: Function {func.__name__} attempted to modify database")
                db.session.rollback()
                raise PermissionError(f"Read-only access violation in {func.__name__}")
            
            return result
        except PermissionError:
            raise
        except Exception as e:
            # Log the error but don't expose internal details
            logger.error(f"Error in read-only query {func.__name__}: {e}")
            raise
    return wrapper


class EnhancedAIAssistantService:
    """
    Enhanced AI Assistant with comprehensive READ-ONLY access to PipLinePro data
    
    SECURITY FEATURES:
    - READ-ONLY database access (no INSERT, UPDATE, or DELETE operations)
    - Excludes all security-related data (passwords, tokens, auth data)
    - All queries are validated to prevent write operations
    - No access to sensitive user credentials or security configurations
    """
    
    def __init__(self):
        """Initialize the enhanced AI assistant service with read-only access"""
        self.chatgpt_service = ChatGPTService()
        self.client = self.chatgpt_service.client if self.chatgpt_service.is_configured() else None
        self.read_only = True  # Enforce read-only mode
        
        # Define accessible sections (excluding security)
        self.accessible_sections = {
            'transactions': self._get_transaction_data,
            'analytics': self._get_analytics_data,
            'financial_performance': self._get_financial_performance_data,
            'psp_tracking': self._get_psp_tracking_data,
            'exchange_rates': self._get_exchange_rate_data,
            'user_management': self._get_user_management_data,
            'system_monitoring': self._get_system_monitoring_data,
            'business_insights': self._get_business_insights_data,
            'reports': self._get_reports_data,
            'configuration': self._get_configuration_data,
            'client_search': self._search_client_transactions
        }
        
        logger.info("✅ Enhanced AI Assistant Service initialized (READ-ONLY mode)")
    
    def is_configured(self) -> bool:
        """Check if the service is properly configured"""
        return self.chatgpt_service.is_configured()
    
    def test_database_connection(self) -> bool:
        """Test database connection for read-only access"""
        try:
            from app.models.transaction import Transaction
            
            # Test read-only query
            count = db.session.query(func.count(Transaction.id)).scalar()
            
            # Verify no pending changes (ensures read-only)
            if db.session.dirty or db.session.new or db.session.deleted:
                logger.error("READ-ONLY VIOLATION: Session has pending changes during connection test")
                db.session.rollback()
                return False
            
            logger.info(f"✅ Database connection test successful (READ-ONLY verified). Transaction count: {count}")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            return False
    
    async def process_query(self, query: str, context: Dict[str, Any] = None) -> Optional[str]:
        """
        Process user queries with comprehensive project context
        
        Args:
            query: User's question or request
            context: Additional context for the query
            
        Returns:
            AI response with relevant project data
        """
        if not self.is_configured():
            return "AI Assistant is not configured. Please contact your administrator."
        
        try:
            # Gather relevant data based on query analysis
            relevant_data = await self._gather_relevant_data(query)
            
            # Build comprehensive system context
            system_context = self._build_system_context(relevant_data)
            
            # Create enhanced prompt with project data
            enhanced_prompt = self._build_enhanced_prompt(query, system_context, context)
            
            # Generate AI response
            messages = [
                {
                    "role": "system",
                    "content": self._get_system_prompt()
                },
                {
                    "role": "user",
                    "content": enhanced_prompt
                }
            ]
            
            response = await self.chatgpt_service.chat(messages)
            return response
            
        except Exception as e:
            logger.error(f"Error processing AI query: {e}")
            logger.error(f"Query was: {query}")
            logger.error(f"Context was: {context}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {str(e)}")
            
            # Check if it's a database-related error
            if "database" in str(e).lower() or "connection" in str(e).lower():
                return "I'm experiencing a database connection issue. Please try again in a moment."
            elif "timeout" in str(e).lower():
                return "The request timed out. Please try again with a shorter query."
            else:
                return f"I encountered an error while processing your request: {str(e)}. Please try again or contact support if the issue persists."
    
    async def _gather_relevant_data(self, query: str) -> Dict[str, Any]:
        """Gather relevant data based on query analysis"""
        relevant_data = {}
        
        try:
            # Analyze query to determine which sections to include
            query_lower = query.lower()
            
            # Transaction-related queries
            if any(keyword in query_lower for keyword in ['transaction', 'payment', 'revenue', 'income', 'expense']):
                try:
                    relevant_data['transactions'] = await self._get_transaction_data()
                except Exception as e:
                    logger.error(f"Error getting transaction data: {e}")
                    relevant_data['transactions'] = {'error': str(e)}
            
            # Client-specific queries - look for names in the query
            import re
            # Common name patterns
            name_patterns = [
                r'\b[a-zA-Z]+\s+[a-zA-Z]+\s+[a-zA-Z]+\b',  # Three words (e.g., "Fevzi Can Bayram")
                r'\b[a-zA-Z]+\s+[a-zA-Z]+\b',  # Two words (e.g., "John Smith")
            ]
            
            # Find potential names in the query
            matches = []
            for pattern in name_patterns:
                matches.extend(re.findall(pattern, query, re.IGNORECASE))
            
            # If we found potential names, search for client transactions
            for match in matches:
                # Check if this looks like a person's name (not common words)
                common_words = ['show', 'give', 'get', 'all', 'transactions', 'for', 'of', 'the', 'a', 'an', 'and', 'or', 'but']
                words = match.lower().split()
                if not any(word in common_words for word in words):
                    # This looks like a client name, search for it
                    logger.info(f"Searching for client: {match}")
                    try:
                        client_search_data = await self._search_client_transactions(match)
                        if client_search_data and 'error' not in client_search_data:
                            logger.info(f"Found client data for {match}: {len(client_search_data.get('exact_matches', []))} exact matches, {len(client_search_data.get('partial_matches', []))} partial matches")
                            relevant_data['client_search'] = client_search_data
                        else:
                            logger.info(f"No client data found for {match}")
                            # Still include the search result even if no matches found
                            relevant_data['client_search'] = {
                                'search_term': match,
                                'exact_matches': [],
                                'partial_matches': [],
                                'similar_clients': [],
                                'message': f'No transactions found for client "{match}"'
                            }
                        break
                    except Exception as search_error:
                        logger.error(f"Error searching for client {match}: {search_error}")
                        continue
        
            # Analytics-related queries
            if any(keyword in query_lower for keyword in ['analytics', 'report', 'statistics', 'metrics', 'dashboard']):
                try:
                    relevant_data['analytics'] = await self._get_analytics_data()
                except Exception as e:
                    logger.error(f"Error getting analytics data: {e}")
                    relevant_data['analytics'] = {'error': str(e)}
                
                try:
                    relevant_data['business_insights'] = await self._get_business_insights_data()
                except Exception as e:
                    logger.error(f"Error getting business insights data: {e}")
                    relevant_data['business_insights'] = {'error': str(e)}
            
            # Financial performance queries
            if any(keyword in query_lower for keyword in ['performance', 'profit', 'commission', 'net', 'gross']):
                try:
                    relevant_data['financial_performance'] = await self._get_financial_performance_data()
                except Exception as e:
                    logger.error(f"Error getting financial performance data: {e}")
                    relevant_data['financial_performance'] = {'error': str(e)}
            
            # PSP-related queries
            if any(keyword in query_lower for keyword in ['psp', 'provider', 'payment service', 'tracking']):
                try:
                    relevant_data['psp_tracking'] = await self._get_psp_tracking_data()
                except Exception as e:
                    logger.error(f"Error getting PSP tracking data: {e}")
                    relevant_data['psp_tracking'] = {'error': str(e)}
            
            # Exchange rate queries
            if any(keyword in query_lower for keyword in ['exchange', 'currency', 'rate', 'conversion']):
                try:
                    relevant_data['exchange_rates'] = await self._get_exchange_rate_data()
                except Exception as e:
                    logger.error(f"Error getting exchange rate data: {e}")
                    relevant_data['exchange_rates'] = {'error': str(e)}
            
            # User management queries (non-security)
            if any(keyword in query_lower for keyword in ['user', 'admin', 'permission', 'role']):
                try:
                    relevant_data['user_management'] = await self._get_user_management_data()
                except Exception as e:
                    logger.error(f"Error getting user management data: {e}")
                    relevant_data['user_management'] = {'error': str(e)}
            
            # System monitoring queries
            if any(keyword in query_lower for keyword in ['system', 'performance', 'monitoring', 'health']):
                try:
                    relevant_data['system_monitoring'] = await self._get_system_monitoring_data()
                except Exception as e:
                    logger.error(f"Error getting system monitoring data: {e}")
                    relevant_data['system_monitoring'] = {'error': str(e)}
            
            # Configuration queries
            if any(keyword in query_lower for keyword in ['setting', 'config', 'option', 'dropdown']):
                try:
                    relevant_data['configuration'] = await self._get_configuration_data()
                except Exception as e:
                    logger.error(f"Error getting configuration data: {e}")
                    relevant_data['configuration'] = {'error': str(e)}
            
            # If no specific keywords, include basic dashboard data
            if not relevant_data:
                try:
                    relevant_data['analytics'] = await self._get_analytics_data()
                    relevant_data['financial_performance'] = await self._get_financial_performance_data()
                except Exception as e:
                    logger.error(f"Error getting default data: {e}")
                    relevant_data = {'error': f"Failed to get default data: {str(e)}"}
            
        except Exception as e:
            logger.error(f"Error in _gather_relevant_data: {e}")
            relevant_data = {'error': f"Failed to gather relevant data: {str(e)}"}
        
        return relevant_data
    
    @read_only_query
    async def _get_transaction_data(self) -> Dict[str, Any]:
        """Get transaction-related data (READ-ONLY access)"""
        try:
            # Recent transactions summary
            recent_transactions = db.session.query(Transaction).order_by(desc(Transaction.date)).limit(10).all()
            
            # Transaction statistics
            total_transactions = db.session.query(func.count(Transaction.id)).scalar()
            
            # Amount statistics
            amount_stats = db.session.query(
                func.sum(Transaction.amount).label('total_amount'),
                func.avg(Transaction.amount).label('avg_amount'),
                func.max(Transaction.amount).label('max_amount'),
                func.min(Transaction.amount).label('min_amount')
            ).first()
            
            # Category breakdown
            category_stats = db.session.query(
                Transaction.category,
                func.count(Transaction.id).label('count'),
                func.sum(Transaction.amount).label('total')
            ).group_by(Transaction.category).all()
            
            # Currency breakdown
            currency_stats = db.session.query(
                Transaction.currency,
                func.count(Transaction.id).label('count'),
                func.sum(Transaction.amount).label('total')
            ).group_by(Transaction.currency).all()
            
            # Client names breakdown (to help with search)
            client_stats = db.session.query(
                Transaction.client_name,
                func.count(Transaction.id).label('count'),
                func.sum(Transaction.amount).label('total')
            ).filter(
                Transaction.client_name.isnot(None),
                Transaction.client_name != ''
            ).group_by(Transaction.client_name).order_by(desc('count')).limit(20).all()
            
            # Search for specific client patterns
            search_patterns = ['fevzi', 'can', 'bayram', 'fevzi can', 'can bayram', 'fevzi can bayram']
            matching_clients = []
            
            for pattern in search_patterns:
                matching = db.session.query(Transaction.client_name).filter(
                    func.lower(Transaction.client_name).like(f'%{pattern.lower()}%')
                ).distinct().limit(5).all()
                matching_clients.extend([row.client_name for row in matching])
            
            # Remove duplicates and get transaction details for matching clients
            unique_matching_clients = list(set(matching_clients))
            client_transactions = []
            
            for client_name in unique_matching_clients[:5]:  # Limit to 5 clients
                client_txns = db.session.query(Transaction).filter(
                    Transaction.client_name == client_name
                ).order_by(desc(Transaction.date)).limit(10).all()
                
                client_transactions.extend([
                    {
                        'id': txn.id,
                        'amount': float(txn.amount),
                        'currency': txn.currency,
                        'category': txn.category,
                        'client_name': txn.client_name,
                        'date': txn.date.isoformat() if txn.date else None,
                        'notes': txn.notes,
                        'psp': txn.psp,
                        'payment_method': txn.payment_method
                    } for txn in client_txns
                ])
            
            return {
                'total_transactions': total_transactions,
                'amount_stats': {
                    'total_amount': float(amount_stats.total_amount or 0),
                    'avg_amount': float(amount_stats.avg_amount or 0),
                    'max_amount': float(amount_stats.max_amount or 0),
                    'min_amount': float(amount_stats.min_amount or 0)
                },
                'category_breakdown': [
                    {
                        'category': cat.category,
                        'count': cat.count,
                        'total': float(cat.total or 0)
                    } for cat in category_stats
                ],
                'currency_breakdown': [
                    {
                        'currency': curr.currency,
                        'count': curr.count,
                        'total': float(curr.total or 0)
                    } for curr in currency_stats
                ],
                'client_breakdown': [
                    {
                        'client_name': client.client_name,
                        'count': client.count,
                        'total': float(client.total or 0)
                    } for client in client_stats
                ],
                'matching_clients': unique_matching_clients,
                'client_transactions': client_transactions,
                'recent_transactions': [
                    {
                        'id': txn.id,
                        'amount': float(txn.amount),
                        'currency': txn.currency,
                        'category': txn.category,
                        'client_name': txn.client_name,
                        'date': txn.date.isoformat() if txn.date else None,
                        'notes': txn.notes,
                        'psp': txn.psp,
                        'payment_method': txn.payment_method
                    } for txn in recent_transactions
                ]
            }
        except Exception as e:
            logger.error(f"Error getting transaction data: {e}")
            return {'error': str(e)}
    
    @read_only_query
    async def _get_analytics_data(self) -> Dict[str, Any]:
        """Get analytics and dashboard data (READ-ONLY access)"""
        try:
            # Date range for analytics (last 30 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            # Daily transaction totals
            daily_stats = db.session.query(
                func.date(Transaction.date).label('date'),
                func.count(Transaction.id).label('transaction_count'),
                func.sum(Transaction.amount).label('total_amount')
            ).filter(
                and_(
                    Transaction.date >= start_date,
                    Transaction.date <= end_date
                )
            ).group_by(func.date(Transaction.date)).order_by('date').all()
            
            # PSP performance
            psp_stats = db.session.query(
                PspTrack.psp_name,
                func.sum(PspTrack.amount).label('total_amount'),
                func.count(PspTrack.id).label('transaction_count')
            ).filter(
                and_(
                    PspTrack.date >= start_date,
                    PspTrack.date <= end_date
                )
            ).group_by(PspTrack.psp_name).all()
            
            # Daily balance trends
            balance_trends = db.session.query(
                DailyBalance.date,
                func.sum(DailyBalance.balance).label('total_balance')
            ).filter(
                and_(
                    DailyBalance.date >= start_date,
                    DailyBalance.date <= end_date
                )
            ).group_by(DailyBalance.date).order_by(DailyBalance.date).all()
            
            return {
                'daily_stats': [
                    {
                        'date': stat.date.isoformat(),
                        'transaction_count': stat.transaction_count,
                        'total_amount': float(stat.total_amount or 0)
                    } for stat in daily_stats
                ],
                'psp_performance': [
                    {
                        'psp': psp.psp_name,
                        'total_amount': float(psp.total_amount or 0),
                        'transaction_count': psp.transaction_count
                    } for psp in psp_stats
                ],
                'balance_trends': [
                    {
                        'date': trend.date.isoformat(),
                        'total_balance': float(trend.total_balance or 0)
                    } for trend in balance_trends
                ],
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': 30
                }
            }
        except Exception as e:
            logger.error(f"Error getting analytics data: {e}")
            return {'error': str(e)}
    
    @read_only_query
    async def _get_financial_performance_data(self) -> Dict[str, Any]:
        """Get financial performance metrics (READ-ONLY access)"""
        try:
            # Commission calculations
            commission_stats = db.session.query(
                func.sum(Transaction.commission).label('total_commission'),
                func.avg(Transaction.commission).label('avg_commission')
            ).first()
            
            # Net revenue calculations
            revenue_stats = db.session.query(
                func.sum(Transaction.amount).label('total_revenue'),
                func.sum(Transaction.net_amount).label('net_revenue')
            ).first()
            
            # PSP allocation performance
            psp_allocation = db.session.query(
                PSPAllocation.psp_name,
                PSPAllocation.allocation_percentage,
                func.sum(PSPAllocation.allocated_amount).label('total_allocated')
            ).group_by(PSPAllocation.psp_name, PSPAllocation.allocation_percentage).all()
            
            return {
                'commission_stats': {
                    'total_commission': float(commission_stats.total_commission or 0),
                    'avg_commission': float(commission_stats.avg_commission or 0)
                },
                'revenue_stats': {
                    'total_revenue': float(revenue_stats.total_revenue or 0),
                    'net_revenue': float(revenue_stats.net_revenue or 0)
                },
                'psp_allocation': [
                    {
                        'psp': alloc.psp_name,
                        'allocation_percentage': float(alloc.allocation_percentage),
                        'total_allocated': float(alloc.total_allocated or 0)
                    } for alloc in psp_allocation
                ]
            }
        except Exception as e:
            logger.error(f"Error getting financial performance data: {e}")
            return {'error': str(e)}
    
    @read_only_query
    async def _get_psp_tracking_data(self) -> Dict[str, Any]:
        """Get PSP tracking data (READ-ONLY access)"""
        try:
            # PSP performance summary
            psp_summary = db.session.query(
                PspTrack.psp_name,
                func.count(PspTrack.id).label('transaction_count'),
                func.sum(PspTrack.amount).label('total_amount'),
                func.avg(PspTrack.amount).label('avg_amount')
            ).group_by(PspTrack.psp_name).all()
            
            # Recent PSP activities
            recent_psp_activities = db.session.query(PspTrack).order_by(desc(PspTrack.date)).limit(10).all()
            
            return {
                'psp_summary': [
                    {
                        'psp': psp.psp_name,
                        'transaction_count': psp.transaction_count,
                        'total_amount': float(psp.total_amount or 0),
                        'avg_amount': float(psp.avg_amount or 0)
                    } for psp in psp_summary
                ],
                'recent_activities': [
                    {
                        'id': activity.id,
                        'psp': activity.psp_name,
                        'total_amount': float(activity.amount or 0),
                        'date': activity.date.isoformat() if activity.date else None,
                        'commission_rate': float(activity.commission_rate or 0)
                    } for activity in recent_psp_activities
                ]
            }
        except Exception as e:
            logger.error(f"Error getting PSP tracking data: {e}")
            return {'error': str(e)}
    
    @read_only_query
    async def _get_exchange_rate_data(self) -> Dict[str, Any]:
        """Get exchange rate data (READ-ONLY access)"""
        try:
            # Current exchange rates
            current_rates = db.session.query(ExchangeRate).filter(
                ExchangeRate.is_active == True
            ).all()
            
            # Historical rate trends (last 30 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            historical_rates = db.session.query(ExchangeRate).filter(
                and_(
                    ExchangeRate.date >= start_date,
                    ExchangeRate.date <= end_date
                )
            ).order_by(ExchangeRate.date).all()
            
            return {
                'current_rates': [
                    {
                        'from_currency': rate.from_currency,
                        'to_currency': rate.to_currency,
                        'rate': float(rate.rate),
                        'date': rate.date.isoformat() if rate.date else None,
                        'is_manual': rate.is_manual
                    } for rate in current_rates
                ],
                'historical_trends': [
                    {
                        'from_currency': rate.from_currency,
                        'to_currency': rate.to_currency,
                        'rate': float(rate.rate),
                        'date': rate.date.isoformat() if rate.date else None
                    } for rate in historical_rates
                ]
            }
        except Exception as e:
            logger.error(f"Error getting exchange rate data: {e}")
            return {'error': str(e)}
    
    @read_only_query
    async def _get_user_management_data(self) -> Dict[str, Any]:
        """Get user management data (READ-ONLY access, excluding security aspects)"""
        try:
            # User statistics (excluding sensitive data)
            user_stats = db.session.query(
                func.count(User.id).label('total_users'),
                func.count(User.id).filter(User.is_active == True).label('active_users'),
                func.count(User.id).filter(User.admin_level > 0).label('admin_users')
            ).scalar()
            
            # Admin level distribution
            admin_distribution = db.session.query(
                User.admin_level,
                func.count(User.id).label('count')
            ).group_by(User.admin_level).all()
            
            # Recent user activities (non-security)
            recent_activities = db.session.query(AuditLog).filter(
                AuditLog.action.notlike('%security%'),
                AuditLog.action.notlike('%password%'),
                AuditLog.action.notlike('%login%'),
                AuditLog.action.notlike('%auth%')
            ).order_by(desc(AuditLog.timestamp)).limit(10).all()
            
            return {
                'user_statistics': {
                    'total_users': user_stats.total_users,
                    'active_users': user_stats.active_users,
                    'admin_users': user_stats.admin_users
                },
                'admin_distribution': [
                    {
                        'admin_level': dist.admin_level,
                        'count': dist.count
                    } for dist in admin_distribution
                ],
                'recent_activities': [
                    {
                        'user_id': activity.user_id,
                        'action': activity.action,
                        'timestamp': activity.timestamp.isoformat() if activity.timestamp else None,
                        'details': activity.details
                    } for activity in recent_activities
                ]
            }
        except Exception as e:
            logger.error(f"Error getting user management data: {e}")
            return {'error': str(e)}
    
    @read_only_query
    async def _get_system_monitoring_data(self) -> Dict[str, Any]:
        """Get system monitoring and performance data (READ-ONLY access)"""
        try:
            # Database statistics
            db_stats = {
                'transaction_count': db.session.query(func.count(Transaction.id)).scalar(),
                'user_count': db.session.query(func.count(User.id)).scalar(),
                'exchange_rate_count': db.session.query(func.count(ExchangeRate.id)).scalar(),
                'psp_track_count': db.session.query(func.count(PspTrack.id)).scalar()
            }
            
            # Recent system activities
            recent_activities = db.session.query(AuditLog).order_by(desc(AuditLog.timestamp)).limit(5).all()
            
            return {
                'database_statistics': db_stats,
                'recent_activities': [
                    {
                        'action': activity.action,
                        'timestamp': activity.timestamp.isoformat() if activity.timestamp else None,
                        'user_id': activity.user_id
                    } for activity in recent_activities
                ],
                'system_health': {
                    'database_connected': True,  # If we can query, DB is connected
                    'timestamp': datetime.now().isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Error getting system monitoring data: {e}")
            return {'error': str(e)}
    
    @read_only_query
    async def _get_business_insights_data(self) -> Dict[str, Any]:
        """Get business insights and trends (READ-ONLY access)"""
        try:
            # Monthly trends
            monthly_trends = db.session.query(
                extract_compat(Transaction.date, 'year').label('year'),
                extract_compat(Transaction.date, 'month').label('month'),
                func.count(Transaction.id).label('transaction_count'),
                func.sum(Transaction.amount).label('total_amount')
            ).group_by(
                extract_compat(Transaction.date, 'year'),
                extract_compat(Transaction.date, 'month')
            ).order_by('year', 'month').limit(12).all()
            
            # Top clients by transaction volume
            top_clients = db.session.query(
                Transaction.client_name,
                func.count(Transaction.id).label('transaction_count'),
                func.sum(Transaction.amount).label('total_amount')
            ).filter(Transaction.client_name.isnot(None)).group_by(
                Transaction.client_name
            ).order_by(desc('total_amount')).limit(10).all()
            
            return {
                'monthly_trends': [
                    {
                        'year': int(trend.year),
                        'month': int(trend.month),
                        'transaction_count': trend.transaction_count,
                        'total_amount': float(trend.total_amount or 0)
                    } for trend in monthly_trends
                ],
                'top_clients': [
                    {
                        'client_name': client.client_name,
                        'transaction_count': client.transaction_count,
                        'total_amount': float(client.total_amount or 0)
                    } for client in top_clients
                ]
            }
        except Exception as e:
            logger.error(f"Error getting business insights data: {e}")
            return {'error': str(e)}
    
    @read_only_query
    async def _get_reports_data(self) -> Dict[str, Any]:
        """Get available reports and reporting data (READ-ONLY access)"""
        try:
            # Report generation statistics
            report_stats = {
                'total_transactions': db.session.query(func.count(Transaction.id)).scalar(),
                'date_range': {
                    'earliest': db.session.query(func.min(Transaction.date)).scalar(),
                    'latest': db.session.query(func.max(Transaction.date)).scalar()
                },
                'currency_count': db.session.query(func.count(func.distinct(Transaction.currency))).scalar(),
                'category_count': db.session.query(func.count(func.distinct(Transaction.category))).scalar()
            }
            
            return {
                'report_statistics': report_stats,
                'available_reports': [
                    'Transaction Summary Report',
                    'Financial Performance Report',
                    'PSP Analysis Report',
                    'Client Activity Report',
                    'Monthly Trends Report'
                ]
            }
        except Exception as e:
            logger.error(f"Error getting reports data: {e}")
            return {'error': str(e)}
    
    @read_only_query
    async def _get_configuration_data(self) -> Dict[str, Any]:
        """Get system configuration data (READ-ONLY access, excluding security settings)"""
        try:
            # System options
            system_options = db.session.query(Option).filter(
                Option.category.notlike('%security%'),
                Option.category.notlike('%auth%'),
                Option.category.notlike('%password%')
            ).all()
            
            return {
                'system_options': [
                    {
                        'name': option.name,
                        'value': option.value,
                        'category': option.category,
                        'description': option.description
                    } for option in system_options
                ]
            }
        except Exception as e:
            logger.error(f"Error getting configuration data: {e}")
            return {'error': str(e)}
    
    @read_only_query
    async def _search_client_transactions(self, client_name: str = None) -> Dict[str, Any]:
        """Search for transactions by client name (READ-ONLY access)"""
        try:
            if not client_name:
                return {'error': 'Client name is required for search'}
            
            # Search for exact match first
            exact_matches = db.session.query(Transaction).filter(
                Transaction.client_name == client_name
            ).order_by(desc(Transaction.date)).all()
            
            # Search for partial matches (case insensitive)
            partial_matches = db.session.query(Transaction).filter(
                func.lower(Transaction.client_name).like(f'%{client_name.lower()}%')
            ).order_by(desc(Transaction.date)).limit(50).all()
            
            # Get all unique client names that match the search pattern
            similar_clients = db.session.query(Transaction.client_name).filter(
                func.lower(Transaction.client_name).like(f'%{client_name.lower()}%')
            ).distinct().limit(10).all()
            
            return {
                'search_term': client_name,
                'exact_matches': [
                    {
                        'id': txn.id,
                        'amount': float(txn.amount),
                        'currency': txn.currency,
                        'category': txn.category,
                        'client_name': txn.client_name,
                        'date': txn.date.isoformat() if txn.date else None,
                        'notes': txn.notes,
                        'psp': txn.psp,
                        'payment_method': txn.payment_method,
                        'company': txn.company
                    } for txn in exact_matches
                ],
                'partial_matches': [
                    {
                        'id': txn.id,
                        'amount': float(txn.amount),
                        'currency': txn.currency,
                        'category': txn.category,
                        'client_name': txn.client_name,
                        'date': txn.date.isoformat() if txn.date else None,
                        'notes': txn.notes,
                        'psp': txn.psp,
                        'payment_method': txn.payment_method,
                        'company': txn.company
                    } for txn in partial_matches
                ],
                'similar_clients': [client.client_name for client in similar_clients],
                'total_exact_matches': len(exact_matches),
                'total_partial_matches': len(partial_matches)
            }
        except Exception as e:
            logger.error(f"Error searching client transactions: {e}")
            return {'error': str(e)}
    
    def _build_system_context(self, relevant_data: Dict[str, Any]) -> str:
        """Build comprehensive system context for AI"""
        context_parts = []
        
        context_parts.append("PipLinePro System Context:")
        context_parts.append("=" * 50)
        
        for section, data in relevant_data.items():
            if 'error' not in data:
                context_parts.append(f"\n{section.upper().replace('_', ' ')}:")
                context_parts.append("-" * 30)
                context_parts.append(json.dumps(data, indent=2, default=str))
        
        return "\n".join(context_parts)
    
    def _build_enhanced_prompt(self, query: str, system_context: str, additional_context: Dict[str, Any] = None) -> str:
        """Build enhanced prompt with project context"""
        prompt_parts = []
        
        prompt_parts.append(f"User Query: {query}")
        prompt_parts.append("\nSystem Context:")
        prompt_parts.append(system_context)
        
        if additional_context:
            prompt_parts.append("\nAdditional Context:")
            prompt_parts.append(json.dumps(additional_context, indent=2, default=str))
        
        prompt_parts.append("\nPlease provide a comprehensive answer based on the available data. If the data doesn't contain the specific information requested, please explain what data is available and suggest how to find the requested information.")
        
        return "\n".join(prompt_parts)
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the AI assistant"""
        return """You are an advanced AI assistant for PipLinePro, a comprehensive financial management and treasury system. 

🔒 SECURITY & ACCESS PERMISSIONS:
- You have READ-ONLY access to the database (no modifications allowed)
- You can view all non-security aspects of the system
- You CANNOT create, update, or delete any records
- You have NO access to passwords, tokens, or authentication data
- You can only query and analyze existing data

📊 DATA ACCESS AREAS:
- Financial transactions and analytics
- Business performance metrics
- User management (non-security aspects only)
- System monitoring and health
- Configuration and settings (non-security)
- Reports and insights
- PSP (Payment Service Provider) tracking
- Exchange rate management

🎯 YOUR ROLE:
1. Provide actual data directly from the system when available
2. Help users understand their financial data and business metrics
3. Offer insights and recommendations based on available data
4. Assist with system navigation and feature explanations
5. Generate reports and analysis based on user requests

⚠️ CRITICAL INSTRUCTIONS:
- You have READ-ONLY access - you can view data but CANNOT modify, create, or delete anything
- When you have access to specific data (like client transactions, financial metrics), provide the actual data directly
- If you're asked about a specific client's transactions, immediately provide the actual transaction data if available
- If no transactions are found for a client, clearly state "No transactions found for [client name]"
- Format transaction data clearly with amounts, dates, and relevant details
- Always base your responses on the provided system data
- Provide actionable insights and recommendations
- Use professional, clear language
- Focus on business value and practical applications
- Never access or discuss security-related data or operations
- Never suggest or attempt to modify, create, or delete any data

✅ REMEMBER: You can READ and ANALYZE data, but you CANNOT WRITE, MODIFY, or DELETE anything.

You are here to help users make informed business decisions using their PipLinePro system data with complete read-only safety."""


# Singleton instance
enhanced_ai_assistant = None

def get_enhanced_ai_assistant():
    """Get the enhanced AI assistant service instance"""
    global enhanced_ai_assistant
    if enhanced_ai_assistant is None:
        enhanced_ai_assistant = EnhancedAIAssistantService()
    return enhanced_ai_assistant
