"""
Google OAuth Service
Google OAuth flow implementation with credential capture
"""

import logging
import secrets
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from urllib.parse import urlencode

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import settings

logger = logging.getLogger(__name__)

class GoogleOAuthService:
    """Google OAuth service for authentication and API access"""
    
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        self.scopes = settings.GOOGLE_SCOPES
        
        # OAuth flow configuration
        self.flow_config = {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self.redirect_uri]
            }
        }

    def is_configured(self) -> bool:
        """Check if Google OAuth service is properly configured"""
        return bool(
            self.client_id and
            self.client_secret and
            self.redirect_uri and
            len(self.client_id) > 10 and  # Basic validation
            len(self.client_secret) > 10 and
            self.redirect_uri.startswith("https://")
        )
    
    def get_authorization_url(self, state: str = None, redirect_uri: str = None) -> str:
        """Get Google OAuth authorization URL"""
        try:
            # Create OAuth flow
            flow = Flow.from_client_config(
                self.flow_config,
                scopes=self.scopes,
                redirect_uri=redirect_uri or self.redirect_uri
            )
            
            # Generate state if not provided
            if not state:
                state = secrets.token_urlsafe(32)
            
            # Get authorization URL
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=state,
                prompt='consent'
            )
            
            logger.info(f"Generated Google OAuth URL with state: {state}")
            return auth_url
            
        except Exception as e:
            logger.error(f"Failed to generate authorization URL: {e}")
            raise
    
    async def exchange_code_for_tokens(self, code: str, redirect_uri: str = None) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access tokens"""
        try:
            # Create OAuth flow
            flow = Flow.from_client_config(
                self.flow_config,
                scopes=self.scopes,
                redirect_uri=redirect_uri or self.redirect_uri
            )
            
            # Exchange code for tokens
            flow.fetch_token(code=code)
            
            # Get credentials
            credentials = flow.credentials
            
            # Extract token information
            token_data = {
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "scopes": credentials.scopes,
                "expires_at": credentials.expiry.isoformat() if credentials.expiry else None,
                "expires_in": int((credentials.expiry - datetime.now(timezone.utc)).total_seconds()) if credentials.expiry else None
            }
            
            logger.info("Successfully exchanged authorization code for tokens")
            return token_data
            
        except Exception as e:
            logger.error(f"Failed to exchange code for tokens: {e}")
            return None
    
    async def get_user_profile(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user profile information using access token"""
        try:
            # Create credentials object
            credentials = Credentials(token=access_token)
            
            # Build service
            service = build('oauth2', 'v2', credentials=credentials)
            
            # Get user info
            user_info = service.userinfo().get().execute()
            
            # Extract relevant information
            profile_data = {
                "google_id": user_info.get("id"),
                "email": user_info.get("email"),
                "verified_email": user_info.get("verified_email"),
                "name": user_info.get("name"),
                "given_name": user_info.get("given_name"),
                "family_name": user_info.get("family_name"),
                "picture": user_info.get("picture"),
                "locale": user_info.get("locale"),
                "hd": user_info.get("hd")  # Hosted domain for G Suite
            }
            
            logger.info(f"Retrieved user profile for: {profile_data.get('email')}")
            return profile_data
            
        except HttpError as e:
            logger.error(f"Google API error getting user profile: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            return None
    
    async def validate_token(self, access_token: str) -> bool:
        """Validate access token"""
        try:
            # Create credentials object
            credentials = Credentials(token=access_token)
            
            # Build service
            service = build('oauth2', 'v2', credentials=credentials)
            
            # Try to get user info to validate token
            user_info = service.userinfo().get().execute()
            
            return bool(user_info.get("id"))
            
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return False
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh access token using refresh token"""
        try:
            # Create credentials object
            credentials = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            
            # Refresh token
            request = GoogleRequest()
            credentials.refresh(request)
            
            # Extract new token information
            token_data = {
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "expires_at": credentials.expiry.isoformat() if credentials.expiry else None,
                "expires_in": int((credentials.expiry - datetime.now(timezone.utc)).total_seconds()) if credentials.expiry else None
            }
            
            logger.info("Successfully refreshed access token")
            return token_data
            
        except Exception as e:
            logger.error(f"Failed to refresh access token: {e}")
            return None
    
    async def revoke_token(self, access_token: str) -> bool:
        """Revoke access token"""
        try:
            # Create credentials object
            credentials = Credentials(token=access_token)
            
            # Revoke token
            credentials.revoke(GoogleRequest())
            
            logger.info("Successfully revoked access token")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
            return False
    
    async def get_gmail_service(self, credentials: Credentials):
        """Get Gmail service using credentials"""
        try:
            # Build Gmail service
            service = build('gmail', 'v1', credentials=credentials)
            return service
            
        except Exception as e:
            logger.error(f"Failed to create Gmail service: {e}")
            return None
    
    async def get_contacts_service(self, credentials: Credentials):
        """Get Google Contacts service using credentials"""
        try:
            # Build Contacts service
            service = build('people', 'v1', credentials=credentials)
            return service
            
        except Exception as e:
            logger.error(f"Failed to create Contacts service: {e}")
            return None
    
    async def get_calendar_service(self, credentials: Credentials):
        """Get Google Calendar service using credentials"""
        try:
            # Build Calendar service
            service = build('calendar', 'v3', credentials=credentials)
            return service
            
        except Exception as e:
            logger.error(f"Failed to create Calendar service: {e}")
            return None
    
    def create_credentials_from_token_data(self, token_data: Dict[str, Any]) -> Credentials:
        """Create Credentials object from token data"""
        try:
            credentials = Credentials(
                token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=self.scopes
            )
            
            # Set expiry if available
            if token_data.get("expires_at"):
                credentials.expiry = datetime.fromisoformat(token_data["expires_at"].replace('Z', '+00:00'))
            
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to create credentials from token data: {e}")
            raise
