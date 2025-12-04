"""
Database Compatibility Utilities
Provides database-agnostic functions for cross-database compatibility
"""
import os
from sqlalchemy import func
from flask import current_app


def get_database_type():
    """Get current database type from environment or connection string - SQLite is default"""
    # PRIORITY 1: Check DATABASE_TYPE environment variable first (highest priority)
    # This ensures explicit configuration is always respected
    db_type_env = os.environ.get('DATABASE_TYPE', '').strip().lower()
    if db_type_env:
        if db_type_env in ['mssql', 'sqlserver']:
            return 'mssql'
        elif db_type_env in ['postgresql', 'postgres']:
            return 'postgresql'
        elif db_type_env == 'sqlite':
            return 'sqlite'
        # If DATABASE_TYPE is explicitly set but unknown, default to SQLite
        return 'sqlite'
    
    # PRIORITY 2: Try to detect from actual connection string (if app is initialized)
    try:
        if current_app:
            db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
            if db_uri:
                if 'mssql' in db_uri.lower() or 'sqlserver' in db_uri.lower() or 'pyodbc' in db_uri.lower():
                    return 'mssql'
                elif 'postgresql' in db_uri.lower() or 'postgres' in db_uri.lower() or 'psycopg2' in db_uri.lower():
                    return 'postgresql'
                elif 'sqlite' in db_uri.lower():
                    return 'sqlite'
    except:
        pass
    
    # PRIORITY 3: If no explicit DATABASE_TYPE, check for MSSQL credentials
    # But only if explicitly configured (not just environment variable pollution)
    # This is a fallback for legacy configurations
    mssql_host = os.environ.get('MSSQL_HOST')
    if mssql_host:
        # Only return MSSQL if all required MSSQL vars are present
        if all([os.environ.get('MSSQL_DB'), os.environ.get('MSSQL_USER'), os.environ.get('MSSQL_PASSWORD')]):
            return 'mssql'
    
    # Default to SQLite if no explicit database type is set
    # This matches the default behavior in config.py
    return 'sqlite'


def ilike_compat(column, pattern):
    """
    Database-agnostic case-insensitive LIKE operation
    Uses ILIKE for PostgreSQL, UPPER() + LIKE for MSSQL
    """
    db_type = get_database_type()
    
    # If db_type is None, try to detect from connection string
    if db_type is None:
        try:
            if current_app:
                db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
                if 'mssql' in db_uri.lower() or 'sqlserver' in db_uri.lower() or 'pyodbc' in db_uri.lower():
                    db_type = 'mssql'
                else:
                    db_type = 'postgresql'  # Default to PostgreSQL/SQLite compatible
        except:
            db_type = 'postgresql'  # Safe fallback
    
    if db_type == 'mssql':
        # MSSQL doesn't support ILIKE, use UPPER() + LIKE
        return func.upper(column).like(func.upper(pattern))
    else:
        # PostgreSQL and SQLite support ILIKE
        return column.ilike(pattern)


def extract_compat(column, part):
    """
    Database-agnostic date/time extraction
    Uses EXTRACT for PostgreSQL, DATEPART for MSSQL
    """
    db_type = get_database_type()
    
    # If db_type is None, try to detect from connection string
    if db_type is None:
        try:
            if current_app:
                db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
                if 'mssql' in db_uri.lower() or 'sqlserver' in db_uri.lower() or 'pyodbc' in db_uri.lower():
                    db_type = 'mssql'
                else:
                    db_type = 'postgresql'  # Default to PostgreSQL/SQLite compatible
        except:
            db_type = 'postgresql'  # Safe fallback
    
    if db_type == 'mssql':
        # MSSQL uses DATEPART
        part_mapping = {
            'year': 'year',
            'month': 'month',
            'day': 'day',
            'hour': 'hour',
            'minute': 'minute',
            'second': 'second',
            'dow': 'weekday',  # Day of week
            'doy': 'dayofyear'  # Day of year
        }
        mssql_part = part_mapping.get(part.lower(), part.lower())
        return func.datepart(mssql_part, column)
    else:
        # PostgreSQL uses EXTRACT
        return func.extract(part, column)

