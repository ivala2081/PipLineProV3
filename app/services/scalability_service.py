"""
Scalability and Load Balancing Service
Provides horizontal scaling capabilities and load balancing
"""

import threading
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

@dataclass
class ServerInstance:
    """Server instance information"""
    id: str
    host: str
    port: int
    status: str  # 'active', 'inactive', 'maintenance'
    load: float  # 0-100
    response_time: float
    last_health_check: datetime
    capabilities: List[str]
    metadata: Dict[str, Any]

@dataclass
class LoadBalancerConfig:
    """Load balancer configuration"""
    algorithm: str  # 'round_robin', 'least_connections', 'weighted', 'ip_hash'
    health_check_interval: int
    health_check_timeout: int
    max_retries: int
    sticky_sessions: bool
    session_timeout: int

class LoadBalancer:
    """Simple load balancer implementation"""
    
    def __init__(self, config: LoadBalancerConfig):
        self.config = config
        self.servers: List[ServerInstance] = []
        self.current_index = 0
        self.server_stats = {}
        self.lock = threading.Lock()
        
    def add_server(self, server: ServerInstance):
        """Add a server to the load balancer"""
        with self.lock:
            self.servers.append(server)
            self.server_stats[server.id] = {
                'requests': 0,
                'active_connections': 0,
                'response_times': [],
                'errors': 0
            }
        logger.info(f"Added server {server.id} to load balancer")
    
    def remove_server(self, server_id: str):
        """Remove a server from the load balancer"""
        with self.lock:
            self.servers = [s for s in self.servers if s.id != server_id]
            if server_id in self.server_stats:
                del self.server_stats[server_id]
        logger.info(f"Removed server {server_id} from load balancer")
    
    def get_next_server(self, client_ip: str = None) -> Optional[ServerInstance]:
        """Get the next server based on the configured algorithm"""
        with self.lock:
            active_servers = [s for s in self.servers if s.status == 'active']
            
            if not active_servers:
                return None
            
            if self.config.algorithm == 'round_robin':
                return self._round_robin(active_servers)
            elif self.config.algorithm == 'least_connections':
                return self._least_connections(active_servers)
            elif self.config.algorithm == 'weighted':
                return self._weighted(active_servers)
            elif self.config.algorithm == 'ip_hash':
                return self._ip_hash(active_servers, client_ip)
            else:
                return self._round_robin(active_servers)
    
    def _round_robin(self, servers: List[ServerInstance]) -> ServerInstance:
        """Round robin selection"""
        server = servers[self.current_index % len(servers)]
        self.current_index += 1
        return server
    
    def _least_connections(self, servers: List[ServerInstance]) -> ServerInstance:
        """Least connections selection"""
        return min(servers, key=lambda s: self.server_stats.get(s.id, {}).get('active_connections', 0))
    
    def _weighted(self, servers: List[ServerInstance]) -> ServerInstance:
        """Weighted selection based on server load"""
        # Simple implementation - select server with lowest load
        return min(servers, key=lambda s: s.load)
    
    def _ip_hash(self, servers: List[ServerInstance], client_ip: str) -> ServerInstance:
        """IP hash selection for sticky sessions"""
        if not client_ip:
            return self._round_robin(servers)
        
        hash_value = hash(client_ip) % len(servers)
        return servers[hash_value]
    
    def update_server_stats(self, server_id: str, response_time: float, success: bool = True):
        """Update server statistics"""
        with self.lock:
            if server_id not in self.server_stats:
                return
            
            stats = self.server_stats[server_id]
            stats['requests'] += 1
            stats['response_times'].append(response_time)
            
            # Keep only last 100 response times
            if len(stats['response_times']) > 100:
                stats['response_times'] = stats['response_times'][-100:]
            
            if not success:
                stats['errors'] += 1
    
    def get_server_stats(self) -> Dict[str, Any]:
        """Get load balancer statistics"""
        with self.lock:
            return {
                'total_servers': len(self.servers),
                'active_servers': len([s for s in self.servers if s.status == 'active']),
                'algorithm': self.config.algorithm,
                'server_stats': dict(self.server_stats)
            }

class AutoScaler:
    """Automatic scaling service"""
    
    def __init__(self, load_balancer: LoadBalancer):
        self.load_balancer = load_balancer
        self.scaling_config = {
            'scale_up_threshold': 80.0,  # CPU/Memory threshold to scale up
            'scale_down_threshold': 20.0,  # CPU/Memory threshold to scale down
            'scale_up_cooldown': 300,  # 5 minutes
            'scale_down_cooldown': 600,  # 10 minutes
            'min_instances': 1,
            'max_instances': 10
        }
        self.last_scale_up = 0
        self.last_scale_down = 0
        self.scaling_active = False
        self.scaling_thread = None
    
    def start_auto_scaling(self, interval: int = 60):
        """Start automatic scaling"""
        if self.scaling_active:
            return
        
        self.scaling_active = True
        self.scaling_thread = threading.Thread(
            target=self._scaling_loop,
            args=(interval,),
            daemon=True
        )
        self.scaling_thread.start()
        logger.info("Auto-scaling started")
    
    def stop_auto_scaling(self):
        """Stop automatic scaling"""
        self.scaling_active = False
        if self.scaling_thread:
            self.scaling_thread.join(timeout=5)
        logger.info("Auto-scaling stopped")
    
    def _scaling_loop(self, interval: int):
        """Main scaling loop"""
        while self.scaling_active:
            try:
                self._check_scaling_conditions()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error in scaling loop: {e}")
                time.sleep(interval)
    
    def _check_scaling_conditions(self):
        """Check if scaling is needed"""
        current_time = time.time()
        active_servers = [s for s in self.load_balancer.servers if s.status == 'active']
        
        if not active_servers:
            return
        
        # Calculate average load
        avg_load = sum(s.load for s in active_servers) / len(active_servers)
        
        # Check scale up conditions
        if (avg_load >= self.scaling_config['scale_up_threshold'] and
            len(active_servers) < self.scaling_config['max_instances'] and
            current_time - self.last_scale_up > self.scaling_config['scale_up_cooldown']):
            
            self._scale_up()
            self.last_scale_up = current_time
        
        # Check scale down conditions
        elif (avg_load <= self.scaling_config['scale_down_threshold'] and
              len(active_servers) > self.scaling_config['min_instances'] and
              current_time - self.last_scale_down > self.scaling_config['scale_down_cooldown']):
            
            self._scale_down()
            self.last_scale_down = current_time
    
    def _scale_up(self):
        """Scale up by adding a new server instance"""
        # In a real implementation, this would:
        # 1. Provision a new server instance
        # 2. Deploy the application
        # 3. Add it to the load balancer
        
        logger.info("Scaling up - would provision new server instance")
        # For now, just log the action
    
    def _scale_down(self):
        """Scale down by removing a server instance"""
        # In a real implementation, this would:
        # 1. Drain connections from a server
        # 2. Remove it from the load balancer
        # 3. Terminate the instance
        
        logger.info("Scaling down - would remove server instance")
        # For now, just log the action

class ScalabilityService:
    """Main scalability service"""
    
    def __init__(self):
        # Default load balancer configuration
        lb_config = LoadBalancerConfig(
            algorithm='round_robin',
            health_check_interval=30,
            health_check_timeout=5,
            max_retries=3,
            sticky_sessions=False,
            session_timeout=3600
        )
        
        self.load_balancer = LoadBalancer(lb_config)
        self.auto_scaler = AutoScaler(self.load_balancer)
        
        # Add default local server
        self._add_local_server()
    
    def _add_local_server(self):
        """Add the local server instance"""
        local_server = ServerInstance(
            id='local-1',
            host='127.0.0.1',
            port=5000,
            status='active',
            load=0.0,
            response_time=0.0,
            last_health_check=datetime.now(),
            capabilities=['web', 'api', 'database'],
            metadata={'environment': 'development'}
        )
        self.load_balancer.add_server(local_server)
    
    def start_services(self):
        """Start all scalability services"""
        self.auto_scaler.start_auto_scaling()
        logger.info("Scalability services started")
    
    def stop_services(self):
        """Stop all scalability services"""
        self.auto_scaler.stop_auto_scaling()
        logger.info("Scalability services stopped")
    
    def add_server_instance(self, server_data: Dict[str, Any]) -> bool:
        """Add a new server instance"""
        try:
            server = ServerInstance(
                id=server_data['id'],
                host=server_data['host'],
                port=server_data['port'],
                status=server_data.get('status', 'active'),
                load=server_data.get('load', 0.0),
                response_time=server_data.get('response_time', 0.0),
                last_health_check=datetime.now(),
                capabilities=server_data.get('capabilities', []),
                metadata=server_data.get('metadata', {})
            )
            
            self.load_balancer.add_server(server)
            return True
        except Exception as e:
            logger.error(f"Error adding server instance: {e}")
            return False
    
    def remove_server_instance(self, server_id: str) -> bool:
        """Remove a server instance"""
        try:
            self.load_balancer.remove_server(server_id)
            return True
        except Exception as e:
            logger.error(f"Error removing server instance: {e}")
            return False
    
    def get_load_balancer_stats(self) -> Dict[str, Any]:
        """Get load balancer statistics"""
        return self.load_balancer.get_server_stats()
    
    def update_scaling_config(self, config: Dict[str, Any]) -> bool:
        """Update auto-scaling configuration"""
        try:
            for key, value in config.items():
                if key in self.auto_scaler.scaling_config:
                    self.auto_scaler.scaling_config[key] = value
            return True
        except Exception as e:
            logger.error(f"Error updating scaling config: {e}")
            return False
    
    def get_scaling_config(self) -> Dict[str, Any]:
        """Get current auto-scaling configuration"""
        return dict(self.auto_scaler.scaling_config)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system scalability status"""
        return {
            'load_balancer': self.get_load_balancer_stats(),
            'auto_scaler': {
                'active': self.auto_scaler.scaling_active,
                'config': self.get_scaling_config(),
                'last_scale_up': self.auto_scaler.last_scale_up,
                'last_scale_down': self.auto_scaler.last_scale_down
            },
            'timestamp': datetime.now().isoformat()
        }

# Global scalability service instance
scalability_service = ScalabilityService()

def get_scalability_service() -> ScalabilityService:
    """Get the global scalability service instance"""
    return scalability_service
