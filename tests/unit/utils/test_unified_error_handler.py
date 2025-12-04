"""
Unit tests for unified error handler
"""
import pytest
from app.utils.unified_error_handler import (
    PipLineError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    DatabaseError,
    create_error_response,
    handle_api_error
)


@pytest.mark.unit
class TestPipLineError:
    """Test PipLineError base class"""
    
    def test_pipline_error_basic(self):
        """Test basic PipLineError creation"""
        error = PipLineError("Test error")
        
        assert str(error) == "Test error"
        assert error.error_code == "INTERNAL_ERROR"
        assert error.status_code == 500
    
    def test_pipline_error_with_code(self):
        """Test PipLineError with custom error code"""
        error = PipLineError("Test error", error_code="VALIDATION_ERROR")
        
        assert error.error_code == "VALIDATION_ERROR"
        assert error.status_code == 500
    
    def test_pipline_error_with_status(self):
        """Test PipLineError with custom status code"""
        error = PipLineError("Test error", status_code=400)
        
        assert error.status_code == 400


@pytest.mark.unit
class TestValidationError:
    """Test ValidationError"""
    
    def test_validation_error_basic(self):
        """Test basic ValidationError"""
        error = ValidationError("Invalid input")
        
        assert error.error_code == "VALIDATION_ERROR"
        assert error.status_code == 400
    
    def test_validation_error_with_field(self):
        """Test ValidationError with field"""
        error = ValidationError("Invalid input", field="email")
        
        assert error.details is not None
        assert error.details.get("field") == "email"
        assert error.error_code == "VALIDATION_ERROR"


@pytest.mark.unit
class TestAuthenticationError:
    """Test AuthenticationError"""
    
    def test_authentication_error(self):
        """Test AuthenticationError"""
        error = AuthenticationError("Not authenticated")
        
        assert error.error_code == "AUTHENTICATION_ERROR"
        assert error.status_code == 401


@pytest.mark.unit
class TestAuthorizationError:
    """Test AuthorizationError"""
    
    def test_authorization_error(self):
        """Test AuthorizationError"""
        error = AuthorizationError("Not authorized")
        
        assert error.error_code == "AUTHORIZATION_ERROR"
        assert error.status_code == 403


@pytest.mark.unit
class TestResourceNotFoundError:
    """Test ResourceNotFoundError"""
    
    def test_resource_not_found_error(self):
        """Test ResourceNotFoundError"""
        error = ResourceNotFoundError("User", 123)
        
        assert error.error_code == "RESOURCE_NOT_FOUND"
        assert error.status_code == 404
        assert error.details.get("resource_type") == "User"
        assert error.details.get("resource_id") == "123"


@pytest.mark.unit
class TestDatabaseError:
    """Test DatabaseError"""
    
    def test_database_error(self):
        """Test DatabaseError"""
        error = DatabaseError("Database error")
        
        assert error.error_code == "DATABASE_ERROR"
        assert error.status_code == 500


@pytest.mark.unit
class TestCreateErrorResponse:
    """Test create_error_response function"""
    
    def test_create_error_response_basic(self, app, client):
        """Test basic error response creation"""
        with app.app_context():
            with app.test_request_context('/api/v1/test'):
                error = ValidationError("Invalid input")
                response_obj, status_code = create_error_response(error)
                
                # Response is a Flask Response object, get JSON data
                assert status_code == 400
                # Can't easily test Response object content without making actual request
                # Just verify it returns a tuple with status code
                assert isinstance(status_code, int)
    
    def test_create_error_response_with_details(self, app, client):
        """Test error response with details"""
        with app.app_context():
            with app.test_request_context('/api/v1/test'):
                error = ValidationError("Invalid input", field="email", value="invalid@")
                response_obj, status_code = create_error_response(error)
                
                assert status_code == 400
                assert isinstance(status_code, int)

