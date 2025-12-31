"""
Unified Database Service for PipLinePro
Consolidates database_optimization_service, db_optimization, and query_optimization_service
"""
import logging
import time
import re
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timezone
from sqlalchemy import text, inspect, Index
from flask import current_app
from app import db
from app.utils.db_compat import get_database_type

logger = logging.getLogger(__name__)


class UnifiedDatabaseService:
    """
    Unified service for all database operations including:
    - Performance optimization
    - Index management
    - Query monitoring
    - Health checks
    - Statistics gathering
    """
    
    def __init__(self):
        self.slow_query_threshold = 1.0  # seconds
        self._query_stats = {}
        self._slow_queries = []
    
    # ========================================================================
    # INDEX MANAGEMENT
    # ========================================================================
    
    @staticmethod
    def _extract_index_name(index_sql):
        """Extract index name from CREATE INDEX SQL statement"""
        try:
            match = re.search(r'idx_[\w]+', index_sql)
            if match:
                return match.group(0)
            match = re.search(r'INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)', index_sql, re.IGNORECASE)
            if match:
                return match.group(1)
            return "unknown_index"
        except Exception:
            return "unknown_index"
    
    @staticmethod
    def _convert_index_sql_for_mssql(index_sql: str) -> str:
        """Convert PostgreSQL/SQLite CREATE INDEX IF NOT EXISTS to MSSQL syntax"""
        # Extract index name, table name, and columns from SQL
        # Pattern: CREATE INDEX IF NOT EXISTS idx_name ON "table"(columns)
        import re
        
        # Extract index name
        index_match = re.search(r'CREATE INDEX IF NOT EXISTS (\w+)', index_sql, re.IGNORECASE)
        if not index_match:
            return index_sql  # Return original if pattern doesn't match
        
        index_name = index_match.group(1)
        
        # Extract table name (with or without quotes)
        table_match = re.search(r'ON\s+["\']?(\w+)["\']?', index_sql, re.IGNORECASE)
        if not table_match:
            return index_sql
        
        table_name = table_match.group(1)
        
        # Extract columns (everything between parentheses)
        columns_match = re.search(r'\(([^)]+)\)', index_sql)
        if not columns_match:
            return index_sql
        
        columns = columns_match.group(1)
        
        # Build MSSQL syntax: IF NOT EXISTS (SELECT...) BEGIN CREATE INDEX... END
        mssql_sql = f"""
        IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = '{index_name}' AND object_id = OBJECT_ID('{table_name}'))
        BEGIN
            CREATE INDEX {index_name} ON {table_name}({columns})
        END
        """
        return mssql_sql.strip()
    
    @staticmethod
    def create_performance_indexes():
        """Create performance indexes for better query performance"""
        try:
            # Get database type - check actual connection string if not available
            db_type = get_database_type()
            if db_type is None:
                # Fallback: check actual database URI
                try:
                    db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
                    if 'mssql' in db_uri.lower() or 'sqlserver' in db_uri.lower() or 'pyodbc' in db_uri.lower():
                        db_type = 'mssql'
                    elif 'postgresql' in db_uri.lower() or 'postgres' in db_uri.lower():
                        db_type = 'postgresql'
                    elif 'sqlite' in db_uri.lower():
                        db_type = 'sqlite'
                    else:
                        db_type = 'sqlite'  # Default fallback
                except:
                    db_type = 'sqlite'  # Safe fallback
            
            indexes_to_create = [
                # Transaction table indexes - Critical for most queries
                # Single column indexes (frequently filtered)
                "CREATE INDEX IF NOT EXISTS idx_transaction_date ON \"transactions\"(date)",
                "CREATE INDEX IF NOT EXISTS idx_transaction_created_at ON \"transactions\"(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_transaction_psp ON \"transactions\"(psp)",
                "CREATE INDEX IF NOT EXISTS idx_transaction_client_name ON \"transactions\"(client_name)",
                "CREATE INDEX IF NOT EXISTS idx_transaction_category ON \"transactions\"(category)",
                
                # Composite indexes for common query patterns
                "CREATE INDEX IF NOT EXISTS idx_transaction_date_category ON \"transactions\"(date, category)",
                "CREATE INDEX IF NOT EXISTS idx_transaction_date_psp ON \"transactions\"(date, psp)",
                "CREATE INDEX IF NOT EXISTS idx_transaction_psp_category ON \"transactions\"(psp, category)",
                "CREATE INDEX IF NOT EXISTS idx_transaction_client_date ON \"transactions\"(client_name, date)",
                "CREATE INDEX IF NOT EXISTS idx_transaction_created_psp ON \"transactions\"(created_at, psp)",
                
                # PSP Track table indexes
                "CREATE INDEX IF NOT EXISTS idx_psp_track_date_psp ON psp_track(date, psp_name)",
                "CREATE INDEX IF NOT EXISTS idx_psp_track_psp_date ON psp_track(psp_name, date)",
                
                # Daily Balance table indexes
                "CREATE INDEX IF NOT EXISTS idx_daily_balance_date_psp ON daily_balance(date, psp)",
                "CREATE INDEX IF NOT EXISTS idx_daily_balance_psp_date ON daily_balance(psp, date)",
                
                # PSP Allocation table indexes
                "CREATE INDEX IF NOT EXISTS idx_psp_allocation_date_psp ON psp_allocation(date, psp_name)",
                "CREATE INDEX IF NOT EXISTS idx_psp_allocation_psp_date ON psp_allocation(psp_name, date)",
                
                # PSP Devir table indexes
                "CREATE INDEX IF NOT EXISTS idx_psp_devir_date_psp ON psp_devir(date, psp_name)",
                "CREATE INDEX IF NOT EXISTS idx_psp_devir_psp_date ON psp_devir(psp_name, date)",
                
                # PSP Kasa Top table indexes
                "CREATE INDEX IF NOT EXISTS idx_psp_kasa_top_date_psp ON psp_kasa_top(date, psp_name)",
                "CREATE INDEX IF NOT EXISTS idx_psp_kasa_top_psp_date ON psp_kasa_top(psp_name, date)",
                
                # User table indexes
                "CREATE INDEX IF NOT EXISTS idx_user_username ON \"users\"(username)",
                "CREATE INDEX IF NOT EXISTS idx_user_email ON \"users\"(email)",
                "CREATE INDEX IF NOT EXISTS idx_user_role ON \"users\"(role)",
                "CREATE INDEX IF NOT EXISTS idx_user_is_active ON \"users\"(is_active)",
                
                # Audit log indexes (matching model definitions)
                "CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_logs(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action)",
                "CREATE INDEX IF NOT EXISTS idx_audit_table ON audit_logs(table_name)",
                "CREATE INDEX IF NOT EXISTS idx_audit_user_timestamp ON audit_logs(user_id, timestamp)",
                
                # User session indexes
                "CREATE INDEX IF NOT EXISTS idx_session_user_id ON user_sessions(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_session_token ON user_sessions(session_token)",
                "CREATE INDEX IF NOT EXISTS idx_session_is_active ON user_sessions(is_active)",
                "CREATE INDEX IF NOT EXISTS idx_session_last_active ON user_sessions(last_active)",
                
                # Login attempt indexes
                "CREATE INDEX IF NOT EXISTS idx_login_username ON login_attempts(username)",
                "CREATE INDEX IF NOT EXISTS idx_login_timestamp ON login_attempts(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_login_success ON login_attempts(success)",
                "CREATE INDEX IF NOT EXISTS idx_login_username_timestamp ON login_attempts(username, timestamp)",
            ]
            
            created_count = 0
            for index_sql in indexes_to_create:
                try:
                    # Convert SQL syntax for MSSQL if needed
                    if db_type == 'mssql':
                        index_sql = UnifiedDatabaseService._convert_index_sql_for_mssql(index_sql)
                    
                    index_name = UnifiedDatabaseService._extract_index_name(index_sql)
                    db.session.execute(text(index_sql))
                    created_count += 1
                    logger.info(f"Created index: {index_name}")
                except Exception as e:
                    index_name = UnifiedDatabaseService._extract_index_name(index_sql)
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        logger.debug(f"Index already exists: {index_name}")
                    else:
                        logger.warning(f"Failed to create index {index_name}: {e}")
            
            db.session.commit()
            
            # Update table statistics for better query planning
            try:
                if db_type == 'mssql':
                    # MSSQL uses UPDATE STATISTICS
                    db.session.execute(text('UPDATE STATISTICS "transaction"'))
                else:
                    # ANALYZE for SQLite/PostgreSQL to update statistics
                    db.session.execute(text('ANALYZE "transaction"'))
                db.session.commit()
            except Exception as e:
                logger.debug(f"Statistics update not supported or failed: {e}")
            
            if created_count > 0:
                logger.info(f"Database optimization completed: {created_count} indexes created")
            else:
                logger.debug("All indexes already exist - database is optimized")
            
            return created_count
                
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            db.session.rollback()
            return 0
    
    # ========================================================================
    # QUERY OPTIMIZATION & VIEWS
    # ========================================================================
    
    def optimize_transaction_queries(self):
        """Create optimized views for common transaction queries"""
        try:
            optimized_views = [
                """
                CREATE VIEW IF NOT EXISTS daily_transaction_summary AS
                SELECT 
                    date,
                    COUNT(*) as transaction_count,
                    SUM(amount) as total_amount,
                    SUM(commission) as total_commission,
                    SUM(net_amount) as total_net,
                    COUNT(DISTINCT client_name) as unique_clients,
                    COUNT(DISTINCT psp) as unique_psps
                FROM "transaction"
                GROUP BY date
                """,
                
                """
                CREATE VIEW IF NOT EXISTS psp_transaction_summary AS
                SELECT 
                    psp,
                    COUNT(*) as transaction_count,
                    SUM(amount) as total_amount,
                    SUM(commission) as total_commission,
                    SUM(net_amount) as total_net,
                    AVG(amount) as avg_amount,
                    COUNT(DISTINCT client_name) as unique_clients
                FROM "transaction"
                WHERE psp IS NOT NULL AND psp != ''
                GROUP BY psp
                """,
                
                """
                CREATE VIEW IF NOT EXISTS monthly_transaction_summary AS
                SELECT 
                    strftime('%Y-%m', date) as month,
                    COUNT(*) as transaction_count,
                    SUM(amount) as total_amount,
                    SUM(commission) as total_commission,
                    SUM(net_amount) as total_net,
                    COUNT(DISTINCT client_name) as unique_clients,
                    COUNT(DISTINCT psp) as unique_psps
                FROM "transaction"
                GROUP BY strftime('%Y-%m', date)
                """
            ]
            
            created_views = 0
            for view_sql in optimized_views:
                try:
                    db.session.execute(text(view_sql))
                    created_views += 1
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        logger.warning(f"Failed to create optimized view: {e}")
            
            db.session.commit()
            logger.info(f"Query optimization completed: {created_views} views created")
            return created_views
            
        except Exception as e:
            logger.error(f"Query optimization failed: {e}")
            db.session.rollback()
            return 0
    
    # ========================================================================
    # HEALTH & MONITORING
    # ========================================================================
    
    def get_database_health(self) -> Dict[str, Any]:
        """Get comprehensive database health status"""
        try:
            start_time = time.time()
            
            # Test connectivity
            db.session.execute(text("SELECT 1"))
            connectivity_ok = True
            
            # Get engine info
            engine = db.engine
            response_time = round((time.time() - start_time) * 1000, 2)
            
            health_info = {
                'connectivity': 'OK',
                'database_type': engine.name,
                'response_time_ms': response_time,
                'pool_size': getattr(engine.pool, 'size', 'Unknown'),
                'checked_out': getattr(engine.pool, 'checkedout', 'Unknown'),
                'checked_in': getattr(engine.pool, 'checkedin', 'Unknown'),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # Health score calculation
            score = 100
            if response_time > 100:
                score -= 20
            if response_time > 500:
                score -= 30
                
            health_info['health_score'] = max(0, score)
            health_info['status'] = 'HEALTHY' if score > 70 else 'WARNING' if score > 30 else 'CRITICAL'
            
            return health_info
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'connectivity': 'FAILED',
                'error': str(e),
                'status': 'CRITICAL',
                'health_score': 0,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        try:
            stats = {}
            
            # Get connection pool statistics
            try:
                pool = db.engine.pool
                stats['connection_pool'] = {
                    'size': pool.size(),
                    'checked_out': pool.checkedout(),
                    'checked_in': pool.checkedin(),
                    'overflow': pool.overflow(),
                }
            except Exception as e:
                logger.debug(f"Could not get connection pool stats: {e}")
                stats['connection_pool'] = {
                    'size': 0,
                    'checked_out': 0,
                    'checked_in': 0,
                    'overflow': 0,
                }
            
            # Get table row counts
            # SECURITY: Use whitelist for table names to prevent SQL injection
            tables = ['transactions', 'users', 'psp_track', 'daily_balance', 'psp_allocation', 'audit_logs']
            for table in tables:
                try:
                    # SECURITY: Table name is from whitelist, but still use parameterized approach
                    # SQLite doesn't support table name parameters, so we validate against whitelist
                    if table not in tables:
                        logger.warning(f"Invalid table name attempted: {table}")
                        continue
                    result = db.session.execute(text(f'SELECT COUNT(*) FROM "{table}"')).fetchone()
                    stats[f"{table}_count"] = result[0] if result else 0
                except Exception as e:
                    stats[f"{table}_count"] = 0
                    logger.debug(f"Table {table} not accessible: {e}")
            
            # Get database size
            try:
                if db.engine.name == 'sqlite':
                    result = db.session.execute(text("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")).fetchone()
                    stats['database_size_bytes'] = result[0] if result else 0
                    stats['database_size_mb'] = round(stats['database_size_bytes'] / (1024 * 1024), 2)
                else:
                    # PostgreSQL
                    result = db.session.execute(text("SELECT pg_database_size(current_database())")).fetchone()
                    stats['database_size_bytes'] = result[0] if result else 0
                    stats['database_size_mb'] = round(stats['database_size_bytes'] / (1024 * 1024), 2)
            except Exception as e:
                stats['database_size_bytes'] = 0
                stats['database_size_mb'] = 0
                logger.debug(f"Could not get database size: {e}")
            
            stats['timestamp'] = datetime.now(timezone.utc).isoformat()
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {"error": str(e)}
    
    def analyze_tables(self) -> Dict[str, Any]:
        """Analyze all database tables"""
        try:
            engine = db.engine
            inspector = inspect(engine)
            
            tables_info = []
            for table_name in inspector.get_table_names():
                try:
                    # SECURITY: Table name comes from inspector (safe), but validate format
                    # Use quoted identifier to prevent injection
                    safe_table_name = table_name.replace('"', '""')  # Escape quotes
                    result = db.session.execute(text(f'SELECT COUNT(*) FROM "{safe_table_name}"'))
                    row_count = result.scalar()
                    
                    # Get indexes
                    indexes = inspector.get_indexes(table_name)
                    
                    tables_info.append({
                        'table_name': table_name,
                        'row_count': row_count,
                        'index_count': len(indexes),
                        'indexes': [idx['name'] for idx in indexes]
                    })
                except Exception as e:
                    logger.debug(f"Could not analyze table {table_name}: {e}")
                    
            return {
                'tables': tables_info,
                'total_tables': len(tables_info),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Table analysis failed: {e}")
            return {'error': str(e)}
    
    # ========================================================================
    # QUERY PERFORMANCE MONITORING
    # ========================================================================
    
    def monitor_query(self, query_name: str, query_func: Callable, *args, **kwargs):
        """Monitor and track query performance"""
        start_time = time.time()
        
        try:
            result = query_func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Record query statistics
            self._record_query_stats(query_name, execution_time, True)
            
            # Log slow queries
            if execution_time > self.slow_query_threshold:
                self._record_slow_query(query_name, execution_time, str(query_func))
                logger.warning(f"Slow query detected: {query_name} took {execution_time:.3f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_query_stats(query_name, execution_time, False)
            logger.error(f"Query {query_name} failed after {execution_time:.3f}s: {e}")
            raise
    
    def _record_query_stats(self, query_name: str, execution_time: float, success: bool):
        """Record query statistics"""
        if query_name not in self._query_stats:
            self._query_stats[query_name] = {
                'total_calls': 0,
                'total_time': 0.0,
                'successful_calls': 0,
                'failed_calls': 0,
                'avg_time': 0.0,
                'max_time': 0.0,
                'min_time': float('inf')
            }
        
        stats = self._query_stats[query_name]
        stats['total_calls'] += 1
        stats['total_time'] += execution_time
        stats['avg_time'] = stats['total_time'] / stats['total_calls']
        stats['max_time'] = max(stats['max_time'], execution_time)
        stats['min_time'] = min(stats['min_time'], execution_time)
        
        if success:
            stats['successful_calls'] += 1
        else:
            stats['failed_calls'] += 1
    
    def _record_slow_query(self, query_name: str, execution_time: float, query_string: str):
        """Record slow query details"""
        self._slow_queries.append({
            'query_name': query_name,
            'execution_time': execution_time,
            'query_string': query_string,
            'timestamp': time.time()
        })
        
        # Keep only last 100 slow queries
        if len(self._slow_queries) > 100:
            self._slow_queries = self._slow_queries[-100:]
    
    def get_query_stats(self) -> Dict[str, Any]:
        """Get query performance statistics"""
        # Analyze slow queries for common patterns
        slow_query_patterns = self._analyze_slow_query_patterns()
        
        return {
            'query_stats': self._query_stats,
            'slow_queries': self._slow_queries[-10:],  # Last 10 slow queries
            'slow_query_threshold': self.slow_query_threshold,
            'total_queries_monitored': len(self._query_stats),
            'slow_query_patterns': slow_query_patterns,
            'index_recommendations': self._generate_index_recommendations_from_slow_queries()
        }
    
    def _analyze_slow_query_patterns(self) -> List[Dict[str, Any]]:
        """Analyze slow queries to identify common patterns"""
        patterns = []
        
        # Group slow queries by pattern
        pattern_counts = {}
        for slow_query in self._slow_queries:
            query_str = slow_query.get('query_string', '')
            # Identify common patterns
            if 'date' in query_str.lower() and 'group by' in query_str.lower():
                pattern = 'date_aggregation'
                if pattern not in pattern_counts:
                    pattern_counts[pattern] = {'count': 0, 'avg_time': 0, 'total_time': 0}
                pattern_counts[pattern]['count'] += 1
                pattern_counts[pattern]['total_time'] += slow_query['execution_time']
                pattern_counts[pattern]['avg_time'] = pattern_counts[pattern]['total_time'] / pattern_counts[pattern]['count']
        
        for pattern, stats in pattern_counts.items():
            if stats['count'] >= 2:  # Pattern appears at least twice
                patterns.append({
                    'pattern': pattern,
                    'count': stats['count'],
                    'avg_execution_time': round(stats['avg_time'], 3)
                })
        
        return patterns
    
    def _generate_index_recommendations_from_slow_queries(self) -> List[str]:
        """Generate index recommendations based on slow queries"""
        recommendations = []
        
        # Check for common slow query patterns
        for slow_query in self._slow_queries[-20:]:  # Check last 20 slow queries
            query_str = slow_query.get('query_string', '').lower()
            
            # Pattern: Date filtering without index
            if 'where date' in query_str and 'idx_transaction_date' not in ' '.join(recommendations):
                recommendations.append('Consider verifying idx_transaction_date exists for date-range queries')
            
            # Pattern: PSP + Date queries
            if 'psp' in query_str and 'date' in query_str and 'idx_transaction_date_psp' not in ' '.join(recommendations):
                recommendations.append('Consider verifying idx_transaction_date_psp exists for PSP + date queries')
        
        return list(set(recommendations))  # Remove duplicates
    
    # ========================================================================
    # DATABASE OPTIMIZATION
    # ========================================================================
    
    def vacuum_database(self):
        """Vacuum database to reclaim space (SQLite only)"""
        if db.engine.name != 'sqlite':
            logger.info("VACUUM not available for non-SQLite databases")
            return False
        
        try:
            db.session.execute(text("VACUUM"))
            db.session.commit()
            logger.info("Database vacuum completed")
            return True
        except Exception as e:
            logger.error(f"Database vacuum failed: {e}")
            return False
    
    def analyze_query_performance(self):
        """Analyze query performance and run ANALYZE"""
        try:
            db.session.execute(text("ANALYZE"))
            db.session.commit()
            logger.info("Query performance analysis completed")
            return True
        except Exception as e:
            logger.error(f"Query performance analysis failed: {e}")
            return False
    
    def optimize_database(self):
        """Run all database optimization tasks"""
        try:
            logger.info("Starting comprehensive database optimization...")
            
            # Create indexes
            indexes_created = self.create_performance_indexes()
            
            # Analyze performance
            analysis_success = self.analyze_query_performance()
            
            # Vacuum database (SQLite only)
            vacuum_success = self.vacuum_database()
            
            # Get final stats
            stats = self.get_database_stats()
            
            logger.info(f"Database optimization completed: {indexes_created} indexes")
            
            return {
                'indexes_created': indexes_created,
                'analysis_success': analysis_success,
                'vacuum_success': vacuum_success,
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            return {"error": str(e)}
    
    # ========================================================================
    # ANALYSIS & SUGGESTIONS
    # ========================================================================
    
    def analyze_query_patterns(self) -> Dict[str, Any]:
        """Analyze query patterns and suggest optimizations"""
        try:
            suggestions = []
            
            # Analyze query statistics
            for query_name, stats in self._query_stats.items():
                if stats['avg_time'] > 0.5:  # Queries taking more than 500ms
                    suggestions.append({
                        'query': query_name,
                        'issue': 'High average execution time',
                        'avg_time': round(stats['avg_time'], 3),
                        'recommendation': 'Consider adding indexes or optimizing the query'
                    })
                
                if stats['failed_calls'] > 0:
                    failure_rate = stats['failed_calls'] / stats['total_calls']
                    if failure_rate > 0.1:  # More than 10% failure rate
                        suggestions.append({
                            'query': query_name,
                            'issue': 'High failure rate',
                            'failure_rate': round(failure_rate, 2),
                            'recommendation': 'Review error handling and query logic'
                        })
            
            return {
                'suggestions': suggestions,
                'total_queries_monitored': len(self._query_stats),
                'slow_queries_count': len(self._slow_queries)
            }
            
        except Exception as e:
            logger.error(f"Query pattern analysis failed: {e}")
            return {"error": str(e)}


# ========================================================================
# GLOBAL INSTANCE & HELPER FUNCTIONS
# ========================================================================

# Global unified database service instance
unified_db_service = UnifiedDatabaseService()

def get_unified_db_service() -> UnifiedDatabaseService:
    """Get the global unified database service"""
    return unified_db_service

def monitor_query_performance(query_name: str):
    """Decorator to monitor query performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            return unified_db_service.monitor_query(query_name, func, *args, **kwargs)
        return wrapper
    return decorator


# ========================================================================
# BACKWARD COMPATIBILITY EXPORTS
# ========================================================================

# For backward compatibility with existing code
DatabaseOptimizationService = UnifiedDatabaseService
query_optimizer = unified_db_service
db_optimization_service = unified_db_service

def get_query_optimizer() -> UnifiedDatabaseService:
    """Backward compatibility - get query optimizer"""
    return unified_db_service

