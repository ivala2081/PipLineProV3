from flask import Blueprint, request, jsonify
from app import db
from app.utils.unified_logger import get_logger
from datetime import datetime, timedelta
import json
import sqlite3

logger = get_logger(__name__)
strategy_bp = Blueprint('strategy', __name__)

@strategy_bp.route('/implement-strategy', methods=['POST'])
def implement_strategy():
    """Implement a revenue optimization strategy"""
    try:
        data = request.get_json()
        strategy_id = data.get('strategy_id')
        user_id = data.get('user_id', 1)  # Default to user 1 for now
        
        if not strategy_id:
            return jsonify({'error': 'Strategy ID is required'}), 400
        
        # Get database connection
        conn = sqlite3.connect('instance/treasury_improved.db')
        cursor = conn.cursor()
        
        # Check if strategy is already implemented
        cursor.execute("""
            SELECT id, status FROM strategy_implementations 
            WHERE strategy_id = ? AND user_id = ? AND status = 'active'
        """, (strategy_id, user_id))
        
        existing = cursor.fetchone()
        if existing:
            return jsonify({
                'success': False,
                'message': 'Strategy is already active',
                'strategy_id': strategy_id
            }), 409
        
        # Implement the specific strategy
        result = implement_specific_strategy(cursor, strategy_id, user_id)
        
        if result['success']:
            conn.commit()
            logger.info(f"Strategy {strategy_id} implemented successfully for user {user_id}")
            return jsonify({
                'success': True,
                'message': result['message'],
                'strategy_id': strategy_id,
                'implementation_id': result.get('implementation_id'),
                'details': result.get('details', {})
            })
        else:
            conn.rollback()
            return jsonify({
                'success': False,
                'message': result['message'],
                'strategy_id': strategy_id
            }), 400
            
    except Exception as e:
        logger.error(f"Error implementing strategy: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        if 'conn' in locals():
            conn.close()

def implement_specific_strategy(cursor, strategy_id, user_id):
    """Implement specific strategy based on ID"""
    
    if strategy_id == 'monday-analysis':
        return implement_monday_strategy(cursor, user_id)
    elif strategy_id == 'peak-hours':
        return implement_peak_hours_strategy(cursor, user_id)
    elif strategy_id == 'weekend-opportunity':
        return implement_weekend_strategy(cursor, user_id)
    elif strategy_id == 'psp-performance':
        return implement_psp_strategy(cursor, user_id)
    else:
        return {'success': False, 'message': 'Unknown strategy ID'}

def implement_monday_strategy(cursor, user_id):
    """Implement Monday revenue boost strategy"""
    try:
        # Create Monday-specific campaign settings
        campaign_data = {
            'discount_percentage': 15,
            'campaign_name': 'Monday Motivation Boost',
            'target_hours': ['09:00', '10:00', '11:00', '12:00'],
            'email_reminder_time': 'sunday_18:00',
            'push_notification': True,
            'special_offers': [
                'Free shipping on Mondays',
                '15% off first transaction',
                'Double loyalty points'
            ]
        }
        
        # Insert strategy implementation record
        cursor.execute("""
            INSERT INTO strategy_implementations 
            (strategy_id, user_id, status, config_data, created_at, updated_at)
            VALUES (?, ?, 'active', ?, ?, ?)
        """, (
            'monday-analysis',
            user_id,
            json.dumps(campaign_data),
            datetime.now(),
            datetime.now()
        ))
        
        implementation_id = cursor.lastrowid
        
        # Update system settings for Monday optimization
        cursor.execute("""
            INSERT OR REPLACE INTO system_settings 
            (setting_key, setting_value, updated_at)
            VALUES ('monday_campaign_active', 'true', ?)
        """, (datetime.now(),))
        
        cursor.execute("""
            INSERT OR REPLACE INTO system_settings 
            (setting_key, setting_value, updated_at)
            VALUES ('monday_discount_percentage', ?, ?)
        """, (str(campaign_data['discount_percentage']), datetime.now()))
        
        return {
            'success': True,
            'message': 'Monday Motivation campaign activated successfully!',
            'implementation_id': implementation_id,
            'details': {
                'discount': f"{campaign_data['discount_percentage']}%",
                'offers': campaign_data['special_offers'],
                'email_reminder': 'Sundays at 6 PM'
            }
        }
        
    except Exception as e:
        logger.error(f"Error implementing Monday strategy: {str(e)}")
        return {'success': False, 'message': f'Failed to implement Monday strategy: {str(e)}'}

def implement_peak_hours_strategy(cursor, user_id):
    """Implement peak hours optimization strategy"""
    try:
        peak_config = {
            'peak_hours': ['14:00', '15:00', '16:00'],
            'staff_multiplier': 1.5,
            'marketing_boost': 2.0,
            'server_scaling': True,
            'time_sensitive_offers': True,
            'priority_routing': True
        }
        
        cursor.execute("""
            INSERT INTO strategy_implementations 
            (strategy_id, user_id, status, config_data, created_at, updated_at)
            VALUES (?, ?, 'active', ?, ?, ?)
        """, (
            'peak-hours',
            user_id,
            json.dumps(peak_config),
            datetime.now(),
            datetime.now()
        ))
        
        implementation_id = cursor.lastrowid
        
        # Update system settings
        cursor.execute("""
            INSERT OR REPLACE INTO system_settings 
            (setting_key, setting_value, updated_at)
            VALUES ('peak_hours_optimization', 'true', ?)
        """, (datetime.now(),))
        
        cursor.execute("""
            INSERT OR REPLACE INTO system_settings 
            (setting_key, setting_value, updated_at)
            VALUES ('peak_hours_config', ?, ?)
        """, (json.dumps(peak_config), datetime.now()))
        
        return {
            'success': True,
            'message': 'Peak hours optimization activated!',
            'implementation_id': implementation_id,
            'details': {
                'peak_hours': '2-4 PM',
                'staff_boost': '50% increase',
                'marketing_boost': '2x budget',
                'server_scaling': 'Enabled'
            }
        }
        
    except Exception as e:
        logger.error(f"Error implementing peak hours strategy: {str(e)}")
        return {'success': False, 'message': f'Failed to implement peak hours strategy: {str(e)}'}

def implement_weekend_strategy(cursor, user_id):
    """Implement weekend revenue opportunity strategy"""
    try:
        weekend_config = {
            'weekend_promotions': True,
            'conversion_optimization': True,
            'extended_support_hours': True,
            'weekend_themes': ['Family Time', 'Relaxation', 'Entertainment'],
            'special_features': ['Weekend-only products', 'Bundle deals', 'Free gifts'],
            'support_hours': {
                'saturday': '09:00-20:00',
                'sunday': '10:00-18:00'
            }
        }
        
        cursor.execute("""
            INSERT INTO strategy_implementations 
            (strategy_id, user_id, status, config_data, created_at, updated_at)
            VALUES (?, ?, 'active', ?, ?, ?)
        """, (
            'weekend-opportunity',
            user_id,
            json.dumps(weekend_config),
            datetime.now(),
            datetime.now()
        ))
        
        implementation_id = cursor.lastrowid
        
        # Update system settings
        cursor.execute("""
            INSERT OR REPLACE INTO system_settings 
            (setting_key, setting_value, updated_at)
            VALUES ('weekend_optimization', 'true', ?)
        """, (datetime.now(),))
        
        return {
            'success': True,
            'message': 'Weekend revenue optimization activated!',
            'implementation_id': implementation_id,
            'details': {
                'promotions': 'Weekend-specific campaigns',
                'support_hours': 'Extended weekend coverage',
                'special_features': 'Weekend-only products and deals'
            }
        }
        
    except Exception as e:
        logger.error(f"Error implementing weekend strategy: {str(e)}")
        return {'success': False, 'message': f'Failed to implement weekend strategy: {str(e)}'}

def implement_psp_strategy(cursor, user_id):
    """Implement PSP performance optimization strategy"""
    try:
        psp_config = {
            'preferred_psp': 'CRYPPAY',
            'high_value_threshold': 1000,
            'routing_rules': {
                'high_value': 'CRYPPAY',
                'low_value': 'AUTO',
                'international': 'CRYPPAY'
            },
            'rate_negotiation': True,
            'performance_monitoring': True,
            'fallback_psps': ['SİPAY', 'PAYTR', 'IYZICO']
        }
        
        cursor.execute("""
            INSERT INTO strategy_implementations 
            (strategy_id, user_id, status, config_data, created_at, updated_at)
            VALUES (?, ?, 'active', ?, ?, ?)
        """, (
            'psp-performance',
            user_id,
            json.dumps(psp_config),
            datetime.now(),
            datetime.now()
        ))
        
        implementation_id = cursor.lastrowid
        
        # Update PSP routing settings
        cursor.execute("""
            INSERT OR REPLACE INTO system_settings 
            (setting_key, setting_value, updated_at)
            VALUES ('psp_optimization', 'true', ?)
        """, (datetime.now(),))
        
        cursor.execute("""
            INSERT OR REPLACE INTO system_settings 
            (setting_key, setting_value, updated_at)
            VALUES ('psp_routing_config', ?, ?)
        """, (json.dumps(psp_config), datetime.now()))
        
        return {
            'success': True,
            'message': 'PSP optimization activated!',
            'implementation_id': implementation_id,
            'details': {
                'preferred_psp': 'CRYPPAY',
                'high_value_threshold': '₺1,000+',
                'routing': 'Smart PSP selection',
                'monitoring': 'Real-time performance tracking'
            }
        }
        
    except Exception as e:
        logger.error(f"Error implementing PSP strategy: {str(e)}")
        return {'success': False, 'message': f'Failed to implement PSP strategy: {str(e)}'}

@strategy_bp.route('/strategy-status', methods=['GET'])
def get_strategy_status():
    """Get status of all implemented strategies"""
    try:
        user_id = request.args.get('user_id', 1)
        
        conn = sqlite3.connect('instance/treasury_improved.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT strategy_id, status, config_data, created_at, updated_at
            FROM strategy_implementations 
            WHERE user_id = ? AND status = 'active'
            ORDER BY created_at DESC
        """, (user_id,))
        
        strategies = []
        for row in cursor.fetchall():
            strategies.append({
                'strategy_id': row[0],
                'status': row[1],
                'config': json.loads(row[2]) if row[2] else {},
                'created_at': row[3],
                'updated_at': row[4]
            })
        
        return jsonify({
            'success': True,
            'strategies': strategies,
            'count': len(strategies)
        })
        
    except Exception as e:
        logger.error(f"Error getting strategy status: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@strategy_bp.route('/deactivate-strategy', methods=['POST'])
def deactivate_strategy():
    """Deactivate a strategy"""
    try:
        data = request.get_json()
        strategy_id = data.get('strategy_id')
        user_id = data.get('user_id', 1)
        
        if not strategy_id:
            return jsonify({'error': 'Strategy ID is required'}), 400
        
        conn = sqlite3.connect('instance/treasury_improved.db')
        cursor = conn.cursor()
        
        # Deactivate strategy
        cursor.execute("""
            UPDATE strategy_implementations 
            SET status = 'inactive', updated_at = ?
            WHERE strategy_id = ? AND user_id = ? AND status = 'active'
        """, (datetime.now(), strategy_id, user_id))
        
        if cursor.rowcount > 0:
            conn.commit()
            return jsonify({
                'success': True,
                'message': f'Strategy {strategy_id} deactivated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Strategy not found or already inactive'
            }), 404
            
    except Exception as e:
        logger.error(f"Error deactivating strategy: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        if 'conn' in locals():
            conn.close()
