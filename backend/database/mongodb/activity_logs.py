"""
Activity Logs Model
Database operations for activity_logs collection
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from pymongo import MongoClient
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)

class ActivityLogModel:
    """Activity logs database operations"""

    def __init__(self, mongodb_client: Optional[MongoClient] = None):
        self.client = mongodb_client
        self.db = None
        self.collection = None

    async def connect(self, database_name: str = "zalopay_phishing"):
        """Connect to MongoDB"""
        try:
            if self.client:
                self.db = self.client[database_name]
                self.collection = self.db.activity_logs
                logger.info("Connected to activity_logs collection")
                return True
            return False
        except PyMongoError as e:
            logger.error(f"MongoDB connection error: {e}")
            return False

    async def create_activity_log(self, log_data: Dict[str, Any]) -> Optional[str]:
        """Create a new activity log"""
        try:
            if not self.collection:
                await self.connect()

            # Add metadata
            log_data["timestamp"] = datetime.now(timezone.utc)
            log_data["created_at"] = datetime.now(timezone.utc)
            
            # Insert document
            result = self.collection.insert_one(log_data)
            
            if result.inserted_id:
                logger.info(f"Activity log created: {result.inserted_id}")
                return str(result.inserted_id)
            else:
                logger.error("Failed to create activity log")
                return None

        except PyMongoError as e:
            logger.error(f"Error creating activity log: {e}")
            return None

    async def get_activity_log_by_id(self, log_id: str) -> Optional[Dict[str, Any]]:
        """Get activity log by ID"""
        try:
            if not self.collection:
                await self.connect()

            log = self.collection.find_one({"_id": log_id})
            
            if log:
                log["_id"] = str(log["_id"])
                return log
            
            return None

        except PyMongoError as e:
            logger.error(f"Error getting activity log by ID: {e}")
            return None

    async def get_activity_logs_paginated(self, page: int, limit: int, sort_by: str, 
                                        sort_order: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get paginated activity logs"""
        try:
            if not self.collection:
                await self.connect()

            # Calculate sort direction
            sort_direction = -1 if sort_order == "desc" else 1
            sort_spec = [(sort_by, sort_direction)]

            # Calculate skip
            skip = (page - 1) * limit

            # Get activity logs
            logs = list(self.collection.find(
                filters,
                sort=sort_spec,
                skip=skip,
                limit=limit
            ))

            # Convert ObjectId to string
            for log in logs:
                log["_id"] = str(log["_id"])

            return logs

        except PyMongoError as e:
            logger.error(f"Error getting paginated activity logs: {e}")
            return []

    async def search_activity_logs(self, query: str, filters: Dict[str, Any], 
                                 sort_by: str, sort_order: str, page: int, limit: int) -> Dict[str, Any]:
        """Search activity logs with text search"""
        try:
            if not self.collection:
                await self.connect()

            # Build search query
            search_query = {"$text": {"$search": query}} if query else {}
            
            # Combine with filters
            if filters:
                search_query.update(filters)

            # Calculate sort direction
            sort_direction = -1 if sort_order == "desc" else 1
            sort_spec = [(sort_by, sort_direction)]

            # Calculate skip
            skip = (page - 1) * limit

            # Get activity logs
            logs = list(self.collection.find(
                search_query,
                sort=sort_spec,
                skip=skip,
                limit=limit
            ))

            # Convert ObjectId to string
            for log in logs:
                log["_id"] = str(log["_id"])

            # Get total count
            total_count = self.collection.count_documents(search_query)

            return {
                "logs": logs,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total_count,
                    "pages": (total_count + limit - 1) // limit
                }
            }

        except PyMongoError as e:
            logger.error(f"Error searching activity logs: {e}")
            return {"logs": [], "pagination": {"page": page, "limit": limit, "total": 0, "pages": 0}}

    async def get_activity_logs_by_admin_id(self, admin_id: str, page: int, limit: int) -> List[Dict[str, Any]]:
        """Get activity logs by admin ID"""
        try:
            if not self.collection:
                await self.connect()

            # Calculate skip
            skip = (page - 1) * limit

            # Get activity logs
            logs = list(self.collection.find(
                {"actor.admin_id": admin_id},
                sort=[("timestamp", -1)],
                skip=skip,
                limit=limit
            ))

            # Convert ObjectId to string
            for log in logs:
                log["_id"] = str(log["_id"])

            return logs

        except PyMongoError as e:
            logger.error(f"Error getting activity logs by admin ID: {e}")
            return []

    async def count_activity_logs(self, filters: Dict[str, Any] = None) -> int:
        """Count activity logs"""
        try:
            if not self.collection:
                await self.connect()

            count = self.collection.count_documents(filters or {})
            return count

        except PyMongoError as e:
            logger.error(f"Error counting activity logs: {e}")
            return 0

    async def count_activity_logs_by_admin_id(self, admin_id: str) -> int:
        """Count activity logs by admin ID"""
        return await self.count_activity_logs({"actor.admin_id": admin_id})

    async def count_activities_since(self, start_time: datetime) -> int:
        """Count activities since start_time"""
        return await self.count_activity_logs({"timestamp": {"$gte": start_time}})

    async def get_activities_by_type_since(self, start_time: datetime) -> Dict[str, int]:
        """Get activities by type since start_time"""
        try:
            if not self.collection:
                await self.connect()

            pipeline = [
                {"$match": {"timestamp": {"$gte": start_time}}},
                {
                    "$group": {
                        "_id": "$action_type",
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"count": -1}}
            ]

            result = list(self.collection.aggregate(pipeline))
            return {item["_id"] or "unknown": item["count"] for item in result}

        except PyMongoError as e:
            logger.error(f"Error getting activities by type: {e}")
            return {}

    async def get_activities_by_admin_since(self, start_time: datetime) -> Dict[str, int]:
        """Get activities by admin since start_time"""
        try:
            if not self.collection:
                await self.connect()

            pipeline = [
                {"$match": {"timestamp": {"$gte": start_time}}},
                {
                    "$group": {
                        "_id": "$actor.admin_id",
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"count": -1}}
            ]

            result = list(self.collection.aggregate(pipeline))
            return {item["_id"] or "unknown": item["count"] for item in result}

        except PyMongoError as e:
            logger.error(f"Error getting activities by admin: {e}")
            return {}

    async def get_activities_by_severity_since(self, start_time: datetime) -> Dict[str, int]:
        """Get activities by severity since start_time"""
        try:
            if not self.collection:
                await self.connect()

            pipeline = [
                {"$match": {"timestamp": {"$gte": start_time}}},
                {
                    "$group": {
                        "_id": "$severity_level",
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"count": -1}}
            ]

            result = list(self.collection.aggregate(pipeline))
            return {item["_id"] or "unknown": item["count"] for item in result}

        except PyMongoError as e:
            logger.error(f"Error getting activities by severity: {e}")
            return {}

    async def get_activity_trends(self, start_time: datetime, end_time: datetime, 
                                granularity: str) -> List[Dict[str, Any]]:
        """Get activity trends over time"""
        try:
            if not self.collection:
                await self.connect()

            # Determine date format based on granularity
            if granularity == "hourly":
                date_format = "%Y-%m-%d %H:00:00"
                group_format = {
                    "year": {"$year": "$timestamp"},
                    "month": {"$month": "$timestamp"},
                    "day": {"$dayOfMonth": "$timestamp"},
                    "hour": {"$hour": "$timestamp"}
                }
            elif granularity == "daily":
                date_format = "%Y-%m-%d"
                group_format = {
                    "year": {"$year": "$timestamp"},
                    "month": {"$month": "$timestamp"},
                    "day": {"$dayOfMonth": "$timestamp"}
                }
            else:  # weekly
                date_format = "%Y-W%U"
                group_format = {
                    "year": {"$year": "$timestamp"},
                    "week": {"$week": "$timestamp"}
                }

            pipeline = [
                {"$match": {"timestamp": {"$gte": start_time, "$lte": end_time}}},
                {
                    "$group": {
                        "_id": group_format,
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"_id": 1}}
            ]

            result = list(self.collection.aggregate(pipeline))
            
            # Format results
            trends_data = []
            for item in result:
                trends_data.append({
                    "period": item["_id"],
                    "count": item["count"]
                })

            return trends_data

        except PyMongoError as e:
            logger.error(f"Error getting activity trends: {e}")
            return []

    async def get_recent_activities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent activities"""
        try:
            if not self.collection:
                await self.connect()

            activities = list(self.collection.find(
                {},
                sort=[("timestamp", -1)],
                limit=limit
            ))

            # Convert ObjectId to string
            for activity in activities:
                activity["_id"] = str(activity["_id"])

            return activities

        except PyMongoError as e:
            logger.error(f"Error getting recent activities: {e}")
            return []

    async def cleanup_old_logs(self, days_to_keep: int) -> int:
        """Clean up old activity logs"""
        try:
            if not self.collection:
                await self.connect()

            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
            
            result = self.collection.delete_many({
                "timestamp": {"$lt": cutoff_date}
            })

            deleted_count = result.deleted_count
            logger.info(f"Cleaned up {deleted_count} old activity logs")
            return deleted_count

        except PyMongoError as e:
            logger.error(f"Error cleaning up old logs: {e}")
            return 0

    async def health_check(self) -> bool:
        """Health check for activity logs collection"""
        try:
            if not self.collection:
                await self.connect()

            # Test basic operations
            self.collection.find_one()
            return True

        except PyMongoError as e:
            logger.error(f"Activity logs health check failed: {e}")
            return False