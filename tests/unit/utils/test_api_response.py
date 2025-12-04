"""
Unit tests for API response utilities
"""
import pytest
from app.utils.api_response import (
    success_response,
    error_response,
    paginated_response,
    ErrorCode
)


@pytest.mark.unit
class TestSuccessResponse:
    """Test success_response function"""
    
    def test_success_response_with_data(self):
        """Test success response with data"""
        data = {"id": 1, "name": "Test"}
        response = success_response(data=data)
        
        assert "data" in response
        assert response["data"] == data
        assert "error" not in response or response["error"] is None
    
    def test_success_response_with_meta(self):
        """Test success response with meta"""
        data = {"id": 1}
        meta = {"timestamp": "2025-01-01"}
        response = success_response(data=data, meta=meta)
        
        assert response["data"] == data
        assert response["meta"] == meta
    
    def test_success_response_empty_data(self):
        """Test success response with empty data"""
        response = success_response(data={})
        
        assert "data" in response
        assert response["data"] == {}


@pytest.mark.unit
class TestErrorResponse:
    """Test error_response function"""
    
    def test_error_response_basic(self):
        """Test basic error response"""
        response = error_response(
            ErrorCode.VALIDATION_ERROR.value,
            "Validation failed"
        )
        
        assert "error" in response
        assert response["error"]["code"] == ErrorCode.VALIDATION_ERROR.value
        assert response["error"]["message"] == "Validation failed"
    
    def test_error_response_with_details(self):
        """Test error response with details"""
        details = {"field": "email", "reason": "invalid format"}
        response = error_response(
            ErrorCode.VALIDATION_ERROR.value,
            "Validation failed",
            details=details
        )
        
        assert response["error"]["details"] == details
    
    def test_error_response_with_status_code(self):
        """Test error response with status code"""
        response = error_response(
            ErrorCode.INTERNAL_ERROR.value,
            "Internal error",
            status_code=500
        )
        
        assert response["error"]["code"] == ErrorCode.INTERNAL_ERROR.value
        assert response["meta"]["status_code"] == 500


@pytest.mark.unit
class TestPaginatedResponse:
    """Test paginated_response function"""
    
    def test_paginated_response_basic(self):
        """Test basic paginated response"""
        items = [{"id": 1}, {"id": 2}]
        response = paginated_response(
            items=items,
            page=1,
            per_page=10,
            total=2
        )
        
        assert "data" in response
        assert response["data"] == items
        assert "meta" in response
        assert "pagination" in response["meta"]
        assert response["meta"]["pagination"]["page"] == 1
        assert response["meta"]["pagination"]["per_page"] == 10
        assert response["meta"]["pagination"]["total"] == 2
    
    def test_paginated_response_multiple_pages(self):
        """Test paginated response with multiple pages"""
        items = [{"id": i} for i in range(1, 11)]
        response = paginated_response(
            items=items,
            page=2,
            per_page=5,
            total=20
        )
        
        assert len(response["data"]) == 10
        assert response["meta"]["pagination"]["page"] == 2
        assert response["meta"]["pagination"]["total_pages"] == 4
        assert response["meta"]["pagination"]["has_prev"] is True
        assert response["meta"]["pagination"]["has_next"] is True
    
    def test_paginated_response_last_page(self):
        """Test paginated response on last page"""
        items = [{"id": 1}]
        response = paginated_response(
            items=items,
            page=3,
            per_page=5,
            total=11
        )
        
        assert response["meta"]["pagination"]["has_next"] is False
        assert response["meta"]["pagination"]["has_prev"] is True
    
    def test_paginated_response_first_page(self):
        """Test paginated response on first page"""
        items = [{"id": i} for i in range(1, 6)]
        response = paginated_response(
            items=items,
            page=1,
            per_page=5,
            total=10
        )
        
        assert response["meta"]["pagination"]["has_prev"] is False
        assert response["meta"]["pagination"]["has_next"] is True

