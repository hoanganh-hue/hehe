"""
Circuit Breaker Pattern Implementation
Provides fault tolerance for external API calls
"""

import asyncio
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Callable, Awaitable
from enum import Enum
import json

logger = logging.getLogger(__name__)

class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreakerConfig:
    """Circuit breaker configuration"""

    def __init__(self,
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: tuple = (Exception,),
                 success_threshold: int = 3):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.success_threshold = success_threshold

class CircuitBreakerStats:
    """Circuit breaker statistics"""

    def __init__(self):
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_success_time = None
        self.total_requests = 0
        self.total_failures = 0
        self.total_successes = 0
        self.state_changes = []

    def record_success(self):
        """Record successful request"""
        self.success_count += 1
        self.total_successes += 1
        self.total_requests += 1
        self.last_success_time = datetime.now(timezone.utc)

    def record_failure(self):
        """Record failed request"""
        self.failure_count += 1
        self.total_failures += 1
        self.total_requests += 1
        self.last_failure_time = datetime.now(timezone.utc)

    def reset(self):
        """Reset counters"""
        self.failure_count = 0
        self.success_count = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_requests": self.total_requests,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            "state_changes_count": len(self.state_changes)
        }

class CircuitBreaker:
    """Circuit breaker implementation"""

    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitBreakerState.CLOSED
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()

        logger.info(f"Circuit breaker '{name}' initialized")

    async def call(self, func: Callable[..., Awaitable], *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit breaker is open or function fails
        """
        async with self._lock:
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    await self._transition_to_half_open()
                else:
                    raise CircuitBreakerOpenException(
                        f"Circuit breaker '{self.name}' is OPEN"
                    )

        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result

        except self.config.expected_exception as e:
            await self._on_failure()
            raise e

    async def _on_success(self):
        """Handle successful execution"""
        async with self._lock:
            self.stats.record_success()

            if self.state == CircuitBreakerState.HALF_OPEN:
                if self.stats.success_count >= self.config.success_threshold:
                    await self._transition_to_closed()

    async def _on_failure(self):
        """Handle failed execution"""
        async with self._lock:
            self.stats.record_failure()

            if self.state == CircuitBreakerState.CLOSED:
                if self.stats.failure_count >= self.config.failure_threshold:
                    await self._transition_to_open()
            elif self.state == CircuitBreakerState.HALF_OPEN:
                await self._transition_to_open()

    async def _transition_to_open(self):
        """Transition to OPEN state"""
        if self.state != CircuitBreakerState.OPEN:
            self.state = CircuitBreakerState.OPEN
            self.stats.state_changes.append({
                "from": "closed" if self.state != CircuitBreakerState.HALF_OPEN else "half_open",
                "to": "open",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            logger.warning(f"Circuit breaker '{self.name}' transitioned to OPEN state")

    async def _transition_to_half_open(self):
        """Transition to HALF_OPEN state"""
        if self.state == CircuitBreakerState.OPEN:
            self.state = CircuitBreakerState.HALF_OPEN
            self.stats.reset()
            self.stats.state_changes.append({
                "from": "open",
                "to": "half_open",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            logger.info(f"Circuit breaker '{self.name}' transitioned to HALF_OPEN state")

    async def _transition_to_closed(self):
        """Transition to CLOSED state"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED
            self.stats.reset()
            self.stats.state_changes.append({
                "from": "half_open",
                "to": "closed",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            logger.info(f"Circuit breaker '{self.name}' transitioned to CLOSED state")

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if not self.stats.last_failure_time:
            return True

        time_since_failure = datetime.now(timezone.utc) - self.stats.last_failure_time
        return time_since_failure.total_seconds() >= self.config.recovery_timeout

    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state"""
        return {
            "name": self.name,
            "state": self.state.value,
            "stats": self.stats.to_dict(),
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold
            }
        }

class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open"""
    pass

class CircuitBreakerManager:
    """Manages multiple circuit breakers"""

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()

    def get_circuit_breaker(self, name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
        """Get or create circuit breaker"""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name, config)
        return self.circuit_breakers[name]

    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get states of all circuit breakers"""
        return {
            name: cb.get_state()
            for name, cb in self.circuit_breakers.items()
        }

    async def reset_all(self):
        """Reset all circuit breakers"""
        async with self._lock:
            for cb in self.circuit_breakers.values():
                cb.state = CircuitBreakerState.CLOSED
                cb.stats.reset()
            logger.info("All circuit breakers reset")

# Global circuit breaker manager
circuit_breaker_manager = CircuitBreakerManager()

def get_circuit_breaker(name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
    """Get circuit breaker instance"""
    return circuit_breaker_manager.get_circuit_breaker(name, config)

async def call_with_circuit_breaker(name: str, func: Callable[..., Awaitable],
                                   config: CircuitBreakerConfig = None,
                                   *args, **kwargs) -> Any:
    """
    Call function with circuit breaker protection

    Args:
        name: Circuit breaker name
        func: Function to call
        config: Circuit breaker configuration
        *args: Function arguments
        **kwargs: Function keyword arguments

    Returns:
        Function result
    """
    cb = get_circuit_breaker(name, config)
    return await cb.call(func, *args, **kwargs)

# Pre-configured circuit breakers for common APIs
def get_gmail_circuit_breaker() -> CircuitBreaker:
    """Get Gmail API circuit breaker"""
    config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=30,
        expected_exception=(Exception,)
    )
    return get_circuit_breaker("gmail_api", config)

def get_clearbit_circuit_breaker() -> CircuitBreaker:
    """Get Clearbit API circuit breaker"""
    config = CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=60,
        expected_exception=(Exception,)
    )
    return get_circuit_breaker("clearbit_api", config)

def get_hunter_circuit_breaker() -> CircuitBreaker:
    """Get Hunter.io API circuit breaker"""
    config = CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=60,
        expected_exception=(Exception,)
    )
    return get_circuit_breaker("hunter_api", config)

def get_facebook_circuit_breaker() -> CircuitBreaker:
    """Get Facebook API circuit breaker"""
    config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=30,
        expected_exception=(Exception,)
    )
    return get_circuit_breaker("facebook_api", config)

def get_apple_circuit_breaker() -> CircuitBreaker:
    """Get Apple API circuit breaker"""
    config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=30,
        expected_exception=(Exception,)
    )
    return get_circuit_breaker("apple_api", config)

def get_google_oauth_circuit_breaker() -> CircuitBreaker:
    """Get Google OAuth circuit breaker"""
    config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=30,
        expected_exception=(Exception,)
    )
    return get_circuit_breaker("google_oauth", config)