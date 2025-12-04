"""
Microservices Management API endpoints for PipLinePro v2
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.services.microservice_service import microservice_service, ServiceType
import logging

logger = logging.getLogger(__name__)

services_api = Blueprint('services_api', __name__)

# Temporarily disable CSRF protection for services API
from app import csrf
csrf.exempt(services_api)

@services_api.route('/', methods=['GET'])
@login_required
def get_services():
    """Get all registered services"""
    try:
        # Check if user has permission
        if not current_user.role == 'admin':
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        services = microservice_service.discover_services()
        
        services_data = {}
        for service_type, instances in services.items():
            services_data[service_type.value] = [
                instance.to_dict() for instance in instances
            ]
        
        return jsonify({
            'status': 'success',
            'services': services_data
        })
    except Exception as e:
        logger.error(f"Error getting services: {e}")
        return jsonify({'error': 'Failed to get services'}), 500

@services_api.route('/stats', methods=['GET'])
@login_required
def get_service_stats():
    """Get service statistics"""
    try:
        # Check if user has permission
        if not current_user.role == 'admin':
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        stats = microservice_service.get_service_stats()
        
        return jsonify({
            'status': 'success',
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Error getting service stats: {e}")
        return jsonify({'error': 'Failed to get service stats'}), 500

@services_api.route('/register', methods=['POST'])
@login_required
def register_service():
    """Register a new service instance"""
    try:
        # Check if user has permission
        if not current_user.role == 'admin':
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        service_type = data.get('service_type')
        host = data.get('host')
        port = data.get('port')
        metadata = data.get('metadata', {})
        
        if not all([service_type, host, port]):
            return jsonify({'error': 'service_type, host, and port are required'}), 400
        
        try:
            service_type_enum = ServiceType(service_type)
        except ValueError:
            return jsonify({
                'error': 'Invalid service type',
                'valid_types': [st.value for st in ServiceType]
            }), 400
        
        service_id = microservice_service.register_service(
            service_type_enum, host, port, metadata
        )
        
        return jsonify({
            'status': 'success',
            'service_id': service_id,
            'message': 'Service registered successfully'
        })
    except Exception as e:
        logger.error(f"Error registering service: {e}")
        return jsonify({'error': 'Failed to register service'}), 500

@services_api.route('/<service_id>', methods=['DELETE'])
@login_required
def unregister_service(service_id):
    """Unregister a service instance"""
    try:
        # Check if user has permission
        if not current_user.role == 'admin':
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        microservice_service.unregister_service(service_id)
        
        return jsonify({
            'status': 'success',
            'message': 'Service unregistered successfully'
        })
    except Exception as e:
        logger.error(f"Error unregistering service: {e}")
        return jsonify({'error': 'Failed to unregister service'}), 500

@services_api.route('/types', methods=['GET'])
@login_required
def get_service_types():
    """Get available service types"""
    try:
        service_types = [
            {
                'value': st.value,
                'description': f'{st.value.replace("_", " ").title()} Service'
            }
            for st in ServiceType
        ]
        
        return jsonify({
            'status': 'success',
            'service_types': service_types
        })
    except Exception as e:
        logger.error(f"Error getting service types: {e}")
        return jsonify({'error': 'Failed to get service types'}), 500
