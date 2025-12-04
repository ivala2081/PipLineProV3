"""
Unit tests for OpenAPI generator
"""
import pytest
from app import create_app
from app.utils.openapi_generator import generate_openapi_spec


@pytest.mark.unit
class TestOpenAPIGenerator:
    """Test OpenAPI specification generator"""
    
    def test_generate_openapi_spec_structure(self, app):
        """Test OpenAPI spec structure"""
        with app.app_context():
            spec = generate_openapi_spec()
            
            assert "openapi" in spec
            assert spec["openapi"] == "3.0.3"
            assert "info" in spec
            assert "paths" in spec
            assert "components" in spec
    
    def test_generate_openapi_spec_info(self, app):
        """Test OpenAPI spec info section"""
        with app.app_context():
            spec = generate_openapi_spec()
            
            assert "title" in spec["info"]
            assert "version" in spec["info"]
            assert "description" in spec["info"]
            assert spec["info"]["title"] == "PipLinePro API"
    
    def test_generate_openapi_spec_servers(self, app):
        """Test OpenAPI spec servers"""
        with app.app_context():
            spec = generate_openapi_spec()
            
            assert "servers" in spec
            assert len(spec["servers"]) > 0
            assert "url" in spec["servers"][0]
    
    def test_generate_openapi_spec_paths(self, app):
        """Test OpenAPI spec paths"""
        with app.app_context():
            spec = generate_openapi_spec()
            
            assert "paths" in spec
            assert len(spec["paths"]) > 0
            
            # Check for common API paths
            paths = list(spec["paths"].keys())
            api_paths = [p for p in paths if p.startswith("/api/v1/")]
            assert len(api_paths) > 0
    
    def test_generate_openapi_spec_components(self, app):
        """Test OpenAPI spec components"""
        with app.app_context():
            spec = generate_openapi_spec()
            
            assert "components" in spec
            assert "schemas" in spec["components"]
            assert "securitySchemes" in spec["components"]
            assert "responses" in spec["components"]
    
    def test_generate_openapi_spec_security(self, app):
        """Test OpenAPI spec security schemes"""
        with app.app_context():
            spec = generate_openapi_spec()
            
            security_schemes = spec["components"]["securitySchemes"]
            assert "sessionAuth" in security_schemes
            assert security_schemes["sessionAuth"]["type"] == "apiKey"
    
    def test_generate_openapi_spec_tags(self, app):
        """Test OpenAPI spec tags"""
        with app.app_context():
            spec = generate_openapi_spec()
            
            assert "tags" in spec
            assert len(spec["tags"]) > 0
            
            # Check tag structure
            for tag in spec["tags"]:
                assert "name" in tag
                assert "description" in tag

