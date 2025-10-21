"""
Comprehensive Monitoring Infrastructure
InfluxDB metrics and alerting system for the ZaloPay Merchant Phishing Platform
"""

import os
import json
import time
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Union
import logging
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import psutil
import requests
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MetricData:
    """Metric data structure"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str]
    fields: Dict[str, Any]

@dataclass
class AlertRule:
    """Alert rule configuration"""
    rule_id: str
    name: str
    metric_name: str
    condition: str  # >, <, >=, <=, ==, !=
    threshold: float
    duration: int  # seconds
    severity: str  # info, warning, error, critical
    enabled: bool
    notification_channels: List[str]
    description: str

@dataclass
class Alert:
    """Alert instance"""
    alert_id: str
    rule_id: str
    metric_name: str
    current_value: float
    threshold: float
    severity: str
    timestamp: datetime
    status: str  # active, resolved, acknowledged
    message: str
    notification_sent: bool

class InfluxDBManager:
    """InfluxDB connection and data management"""
    
    def __init__(self, url: str = None, token: str = None, org: str = None, bucket: str = None):
        self.url = url or os.getenv("INFLUXDB_URL", "http://localhost:8086")
        self.token = token or os.getenv("INFLUXDB_TOKEN", "")
        self.org = org or os.getenv("INFLUXDB_ORG", "zalopay")
        self.bucket = bucket or os.getenv("INFLUXDB_BUCKET", "phishing_metrics")
        
        self.client = None
        self.write_api = None
        self.query_api = None
        
        self._connect()
    
    def _connect(self):
        """Connect to InfluxDB"""
        try:
            self.client = InfluxDBClient(
                url=self.url,
                token=self.token,
                org=self.org
            )
            
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()
            
            # Test connection
            self.client.ping()
            logger.info(f"Connected to InfluxDB: {self.url}")
            
        except Exception as e:
            logger.error(f"Error connecting to InfluxDB: {e}")
            raise
    
    def write_metric(self, metric: MetricData):
        """Write metric to InfluxDB"""
        try:
            point = Point(metric.name) \
                .time(metric.timestamp, WritePrecision.MS)
            
            # Add tags
            for key, value in metric.tags.items():
                point = point.tag(key, value)
            
            # Add fields
            for key, value in metric.fields.items():
                point = point.field(key, value)
            
            self.write_api.write(bucket=self.bucket, record=point)
            
        except Exception as e:
            logger.error(f"Error writing metric {metric.name}: {e}")
    
    def write_metrics_batch(self, metrics: List[MetricData]):
        """Write multiple metrics in batch"""
        try:
            points = []
            
            for metric in metrics:
                point = Point(metric.name) \
                    .time(metric.timestamp, WritePrecision.MS)
                
                # Add tags
                for key, value in metric.tags.items():
                    point = point.tag(key, value)
                
                # Add fields
                for key, value in metric.fields.items():
                    point = point.field(key, value)
                
                points.append(point)
            
            self.write_api.write(bucket=self.bucket, record=points)
            
        except Exception as e:
            logger.error(f"Error writing metrics batch: {e}")
    
    def query_metrics(self, query: str) -> List[Dict[str, Any]]:
        """Query metrics from InfluxDB"""
        try:
            result = self.query_api.query(query)
            
            data = []
            for table in result:
                for record in table.records:
                    data.append({
                        "time": record.get_time(),
                        "measurement": record.get_measurement(),
                        "field": record.get_field(),
                        "value": record.get_value(),
                        "tags": record.values
                    })
            
            return data
            
        except Exception as e:
            logger.error(f"Error querying metrics: {e}")
            return []
    
    def close(self):
        """Close InfluxDB connection"""
        if self.client:
            self.client.close()

class SystemMonitor:
    """System resource monitoring"""
    
    def __init__(self, influxdb_manager: InfluxDBManager):
        self.influxdb = influxdb_manager
        self.monitoring = False
        self.monitor_thread = None
        
    def start_monitoring(self, interval: int = 60):
        """Start system monitoring"""
        try:
            self.monitoring = True
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop,
                args=(interval,),
                daemon=True
            )
            self.monitor_thread.start()
            logger.info("System monitoring started")
            
        except Exception as e:
            logger.error(f"Error starting system monitoring: {e}")
            raise
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("System monitoring stopped")
    
    def _monitor_loop(self, interval: int):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                metrics = self._collect_system_metrics()
                self.influxdb.write_metrics_batch(metrics)
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)
    
    def _collect_system_metrics(self) -> List[MetricData]:
        """Collect system metrics"""
        try:
            metrics = []
            now = datetime.now(timezone.utc)
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            metrics.append(MetricData(
                name="system_cpu",
                value=cpu_percent,
                timestamp=now,
                tags={"type": "usage_percent"},
                fields={"cpu_count": cpu_count, "cpu_freq": cpu_freq.current if cpu_freq else 0}
            ))
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            metrics.append(MetricData(
                name="system_memory",
                value=memory.percent,
                timestamp=now,
                tags={"type": "usage_percent"},
                fields={
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "free": memory.free,
                    "swap_total": swap.total,
                    "swap_used": swap.used,
                    "swap_free": swap.free
                }
            ))
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            metrics.append(MetricData(
                name="system_disk",
                value=(disk.used / disk.total) * 100,
                timestamp=now,
                tags={"type": "usage_percent", "device": "/"},
                fields={
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "read_bytes": disk_io.read_bytes if disk_io else 0,
                    "write_bytes": disk_io.write_bytes if disk_io else 0
                }
            ))
            
            # Network metrics
            network_io = psutil.net_io_counters()
            
            metrics.append(MetricData(
                name="system_network",
                value=0,  # Placeholder
                timestamp=now,
                tags={"type": "io"},
                fields={
                    "bytes_sent": network_io.bytes_sent,
                    "bytes_recv": network_io.bytes_recv,
                    "packets_sent": network_io.packets_sent,
                    "packets_recv": network_io.packets_recv
                }
            ))
            
            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()
            
            metrics.append(MetricData(
                name="application_process",
                value=process_cpu,
                timestamp=now,
                tags={"type": "cpu_usage"},
                fields={
                    "memory_rss": process_memory.rss,
                    "memory_vms": process_memory.vms,
                    "num_threads": process.num_threads(),
                    "create_time": process.create_time()
                }
            ))
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return []

class PerformanceTracker:
    """Application performance tracking"""
    
    def __init__(self, influxdb_manager: InfluxDBManager):
        self.influxdb = influxdb_manager
        self.metrics_buffer = deque(maxlen=1000)
        self.api_latencies = defaultdict(list)
        
    def track_api_call(self, endpoint: str, method: str, status_code: int, 
                      latency: float, response_size: int = 0):
        """Track API call performance"""
        try:
            now = datetime.now(timezone.utc)
            
            metric = MetricData(
                name="api_performance",
                value=latency,
                timestamp=now,
                tags={
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": str(status_code)
                },
                fields={
                    "response_size": response_size,
                    "status_code": status_code
                }
            )
            
            self.metrics_buffer.append(metric)
            self.api_latencies[endpoint].append(latency)
            
            # Keep only last 100 latencies per endpoint
            if len(self.api_latencies[endpoint]) > 100:
                self.api_latencies[endpoint] = self.api_latencies[endpoint][-100:]
            
        except Exception as e:
            logger.error(f"Error tracking API call: {e}")
    
    def track_database_operation(self, operation: str, collection: str, 
                               duration: float, success: bool, records_affected: int = 0):
        """Track database operation performance"""
        try:
            now = datetime.now(timezone.utc)
            
            metric = MetricData(
                name="database_performance",
                value=duration,
                timestamp=now,
                tags={
                    "operation": operation,
                    "collection": collection,
                    "success": str(success)
                },
                fields={
                    "records_affected": records_affected
                }
            )
            
            self.metrics_buffer.append(metric)
            
        except Exception as e:
            logger.error(f"Error tracking database operation: {e}")
    
    def track_campaign_metrics(self, campaign_id: str, metric_name: str, 
                             value: float, tags: Dict[str, str] = None):
        """Track campaign-specific metrics"""
        try:
            now = datetime.now(timezone.utc)
            
            metric_tags = {"campaign_id": campaign_id}
            if tags:
                metric_tags.update(tags)
            
            metric = MetricData(
                name=f"campaign_{metric_name}",
                value=value,
                timestamp=now,
                tags=metric_tags,
                fields={}
            )
            
            self.metrics_buffer.append(metric)
            
        except Exception as e:
            logger.error(f"Error tracking campaign metrics: {e}")
    
    def track_victim_metrics(self, victim_id: str, metric_name: str, 
                           value: float, tags: Dict[str, str] = None):
        """Track victim-specific metrics"""
        try:
            now = datetime.now(timezone.utc)
            
            metric_tags = {"victim_id": victim_id}
            if tags:
                metric_tags.update(tags)
            
            metric = MetricData(
                name=f"victim_{metric_name}",
                value=value,
                timestamp=now,
                tags=metric_tags,
                fields={}
            )
            
            self.metrics_buffer.append(metric)
            
        except Exception as e:
            logger.error(f"Error tracking victim metrics: {e}")
    
    def flush_metrics(self):
        """Flush buffered metrics to InfluxDB"""
        try:
            if self.metrics_buffer:
                metrics = list(self.metrics_buffer)
                self.influxdb.write_metrics_batch(metrics)
                self.metrics_buffer.clear()
                logger.debug(f"Flushed {len(metrics)} metrics to InfluxDB")
                
        except Exception as e:
            logger.error(f"Error flushing metrics: {e}")
    
    def get_api_latency_stats(self, endpoint: str) -> Dict[str, float]:
        """Get API latency statistics for an endpoint"""
        try:
            latencies = self.api_latencies.get(endpoint, [])
            
            if not latencies:
                return {}
            
            return {
                "count": len(latencies),
                "avg": sum(latencies) / len(latencies),
                "min": min(latencies),
                "max": max(latencies),
                "p95": sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0,
                "p99": sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting API latency stats: {e}")
            return {}

class AlertManager:
    """Alert management and notification system"""
    
    def __init__(self, influxdb_manager: InfluxDBManager):
        self.influxdb = influxdb_manager
        self.alert_rules = {}
        self.active_alerts = {}
        self.alert_history = deque(maxlen=10000)
        
        # Initialize default alert rules
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default alert rules"""
        default_rules = [
            AlertRule(
                rule_id="high_cpu_usage",
                name="High CPU Usage",
                metric_name="system_cpu",
                condition=">",
                threshold=80.0,
                duration=300,  # 5 minutes
                severity="warning",
                enabled=True,
                notification_channels=["email", "webhook"],
                description="CPU usage exceeds 80% for 5 minutes"
            ),
            AlertRule(
                rule_id="high_memory_usage",
                name="High Memory Usage",
                metric_name="system_memory",
                condition=">",
                threshold=85.0,
                duration=300,
                severity="warning",
                enabled=True,
                notification_channels=["email", "webhook"],
                description="Memory usage exceeds 85% for 5 minutes"
            ),
            AlertRule(
                rule_id="high_disk_usage",
                name="High Disk Usage",
                metric_name="system_disk",
                condition=">",
                threshold=90.0,
                duration=600,  # 10 minutes
                severity="error",
                enabled=True,
                notification_channels=["email", "webhook", "sms"],
                description="Disk usage exceeds 90% for 10 minutes"
            ),
            AlertRule(
                rule_id="api_high_latency",
                name="High API Latency",
                metric_name="api_performance",
                condition=">",
                threshold=5.0,  # 5 seconds
                duration=180,  # 3 minutes
                severity="warning",
                enabled=True,
                notification_channels=["email", "webhook"],
                description="API response time exceeds 5 seconds for 3 minutes"
            ),
            AlertRule(
                rule_id="database_slow_queries",
                name="Slow Database Queries",
                metric_name="database_performance",
                condition=">",
                threshold=2.0,  # 2 seconds
                duration=300,
                severity="warning",
                enabled=True,
                notification_channels=["email", "webhook"],
                description="Database queries taking longer than 2 seconds"
            )
        ]
        
        for rule in default_rules:
            self.alert_rules[rule.rule_id] = rule
    
    def add_alert_rule(self, rule: AlertRule):
        """Add a new alert rule"""
        self.alert_rules[rule.rule_id] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_alert_rule(self, rule_id: str):
        """Remove an alert rule"""
        if rule_id in self.alert_rules:
            del self.alert_rules[rule_id]
            logger.info(f"Removed alert rule: {rule_id}")
    
    def check_alerts(self, metric: MetricData):
        """Check if a metric triggers any alerts"""
        try:
            for rule_id, rule in self.alert_rules.items():
                if not rule.enabled or rule.metric_name != metric.name:
                    continue
                
                # Check if condition is met
                condition_met = self._evaluate_condition(
                    metric.value, rule.condition, rule.threshold
                )
                
                if condition_met:
                    # Check if alert is already active
                    alert_key = f"{rule_id}_{metric.tags.get('endpoint', 'default')}"
                    
                    if alert_key not in self.active_alerts:
                        # Create new alert
                        alert = Alert(
                            alert_id=f"alert_{int(time.time())}_{rule_id}",
                            rule_id=rule_id,
                            metric_name=metric.name,
                            current_value=metric.value,
                            threshold=rule.threshold,
                            severity=rule.severity,
                            timestamp=datetime.now(timezone.utc),
                            status="active",
                            message=f"{rule.name}: {metric.name} = {metric.value} {rule.condition} {rule.threshold}",
                            notification_sent=False
                        )
                        
                        self.active_alerts[alert_key] = alert
                        self.alert_history.append(alert)
                        
                        # Send notification
                        self._send_notification(alert, rule)
                        
                        logger.warning(f"Alert triggered: {alert.message}")
                
                else:
                    # Check if alert should be resolved
                    alert_key = f"{rule_id}_{metric.tags.get('endpoint', 'default')}"
                    if alert_key in self.active_alerts:
                        alert = self.active_alerts[alert_key]
                        if alert.status == "active":
                            alert.status = "resolved"
                            alert.message += " (RESOLVED)"
                            logger.info(f"Alert resolved: {alert.message}")
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Evaluate alert condition"""
        try:
            if condition == ">":
                return value > threshold
            elif condition == "<":
                return value < threshold
            elif condition == ">=":
                return value >= threshold
            elif condition == "<=":
                return value <= threshold
            elif condition == "==":
                return value == threshold
            elif condition == "!=":
                return value != threshold
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False
    
    def _send_notification(self, alert: Alert, rule: AlertRule):
        """Send alert notification"""
        try:
            for channel in rule.notification_channels:
                if channel == "email":
                    self._send_email_notification(alert)
                elif channel == "webhook":
                    self._send_webhook_notification(alert)
                elif channel == "sms":
                    self._send_sms_notification(alert)
            
            alert.notification_sent = True
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def _send_email_notification(self, alert: Alert):
        """Send email notification"""
        try:
            # TODO: Implement email notification
            logger.info(f"Email notification: {alert.message}")
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
    
    def _send_webhook_notification(self, alert: Alert):
        """Send webhook notification"""
        try:
            webhook_url = os.getenv("ALERT_WEBHOOK_URL")
            if not webhook_url:
                return
            
            payload = {
                "alert_id": alert.alert_id,
                "rule_id": alert.rule_id,
                "severity": alert.severity,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "current_value": alert.current_value,
                "threshold": alert.threshold
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Webhook notification sent: {alert.message}")
            
        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")
    
    def _send_sms_notification(self, alert: Alert):
        """Send SMS notification"""
        try:
            # TODO: Implement SMS notification
            logger.info(f"SMS notification: {alert.message}")
            
        except Exception as e:
            logger.error(f"Error sending SMS notification: {e}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return [alert for alert in self.active_alerts.values() if alert.status == "active"]
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history"""
        return list(self.alert_history)[-limit:]
    
    def acknowledge_alert(self, alert_id: str, admin_id: str):
        """Acknowledge an alert"""
        try:
            for alert in self.active_alerts.values():
                if alert.alert_id == alert_id:
                    alert.status = "acknowledged"
                    alert.message += f" (ACKNOWLEDGED by {admin_id})"
                    logger.info(f"Alert acknowledged: {alert_id} by {admin_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error acknowledging alert: {e}")
            return False

class MonitoringInfrastructure:
    """Main monitoring infrastructure coordinator"""
    
    def __init__(self, influxdb_url: str = None, influxdb_token: str = None):
        self.influxdb_manager = InfluxDBManager(influxdb_url, influxdb_token)
        self.system_monitor = SystemMonitor(self.influxdb_manager)
        self.performance_tracker = PerformanceTracker(self.influxdb_manager)
        self.alert_manager = AlertManager(self.influxdb_manager)
        
        self.monitoring_active = False
        self.metrics_thread = None
    
    def start_monitoring(self, system_interval: int = 60, metrics_interval: int = 30):
        """Start all monitoring systems"""
        try:
            self.monitoring_active = True
            
            # Start system monitoring
            self.system_monitor.start_monitoring(system_interval)
            
            # Start metrics flushing
            self.metrics_thread = threading.Thread(
                target=self._metrics_flush_loop,
                args=(metrics_interval,),
                daemon=True
            )
            self.metrics_thread.start()
            
            logger.info("Monitoring infrastructure started")
            
        except Exception as e:
            logger.error(f"Error starting monitoring: {e}")
            raise
    
    def stop_monitoring(self):
        """Stop all monitoring systems"""
        try:
            self.monitoring_active = False
            
            # Stop system monitoring
            self.system_monitor.stop_monitoring()
            
            # Stop metrics flushing
            if self.metrics_thread:
                self.metrics_thread.join()
            
            # Flush remaining metrics
            self.performance_tracker.flush_metrics()
            
            logger.info("Monitoring infrastructure stopped")
            
        except Exception as e:
            logger.error(f"Error stopping monitoring: {e}")
    
    def _metrics_flush_loop(self, interval: int):
        """Metrics flushing loop"""
        while self.monitoring_active:
            try:
                self.performance_tracker.flush_metrics()
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in metrics flush loop: {e}")
                time.sleep(interval)
    
    def track_metric(self, name: str, value: float, tags: Dict[str, str] = None, 
                   fields: Dict[str, Any] = None):
        """Track a custom metric"""
        try:
            metric = MetricData(
                name=name,
                value=value,
                timestamp=datetime.now(timezone.utc),
                tags=tags or {},
                fields=fields or {}
            )
            
            self.performance_tracker.metrics_buffer.append(metric)
            
            # Check for alerts
            self.alert_manager.check_alerts(metric)
            
        except Exception as e:
            logger.error(f"Error tracking metric: {e}")
    
    def get_system_metrics(self, time_range: str = "1h") -> Dict[str, Any]:
        """Get system metrics for the specified time range"""
        try:
            query = f'''
            from(bucket: "{self.influxdb_manager.bucket}")
            |> range(start: -{time_range})
            |> filter(fn: (r) => r._measurement =~ /^system_/)
            |> group(columns: ["_measurement", "_field"])
            |> mean()
            '''
            
            data = self.influxdb_manager.query_metrics(query)
            
            metrics = {}
            for record in data:
                measurement = record.get("measurement", "")
                field = record.get("field", "")
                value = record.get("value", 0)
                
                if measurement not in metrics:
                    metrics[measurement] = {}
                
                metrics[measurement][field] = value
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}
    
    def get_api_metrics(self, time_range: str = "1h") -> Dict[str, Any]:
        """Get API metrics for the specified time range"""
        try:
            query = f'''
            from(bucket: "{self.influxdb_manager.bucket}")
            |> range(start: -{time_range})
            |> filter(fn: (r) => r._measurement == "api_performance")
            |> group(columns: ["endpoint", "method"])
            |> mean(column: "_value")
            '''
            
            data = self.influxdb_manager.query_metrics(query)
            
            metrics = {}
            for record in data:
                endpoint = record.get("endpoint", "")
                method = record.get("method", "")
                value = record.get("value", 0)
                
                key = f"{method} {endpoint}"
                metrics[key] = value
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting API metrics: {e}")
            return {}
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary"""
        try:
            active_alerts = self.alert_manager.get_active_alerts()
            alert_history = self.alert_manager.get_alert_history(100)
            
            summary = {
                "active_alerts": len(active_alerts),
                "total_alerts_24h": len([a for a in alert_history 
                                       if a.timestamp > datetime.now(timezone.utc) - timedelta(hours=24)]),
                "alerts_by_severity": {},
                "recent_alerts": [asdict(alert) for alert in alert_history[-10:]]
            }
            
            # Count by severity
            for alert in active_alerts:
                severity = alert.severity
                summary["alerts_by_severity"][severity] = summary["alerts_by_severity"].get(severity, 0) + 1
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting alert summary: {e}")
            return {}
    
    def close(self):
        """Close monitoring infrastructure"""
        self.stop_monitoring()
        self.influxdb_manager.close()

# Global monitoring infrastructure instance
monitoring_infrastructure = None

def initialize_monitoring_infrastructure(influxdb_url: str = None, influxdb_token: str = None) -> MonitoringInfrastructure:
    """Initialize monitoring infrastructure"""
    global monitoring_infrastructure
    monitoring_infrastructure = MonitoringInfrastructure(influxdb_url, influxdb_token)
    return monitoring_infrastructure

def get_monitoring_infrastructure() -> MonitoringInfrastructure:
    """Get monitoring infrastructure instance"""
    global monitoring_infrastructure
    if monitoring_infrastructure is None:
        monitoring_infrastructure = MonitoringInfrastructure()
    return monitoring_infrastructure
