"""
Real-Time Event Broadcasting
Broadcast real-time events to WebSocket clients
"""

import os
import json
import time
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Callable
import logging
import threading
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventConfig:
    """Event broadcasting configuration"""

    def __init__(self):
        self.event_buffer_size = int(os.getenv("EVENT_BUFFER_SIZE", "1000"))
        self.event_ttl = int(os.getenv("EVENT_TTL", "3600"))  # 1 hour
        self.enable_event_filtering = os.getenv("ENABLE_EVENT_FILTERING", "true").lower() == "true"
        self.enable_event_compression = os.getenv("ENABLE_EVENT_COMPRESSION", "true").lower() == "true"
        self.max_events_per_second = int(os.getenv("MAX_EVENTS_PER_SECOND", "100"))

class Event:
    """Real-time event container"""

    def __init__(self, event_type: str, data: Any, source: str = "system",
                 severity: str = "info", target_audience: str = "all"):
        self.event_id = f"evt_{int(time.time())}_{secrets.token_hex(4)}"
        self.event_type = event_type
        self.data = data
        self.source = source
        self.severity = severity
        self.target_audience = target_audience
        self.timestamp = datetime.now(timezone.utc)

        # Event metadata
        self.tags = []
        self.priority = self._calculate_priority()
        self.expires_at = self.timestamp + timedelta(seconds=self._get_event_ttl())

    def _calculate_priority(self) -> int:
        """Calculate event priority"""
        priority_map = {
            "critical": 100,
            "high": 75,
            "medium": 50,
            "low": 25,
            "info": 10
        }
        return priority_map.get(self.severity, 10)

    def _get_event_ttl(self) -> int:
        """Get event TTL based on severity"""
        ttl_map = {
            "critical": 7200,  # 2 hours
            "high": 3600,      # 1 hour
            "medium": 1800,    # 30 minutes
            "low": 900,        # 15 minutes
            "info": 300        # 5 minutes
        }
        return ttl_map.get(self.severity, 300)

    def is_expired(self) -> bool:
        """Check if event is expired"""
        return datetime.now(timezone.utc) > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "data": self.data,
            "source": self.source,
            "severity": self.severity,
            "target_audience": self.target_audience,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "priority": self.priority,
            "expires_at": self.expires_at.isoformat()
        }

class EventFilter:
    """Event filtering criteria"""

    def __init__(self):
        self.event_types = []
        self.severities = []
        self.sources = []
        self.target_audiences = []
        self.tags = []
        self.min_priority = 0
        self.max_age_seconds = None

    def matches(self, event: Event) -> bool:
        """Check if event matches filter"""
        try:
            # Check event type
            if self.event_types and event.event_type not in self.event_types:
                return False

            # Check severity
            if self.severities and event.severity not in self.severities:
                return False

            # Check source
            if self.sources and event.source not in self.sources:
                return False

            # Check target audience
            if self.target_audiences and event.target_audience not in self.target_audiences:
                return False

            # Check tags
            if self.tags and not any(tag in event.tags for tag in self.tags):
                return False

            # Check priority
            if event.priority < self.min_priority:
                return False

            # Check age
            if self.max_age_seconds:
                age = (datetime.now(timezone.utc) - event.timestamp).total_seconds()
                if age > self.max_age_seconds:
                    return False

            return True

        except Exception as e:
            logger.error(f"Error checking event filter: {e}")
            return False

class EventBroadcaster:
    """Real-time event broadcasting engine"""

    def __init__(self, connection_manager=None):
        self.connection_manager = connection_manager

        self.config = EventConfig()
        self.events: List[Event] = []
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self.event_buffer: List[Event] = []

        # Rate limiting
        self.event_timestamps: List[float] = []
        self.rate_limit_window = 1.0  # 1 second

        # Start event processing
        self._start_event_processor()

    def _start_event_processor(self):
        """Start event processing thread"""
        processor_thread = threading.Thread(target=self._process_events, daemon=True)
        processor_thread.start()

    def _process_events(self):
        """Process events for broadcasting"""
        while True:
            try:
                # Process pending events
                if self.event_buffer:
                    events_to_process = self.event_buffer.copy()
                    self.event_buffer.clear()

                    for event in events_to_process:
                        self._broadcast_event(event)

                time.sleep(0.1)  # Process every 100ms

            except Exception as e:
                logger.error(f"Error in event processor: {e}")
                time.sleep(1)

    def _broadcast_event(self, event: Event):
        """Broadcast event to subscribers"""
        try:
            if not self.connection_manager:
                return

            # Check rate limits
            if not self._check_rate_limit():
                logger.warning("Event rate limit exceeded, dropping event")
                return

            # Add to events list
            self.events.append(event)

            # Limit events list size
            if len(self.events) > self.config.event_buffer_size:
                self.events = self.events[-self.config.event_buffer_size:]

            # Broadcast based on target audience
            if event.target_audience == "all":
                # Broadcast to all authenticated connections
                sent_count = 0
                for connection in self.connection_manager.connections.values():
                    if connection.is_authenticated:
                        if self.connection_manager.send_to_connection(connection.connection_id, event.to_dict()):
                            sent_count += 1

            elif event.target_audience == "admins":
                # Broadcast to admin users only
                sent_count = 0
                for connection in self.connection_manager.connections.values():
                    if connection.is_authenticated and connection.user_role in ["admin", "super_admin"]:
                        if self.connection_manager.send_to_connection(connection.connection_id, event.to_dict()):
                            sent_count += 1

            elif event.target_audience.startswith("role:"):
                # Broadcast to specific role
                target_role = event.target_audience[5:]  # Remove "role:" prefix
                sent_count = 0
                for connection in self.connection_manager.connections.values():
                    if connection.is_authenticated and connection.user_role == target_role:
                        if self.connection_manager.send_to_connection(connection.connection_id, event.to_dict()):
                            sent_count += 1

            elif event.target_audience.startswith("user:"):
                # Broadcast to specific user
                target_user = event.target_audience[5:]  # Remove "user:" prefix
                sent_count = self.connection_manager.send_to_user(target_user, event.to_dict())

            else:
                # Broadcast to specific channel
                sent_count = self.connection_manager.broadcast_to_channel(event.target_audience, event.to_dict())

            logger.info(f"Event broadcast: {event.event_type} to {sent_count} connections")

        except Exception as e:
            logger.error(f"Error broadcasting event: {e}")

    def _check_rate_limit(self) -> bool:
        """Check event rate limit"""
        try:
            current_time = time.time()

            # Clean old timestamps
            self.event_timestamps = [
                ts for ts in self.event_timestamps
                if current_time - ts < self.rate_limit_window
            ]

            # Check limit
            if len(self.event_timestamps) >= self.config.max_events_per_second:
                return False

            # Add current timestamp
            self.event_timestamps.append(current_time)
            return True

        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return False

    def emit_event(self, event_type: str, data: Any, source: str = "system",
                  severity: str = "info", target_audience: str = "all",
                  tags: List[str] = None) -> str:
        """
        Emit real-time event

        Args:
            event_type: Type of event
            data: Event data
            source: Event source
            severity: Event severity
            target_audience: Target audience
            tags: Event tags

        Returns:
            Event ID
        """
        try:
            event = Event(event_type, data, source, severity, target_audience)

            if tags:
                event.tags = tags

            # Add to buffer for processing
            self.event_buffer.append(event)

            logger.info(f"Event emitted: {event_type} - {severity}")
            return event.event_id

        except Exception as e:
            logger.error(f"Error emitting event: {e}")
            return ""

    def register_event_handler(self, event_type: str, handler: Callable):
        """Register event handler"""
        try:
            self.event_handlers[event_type].append(handler)
            logger.info(f"Event handler registered for: {event_type}")

        except Exception as e:
            logger.error(f"Error registering event handler: {e}")

    def unregister_event_handler(self, event_type: str, handler: Callable):
        """Unregister event handler"""
        try:
            if event_type in self.event_handlers:
                self.event_handlers[event_type].remove(handler)
                logger.info(f"Event handler unregistered for: {event_type}")

        except Exception as e:
            logger.error(f"Error unregistering event handler: {e}")

    def get_recent_events(self, limit: int = 50, event_filter: EventFilter = None) -> List[Dict[str, Any]]:
        """Get recent events"""
        try:
            # Filter events
            filtered_events = self.events

            if event_filter:
                filtered_events = [event for event in filtered_events if event_filter.matches(event)]

            # Sort by timestamp (newest first) and limit
            filtered_events.sort(key=lambda e: e.timestamp, reverse=True)
            recent_events = filtered_events[:limit]

            return [event.to_dict() for event in recent_events]

        except Exception as e:
            logger.error(f"Error getting recent events: {e}")
            return []

    def get_events_by_type(self, event_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get events by type"""
        try:
            type_events = [event for event in self.events if event.event_type == event_type]
            type_events.sort(key=lambda e: e.timestamp, reverse=True)
            recent_events = type_events[:limit]

            return [event.to_dict() for event in recent_events]

        except Exception as e:
            logger.error(f"Error getting events by type: {e}")
            return []

    def cleanup_expired_events(self) -> int:
        """Clean up expired events"""
        try:
            expired_count = 0
            current_time = datetime.now(timezone.utc)

            # Remove expired events
            self.events = [
                event for event in self.events
                if not event.is_expired()
            ]

            logger.info(f"Cleaned up {expired_count} expired events")
            return expired_count

        except Exception as e:
            logger.error(f"Error cleaning up expired events: {e}")
            return 0

    def get_event_statistics(self) -> Dict[str, Any]:
        """Get event broadcasting statistics"""
        try:
            # Event type distribution
            event_types = {}
            for event in self.events:
                event_type = event.event_type
                event_types[event_type] = event_types.get(event_type, 0) + 1

            # Severity distribution
            severities = {}
            for event in self.events:
                severity = event.severity
                severities[severity] = severities.get(severity, 0) + 1

            # Source distribution
            sources = {}
            for event in self.events:
                source = event.source
                sources[source] = sources.get(source, 0) + 1

            # Calculate rates
            current_time = time.time()
            recent_events = [
                event for event in self.events
                if (current_time - event.timestamp.timestamp()) < 60  # Last minute
            ]

            return {
                "total_events": len(self.events),
                "events_last_minute": len(recent_events),
                "event_types": event_types,
                "severities": severities,
                "sources": sources,
                "buffer_size": len(self.event_buffer),
                "registered_handlers": len(self.event_handlers),
                "events_per_second": len(recent_events) / 60.0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting event statistics: {e}")
            return {"error": "Failed to get statistics"}

class SystemEventEmitter:
    """System event emitter for common events"""

    def __init__(self, event_broadcaster: EventBroadcaster):
        self.event_broadcaster = event_broadcaster

    def emit_victim_acquired(self, victim_id: str, acquisition_method: str, victim_data: Dict[str, Any] = None):
        """Emit victim acquired event"""
        event_data = {
            "victim_id": victim_id,
            "acquisition_method": acquisition_method,
            "victim_data": victim_data or {}
        }

        return self.event_broadcaster.emit_event(
            "victim_acquired",
            event_data,
            source="victim_acquisition",
            severity="medium",
            target_audience="admins",
            tags=["victim", "acquisition"]
        )

    def emit_gmail_access_obtained(self, victim_id: str, access_level: str, capabilities: List[str]):
        """Emit Gmail access obtained event"""
        event_data = {
            "victim_id": victim_id,
            "access_level": access_level,
            "capabilities": capabilities
        }

        return self.event_broadcaster.emit_event(
            "gmail_access_obtained",
            event_data,
            source="gmail_exploitation",
            severity="high",
            target_audience="admins",
            tags=["gmail", "access", "exploitation"]
        )

    def emit_beef_hook_established(self, victim_id: str, hook_type: str, browser_info: Dict[str, Any]):
        """Emit BeEF hook established event"""
        event_data = {
            "victim_id": victim_id,
            "hook_type": hook_type,
            "browser_info": browser_info
        }

        return self.event_broadcaster.emit_event(
            "beef_hook_established",
            event_data,
            source="beef_exploitation",
            severity="high",
            target_audience="admins",
            tags=["beef", "hook", "browser"]
        )

    def emit_campaign_status_changed(self, campaign_id: str, old_status: str, new_status: str, details: Dict[str, Any] = None):
        """Emit campaign status changed event"""
        event_data = {
            "campaign_id": campaign_id,
            "old_status": old_status,
            "new_status": new_status,
            "details": details or {}
        }

        severity = "medium"
        if new_status in ["active", "completed"]:
            severity = "high"
        elif new_status == "failed":
            severity = "critical"

        return self.event_broadcaster.emit_event(
            "campaign_status_changed",
            event_data,
            source="campaign_management",
            severity=severity,
            target_audience="admins",
            tags=["campaign", "status_change"]
        )

    def emit_security_alert(self, alert_type: str, severity: str, message: str, details: Dict[str, Any] = None):
        """Emit security alert event"""
        event_data = {
            "alert_type": alert_type,
            "message": message,
            "details": details or {}
        }

        return self.event_broadcaster.emit_event(
            "security_alert",
            event_data,
            source="security_system",
            severity=severity,
            target_audience="admins",
            tags=["security", "alert"]
        )

    def emit_system_metric_update(self, metric_name: str, value: Any, threshold: float = None):
        """Emit system metric update event"""
        event_data = {
            "metric_name": metric_name,
            "value": value,
            "threshold": threshold
        }

        # Determine severity based on threshold
        severity = "info"
        if threshold:
            if isinstance(value, (int, float)):
                if value > threshold * 1.5:
                    severity = "warning"
                elif value > threshold * 2.0:
                    severity = "critical"

        return self.event_broadcaster.emit_event(
            "system_metric_update",
            event_data,
            source="system_monitoring",
            severity=severity,
            target_audience="admins",
            tags=["system", "metrics"]
        )

    def emit_data_exfiltration(self, victim_id: str, data_type: str, data_size: int, risk_level: str):
        """Emit data exfiltration event"""
        event_data = {
            "victim_id": victim_id,
            "data_type": data_type,
            "data_size": data_size,
            "risk_level": risk_level
        }

        # Determine severity based on risk level
        severity_map = {
            "low": "medium",
            "medium": "high",
            "high": "critical"
        }
        severity = severity_map.get(risk_level, "medium")

        return self.event_broadcaster.emit_event(
            "data_exfiltration",
            event_data,
            source="data_exploitation",
            severity=severity,
            target_audience="admins",
            tags=["data", "exfiltration", "risk"]
        )

# Global event broadcaster instance
event_broadcaster = None

def initialize_event_broadcaster(connection_manager=None) -> EventBroadcaster:
    """Initialize global event broadcaster"""
    global event_broadcaster
    event_broadcaster = EventBroadcaster(connection_manager)
    return event_broadcaster

def get_event_broadcaster() -> EventBroadcaster:
    """Get global event broadcaster"""
    if event_broadcaster is None:
        raise ValueError("Event broadcaster not initialized")
    return event_broadcaster

# Convenience functions
def emit_event(event_type: str, data: Any, source: str = "system", severity: str = "info",
              target_audience: str = "all", tags: List[str] = None) -> str:
    """Emit event (global convenience function)"""
    return get_event_broadcaster().emit_event(event_type, data, source, severity, target_audience, tags)

def get_recent_events(limit: int = 50, event_filter: EventFilter = None) -> List[Dict[str, Any]]:
    """Get recent events (global convenience function)"""
    return get_event_broadcaster().get_recent_events(limit, event_filter)

def get_events_by_type(event_type: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get events by type (global convenience function)"""
    return get_event_broadcaster().get_events_by_type(event_type, limit)

def get_event_statistics() -> Dict[str, Any]:
    """Get event statistics (global convenience function)"""
    return get_event_broadcaster().get_event_statistics()

# System event emitters
system_event_emitter = None

def initialize_system_event_emitter(event_broadcaster: EventBroadcaster) -> SystemEventEmitter:
    """Initialize global system event emitter"""
    global system_event_emitter
    system_event_emitter = SystemEventEmitter(event_broadcaster)
    return system_event_emitter

def get_system_event_emitter() -> SystemEventEmitter:
    """Get global system event emitter"""
    if system_event_emitter is None:
        raise ValueError("System event emitter not initialized")
    return system_event_emitter

# System event convenience functions
def emit_victim_acquired(victim_id: str, acquisition_method: str, victim_data: Dict[str, Any] = None) -> str:
    """Emit victim acquired event (global convenience function)"""
    return get_system_event_emitter().emit_victim_acquired(victim_id, acquisition_method, victim_data)

def emit_gmail_access_obtained(victim_id: str, access_level: str, capabilities: List[str]) -> str:
    """Emit Gmail access obtained event (global convenience function)"""
    return get_system_event_emitter().emit_gmail_access_obtained(victim_id, access_level, capabilities)

def emit_beef_hook_established(victim_id: str, hook_type: str, browser_info: Dict[str, Any]) -> str:
    """Emit BeEF hook established event (global convenience function)"""
    return get_system_event_emitter().emit_beef_hook_established(victim_id, hook_type, browser_info)

def emit_campaign_status_changed(campaign_id: str, old_status: str, new_status: str, details: Dict[str, Any] = None) -> str:
    """Emit campaign status changed event (global convenience function)"""
    return get_system_event_emitter().emit_campaign_status_changed(campaign_id, old_status, new_status, details)

def emit_security_alert(alert_type: str, severity: str, message: str, details: Dict[str, Any] = None) -> str:
    """Emit security alert event (global convenience function)"""
    return get_system_event_emitter().emit_security_alert(alert_type, severity, message, details)

def emit_system_metric_update(metric_name: str, value: Any, threshold: float = None) -> str:
    """Emit system metric update event (global convenience function)"""
    return get_system_event_emitter().emit_system_metric_update(metric_name, value, threshold)

def emit_data_exfiltration(victim_id: str, data_type: str, data_size: int, risk_level: str) -> str:
    """Emit data exfiltration event (global convenience function)"""
    return get_system_event_emitter().emit_data_exfiltration(victim_id, data_type, data_size, risk_level)