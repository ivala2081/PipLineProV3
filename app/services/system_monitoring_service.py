"""
Comprehensive System Monitoring Service
Provides real-time system health, performance metrics, and alerting
"""

import psutil
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import deque
import json

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    network_sent_mb: float
    network_recv_mb: float
    active_connections: int
    load_average: List[float]
    uptime_seconds: float

@dataclass
class ApplicationMetrics:
    """Application-specific metrics"""
    timestamp: datetime
    active_users: int
    total_requests: int
    requests_per_minute: float
    avg_response_time: float
    error_rate: float
    cache_hit_rate: float
    database_connections: int
    queue_size: int
    background_jobs: int

@dataclass
class HealthStatus:
    """System health status"""
    status: str  # 'healthy', 'warning', 'critical'
    score: float  # 0-100 health score
    issues: List[str]
    recommendations: List[str]
    last_updated: datetime

class SystemMonitoringService:
    """Comprehensive system monitoring service"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.system_metrics_history = deque(maxlen=max_history)
        self.application_metrics_history = deque(maxlen=max_history)
        self.health_status = HealthStatus(
            status='unknown',
            score=0,
            issues=[],
            recommendations=[],
            last_updated=datetime.now()
        )
        
        # Monitoring configuration
        self.monitoring_config = {
            'cpu_warning_threshold': 80.0,
            'cpu_critical_threshold': 95.0,
            'memory_warning_threshold': 85.0,
            'memory_critical_threshold': 95.0,
            'disk_warning_threshold': 85.0,
            'disk_critical_threshold': 95.0,
            'response_time_warning': 2.0,
            'response_time_critical': 5.0,
            'error_rate_warning': 5.0,
            'error_rate_critical': 10.0
        }
        
        # Network baseline for calculating network usage
        self.network_baseline = None
        self.last_network_check = None
        
        # Start monitoring thread
        self.monitoring_active = False
        self.monitoring_thread = None
        
    def start_monitoring(self, interval: int = 30):
        """Start continuous monitoring"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info(f"System monitoring started with {interval}s interval")
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("System monitoring stopped")
    
    def _monitoring_loop(self, interval: int):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                system_metrics = self._collect_system_metrics()
                self.system_metrics_history.append(system_metrics)
                
                # Collect application metrics
                app_metrics = self._collect_application_metrics()
                self.application_metrics_history.append(app_metrics)
                
                # Update health status
                self._update_health_status(system_metrics, app_metrics)
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system-level metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)
            memory_total_gb = memory.total / (1024**3)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_used_gb = disk.used / (1024**3)
            disk_total_gb = disk.total / (1024**3)
            
            # Network metrics
            network = psutil.net_io_counters()
            network_sent_mb = network.bytes_sent / (1024**2)
            network_recv_mb = network.bytes_recv / (1024**2)
            
            # Connection metrics
            connections = len(psutil.net_connections())
            
            # Uptime
            uptime = time.time() - psutil.boot_time()
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_gb=memory_used_gb,
                memory_total_gb=memory_total_gb,
                disk_percent=disk_percent,
                disk_used_gb=disk_used_gb,
                disk_total_gb=disk_total_gb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                active_connections=connections,
                load_average=list(load_avg),
                uptime_seconds=uptime
            )
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return self._get_empty_system_metrics()
    
    def _collect_application_metrics(self) -> ApplicationMetrics:
        """Collect application-specific metrics"""
        try:
            # This would integrate with your application's metrics
            # For now, we'll use placeholder values
            
            return ApplicationMetrics(
                timestamp=datetime.now(),
                active_users=0,  # Would come from session store
                total_requests=0,  # Would come from request counter
                requests_per_minute=0.0,  # Would be calculated
                avg_response_time=0.0,  # Would come from response time tracker
                error_rate=0.0,  # Would be calculated from error logs
                cache_hit_rate=0.0,  # Would come from cache service
                database_connections=0,  # Would come from DB connection pool
                queue_size=0,  # Would come from task queue
                background_jobs=0  # Would come from job scheduler
            )
            
        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")
            return self._get_empty_application_metrics()
    
    def _update_health_status(self, system_metrics: SystemMetrics, app_metrics: ApplicationMetrics):
        """Update overall system health status"""
        issues = []
        recommendations = []
        score = 100.0
        
        # Check CPU
        if system_metrics.cpu_percent >= self.monitoring_config['cpu_critical_threshold']:
            issues.append(f"Critical CPU usage: {system_metrics.cpu_percent:.1f}%")
            recommendations.append("Consider scaling horizontally or optimizing CPU-intensive operations")
            score -= 30
        elif system_metrics.cpu_percent >= self.monitoring_config['cpu_warning_threshold']:
            issues.append(f"High CPU usage: {system_metrics.cpu_percent:.1f}%")
            recommendations.append("Monitor CPU usage and consider optimization")
            score -= 15
        
        # Check Memory
        if system_metrics.memory_percent >= self.monitoring_config['memory_critical_threshold']:
            issues.append(f"Critical memory usage: {system_metrics.memory_percent:.1f}%")
            recommendations.append("Immediate memory optimization required")
            score -= 30
        elif system_metrics.memory_percent >= self.monitoring_config['memory_warning_threshold']:
            issues.append(f"High memory usage: {system_metrics.memory_percent:.1f}%")
            recommendations.append("Monitor memory usage and consider cleanup")
            score -= 15
        
        # Check Disk
        if system_metrics.disk_percent >= self.monitoring_config['disk_critical_threshold']:
            issues.append(f"Critical disk usage: {system_metrics.disk_percent:.1f}%")
            recommendations.append("Immediate disk cleanup required")
            score -= 25
        elif system_metrics.disk_percent >= self.monitoring_config['disk_warning_threshold']:
            issues.append(f"High disk usage: {system_metrics.disk_percent:.1f}%")
            recommendations.append("Monitor disk usage and consider cleanup")
            score -= 10
        
        # Check Response Time
        if app_metrics.avg_response_time >= self.monitoring_config['response_time_critical']:
            issues.append(f"Critical response time: {app_metrics.avg_response_time:.2f}s")
            recommendations.append("Optimize database queries and caching")
            score -= 20
        elif app_metrics.avg_response_time >= self.monitoring_config['response_time_warning']:
            issues.append(f"Slow response time: {app_metrics.avg_response_time:.2f}s")
            recommendations.append("Monitor response times and optimize bottlenecks")
            score -= 10
        
        # Check Error Rate
        if app_metrics.error_rate >= self.monitoring_config['error_rate_critical']:
            issues.append(f"Critical error rate: {app_metrics.error_rate:.1f}%")
            recommendations.append("Immediate error investigation required")
            score -= 25
        elif app_metrics.error_rate >= self.monitoring_config['error_rate_warning']:
            issues.append(f"High error rate: {app_metrics.error_rate:.1f}%")
            recommendations.append("Monitor error logs and fix issues")
            score -= 15
        
        # Determine status
        if score >= 90:
            status = 'healthy'
        elif score >= 70:
            status = 'warning'
        else:
            status = 'critical'
        
        self.health_status = HealthStatus(
            status=status,
            score=max(0, score),
            issues=issues,
            recommendations=recommendations,
            last_updated=datetime.now()
        )
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current system and application metrics"""
        system_metrics = self.system_metrics_history[-1] if self.system_metrics_history else None
        app_metrics = self.application_metrics_history[-1] if self.application_metrics_history else None
        
        return {
            'system': asdict(system_metrics) if system_metrics else None,
            'application': asdict(app_metrics) if app_metrics else None,
            'health': asdict(self.health_status),
            'monitoring_active': self.monitoring_active,
            'metrics_count': {
                'system': len(self.system_metrics_history),
                'application': len(self.application_metrics_history)
            }
        }
    
    def get_metrics_history(self, hours: int = 24) -> Dict[str, List[Dict]]:
        """Get metrics history for the specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        system_history = [
            asdict(metric) for metric in self.system_metrics_history
            if metric.timestamp >= cutoff_time
        ]
        
        app_history = [
            asdict(metric) for metric in self.application_metrics_history
            if metric.timestamp >= cutoff_time
        ]
        
        return {
            'system': system_history,
            'application': app_history
        }
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get a summary of system health"""
        return {
            'status': self.health_status.status,
            'score': self.health_status.score,
            'issues_count': len(self.health_status.issues),
            'recommendations_count': len(self.health_status.recommendations),
            'last_updated': self.health_status.last_updated.isoformat(),
            'uptime': self._get_uptime_string()
        }
    
    def _get_uptime_string(self) -> str:
        """Get formatted uptime string"""
        if not self.system_metrics_history:
            return "Unknown"
        
        uptime_seconds = self.system_metrics_history[-1].uptime_seconds
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        
        return f"{days}d {hours}h {minutes}m"
    
    def _get_empty_system_metrics(self) -> SystemMetrics:
        """Get empty system metrics for error cases"""
        return SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=0,
            memory_percent=0,
            memory_used_gb=0,
            memory_total_gb=0,
            disk_percent=0,
            disk_used_gb=0,
            disk_total_gb=0,
            network_sent_mb=0,
            network_recv_mb=0,
            active_connections=0,
            load_average=[0, 0, 0],
            uptime_seconds=0
        )
    
    def _get_empty_application_metrics(self) -> ApplicationMetrics:
        """Get empty application metrics for error cases"""
        return ApplicationMetrics(
            timestamp=datetime.now(),
            active_users=0,
            total_requests=0,
            requests_per_minute=0.0,
            avg_response_time=0.0,
            error_rate=0.0,
            cache_hit_rate=0.0,
            database_connections=0,
            queue_size=0,
            background_jobs=0
        )

# Global monitoring service instance
system_monitor = SystemMonitoringService()

def get_system_monitor() -> SystemMonitoringService:
    """Get the global system monitoring service instance"""
    return system_monitor
