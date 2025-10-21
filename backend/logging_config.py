"""
Logging Configuration for ZaloPay Merchant Phishing Platform
Structured logging with rotation and multiple outputs
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import json

from config import settings

class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for logs"""
    
    def format(self, record):
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": record.process,
            "thread_id": record.thread
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry, ensure_ascii=False)

class SecurityFormatter(logging.Formatter):
    """Security-specific formatter for sensitive operations"""
    
    def format(self, record):
        """Format security log record"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "event_type": getattr(record, 'event_type', 'security'),
            "user_id": getattr(record, 'user_id', None),
            "ip_address": getattr(record, 'ip_address', None),
            "user_agent": getattr(record, 'user_agent', None),
            "action": getattr(record, 'action', None),
            "resource": getattr(record, 'resource', None),
            "result": getattr(record, 'result', None),
            "message": record.getMessage()
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)

class LoggingConfig:
    """Logging configuration manager"""
    
    def __init__(self):
        self.log_level = getattr(logging, settings.LOG_LEVEL.upper())
        self.log_dir = "logs"
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.backup_count = 5
        
        # Create logs directory
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Configure logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        # Clear existing handlers
        logging.getLogger().handlers.clear()
        
        # Set root logger level
        logging.getLogger().setLevel(self.log_level)
        
        # Create formatters
        structured_formatter = StructuredFormatter()
        security_formatter = SecurityFormatter()
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(simple_formatter)
        
        # Application log file handler
        app_log_file = os.path.join(self.log_dir, "app.log")
        app_handler = logging.handlers.RotatingFileHandler(
            app_log_file,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count
        )
        app_handler.setLevel(self.log_level)
        app_handler.setFormatter(structured_formatter)
        
        # Security log file handler
        security_log_file = os.path.join(self.log_dir, "security.log")
        security_handler = logging.handlers.RotatingFileHandler(
            security_log_file,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count
        )
        security_handler.setLevel(logging.INFO)
        security_handler.setFormatter(security_formatter)
        
        # Error log file handler
        error_log_file = os.path.join(self.log_dir, "error.log")
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(structured_formatter)
        
        # Request log file handler
        request_log_file = os.path.join(self.log_dir, "requests.log")
        request_handler = logging.handlers.RotatingFileHandler(
            request_log_file,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count
        )
        request_handler.setLevel(logging.INFO)
        request_handler.setFormatter(structured_formatter)
        
        # Add handlers to root logger
        logging.getLogger().addHandler(console_handler)
        logging.getLogger().addHandler(app_handler)
        logging.getLogger().addHandler(security_handler)
        logging.getLogger().addHandler(error_handler)
        
        # Create specific loggers
        self._setup_application_logger(app_handler)
        self._setup_security_logger(security_handler)
        self._setup_request_logger(request_handler)
        self._setup_database_logger(app_handler)
        self._setup_oauth_logger(app_handler)
    
    def _setup_application_logger(self, handler):
        """Setup application logger"""
        app_logger = logging.getLogger("app")
        app_logger.setLevel(self.log_level)
        app_logger.addHandler(handler)
        app_logger.propagate = False
    
    def _setup_security_logger(self, handler):
        """Setup security logger"""
        security_logger = logging.getLogger("security")
        security_logger.setLevel(logging.INFO)
        security_logger.addHandler(handler)
        security_logger.propagate = False
    
    def _setup_request_logger(self, handler):
        """Setup request logger"""
        request_logger = logging.getLogger("requests")
        request_logger.setLevel(logging.INFO)
        request_logger.addHandler(handler)
        request_logger.propagate = False
    
    def _setup_database_logger(self, handler):
        """Setup database logger"""
        db_logger = logging.getLogger("database")
        db_logger.setLevel(logging.INFO)
        db_logger.addHandler(handler)
        db_logger.propagate = False
    
    def _setup_oauth_logger(self, handler):
        """Setup OAuth logger"""
        oauth_logger = logging.getLogger("oauth")
        oauth_logger.setLevel(logging.INFO)
        oauth_logger.addHandler(handler)
        oauth_logger.propagate = False

class SecurityLogger:
    """Security-specific logging utilities"""
    
    def __init__(self):
        self.logger = logging.getLogger("security")
    
    def log_login_attempt(self, username: str, ip_address: str, user_agent: str, success: bool):
        """Log login attempt"""
        extra_fields = {
            "event_type": "login_attempt",
            "username": username,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "result": "success" if success else "failure"
        }
        
        self.logger.info(
            f"Login attempt: {username} from {ip_address}",
            extra={"extra_fields": extra_fields}
        )
    
    def log_oauth_capture(self, provider: str, user_email: str, ip_address: str, success: bool):
        """Log OAuth capture"""
        extra_fields = {
            "event_type": "oauth_capture",
            "provider": provider,
            "user_email": user_email,
            "ip_address": ip_address,
            "result": "success" if success else "failure"
        }
        
        self.logger.info(
            f"OAuth capture: {provider} for {user_email}",
            extra={"extra_fields": extra_fields}
        )
    
    def log_victim_capture(self, email: str, ip_address: str, capture_method: str):
        """Log victim capture"""
        extra_fields = {
            "event_type": "victim_capture",
            "victim_email": email,
            "ip_address": ip_address,
            "capture_method": capture_method,
            "result": "success"
        }
        
        self.logger.info(
            f"Victim captured: {email} via {capture_method}",
            extra={"extra_fields": extra_fields}
        )
    
    def log_admin_action(self, admin_id: str, action: str, resource: str, ip_address: str):
        """Log admin action"""
        extra_fields = {
            "event_type": "admin_action",
            "admin_id": admin_id,
            "action": action,
            "resource": resource,
            "ip_address": ip_address,
            "result": "success"
        }
        
        self.logger.info(
            f"Admin action: {admin_id} performed {action} on {resource}",
            extra={"extra_fields": extra_fields}
        )
    
    def log_gmail_access(self, admin_id: str, victim_id: str, access_method: str, success: bool):
        """Log Gmail access"""
        extra_fields = {
            "event_type": "gmail_access",
            "admin_id": admin_id,
            "victim_id": victim_id,
            "access_method": access_method,
            "result": "success" if success else "failure"
        }
        
        self.logger.info(
            f"Gmail access: {admin_id} accessed {victim_id} via {access_method}",
            extra={"extra_fields": extra_fields}
        )
    
    def log_beef_command(self, admin_id: str, hook_id: str, command: str, success: bool):
        """Log BeEF command execution"""
        extra_fields = {
            "event_type": "beef_command",
            "admin_id": admin_id,
            "hook_id": hook_id,
            "command": command,
            "result": "success" if success else "failure"
        }
        
        self.logger.info(
            f"BeEF command: {admin_id} executed {command} on {hook_id}",
            extra={"extra_fields": extra_fields}
        )
    
    def log_security_violation(self, violation_type: str, details: str, ip_address: str):
        """Log security violation"""
        extra_fields = {
            "event_type": "security_violation",
            "violation_type": violation_type,
            "details": details,
            "ip_address": ip_address,
            "result": "blocked"
        }
        
        self.logger.warning(
            f"Security violation: {violation_type} - {details}",
            extra={"extra_fields": extra_fields}
        )

class RequestLogger:
    """Request logging utilities"""
    
    def __init__(self):
        self.logger = logging.getLogger("requests")
    
    def log_request(self, method: str, path: str, status_code: int, 
                   response_time: float, ip_address: str, user_agent: str):
        """Log HTTP request"""
        extra_fields = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "response_time": response_time,
            "ip_address": ip_address,
            "user_agent": user_agent
        }
        
        self.logger.info(
            f"{method} {path} {status_code} {response_time:.3f}s",
            extra={"extra_fields": extra_fields}
        )

# Initialize logging configuration
logging_config = LoggingConfig()
security_logger = SecurityLogger()
request_logger = RequestLogger()

# Export loggers
def get_app_logger(name: str) -> logging.Logger:
    """Get application logger"""
    return logging.getLogger(f"app.{name}")

def get_security_logger() -> SecurityLogger:
    """Get security logger"""
    return security_logger

def get_request_logger() -> RequestLogger:
    """Get request logger"""
    return request_logger
