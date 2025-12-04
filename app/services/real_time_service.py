"""
Real-Time Service for PipLinePro
Handles WebSocket connections and real-time data streaming
"""
import json
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set
from flask import current_app
from flask_socketio import SocketIO, emit, join_room, leave_room
from app.services.event_service import EventService, Event, EventType

logger = logging.getLogger(__name__)

class RealTimeService:
    """Service for managing real-time connections and data streaming"""
    
    def __init__(self, socketio: SocketIO, event_service: EventService):
        self.socketio = socketio
        self.event_service = event_service
        self.connected_users: Set[str] = set()
        self.user_rooms: Dict[str, Set[str]] = {}
        
        # Register event handlers
        self._register_event_handlers()
        self._register_socket_handlers()
    
    def _register_event_handlers(self):
        """Register handlers for system events"""
        self.event_service.subscribe_to_events([
            EventType.TRANSACTION_CREATED,
            EventType.TRANSACTION_UPDATED,
            EventType.TRANSACTION_DELETED
        ], self._handle_transaction_events)
        
        self.event_service.subscribe_to_events([
            EventType.PSP_TRACK_UPDATED,
            EventType.DAILY_BALANCE_UPDATED
        ], self._handle_financial_events)
        
        self.event_service.subscribe_to_events([
            EventType.SYSTEM_ALERT
        ], self._handle_system_events)
    
    def _register_socket_handlers(self):
        """Register WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            user_id = self._get_user_id_from_session()
            if user_id:
                self.connected_users.add(user_id)
                join_room(f"user_{user_id}")
                join_room("global")
                
                logger.info(f"User {user_id} connected to real-time service")
                emit('connected', {'status': 'success', 'user_id': user_id})
            else:
                emit('error', {'message': 'Authentication required'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            user_id = self._get_user_id_from_session()
            if user_id:
                self.connected_users.discard(user_id)
                leave_room(f"user_{user_id}")
                leave_room("global")
                
                logger.info(f"User {user_id} disconnected from real-time service")
        
        @self.socketio.on('join_room')
        def handle_join_room(data):
            """Handle joining a specific room"""
            user_id = self._get_user_id_from_session()
            room = data.get('room')
            
            if user_id and room:
                join_room(room)
                if user_id not in self.user_rooms:
                    self.user_rooms[user_id] = set()
                self.user_rooms[user_id].add(room)
                
                emit('joined_room', {'room': room})
                logger.info(f"User {user_id} joined room {room}")
        
        @self.socketio.on('leave_room')
        def handle_leave_room(data):
            """Handle leaving a specific room"""
            user_id = self._get_user_id_from_session()
            room = data.get('room')
            
            if user_id and room:
                leave_room(room)
                if user_id in self.user_rooms:
                    self.user_rooms[user_id].discard(room)
                
                emit('left_room', {'room': room})
                logger.info(f"User {user_id} left room {room}")
        
        @self.socketio.on('subscribe_transactions')
        def handle_subscribe_transactions():
            """Handle subscription to transaction updates"""
            user_id = self._get_user_id_from_session()
            if user_id:
                join_room(f"transactions_{user_id}")
                emit('subscribed', {'type': 'transactions'})
        
        @self.socketio.on('subscribe_analytics')
        def handle_subscribe_analytics():
            """Handle subscription to analytics updates"""
            user_id = self._get_user_id_from_session()
            if user_id:
                join_room(f"analytics_{user_id}")
                emit('subscribed', {'type': 'analytics'})
        
        @self.socketio.on('subscribe_psp_track')
        def handle_subscribe_psp_track():
            """Handle subscription to PSP track updates"""
            user_id = self._get_user_id_from_session()
            if user_id:
                join_room(f"psp_track_{user_id}")
                emit('subscribed', {'type': 'psp_track'})
    
    def _get_user_id_from_session(self) -> Optional[str]:
        """Get user ID from current session"""
        try:
            from flask_login import current_user
            if current_user.is_authenticated:
                return str(current_user.id)
        except Exception as e:
            logger.error(f"Error getting user ID from session: {e}")
        return None
    
    def _handle_transaction_events(self, event: Event):
        """Handle transaction-related events"""
        try:
            # Broadcast to all users subscribed to transactions
            self.socketio.emit('transaction_update', {
                'type': event.type.value,
                'data': event.data,
                'timestamp': event.timestamp.isoformat()
            }, room='global')
            
            # Send to specific user if transaction belongs to them
            user_id = event.data.get('user_id')
            if user_id:
                self.socketio.emit('transaction_update', {
                    'type': event.type.value,
                    'data': event.data,
                    'timestamp': event.timestamp.isoformat()
                }, room=f"transactions_{user_id}")
                
        except Exception as e:
            logger.error(f"Error handling transaction event: {e}")
    
    def _handle_financial_events(self, event: Event):
        """Handle financial-related events"""
        try:
            # Broadcast to all users subscribed to analytics
            self.socketio.emit('financial_update', {
                'type': event.type.value,
                'data': event.data,
                'timestamp': event.timestamp.isoformat()
            }, room='global')
            
            # Send to PSP track subscribers
            if event.type == EventType.PSP_TRACK_UPDATED:
                psp_name = event.data.get('psp_name')
                if psp_name:
                    self.socketio.emit('psp_track_update', {
                        'type': event.type.value,
                        'data': event.data,
                        'timestamp': event.timestamp.isoformat()
                    }, room=f"psp_{psp_name}")
                
        except Exception as e:
            logger.error(f"Error handling financial event: {e}")
    
    def _handle_system_events(self, event: Event):
        """Handle system events"""
        try:
            # Broadcast system alerts to all connected users
            self.socketio.emit('system_alert', {
                'type': event.type.value,
                'data': event.data,
                'timestamp': event.timestamp.isoformat()
            }, room='global')
                
        except Exception as e:
            logger.error(f"Error handling system event: {e}")
    
    def send_notification(self, user_id: str, notification: Dict[str, Any]):
        """Send a notification to a specific user"""
        try:
            self.socketio.emit('notification', {
                'data': notification,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }, room=f"user_{user_id}")
            
        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {e}")
    
    def broadcast_analytics_update(self, analytics_data: Dict[str, Any]):
        """Broadcast analytics update to all subscribers"""
        try:
            self.socketio.emit('analytics_update', {
                'data': analytics_data,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }, room='global')
            
        except Exception as e:
            logger.error(f"Error broadcasting analytics update: {e}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get real-time connection statistics"""
        return {
            'connected_users': len(self.connected_users),
            'total_rooms': len(set().union(*self.user_rooms.values())) if self.user_rooms else 0,
            'user_rooms': {user_id: list(rooms) for user_id, rooms in self.user_rooms.items()}
        }

# Global real-time service instance (will be initialized in app factory)
real_time_service = None

def init_real_time_service(socketio: SocketIO, event_service: EventService):
    """Initialize the global real-time service"""
    global real_time_service
    real_time_service = RealTimeService(socketio, event_service)
    return real_time_service
