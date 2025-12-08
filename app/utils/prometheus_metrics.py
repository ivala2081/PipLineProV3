"""
Enhanced Prometheus Metrics
Comprehensive metrics collection for monitoring and observability
"""
import time
from typing import Dict, Optional
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest
from flask import request, current_app
import functools

# HTTP Metrics
http_request_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Database Metrics
db_query_total = Counter(
    'db_queries_total',
    'Total database queries',
    ['operation', 'table']
)

db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table']
)

db_connection_pool_size = Gauge(
    'db_connection_pool_size',
    'Database connection pool size',
    ['state']  # active, idle, waiting
)

db_slow_queries_total = Counter(
    'db_slow_queries_total',
    'Total slow queries (>1s)',
    ['table']
)

# Cache Metrics
cache_operations_total = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['operation', 'status']  # operation: get, set, delete, status: hit, miss
)

cache_size = Gauge(
    'cache_size',
    'Cache size in bytes'
)

# Business Metrics
transactions_total = Counter(
    'transactions_total',
    'Total transactions processed',
    ['status', 'psp', 'currency']
)

transaction_amount = Histogram(
    'transaction_amount',
    'Transaction amounts',
    ['currency'],
    buckets=[10, 50, 100, 500, 1000, 5000, 10000, 50000, 100000]
)

psp_commissions_total = Counter(
    'psp_commissions_total',
    'Total PSP commissions',
    ['psp_name']
)

# System Metrics
system_cpu_percent = Gauge(
    'system_cpu_percent',
    'CPU usage percentage'
)

system_memory_bytes = Gauge(
    'system_memory_bytes',
    'Memory usage in bytes',
    ['state']  # total, used, available
)

system_disk_bytes = Gauge(
    'system_disk_bytes',
    'Disk usage in bytes',
    ['state']  # total, used, free
)

# Application Info
# Note: app_info is automatically created by prometheus_flask_exporter's PrometheusMetrics
# We don't create it here to avoid duplicate metric errors
# If needed, use it through the PrometheusMetrics instance
app_info = None  # Managed by PrometheusMetrics


def track_request_duration(func):
    """Decorator to track HTTP request duration"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            response = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Track metrics
            endpoint = request.endpoint or 'unknown'
            method = request.method
            status = response.status_code if hasattr(response, 'status_code') else 200
            
            http_request_duration.labels(method=method, endpoint=endpoint).observe(duration)
            http_request_total.labels(method=method, endpoint=endpoint, status=status).inc()
            
            return response
        except Exception as e:
            duration = time.time() - start_time
            endpoint = request.endpoint or 'unknown'
            method = request.method
            
            http_request_duration.labels(method=method, endpoint=endpoint).observe(duration)
            http_request_total.labels(method=method, endpoint=endpoint, status=500).inc()
            raise
    return wrapper


def track_db_query(operation: str, table: str):
    """Track database query metrics"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                db_query_duration.labels(operation=operation, table=table).observe(duration)
                db_query_total.labels(operation=operation, table=table).inc()
                
                # Track slow queries
                if duration > 1.0:  # > 1 second
                    db_slow_queries_total.labels(table=table).inc()
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                db_query_duration.labels(operation=operation, table=table).observe(duration)
                db_query_total.labels(operation=operation, table=table).inc()
                raise
        return wrapper
    return decorator


def update_system_metrics():
    """Update system metrics (CPU, Memory, Disk)"""
    try:
        import psutil
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        system_cpu_percent.set(cpu_percent)
        
        # Memory
        memory = psutil.virtual_memory()
        system_memory_bytes.labels(state='total').set(memory.total)
        system_memory_bytes.labels(state='used').set(memory.used)
        system_memory_bytes.labels(state='available').set(memory.available)
        
        # Disk
        disk = psutil.disk_usage('/')
        system_disk_bytes.labels(state='total').set(disk.total)
        system_disk_bytes.labels(state='used').set(disk.used)
        system_disk_bytes.labels(state='free').set(disk.free)
    except Exception as e:
        current_app.logger.warning(f"Failed to update system metrics: {e}")


def track_cache_operation(operation: str, hit: bool):
    """Track cache operations"""
    status = 'hit' if hit else 'miss'
    cache_operations_total.labels(operation=operation, status=status).inc()


def track_transaction(status: str, psp: Optional[str] = None, currency: str = 'USD', amount: float = 0):
    """Track business transaction metrics"""
    transactions_total.labels(status=status, psp=psp or 'unknown', currency=currency).inc()
    if amount > 0:
        transaction_amount.labels(currency=currency).observe(amount)


def track_psp_commission(psp_name: str, amount: float):
    """Track PSP commission metrics"""
    psp_commissions_total.labels(psp_name=psp_name).inc(amount)


def get_metrics():
    """Get all Prometheus metrics in text format"""
    return generate_latest()

