"""
Activity Logs API
Admin interface for system activity monitoring and audit trails
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel

from database.mongodb.activity_logs import ActivityLogModel
from middleware.authentication import get_current_admin_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class ActivityLogSearchRequest(BaseModel):
    query: Optional[str] = None
    admin_id: Optional[str] = None
    action_type: Optional[str] = None
    action_category: Optional[str] = None
    severity_level: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    sort_by: str = "timestamp"
    sort_order: str = "desc"
    page: int = 1
    limit: int = 50

class ActivityLogFilterRequest(BaseModel):
    filters: Dict[str, Any]
    time_range: Optional[str] = None
    group_by: Optional[str] = None

@router.get("/")
async def list_activity_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    sort_by: str = Query("timestamp"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    admin_id: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    action_category: Optional[str] = Query(None),
    severity_level: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get paginated list of activity logs with filtering"""
    try:
        activity_model = ActivityLogModel()
        
        # Build filters
        filters = {}
        if admin_id:
            filters["actor.admin_id"] = admin_id
        if action_type:
            filters["action_type"] = action_type
        if action_category:
            filters["action_category"] = action_category
        if severity_level:
            filters["severity_level"] = severity_level
        if start_date:
            filters["timestamp"] = {"$gte": start_date}
        if end_date:
            if "timestamp" in filters:
                filters["timestamp"]["$lte"] = end_date
            else:
                filters["timestamp"] = {"$lte": end_date}
        
        # Get activity logs
        logs = await activity_model.get_activity_logs_paginated(
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
            filters=filters
        )
        
        # Get total count
        total_count = await activity_model.count_activity_logs(filters)
        
        return {
            "success": True,
            "activity_logs": logs,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing activity logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list activity logs"
        )

@router.post("/search")
async def search_activity_logs(
    request: ActivityLogSearchRequest,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Search activity logs with advanced filtering"""
    try:
        activity_model = ActivityLogModel()
        
        # Build filters
        filters = {}
        if request.admin_id:
            filters["actor.admin_id"] = request.admin_id
        if request.action_type:
            filters["action_type"] = request.action_type
        if request.action_category:
            filters["action_category"] = request.action_category
        if request.severity_level:
            filters["severity_level"] = request.severity_level
        if request.start_date:
            filters["timestamp"] = {"$gte": request.start_date}
        if request.end_date:
            if "timestamp" in filters:
                filters["timestamp"]["$lte"] = request.end_date
            else:
                filters["timestamp"] = {"$lte": request.end_date}
        
        # Perform search
        results = await activity_model.search_activity_logs(
            query=request.query,
            filters=filters,
            sort_by=request.sort_by,
            sort_order=request.sort_order,
            page=request.page,
            limit=request.limit
        )
        
        return {
            "success": True,
            "results": results["logs"],
            "pagination": results["pagination"],
            "search_info": {
                "query": request.query,
                "total_found": results["pagination"]["total"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error searching activity logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search activity logs"
        )

@router.get("/{log_id}")
async def get_activity_log_details(
    log_id: str,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get detailed information about a specific activity log"""
    try:
        activity_model = ActivityLogModel()
        
        # Get activity log
        log = await activity_model.get_activity_log_by_id(log_id)
        if not log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity log not found"
            )
        
        return {
            "success": True,
            "activity_log": log
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting activity log details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get activity log details"
        )

@router.get("/admin/{admin_id}")
async def get_admin_activity_logs(
    admin_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get activity logs for a specific admin user"""
    try:
        activity_model = ActivityLogModel()
        
        # Get activity logs for admin
        logs = await activity_model.get_activity_logs_by_admin_id(
            admin_id=admin_id,
            page=page,
            limit=limit
        )
        
        # Get total count
        total_count = await activity_model.count_activity_logs_by_admin_id(admin_id)
        
        return {
            "success": True,
            "admin_id": admin_id,
            "activity_logs": logs,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting admin activity logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get admin activity logs"
        )

@router.get("/statistics/summary")
async def get_activity_statistics_summary(
    time_range: str = Query("24h", regex="^(1h|24h|7d|30d)$"),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get activity statistics summary"""
    try:
        activity_model = ActivityLogModel()
        
        # Calculate time range
        now = datetime.now(timezone.utc)
        if time_range == "1h":
            start_time = now - timedelta(hours=1)
        elif time_range == "24h":
            start_time = now - timedelta(days=1)
        elif time_range == "7d":
            start_time = now - timedelta(days=7)
        else:  # 30d
            start_time = now - timedelta(days=30)
        
        # Get statistics
        total_activities = await activity_model.count_activities_since(start_time)
        activities_by_type = await activity_model.get_activities_by_type_since(start_time)
        activities_by_admin = await activity_model.get_activities_by_admin_since(start_time)
        activities_by_severity = await activity_model.get_activities_by_severity_since(start_time)
        
        return {
            "success": True,
            "time_range": time_range,
            "start_time": start_time.isoformat(),
            "end_time": now.isoformat(),
            "statistics": {
                "total_activities": total_activities,
                "activities_by_type": activities_by_type,
                "activities_by_admin": activities_by_admin,
                "activities_by_severity": activities_by_severity
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting activity statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get activity statistics"
        )

@router.get("/statistics/trends")
async def get_activity_trends(
    time_range: str = Query("7d", regex="^(1d|7d|30d|90d)$"),
    granularity: str = Query("daily", regex="^(hourly|daily|weekly)$"),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get activity trends over time"""
    try:
        activity_model = ActivityLogModel()
        
        # Calculate time range
        now = datetime.now(timezone.utc)
        if time_range == "1d":
            start_time = now - timedelta(days=1)
        elif time_range == "7d":
            start_time = now - timedelta(days=7)
        elif time_range == "30d":
            start_time = now - timedelta(days=30)
        else:  # 90d
            start_time = now - timedelta(days=90)
        
        # Get trends data
        trends_data = await activity_model.get_activity_trends(
            start_time=start_time,
            end_time=now,
            granularity=granularity
        )
        
        return {
            "success": True,
            "time_range": time_range,
            "granularity": granularity,
            "start_time": start_time.isoformat(),
            "end_time": now.isoformat(),
            "trends_data": trends_data
        }
        
    except Exception as e:
        logger.error(f"Error getting activity trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get activity trends"
        )

@router.get("/security/events")
async def get_security_events(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    severity_level: Optional[str] = Query(None),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get security-related activity events"""
    try:
        activity_model = ActivityLogModel()
        
        # Build filters for security events
        filters = {
            "action_category": "security",
            "severity_level": {"$in": ["high", "critical"]}
        }
        
        if severity_level:
            filters["severity_level"] = severity_level
        
        # Get security events
        events = await activity_model.get_activity_logs_paginated(
            page=page,
            limit=limit,
            sort_by="timestamp",
            sort_order="desc",
            filters=filters
        )
        
        # Get total count
        total_count = await activity_model.count_activity_logs(filters)
        
        return {
            "success": True,
            "security_events": events,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting security events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get security events"
        )

@router.get("/audit/trail")
async def get_audit_trail(
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get audit trail for specific resources"""
    try:
        activity_model = ActivityLogModel()
        
        # Build filters for audit trail
        filters = {}
        if resource_type:
            filters["target.resource_type"] = resource_type
        if resource_id:
            filters["target.resource_id"] = resource_id
        
        # Get audit trail
        audit_logs = await activity_model.get_activity_logs_paginated(
            page=page,
            limit=limit,
            sort_by="timestamp",
            sort_order="desc",
            filters=filters
        )
        
        # Get total count
        total_count = await activity_model.count_activity_logs(filters)
        
        return {
            "success": True,
            "audit_trail": audit_logs,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting audit trail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit trail"
        )

@router.delete("/cleanup")
async def cleanup_old_activity_logs(
    days_to_keep: int = Query(90, ge=30, le=365),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Clean up old activity logs (admin only)"""
    try:
        # Check if current admin has permission
        if current_admin.get("role") not in ["super_admin", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to perform cleanup"
            )
        
        activity_model = ActivityLogModel()
        
        # Clean up old logs
        deleted_count = await activity_model.cleanup_old_logs(days_to_keep)
        
        return {
            "success": True,
            "message": f"Cleaned up {deleted_count} old activity logs",
            "deleted_count": deleted_count,
            "days_kept": days_to_keep
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up activity logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clean up activity logs"
        )