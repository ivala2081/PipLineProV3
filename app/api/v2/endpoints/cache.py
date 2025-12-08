"""
Cache Management API endpoints for PipLinePro v2
Cache statistics, invalidation, and warming
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.services.enhanced_cache_service import cache_service, CacheKey
from app.services.event_service import event_service, EventType
import logging

logger = logging.getLogger(__name__)

cache_api = Blueprint('cache_api', __name__)

# Temporarily disable CSRF protection for cache API
from app import csrf
csrf.exempt(cache_api)

@cache_api.route('/stats', methods=['GET'])
@login_required
def get_cache_stats():
    """Get cache statistics"""
    try:
        stats = cache_service.get_stats()
        return jsonify({
            'status': 'success',
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return jsonify({'error': 'Failed to get cache stats'}), 500

@cache_api.route('/invalidate', methods=['POST'])
@login_required
def invalidate_cache():
    """Invalidate cache by pattern"""
    try:
        data = request.get_json()
        pattern = data.get('pattern')
        
        if not pattern:
            return jsonify({'error': 'Pattern is required'}), 400
        
        # Check if user has permission to invalidate cache
        if not current_user.role == 'admin':
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        invalidated_count = cache_service.invalidate_pattern(pattern)
        
        return jsonify({
            'status': 'success',
            'pattern': pattern,
            'invalidated_count': invalidated_count,
            'message': f'Invalidated {invalidated_count} cache entries'
        })
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        return jsonify({'error': 'Failed to invalidate cache'}), 500

@cache_api.route('/invalidate/transactions', methods=['POST'])
@login_required
def invalidate_transaction_cache():
    """Invalidate transaction-related cache"""
    try:
        data = request.get_json()
        transaction_id = data.get('transaction_id')
        
        invalidated_count = cache_service.invalidate_transaction_cache(transaction_id)
        
        return jsonify({
            'status': 'success',
            'transaction_id': transaction_id,
            'invalidated_count': invalidated_count,
            'message': f'Invalidated {invalidated_count} transaction cache entries'
        })
    except Exception as e:
        logger.error(f"Error invalidating transaction cache: {e}")
        return jsonify({'error': 'Failed to invalidate transaction cache'}), 500

@cache_api.route('/warm', methods=['POST'])
@login_required
def warm_cache():
    """Warm cache using specified strategy"""
    try:
        data = request.get_json()
        strategy = data.get('strategy')
        
        if not strategy:
            return jsonify({'error': 'Strategy is required'}), 400
        
        # Check if user has permission to warm cache
        if not current_user.role == 'admin':
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        success = cache_service.warm_cache(strategy, **data.get('params', {}))
        
        if success:
            return jsonify({
                'status': 'success',
                'strategy': strategy,
                'message': f'Cache warmed successfully using {strategy} strategy'
            })
        else:
            return jsonify({
                'status': 'error',
                'strategy': strategy,
                'message': f'Failed to warm cache using {strategy} strategy'
            }), 500
    except Exception as e:
        logger.error(f"Error warming cache: {e}")
        return jsonify({'error': 'Failed to warm cache'}), 500

@cache_api.route('/clear', methods=['POST'])
@login_required
def clear_all_cache():
    """Clear all cache (admin only)"""
    try:
        # Check if user has permission to clear cache
        if not current_user.role == 'admin':
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        success = cache_service.clear_all()
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'All cache cleared successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to clear cache'
            }), 500
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return jsonify({'error': 'Failed to clear cache'}), 500

@cache_api.route('/key/<path:key>', methods=['GET'])
@login_required
def get_cache_key(key):
    """Get value for a specific cache key"""
    try:
        value = cache_service.get(key)
        
        if value is not None:
            return jsonify({
                'status': 'success',
                'key': key,
                'value': value,
                'hit': True
            })
        else:
            return jsonify({
                'status': 'success',
                'key': key,
                'value': None,
                'hit': False
            })
    except Exception as e:
        logger.error(f"Error getting cache key: {e}")
        return jsonify({'error': 'Failed to get cache key'}), 500

@cache_api.route('/key/<path:key>', methods=['DELETE'])
@login_required
def delete_cache_key(key):
    """Delete a specific cache key"""
    try:
        # Check if user has permission to delete cache keys
        if not current_user.role == 'admin':
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        success = cache_service.delete(key)
        
        if success:
            return jsonify({
                'status': 'success',
                'key': key,
                'message': 'Cache key deleted successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'key': key,
                'message': 'Failed to delete cache key'
            }), 500
    except Exception as e:
        logger.error(f"Error deleting cache key: {e}")
        return jsonify({'error': 'Failed to delete cache key'}), 500

@cache_api.route('/patterns', methods=['GET'])
@login_required
def get_cache_patterns():
    """Get available cache key patterns"""
    try:
        patterns = {
            'transaction_list': 'pipeline:transactions:*',
            'transaction_detail': 'pipeline:transaction:*',
            'psp_summary': 'pipeline:psp_summary:*',
            'daily_balance': 'pipeline:daily_balance:*',
            'analytics_dashboard': 'pipeline:analytics:*',
            'exchange_rate': 'pipeline:exchange_rate:*',
            'user_session': 'pipeline:session:*',
            'all': 'pipeline:*'
        }
        
        return jsonify({
            'status': 'success',
            'patterns': patterns
        })
    except Exception as e:
        logger.error(f"Error getting cache patterns: {e}")
        return jsonify({'error': 'Failed to get cache patterns'}), 500

@cache_api.route('/strategies', methods=['GET'])
@login_required
def get_warming_strategies():
    """Get available cache warming strategies"""
    try:
        strategies = {
            'transaction_list': 'Warm transaction list cache for common queries',
            'psp_summary': 'Warm PSP summary cache for recent dates',
            'analytics_dashboard': 'Warm analytics dashboard cache',
            'exchange_rates': 'Warm exchange rates cache for major currencies'
        }
        
        return jsonify({
            'status': 'success',
            'strategies': strategies
        })
    except Exception as e:
        logger.error(f"Error getting warming strategies: {e}")
        return jsonify({'error': 'Failed to get warming strategies'}), 500
