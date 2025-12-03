# Backend/app/utils/logging.py
"""
Structured logging utilities with context
Improves traceability and debugging in production
"""

import logging
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from contextvars import ContextVar

# Context variable for request ID
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


class StructuredLogger:
    """
    Structured logger that automatically adds context to all logs
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.name = name
    
    def _build_log_data(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Build structured dictionary for log entry"""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "logger": self.name,
            "message": message,
        }
        
        # Add request_id if exists in context
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id
        
        # Add extra data
        if extra:
            log_data.update(extra)
        
        # Add kwargs
        if kwargs:
            log_data.update(kwargs)
        
        return log_data
    
    def _format_message(self, log_data: Dict[str, Any]) -> str:
        """Format message for readable logging"""
        # Readable format for development
        parts = [f"[{log_data.get('logger', 'app')}]"]
        
        if 'request_id' in log_data:
            parts.append(f"[{log_data['request_id'][:8]}]")
        
        parts.append(log_data['message'])
        
        # Add additional fields
        extra_fields = {k: v for k, v in log_data.items() 
                       if k not in ['timestamp', 'logger', 'message', 'request_id']}
        
        if extra_fields:
            parts.append(json.dumps(extra_fields))
        
        return " ".join(parts)
    
    def info(self, message: str, **kwargs):
        """Log INFO level with context"""
        log_data = self._build_log_data(message, **kwargs)
        self.logger.info(self._format_message(log_data))
    
    def warning(self, message: str, **kwargs):
        """Log WARNING level with context"""
        log_data = self._build_log_data(message, **kwargs)
        self.logger.warning(self._format_message(log_data))
    
    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log ERROR level with context"""
        log_data = self._build_log_data(message, **kwargs)
        self.logger.error(self._format_message(log_data), exc_info=exc_info)
    
    def debug(self, message: str, **kwargs):
        """Log DEBUG level with context"""
        log_data = self._build_log_data(message, **kwargs)
        self.logger.debug(self._format_message(log_data))
    
    def critical(self, message: str, **kwargs):
        """Log CRITICAL level with context"""
        log_data = self._build_log_data(message, **kwargs)
        self.logger.critical(self._format_message(log_data))


def get_logger(name: str) -> StructuredLogger:
    """
    Factory to get a structured logger
    
    Usage:
        from app.utils.logging import get_logger
        logger = get_logger(__name__)
        logger.info("User logged in", user_id="123", email="user@example.com")
    """
    return StructuredLogger(name)


class LoggerAdapter:
    """
    Adapter to maintain compatibility with standard logging.Logger
    Allows gradual migration of existing code
    """
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
    
    def info(self, msg: str, *args, **kwargs):
        """Compatible with logging.Logger.info()"""
        if args:
            msg = msg % args
        self.logger.info(msg, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        """Compatible with logging.Logger.warning()"""
        if args:
            msg = msg % args
        self.logger.warning(msg, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        """Compatible with logging.Logger.error()"""
        if args:
            msg = msg % args
        exc_info = kwargs.pop('exc_info', False)
        self.logger.error(msg, exc_info=exc_info, **kwargs)
    
    def debug(self, msg: str, *args, **kwargs):
        """Compatible with logging.Logger.debug()"""
        if args:
            msg = msg % args
        self.logger.debug(msg, **kwargs)


def log_with_context(
    level: str,
    message: str,
    logger_name: str = "app",
    **context
):
    """
    Helper for quick logging with context
    
    Usage:
        log_with_context("info", "Processing file", 
                        filename="data.csv", rows=1000)
    """
    logger = get_logger(logger_name)
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(message, **context)


# JSON format configuration for production (optional)
class JSONFormatter(logging.Formatter):
    """
    Formatter for JSON output in production
    Useful for centralized logging systems (ELK, Splunk, etc.)
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add request_id if exists
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id
        
        # Add exception info if exists
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        return json.dumps(log_data)


# Production usage example
def configure_production_logging():
    """
    Configure logging for production with JSON format
    Call this in main.py for production environments
    """
    root_logger = logging.getLogger()
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create handler with JSON format
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
