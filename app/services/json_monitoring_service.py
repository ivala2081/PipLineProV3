"""
JSON Monitoring Service
Tracks JSON errors and provides analytics on the automated fixing system
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from app.utils.unified_logger import get_logger

# Decimal/Float type mismatch prevention
from app.services.decimal_float_fix_service import decimal_float_service


logger = get_logger(__name__)

@dataclass
class JSONErrorEvent:
    """Represents a JSON error event"""
    timestamp: datetime
    error_type: str
    error_message: str
    source: str
    fixed: bool
    fix_time_ms: Optional[float] = None
    original_data: Optional[str] = None
    fixed_data: Optional[str] = None

@dataclass
class JSONMetrics:
    """JSON processing metrics"""
    total_errors: int
    fixed_errors: int
    error_rate: float
    avg_fix_time_ms: float
    most_common_errors: List[Dict[str, Any]]
    error_trend: List[Dict[str, Any]]

class JSONMonitoringService:
    """Service to monitor and analyze JSON processing"""
    
    def __init__(self, max_events: int = 1000):
        self.max_events = max_events
        self.events = deque(maxlen=max_events)
        self.error_counts = defaultdict(int)
        self.fix_times = []
        self.start_time = datetime.now()
        
    def record_error(self, error_type: str, error_message: str, source: str, 
                    original_data: Optional[str] = None, fixed: bool = False,
                    fix_time_ms: Optional[float] = None, fixed_data: Optional[str] = None):
        """Record a JSON error event"""
        event = JSONErrorEvent(
            timestamp=datetime.now(),
            error_type=error_type,
            error_message=error_message,
            source=source,
            fixed=fixed,
            fix_time_ms=fix_time_ms,
            original_data=original_data[:200] if original_data else None,  # Truncate for storage
            fixed_data=fixed_data[:200] if fixed_data else None
        )
        
        self.events.append(event)
        self.error_counts[error_type] += 1
        
        if fix_time_ms:
            self.fix_times.append(fix_time_ms)
        
        logger.info(f"JSON error recorded: {error_type} from {source} - Fixed: {fixed}")
    
    def get_metrics(self, hours: int = 24) -> JSONMetrics:
        """Get JSON processing metrics for the specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter events within time period
        recent_events = [e for e in self.events if e.timestamp >= cutoff_time]
        
        total_errors = len(recent_events)
        fixed_errors = len([e for e in recent_events if e.fixed])
        error_rate = (total_errors / max(1, len(self.events))) * 100
        
        # Calculate average fix time
        recent_fix_times = [e.fix_time_ms for e in recent_events if e.fix_time_ms]
        avg_fix_time = sum(recent_fix_times) / len(recent_fix_times) if recent_fix_times else 0
        
        # Most common errors
        error_type_counts = defaultdict(int)
        for event in recent_events:
            error_type_counts[event.error_type] += 1
        
        most_common_errors = [
            {"error_type": error_type, "count": count}
            for error_type, count in sorted(error_type_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Error trend (hourly)
        hourly_errors = defaultdict(int)
        for event in recent_events:
            hour_key = event.timestamp.replace(minute=0, second=0, microsecond=0)
            hourly_errors[hour_key] += 1
        
        error_trend = [
            {"hour": hour.isoformat(), "count": count}
            for hour, count in sorted(hourly_errors.items())
        ]
        
        return JSONMetrics(
            total_errors=total_errors,
            fixed_errors=fixed_errors,
            error_rate=error_rate,
            avg_fix_time_ms=avg_fix_time,
            most_common_errors=most_common_errors,
            error_trend=error_trend
        )
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get a summary of JSON errors"""
        if not self.events:
            return {
                "status": "No errors recorded",
                "total_errors": 0,
                "fixed_errors": 0,
                "success_rate": 100.0
            }
        
        total_errors = len(self.events)
        fixed_errors = len([e for e in self.events if e.fixed])
        success_rate = ((total_errors - fixed_errors) / total_errors) * 100 if total_errors > 0 else 100
        
        return {
            "status": "Active monitoring",
            "total_errors": total_errors,
            "fixed_errors": fixed_errors,
            "success_rate": round(success_rate, 2),
            "uptime_hours": round((datetime.now() - self.start_time).total_seconds() / 3600, 2),
            "most_common_error": max(self.error_counts.items(), key=lambda x: x[1])[0] if self.error_counts else "None"
        }
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent error events"""
        recent_events = list(self.events)[-limit:]
        return [asdict(event) for event in recent_events]
    
    def clear_old_events(self, days: int = 7):
        """Clear events older than specified days"""
        cutoff_time = datetime.now() - timedelta(days=days)
        self.events = deque(
            [e for e in self.events if e.timestamp >= cutoff_time],
            maxlen=self.max_events
        )
        logger.info(f"Cleared events older than {days} days")
    
    def export_metrics(self) -> Dict[str, Any]:
        """Export all metrics for external analysis"""
        return {
            "summary": self.get_error_summary(),
            "metrics_24h": asdict(self.get_metrics(24)),
            "metrics_7d": asdict(self.get_metrics(168)),  # 7 days
            "recent_errors": self.get_recent_errors(50),
            "error_counts": dict(self.error_counts),
            "service_info": {
                "start_time": self.start_time.isoformat(),
                "max_events": self.max_events,
                "current_events": len(self.events)
            }
        }

# Global monitoring service instance
json_monitoring_service = JSONMonitoringService()

def record_json_error(error_type: str, error_message: str, source: str, 
                     original_data: Optional[str] = None, fixed: bool = False,
                     fix_time_ms: Optional[float] = None, fixed_data: Optional[str] = None):
    """Convenience function to record JSON errors"""
    json_monitoring_service.record_error(
        error_type=error_type,
        error_message=error_message,
        source=source,
        original_data=original_data,
        fixed=fixed,
        fix_time_ms=fix_time_ms,
        fixed_data=fixed_data
    )

def get_json_metrics(hours: int = 24) -> JSONMetrics:
    """Get JSON metrics for the specified time period"""
    return json_monitoring_service.get_metrics(hours)

def get_json_summary() -> Dict[str, Any]:
    """Get JSON error summary"""
    return json_monitoring_service.get_error_summary() 