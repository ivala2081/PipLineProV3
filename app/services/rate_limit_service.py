"""
Enhanced Rate Limiting Service with Monitoring and Analytics
Provides comprehensive rate limiting with detailed tracking and alerting
"""
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque
from flask import request, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.utils.unified_logger import get_logger
from app.utils.unified_error_handler import RateLimitError

logger = get_logger("RateLimitService")


class RateLimitTracker:
    """Track rate limit events and violations"""
    
    def __init__(self, max_events: int = 10000):
        self.events: deque = deque(maxlen=max_events)
        self.violations: deque = deque(maxlen=1000)
        self.endpoint_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total_requests': 0,
            'allowed': 0,
            'blocked': 0,
            'violations': 0,
            'last_reset': datetime.now(timezone.utc)
        })
        self.ip_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total_requests': 0,
            'violations': 0,
            'first_seen': datetime.now(timezone.utc),
            'last_seen': datetime.now(timezone.utc),
            'endpoints': defaultdict(int)
        })
    
    def record_request(self, endpoint: str, ip: str, allowed: bool, limit: Optional[str] = None):
        """Record a rate limit event"""
        timestamp = datetime.now(timezone.utc)
        
        # Record event
        self.events.append({
            'timestamp': timestamp.isoformat(),
            'endpoint': endpoint,
            'ip': ip,
            'allowed': allowed,
            'limit': limit
        })
        
        # Update endpoint stats
        self.endpoint_stats[endpoint]['total_requests'] += 1
        if allowed:
            self.endpoint_stats[endpoint]['allowed'] += 1
        else:
            self.endpoint_stats[endpoint]['blocked'] += 1
            self.endpoint_stats[endpoint]['violations'] += 1
            
            # Record violation
            self.violations.append({
                'timestamp': timestamp.isoformat(),
                'endpoint': endpoint,
                'ip': ip,
                'limit': limit
            })
        
        # Update IP stats
        self.ip_stats[ip]['total_requests'] += 1
        self.ip_stats[ip]['last_seen'] = timestamp
        self.ip_stats[ip]['endpoints'][endpoint] += 1
        if not allowed:
            self.ip_stats[ip]['violations'] += 1
        
        # Log violations
        if not allowed:
            logger.warning(
                f"Rate limit exceeded: {endpoint} from {ip}",
                extra={
                    'rate_limit': True,
                    'endpoint': endpoint,
                    'ip': ip,
                    'limit': limit
                }
            )
    
    def get_endpoint_stats(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for endpoint(s)"""
        if endpoint:
            return self.endpoint_stats.get(endpoint, {})
        return dict(self.endpoint_stats)
    
    def get_ip_stats(self, ip: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for IP(s)"""
        if ip:
            stats = self.ip_stats.get(ip, {})
            # Convert defaultdict to dict
            if 'endpoints' in stats:
                stats['endpoints'] = dict(stats['endpoints'])
            return stats
        return {ip: dict(stats) for ip, stats in self.ip_stats.items()}
    
    def get_recent_violations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent rate limit violations"""
        return list(self.violations)[-limit:]
    
    def get_top_violators(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top IPs by violation count"""
        violators = sorted(
            self.ip_stats.items(),
            key=lambda x: x[1]['violations'],
            reverse=True
        )[:limit]
        
        return [
            {
                'ip': ip,
                'violations': stats['violations'],
                'total_requests': stats['total_requests'],
                'violation_rate': stats['violations'] / max(stats['total_requests'], 1) * 100,
                'first_seen': stats['first_seen'].isoformat(),
                'last_seen': stats['last_seen'].isoformat(),
                'top_endpoints': dict(sorted(
                    stats['endpoints'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5])
            }
            for ip, stats in violators
        ]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive rate limiting summary"""
        total_events = len(self.events)
        total_violations = len(self.violations)
        violation_rate = (total_violations / max(total_events, 1)) * 100
        
        return {
            'total_requests': total_events,
            'total_violations': total_violations,
            'violation_rate_percent': round(violation_rate, 2),
            'endpoints_tracked': len(self.endpoint_stats),
            'unique_ips': len(self.ip_stats),
            'top_violators': self.get_top_violators(5),
            'recent_violations': self.get_recent_violations(20),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


class EnhancedRateLimitService:
    """Enhanced rate limiting service with monitoring"""
    
    def __init__(self, limiter: Limiter):
        self.limiter = limiter
        self.tracker = RateLimitTracker()
        self._setup_hooks()
    
    def _setup_hooks(self):
        """Setup rate limit hooks for tracking"""
        @self.limiter.request_filter
        def track_rate_limit():
            """Track rate limit events"""
            try:
                endpoint = request.endpoint or request.path
                ip = get_remote_address()
                
                # This will be called before rate limit check
                # We'll track after the check in the decorator
                pass
            except Exception:
                pass
    
    def get_limit_decorator(self, limit: str, key_func=None):
        """Get rate limit decorator with tracking"""
        def decorator(f):
            original_decorator = self.limiter.limit(limit, key_func=key_func)
            decorated = original_decorator(f)
            
            # Wrap to track
            def wrapper(*args, **kwargs):
                endpoint = request.endpoint or request.path
                ip = get_remote_address()
                
                # Check if rate limit was exceeded
                # This is a simplified check - actual limit check happens in limiter
                try:
                    result = decorated(*args, **kwargs)
                    self.tracker.record_request(endpoint, ip, allowed=True, limit=limit)
                    return result
                except Exception as e:
                    # Check if it's a rate limit error
                    if '429' in str(e) or 'rate limit' in str(e).lower():
                        self.tracker.record_request(endpoint, ip, allowed=False, limit=limit)
                    raise
            
            return wrapper
        return decorator
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics"""
        return self.tracker.get_summary()
    
    def get_endpoint_stats(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """Get endpoint statistics"""
        return self.tracker.get_endpoint_stats(endpoint)
    
    def get_ip_stats(self, ip: Optional[str] = None) -> Dict[str, Any]:
        """Get IP statistics"""
        return self.tracker.get_ip_stats(ip)
    
    def get_violations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent violations"""
        return self.tracker.get_recent_violations(limit)
    
    def get_top_violators(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top violators"""
        return self.tracker.get_top_violators(limit)


# Global instance
_rate_limit_service: Optional[EnhancedRateLimitService] = None


def get_rate_limit_service(limiter: Optional[Limiter] = None) -> Optional[EnhancedRateLimitService]:
    """Get or create rate limit service instance"""
    global _rate_limit_service
    
    if _rate_limit_service is None and limiter:
        _rate_limit_service = EnhancedRateLimitService(limiter)
    
    return _rate_limit_service


def init_rate_limit_service(limiter: Limiter):
    """Initialize rate limit service"""
    return get_rate_limit_service(limiter)

