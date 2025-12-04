"""
Monitoring and Alerting Service
Provides comprehensive system monitoring, metrics collection, and alerting
"""
import time
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone, timedelta
from collections import deque
from enum import Enum
import psutil

from app.utils.unified_logger import get_logger
from app.utils.unified_error_handler import PipLineError

logger = get_logger("MonitoringService")


class AlertLevel(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Alert:
    """Alert object"""
    
    def __init__(
        self,
        title: str,
        message: str,
        level: AlertLevel,
        source: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.title = title
        self.message = message
        self.level = level
        self.source = source
        self.metadata = metadata or {}
        self.timestamp = datetime.now(timezone.utc)
        self.id = f"{source}_{int(time.time())}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'level': self.level.value,
            'source': self.source,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }


class MetricCollector:
    """Collect and store system metrics"""
    
    def __init__(self, max_metrics: int = 10000):
        self.metrics: Dict[str, deque] = {}
        self.max_metrics = max_metrics
        self.lock = threading.Lock()
    
    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a metric"""
        with self.lock:
            if name not in self.metrics:
                self.metrics[name] = deque(maxlen=self.max_metrics)
            
            self.metrics[name].append({
                'value': value,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'tags': tags or {}
            })
    
    def get_metric(self, name: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get metric values"""
        with self.lock:
            if name not in self.metrics:
                return []
            
            metrics = list(self.metrics[name])
            if limit:
                return metrics[-limit:]
            return metrics
    
    def get_metric_summary(self, name: str) -> Dict[str, Any]:
        """Get metric summary statistics"""
        with self.lock:
            if name not in self.metrics or not self.metrics[name]:
                return {}
            
            values = [m['value'] for m in self.metrics[name]]
            return {
                'name': name,
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'avg': sum(values) / len(values),
                'latest': values[-1] if values else None
            }


class MonitoringService:
    """Comprehensive monitoring and alerting service"""
    
    def __init__(self):
        self.alerts: deque = deque(maxlen=1000)
        self.metric_collector = MetricCollector()
        self.alert_handlers: List[Callable] = []
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.thresholds: Dict[str, Dict[str, float]] = {
            'cpu': {'warning': 70, 'error': 85, 'critical': 95},
            'memory': {'warning': 75, 'error': 85, 'critical': 95},
            'disk': {'warning': 80, 'error': 90, 'critical': 95},
            'response_time': {'warning': 1.0, 'error': 2.0, 'critical': 5.0},
        }
    
    def start_monitoring(self, interval: int = 60):
        """Start background monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("Monitoring service started")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Monitoring service stopped")
    
    def _monitor_loop(self, interval: int):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                self._collect_system_metrics()
                self._check_thresholds()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)
    
    def _collect_system_metrics(self):
        """Collect system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.metric_collector.record_metric('system.cpu.percent', cpu_percent)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.metric_collector.record_metric('system.memory.percent', memory.percent)
            self.metric_collector.record_metric('system.memory.available_gb', memory.available / (1024**3))
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            self.metric_collector.record_metric('system.disk.percent', disk.percent)
            self.metric_collector.record_metric('system.disk.free_gb', disk.free / (1024**3))
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def _check_thresholds(self):
        """Check metrics against thresholds"""
        try:
            # Check CPU
            cpu_summary = self.metric_collector.get_metric_summary('system.cpu.percent')
            if cpu_summary and 'latest' in cpu_summary:
                cpu = cpu_summary['latest']
                if cpu >= self.thresholds['cpu']['critical']:
                    self.create_alert(
                        "High CPU Usage",
                        f"CPU usage is at {cpu:.1f}% (critical threshold: {self.thresholds['cpu']['critical']}%)",
                        AlertLevel.CRITICAL,
                        "system.cpu"
                    )
                elif cpu >= self.thresholds['cpu']['error']:
                    self.create_alert(
                        "High CPU Usage",
                        f"CPU usage is at {cpu:.1f}% (error threshold: {self.thresholds['cpu']['error']}%)",
                        AlertLevel.ERROR,
                        "system.cpu"
                    )
                elif cpu >= self.thresholds['cpu']['warning']:
                    self.create_alert(
                        "Elevated CPU Usage",
                        f"CPU usage is at {cpu:.1f}% (warning threshold: {self.thresholds['cpu']['warning']}%)",
                        AlertLevel.WARNING,
                        "system.cpu"
                    )
            
            # Check Memory
            memory_summary = self.metric_collector.get_metric_summary('system.memory.percent')
            if memory_summary and 'latest' in memory_summary:
                memory = memory_summary['latest']
                if memory >= self.thresholds['memory']['critical']:
                    self.create_alert(
                        "High Memory Usage",
                        f"Memory usage is at {memory:.1f}% (critical threshold: {self.thresholds['memory']['critical']}%)",
                        AlertLevel.CRITICAL,
                        "system.memory"
                    )
                elif memory >= self.thresholds['memory']['error']:
                    self.create_alert(
                        "High Memory Usage",
                        f"Memory usage is at {memory:.1f}% (error threshold: {self.thresholds['memory']['error']}%)",
                        AlertLevel.ERROR,
                        "system.memory"
                    )
                elif memory >= self.thresholds['memory']['warning']:
                    self.create_alert(
                        "Elevated Memory Usage",
                        f"Memory usage is at {memory:.1f}% (warning threshold: {self.thresholds['memory']['warning']}%)",
                        AlertLevel.WARNING,
                        "system.memory"
                    )
            
            # Check Disk
            disk_summary = self.metric_collector.get_metric_summary('system.disk.percent')
            if disk_summary and 'latest' in disk_summary:
                disk = disk_summary['latest']
                if disk >= self.thresholds['disk']['critical']:
                    self.create_alert(
                        "Critical Disk Usage",
                        f"Disk usage is at {disk:.1f}% (critical threshold: {self.thresholds['disk']['critical']}%)",
                        AlertLevel.CRITICAL,
                        "system.disk"
                    )
                elif disk >= self.thresholds['disk']['error']:
                    self.create_alert(
                        "High Disk Usage",
                        f"Disk usage is at {disk:.1f}% (error threshold: {self.thresholds['disk']['error']}%)",
                        AlertLevel.ERROR,
                        "system.disk"
                    )
                elif disk >= self.thresholds['disk']['warning']:
                    self.create_alert(
                        "Elevated Disk Usage",
                        f"Disk usage is at {disk:.1f}% (warning threshold: {self.thresholds['disk']['warning']}%)",
                        AlertLevel.WARNING,
                        "system.disk"
                    )
                    
        except Exception as e:
            logger.error(f"Error checking thresholds: {e}")
    
    def create_alert(
        self,
        title: str,
        message: str,
        level: AlertLevel,
        source: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Create and store an alert"""
        alert = Alert(title, message, level, source, metadata)
        
        # Check for duplicates (same alert in last 5 minutes)
        recent_alerts = [a for a in self.alerts if 
                        a.source == source and 
                        a.title == title and
                        (datetime.now(timezone.utc) - a.timestamp).total_seconds() < 300]
        
        if not recent_alerts:
            self.alerts.append(alert)
            
            # Log alert
            log_level = {
                AlertLevel.INFO: logger.info,
                AlertLevel.WARNING: logger.warning,
                AlertLevel.ERROR: logger.error,
                AlertLevel.CRITICAL: logger.critical
            }.get(level, logger.info)
            
            log_level(f"Alert [{level.value.upper()}]: {title} - {message}")
            
            # Notify handlers
            for handler in self.alert_handlers:
                try:
                    handler(alert)
                except Exception as e:
                    logger.error(f"Error in alert handler: {e}")
    
    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a custom metric"""
        self.metric_collector.record_metric(name, value, tags)
    
    def get_metrics(self, name: Optional[str] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        """Get metrics"""
        if name:
            return {
                'metric': name,
                'data': self.metric_collector.get_metric(name, limit),
                'summary': self.metric_collector.get_metric_summary(name)
            }
        
        # Return all metrics
        return {
            name: {
                'data': self.metric_collector.get_metric(name, limit),
                'summary': self.metric_collector.get_metric_summary(name)
            }
            for name in self.metric_collector.metrics.keys()
        }
    
    def get_alerts(
        self,
        level: Optional[AlertLevel] = None,
        source: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get alerts"""
        alerts = list(self.alerts)
        
        # Filter by level
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        # Filter by source
        if source:
            alerts = [a for a in alerts if a.source == source]
        
        # Limit results
        alerts = alerts[-limit:]
        
        return [alert.to_dict() for alert in alerts]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get monitoring summary"""
        return {
            'monitoring_active': self.monitoring_active,
            'total_alerts': len(self.alerts),
            'alerts_by_level': {
                level.value: len([a for a in self.alerts if a.level == level])
                for level in AlertLevel
            },
            'metrics_tracked': len(self.metric_collector.metrics),
            'recent_alerts': [a.to_dict() for a in list(self.alerts)[-10:]],
            'system_metrics': {
                'cpu': self.metric_collector.get_metric_summary('system.cpu.percent'),
                'memory': self.metric_collector.get_metric_summary('system.memory.percent'),
                'disk': self.metric_collector.get_metric_summary('system.disk.percent'),
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def register_alert_handler(self, handler: Callable[[Alert], None]):
        """Register an alert handler callback"""
        self.alert_handlers.append(handler)


# Global instance
_monitoring_service: Optional[MonitoringService] = None


def get_monitoring_service() -> MonitoringService:
    """Get or create monitoring service instance"""
    global _monitoring_service
    
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
        # Don't start monitoring automatically - let app initialization handle it
        # _monitoring_service.start_monitoring()
    
    return _monitoring_service
