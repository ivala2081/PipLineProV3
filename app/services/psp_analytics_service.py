"""
PSP Analytics Service
Provides comprehensive analytics and metrics for Payment Service Providers
"""
from datetime import datetime, timedelta, date
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
from typing import Dict, List, Any
import statistics
from app.models.financial import PspTrack
from app import db

# Decimal/Float type mismatch prevention
from app.services.decimal_float_fix_service import decimal_float_service



class PspAnalyticsService:
    """Service for PSP analytics and metrics calculation"""
    
    @staticmethod
    def calculate_psp_metrics(psp_tracks: List[PspTrack]) -> Dict[str, Any]:
        """
        Calculate comprehensive metrics for all PSPs
        
        Args:
            psp_tracks: List of PspTrack objects
            
        Returns:
            Dictionary containing detailed PSP metrics
        """
        if not psp_tracks:
            return {
                'total_active_psps': 0,
                'total_allocation': 0,
                'total_rollover': 0,
                'avg_allocation': 0,
                'psps': {},
                'overall_metrics': {}
            }
        
        # Group tracks by PSP
        psp_data = defaultdict(list)
        for track in psp_tracks:
            psp_data[track.psp_name].append(track)
        
        # Calculate metrics for each PSP
        psp_metrics = {}
        total_allocation = Decimal('0')  # FIXED: Only user-entered allocations
        total_amount = Decimal('0')      # FIXED: Total transaction amounts
        total_rollover = Decimal('0')
        total_commission = Decimal('0')
        total_transactions = 0
        
        for psp_name, tracks in psp_data.items():
            metrics = PspAnalyticsService._calculate_individual_psp_metrics(psp_name, tracks)
            psp_metrics[psp_name] = metrics
            
            total_allocation += Decimal(str(metrics['total_allocation']))  # FIXED: Only user-entered allocations
            total_amount += Decimal(str(metrics['total_amount']))          # FIXED: Total transaction amounts
            total_rollover += Decimal(str(metrics['total_rollover']))
            total_commission += Decimal(str(metrics['total_commission']))
            total_transactions += metrics['transaction_count']
        
        # Calculate overall metrics
        overall_metrics = PspAnalyticsService._calculate_overall_metrics(
            psp_metrics, total_amount, total_rollover, total_commission, total_transactions
        )
        
        return {
            'total_active_psps': len(psp_metrics),
            'total_allocation': float(total_allocation),
            'total_rollover': float(total_rollover),
            'avg_allocation': float(total_allocation / len(psp_metrics)) if psp_metrics else 0,
            'psps': psp_metrics,
            'overall_metrics': overall_metrics
        }
    
    @staticmethod
    def _calculate_individual_psp_metrics(psp_name: str, tracks: List[PspTrack]) -> Dict[str, Any]:
        """Calculate detailed metrics for a single PSP"""
        
        # Sort tracks by date
        tracks.sort(key=lambda x: x.date)
        
        # Basic calculations - FIXED: Use correct fields
        total_amount = sum(track.amount or Decimal('0') for track in tracks)  # Total transaction amount
        total_withdraw = sum(track.withdraw or Decimal('0') for track in tracks)
        total_commission = sum(track.commission_amount or Decimal('0') for track in tracks)
        total_rollover = sum(track.difference or Decimal('0') for track in tracks)
        
        # FIXED: Only count allocation amounts that users have actually entered
        total_allocation = sum(track.allocation or Decimal('0') for track in tracks if track.allocation and track.allocation > 0)
        
        # Date range analysis
        dates = [track.date for track in tracks]
        active_days = len(set(dates))
        first_date = min(dates)
        last_date = max(dates)
        days_active = (last_date - first_date).days + 1
        
        # Performance metrics
        net_amount = total_amount - total_commission
        
        # FIXED: ROI should be calculated based on allocation, not transaction amount
        # If no allocation is entered, ROI is undefined (set to 0)
        if total_allocation > 0:
            roi = float((net_amount / total_allocation * 100))
        else:
            roi = 0.0  # No allocation means no ROI calculation possible
        
        # Commission efficiency
        avg_commission_rate = float((total_commission / total_amount * 100) if total_amount > 0 else 0)
        
        # Transaction patterns
        transaction_count = len(tracks)
        avg_daily_transactions = transaction_count / active_days if active_days > 0 else 0
        
        # Trend analysis (last 30 days vs previous 30 days)
        thirty_days_ago = date.today() - timedelta(days=30)
        sixty_days_ago = date.today() - timedelta(days=60)
        
        recent_tracks = [t for t in tracks if t.date >= thirty_days_ago]
        previous_tracks = [t for t in tracks if sixty_days_ago <= t.date < thirty_days_ago]
        
        recent_amount = sum(t.amount or Decimal('0') for t in recent_tracks)
        previous_amount = sum(t.amount or Decimal('0') for t in previous_tracks)
        
        # Growth rate calculation
        growth_rate = 0.0
        if previous_amount > 0:
            growth_rate = float(((recent_amount - previous_amount) / previous_amount) * 100)
        
        # Risk indicators
        daily_amounts = []
        for track in tracks:
            daily_amounts.append(float(track.amount or 0))
        
        volatility = statistics.stdev(daily_amounts) if len(daily_amounts) > 1 else 0
        consistency_score = PspAnalyticsService._calculate_consistency_score(tracks)
        
        # Status determination
        is_active = last_date >= (date.today() - timedelta(days=7))
        performance_tier = PspAnalyticsService._determine_performance_tier(roi, growth_rate, consistency_score)
        
        # Efficiency metrics
        efficiency_score = PspAnalyticsService._calculate_efficiency_score(
            total_amount, total_commission, active_days, transaction_count
        )
        
        return {
            'psp_name': psp_name,
            'total_amount': float(total_amount),  # FIXED: Renamed from total_allocation
            'total_allocation': float(total_allocation),  # FIXED: Only user-entered allocations
            'total_withdraw': float(total_withdraw),
            'total_commission': float(total_commission),
            'total_rollover': float(total_rollover),
            'net_amount': float(net_amount),
            'transaction_count': transaction_count,
            'active_days': active_days,
            'days_active': days_active,
            'first_date': first_date.isoformat(),
            'last_date': last_date.isoformat(),
            'roi_percentage': float(roi),
            'avg_commission_rate': float(avg_commission_rate),
            'avg_daily_transactions': float(avg_daily_transactions),
            'growth_rate': float(growth_rate),
            'volatility': float(volatility),
            'consistency_score': float(consistency_score),
            'efficiency_score': float(efficiency_score),
            'is_active': is_active,
            'performance_tier': performance_tier,
            'recent_30_days': {
                'amount': float(recent_amount),  # FIXED: Renamed from allocation
                'transactions': len(recent_tracks),
                'avg_daily': float(recent_amount / 30) if recent_amount > 0 else 0
            },
            'previous_30_days': {
                'amount': float(previous_amount),
                'transactions': len(previous_tracks),
                'avg_daily': float(previous_amount / 30) if previous_amount > 0 else 0
            }
        }
    
    @staticmethod
    def _calculate_overall_metrics(psp_metrics: Dict, total_amount: Decimal, 
                                 total_rollover: Decimal, total_commission: Decimal, 
                                 total_transactions: int) -> Dict[str, Any]:
        """Calculate overall system metrics"""
        
        if not psp_metrics:
            return {}
        
        # Performance distribution
        rois = [metrics['roi_percentage'] for metrics in psp_metrics.values()]
        avg_roi = sum(rois) / len(rois)
        
        # Risk assessment
        volatilities = [metrics['volatility'] for metrics in psp_metrics.values()]
        avg_volatility = sum(volatilities) / len(volatilities) if volatilities else 0
        
        # Efficiency metrics
        efficiency_scores = [metrics['efficiency_score'] for metrics in psp_metrics.values()]
        avg_efficiency = sum(efficiency_scores) / len(efficiency_scores)
        
        # Active PSPs
        active_psps = sum(1 for metrics in psp_metrics.values() if metrics['is_active'])
        
        return {
            'avg_roi': float(avg_roi),
            'avg_volatility': float(avg_volatility),
            'avg_efficiency': float(avg_efficiency),
            'active_psps': active_psps,
            'total_psps': len(psp_metrics),
            'system_health_score': float((avg_roi + avg_efficiency) / 2)
        }
    
    @staticmethod
    def _calculate_consistency_score(tracks: List[PspTrack]) -> float:
        """Calculate consistency score based on transaction patterns"""
        if len(tracks) < 2:
            return 100.0
        
        # Calculate daily amounts and their consistency
        daily_amounts = defaultdict(Decimal)
        for track in tracks:
            daily_amounts[track.date] += track.amount or Decimal('0')
        
        amounts = list(daily_amounts.values())
        if len(amounts) < 2:
            return 100.0
        
        # Calculate coefficient of variation (lower is more consistent)
        mean_amount = sum(amounts) / len(amounts)
        if mean_amount == 0:
            return 100.0
        
        variance = sum((amount - mean_amount) ** 2 for amount in amounts) / len(amounts)
        std_dev = float(variance) ** 0.5
        cv = (std_dev / float(mean_amount)) * 100
        
        # Convert to consistency score (0-100, higher is more consistent)
        consistency_score = max(0, 100 - cv)
        return float(consistency_score)
    
    @staticmethod
    def _calculate_efficiency_score(total_amount: Decimal, total_commission: Decimal, 
                                  active_days: int, transaction_count: int) -> float:
        """Calculate efficiency score based on multiple factors"""
        
        if total_amount == 0:
            return 0.0
        
        # Commission efficiency (lower commission rate is better)
        commission_rate = float((total_commission / total_amount) * 100)
        commission_score = max(0, 100 - commission_rate * 10)  # Scale factor
        
        # Activity efficiency (more transactions per day is better)
        activity_score = min(100, (transaction_count / active_days) * 10) if active_days > 0 else 0
        
        # Volume efficiency (higher amount per transaction is better)
        volume_score = min(100, float(total_amount / transaction_count / 1000)) if transaction_count > 0 else 0
        
        # Weighted average
        efficiency_score = (commission_score * 0.4 + activity_score * 0.3 + volume_score * 0.3)
        return float(efficiency_score)
    
    @staticmethod
    def _determine_performance_tier(roi: float, growth_rate: float, consistency_score: float) -> str:
        """Determine performance tier based on metrics"""
        
        # Ensure all values are floats
        roi = float(roi)
        growth_rate = float(growth_rate)
        consistency_score = float(consistency_score)
        
        # Calculate composite score
        composite_score = (roi * 0.4 + growth_rate * 0.3 + consistency_score * 0.3)
        
        if composite_score >= 80:
            return 'excellent'
        elif composite_score >= 60:
            return 'good'
        elif composite_score >= 40:
            return 'average'
        elif composite_score >= 20:
            return 'below_average'
        else:
            return 'poor'
    
    @staticmethod
    def get_psp_trend_data(psp_name: str, days: int = 30) -> Dict[str, Any]:
        """Get trend data for a specific PSP"""
        
        start_date = date.today() - timedelta(days=days)
        tracks = PspTrack.query.filter(
            PspTrack.psp_name == psp_name,
            PspTrack.date >= start_date
        ).order_by(PspTrack.date).all()
        
        if not tracks:
            return {'dates': [], 'amounts': [], 'commissions': []}
        
        # Group by date
        daily_data = defaultdict(lambda: {'amount': Decimal('0'), 'commission': Decimal('0')})
        for track in tracks:
            daily_data[track.date]['amount'] += track.amount or Decimal('0')
            daily_data[track.date]['commission'] += track.commission_amount or Decimal('0')
        
        # Sort by date
        sorted_data = sorted(daily_data.items())
        
        return {
            'dates': [d[0].isoformat() for d in sorted_data],
            'amounts': [float(d[1]['amount']) for d in sorted_data],
            'commissions': [float(d[1]['commission']) for d in sorted_data]
        } 