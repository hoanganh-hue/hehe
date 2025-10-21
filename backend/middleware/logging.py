"""
Logging Middleware
Request/response logging and activity tracking
"""

import logging
import time
import json
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from config import settings

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Logging middleware for request/response tracking"""
    
    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.logger = logging.getLogger("request_logger")
        
        # Configure request logger
        handler = logging.FileHandler("logs/requests.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    async def dispatch(self, request: Request, call_next):
        """Process request through logging middleware"""
        start_time = time.time()
        
        # Extract request information
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "headers": dict(request.headers)
        }
        
        # Log request
        self.logger.info(f"Request: {json.dumps(request_info)}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Extract response information
            response_info = {
                "status_code": response.status_code,
                "process_time": round(process_time, 4),
                "response_headers": dict(response.headers)
            }
            
            # Log response
            self.logger.info(f"Response: {json.dumps(response_info)}")
            
            # Add custom headers
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = self._generate_request_id()
            
            return response
            
        except Exception as e:
            # Log error
            error_info = {
                "error": str(e),
                "process_time": time.time() - start_time,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            self.logger.error(f"Request Error: {json.dumps(error_info)}")
            raise
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        import uuid
        return str(uuid.uuid4())

def setup_logging_middleware(app: FastAPI):
    """Setup logging middleware"""
    try:
        app.add_middleware(LoggingMiddleware)
        logger.info("Logging middleware configured")
        
    except Exception as e:
        logger.error(f"Failed to setup logging middleware: {e}")
        raise
