"""
Index Optimization Service
Verifies existing indexes, identifies missing indexes, and provides recommendations
"""
import logging
from typing import Dict, List, Tuple, Any
from sqlalchemy import text, inspect
from flask import current_app
from app import db

logger = logging.getLogger(__name__)


class IndexOptimizationService:
    """Service for database index management and optimization"""
    
    def __init__(self):
        self.db_dialect = None
    
    def _get_db_dialect(self):
        """Get database dialect"""
        if self.db_dialect is None:
            engine = db.engine
            self.db_dialect = engine.dialect.name
        return self.db_dialect
    
    def get_existing_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Get all existing indexes for a table"""
        try:
            dialect = self._get_db_dialect()
            indexes = []
            
            if dialect == 'sqlite':
                # SQLite query
                result = db.session.execute(text(f"""
                    SELECT 
                        name as index_name,
                        sql
                    FROM sqlite_master
                    WHERE type='index' 
                    AND tbl_name='{table_name}'
                    AND sql IS NOT NULL
                """))
                for row in result:
                    indexes.append({
                        'name': row[0],
                        'sql': row[1],
                        'columns': self._extract_columns_from_sql(row[1])
                    })
            elif dialect == 'postgresql':
                # PostgreSQL query
                result = db.session.execute(text(f"""
                    SELECT
                        i.relname as index_name,
                        a.attname as column_name,
                        am.amname as index_type
                    FROM pg_class t
                    JOIN pg_index ix ON t.oid = ix.indrelid
                    JOIN pg_class i ON i.oid = ix.indexrelid
                    JOIN pg_am am ON i.relam = am.oid
                    JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
                    WHERE t.relname = '{table_name}'
                    ORDER BY i.relname, a.attnum
                """))
                # Group by index name
                index_dict = {}
                for row in result:
                    idx_name = row[0]
                    if idx_name not in index_dict:
                        index_dict[idx_name] = {
                            'name': idx_name,
                            'columns': [],
                            'type': row[2]
                        }
                    index_dict[idx_name]['columns'].append(row[1])
                indexes = list(index_dict.values())
            
            return indexes
        except Exception as e:
            logger.error(f"Error getting existing indexes for {table_name}: {e}")
            return []
    
    def _extract_columns_from_sql(self, sql: str) -> List[str]:
        """Extract column names from CREATE INDEX SQL"""
        import re
        if not sql:
            return []
        # Match CREATE INDEX ... ON table (col1, col2, ...)
        match = re.search(r'\(([^)]+)\)', sql)
        if match:
            cols = [col.strip().strip('"') for col in match.group(1).split(',')]
            return cols
        return []
    
    def verify_index_exists(self, table_name: str, index_name: str) -> bool:
        """Verify if an index exists"""
        existing = self.get_existing_indexes(table_name)
        return any(idx['name'] == index_name for idx in existing)
    
    def get_index_recommendations(self) -> Dict[str, Any]:
        """Analyze query patterns and recommend indexes"""
        recommendations = {
            'missing_indexes': [],
            'redundant_indexes': [],
            'suggestions': []
        }
        
        # Critical indexes for transaction table based on common query patterns
        critical_indexes = {
            'transactions': [
                # Single column indexes (already in migration)
                ('idx_transaction_date', ['date']),
                ('idx_transaction_created_at', ['created_at']),
                ('idx_transaction_psp', ['psp']),
                ('idx_transaction_client_name', ['client_name']),
                ('idx_transaction_category', ['category']),
                
                # Composite indexes for common query patterns
                ('idx_transaction_date_category', ['date', 'category']),
                ('idx_transaction_date_psp', ['date', 'psp']),
                ('idx_transaction_psp_category', ['psp', 'category']),
                ('idx_transaction_client_date', ['client_name', 'date']),
            ],
            'psp_track': [
                ('idx_psp_track_date_psp', ['date', 'psp_name']),
                ('idx_psp_track_psp_date', ['psp_name', 'date']),
            ],
            'psp_allocation': [
                ('idx_psp_allocation_date_psp', ['date', 'psp_name']),
                ('idx_psp_allocation_psp_date', ['psp_name', 'date']),
            ],
            'psp_devir': [
                ('idx_psp_devir_date_psp', ['date', 'psp_name']),
                ('idx_psp_devir_psp_date', ['psp_name', 'date']),
            ],
            'audit_logs': [
                ('idx_audit_user_id', ['user_id']),  # Match model definition
                ('idx_audit_timestamp', ['timestamp']),  # Match model definition
                ('idx_audit_action', ['action']),  # Match model definition
                ('idx_audit_user_timestamp', ['user_id', 'timestamp']),  # Composite for common queries - matches model definition
            ],
            'user_sessions': [
                ('idx_session_user_id', ['user_id']),
                ('idx_session_token', ['session_token']),
                ('idx_session_is_active', ['is_active']),
                ('idx_session_last_active', ['last_active']),
            ],
            'login_attempts': [
                ('idx_login_username', ['username']),
                ('idx_login_timestamp', ['timestamp']),
                ('idx_login_success', ['success']),
                ('idx_login_username_timestamp', ['username', 'timestamp']),  # Composite for user login history
            ],
        }
        
        # Check each table
        for table_name, indexes in critical_indexes.items():
            try:
                existing_indexes = self.get_existing_indexes(table_name)
                existing_names = {idx['name'] for idx in existing_indexes}
                
                for idx_name, columns in indexes:
                    if idx_name not in existing_names:
                        recommendations['missing_indexes'].append({
                            'table': table_name,
                            'index': idx_name,
                            'columns': columns,
                            'priority': 'high'
                        })
            except Exception as e:
                logger.warning(f"Could not check indexes for {table_name}: {e}")
        
        return recommendations
    
    def create_missing_indexes(self) -> Dict[str, Any]:
        """Create missing critical indexes"""
        recommendations = self.get_index_recommendations()
        created = []
        failed = []
        
        for idx_info in recommendations['missing_indexes']:
            try:
                table_name = idx_info['table']
                index_name = idx_info['index']
                columns = idx_info['columns']
                
                # Build CREATE INDEX statement
                columns_str = ', '.join(f'"{col}"' if self._get_db_dialect() == 'sqlite' else col for col in columns)
                sql = f'CREATE INDEX IF NOT EXISTS {index_name} ON "{table_name}" ({columns_str})'
                
                db.session.execute(text(sql))
                created.append({
                    'table': table_name,
                    'index': index_name,
                    'columns': columns
                })
                logger.info(f"Created index: {index_name} on {table_name}({columns_str})")
            except Exception as e:
                failed.append({
                    'index': idx_info['index'],
                    'error': str(e)
                })
                logger.error(f"Failed to create index {idx_info['index']}: {e}")
        
        if created:
            db.session.commit()
            logger.info(f"Created {len(created)} missing indexes")
        
        return {
            'created': created,
            'failed': failed,
            'total_created': len(created)
        }


# Global instance
index_optimization_service = IndexOptimizationService()

