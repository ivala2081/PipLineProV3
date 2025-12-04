"""
Database Prevention Service for PipLinePro
Implements preventive measures to avoid database corruption
"""
import os
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app import db

logger = logging.getLogger(__name__)

class DatabasePreventionService:
    """Service for preventing database corruption and maintaining health"""
    
    def __init__(self):
        self.last_vacuum = None
        self.last_analyze = None
        self.vacuum_interval = timedelta(days=7)  # Weekly vacuum
        self.analyze_interval = timedelta(days=1)  # Daily analyze
    
    def perform_maintenance(self) -> Dict[str, Any]:
        """Perform routine database maintenance"""
        try:
            logger.info("Starting database maintenance...")
            
            maintenance_results = {
                'timestamp': datetime.now().isoformat(),
                'operations': [],
                'success': True,
                'errors': []
            }
            
            # Check if maintenance is needed
            if self._should_vacuum():
                vacuum_result = self._vacuum_database()
                maintenance_results['operations'].append(vacuum_result)
                if not vacuum_result['success']:
                    maintenance_results['success'] = False
                    maintenance_results['errors'].append(vacuum_result['error'])
            
            if self._should_analyze():
                analyze_result = self._analyze_database()
                maintenance_results['operations'].append(analyze_result)
                if not analyze_result['success']:
                    maintenance_results['success'] = False
                    maintenance_results['errors'].append(analyze_result['error'])
            
            # Check database integrity
            integrity_result = self._check_integrity()
            maintenance_results['operations'].append(integrity_result)
            if not integrity_result['success']:
                maintenance_results['success'] = False
                maintenance_results['errors'].append(integrity_result['error'])
            
            # Optimize database settings
            settings_result = self._optimize_settings()
            maintenance_results['operations'].append(settings_result)
            if not settings_result['success']:
                maintenance_results['success'] = False
                maintenance_results['errors'].append(settings_result['error'])
            
            logger.info(f"Database maintenance completed. Success: {maintenance_results['success']}")
            return maintenance_results
            
        except Exception as e:
            logger.error(f"Error during database maintenance: {str(e)}")
            return {
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e),
                'operations': []
            }
    
    def _should_vacuum(self) -> bool:
        """Check if vacuum is needed"""
        if self.last_vacuum is None:
            return True
        
        return datetime.now() - self.last_vacuum > self.vacuum_interval
    
    def _should_analyze(self) -> bool:
        """Check if analyze is needed"""
        if self.last_analyze is None:
            return True
        
        return datetime.now() - self.last_analyze > self.analyze_interval
    
    def _vacuum_database(self) -> Dict[str, Any]:
        """Perform VACUUM operation to rebuild database"""
        try:
            logger.info("Performing database VACUUM...")
            
            # Get database path for SQLite
            db_uri = db.engine.url
            if db_uri.drivername != 'sqlite':
                return {
                    'operation': 'vacuum',
                    'success': True,
                    'message': 'VACUUM not needed for non-SQLite database'
                }
            
            # Perform VACUUM
            db.session.execute(text("VACUUM"))
            db.session.commit()
            
            self.last_vacuum = datetime.now()
            
            logger.info("Database VACUUM completed successfully")
            return {
                'operation': 'vacuum',
                'success': True,
                'message': 'Database VACUUM completed successfully',
                'timestamp': self.last_vacuum.isoformat()
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Error during VACUUM: {str(e)}")
            db.session.rollback()
            return {
                'operation': 'vacuum',
                'success': False,
                'error': str(e),
                'message': f'VACUUM failed: {str(e)}'
            }
    
    def _analyze_database(self) -> Dict[str, Any]:
        """Perform ANALYZE operation to update statistics"""
        try:
            logger.info("Performing database ANALYZE...")
            
            # Get database path for SQLite
            db_uri = db.engine.url
            if db_uri.drivername != 'sqlite':
                return {
                    'operation': 'analyze',
                    'success': True,
                    'message': 'ANALYZE not needed for non-SQLite database'
                }
            
            # Perform ANALYZE
            db.session.execute(text("ANALYZE"))
            db.session.commit()
            
            self.last_analyze = datetime.now()
            
            logger.info("Database ANALYZE completed successfully")
            return {
                'operation': 'analyze',
                'success': True,
                'message': 'Database ANALYZE completed successfully',
                'timestamp': self.last_analyze.isoformat()
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Error during ANALYZE: {str(e)}")
            db.session.rollback()
            return {
                'operation': 'analyze',
                'success': False,
                'error': str(e),
                'message': f'ANALYZE failed: {str(e)}'
            }
    
    def _check_integrity(self) -> Dict[str, Any]:
        """Check database integrity"""
        try:
            logger.info("Checking database integrity...")
            
            # Get database path for SQLite
            db_uri = db.engine.url
            if db_uri.drivername != 'sqlite':
                return {
                    'operation': 'integrity_check',
                    'success': True,
                    'message': 'Integrity check not needed for non-SQLite database'
                }
            
            # Perform integrity check
            result = db.session.execute(text("PRAGMA integrity_check")).fetchone()
            
            if result and result[0] == 'ok':
                logger.info("Database integrity check passed")
                return {
                    'operation': 'integrity_check',
                    'success': True,
                    'message': 'Database integrity check passed',
                    'result': result[0]
                }
            else:
                logger.warning(f"Database integrity check failed: {result[0] if result else 'No result'}")
                return {
                    'operation': 'integrity_check',
                    'success': False,
                    'error': f'Integrity check failed: {result[0] if result else "No result"}',
                    'message': 'Database integrity issues detected'
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Error during integrity check: {str(e)}")
            return {
                'operation': 'integrity_check',
                'success': False,
                'error': str(e),
                'message': f'Integrity check failed: {str(e)}'
            }
    
    def _optimize_settings(self) -> Dict[str, Any]:
        """Optimize database settings for better performance and reliability"""
        try:
            logger.info("Optimizing database settings...")
            
            # Get database path for SQLite
            db_uri = db.engine.url
            if db_uri.drivername != 'sqlite':
                return {
                    'operation': 'optimize_settings',
                    'success': True,
                    'message': 'Settings optimization not needed for non-SQLite database'
                }
            
            # SQLite optimization settings
            optimizations = [
                ("PRAGMA journal_mode=WAL", "Enable WAL mode for better concurrency"),
                ("PRAGMA synchronous=NORMAL", "Set synchronous mode to NORMAL for better performance"),
                ("PRAGMA cache_size=10000", "Increase cache size"),
                ("PRAGMA temp_store=MEMORY", "Store temporary tables in memory"),
                ("PRAGMA mmap_size=268435456", "Enable memory-mapped I/O (256MB)"),
                ("PRAGMA optimize", "Run query optimizer")
            ]
            
            applied_optimizations = []
            for pragma, description in optimizations:
                try:
                    result = db.session.execute(text(pragma)).fetchone()
                    applied_optimizations.append({
                        'pragma': pragma,
                        'description': description,
                        'result': result[0] if result else 'OK'
                    })
                except SQLAlchemyError as e:
                    logger.warning(f"Failed to apply {pragma}: {str(e)}")
            
            db.session.commit()
            
            logger.info(f"Applied {len(applied_optimizations)} database optimizations")
            return {
                'operation': 'optimize_settings',
                'success': True,
                'message': f'Applied {len(applied_optimizations)} database optimizations',
                'optimizations': applied_optimizations
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Error optimizing database settings: {str(e)}")
            db.session.rollback()
            return {
                'operation': 'optimize_settings',
                'success': False,
                'error': str(e),
                'message': f'Failed to optimize settings: {str(e)}'
            }
    
    def get_maintenance_status(self) -> Dict[str, Any]:
        """Get current maintenance status"""
        return {
            'last_vacuum': self.last_vacuum.isoformat() if self.last_vacuum else None,
            'last_analyze': self.last_analyze.isoformat() if self.last_analyze else None,
            'vacuum_needed': self._should_vacuum(),
            'analyze_needed': self._should_analyze(),
            'vacuum_interval_days': self.vacuum_interval.days,
            'analyze_interval_days': self.analyze_interval.days
        }
    
    def schedule_maintenance(self) -> Dict[str, Any]:
        """Schedule automatic maintenance if needed"""
        try:
            status = self.get_maintenance_status()
            
            if status['vacuum_needed'] or status['analyze_needed']:
                logger.info("Scheduled maintenance needed, performing now...")
                return self.perform_maintenance()
            else:
                return {
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'message': 'No maintenance needed at this time',
                    'status': status
                }
                
        except Exception as e:
            logger.error(f"Error in scheduled maintenance: {str(e)}")
            return {
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            }

# Global instance
database_prevention_service = DatabasePreventionService()
