"""
API Documentation endpoints for PipLinePro
Enhanced with comprehensive OpenAPI/Swagger documentation
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
import logging

from app.utils.openapi_generator import generate_openapi_spec

logger = logging.getLogger(__name__)

docs_api = Blueprint('docs_api', __name__)


@docs_api.route('/')
def api_documentation():
    """Main API documentation endpoint - Shows HTML landing page"""
    from flask import Response, current_app
    
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PipLinePro API Documentation</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 800px;
            width: 100%;
            padding: 40px;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        .links {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .link-card {
            background: #f8f9fa;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            padding: 25px;
            text-decoration: none;
            color: #333;
            transition: all 0.3s ease;
            display: block;
        }
        .link-card:hover {
            border-color: #667eea;
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.2);
        }
        .link-card h3 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.3em;
        }
        .link-card p {
            color: #666;
            font-size: 0.9em;
            line-height: 1.5;
        }
        .info {
            background: #e7f3ff;
            border-left: 4px solid #2196F3;
            padding: 15px;
            margin-top: 30px;
            border-radius: 4px;
        }
        .info h4 {
            color: #1976D2;
            margin-bottom: 8px;
        }
        .info ul {
            margin-left: 20px;
            color: #555;
        }
        .info li {
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 PipLinePro API Documentation</h1>
        <p class="subtitle">Version 1.0.0 - Comprehensive API documentation for Treasury Management System</p>
        
        <div class="links">
            <a href="/api/v1/docs/swagger" class="link-card">
                <h3>🔍 Swagger UI</h3>
                <p>Interactive API documentation with try-it-out functionality</p>
            </a>
            
            <a href="/api/v1/docs/redoc" class="link-card">
                <h3>📖 ReDoc</h3>
                <p>Beautiful, responsive API documentation interface</p>
            </a>
            
            <a href="/api/v1/docs/openapi.json" class="link-card">
                <h3>📄 OpenAPI JSON</h3>
                <p>Machine-readable OpenAPI 3.0 specification (JSON)</p>
            </a>
            
            <a href="/api/v1/docs/openapi.yaml" class="link-card">
                <h3>📋 OpenAPI YAML</h3>
                <p>Machine-readable OpenAPI 3.0 specification (YAML)</p>
            </a>
        </div>
        
        <div class="info">
            <h4>ℹ️ Quick Info</h4>
            <ul>
                <li><strong>Authentication:</strong> Session-based with CSRF protection</li>
                <li><strong>Base URL:</strong> <code>/api/v1</code></li>
                <li><strong>Content-Type:</strong> <code>application/json</code></li>
                <li><strong>CSRF Token:</strong> Required for POST/PUT/DELETE requests</li>
            </ul>
        </div>
    </div>
</body>
</html>
    """
    
    try:
        # Try render_template_string first (for consistency with other endpoints)
        from flask import render_template_string
        result = render_template_string(html)
        return result
    except Exception as e:
        # If render_template_string fails, log the error and return HTML directly
        logger.error(f"Error rendering template in api_documentation: {e}", exc_info=True)
        # Return HTML directly with proper content-type header
        return Response(html, mimetype='text/html')

@docs_api.route('/transactions')
def transactions_docs():
    """Detailed transactions API documentation"""
    return jsonify({
        "endpoint": "/api/v1/transactions/",
        "description": "Transaction management endpoints",
        "methods": {
            "GET": {
                "description": "List transactions with pagination and filtering",
                "parameters": {
                    "page": "Page number (default: 1)",
                    "per_page": "Items per page (default: 20, max: 100)",
                    "sort_by": "Sort field (created_at, amount, date)",
                    "sort_order": "Sort order (asc, desc)",
                    "start_date": "Filter by start date (YYYY-MM-DD)",
                    "end_date": "Filter by end date (YYYY-MM-DD)",
                    "psp": "Filter by PSP name",
                    "client_name": "Filter by client name",
                    "currency": "Filter by currency"
                },
                "response": {
                    "transactions": "Array of transaction objects",
                    "pagination": "Pagination metadata",
                    "total": "Total number of transactions"
                }
            },
            "POST": {
                "description": "Create a new transaction",
                "body": {
                    "amount": "Transaction amount (required)",
                    "currency": "Currency code (required)",
                    "psp": "PSP name (required)",
                    "client_name": "Client name (required)",
                    "date": "Transaction date (YYYY-MM-DD)",
                    "category": "Transaction category",
                    "description": "Transaction description"
                },
                "response": {
                    "transaction": "Created transaction object",
                    "message": "Success message"
                }
            }
        },
        "special_endpoints": {
            "psp_summary_stats": {
                "method": "GET",
                "description": "Get PSP summary statistics with allocations",
                "caching": "5 minutes",
                "response": "Array of PSP statistics with totals and allocations"
            },
            "psp_monthly_stats": {
                "method": "GET", 
                "description": "Get PSP monthly statistics",
                "parameters": {
                    "year": "Year (default: current year)",
                    "month": "Month (default: current month)"
                },
                "caching": "10 minutes",
                "response": "Array of monthly PSP statistics"
            }
        }
    })

@docs_api.route('/analytics')
def analytics_docs():
    """Detailed analytics API documentation"""
    return jsonify({
        "endpoint": "/api/v1/analytics/",
        "description": "Analytics and reporting endpoints",
        "endpoints": {
            "dashboard_stats": {
                "method": "GET",
                "description": "Get comprehensive dashboard statistics",
                "parameters": {
                    "range": "Time range (today, week, month, quarter, year, all)"
                },
                "response": {
                    "revenue": "Revenue analytics",
                    "transactions": "Transaction counts",
                    "psps": "PSP statistics",
                    "trends": "Performance trends"
                }
            },
            "system_performance": {
                "method": "GET",
                "description": "Get system performance metrics",
                "response": {
                    "cpu": "CPU usage percentage",
                    "memory": "Memory usage statistics",
                    "database": "Database performance metrics",
                    "cache": "Cache performance statistics"
                }
            },
            "data_quality": {
                "method": "GET",
                "description": "Get data quality metrics",
                "response": {
                    "completeness": "Data completeness percentage",
                    "accuracy": "Data accuracy metrics",
                    "consistency": "Data consistency checks",
                    "issues": "Data quality issues found"
                }
            }
        }
    })

@docs_api.route('/performance')
def performance_docs():
    """Detailed performance API documentation"""
    return jsonify({
        "endpoint": "/api/v1/performance/",
        "description": "Performance monitoring and optimization endpoints",
        "endpoints": {
            "metrics": {
                "method": "GET",
                "description": "Get comprehensive performance metrics",
                "response": {
                    "system": "System resource usage",
                    "cache": "Cache performance statistics",
                    "queries": "Database query performance",
                    "security": "Security metrics"
                }
            },
            "cache_management": {
                "stats": {
                    "method": "GET",
                    "description": "Get cache statistics"
                },
                "clear": {
                    "method": "POST",
                    "description": "Clear all cache entries"
                }
            },
            "query_optimization": {
                "stats": {
                    "method": "GET", 
                    "description": "Get query performance statistics"
                },
                "optimize": {
                    "method": "POST",
                    "description": "Run query optimization"
                }
            },
            "health": {
                "method": "GET",
                "description": "Get detailed system health status",
                "response": {
                    "status": "Overall health status",
                    "components": "Individual component status",
                    "issues": "Any issues found"
                }
            }
        }
    })

@docs_api.route('/examples')
def api_examples():
    """API usage examples"""
    return jsonify({
        "examples": {
            "get_transactions": {
                "description": "Get paginated transactions",
                "request": {
                    "method": "GET",
                    "url": "/api/v1/transactions/?page=1&per_page=20&sort_by=created_at&sort_order=desc",
                    "headers": {
                        "Authorization": "Session cookie required"
                    }
                },
                "response": {
                    "status": 200,
                    "data": {
                        "transactions": [
                            {
                                "id": 1,
                                "amount": 1000.00,
                                "currency": "TRY",
                                "psp": "SİPAY",
                                "client_name": "Client A",
                                "date": "2025-09-23",
                                "created_at": "2025-09-23T14:24:15Z"
                            }
                        ],
                        "pagination": {
                            "page": 1,
                            "per_page": 20,
                            "total": 100,
                            "pages": 5
                        }
                    }
                }
            },
            "create_transaction": {
                "description": "Create a new transaction",
                "request": {
                    "method": "POST",
                    "url": "/api/v1/transactions/",
                    "headers": {
                        "Content-Type": "application/json",
                        "X-CSRFToken": "csrf_token_here"
                    },
                    "body": {
                        "amount": 2500.00,
                        "currency": "TRY",
                        "psp": "SİPAY",
                        "client_name": "Client B",
                        "date": "2025-09-23",
                        "category": "Payment",
                        "description": "Monthly payment"
                    }
                },
                "response": {
                    "status": 201,
                    "data": {
                        "transaction": {
                            "id": 2,
                            "amount": 2500.00,
                            "currency": "TRY",
                            "psp": "SİPAY",
                            "client_name": "Client B",
                            "date": "2025-09-23",
                            "created_at": "2025-09-23T14:24:15Z"
                        },
                        "message": "Transaction created successfully"
                    }
                }
            },
            "get_analytics": {
                "description": "Get dashboard analytics",
                "request": {
                    "method": "GET",
                    "url": "/api/v1/analytics/dashboard/stats?range=month",
                    "headers": {
                        "Authorization": "Session cookie required"
                    }
                },
                "response": {
                    "status": 200,
                    "data": {
                        "revenue": {
                            "total": 150000.00,
                            "daily": 5000.00,
                            "trend": 12.5
                        },
                        "transactions": {
                            "total": 1500,
                            "daily": 50,
                            "trend": 8.3
                        },
                        "psps": [
                            {
                                "name": "SİPAY",
                                "amount": 75000.00,
                                "percentage": 50.0
                            }
                        ]
                    }
                }
            }
        }
    })

@docs_api.route('/openapi.json')
@docs_api.route('/openapi')
def openapi_spec():
    """OpenAPI 3.0 specification - Comprehensive and auto-generated"""
    try:
        spec = generate_openapi_spec()
        return jsonify(spec)
    except Exception as e:
        logger.error(f"Error generating OpenAPI spec: {e}")
        return jsonify({
            "error": "Failed to generate API documentation",
            "message": str(e)
        }), 500


@docs_api.route('/swagger')
def swagger_ui():
    """Serve Swagger UI for interactive API documentation"""
    from flask import Response, render_template_string
    
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PipLinePro API Documentation - Swagger UI</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.10.5/swagger-ui.css" />
    <style>
        html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
        *, *:before, *:after { box-sizing: inherit; }
        body { margin:0; background: #fafafa; }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.10.5/swagger-ui-bundle.js" charset="UTF-8"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.10.5/swagger-ui-standalone-preset.js" charset="UTF-8"></script>
    <script>
        window.onload = function() {
            const ui = SwaggerUIBundle({
                url: "/api/v1/docs/openapi.json",
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                validatorUrl: null
            });
            window.ui = ui;
        };
    </script>
</body>
</html>
    """
    
    try:
        return render_template_string(html)
    except Exception as e:
        logger.error(f"Error rendering Swagger UI template: {e}", exc_info=True)
        return Response(html, mimetype='text/html')


@docs_api.route('/redoc')
def redoc_ui():
    """Serve ReDoc UI for alternative API documentation view"""
    from flask import Response, render_template_string
    
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>PipLinePro API Documentation - ReDoc</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
    <style>
        body { margin: 0; padding: 0; }
    </style>
</head>
<body>
    <redoc spec-url="/api/v1/docs/openapi.json"></redoc>
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
</body>
</html>
    """
    
    try:
        return render_template_string(html)
    except Exception as e:
        logger.error(f"Error rendering ReDoc UI template: {e}", exc_info=True)
        return Response(html, mimetype='text/html')
