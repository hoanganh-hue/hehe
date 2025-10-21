"""
Proxy Collection Model for MongoDB
Database operations and schema management for proxy pool
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from bson import ObjectId

import pymongo
from pymongo.errors import DuplicateKeyError, OperationFailure

logger = logging.getLogger(__name__)

class ProxyCollection:
    """MongoDB collection manager for proxies"""
    
    def __init__(self, db):
        self.db = db
        self.collection = db.proxies
        self.collection_name = "proxies"
    
    async def create_collection(self):
        """Create the proxies collection with validation schema"""
        try:
            # Check if collection already exists
            if self.collection_name in await self.db.list_collection_names():
                logger.info("Proxies collection already exists")
                return
            
            # Create collection with validation schema
            await self.db.create_collection(
                self.collection_name,
                validator={
                    "$jsonSchema": {
                        "bsonType": "object",
                        "required": ["proxy_url", "type", "country", "status"],
                        "properties": {
                            "proxy_url": {
                                "bsonType": "string",
                                "pattern": "^(http|https|socks4|socks5)://[^:]+:[0-9]+$",
                                "description": "Proxy URL must be a valid proxy format"
                            },
                            "type": {
                                "bsonType": "string",
                                "enum": ["residential", "datacenter", "mobile"],
                                "description": "Proxy type must be residential, datacenter, or mobile"
                            },
                            "country": {
                                "bsonType": "string",
                                "pattern": "^[A-Z]{2}$",
                                "description": "Country code must be 2 uppercase letters"
                            },
                            "provider": {
                                "bsonType": ["string", "null"],
                                "description": "Proxy provider name"
                            },
                            "username": {
                                "bsonType": ["string", "null"],
                                "description": "Proxy username for authentication"
                            },
                            "password": {
                                "bsonType": ["string", "null"],
                                "description": "Proxy password for authentication"
                            },
                            "status": {
                                "bsonType": "string",
                                "enum": ["active", "inactive", "error", "testing"],
                                "description": "Proxy status"
                            },
                            "avg_response_time": {
                                "bsonType": ["int", "null"],
                                "minimum": 0,
                                "description": "Average response time in milliseconds"
                            },
                            "success_rate": {
                                "bsonType": ["double", "null"],
                                "minimum": 0,
                                "maximum": 100,
                                "description": "Success rate percentage"
                            },
                            "last_check": {
                                "bsonType": ["date", "null"],
                                "description": "Last health check timestamp"
                            },
                            "notes": {
                                "bsonType": ["string", "null"],
                                "description": "Additional notes"
                            },
                            "created_at": {
                                "bsonType": "date",
                                "description": "Creation timestamp"
                            },
                            "updated_at": {
                                "bsonType": "date",
                                "description": "Last update timestamp"
                            }
                        }
                    }
                }
            )
            
            logger.info("Proxies collection created with validation schema")
            
        except Exception as e:
            logger.error(f"Failed to create proxies collection: {e}")
            raise
    
    async def create_indexes(self):
        """Create indexes for optimal query performance"""
        try:
            indexes = [
                # Single field indexes
                ("proxy_url", pymongo.ASCENDING),
                ("type", pymongo.ASCENDING),
                ("country", pymongo.ASCENDING),
                ("status", pymongo.ASCENDING),
                ("provider", pymongo.ASCENDING),
                ("last_check", pymongo.DESCENDING),
                ("success_rate", pymongo.DESCENDING),
                ("avg_response_time", pymongo.ASCENDING),
                ("created_at", pymongo.DESCENDING),
                ("updated_at", pymongo.DESCENDING),
                
                # Compound indexes for common queries
                ("status", pymongo.ASCENDING, "type", pymongo.ASCENDING),
                ("country", pymongo.ASCENDING, "status", pymongo.ASCENDING),
                ("type", pymongo.ASCENDING, "success_rate", pymongo.DESCENDING),
                ("status", pymongo.ASCENDING, "last_check", pymongo.DESCENDING),
                
                # Text index for search
                ("proxy_url", pymongo.TEXT, "provider", pymongo.TEXT)
            ]
            
            for index_spec in indexes:
                try:
                    if len(index_spec) == 2:
                        # Single field index
                        await self.collection.create_index([(index_spec[0], index_spec[1])])
                    elif len(index_spec) == 4:
                        # Compound index
                        await self.collection.create_index([
                            (index_spec[0], index_spec[1]),
                            (index_spec[2], index_spec[3])
                        ])
                    elif len(index_spec) == 4 and index_spec[1] == pymongo.TEXT:
                        # Text index
                        await self.collection.create_index([
                            (index_spec[0], index_spec[1]),
                            (index_spec[2], index_spec[3])
                        ])
                except Exception as e:
                    logger.warning(f"Failed to create index {index_spec}: {e}")
            
            # Unique index on proxy_url
            try:
                await self.collection.create_index("proxy_url", unique=True)
            except Exception as e:
                logger.warning(f"Failed to create unique index on proxy_url: {e}")
            
            logger.info("Proxies collection indexes created")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            raise
    
    async def insert_proxy(self, proxy_data: Dict[str, Any]) -> str:
        """Insert a new proxy document"""
        try:
            # Add timestamps
            now = datetime.now(timezone.utc)
            proxy_data.update({
                "created_at": now,
                "updated_at": now
            })
            
            # Set default values
            proxy_data.setdefault("status", "active")
            proxy_data.setdefault("avg_response_time", None)
            proxy_data.setdefault("success_rate", None)
            proxy_data.setdefault("last_check", None)
            
            result = await self.collection.insert_one(proxy_data)
            logger.info(f"Inserted proxy with ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except DuplicateKeyError:
            logger.warning(f"Proxy already exists: {proxy_data.get('proxy_url')}")
            raise ValueError("Proxy already exists")
        except Exception as e:
            logger.error(f"Failed to insert proxy: {e}")
            raise
    
    async def find_proxy_by_id(self, proxy_id: str) -> Optional[Dict[str, Any]]:
        """Find a proxy by ID"""
        try:
            proxy = await self.collection.find_one({"_id": ObjectId(proxy_id)})
            if proxy:
                proxy["_id"] = str(proxy["_id"])
            return proxy
        except Exception as e:
            logger.error(f"Failed to find proxy {proxy_id}: {e}")
            return None
    
    async def find_proxy_by_url(self, proxy_url: str) -> Optional[Dict[str, Any]]:
        """Find a proxy by URL"""
        try:
            proxy = await self.collection.find_one({"proxy_url": proxy_url})
            if proxy:
                proxy["_id"] = str(proxy["_id"])
            return proxy
        except Exception as e:
            logger.error(f"Failed to find proxy by URL {proxy_url}: {e}")
            return None
    
    async def find_proxies(
        self,
        filter_query: Dict[str, Any] = None,
        skip: int = 0,
        limit: int = 100,
        sort_field: str = "created_at",
        sort_direction: int = pymongo.DESCENDING
    ) -> List[Dict[str, Any]]:
        """Find proxies with filtering, pagination, and sorting"""
        try:
            filter_query = filter_query or {}
            
            cursor = self.collection.find(filter_query).skip(skip).limit(limit).sort(sort_field, sort_direction)
            proxies = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string
            for proxy in proxies:
                proxy["_id"] = str(proxy["_id"])
            
            return proxies
            
        except Exception as e:
            logger.error(f"Failed to find proxies: {e}")
            raise
    
    async def update_proxy(self, proxy_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a proxy document"""
        try:
            update_data["updated_at"] = datetime.now(timezone.utc)
            
            result = await self.collection.update_one(
                {"_id": ObjectId(proxy_id)},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Failed to update proxy {proxy_id}: {e}")
            return False
    
    async def delete_proxy(self, proxy_id: str) -> bool:
        """Delete a proxy document"""
        try:
            result = await self.collection.delete_one({"_id": ObjectId(proxy_id)})
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Failed to delete proxy {proxy_id}: {e}")
            return False
    
    async def count_proxies(self, filter_query: Dict[str, Any] = None) -> int:
        """Count proxies matching filter"""
        try:
            filter_query = filter_query or {}
            return await self.collection.count_documents(filter_query)
        except Exception as e:
            logger.error(f"Failed to count proxies: {e}")
            return 0
    
    async def get_proxy_stats(self) -> Dict[str, Any]:
        """Get comprehensive proxy statistics"""
        try:
            # Basic counts
            total = await self.collection.count_documents({})
            active = await self.collection.count_documents({"status": "active"})
            inactive = await self.collection.count_documents({"status": "inactive"})
            error = await self.collection.count_documents({"status": "error"})
            testing = await self.collection.count_documents({"status": "testing"})
            
            # Average response time
            pipeline = [
                {"$match": {"avg_response_time": {"$ne": None, "$gt": 0}}},
                {"$group": {"_id": None, "avg": {"$avg": "$avg_response_time"}}}
            ]
            avg_response_result = await self.collection.aggregate(pipeline).to_list(1)
            avg_response_time = avg_response_result[0]["avg"] if avg_response_result else 0
            
            # Average success rate
            pipeline = [
                {"$match": {"success_rate": {"$ne": None, "$gte": 0}}},
                {"$group": {"_id": None, "avg": {"$avg": "$success_rate"}}}
            ]
            avg_success_result = await self.collection.aggregate(pipeline).to_list(1)
            avg_success_rate = avg_success_result[0]["avg"] if avg_success_result else 0
            
            # Proxies by type
            type_pipeline = [
                {"$group": {"_id": "$type", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            type_results = await self.collection.aggregate(type_pipeline).to_list(10)
            proxies_by_type = {item["_id"]: item["count"] for item in type_results}
            
            # Proxies by country
            country_pipeline = [
                {"$group": {"_id": "$country", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            country_results = await self.collection.aggregate(country_pipeline).to_list(20)
            proxies_by_country = {item["_id"]: item["count"] for item in country_results}
            
            # Proxies by status
            status_pipeline = [
                {"$group": {"_id": "$status", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            status_results = await self.collection.aggregate(status_pipeline).to_list(10)
            proxies_by_status = {item["_id"]: item["count"] for item in status_results}
            
            # Response time distribution
            response_time_pipeline = [
                {"$match": {"avg_response_time": {"$ne": None, "$gt": 0}}},
                {"$bucket": {
                    "groupBy": "$avg_response_time",
                    "boundaries": [0, 100, 500, 1000, 2000, 5000, 10000],
                    "default": "10000+",
                    "output": {"count": {"$sum": 1}}
                }}
            ]
            response_time_results = await self.collection.aggregate(response_time_pipeline).to_list(10)
            response_time_distribution = {item["_id"]: item["count"] for item in response_time_results}
            
            # Success rate distribution
            success_rate_pipeline = [
                {"$match": {"success_rate": {"$ne": None, "$gte": 0}}},
                {"$bucket": {
                    "groupBy": "$success_rate",
                    "boundaries": [0, 25, 50, 75, 90, 95, 100],
                    "default": "100",
                    "output": {"count": {"$sum": 1}}
                }}
            ]
            success_rate_results = await self.collection.aggregate(success_rate_pipeline).to_list(10)
            success_rate_distribution = {item["_id"]: item["count"] for item in success_rate_results}
            
            # Recent activity (last 24 hours)
            yesterday = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            recent_activity = await self.collection.count_documents({
                "last_check": {"$gte": yesterday}
            })
            
            return {
                "total_proxies": total,
                "active_proxies": active,
                "inactive_proxies": inactive,
                "error_proxies": error,
                "testing_proxies": testing,
                "avg_response_time": round(avg_response_time, 2),
                "avg_success_rate": round(avg_success_rate, 2),
                "proxies_by_type": proxies_by_type,
                "proxies_by_country": proxies_by_country,
                "proxies_by_status": proxies_by_status,
                "response_time_distribution": response_time_distribution,
                "success_rate_distribution": success_rate_distribution,
                "recent_activity": recent_activity,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get proxy stats: {e}")
            return {}
    
    async def get_active_proxies_for_assignment(self, country: str = None, proxy_type: str = None) -> List[Dict[str, Any]]:
        """Get active proxies suitable for assignment to victims"""
        try:
            filter_query = {"status": "active"}
            
            if country:
                filter_query["country"] = country
            
            if proxy_type:
                filter_query["type"] = proxy_type
            
            # Sort by success rate and response time for optimal assignment
            cursor = self.collection.find(filter_query).sort([
                ("success_rate", pymongo.DESCENDING),
                ("avg_response_time", pymongo.ASCENDING)
            ])
            
            proxies = await cursor.to_list(length=100)  # Limit to top 100
            
            # Convert ObjectId to string
            for proxy in proxies:
                proxy["_id"] = str(proxy["_id"])
            
            return proxies
            
        except Exception as e:
            logger.error(f"Failed to get active proxies for assignment: {e}")
            return []
    
    async def update_proxy_health(self, proxy_id: str, test_result: Dict[str, Any]) -> bool:
        """Update proxy health statistics based on test result"""
        try:
            proxy = await self.find_proxy_by_id(proxy_id)
            if not proxy:
                return False
            
            # Calculate new statistics using exponential moving average
            current_success_rate = proxy.get("success_rate", 0) or 0
            current_response_time = proxy.get("avg_response_time", 0) or 0
            
            # Alpha factor for EMA (0.1 = 10% weight for new value)
            alpha = 0.1
            
            new_success_rate = (current_success_rate * (1 - alpha)) + (100 if test_result.get("success") else 0) * alpha
            new_response_time = int((current_response_time * (1 - alpha)) + (test_result.get("response_time", 0) or 0) * alpha)
            
            # Determine status based on test result
            if test_result.get("success"):
                status = "active"
            else:
                # Check if this is a temporary failure or persistent error
                if current_success_rate < 50:  # If success rate is already low
                    status = "error"
                else:
                    status = "active"  # Keep as active for temporary failures
            
            update_data = {
                "status": status,
                "success_rate": round(new_success_rate, 2),
                "avg_response_time": new_response_time,
                "last_check": datetime.now(timezone.utc)
            }
            
            return await self.update_proxy(proxy_id, update_data)
            
        except Exception as e:
            logger.error(f"Failed to update proxy health for {proxy_id}: {e}")
            return False
    
    async def bulk_update_status(self, proxy_ids: List[str], status: str) -> int:
        """Bulk update proxy status"""
        try:
            object_ids = [ObjectId(pid) for pid in proxy_ids]
            
            result = await self.collection.update_many(
                {"_id": {"$in": object_ids}},
                {
                    "$set": {
                        "status": status,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            return result.modified_count
            
        except Exception as e:
            logger.error(f"Failed to bulk update proxy status: {e}")
            return 0
    
    async def cleanup_old_proxies(self, days_old: int = 30) -> int:
        """Remove proxies that haven't been checked in specified days"""
        try:
            cutoff_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_old)
            
            result = await self.collection.delete_many({
                "last_check": {"$lt": cutoff_date},
                "status": {"$in": ["error", "inactive"]}
            })
            
            logger.info(f"Cleaned up {result.deleted_count} old proxies")
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old proxies: {e}")
            return 0
    
    async def get_proxy_performance_report(self, days: int = 7) -> Dict[str, Any]:
        """Generate proxy performance report for specified days"""
        try:
            cutoff_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
            
            # Top performing proxies
            top_performers = await self.collection.find({
                "last_check": {"$gte": cutoff_date},
                "status": "active"
            }).sort([
                ("success_rate", pymongo.DESCENDING),
                ("avg_response_time", pymongo.ASCENDING)
            ]).limit(10).to_list(10)
            
            # Worst performing proxies
            worst_performers = await self.collection.find({
                "last_check": {"$gte": cutoff_date},
                "status": {"$in": ["error", "inactive"]}
            }).sort([
                ("success_rate", pymongo.ASCENDING),
                ("avg_response_time", pymongo.DESCENDING)
            ]).limit(10).to_list(10)
            
            # Convert ObjectIds to strings
            for proxy in top_performers + worst_performers:
                proxy["_id"] = str(proxy["_id"])
            
            return {
                "period_days": days,
                "top_performers": top_performers,
                "worst_performers": worst_performers,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate proxy performance report: {e}")
            return {}

# Utility functions
def validate_proxy_data(proxy_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize proxy data"""
    errors = []
    
    # Required fields
    required_fields = ["proxy_url", "type", "country"]
    for field in required_fields:
        if not proxy_data.get(field):
            errors.append(f"Missing required field: {field}")
    
    # Validate proxy URL format
    if proxy_data.get("proxy_url"):
        proxy_url = proxy_data["proxy_url"]
        if not any(proxy_url.startswith(scheme) for scheme in ["http://", "https://", "socks4://", "socks5://"]):
            errors.append("Invalid proxy URL format")
    
    # Validate type
    if proxy_data.get("type") not in ["residential", "datacenter", "mobile"]:
        errors.append("Invalid proxy type")
    
    # Validate country code
    if proxy_data.get("country"):
        country = proxy_data["country"]
        if len(country) != 2 or not country.isalpha():
            errors.append("Invalid country code")
        else:
            proxy_data["country"] = country.upper()
    
    if errors:
        raise ValueError("; ".join(errors))
    
    return proxy_data

def create_proxy_document(proxy_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a properly formatted proxy document"""
    now = datetime.now(timezone.utc)
    
    return {
        "proxy_url": proxy_data["proxy_url"],
        "type": proxy_data["type"],
        "country": proxy_data["country"],
        "provider": proxy_data.get("provider"),
        "username": proxy_data.get("username"),
        "password": proxy_data.get("password"),
        "status": proxy_data.get("status", "active"),
        "avg_response_time": proxy_data.get("avg_response_time"),
        "success_rate": proxy_data.get("success_rate"),
        "last_check": proxy_data.get("last_check"),
        "notes": proxy_data.get("notes"),
        "created_at": now,
        "updated_at": now
    }
