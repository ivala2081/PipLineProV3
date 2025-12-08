"""
Database Recovery Service for PipLinePro
Handles SQLite database corruption recovery and integrity checks
"""
import os
import shutil
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import text, create_engine
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from app import db

logger = logging.getLogger(__name__)

class DatabaseRecoveryService:
    """Service for database recovery and integrity management"""
    
    def __init__(self):
        self.db_path = None
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    def get_database_path(self) -> str:
        """Get the current database file path"""
        if self.db_path:
            return self.db_path
            
        # Extract database path from SQLAlchemy URI
        db_uri = db.engine.url
        if db_uri.drivername == 'sqlite':
            self.db_path = db_uri.database
            return self.db_path
        else:
            raise ValueError("Database recovery service only supports SQLite databases")
    
    def check_database_integrity(self) -> Dict[str, Any]:
        """Check database integrity and return detailed report"""
        try:
            db_path = self.get_database_path()
            logger.info(f"Checking database integrity for: {db_path}")
            
            # Check if file exists
            if not os.path.exists(db_path):
                return {
                    'status': 'error',
                    'message': f'Database file not found: {db_path}',
                    'corrupted': True,
                    'recoverable': False
                }
            
            # Check file size
            file_size = os.path.getsize(db_path)
            if file_size == 0:
                return {
                    'status': 'error',
                    'message': 'Database file is empty',
                    'corrupted': True,
                    'recoverable': False,
                    'file_size': file_size
                }
            
            # Try to connect and run integrity check
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Run PRAGMA integrity_check
                cursor.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()
                
                # Run PRAGMA quick_check (faster)
                cursor.execute("PRAGMA quick_check")
                quick_check_result = cursor.fetchone()
                
                # Get database info
                cursor.execute("PRAGMA database_list")
                db_info = cursor.fetchall()
                
                # Get table count
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                conn.close()
                
                # Determine if database is corrupted
                is_corrupted = (
                    integrity_result[0] != 'ok' or 
                    quick_check_result[0] != 'ok' or
                    len(tables) == 0
                )
                
                return {
                    'status': 'success' if not is_corrupted else 'corrupted',
                    'message': 'Database integrity check completed',
                    'corrupted': is_corrupted,
                    'recoverable': True,
                    'file_size': file_size,
                    'integrity_check': integrity_result[0] if integrity_result else 'failed',
                    'quick_check': quick_check_result[0] if quick_check_result else 'failed',
                    'table_count': len(tables),
                    'tables': [table[0] for table in tables],
                    'database_info': db_info
                }
                
            except sqlite3.DatabaseError as e:
                logger.error(f"Database integrity check failed: {str(e)}")
                return {
                    'status': 'error',
                    'message': f'Database is corrupted: {str(e)}',
                    'corrupted': True,
                    'recoverable': True,
                    'file_size': file_size,
                    'error': str(e)
                }
                
        except Exception as e:
            logger.error(f"Error checking database integrity: {str(e)}")
            return {
                'status': 'error',
                'message': f'Error checking database: {str(e)}',
                'corrupted': True,
                'recoverable': False,
                'error': str(e)
            }
    
    def create_backup(self, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """Create a backup of the current database"""
        try:
            db_path = self.get_database_path()
            
            if not os.path.exists(db_path):
                return {
                    'status': 'error',
                    'message': f'Database file not found: {db_path}'
                }
            
            # Generate backup filename
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"treasury_backup_{timestamp}.db"
            
            backup_path = self.backup_dir / backup_name
            
            # Create backup
            shutil.copy2(db_path, backup_path)
            
            # Verify backup
            if os.path.exists(backup_path) and os.path.getsize(backup_path) > 0:
                logger.info(f"Database backup created: {backup_path}")
                return {
                    'status': 'success',
                    'message': 'Database backup created successfully',
                    'backup_path': str(backup_path),
                    'backup_size': os.path.getsize(backup_path),
                    'original_size': os.path.getsize(db_path)
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Backup creation failed - file not created or empty'
                }
                
        except Exception as e:
            logger.error(f"Error creating database backup: {str(e)}")
            return {
                'status': 'error',
                'message': f'Error creating backup: {str(e)}'
            }
    
    def recover_database(self, backup_path: Optional[str] = None) -> Dict[str, Any]:
        """Recover database from backup or recreate if necessary"""
        try:
            db_path = self.get_database_path()
            logger.info(f"Starting database recovery for: {db_path}")
            
            # Create backup of current corrupted database
            corrupted_backup = self.create_backup("corrupted_database_backup.db")
            if corrupted_backup['status'] != 'success':
                logger.warning("Could not create backup of corrupted database")
            
            # If no backup path provided, try to find the most recent backup
            if not backup_path:
                backup_path = self._find_latest_backup()
            
            if backup_path and os.path.exists(backup_path):
                # Restore from backup
                logger.info(f"Restoring database from backup: {backup_path}")
                shutil.copy2(backup_path, db_path)
                
                # Verify restoration
                integrity_check = self.check_database_integrity()
                if integrity_check['status'] == 'success':
                    logger.info("Database successfully restored from backup")
                    return {
                        'status': 'success',
                        'message': 'Database restored from backup successfully',
                        'backup_used': backup_path,
                        'integrity_check': integrity_check
                    }
                else:
                    logger.error("Restored database still has integrity issues")
                    return {
                        'status': 'error',
                        'message': 'Restored database still has integrity issues',
                        'backup_used': backup_path,
                        'integrity_check': integrity_check
                    }
            else:
                # No backup available, recreate database
                logger.warning("No backup available, recreating database from scratch")
                return self._recreate_database()
                
        except Exception as e:
            logger.error(f"Error recovering database: {str(e)}")
            return {
                'status': 'error',
                'message': f'Error recovering database: {str(e)}'
            }
    
    def _find_latest_backup(self) -> Optional[str]:
        """Find the most recent backup file"""
        try:
            backup_files = []
            for file in self.backup_dir.glob("treasury_backup_*.db"):
                if file.is_file():
                    backup_files.append((file.stat().st_mtime, str(file)))
            
            if backup_files:
                # Sort by modification time (newest first)
                backup_files.sort(reverse=True)
                return backup_files[0][1]
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding latest backup: {str(e)}")
            return None
    
    def _recreate_database(self) -> Dict[str, Any]:
        """Recreate database from scratch using migrations"""
        try:
            db_path = self.get_database_path()
            logger.info("Recreating database from scratch")
            
            # Remove corrupted database file
            if os.path.exists(db_path):
                os.remove(db_path)
            
            # Create new database using Flask-Migrate
            from flask_migrate import upgrade
            from app import create_app
            
            app = create_app()
            with app.app_context():
                # Run migrations to create fresh database
                upgrade()
                
                # Verify new database
                integrity_check = self.check_database_integrity()
                
                if integrity_check['status'] == 'success':
                    logger.info("Database successfully recreated")
                    return {
                        'status': 'success',
                        'message': 'Database recreated successfully',
                        'integrity_check': integrity_check,
                        'note': 'Database was recreated from scratch. All data has been lost.'
                    }
                else:
                    return {
                        'status': 'error',
                        'message': 'Recreated database has integrity issues',
                        'integrity_check': integrity_check
                    }
                    
        except Exception as e:
            logger.error(f"Error recreating database: {str(e)}")
            return {
                'status': 'error',
                'message': f'Error recreating database: {str(e)}'
            }
    
    def repair_database(self) -> Dict[str, Any]:
        """Attempt to repair a corrupted database"""
        try:
            db_path = self.get_database_path()
            logger.info(f"Attempting to repair database: {db_path}")
            
            # Create backup first
            backup_result = self.create_backup("pre_repair_backup.db")
            if backup_result['status'] != 'success':
                logger.warning("Could not create backup before repair")
            
            # Try SQLite's built-in repair mechanisms
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Try VACUUM to rebuild database
                cursor.execute("VACUUM")
                
                # Try REINDEX to rebuild indexes
                cursor.execute("REINDEX")
                
                conn.close()
                
                # Check integrity after repair
                integrity_check = self.check_database_integrity()
                
                if integrity_check['status'] == 'success':
                    logger.info("Database repair successful")
                    return {
                        'status': 'success',
                        'message': 'Database repair successful',
                        'integrity_check': integrity_check
                    }
                else:
                    logger.warning("Database repair did not resolve all issues")
                    return {
                        'status': 'partial',
                        'message': 'Database repair partially successful',
                        'integrity_check': integrity_check
                    }
                    
            except sqlite3.DatabaseError as e:
                logger.error(f"Database repair failed: {str(e)}")
                return {
                    'status': 'error',
                    'message': f'Database repair failed: {str(e)}',
                    'suggestion': 'Try database recovery from backup'
                }
                
        except Exception as e:
            logger.error(f"Error during database repair: {str(e)}")
            return {
                'status': 'error',
                'message': f'Error during repair: {str(e)}'
            }
    
    def get_recovery_options(self) -> Dict[str, Any]:
        """Get available recovery options and their status"""
        try:
            integrity_check = self.check_database_integrity()
            latest_backup = self._find_latest_backup()
            
            options = {
                'database_status': integrity_check,
                'available_backups': self._list_backups(),
                'latest_backup': latest_backup,
                'recovery_options': []
            }
            
            if integrity_check['corrupted']:
                options['recovery_options'].extend([
                    {
                        'option': 'repair',
                        'description': 'Attempt to repair the corrupted database',
                        'recommended': True,
                        'data_loss_risk': 'Low'
                    }
                ])
                
                if latest_backup:
                    options['recovery_options'].append({
                        'option': 'restore_from_backup',
                        'description': f'Restore from backup: {os.path.basename(latest_backup)}',
                        'recommended': True,
                        'data_loss_risk': 'Depends on backup age'
                    })
                
                options['recovery_options'].append({
                    'option': 'recreate',
                    'description': 'Recreate database from scratch (loses all data)',
                    'recommended': False,
                    'data_loss_risk': 'Complete data loss'
                })
            
            return options
            
        except Exception as e:
            logger.error(f"Error getting recovery options: {str(e)}")
            return {
                'status': 'error',
                'message': f'Error getting recovery options: {str(e)}'
            }
    
    def _list_backups(self) -> List[Dict[str, Any]]:
        """List all available backup files"""
        try:
            backups = []
            for file in self.backup_dir.glob("*.db"):
                if file.is_file():
                    stat = file.stat()
                    backups.append({
                        'filename': file.name,
                        'path': str(file),
                        'size': stat.st_size,
                        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            # Sort by modification time (newest first)
            backups.sort(key=lambda x: x['modified'], reverse=True)
            return backups
            
        except Exception as e:
            logger.error(f"Error listing backups: {str(e)}")
            return []

# Global instance
database_recovery_service = DatabaseRecoveryService()
