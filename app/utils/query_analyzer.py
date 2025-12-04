"""
Query Analyzer
Analyzes SQL queries for optimization opportunities
"""
import logging
import re
from typing import Dict, List, Any, Optional
from sqlalchemy import text
from app import db
from app.utils.db_compat import get_database_type

logger = logging.getLogger(__name__)


class QueryAnalyzer:
    """Analyze queries for performance issues"""
    
    @staticmethod
    def analyze_query_sql(sql: str) -> Dict[str, Any]:
        """
        Analyze SQL query for potential issues
        
        Args:
            sql: SQL query string
        
        Returns:
            Dictionary with analysis results
        """
        issues = []
        recommendations = []
        
        sql_upper = sql.upper()
        
        # Check for SELECT *
        if re.search(r'SELECT\s+\*', sql_upper):
            issues.append('SELECT * detected - consider selecting specific columns')
            recommendations.append('Replace SELECT * with specific column names')
        
        # Check for missing WHERE clause in DELETE/UPDATE
        if re.search(r'(DELETE|UPDATE)\s+\w+\s+(?!WHERE)', sql_upper):
            issues.append('DELETE/UPDATE without WHERE clause - potential data loss risk')
        
        # Check for LIKE without index
        if re.search(r'LIKE\s+[\'"]%', sql_upper):
            issues.append('LIKE with leading wildcard - cannot use index efficiently')
            recommendations.append('Consider full-text search or different pattern')
        
        # Check for multiple JOINs
        join_count = len(re.findall(r'\bJOIN\b', sql_upper))
        if join_count > 5:
            issues.append(f'Multiple JOINs detected ({join_count}) - consider query optimization')
            recommendations.append('Break into multiple queries or use materialized views')
        
        # Check for subqueries
        subquery_count = len(re.findall(r'\(\s*SELECT', sql_upper))
        if subquery_count > 3:
            issues.append(f'Multiple subqueries detected ({subquery_count}) - consider JOINs')
            recommendations.append('Convert subqueries to JOINs for better performance')
        
        # Check for ORDER BY without LIMIT
        if 'ORDER BY' in sql_upper and 'LIMIT' not in sql_upper:
            issues.append('ORDER BY without LIMIT - may return large result set')
            recommendations.append('Add LIMIT clause or pagination')
        
        # Check for functions in WHERE clause
        if re.search(r'WHERE\s+.*\(.*\)', sql_upper):
            issues.append('Functions in WHERE clause - may prevent index usage')
            recommendations.append('Move function to SELECT or use computed columns')
        
        return {
            'issues': issues,
            'recommendations': recommendations,
            'join_count': join_count,
            'subquery_count': subquery_count,
            'complexity': 'high' if (join_count > 3 or subquery_count > 2) else 'medium' if (join_count > 1 or subquery_count > 0) else 'low'
        }
    
    @staticmethod
    def explain_query(sql: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Get query execution plan (EXPLAIN)
        
        Args:
            sql: SQL query string
            params: Query parameters
        
        Returns:
            List of execution plan rows
        """
        db_type = get_database_type()
        
        try:
            if db_type == 'postgresql':
                explain_sql = f"EXPLAIN ANALYZE {sql}"
            elif db_type == 'mysql':
                explain_sql = f"EXPLAIN {sql}"
            elif db_type == 'sqlite':
                explain_sql = f"EXPLAIN QUERY PLAN {sql}"
            else:
                logger.warning(f"EXPLAIN not supported for {db_type}")
                return []
            
            result = db.session.execute(text(explain_sql), params or {})
            
            # Convert to list of dicts
            columns = result.keys()
            plan = [dict(zip(columns, row)) for row in result.fetchall()]
            
            return plan
        except Exception as e:
            logger.error(f"Error explaining query: {e}")
            return []
    
    @staticmethod
    def suggest_indexes(sql: str, table_name: str) -> List[str]:
        """
        Suggest indexes based on query patterns
        
        Args:
            sql: SQL query string
            table_name: Table name
        
        Returns:
            List of suggested index SQL statements
        """
        suggestions = []
        sql_upper = sql.upper()
        
        # Extract WHERE conditions
        where_match = re.search(r'WHERE\s+(.+?)(?:\s+GROUP\s+BY|\s+ORDER\s+BY|\s+LIMIT|$)', sql_upper, re.IGNORECASE | re.DOTALL)
        if where_match:
            where_clause = where_match.group(1)
            
            # Find column names in WHERE
            column_pattern = r'\b(\w+)\s*[=<>]'
            columns = re.findall(column_pattern, where_clause)
            
            if columns:
                # Suggest index on WHERE columns
                index_name = f"idx_{table_name}_{'_'.join(columns[:3])}"
                suggestions.append(
                    f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({', '.join(columns[:3])})"
                )
        
        # Extract ORDER BY columns
        order_match = re.search(r'ORDER\s+BY\s+(.+?)(?:\s+LIMIT|$)', sql_upper, re.IGNORECASE)
        if order_match:
            order_clause = order_match.group(1)
            # Remove ASC/DESC keywords
            order_clause = re.sub(r'\s+(ASC|DESC)', '', order_clause, flags=re.IGNORECASE)
            columns = [col.strip() for col in order_clause.split(',')]
            
            if columns:
                index_name = f"idx_{table_name}_order_{'_'.join(columns[:2])}"
                suggestions.append(
                    f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({', '.join(columns[:2])})"
                )
        
        return suggestions

