"""
Advanced Proxy Health Monitor
Comprehensive health monitoring, failover, and performance tracking
"""

import os
import json
import time
import asyncio
import socket
import struct
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple, Set
import logging
import statistics
from collections import defaultdict, deque
import requests
import concurrent.futures

from api.capture.proxy_manager import ProxyManager, ProxyInfo, ProxyPool

logger = logging.getLogger(__name__)

class HealthCheckResult:
    """Health check result container"""
    
    def __init__(self, proxy_id: str, is_healthy: bool, response_time: int = None,
                 error_message: str = None, check_type: str = "basic"):
        self.proxy_id = proxy_id
        self.is_healthy = is_healthy
        self.response_time = response_time
        self.error_message = error_message
        self.check_type = check_type
        self.timestamp = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "proxy_id": self.proxy_id,
            "is_healthy": self.is_healthy,
            "response_time": self.response_time,
            "error_message": self.error_message,
            "check_type": self.check_type,
            "timestamp": self.timestamp.isoformat()
        }

class ProxyPerformanceMetrics:
    """Proxy performance metrics tracking"""
    
    def __init__(self, proxy_id: str):
        self.proxy_id = proxy_id
        self.response_times = deque(maxlen=100)  # Keep last 100 response times
        self.success_count = 0
        self.failure_count = 0
        self.last_check_time = None
        self.uptime_percentage = 100.0
        self.avg_response_time = 0.0
        self.min_response_time = None
        self.max_response_time = None
        
        # Health check history
        self.health_history = deque(maxlen=50)  # Keep last 50 health checks
        
        # Performance trends
        self.performance_trend = "stable"  # improving, stable, degrading
        self.trend_score = 0.0
    
    def add_health_check(self, result: HealthCheckResult):
        """Add health check result"""
        self.health_history.append(result)
        self.last_check_time = result.timestamp
        
        if result.is_healthy:
            self.success_count += 1
            if result.response_time:
                self.response_times.append(result.response_time)
                self._update_response_time_stats()
        else:
            self.failure_count += 1
        
        self._update_uptime_percentage()
        self._update_performance_trend()
    
    def _update_response_time_stats(self):
        """Update response time statistics"""
        if not self.response_times:
            return
        
        self.avg_response_time = statistics.mean(self.response_times)
        self.min_response_time = min(self.response_times)
        self.max_response_time = max(self.response_times)
    
    def _update_uptime_percentage(self):
        """Update uptime percentage"""
        total_checks = self.success_count + self.failure_count
        if total_checks > 0:
            self.uptime_percentage = (self.success_count / total_checks) * 100
    
    def _update_performance_trend(self):
        """Update performance trend analysis"""
        if len(self.response_times) < 10:
            return
        
        # Compare recent vs older response times
        recent_times = list(self.response_times)[-10:]
        older_times = list(self.response_times)[-20:-10] if len(self.response_times) >= 20 else []
        
        if older_times:
            recent_avg = statistics.mean(recent_times)
            older_avg = statistics.mean(older_times)
            
            improvement = (older_avg - recent_avg) / older_avg
            
            if improvement > 0.1:  # 10% improvement
                self.performance_trend = "improving"
                self.trend_score = improvement
            elif improvement < -0.1:  # 10% degradation
                self.performance_trend = "degrading"
                self.trend_score = abs(improvement)
            else:
                self.performance_trend = "stable"
                self.trend_score = 0.0
    
    def get_health_score(self) -> float:
        """Calculate overall health score (0-100)"""
        score = 0.0
        
        # Uptime component (40%)
        score += (self.uptime_percentage / 100) * 40
        
        # Response time component (30%)
        if self.avg_response_time > 0:
            # Lower response time = higher score
            response_score = max(0, 30 - (self.avg_response_time / 1000) * 10)
            score += response_score
        
        # Trend component (20%)
        if self.performance_trend == "improving":
            score += 20
        elif self.performance_trend == "stable":
            score += 15
        else:  # degrading
            score += max(0, 10 - self.trend_score * 10)
        
        # Consistency component (10%)
        if len(self.response_times) > 5:
            consistency = 1 - (statistics.stdev(self.response_times) / self.avg_response_time)
            score += max(0, consistency * 10)
        
        return min(100.0, max(0.0, score))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "proxy_id": self.proxy_id,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "uptime_percentage": self.uptime_percentage,
            "avg_response_time": self.avg_response_time,
            "min_response_time": self.min_response_time,
            "max_response_time": self.max_response_time,
            "performance_trend": self.performance_trend,
            "trend_score": self.trend_score,
            "health_score": self.get_health_score(),
            "last_check_time": self.last_check_time.isoformat() if self.last_check_time else None,
            "total_checks": self.success_count + self.failure_count
        }

class ProxyHealthMonitor:
    """Advanced proxy health monitoring system"""
    
    def __init__(self, proxy_manager: ProxyManager, mongodb_connection=None, redis_client=None):
        self.proxy_manager = proxy_manager
        self.mongodb = mongodb_connection
        self.redis = redis_client
        
        # Configuration
        self.health_check_interval = int(os.getenv("HEALTH_CHECK_INTERVAL", "60"))  # seconds
        self.deep_check_interval = int(os.getenv("DEEP_CHECK_INTERVAL", "300"))  # 5 minutes
        self.health_check_timeout = int(os.getenv("HEALTH_CHECK_TIMEOUT", "10"))  # seconds
        self.max_concurrent_checks = int(os.getenv("MAX_CONCURRENT_CHECKS", "10"))
        
        # Performance tracking
        self.performance_metrics: Dict[str, ProxyPerformanceMetrics] = {}
        
        # Health check targets
        self.health_check_targets = [
            {"url": "http://httpbin.org/ip", "method": "GET"},
            {"url": "http://httpbin.org/user-agent", "method": "GET"},
            {"url": "https://www.google.com", "method": "GET"},
            {"url": "https://www.facebook.com", "method": "GET"}
        ]
        
        # Vietnamese-specific targets
        self.vietnamese_targets = [
            {"url": "https://zalopay.vn", "method": "GET"},
            {"url": "https://www.vietcombank.com.vn", "method": "GET"},
            {"url": "https://www.vietinbank.com.vn", "method": "GET"}
        ]
        
        # Monitoring state
        self.monitoring_active = False
        self.monitor_thread = None
        self.deep_check_thread = None
        
        # Alert thresholds
        self.alert_thresholds = {
            "uptime_percentage": 80.0,
            "avg_response_time": 5000,  # 5 seconds
            "health_score": 60.0,
            "consecutive_failures": 3
        }
        
        # Initialize performance metrics for existing proxies
        self._initialize_performance_metrics()
        
        # Start monitoring
        self.start_monitoring()
    
    def _initialize_performance_metrics(self):
        """Initialize performance metrics for existing proxies"""
        try:
            for proxy_id, proxy in self.proxy_manager.proxy_pool.proxies.items():
                if proxy_id not in self.performance_metrics:
                    self.performance_metrics[proxy_id] = ProxyPerformanceMetrics(proxy_id)
            
            logger.info(f"Initialized performance metrics for {len(self.performance_metrics)} proxies")
            
        except Exception as e:
            logger.error(f"Error initializing performance metrics: {e}")
    
    def start_monitoring(self):
        """Start health monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        # Start basic health check thread
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        # Start deep health check thread
        self.deep_check_thread = threading.Thread(target=self._deep_check_loop, daemon=True)
        self.deep_check_thread.start()
        
        logger.info("Proxy health monitoring started")
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        if self.deep_check_thread:
            self.deep_check_thread.join(timeout=5)
        
        logger.info("Proxy health monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Perform health checks on all proxies
                self.perform_health_checks()
                
                # Wait for next check
                time.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait before retrying
    
    def _deep_check_loop(self):
        """Deep health check loop"""
        while self.monitoring_active:
            try:
                # Perform deep health checks
                self.perform_deep_health_checks()
                
                # Wait for next deep check
                time.sleep(self.deep_check_interval)
                
            except Exception as e:
                logger.error(f"Error in deep check loop: {e}")
                time.sleep(300)  # Wait before retrying
    
    def perform_health_checks(self) -> Dict[str, HealthCheckResult]:
        """Perform health checks on all proxies"""
        try:
            results = {}
            proxies = list(self.proxy_manager.proxy_pool.proxies.items())
            
            # Use thread pool for concurrent checks
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent_checks) as executor:
                future_to_proxy = {
                    executor.submit(self._check_proxy_health, proxy_id, proxy): proxy_id
                    for proxy_id, proxy in proxies
                }
                
                for future in concurrent.futures.as_completed(future_to_proxy):
                    proxy_id = future_to_proxy[future]
                    try:
                        result = future.result()
                        results[proxy_id] = result
                        
                        # Update performance metrics
                        if proxy_id not in self.performance_metrics:
                            self.performance_metrics[proxy_id] = ProxyPerformanceMetrics(proxy_id)
                        
                        self.performance_metrics[proxy_id].add_health_check(result)
                        
                        # Update proxy status
                        proxy = self.proxy_manager.proxy_pool.get_proxy(proxy_id)
                        if proxy:
                            proxy.update_health_status(result.is_healthy, result.response_time)
                        
                    except Exception as e:
                        logger.error(f"Error checking proxy {proxy_id}: {e}")
                        results[proxy_id] = HealthCheckResult(
                            proxy_id, False, error_message=str(e)
                        )
            
            # Check for alerts
            self._check_alerts()
            
            # Store results
            self._store_health_check_results(results)
            
            logger.info(f"Completed health checks for {len(results)} proxies")
            return results
            
        except Exception as e:
            logger.error(f"Error performing health checks: {e}")
            return {}
    
    def perform_deep_health_checks(self) -> Dict[str, List[HealthCheckResult]]:
        """Perform deep health checks with multiple targets"""
        try:
            results = {}
            proxies = list(self.proxy_manager.proxy_pool.proxies.items())
            
            for proxy_id, proxy in proxies:
                if not proxy.is_active:
                    continue
                
                proxy_results = []
                
                # Test against multiple targets
                all_targets = self.health_check_targets + self.vietnamese_targets
                
                for target in all_targets[:5]:  # Limit to 5 targets for deep check
                    try:
                        result = self._check_proxy_against_target(proxy, target)
                        proxy_results.append(result)
                        
                        # Update performance metrics
                        if proxy_id not in self.performance_metrics:
                            self.performance_metrics[proxy_id] = ProxyPerformanceMetrics(proxy_id)
                        
                        self.performance_metrics[proxy_id].add_health_check(result)
                        
                    except Exception as e:
                        logger.error(f"Error in deep check for proxy {proxy_id}: {e}")
                        proxy_results.append(HealthCheckResult(
                            proxy_id, False, error_message=str(e), check_type="deep"
                        ))
                
                results[proxy_id] = proxy_results
            
            logger.info(f"Completed deep health checks for {len(results)} proxies")
            return results
            
        except Exception as e:
            logger.error(f"Error performing deep health checks: {e}")
            return {}
    
    def _check_proxy_health(self, proxy_id: str, proxy: ProxyInfo) -> HealthCheckResult:
        """Check individual proxy health"""
        try:
            start_time = time.time()
            
            # Basic SOCKS5 connectivity test
            is_healthy, response_time = self._test_socks5_connectivity(proxy)
            
            if is_healthy:
                response_time = int((time.time() - start_time) * 1000)
                return HealthCheckResult(proxy_id, True, response_time, check_type="basic")
            else:
                return HealthCheckResult(proxy_id, False, check_type="basic")
                
        except Exception as e:
            return HealthCheckResult(proxy_id, False, error_message=str(e), check_type="basic")
    
    def _check_proxy_against_target(self, proxy: ProxyInfo, target: Dict[str, str]) -> HealthCheckResult:
        """Check proxy against specific target"""
        try:
            start_time = time.time()
            
            # Test HTTP connectivity through proxy
            is_healthy, response_time = self._test_http_through_proxy(proxy, target)
            
            if is_healthy:
                response_time = int((time.time() - start_time) * 1000)
                return HealthCheckResult(
                    proxy.get_address(), True, response_time, 
                    check_type=f"target_{target['url']}"
                )
            else:
                return HealthCheckResult(
                    proxy.get_address(), False, 
                    check_type=f"target_{target['url']}"
                )
                
        except Exception as e:
            return HealthCheckResult(
                proxy.get_address(), False, 
                error_message=str(e), 
                check_type=f"target_{target['url']}"
            )
    
    def _test_socks5_connectivity(self, proxy: ProxyInfo) -> Tuple[bool, Optional[int]]:
        """Test SOCKS5 connectivity"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.health_check_timeout)
            
            # Connect to proxy
            sock.connect((proxy.host, proxy.port))
            
            # SOCKS5 handshake
            if not self._perform_socks5_handshake(sock, proxy):
                sock.close()
                return False, None
            
            sock.close()
            return True, None
            
        except Exception as e:
            logger.debug(f"SOCKS5 connectivity test failed for {proxy.get_address()}: {e}")
            return False, None
    
    def _test_http_through_proxy(self, proxy: ProxyInfo, target: Dict[str, str]) -> Tuple[bool, Optional[int]]:
        """Test HTTP connectivity through proxy"""
        try:
            # Configure proxy for requests
            proxy_config = {
                'http': f'socks5://{proxy.get_address()}',
                'https': f'socks5://{proxy.get_address()}'
            }
            
            if proxy.username and proxy.password:
                proxy_config = {
                    'http': f'socks5://{proxy.username}:{proxy.password}@{proxy.get_address()}',
                    'https': f'socks5://{proxy.username}:{proxy.password}@{proxy.get_address()}'
                }
            
            # Make request through proxy
            response = requests.get(
                target['url'],
                proxies=proxy_config,
                timeout=self.health_check_timeout,
                allow_redirects=True
            )
            
            # Check if request was successful
            if response.status_code == 200:
                return True, None
            else:
                return False, None
                
        except Exception as e:
            logger.debug(f"HTTP test failed for {proxy.get_address()}: {e}")
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
            logger.debug(f"SOCKS5 handshake failed: {e}")
            return False
    
    def _check_alerts(self):
        """Check for alert conditions"""
        try:
            alerts = []
            
            for proxy_id, metrics in self.performance_metrics.items():
                # Check uptime percentage
                if metrics.uptime_percentage < self.alert_thresholds["uptime_percentage"]:
                    alerts.append({
                        "type": "low_uptime",
                        "proxy_id": proxy_id,
                        "value": metrics.uptime_percentage,
                        "threshold": self.alert_thresholds["uptime_percentage"]
                    })
                
                # Check response time
                if metrics.avg_response_time > self.alert_thresholds["avg_response_time"]:
                    alerts.append({
                        "type": "high_response_time",
                        "proxy_id": proxy_id,
                        "value": metrics.avg_response_time,
                        "threshold": self.alert_thresholds["avg_response_time"]
                    })
                
                # Check health score
                health_score = metrics.get_health_score()
                if health_score < self.alert_thresholds["health_score"]:
                    alerts.append({
                        "type": "low_health_score",
                        "proxy_id": proxy_id,
                        "value": health_score,
                        "threshold": self.alert_thresholds["health_score"]
                    })
                
                # Check consecutive failures
                if metrics.failure_count >= self.alert_thresholds["consecutive_failures"]:
                    alerts.append({
                        "type": "consecutive_failures",
                        "proxy_id": proxy_id,
                        "value": metrics.failure_count,
                        "threshold": self.alert_thresholds["consecutive_failures"]
                    })
            
            # Process alerts
            if alerts:
                self._process_alerts(alerts)
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    def _process_alerts(self, alerts: List[Dict[str, Any]]):
        """Process and handle alerts"""
        try:
            for alert in alerts:
                logger.warning(f"Proxy Alert: {alert['type']} for {alert['proxy_id']} "
                             f"(value: {alert['value']}, threshold: {alert['threshold']})")
                
                # Store alert in database
                if self.mongodb:
                    self._store_alert(alert)
                
                # Store alert in Redis for real-time notifications
                if self.redis:
                    alert_key = f"proxy_alert:{alert['proxy_id']}:{alert['type']}"
                    self.redis.setex(alert_key, 3600, json.dumps(alert))
            
        except Exception as e:
            logger.error(f"Error processing alerts: {e}")
    
    def _store_alert(self, alert: Dict[str, Any]):
        """Store alert in MongoDB"""
        try:
            if not self.mongodb:
                return
            
            db = self.mongodb.get_database("zalopay_phishing")
            alerts_collection = db.proxy_alerts
            
            document = {
                "alert": alert,
                "created_at": datetime.now(timezone.utc),
                "status": "active"
            }
            
            alerts_collection.insert_one(document)
            
        except Exception as e:
            logger.error(f"Error storing alert: {e}")
    
    def _store_health_check_results(self, results: Dict[str, HealthCheckResult]):
        """Store health check results"""
        try:
            if not self.mongodb:
                return
            
            db = self.mongodb.get_database("zalopay_phishing")
            health_checks_collection = db.proxy_health_checks
            
            documents = []
            for proxy_id, result in results.items():
                document = {
                    "proxy_id": proxy_id,
                    "result": result.to_dict(),
                    "created_at": datetime.now(timezone.utc)
                }
                documents.append(document)
            
            if documents:
                health_checks_collection.insert_many(documents)
            
        except Exception as e:
            logger.error(f"Error storing health check results: {e}")
    
    def get_proxy_health_status(self, proxy_id: str) -> Optional[Dict[str, Any]]:
        """Get health status for specific proxy"""
        try:
            if proxy_id not in self.performance_metrics:
                return None
            
            metrics = self.performance_metrics[proxy_id]
            proxy = self.proxy_manager.proxy_pool.get_proxy(proxy_id)
            
            if not proxy:
                return None
            
            return {
                "proxy_info": proxy.to_dict(),
                "performance_metrics": metrics.to_dict(),
                "is_monitoring": self.monitoring_active,
                "last_check": metrics.last_check_time.isoformat() if metrics.last_check_time else None
            }
            
        except Exception as e:
            logger.error(f"Error getting proxy health status: {e}")
            return None
    
    def get_all_proxy_health_status(self) -> Dict[str, Dict[str, Any]]:
        """Get health status for all proxies"""
        try:
            status = {}
            
            for proxy_id in self.performance_metrics:
                proxy_status = self.get_proxy_health_status(proxy_id)
                if proxy_status:
                    status[proxy_id] = proxy_status
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting all proxy health status: {e}")
            return {}
    
    def get_health_monitor_stats(self) -> Dict[str, Any]:
        """Get health monitor statistics"""
        try:
            total_proxies = len(self.performance_metrics)
            healthy_proxies = sum(1 for metrics in self.performance_metrics.values() 
                                if metrics.get_health_score() > 70)
            
            avg_health_score = 0
            if total_proxies > 0:
                avg_health_score = sum(metrics.get_health_score() 
                                     for metrics in self.performance_metrics.values()) / total_proxies
            
            return {
                "total_proxies": total_proxies,
                "healthy_proxies": healthy_proxies,
                "unhealthy_proxies": total_proxies - healthy_proxies,
                "avg_health_score": avg_health_score,
                "monitoring_active": self.monitoring_active,
                "health_check_interval": self.health_check_interval,
                "deep_check_interval": self.deep_check_interval,
                "alert_thresholds": self.alert_thresholds,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting health monitor stats: {e}")
            return {}
    
    def set_alert_threshold(self, threshold_type: str, value: float):
        """Set alert threshold"""
        try:
            if threshold_type in self.alert_thresholds:
                self.alert_thresholds[threshold_type] = value
                logger.info(f"Alert threshold {threshold_type} set to {value}")
            else:
                logger.error(f"Invalid threshold type: {threshold_type}")
                
        except Exception as e:
            logger.error(f"Error setting alert threshold: {e}")
    
    def force_health_check(self, proxy_id: str = None) -> Dict[str, HealthCheckResult]:
        """Force immediate health check"""
        try:
            if proxy_id:
                proxy = self.proxy_manager.proxy_pool.get_proxy(proxy_id)
                if proxy:
                    result = self._check_proxy_health(proxy_id, proxy)
                    
                    # Update performance metrics
                    if proxy_id not in self.performance_metrics:
                        self.performance_metrics[proxy_id] = ProxyPerformanceMetrics(proxy_id)
                    
                    self.performance_metrics[proxy_id].add_health_check(result)
                    
                    return {proxy_id: result}
                else:
                    return {}
            else:
                return self.perform_health_checks()
                
        except Exception as e:
            logger.error(f"Error forcing health check: {e}")
            return {}

# Global health monitor instance
proxy_health_monitor = None

def initialize_proxy_health_monitor(proxy_manager: ProxyManager, 
                                  mongodb_connection=None, redis_client=None) -> ProxyHealthMonitor:
    """Initialize global proxy health monitor"""
    global proxy_health_monitor
    proxy_health_monitor = ProxyHealthMonitor(proxy_manager, mongodb_connection, redis_client)
    return proxy_health_monitor

def get_proxy_health_monitor() -> ProxyHealthMonitor:
    """Get global proxy health monitor"""
    if proxy_health_monitor is None:
        raise ValueError("Proxy health monitor not initialized")
    return proxy_health_monitor

# Convenience functions
def get_proxy_health_status(proxy_id: str) -> Optional[Dict[str, Any]]:
    """Get proxy health status (global convenience function)"""
    return get_proxy_health_monitor().get_proxy_health_status(proxy_id)

def get_all_proxy_health_status() -> Dict[str, Dict[str, Any]]:
    """Get all proxy health status (global convenience function)"""
    return get_proxy_health_monitor().get_all_proxy_health_status()

def force_health_check(proxy_id: str = None) -> Dict[str, HealthCheckResult]:
    """Force health check (global convenience function)"""
    return get_proxy_health_monitor().force_health_check(proxy_id)
