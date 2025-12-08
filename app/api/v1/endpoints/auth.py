"""
API Authentication endpoints for React frontend
"""
from flask import Blueprint, request, jsonify, session, current_app
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import check_password_hash
from datetime import datetime, timezone, timedelta
import uuid
import logging

from app import db, limiter, csrf
from app.models.user import User
from app.models.audit import LoginAttempt, UserSession
from app.utils.unified_error_handler import handle_errors, AuthenticationError
from app.utils.unified_logger import get_logger

logger = get_logger(__name__)

auth_api = Blueprint('auth_api', __name__)

# Exempt auth API endpoints from CSRF protection
csrf.exempt(auth_api)

def check_account_lockout(user):
    """Check if user account is locked"""
    if user.account_locked_until:
        # Handle both timezone-aware and timezone-naive datetimes
        lockout_time = user.account_locked_until
        if lockout_time.tzinfo is None:
            # Timezone-naive, assume UTC
            lockout_time = lockout_time.replace(tzinfo=timezone.utc)
        
        if lockout_time > datetime.now(timezone.utc):
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
            pass

def handle_failed_login(user):
    """Handle failed login attempt"""
    try:
        if user.failed_login_attempts is None:
            user.failed_login_attempts = 0
        
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
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

@auth_api.route('/csrf-token', methods=['GET'])
def get_csrf_token():
    """Get CSRF token for API requests with enhanced session handling"""
    try:
        # Ensure user is authenticated
        if not current_user.is_authenticated:
            return jsonify({
                'error': 'Authentication required'
            }), 401
        
        # Clean up session to prevent cookie size issues
        # Remove any unnecessary session data that might bloat the cookie
        # BUT preserve authentication-related keys
        keys_to_remove = [
            'recent_csrf_tokens',
            'api_csrf_token',
        ]
        for key in keys_to_remove:
            if key in session:
                del session[key]
        
        # Generate a secure token using Flask-WTF's built-in token generation
        # Flask-WTF automatically stores the token in the session, so we don't need to store it manually
        from flask_wtf.csrf import generate_csrf
        token = generate_csrf()
        
        # Clean up flash messages if they exist (they can accumulate)
        # But only if there are too many (more than 10)
        if '_flashes' in session:
            flashes = session.get('_flashes', [])
            if isinstance(flashes, list) and len(flashes) > 10:
                # Keep only the last 5 flash messages
                session['_flashes'] = flashes[-5:]
        
        # Don't remove other session keys - they might be needed for authentication
        # Flask-Login and Flask-Session use various internal keys that start with '_'
        
        # Mark session as modified to ensure changes are saved
        session.modified = True
        
        logger.debug(f"CSRF token generated for user {current_user.username}: {token[:20]}...")
        
        return jsonify({
            'csrf_token': token,
            'message': 'CSRF token generated successfully',
            'user_id': current_user.id,
            'token_length': len(token)
        }), 200
    except Exception as e:
        logger.error(f"Error generating CSRF token: {str(e)}")
        return jsonify({
            'error': 'Failed to generate CSRF token',
            'message': str(e)
        }), 500

@auth_api.route('/check', methods=['GET'])
@limiter.limit("120 per minute, 5000 per hour")  # Increased - lightweight session checks need higher limits
def check_auth():
    """Check if user is authenticated - with enhanced error handling"""
    try:
        # Safe access to current_user
        try:
            is_authenticated = current_user.is_authenticated if hasattr(current_user, 'is_authenticated') else False
        except Exception as user_error:
            logger.warning(f"Error accessing current_user: {str(user_error)}")
            is_authenticated = False
        
        # Add debugging information (only in debug mode)
        if current_app.config.get('DEBUG'):
            logger.debug(f"Auth check - current_user: {current_user}")
            logger.debug(f"Auth check - is_authenticated: {is_authenticated}")
            logger.debug(f"Auth check - session keys: {list(session.keys())}")
        
        if is_authenticated:
            # Check session timeout - with safe error handling
            try:
                session_timeout = current_app.config.get('PERMANENT_SESSION_LIFETIME')
                if session_timeout and session.get('_session_created'):
                    session_created = session.get('_session_created')
                    try:
                        if isinstance(session_created, str):
                            # Parse string datetime
                            session_created = datetime.fromisoformat(session_created.replace('Z', '+00:00'))
                        elif not isinstance(session_created, datetime):
                            # If not a datetime object, skip timeout check
                            session_created = None
                        
                        if session_created:
                            session_age = datetime.now(timezone.utc) - session_created
                            if session_age > session_timeout:
                                # Session expired, logout user
                                try:
                                    logout_user()
                                except:
                                    pass  # Ignore logout errors
                                return jsonify({
                                    'authenticated': False,
                                    'message': 'Session expired'
                                }), 401
                    except (ValueError, TypeError) as parse_error:
                        logger.warning(f"Error parsing session created time: {str(parse_error)}")
                        # Continue with normal authentication if parsing fails
            except Exception as timeout_error:
                logger.warning(f"Session timeout check failed: {str(timeout_error)}")
                # Continue with normal authentication if timeout check fails
            
            # Serialize user - with fallback to basic info
            try:
                user_dict = current_user.to_dict()
            except Exception as serialize_error:
                logger.error(f"Error serializing user: {str(serialize_error)}")
                # Return basic auth info if user serialization fails
                try:
                    user_dict = {
                        'id': getattr(current_user, 'id', None),
                        'username': getattr(current_user, 'username', 'unknown'),
                        'role': getattr(current_user, 'role', 'user')
                    }
                except Exception as attr_error:
                    logger.error(f"Error accessing user attributes: {str(attr_error)}")
                    # Last resort: return minimal info
                    return jsonify({
                        'authenticated': False,
                        'message': 'User data error',
                        'error': 'Failed to access user information'
                    }), 500
            
            return jsonify({
                'authenticated': True,
                'user': user_dict,
                'message': 'User is authenticated'
            }), 200
        else:
            # User is not authenticated - normal case, not an error
            return jsonify({
                'authenticated': False,
                'message': 'User is not authenticated'
            }), 401
    except Exception as e:
        logger.error(f"Unexpected error in auth check: {str(e)}", exc_info=True)
        # Return JSON response even on error - don't expose internal details in production
        return jsonify({
            'authenticated': False,
            'error': 'Authentication check failed',
            'message': str(e) if current_app.config.get('DEBUG') else 'Internal server error'
        }), 500


@auth_api.route('/login', methods=['POST'])
@limiter.limit("10 per minute, 20 per hour")  # Re-enabled with stricter limits for security
@handle_errors
def api_login():
    """Handle API login"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Invalid request data'
            }), 400

        username = data.get('username', '').strip()
        password = data.get('password', '')
        remember_me = data.get('remember_me', False)

        if not username or not password:
            return jsonify({
                'error': 'Username and password are required'
            }), 400

        ip_address = request.remote_addr

        # Find user - with explicit error handling
        try:
            logger.info(f"Attempting to query user: {username}")
            user = User.query.filter_by(username=username).first()
            logger.info(f"User query successful: {user is not None}")
        except Exception as db_error:
            logger.error(f"Database error during user query: {str(db_error)}", exc_info=True)
            logger.error(f"Database URI: {current_app.config.get('SQLALCHEMY_DATABASE_URI')}")
            # Return proper error response instead of raising
            return jsonify({
                'error': 'Database connection error',
                'message': 'Unable to connect to database. Please check server configuration.',
                'details': str(db_error) if current_app.config.get('DEBUG') else None
            }), 500

        if user and user.is_active:
            # Check if account is locked - TEMPORARILY DISABLED
            # if check_account_lockout(user):
            #     lockout_time = user.account_locked_until.strftime('%H:%M:%S')
            #     record_login_attempt(username, ip_address, success=False, failure_reason='account_locked')
            #     return jsonify({
            #         'error': f'Account is locked until {lockout_time}. Please try again later.'
            #     }), 423

            # Check password
            logger.info(f"Checking password for user {username}")
            password_valid = check_password_hash(user.password, password)
            logger.info(f"Password check result: {password_valid}")
            
            if password_valid:
                # Successful login
                logger.info(f"Password valid, logging in user {username}")
                login_user(user, remember=remember_me)
                
                # Try to reset failed attempts and record login (non-critical)
                try:
                    reset_failed_attempts(user)
                    record_login_attempt(username, ip_address, success=True)
                except Exception as e:
                    logger.warning(f"Failed to record login attempt: {str(e)}")
                    # Continue with login even if recording fails

                # Create session token
                session_token = str(uuid.uuid4())
                session['session_token'] = session_token
                session['_session_created'] = datetime.now(timezone.utc).isoformat()
                session.permanent = True
                
                # Set session duration based on remember me
                if remember_me:
                    # Remember me: 30 days
                    session.permanent_session_lifetime = timedelta(days=30)
                    logger.info(f"User {username} logged in with remember me enabled (30 days)")
                else:
                    # Regular session: 8 hours
                    session.permanent_session_lifetime = timedelta(hours=8)
                    logger.info(f"User {username} logged in with regular session (8 hours)")

                # Store session in database (non-critical, continue if fails)
                try:
                    user_session = UserSession(
                        user_id=user.id,
                        session_token=session_token,
                        ip_address=ip_address,
                        user_agent=request.headers.get('User-Agent', '')
                    )
                    db.session.add(user_session)
                    db.session.commit()
                except Exception as e:
                    logger.warning(f"Failed to store user session: {str(e)}")
                    db.session.rollback()
                    # Continue with login even if session storage fails

                try:
                    user_dict = user.to_dict()
                except Exception as e:
                    logger.warning(f"Failed to serialize user: {str(e)}")
                    user_dict = {
                        'id': user.id,
                        'username': user.username,
                        'role': user.role
                    }

                return jsonify({
                    'success': True,
                    'message': f'Welcome back, {user.username}!',
                    'user': user_dict
                }), 200
            else:
                # Failed login - wrong password
                try:
                    # handle_failed_login(user)  # Temporarily disabled
                    record_login_attempt(username, ip_address, success=False, failure_reason='invalid_credentials')
                except Exception as e:
                    logger.warning(f"Error recording failed login attempt: {str(e)}")
                    try:
                        db.session.rollback()
                    except:
                        pass

                return jsonify({
                    'error': 'Invalid credentials. Please verify your username and password and try again.'
                }), 401
        else:
            # User not found
            try:
                record_login_attempt(username, ip_address, success=False, failure_reason='user_not_found')
            except Exception as e:
                logger.warning(f"Error recording login attempt: {str(e)}")
                try:
                    db.session.rollback()
                except:
                    pass
            
            return jsonify({
                'error': 'Invalid credentials. Please verify your username and password and try again.'
            }), 401

    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Error during API login process: {str(e)}")
        logger.error(f"Traceback: {error_traceback}")
        
        # Check if it's a database error
        from sqlalchemy.exc import SQLAlchemyError
        if isinstance(e, SQLAlchemyError):
            logger.error(f"Database error details: {str(e)}")
            try:
                db.session.rollback()
            except:
                pass
            return jsonify({
                'error': 'Database connection error',
                'message': 'Unable to connect to database. Please check server configuration.',
                'details': str(e) if current_app.config.get('DEBUG') else None
            }), 500
        
        # Ensure we always return valid JSON
        return jsonify({
            'error': 'An error occurred during login',
            'message': 'Please try again later.',
            'details': str(e) if current_app.config.get('DEBUG') else None
        }), 500

@auth_api.route('/logout', methods=['POST'])
@login_required
@limiter.limit("30 per minute")  # Logout - reasonable limit for normal use
def api_logout():
    """Handle API logout"""
    try:
        # Mark current session as inactive
        token = session.get('session_token')
        if token:
            user_session = UserSession.query.filter_by(
                session_token=token, 
                is_active=True
            ).first()
            if user_session:
                user_session.is_active = False
                db.session.commit()

        # Clear session
        session.pop('session_token', None)
        logout_user()

        return jsonify({
            'success': True,
            'message': 'You have been logged out successfully.'
        }), 200

    except Exception as e:
        logger.error(f"Error during API logout: {str(e)}")
        return jsonify({
            'error': 'An error occurred during logout.'
        }), 500

@auth_api.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """Get current user profile"""
    try:
        return jsonify({
            'success': True,
            'user': current_user.to_dict()
        }), 200
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        return jsonify({
            'error': 'Failed to get user profile'
        }), 500

@auth_api.route('/sessions', methods=['GET'])
@login_required
def get_sessions():
    """Get user's active sessions"""
    try:
        active_sessions = UserSession.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).order_by(UserSession.created_at.desc()).all()

        sessions_data = []
        for session in active_sessions:
            sessions_data.append({
                'id': session.id,
                'session_token': session.session_token,
                'ip_address': session.ip_address,
                'user_agent': session.user_agent,
                'created_at': session.created_at.isoformat() if session.created_at else None,
                'last_activity': session.last_activity.isoformat() if session.last_activity else None
            })

        return jsonify({
            'success': True,
            'sessions': sessions_data
        }), 200
    except Exception as e:
        logger.error(f"Error getting user sessions: {str(e)}")
        return jsonify({
            'error': 'Failed to get user sessions'
        }), 500

@auth_api.route('/sessions/<int:session_id>', methods=['DELETE'])
@login_required
def logout_session(session_id):
    """Logout from a specific session"""
    try:
        session_obj = UserSession.query.filter_by(
            id=session_id,
            user_id=current_user.id,
            is_active=True
        ).first()

        if session_obj:
            session_obj.is_active = False
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Session logged out successfully.'
            }), 200
        else:
            return jsonify({
                'error': 'Session not found or already inactive.'
            }), 404

    except Exception as e:
        logger.error(f"Error logging out session: {str(e)}")
        return jsonify({
            'error': 'Failed to logout session'
        }), 500 