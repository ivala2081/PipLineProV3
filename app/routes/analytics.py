"""
Analytics routes blueprint
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta, timezone
from sqlalchemy import func, extract, desc, and_, or_, case, cast, Float
import pandas as pd
import json
from decimal import Decimal, InvalidOperation
from collections import defaultdict
import logging

from app import db, socketio
from flask_socketio import emit, join_room, leave_room
from app.models.transaction import Transaction
from app.models.user import User
from app.models.config import Option
from app.models.config import ExchangeRate
from app.models.financial import PspTrack, DailyBalance
from app.services.optimized_query_service import optimized_query_service
# from app.services.performance_optimized_service import performance_optimized_service
from app.utils.template_helpers import legacy_ultimate_tojson
from app.utils.unified_error_handler import handle_errors, handle_api_errors

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
analytics_bp = Blueprint('analytics', __name__)

def calculate_psp_overview_data():
    """Calculate PSP overview data"""
    try:
        # Get date range (default to last 30 days)
        days = request.args.get('days', 30, type=int)
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get transactions in date range
        transactions = Transaction.query.filter(
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).all()
        
        # Group by PSP
        psp_data = defaultdict(lambda: {
            'total_amount': Decimal('0'),
            'total_commission': Decimal('0'),
            'total_net': Decimal('0'),
            'transaction_count': 0,
            'daily_averages': defaultdict(lambda: Decimal('0'))
        })
        
        for transaction in transactions:
            psp = transaction.psp or 'Unknown'
            psp_data[psp]['total_amount'] += transaction.amount
            psp_data[psp]['total_commission'] += transaction.commission
            psp_data[psp]['total_net'] += transaction.net_amount
            psp_data[psp]['transaction_count'] += 1
            psp_data[psp]['daily_averages'][transaction.date] += transaction.amount
        
        # Calculate averages and format data
        result = []
        for psp, data in psp_data.items():
            avg_daily = sum(data['daily_averages'].values()) / len(data['daily_averages']) if data['daily_averages'] else Decimal('0')
            result.append({
                'psp': psp,
                'total_amount': float(data['total_amount']),
                'total_commission': float(data['total_commission']),
                'total_net': float(data['total_net']),
                'transaction_count': data['transaction_count'],
                'avg_daily_amount': float(avg_daily),
                'commission_rate': float(data['total_commission'] / data['total_amount'] * 100) if data['total_amount'] > 0 else 0
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error calculating PSP overview: {str(e)}")
        return []

def get_exchange_rate(date_obj, currency='USD'):
    """Get exchange rate for a specific date"""
    try:
        rate = ExchangeRate.query.filter_by(date=date_obj).first()
        if rate:
            if currency == 'USD':
                return rate.usd_to_tl
            elif currency == 'EUR':
                return rate.eur_to_tl or 0
        return 1.0  # Default fallback
    except Exception as e:
        logger.error(f"Error getting exchange rate: {str(e)}")
        return 1.0

def validate_exchange_rates(date_obj):
    """Validate exchange rates for a date"""
    try:
        rate = ExchangeRate.query.filter_by(date=date_obj).first()
        if not rate:
            return False, "No exchange rates found for this date"
        if not rate.usd_to_tl or rate.usd_to_tl <= 0:
            return False, "Invalid USD exchange rate"
        return True, "Exchange rates are valid"
    except Exception as e:
        logger.error(f"Error validating exchange rates: {str(e)}")
        return False, f"Error validating exchange rates: {str(e)}"

def get_safe_exchange_rate(date_obj, currency='USD', fallback_rate=1.0):
    """Get exchange rate with fallback"""
    try:
        rate = get_exchange_rate(date_obj, currency)
        if rate and rate > 0:
            return rate
        return fallback_rate
    except Exception as e:
        logger.error(f"Error getting safe exchange rate: {str(e)}")
        return fallback_rate

@analytics_bp.route('/dashboard')
@login_required
@handle_errors
def dashboard():
    """Dashboard page - serve React frontend"""
    try:
        from flask import send_from_directory
        frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontend', 'dist_prod')
        if not os.path.exists(frontend_dist):
            frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontend', 'dist')
        index_path = os.path.join(frontend_dist, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(frontend_dist, 'index.html')
        return redirect('/')
                           
    except Exception as e:
        logger.error(f"Error in dashboard: {str(e)}")
        flash('Error loading dashboard data', 'error')
        return redirect('/')

@analytics_bp.route('/analytics')
@login_required
@handle_errors
def analytics():
    """Advanced analytics page"""
    try:
        # Get date range
        days = request.args.get('days', 30, type=int)
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get transactions in date range
        transactions = Transaction.query.filter(
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).all()
        
        # Calculate advanced metrics
        total_amount = sum(t.amount for t in transactions)
        total_commission = sum(t.commission for t in transactions)
        avg_transaction_size = total_amount / len(transactions) if transactions else 0
        
        # Calculate growth rate (compare with previous period)
        prev_start_date = start_date - timedelta(days=days)
        prev_transactions = Transaction.query.filter(
            Transaction.date >= prev_start_date,
            Transaction.date < start_date
        ).all()
        
        prev_total = sum(t.amount for t in prev_transactions)
        growth_rate = ((total_amount - prev_total) / prev_total * 100) if prev_total > 0 else 0
        
        # Get top clients
        client_data = defaultdict(lambda: Decimal('0'))
        for transaction in transactions:
            client_data[transaction.client_name] += transaction.amount
        
        top_clients = sorted(client_data.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Get PSP performance
        psp_data = defaultdict(lambda: {
            'amount': Decimal('0'),
            'commission': Decimal('0'),
            'count': 0
        })
        
        for transaction in transactions:
            psp = transaction.psp or 'Unknown'
            psp_data[psp]['amount'] += transaction.amount
            psp_data[psp]['commission'] += transaction.commission
            psp_data[psp]['count'] += 1
        
        psp_performance = []
        for psp, data in psp_data.items():
            avg_commission_rate = float(data['commission'] / data['amount'] * 100) if data['amount'] > 0 else 0
            psp_performance.append({
                'psp': psp,
                'amount': float(data['amount']),
                'commission': float(data['commission']),
                'count': data['count'],
                'avg_commission_rate': avg_commission_rate
            })
        
        return redirect('http://localhost:3000/analytics')
        
    except Exception as e:
        logger.error(f"Error loading analytics: {str(e)}")
        flash('Error loading analytics data.', 'error')
        return redirect('http://localhost:3000/analytics')

@analytics_bp.route('/business-analytics')
@login_required
@handle_errors
def business_analytics():
    """Business intelligence dashboard - OPTIMIZED"""
    try:
        # Get date range
        days = request.args.get('days', 30, type=int)
        
        # Use optimized query service
        analytics_data = optimized_query_service.get_business_analytics(days)
        
        # Calculate additional metrics for the template
        total_revenue = analytics_data['metrics']['total_revenue']
        net_profit = analytics_data['metrics']['net_profit']
        active_clients = analytics_data['metrics']['active_clients']
        
        # Calculate growth percentages (simplified for now)
        revenue_growth = 0  # Placeholder
        profit_growth = 0   # Placeholder
        transaction_growth = 0  # Placeholder
        client_growth = 0   # Placeholder
        
        # Calculate additional metrics
        avg_daily_revenue = analytics_data['metrics']['avg_daily_revenue']
        cost_ratio = analytics_data['metrics']['cost_ratio']
        
        # Find peak revenue day and ensure it's a datetime object
        peak_revenue_date = analytics_data['peak_revenue_date']
        if isinstance(peak_revenue_date, str):
            from app.services.datetime_fix_service import ensure_datetime
            peak_revenue_date = ensure_datetime(peak_revenue_date) or date.today()
        
        # Calculate additional metrics for template
        retention_rate = 85.0  # Placeholder - should be calculated based on repeat transactions
        avg_transaction_value = analytics_data['metrics']['avg_transaction_value']
        transactions_per_day = analytics_data['metrics']['transactions_per_day']
        next_month_forecast = float(total_revenue) * 1.1  # Placeholder - should use proper forecasting
        next_quarter_forecast = float(total_revenue) * 1.3  # Placeholder
        forecast_growth = 10.0  # Placeholder
        
        # Trend data will be serialized by the template filters
        sanitized_trends = analytics_data['trends']
        
        return redirect('http://localhost:3000/business-analytics')
        
    except Exception as e:
        logger.error(f"Error loading business analytics: {str(e)}")
        flash('Error loading business analytics data.', 'error')
        return redirect('http://localhost:3000/business-analytics')

@analytics_bp.route('/api/analytics/data')
@login_required
def api_analytics_data():
    """API endpoint for analytics data"""
    try:
        days = request.args.get('days', 30, type=int)
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get transactions
        transactions = Transaction.query.filter(
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).all()
        
        # Calculate metrics
        total_amount = sum(t.amount for t in transactions)
        total_commission = sum(t.commission for t in transactions)
        total_net = sum(t.net_amount for t in transactions)
        
        # Group by date
        daily_data = defaultdict(lambda: {
            'amount': Decimal('0'),
            'commission': Decimal('0'),
            'net': Decimal('0'),
            'count': 0
        })
        
        for transaction in transactions:
            daily_data[transaction.date]['amount'] += transaction.amount
            daily_data[transaction.date]['commission'] += transaction.commission
            daily_data[transaction.date]['net'] += transaction.net_amount
            daily_data[transaction.date]['count'] += 1
        
        # Format for API response
        result = {
            'summary': {
                'total_amount': float(total_amount),
                'total_commission': float(total_commission),
                'total_net': float(total_net),
                'transaction_count': len(transactions)
            },
            'daily_data': [
                {
                    'date': d.strftime('%Y-%m-%d'),
                    'amount': float(data['amount']),
                    'commission': float(data['commission']),
                    'net': float(data['net']),
                    'count': data['count']
                }
                for d, data in sorted(daily_data.items())
            ]
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in analytics API: {str(e)}")
        return jsonify({'error': 'Failed to load analytics data'}), 500

@analytics_bp.route('/psp_track')
@login_required
def psp_track():
    """PSP tracking page with enhanced analytics"""
    try:
        from app.models.financial import PspTrack
        from app.services.psp_analytics_service import PspAnalyticsService
        
        # Debug: Check if user is authenticated
        logger.info(f"PSP track accessed by user: {current_user.username if current_user.is_authenticated else 'Not authenticated'}")
        
        # Get PSP tracks
        psp_tracks = PspTrack.query.order_by(PspTrack.date.desc()).all()
        
        logger.info(f"Found {len(psp_tracks)} PSP tracks in database")
        
        if not psp_tracks:
            logger.warning("No PSP tracks found in database")
            return redirect('http://localhost:3000/psp-track')
        
        # Use the new analytics service to calculate comprehensive metrics
        analytics_data = PspAnalyticsService.calculate_psp_metrics(psp_tracks)
        
        # Keep the existing summary data structure for backward compatibility
        daily_data = defaultdict(lambda: {
            'date': None,
            'psps': {},
            'totals': {
                'total_psp': 0,
                'toplam': Decimal('0'),
                'net': Decimal('0'),
                'komisyon': Decimal('0'),
                'deposit': Decimal('0'),
                'cekme': Decimal('0'),
                'withdraw': Decimal('0'),
                'allocation': Decimal('0'),
                'devir': Decimal('0'),
                'carry_over': Decimal('0')
            }
        })
        
        for track in psp_tracks:
            # Initialize date if not set
            if daily_data[track.date]['date'] is None:
                daily_data[track.date]['date'] = track.date
            
            # Calculate amounts with proper null handling
            amount = track.amount or Decimal('0')
            withdraw_amount = track.withdraw or Decimal('0')
            commission_amount = track.commission_amount or Decimal('0')
            
            # Calculate deposit (positive amounts)
            deposit_amount = max(amount, Decimal('0'))
            
            # Calculate net amount
            net_amount = amount - commission_amount
            
            psp_data = {
                'psp_name': track.psp_name,
                'toplam': amount,
                'deposit': deposit_amount,
                'cekme': withdraw_amount,
                'withdraw': withdraw_amount,
                'komisyon': commission_amount,
                'net': net_amount,
                'allocation': track.allocation or Decimal('0'),
                'rollover': track.difference or Decimal('0'),
                'paid': False,
                'transaction_count': 1
            }
            
            daily_data[track.date]['psps'][track.psp_name] = psp_data
            
            # Update totals
            daily_data[track.date]['totals']['total_psp'] = len(daily_data[track.date]['psps'])
            daily_data[track.date]['totals']['toplam'] += psp_data['toplam']
            daily_data[track.date]['totals']['net'] += psp_data['net']
            daily_data[track.date]['totals']['komisyon'] += psp_data['komisyon']
            daily_data[track.date]['totals']['deposit'] += psp_data['deposit']
            daily_data[track.date]['totals']['cekme'] += psp_data['cekme']
            daily_data[track.date]['totals']['withdraw'] += psp_data['withdraw']
            daily_data[track.date]['totals']['allocation'] += psp_data['allocation']
            daily_data[track.date]['totals']['devir'] += psp_data['rollover']
            
            # Carry over logic: only unpaid amounts
            if not psp_data['paid']:
                daily_data[track.date]['totals']['carry_over'] += psp_data['net']
        
        # Convert to list and sort by date
        summary_data = list(daily_data.values())
        summary_data.sort(key=lambda x: x['date'], reverse=True)
        
        logger.info(f"Processed {len(summary_data)} summary data entries")
        if summary_data:
            logger.info(f"First summary entry date: {summary_data[0]['date']}")
            logger.info(f"First summary entry PSPs: {list(summary_data[0]['psps'].keys())}")
        
        # Use the enhanced analytics data
        overview_data = analytics_data
        
        # Get active tab from URL parameter, fallback to ledger if not specified
        active_tab = request.args.get('tab', 'ledger')
        
        logger.info(f"Active tab: {active_tab}")
        
        now = datetime.now()
        
        return redirect('http://localhost:3000/psp-track')
        
    except Exception as e:
        logger.error(f"Error loading PSP track data: {str(e)}")
        flash('Error loading PSP track data.', 'error')
        return redirect('http://localhost:3000/psp-track')

@analytics_bp.route('/analytics/api/psp_details/<psp_name>')
@login_required
def get_psp_details(psp_name):
    """Get detailed PSP data including history"""
    try:
        from app.models.financial import PspTrack
        from app.services.psp_analytics_service import PspAnalyticsService
        
        # Get all tracks for this PSP
        psp_tracks = PspTrack.query.filter_by(psp_name=psp_name).order_by(PspTrack.date.desc()).all()
        
        if not psp_tracks:
            return jsonify({'error': 'PSP not found'}), 404
        
        # Calculate metrics for this PSP
        analytics_data = PspAnalyticsService.calculate_psp_metrics(psp_tracks)
        psp_metrics = analytics_data['psps'].get(psp_name, {})
        
        # Get trend data
        trend_data = PspAnalyticsService.get_psp_trend_data(psp_name, days=60)
        
        # Prepare history data
        history = []
        for track in psp_tracks:
            history.append({
                'date': track.date.isoformat(),
                'amount': float(track.amount or 0),
                'withdraw': float(track.withdraw or 0),
                'commission_rate': float(track.commission_rate or 0),
                'commission_amount': float(track.commission_amount or 0),
                'difference': float(track.difference or 0),
                'net_amount': float((track.amount or 0) - (track.commission_amount or 0)),
                'created_at': track.created_at.isoformat() if track.created_at else None
            })
        
        return jsonify({
            'psp_name': psp_name,
            'metrics': psp_metrics,
            'history': history,
            'trend_data': trend_data
        })
        
    except Exception as e:
        logger.error(f"Error getting PSP details for {psp_name}: {str(e)}")
        return jsonify({'error': 'Failed to get PSP details'}), 500

@analytics_bp.route('/add_employee', methods=['GET', 'POST'])
@login_required
def add_employee():
    """Add new employee"""
    if request.method == 'POST':
        try:
            from app.models.financial import Employee
            
            # Get form data
            name = request.form.get('name', '').strip()
            department = request.form.get('department', '').strip()
            working_status = request.form.get('working_status', 'active')
            company_name = request.form.get('company_name', '').strip()
            stage_name = request.form.get('stage_name', '').strip()
            net_salary = request.form.get('net_salary', '0')
            insurance = request.form.get('insurance') == 'yes'
            deducted_amount = request.form.get('deducted_amount', '0')
            advance = request.form.get('advance', '0')
            usd_rate = request.form.get('usd_rate', '1.0')
            
            # Validate required fields
            if not name:
                flash('Employee name is required.', 'error')
                return redirect('http://localhost:3000/employees/add')
            
            if not department:
                flash('Department is required.', 'error')
                return redirect('http://localhost:3000/employees/add')
            
            if not company_name:
                flash('Company name is required.', 'error')
                return redirect('http://localhost:3000/employees/add')
            
            if not stage_name:
                flash('Stage name is required.', 'error')
                return redirect('http://localhost:3000/employees/add')
            
            # Convert numeric values
            try:
                net_salary = Decimal(net_salary)
                deducted_amount = Decimal(deducted_amount)
                advance = Decimal(advance)
                usd_rate = Decimal(usd_rate)
            except (ValueError, InvalidOperation):
                flash('Invalid numeric values provided.', 'error')
                return redirect('http://localhost:3000/employees/add')
            
            # Create new employee
            employee = Employee()
            employee.name = name
            employee.department = department
            employee.working_status = working_status
            employee.company_name = company_name
            employee.stage_name = stage_name
            employee.net_salary = net_salary
            employee.insurance = insurance
            employee.deducted_amount = deducted_amount
            employee.advance = advance
            employee.usd_rate = usd_rate
            
            # Calculate final values
            employee.update_calculations()
            
            # Save to database
            db.session.add(employee)
            db.session.commit()
            
            flash('Employee added successfully!', 'success')
            return redirect(url_for('analytics.agent_management'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding employee: {str(e)}")
            flash(f'Error adding employee: {str(e)}', 'error')
            return render_template('add_employee.html')
    
    # GET request - show form
    departments = ['Conversion', 'Marketing', 'Retention', 'Research', 'Operation', 'Developers', 'Management']
    return redirect('http://localhost:3000/employees/add')

@analytics_bp.route('/edit_employee/<int:employee_id>', methods=['GET', 'POST'])
@login_required
def edit_employee(employee_id):
    """Edit existing employee"""
    try:
        from app.models.financial import Employee
        
        employee = Employee.query.get_or_404(employee_id)
        
        if request.method == 'POST':
            # Get form data
            name = request.form.get('name', '').strip()
            department = request.form.get('department', '').strip()
            working_status = request.form.get('working_status', 'active')
            company_name = request.form.get('company_name', '').strip()
            stage_name = request.form.get('stage_name', '').strip()
            net_salary = request.form.get('net_salary', '0')
            insurance = request.form.get('insurance') == 'yes'
            deducted_amount = request.form.get('deducted_amount', '0')
            advance = request.form.get('advance', '0')
            usd_rate = request.form.get('usd_rate', '1.0')
            
            # Validate required fields
            if not name:
                flash('Employee name is required.', 'error')
                return redirect(f'http://localhost:3000/employees/edit/{employee_id}')
            
            if not department:
                flash('Department is required.', 'error')
                return redirect(f'http://localhost:3000/employees/edit/{employee_id}')
            
            if not company_name:
                flash('Company name is required.', 'error')
                return redirect(f'http://localhost:3000/employees/edit/{employee_id}')
            
            if not stage_name:
                flash('Stage name is required.', 'error')
                return redirect(f'http://localhost:3000/employees/edit/{employee_id}')
            
            # Convert numeric values
            try:
                net_salary = Decimal(net_salary)
                deducted_amount = Decimal(deducted_amount)
                advance = Decimal(advance)
                usd_rate = Decimal(usd_rate)
            except (ValueError, InvalidOperation):
                flash('Invalid numeric values provided.', 'error')
                return redirect(f'http://localhost:3000/employees/edit/{employee_id}')
            
            # Update employee
            employee.name = name
            employee.department = department
            employee.working_status = working_status
            employee.company_name = company_name
            employee.stage_name = stage_name
            employee.net_salary = net_salary
            employee.insurance = insurance
            employee.deducted_amount = deducted_amount
            employee.advance = advance
            employee.usd_rate = usd_rate
            
            # Calculate final values
            employee.update_calculations()
            
            # Save to database
            db.session.commit()
            
            flash('Employee updated successfully!', 'success')
            return redirect(url_for('analytics.agent_management'))
        
        # GET request - show form
        departments = ['Conversion', 'Marketing', 'Retention', 'Research', 'Operation', 'Developers', 'Management']
        return redirect(f'http://localhost:3000/employees/edit/{employee_id}')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating employee: {str(e)}")
        flash(f'Error updating employee: {str(e)}', 'error')
        return redirect(url_for('analytics.agent_management'))

@analytics_bp.route('/delete_employee/<int:employee_id>', methods=['POST'])
@login_required
def delete_employee(employee_id):
    """Delete employee"""
    try:
        from app.models.financial import Employee
        
        employee = Employee.query.get_or_404(employee_id)
        db.session.delete(employee)
        db.session.commit()
        
        flash('Employee deleted successfully!', 'success')
        return redirect(url_for('analytics.agent_management'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting employee: {str(e)}")
        flash(f'Error deleting employee: {str(e)}', 'error')
        return redirect(url_for('analytics.agent_management'))

@analytics_bp.route('/agent_management')
@login_required
def agent_management():
    """Agent Management - Salary, bonuses and commission calculations"""
    try:
        from app.models.financial import Employee
        
        # Get date range for calculations
        days = request.args.get('days', 30, type=int)
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get all employees from database
        employees = Employee.query.all()
        
        # Get active tab and department filter
        active_tab = request.args.get('tab', 'overview')
        selected_department = request.args.get('department', '')
        
        # Filter employees by department if specified
        if selected_department and selected_department != 'overview':
            employees = [emp for emp in employees if emp.department == selected_department]
        
        # Convert employees to dictionary format
        agents = []
        for employee in employees:
            # Update calculations for each employee
            employee.update_calculations()
            
            agents.append({
                'id': employee.id,
                'name': employee.name,
                'department': employee.department,
                'working_status': employee.working_status,
                'company_name': employee.company_name,
                'stage_name': employee.stage_name,
                'net_salary': float(employee.net_salary),
                'insurance': employee.insurance,
                'deducted_amount': float(employee.deducted_amount),
                'advance': float(employee.advance),
                'final_salary': float(employee.final_salary),
                'usd_rate': float(employee.usd_rate),
                'salary_in_usd': float(employee.salary_in_usd),
                'created_at': employee.created_at
            })
        
        # Calculate department summaries
        departments = {}
        for agent in agents:
            dept = agent['department']
            if dept not in departments:
                departments[dept] = {
                    'total_agents': 0,
                    'total_net_salary': 0,
                    'total_final_salary': 0,
                    'total_deducted': 0,
                    'total_advance': 0,
                    'total_usd_salary': 0,
                    'active_agents': 0,
                    'inactive_agents': 0
                }
            
            departments[dept]['total_agents'] += 1
            departments[dept]['total_net_salary'] += agent['net_salary']
            departments[dept]['total_final_salary'] += agent['final_salary']
            departments[dept]['total_deducted'] += agent['deducted_amount']
            departments[dept]['total_advance'] += agent['advance']
            departments[dept]['total_usd_salary'] += agent['salary_in_usd']
            
            if agent['working_status'] == 'active':
                departments[dept]['active_agents'] += 1
            else:
                departments[dept]['inactive_agents'] += 1
        
        # Calculate overall statistics
        total_agents = len(agents)
        total_net_salary = sum(agent['net_salary'] for agent in agents)
        total_final_salary = sum(agent['final_salary'] for agent in agents)
        total_deducted = sum(agent['deducted_amount'] for agent in agents)
        total_advance = sum(agent['advance'] for agent in agents)
        total_usd_salary = sum(agent['salary_in_usd'] for agent in agents)
        active_agents = sum(1 for agent in agents if agent['working_status'] == 'active')
        inactive_agents = sum(1 for agent in agents if agent['working_status'] == 'inactive')
        
        # Available departments for tabs
        available_departments = ['overview', 'Conversion', 'Marketing', 'Retention', 'Research', 'Operation', 'Developers', 'Management']
        
        return redirect('http://localhost:3000/agent-management')
        
    except Exception as e:
        logger.error(f"Error loading agent management data: {str(e)}")
        flash('Error loading agent management data.', 'error')
        return redirect('http://localhost:3000/agent-management')

@analytics_bp.route('/view_psp_track/<psp>/<date>')
@login_required
def view_psp_track(psp, date):
    """View PSP track entry details"""
    try:
        from datetime import datetime
        from urllib.parse import unquote
        
        # URL decode the PSP name to handle special characters like #
        psp_decoded = unquote(psp)
        
        # Log the request for debugging
        logger.info(f"View PSP track request: PSP={psp} (decoded: {psp_decoded}), Date={date}")
        
        # Validate date format
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError as e:
            logger.error(f"Invalid date format: {date} - {str(e)}")
            flash('Invalid date format.', 'error')
            return redirect(url_for('analytics.psp_track'))
        
        # Get the PSP track entry using the decoded name
        entry = PspTrack.query.filter_by(
            psp_name=psp_decoded,
            date=date_obj
        ).first()
        
        if not entry:
            logger.warning(f"PSP track entry not found: PSP={psp_decoded}, Date={date}")
            flash(f'PSP track entry not found for {psp_decoded} on {date}.', 'error')
            return redirect(url_for('analytics.psp_track'))
        
        logger.info(f"Successfully found PSP track entry: {entry.psp_name} on {entry.date}")
        
        return redirect('http://localhost:3000/psp-track/view')
        
    except Exception as e:
        logger.error(f"Error viewing PSP track: {str(e)}")
        flash('Error viewing PSP track entry.', 'error')
        return redirect(url_for('analytics.psp_track'))



@analytics_bp.route('/add_psp_track', methods=['GET', 'POST'])
@login_required
def add_psp_track():
    """Add new PSP track entry"""
    try:
        from datetime import datetime
        from decimal import Decimal
        
        if request.method == 'POST':
            # Get form data
            psp_name = request.form.get('psp_name', '').strip()
            date_str = request.form.get('date', '')
            amount = request.form.get('deposit', '0')
            withdraw = request.form.get('withdraw', '0')
            commission_amount = request.form.get('komisyon', '0')
            difference = request.form.get('difference', '0')
            
            # Validate required fields
            if not psp_name or not date_str:
                flash('PSP name and date are required.', 'error')
                return redirect(url_for('analytics.add_psp_track'))
            
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                amount_decimal = Decimal(str(amount))
                withdraw_decimal = Decimal(str(withdraw))
                commission_decimal = Decimal(str(commission_amount))
                difference_decimal = Decimal(str(difference))
            except (ValueError, InvalidOperation) as e:
                flash(f'Invalid data format: {str(e)}', 'error')
                return redirect(url_for('analytics.add_psp_track'))
            
            # Check if entry already exists
            existing_entry = PspTrack.query.filter_by(
                psp_name=psp_name,
                date=date_obj
            ).first()
            
            if existing_entry:
                flash('PSP track entry already exists for this date and PSP.', 'error')
                return redirect(url_for('analytics.add_psp_track'))
            
            # Create new entry
            new_entry = PspTrack(
                psp_name=psp_name,
                date=date_obj,
                amount=amount_decimal,
                withdraw=withdraw_decimal,
                commission_amount=commission_decimal,
                difference=difference_decimal
            )
            
            db.session.add(new_entry)
            db.session.commit()
            
            flash('PSP track entry added successfully.', 'success')
            return redirect(url_for('analytics.psp_track'))
        
        # GET request - show form
        psps = Option.query.filter_by(field_name='psp').all()
        return redirect('http://localhost:3000/psp-track/add')
        
    except Exception as e:
        logger.error(f"Error adding PSP track: {str(e)}")
        flash('Error adding PSP track entry.', 'error')
        return redirect(url_for('analytics.psp_track'))



@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    pass

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    pass

@socketio.on('join_analytics')
def handle_join_analytics(data):
    """Join analytics room for real-time updates"""
    room = 'analytics'
    join_room(room)
    # Client joined analytics room

@socketio.on('request_analytics')
def handle_analytics_request(data):
    """Handle analytics data request via WebSocket"""
    try:
        days = data.get('days', 30)
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get recent transactions
        transactions = Transaction.query.filter(
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).all()
        
        # Calculate real-time metrics
        total_amount = sum(t.amount for t in transactions)
        total_commission = sum(t.commission for t in transactions)
        
        # Emit real-time data
        emit('analytics_update', {
            'total_amount': float(total_amount),
            'total_commission': float(total_commission),
            'transaction_count': len(transactions),
            'timestamp': datetime.now().isoformat()
        }, room='analytics')
        
    except Exception as e:
        logger.error(f"Error in WebSocket analytics: {str(e)}")
        emit('analytics_error', {'error': 'Failed to load analytics data'})

@socketio.on('join_dashboard')
def handle_join_dashboard(data):
    """Join dashboard room for real-time updates"""
    room = 'dashboard'
    join_room(room)
    # Client joined dashboard room

@socketio.on('request_dashboard_data')
def handle_dashboard_request(data):
    """Handle dashboard data request via WebSocket"""
    try:
        days = data.get('days', 30)
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get recent transactions
        transactions = Transaction.query.filter(
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).all()
        
        # Calculate dashboard metrics
        total_amount = sum(t.amount for t in transactions)
        total_commission = sum(t.commission for t in transactions)
        total_net = sum(t.net_amount for t in transactions)
        
        # Get today's transactions
        today = date.today()
        today_transactions = [t for t in transactions if t.date == today]
        today_amount = sum(t.amount for t in today_transactions)
        today_commission = sum(t.commission for t in today_transactions)
        
        # Emit real-time data
        emit('dashboard_update', {
            'total_amount': float(total_amount),
            'total_commission': float(total_commission),
            'total_net': float(total_net),
            'transaction_count': len(transactions),
            'today_amount': float(today_amount),
            'today_commission': float(today_commission),
            'today_count': len(today_transactions),
            'timestamp': datetime.now().isoformat()
        }, room='dashboard')
        
    except Exception as e:
        logger.error(f"Error in WebSocket dashboard: {str(e)}")
        emit('dashboard_error', {'error': 'Failed to load dashboard data'})

def broadcast_analytics_update():
    """Broadcast analytics update to all connected clients"""
    try:
        # Get recent data
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        transactions = Transaction.query.filter(
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).all()
        
        total_amount = sum(t.amount for t in transactions)
        total_commission = sum(t.commission for t in transactions)
        
        # Broadcast to all rooms
        socketio.emit('analytics_broadcast', {
            'total_amount': float(total_amount),
            'total_commission': float(total_commission),
            'transaction_count': len(transactions),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error broadcasting analytics: {str(e)}")

# Add missing routes for navigation
@analytics_bp.route('/reports')
@login_required
def reports():
    """Reports page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading reports: {str(e)}")
        flash('Error loading reports.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/forecasting')
@login_required
def forecasting():
    """Forecasting page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading forecasting: {str(e)}")
        flash('Error loading forecasting.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/risk-management')
@login_required
def risk_management():
    """Risk management page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading risk management: {str(e)}")
        flash('Error loading risk management.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/compliance')
@login_required
def compliance():
    """Compliance page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading compliance: {str(e)}")
        flash('Error loading compliance.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/audit')
@login_required
def audit():
    """Audit page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading audit: {str(e)}")
        flash('Error loading audit.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/alerts')
@login_required
def alerts():
    """Alerts page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading alerts: {str(e)}")
        flash('Error loading alerts.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/integrations')
@login_required
def integrations():
    """Integrations page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading integrations: {str(e)}")
        flash('Error loading integrations.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/api')
@login_required
def api():
    """API page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading API: {str(e)}")
        flash('Error loading API.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/webhooks')
@login_required
def webhooks():
    """Webhooks page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading webhooks: {str(e)}")
        flash('Error loading webhooks.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/automation')
@login_required
def automation():
    """Automation page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading automation: {str(e)}")
        flash('Error loading automation.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/scheduling')
@login_required
def scheduling():
    """Scheduling page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading scheduling: {str(e)}")
        flash('Error loading scheduling.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/backup')
@login_required
def backup():
    """Backup page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading backup: {str(e)}")
        flash('Error loading backup.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/restore')
@login_required
def restore():
    """Restore page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading restore: {str(e)}")
        flash('Error loading restore.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/security')
@login_required
def security():
    """Security page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading security: {str(e)}")
        flash('Error loading security.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/monitoring')
@login_required
def monitoring():
    """Monitoring page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading monitoring: {str(e)}")
        flash('Error loading monitoring.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/performance')
@login_required
def performance():
    """Performance page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading performance: {str(e)}")
        flash('Error loading performance.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/logs')
@login_required
def logs():
    """Logs page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading logs: {str(e)}")
        flash('Error loading logs.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/support')
@login_required
def support():
    """Support page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading support: {str(e)}")
        flash('Error loading support.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/documentation')
@login_required
def documentation():
    """Documentation page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading documentation: {str(e)}")
        flash('Error loading documentation.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/training')
@login_required
def training():
    """Training page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading training: {str(e)}")
        flash('Error loading training.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/updates')
@login_required
def updates():
    """Updates page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading updates: {str(e)}")
        flash('Error loading updates.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/users')
@login_required
def users():
    """Users page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading users: {str(e)}")
        flash('Error loading users.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/roles')
@login_required
def roles():
    """Roles page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading roles: {str(e)}")
        flash('Error loading roles.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/permissions')
@login_required
def permissions():
    """Permissions page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading permissions: {str(e)}")
        flash('Error loading permissions.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/notifications')
@login_required
def notifications():
    """Notifications page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading notifications: {str(e)}")
        flash('Error loading notifications.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/templates')
@login_required
def templates():
    """Templates page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading templates: {str(e)}")
        flash('Error loading templates.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/workflows')
@login_required
def workflows():
    """Workflows page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading workflows: {str(e)}")
        flash('Error loading workflows.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/approvals')
@login_required
def approvals():
    """Approvals page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading approvals: {str(e)}")
        flash('Error loading approvals.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/feedback')
@login_required
def feedback():
    """Feedback page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading feedback: {str(e)}")
        flash('Error loading feedback.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/help')
@login_required
def help():
    """Help page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading help: {str(e)}")
        flash('Error loading help.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/about')
@login_required
def about():
    """About page"""
    try:
        return redirect('http://localhost:3000/analytics')
    except Exception as e:
        logger.error(f"Error loading about: {str(e)}")
        flash('Error loading about.', 'error')
        return redirect(url_for('analytics.dashboard'))

@analytics_bp.route('/api/analytics/track', methods=['POST'])
@login_required
def track_analytics():
    """Track analytics events"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        event_type = data.get('type')
        event_data = data.get('data', {})
        
        # Log the analytics event
        logger.info(f"Analytics event: {event_type} - {event_data}")
        
        # In a production environment, you would store this in a database
        # For now, we'll just log it and return success
        
        return jsonify({
            'success': True,
            'message': 'Event tracked successfully',
            'event_type': event_type,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error tracking analytics: {str(e)}")
        return jsonify({'error': 'Failed to track analytics'}), 500

@analytics_bp.route('/test_csrf')
@login_required
def test_csrf():
    """Test CSRF token generation"""
    from flask_wtf.csrf import generate_csrf
    token = generate_csrf()
    return f"CSRF Token: {token}"