"""
Microservice Service for PipLinePro
Manages service discovery, communication, and load balancing
"""
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import requests
import redis
from flask import current_app

logger = logging.getLogger(__name__)

class ServiceType(Enum):
    """Service types in the microservices architecture"""
    TRANSACTION_SERVICE = "transaction_service"
    ANALYTICS_SERVICE = "analytics_service"
    USER_SERVICE = "user_service"
    PSP_SERVICE = "psp_service"
    NOTIFICATION_SERVICE = "notification_service"
    CACHE_SERVICE = "cache_service"
    AUTH_SERVICE = "auth_service"

class ServiceStatus(Enum):
    """Service status"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    STOPPING = "stopping"

@dataclass
class ServiceInstance:
    """Service instance information"""
    id: str
    service_type: ServiceType
    host: str
    port: int
    status: ServiceStatus
    last_heartbeat: datetime
    metadata: Dict[str, Any]
    
    @property
    def url(self) -> str:
        """Get service URL"""
        return f"http://{self.host}:{self.port}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'service_type': self.service_type.value,
            'host': self.host,
            'port': self.port,
            'status': self.status.value,
            'last_heartbeat': self.last_heartbeat.isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServiceInstance':
        """Create from dictionary"""
        return cls(
            id=data['id'],
            service_type=ServiceType(data['service_type']),
            host=data['host'],
            port=data['port'],
            status=ServiceStatus(data['status']),
            last_heartbeat=datetime.fromisoformat(data['last_heartbeat']),
            metadata=data.get('metadata', {})
        )

class LoadBalancer:
    """Simple load balancer for service instances"""
    
    def __init__(self):
        self.round_robin_index = 0
    
    def select_instance(self, instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        """Select an instance using round-robin"""
        healthy_instances = [i for i in instances if i.status == ServiceStatus.HEALTHY]
        if not healthy_instances:
            return None
        
        instance = healthy_instances[self.round_robin_index % len(healthy_instances)]
        self.round_robin_index += 1
        return instance

class MicroserviceService:
    """Service for managing microservices architecture"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self._redis_client = redis_client
        self._redis_initialized = False
        self._heartbeat_started = False
        self.service_registry_key = "pipeline:services"
        self.heartbeat_interval = 30  # seconds
        self.service_timeout = 60  # seconds
        self.load_balancer = LoadBalancer()
        self.service_instances: Dict[ServiceType, List[ServiceInstance]] = {}
        
        # Service communication
        self.service_clients: Dict[ServiceType, Any] = {}
    
    @property
    def redis_client(self) -> Optional[redis.Redis]:
        """Lazy initialization of Redis client"""
        if not self._redis_initialized:
            self._redis_client = self._get_redis_client()
            self._redis_initialized = True
            # Start heartbeat monitoring on first access
            if self._redis_client and not self._heartbeat_started:
                self._start_heartbeat_monitor()
                self._heartbeat_started = True
        return self._redis_client
    
    def _get_redis_client(self) -> Optional[redis.Redis]:
        """Get Redis client"""
        try:
            from flask import has_app_context
            if not has_app_context():
                return None
            
            redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
            redis_enabled = current_app.config.get('REDIS_ENABLED', False)
            if isinstance(redis_enabled, str):
                redis_enabled = redis_enabled.lower() == 'true'
            
            if not redis_enabled:
                return None
                
            return redis.from_url(redis_url, decode_responses=True)
        except Exception as e:
            logger.debug(f"Redis not available: {e}")
            return None
    
    def register_service(self, service_type: ServiceType, host: str, port: int, 
                        metadata: Dict[str, Any] = None) -> str:
        """Register a service instance"""
        service_id = str(uuid.uuid4())
        instance = ServiceInstance(
            id=service_id,
            service_type=service_type,
            host=host,
            port=port,
            status=ServiceStatus.HEALTHY,
            last_heartbeat=datetime.now(timezone.utc),
            metadata=metadata or {}
        )
        
        # Store in Redis
        if self.redis_client:
            try:
                self.redis_client.hset(
                    self.service_registry_key,
                    service_id,
                    json.dumps(instance.to_dict())
                )
                self.redis_client.expire(self.service_registry_key, 3600)  # 1 hour TTL
            except Exception as e:
                logger.error(f"Error registering service: {e}")
        
        # Update local registry
        if service_type not in self.service_instances:
            self.service_instances[service_type] = []
        self.service_instances[service_type].append(instance)
        
        logger.info(f"Registered service {service_type.value} at {host}:{port}")
        return service_id
    
    def unregister_service(self, service_id: str):
        """Unregister a service instance"""
        # Remove from Redis
        if self.redis_client:
            try:
                self.redis_client.hdel(self.service_registry_key, service_id)
            except Exception as e:
                logger.error(f"Error unregistering service: {e}")
        
        # Remove from local registry
        for service_type, instances in self.service_instances.items():
            self.service_instances[service_type] = [
                i for i in instances if i.id != service_id
            ]
        
        logger.info(f"Unregistered service {service_id}")
    
    def discover_services(self) -> Dict[ServiceType, List[ServiceInstance]]:
        """Discover all registered services"""
        if not self.redis_client:
            return self.service_instances
        
        try:
            # Get all services from Redis
            services_data = self.redis_client.hgetall(self.service_registry_key)
            
            # Parse and organize by service type
            discovered_services = {}
            for service_id, service_json in services_data.items():
                try:
                    service_data = json.loads(service_json)
                    instance = ServiceInstance.from_dict(service_data)
                    
                    if instance.service_type not in discovered_services:
                        discovered_services[instance.service_type] = []
                    discovered_services[instance.service_type].append(instance)
                    
                except Exception as e:
                    logger.error(f"Error parsing service data for {service_id}: {e}")
            
            # Update local registry
            self.service_instances = discovered_services
            return discovered_services
            
        except Exception as e:
            logger.error(f"Error discovering services: {e}")
            return self.service_instances
    
    def get_service_instance(self, service_type: ServiceType) -> Optional[ServiceInstance]:
        """Get a healthy service instance"""
        instances = self.service_instances.get(service_type, [])
        return self.load_balancer.select_instance(instances)
    
    def call_service(self, service_type: ServiceType, endpoint: str, 
                    method: str = 'GET', data: Dict[str, Any] = None,
                    timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Call a service endpoint"""
        instance = self.get_service_instance(service_type)
        if not instance:
            logger.error(f"No healthy instance found for {service_type.value}")
            return None
        
        try:
            url = f"{instance.url}{endpoint}"
            headers = {'Content-Type': 'application/json'}
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            response.raise_for_status()
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling service {service_type.value}: {e}")
            # Mark instance as unhealthy
            instance.status = ServiceStatus.UNHEALTHY
            return None
    
    def _start_heartbeat_monitor(self):
        """Start monitoring service heartbeats"""
        import threading
        
        def monitor_heartbeats():
            while True:
                try:
                    self._check_service_health()
                    time.sleep(self.heartbeat_interval)
                except Exception as e:
                    logger.error(f"Error in heartbeat monitor: {e}")
                    time.sleep(self.heartbeat_interval)
        
        monitor_thread = threading.Thread(target=monitor_heartbeats, daemon=True)
        monitor_thread.start()
    
    def _check_service_health(self):
        """Check health of all registered services"""
        current_time = datetime.now(timezone.utc)
        
        for service_type, instances in self.service_instances.items():
            for instance in instances:
                # Check if heartbeat is too old
                time_since_heartbeat = (current_time - instance.last_heartbeat).total_seconds()
                
                if time_since_heartbeat > self.service_timeout:
                    if instance.status == ServiceStatus.HEALTHY:
                        logger.warning(f"Service {instance.id} appears unhealthy (no heartbeat for {time_since_heartbeat}s)")
                        instance.status = ServiceStatus.UNHEALTHY
                else:
                    if instance.status == ServiceStatus.UNHEALTHY:
                        logger.info(f"Service {instance.id} is healthy again")
                        instance.status = ServiceStatus.HEALTHY
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        stats = {
            'total_services': 0,
            'healthy_services': 0,
            'unhealthy_services': 0,
            'services_by_type': {}
        }
        
        for service_type, instances in self.service_instances.items():
            healthy_count = sum(1 for i in instances if i.status == ServiceStatus.HEALTHY)
            unhealthy_count = len(instances) - healthy_count
            
            stats['total_services'] += len(instances)
            stats['healthy_services'] += healthy_count
            stats['unhealthy_services'] += unhealthy_count
            stats['services_by_type'][service_type.value] = {
                'total': len(instances),
                'healthy': healthy_count,
                'unhealthy': unhealthy_count
            }
        
        return stats

# Global microservice service instance
microservice_service = MicroserviceService()

# Service client decorators
def service_client(service_type: ServiceType):
    """Decorator to create service client methods"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            return microservice_service.call_service(service_type, *args, **kwargs)
        return wrapper
    return decorator

# Example service clients
class TransactionServiceClient:
    """Client for transaction service"""
    
    @staticmethod
    @service_client(ServiceType.TRANSACTION_SERVICE)
    def create_transaction(endpoint: str = '/transactions', method: str = 'POST', data: Dict[str, Any] = None):
        pass
    
    @staticmethod
    @service_client(ServiceType.TRANSACTION_SERVICE)
    def get_transactions(endpoint: str = '/transactions', method: str = 'GET'):
        pass

class AnalyticsServiceClient:
    """Client for analytics service"""
    
    @staticmethod
    @service_client(ServiceType.ANALYTICS_SERVICE)
    def get_dashboard_stats(endpoint: str = '/analytics/dashboard', method: str = 'GET'):
        pass
    
    @staticmethod
    @service_client(ServiceType.ANALYTICS_SERVICE)
    def get_psp_summary(endpoint: str = '/analytics/psp-summary', method: str = 'GET'):
        pass
