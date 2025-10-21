"""
Campaigns Model
Database operations for campaigns collection
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from pymongo import MongoClient
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)

class CampaignModel:
    """Campaigns database operations"""

    def __init__(self, mongodb_client: Optional[MongoClient] = None):
        self.client = mongodb_client
        self.db = None
        self.collection = None

    async def connect(self, database_name: str = "zalopay_phishing"):
        """Connect to MongoDB"""
        try:
            if self.client:
                self.db = self.client[database_name]
                self.collection = self.db.campaigns
                logger.info("Connected to campaigns collection")
                return True
            return False
        except PyMongoError as e:
            logger.error(f"MongoDB connection error: {e}")
            return False

    async def create_campaign(self, campaign_data: Dict[str, Any]) -> Optional[str]:
        """Create a new campaign"""
        try:
            if not self.collection:
                await self.connect()

            # Add metadata
            campaign_data["created_at"] = datetime.now(timezone.utc)
            campaign_data["updated_at"] = datetime.now(timezone.utc)
            
            # Insert document
            result = self.collection.insert_one(campaign_data)
            
            if result.inserted_id:
                logger.info(f"Campaign created: {result.inserted_id}")
                return str(result.inserted_id)
            else:
                logger.error("Failed to create campaign")
                return None

        except PyMongoError as e:
            logger.error(f"Error creating campaign: {e}")
            return None

    async def get_campaign_by_id(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get campaign by ID"""
        try:
            if not self.collection:
                await self.connect()

            campaign = self.collection.find_one({"_id": campaign_id})
            
            if campaign:
                campaign["_id"] = str(campaign["_id"])
                return campaign
            
            return None

        except PyMongoError as e:
            logger.error(f"Error getting campaign by ID: {e}")
            return None

    async def get_campaign_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Get campaign by code"""
        try:
            if not self.collection:
                await self.connect()

            campaign = self.collection.find_one({"code": code})
            
            if campaign:
                campaign["_id"] = str(campaign["_id"])
                return campaign
            
            return None

        except PyMongoError as e:
            logger.error(f"Error getting campaign by code: {e}")
            return None

    async def get_campaigns_paginated(self, page: int, limit: int, sort_by: str, 
                                    sort_order: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get paginated campaigns"""
        try:
            if not self.collection:
                await self.connect()

            # Calculate sort direction
            sort_direction = -1 if sort_order == "desc" else 1
            sort_spec = [(sort_by, sort_direction)]

            # Calculate skip
            skip = (page - 1) * limit

            # Get campaigns
            campaigns = list(self.collection.find(
                filters,
                sort=sort_spec,
                skip=skip,
                limit=limit
            ))

            # Convert ObjectId to string
            for campaign in campaigns:
                campaign["_id"] = str(campaign["_id"])

            return campaigns

        except PyMongoError as e:
            logger.error(f"Error getting paginated campaigns: {e}")
            return []

    async def update_campaign(self, campaign_id: str, update_data: Dict[str, Any]) -> bool:
        """Update campaign"""
        try:
            if not self.collection:
                await self.connect()

            update_data["updated_at"] = datetime.now(timezone.utc)

            result = self.collection.update_one(
                {"_id": campaign_id},
                {"$set": update_data}
            )

            if result.modified_count > 0:
                logger.info(f"Campaign updated: {campaign_id}")
                return True
            else:
                logger.warning(f"No campaign updated: {campaign_id}")
                return False

        except PyMongoError as e:
            logger.error(f"Error updating campaign: {e}")
            return False

    async def update_campaign_status(self, campaign_id: str, new_status: str, 
                                   changed_by: str, reason: str = None) -> bool:
        """Update campaign status with history"""
        try:
            if not self.collection:
                await self.connect()

            # Add status history entry
            status_history_entry = {
                "status": new_status,
                "timestamp": datetime.now(timezone.utc),
                "changed_by": changed_by,
                "reason": reason or "Status updated"
            }

            update_data = {
                "status": new_status,
                "updated_at": datetime.now(timezone.utc),
                "$push": {"status_history": status_history_entry}
            }

            result = self.collection.update_one(
                {"_id": campaign_id},
                {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc)},
                "$push": {"status_history": status_history_entry}}
            )

            if result.modified_count > 0:
                logger.info(f"Campaign status updated: {campaign_id} -> {new_status}")
                return True
            else:
                logger.warning(f"No campaign status updated: {campaign_id}")
                return False

        except PyMongoError as e:
            logger.error(f"Error updating campaign status: {e}")
            return False

    async def delete_campaign(self, campaign_id: str) -> bool:
        """Delete campaign"""
        try:
            if not self.collection:
                await self.connect()

            result = self.collection.delete_one({"_id": campaign_id})

            if result.deleted_count > 0:
                logger.info(f"Campaign deleted: {campaign_id}")
                return True
            else:
                logger.warning(f"No campaign deleted: {campaign_id}")
                return False

        except PyMongoError as e:
            logger.error(f"Error deleting campaign: {e}")
            return False

    async def count_campaigns(self, filters: Dict[str, Any] = None) -> int:
        """Count campaigns"""
        try:
            if not self.collection:
                await self.connect()

            count = self.collection.count_documents(filters or {})
            return count

        except PyMongoError as e:
            logger.error(f"Error counting campaigns: {e}")
            return 0

    async def count_total_campaigns(self) -> int:
        """Count total campaigns"""
        return await self.count_campaigns()

    async def count_active_campaigns(self) -> int:
        """Count active campaigns"""
        return await self.count_campaigns({"status": "active"})

    async def count_completed_campaigns(self) -> int:
        """Count completed campaigns"""
        return await self.count_campaigns({"status": "completed"})

    async def get_total_visits(self) -> int:
        """Get total visits across all campaigns"""
        try:
            if not self.collection:
                await self.connect()

            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_visits": {"$sum": "$statistics.total_visits"}
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))
            return result[0]["total_visits"] if result else 0

        except PyMongoError as e:
            logger.error(f"Error getting total visits: {e}")
            return 0

    async def get_total_captures(self) -> int:
        """Get total captures across all campaigns"""
        try:
            if not self.collection:
                await self.connect()

            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_captures": {"$sum": "$statistics.credential_captures"}
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))
            return result[0]["total_captures"] if result else 0

        except PyMongoError as e:
            logger.error(f"Error getting total captures: {e}")
            return 0

    async def get_top_performing_campaigns(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top performing campaigns"""
        try:
            if not self.collection:
                await self.connect()

            campaigns = list(self.collection.find(
                {},
                sort=[("statistics.credential_captures", -1)],
                limit=limit,
                projection={
                    "name": 1,
                    "code": 1,
                    "status": 1,
                    "statistics.total_visits": 1,
                    "statistics.credential_captures": 1,
                    "statistics.conversion_rates.overall_conversion": 1,
                    "created_at": 1
                }
            ))

            # Convert ObjectId to string
            for campaign in campaigns:
                campaign["_id"] = str(campaign["_id"])

            return campaigns

        except PyMongoError as e:
            logger.error(f"Error getting top performing campaigns: {e}")
            return []

    async def count_campaigns_since(self, start_time: datetime) -> int:
        """Count campaigns created since start_time"""
        return await self.count_campaigns({"created_at": {"$gte": start_time}})

    async def get_visits_since(self, start_time: datetime) -> int:
        """Get visits since start_time"""
        try:
            if not self.collection:
                await self.connect()

            pipeline = [
                {"$match": {"created_at": {"$gte": start_time}}},
                {
                    "$group": {
                        "_id": None,
                        "total_visits": {"$sum": "$statistics.total_visits"}
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))
            return result[0]["total_visits"] if result else 0

        except PyMongoError as e:
            logger.error(f"Error getting visits since: {e}")
            return 0

    async def get_captures_since(self, start_time: datetime) -> int:
        """Get captures since start_time"""
        try:
            if not self.collection:
                await self.connect()

            pipeline = [
                {"$match": {"created_at": {"$gte": start_time}}},
                {
                    "$group": {
                        "_id": None,
                        "total_captures": {"$sum": "$statistics.credential_captures"}
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))
            return result[0]["total_captures"] if result else 0

        except PyMongoError as e:
            logger.error(f"Error getting captures since: {e}")
            return 0

    async def health_check(self) -> bool:
        """Health check for campaigns collection"""
        try:
            if not self.collection:
                await self.connect()

            # Test basic operations
            self.collection.find_one()
            return True

        except PyMongoError as e:
            logger.error(f"Campaigns health check failed: {e}")
            return False