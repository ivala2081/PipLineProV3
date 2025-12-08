"""
Performance Monitoring and Optimization Service
Provides safe performance monitoring and optimization utilities
"""

import time
import logging
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
from flask import request, g
from functools import wraps
import gc

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Performance monitoring service"""
    
    def __init__(self):
        self.request_times = deque(maxlen=1000)  # Last 1000 requests
        self.slow_queries = deque(maxlen=100)    # Last 100 slow queries
        self.endpoint_stats = defaultdict(list)
        self.system_stats = deque(maxlen=100)    # System metrics
        self.slow_threshold = 1.0  # 1 second
        
    def record_request(self, endpoint: str, duration: float, status_code: int):
        """Record request performance"""
        timestamp = datetime.now()
        
        request_data = {
            'endpoint': endpoint,
            'duration': duration,
            'status_code': status_code,
            'timestamp': timestamp
        }
        
        self.request_times.append(request_data)
        self.endpoint_stats[endpoint].append(duration)
        
        # Track slow requests
        if duration > self.slow_threshold:
            self.slow_queries.append(request_data)
            logger.warning(f"Slow request detected: {endpoint} took {duration:.2f}s")
    
    def record_system_metrics(self):
        """Record system performance metrics"""
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            
            metrics = {
                'timestamp': datetime.now(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available': memory.available,
                'memory_used': memory.used
            }
            
            self.system_stats.append(metrics)
            
        except Exception as e:
            logger.error(f"Error recording system metrics: {e}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.request_times:
            return {'status': 'no_data', 'message': 'No performance data available'}
        
        # Calculate statistics
        recent_requests = list(self.request_times)[-100:]  # Last 100 requests
        durations = [req['duration'] for req in recent_requests]
        
        avg_response_time = sum(durations) / len(durations) if durations else 0
        max_response_time = max(durations) if durations else 0
        min_response_time = min(durations) if durations else 0
        
        # Count requests by status
        status_counts = defaultdict(int)
        for req in recent_requests:
            status_counts[req['status_code']] += 1
        
        # Get slowest endpoints
        endpoint_averages = {}
        for endpoint, times in self.endpoint_stats.items():
            if times:
                endpoint_averages[endpoint] = sum(times) / len(times)
        
        slowest_endpoints = sorted(
            endpoint_averages.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        # System metrics
        system_summary = {}
        if self.system_stats:
            latest_system = list(self.system_stats)[-1]
            system_summary = {
                'cpu_percent': latest_system['cpu_percent'],
                'memory_percent': latest_system['memory_percent'],
                'memory_available_mb': latest_system['memory_available'] / (1024 * 1024)
            }
        
        return {
            'status': 'ok',
            'summary': {
                'total_requests': len(recent_requests),
                'avg_response_time': round(avg_response_time, 3),
                'max_response_time': round(max_response_time, 3),
                'min_response_time': round(min_response_time, 3),
                'slow_requests_count': len([r for r in recent_requests if r['duration'] > self.slow_threshold]),
                'status_codes': dict(status_counts),
                'slowest_endpoints': slowest_endpoints,
                'system_metrics': system_summary
            }
        }
    
    def optimize_memory(self) -> Dict[str, Any]:
        """Perform safe memory optimization"""
        try:
            # Get memory before cleanup
            memory_before = psutil.virtual_memory().percent
            
            # Force garbage collection
            collected = gc.collect()
            
            # Get memory after cleanup  
            memory_after = psutil.virtual_memory().percent
            
            result = {
                'status': 'success',
                'memory_before': memory_before,
                'memory_after': memory_after,
                'improvement': memory_before - memory_after,
                'objects_collected': collected
            }
            
            logger.info(f"Memory optimization: {memory_before}% -> {memory_after}% (freed {collected} objects)")
            return result
            
        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
            return {'status': 'error', 'message': str(e)}


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def monitor_performance(f):
    """Decorator to monitor endpoint performance"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = f(*args, **kwargs)
            status_code = getattr(result, 'status_code', 200)
        except Exception as e:
            status_code = 500
            raise
        finally:
            duration = time.time() - start_time
            endpoint = request.endpoint or 'unknown'
            performance_monitor.record_request(endpoint, duration, status_code)
        
        return result
    return decorated_function


def start_system_monitoring():
    """Start background system monitoring"""
    def monitor_loop():
        while True:
            try:
                performance_monitor.record_system_metrics()
                time.sleep(30)  # Record every 30 seconds
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                time.sleep(60)  # Wait longer on error
    
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()
    logger.info("System performance monitoring started")
