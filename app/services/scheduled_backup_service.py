"""Scheduled backup service for automated weekly backups"""
import logging
import threading
import schedule
import time
from datetime import datetime, timedelta
from flask import current_app
from app.services.backup_service import BackupService

logger = logging.getLogger(__name__)


class ScheduledBackupService:
    """Service for managing scheduled database backups"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.backup_service = None
        self.schedule_time = "23:59"  # Default: 23:59
        self.last_backup_time = None  # Track last backup
        self.backup_interval_hours = 24  # Minimum 24 hours between backups
    
    def init_app(self, app):
        """Initialize scheduled backup service"""
        self.app = app
        config = app.config if hasattr(app, 'config') else {}
        self.backup_service = BackupService(config)
        
        # Get schedule time from config or environment
        self.schedule_time = config.get('BACKUP_SCHEDULE_TIME', '23:59')
        
        # Validate schedule time format
        try:
            datetime.strptime(self.schedule_time, '%H:%M')
        except ValueError:
            logger.error(f"Invalid BACKUP_SCHEDULE_TIME format: {self.schedule_time}, using default 23:59")
            self.schedule_time = "23:59"
        
        # Clear any existing schedules (prevent duplicates)
        schedule.clear()
        
        # Schedule daily backups at specified time (local time)
        schedule.every().day.at(self.schedule_time).do(self._run_backup)
        
        logger.info(f"Scheduled backup service initialized: Daily at {self.schedule_time} local time")
    
    def _run_backup(self):
        """Execute scheduled backup with throttling"""
        if not self.app:
            logger.error("Flask app not initialized for backup service")
            return
        
        # KRITIK: Backup throttling - çok sık backup engelleniyor
        now = datetime.now()
        if self.last_backup_time:
            time_since_last = (now - self.last_backup_time).total_seconds() / 3600  # hours
            if time_since_last < self.backup_interval_hours:
                logger.warning(f"⏸️ Backup skipped: Last backup was {time_since_last:.1f} hours ago (minimum: {self.backup_interval_hours}h)")
                return
        
        with self.app.app_context():
            try:
                logger.info("Starting scheduled backup...")
                
                # Get database URL from config
                database_url = current_app.config.get('SQLALCHEMY_DATABASE_URI')
                if not database_url:
                    database_url = current_app.config.get('DATABASE_URL')
                
                success, message, backup_path = self.backup_service.create_backup(database_url)
                
                if success:
                    self.last_backup_time = now  # Update last backup time
                    logger.info(f"✅ Scheduled backup completed: {message}")
                    if backup_path:
                        logger.info(f"📁 Backup location: {backup_path}")
                else:
                    logger.error(f"❌ Scheduled backup failed: {message}")
                
            except Exception as e:
                logger.error(f"💥 Scheduled backup error: {e}", exc_info=True)
    
    def start(self):
        """Start the backup scheduler in a background thread"""
        if self.running:
            logger.warning("⚠️ Backup scheduler already running - skipping start")
            return
        
        # Check if thread is already alive (prevent duplicate instances)
        if self.thread and self.thread.is_alive():
            logger.error("🔴 Backup scheduler thread already alive! This indicates multiple instances.")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._scheduler_loop, daemon=True, name="BackupScheduler")
        self.thread.start()
        logger.info(f"✅ Backup scheduler started - Thread ID: {self.thread.ident}")
    
    def stop(self):
        """Stop the backup scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Backup scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop - checks every 10 minutes"""
        logger.info(f"🔄 Backup scheduler loop started (checking every 10 minutes)")
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(600)  # Check every 10 minutes (reduced CPU usage)
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                time.sleep(60)  # Fallback to 1 minute on error
    
    def trigger_backup_now(self):
        """Manually trigger a backup (for testing)"""
        logger.info("Manual backup triggered")
        self._run_backup()
    
    def get_next_backup_time(self):
        """Get next scheduled backup time with status info"""
        next_run = schedule.next_run()
        status = {
            'next_run': next_run.strftime("%Y-%m-%d %H:%M:%S") if next_run else None,
            'last_backup': self.last_backup_time.strftime("%Y-%m-%d %H:%M:%S") if self.last_backup_time else "Never",
            'schedule_time': self.schedule_time,
            'interval_hours': self.backup_interval_hours,
            'running': self.running
        }
        
        if next_run:
            return next_run.strftime("%Y-%m-%d %H:%M:%S")
        return None
    
    def get_status(self):
        """Get detailed backup scheduler status"""
        next_run = schedule.next_run()
        return {
            'running': self.running,
            'next_backup': next_run.strftime("%Y-%m-%d %H:%M:%S") if next_run else None,
            'last_backup': self.last_backup_time.strftime("%Y-%m-%d %H:%M:%S") if self.last_backup_time else "Never",
            'schedule_time': self.schedule_time,
            'min_interval_hours': self.backup_interval_hours,
            'thread_alive': self.thread.is_alive() if self.thread else False,
            'thread_id': self.thread.ident if self.thread else None
        }


# Global instance
scheduled_backup_service = ScheduledBackupService()

