"""
InfluxDB Client for Metrics Collection
Handles time-series data storage and retrieval
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json

try:
    from influxdb_client import InfluxDBClient, Point, WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS
    from influxdb_client.client.exceptions import InfluxDBError
except ImportError:
    InfluxDBClient = None
    Point = None
    WritePrecision = None
    SYNCHRONOUS = None
    InfluxDBError = Exception

logger = logging.getLogger(__name__)

@dataclass
class MetricPoint:
    """Represents a single metric data point"""
    measurement: str
    tags: Dict[str, str]
    fields: Dict[str, Any]
    timestamp: Optional[datetime] = None

class InfluxDBMetricsClient:
    """
    InfluxDB client for metrics collection and storage
    """
    
    def __init__(self, url: str, token: str, org: str, bucket: str):
        """
        Initialize InfluxDB client
        
        Args:
            url: InfluxDB server URL
            token: Authentication token
            org: Organization name
            bucket: Bucket name for data storage
        """
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.client = None
        self.write_api = None
        self.query_api = None
        self._connected = False
        
    async def connect(self) -> bool:
        """
        Connect to InfluxDB
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if InfluxDBClient is None:
                logger.error("InfluxDB client not available. Install influxdb-client package.")
                return False
                
            self.client = InfluxDBClient(
                url=self.url,
                token=self.token,
                org=self.org
            )
            
            # Test connection
            health = self.client.health()
            if health.status == "pass":
                self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
                self.query_api = self.client.query_api()
                self._connected = True
                logger.info("Connected to InfluxDB successfully")
                return True
            else:
                logger.error(f"InfluxDB health check failed: {health.message}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to InfluxDB: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from InfluxDB"""
        if self.client:
            self.client.close()
            self._connected = False
            logger.info("Disconnected from InfluxDB")
    
    async def write_metric(self, metric: MetricPoint) -> bool:
        """
        Write a single metric to InfluxDB
        
        Args:
            metric: MetricPoint to write
            
        Returns:
            True if successful, False otherwise
        """
        if not self._connected:
            logger.warning("Not connected to InfluxDB")
            return False
            
        try:
            point = Point(metric.measurement)
            
            # Add tags
            for key, value in metric.tags.items():
                point = point.tag(key, value)
            
            # Add fields
            for key, value in metric.fields.items():
                if isinstance(value, (int, float)):
                    point = point.field(key, value)
                elif isinstance(value, bool):
                    point = point.field(key, value)
                elif isinstance(value, str):
                    point = point.field(key, value)
                else:
                    point = point.field(key, str(value))
            
            # Set timestamp
            if metric.timestamp:
                point = point.time(metric.timestamp, WritePrecision.NS)
            else:
                point = point.time(datetime.now(timezone.utc), WritePrecision.NS)
            
            # Write to InfluxDB
            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True
            
        except InfluxDBError as e:
            logger.error(f"InfluxDB write error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error writing metric to InfluxDB: {e}")
            return False
    
    async def write_metrics(self, metrics: List[MetricPoint]) -> bool:
        """
        Write multiple metrics to InfluxDB
        
        Args:
            metrics: List of MetricPoint objects
            
        Returns:
            True if successful, False otherwise
        """
        if not self._connected:
            logger.warning("Not connected to InfluxDB")
            return False
            
        try:
            points = []
            
            for metric in metrics:
                point = Point(metric.measurement)
                
                # Add tags
                for key, value in metric.tags.items():
                    point = point.tag(key, value)
                
                # Add fields
                for key, value in metric.fields.items():
                    if isinstance(value, (int, float)):
                        point = point.field(key, value)
                    elif isinstance(value, bool):
                        point = point.field(key, value)
                    elif isinstance(value, str):
                        point = point.field(key, value)
                    else:
                        point = point.field(key, str(value))
                
                # Set timestamp
                if metric.timestamp:
                    point = point.time(metric.timestamp, WritePrecision.NS)
                else:
                    point = point.time(datetime.now(timezone.utc), WritePrecision.NS)
                
                points.append(point)
            
            # Write to InfluxDB
            self.write_api.write(bucket=self.bucket, org=self.org, record=points)
            return True
            
        except InfluxDBError as e:
            logger.error(f"InfluxDB write error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error writing metrics to InfluxDB: {e}")
            return False
    
    async def query_metrics(self, query: str) -> List[Dict[str, Any]]:
        """
        Query metrics from InfluxDB
        
        Args:
            query: Flux query string
            
        Returns:
            List of query results
        """
        if not self._connected:
            logger.warning("Not connected to InfluxDB")
            return []
            
        try:
            result = self.query_api.query(org=self.org, query=query)
            
            data = []
            for table in result:
                for record in table.records:
                    data.append({
                        'measurement': record.get_measurement(),
                        'tags': record.values,
                        'fields': record.values,
                        'timestamp': record.get_time()
                    })
            
            return data
            
        except InfluxDBError as e:
            logger.error(f"InfluxDB query error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error querying InfluxDB: {e}")
            return []
    
    async def get_system_metrics(self, time_range: str = "1h") -> Dict[str, Any]:
        """
        Get system metrics for dashboard
        
        Args:
            time_range: Time range for metrics (e.g., "1h", "24h", "7d")
            
        Returns:
            Dictionary of system metrics
        """
        metrics = {}
        
        # CPU usage
        cpu_query = f'''
        from(bucket: "{self.bucket}")
        |> range(start: -{time_range})
        |> filter(fn: (r) => r._measurement == "system_cpu")
        |> filter(fn: (r) => r._field == "usage_percent")
        |> mean()
        '''
        
        cpu_data = await self.query_metrics(cpu_query)
        metrics['cpu_usage'] = cpu_data[0]['fields']['_value'] if cpu_data else 0
        
        # Memory usage
        memory_query = f'''
        from(bucket: "{self.bucket}")
        |> range(start: -{time_range})
        |> filter(fn: (r) => r._measurement == "system_memory")
        |> filter(fn: (r) => r._field == "usage_percent")
        |> mean()
        '''
        
        memory_data = await self.query_metrics(memory_query)
        metrics['memory_usage'] = memory_data[0]['fields']['_value'] if memory_data else 0
        
        # Disk usage
        disk_query = f'''
        from(bucket: "{self.bucket}")
        |> range(start: -{time_range})
        |> filter(fn: (r) => r._measurement == "system_disk")
        |> filter(fn: (r) => r._field == "usage_percent")
        |> mean()
        '''
        
        disk_data = await self.query_metrics(disk_query)
        metrics['disk_usage'] = disk_data[0]['fields']['_value'] if disk_data else 0
        
        # Network traffic
        network_query = f'''
        from(bucket: "{self.bucket}")
        |> range(start: -{time_range})
        |> filter(fn: (r) => r._measurement == "system_network")
        |> filter(fn: (r) => r._field == "bytes_sent" or r._field == "bytes_received")
        |> sum()
        '''
        
        network_data = await self.query_metrics(network_query)
        metrics['network_traffic'] = {
            'bytes_sent': 0,
            'bytes_received': 0
        }
        
        for record in network_data:
            if record['fields']['_field'] == 'bytes_sent':
                metrics['network_traffic']['bytes_sent'] = record['fields']['_value']
            elif record['fields']['_field'] == 'bytes_received':
                metrics['network_traffic']['bytes_received'] = record['fields']['_value']
        
        return metrics
    
    async def get_application_metrics(self, time_range: str = "1h") -> Dict[str, Any]:
        """
        Get application metrics for dashboard
        
        Args:
            time_range: Time range for metrics (e.g., "1h", "24h", "7d")
            
        Returns:
            Dictionary of application metrics
        """
        metrics = {}
        
        # Request count
        request_query = f'''
        from(bucket: "{self.bucket}")
        |> range(start: -{time_range})
        |> filter(fn: (r) => r._measurement == "http_requests")
        |> filter(fn: (r) => r._field == "count")
        |> sum()
        '''
        
        request_data = await self.query_metrics(request_query)
        metrics['total_requests'] = request_data[0]['fields']['_value'] if request_data else 0
        
        # Response time
        response_time_query = f'''
        from(bucket: "{self.bucket}")
        |> range(start: -{time_range})
        |> filter(fn: (r) => r._measurement == "http_requests")
        |> filter(fn: (r) => r._field == "response_time")
        |> mean()
        '''
        
        response_time_data = await self.query_metrics(response_time_query)
        metrics['avg_response_time'] = response_time_data[0]['fields']['_value'] if response_time_data else 0
        
        # Error rate
        error_query = f'''
        from(bucket: "{self.bucket}")
        |> range(start: -{time_range})
        |> filter(fn: (r) => r._measurement == "http_requests")
        |> filter(fn: (r) => r._field == "status_code")
        |> filter(fn: (r) => r._value >= 400)
        |> count()
        '''
        
        error_data = await self.query_metrics(error_query)
        metrics['error_count'] = error_data[0]['fields']['_value'] if error_data else 0
        
        # Active users
        users_query = f'''
        from(bucket: "{self.bucket}")
        |> range(start: -{time_range})
        |> filter(fn: (r) => r._measurement == "active_users")
        |> filter(fn: (r) => r._field == "count")
        |> max()
        '''
        
        users_data = await self.query_metrics(users_query)
        metrics['active_users'] = users_data[0]['fields']['_value'] if users_data else 0
        
        return metrics
    
    async def get_security_metrics(self, time_range: str = "1h") -> Dict[str, Any]:
        """
        Get security metrics for dashboard
        
        Args:
            time_range: Time range for metrics (e.g., "1h", "24h", "7d")
            
        Returns:
            Dictionary of security metrics
        """
        metrics = {}
        
        # Failed login attempts
        failed_login_query = f'''
        from(bucket: "{self.bucket}")
        |> range(start: -{time_range})
        |> filter(fn: (r) => r._measurement == "security_events")
        |> filter(fn: (r) => r._field == "failed_logins")
        |> sum()
        '''
        
        failed_login_data = await self.query_metrics(failed_login_query)
        metrics['failed_logins'] = failed_login_data[0]['fields']['_value'] if failed_login_data else 0
        
        # Suspicious activities
        suspicious_query = f'''
        from(bucket: "{self.bucket}")
        |> range(start: -{time_range})
        |> filter(fn: (r) => r._measurement == "security_events")
        |> filter(fn: (r) => r._field == "suspicious_activities")
        |> sum()
        '''
        
        suspicious_data = await self.query_metrics(suspicious_query)
        metrics['suspicious_activities'] = suspicious_data[0]['fields']['_value'] if suspicious_data else 0
        
        # Blocked IPs
        blocked_ip_query = f'''
        from(bucket: "{self.bucket}")
        |> range(start: -{time_range})
        |> filter(fn: (r) => r._measurement == "security_events")
        |> filter(fn: (r) => r._field == "blocked_ips")
        |> sum()
        '''
        
        blocked_ip_data = await self.query_metrics(blocked_ip_query)
        metrics['blocked_ips'] = blocked_ip_data[0]['fields']['_value'] if blocked_ip_data else 0
        
        return metrics

# Global InfluxDB client instance
influxdb_client: Optional[InfluxDBMetricsClient] = None

async def get_influxdb_client() -> Optional[InfluxDBMetricsClient]:
    """Get the global InfluxDB client instance"""
    return influxdb_client

async def initialize_influxdb(url: str, token: str, org: str, bucket: str) -> bool:
    """
    Initialize the global InfluxDB client
    
    Args:
        url: InfluxDB server URL
        token: Authentication token
        org: Organization name
        bucket: Bucket name for data storage
        
    Returns:
        True if initialization successful, False otherwise
    """
    global influxdb_client
    
    try:
        influxdb_client = InfluxDBMetricsClient(url, token, org, bucket)
        success = await influxdb_client.connect()
        
        if success:
            logger.info("InfluxDB client initialized successfully")
        else:
            logger.error("Failed to initialize InfluxDB client")
            
        return success
        
    except Exception as e:
        logger.error(f"Error initializing InfluxDB client: {e}")
        return False

async def record_metric(measurement: str, tags: Dict[str, str], fields: Dict[str, Any], timestamp: Optional[datetime] = None) -> bool:
    """
    Record a single metric
    
    Args:
        measurement: Measurement name
        tags: Tags dictionary
        fields: Fields dictionary
        timestamp: Optional timestamp
        
    Returns:
        True if successful, False otherwise
    """
    if not influxdb_client:
        logger.warning("InfluxDB client not initialized")
        return False
        
    metric = MetricPoint(
        measurement=measurement,
        tags=tags,
        fields=fields,
        timestamp=timestamp
    )
    
    return await influxdb_client.write_metric(metric)

async def record_metrics(metrics: List[MetricPoint]) -> bool:
    """
    Record multiple metrics
    
    Args:
        metrics: List of MetricPoint objects
        
    Returns:
        True if successful, False otherwise
    """
    if not influxdb_client:
        logger.warning("InfluxDB client not initialized")
        return False
        
    return await influxdb_client.write_metrics(metrics)
