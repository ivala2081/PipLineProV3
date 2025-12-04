"""
Settings routes blueprint
"""
from flask import Blueprint, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timezone
import json
import logging
from decimal import Decimal, InvalidOperation

from app import db
from app.models.config import Option, UserSettings
from app.models.user import User
from app.services.psp_options_service import PspOptionsService
from app.services.company_options_service import CompanyOptionsService

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings')
@login_required
def settings():
    """Main settings page"""
    try:
        # Get all active options grouped by field name (excluding PSP and Company)
        options = Option.query.filter_by(is_active=True).filter(Option.field_name != 'psp').filter(Option.field_name != 'company').order_by(Option.field_name, Option.value).all()
        
        # Group by field name
        grouped_options = {}
        for option in options:
            if option.field_name not in grouped_options:
                grouped_options[option.field_name] = []
            grouped_options[option.field_name].append(option)
        
        # Get available field names for dropdown (PSP and Company are now fixed from database)
        fields = ['category', 'payment_method', 'currency']
        
        # Get user sessions for the sessions tab
        from app.models.audit import UserSession
        sessions = UserSession.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).order_by(UserSession.last_active.desc()).all()
        
        # Get user settings
        user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        
        # Get fixed PSP options from database
        fixed_psp_options = PspOptionsService.create_fixed_psp_options()
        
        # Get fixed Company options from database
        fixed_company_options = CompanyOptionsService.create_fixed_company_options()
        
        return redirect('http://localhost:3000/settings')
                            
    except Exception as e:
        logger.error(f"Error in settings: {str(e)}")
        flash('Error loading settings. Please try again.', 'error')
        return redirect('http://localhost:3000/settings')

@settings_bp.route('/settings/dropdowns', methods=['GET', 'POST'])
@login_required
def settings_dropdowns():
    """Manage dropdown options"""
    if request.method == 'POST':
        try:
            action = request.form.get('action')
            
            if action == 'add':
                field_name = request.form.get('field_name', '').strip()
                value = request.form.get('value', '').strip()
                commission_rate = request.form.get('commission_rate', '').strip()
                
                if not field_name or not value:
                    flash('Field name and value are required.', 'error')
                    return redirect(url_for('settings.settings_dropdowns'))
                
                # Validate commission rate if provided
                commission_decimal = None
                if commission_rate:
                    try:
                        commission_decimal = Decimal(commission_rate)
                        if commission_decimal < 0 or commission_decimal > 1:
                            flash('Commission rate must be between 0 and 1.', 'error')
                            return redirect(url_for('settings.settings_dropdowns'))
                    except (InvalidOperation, ValueError):
                        flash('Invalid commission rate format.', 'error')
                        return redirect(url_for('settings.settings_dropdowns'))
                
                # Check if option already exists
                existing = Option.query.filter_by(
                    field_name=field_name,
                    value=value,
                    is_active=True
                ).first()
                
                if existing:
                    flash('This option already exists.', 'error')
                    return redirect(url_for('settings.settings_dropdowns'))
                
                # Create new option
                option = Option(
                    field_name=field_name,
                    value=value,
                    commission_rate=commission_decimal
                )
                
                db.session.add(option)
                db.session.commit()
                
                flash('Option added successfully!', 'success')
                
            elif action == 'delete':
                option_id = request.form.get('option_id')
                if option_id:
                    option = Option.query.get(option_id)
                    if option:
                        option.is_active = False
                        db.session.commit()
                        flash('Option deactivated successfully!', 'success')
                    else:
                        flash('Option not found.', 'error')
                else:
                    flash('Option ID is required.', 'error')
            
            elif action == 'edit':
                option_id = request.form.get('option_id')
                new_value = request.form.get('new_value', '').strip()
                commission_rate = request.form.get('commission_rate', '').strip()
                
                if not option_id or not new_value:
                    flash('Option ID and new value are required.', 'error')
                    return redirect(url_for('settings.settings_dropdowns'))
                
                option = Option.query.get(option_id)
                if not option:
                    flash('Option not found.', 'error')
                    return redirect(url_for('settings.settings_dropdowns'))
                
                # Validate commission rate if provided
                commission_decimal = None
                if commission_rate:
                    try:
                        commission_decimal = Decimal(commission_rate)
                        if commission_decimal < 0 or commission_decimal > 1:
                            flash('Commission rate must be between 0 and 1.', 'error')
                            return redirect(url_for('settings.settings_dropdowns'))
                    except (InvalidOperation, ValueError):
                        flash('Invalid commission rate format.', 'error')
                        return redirect(url_for('settings.settings_dropdowns'))
                
                option.value = new_value
                option.commission_rate = commission_decimal
                db.session.commit()
                
                flash('Option updated successfully!', 'success')
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in settings dropdowns: {str(e)}")
            flash('Error processing request. Please try again.', 'error')
    
    # Get all active options grouped by field name (excluding PSP and Company)
    options = Option.query.filter_by(is_active=True).filter(Option.field_name != 'psp').filter(Option.field_name != 'company').order_by(Option.field_name, Option.value).all()
    
    # Group by field name
    grouped_options = {}
    for option in options:
        if option.field_name not in grouped_options:
            grouped_options[option.field_name] = []
        grouped_options[option.field_name].append(option)
    
    # Define available fields for the dropdown (PSP and Company are now fixed from database)
    fields = ['iban', 'payment_method', 'company_order', 'currency']
    
    return redirect('http://localhost:3000/settings')

@settings_bp.route('/edit_option/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_option(id):
    """Edit specific option"""
    option = Option.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            value = request.form.get('value', '').strip()
            commission_rate = request.form.get('commission_rate', '').strip()
            
            if not value:
                flash('Value is required.', 'error')
                return redirect('http://localhost:3000/settings')
            
            # Validate commission rate if provided
            commission_decimal = None
            if commission_rate:
                try:
                    commission_decimal = Decimal(commission_rate)
                    if commission_decimal < 0 or commission_decimal > 1:
                        flash('Commission rate must be between 0 and 1.', 'error')
                        return redirect('http://localhost:3000/settings')
                except (InvalidOperation, ValueError):
                    flash('Invalid commission rate format.', 'error')
                    return redirect('http://localhost:3000/settings')
            
            option.value = value
            option.commission_rate = commission_decimal
            db.session.commit()
            
            flash('Option updated successfully!', 'success')
            return redirect(url_for('settings.settings_dropdowns'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating option: {str(e)}")
            flash('Error updating option. Please try again.', 'error')
    
    return redirect('http://localhost:3000/settings')

@settings_bp.route('/delete_option/<int:id>', methods=['POST'])
@login_required
def delete_option(id):
    """Delete option (soft delete)"""
    option = Option.query.get_or_404(id)
    
    try:
        option.is_active = False
        db.session.commit()
        flash('Option deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting option: {str(e)}")
        flash('Error deleting option. Please try again.', 'error')
    
    return redirect(url_for('settings.settings_dropdowns'))

@settings_bp.route('/exchange_rates_validation')
@login_required
def exchange_rates_validation():
    """Exchange rates validation page"""
    try:
        from app.models.config import ExchangeRate
        from datetime import date, timedelta
        
        # Get exchange rates from the last 30 days
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        # Get all exchange rates in the date range
        exchange_rates = ExchangeRate.query.filter(
            ExchangeRate.date >= start_date,
            ExchangeRate.date <= end_date
        ).order_by(ExchangeRate.date.desc()).all()
        
        # Group by date
        rates_by_date = {}
        for rate in exchange_rates:
            date_str = rate.date.strftime('%Y-%m-%d')
            if date_str not in rates_by_date:
                rates_by_date[date_str] = {}
            rates_by_date[date_str][rate.currency] = rate.rate
        
        # Find missing rates
        missing_rates = []
        for date_str, rates in rates_by_date.items():
            if 'USD' not in rates:
                missing_rates.append({'date': date_str, 'currency': 'USD', 'status': 'Missing'})
            if 'EUR' not in rates:
                missing_rates.append({'date': date_str, 'currency': 'EUR', 'status': 'Missing'})
        
        return redirect('http://localhost:3000/settings')
                            
    except Exception as e:
        logger.error(f"Error in exchange rates validation: {str(e)}")
        flash('Error loading exchange rates validation. Please try again.', 'error')
        return redirect(url_for('settings.settings'))

@settings_bp.route('/settings/save_preferences', methods=['POST'])
@login_required
def save_preferences():
    """Save user preferences"""
    try:
        # Debug: Log form data
        logger.info(f"Form data received: {dict(request.form)}")
        
        # Get or create user settings
        user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not user_settings:
            user_settings = UserSettings(user_id=current_user.id)
            db.session.add(user_settings)
        
        # Update settings from form
        language = request.form.get('language', 'en')
        logger.info(f"Setting language to: {language}")
        user_settings.language = language
        
        # Set default values for missing fields
        user_settings.landing_page = request.form.get('landing_page', 'dashboard')
        user_settings.table_page_size = int(request.form.get('table_page_size', 25))
        user_settings.table_density = request.form.get('table_density', 'comfortable')
        user_settings.font_size = request.form.get('font_size', 'medium')
        user_settings.color_scheme = request.form.get('color_scheme', 'default')
        
        db.session.commit()
        logger.info(f"Preferences saved successfully. Language: {user_settings.language}")
        
        flash('Preferences saved successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving preferences: {str(e)}")
        flash('Error saving preferences. Please try again.', 'error')
    
    return redirect(url_for('settings.settings'))

@settings_bp.route('/change_language/<language>', methods=['POST'])
@login_required
def change_language(language):
    """Change user language"""
    try:
        from flask_babel import gettext as _
        
        # Validate language
        if language not in ['en', 'tr']:
            flash('Invalid language selected.', 'error')
            return redirect(url_for('settings.settings'))
        
        # Get or create user settings
        user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not user_settings:
            user_settings = UserSettings(user_id=current_user.id)
            db.session.add(user_settings)
        
        # Update language
        user_settings.language = language
        db.session.commit()
        
        flash('Language changed successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error changing language: {str(e)}")
        flash('Error changing language. Please try again.', 'error')
    
    return redirect(url_for('settings.settings'))

@settings_bp.route('/toggle_theme', methods=['POST'])
@login_required
def toggle_theme():
    """Toggle between light and dark theme"""
    try:
        # Get or create user settings
        user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not user_settings:
            user_settings = UserSettings(user_id=current_user.id)
            db.session.add(user_settings)
        
        # Toggle theme
        current_theme = user_settings.color_scheme or 'default'
        new_theme = 'dark' if current_theme == 'light' else 'light'
        user_settings.color_scheme = new_theme
        
        db.session.commit()
        
        return jsonify({'success': True, 'theme': new_theme})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling theme: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to toggle theme'})

@settings_bp.route('/api/user_preferences')
@login_required
def api_user_preferences():
    """Get user preferences via API"""
    try:
        user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        
        if user_settings:
            return jsonify({
                'language': user_settings.language,
                'landing_page': user_settings.landing_page,
                'table_page_size': user_settings.table_page_size,
                'table_density': user_settings.table_density,
                'font_size': user_settings.font_size,
                'color_scheme': user_settings.color_scheme
            })
        else:
            return jsonify({
                'language': 'en',
                'landing_page': 'dashboard',
                'table_page_size': 25,
                'table_density': 'comfortable',
                'font_size': 'medium',
                'color_scheme': 'default'
            })
            
    except Exception as e:
        logger.error(f"Error getting user preferences: {str(e)}")
        return jsonify({'error': 'Failed to get preferences'}), 500

@settings_bp.route('/api/system_info')
@login_required
def api_system_info():
    """Get system information"""
    try:
        import platform
        import psutil
        
        # Get system information
        system_info = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'memory_available': psutil.virtual_memory().available,
            'disk_usage': psutil.disk_usage('/').percent
        }
        
        return jsonify(system_info)
        
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        return jsonify({'error': 'Failed to get system information'}), 500

@settings_bp.route('/api/database/stats')
@login_required
def api_database_stats():
    """Get database statistics"""
    try:
        from app.services.database_service import get_database_stats
        
        stats = get_database_stats()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting database stats: {str(e)}")
        return jsonify({'error': 'Failed to get database statistics'}), 500

@settings_bp.route('/api/database/slow-queries')
@login_required
def api_slow_queries():
    """Get slow query information"""
    try:
        from app.services.database_service import get_slow_queries
        
        queries = get_slow_queries()
        return jsonify(queries)
        
    except Exception as e:
        logger.error(f"Error getting slow queries: {str(e)}")
        return jsonify({'error': 'Failed to get slow queries'}), 500

@settings_bp.route('/database/monitoring')
@login_required
def database_monitoring():
    """Database monitoring dashboard"""
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('analytics.dashboard'))
    
    return redirect('http://localhost:3000/settings') 