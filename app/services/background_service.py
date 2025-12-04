"""
Background Task Service for Asynchronous Operations
"""
import time
import logging
from typing import Any, Dict, List, Optional
from functools import wraps
from flask import current_app
from celery import Celery
from app.utils.unified_logger import get_logger

# Get logger instance
logger = logging.getLogger(__name__)

class BackgroundTaskService:
    """Background task service for handling heavy operations asynchronously"""
    
    def __init__(self, app=None):
        self.app = app
        self.celery = None
        self.connected = False
        self.task_stats = {
            'pending': 0,
            'running': 0,
            'completed': 0,
            'failed': 0,
            'total_created': 0
        }
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize background task service with Flask app"""
        self.app = app
        
        try:
            if app.config.get('CELERY_ENABLED', False):
                # Initialize Celery
                self.celery = Celery(
                    'pipelinepro',
                    broker=app.config.get('CELERY_BROKER_URL', 'redis://localhost:6379/1'),
                    backend=app.config.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')
                )
                
                # Configure Celery
                self.celery.conf.update(
                    task_serializer=app.config.get('CELERY_TASK_SERIALIZER', 'json'),
                    result_serializer=app.config.get('CELERY_RESULT_SERIALIZER', 'json'),
                    accept_content=app.config.get('CELERY_ACCEPT_CONTENT', ['json']),
                    timezone=app.config.get('CELERY_TIMEZONE', 'UTC'),
                    enable_utc=app.config.get('CELERY_ENABLE_UTC', True),
                    task_track_started=app.config.get('CELERY_TASK_TRACK_STARTED', True),
                    task_time_limit=app.config.get('CELERY_TASK_TIME_LIMIT', 30 * 60),
                    task_soft_time_limit=app.config.get('CELERY_TASK_SOFT_TIME_LIMIT', 25 * 60)
                )
                
                self.connected = True
                logger.info("✅ Background task service initialized successfully")
                
            else:
                logger.info("⚠️ Background tasks disabled in configuration")
                
        except Exception as e:
            logger.warning(f"⚠️ Background task service initialization failed: {e}")
            self.connected = False
    
    def is_connected(self) -> bool:
        """Check if background task service is connected"""
        return self.connected and self.celery is not None
    
    def submit_task(self, task_name: str, args: tuple = None, kwargs: dict = None) -> Optional[str]:
        """Submit a background task"""
        if not self.is_connected():
            logging.warning("Background task service not available")
            return None
        
        try:
            args = args or ()
            kwargs = kwargs or {}
            
            # Submit task to Celery
            task = self.celery.send_task(task_name, args=args, kwargs=kwargs)
            
            self.task_stats['total_created'] += 1
            self.task_stats['pending'] += 1
            
            logging.info(f"Background task submitted: {task_name} (ID: {task.id})")
            return task.id
            
        except Exception as e:
            logging.error(f"Error submitting background task: {e}")
            return None
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a background task"""
        if not self.is_connected():
            return {'status': 'service_unavailable', 'message': 'Background task service not available'}
        
        try:
            task_result = self.celery.AsyncResult(task_id)
            
            status_info = {
                'id': task_id,
                'status': task_result.status,
                'ready': task_result.ready(),
                'successful': task_result.successful(),
                'failed': task_result.failed()
            }
            
            if task_result.ready():
                if task_result.successful():
                    status_info['result'] = task_result.result
                    self.task_stats['completed'] += 1
                    self.task_stats['pending'] -= 1
                else:
                    status_info['error'] = str(task_result.info)
                    self.task_stats['failed'] += 1
                    self.task_stats['pending'] -= 1
            
            return status_info
            
        except Exception as e:
            logging.error(f"Error getting task status: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get background task queue statistics"""
        if not self.is_connected():
            return {'connected': False, 'message': 'Background task service not available'}
        
        try:
            # Get active tasks
            active_tasks = self.celery.control.inspect().active()
            running_count = sum(len(tasks) for tasks in active_tasks.values()) if active_tasks else 0
            
            # Get reserved tasks
            reserved_tasks = self.celery.control.inspect().reserved()
            pending_count = sum(len(tasks) for tasks in reserved_tasks.values()) if reserved_tasks else 0
            
            return {
                'connected': True,
                'running_tasks': running_count,
                'pending_tasks': pending_count,
                'completed_tasks': self.task_stats['completed'],
                'failed_tasks': self.task_stats['failed'],
                'total_tasks': self.task_stats['total_created'],
                'worker_count': len(active_tasks) if active_tasks else 0
            }
            
        except Exception as e:
            logging.error(f"Error getting queue stats: {e}")
            return {'connected': False, 'error': str(e)}
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running background task"""
        if not self.is_connected():
            return False
        
        try:
            self.celery.control.revoke(task_id, terminate=True)
            logging.info(f"Background task cancelled: {task_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error cancelling task: {e}")
            return False
    
    def clear_completed_tasks(self):
        """Clear completed task statistics"""
        self.task_stats['completed'] = 0
        self.task_stats['failed'] = 0
        logging.info("Completed task statistics cleared")
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for background task service"""
        try:
            if not self.is_connected():
                return {
                    'status': 'disconnected',
                    'message': 'Background task service not available',
                    'timestamp': time.time()
                }
            
            # Test basic operations
            test_task_id = self.submit_task('test_task', args=('test',), kwargs={'test': True})
            if not test_task_id:
                return {
                    'status': 'error',
                    'message': 'Task submission failed',
                    'timestamp': time.time()
                }
            
            # Get task status
            task_status = self.get_task_status(test_task_id)
            if task_status['status'] == 'error':
                return {
                    'status': 'error',
                    'message': 'Task status retrieval failed',
                    'timestamp': time.time()
                }
            
            # Cancel test task
            cancel_result = self.cancel_task(test_task_id)
            if not cancel_result:
                return {
                    'status': 'warning',
                    'message': 'Task cancellation failed',
                    'timestamp': time.time()
                }
            
            return {
                'status': 'healthy',
                'message': 'All background task operations working correctly',
                'timestamp': time.time(),
                'stats': self.get_queue_stats()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Background task health check failed: {str(e)}',
                'timestamp': time.time()
            }

# Background task decorator
def background_task(task_name: str = None):
    """Decorator for background task execution"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if we should run in background
            run_background = kwargs.pop('run_background', False)
            
            if run_background and current_app.config.get('CELERY_ENABLED', False):
                # Submit to background
                background_service = current_app.background_service if hasattr(current_app, 'background_service') else None
                
                if background_service and background_service.is_connected():
                    task_id = background_service.submit_task(
                        task_name or func.__name__,
                        args=args,
                        kwargs=kwargs
                    )
                    return {'task_id': task_id, 'status': 'submitted'}
            
            # Run synchronously
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Initialize background task service
background_task_service = BackgroundTaskService()
