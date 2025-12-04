"""
OpenAPI 3.0 Specification Generator for PipLinePro API
Generates comprehensive OpenAPI specification from Flask routes
Otomatik olarak tüm Flask route'larını tarar ve dokümantasyon oluşturur
"""
from typing import Dict, Any, List, Set, Optional
from flask import current_app
from datetime import datetime
import re
import inspect
from collections import defaultdict


def generate_openapi_spec() -> Dict[str, Any]:
    """
    Generate OpenAPI 3.0 specification for PipLinePro API
    
    Returns:
        Complete OpenAPI 3.0 specification as dictionary
    """
    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "PipLinePro API",
            "version": "1.0.0",
            "description": "Comprehensive API for PipLinePro Treasury Management System",
            "contact": {
                "name": "PipLinePro Support",
                "email": "support@pipeline.com"
            },
            "license": {
                "name": "Proprietary"
            }
        },
        "servers": [
            {
                "url": "http://localhost:5000",
                "description": "Development server"
            },
            {
                "url": "https://api.pipeline.com",
                "description": "Production server"
            }
        ],
        "tags": _generate_tags(),
        "paths": _generate_paths(),
        "components": {
            "schemas": _generate_schemas(),
            "parameters": _generate_parameters(),
            "securitySchemes": {
                "sessionAuth": {
                    "type": "apiKey",
                    "in": "cookie",
                    "name": "session",
                    "description": "Session-based authentication using Flask-Login"
                },
                "csrfToken": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-CSRFToken",
                    "description": "CSRF token for POST/PUT/DELETE requests"
                }
            },
            "responses": _generate_responses()
        },
        "security": [
            {"sessionAuth": []}
        ]
    }
    
    return spec


def _generate_tags() -> List[Dict[str, Any]]:
    """Tag'leri dinamik olarak oluştur"""
    tags = [
        {"name": "Authentication", "description": "User authentication and session management"},
        {"name": "Transactions", "description": "Transaction management operations"},
        {"name": "Analytics", "description": "Analytics and reporting endpoints"},
        {"name": "Health", "description": "System health and monitoring"},
        {"name": "Performance", "description": "Performance metrics and optimization"},
        {"name": "Exchange Rates", "description": "Exchange rate management"},
        {"name": "Configuration", "description": "System configuration endpoints"},
        {"name": "Users", "description": "User management endpoints"},
        {"name": "Database", "description": "Database management endpoints"},
        {"name": "Monitoring", "description": "System monitoring and metrics"},
        {"name": "Security", "description": "Security and access control"},
        {"name": "Financial Performance", "description": "Financial performance analytics"},
        {"name": "Trust Wallet", "description": "Trust Wallet integration"},
        {"name": "Accounting", "description": "Accounting operations"},
        {"name": "Translations", "description": "Translation management"},
        {"name": "Currency Management", "description": "Currency and exchange rate management"},
        {"name": "AI", "description": "AI-powered analysis and assistance"},
        {"name": "Realtime", "description": "Real-time analytics and updates"}
    ]
    
    # Flask route'larından unique tag'leri çıkar
    if current_app:
        unique_tags = set()
        for rule in current_app.url_map.iter_rules():
            if rule.rule.startswith('/api/v1/'):
                tag = _extract_tag(rule.rule)
                unique_tags.add(tag)
        
        # Mevcut tag'lerde yoksa ekle
        existing_tag_names = {tag["name"] for tag in tags}
        for tag_name in unique_tags:
            if tag_name not in existing_tag_names:
                tags.append({
                    "name": tag_name,
                    "description": f"{tag_name} endpoints"
                })
    
    return tags


def _generate_paths() -> Dict[str, Any]:
    """Generate API paths specification - Otomatik olarak Flask route'larını tarar"""
    paths = {}
    
    if not current_app:
        return _generate_static_paths()
    
    # Flask url_map'inden tüm route'ları al
    route_map = defaultdict(list)
    
    for rule in current_app.url_map.iter_rules():
        # Sadece API v1 endpoint'lerini dahil et
        if rule.rule.startswith('/api/v1/'):
            # Route'u normalize et
            path = _normalize_path(rule.rule)
            
            # Her HTTP method için endpoint bilgisi oluştur
            methods = rule.methods - {'HEAD', 'OPTIONS'}  # HEAD ve OPTIONS'ı atla
            
            if path not in paths:
                paths[path] = {}
            
            for method in methods:
                if method.lower() not in paths[path]:
                    # Endpoint fonksiyonunu bul
                    endpoint_func = _get_endpoint_function(rule.endpoint)
                    
                    # OpenAPI operation oluştur
                    operation = _create_operation(
                        method=method,
                        rule=rule,
                        endpoint_func=endpoint_func
                    )
                    
                    if operation:
                        paths[path][method.lower()] = operation
    
    # Statik path'leri de ekle (fallback)
    static_paths = _generate_static_paths()
    for path, methods in static_paths.items():
        if path not in paths:
            paths[path] = methods
        else:
            # Mevcut path'e eksik method'ları ekle
            for method, operation in methods.items():
                if method not in paths[path]:
                    paths[path][method] = operation
    
    return paths


def _normalize_path(path: str) -> str:
    """Path'i OpenAPI formatına normalize et"""
    # Flask converter'ları OpenAPI formatına çevir
    # <int:id> -> {id}
    # <string:name> -> {name}
    path = re.sub(r'<int:(\w+)>', r'{\1}', path)
    path = re.sub(r'<string:(\w+)>', r'{\1}', path)
    path = re.sub(r'<(\w+)>', r'{\1}', path)
    
    # Trailing slash'i koru ama normalize et
    if path.endswith('/') and path != '/':
        path = path.rstrip('/')
    
    return path


def _get_endpoint_function(endpoint_name: str):
    """Endpoint fonksiyonunu Flask view registry'den al"""
    try:
        view_func = current_app.view_functions.get(endpoint_name)
        if view_func:
            # Decorator'ları atla, gerçek fonksiyonu al
            while hasattr(view_func, '__wrapped__'):
                view_func = view_func.__wrapped__
            return view_func
    except Exception:
        pass
    return None


def _create_operation(method: str, rule, endpoint_func) -> Optional[Dict[str, Any]]:
    """Endpoint fonksiyonundan OpenAPI operation oluştur"""
    operation = {
        "summary": _extract_summary(endpoint_func, rule.endpoint),
        "description": _extract_description(endpoint_func),
        "tags": [_extract_tag(rule.rule)],
        "responses": _generate_default_responses(method)
    }
    
    # Security gereksinimlerini kontrol et
    security = _extract_security(endpoint_func)
    if security:
        operation["security"] = security
    
    # Query parametrelerini çıkar
    parameters = _extract_parameters(rule, endpoint_func)
    if parameters:
        operation["parameters"] = parameters
    
    # Request body (POST, PUT, PATCH için)
    if method.upper() in ['POST', 'PUT', 'PATCH']:
        request_body = _extract_request_body(endpoint_func, rule.endpoint)
        if request_body:
            operation["requestBody"] = request_body
    
    return operation


def _extract_summary(func, endpoint_name: str) -> str:
    """Fonksiyon docstring'inden veya endpoint adından summary çıkar"""
    if func and func.__doc__:
        # İlk satırı summary olarak kullan
        first_line = func.__doc__.strip().split('\n')[0]
        if first_line:
            return first_line.strip()
    
    # Endpoint adından summary oluştur
    name = endpoint_name.split('.')[-1]
    name = re.sub(r'([A-Z])', r' \1', name).strip()
    return name.replace('_', ' ').title()


def _extract_description(func) -> str:
    """Fonksiyon docstring'inden tam açıklama çıkar"""
    if func and func.__doc__:
        lines = [line.strip() for line in func.__doc__.strip().split('\n')]
        # İlk satırı atla (summary), geri kalanını al
        if len(lines) > 1:
            return '\n'.join(lines[1:]).strip()
        return lines[0] if lines else ""
    return ""


def _extract_tag(path: str) -> str:
    """Path'den tag çıkar (örn: /api/v1/transactions -> Transactions)"""
    # /api/v1/transactions -> transactions
    parts = path.split('/')
    if len(parts) >= 4:
        tag = parts[3]  # /api/v1/transactions -> transactions
        # Kebab-case'i Title Case'e çevir
        tag = tag.replace('-', ' ').title()
        return tag
    return "API"


def _extract_security(func) -> Optional[List[Dict[str, Any]]]:
    """Fonksiyon decorator'larından security gereksinimlerini çıkar"""
    if not func:
        return None
    
    # login_required decorator'ını kontrol et
    # Flask-Login'in login_required decorator'ı varsa
    if hasattr(func, '__wrapped__'):
        # Decorator chain'ini kontrol et
        wrapped = func
        while hasattr(wrapped, '__wrapped__'):
            # login_required kontrolü
            if 'login_required' in str(wrapped) or hasattr(wrapped, 'login_required'):
                return [{"sessionAuth": []}]
            wrapped = wrapped.__wrapped__
    
    # Varsayılan olarak authenticated endpoint'ler için security ekle
    # (API v1 endpoint'leri genelde authenticated)
    return [{"sessionAuth": []}]


def _extract_parameters(rule, func) -> List[Dict[str, Any]]:
    """Path ve query parametrelerini çıkar"""
    parameters = []
    
    # Path parametrelerini ekle
    for arg in rule.arguments:
        param = {
            "name": arg,
            "in": "path",
            "required": True,
            "schema": {"type": "integer" if 'id' in arg.lower() else "string"},
            "description": f"{arg} parameter"
        }
        parameters.append(param)
    
    # Fonksiyon signature'ından query parametrelerini tahmin et
    if func:
        sig = inspect.signature(func)
        for param_name, param_obj in sig.parameters.items():
            # request.args.get() kullanılan parametreleri tahmin et
            if param_name not in ['self', 'request', 'current_user']:
                # Bu basit bir tahmin, gerçek implementasyonda daha gelişmiş olabilir
                pass
    
    return parameters if parameters else None


def _extract_request_body(func, endpoint_name: str) -> Optional[Dict[str, Any]]:
    """Request body şemasını çıkar"""
    # Basit bir JSON request body şeması oluştur
    return {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {}
                }
            }
        }
    }


def _generate_default_responses(method: str) -> Dict[str, Any]:
    """Varsayılan response'ları oluştur"""
    responses = {
        "200": {
            "description": "Successful operation",
            "content": {
                "application/json": {
                    "schema": {"type": "object"}
                }
            }
        },
        "400": {"$ref": "#/components/responses/ValidationError"},
        "401": {"$ref": "#/components/responses/Unauthorized"},
        "500": {"$ref": "#/components/responses/InternalError"}
    }
    
    if method.upper() == 'POST':
        responses["201"] = {
            "description": "Resource created",
            "content": {
                "application/json": {
                    "schema": {"type": "object"}
                }
            }
        }
    
    if method.upper() in ['GET', 'PUT', 'PATCH']:
        responses["404"] = {"$ref": "#/components/responses/NotFound"}
    
    return responses


def _generate_static_paths() -> Dict[str, Any]:
    """Statik path'leri oluştur (fallback)"""
    return {
        "/api/v1/auth/login": {
            "post": {
                "tags": ["Authentication"],
                "summary": "User login",
                "description": "Authenticate user and create session",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["username", "password"],
                                "properties": {
                                    "username": {"type": "string", "example": "admin"},
                                    "password": {"type": "string", "format": "password"},
                                    "remember_me": {"type": "boolean", "default": False}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"$ref": "#/components/responses/Success"},
                    "401": {"$ref": "#/components/responses/Unauthorized"},
                    "400": {"$ref": "#/components/responses/ValidationError"}
                }
            }
        },
        "/api/v1/auth/logout": {
            "post": {
                "tags": ["Authentication"],
                "summary": "User logout",
                "description": "End user session",
                "responses": {
                    "200": {"$ref": "#/components/responses/Success"},
                    "401": {"$ref": "#/components/responses/Unauthorized"}
                },
                "security": [{"sessionAuth": []}]
            }
        },
        "/api/v1/auth/check": {
            "get": {
                "tags": ["Authentication"],
                "summary": "Check authentication status",
                "description": "Verify if user is authenticated",
                "responses": {
                    "200": {"$ref": "#/components/responses/Success"},
                    "401": {"$ref": "#/components/responses/Unauthorized"}
                },
                "security": [{"sessionAuth": []}]
            }
        },
        "/api/v1/transactions/": {
            "get": {
                "tags": ["Transactions"],
                "summary": "List transactions",
                "description": "Get paginated list of transactions with filtering",
                "parameters": [
                    {"$ref": "#/components/parameters/Page"},
                    {"$ref": "#/components/parameters/PerPage"},
                    {"$ref": "#/components/parameters/SortBy"},
                    {"$ref": "#/components/parameters/SortOrder"},
                    {"$ref": "#/components/parameters/StartDate"},
                    {"$ref": "#/components/parameters/EndDate"},
                    {"$ref": "#/components/parameters/PSPFilter"},
                    {"$ref": "#/components/parameters/ClientFilter"},
                    {"$ref": "#/components/parameters/CurrencyFilter"}
                ],
                "responses": {
                    "200": {
                        "description": "List of transactions",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "transactions": {
                                            "type": "array",
                                            "items": {"$ref": "#/components/schemas/Transaction"}
                                        },
                                        "pagination": {"$ref": "#/components/schemas/Pagination"}
                                    }
                                }
                            }
                        }
                    },
                    "401": {"$ref": "#/components/responses/Unauthorized"},
                    "400": {"$ref": "#/components/responses/ValidationError"}
                },
                "security": [{"sessionAuth": []}]
            },
            "post": {
                "tags": ["Transactions"],
                "summary": "Create transaction",
                "description": "Create a new transaction",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/TransactionCreate"}
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Transaction created",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "transaction": {"$ref": "#/components/schemas/Transaction"},
                                        "message": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "400": {"$ref": "#/components/responses/ValidationError"},
                    "401": {"$ref": "#/components/responses/Unauthorized"}
                },
                "security": [{"sessionAuth": []}, {"csrfToken": []}]
            }
        },
        "/api/v1/transactions/{id}": {
            "get": {
                "tags": ["Transactions"],
                "summary": "Get transaction",
                "description": "Get transaction by ID",
                "parameters": [{"$ref": "#/components/parameters/TransactionId"}],
                "responses": {
                    "200": {
                        "description": "Transaction details",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Transaction"}
                            }
                        }
                    },
                    "404": {"$ref": "#/components/responses/NotFound"},
                    "401": {"$ref": "#/components/responses/Unauthorized"}
                },
                "security": [{"sessionAuth": []}]
            },
            "put": {
                "tags": ["Transactions"],
                "summary": "Update transaction",
                "description": "Update existing transaction",
                "parameters": [{"$ref": "#/components/parameters/TransactionId"}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/TransactionUpdate"}
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Transaction updated",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Transaction"}
                            }
                        }
                    },
                    "400": {"$ref": "#/components/responses/ValidationError"},
                    "404": {"$ref": "#/components/responses/NotFound"},
                    "401": {"$ref": "#/components/responses/Unauthorized"}
                },
                "security": [{"sessionAuth": []}, {"csrfToken": []}]
            },
            "delete": {
                "tags": ["Transactions"],
                "summary": "Delete transaction",
                "description": "Delete transaction by ID",
                "parameters": [{"$ref": "#/components/parameters/TransactionId"}],
                "responses": {
                    "200": {"$ref": "#/components/responses/Success"},
                    "404": {"$ref": "#/components/responses/NotFound"},
                    "401": {"$ref": "#/components/responses/Unauthorized"}
                },
                "security": [{"sessionAuth": []}, {"csrfToken": []}]
            }
        },
        "/api/v1/analytics/dashboard/stats": {
            "get": {
                "tags": ["Analytics"],
                "summary": "Get dashboard statistics",
                "description": "Get comprehensive dashboard analytics",
                "parameters": [
                    {
                        "name": "range",
                        "in": "query",
                        "description": "Time range for analytics",
                        "required": False,
                        "schema": {
                            "type": "string",
                            "enum": ["today", "week", "month", "quarter", "year", "all"],
                            "default": "all"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Dashboard statistics",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/DashboardStats"}
                            }
                        }
                    },
                    "401": {"$ref": "#/components/responses/Unauthorized"}
                },
                "security": [{"sessionAuth": []}]
            }
        },
        "/api/v1/health/": {
            "get": {
                "tags": ["Health"],
                "summary": "Basic health check",
                "description": "Check if service is running",
                "responses": {
                    "200": {
                        "description": "Service is healthy",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/HealthCheck"}
                            }
                        }
                    },
                    "503": {
                        "description": "Service is unhealthy",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/HealthCheck"}
                            }
                        }
                    }
                }
            }
        },
        "/api/v1/health/detailed": {
            "get": {
                "tags": ["Health"],
                "summary": "Detailed health check",
                "description": "Get detailed system health information",
                "responses": {
                    "200": {
                        "description": "Detailed health information",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/DetailedHealthCheck"}
                            }
                        }
                    }
                },
                "security": [{"sessionAuth": []}]
            }
        },
        "/api/v1/performance/metrics": {
            "get": {
                "tags": ["Performance"],
                "summary": "Get performance metrics",
                "description": "Get comprehensive performance metrics",
                "responses": {
                    "200": {
                        "description": "Performance metrics",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/PerformanceMetrics"}
                            }
                        }
                    },
                    "401": {"$ref": "#/components/responses/Unauthorized"}
                },
                "security": [{"sessionAuth": []}]
            }
        }
    }


def _generate_schemas() -> Dict[str, Any]:
    """Generate component schemas"""
    return {
        "Transaction": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "example": 1},
                "amount": {"type": "number", "format": "decimal", "example": 1000.00},
                "currency": {"type": "string", "enum": ["TL", "USD", "EUR"], "example": "TL"},
                "psp": {"type": "string", "example": "SİPAY"},
                "client_name": {"type": "string", "example": "Client A"},
                "date": {"type": "string", "format": "date", "example": "2025-09-23"},
                "category": {"type": "string", "example": "Payment"},
                "description": {"type": "string", "example": "Transaction description"},
                "created_at": {"type": "string", "format": "date-time"},
                "updated_at": {"type": "string", "format": "date-time"}
            }
        },
        "TransactionCreate": {
            "type": "object",
            "required": ["amount", "currency", "psp", "client_name"],
            "properties": {
                "amount": {"type": "number", "format": "decimal"},
                "currency": {"type": "string", "enum": ["TL", "USD", "EUR"]},
                "psp": {"type": "string"},
                "client_name": {"type": "string"},
                "date": {"type": "string", "format": "date"},
                "category": {"type": "string"},
                "description": {"type": "string"},
                "payment_method": {"type": "string"},
                "commission": {"type": "number", "format": "decimal"}
            }
        },
        "TransactionUpdate": {
            "type": "object",
            "properties": {
                "amount": {"type": "number", "format": "decimal"},
                "currency": {"type": "string", "enum": ["TL", "USD", "EUR"]},
                "psp": {"type": "string"},
                "client_name": {"type": "string"},
                "date": {"type": "string", "format": "date"},
                "category": {"type": "string"},
                "description": {"type": "string"}
            }
        },
        "Pagination": {
            "type": "object",
            "properties": {
                "page": {"type": "integer", "example": 1},
                "per_page": {"type": "integer", "example": 20},
                "total": {"type": "integer", "example": 100},
                "total_pages": {"type": "integer", "example": 5},
                "has_prev": {"type": "boolean"},
                "has_next": {"type": "boolean"}
            }
        },
        "DashboardStats": {
            "type": "object",
            "properties": {
                "revenue": {
                    "type": "object",
                    "properties": {
                        "total": {"type": "number"},
                        "daily": {"type": "number"},
                        "trend": {"type": "number"}
                    }
                },
                "transactions": {
                    "type": "object",
                    "properties": {
                        "total": {"type": "integer"},
                        "daily": {"type": "integer"},
                        "trend": {"type": "number"}
                    }
                }
            }
        },
        "HealthCheck": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["healthy", "unhealthy"]},
                "timestamp": {"type": "string", "format": "date-time"}
            }
        },
        "DetailedHealthCheck": {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "checks": {
                    "type": "object",
                    "properties": {
                        "database": {"type": "object"},
                        "cache": {"type": "object"},
                        "redis": {"type": "object"}
                    }
                }
            }
        },
        "PerformanceMetrics": {
            "type": "object",
            "properties": {
                "system": {"type": "object"},
                "cache": {"type": "object"},
                "queries": {"type": "object"}
            }
        },
        "Error": {
            "type": "object",
            "properties": {
                "error": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "message": {"type": "string"},
                        "request_id": {"type": "string"},
                        "timestamp": {"type": "string", "format": "date-time"}
                    }
                }
            }
        }
    }


def _generate_responses() -> Dict[str, Any]:
    """Generate common response schemas"""
    return {
        "Success": {
            "description": "Successful operation",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "data": {"type": "object"},
                            "message": {"type": "string"}
                        }
                    }
                }
            }
        },
        "ValidationError": {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/Error"}
                }
            }
        },
        "Unauthorized": {
            "description": "Authentication required",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/Error"}
                }
            }
        },
        "NotFound": {
            "description": "Resource not found",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/Error"}
                }
            }
        },
        "InternalError": {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/Error"}
                }
            }
        }
    }


def _generate_parameters() -> Dict[str, Any]:
    """Generate common parameter schemas"""
    return {
        "Page": {
            "name": "page",
            "in": "query",
            "description": "Page number",
            "required": False,
            "schema": {"type": "integer", "default": 1, "minimum": 1}
        },
        "PerPage": {
            "name": "per_page",
            "in": "query",
            "description": "Items per page",
            "required": False,
            "schema": {"type": "integer", "default": 20, "minimum": 1, "maximum": 100}
        },
        "SortBy": {
            "name": "sort_by",
            "in": "query",
            "description": "Field to sort by",
            "required": False,
            "schema": {"type": "string", "enum": ["created_at", "amount", "date"]}
        },
        "SortOrder": {
            "name": "sort_order",
            "in": "query",
            "description": "Sort order",
            "required": False,
            "schema": {"type": "string", "enum": ["asc", "desc"], "default": "desc"}
        },
        "StartDate": {
            "name": "start_date",
            "in": "query",
            "description": "Start date filter (YYYY-MM-DD)",
            "required": False,
            "schema": {"type": "string", "format": "date"}
        },
        "EndDate": {
            "name": "end_date",
            "in": "query",
            "description": "End date filter (YYYY-MM-DD)",
            "required": False,
            "schema": {"type": "string", "format": "date"}
        },
        "PSPFilter": {
            "name": "psp",
            "in": "query",
            "description": "Filter by PSP name",
            "required": False,
            "schema": {"type": "string"}
        },
        "ClientFilter": {
            "name": "client_name",
            "in": "query",
            "description": "Filter by client name",
            "required": False,
            "schema": {"type": "string"}
        },
        "CurrencyFilter": {
            "name": "currency",
            "in": "query",
            "description": "Filter by currency",
            "required": False,
            "schema": {"type": "string", "enum": ["TL", "USD", "EUR"]}
        },
        "TransactionId": {
            "name": "id",
            "in": "path",
            "description": "Transaction ID",
            "required": True,
            "schema": {"type": "integer"}
        }
    }
