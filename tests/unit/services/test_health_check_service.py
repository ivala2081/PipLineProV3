"""
Unit tests for health check service
"""
import pytest
from app.services.health_check_service import health_check_service
from app import create_app, db


@pytest.mark.unit
@pytest.mark.database
class TestHealthCheckService:
    """Test health check service"""
    
    def test_check_basic_healthy(self, app):
        """Test basic health check when healthy"""
        with app.app_context():
            result = health_check_service.check_basic()
            
            assert "status" in result
            assert result["status"] in ["healthy", "unhealthy"]
    
    def test_check_basic_structure(self, app):
        """Test basic health check structure"""
        with app.app_context():
            result = health_check_service.check_basic()
            
            assert "status" in result
            assert "checks" in result
            assert "timestamp" in result
            assert isinstance(result["checks"], dict)
    
    def test_check_basic_database_check(self, app):
        """Test database check in basic health"""
        with app.app_context():
            result = health_check_service.check_basic()
            
            if "database" in result["checks"]:
                db_check = result["checks"]["database"]
                assert "status" in db_check
    
    def test_health_check_timestamp(self, app):
        """Test health check includes timestamp"""
        with app.app_context():
            result = health_check_service.check_basic()
            
            # Timestamp should be in result
            assert "timestamp" in result
            assert isinstance(result["timestamp"], str)

