"""
Webhooks Management API endpoints for PipLinePro v2
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import logging

logger = logging.getLogger(__name__)

webhooks_api = Blueprint('webhooks_api', __name__)

# Temporarily disable CSRF protection for webhooks API
from app import csrf
csrf.exempt(webhooks_api)

@webhooks_api.route('/', methods=['GET'])
@login_required
def get_webhooks():
    """Get all webhooks for the current user"""
    try:
        # This would typically come from a webhooks service
        webhooks = [
            {
                'id': '1',
                'name': 'Transaction Created',
                'url': 'https://example.com/webhook/transaction-created',
                'events': ['transaction.created'],
                'active': True,
                'created_at': '2024-01-15T10:30:00Z'
            },
            {
                'id': '2',
                'name': 'PSP Update',
                'url': 'https://example.com/webhook/psp-update',
                'events': ['psp_track.updated'],
                'active': False,
                'created_at': '2024-01-14T15:20:00Z'
            }
        ]
        
        return jsonify({
            'status': 'success',
            'webhooks': webhooks
        })
    except Exception as e:
        logger.error(f"Error getting webhooks: {e}")
        return jsonify({'error': 'Failed to get webhooks'}), 500

@webhooks_api.route('/', methods=['POST'])
@login_required
def create_webhook():
    """Create a new webhook"""
    try:
        data = request.get_json()
        
        name = data.get('name')
        url = data.get('url')
        events = data.get('events', [])
        
        if not all([name, url]):
            return jsonify({'error': 'name and url are required'}), 400
        
        # This would create the webhook in the database
        webhook_id = '3'  # Mock ID
        
        return jsonify({
            'status': 'success',
            'webhook_id': webhook_id,
            'message': 'Webhook created successfully'
        }), 201
    except Exception as e:
        logger.error(f"Error creating webhook: {e}")
        return jsonify({'error': 'Failed to create webhook'}), 500

@webhooks_api.route('/<webhook_id>', methods=['GET'])
@login_required
def get_webhook(webhook_id):
    """Get a specific webhook"""
    try:
        # This would get the webhook from the database
        webhook = {
            'id': webhook_id,
            'name': 'Transaction Created',
            'url': 'https://example.com/webhook/transaction-created',
            'events': ['transaction.created'],
            'active': True,
            'created_at': '2024-01-15T10:30:00Z',
            'last_triggered': '2024-01-15T14:25:00Z',
            'success_count': 45,
            'failure_count': 2
        }
        
        return jsonify({
            'status': 'success',
            'webhook': webhook
        })
    except Exception as e:
        logger.error(f"Error getting webhook: {e}")
        return jsonify({'error': 'Failed to get webhook'}), 500

@webhooks_api.route('/<webhook_id>', methods=['PUT'])
@login_required
def update_webhook(webhook_id):
    """Update a webhook"""
    try:
        data = request.get_json()
        
        # This would update the webhook in the database
        return jsonify({
            'status': 'success',
            'message': 'Webhook updated successfully'
        })
    except Exception as e:
        logger.error(f"Error updating webhook: {e}")
        return jsonify({'error': 'Failed to update webhook'}), 500

@webhooks_api.route('/<webhook_id>', methods=['DELETE'])
@login_required
def delete_webhook(webhook_id):
    """Delete a webhook"""
    try:
        # This would delete the webhook from the database
        return jsonify({
            'status': 'success',
            'message': 'Webhook deleted successfully'
        })
    except Exception as e:
        logger.error(f"Error deleting webhook: {e}")
        return jsonify({'error': 'Failed to delete webhook'}), 500

@webhooks_api.route('/<webhook_id>/test', methods=['POST'])
@login_required
def test_webhook(webhook_id):
    """Test a webhook"""
    try:
        # This would send a test payload to the webhook
        return jsonify({
            'status': 'success',
            'message': 'Test webhook sent successfully'
        })
    except Exception as e:
        logger.error(f"Error testing webhook: {e}")
        return jsonify({'error': 'Failed to test webhook'}), 500

@webhooks_api.route('/events', methods=['GET'])
@login_required
def get_webhook_events():
    """Get available webhook events"""
    try:
        events = [
            {
                'name': 'transaction.created',
                'description': 'Triggered when a new transaction is created'
            },
            {
                'name': 'transaction.updated',
                'description': 'Triggered when a transaction is updated'
            },
            {
                'name': 'transaction.deleted',
                'description': 'Triggered when a transaction is deleted'
            },
            {
                'name': 'psp_track.updated',
                'description': 'Triggered when PSP track data is updated'
            },
            {
                'name': 'daily_balance.updated',
                'description': 'Triggered when daily balance is updated'
            },
            {
                'name': 'system.alert',
                'description': 'Triggered when a system alert occurs'
            }
        ]
        
        return jsonify({
            'status': 'success',
            'events': events
        })
    except Exception as e:
        logger.error(f"Error getting webhook events: {e}")
        return jsonify({'error': 'Failed to get webhook events'}), 500
