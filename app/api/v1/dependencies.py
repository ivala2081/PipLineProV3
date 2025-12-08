"""
API dependencies for authentication and database access

NOTE: FastAPI is currently disabled. This application uses Flask with
Flask-Login for session-based authentication.

This file is kept for potential future FastAPI migration but is not active.
All authentication should use Flask-Login's @login_required decorator.
"""
# FastAPI dependencies (DISABLED - not currently used)
# from fastapi import Depends, HTTPException, status
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# from sqlalchemy.orm import Session
# from typing import Optional
# 
# from app import db
# from app.models.user import User
# from app.utils.auth import get_current_user_id
# 
# # Security scheme
# security = HTTPBearer()
# 
# def get_db() -> Session:
#     """Get database session"""
#     try:
#         database = db.session
#         yield database
#     finally:
#         database.close()
# 
# def get_current_user(
#     credentials: HTTPAuthorizationCredentials = Depends(security),
#     database: Session = Depends(get_db)
# ) -> User:
#     """Get current authenticated user"""
#     try:
#         user_id = get_current_user_id()
#         
#         if not user_id:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid authentication credentials",
#                 headers={"WWW-Authenticate": "Bearer"},
#             )
#         
#         user = database.query(User).filter(User.id == user_id).first()
#         if not user:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="User not found",
#                 headers={"WWW-Authenticate": "Bearer"},
#             )
#         
#         if not user.is_active:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="User account is inactive",
#                 headers={"WWW-Authenticate": "Bearer"},
#             )
#         
#         return user
#         
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Authentication failed",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
# 
# def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
#     """Get current active user"""
#     if not current_user.is_active:
#         raise HTTPException(status_code=400, detail="Inactive user")
#     return current_user
# 
# def require_admin(current_user: User = Depends(get_current_user)) -> User:
#     """Require admin privileges"""
#     if current_user.role != 'admin':
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Admin privileges required"
#         )
#     return current_user

# Placeholder to prevent import errors
pass
