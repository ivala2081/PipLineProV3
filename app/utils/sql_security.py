"""
SQL Security Utilities for PipLine Treasury System
Provides comprehensive protection against SQL injection attacks
"""
import re
import logging
from typing import List, Dict, Any, Optional, Union
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

class SQLSecurityValidator:
    """Validator for SQL security to prevent injection attacks"""
    
    # Dangerous SQL keywords that could be used for injection
    DANGEROUS_KEYWORDS = [
        'drop', 'delete', 'truncate', 'alter', 'create', 'insert', 'update',
        'grant', 'revoke', 'exec', 'execute', 'xp_', 'sp_', 'backup', 'restore',
        'shutdown', 'kill', 'waitfor', 'delay', 'begin', 'commit', 'rollback'
    ]
    
    # Suspicious patterns that could indicate injection attempts
    SUSPICIOUS_PATTERNS = [
        '--',  # SQL comments
        '/*',  # Multi-line comments
        '*/',
        'union',  # UNION attacks
        'information_schema',  # System tables
        'sys.tables', 'sys.columns', 'sys.databases',
        'master..', 'tempdb..', 'model..', 'msdb..',
        'xp_cmdshell', 'sp_configure', 'sp_executesql',
        'char(', 'nchar(', 'varchar(', 'nvarchar(',
        'cast(', 'convert(', 'substring(', 'len(',
        'ascii(', 'charindex(', 'patindex('
    ]
    
    # Allowed table names (whitelist approach)
    ALLOWED_TABLES = {
        'transaction', 'user', 'option', 'exchange_rate', 
        'psp_track', 'daily_balance', 'audit_log', 'user_session',
        'user_settings', 'employee', 'reconciliation'
    }
    
    # Allowed column names (whitelist approach)
    ALLOWED_COLUMNS = {
        'id', 'username', 'password', 'role', 'admin_level', 'admin_permissions',
        'created_by', 'created_at', 'is_active', 'profile_picture', 'last_login',
        'failed_login_attempts', 'account_locked_until', 'password_changed_at', 'email',
        'client_name', 'iban', 'payment_method', 'company_order', 'date', 'category',
        'amount', 'commission', 'net_amount', 'currency', 'psp', 'notes', 'updated_at',
        'field_name', 'value', 'is_active', 'usd_to_tl', 'eur_to_tl', 'currency',
        'psp_name', 'withdraw', 'commission_amount', 'difference', 'allocation',
        'balance', 'session_token', 'ip_address', 'user_agent', 'action', 'details',
        'net_salary', 'insurance', 'deducted_amount', 'advance', 'usd_rate',
        'final_salary', 'salary_in_usd', 'department', 'working_status', 'company_name',
        'stage_name', 'total_amount', 'total_commission', 'total_net', 'transaction_count'
    }
    
    @classmethod
    def validate_sql_statement(cls, statement: str) -> bool:
        """
        Validate SQL statement to prevent injection attacks
        
        Args:
            statement: SQL statement to validate
            
        Returns:
            bool: True if safe, False if dangerous
        """
        if not statement or not isinstance(statement, str):
            return False
        
        # Convert to lowercase for case-insensitive checking
        stmt_lower = statement.lower().strip()
        
        # Check for dangerous keywords
        for keyword in cls.DANGEROUS_KEYWORDS:
            if keyword in stmt_lower:
                logger.warning(f"Dangerous SQL keyword detected: {keyword}")
                return False
        
        # Check for suspicious patterns
        for pattern in cls.SUSPICIOUS_PATTERNS:
            if pattern in stmt_lower:
                logger.warning(f"Suspicious SQL pattern detected: {pattern}")
                return False
        
        # Check for multiple statements (batch injection)
        if ';' in stmt_lower and stmt_lower.count(';') > 1:
            logger.warning("Multiple SQL statements detected")
            return False
        
        return True
    
    @classmethod
    def validate_table_name(cls, table_name: str) -> bool:
        """
        Validate table name to prevent injection
        
        Args:
            table_name: Table name to validate
            
        Returns:
            bool: True if safe, False if dangerous
        """
        if not table_name or not isinstance(table_name, str):
            return False
        
        # Check against whitelist
        if table_name.lower() not in cls.ALLOWED_TABLES:
            logger.warning(f"Table name not in whitelist: {table_name}")
            return False
        
        # Check for valid characters (alphanumeric and underscore only)
        if not re.match(r'^[a-zA-Z0-9_]+$', table_name):
            logger.warning(f"Invalid characters in table name: {table_name}")
            return False
        
        return True
    
    @classmethod
    def validate_column_name(cls, column_name: str) -> bool:
        """
        Validate column name to prevent injection
        
        Args:
            column_name: Column name to validate
            
        Returns:
            bool: True if safe, False if dangerous
        """
        if not column_name or not isinstance(column_name, str):
            return False
        
        # Check against whitelist
        if column_name.lower() not in cls.ALLOWED_COLUMNS:
            logger.warning(f"Column name not in whitelist: {column_name}")
            return False
        
        # Check for valid characters (alphanumeric and underscore only)
        if not re.match(r'^[a-zA-Z0-9_]+$', column_name):
            logger.warning(f"Invalid characters in column name: {column_name}")
            return False
        
        return True
    
    @classmethod
    def validate_column_list(cls, columns: List[str]) -> bool:
        """
        Validate list of column names
        
        Args:
            columns: List of column names to validate
            
        Returns:
            bool: True if all safe, False if any dangerous
        """
        if not columns or not isinstance(columns, list):
            return False
        
        for column in columns:
            if not cls.validate_column_name(column):
                return False
        
        return True
    
    @classmethod
    def sanitize_identifier(cls, identifier: str) -> str:
        """
        Sanitize SQL identifier (table/column name)
        
        Args:
            identifier: Identifier to sanitize
            
        Returns:
            str: Sanitized identifier
        """
        if not identifier or not isinstance(identifier, str):
            return ''
        
        # Remove any non-alphanumeric characters except underscore
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '', identifier)
        
        # Ensure it doesn't start with a number
        if sanitized and sanitized[0].isdigit():
            sanitized = 'id_' + sanitized
        
        return sanitized

class SecureSQLExecutor:
    """Secure SQL executor with built-in injection protection"""
    
    def __init__(self, db_session):
        self.db_session = db_session
        self.validator = SQLSecurityValidator()
    
    def execute_safe_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a safe SQL query with validation
        
        Args:
            query: SQL query to execute
            parameters: Query parameters
            
        Returns:
            Query result
            
        Raises:
            ValueError: If query is unsafe
            SQLAlchemyError: If query execution fails
        """
        # Validate the query
        if not self.validator.validate_sql_statement(query):
            raise ValueError("Unsafe SQL statement detected")
        
        try:
            # Execute with parameters
            result = self.db_session.execute(text(query), parameters or {})
            return result
        except SQLAlchemyError as e:
            logger.error(f"SQL execution failed: {str(e)}")
            raise
    
    def execute_safe_select(self, table: str, columns: Optional[List[str]] = None, 
                          where_clause: Optional[str] = None, 
                          parameters: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a safe SELECT query
        
        Args:
            table: Table name
            columns: List of columns to select (None for all)
            where_clause: WHERE clause (optional)
            parameters: Query parameters
            
        Returns:
            Query result
        """
        # Validate table name
        if not self.validator.validate_table_name(table):
            raise ValueError(f"Invalid table name: {table}")
        
        # Build SELECT clause
        if columns:
            if not self.validator.validate_column_list(columns):
                raise ValueError("Invalid column names")
            select_clause = ', '.join(columns)
        else:
            select_clause = '*'
        
        # Build query
        query = f"SELECT {select_clause} FROM {table}"
        
        if where_clause:
            # Validate WHERE clause
            if not self.validator.validate_sql_statement(where_clause):
                raise ValueError("Unsafe WHERE clause")
            query += f" WHERE {where_clause}"
        
        return self.execute_safe_query(query, parameters)
    
    def execute_safe_count(self, table: str, where_clause: Optional[str] = None,
                          parameters: Optional[Dict[str, Any]] = None) -> int:
        """
        Execute a safe COUNT query
        
        Args:
            table: Table name
            where_clause: WHERE clause (optional)
            parameters: Query parameters
            
        Returns:
            Count result
        """
        # Validate table name
        if not self.validator.validate_table_name(table):
            raise ValueError(f"Invalid table name: {table}")
        
        # Build query
        query = f"SELECT COUNT(*) FROM {table}"
        
        if where_clause:
            # Validate WHERE clause
            if not self.validator.validate_sql_statement(where_clause):
                raise ValueError("Unsafe WHERE clause")
            query += f" WHERE {where_clause}"
        
        result = self.execute_safe_query(query, parameters)
        return result.scalar()

def create_secure_executor(db_session) -> SecureSQLExecutor:
    """
    Create a secure SQL executor instance
    
    Args:
        db_session: Database session
        
    Returns:
        SecureSQLExecutor: Secure executor instance
    """
    return SecureSQLExecutor(db_session)

def validate_and_execute_query(db_session, query: str, parameters: Optional[Dict[str, Any]] = None) -> Any:
    """
    Validate and execute a SQL query safely
    
    Args:
        db_session: Database session
        query: SQL query to execute
        parameters: Query parameters
        
    Returns:
        Query result
        
    Raises:
        ValueError: If query is unsafe
        SQLAlchemyError: If query execution fails
    """
    validator = SQLSecurityValidator()
    
    # Validate the query
    if not validator.validate_sql_statement(query):
        raise ValueError("Unsafe SQL statement detected")
    
    try:
        # Execute with parameters
        result = db_session.execute(text(query), parameters or {})
        return result
    except SQLAlchemyError as e:
        logger.error(f"SQL execution failed: {str(e)}")
        raise 