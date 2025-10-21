"""
Proxy Management API for ZaloPay Admin Dashboard
Comprehensive proxy pool management with health monitoring and testing
"""

import asyncio
import csv
import io
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

import httpx
import pymongo
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field, validator

from ..auth.admin_auth import get_current_admin_user
from ..auth.permissions import require_permission
from ...database.connection import get_mongodb_client
from ...config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class ProxyCreate(BaseModel):
    proxy_url: str = Field(..., description="Proxy URL (socks5://ip:port or http://ip:port)")
    type: str = Field(..., description="Proxy type: residential, datacenter, mobile")
    country: str = Field(..., description="Country code (VN, TH, MY, SG, etc.)")
    provider: Optional[str] = Field(None, description="Proxy provider name")
    username: Optional[str] = Field(None, description="Proxy username")
    password: Optional[str] = Field(None, description="Proxy password")
    notes: Optional[str] = Field(None, description="Additional notes")

    @validator('proxy_url')
    def validate_proxy_url(cls, v):
        """Validate proxy URL format"""
        try:
            parsed = urlparse(v)
            if parsed.scheme not in ['http', 'https', 'socks4', 'socks5']:
                raise ValueError("Invalid proxy scheme")
            if not parsed.hostname:
                raise ValueError("Missing hostname")
            if not parsed.port:
                raise ValueError("Missing port")
            return v
        except Exception as e:
            raise ValueError(f"Invalid proxy URL: {e}")

    @validator('type')
    def validate_type(cls, v):
        """Validate proxy type"""
        if v not in ['residential', 'datacenter', 'mobile']:
            raise ValueError("Type must be residential, datacenter, or mobile")
        return v

    @validator('country')
    def validate_country(cls, v):
        """Validate country code"""
        if len(v) != 2 or not v.isalpha():
            raise ValueError("Country must be a 2-letter code")
        return v.upper()

class ProxyUpdate(BaseModel):
    proxy_url: Optional[str] = None
    type: Optional[str] = None
    country: Optional[str] = None
    provider: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None

class ProxyTestRequest(BaseModel):
    proxy_id: Optional[str] = None
    proxy_url: Optional[str] = None
    test_url: str = Field(default="https://httpbin.org/ip", description="URL to test proxy with")

class ProxyTestResult(BaseModel):
    success: bool
    response_time: Optional[int] = None
    error: Optional[str] = None
    ip_address: Optional[str] = None
    test_url: str
    timestamp: datetime

class ProxyResponse(BaseModel):
    _id: str
    proxy_url: str
    type: str
    country: str
    provider: Optional[str] = None
    username: Optional[str] = None
    status: str
    avg_response_time: Optional[int] = None
    success_rate: Optional[float] = None
    last_check: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class BulkImportRequest(BaseModel):
    csv_data: str = Field(..., description="CSV data containing proxy information")

class ProxyStats(BaseModel):
    total_proxies: int
    active_proxies: int
    inactive_proxies: int
    error_proxies: int
    avg_response_time: float
    avg_success_rate: float
    proxies_by_type: Dict[str, int]
    proxies_by_country: Dict[str, int]

# Database operations
class ProxyManager:
    def __init__(self):
        self.db = None
        self.collection = None
    
    async def initialize(self):
        """Initialize database connection"""
        try:
            self.db = await get_mongodb_client()
            self.collection = self.db.proxies
            
            # Create indexes if they don't exist
            await self.create_indexes()
            logger.info("ProxyManager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ProxyManager: {e}")
            raise
    
    async def create_indexes(self):
        """Create database indexes for optimal performance"""
        try:
            indexes = [
                ("proxy_url", pymongo.ASCENDING),
                ("type", pymongo.ASCENDING),
                ("country", pymongo.ASCENDING),
                ("status", pymongo.ASCENDING),
                ("last_check", pymongo.DESCENDING),
                ("success_rate", pymongo.DESCENDING),
                ("created_at", pymongo.DESCENDING)
            ]
            
            for field, direction in indexes:
                await self.collection.create_index([(field, direction)])
            
            # Compound indexes
            await self.collection.create_index([
                ("status", pymongo.ASCENDING),
                ("type", pymongo.ASCENDING)
            ])
            await self.collection.create_index([
                ("country", pymongo.ASCENDING),
                ("status", pymongo.ASCENDING)
            ])
            
            logger.info("Proxy collection indexes created")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
    
    async def create_proxy(self, proxy_data: Dict[str, Any]) -> str:
        """Create a new proxy entry"""
        try:
            proxy_doc = {
                **proxy_data,
                "status": "active",
                "avg_response_time": None,
                "success_rate": None,
                "last_check": None,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            
            result = await self.collection.insert_one(proxy_doc)
            logger.info(f"Created proxy with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to create proxy: {e}")
            raise HTTPException(status_code=500, detail="Failed to create proxy")
    
    async def get_proxies(
        self, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None,
        type: Optional[str] = None,
        country: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get proxies with filtering and pagination"""
        try:
            # Build filter query
            filter_query = {}
            
            if status:
                filter_query["status"] = status
            if type:
                filter_query["type"] = type
            if country:
                filter_query["country"] = country
            if search:
                filter_query["$or"] = [
                    {"proxy_url": {"$regex": search, "$options": "i"}},
                    {"provider": {"$regex": search, "$options": "i"}}
                ]
            
            # Execute query
            cursor = self.collection.find(filter_query).skip(skip).limit(limit).sort("created_at", -1)
            proxies = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string
            for proxy in proxies:
                proxy["_id"] = str(proxy["_id"])
            
            return proxies
        except Exception as e:
            logger.error(f"Failed to get proxies: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve proxies")
    
    async def get_proxy_by_id(self, proxy_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific proxy by ID"""
        try:
            from bson import ObjectId
            proxy = await self.collection.find_one({"_id": ObjectId(proxy_id)})
            if proxy:
                proxy["_id"] = str(proxy["_id"])
            return proxy
        except Exception as e:
            logger.error(f"Failed to get proxy {proxy_id}: {e}")
            return None
    
    async def update_proxy(self, proxy_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a proxy entry"""
        try:
            from bson import ObjectId
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
        """Delete a proxy entry"""
        try:
            from bson import ObjectId
            result = await self.collection.delete_one({"_id": ObjectId(proxy_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete proxy {proxy_id}: {e}")
            return False
    
    async def get_stats(self) -> ProxyStats:
        """Get proxy statistics"""
        try:
            # Total counts
            total = await self.collection.count_documents({})
            active = await self.collection.count_documents({"status": "active"})
            inactive = await self.collection.count_documents({"status": "inactive"})
            error = await self.collection.count_documents({"status": "error"})
            
            # Average response time
            pipeline = [
                {"$match": {"avg_response_time": {"$ne": None}}},
                {"$group": {"_id": None, "avg": {"$avg": "$avg_response_time"}}}
            ]
            avg_response_result = await self.collection.aggregate(pipeline).to_list(1)
            avg_response_time = avg_response_result[0]["avg"] if avg_response_result else 0
            
            # Average success rate
            pipeline = [
                {"$match": {"success_rate": {"$ne": None}}},
                {"$group": {"_id": None, "avg": {"$avg": "$success_rate"}}}
            ]
            avg_success_result = await self.collection.aggregate(pipeline).to_list(1)
            avg_success_rate = avg_success_result[0]["avg"] if avg_success_result else 0
            
            # Proxies by type
            type_pipeline = [
                {"$group": {"_id": "$type", "count": {"$sum": 1}}}
            ]
            type_results = await self.collection.aggregate(type_pipeline).to_list(10)
            proxies_by_type = {item["_id"]: item["count"] for item in type_results}
            
            # Proxies by country
            country_pipeline = [
                {"$group": {"_id": "$country", "count": {"$sum": 1}}}
            ]
            country_results = await self.collection.aggregate(country_pipeline).to_list(20)
            proxies_by_country = {item["_id"]: item["count"] for item in country_results}
            
            return ProxyStats(
                total_proxies=total,
                active_proxies=active,
                inactive_proxies=inactive,
                error_proxies=error,
                avg_response_time=avg_response_time,
                avg_success_rate=avg_success_rate,
                proxies_by_type=proxies_by_type,
                proxies_by_country=proxies_by_country
            )
        except Exception as e:
            logger.error(f"Failed to get proxy stats: {e}")
            raise HTTPException(status_code=500, detail="Failed to get statistics")

# Global proxy manager instance
proxy_manager = ProxyManager()

# Proxy testing functionality
class ProxyTester:
    def __init__(self):
        self.test_timeout = 10.0
        self.test_urls = [
            "https://httpbin.org/ip",
            "https://api.ipify.org?format=json",
            "https://ipinfo.io/json"
        ]
    
    async def test_proxy(self, proxy_url: str, test_url: str = None) -> ProxyTestResult:
        """Test a single proxy"""
        test_url = test_url or self.test_urls[0]
        start_time = time.time()
        
        try:
            # Parse proxy URL
            parsed = urlparse(proxy_url)
            
            # Configure proxy based on scheme
            if parsed.scheme in ['socks4', 'socks5']:
                proxy_config = {
                    "http://": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
                    "https://": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
                }
            else:
                proxy_config = {
                    "http://": f"http://{parsed.hostname}:{parsed.port}",
                    "https://": f"http://{parsed.hostname}:{parsed.port}"
                }
            
            # Add authentication if provided
            if parsed.username and parsed.password:
                auth = f"{parsed.username}:{parsed.password}@"
                for scheme in proxy_config:
                    proxy_config[scheme] = proxy_config[scheme].replace("://", f"://{auth}")
            
            # Test proxy
            async with httpx.AsyncClient(
                proxies=proxy_config,
                timeout=self.test_timeout,
                follow_redirects=True
            ) as client:
                response = await client.get(test_url)
                response_time = int((time.time() - start_time) * 1000)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        ip_address = data.get("origin") or data.get("ip") or "Unknown"
                    except:
                        ip_address = "Unknown"
                    
                    return ProxyTestResult(
                        success=True,
                        response_time=response_time,
                        ip_address=ip_address,
                        test_url=test_url,
                        timestamp=datetime.now(timezone.utc)
                    )
                else:
                    return ProxyTestResult(
                        success=False,
                        response_time=response_time,
                        error=f"HTTP {response.status_code}",
                        test_url=test_url,
                        timestamp=datetime.now(timezone.utc)
                    )
        
        except httpx.TimeoutException:
            return ProxyTestResult(
                success=False,
                error="Connection timeout",
                test_url=test_url,
                timestamp=datetime.now(timezone.utc)
            )
        except httpx.ConnectError:
            return ProxyTestResult(
                success=False,
                error="Connection failed",
                test_url=test_url,
                timestamp=datetime.now(timezone.utc)
            )
        except Exception as e:
            return ProxyTestResult(
                success=False,
                error=str(e),
                test_url=test_url,
                timestamp=datetime.now(timezone.utc)
            )

# Global proxy tester instance
proxy_tester = ProxyTester()

# API Routes
@router.on_event("startup")
async def startup_event():
    """Initialize proxy manager on startup"""
    await proxy_manager.initialize()

@router.get("/", response_model=List[ProxyResponse])
async def get_proxies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Get proxies with filtering and pagination"""
    require_permission(admin_user, "proxy_management")
    
    proxies = await proxy_manager.get_proxies(
        skip=skip,
        limit=limit,
        status=status,
        type=type,
        country=country,
        search=search
    )
    
    return proxies

@router.get("/stats", response_model=ProxyStats)
async def get_proxy_stats(
    admin_user: dict = Depends(get_current_admin_user)
):
    """Get proxy statistics"""
    require_permission(admin_user, "proxy_management")
    
    stats = await proxy_manager.get_stats()
    return stats

@router.get("/{proxy_id}", response_model=ProxyResponse)
async def get_proxy(
    proxy_id: str,
    admin_user: dict = Depends(get_current_admin_user)
):
    """Get a specific proxy by ID"""
    require_permission(admin_user, "proxy_management")
    
    proxy = await proxy_manager.get_proxy_by_id(proxy_id)
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
    
    return proxy

@router.post("/", response_model=Dict[str, str])
async def create_proxy(
    proxy_data: ProxyCreate,
    admin_user: dict = Depends(get_current_admin_user)
):
    """Create a new proxy"""
    require_permission(admin_user, "proxy_management")
    
    # Check if proxy already exists
    existing = await proxy_manager.get_proxies(search=proxy_data.proxy_url)
    if existing:
        raise HTTPException(status_code=400, detail="Proxy already exists")
    
    proxy_id = await proxy_manager.create_proxy(proxy_data.dict())
    
    return {"id": proxy_id, "message": "Proxy created successfully"}

@router.put("/{proxy_id}")
async def update_proxy(
    proxy_id: str,
    proxy_data: ProxyUpdate,
    admin_user: dict = Depends(get_current_admin_user)
):
    """Update a proxy"""
    require_permission(admin_user, "proxy_management")
    
    # Check if proxy exists
    proxy = await proxy_manager.get_proxy_by_id(proxy_id)
    if not proxy:
        raise HTTPException(status_code=404, detail="Proxy not found")
    
    # Update proxy
    update_data = {k: v for k, v in proxy_data.dict().items() if v is not None}
    success = await proxy_manager.update_proxy(proxy_id, update_data)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update proxy")
    
    return {"message": "Proxy updated successfully"}

@router.delete("/{proxy_id}")
async def delete_proxy(
    proxy_id: str,
    admin_user: dict = Depends(get_current_admin_user)
):
    """Delete a proxy"""
    require_permission(admin_user, "proxy_management")
    
    success = await proxy_manager.delete_proxy(proxy_id)
    if not success:
        raise HTTPException(status_code=404, detail="Proxy not found")
    
    return {"message": "Proxy deleted successfully"}

@router.post("/test", response_model=ProxyTestResult)
async def test_proxy(
    test_request: ProxyTestRequest,
    admin_user: dict = Depends(get_current_admin_user)
):
    """Test a proxy"""
    require_permission(admin_user, "proxy_management")
    
    proxy_url = None
    
    if test_request.proxy_id:
        proxy = await proxy_manager.get_proxy_by_id(test_request.proxy_id)
        if not proxy:
            raise HTTPException(status_code=404, detail="Proxy not found")
        proxy_url = proxy["proxy_url"]
    elif test_request.proxy_url:
        proxy_url = test_request.proxy_url
    else:
        raise HTTPException(status_code=400, detail="Either proxy_id or proxy_url must be provided")
    
    # Test the proxy
    result = await proxy_tester.test_proxy(proxy_url, test_request.test_url)
    
    # Update proxy statistics if testing by ID
    if test_request.proxy_id:
        await update_proxy_stats(test_request.proxy_id, result)
    
    return result

@router.post("/test-all")
async def test_all_proxies(
    background_tasks: BackgroundTasks,
    admin_user: dict = Depends(get_current_admin_user)
):
    """Test all active proxies in background"""
    require_permission(admin_user, "proxy_management")
    
    # Start background task
    background_tasks.add_task(test_all_proxies_background)
    
    return {"message": "Proxy testing started in background"}

async def test_all_proxies_background():
    """Background task to test all proxies"""
    try:
        proxies = await proxy_manager.get_proxies(status="active", limit=1000)
        
        for proxy in proxies:
            try:
                result = await proxy_tester.test_proxy(proxy["proxy_url"])
                await update_proxy_stats(proxy["_id"], result)
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Failed to test proxy {proxy['_id']}: {e}")
        
        logger.info(f"Completed testing {len(proxies)} proxies")
    except Exception as e:
        logger.error(f"Background proxy testing failed: {e}")

async def update_proxy_stats(proxy_id: str, test_result: ProxyTestResult):
    """Update proxy statistics based on test result"""
    try:
        proxy = await proxy_manager.get_proxy_by_id(proxy_id)
        if not proxy:
            return
        
        # Calculate new statistics
        current_success_rate = proxy.get("success_rate", 0) or 0
        current_response_time = proxy.get("avg_response_time", 0) or 0
        
        # Simple moving average (can be improved with more sophisticated algorithms)
        new_success_rate = (current_success_rate * 0.9) + (100 if test_result.success else 0) * 0.1
        new_response_time = int((current_response_time * 0.9) + (test_result.response_time or 0) * 0.1)
        
        # Determine status
        if test_result.success:
            status = "active"
        else:
            status = "error"
        
        # Update proxy
        update_data = {
            "status": status,
            "success_rate": round(new_success_rate, 2),
            "avg_response_time": new_response_time,
            "last_check": test_result.timestamp
        }
        
        await proxy_manager.update_proxy(proxy_id, update_data)
        
    except Exception as e:
        logger.error(f"Failed to update proxy stats for {proxy_id}: {e}")

@router.post("/import")
async def import_proxies(
    import_request: BulkImportRequest,
    admin_user: dict = Depends(get_current_admin_user)
):
    """Import proxies from CSV data"""
    require_permission(admin_user, "proxy_management")
    
    try:
        # Parse CSV data
        csv_reader = csv.DictReader(io.StringIO(import_request.csv_data))
        
        imported_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, 1):
            try:
                # Validate required fields
                if not row.get("proxy_url"):
                    errors.append(f"Row {row_num}: Missing proxy_url")
                    continue
                
                # Create proxy data
                proxy_data = {
                    "proxy_url": row["proxy_url"].strip(),
                    "type": row.get("type", "datacenter").strip(),
                    "country": row.get("country", "VN").strip(),
                    "provider": row.get("provider", "").strip() or None,
                    "username": row.get("username", "").strip() or None,
                    "password": row.get("password", "").strip() or None,
                    "notes": row.get("notes", "").strip() or None
                }
                
                # Validate data
                proxy_create = ProxyCreate(**proxy_data)
                
                # Check if proxy already exists
                existing = await proxy_manager.get_proxies(search=proxy_create.proxy_url)
                if existing:
                    errors.append(f"Row {row_num}: Proxy already exists")
                    continue
                
                # Create proxy
                await proxy_manager.create_proxy(proxy_create.dict())
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        return {
            "imported": imported_count,
            "errors": errors,
            "message": f"Imported {imported_count} proxies successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to import proxies: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@router.get("/export/csv")
async def export_proxies_csv(
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Export proxies as CSV"""
    require_permission(admin_user, "proxy_management")
    
    proxies = await proxy_manager.get_proxies(
        limit=10000,  # Large limit for export
        status=status,
        type=type,
        country=country
    )
    
    # Create CSV
    output = io.StringIO()
    fieldnames = [
        "proxy_url", "type", "country", "provider", "status",
        "avg_response_time", "success_rate", "last_check", "notes"
    ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for proxy in proxies:
        writer.writerow({
            "proxy_url": proxy.get("proxy_url", ""),
            "type": proxy.get("type", ""),
            "country": proxy.get("country", ""),
            "provider": proxy.get("provider", ""),
            "status": proxy.get("status", ""),
            "avg_response_time": proxy.get("avg_response_time", ""),
            "success_rate": proxy.get("success_rate", ""),
            "last_check": proxy.get("last_check", ""),
            "notes": proxy.get("notes", "")
        })
    
    csv_content = output.getvalue()
    output.close()
    
    return {
        "content": csv_content,
        "filename": f"proxies_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "content_type": "text/csv"
    }

@router.get("/export/json")
async def export_proxies_json(
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    admin_user: dict = Depends(get_current_admin_user)
):
    """Export proxies as JSON"""
    require_permission(admin_user, "proxy_management")
    
    proxies = await proxy_manager.get_proxies(
        limit=10000,  # Large limit for export
        status=status,
        type=type,
        country=country
    )
    
    return {
        "proxies": proxies,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "total_count": len(proxies)
    }
