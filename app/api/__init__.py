"""
FastAPI Application for PipLine Treasury System
NOTE: This FastAPI app is currently disabled to avoid conflicts with Flask Blueprints.
The main application uses Flask Blueprints for API endpoints.
"""
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.middleware.trustedhost import TrustedHostMiddleware
# import os

# from app.api.v1 import api_v1

# def create_fastapi_app():
#     """Create and configure FastAPI application"""
#     app = FastAPI(
#         title="PipLine API",
#         description="Treasury Management System API",
#         version="1.0.0",
#         docs_url="/api/docs",
#         redoc_url="/api/redoc",
#         openapi_url="/api/openapi.json"
#     )
    
#     @app.get("/")
#     async def root():
#         """Root endpoint with API information"""
#         return {
#             "message": "Welcome to PipLine Treasury System API",
#             "version": "1.0.0",
#             "status": "active",
#             "documentation": "/api/docs",
#             "api_base": "/api/v1",
#             "endpoints": {
#                 "health": "/api/v1/health",
#                 "transactions": "/api/v1/transactions",
#                 "analytics": "/api/v1/analytics",
#                 "users": "/api/v1/users"
#             }
#         }
    
#     # CORS middleware for frontend integration
#     app.add_middleware(
#         CORSMiddleware,
#         allow_origins=[
#             "http://localhost:3000",  # React dev server
#             "http://localhost:5173",  # Vite dev server
#             "https://yourdomain.com"  # Production domain
#         ],
#         allow_credentials=True,
#         allow_methods=["*"],
#         allow_headers=["*"],
#     )
    
#     # Security middleware
#     app.add_middleware(
#         TrustedHostMiddleware,
#         allowed_hosts=["localhost", "127.0.0.1", "yourdomain.com"]
#     )
    
#     # Include API routes
#     app.include_router(api_v1, prefix="/api/v1")
    
#     return app

# # Create the FastAPI app instance
# fastapi_app = create_fastapi_app()
