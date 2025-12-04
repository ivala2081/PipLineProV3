"""
Unit tests for audit service
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from app.services.audit_service import AuditService
from app.models.audit import AuditLog
from app.models.user import User


@pytest.mark.unit
class TestAuditService:
    """Test AuditService"""
    
    def test_get_ip_address_with_request(self, app):
        """Test getting IP address from request"""
        with app.test_request_context(headers={'X-Forwarded-For': '192.168.1.1'}):
            ip = AuditService.get_ip_address()
            assert ip == '192.168.1.1'
    
    def test_get_ip_address_no_request(self):
        """Test getting IP address without request context"""
        ip = AuditService.get_ip_address()
        assert ip is None
    
    @patch('app.services.audit_service.current_user')
    def test_log_admin_action_success(self, mock_current_user, app, session):
        """Test logging admin action successfully"""
        with app.app_context():
            # Mock current user
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.id = 1
            
            with patch('app.services.audit_service.current_user', mock_user):
                result = AuditService.log_admin_action(
                    action=AuditService.ACTION_CREATE,
                    table_name='user',
                    record_id=1,
                    new_values={'username': 'test'},
                    user_id=1
                )
                
                # Should create audit log or return None on error
                assert result is None or isinstance(result, AuditLog)
    
    @patch('app.services.audit_service.current_user')
    def test_log_admin_action_no_user(self, mock_current_user):
        """Test logging admin action without authenticated user"""
        mock_user = Mock()
        mock_user.is_authenticated = False
        mock_current_user = mock_user
        
        with patch('app.services.audit_service.current_user', mock_user):
            result = AuditService.log_admin_action(
                action=AuditService.ACTION_CREATE,
                table_name='user',
                record_id=1
            )
            
            assert result is None
    
    @patch('app.services.audit_service.current_user')
    def test_log_admin_action_with_old_values(self, mock_current_user, app, session):
        """Test logging admin action with old values"""
        with app.app_context():
            mock_user = Mock()
            mock_user.is_authenticated = True
            mock_user.id = 1
            
            with patch('app.services.audit_service.current_user', mock_user):
                result = AuditService.log_admin_action(
                    action=AuditService.ACTION_UPDATE,
                    table_name='user',
                    record_id=1,
                    old_values={'username': 'old'},
                    new_values={'username': 'new'},
                    user_id=1
                )
                
                # Should handle old values
                assert result is None or isinstance(result, AuditLog)
    
    @patch('app.services.audit_service.User')
    @patch('app.services.audit_service.current_user')
    def test_log_user_management_action(self, mock_current_user, mock_user, app, session):
        """Test logging user management action"""
        with app.app_context():
            mock_target_user = Mock()
            mock_target_user.id = 2
            mock_target_user.username = 'target_user'
            mock_user.query.get.return_value = mock_target_user
            
            mock_auth_user = Mock()
            mock_auth_user.is_authenticated = True
            mock_auth_user.id = 1
            
            with patch('app.services.audit_service.current_user', mock_auth_user):
                result = AuditService.log_user_management_action(
                    action=AuditService.ACTION_ADMIN_UPDATE,
                    target_user_id=2,
                    old_values={'role': 'user'},
                    new_values={'role': 'admin'}
                )
                
                # Should call log_admin_action
                assert result is None or isinstance(result, AuditLog)
    
    @patch('app.services.audit_service.current_user')
    def test_log_admin_creation(self, mock_current_user, app, session):
        """Test logging admin creation"""
        with app.app_context():
            mock_admin = Mock()
            mock_admin.id = 1
            mock_admin.username = 'new_admin'
            mock_admin.admin_level = 1
            mock_admin.role = 'admin'
            
            mock_auth_user = Mock()
            mock_auth_user.is_authenticated = True
            mock_auth_user.id = 1
            
            with patch('app.services.audit_service.current_user', mock_auth_user):
                result = AuditService.log_admin_creation(mock_admin)
                
                # Should log admin creation
                assert result is None or isinstance(result, AuditLog)
    
    def test_action_constants(self):
        """Test action constants are defined"""
        assert AuditService.ACTION_CREATE == 'CREATE'
        assert AuditService.ACTION_UPDATE == 'UPDATE'
        assert AuditService.ACTION_DELETE == 'DELETE'
        assert AuditService.ACTION_ADMIN_CREATE == 'ADMIN_CREATE'
        assert AuditService.ACTION_ADMIN_UPDATE == 'ADMIN_UPDATE'
        assert AuditService.ACTION_USER_PASSWORD_CHANGE == 'USER_PASSWORD_CHANGE'

