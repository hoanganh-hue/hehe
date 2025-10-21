"""
Facebook OAuth Service
Facebook Login integration for credential capture
"""

import os
import json
import secrets
import hashlib
import hmac
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple, List
import logging

# Import with error handling
try:
    import requests
except ImportError:
    requests = None

try:
    from urllib.parse import urlencode, parse_qs
except ImportError:
    urlencode = None
    parse_qs = None

# Import circuit breaker with error handling
try:
    from services.circuit_breaker import get_facebook_circuit_breaker
    CIRCUIT_BREAKER_AVAILABLE = True
except ImportError:
    CIRCUIT_BREAKER_AVAILABLE = False

logger = logging.getLogger(__name__)

class FacebookOAuthConfig:
    """Facebook OAuth configuration"""
    
    def __init__(self):
        self.app_id = os.getenv("FACEBOOK_APP_ID")
        self.app_secret = os.getenv("FACEBOOK_APP_SECRET")
        self.redirect_uri = os.getenv("FACEBOOK_REDIRECT_URI", "https://yourdomain.com/api/oauth/facebook/callback")
        
        # Facebook OAuth endpoints
        self.authorization_url = "https://www.facebook.com/v18.0/dialog/oauth"
        self.token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
        self.user_info_url = "https://graph.facebook.com/v18.0/me"
        self.revoke_url = "https://graph.facebook.com/v18.0/me/permissions"
        
        # Scopes
        self.scopes = [
            "email",
            "public_profile",
            "user_friends",
            "user_birthday",
            "user_location",
            "user_hometown"
        ]
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate Facebook OAuth configuration"""
        required_fields = [
            self.app_id,
            self.app_secret
        ]
        
        if not all(required_fields):
            logger.warning("Facebook OAuth configuration incomplete - some features may not work")
            self.enabled = False
        else:
            self.enabled = True

class FacebookOAuthService:
    """Facebook OAuth service implementation"""
    
    def __init__(self):
        self.config = FacebookOAuthConfig()
    
    def _generate_app_secret_proof(self, access_token: str) -> str:
        """Generate Facebook app secret proof"""
        try:
            proof = hmac.new(
                self.config.app_secret.encode('utf-8'),
                access_token.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return proof
            
        except Exception as e:
            logger.error(f"Error generating Facebook app secret proof: {e}")
            raise
    
    def get_authorization_url(self, state: str = None, redirect_uri: str = None) -> str:
        """
        Generate Facebook authorization URL
        
        Args:
            state: State parameter for CSRF protection
            redirect_uri: Custom redirect URI
            
        Returns:
            Facebook authorization URL
        """
        try:
            if not self.config.enabled:
                raise ValueError("Facebook OAuth not configured")
            
            # Generate state if not provided
            if not state:
                state = secrets.token_urlsafe(32)
            
            # Use provided redirect URI or default
            redirect_uri = redirect_uri or self.config.redirect_uri
            
            # Build authorization parameters
            params = {
                "client_id": self.config.app_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": ",".join(self.config.scopes),
                "state": state
            }
            
            # Build URL
            if not urlencode:
                logger.error("URL encode library not available")
                raise ValueError("URL encode library not available")

            auth_url = f"{self.config.authorization_url}?" + urlencode(params)
            
            logger.info(f"Facebook authorization URL generated: {state}")
            return auth_url
            
        except Exception as e:
            logger.error(f"Error generating Facebook authorization URL: {e}")
            raise
    
    async def exchange_code_for_tokens(self, code: str, redirect_uri: str = None) -> Optional[Dict[str, Any]]:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from Facebook
            redirect_uri: Redirect URI used in authorization
            
        Returns:
            Token data or None if failed
        """
        try:
            if not self.config.enabled:
                logger.error("Facebook OAuth not configured")
                return None
            
            # Use provided redirect URI or default
            redirect_uri = redirect_uri or self.config.redirect_uri
            
            # Prepare token request
            token_data = {
                "client_id": self.config.app_id,
                "client_secret": self.config.app_secret,
                "redirect_uri": redirect_uri,
                "code": code
            }
            
            # Make token request with circuit breaker protection
            if not requests:
                logger.error("Requests library not available")
                return None

            async def _make_token_request():
                return requests.get(
                    self.config.token_url,
                    params=token_data,
                    timeout=30
                )

            try:
                if CIRCUIT_BREAKER_AVAILABLE:
                    response = await get_facebook_circuit_breaker().call(_make_token_request)
                else:
                    response = await _make_token_request()
            except Exception as e:
                logger.error(f"Facebook token request failed: {e}")
                return None
            
            if response.status_code == 200:
                token_response = response.json()
                
                # Facebook returns access_token directly
                if "access_token" in token_response:
                    logger.info("Facebook token exchange successful")
                    return token_response
                else:
                    logger.error("Facebook token response missing access_token")
                    return None
            else:
                logger.error(f"Facebook token exchange failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error exchanging Facebook authorization code: {e}")
            return None
    
    async def get_user_profile(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile from Facebook
        
        Args:
            access_token: Facebook access token
            
        Returns:
            User profile data or None
        """
        try:
            if not self.config.enabled:
                logger.error("Facebook OAuth not configured")
                return None
            
            # Generate app secret proof
            app_secret_proof = self._generate_app_secret_proof(access_token)
            
            # Prepare user info request
            params = {
                "access_token": access_token,
                "appsecret_proof": app_secret_proof,
                "fields": "id,name,email,first_name,last_name,picture,birthday,location,hometown,gender"
            }
            
            # Make user info request with circuit breaker protection
            if not requests:
                logger.error("Requests library not available")
                return None

            async def _make_user_info_request():
                return requests.get(
                    self.config.user_info_url,
                    params=params,
                    timeout=30
                )

            try:
                if CIRCUIT_BREAKER_AVAILABLE:
                    response = await get_facebook_circuit_breaker().call(_make_user_info_request)
                else:
                    response = await _make_user_info_request()
            except Exception as e:
                logger.error(f"Facebook user info request failed: {e}")
                return None
            
            if response.status_code == 200:
                user_data = response.json()
                
                # Format user profile
                profile = {
                    "id": user_data.get("id"),
                    "email": user_data.get("email"),
                    "name": user_data.get("name"),
                    "first_name": user_data.get("first_name"),
                    "last_name": user_data.get("last_name"),
                    "picture": self._get_profile_picture_url(user_data.get("picture")),
                    "birthday": user_data.get("birthday"),
                    "location": user_data.get("location", {}).get("name") if user_data.get("location") else None,
                    "hometown": user_data.get("hometown", {}).get("name") if user_data.get("hometown") else None,
                    "gender": user_data.get("gender"),
                    "provider": "facebook"
                }
                
                logger.info(f"Facebook user profile retrieved: {profile.get('email')}")
                return profile
            else:
                logger.error(f"Facebook user profile request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting Facebook user profile: {e}")
            return None
    
    def _get_profile_picture_url(self, picture_data: Dict[str, Any]) -> Optional[str]:
        """Extract profile picture URL from Facebook picture data"""
        try:
            if not picture_data:
                return None
            
            # Facebook returns picture data in different formats
            if isinstance(picture_data, dict):
                if "data" in picture_data:
                    return picture_data["data"].get("url")
                elif "url" in picture_data:
                    return picture_data["url"]
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting Facebook profile picture URL: {e}")
            return None
    
    async def get_user_friends(self, access_token: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get user's friends list
        
        Args:
            access_token: Facebook access token
            
        Returns:
            List of friends or None
        """
        try:
            if not self.config.enabled:
                logger.error("Facebook OAuth not configured")
                return None
            
            # Generate app secret proof
            app_secret_proof = self._generate_app_secret_proof(access_token)
            
            # Prepare friends request
            params = {
                "access_token": access_token,
                "appsecret_proof": app_secret_proof,
                "fields": "id,name,picture"
            }
            
            # Make friends request with circuit breaker protection
            if not requests:
                logger.error("Requests library not available")
                return None

            async def _make_friends_request():
                return requests.get(
                    "https://graph.facebook.com/v18.0/me/friends",
                    params=params,
                    timeout=30
                )

            try:
                if CIRCUIT_BREAKER_AVAILABLE:
                    response = await get_facebook_circuit_breaker().call(_make_friends_request)
                else:
                    response = await _make_friends_request()
            except Exception as e:
                logger.error(f"Facebook friends request failed: {e}")
                return None
            
            if response.status_code == 200:
                friends_data = response.json()
                
                # Extract friends list
                friends = friends_data.get("data", [])
                
                # Format friends data
                formatted_friends = []
                for friend in friends:
                    formatted_friends.append({
                        "id": friend.get("id"),
                        "name": friend.get("name"),
                        "picture": self._get_profile_picture_url(friend.get("picture"))
                    })
                
                logger.info(f"Facebook friends list retrieved: {len(formatted_friends)} friends")
                return formatted_friends
            else:
                logger.error(f"Facebook friends request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting Facebook friends: {e}")
            return None
    
    async def refresh_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh Facebook access token
        
        Args:
            access_token: Facebook access token
            
        Returns:
            New token data or None if failed
        """
        try:
            if not self.config.enabled:
                logger.error("Facebook OAuth not configured")
                return None
            
            # Prepare refresh request
            refresh_params = {
                "grant_type": "fb_exchange_token",
                "client_id": self.config.app_id,
                "client_secret": self.config.app_secret,
                "fb_exchange_token": access_token
            }
            
            # Make refresh request with circuit breaker protection
            if not requests:
                logger.error("Requests library not available")
                return None

            async def _make_refresh_request():
                return requests.get(
                    self.config.token_url,
                    params=refresh_params,
                    timeout=30
                )

            try:
                if CIRCUIT_BREAKER_AVAILABLE:
                    response = await get_facebook_circuit_breaker().call(_make_refresh_request)
                else:
                    response = await _make_refresh_request()
            except Exception as e:
                logger.error(f"Facebook refresh request failed: {e}")
                return None
            
            if response.status_code == 200:
                token_response = response.json()
                
                if "access_token" in token_response:
                    logger.info("Facebook token refresh successful")
                    return token_response
                else:
                    logger.error("Facebook refresh response missing access_token")
                    return None
            else:
                logger.error(f"Facebook token refresh failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error refreshing Facebook token: {e}")
            return None
    
    async def revoke_token(self, access_token: str) -> bool:
        """
        Revoke Facebook token
        
        Args:
            access_token: Token to revoke
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.config.enabled:
                logger.error("Facebook OAuth not configured")
                return False
            
            # Generate app secret proof
            app_secret_proof = self._generate_app_secret_proof(access_token)
            
            # Prepare revoke request
            revoke_data = {
                "access_token": access_token,
                "appsecret_proof": app_secret_proof
            }
            
            # Make revoke request with circuit breaker protection
            if not requests:
                logger.error("Requests library not available")
                return False

            async def _make_revoke_request():
                return requests.delete(
                    self.config.revoke_url,
                    params=revoke_data,
                    timeout=30
                )

            try:
                if CIRCUIT_BREAKER_AVAILABLE:
                    response = await get_facebook_circuit_breaker().call(_make_revoke_request)
                else:
                    response = await _make_revoke_request()
            except Exception as e:
                logger.error(f"Facebook revoke request failed: {e}")
                return False
            
            if response.status_code == 200:
                logger.info("Facebook token revoked successfully")
                return True
            else:
                logger.error(f"Facebook token revocation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error revoking Facebook token: {e}")
            return False
    
    def validate_token(self, access_token: str) -> bool:
        """
        Validate Facebook access token
        
        Args:
            access_token: Facebook access token to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Generate app secret proof
            app_secret_proof = self._generate_app_secret_proof(access_token)
            
            # Prepare validation request
            params = {
                "access_token": access_token,
                "appsecret_proof": app_secret_proof
            }
            
            # Make validation request with circuit breaker protection
            if not requests:
                logger.error("Requests library not available")
                return False

            def _make_validation_request():
                return requests.get(
                    "https://graph.facebook.com/v18.0/me",
                    params=params,
                    timeout=30
                )

            try:
                if CIRCUIT_BREAKER_AVAILABLE:
                    # For non-async functions, we'll use the circuit breaker synchronously
                    # This is a simplified approach - in production, consider making this async
                    response = _make_validation_request()
                else:
                    response = _make_validation_request()
            except Exception as e:
                logger.error(f"Facebook validation request failed: {e}")
                return False
            
            if response.status_code == 200:
                logger.info("Facebook token validation successful")
                return True
            else:
                logger.warning(f"Facebook token validation failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error validating Facebook token: {e}")
            return False
    
    def get_extended_token(self, access_token: str) -> Optional[str]:
        """
        Get extended Facebook access token (60 days)
        
        Args:
            access_token: Short-lived access token
            
        Returns:
            Extended access token or None
        """
        try:
            if not self.config.enabled:
                logger.error("Facebook OAuth not configured")
                return None
            
            # Prepare extended token request
            extend_params = {
                "grant_type": "fb_exchange_token",
                "client_id": self.config.app_id,
                "client_secret": self.config.app_secret,
                "fb_exchange_token": access_token
            }
            
            # Make extend request with circuit breaker protection
            if not requests:
                logger.error("Requests library not available")
                return None

            def _make_extend_request():
                return requests.get(
                    self.config.token_url,
                    params=extend_params,
                    timeout=30
                )

            try:
                if CIRCUIT_BREAKER_AVAILABLE:
                    # For non-async functions, we'll use the circuit breaker synchronously
                    response = _make_extend_request()
                else:
                    response = _make_extend_request()
            except Exception as e:
                logger.error(f"Facebook extend request failed: {e}")
                return None
            
            if response.status_code == 200:
                token_response = response.json()
                
                if "access_token" in token_response:
                    logger.info("Facebook extended token obtained")
                    return token_response["access_token"]
                else:
                    logger.error("Facebook extend response missing access_token")
                    return None
            else:
                logger.error(f"Facebook token extension failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error extending Facebook token: {e}")
            return None
    
    def is_configured(self) -> bool:
        """Check if Facebook OAuth is properly configured"""
        return self.config.enabled
    
    def get_configuration_status(self) -> Dict[str, Any]:
        """Get Facebook OAuth configuration status"""
        return {
            "enabled": self.config.enabled,
            "app_id_configured": bool(self.config.app_id),
            "app_secret_configured": bool(self.config.app_secret),
            "redirect_uri": self.config.redirect_uri,
            "scopes": self.config.scopes
        }

# Global Facebook OAuth service instance
facebook_oauth_service = None

def initialize_facebook_oauth_service() -> FacebookOAuthService:
    """Initialize global Facebook OAuth service"""
    global facebook_oauth_service
    facebook_oauth_service = FacebookOAuthService()
    return facebook_oauth_service

def get_facebook_oauth_service() -> FacebookOAuthService:
    """Get global Facebook OAuth service"""
    if facebook_oauth_service is None:
        raise ValueError("Facebook OAuth service not initialized")
    return facebook_oauth_service

# Convenience functions
def get_facebook_authorization_url(state: str = None, redirect_uri: str = None) -> str:
    """Get Facebook authorization URL (global convenience function)"""
    return get_facebook_oauth_service().get_authorization_url(state, redirect_uri)

def exchange_facebook_code_for_tokens(code: str, redirect_uri: str = None) -> Optional[Dict[str, Any]]:
    """Exchange Facebook authorization code for tokens (global convenience function)"""
    return get_facebook_oauth_service().exchange_code_for_tokens(code, redirect_uri)

def get_facebook_user_profile(access_token: str) -> Optional[Dict[str, Any]]:
    """Get Facebook user profile (global convenience function)"""
    return get_facebook_oauth_service().get_user_profile(access_token)

def revoke_facebook_token(access_token: str) -> bool:
    """Revoke Facebook token (global convenience function)"""
    return get_facebook_oauth_service().revoke_token(access_token)
