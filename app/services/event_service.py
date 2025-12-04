"""
Event Service for PipLinePro
Handles event-driven architecture with Redis Streams and message queues
"""
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import redis
from flask import current_app

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Event types for the system"""
    TRANSACTION_CREATED = "transaction.created"
    TRANSACTION_UPDATED = "transaction.updated"
    TRANSACTION_DELETED = "transaction.deleted"
    PSP_TRACK_UPDATED = "psp_track.updated"
    DAILY_BALANCE_UPDATED = "daily_balance.updated"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    CACHE_INVALIDATED = "cache.invalidated"
    SYSTEM_ALERT = "system.alert"
    EXCHANGE_RATE_UPDATED = "exchange_rate.updated"

@dataclass
class Event:
    """Event data structure"""
    id: str
    type: EventType
    timestamp: datetime
    source: str
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            'id': self.id,
            'type': self.type.value,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'data': self.data,
            'metadata': self.metadata or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary"""
        return cls(
            id=data['id'],
            type=EventType(data['type']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            source=data['source'],
            data=data['data'],
            metadata=data.get('metadata', {})
        )

class EventService:
    """Service for managing events and event-driven architecture"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self._redis_client = redis_client
        self._redis_initialized = False
        self.event_handlers: Dict[EventType, List[Callable]] = {}
        self.stream_name = "pipeline_events"
        self.consumer_group = "pipeline_consumers"
        self.consumer_name = f"consumer_{uuid.uuid4().hex[:8]}"
    
    @property
    def redis_client(self) -> Optional[redis.Redis]:
        """Lazy initialization of Redis client"""
        if not self._redis_initialized:
            self._redis_client = self._get_redis_client()
            self._redis_initialized = True
            # Initialize consumer group on first access
            self._init_consumer_group()
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
    
    def _init_consumer_group(self):
        """Initialize Redis Stream consumer group"""
        if not self.redis_client:
            return
            
        try:
            self.redis_client.xgroup_create(
                self.stream_name, 
                self.consumer_group, 
                id='0', 
                mkstream=True
            )
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                logger.error(f"Failed to create consumer group: {e}")
    
    def publish_event(self, event_type: EventType, data: Dict[str, Any], 
                     source: str = "pipeline", metadata: Optional[Dict[str, Any]] = None) -> str:
        """Publish an event to the stream"""
        event = Event(
            id=str(uuid.uuid4()),
            type=event_type,
            timestamp=datetime.now(timezone.utc),
            source=source,
            data=data,
            metadata=metadata
        )
        
        if not self.redis_client:
            logger.warning("Redis not available, event not published")
            return event.id
        
        try:
            # Add event to Redis Stream
            event_id = self.redis_client.xadd(
                self.stream_name,
                event.to_dict(),
                maxlen=10000  # Keep last 10k events
            )
            
            logger.info(f"Published event {event_type.value} with ID {event_id}")
            
            # Also trigger local handlers immediately for real-time processing
            self._trigger_handlers(event)
            
            return event_id
            
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            return event.id
    
    def subscribe_to_events(self, event_types: List[EventType], 
                          handler: Callable[[Event], None]):
        """Subscribe to specific event types"""
        for event_type in event_types:
            if event_type not in self.event_handlers:
                self.event_handlers[event_type] = []
            self.event_handlers[event_type].append(handler)
            logger.info(f"Subscribed handler to {event_type.value}")
    
    def _trigger_handlers(self, event: Event):
        """Trigger handlers for an event"""
        handlers = self.event_handlers.get(event.type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler for {event.type.value}: {e}")
    
    def consume_events(self, count: int = 10, block: int = 1000) -> List[Event]:
        """Consume events from the stream"""
        if not self.redis_client:
            return []
        
        try:
            messages = self.redis_client.xreadgroup(
                self.consumer_group,
                self.consumer_name,
                {self.stream_name: '>'},
                count=count,
                block=block
            )
            
            events = []
            for stream, msgs in messages:
                for msg_id, fields in msgs:
                    try:
                        event = Event.from_dict(fields)
                        events.append(event)
                        
                        # Acknowledge message
                        self.redis_client.xack(self.stream_name, self.consumer_group, msg_id)
                        
                    except Exception as e:
                        logger.error(f"Error processing message {msg_id}: {e}")
            
            return events
            
        except Exception as e:
            logger.error(f"Error consuming events: {e}")
            return []
    
    def get_event_history(self, count: int = 100) -> List[Event]:
        """Get recent event history"""
        if not self.redis_client:
            return []
        
        try:
            messages = self.redis_client.xrevrange(
                self.stream_name,
                count=count
            )
            
            events = []
            for msg_id, fields in messages:
                try:
                    event = Event.from_dict(fields)
                    events.append(event)
                except Exception as e:
                    logger.error(f"Error parsing event {msg_id}: {e}")
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting event history: {e}")
            return []
    
    def get_stream_info(self) -> Dict[str, Any]:
        """Get stream information"""
        if not self.redis_client:
            return {}
        
        try:
            info = self.redis_client.xinfo_stream(self.stream_name)
            return {
                'length': info.get('length', 0),
                'first_entry': info.get('first-entry'),
                'last_entry': info.get('last-entry'),
                'groups': info.get('groups', 0)
            }
        except Exception as e:
            logger.error(f"Error getting stream info: {e}")
            return {}

# Global event service instance
event_service = EventService()

# Event handlers for real-time processing
def handle_transaction_created(event: Event):
    """Handle transaction created events"""
    # Removed verbose event logging - only log errors
    # Trigger real-time updates, notifications, etc.

def handle_psp_track_updated(event: Event):
    """Handle PSP track updated events"""
    # Removed verbose event logging - only log errors
    # Update real-time dashboards, send notifications

def handle_cache_invalidated(event: Event):
    """Handle cache invalidation events"""
    # Removed verbose cache invalidation logging
    # Could trigger cache warming or other optimizations

# Register default handlers
event_service.subscribe_to_events([EventType.TRANSACTION_CREATED], handle_transaction_created)
event_service.subscribe_to_events([EventType.PSP_TRACK_UPDATED], handle_psp_track_updated)
event_service.subscribe_to_events([EventType.CACHE_INVALIDATED], handle_cache_invalidated)
