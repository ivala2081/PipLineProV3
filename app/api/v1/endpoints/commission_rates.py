"""
Commission Rate Management API endpoints
Handles time-based PSP commission rate changes
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
from datetime import datetime, date
from decimal import Decimal
import logging

from app.services.commission_rate_service import CommissionRateService
from app.models.psp_commission_rate import PSPCommissionRate

logger = logging.getLogger(__name__)

commission_rates_api = Blueprint('commission_rates_api', __name__)

@commission_rates_api.route('/commission-rates', methods=['GET'])
@login_required
def get_commission_rates():
    """Get all commission rates with optional PSP filter"""
    try:
        psp_name = request.args.get('psp')
        
        if psp_name:
            # Get rates for specific PSP
            rates = PSPCommissionRate.query.filter_by(psp_name=psp_name, is_active=True).order_by(PSPCommissionRate.effective_from.desc()).all()
        else:
            # Get all rates
            rates = PSPCommissionRate.query.filter_by(is_active=True).order_by(PSPCommissionRate.psp_name, PSPCommissionRate.effective_from.desc()).all()
        
        return jsonify({
            'success': True,
            'rates': [rate.to_dict() for rate in rates]
        })
        
    except Exception as e:
        logger.error(f"Error getting commission rates: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@commission_rates_api.route('/commission-rates/history/<psp_name>', methods=['GET'])
@login_required
def get_commission_rate_history(psp_name):
    """Get commission rate history for a specific PSP"""
    try:
        history = CommissionRateService.get_rate_history(psp_name)
        
        return jsonify({
            'success': True,
            'psp_name': psp_name,
            'history': [rate.to_dict() for rate in history]
        })
        
    except Exception as e:
        logger.error(f"Error getting commission rate history for {psp_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@commission_rates_api.route('/commission-rates', methods=['POST'])
@login_required
def set_commission_rate():
    """Set a new commission rate for a PSP"""
    try:
        data = request.get_json()
        
        psp_name = data.get('psp_name')
        commission_rate = data.get('commission_rate')
        effective_from = data.get('effective_from')
        effective_until = data.get('effective_until')
        
        if not all([psp_name, commission_rate, effective_from]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: psp_name, commission_rate, effective_from'
            }), 400
        
        # Parse dates
        try:
            effective_from_date = datetime.strptime(effective_from, '%Y-%m-%d').date()
            effective_until_date = None
            if effective_until:
                effective_until_date = datetime.strptime(effective_until, '%Y-%m-%d').date()
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': f'Invalid date format: {e}'
            }), 400
        
        # Parse commission rate
        try:
            rate_decimal = Decimal(str(commission_rate))
            if rate_decimal < 0 or rate_decimal > 1:
                return jsonify({
                    'success': False,
                    'error': 'Commission rate must be between 0 and 1 (0.15 = 15%)'
                }), 400
        except (ValueError, InvalidOperation) as e:
            return jsonify({
                'success': False,
                'error': f'Invalid commission rate: {e}'
            }), 400
        
        # Set the new rate
        rate_record = CommissionRateService.set_commission_rate(
            psp_name=psp_name,
            new_rate=rate_decimal,
            effective_from=effective_from_date,
            effective_until=effective_until_date
        )
        
        return jsonify({
            'success': True,
            'message': f'Commission rate set for {psp_name}',
            'rate': rate_record.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error setting commission rate: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@commission_rates_api.route('/commission-rates/<int:rate_id>', methods=['PUT'])
@login_required
def update_commission_rate(rate_id):
    """Update an existing commission rate"""
    try:
        rate_record = PSPCommissionRate.query.get(rate_id)
        if not rate_record:
            return jsonify({
                'success': False,
                'error': 'Commission rate not found'
            }), 404
        
        data = request.get_json()
        
        # Update fields if provided
        if 'commission_rate' in data:
            try:
                rate_decimal = Decimal(str(data['commission_rate']))
                if rate_decimal < 0 or rate_decimal > 1:
                    return jsonify({
                        'success': False,
                        'error': 'Commission rate must be between 0 and 1 (0.15 = 15%)'
                    }), 400
                rate_record.commission_rate = rate_decimal
            except (ValueError, InvalidOperation) as e:
                return jsonify({
                    'success': False,
                    'error': f'Invalid commission rate: {e}'
                }), 400
        
        if 'effective_from' in data:
            try:
                rate_record.effective_from = datetime.strptime(data['effective_from'], '%Y-%m-%d').date()
            except ValueError as e:
                return jsonify({
                    'success': False,
                    'error': f'Invalid effective_from date: {e}'
                }), 400
        
        if 'effective_until' in data:
            if data['effective_until']:
                try:
                    rate_record.effective_until = datetime.strptime(data['effective_until'], '%Y-%m-%d').date()
                except ValueError as e:
                    return jsonify({
                        'success': False,
                        'error': f'Invalid effective_until date: {e}'
                    }), 400
            else:
                rate_record.effective_until = None
        
        if 'is_active' in data:
            rate_record.is_active = bool(data['is_active'])
        
        from app import db
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Commission rate updated successfully',
            'rate': rate_record.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating commission rate {rate_id}: {e}")
        from app import db
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@commission_rates_api.route('/commission-rates/<int:rate_id>', methods=['DELETE'])
@login_required
def delete_commission_rate(rate_id):
    """Delete a commission rate (soft delete)"""
    try:
        rate_record = PSPCommissionRate.query.get(rate_id)
        if not rate_record:
            return jsonify({
                'success': False,
                'error': 'Commission rate not found'
            }), 404
        
        # Soft delete
        rate_record.is_active = False
        from app import db
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Commission rate deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting commission rate {rate_id}: {e}")
        from app import db
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@commission_rates_api.route('/commission-rates/rate/<psp_name>', methods=['GET'])
@login_required
def get_current_rate(psp_name):
    """Get current commission rate for a PSP"""
    try:
        target_date = request.args.get('date')
        if target_date:
            try:
                target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid date format. Use YYYY-MM-DD'
                }), 400
        else:
            target_date = date.today()
        
        rate = CommissionRateService.get_commission_rate(psp_name, target_date)
        rate_percent = CommissionRateService.get_commission_rate_percentage(psp_name, target_date)
        
        return jsonify({
            'success': True,
            'psp_name': psp_name,
            'date': target_date.isoformat(),
            'rate': float(rate),
            'rate_percent': rate_percent
        })
        
    except Exception as e:
        logger.error(f"Error getting current rate for {psp_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
