"""
Real-Time API endpoints for PipLinePro v2
WebSocket connections and real-time data streaming
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from flask_socketio import emit, join_room, leave_room
from app.services.real_time_service import real_time_service
from app.services.event_service import event_service, EventType
import logging

logger = logging.getLogger(__name__)

real_time_api = Blueprint('real_time_api', __name__)

# Temporarily disable CSRF protection for real-time API
from app import csrf
csrf.exempt(real_time_api)

@real_time_api.route('/connect', methods=['GET'])
@login_required
def connect_info():
    """Get WebSocket connection information"""
    try:
        return jsonify({
            'status': 'success',
            'websocket_url': f'ws://{request.host}/socket.io/',
            'user_id': current_user.id,
            'rooms': [
                f'user_{current_user.id}',
                'global',
                f'transactions_{current_user.id}',
                f'analytics_{current_user.id}',
                f'psp_track_{current_user.id}'
            ],
            'events': [
                'transaction_update',
                'financial_update',
                'psp_track_update',
                'system_alert',
                'notification',
                'analytics_update'
            ]
        })
    except Exception as e:
        logger.error(f"Error getting connection info: {e}")
        return jsonify({'error': 'Failed to get connection info'}), 500

@real_time_api.route('/events', methods=['GET'])
@login_required
def get_recent_events():
    """Get recent events from the event stream"""
    try:
        count = request.args.get('count', 50, type=int)
        events = event_service.get_event_history(count)
        
        return jsonify({
            'status': 'success',
            'events': [event.to_dict() for event in events],
            'count': len(events)
        })
    except Exception as e:
        logger.error(f"Error getting recent events: {e}")
        return jsonify({'error': 'Failed to get events'}), 500

@real_time_api.route('/subscribe', methods=['POST'])
@login_required
def subscribe_to_events():
    """Subscribe to specific event types"""
    try:
        data = request.get_json()
        event_types = data.get('event_types', [])
        
        if not event_types:
            return jsonify({'error': 'No event types specified'}), 400
        
        # Validate event types
        valid_types = [et.value for et in EventType]
        invalid_types = [et for et in event_types if et not in valid_types]
        
        if invalid_types:
            return jsonify({
                'error': f'Invalid event types: {invalid_types}',
                'valid_types': valid_types
            }), 400
        
        # Subscribe to events (this would be handled by WebSocket connection)
        return jsonify({
            'status': 'success',
            'subscribed_to': event_types,
            'message': 'Subscription will be active for WebSocket connection'
        })
    except Exception as e:
        logger.error(f"Error subscribing to events: {e}")
        return jsonify({'error': 'Failed to subscribe to events'}), 500

@real_time_api.route('/notifications', methods=['GET'])
@login_required
def get_notifications():
    """Get user notifications"""
    try:
        # This would typically come from a notifications service
        notifications = [
            {
                'id': '1',
                'type': 'info',
                'title': 'System Update',
                'message': 'System will be updated tonight at 2 AM',
                'timestamp': '2024-01-15T10:30:00Z',
                'read': False
            },
            {
                'id': '2',
                'type': 'warning',
                'title': 'High Transaction Volume',
                'message': 'Transaction volume is 150% above normal',
                'timestamp': '2024-01-15T09:15:00Z',
                'read': True
            }
        ]
        
        return jsonify({
            'status': 'success',
            'notifications': notifications,
            'unread_count': sum(1 for n in notifications if not n['read'])
        })
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return jsonify({'error': 'Failed to get notifications'}), 500

@real_time_api.route('/notifications/<notification_id>/read', methods=['PUT'])
@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    try:
        # This would update the notification in the database
        return jsonify({
            'status': 'success',
            'message': f'Notification {notification_id} marked as read'
        })
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        return jsonify({'error': 'Failed to mark notification as read'}), 500

@real_time_api.route('/stats', methods=['GET'])
@login_required
def get_connection_stats():
    """Get real-time connection statistics"""
    try:
        if real_time_service:
            stats = real_time_service.get_connection_stats()
            return jsonify({
                'status': 'success',
                'stats': stats
            })
        else:
            return jsonify({
                'status': 'success',
                'stats': {
                    'connected_users': 0,
                    'total_rooms': 0,
                    'user_rooms': {}
                }
            })
    except Exception as e:
        logger.error(f"Error getting connection stats: {e}")
        return jsonify({'error': 'Failed to get connection stats'}), 500

@real_time_api.route('/test-event', methods=['POST'])
@login_required
def test_event():
    """Test event publishing (for development)"""
    try:
        data = request.get_json()
        event_type = data.get('event_type', 'system.alert')
        event_data = data.get('data', {'message': 'Test event'})
        
        # Publish test event
        event_id = event_service.publish_event(
            EventType.SYSTEM_ALERT,
            event_data,
            source='api_test'
        )
        
        return jsonify({
            'status': 'success',
            'event_id': event_id,
            'message': 'Test event published successfully'
        })
    except Exception as e:
        logger.error(f"Error publishing test event: {e}")
        return jsonify({'error': 'Failed to publish test event'}), 500
