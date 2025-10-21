"""
Admin Notification System
Real-time notifications for admin users
"""

import os
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List
import logging
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class NotificationType(Enum):
    """Notification types"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SECURITY = "security"
    SYSTEM = "system"

class NotificationConfig:
    """Notification configuration"""

    def __init__(self):
        self.max_notifications_per_user = int(os.getenv("MAX_NOTIFICATIONS_PER_USER", "100"))
        self.notification_ttl = int(os.getenv("NOTIFICATION_TTL", "86400"))  # 24 hours
        self.enable_notification_grouping = os.getenv("ENABLE_NOTIFICATION_GROUPING", "true").lower() == "true"
        self.grouping_window_minutes = int(os.getenv("NOTIFICATION_GROUPING_WINDOW", "5"))
        self.enable_sound_notifications = os.getenv("ENABLE_SOUND_NOTIFICATIONS", "true").lower() == "true"
        self.enable_desktop_notifications = os.getenv("ENABLE_DESKTOP_NOTIFICATIONS", "true").lower() == "true"

class Notification:
    """Admin notification container"""

    def __init__(self, notification_id: str, user_id: str, title: str, message: str,
                 notification_type: str = NotificationType.INFO.value,
                 priority: str = NotificationPriority.MEDIUM.value):
        self.notification_id = notification_id
        self.user_id = user_id
        self.title = title
        self.message = message
        self.notification_type = notification_type
        self.priority = priority
        self.created_at = datetime.now(timezone.utc)

        # Notification state
        self.is_read = False
        self.read_at = None
        self.is_archived = False
        self.archived_at = None

        # Notification metadata
        self.source = "system"
        self.category = "general"
        self.tags = []
        self.actions = []
        self.expires_at = self.created_at + timedelta(seconds=self._get_notification_ttl())

        # Display settings
        self.sound_enabled = self._should_play_sound()
        self.desktop_notification = self._should_show_desktop()
        self.auto_dismiss = self._get_auto_dismiss_time()

    def _get_notification_ttl(self) -> int:
        """Get notification TTL based on priority"""
        ttl_map = {
            NotificationPriority.LOW.value: 3600,      # 1 hour
            NotificationPriority.MEDIUM.value: 7200,   # 2 hours
            NotificationPriority.HIGH.value: 21600,    # 6 hours
            NotificationPriority.CRITICAL.value: 86400 # 24 hours
        }
        return ttl_map.get(self.priority, 7200)

    def _should_play_sound(self) -> bool:
        """Check if sound should be played"""
        if not self._is_sound_enabled():
            return False

        # Play sound for high priority and above
        return self.priority in [NotificationPriority.HIGH.value, NotificationPriority.CRITICAL.value]

    def _should_show_desktop(self) -> bool:
        """Check if desktop notification should be shown"""
        if not self._is_desktop_enabled():
            return False

        # Show desktop for medium priority and above
        return self.priority in [NotificationPriority.MEDIUM.value, NotificationPriority.HIGH.value, NotificationPriority.CRITICAL.value]

    def _get_auto_dismiss_time(self) -> int:
        """Get auto-dismiss time in seconds"""
        dismiss_map = {
            NotificationPriority.LOW.value: 10,
            NotificationPriority.MEDIUM.value: 15,
            NotificationPriority.HIGH.value: 30,
            NotificationPriority.CRITICAL.value: 0  # Never auto-dismiss
        }
        return dismiss_map.get(self.priority, 15)

    def _is_sound_enabled(self) -> bool:
        """Check if sound notifications are enabled"""
        return os.getenv("ENABLE_SOUND_NOTIFICATIONS", "true").lower() == "true"

    def _is_desktop_enabled(self) -> bool:
        """Check if desktop notifications are enabled"""
        return os.getenv("ENABLE_DESKTOP_NOTIFICATIONS", "true").lower() == "true"

    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.now(timezone.utc)

    def mark_as_archived(self):
        """Mark notification as archived"""
        self.is_archived = True
        self.archived_at = datetime.now(timezone.utc)

    def is_expired(self) -> bool:
        """Check if notification is expired"""
        return datetime.now(timezone.utc) > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "notification_id": self.notification_id,
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "notification_type": self.notification_type,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "is_read": self.is_read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "is_archived": self.is_archived,
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
            "source": self.source,
            "category": self.category,
            "tags": self.tags,
            "actions": self.actions,
            "expires_at": self.expires_at.isoformat(),
            "sound_enabled": self.sound_enabled,
            "desktop_notification": self.desktop_notification,
            "auto_dismiss": self.auto_dismiss_time
        }

class NotificationManager:
    """Admin notification management"""

    def __init__(self, mongodb_connection=None, redis_client=None, event_broadcaster=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        self.event_broadcaster = event_broadcaster

        self.config = NotificationConfig()
        self.notifications: Dict[str, Notification] = {}  # notification_id -> notification
        self.user_notifications: Dict[str, List[str]] = defaultdict(list)  # user_id -> notification_ids

        # Notification grouping
        self.notification_groups: Dict[str, List[str]] = defaultdict(list)  # group_key -> notification_ids

    def create_notification(self, user_id: str, title: str, message: str,
                          notification_type: str = NotificationType.INFO.value,
                          priority: str = NotificationPriority.MEDIUM.value,
                          source: str = "system", category: str = "general",
                          tags: List[str] = None, actions: List[Dict[str, Any]] = None) -> str:
        """
        Create new notification

        Args:
            user_id: Target user ID
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            priority: Notification priority
            source: Notification source
            category: Notification category
            tags: Notification tags
            actions: Available actions

        Returns:
            Notification ID
        """
        try:
            notification_id = f"notif_{int(time.time())}_{secrets.token_hex(4)}"

            notification = Notification(
                notification_id=notification_id,
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                priority=priority
            )

            notification.source = source
            notification.category = category

            if tags:
                notification.tags = tags

            if actions:
                notification.actions = actions

            # Check notification limit for user
            if len(self.user_notifications[user_id]) >= self.config.max_notifications_per_user:
                self._cleanup_user_notifications(user_id)

            # Store notification
            self.notifications[notification_id] = notification
            self.user_notifications[user_id].append(notification_id)

            # Group notifications if enabled
            if self.config.enable_notification_grouping:
                self._group_notification(notification)

            # Store in database
            if self.mongodb:
                self._store_notification_in_db(notification)

            # Emit real-time notification event
            if self.event_broadcaster:
                self.event_broadcaster.emit_event(
                    "notification_created",
                    notification.to_dict(),
                    source="notification_system",
                    severity=priority,
                    target_audience=f"user:{user_id}",
                    tags=["notification", "realtime"]
                )

            logger.info(f"Notification created: {notification_id} for user: {user_id}")
            return notification_id

        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            return ""

    def _cleanup_user_notifications(self, user_id: str):
        """Clean up old notifications for user"""
        try:
            if user_id not in self.user_notifications:
                return

            notification_ids = self.user_notifications[user_id]

            # Remove expired notifications
            current_time = datetime.now(timezone.utc)
            active_notifications = []

            for notification_id in notification_ids:
                if notification_id in self.notifications:
                    notification = self.notifications[notification_id]

                    if not notification.is_expired():
                        active_notifications.append(notification_id)
                    else:
                        # Remove expired notification
                        del self.notifications[notification_id]

            # If still too many, remove oldest read notifications
            if len(active_notifications) >= self.config.max_notifications_per_user:
                read_notifications = [
                    nid for nid in active_notifications
                    if self.notifications[nid].is_read
                ]

                # Remove oldest read notifications
                read_notifications.sort(
                    key=lambda nid: self.notifications[nid].created_at
                )

                to_remove = read_notifications[:len(active_notifications) - self.config.max_notifications_per_user + 10]
                for notification_id in to_remove:
                    del self.notifications[notification_id]
                    active_notifications.remove(notification_id)

            self.user_notifications[user_id] = active_notifications

        except Exception as e:
            logger.error(f"Error cleaning up user notifications: {e}")

    def _group_notification(self, notification: Notification):
        """Group similar notifications"""
        try:
            # Create group key based on type, source, and category
            group_key = f"{notification.notification_type}_{notification.source}_{notification.category}"

            # Check for similar recent notifications
            recent_notifications = self.notification_groups.get(group_key, [])

            # Look for notifications in the last grouping window
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=self.config.grouping_window_minutes)

            similar_notifications = []
            for notification_id in recent_notifications:
                if notification_id in self.notifications:
                    existing_notification = self.notifications[notification_id]
                    if existing_notification.created_at >= cutoff_time:
                        similar_notifications.append(existing_notification)

            # If similar notifications found, group them
            if similar_notifications:
                # Update the most recent notification with count
                latest_notification = max(similar_notifications, key=lambda n: n.created_at)
                if "group_count" not in latest_notification.message:
                    latest_notification.message = f"{latest_notification.message} (2 notifications)"

                # Mark older notifications as grouped
                for old_notification in similar_notifications[:-1]:
                    if not old_notification.is_archived:
                        old_notification.mark_as_archived()

            # Add to group
            self.notification_groups[group_key].append(notification.notification_id)

        except Exception as e:
            logger.error(f"Error grouping notification: {e}")

    def get_user_notifications(self, user_id: str, include_read: bool = False,
                             include_archived: bool = False, limit: int = 50) -> List[Dict[str, Any]]:
        """Get notifications for user"""
        try:
            if user_id not in self.user_notifications:
                return []

            notification_ids = self.user_notifications[user_id]
            user_notifications = []

            for notification_id in notification_ids:
                if notification_id in self.notifications:
                    notification = self.notifications[notification_id]

                    # Filter based on parameters
                    if not include_read and notification.is_read:
                        continue
                    if not include_archived and notification.is_archived:
                        continue

                    user_notifications.append(notification.to_dict())

            # Sort by creation time (newest first) and limit
            user_notifications.sort(key=lambda n: n["created_at"], reverse=True)
            return user_notifications[:limit]

        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            return []

    def mark_notification_as_read(self, user_id: str, notification_id: str) -> bool:
        """Mark notification as read"""
        try:
            if notification_id not in self.notifications:
                return False

            notification = self.notifications[notification_id]

            # Check if notification belongs to user
            if notification.user_id != user_id:
                return False

            notification.mark_as_read()

            # Update in database
            if self.mongodb:
                self._update_notification_in_db(notification)

            logger.info(f"Notification marked as read: {notification_id}")
            return True

        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False

    def mark_all_notifications_as_read(self, user_id: str) -> int:
        """Mark all user notifications as read"""
        try:
            if user_id not in self.user_notifications:
                return 0

            notification_ids = self.user_notifications[user_id]
            marked_count = 0

            for notification_id in notification_ids:
                if notification_id in self.notifications:
                    notification = self.notifications[notification_id]

                    if not notification.is_read:
                        notification.mark_as_read()
                        marked_count += 1

            # Update in database
            if self.mongodb and marked_count > 0:
                self._batch_update_notifications_in_db(notification_ids)

            logger.info(f"Marked {marked_count} notifications as read for user: {user_id}")
            return marked_count

        except Exception as e:
            logger.error(f"Error marking all notifications as read: {e}")
            return 0

    def archive_notification(self, user_id: str, notification_id: str) -> bool:
        """Archive notification"""
        try:
            if notification_id not in self.notifications:
                return False

            notification = self.notifications[notification_id]

            # Check if notification belongs to user
            if notification.user_id != user_id:
                return False

            notification.mark_as_archived()

            # Update in database
            if self.mongodb:
                self._update_notification_in_db(notification)

            logger.info(f"Notification archived: {notification_id}")
            return True

        except Exception as e:
            logger.error(f"Error archiving notification: {e}")
            return False

    def delete_notification(self, user_id: str, notification_id: str) -> bool:
        """Delete notification"""
        try:
            if notification_id not in self.notifications:
                return False

            notification = self.notifications[notification_id]

            # Check if notification belongs to user
            if notification.user_id != user_id:
                return False

            # Remove from user notifications
            if user_id in self.user_notifications:
                self.user_notifications[user_id].remove(notification_id)

            # Remove from groups
            for group_notifications in self.notification_groups.values():
                if notification_id in group_notifications:
                    group_notifications.remove(notification_id)

            # Remove notification
            del self.notifications[notification_id]

            # Remove from database
            if self.mongodb:
                self._delete_notification_from_db(notification_id)

            logger.info(f"Notification deleted: {notification_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting notification: {e}")
            return False

    def get_unread_count(self, user_id: str) -> int:
        """Get unread notification count for user"""
        try:
            if user_id not in self.user_notifications:
                return 0

            notification_ids = self.user_notifications[user_id]

            unread_count = 0
            for notification_id in notification_ids:
                if notification_id in self.notifications:
                    notification = self.notifications[notification_id]

                    if not notification.is_read and not notification.is_archived:
                        unread_count += 1

            return unread_count

        except Exception as e:
            logger.error(f"Error getting unread count: {e}")
            return 0

    def get_notification_summary(self, user_id: str) -> Dict[str, Any]:
        """Get notification summary for user"""
        try:
            notifications = self.get_user_notifications(user_id, include_read=True, include_archived=False)

            # Count by priority
            priority_counts = {
                NotificationPriority.LOW.value: 0,
                NotificationPriority.MEDIUM.value: 0,
                NotificationPriority.HIGH.value: 0,
                NotificationPriority.CRITICAL.value: 0
            }

            # Count by type
            type_counts = {
                NotificationType.INFO.value: 0,
                NotificationType.SUCCESS.value: 0,
                NotificationType.WARNING.value: 0,
                NotificationType.ERROR.value: 0,
                NotificationType.SECURITY.value: 0,
                NotificationType.SYSTEM.value: 0
            }

            unread_count = 0

            for notification in notifications:
                priority = notification["priority"]
                if priority in priority_counts:
                    priority_counts[priority] += 1

                notification_type = notification["notification_type"]
                if notification_type in type_counts:
                    type_counts[notification_type] += 1

                if not notification["is_read"]:
                    unread_count += 1

            return {
                "user_id": user_id,
                "total_notifications": len(notifications),
                "unread_notifications": unread_count,
                "priority_distribution": priority_counts,
                "type_distribution": type_counts,
                "last_notification": notifications[0]["created_at"] if notifications else None,
                "summary_generated_at": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting notification summary: {e}")
            return {"error": "Failed to get summary"}

    def _store_notification_in_db(self, notification: Notification):
        """Store notification in database"""
        try:
            if not self.mongodb:
                return

            db = self.mongodb.get_database("zalopay_phishing")
            notifications_collection = db.admin_notifications

            document = notification.to_dict()
            document["expires_at"] = notification.expires_at

            notifications_collection.replace_one(
                {"notification_id": notification.notification_id},
                document,
                upsert=True
            )

        except Exception as e:
            logger.error(f"Error storing notification in database: {e}")

    def _update_notification_in_db(self, notification: Notification):
        """Update notification in database"""
        try:
            if not self.mongodb:
                return

            db = self.mongodb.get_database("zalopay_phishing")
            notifications_collection = db.admin_notifications

            update_data = {
                "is_read": notification.is_read,
                "read_at": notification.read_at,
                "is_archived": notification.is_archived,
                "archived_at": notification.archived_at,
                "updated_at": datetime.now(timezone.utc)
            }

            notifications_collection.update_one(
                {"notification_id": notification.notification_id},
                {"$set": update_data}
            )

        except Exception as e:
            logger.error(f"Error updating notification in database: {e}")

    def _batch_update_notifications_in_db(self, notification_ids: List[str]):
        """Batch update notifications in database"""
        try:
            if not self.mongodb:
                return

            db = self.mongodb.get_database("zalopay_phishing")
            notifications_collection = db.admin_notifications

            # Get current state of notifications
            notifications = notifications_collection.find(
                {"notification_id": {"$in": notification_ids}}
            )

            # Update each notification
            for notification_doc in notifications:
                notification_id = notification_doc["notification_id"]
                if notification_id in self.notifications:
                    notification = self.notifications[notification_id]

                    update_data = {
                        "is_read": notification.is_read,
                        "read_at": notification.read_at,
                        "is_archived": notification.is_archived,
                        "archived_at": notification.archived_at,
                        "updated_at": datetime.now(timezone.utc)
                    }

                    notifications_collection.update_one(
                        {"notification_id": notification_id},
                        {"$set": update_data}
                    }

        except Exception as e:
            logger.error(f"Error batch updating notifications in database: {e}")

    def _delete_notification_from_db(self, notification_id: str):
        """Delete notification from database"""
        try:
            if not self.mongodb:
                return

            db = self.mongodb.get_database("zalopay_phishing")
            notifications_collection = db.admin_notifications

            notifications_collection.delete_one({"notification_id": notification_id})

        except Exception as e:
            logger.error(f"Error deleting notification from database: {e}")

    def cleanup_expired_notifications(self) -> int:
        """Clean up expired notifications"""
        try:
            expired_notifications = []

            for notification_id, notification in self.notifications.items():
                if notification.is_expired():
                    expired_notifications.append(notification_id)

            for notification_id in expired_notifications:
                notification = self.notifications[notification_id]

                # Remove from user notifications
                if notification.user_id in self.user_notifications:
                    self.user_notifications[notification.user_id].remove(notification_id)

                # Remove from groups
                for group_notifications in self.notification_groups.values():
                    if notification_id in group_notifications:
                        group_notifications.remove(notification_id)

                # Remove notification
                del self.notifications[notification_id]

            if expired_notifications:
                logger.info(f"Cleaned up {len(expired_notifications)} expired notifications")

            return len(expired_notifications)

        except Exception as e:
            logger.error(f"Error cleaning up expired notifications: {e}")
            return 0

    def get_notification_statistics(self) -> Dict[str, Any]:
        """Get notification statistics"""
        try:
            total_notifications = len(self.notifications)

            # Count by status
            read_count = sum(1 for n in self.notifications.values() if n.is_read)
            archived_count = sum(1 for n in self.notifications.values() if n.is_archived)

            # Count by priority
            priority_counts = {
                NotificationPriority.LOW.value: 0,
                NotificationPriority.MEDIUM.value: 0,
                NotificationPriority.HIGH.value: 0,
                NotificationPriority.CRITICAL.value: 0
            }

            # Count by type
            type_counts = {
                NotificationType.INFO.value: 0,
                NotificationType.SUCCESS.value: 0,
                NotificationType.WARNING.value: 0,
                NotificationType.ERROR.value: 0,
                NotificationType.SECURITY.value: 0,
                NotificationType.SYSTEM.value: 0
            }

            for notification in self.notifications.values():
                priority = notification.priority
                if priority in priority_counts:
                    priority_counts[priority] += 1

                notification_type = notification.notification_type
                if notification_type in type_counts:
                    type_counts[notification_type] += 1

            return {
                "total_notifications": total_notifications,
                "read_notifications": read_count,
                "archived_notifications": archived_count,
                "unread_notifications": total_notifications - read_count,
                "priority_distribution": priority_counts,
                "type_distribution": type_counts,
                "active_users": len(self.user_notifications),
                "notification_groups": len(self.notification_groups),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting notification statistics: {e}")
            return {"error": "Failed to get statistics"}

# Global notification manager instance
notification_manager = None

def initialize_notification_manager(mongodb_connection=None, redis_client=None, event_broadcaster=None) -> NotificationManager:
    """Initialize global notification manager"""
    global notification_manager
    notification_manager = NotificationManager(mongodb_connection, redis_client, event_broadcaster)
    return notification_manager

def get_notification_manager() -> NotificationManager:
    """Get global notification manager"""
    if notification_manager is None:
        raise ValueError("Notification manager not initialized")
    return notification_manager

# Convenience functions
def create_notification(user_id: str, title: str, message: str,
                       notification_type: str = NotificationType.INFO.value,
                       priority: str = NotificationPriority.MEDIUM.value,
                       source: str = "system", category: str = "general",
                       tags: List[str] = None, actions: List[Dict[str, Any]] = None) -> str:
    """Create notification (global convenience function)"""
    return get_notification_manager().create_notification(
        user_id, title, message, notification_type, priority, source, category, tags, actions
    )

def get_user_notifications(user_id: str, include_read: bool = False, include_archived: bool = False,
                          limit: int = 50) -> List[Dict[str, Any]]:
    """Get user notifications (global convenience function)"""
    return get_notification_manager().get_user_notifications(user_id, include_read, include_archived, limit)

def mark_notification_as_read(user_id: str, notification_id: str) -> bool:
    """Mark notification as read (global convenience function)"""
    return get_notification_manager().mark_notification_as_read(user_id, notification_id)

def mark_all_notifications_as_read(user_id: str) -> int:
    """Mark all notifications as read (global convenience function)"""
    return get_notification_manager().mark_all_notifications_as_read(user_id)

def get_unread_count(user_id: str) -> int:
    """Get unread count (global convenience function)"""
    return get_notification_manager().get_unread_count(user_id)

def get_notification_summary(user_id: str) -> Dict[str, Any]:
    """Get notification summary (global convenience function)"""
    return get_notification_manager().get_notification_summary(user_id)

def get_notification_statistics() -> Dict[str, Any]:
    """Get notification statistics (global convenience function)"""
    return get_notification_manager().get_notification_statistics()