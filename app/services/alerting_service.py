"""
Alerting Service for PipLinePro
Sends alerts for critical system events and thresholds
"""
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum
from flask import current_app

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert data structure"""
    level: AlertLevel
    title: str
    message: str
    source: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary"""
        return {
            'level': self.level.value,
            'title': self.title,
            'message': self.message,
            'source': self.source,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata or {}
        }


class AlertingService:
    """Service for managing and sending alerts"""
    
    def __init__(self):
        self.alert_handlers: List[Callable[[Alert], None]] = []
        self.alert_history: List[Alert] = []
        self.max_history = 1000
        self.thresholds = {
            'cpu_percent': 85.0,
            'memory_percent': 85.0,
            'disk_percent': 90.0,
            'slow_query_threshold': 2.0,
            'error_rate_threshold': 0.1,  # 10% error rate
        }
    
    def register_handler(self, handler: Callable[[Alert], None]):
        """Register alert handler"""
        self.alert_handlers.append(handler)
        logger.info(f"Alert handler registered: {handler.__name__}")
    
    def send_alert(self, alert: Alert):
        """Send alert to all registered handlers"""
        # Add to history
        self.alert_history.append(alert)
        if len(self.alert_history) > self.max_history:
            self.alert_history = self.alert_history[-self.max_history:]
        
        # Log alert
        log_level = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL,
        }.get(alert.level, logging.INFO)
        
        logger.log(
            log_level,
            f"Alert [{alert.level.value.upper()}]: {alert.title} - {alert.message}",
            extra=alert.to_dict()
        )
        
        # Send to handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler {handler.__name__}: {e}")
    
    def check_system_metrics(self, metrics: Dict[str, Any]):
        """Check system metrics and send alerts if thresholds exceeded"""
        system = metrics.get('system', {})
        
        # CPU check
        cpu_percent = system.get('cpu_percent', 0)
        if cpu_percent > self.thresholds['cpu_percent']:
            self.send_alert(Alert(
                level=AlertLevel.WARNING if cpu_percent < 95 else AlertLevel.CRITICAL,
                title="High CPU Usage",
                message=f"CPU usage is at {cpu_percent:.1f}% (threshold: {self.thresholds['cpu_percent']}%)",
                source="system_monitoring",
                timestamp=datetime.now(timezone.utc),
                metadata={'cpu_percent': cpu_percent, 'threshold': self.thresholds['cpu_percent']}
            ))
        
        # Memory check
        memory_percent = system.get('memory_percent', 0)
        if memory_percent > self.thresholds['memory_percent']:
            self.send_alert(Alert(
                level=AlertLevel.WARNING if memory_percent < 95 else AlertLevel.CRITICAL,
                title="High Memory Usage",
                message=f"Memory usage is at {memory_percent:.1f}% (threshold: {self.thresholds['memory_percent']}%)",
                source="system_monitoring",
                timestamp=datetime.now(timezone.utc),
                metadata={'memory_percent': memory_percent, 'threshold': self.thresholds['memory_percent']}
            ))
        
        # Disk check
        disk_percent = system.get('disk_percent', 0)
        if disk_percent > self.thresholds['disk_percent']:
            self.send_alert(Alert(
                level=AlertLevel.WARNING if disk_percent < 95 else AlertLevel.CRITICAL,
                title="High Disk Usage",
                message=f"Disk usage is at {disk_percent:.1f}% (threshold: {self.thresholds['disk_percent']}%)",
                source="system_monitoring",
                timestamp=datetime.now(timezone.utc),
                metadata={'disk_percent': disk_percent, 'threshold': self.thresholds['disk_percent']}
            ))
    
    def check_slow_queries(self, query_time: float, query_name: str):
        """Check for slow queries and send alert"""
        if query_time > self.thresholds['slow_query_threshold']:
            self.send_alert(Alert(
                level=AlertLevel.WARNING,
                title="Slow Query Detected",
                message=f"Query '{query_name}' took {query_time:.3f}s (threshold: {self.thresholds['slow_query_threshold']}s)",
                source="query_monitoring",
                timestamp=datetime.now(timezone.utc),
                metadata={'query_name': query_name, 'duration': query_time}
            ))
    
    def check_error_rate(self, error_count: int, total_requests: int):
        """Check error rate and send alert"""
        if total_requests == 0:
            return
        
        error_rate = error_count / total_requests
        if error_rate > self.thresholds['error_rate_threshold']:
            self.send_alert(Alert(
                level=AlertLevel.ERROR,
                title="High Error Rate",
                message=f"Error rate is {error_rate*100:.1f}% ({error_count}/{total_requests} requests) (threshold: {self.thresholds['error_rate_threshold']*100}%)",
                source="request_monitoring",
                timestamp=datetime.now(timezone.utc),
                metadata={'error_count': error_count, 'total_requests': total_requests, 'error_rate': error_rate}
            ))
    
    def get_recent_alerts(self, limit: int = 100, level: Optional[AlertLevel] = None) -> List[Alert]:
        """Get recent alerts"""
        alerts = self.alert_history[-limit:] if limit else self.alert_history
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        return alerts
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        total = len(self.alert_history)
        by_level = {}
        
        for level in AlertLevel:
            by_level[level.value] = len([a for a in self.alert_history if a.level == level])
        
        return {
            'total_alerts': total,
            'by_level': by_level,
            'recent_critical': len([a for a in self.alert_history[-100:] if a.level == AlertLevel.CRITICAL])
        }


# Global alerting service instance
alerting_service = AlertingService()
