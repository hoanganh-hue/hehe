"""
Structured Logging Configuration
Provides structured logging with JSON format and log rotation
"""

import logging
import logging.handlers
import json
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path
import os

class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured JSON logging
    """
    
    def __init__(self, service_name: str = "zalopay_phishing"):
        super().__init__()
        self.service_name = service_name
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as structured JSON
        
        Args:
            record: Log record to format
            
        Returns:
            JSON formatted log string
        """
        # Base log structure
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "service": self.service_name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in [
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'lineno', 'funcName', 'created',
                'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'getMessage', 'exc_info',
                'exc_text', 'stack_info'
            ]:
                log_data[key] = value
        
        return json.dumps(log_data, ensure_ascii=False, default=str)

class SecurityFormatter(logging.Formatter):
    """
    Custom formatter for security events
    """
    
    def __init__(self, service_name: str = "zalopay_phishing"):
        super().__init__()
        self.service_name = service_name
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format security log record
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted security log string
        """
        # Security log structure
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "service": self.service_name,
            "event_type": "security",
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add security-specific fields
        security_fields = [
            'user_id', 'ip_address', 'user_agent', 'request_id',
            'session_id', 'event_type', 'risk_level', 'threat_type',
            'action_taken', 'resource', 'method', 'status_code'
        ]
        
        for field in security_fields:
            if hasattr(record, field):
                log_data[field] = getattr(record, field)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }
        
        return json.dumps(log_data, ensure_ascii=False, default=str)

class AuditFormatter(logging.Formatter):
    """
    Custom formatter for audit logs
    """
    
    def __init__(self, service_name: str = "zalopay_phishing"):
        super().__init__()
        self.service_name = service_name
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format audit log record
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted audit log string
        """
        # Audit log structure
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "service": self.service_name,
            "event_type": "audit",
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add audit-specific fields
        audit_fields = [
            'user_id', 'admin_id', 'action', 'resource', 'resource_id',
            'ip_address', 'user_agent', 'request_id', 'session_id',
            'old_values', 'new_values', 'status', 'reason'
        ]
        
        for field in audit_fields:
            if hasattr(record, field):
                log_data[field] = getattr(record, field)
        
        return json.dumps(log_data, ensure_ascii=False, default=str)

class LoggingManager:
    """
    Centralized logging management
    """
    
    def __init__(self, service_name: str = "zalopay_phishing"):
        self.service_name = service_name
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Log file paths
        self.app_log_file = self.log_dir / "application.log"
        self.security_log_file = self.log_dir / "security.log"
        self.audit_log_file = self.log_dir / "audit.log"
        self.error_log_file = self.log_dir / "error.log"
        
        # Initialize loggers
        self._setup_loggers()
    
    def _setup_loggers(self):
        """Setup all loggers with appropriate handlers and formatters"""
        
        # Root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Application logger
        self._setup_application_logger()
        
        # Security logger
        self._setup_security_logger()
        
        # Audit logger
        self._setup_audit_logger()
        
        # Error logger
        self._setup_error_logger()
        
        # Console logger
        self._setup_console_logger()
    
    def _setup_application_logger(self):
        """Setup application logger"""
        app_logger = logging.getLogger("application")
        app_logger.setLevel(logging.INFO)
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            self.app_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(StructuredFormatter(self.service_name))
        app_logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        app_logger.propagate = False
    
    def _setup_security_logger(self):
        """Setup security logger"""
        security_logger = logging.getLogger("security")
        security_logger.setLevel(logging.INFO)
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            self.security_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,  # Keep more security logs
            encoding='utf-8'
        )
        file_handler.setFormatter(SecurityFormatter(self.service_name))
        security_logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        security_logger.propagate = False
    
    def _setup_audit_logger(self):
        """Setup audit logger"""
        audit_logger = logging.getLogger("audit")
        audit_logger.setLevel(logging.INFO)
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            self.audit_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=20,  # Keep more audit logs
            encoding='utf-8'
        )
        file_handler.setFormatter(AuditFormatter(self.service_name))
        audit_logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        audit_logger.propagate = False
    
    def _setup_error_logger(self):
        """Setup error logger"""
        error_logger = logging.getLogger("error")
        error_logger.setLevel(logging.ERROR)
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            self.error_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(StructuredFormatter(self.service_name))
        error_logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        error_logger.propagate = False
    
    def _setup_console_logger(self):
        """Setup console logger for development"""
        console_logger = logging.getLogger("console")
        console_logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(StructuredFormatter(self.service_name))
        console_logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        console_logger.propagate = False
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger instance
        
        Args:
            name: Logger name
            
        Returns:
            Logger instance
        """
        return logging.getLogger(name)
    
    def get_application_logger(self) -> logging.Logger:
        """Get application logger"""
        return logging.getLogger("application")
    
    def get_security_logger(self) -> logging.Logger:
        """Get security logger"""
        return logging.getLogger("security")
    
    def get_audit_logger(self) -> logging.Logger:
        """Get audit logger"""
        return logging.getLogger("audit")
    
    def get_error_logger(self) -> logging.Logger:
        """Get error logger"""
        return logging.getLogger("error")
    
    def get_console_logger(self) -> logging.Logger:
        """Get console logger"""
        return logging.getLogger("console")
    
    def log_application_event(self, level: str, message: str, **kwargs):
        """
        Log application event
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            **kwargs: Additional fields
        """
        logger = self.get_application_logger()
        log_level = getattr(logging, level.upper(), logging.INFO)
        logger.log(log_level, message, extra=kwargs)
    
    def log_security_event(self, level: str, message: str, **kwargs):
        """
        Log security event
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            **kwargs: Additional fields
        """
        logger = self.get_security_logger()
        log_level = getattr(logging, level.upper(), logging.INFO)
        logger.log(log_level, message, extra=kwargs)
    
    def log_audit_event(self, level: str, message: str, **kwargs):
        """
        Log audit event
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            **kwargs: Additional fields
        """
        logger = self.get_audit_logger()
        log_level = getattr(logging, level.upper(), logging.INFO)
        logger.log(log_level, message, extra=kwargs)
    
    def log_error(self, level: str, message: str, **kwargs):
        """
        Log error event
        
        Args:
            level: Log level (ERROR, CRITICAL)
            message: Log message
            **kwargs: Additional fields
        """
        logger = self.get_error_logger()
        log_level = getattr(logging, level.upper(), logging.ERROR)
        logger.log(log_level, message, extra=kwargs)
    
    def log_console(self, level: str, message: str, **kwargs):
        """
        Log to console
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            **kwargs: Additional fields
        """
        logger = self.get_console_logger()
        log_level = getattr(logging, level.upper(), logging.INFO)
        logger.log(log_level, message, extra=kwargs)
    
    def cleanup_old_logs(self, days: int = 30):
        """
        Clean up old log files
        
        Args:
            days: Number of days to keep logs
        """
        import time
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        
        for log_file in self.log_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
                print(f"Deleted old log file: {log_file}")

# Global logging manager instance
logging_manager: Optional[LoggingManager] = None

def get_logging_manager() -> LoggingManager:
    """Get the global logging manager instance"""
    global logging_manager
    if logging_manager is None:
        logging_manager = LoggingManager()
    return logging_manager

def setup_logging(service_name: str = "zalopay_phishing") -> LoggingManager:
    """
    Setup logging system
    
    Args:
        service_name: Name of the service
        
    Returns:
        LoggingManager instance
    """
    global logging_manager
    logging_manager = LoggingManager(service_name)
    return logging_manager

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return get_logging_manager().get_logger(name)

def log_application_event(level: str, message: str, **kwargs):
    """Log application event"""
    get_logging_manager().log_application_event(level, message, **kwargs)

def log_security_event(level: str, message: str, **kwargs):
    """Log security event"""
    get_logging_manager().log_security_event(level, message, **kwargs)

def log_audit_event(level: str, message: str, **kwargs):
    """Log audit event"""
    get_logging_manager().log_audit_event(level, message, **kwargs)

def log_error(level: str, message: str, **kwargs):
    """Log error event"""
    get_logging_manager().log_error(level, message, **kwargs)

def log_console(level: str, message: str, **kwargs):
    """Log to console"""
    get_logging_manager().log_console(level, message, **kwargs)

# Convenience functions for common logging scenarios
def log_request(request_id: str, method: str, path: str, status_code: int, response_time: float, **kwargs):
    """Log HTTP request"""
    log_application_event(
        "INFO",
        f"HTTP {method} {path} - {status_code}",
        request_id=request_id,
        method=method,
        path=path,
        status_code=status_code,
        response_time=response_time,
        **kwargs
    )

def log_authentication(user_id: str, success: bool, ip_address: str, **kwargs):
    """Log authentication event"""
    level = "INFO" if success else "WARNING"
    message = f"Authentication {'successful' if success else 'failed'} for user {user_id}"
    
    log_security_event(
        level,
        message,
        user_id=user_id,
        success=success,
        ip_address=ip_address,
        event_type="authentication",
        **kwargs
    )

def log_admin_action(admin_id: str, action: str, resource: str, resource_id: str, **kwargs):
    """Log admin action"""
    log_audit_event(
        "INFO",
        f"Admin {admin_id} performed {action} on {resource} {resource_id}",
        admin_id=admin_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        **kwargs
    )

def log_victim_activity(victim_id: str, activity: str, **kwargs):
    """Log victim activity"""
    log_application_event(
        "INFO",
        f"Victim {victim_id} activity: {activity}",
        victim_id=victim_id,
        activity=activity,
        **kwargs
    )

def log_system_error(error: Exception, context: str = "", **kwargs):
    """Log system error"""
    log_error(
        "ERROR",
        f"System error in {context}: {str(error)}",
        error_type=type(error).__name__,
        error_message=str(error),
        context=context,
        **kwargs
    )
