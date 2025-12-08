"""
Authentication routes blueprint
"""
from flask import Blueprint, request, redirect, url_for, flash, session as flask_session, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
from werkzeug.security import check_password_hash
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, urljoin
import uuid
import re
import logging
import os

from app import db, limiter
from app.models.user import User
from app.models.audit import LoginAttempt, UserSession
from app.utils.unified_error_handler import (
    handle_errors, handle_api_errors, validate_request_data,
    PipLineError, ValidationError, AuthenticationError, AuthorizationError,
    DatabaseError, log_error, safe_execute
)
from app.utils.unified_logger import get_logger, log_function_call as performance_log

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__)

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=80, message='Username must be between 3 and 80 characters')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=12, message='Password must be at least 12 characters long')
    ])
    remember_me = StringField('Remember Me')  # Will be handled as checkbox
    submit = SubmitField('Login')

def validate_password_strength(password):
    """Validate password strength according to security requirements"""
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Password must contain at least one special character"
    return True, "Password is strong"

def check_account_lockout(user):
    """Check if user account is locked"""
    if user.account_locked_until and user.account_locked_until > datetime.now(timezone.utc):
        return True
    return False

def record_login_attempt(username, ip_address, success, failure_reason=None):
    """Record login attempt for security monitoring"""
    try:
        attempt = LoginAttempt(
            username=username,
            ip_address=ip_address,
            user_agent=request.headers.get('User-Agent', ''),
            success=success,
            failure_reason=failure_reason
        )
        db.session.add(attempt)
        db.session.commit()
    except Exception as e:
        logger.error(f"Failed to record login attempt for {username}: {str(e)}")
        try:
            db.session.rollback()
        except:
            pass  # Ignore rollback errors

def handle_failed_login(user):
    """Handle failed login attempt"""
    try:
        # Ensure failed_login_attempts is initialized
        if user.failed_login_attempts is None:
            user.failed_login_attempts = 0
        
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            # Lock account for 30 minutes
            user.account_locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()
    except Exception as e:
        logger.error(f"Error in handle_failed_login for user {user.username}: {str(e)}")
        db.session.rollback()
        raise

def reset_failed_attempts(user):
    """Reset failed login attempts on successful login"""
    try:
        user.failed_login_attempts = 0
        user.account_locked_until = None
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()
    except Exception as e:
        logger.error(f"Error in reset_failed_attempts for user {user.username}: {str(e)}")
        db.session.rollback()
        raise

def url_is_safe(target):
    """Check if the target URL is safe for redirect"""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("100 per minute")  # Temporarily increased rate limit
@handle_errors
@performance_log
def login():
    """Handle user login"""
    # For GET requests, serve React frontend
    if request.method == 'GET':
        from flask import send_from_directory
        frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontend', 'dist')
        if not os.path.exists(frontend_dist):
            frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontend', 'dist_prod')
        index_path = os.path.join(frontend_dist, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(frontend_dist, 'index.html')
    
    # Clear any existing flash messages to prevent conflicts
    if current_user.is_authenticated:
        return redirect(url_for('analytics.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data
        ip_address = request.remote_addr
        
        try:
            user = User.query.filter_by(username=username).first()
            
            if user and user.is_active:
                # Check if account is locked - TEMPORARILY DISABLED
                # if check_account_lockout(user):
                #     lockout_time = user.account_locked_until.strftime('%H:%M:%S')
                #     flash(f'Account is locked until {lockout_time}. Please try again later.', 'error')
                #     record_login_attempt(username, ip_address, success=False, failure_reason='account_locked')
                #     from app.utils.frontend_helper import serve_frontend
                #     return serve_frontend('/login')
                
                if check_password_hash(user.password, password):
                    # Check if remember me is enabled
                    remember_me = request.form.get('remember_me') == 'on'
                    
                    # Log the remember me status for debugging
                    logger.info(f"Login attempt for user {username}: remember_me={remember_me}")
                    
                    # Successful login
                    login_user(user, remember=remember_me)
                    reset_failed_attempts(user)
                    record_login_attempt(username, ip_address, success=True)
                    
                    # Create session token for security
                    session_token = str(uuid.uuid4())
                    flask_session['session_token'] = session_token
                    
                    # Store session in database
                    user_session = UserSession(
                        user_id=user.id,
                        session_token=session_token,
                        ip_address=ip_address,
                        user_agent=request.headers.get('User-Agent', '')
                    )
                    db.session.add(user_session)
                    db.session.commit()
                    
                    # Use a more specific success message
                    flash(f'Welcome back, {user.username}!', 'success')
                    
                    # Handle next parameter for redirect after login
                    next_page = request.args.get('next')
                    if next_page and url_is_safe(next_page):
                        # Store the intended destination in session
                        flask_session['intended_destination'] = next_page
                        return redirect(next_page)
                    else:
                        # Check if user has a preferred landing page
                        from app.models.config import UserSettings
                        user_settings = UserSettings.query.filter_by(user_id=user.id).first()
                        if user_settings and user_settings.landing_page:
                            if user_settings.landing_page == 'dashboard':
                                return redirect(url_for('analytics.dashboard'))
                            elif user_settings.landing_page == 'transactions':
                                return redirect(url_for('transactions.clients'))
                            elif user_settings.landing_page == 'summary':
                                return redirect(url_for('analytics.summary'))
                            elif user_settings.landing_page == 'analytics':
                                return redirect(url_for('analytics.analytics'))
                        
                        # Default to dashboard
                        return redirect(url_for('analytics.dashboard'))
                else:
                    # Failed login - wrong password
                    try:
                        # handle_failed_login(user)  # Temporarily disabled
                        record_login_attempt(username, ip_address, success=False, failure_reason='invalid_credentials')
                    except Exception as e:
                        logger.error(f"Error handling failed login for user {username}: {str(e)}")
                        db.session.rollback()
                        record_login_attempt(username, ip_address, success=False, failure_reason='invalid_credentials')
                    
                    flash('⚠️ Invalid credentials. Please verify your username and password and try again.', 'error')
            else:
                # User not found
                record_login_attempt(username, ip_address, success=False, failure_reason='user_not_found')
                flash('⚠️ Invalid credentials. Please verify your username and password and try again.', 'error')
                
        except Exception as e:
            logger.error(f"Error during login process for username {username}: {str(e)}")
            db.session.rollback()
            record_login_attempt(username, ip_address, success=False, failure_reason='system_error')
            flash('An error occurred during login. Please try again.', 'error')
    elif request.method == 'POST':
        # Handle form validation errors - treat them as authentication failures
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        ip_address = request.remote_addr
        
        # Record failed attempt due to validation error
        record_login_attempt(username, ip_address, success=False, failure_reason='validation_error')
        flash('⚠️ Invalid credentials. Please verify your username and password and try again.', 'error')
    
    # Serve React frontend for login page (SPA routing)
    from app.utils.frontend_helper import serve_frontend
    return serve_frontend('/login')

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    # Mark current session as inactive
    token = flask_session.get('session_token')
    if token:
        user_session = UserSession.query.filter_by(
            session_token=token, 
            is_active=True
        ).first()
        if user_session:
            user_session.is_active = False
            db.session.commit()
    
    # Clear session
    flask_session.pop('session_token', None)
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout_page')
def logout_page():
    """Show logout confirmation page"""
    from app.utils.frontend_helper import serve_frontend
    return serve_frontend('/logout')

@auth_bp.route('/logout_session/<int:session_id>', methods=['POST'])
@login_required
def logout_session(session_id):
    """Logout from a specific session"""
    session = UserSession.query.filter_by(
        id=session_id,
        user_id=current_user.id,
        is_active=True
    ).first()
    
    if session:
        session.is_active = False
        db.session.commit()
        flash('Session logged out successfully.', 'success')
    else:
        flash('Session not found or already inactive.', 'error')
    
    return redirect(url_for('account_security'))

@auth_bp.route('/account/security')
@login_required
def account_security():
    """Show account security page"""
    # Get user's active sessions
    active_sessions = UserSession.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).order_by(UserSession.created_at.desc()).all()
    
    from app.utils.frontend_helper import serve_frontend
    return serve_frontend('/account/security')

@auth_bp.route('/account/force_logout_all', methods=['POST'])
@login_required
def force_logout_all():
    """Force logout from all sessions except current"""
    current_token = flask_session.get('session_token')
    
    # Deactivate all sessions except current
    UserSession.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).filter(UserSession.session_token != current_token).update({
        'is_active': False
    })
    
    db.session.commit()
    flash('All other sessions have been logged out.', 'success')
    return redirect(url_for('auth.account_security'))

@auth_bp.route('/account/unlock', methods=['POST'])
@login_required
def unlock_account():
    """Unlock user account (admin only)"""
    if current_user.role != 'admin':
        flash('Only administrators can unlock accounts.', 'error')
        return redirect(url_for('auth.account_security'))
    
    user_id = request.form.get('user_id')
    if not user_id:
        flash('User ID is required.', 'error')
        return redirect(url_for('auth.account_security'))
    
    user = User.query.get(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('auth.account_security'))
    
    user.failed_login_attempts = 0
    user.account_locked_until = None
    db.session.commit()
    
    flash(f'Account for user {user.username} has been unlocked.', 'success')
    return redirect(url_for('auth.account_security'))

@auth_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not all([current_password, new_password, confirm_password]):
        flash('All password fields are required.', 'error')
        return redirect(url_for('auth.account_security'))
    
    if new_password != confirm_password:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('auth.account_security'))
    
    # Validate current password
    if not check_password_hash(current_user.password, current_password):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('auth.account_security'))
    
    # Validate new password strength
    is_valid, message = validate_password_strength(new_password)
    if not is_valid:
        flash(message, 'error')
        return redirect(url_for('auth.account_security'))
    
    # Update password
    from werkzeug.security import generate_password_hash
    current_user.password = generate_password_hash(new_password)
    current_user.password_changed_at = datetime.now(timezone.utc)
    db.session.commit()
    
    flash('Password changed successfully.', 'success')
    return redirect(url_for('auth.account_security'))

@auth_bp.route('/upload_profile_picture', methods=['POST'])
@login_required
def upload_profile_picture():
    """Upload user profile picture"""
    if 'profile_picture' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('auth.account_security'))
    
    file = request.files['profile_picture']
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('auth.account_security'))
    
    # Validate file type
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    if not file.filename.lower().endswith(tuple('.' + ext for ext in allowed_extensions)):
        flash('Invalid file type. Please upload PNG, JPG, JPEG, or GIF.', 'error')
        return redirect(url_for('auth.account_security'))
    
    # Generate unique filename
    import uuid
    filename = f"user_{current_user.id}_{uuid.uuid4().hex}.{file.filename.rsplit('.', 1)[1].lower()}"
    
    # Save file
    from flask import current_app
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(upload_path)
    
    # Update user profile
    current_user.profile_picture = filename
    db.session.commit()
    
    flash('Profile picture updated successfully.', 'success')
    return redirect(url_for('auth.account_security')) 