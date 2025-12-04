"""
Advanced security service for PipLinePro
"""
import hashlib
import hmac
import secrets
import time
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from flask import request, current_app
from werkzeug.security import check_password_hash, generate_password_hash

logger = logging.getLogger(__name__)

class SecurityService:
    """
    Comprehensive security service for PipLinePro
    """
    
    def __init__(self):
        self._failed_attempts = {}
        self._blocked_ips = set()
        self._suspicious_activities = []
        self._max_attempts = 5
        self._lockout_duration = 900  # 15 minutes
        self._rate_limit_window = 60  # 1 minute
        self._rate_limits = {}
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password strength according to security requirements"""
        issues = []
        score = 0
        
        # Length check
        if len(password) < 12:
            issues.append("Password must be at least 12 characters long")
        else:
            score += 1
        
        # Character variety checks
        if not any(c.isupper() for c in password):
            issues.append("Password must contain at least one uppercase letter")
        else:
            score += 1
        
        if not any(c.islower() for c in password):
            issues.append("Password must contain at least one lowercase letter")
        else:
            score += 1
        
        if not any(c.isdigit() for c in password):
            issues.append("Password must contain at least one number")
        else:
            score += 1
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            issues.append("Password must contain at least one special character")
        else:
            score += 1
        
        # Common password check
        common_passwords = [
            'password', '123456', 'admin', 'qwerty', 'letmein',
            'welcome', 'monkey', 'dragon', 'master', 'hello'
        ]
        if password.lower() in common_passwords:
            issues.append("Password is too common")
            score -= 2
        
        # Sequential character check
        if self._has_sequential_chars(password):
            issues.append("Password contains sequential characters")
            score -= 1
        
        # Repeated character check
        if self._has_repeated_chars(password):
            issues.append("Password contains too many repeated characters")
            score -= 1
        
        strength = "weak"
        if score >= 4:
            strength = "strong"
        elif score >= 2:
            strength = "medium"
        
        return {
            'is_valid': len(issues) == 0,
            'strength': strength,
            'score': max(0, score),
            'issues': issues
        }
    
    def _has_sequential_chars(self, password: str) -> bool:
        """Check for sequential characters"""
        for i in range(len(password) - 2):
            if (ord(password[i+1]) == ord(password[i]) + 1 and 
                ord(password[i+2]) == ord(password[i]) + 2):
                return True
        return False
    
    def _has_repeated_chars(self, password: str) -> bool:
        """Check for repeated characters"""
        char_count = {}
        for char in password:
            char_count[char] = char_count.get(char, 0) + 1
            if char_count[char] > 3:  # More than 3 repetitions
                return True
        return False
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate a cryptographically secure token"""
        return secrets.token_urlsafe(length)
    
    def hash_password(self, password: str) -> str:
        """Hash password with salt"""
        return generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return check_password_hash(password_hash, password)
    
    def check_rate_limit(self, identifier: str, limit: int = 10) -> bool:
        """Check if identifier is within rate limit"""
        current_time = time.time()
        window_start = current_time - self._rate_limit_window
        
        # Clean old entries
        if identifier in self._rate_limits:
            self._rate_limits[identifier] = [
                timestamp for timestamp in self._rate_limits[identifier]
                if timestamp > window_start
            ]
        else:
            self._rate_limits[identifier] = []
                
        # Check if within limit
        if len(self._rate_limits[identifier]) >= limit:
            return False
                
        # Add current request
        self._rate_limits[identifier].append(current_time)
        return True
                
    def record_failed_attempt(self, identifier: str, ip_address: str, 
                             user_agent: str, reason: str = "invalid_credentials"):
        """Record a failed authentication attempt"""
        current_time = time.time()
        
        if identifier not in self._failed_attempts:
            self._failed_attempts[identifier] = []
        
        self._failed_attempts[identifier].append({
            'timestamp': current_time,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'reason': reason
        })
        
        # Clean old attempts
        cutoff_time = current_time - self._lockout_duration
        self._failed_attempts[identifier] = [
            attempt for attempt in self._failed_attempts[identifier]
            if attempt['timestamp'] > cutoff_time
        ]
        
        # Check if should be locked out
        if len(self._failed_attempts[identifier]) >= self._max_attempts:
            self._blocked_ips.add(ip_address)
            logger.warning(f"IP {ip_address} blocked due to {len(self._failed_attempts[identifier])} failed attempts")
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP address is blocked"""
        return ip_address in self._blocked_ips
    
    def is_account_locked(self, identifier: str) -> bool:
        """Check if account is locked due to failed attempts"""
        if identifier not in self._failed_attempts:
            return False
        
        current_time = time.time()
        recent_attempts = [
            attempt for attempt in self._failed_attempts[identifier]
            if current_time - attempt['timestamp'] < self._lockout_duration
        ]
        
        return len(recent_attempts) >= self._max_attempts
    
    def get_lockout_time_remaining(self, identifier: str) -> int:
        """Get remaining lockout time in seconds"""
        if not self.is_account_locked(identifier):
            return 0
        
        if identifier not in self._failed_attempts:
            return 0
        
        current_time = time.time()
        oldest_attempt = min(
            attempt['timestamp'] for attempt in self._failed_attempts[identifier]
        )
        
        lockout_end = oldest_attempt + self._lockout_duration
        return max(0, int(lockout_end - current_time))
    
    def reset_failed_attempts(self, identifier: str):
        """Reset failed attempts for identifier"""
        if identifier in self._failed_attempts:
            del self._failed_attempts[identifier]
    
    def unblock_ip(self, ip_address: str):
        """Unblock an IP address"""
        self._blocked_ips.discard(ip_address)
    
    def detect_suspicious_activity(self, ip_address: str, user_agent: str, 
                                 activity_type: str, details: Dict[str, Any]):
        """Detect and record suspicious activities"""
        current_time = time.time()
        
        # Check for unusual patterns
        suspicious = False
        reasons = []
        
        # Check for rapid requests
        if activity_type == 'api_request':
            if not self.check_rate_limit(ip_address, 50):  # 50 requests per minute
                suspicious = True
                reasons.append("High request frequency")
        
        # Check for unusual user agents
        if user_agent and len(user_agent) < 10:
            suspicious = True
            reasons.append("Suspicious user agent")
        
        # Check for SQL injection patterns
        if 'sql' in str(details).lower() or 'union' in str(details).lower():
            suspicious = True
            reasons.append("Potential SQL injection attempt")
        
        if suspicious:
            self._suspicious_activities.append({
                'timestamp': current_time,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'activity_type': activity_type,
                'reasons': reasons,
                'details': details
            })
            
            logger.warning(f"Suspicious activity detected from {ip_address}: {reasons}")
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics and statistics"""
        current_time = time.time()
        
        # Count active lockouts
        active_lockouts = 0
        for attempts in self._failed_attempts.values():
            recent_attempts = [
                attempt for attempt in attempts
                if current_time - attempt['timestamp'] < self._lockout_duration
            ]
            if len(recent_attempts) >= self._max_attempts:
                active_lockouts += 1
        
        # Count recent suspicious activities
        recent_suspicious = [
            activity for activity in self._suspicious_activities
            if current_time - activity['timestamp'] < 3600  # Last hour
        ]
        
        return {
            'blocked_ips_count': len(self._blocked_ips),
            'active_lockouts': active_lockouts,
            'recent_suspicious_activities': len(recent_suspicious),
            'total_failed_attempts': sum(len(attempts) for attempts in self._failed_attempts.values()),
            'rate_limited_identifiers': len([
                identifier for identifier, timestamps in self._rate_limits.items()
                if len(timestamps) >= 10
            ])
        }
    
    def generate_csrf_token(self, user_id: int) -> str:
        """Generate CSRF token for user"""
        secret = current_app.config.get('SECRET_KEY', 'default-secret')
        data = f"{user_id}:{int(time.time())}"
        return hmac.new(
            secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def verify_csrf_token(self, token: str, user_id: int, max_age: int = 3600) -> bool:
        """Verify CSRF token"""
        try:
            secret = current_app.config.get('SECRET_KEY', 'default-secret')
            current_time = int(time.time())
            
            # Check tokens for the last hour
            for i in range(max_age):
                data = f"{user_id}:{current_time - i}"
                expected_token = hmac.new(
                    secret.encode(),
                    data.encode(),
                    hashlib.sha256
                ).hexdigest()
                
                if hmac.compare_digest(token, expected_token):
                    return True
            
            return False
        except Exception as e:
            logger.error(f"CSRF token verification failed: {e}")
            return False

# Global security service instance
security_service = SecurityService() 

def get_security_service() -> SecurityService:
    """Get the global security service instance"""
    return security_service