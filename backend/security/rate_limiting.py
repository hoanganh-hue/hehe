"""
Rate Limiting Implementation
Provides rate limiting for API endpoints and user actions
"""

import time
import asyncio
from typing import Dict, Optional, Tuple
from datetime import datetime, timezone, timedelta
import logging
from dataclasses import dataclass
from collections import defaultdict, deque
import hashlib

from ..database.redis_client import get_redis_client

logger = logging.getLogger(__name__)

@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10
    window_size: int = 60  # seconds

@dataclass
class RateLimitResult:
    """Rate limit check result"""
    allowed: bool
    remaining: int
    reset_time: int
    retry_after: Optional[int] = None

class RateLimiter:
    """
    Rate limiter implementation using sliding window algorithm
    """
    
    def __init__(self, config: RateLimitConfig):
        """
        Initialize rate limiter
        
        Args:
            config: Rate limit configuration
        """
        self.config = config
        self.redis_client = None
        self.local_cache = defaultdict(lambda: deque())
        self.cache_cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    async def initialize(self):
        """Initialize rate limiter with Redis client"""
        try:
            self.redis_client = await get_redis_client()
            logger.info("Rate limiter initialized with Redis")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis for rate limiting: {e}")
            logger.info("Using local cache for rate limiting")
    
    def _get_cache_key(self, identifier: str, window: str) -> str:
        """
        Generate cache key for rate limiting
        
        Args:
            identifier: Unique identifier (IP, user ID, etc.)
            window: Time window (minute, hour, day)
            
        Returns:
            Cache key string
        """
        return f"rate_limit:{identifier}:{window}"
    
    def _get_window_start(self, window: str) -> int:
        """
        Get window start timestamp
        
        Args:
            window: Time window (minute, hour, day)
            
        Returns:
            Window start timestamp
        """
        now = time.time()
        
        if window == "minute":
            return int(now // 60) * 60
        elif window == "hour":
            return int(now // 3600) * 3600
        elif window == "day":
            return int(now // 86400) * 86400
        else:
            return int(now)
    
    async def _check_redis_rate_limit(self, identifier: str, window: str, limit: int) -> RateLimitResult:
        """
        Check rate limit using Redis
        
        Args:
            identifier: Unique identifier
            window: Time window
            limit: Request limit
            
        Returns:
            Rate limit result
        """
        try:
            if not self.redis_client:
                return RateLimitResult(False, 0, 0)
            
            cache_key = self._get_cache_key(identifier, window)
            window_start = self._get_window_start(window)
            
            # Use Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            
            # Get current count
            pipe.zcard(cache_key)
            pipe.zremrangebyscore(cache_key, 0, window_start - 1)
            pipe.zadd(cache_key, {str(time.time()): time.time()})
            pipe.expire(cache_key, self.config.window_size)
            
            results = await pipe.execute()
            current_count = results[0]
            
            # Check if limit exceeded
            if current_count >= limit:
                # Get oldest request time for retry_after calculation
                oldest_requests = await self.redis_client.zrange(cache_key, 0, 0, withscores=True)
                if oldest_requests:
                    oldest_time = oldest_requests[0][1]
                    retry_after = int(oldest_time + self.config.window_size - time.time())
                else:
                    retry_after = self.config.window_size
                
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=window_start + self.config.window_size,
                    retry_after=retry_after
                )
            
            return RateLimitResult(
                allowed=True,
                remaining=limit - current_count - 1,
                reset_time=window_start + self.config.window_size
            )
            
        except Exception as e:
            logger.error(f"Error checking Redis rate limit: {e}")
            return RateLimitResult(False, 0, 0)
    
    def _check_local_rate_limit(self, identifier: str, window: str, limit: int) -> RateLimitResult:
        """
        Check rate limit using local cache
        
        Args:
            identifier: Unique identifier
            window: Time window
            limit: Request limit
            
        Returns:
            Rate limit result
        """
        try:
            cache_key = f"{identifier}:{window}"
            now = time.time()
            window_start = self._get_window_start(window)
            
            # Clean up old entries
            request_times = self.local_cache[cache_key]
            while request_times and request_times[0] < window_start:
                request_times.popleft()
            
            # Check if limit exceeded
            if len(request_times) >= limit:
                retry_after = int(request_times[0] + self.config.window_size - now)
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=window_start + self.config.window_size,
                    retry_after=retry_after
                )
            
            # Add current request
            request_times.append(now)
            
            return RateLimitResult(
                allowed=True,
                remaining=limit - len(request_times),
                reset_time=window_start + self.config.window_size
            )
            
        except Exception as e:
            logger.error(f"Error checking local rate limit: {e}")
            return RateLimitResult(False, 0, 0)
    
    async def check_rate_limit(self, identifier: str, window: str, limit: int) -> RateLimitResult:
        """
        Check rate limit for identifier
        
        Args:
            identifier: Unique identifier (IP, user ID, etc.)
            window: Time window (minute, hour, day)
            limit: Request limit
            
        Returns:
            Rate limit result
        """
        try:
            # Clean up local cache periodically
            if time.time() - self.last_cleanup > self.cache_cleanup_interval:
                await self._cleanup_local_cache()
                self.last_cleanup = time.time()
            
            # Try Redis first, fallback to local cache
            if self.redis_client:
                result = await self._check_redis_rate_limit(identifier, window, limit)
                if result.allowed or result.retry_after is not None:
                    return result
            
            # Fallback to local cache
            return self._check_local_rate_limit(identifier, window, limit)
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return RateLimitResult(False, 0, 0)
    
    async def _cleanup_local_cache(self):
        """Clean up old entries from local cache"""
        try:
            now = time.time()
            cutoff_time = now - (24 * 60 * 60)  # 24 hours ago
            
            for cache_key in list(self.local_cache.keys()):
                request_times = self.local_cache[cache_key]
                while request_times and request_times[0] < cutoff_time:
                    request_times.popleft()
                
                # Remove empty entries
                if not request_times:
                    del self.local_cache[cache_key]
                    
        except Exception as e:
            logger.error(f"Error cleaning up local cache: {e}")
    
    async def reset_rate_limit(self, identifier: str, window: str):
        """
        Reset rate limit for identifier
        
        Args:
            identifier: Unique identifier
            window: Time window
        """
        try:
            if self.redis_client:
                cache_key = self._get_cache_key(identifier, window)
                await self.redis_client.delete(cache_key)
            
            # Also clear from local cache
            cache_key = f"{identifier}:{window}"
            if cache_key in self.local_cache:
                del self.local_cache[cache_key]
                
        except Exception as e:
            logger.error(f"Error resetting rate limit: {e}")

class IPRateLimiter:
    """
    IP-based rate limiter
    """
    
    def __init__(self, config: RateLimitConfig):
        """
        Initialize IP rate limiter
        
        Args:
            config: Rate limit configuration
        """
        self.rate_limiter = RateLimiter(config)
        self.blocked_ips = set()
        self.blocked_until = {}
        self.max_violations = 5
        self.block_duration = 3600  # 1 hour
    
    async def initialize(self):
        """Initialize IP rate limiter"""
        await self.rate_limiter.initialize()
    
    async def check_ip_rate_limit(self, ip_address: str) -> RateLimitResult:
        """
        Check rate limit for IP address
        
        Args:
            ip_address: IP address
            
        Returns:
            Rate limit result
        """
        try:
            # Check if IP is blocked
            if ip_address in self.blocked_ips:
                if ip_address in self.blocked_until:
                    if time.time() < self.blocked_until[ip_address]:
                        return RateLimitResult(
                            allowed=False,
                            remaining=0,
                            reset_time=self.blocked_until[ip_address],
                            retry_after=int(self.blocked_until[ip_address] - time.time())
                        )
                    else:
                        # Unblock IP
                        self.blocked_ips.discard(ip_address)
                        del self.blocked_until[ip_address]
            
            # Check rate limits
            minute_result = await self.rate_limiter.check_rate_limit(
                ip_address, "minute", self.rate_limiter.config.requests_per_minute
            )
            
            if not minute_result.allowed:
                await self._record_violation(ip_address)
                return minute_result
            
            hour_result = await self.rate_limiter.check_rate_limit(
                ip_address, "hour", self.rate_limiter.config.requests_per_hour
            )
            
            if not hour_result.allowed:
                await self._record_violation(ip_address)
                return hour_result
            
            day_result = await self.rate_limiter.check_rate_limit(
                ip_address, "day", self.rate_limiter.config.requests_per_day
            )
            
            if not day_result.allowed:
                await self._record_violation(ip_address)
                return day_result
            
            # Return the most restrictive result
            if not day_result.allowed:
                return day_result
            elif not hour_result.allowed:
                return hour_result
            else:
                return minute_result
                
        except Exception as e:
            logger.error(f"Error checking IP rate limit: {e}")
            return RateLimitResult(False, 0, 0)
    
    async def _record_violation(self, ip_address: str):
        """
        Record rate limit violation for IP
        
        Args:
            ip_address: IP address
        """
        try:
            violation_key = f"rate_limit_violations:{ip_address}"
            
            if self.rate_limiter.redis_client:
                # Use Redis to track violations
                violations = await self.rate_limiter.redis_client.incr(violation_key)
                await self.rate_limiter.redis_client.expire(violation_key, 3600)  # 1 hour
                
                if violations >= self.max_violations:
                    await self._block_ip(ip_address)
            else:
                # Use local tracking
                if ip_address not in self.blocked_until:
                    self.blocked_until[ip_address] = time.time() + self.block_duration
                    self.blocked_ips.add(ip_address)
                    
        except Exception as e:
            logger.error(f"Error recording violation: {e}")
    
    async def _block_ip(self, ip_address: str):
        """
        Block IP address
        
        Args:
            ip_address: IP address
        """
        try:
            self.blocked_ips.add(ip_address)
            self.blocked_until[ip_address] = time.time() + self.block_duration
            
            logger.warning(f"Blocked IP address due to rate limit violations: {ip_address}")
            
        except Exception as e:
            logger.error(f"Error blocking IP: {e}")
    
    async def unblock_ip(self, ip_address: str):
        """
        Unblock IP address
        
        Args:
            ip_address: IP address
        """
        try:
            self.blocked_ips.discard(ip_address)
            if ip_address in self.blocked_until:
                del self.blocked_until[ip_address]
            
            # Reset rate limits
            await self.rate_limiter.reset_rate_limit(ip_address, "minute")
            await self.rate_limiter.reset_rate_limit(ip_address, "hour")
            await self.rate_limiter.reset_rate_limit(ip_address, "day")
            
            logger.info(f"Unblocked IP address: {ip_address}")
            
        except Exception as e:
            logger.error(f"Error unblocking IP: {e}")

class UserRateLimiter:
    """
    User-based rate limiter
    """
    
    def __init__(self, config: RateLimitConfig):
        """
        Initialize user rate limiter
        
        Args:
            config: Rate limit configuration
        """
        self.rate_limiter = RateLimiter(config)
    
    async def initialize(self):
        """Initialize user rate limiter"""
        await self.rate_limiter.initialize()
    
    async def check_user_rate_limit(self, user_id: str, action: str = "general") -> RateLimitResult:
        """
        Check rate limit for user
        
        Args:
            user_id: User ID
            action: Action type (general, login, api, etc.)
            
        Returns:
            Rate limit result
        """
        try:
            identifier = f"{user_id}:{action}"
            
            # Different limits for different actions
            if action == "login":
                limit = 5  # 5 login attempts per minute
                window = "minute"
            elif action == "api":
                limit = self.rate_limiter.config.requests_per_minute
                window = "minute"
            else:
                limit = self.rate_limiter.config.requests_per_minute
                window = "minute"
            
            return await self.rate_limiter.check_rate_limit(identifier, window, limit)
            
        except Exception as e:
            logger.error(f"Error checking user rate limit: {e}")
            return RateLimitResult(False, 0, 0)
    
    async def reset_user_rate_limit(self, user_id: str, action: str = "general"):
        """
        Reset rate limit for user
        
        Args:
            user_id: User ID
            action: Action type
        """
        try:
            identifier = f"{user_id}:{action}"
            await self.rate_limiter.reset_rate_limit(identifier, "minute")
            
        except Exception as e:
            logger.error(f"Error resetting user rate limit: {e}")

class EndpointRateLimiter:
    """
    Endpoint-specific rate limiter
    """
    
    def __init__(self):
        """
        Initialize endpoint rate limiter
        """
        self.endpoint_configs = {
            "/api/auth/login": RateLimitConfig(requests_per_minute=5, requests_per_hour=20),
            "/api/auth/register": RateLimitConfig(requests_per_minute=3, requests_per_hour=10),
            "/api/admin": RateLimitConfig(requests_per_minute=30, requests_per_hour=500),
            "/api/victims": RateLimitConfig(requests_per_minute=60, requests_per_hour=1000),
            "/api/campaigns": RateLimitConfig(requests_per_minute=30, requests_per_hour=500),
            "/api/gmail": RateLimitConfig(requests_per_minute=10, requests_per_hour=100),
            "/api/beef": RateLimitConfig(requests_per_minute=20, requests_per_hour=200),
            "/ws": RateLimitConfig(requests_per_minute=100, requests_per_hour=2000),
        }
        self.rate_limiters = {}
    
    async def initialize(self):
        """Initialize endpoint rate limiters"""
        for endpoint, config in self.endpoint_configs.items():
            self.rate_limiters[endpoint] = RateLimiter(config)
            await self.rate_limiters[endpoint].initialize()
    
    async def check_endpoint_rate_limit(self, endpoint: str, identifier: str) -> RateLimitResult:
        """
        Check rate limit for endpoint
        
        Args:
            endpoint: API endpoint
            identifier: Unique identifier (IP, user ID, etc.)
            
        Returns:
            Rate limit result
        """
        try:
            # Find matching endpoint config
            config = None
            for pattern, endpoint_config in self.endpoint_configs.items():
                if endpoint.startswith(pattern):
                    config = endpoint_config
                    break
            
            if not config:
                # Use default config
                config = RateLimitConfig()
                if endpoint not in self.rate_limiters:
                    self.rate_limiters[endpoint] = RateLimiter(config)
                    await self.rate_limiters[endpoint].initialize()
            
            rate_limiter = self.rate_limiters.get(endpoint, self.rate_limiters.get("/api/admin"))
            
            return await rate_limiter.check_rate_limit(
                identifier, "minute", config.requests_per_minute
            )
            
        except Exception as e:
            logger.error(f"Error checking endpoint rate limit: {e}")
            return RateLimitResult(False, 0, 0)

# Global rate limiter instances
ip_rate_limiter: Optional[IPRateLimiter] = None
user_rate_limiter: Optional[UserRateLimiter] = None
endpoint_rate_limiter: Optional[EndpointRateLimiter] = None

async def initialize_rate_limiters():
    """Initialize all rate limiters"""
    global ip_rate_limiter, user_rate_limiter, endpoint_rate_limiter
    
    try:
        # Initialize IP rate limiter
        ip_config = RateLimitConfig(
            requests_per_minute=60,
            requests_per_hour=1000,
            requests_per_day=10000
        )
        ip_rate_limiter = IPRateLimiter(ip_config)
        await ip_rate_limiter.initialize()
        
        # Initialize user rate limiter
        user_config = RateLimitConfig(
            requests_per_minute=100,
            requests_per_hour=2000,
            requests_per_day=50000
        )
        user_rate_limiter = UserRateLimiter(user_config)
        await user_rate_limiter.initialize()
        
        # Initialize endpoint rate limiter
        endpoint_rate_limiter = EndpointRateLimiter()
        await endpoint_rate_limiter.initialize()
        
        logger.info("All rate limiters initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing rate limiters: {e}")

async def check_rate_limit(ip_address: str, user_id: Optional[str] = None, endpoint: str = "/") -> RateLimitResult:
    """
    Check rate limit for request
    
    Args:
        ip_address: IP address
        user_id: User ID (optional)
        endpoint: API endpoint
        
    Returns:
        Rate limit result
    """
    try:
        # Check IP rate limit first
        ip_result = await ip_rate_limiter.check_ip_rate_limit(ip_address)
        if not ip_result.allowed:
            return ip_result
        
        # Check endpoint rate limit
        endpoint_result = await endpoint_rate_limiter.check_endpoint_rate_limit(endpoint, ip_address)
        if not endpoint_result.allowed:
            return endpoint_result
        
        # Check user rate limit if user_id provided
        if user_id:
            user_result = await user_rate_limiter.check_user_rate_limit(user_id, "api")
            if not user_result.allowed:
                return user_result
        
        # Return the most restrictive result
        if not endpoint_result.allowed:
            return endpoint_result
        elif user_id and not user_result.allowed:
            return user_result
        else:
            return ip_result
            
    except Exception as e:
        logger.error(f"Error checking rate limit: {e}")
        return RateLimitResult(False, 0, 0)

async def reset_rate_limit(ip_address: str, user_id: Optional[str] = None):
    """
    Reset rate limit for identifier
    
    Args:
        ip_address: IP address
        user_id: User ID (optional)
    """
    try:
        if ip_rate_limiter:
            await ip_rate_limiter.rate_limiter.reset_rate_limit(ip_address, "minute")
            await ip_rate_limiter.rate_limiter.reset_rate_limit(ip_address, "hour")
            await ip_rate_limiter.rate_limiter.reset_rate_limit(ip_address, "day")
        
        if user_id and user_rate_limiter:
            await user_rate_limiter.reset_user_rate_limit(user_id, "api")
            
    except Exception as e:
        logger.error(f"Error resetting rate limit: {e}")
