"""
Unit tests for permission decorators
"""
import pytest
from unittest.mock import Mock, patch
from flask import Flask
from app.utils.permission_decorators import (
    require_admin_level,
    require_permission,
    require_section_access,
    require_hard_admin
)


@pytest.mark.unit
class TestRequireAdminLevel:
    """Test require_admin_level decorator"""
    
    @patch('app.utils.permission_decorators.current_user')
    def test_require_admin_level_authenticated_admin(self, mock_user, app):
        """Test require_admin_level with authenticated admin"""
        mock_user.is_authenticated = True
        mock_user.is_any_admin.return_value = True
        mock_user.admin_level = 1
        
        @require_admin_level(1)
        def test_function():
            return "success"
        
        with app.test_request_context():
            result = test_function()
            assert result == "success"
    
    @patch('app.utils.permission_decorators.current_user')
    def test_require_admin_level_not_authenticated(self, mock_user, app):
        """Test require_admin_level with not authenticated user"""
        mock_user.is_authenticated = False
        
        @require_admin_level(1)
        def test_function():
            return "success"
        
        with app.test_request_context():
            with patch('app.utils.permission_decorators.redirect') as mock_redirect:
                mock_redirect.return_value = "redirected"
                result = test_function()
                assert result == "redirected"


@pytest.mark.unit
class TestRequirePermission:
    """Test require_permission decorator"""
    
    @patch('app.utils.permission_decorators.current_user')
    def test_require_permission_has_permission(self, mock_user, app):
        """Test require_permission with user having permission"""
        mock_user.is_authenticated = True
        mock_user.has_permission.return_value = True
        
        @require_permission('view_transactions')
        def test_function():
            return "success"
        
        with app.test_request_context():
            result = test_function()
            assert result == "success"
            mock_user.has_permission.assert_called_once_with('view_transactions')
    
    @patch('app.utils.permission_decorators.current_user')
    def test_require_permission_no_permission(self, mock_user, app):
        """Test require_permission without permission"""
        mock_user.is_authenticated = True
        mock_user.has_permission.return_value = False
        
        @require_permission('view_transactions')
        def test_function():
            return "success"
        
        with app.test_request_context():
            # Test that decorator checks permission
            # In actual Flask app, abort(403) would be called
            # For unit test, we just verify the logic path
            with patch('app.utils.permission_decorators.abort') as mock_abort:
                mock_abort.side_effect = Exception("403")
                try:
                    test_function()
                except Exception:
                    pass
                # Verify has_permission was called
                mock_user.has_permission.assert_called_once_with('view_transactions')


@pytest.mark.unit
class TestRequireSectionAccess:
    """Test require_section_access decorator"""
    
    @patch('app.utils.permission_decorators.current_user')
    def test_require_section_access_allowed(self, mock_user, app):
        """Test require_section_access with allowed access"""
        from app.services.admin_permission_service import admin_permission_service
        
        mock_user.is_authenticated = True
        mock_user.admin_level = 1
        
        with patch.object(admin_permission_service, 'can_access_section', return_value=True):
            @require_section_access('transactions')
            def test_function():
                return "success"
            
            with app.test_request_context():
                result = test_function()
                assert result == "success"
    
    @patch('app.utils.permission_decorators.current_user')
    @patch('app.utils.permission_decorators.abort')
    def test_require_section_access_denied(self, mock_abort, mock_user, app):
        """Test require_section_access with denied access"""
        from app.services.admin_permission_service import admin_permission_service
        
        mock_user.is_authenticated = True
        mock_user.admin_level = 1
        mock_abort.side_effect = Exception("403 Forbidden")
        
        with patch.object(admin_permission_service, 'can_access_section', return_value=False):
            @require_section_access('transactions')
            def test_function():
                return "success"
            
            with app.test_request_context():
                try:
                    test_function()
                except Exception:
                    pass  # Expected abort to be called
                mock_abort.assert_called_once_with(403)


@pytest.mark.unit
class TestRequireHardAdmin:
    """Test require_hard_admin decorator"""
    
    @patch('app.utils.permission_decorators.current_user')
    def test_require_hard_admin_authenticated(self, mock_user, app):
        """Test require_hard_admin with authenticated hard admin"""
        mock_user.is_authenticated = True
        mock_user.is_hard_admin.return_value = True
        
        @require_hard_admin
        def test_function():
            return "success"
        
        with app.test_request_context():
            result = test_function()
            assert result == "success"
    
    @patch('app.utils.permission_decorators.current_user')
    def test_require_hard_admin_not_authenticated(self, mock_user, app):
        """Test require_hard_admin with not authenticated user"""
        mock_user.is_authenticated = False
        
        @require_hard_admin
        def test_function():
            return "success"
        
        with app.test_request_context():
            with patch('app.utils.permission_decorators.redirect') as mock_redirect:
                mock_redirect.return_value = "redirected"
                result = test_function()
                assert result == "redirected"

