"""
Advanced Performance Monitoring Service for PipLinePro
Real-time performance metrics and optimization recommendations
"""

import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Advanced performance monitoring with real-time optimization"""
    
    def __init__(self):
        self.metrics_history: List[Dict] = []
        self.performance_alerts: List[Dict] = []
        self.optimization_recommendations: List[Dict] = []
        self.monitoring_active = False
        self.monitor_thread = None
        self.last_cleanup = time.time()
        
        # Performance thresholds
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 80.0,
            'disk_percent': 90.0,
            'response_time_ms': 500.0,
            'database_pool_usage': 80.0,
            'cache_hit_rate': 70.0,
            'error_rate': 5.0
        }
        
        # Performance counters
        self.counters = {
            'total_requests': 0,
            'slow_requests': 0,
            'errors': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'database_queries': 0,
            'slow_queries': 0
        }
        
        # Performance trends
        self.trends = {
            'response_time': [],
            'memory_usage': [],
            'cpu_usage': [],
            'database_pool': [],
            'cache_efficiency': []
        }
        
    def start_monitoring(self):
        """Start continuous performance monitoring"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Performance monitoring started")
        
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Performance monitoring stopped")
        
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                self._collect_metrics()
                self._analyze_performance()
                self._generate_recommendations()
                self._cleanup_old_data()
                time.sleep(30)  # Monitor every 30 seconds
            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                time.sleep(60)  # Wait longer on error
                
    def _collect_metrics(self):
        """Collect current system metrics"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Application metrics
            app_metrics = self._get_application_metrics()
            
            # Database metrics
            db_metrics = self._get_database_metrics()
            
            # Cache metrics
            cache_metrics = self._get_cache_metrics()
            
            # Network metrics
            network_metrics = self._get_network_metrics()
            
            # Create metrics snapshot
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_gb': memory.available / (1024**3),
                    'disk_percent': disk.percent,
                    'disk_free_gb': disk.free / (1024**3)
                },
                'application': app_metrics,
                'database': db_metrics,
                'cache': cache_metrics,
                'network': network_metrics,
                'counters': self.counters.copy()
            }
            
            # Store metrics
            self.metrics_history.append(metrics)
            
            # Keep only last 1000 metrics
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-1000:]
                
            # Update trends
            self._update_trends(metrics)
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            
    def _get_application_metrics(self) -> Dict:
        """Get application-specific metrics"""
        try:
            app = current_app._get_current_object()
            
            # Get Flask app metrics
            metrics = {
                'active_requests': getattr(app, 'active_requests', 0),
                'total_requests': getattr(app, 'total_requests', 0),
                'error_rate': getattr(app, 'error_rate', 0.0),
                'average_response_time': getattr(app, 'avg_response_time', 0.0),
                'session_count': getattr(app, 'session_count', 0),
                'cache_size': getattr(app, 'cache_size', 0),
                'rate_limit_hits': getattr(app, 'rate_limit_hits', 0)
            }
            
            return metrics
        except Exception as e:
            logger.error(f"Error getting application metrics: {e}")
            return {}
            
    def _get_database_metrics(self) -> Dict:
        """Get database performance metrics"""
        try:
            app = current_app._get_current_object()
            
            if hasattr(app, 'db') and app.db:
                engine = app.db.engine
                pool = engine.pool
                
                metrics = {
                    'pool_size': getattr(pool, 'size', 0),
                    'checked_out': getattr(pool, 'checkedout', 0),
                    'checked_in': getattr(pool, 'checkedin', 0),
                    'overflow': getattr(pool, 'overflow', 0),
                    'invalid': getattr(pool, 'invalid', 0),
                    'pool_usage_percent': 0
                }
                
                if metrics['pool_size'] > 0:
                    total = metrics['pool_size'] + metrics['overflow']
                    used = metrics['checked_out'] + metrics['invalid']
                    metrics['pool_usage_percent'] = (used / total) * 100
                    
                return metrics
        except Exception as e:
            logger.error(f"Error getting database metrics: {e}")
            return {}
            
    def _get_cache_metrics(self) -> Dict:
        """Get cache performance metrics"""
        try:
            app = current_app._get_current_object()
            
            if hasattr(app, 'cache'):
                cache = app.cache
                
                # Try to get cache stats
                try:
                    stats = cache.get('cache_stats')
                    if stats:
                        return stats
                except:
                    pass
                    
                # Fallback to basic metrics
                total_requests = self.counters['cache_hits'] + self.counters['cache_misses']
                hit_rate = (self.counters['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
                
                return {
                    'hit_rate': hit_rate,
                    'hits': self.counters['cache_hits'],
                    'misses': self.counters['cache_misses'],
                    'total_requests': total_requests,
                    'efficiency': 'high' if hit_rate > 80 else 'medium' if hit_rate > 60 else 'low'
                }
        except Exception as e:
            logger.error(f"Error getting cache metrics: {e}")
            return {}
            
    def _get_network_metrics(self) -> Dict:
        """Get network performance metrics"""
        try:
            # Get network I/O stats
            net_io = psutil.net_io_counters()
            
            return {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'errin': net_io.errin,
                'errout': net_io.errout,
                'dropin': net_io.dropin,
                'dropout': net_io.dropout
            }
        except Exception as e:
            logger.error(f"Error getting network metrics: {e}")
            return {}
            
    def _update_trends(self, metrics: Dict):
        """Update performance trends"""
        try:
            # Response time trend
            if 'application' in metrics and 'average_response_time' in metrics['application']:
                self.trends['response_time'].append({
                    'timestamp': metrics['timestamp'],
                    'value': metrics['application']['average_response_time']
                })
                
            # Memory usage trend
            if 'system' in metrics and 'memory_percent' in metrics['system']:
                self.trends['memory_usage'].append({
                    'timestamp': metrics['timestamp'],
                    'value': metrics['system']['memory_percent']
                })
                
            # CPU usage trend
            if 'system' in metrics and 'cpu_percent' in metrics['system']:
                self.trends['cpu_usage'].append({
                    'timestamp': metrics['timestamp'],
                    'value': metrics['system']['cpu_percent']
                })
                
            # Database pool trend
            if 'database' in metrics and 'pool_usage_percent' in metrics['database']:
                self.trends['database_pool'].append({
                    'timestamp': metrics['timestamp'],
                    'value': metrics['database']['pool_usage_percent']
                })
                
            # Cache efficiency trend
            if 'cache' in metrics and 'hit_rate' in metrics['cache']:
                self.trends['cache_efficiency'].append({
                    'timestamp': metrics['timestamp'],
                    'value': metrics['cache']['hit_rate']
                })
                
            # Keep only last 100 trend points
            for trend_name in self.trends:
                if len(self.trends[trend_name]) > 100:
                    self.trends[trend_name] = self.trends[trend_name][-100:]
                    
        except Exception as e:
            logger.error(f"Error updating trends: {e}")
            
    def _analyze_performance(self):
        """Analyze performance and detect issues"""
        try:
            if not self.metrics_history:
                return
                
            latest_metrics = self.metrics_history[-1]
            
            # Check CPU usage
            if latest_metrics['system']['cpu_percent'] > self.thresholds['cpu_percent']:
                self._create_alert('high_cpu', f"CPU usage is {latest_metrics['system']['cpu_percent']:.1f}%")
                
            # Check memory usage
            if latest_metrics['system']['memory_percent'] > self.thresholds['memory_percent']:
                self._create_alert('high_memory', f"Memory usage is {latest_metrics['system']['memory_percent']:.1f}%")
                
            # Check disk usage
            if latest_metrics['system']['disk_percent'] > self.thresholds['disk_percent']:
                self._create_alert('high_disk', f"Disk usage is {latest_metrics['system']['disk_percent']:.1f}%")
                
            # Check database pool usage
            if 'database' in latest_metrics and 'pool_usage_percent' in latest_metrics['database']:
                pool_usage = latest_metrics['database']['pool_usage_percent']
                if pool_usage > self.thresholds['database_pool_usage']:
                    self._create_alert('high_db_pool', f"Database pool usage is {pool_usage:.1f}%")
                    
            # Check cache hit rate
            if 'cache' in latest_metrics and 'hit_rate' in latest_metrics['cache']:
                hit_rate = latest_metrics['cache']['hit_rate']
                if hit_rate < self.thresholds['cache_hit_rate']:
                    self._create_alert('low_cache_hit', f"Cache hit rate is {hit_rate:.1f}%")
                    
        except Exception as e:
            logger.error(f"Error analyzing performance: {e}")
            
    def _create_alert(self, alert_type: str, message: str):
        """Create a performance alert"""
        alert = {
            'id': f"{alert_type}_{int(time.time())}",
            'type': alert_type,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'severity': 'warning',
            'acknowledged': False
        }
        
        self.performance_alerts.append(alert)
        
        # Keep only last 100 alerts
        if len(self.performance_alerts) > 100:
            self.performance_alerts = self.performance_alerts[-100:]
            
        logger.warning(f"Performance alert: {message}")
        
    def _generate_recommendations(self):
        """Generate performance optimization recommendations"""
        try:
            if not self.metrics_history:
                return
                
            latest_metrics = self.metrics_history[-1]
            recommendations = []
            
            # CPU optimization recommendations
            if latest_metrics['system']['cpu_percent'] > 70:
                recommendations.append({
                    'type': 'cpu_optimization',
                    'priority': 'high',
                    'title': 'Optimize CPU Usage',
                    'description': 'Consider implementing async processing, reducing database queries, or scaling horizontally',
                    'impact': 'high',
                    'effort': 'medium'
                })
                
            # Memory optimization recommendations
            if latest_metrics['system']['memory_percent'] > 70:
                recommendations.append({
                    'type': 'memory_optimization',
                    'priority': 'high',
                    'title': 'Optimize Memory Usage',
                    'description': 'Implement memory pooling, reduce object creation, or increase memory limits',
                    'impact': 'high',
                    'effort': 'medium'
                })
                
            # Database optimization recommendations
            if 'database' in latest_metrics and 'pool_usage_percent' in latest_metrics['database']:
                pool_usage = latest_metrics['database']['pool_usage_percent']
                if pool_usage > 70:
                    recommendations.append({
                        'type': 'database_optimization',
                        'priority': 'medium',
                        'title': 'Optimize Database Pool',
                        'description': f'Database pool usage is {pool_usage:.1f}%. Consider increasing pool size or optimizing queries',
                        'impact': 'medium',
                        'effort': 'low'
                    })
                    
            # Cache optimization recommendations
            if 'cache' in latest_metrics and 'hit_rate' in latest_metrics['cache']:
                hit_rate = latest_metrics['cache']['hit_rate']
                if hit_rate < 60:
                    recommendations.append({
                        'type': 'cache_optimization',
                        'priority': 'medium',
                        'title': 'Improve Cache Efficiency',
                        'description': f'Cache hit rate is {hit_rate:.1f}%. Consider increasing cache size or optimizing cache keys',
                        'impact': 'medium',
                        'effort': 'low'
                    })
                    
            # Update recommendations
            self.optimization_recommendations = recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            
    def _cleanup_old_data(self):
        """Clean up old performance data"""
        try:
            current_time = time.time()
            
            # Clean up old metrics (keep last 24 hours)
            cutoff_time = current_time - (24 * 60 * 60)
            
            # Clean up old alerts (keep last 7 days)
            alert_cutoff = current_time - (7 * 24 * 60 * 60)
            
            # Clean up old trends (keep last 7 days)
            trend_cutoff = current_time - (7 * 24 * 60 * 60)
            
            # Clean up metrics
            self.metrics_history = [
                m for m in self.metrics_history
                if time.mktime(datetime.fromisoformat(m['timestamp']).timetuple()) > cutoff_time
            ]
            
            # Clean up alerts
            self.performance_alerts = [
                a for a in self.performance_alerts
                if time.mktime(datetime.fromisoformat(a['timestamp']).timetuple()) > alert_cutoff
            ]
            
            # Clean up trends
            for trend_name in self.trends:
                self.trends[trend_name] = [
                    t for t in self.trends[trend_name]
                    if time.mktime(datetime.fromisoformat(t['timestamp']).timetuple()) > trend_cutoff
                ]
                
            # Update cleanup time
            self.last_cleanup = current_time
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            
    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary"""
        try:
            if not self.metrics_history:
                return {'error': 'No performance data available'}
                
            latest_metrics = self.metrics_history[-1]
            
            # Calculate averages for the last hour
            one_hour_ago = datetime.now() - timedelta(hours=1)
            recent_metrics = [
                m for m in self.metrics_history
                if datetime.fromisoformat(m['timestamp']) > one_hour_ago
            ]
            
            if recent_metrics:
                avg_cpu = sum(m['system']['cpu_percent'] for m in recent_metrics) / len(recent_metrics)
                avg_memory = sum(m['system']['memory_percent'] for m in recent_metrics) / len(recent_metrics)
                avg_disk = sum(m['system']['disk_percent'] for m in recent_metrics) / len(recent_metrics)
            else:
                avg_cpu = avg_memory = avg_disk = 0
                
            # Performance score calculation
            performance_score = self._calculate_performance_score(latest_metrics)
            
            summary = {
                'current_metrics': latest_metrics,
                'hourly_averages': {
                    'cpu_percent': round(avg_cpu, 2),
                    'memory_percent': round(avg_memory, 2),
                    'disk_percent': round(avg_disk, 2)
                },
                'performance_score': performance_score,
                'alerts_count': len(self.performance_alerts),
                'recommendations_count': len(self.optimization_recommendations),
                'trends': self.trends,
                'counters': self.counters,
                'monitoring_status': {
                    'active': self.monitoring_active,
                    'last_update': latest_metrics['timestamp'],
                    'metrics_count': len(self.metrics_history)
                }
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {'error': str(e)}
            
    def _calculate_performance_score(self, metrics: Dict) -> int:
        """Calculate overall performance score (0-100)"""
        try:
            score = 100
            
            # Deduct points for high resource usage
            if metrics['system']['cpu_percent'] > 80:
                score -= 20
            elif metrics['system']['cpu_percent'] > 60:
                score -= 10
                
            if metrics['system']['memory_percent'] > 80:
                score -= 20
            elif metrics['system']['memory_percent'] > 60:
                score -= 10
                
            if metrics['system']['disk_percent'] > 90:
                score -= 15
            elif metrics['system']['disk_percent'] > 70:
                score -= 5
                
            # Deduct points for database issues
            if 'database' in metrics and 'pool_usage_percent' in metrics['database']:
                pool_usage = metrics['database']['pool_usage_percent']
                if pool_usage > 80:
                    score -= 15
                elif pool_usage > 60:
                    score -= 5
                    
            # Deduct points for cache issues
            if 'cache' in metrics and 'hit_rate' in metrics['cache']:
                hit_rate = metrics['cache']['hit_rate']
                if hit_rate < 50:
                    score -= 15
                elif hit_rate < 70:
                    score -= 5
                    
            # Ensure score is between 0 and 100
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating performance score: {e}")
            return 50
            
    def get_optimization_recommendations(self) -> List[Dict]:
        """Get current optimization recommendations"""
        return self.optimization_recommendations.copy()
        
    def get_performance_alerts(self) -> List[Dict]:
        """Get current performance alerts"""
        return self.performance_alerts.copy()
        
    def acknowledge_alert(self, alert_id: str):
        """Acknowledge a performance alert"""
        for alert in self.performance_alerts:
            if alert['id'] == alert_id:
                alert['acknowledged'] = True
                break
                
    def reset_counters(self):
        """Reset performance counters"""
        for key in self.counters:
            self.counters[key] = 0
            
    def increment_counter(self, counter_name: str, value: int = 1):
        """Increment a performance counter"""
        if counter_name in self.counters:
            self.counters[counter_name] += value

# Global performance monitor instance
performance_monitor = PerformanceMonitor()
