"""
Enhanced Backup Service
Supports SQLite, PostgreSQL, and S3 offsite backups
"""
import os
import shutil
import subprocess
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Tuple

logger = logging.getLogger(__name__)


class BackupService:
    """Comprehensive backup service for database backups"""
    
    def __init__(self, config=None):
        """
        Initialize backup service
        
        Args:
            config: Flask app config or dict with backup settings
        """
        self.config = config or {}
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # Backup settings
        self.retention_days = self.config.get('BACKUP_RETENTION_DAYS', 30)
        self.backup_enabled = self.config.get('BACKUP_ENABLED', True)
        
        # S3 settings
        self.s3_enabled = all([
            os.getenv('AWS_ACCESS_KEY_ID'),
            os.getenv('AWS_SECRET_ACCESS_KEY'),
            os.getenv('S3_BUCKET')
        ])
        
        if self.s3_enabled:
            self.s3_bucket = os.getenv('S3_BUCKET')
            self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
    
    def create_backup(self, database_url: str = None) -> Tuple[bool, str, Optional[str]]:
        """
        Create database backup
        
        Args:
            database_url: Database connection string
            
        Returns:
            Tuple of (success, message, backup_path)
        """
        if not self.backup_enabled:
            return False, "Backups are disabled", None
        
        try:
            # Determine database type
            if database_url and database_url.startswith('postgresql'):
                return self._backup_postgresql(database_url)
            else:
                return self._backup_sqlite()
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False, f"Backup failed: {str(e)}", None
    
    def _backup_sqlite(self) -> Tuple[bool, str, Optional[str]]:
        """Create SQLite database backup"""
        source_db = Path("instance/treasury_improved.db")
        
        if not source_db.exists():
            return False, "Source database not found", None
        
        # Create timestamped backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"sqlite_backup_{timestamp}.db"
        backup_path = self.backup_dir / backup_filename
        
        try:
            # Copy database file
            shutil.copy2(source_db, backup_path)
            file_size = backup_path.stat().st_size
            
            logger.info(f"SQLite backup created: {backup_filename} ({file_size} bytes)")
            
            # Upload to S3 if enabled
            if self.s3_enabled:
                s3_success, s3_message = self._upload_to_s3(backup_path)
                if s3_success:
                    logger.info(f"Backup uploaded to S3: {s3_message}")
            
            # Clean up old backups
            self._cleanup_old_backups()
            
            return True, f"SQLite backup created: {backup_filename}", str(backup_path)
            
        except Exception as e:
            logger.error(f"SQLite backup failed: {e}")
            return False, f"SQLite backup failed: {str(e)}", None
    
    def _backup_postgresql(self, database_url: str) -> Tuple[bool, str, Optional[str]]:
        """
        Create PostgreSQL database backup using pg_dump
        
        Args:
            database_url: PostgreSQL connection string
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"postgres_backup_{timestamp}.sql"
        backup_path = self.backup_dir / backup_filename
        
        try:
            # Parse database URL
            # Format: postgresql://user:password@host:port/database
            from urllib.parse import urlparse
            
            parsed = urlparse(database_url)
            
            # Set environment variables for pg_dump
            env = os.environ.copy()
            if parsed.password:
                env['PGPASSWORD'] = parsed.password
            
            # Build pg_dump command
            cmd = [
                'pg_dump',
                '-h', parsed.hostname or 'localhost',
                '-p', str(parsed.port or 5432),
                '-U', parsed.username or 'postgres',
                '-d', parsed.path.lstrip('/') if parsed.path else 'postgres',
                '-F', 'c',  # Custom format (compressed)
                '-f', str(backup_path),
                '--verbose'
            ]
            
            # Execute pg_dump
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or "Unknown error"
                logger.error(f"pg_dump failed: {error_msg}")
                return False, f"PostgreSQL backup failed: {error_msg}", None
            
            file_size = backup_path.stat().st_size
            logger.info(f"PostgreSQL backup created: {backup_filename} ({file_size} bytes)")
            
            # Upload to S3 if enabled
            if self.s3_enabled:
                s3_success, s3_message = self._upload_to_s3(backup_path)
                if s3_success:
                    logger.info(f"Backup uploaded to S3: {s3_message}")
            
            # Clean up old backups
            self._cleanup_old_backups()
            
            return True, f"PostgreSQL backup created: {backup_filename}", str(backup_path)
            
        except FileNotFoundError:
            error_msg = "pg_dump not found. Please install PostgreSQL client tools."
            logger.error(error_msg)
            return False, error_msg, None
        except subprocess.TimeoutExpired:
            error_msg = "Backup timeout - database might be too large"
            logger.error(error_msg)
            return False, error_msg, None
        except Exception as e:
            logger.error(f"PostgreSQL backup failed: {e}")
            return False, f"PostgreSQL backup failed: {str(e)}", None
    
    def _upload_to_s3(self, backup_path: Path) -> Tuple[bool, str]:
        """
        Upload backup to S3
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            Tuple of (success, message)
        """
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            s3_client = boto3.client(
                's3',
                region_name=self.aws_region,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            
            # S3 key with date prefix for organization
            date_prefix = datetime.now().strftime("%Y/%m/%d")
            s3_key = f"backups/{date_prefix}/{backup_path.name}"
            
            # Upload file
            s3_client.upload_file(
                str(backup_path),
                self.s3_bucket,
                s3_key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',  # Encrypt at rest
                    'StorageClass': 'STANDARD_IA'  # Infrequent access for cost savings
                }
            )
            
            logger.info(f"Uploaded to S3: s3://{self.s3_bucket}/{s3_key}")
            return True, f"s3://{self.s3_bucket}/{s3_key}"
            
        except ImportError:
            logger.warning("boto3 not installed. Install with: pip install boto3")
            return False, "boto3 not installed"
        except ClientError as e:
            error_msg = f"S3 upload failed: {e}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"S3 upload error: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def _cleanup_old_backups(self):
        """Remove backups older than retention period"""
        try:
            cutoff_time = time.time() - (self.retention_days * 24 * 60 * 60)
            
            for backup_file in self.backup_dir.glob("*_backup_*.{db,sql}"):
                if backup_file.stat().st_mtime < cutoff_time:
                    backup_file.unlink()
                    logger.info(f"Removed old backup: {backup_file.name}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up backups: {e}")
    
    def list_backups(self) -> List[Dict]:
        """
        List all available backups
        
        Returns:
            List of backup info dictionaries
        """
        backups = []
        
        try:
            for backup_file in sorted(self.backup_dir.glob("*_backup_*"), reverse=True):
                stat = backup_file.stat()
                backups.append({
                    'filename': backup_file.name,
                    'path': str(backup_file),
                    'size': stat.st_size,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'created': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'age_days': round((time.time() - stat.st_mtime) / (24 * 60 * 60), 1)
                })
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
        
        return backups
    
    def restore_backup(self, backup_path: str, database_url: str = None) -> Tuple[bool, str]:
        """
        Restore database from backup
        
        Args:
            backup_path: Path to backup file
            database_url: Database connection string (for PostgreSQL)
            
        Returns:
            Tuple of (success, message)
        """
        backup_file = Path(backup_path)
        
        if not backup_file.exists():
            return False, f"Backup file not found: {backup_path}"
        
        try:
            if backup_file.suffix == '.db':
                return self._restore_sqlite(backup_file)
            elif backup_file.suffix == '.sql':
                if not database_url:
                    return False, "Database URL required for PostgreSQL restore"
                return self._restore_postgresql(backup_file, database_url)
            else:
                return False, f"Unknown backup type: {backup_file.suffix}"
                
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False, f"Restore failed: {str(e)}"
    
    def _restore_sqlite(self, backup_file: Path) -> Tuple[bool, str]:
        """Restore SQLite database from backup"""
        target_db = Path("instance/treasury_improved.db")
        
        try:
            # Create backup of current database
            if target_db.exists():
                backup_current = target_db.with_suffix('.db.pre-restore')
                shutil.copy2(target_db, backup_current)
                logger.info(f"Current database backed up to: {backup_current}")
            
            # Restore from backup
            shutil.copy2(backup_file, target_db)
            
            logger.info(f"SQLite database restored from: {backup_file.name}")
            return True, f"Database restored from {backup_file.name}"
            
        except Exception as e:
            logger.error(f"SQLite restore failed: {e}")
            return False, f"SQLite restore failed: {str(e)}"
    
    def _restore_postgresql(self, backup_file: Path, database_url: str) -> Tuple[bool, str]:
        """Restore PostgreSQL database from backup"""
        try:
            from urllib.parse import urlparse
            
            parsed = urlparse(database_url)
            
            # Set environment variables for pg_restore
            env = os.environ.copy()
            if parsed.password:
                env['PGPASSWORD'] = parsed.password
            
            # Build pg_restore command
            cmd = [
                'pg_restore',
                '-h', parsed.hostname or 'localhost',
                '-p', str(parsed.port or 5432),
                '-U', parsed.username or 'postgres',
                '-d', parsed.path.lstrip('/') if parsed.path else 'postgres',
                '--clean',  # Drop existing objects
                '--if-exists',  # Don't error if objects don't exist
                '--verbose',
                str(backup_file)
            ]
            
            # Execute pg_restore
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or "Unknown error"
                logger.error(f"pg_restore failed: {error_msg}")
                return False, f"PostgreSQL restore failed: {error_msg}"
            
            logger.info(f"PostgreSQL database restored from: {backup_file.name}")
            return True, f"Database restored from {backup_file.name}"
            
        except FileNotFoundError:
            error_msg = "pg_restore not found. Please install PostgreSQL client tools."
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            logger.error(f"PostgreSQL restore failed: {e}")
            return False, f"PostgreSQL restore failed: {str(e)}"
    
    def verify_backup(self, backup_path: str) -> Tuple[bool, str, Dict]:
        """
        Verify backup file integrity
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            Tuple of (is_valid, message, details)
        """
        backup_file = Path(backup_path)
        
        if not backup_file.exists():
            return False, "Backup file not found", {}
        
        details = {
            'file': backup_file.name,
            'size': backup_file.stat().st_size,
            'created': datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat()
        }
        
        try:
            if backup_file.suffix == '.db':
                # SQLite - try to open and query
                import sqlite3
                conn = sqlite3.connect(str(backup_file))
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                conn.close()
                
                details['tables'] = len(tables)
                details['table_names'] = [t[0] for t in tables]
                
                return True, f"SQLite backup valid - {len(tables)} tables found", details
                
            elif backup_file.suffix == '.sql':
                # PostgreSQL - check file format
                with open(backup_file, 'rb') as f:
                    header = f.read(5)
                    if header == b'PGDMP':  # PostgreSQL custom format magic number
                        details['format'] = 'PostgreSQL custom format'
                        return True, "PostgreSQL backup format valid", details
                    else:
                        return False, "Invalid PostgreSQL backup format", details
            else:
                return False, f"Unknown backup type: {backup_file.suffix}", details
                
        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return False, f"Verification failed: {str(e)}", details


def get_backup_service(app=None):
    """Get backup service instance"""
    config = app.config if app else {}
    return BackupService(config)

