"""
Extended unit tests for API response utilities
"""
import pytest
from app.utils.api_response import (
    make_response,
    success_response,
    error_response,
    paginated_response,
    ErrorCode
)


@pytest.mark.unit
class TestMakeResponse:
    """Test make_response function"""
    
    def test_make_response_with_data(self):
        """Test make_response with data only"""
        result = make_response(data={'key': 'value'})
        
        assert result['data'] == {'key': 'value'}
        assert result['error'] is None
        assert result['meta'] is None
    
    def test_make_response_with_error(self):
        """Test make_response with error"""
        error = {'code': 'ERROR', 'message': 'Test error'}
        result = make_response(error=error)
        
        assert result['data'] is None
        assert result['error'] == error
        assert result['meta'] is None
    
    def test_make_response_with_meta(self):
        """Test make_response with meta"""
        result = make_response(data={'key': 'value'}, meta={'timestamp': '2025-01-01'})
        
        assert result['data'] == {'key': 'value'}
        assert result['meta'] == {'timestamp': '2025-01-01'}
    
    def test_make_response_complete(self):
        """Test make_response with all parameters"""
        result = make_response(
            data={'key': 'value'},
            error=None,
            meta={'page': 1}
        )
        
        assert result['data'] == {'key': 'value'}
        assert result['error'] is None
        assert result['meta'] == {'page': 1}


@pytest.mark.unit
class TestSuccessResponse:
    """Test success_response function"""
    
    def test_success_response_with_data(self):
        """Test success_response with data"""
        result = success_response(data={'id': 1, 'name': 'Test'})
        
        assert result['data'] == {'id': 1, 'name': 'Test'}
        assert result['error'] is None
    
    def test_success_response_with_meta(self):
        """Test success_response with meta"""
        result = success_response(
            data={'id': 1},
            meta={'message': 'Success', 'timestamp': '2025-01-01'}
        )
        
        assert result['data'] == {'id': 1}
        assert result['meta'] == {'message': 'Success', 'timestamp': '2025-01-01'}
    
    def test_success_response_empty(self):
        """Test success_response with no data"""
        result = success_response()
        
        assert result['data'] is None
        assert result['error'] is None


@pytest.mark.unit
class TestErrorResponse:
    """Test error_response function"""
    
    def test_error_response_basic(self):
        """Test basic error_response"""
        result = error_response('VALIDATION_ERROR', 'Invalid input')
        
        assert result['data'] is None
        assert result['error']['code'] == 'VALIDATION_ERROR'
        assert result['error']['message'] == 'Invalid input'
        assert result['meta']['status_code'] == 400
    
    def test_error_response_with_details(self):
        """Test error_response with details"""
        result = error_response(
            'VALIDATION_ERROR',
            'Invalid input',
            details={'field': 'email', 'value': 'invalid'}
        )
        
        assert result['error']['details'] == {'field': 'email', 'value': 'invalid'}
    
    def test_error_response_with_custom_status(self):
        """Test error_response with custom status code"""
        result = error_response('NOT_FOUND', 'Resource not found', status_code=404)
        
        assert result['meta']['status_code'] == 404
    
    def test_error_response_with_error_code_enum(self):
        """Test error_response with ErrorCode enum"""
        result = error_response(ErrorCode.AUTHENTICATION_ERROR.value, 'Not authenticated')
        
        assert result['error']['code'] == 'AUTHENTICATION_ERROR'


@pytest.mark.unit
class TestPaginatedResponse:
    """Test paginated_response function"""
    
    def test_paginated_response_basic(self):
        """Test basic paginated_response"""
        items = [{'id': 1}, {'id': 2}]
        result = paginated_response(items, page=1, per_page=10, total=2)
        
        assert result['data'] == items
        assert result['meta']['pagination']['page'] == 1
        assert result['meta']['pagination']['per_page'] == 10
        assert result['meta']['pagination']['total'] == 2
        assert result['meta']['pagination']['total_pages'] == 1
    
    def test_paginated_response_multiple_pages(self):
        """Test paginated_response with multiple pages"""
        items = [{'id': 1}, {'id': 2}]
        result = paginated_response(items, page=1, per_page=2, total=10)
        
        assert result['meta']['pagination']['total_pages'] == 5
        assert result['meta']['pagination']['has_next'] is True
        assert result['meta']['pagination']['has_prev'] is False
        assert result['meta']['pagination']['next_page'] == 2
        assert result['meta']['pagination']['prev_page'] is None
    
    def test_paginated_response_last_page(self):
        """Test paginated_response on last page"""
        items = [{'id': 9}, {'id': 10}]
        result = paginated_response(items, page=5, per_page=2, total=10)
        
        assert result['meta']['pagination']['has_next'] is False
        assert result['meta']['pagination']['has_prev'] is True
        assert result['meta']['pagination']['next_page'] is None
        assert result['meta']['pagination']['prev_page'] == 4
    
    def test_paginated_response_with_additional_meta(self):
        """Test paginated_response with additional metadata"""
        items = [{'id': 1}]
        result = paginated_response(
            items,
            page=1,
            per_page=10,
            total=1,
            meta={'message': 'Success'}
        )
        
        assert result['meta']['message'] == 'Success'
        assert 'pagination' in result['meta']
    
    def test_paginated_response_zero_per_page(self):
        """Test paginated_response with zero per_page"""
        items = []
        result = paginated_response(items, page=1, per_page=0, total=0)
        
        assert result['meta']['pagination']['total_pages'] == 0


@pytest.mark.unit
class TestErrorCode:
    """Test ErrorCode enum"""
    
    def test_error_code_values(self):
        """Test ErrorCode enum values"""
        assert ErrorCode.VALIDATION_ERROR.value == "VALIDATION_ERROR"
        assert ErrorCode.AUTHENTICATION_ERROR.value == "AUTHENTICATION_ERROR"
        assert ErrorCode.AUTHORIZATION_ERROR.value == "AUTHORIZATION_ERROR"
        assert ErrorCode.NOT_FOUND.value == "NOT_FOUND"
        assert ErrorCode.DATABASE_ERROR.value == "DATABASE_ERROR"
        assert ErrorCode.INTERNAL_ERROR.value == "INTERNAL_ERROR"
        assert ErrorCode.RATE_LIMIT_ERROR.value == "RATE_LIMIT_ERROR"
        assert ErrorCode.INVALID_REQUEST.value == "INVALID_REQUEST"

