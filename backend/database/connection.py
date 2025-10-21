"""
Database Connection Manager
Centralized connection management for MongoDB, Redis, and InfluxDB
"""

import os
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
import logging
import threading
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectionStatus(Enum):
    """Connection status enumeration"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"

@dataclass
class ConnectionInfo:
    """Connection information dataclass"""
    name: str
    status: ConnectionStatus
    last_connected: Optional[datetime] = None
    last_error: Optional[str] = None
    connection_count: int = 0
    error_count: int = 0

class DatabaseConnectionManager:
    """Centralized database connection management"""

    def __init__(self):
        self.connections: Dict[str, Any] = {}
        self.connection_info: Dict[str, ConnectionInfo] = {}
        self.lock = threading.Lock()

        # Connection pool settings
        self.max_connection_attempts = 3
        self.connection_timeout = 30
        self.health_check_interval = 60  # seconds

        # Initialize connection tracking
        self._initialize_connection_tracking()

        # Start health check thread
        self.health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self.health_check_thread.start()

    def _initialize_connection_tracking(self):
        """Initialize connection tracking for all databases"""
        databases = ["mongodb", "redis", "influxdb"]
        for db_name in databases:
            self.connection_info[db_name] = ConnectionInfo(
                name=db_name,
                status=ConnectionStatus.DISCONNECTED
            )

    def _health_check_loop(self):
        """Background health check loop"""
        while True:
            try:
                time.sleep(self.health_check_interval)
                self.perform_health_checks()
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")

    def perform_health_checks(self) -> Dict[str, Dict[str, Any]]:
        """Perform health checks on all connections"""
        results = {}

        for db_name in ["mongodb", "redis", "influxdb"]:
            try:
                if db_name == "mongodb":
                    result = self._check_mongodb_health()
                elif db_name == "redis":
                    result = self._check_redis_health()
                elif db_name == "influxdb":
                    result = self._check_influxdb_health()
                else:
                    result = {"healthy": False, "error": "Unknown database"}

                results[db_name] = result

                # Update connection info
                with self.lock:
                    conn_info = self.connection_info[db_name]
                    conn_info.last_error = result.get("error")
                    if result.get("healthy"):
                        conn_info.status = ConnectionStatus.CONNECTED
                        conn_info.last_connected = datetime.now(timezone.utc)
                    else:
                        conn_info.status = ConnectionStatus.ERROR

            except Exception as e:
                logger.error(f"Error checking {db_name} health: {e}")
                results[db_name] = {"healthy": False, "error": str(e)}

        return results

    def _check_mongodb_health(self) -> Dict[str, Any]:
        """Check MongoDB connection health"""
        try:
            if "mongodb" not in self.connections:
                return {"healthy": False, "error": "MongoDB not connected"}

            client = self.connections["mongodb"]
            # Ping the server
            ping_result = client.admin.command('ping')

            if ping_result.get('ok') == 1:
                return {"healthy": True, "response_time_ms": 100}
            else:
                return {"healthy": False, "error": "Ping failed"}

        except Exception as e:
            return {"healthy": False, "error": str(e)}

    def _check_redis_health(self) -> Dict[str, Any]:
        """Check Redis connection health"""
        try:
            if "redis" not in self.connections:
                return {"healthy": False, "error": "Redis not connected"}

            redis_client = self.connections["redis"]
            start_time = time.time()

            # Test ping
            redis_client.ping()

            response_time = (time.time() - start_time) * 1000
            return {"healthy": True, "response_time_ms": response_time}

        except Exception as e:
            return {"healthy": False, "error": str(e)}

    def _check_influxdb_health(self) -> Dict[str, Any]:
        """Check InfluxDB connection health"""
        try:
            if "influxdb" not in self.connections:
                return {"healthy": False, "error": "InfluxDB not connected"}

            influx_client = self.connections["influxdb"]
            start_time = time.time()

            # Check health
            health = influx_client.client.health()

            response_time = (time.time() - start_time) * 1000

            if health.status == "pass":
                return {"healthy": True, "response_time_ms": response_time}
            else:
                return {"healthy": False, "error": f"Health check failed: {health.status}"}

        except Exception as e:
            return {"healthy": False, "error": str(e)}

    def connect_mongodb(self, connection_string: str = None, database_name: str = "zalopay_phishing") -> bool:
        """Connect to MongoDB"""
        try:
            from pymongo import MongoClient

            conn_str = connection_string or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
            db_name = database_name or os.getenv("MONGODB_DATABASE", "zalopay_phishing")

            # Update status
            with self.lock:
                self.connection_info["mongodb"].status = ConnectionStatus.CONNECTING

            # Create connection
            client = MongoClient(
                conn_str,
                serverSelectionTimeoutMS=5000,
                maxPoolSize=10,
                minPoolSize=2
            )

            # Test connection
            client.admin.command('ping')

            # Store connection
            self.connections["mongodb"] = client

            # Update connection info
            with self.lock:
                conn_info = self.connection_info["mongodb"]
                conn_info.status = ConnectionStatus.CONNECTED
                conn_info.last_connected = datetime.now(timezone.utc)
                conn_info.connection_count += 1

            logger.info(f"MongoDB connected: {db_name}")
            return True

        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")

            with self.lock:
                conn_info = self.connection_info["mongodb"]
                conn_info.status = ConnectionStatus.ERROR
                conn_info.last_error = str(e)
                conn_info.error_count += 1

            return False

    def connect_redis(self, host: str = None, port: int = None, db: int = None, password: str = None) -> bool:
        """Connect to Redis"""
        try:
            import redis

            redis_host = host or os.getenv("REDIS_HOST", "localhost")
            redis_port = port or int(os.getenv("REDIS_PORT", "6379"))
            redis_db = db or int(os.getenv("REDIS_DB", "0"))
            redis_password = password or os.getenv("REDIS_PASSWORD")

            # Update status
            with self.lock:
                self.connection_info["redis"].status = ConnectionStatus.CONNECTING

            # Create connection pool
            connection_pool = redis.ConnectionPool(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                max_connections=20,
                retry_on_timeout=True,
                socket_timeout=5
            )

            # Create client
            client = redis.Redis(connection_pool=connection_pool)

            # Test connection
            client.ping()

            # Store connection
            self.connections["redis"] = client

            # Update connection info
            with self.lock:
                conn_info = self.connection_info["redis"]
                conn_info.status = ConnectionStatus.CONNECTED
                conn_info.last_connected = datetime.now(timezone.utc)
                conn_info.connection_count += 1

            logger.info(f"Redis connected: {redis_host}:{redis_port}/{redis_db}")
            return True

        except Exception as e:
            logger.error(f"Redis connection failed: {e}")

            with self.lock:
                conn_info = self.connection_info["redis"]
                conn_info.status = ConnectionStatus.ERROR
                conn_info.last_error = str(e)
                conn_info.error_count += 1

            return False

    def connect_influxdb(self, url: str = None, token: str = None, org: str = None, bucket: str = None) -> bool:
        """Connect to InfluxDB"""
        try:
            from influxdb_client import InfluxDBClient

            influx_url = url or os.getenv("INFLUXDB_URL", "http://localhost:8086")
            influx_token = token or os.getenv("INFLUXDB_TOKEN")
            influx_org = org or os.getenv("INFLUXDB_ORG", "zalopay")
            influx_bucket = bucket or os.getenv("INFLUXDB_BUCKET", "zalopay_metrics")

            # Update status
            with self.lock:
                self.connection_info["influxdb"].status = ConnectionStatus.CONNECTING

            # Create client
            client = InfluxDBClient(
                url=influx_url,
                token=influx_token,
                org=influx_org,
                timeout=30000
            )

            # Test connection
            health = client.health()
            if health.status != "pass":
                raise Exception(f"InfluxDB health check failed: {health}")

            # Store connection
            self.connections["influxdb"] = client

            # Update connection info
            with self.lock:
                conn_info = self.connection_info["influxdb"]
                conn_info.status = ConnectionStatus.CONNECTED
                conn_info.last_connected = datetime.now(timezone.utc)
                conn_info.connection_count += 1

            logger.info(f"InfluxDB connected: {influx_org}/{influx_bucket}")
            return True

        except Exception as e:
            logger.error(f"InfluxDB connection failed: {e}")

            with self.lock:
                conn_info = self.connection_info["influxdb"]
                conn_info.status = ConnectionStatus.ERROR
                conn_info.last_error = str(e)
                conn_info.error_count += 1

            return False

    def connect_all(self) -> Dict[str, bool]:
        """Connect to all databases"""
        results = {}

        # Connect to MongoDB
        results["mongodb"] = self.connect_mongodb()

        # Connect to Redis
        results["redis"] = self.connect_redis()

        # Connect to InfluxDB
        results["influxdb"] = self.connect_influxdb()

        return results

    def disconnect_all(self) -> Dict[str, bool]:
        """Disconnect from all databases"""
        results = {}

        for db_name in ["mongodb", "redis", "influxdb"]:
            try:
                if db_name in self.connections:
                    client = self.connections[db_name]

                    if db_name == "mongodb":
                        client.close()
                    elif db_name == "redis":
                        client.connection_pool.disconnect()
                    elif db_name == "influxdb":
                        client.close()

                    del self.connections[db_name]

                # Update connection info
                with self.lock:
                    self.connection_info[db_name].status = ConnectionStatus.DISCONNECTED

                results[db_name] = True
                logger.info(f"{db_name} disconnected")

            except Exception as e:
                logger.error(f"Error disconnecting {db_name}: {e}")
                results[db_name] = False

        return results

    def get_connection(self, db_name: str) -> Any:
        """Get database connection"""
        if db_name not in self.connections:
            raise ValueError(f"No connection found for {db_name}")

        return self.connections[db_name]

    def get_connection_info(self) -> Dict[str, Dict[str, Any]]:
        """Get connection information for all databases"""
        with self.lock:
            return {
                name: {
                    "name": info.name,
                    "status": info.status.value,
                    "last_connected": info.last_connected.isoformat() if info.last_connected else None,
                    "last_error": info.last_error,
                    "connection_count": info.connection_count,
                    "error_count": info.error_count
                }
                for name, info in self.connection_info.items()
            }

    def is_healthy(self) -> bool:
        """Check if all connections are healthy"""
        health_results = self.perform_health_checks()
        return all(result.get("healthy", False) for result in health_results.values())

    def reconnect(self, db_name: str) -> bool:
        """Reconnect to specific database"""
        try:
            # Disconnect first
            if db_name in self.connections:
                if db_name == "mongodb":
                    self.connections[db_name].close()
                elif db_name == "redis":
                    self.connections[db_name].connection_pool.disconnect()
                elif db_name == "influxdb":
                    self.connections[db_name].close()

            # Update status
            with self.lock:
                self.connection_info[db_name].status = ConnectionStatus.RECONNECTING

            # Reconnect
            if db_name == "mongodb":
                return self.connect_mongodb()
            elif db_name == "redis":
                return self.connect_redis()
            elif db_name == "influxdb":
                return self.connect_influxdb()
            else:
                return False

        except Exception as e:
            logger.error(f"Error reconnecting to {db_name}: {e}")
            return False

    def reconnect_all(self) -> Dict[str, bool]:
        """Reconnect to all databases"""
        results = {}

        for db_name in ["mongodb", "redis", "influxdb"]:
            results[db_name] = self.reconnect(db_name)

        return results

    @contextmanager
    def get_mongodb_connection(self):
        """Context manager for MongoDB connection"""
        try:
            yield self.get_connection("mongodb")
        except Exception as e:
            logger.error(f"Error in MongoDB context: {e}")
            raise

    @contextmanager
    def get_redis_connection(self):
        """Context manager for Redis connection"""
        try:
            yield self.get_connection("redis")
        except Exception as e:
            logger.error(f"Error in Redis context: {e}")
            raise

    @contextmanager
    def get_influxdb_connection(self):
        """Context manager for InfluxDB connection"""
        try:
            yield self.get_connection("influxdb")
        except Exception as e:
            logger.error(f"Error in InfluxDB context: {e}")
            raise

    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        stats = {
            "connections": self.get_connection_info(),
            "health": self.perform_health_checks(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Add database-specific stats if connected
        try:
            if "mongodb" in self.connections:
                mongodb = self.connections["mongodb"]
                db = mongodb.get_database()
                stats["mongodb"] = {
                    "database_name": db.name,
                    "collections": db.list_collection_names(),
                    "server_info": mongodb.server_info()
                }
        except Exception as e:
            stats["mongodb"] = {"error": str(e)}

        try:
            if "redis" in self.connections:
                redis_client = self.connections["redis"]
                info = redis_client.info()
                stats["redis"] = {
                    "memory_used": info.get("used_memory_human", "unknown"),
                    "connected_clients": info.get("connected_clients", 0),
                    "uptime_days": info.get("uptime_in_days", 0)
                }
        except Exception as e:
            stats["redis"] = {"error": str(e)}

        try:
            if "influxdb" in self.connections:
                influx_client = self.connections["influxdb"]
                health = influx_client.health()
                stats["influxdb"] = {
                    "status": health.status if hasattr(health, 'status') else "unknown",
                    "version": health.version if hasattr(health, 'version') else "unknown"
                }
        except Exception as e:
            stats["influxdb"] = {"error": str(e)}

        return stats

class ConnectionPool:
    """Connection pool for managing multiple database connections"""

    def __init__(self):
        self.manager = DatabaseConnectionManager()

    def initialize(self) -> bool:
        """Initialize all database connections"""
        try:
            results = self.manager.connect_all()

            if all(results.values()):
                logger.info("All database connections initialized successfully")
                return True
            else:
                logger.warning("Some database connections failed to initialize")
                for db_name, success in results.items():
                    if not success:
                        logger.error(f"Failed to connect to {db_name}")
                return False

        except Exception as e:
            logger.error(f"Error initializing database connections: {e}")
            return False

    def get_mongodb(self):
        """Get MongoDB connection"""
        return self.manager.get_connection("mongodb")

    def get_redis(self):
        """Get Redis connection"""
        return self.manager.get_connection("redis")

    def get_influxdb(self):
        """Get InfluxDB connection"""
        return self.manager.get_connection("influxdb")

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all connections"""
        return self.manager.perform_health_checks()

    def close_all(self):
        """Close all connections"""
        return self.manager.disconnect_all()

# Global connection pool instance
connection_pool = ConnectionPool()

def initialize_databases() -> bool:
    """Initialize all databases (convenience function)"""
    return connection_pool.initialize()

def get_database_connection(db_name: str):
    """Get database connection (convenience function)"""
    if db_name == "mongodb":
        return connection_pool.get_mongodb()
    elif db_name == "redis":
        return connection_pool.get_redis()
    elif db_name == "influxdb":
        return connection_pool.get_influxdb()
    else:
        raise ValueError(f"Unknown database: {db_name}")

@contextmanager
def mongodb_connection():
    """Context manager for MongoDB connection"""
    with connection_pool.manager.get_mongodb_connection() as conn:
        yield conn

@contextmanager
def redis_connection():
    """Context manager for Redis connection"""
    with connection_pool.manager.get_redis_connection() as conn:
        yield conn

@contextmanager
def influxdb_connection():
    """Context manager for InfluxDB connection"""
    with connection_pool.manager.get_influxdb_connection() as conn:
        yield conn