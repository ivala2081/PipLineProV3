"""
Metrics Collector
Centralized metrics collection and aggregation
"""
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from collections import defaultdict, deque
from flask import g, request
from app.utils.prometheus_metrics import (
    http_request_total, http_request_duration,
    db_query_total, db_query_duration,
    cache_operations_total,
    transactions_total
)

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collect and aggregate application metrics"""
    
    def __init__(self):
        self.request_metrics = defaultdict(list)
        self.query_metrics = defaultdict(list)
        self.cache_metrics = defaultdict(int)
        self.business_metrics = defaultdict(int)
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        # Record in Prometheus
        http_request_total.labels(
            method=method,
            endpoint=endpoint,
            status=status_code
        ).inc()
        
        http_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
        # Store in memory for aggregation
        self.request_metrics[endpoint].append({
            'method': method,
            'status_code': status_code,
            'duration': duration,
            'timestamp': datetime.now(timezone.utc)
        })
        
        # Keep only last 1000 requests per endpoint
        if len(self.request_metrics[endpoint]) > 1000:
            self.request_metrics[endpoint] = self.request_metrics[endpoint][-1000:]
    
    def record_query(self, operation: str, table: str, duration: float):
        """Record database query metrics"""
        # Record in Prometheus
        db_query_total.labels(
            operation=operation,
            table=table
        ).inc()
        
        db_query_duration.labels(
            operation=operation,
            table=table
        ).observe(duration)
        
        # Store in memory
        key = f"{operation}:{table}"
        self.query_metrics[key].append({
            'duration': duration,
            'timestamp': datetime.now(timezone.utc)
        })
    
    def record_cache_operation(self, operation: str, status: str):
        """Record cache operation metrics"""
        # Record in Prometheus
        cache_operations_total.labels(
            operation=operation,
            status=status
        ).inc()
        
        # Store in memory
        self.cache_metrics[f"{operation}:{status}"] += 1
    
    def record_transaction(self, status: str, psp: str, currency: str):
        """Record business transaction metrics"""
        # Record in Prometheus
        transactions_total.labels(
            status=status,
            psp=psp,
            currency=currency
        ).inc()
        
        # Store in memory
        self.business_metrics[f"transaction:{status}:{psp}:{currency}"] += 1
    
    def get_request_stats(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """Get request statistics"""
        if endpoint:
            metrics = self.request_metrics.get(endpoint, [])
        else:
            # Aggregate all endpoints
            metrics = []
            for endpoint_metrics in self.request_metrics.values():
                metrics.extend(endpoint_metrics)
        
        if not metrics:
            return {}
        
        durations = [m['duration'] for m in metrics]
        status_codes = [m['status_code'] for m in metrics]
        
        return {
            'total_requests': len(metrics),
            'avg_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'status_codes': {
                code: status_codes.count(code) for code in set(status_codes)
            }
        }
    
    def get_query_stats(self) -> Dict[str, Any]:
        """Get query statistics"""
        all_queries = []
        for queries in self.query_metrics.values():
            all_queries.extend(queries)
        
        if not all_queries:
            return {}
        
        durations = [q['duration'] for q in all_queries]
        
        return {
            'total_queries': len(all_queries),
            'avg_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'slow_queries': len([d for d in durations if d > 1.0])
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        hits = self.cache_metrics.get('get:hit', 0)
        misses = self.cache_metrics.get('get:miss', 0)
        total = hits + misses
        
        return {
            'hits': hits,
            'misses': misses,
            'total': total,
            'hit_rate': (hits / total * 100) if total > 0 else 0
        }
    
    def get_business_stats(self) -> Dict[str, Any]:
        """Get business metrics statistics"""
        return dict(self.business_metrics)


# Global metrics collector instance
metrics_collector = MetricsCollector()

