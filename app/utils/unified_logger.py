"""
Unified Logging System for PipLinePro
Consolidates all logging functionality into a single, efficient system
Supports both structured JSON logging and traditional text logging
Windows-compatible log rotation using ConcurrentRotatingFileHandler
"""
import logging
import logging.handlers
import os
import sys
import json
import traceback
import time
import platform
import psutil
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union
from functools import wraps
from flask import request, g, current_app
import jinja2
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError

# Try to import concurrent_log_handler for Windows compatibility
try:
    from concurrent_log_handler import ConcurrentRotatingFileHandler
    HAS_CONCURRENT_HANDLER = True
except ImportError:
    HAS_CONCURRENT_HANDLER = False
    # Use safe print for Windows compatibility
    try:
        import sys
        msg = "WARNING: concurrent-log-handler not installed. Install with: pip install concurrent-log-handler"
        sys.stdout.buffer.write(msg.encode('utf-8'))
        sys.stdout.buffer.write(b'\n')
        msg2 = "   Falling back to standard RotatingFileHandler (may cause issues on Windows)"
        sys.stdout.buffer.write(msg2.encode('utf-8'))
        sys.stdout.buffer.write(b'\n')
    except Exception:
        print("WARNING: concurrent-log-handler not installed. Install with: pip install concurrent-log-handler")
        print("   Falling back to standard RotatingFileHandler (may cause issues on Windows)")


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging with correlation IDs"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data: Dict[str, Any] = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add correlation ID if available (check if we're in a request context)
        try:
            from flask import has_request_context
            if has_request_context() and hasattr(request, 'request_id'):
                log_data['request_id'] = request.request_id
        except (RuntimeError, ImportError):
            pass
        
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        
        # Add request context if available (only in request context)
        try:
            from flask import has_request_context
            if has_request_context() and request and hasattr(request, 'method'):
                log_data['request'] = {
                    'method': request.method,
                    'path': request.path,
                    'url': request.url,
                    'remote_addr': request.remote_addr,
                }
        except (RuntimeError, ImportError):
            pass
        
        # Add user context if available (only in request context)
        try:
            from flask import has_request_context
            if has_request_context() and hasattr(g, 'user_id'):
                log_data['user_id'] = g.user_id
        except (RuntimeError, ImportError):
            pass
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': self.formatException(record.exc_info) if record.exc_info else None
            }
        
        # Add any extra fields
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        # Add any custom fields from record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'levelname', 
                          'levelno', 'lineno', 'module', 'msecs', 'message', 'pathname',
                          'process', 'processName', 'relativeCreated', 'thread', 'threadName',
                          'exc_info', 'exc_text', 'stack_info']:
                if not key.startswith('_'):
                    log_data[key] = value
        
        return json.dumps(log_data, default=str, ensure_ascii=False)


class UnifiedLogger:
    """Unified logging system that handles all logging needs"""
    
    def __init__(self, name: str = "PipLinePro", use_json: Optional[bool] = None):
        self.name = name
        self.logger = logging.getLogger(name)
        self.is_development = self._is_development()
        # Use JSON logging in production by default, can be overridden
        self.use_json = use_json if use_json is not None else (not self.is_development)
        self._setup_logger()
    
    def _is_development(self) -> bool:
        """Check if we're in development mode"""
        return (os.environ.get('FLASK_ENV') == 'development' or 
                os.environ.get('DEBUG') == 'True' or 
                os.environ.get('FLASK_DEBUG') == '1')
    
    def _setup_logger(self):
        """Setup the logger based on environment"""
        # Clear existing handlers to prevent duplicates
        self.logger.handlers.clear()
        
        # Set level based on environment
        if self.is_development:
            self.logger.setLevel(logging.INFO)
        else:
            self.logger.setLevel(logging.WARNING)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Create formatter - use JSON in production, text in development
        if self.use_json:
            formatter = JSONFormatter()
        else:
            if self.is_development:
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%H:%M:%S'
                )
            else:
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
        
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Always add file handler (both development and production)
        self._setup_file_handler()
    
    def _setup_file_handler(self):
        """Setup file handler with Windows-compatible rotation"""
        try:
            # Ensure logs directory exists
            os.makedirs('logs', exist_ok=True)
            
            # Create formatter - use JSON for structured logs
            if self.use_json:
                formatter = JSONFormatter()
            else:
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            
            # Use ConcurrentRotatingFileHandler on Windows for better file locking
            if HAS_CONCURRENT_HANDLER and platform.system() == 'Windows':
                # Main log with size-based rotation (Windows-safe)
                main_file_handler = ConcurrentRotatingFileHandler(
                    'logs/pipelinepro_enhanced.log',
                    mode='a',
                    maxBytes=10*1024*1024,  # 10MB per file
                    backupCount=7,  # Keep 7 backup files
                    encoding='utf-8'
                )
                # Use safe print for Windows compatibility
                try:
                    import sys
                    msg = "OK: Using ConcurrentRotatingFileHandler (Windows-safe)"
                    sys.stdout.buffer.write(msg.encode('utf-8'))
                    sys.stdout.buffer.write(b'\n')
                except Exception:
                    print("OK: Using ConcurrentRotatingFileHandler (Windows-safe)")
            else:
                # Fallback to TimedRotatingFileHandler (may have issues on Windows)
                main_file_handler = logging.handlers.TimedRotatingFileHandler(
                    'logs/pipelinepro_enhanced.log',
                    when='midnight',
                    interval=1,
                    backupCount=7,
                    encoding='utf-8',
                    delay=True
                )
                if platform.system() == 'Windows':
                    # Use safe print for Windows compatibility
                    try:
                        import sys
                        msg = "WARNING: Using TimedRotatingFileHandler on Windows - may cause file lock issues"
                        sys.stdout.buffer.write(msg.encode('utf-8'))
                        sys.stdout.buffer.write(b'\n')
                    except Exception:
                        print("WARNING: Using TimedRotatingFileHandler on Windows - may cause file lock issues")
            
            main_file_handler.setLevel(logging.INFO)
            main_file_handler.setFormatter(formatter)
            self.logger.addHandler(main_file_handler)
            
            # Error file handler
            if HAS_CONCURRENT_HANDLER and platform.system() == 'Windows':
                error_file_handler = ConcurrentRotatingFileHandler(
                    'logs/pipelinepro_errors_enhanced.log',
                    mode='a',
                    maxBytes=10*1024*1024,  # 10MB
                    backupCount=7,
                    encoding='utf-8'
                )
            else:
                error_file_handler = logging.handlers.TimedRotatingFileHandler(
                    'logs/pipelinepro_errors_enhanced.log',
                    when='midnight',
                    interval=1,
                    backupCount=7,
                    encoding='utf-8',
                    delay=True
                )
            
            error_file_handler.setLevel(logging.ERROR)
            error_file_handler.setFormatter(formatter)
            self.logger.addHandler(error_file_handler)
            
            # Debug file handler for development
            if self.is_development:
                if HAS_CONCURRENT_HANDLER and platform.system() == 'Windows':
                    debug_file_handler = ConcurrentRotatingFileHandler(
                        'logs/pipelinepro_debug_enhanced.log',
                        mode='a',
                        maxBytes=10*1024*1024,  # 10MB
                        backupCount=3,
                        encoding='utf-8'
                    )
                else:
                    debug_file_handler = logging.handlers.TimedRotatingFileHandler(
                        'logs/pipelinepro_debug_enhanced.log',
                        when='midnight',
                        interval=1,
                        backupCount=3,
                        encoding='utf-8',
                        delay=True
                    )
                
                debug_file_handler.setLevel(logging.DEBUG)
                debug_file_handler.setFormatter(formatter)
                self.logger.addHandler(debug_file_handler)
                
        except Exception as e:
            # Use print since logger might not be available
            # Ensure UTF-8 encoding for error messages
            try:
                import sys
                error_msg = f"Failed to setup file handler: {e}"
                sys.stdout.buffer.write(error_msg.encode('utf-8'))
                sys.stdout.buffer.write(b'\n')
            except Exception:
                # Fallback to ASCII-safe message
                print(f"Failed to setup file handler: {str(e).encode('ascii', 'replace').decode('ascii')}")
    
    def info(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log info message with optional structured data"""
        if self.use_json and extra_data:
            # Store extra_data in record for JSON formatter
            self.logger.info(message, extra={'extra_data': extra_data})
        else:
            if extra_data:
                message = f"{message} | {json.dumps(extra_data)}"
            self.logger.info(message)
    
    def warning(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log warning message"""
        if extra_data:
            message = f"{message} | {json.dumps(extra_data)}"
        self.logger.warning(message)
    
    def error(self, message: str, extra_data: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """Log error message with optional structured data and exception info"""
        if self.use_json and extra_data:
            self.logger.error(message, extra={'extra_data': extra_data}, exc_info=exc_info)
        else:
            if extra_data:
                message = f"{message} | {json.dumps(extra_data)}"
            self.logger.error(message, exc_info=exc_info)
    
    def critical(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log critical message with optional structured data"""
        if self.use_json and extra_data:
            self.logger.critical(message, extra={'extra_data': extra_data})
        else:
            if extra_data:
                message = f"{message} | {json.dumps(extra_data)}"
            self.logger.critical(message)
    
    def debug(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log debug message (only in development)"""
        if self.is_development:
            if extra_data:
                message = f"{message} | {json.dumps(extra_data)}"
            self.logger.debug(message)
    
    def log_performance(self, operation: str, duration: float, extra_data: Optional[Dict[str, Any]] = None):
        """Log performance metrics"""
        if duration > 1.0 or not self.is_development:  # Log slow operations or in production
            data = {'operation': operation, 'duration': duration}
            if extra_data:
                data.update(extra_data)
            self.warning(f"Performance: {operation} took {duration:.2f}s", data)
    
    def log_request(self, method: str, path: str, status_code: int, duration: float):
        """Log HTTP request"""
        if status_code >= 400 or duration > 0.5:  # Log errors or slow requests
            self.warning(f"Request: {method} {path} - {status_code} ({duration:.2f}s)")
        elif not self.is_development:  # Log all requests in production
            self.info(f"Request: {method} {path} - {status_code} ({duration:.2f}s)")
    
    def log_database_operation(self, operation: str, duration: float, query_count: int = 1):
        """Log database operations"""
        if duration > 0.1 or query_count > 10:  # Log slow operations or high query count
            self.warning(f"Database: {operation} - {duration:.2f}s ({query_count} queries)")
    
    def log_security_event(self, event_type: str, details: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log security events"""
        data = {'event_type': event_type, 'details': details}
        if extra_data:
            data.update(extra_data)
        self.warning(f"Security: {event_type} - {details}", data)
    
    def log_exception(self, error: Exception, context: Optional[Dict[str, Any]] = None, include_traceback: bool = True):
        """Log exception with context and correlation ID"""
        # Get request ID for correlation (only if in request context)
        request_id = None
        try:
            from flask import has_request_context
            if has_request_context() and request and hasattr(request, 'request_id'):
                request_id = request.request_id
        except (RuntimeError, ImportError):
            pass
        
        error_message = f"Exception: {type(error).__name__}: {str(error)}"
        
        if self.use_json:
            # Use structured logging with exception info
            exc_info = sys.exc_info() if include_traceback else None
            extra = {'extra_data': context or {}, 'request_id': request_id}
            self.logger.error(error_message, exc_info=exc_info, extra=extra)
        else:
            if context:
                error_message += f" | Context: {json.dumps(context, default=str)}"
            if request_id:
                error_message += f" | Request ID: {request_id}"
            
            if include_traceback:
                error_message += f"\n{traceback.format_exc()}"
            
            self.error(error_message)
    
    def log_database_query(self, query: str, params: tuple = None, duration: float = 0.0, slow_query_threshold: float = 1.0):
        """Log database query"""
        if duration > slow_query_threshold:
            self.warning(f"Slow DB Query ({duration:.3f}s): {query[:200]}...")
        elif self.is_development:
            self.debug(f"DB Query ({duration:.3f}s): {query[:200]}...")
    
    def log_performance_metrics(self, operation: str, duration: float, additional_metrics: Optional[Dict[str, Any]] = None):
        """Log performance metrics"""
        message = f"Performance: {operation} - {duration:.3f}s"
        if additional_metrics:
            message += f" | {json.dumps(additional_metrics, default=str)}"
        self.info(message)


class PerformanceLogger:
    """Context manager for performance logging"""
    
    def __init__(self, logger: UnifiedLogger, operation: str, context: Optional[Dict[str, Any]] = None):
        self.logger = logger
        self.operation = operation
        self.context = context or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        if exc_type is not None:
            self.logger.error(f"Performance: {self.operation} failed after {duration:.3f}s: {exc_val}")
        else:
            self.logger.log_performance(self.operation, duration, self.context)
        return False


# Global logger instance
_logger_instance = None

def get_logger(name: str = "PipLinePro") -> UnifiedLogger:
    """Get or create a logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = UnifiedLogger(name)
    return _logger_instance

# Compatibility alias
get_enhanced_logger = get_logger

def setup_logging(app):
    """Setup logging for Flask app"""
    logger = get_logger("PipLinePro")
    
    # Configure Flask's logger
    app.logger.setLevel(logging.INFO)
    
    # Remove default handlers
    for handler in app.logger.handlers[:]:
        app.logger.removeHandler(handler)
    
    # Add our unified logger
    app.logger.addHandler(logger.logger.handlers[0])
    
    return logger

def log_function_call(func):
    """Decorator to log function calls"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger("FunctionCall")
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.debug(f"Function {func.__name__} completed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Function {func.__name__} failed after {duration:.2f}s: {str(e)}")
            raise
    
    return wrapper

def log_api_call(func):
    """Decorator to log API calls"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger("APICall")
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.log_performance(f"API {func.__name__}", duration)
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"API {func.__name__} failed after {duration:.2f}s: {str(e)}")
            raise
    
    return wrapper
