"""
Campaign Management API
Admin interface for campaign creation and management
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, status, Depends, Query, Request
from pydantic import BaseModel

from database.mongodb.campaigns import CampaignModel
from database.mongodb.victims import VictimModel
from middleware.authentication import get_current_admin_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class CampaignCreateRequest(BaseModel):
    name: str
    code: str
    description: str
    config: Dict[str, Any]
    infrastructure: Optional[Dict[str, Any]] = None
    timeline: Optional[Dict[str, Any]] = None
    success_criteria: Optional[Dict[str, Any]] = None
    team: Optional[Dict[str, Any]] = None

class CampaignUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    infrastructure: Optional[Dict[str, Any]] = None
    timeline: Optional[Dict[str, Any]] = None
    success_criteria: Optional[Dict[str, Any]] = None
    team: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class CampaignStatusUpdateRequest(BaseModel):
    status: str
    reason: Optional[str] = None

@router.get("/")
async def list_campaigns(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    status: Optional[str] = Query(None),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get paginated list of campaigns with filtering"""
    try:
        campaign_model = CampaignModel()
        
        # Build filters
        filters = {}
        if status:
            filters["status"] = status
        
        # Get campaigns
        campaigns = await campaign_model.get_campaigns_paginated(
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
            filters=filters
        )
        
        # Get total count
        total_count = await campaign_model.count_campaigns(filters)
        
        return {
            "success": True,
            "campaigns": campaigns,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing campaigns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list campaigns"
        )

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_campaign(
    request: CampaignCreateRequest,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Create a new campaign"""
    try:
        campaign_model = CampaignModel()
        
        # Check if campaign code already exists
        existing_campaign = await campaign_model.get_campaign_by_code(request.code)
        if existing_campaign:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Campaign code already exists"
            )
        
        # Prepare campaign data
        campaign_data = {
            "name": request.name,
            "code": request.code,
            "description": request.description,
            "config": request.config,
            "infrastructure": request.infrastructure or {},
            "timeline": request.timeline or {
                "planned_start": None,
                "actual_start": None,
                "planned_end": None,
                "current_phase": "planning",
                "milestones": []
            },
            "success_criteria": request.success_criteria or {},
            "team": request.team or {},
            "statistics": {
                "total_visits": 0,
                "unique_visitors": 0,
                "credential_captures": 0,
                "successful_validations": 0,
                "high_value_targets": 0,
                "business_accounts": 0,
                "conversion_rates": {
                    "visit_to_interaction": 0.0,
                    "interaction_to_auth_attempt": 0.0,
                    "auth_attempt_to_capture": 0.0,
                    "capture_to_validation": 0.0,
                    "overall_conversion": 0.0
                },
                "performance_metrics": {
                    "average_session_duration_seconds": 0,
                    "bounce_rate": 0.0,
                    "pages_per_session": 0.0,
                    "load_time_average_ms": 0,
                    "proxy_success_rate": 0.0
                },
                "geographic_distribution": {},
                "hourly_performance": {
                    "peak_hours": [],
                    "best_conversion_hours": [],
                    "worst_performance_hours": []
                }
            },
            "risk_assessment": {
                "current_risk_level": "low",
                "detection_incidents": 0,
                "law_enforcement_interest": "none",
                "technical_countermeasures": 0,
                "mitigation_actions": []
            },
            "status": "draft",
            "status_history": [{
                "status": "draft",
                "timestamp": datetime.now(timezone.utc),
                "changed_by": current_admin["admin_id"],
                "reason": "Campaign created"
            }],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "created_by": current_admin["admin_id"]
        }
        
        # Create campaign
        campaign_id = await campaign_model.create_campaign(campaign_data)
        
        if campaign_id:
            return {
                "success": True,
                "message": "Campaign created successfully",
                "campaign_id": campaign_id
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create campaign"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create campaign"
        )

@router.get("/{campaign_id}")
async def get_campaign_details(
    campaign_id: str,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get detailed information about a specific campaign"""
    try:
        campaign_model = CampaignModel()
        victim_model = VictimModel()
        
        # Get campaign data
        campaign = await campaign_model.get_campaign_by_id(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Get campaign victims
        campaign_victims = await victim_model.get_victims_by_campaign_id(campaign_id)
        
        return {
            "success": True,
            "campaign": campaign,
            "victims": campaign_victims,
            "victim_count": len(campaign_victims)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting campaign details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get campaign details"
        )

@router.put("/{campaign_id}")
async def update_campaign(
    campaign_id: str,
    request: CampaignUpdateRequest,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Update campaign information"""
    try:
        campaign_model = CampaignModel()
        
        # Check if campaign exists
        campaign = await campaign_model.get_campaign_by_id(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Prepare update data
        update_data = {}
        if request.name is not None:
            update_data["name"] = request.name
        if request.description is not None:
            update_data["description"] = request.description
        if request.config is not None:
            update_data["config"] = request.config
        if request.infrastructure is not None:
            update_data["infrastructure"] = request.infrastructure
        if request.timeline is not None:
            update_data["timeline"] = request.timeline
        if request.success_criteria is not None:
            update_data["success_criteria"] = request.success_criteria
        if request.team is not None:
            update_data["team"] = request.team
        if request.status is not None:
            update_data["status"] = request.status
            
            # Add status history entry
            status_history_entry = {
                "status": request.status,
                "timestamp": datetime.now(timezone.utc),
                "changed_by": current_admin["admin_id"],
                "reason": "Campaign updated"
            }
            update_data["$push"] = {"status_history": status_history_entry}
        
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        # Update campaign
        success = await campaign_model.update_campaign(campaign_id, update_data)
        
        if success:
            return {
                "success": True,
                "message": "Campaign updated successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update campaign"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating campaign: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update campaign"
        )

@router.patch("/{campaign_id}/status")
async def update_campaign_status(
    campaign_id: str,
    request: CampaignStatusUpdateRequest,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Update campaign status"""
    try:
        campaign_model = CampaignModel()
        
        # Check if campaign exists
        campaign = await campaign_model.get_campaign_by_id(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Validate status transition
        current_status = campaign.get("status")
        valid_transitions = {
            "draft": ["active", "cancelled"],
            "active": ["paused", "completed", "cancelled"],
            "paused": ["active", "completed", "cancelled"],
            "completed": [],
            "cancelled": []
        }
        
        if request.status not in valid_transitions.get(current_status, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from {current_status} to {request.status}"
            )
        
        # Update status
        success = await campaign_model.update_campaign_status(
            campaign_id=campaign_id,
            new_status=request.status,
            changed_by=current_admin["admin_id"],
            reason=request.reason
        )
        
        if success:
            return {
                "success": True,
                "message": f"Campaign status updated to {request.status}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update campaign status"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating campaign status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update campaign status"
        )

@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Delete a campaign"""
    try:
        campaign_model = CampaignModel()
        
        # Check if campaign exists
        campaign = await campaign_model.get_campaign_by_id(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Check if campaign can be deleted
        if campaign.get("status") == "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete active campaign. Please pause or complete it first."
            )
        
        # Delete campaign
        success = await campaign_model.delete_campaign(campaign_id)
        
        if success:
            return {
                "success": True,
                "message": "Campaign deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete campaign"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting campaign: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete campaign"
        )

@router.get("/{campaign_id}/statistics")
async def get_campaign_statistics(
    campaign_id: str,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get detailed statistics for a specific campaign"""
    try:
        campaign_model = CampaignModel()
        victim_model = VictimModel()
        
        # Check if campaign exists
        campaign = await campaign_model.get_campaign_by_id(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Get campaign statistics
        campaign_stats = campaign.get("statistics", {})
        
        # Get victim statistics for this campaign
        campaign_victims = await victim_model.get_victims_by_campaign_id(campaign_id)
        victim_stats = {
            "total_victims": len(campaign_victims),
            "high_value_victims": len([v for v in campaign_victims if v.get("risk_score", 0) > 80]),
            "verified_victims": len([v for v in campaign_victims if v.get("verification_status") == "verified"]),
            "geographic_distribution": {}
        }
        
        # Calculate geographic distribution
        for victim in campaign_victims:
            country = victim.get("location", {}).get("country", "Unknown")
            victim_stats["geographic_distribution"][country] = victim_stats["geographic_distribution"].get(country, 0) + 1
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "campaign_statistics": campaign_stats,
            "victim_statistics": victim_stats,
            "performance_metrics": {
                "conversion_rate": campaign_stats.get("conversion_rates", {}).get("overall_conversion", 0.0),
                "success_rate": campaign_stats.get("performance_metrics", {}).get("proxy_success_rate", 0.0),
                "average_session_duration": campaign_stats.get("performance_metrics", {}).get("average_session_duration_seconds", 0)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting campaign statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get campaign statistics"
        )

@router.get("/{campaign_id}/performance")
async def get_campaign_performance(
    campaign_id: str,
    time_range: str = Query("7d", regex="^(1d|7d|30d|90d)$"),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get campaign performance metrics over time"""
    try:
        campaign_model = CampaignModel()
        
        # Check if campaign exists
        campaign = await campaign_model.get_campaign_by_id(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
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
        
        # Get performance data (in a real implementation, this would query time-series data)
        performance_data = {
            "time_range": time_range,
            "start_time": start_time.isoformat(),
            "end_time": now.isoformat(),
            "daily_metrics": [
                {
                    "date": (now - timedelta(days=i)).strftime("%Y-%m-%d"),
                    "visits": 0,
                    "captures": 0,
                    "conversion_rate": 0.0
                }
                for i in range(int(time_range[:-1]))
            ],
            "hourly_distribution": {
                "peak_hours": campaign.get("statistics", {}).get("hourly_performance", {}).get("peak_hours", []),
                "best_conversion_hours": campaign.get("statistics", {}).get("hourly_performance", {}).get("best_conversion_hours", []),
                "worst_performance_hours": campaign.get("statistics", {}).get("hourly_performance", {}).get("worst_performance_hours", [])
            }
        }
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "performance_data": performance_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting campaign performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get campaign performance"
        )

@router.get("/statistics/summary")
async def get_campaign_statistics_summary(
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get overall campaign statistics summary"""
    try:
        campaign_model = CampaignModel()
        
        # Get various statistics
        total_campaigns = await campaign_model.count_total_campaigns()
        active_campaigns = await campaign_model.count_active_campaigns()
        completed_campaigns = await campaign_model.count_completed_campaigns()
        
        # Get performance metrics
        total_visits = await campaign_model.get_total_visits()
        total_captures = await campaign_model.get_total_captures()
        overall_conversion_rate = total_captures / total_visits if total_visits > 0 else 0.0
        
        # Get top performing campaigns
        top_campaigns = await campaign_model.get_top_performing_campaigns(limit=5)
        
        return {
            "success": True,
            "statistics": {
                "total_campaigns": total_campaigns,
                "active_campaigns": active_campaigns,
                "completed_campaigns": completed_campaigns,
                "total_visits": total_visits,
                "total_captures": total_captures,
                "overall_conversion_rate": overall_conversion_rate,
                "top_performing_campaigns": top_campaigns
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting campaign statistics summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get campaign statistics summary"
        )