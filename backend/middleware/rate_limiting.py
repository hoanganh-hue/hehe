"""
Rate Limiting Middleware
Redis-based rate limiting for API protection
"""

import logging
import time
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from config import settings
from database.connection import get_database_connection

logger = logging.getLogger(__name__)

class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis"""
    
    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.redis_client = None
        self.rate_limit_requests = settings.RATE_LIMIT_REQUESTS
        self.rate_limit_window = settings.RATE_LIMIT_WINDOW
        
        # Rate limit rules per endpoint
        self.rate_limit_rules = {
            "/api/auth/login": {"requests": 5, "window": 300},  # 5 requests per 5 minutes
            "/api/capture": {"requests": 100, "window": 60},     # 100 requests per minute
            "/api/admin": {"requests": 200, "window": 60},       # 200 requests per minute
            "/api/oauth": {"requests": 50, "window": 60},       # 50 requests per minute
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request through rate limiting middleware"""
        try:
            # Get Redis client
            if not self.redis_client:
                self.redis_client = get_database_connection("redis")
            
            # Get client identifier
            client_id = self._get_client_id(request)
            
            # Check rate limit
            if await self._is_rate_limited(client_id, request.url.path):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later.",
                    headers={"Retry-After": str(self.rate_limit_window)}
                )
            
            # Process request
            response = await call_next(request)
            
            # Update rate limit counter
            await self._update_rate_limit(client_id, request.url.path)
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Rate limiting middleware error: {e}")
            # Don't block requests if rate limiting fails
            return await call_next(request)
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier"""
        # Use IP address as primary identifier
        client_ip = request.client.host
        
        # Add user agent hash for additional uniqueness
        user_agent = request.headers.get("user-agent", "")
        user_agent_hash = str(hash(user_agent))[:8]
        
        return f"{client_ip}:{user_agent_hash}"
    
    async def _is_rate_limited(self, client_id: str, path: str) -> bool:
        """Check if client is rate limited"""
        try:
            # Get rate limit rule for path
            rule = self._get_rate_limit_rule(path)
            
            # Create Redis key
            key = f"rate_limit:{client_id}:{path}"
            
            # Get current count
            current_count = await self.redis_client.get(key)
            
            if current_count is None:
                return False
            
            return int(current_count) >= rule["requests"]
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return False
    
    async def _update_rate_limit(self, client_id: str, path: str):
        """Update rate limit counter"""
        try:
            # Get rate limit rule for path
            rule = self._get_rate_limit_rule(path)
            
            # Create Redis key
            key = f"rate_limit:{client_id}:{path}"
            
            # Increment counter with expiration
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, rule["window"])
            await pipe.execute()
            
        except Exception as e:
            logger.error(f"Rate limit update error: {e}")
    
    def _get_rate_limit_rule(self, path: str) -> Dict[str, Any]:
        """Get rate limit rule for path"""
        # Check for specific path rules
        for rule_path, rule in self.rate_limit_rules.items():
            if path.startswith(rule_path):
                return rule
        
        # Default rule
        return {
            "requests": self.rate_limit_requests,
            "window": self.rate_limit_window
        }

def setup_rate_limiting(app: FastAPI):
    """Setup rate limiting middleware"""
    try:
        app.add_middleware(RateLimitingMiddleware)
        logger.info("Rate limiting middleware configured")
        
    except Exception as e:
        logger.error(f"Failed to setup rate limiting middleware: {e}")
        raise
