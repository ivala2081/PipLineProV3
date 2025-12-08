"""
Security Management API Endpoints
Handles session management, audit logs, login attempts, and security settings
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models.user import User
from app.models.audit import AuditLog, UserSession, LoginAttempt
from datetime import datetime, timedelta, timezone
from sqlalchemy import desc, func, and_
import json

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        if current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

security_bp = Blueprint('security', __name__)


@security_bp.route('/sessions', methods=['GET'])
@login_required
@admin_required
def get_active_sessions():
    """Get all active user sessions"""
    try:
        # Get query parameters
        user_id = request.args.get('user_id', type=int)
        is_active = request.args.get('is_active', 'true').lower() == 'true'
        limit = request.args.get('limit', 100, type=int)
        
        # Build query
        query = UserSession.query
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        if is_active is not None:
            query = query.filter_by(is_active=is_active)
        
        sessions = query.order_by(desc(UserSession.last_active)).limit(limit).all()
        
        # Join with user data
        session_data = []
        for session in sessions:
            user = User.query.get(session.user_id)
            session_dict = session.to_dict()
            session_dict['username'] = user.username if user else 'Unknown'
            session_dict['role'] = user.role if user else 'unknown'
            session_data.append(session_dict)
        
        return jsonify({
            'success': True,
            'sessions': session_data,
            'count': len(session_data)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@security_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
@login_required
@admin_required
def terminate_session(session_id):
    """Terminate a specific session (force logout)"""
    try:
        session = UserSession.query.get(session_id)
        
        if not session:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404
        
        session.is_active = False
        db.session.commit()
        
        # Log the action
        audit = AuditLog(
            user_id=current_user.id,
            action='DELETE',
            table_name='user_session',
            record_id=session_id,
            ip_address=request.remote_addr,
            new_values=json.dumps({'terminated_by': current_user.username})
        )
        db.session.add(audit)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Session terminated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@security_bp.route('/sessions/user/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def terminate_user_sessions(user_id):
    """Terminate all sessions for a specific user"""
    try:
        sessions = UserSession.query.filter_by(user_id=user_id, is_active=True).all()
        
        count = 0
        for session in sessions:
            session.is_active = False
            count += 1
        
        db.session.commit()
        
        # Log the action
        audit = AuditLog(
            user_id=current_user.id,
            action='DELETE',
            table_name='user_session',
            record_id=user_id,
            ip_address=request.remote_addr,
            new_values=json.dumps({'terminated_count': count, 'terminated_by': current_user.username})
        )
        db.session.add(audit)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{count} sessions terminated',
            'count': count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@security_bp.route('/audit-logs', methods=['GET'])
@login_required
@admin_required
def get_audit_logs():
    """Get audit logs with filtering"""
    try:
        # Get query parameters
        user_id = request.args.get('user_id', type=int)
        action = request.args.get('action')
        table_name = request.args.get('table_name')
        days = request.args.get('days', 30, type=int)
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = AuditLog.query
        
        # Filter by date range
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        query = query.filter(AuditLog.timestamp >= start_date)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        if action:
            query = query.filter_by(action=action)
        
        if table_name:
            query = query.filter_by(table_name=table_name)
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        logs = query.order_by(desc(AuditLog.timestamp)).offset(offset).limit(limit).all()
        
        # Join with user data
        log_data = []
        for log in logs:
            user = User.query.get(log.user_id)
            log_dict = log.to_dict()
            log_dict['username'] = user.username if user else 'Unknown'
            log_data.append(log_dict)
        
        return jsonify({
            'success': True,
            'logs': log_data,
            'count': len(log_data),
            'total': total_count,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@security_bp.route('/login-attempts', methods=['GET'])
@login_required
@admin_required
def get_login_attempts():
    """Get login attempts with filtering"""
    try:
        # Get query parameters
        username = request.args.get('username')
        ip_address = request.args.get('ip_address')
        success = request.args.get('success')
        days = request.args.get('days', 7, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        # Build query
        query = LoginAttempt.query
        
        # Filter by date range
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        query = query.filter(LoginAttempt.timestamp >= start_date)
        
        if username:
            query = query.filter_by(username=username)
        
        if ip_address:
            query = query.filter_by(ip_address=ip_address)
        
        if success is not None:
            query = query.filter_by(success=success.lower() == 'true')
        
        attempts = query.order_by(desc(LoginAttempt.timestamp)).limit(limit).all()
        
        return jsonify({
            'success': True,
            'attempts': [attempt.to_dict() for attempt in attempts],
            'count': len(attempts)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@security_bp.route('/login-attempts/stats', methods=['GET'])
@login_required
@admin_required
def get_login_stats():
    """Get login attempt statistics"""
    try:
        days = request.args.get('days', 7, type=int)
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Total attempts
        total_attempts = LoginAttempt.query.filter(
            LoginAttempt.timestamp >= start_date
        ).count()
        
        # Failed attempts
        failed_attempts = LoginAttempt.query.filter(
            and_(
                LoginAttempt.timestamp >= start_date,
                LoginAttempt.success == False
            )
        ).count()
        
        # Unique IPs with failures
        failed_ips = db.session.query(
            func.count(func.distinct(LoginAttempt.ip_address))
        ).filter(
            and_(
                LoginAttempt.timestamp >= start_date,
                LoginAttempt.success == False
            )
        ).scalar()
        
        # Recently locked accounts
        locked_accounts = User.query.filter(
            User.account_locked_until > datetime.now(timezone.utc)
        ).count()
        
        # Top failed IPs
        top_failed_ips = db.session.query(
            LoginAttempt.ip_address,
            func.count(LoginAttempt.id).label('count')
        ).filter(
            and_(
                LoginAttempt.timestamp >= start_date,
                LoginAttempt.success == False
            )
        ).group_by(LoginAttempt.ip_address).order_by(
            desc('count')
        ).limit(10).all()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_attempts': total_attempts,
                'failed_attempts': failed_attempts,
                'success_rate': round((total_attempts - failed_attempts) / total_attempts * 100, 2) if total_attempts > 0 else 100,
                'failed_ips': failed_ips,
                'locked_accounts': locked_accounts,
                'top_failed_ips': [
                    {'ip': ip, 'count': count}
                    for ip, count in top_failed_ips
                ]
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@security_bp.route('/users/<int:user_id>/unlock', methods=['POST'])
@login_required
@admin_required
def unlock_user_account(user_id):
    """Unlock a locked user account"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        user.reset_failed_attempts()
        db.session.commit()
        
        # Log the action
        audit = AuditLog(
            user_id=current_user.id,
            action='UPDATE',
            table_name='user',
            record_id=user_id,
            ip_address=request.remote_addr,
            new_values=json.dumps({
                'unlocked_by': current_user.username,
                'action': 'account_unlocked'
            })
        )
        db.session.add(audit)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Account {user.username} unlocked successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@security_bp.route('/security-overview', methods=['GET'])
@login_required
@admin_required
def get_security_overview():
    """Get overall security dashboard data"""
    try:
        now = datetime.now(timezone.utc)
        
        # Active sessions
        active_sessions = UserSession.query.filter_by(is_active=True).count()
        
        # Recent failed logins (last 24 hours)
        yesterday = now - timedelta(days=1)
        recent_failures = LoginAttempt.query.filter(
            and_(
                LoginAttempt.timestamp >= yesterday,
                LoginAttempt.success == False
            )
        ).count()
        
        # Locked accounts
        locked_accounts = User.query.filter(
            User.account_locked_until > now
        ).count()
        
        # Recent audit activity (last 24 hours)
        recent_audits = AuditLog.query.filter(
            AuditLog.timestamp >= yesterday
        ).count()
        
        # Critical actions (last 7 days)
        week_ago = now - timedelta(days=7)
        critical_actions = AuditLog.query.filter(
            and_(
                AuditLog.timestamp >= week_ago,
                AuditLog.action == 'DELETE'
            )
        ).count()
        
        return jsonify({
            'success': True,
            'overview': {
                'active_sessions': active_sessions,
                'recent_failed_logins': recent_failures,
                'locked_accounts': locked_accounts,
                'recent_audit_entries': recent_audits,
                'critical_actions_week': critical_actions
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

