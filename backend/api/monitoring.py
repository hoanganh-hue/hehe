"""
Monitoring API Endpoints
REST API for monitoring and metrics management
"""

import os
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import logging
from fastapi import APIRouter, HTTPException, Query, Body, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])

# Pydantic models
class MetricRequest(BaseModel):
    name: str
    value: float
    tags: Dict[str, str] = {}
    fields: Dict[str, Any] = {}

class AlertRuleRequest(BaseModel):
    name: str
    metric_name: str
    condition: str
    threshold: float
    duration: int
    severity: str
    enabled: bool = True
    notification_channels: List[str] = []
    description: str = ""

class AlertAcknowledgeRequest(BaseModel):
    admin_id: str
    notes: str = ""

# Dependency to get monitoring infrastructure
def get_monitoring():
    from monitoring.infrastructure import get_monitoring_infrastructure
    return get_monitoring_infrastructure()

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        monitoring = get_monitoring()
        
        # Check InfluxDB connection
        try:
            monitoring.influxdb_manager.client.ping()
            influxdb_status = "healthy"
        except:
            influxdb_status = "unhealthy"
        
        # Check system resources
        import psutil
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent
        
        health_status = {
            "status": "healthy" if influxdb_status == "healthy" else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {
                "influxdb": influxdb_status,
                "monitoring": "active" if monitoring.monitoring_active else "inactive"
            },
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_percent": disk_percent
            }
        }
        
        return JSONResponse(content=health_status)
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@router.post("/metrics")
async def track_metric(
    metric: MetricRequest,
    monitoring = Depends(get_monitoring)
):
    """Track a custom metric"""
    try:
        monitoring.track_metric(
            name=metric.name,
            value=metric.value,
            tags=metric.tags,
            fields=metric.fields
        )
        
        return JSONResponse(content={
            "success": True,
            "message": "Metric tracked successfully"
        })
        
    except Exception as e:
        logger.error(f"Error tracking metric: {e}")
        raise HTTPException(status_code=500, detail="Failed to track metric")

@router.get("/metrics/system")
async def get_system_metrics(
    time_range: str = Query("1h", description="Time range (e.g., 1h, 24h, 7d)"),
    monitoring = Depends(get_monitoring)
):
    """Get system metrics"""
    try:
        metrics = monitoring.get_system_metrics(time_range)
        
        return JSONResponse(content={
            "success": True,
            "time_range": time_range,
            "metrics": metrics
        })
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system metrics")

@router.get("/metrics/api")
async def get_api_metrics(
    time_range: str = Query("1h", description="Time range (e.g., 1h, 24h, 7d)"),
    monitoring = Depends(get_monitoring)
):
    """Get API performance metrics"""
    try:
        metrics = monitoring.get_api_metrics(time_range)
        
        # Get latency statistics
        latency_stats = {}
        for endpoint in monitoring.performance_tracker.api_latencies:
            stats = monitoring.performance_tracker.get_api_latency_stats(endpoint)
            if stats:
                latency_stats[endpoint] = stats
        
        return JSONResponse(content={
            "success": True,
            "time_range": time_range,
            "metrics": metrics,
            "latency_stats": latency_stats
        })
        
    except Exception as e:
        logger.error(f"Error getting API metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get API metrics")

@router.get("/alerts")
async def get_alerts(
    status: str = Query(None, description="Filter by alert status"),
    severity: str = Query(None, description="Filter by severity"),
    limit: int = Query(100, description="Maximum number of alerts"),
    monitoring = Depends(get_monitoring)
):
    """Get alerts"""
    try:
        if status == "active":
            alerts = monitoring.alert_manager.get_active_alerts()
        else:
            alerts = monitoring.alert_manager.get_alert_history(limit)
        
        # Filter by severity if specified
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        
        # Convert to dict format
        alerts_data = []
        for alert in alerts:
            alerts_data.append({
                "alert_id": alert.alert_id,
                "rule_id": alert.rule_id,
                "metric_name": alert.metric_name,
                "current_value": alert.current_value,
                "threshold": alert.threshold,
                "severity": alert.severity,
                "timestamp": alert.timestamp.isoformat(),
                "status": alert.status,
                "message": alert.message,
                "notification_sent": alert.notification_sent
            })
        
        return JSONResponse(content={
            "success": True,
            "alerts": alerts_data,
            "total": len(alerts_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alerts")

@router.get("/alerts/summary")
async def get_alert_summary(monitoring = Depends(get_monitoring)):
    """Get alert summary"""
    try:
        summary = monitoring.get_alert_summary()
        
        return JSONResponse(content={
            "success": True,
            "summary": summary
        })
        
    except Exception as e:
        logger.error(f"Error getting alert summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alert summary")

@router.post("/alerts/rules")
async def create_alert_rule(
    rule: AlertRuleRequest,
    monitoring = Depends(get_monitoring)
):
    """Create a new alert rule"""
    try:
        from monitoring.infrastructure import AlertRule
        import uuid
        
        alert_rule = AlertRule(
            rule_id=f"rule_{uuid.uuid4().hex[:8]}",
            name=rule.name,
            metric_name=rule.metric_name,
            condition=rule.condition,
            threshold=rule.threshold,
            duration=rule.duration,
            severity=rule.severity,
            enabled=rule.enabled,
            notification_channels=rule.notification_channels,
            description=rule.description
        )
        
        monitoring.alert_manager.add_alert_rule(alert_rule)
        
        return JSONResponse(content={
            "success": True,
            "rule_id": alert_rule.rule_id,
            "message": "Alert rule created successfully"
        })
        
    except Exception as e:
        logger.error(f"Error creating alert rule: {e}")
        raise HTTPException(status_code=500, detail="Failed to create alert rule")

@router.get("/alerts/rules")
async def get_alert_rules(monitoring = Depends(get_monitoring)):
    """Get all alert rules"""
    try:
        rules_data = []
        for rule in monitoring.alert_manager.alert_rules.values():
            rules_data.append({
                "rule_id": rule.rule_id,
                "name": rule.name,
                "metric_name": rule.metric_name,
                "condition": rule.condition,
                "threshold": rule.threshold,
                "duration": rule.duration,
                "severity": rule.severity,
                "enabled": rule.enabled,
                "notification_channels": rule.notification_channels,
                "description": rule.description
            })
        
        return JSONResponse(content={
            "success": True,
            "rules": rules_data
        })
        
    except Exception as e:
        logger.error(f"Error getting alert rules: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alert rules")

@router.put("/alerts/rules/{rule_id}")
async def update_alert_rule(
    rule_id: str,
    rule: AlertRuleRequest,
    monitoring = Depends(get_monitoring)
):
    """Update an alert rule"""
    try:
        if rule_id not in monitoring.alert_manager.alert_rules:
            raise HTTPException(status_code=404, detail="Alert rule not found")
        
        from monitoring.infrastructure import AlertRule
        
        updated_rule = AlertRule(
            rule_id=rule_id,
            name=rule.name,
            metric_name=rule.metric_name,
            condition=rule.condition,
            threshold=rule.threshold,
            duration=rule.duration,
            severity=rule.severity,
            enabled=rule.enabled,
            notification_channels=rule.notification_channels,
            description=rule.description
        )
        
        monitoring.alert_manager.alert_rules[rule_id] = updated_rule
        
        return JSONResponse(content={
            "success": True,
            "message": "Alert rule updated successfully"
        })
        
    except Exception as e:
        logger.error(f"Error updating alert rule: {e}")
        raise HTTPException(status_code=500, detail="Failed to update alert rule")

@router.delete("/alerts/rules/{rule_id}")
async def delete_alert_rule(
    rule_id: str,
    monitoring = Depends(get_monitoring)
):
    """Delete an alert rule"""
    try:
        monitoring.alert_manager.remove_alert_rule(rule_id)
        
        return JSONResponse(content={
            "success": True,
            "message": "Alert rule deleted successfully"
        })
        
    except Exception as e:
        logger.error(f"Error deleting alert rule: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete alert rule")

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    request: AlertAcknowledgeRequest,
    monitoring = Depends(get_monitoring)
):
    """Acknowledge an alert"""
    try:
        success = monitoring.alert_manager.acknowledge_alert(alert_id, request.admin_id)
        
        if success:
            return JSONResponse(content={
                "success": True,
                "message": "Alert acknowledged successfully"
            })
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
        
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to acknowledge alert")

@router.get("/dashboard")
async def get_dashboard_data(monitoring = Depends(get_monitoring)):
    """Get comprehensive dashboard data"""
    try:
        # Get system metrics
        system_metrics = monitoring.get_system_metrics("1h")
        
        # Get API metrics
        api_metrics = monitoring.get_api_metrics("1h")
        
        # Get alert summary
        alert_summary = monitoring.get_alert_summary()
        
        # Get recent alerts
        recent_alerts = monitoring.alert_manager.get_alert_history(10)
        
        # Get latency statistics
        latency_stats = {}
        for endpoint in monitoring.performance_tracker.api_latencies:
            stats = monitoring.performance_tracker.get_api_latency_stats(endpoint)
            if stats:
                latency_stats[endpoint] = stats
        
        dashboard_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system_metrics": system_metrics,
            "api_metrics": api_metrics,
            "alert_summary": alert_summary,
            "recent_alerts": [{
                "alert_id": alert.alert_id,
                "rule_id": alert.rule_id,
                "severity": alert.severity,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "status": alert.status
            } for alert in recent_alerts],
            "latency_stats": latency_stats,
            "monitoring_status": {
                "active": monitoring.monitoring_active,
                "influxdb_connected": True  # TODO: Check actual connection status
            }
        }
        
        return JSONResponse(content={
            "success": True,
            "data": dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard data")

@router.post("/start")
async def start_monitoring(
    system_interval: int = Body(60, description="System monitoring interval in seconds"),
    metrics_interval: int = Body(30, description="Metrics flush interval in seconds"),
    monitoring = Depends(get_monitoring)
):
    """Start monitoring"""
    try:
        monitoring.start_monitoring(system_interval, metrics_interval)
        
        return JSONResponse(content={
            "success": True,
            "message": "Monitoring started successfully"
        })
        
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise HTTPException(status_code=500, detail="Failed to start monitoring")

@router.post("/stop")
async def stop_monitoring(monitoring = Depends(get_monitoring)):
    """Stop monitoring"""
    try:
        monitoring.stop_monitoring()
        
        return JSONResponse(content={
            "success": True,
            "message": "Monitoring stopped successfully"
        })
        
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop monitoring")

@router.get("/status")
async def get_monitoring_status(monitoring = Depends(get_monitoring)):
    """Get monitoring status"""
    try:
        status = {
            "monitoring_active": monitoring.monitoring_active,
            "system_monitoring": monitoring.system_monitor.monitoring,
            "metrics_buffer_size": len(monitoring.performance_tracker.metrics_buffer),
            "active_alerts": len(monitoring.alert_manager.get_active_alerts()),
            "total_alert_rules": len(monitoring.alert_manager.alert_rules),
            "influxdb_bucket": monitoring.influxdb_manager.bucket,
            "influxdb_org": monitoring.influxdb_manager.org
        }
        
        return JSONResponse(content={
            "success": True,
            "status": status
        })
        
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get monitoring status")
