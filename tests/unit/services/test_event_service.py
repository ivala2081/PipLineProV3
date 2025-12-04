"""
Unit tests for event service
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from app.services.event_service import EventService, Event, EventType


@pytest.mark.unit
class TestEvent:
    """Test Event dataclass"""
    
    def test_event_creation(self):
        """Test event creation"""
        event = Event(
            id="test-id",
            type=EventType.TRANSACTION_CREATED,
            timestamp=datetime.now(timezone.utc),
            source="test_source",
            data={"key": "value"}
        )
        
        assert event.id == "test-id"
        assert event.type == EventType.TRANSACTION_CREATED
        assert event.source == "test_source"
        assert event.data == {"key": "value"}
    
    def test_event_to_dict(self):
        """Test event to_dict conversion"""
        timestamp = datetime.now(timezone.utc)
        event = Event(
            id="test-id",
            type=EventType.TRANSACTION_CREATED,
            timestamp=timestamp,
            source="test_source",
            data={"key": "value"}
        )
        
        event_dict = event.to_dict()
        
        assert event_dict['id'] == "test-id"
        assert event_dict['type'] == EventType.TRANSACTION_CREATED.value
        assert event_dict['source'] == "test_source"
        assert event_dict['data'] == {"key": "value"}
        assert 'timestamp' in event_dict
    
    def test_event_from_dict(self):
        """Test event from_dict creation"""
        timestamp = datetime.now(timezone.utc)
        event_dict = {
            'id': 'test-id',
            'type': EventType.TRANSACTION_CREATED.value,
            'timestamp': timestamp.isoformat(),
            'source': 'test_source',
            'data': {'key': 'value'},
            'metadata': {}
        }
        
        event = Event.from_dict(event_dict)
        
        assert event.id == 'test-id'
        assert event.type == EventType.TRANSACTION_CREATED
        assert event.source == 'test_source'
        assert event.data == {'key': 'value'}


@pytest.mark.unit
class TestEventService:
    """Test EventService"""
    
    def test_event_service_initialization(self):
        """Test event service initialization"""
        service = EventService()
        
        assert service is not None
        assert service.stream_name == "pipeline_events"
        assert service.consumer_group == "pipeline_consumers"
        assert len(service.event_handlers) == 0
    
    def test_event_service_initialization_with_redis(self):
        """Test event service initialization with Redis client"""
        mock_redis = Mock()
        service = EventService(redis_client=mock_redis)
        
        assert service._redis_client == mock_redis
        assert service._redis_initialized is True
    
    @patch('app.services.event_service.current_app')
    def test_get_redis_client_disabled(self, mock_app):
        """Test getting Redis client when Redis is disabled"""
        mock_app.config = {
            'REDIS_ENABLED': False
        }
        
        service = EventService()
        client = service._get_redis_client()
        
        assert client is None
    
    @patch('app.services.event_service.current_app')
    @patch('app.services.event_service.redis')
    def test_get_redis_client_enabled(self, mock_redis_module, mock_app):
        """Test getting Redis client when Redis is enabled"""
        mock_app.config = {
            'REDIS_ENABLED': True,
            'REDIS_URL': 'redis://localhost:6379/0'
        }
        
        mock_redis_client = Mock()
        mock_redis_module.from_url.return_value = mock_redis_client
        
        service = EventService()
        client = service._get_redis_client()
        
        assert client == mock_redis_client
        mock_redis_module.from_url.assert_called_once()
    
    def test_publish_event_no_redis(self):
        """Test publishing event without Redis"""
        service = EventService()
        service._redis_client = None
        
        event = Event(
            id="test-id",
            type=EventType.TRANSACTION_CREATED,
            timestamp=datetime.now(timezone.utc),
            source="test_source",
            data={"key": "value"}
        )
        
        # Should not raise error
        result = service.publish_event(event)
        assert result is False
    
    def test_publish_event_with_redis(self):
        """Test publishing event with Redis"""
        mock_redis = Mock()
        mock_redis.xadd.return_value = "stream-id"
        
        service = EventService(redis_client=mock_redis)
        
        event = Event(
            id="test-id",
            type=EventType.TRANSACTION_CREATED,
            timestamp=datetime.now(timezone.utc),
            source="test_source",
            data={"key": "value"}
        )
        
        result = service.publish_event(event)
        
        assert result is True
        mock_redis.xadd.assert_called_once()
    
    def test_subscribe_to_event(self):
        """Test subscribing to event type"""
        service = EventService()
        
        def handler(event):
            pass
        
        service.subscribe(EventType.TRANSACTION_CREATED, handler)
        
        assert EventType.TRANSACTION_CREATED in service.event_handlers
        assert handler in service.event_handlers[EventType.TRANSACTION_CREATED]
    
    def test_unsubscribe_from_event(self):
        """Test unsubscribing from event type"""
        service = EventService()
        
        def handler(event):
            pass
        
        service.subscribe(EventType.TRANSACTION_CREATED, handler)
        service.unsubscribe(EventType.TRANSACTION_CREATED, handler)
        
        assert EventType.TRANSACTION_CREATED not in service.event_handlers or \
               handler not in service.event_handlers[EventType.TRANSACTION_CREATED]
    
    def test_emit_event(self):
        """Test emitting event to handlers"""
        service = EventService()
        
        handler_called = []
        
        def handler(event):
            handler_called.append(event)
        
        service.subscribe(EventType.TRANSACTION_CREATED, handler)
        
        event = Event(
            id="test-id",
            type=EventType.TRANSACTION_CREATED,
            timestamp=datetime.now(timezone.utc),
            source="test_source",
            data={"key": "value"}
        )
        
        service.emit(event)
        
        assert len(handler_called) == 1
        assert handler_called[0] == event

