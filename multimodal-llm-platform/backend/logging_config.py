#!/usr/bin/env python3
"""
Comprehensive logging and error tracking system for Autopicker Platform
Implements structured logging, error tracking, and observability
"""

import os
import sys
import json
import time
import asyncio
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
import functools

# Third-party imports for enhanced logging
try:
    import structlog
    from pythonjsonlogger import jsonlogger
    STRUCTURED_LOGGING_AVAILABLE = True
except ImportError:
    STRUCTURED_LOGGING_AVAILABLE = False
    print("Warning: Advanced logging libraries not available. Using basic logging.")

# Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "json")  # json, text, or structured
LOG_DIR = Path(os.getenv("LOG_DIR", "/tmp/autopicker/logs"))
MAX_LOG_SIZE = int(os.getenv("MAX_LOG_SIZE", "10485760"))  # 10MB
BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)


class CustomJSONFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""
    
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add service information
        log_record['service'] = 'autopicker-platform'
        log_record['version'] = '1.0.0'
        
        # Add request ID if available
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        
        # Add user information if available
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        
        # Add performance metrics if available
        if hasattr(record, 'duration_ms'):
            log_record['duration_ms'] = record.duration_ms


class ErrorTracker:
    """Centralized error tracking and reporting"""
    
    def __init__(self):
        self.error_counts = {}
        self.recent_errors = []
        self.max_recent_errors = 100
        
    def track_error(self, error: Exception, context: Dict[str, Any] = None):
        """Track an error occurrence"""
        error_type = type(error).__name__
        error_message = str(error)
        
        # Count errors by type
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Store recent error
        error_info = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': error_type,
            'message': error_message,
            'traceback': traceback.format_exc(),
            'context': context or {}
        }
        
        self.recent_errors.append(error_info)
        
        # Limit recent errors list
        if len(self.recent_errors) > self.max_recent_errors:
            self.recent_errors.pop(0)
        
        return error_info
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of tracked errors"""
        return {
            'error_counts': self.error_counts,
            'recent_errors_count': len(self.recent_errors),
            'recent_errors': self.recent_errors[-10:],  # Last 10 errors
            'total_errors': sum(self.error_counts.values())
        }


class PerformanceTracker:
    """Track performance metrics and timing"""
    
    def __init__(self):
        self.metrics = {}
        self.request_times = []
        self.max_request_times = 1000
    
    @contextmanager
    def track_time(self, operation: str, context: Dict[str, Any] = None):
        """Context manager to track operation timing"""
        start_time = time.time()
        start_timestamp = datetime.utcnow()
        
        try:
            yield
        finally:
            duration = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Track in metrics
            if operation not in self.metrics:
                self.metrics[operation] = {
                    'count': 0,
                    'total_time': 0,
                    'min_time': float('inf'),
                    'max_time': 0,
                    'avg_time': 0
                }
            
            metric = self.metrics[operation]
            metric['count'] += 1
            metric['total_time'] += duration
            metric['min_time'] = min(metric['min_time'], duration)
            metric['max_time'] = max(metric['max_time'], duration)
            metric['avg_time'] = metric['total_time'] / metric['count']
            
            # Track request timing
            request_info = {
                'operation': operation,
                'duration_ms': duration,
                'timestamp': start_timestamp.isoformat(),
                'context': context or {}
            }
            
            self.request_times.append(request_info)
            
            # Limit request times list
            if len(self.request_times) > self.max_request_times:
                self.request_times.pop(0)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance metrics summary"""
        return {
            'metrics': self.metrics,
            'recent_requests': len(self.request_times),
            'slow_requests': [
                req for req in self.request_times[-100:] 
                if req['duration_ms'] > 1000  # Slower than 1 second
            ]
        }


class LoggingManager:
    """Central logging management"""
    
    def __init__(self):
        self.error_tracker = ErrorTracker()
        self.performance_tracker = PerformanceTracker()
        self.setup_logging()
    
    def setup_logging(self):
        """Setup comprehensive logging configuration"""
        # Create formatters
        if LOG_FORMAT == "json" and STRUCTURED_LOGGING_AVAILABLE:
            formatter = CustomJSONFormatter(
                fmt='%(timestamp)s %(level)s %(name)s %(message)s'
            )
        else:
            formatter = logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, LOG_LEVEL))
        
        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(getattr(logging, LOG_LEVEL))
        root_logger.addHandler(console_handler)
        
        # File handlers
        self.setup_file_handlers(formatter)
        
        # Setup structured logging if available
        if STRUCTURED_LOGGING_AVAILABLE:
            self.setup_structured_logging()
    
    def setup_file_handlers(self, formatter):
        """Setup rotating file handlers"""
        from logging.handlers import RotatingFileHandler
        
        # Main application log
        app_handler = RotatingFileHandler(
            LOG_DIR / "autopicker.log",
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT
        )
        app_handler.setFormatter(formatter)
        app_handler.setLevel(logging.INFO)
        
        # Error log
        error_handler = RotatingFileHandler(
            LOG_DIR / "errors.log",
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT
        )
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        
        # Performance log
        perf_handler = RotatingFileHandler(
            LOG_DIR / "performance.log",
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT
        )
        perf_handler.setFormatter(formatter)
        perf_handler.setLevel(logging.INFO)
        
        # Add handlers to loggers
        app_logger = logging.getLogger("autopicker")
        app_logger.addHandler(app_handler)
        app_logger.addHandler(error_handler)
        
        perf_logger = logging.getLogger("autopicker.performance")
        perf_logger.addHandler(perf_handler)
    
    def setup_structured_logging(self):
        """Setup structured logging with structlog"""
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )


# Global instances
logging_manager = LoggingManager()
error_tracker = logging_manager.error_tracker
performance_tracker = logging_manager.performance_tracker


def log_error(error: Exception, context: Dict[str, Any] = None, logger_name: str = "autopicker"):
    """Log an error with tracking"""
    logger = logging.getLogger(logger_name)
    
    # Track the error
    error_info = error_tracker.track_error(error, context)
    
    # Log with full context
    logger.error(
        f"Error: {error}",
        extra={
            'error_type': type(error).__name__,
            'error_context': context or {},
            'traceback': traceback.format_exc()
        }
    )
    
    return error_info


def log_performance(operation: str, duration_ms: float, context: Dict[str, Any] = None):
    """Log performance metrics"""
    perf_logger = logging.getLogger("autopicker.performance")
    
    perf_logger.info(
        f"Performance: {operation}",
        extra={
            'operation': operation,
            'duration_ms': duration_ms,
            'context': context or {}
        }
    )


def performance_monitor(operation_name: str = None):
    """Decorator to monitor function performance"""
    def decorator(func):
        nonlocal operation_name
        if operation_name is None:
            operation_name = f"{func.__module__}.{func.__name__}"
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with performance_tracker.track_time(operation_name):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration = (time.time() - start_time) * 1000
                    log_performance(operation_name, duration)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with performance_tracker.track_time(operation_name):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = (time.time() - start_time) * 1000
                    log_performance(operation_name, duration)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


def error_handler(logger_name: str = "autopicker"):
    """Decorator to handle and log errors"""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                log_error(e, {
                    'function': func.__name__,
                    'args': str(args)[:200],
                    'kwargs': str(kwargs)[:200]
                }, logger_name)
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_error(e, {
                    'function': func.__name__,
                    'args': str(args)[:200],
                    'kwargs': str(kwargs)[:200]
                }, logger_name)
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


class RequestLogger:
    """Middleware for logging HTTP requests"""
    
    def __init__(self, logger_name: str = "autopicker.requests"):
        self.logger = logging.getLogger(logger_name)
    
    async def log_request(self, request, response, duration_ms: float):
        """Log HTTP request details"""
        self.logger.info(
            f"{request.method} {request.url.path}",
            extra={
                'method': request.method,
                'path': request.url.path,
                'status_code': response.status_code,
                'duration_ms': duration_ms,
                'client_ip': request.client.host if request.client else 'unknown',
                'user_agent': request.headers.get('user-agent', 'unknown'),
                'request_size': request.headers.get('content-length', 0),
                'response_size': response.headers.get('content-length', 0)
            }
        )


def get_logging_status() -> Dict[str, Any]:
    """Get current logging system status"""
    return {
        'log_level': LOG_LEVEL,
        'log_format': LOG_FORMAT,
        'log_directory': str(LOG_DIR),
        'error_tracking': error_tracker.get_error_summary(),
        'performance_tracking': performance_tracker.get_performance_summary(),
        'active_loggers': [
            name for name in logging.Logger.manager.loggerDict.keys()
            if not name.startswith('_')
        ]
    }


async def log_system_health():
    """Background task to log system health metrics"""
    logger = logging.getLogger("autopicker.health")
    
    while True:
        try:
            import psutil
            
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            logger.info(
                "System health check",
                extra={
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_gb': memory.available / (1024**3),
                    'disk_percent': disk.percent,
                    'disk_free_gb': disk.free / (1024**3),
                    'process_count': len(psutil.pids())
                }
            )
            
            await asyncio.sleep(300)  # Log every 5 minutes
            
        except Exception as e:
            log_error(e, {'context': 'system_health_logging'})
            await asyncio.sleep(60)  # Retry after 1 minute


if __name__ == "__main__":
    # Test logging system
    logger = logging.getLogger("autopicker.test")
    
    print("Testing logging system...")
    
    # Test regular logging
    logger.info("Test info message")
    logger.warning("Test warning message")
    
    # Test error tracking
    try:
        raise ValueError("Test error for tracking")
    except Exception as e:
        log_error(e, {'test_context': 'unit_test'})
    
    # Test performance tracking
    @performance_monitor("test_operation")
    def test_function():
        time.sleep(0.1)
        return "test result"
    
    result = test_function()
    
    # Show status
    status = get_logging_status()
    print(f"Logging system status: {json.dumps(status, indent=2, default=str)}")
    
    print("Logging system test completed!")