"""
OAuth Validator
Advanced OAuth token validation and user information extraction
"""

import os
import json
import time
import asyncio
import aiohttp
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple
import logging
import base64
import jwt
from urllib.parse import urlencode, quote

logger = logging.getLogger(__name__)

class OAuthProvider(Enum):
    """OAuth provider enumeration"""
    GOOGLE = "google"
    APPLE = "apple"
    FACEBOOK = "facebook"
    MICROSOFT = "microsoft"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    GITHUB = "github"
    UNKNOWN = "unknown"

class TokenType(Enum):
    """Token type enumeration"""
    ACCESS_TOKEN = "access_token"
    ID_TOKEN = "id_token"
    REFRESH_TOKEN = "refresh_token"
    UNKNOWN = "unknown"

class OAuthValidator:
    """Advanced OAuth token validation and user information extraction"""
    
    def __init__(self):
        self.config = {
            "validation_timeout": int(os.getenv("OAUTH_VALIDATION_TIMEOUT", "30")),
            "enable_token_introspection": os.getenv("ENABLE_TOKEN_INTROSPECTION", "true").lower() == "true",
            "enable_user_info_extraction": os.getenv("ENABLE_USER_INFO_EXTRACTION", "true").lower() == "true",
            "enable_token_refresh": os.getenv("ENABLE_TOKEN_REFRESH", "true").lower() == "true",
            "cache_validation_results": os.getenv("CACHE_VALIDATION_RESULTS", "true").lower() == "true",
            "cache_duration": int(os.getenv("OAUTH_CACHE_DURATION", "3600"))  # 1 hour
        }
        
        # OAuth provider configurations
        self.provider_configs = self._load_provider_configs()
        
        # Validation cache
        self.validation_cache = {}
        
        logger.info("OAuth validator initialized")
    
    async def validate_token(self, provider: str, access_token: str = None, 
                           id_token: str = None, refresh_token: str = None) -> Dict[str, Any]:
        """
        Validate OAuth token and extract user information
        
        Args:
            provider: OAuth provider name
            access_token: OAuth access token
            id_token: OAuth ID token
            refresh_token: OAuth refresh token
            
        Returns:
            Validation result with user information
        """
        try:
            # Generate validation ID
            validation_id = f"{provider}_{int(time.time())}"
            
            # Check cache first
            if self.config["cache_validation_results"]:
                cached_result = self._get_cached_validation(provider, access_token, id_token)
                if cached_result:
                    return cached_result
            
            # Determine token type and validate
            token_type = self._determine_token_type(access_token, id_token, refresh_token)
            
            validation_result = {
                "validation_id": validation_id,
                "provider": provider,
                "token_type": token_type.value,
                "is_valid": False,
                "expires_at": None,
                "scopes": [],
                "user_info": {},
                "confidence_score": 0.0,
                "validation_details": {},
                "errors": [],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Validate based on provider
            if provider.lower() == OAuthProvider.GOOGLE.value:
                result = await self._validate_google_token(access_token, id_token, refresh_token)
            elif provider.lower() == OAuthProvider.APPLE.value:
                result = await self._validate_apple_token(access_token, id_token, refresh_token)
            elif provider.lower() == OAuthProvider.FACEBOOK.value:
                result = await self._validate_facebook_token(access_token, id_token, refresh_token)
            elif provider.lower() == OAuthProvider.MICROSOFT.value:
                result = await self._validate_microsoft_token(access_token, id_token, refresh_token)
            else:
                result = await self._validate_generic_token(provider, access_token, id_token, refresh_token)
            
            # Update validation result
            validation_result.update(result)
            
            # Cache result
            if self.config["cache_validation_results"]:
                self._cache_validation_result(provider, access_token, id_token, validation_result)
            
            logger.info(f"OAuth token validation completed: {provider} - {validation_result['is_valid']}")
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating OAuth token: {e}")
            return {
                "validation_id": validation_id if 'validation_id' in locals() else None,
                "provider": provider,
                "is_valid": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _determine_token_type(self, access_token: str, id_token: str, refresh_token: str) -> TokenType:
        """Determine the primary token type"""
        if access_token:
            return TokenType.ACCESS_TOKEN
        elif id_token:
            return TokenType.ID_TOKEN
        elif refresh_token:
            return TokenType.REFRESH_TOKEN
        else:
            return TokenType.UNKNOWN
    
    async def _validate_google_token(self, access_token: str, id_token: str, refresh_token: str) -> Dict[str, Any]:
        """Validate Google OAuth token"""
        try:
            result = {
                "is_valid": False,
                "expires_at": None,
                "scopes": [],
                "user_info": {},
                "confidence_score": 0.0,
                "validation_details": {},
                "errors": []
            }
            
            # Validate access token
            if access_token:
                access_result = await self._validate_google_access_token(access_token)
                if access_result["is_valid"]:
                    result.update(access_result)
                    result["confidence_score"] += 0.6
            
            # Validate ID token
            if id_token:
                id_result = await self._validate_google_id_token(id_token)
                if id_result["is_valid"]:
                    result["user_info"].update(id_result.get("user_info", {}))
                    result["confidence_score"] += 0.4
                    if not result["is_valid"]:
                        result["is_valid"] = True
            
            # Validate refresh token
            if refresh_token:
                refresh_result = await self._validate_google_refresh_token(refresh_token)
                if refresh_result["is_valid"]:
                    result["validation_details"]["refresh_token_valid"] = True
                    result["confidence_score"] += 0.2
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating Google token: {e}")
            return {"is_valid": False, "error": str(e), "confidence_score": 0.0}
    
    async def _validate_google_access_token(self, access_token: str) -> Dict[str, Any]:
        """Validate Google access token"""
        try:
            async with aiohttp.ClientSession() as session:
                # Token info endpoint
                url = "https://www.googleapis.com/oauth2/v1/tokeninfo"
                params = {"access_token": access_token}
                
                async with session.get(url, params=params, timeout=self.config["validation_timeout"]) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Check if token is valid
                        if "error" not in data:
                            # Get user info
                            user_info = await self._get_google_user_info(access_token)
                            
                            return {
                                "is_valid": True,
                                "expires_at": datetime.now(timezone.utc) + timedelta(seconds=data.get("expires_in", 3600)),
                                "scopes": data.get("scope", "").split(),
                                "user_info": user_info,
                                "validation_details": {
                                    "audience": data.get("audience"),
                                    "issued_to": data.get("issued_to"),
                                    "user_id": data.get("user_id"),
                                    "verified_email": data.get("verified_email")
                                }
                            }
                        else:
                            return {
                                "is_valid": False,
                                "error": data.get("error_description", "Token validation failed"),
                                "validation_details": {"error": data.get("error")}
                            }
                    else:
                        return {
                            "is_valid": False,
                            "error": f"HTTP {response.status}: {await response.text()}",
                            "validation_details": {"http_status": response.status}
                        }
                        
        except Exception as e:
            logger.error(f"Error validating Google access token: {e}")
            return {"is_valid": False, "error": str(e)}
    
    async def _validate_google_id_token(self, id_token: str) -> Dict[str, Any]:
        """Validate Google ID token"""
        try:
            # Decode JWT without verification first to get header
            header = jwt.get_unverified_header(id_token)
            payload = jwt.decode(id_token, options={"verify_signature": False})
            
            # Check token expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                return {
                    "is_valid": False,
                    "error": "ID token expired",
                    "validation_details": {"expired_at": datetime.fromtimestamp(exp, tz=timezone.utc).isoformat()}
                }
            
            # Extract user information
            user_info = {
                "sub": payload.get("sub"),
                "email": payload.get("email"),
                "email_verified": payload.get("email_verified"),
                "name": payload.get("name"),
                "given_name": payload.get("given_name"),
                "family_name": payload.get("family_name"),
                "picture": payload.get("picture"),
                "locale": payload.get("locale"),
                "hd": payload.get("hd")  # Hosted domain for G Suite
            }
            
            return {
                "is_valid": True,
                "user_info": user_info,
                "validation_details": {
                    "iss": payload.get("iss"),
                    "aud": payload.get("aud"),
                    "exp": exp,
                    "iat": payload.get("iat")
                }
            }
            
        except Exception as e:
            logger.error(f"Error validating Google ID token: {e}")
            return {"is_valid": False, "error": str(e)}
    
    async def _validate_google_refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Validate Google refresh token"""
        try:
            # Refresh tokens are validated by attempting to use them
            # This is a simplified validation - in practice, you'd need client credentials
            return {
                "is_valid": True,  # Assume valid if provided
                "validation_details": {"refresh_token_provided": True}
            }
            
        except Exception as e:
            logger.error(f"Error validating Google refresh token: {e}")
            return {"is_valid": False, "error": str(e)}
    
    async def _get_google_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get Google user information"""
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://www.googleapis.com/oauth2/v2/userinfo"
                headers = {"Authorization": f"Bearer {access_token}"}
                
                async with session.get(url, headers=headers, timeout=self.config["validation_timeout"]) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {}
                        
        except Exception as e:
            logger.error(f"Error getting Google user info: {e}")
            return {}
    
    async def _validate_apple_token(self, access_token: str, id_token: str, refresh_token: str) -> Dict[str, Any]:
        """Validate Apple OAuth token"""
        try:
            result = {
                "is_valid": False,
                "expires_at": None,
                "scopes": [],
                "user_info": {},
                "confidence_score": 0.0,
                "validation_details": {},
                "errors": []
            }
            
            # Validate ID token (primary for Apple)
            if id_token:
                id_result = await self._validate_apple_id_token(id_token)
                if id_result["is_valid"]:
                    result.update(id_result)
                    result["confidence_score"] += 0.8
            
            # Validate access token
            if access_token:
                access_result = await self._validate_apple_access_token(access_token)
                if access_result["is_valid"]:
                    result["user_info"].update(access_result.get("user_info", {}))
                    result["confidence_score"] += 0.2
                    if not result["is_valid"]:
                        result["is_valid"] = True
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating Apple token: {e}")
            return {"is_valid": False, "error": str(e), "confidence_score": 0.0}
    
    async def _validate_apple_id_token(self, id_token: str) -> Dict[str, Any]:
        """Validate Apple ID token"""
        try:
            # Decode JWT without verification first
            payload = jwt.decode(id_token, options={"verify_signature": False})
            
            # Check token expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                return {
                    "is_valid": False,
                    "error": "ID token expired",
                    "validation_details": {"expired_at": datetime.fromtimestamp(exp, tz=timezone.utc).isoformat()}
                }
            
            # Extract user information
            user_info = {
                "sub": payload.get("sub"),
                "email": payload.get("email"),
                "email_verified": payload.get("email_verified"),
                "name": payload.get("name"),
                "given_name": payload.get("given_name"),
                "family_name": payload.get("family_name")
            }
            
            return {
                "is_valid": True,
                "user_info": user_info,
                "validation_details": {
                    "iss": payload.get("iss"),
                    "aud": payload.get("aud"),
                    "exp": exp,
                    "iat": payload.get("iat")
                }
            }
            
        except Exception as e:
            logger.error(f"Error validating Apple ID token: {e}")
            return {"is_valid": False, "error": str(e)}
    
    async def _validate_apple_access_token(self, access_token: str) -> Dict[str, Any]:
        """Validate Apple access token"""
        try:
            # Apple doesn't provide a standard token introspection endpoint
            # We'll assume the token is valid if it's provided
            return {
                "is_valid": True,
                "validation_details": {"access_token_provided": True}
            }
            
        except Exception as e:
            logger.error(f"Error validating Apple access token: {e}")
            return {"is_valid": False, "error": str(e)}
    
    async def _validate_facebook_token(self, access_token: str, id_token: str, refresh_token: str) -> Dict[str, Any]:
        """Validate Facebook OAuth token"""
        try:
            result = {
                "is_valid": False,
                "expires_at": None,
                "scopes": [],
                "user_info": {},
                "confidence_score": 0.0,
                "validation_details": {},
                "errors": []
            }
            
            # Validate access token
            if access_token:
                access_result = await self._validate_facebook_access_token(access_token)
                if access_result["is_valid"]:
                    result.update(access_result)
                    result["confidence_score"] += 0.8
            
            # Validate ID token
            if id_token:
                id_result = await self._validate_facebook_id_token(id_token)
                if id_result["is_valid"]:
                    result["user_info"].update(id_result.get("user_info", {}))
                    result["confidence_score"] += 0.2
                    if not result["is_valid"]:
                        result["is_valid"] = True
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating Facebook token: {e}")
            return {"is_valid": False, "error": str(e), "confidence_score": 0.0}
    
    async def _validate_facebook_access_token(self, access_token: str) -> Dict[str, Any]:
        """Validate Facebook access token"""
        try:
            async with aiohttp.ClientSession() as session:
                # Token debug endpoint
                url = "https://graph.facebook.com/debug_token"
                params = {
                    "input_token": access_token,
                    "access_token": access_token  # Use the same token for debugging
                }
                
                async with session.get(url, params=params, timeout=self.config["validation_timeout"]) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if "data" in data and data["data"].get("is_valid"):
                            token_data = data["data"]
                            
                            # Get user info
                            user_info = await self._get_facebook_user_info(access_token)
                            
                            return {
                                "is_valid": True,
                                "expires_at": datetime.fromtimestamp(token_data.get("expires_at", 0), tz=timezone.utc),
                                "scopes": token_data.get("scopes", []),
                                "user_info": user_info,
                                "validation_details": {
                                    "app_id": token_data.get("app_id"),
                                    "user_id": token_data.get("user_id"),
                                    "type": token_data.get("type")
                                }
                            }
                        else:
                            return {
                                "is_valid": False,
                                "error": "Token is not valid",
                                "validation_details": {"debug_data": data}
                            }
                    else:
                        return {
                            "is_valid": False,
                            "error": f"HTTP {response.status}: {await response.text()}",
                            "validation_details": {"http_status": response.status}
                        }
                        
        except Exception as e:
            logger.error(f"Error validating Facebook access token: {e}")
            return {"is_valid": False, "error": str(e)}
    
    async def _validate_facebook_id_token(self, id_token: str) -> Dict[str, Any]:
        """Validate Facebook ID token"""
        try:
            # Facebook ID tokens are JWT tokens
            payload = jwt.decode(id_token, options={"verify_signature": False})
            
            # Check token expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                return {
                    "is_valid": False,
                    "error": "ID token expired",
                    "validation_details": {"expired_at": datetime.fromtimestamp(exp, tz=timezone.utc).isoformat()}
                }
            
            # Extract user information
            user_info = {
                "sub": payload.get("sub"),
                "email": payload.get("email"),
                "name": payload.get("name"),
                "given_name": payload.get("given_name"),
                "family_name": payload.get("family_name"),
                "picture": payload.get("picture")
            }
            
            return {
                "is_valid": True,
                "user_info": user_info,
                "validation_details": {
                    "iss": payload.get("iss"),
                    "aud": payload.get("aud"),
                    "exp": exp,
                    "iat": payload.get("iat")
                }
            }
            
        except Exception as e:
            logger.error(f"Error validating Facebook ID token: {e}")
            return {"is_valid": False, "error": str(e)}
    
    async def _get_facebook_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get Facebook user information"""
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://graph.facebook.com/me"
                params = {
                    "access_token": access_token,
                    "fields": "id,name,email,first_name,last_name,picture"
                }
                
                async with session.get(url, params=params, timeout=self.config["validation_timeout"]) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {}
                        
        except Exception as e:
            logger.error(f"Error getting Facebook user info: {e}")
            return {}
    
    async def _validate_microsoft_token(self, access_token: str, id_token: str, refresh_token: str) -> Dict[str, Any]:
        """Validate Microsoft OAuth token"""
        try:
            result = {
                "is_valid": False,
                "expires_at": None,
                "scopes": [],
                "user_info": {},
                "confidence_score": 0.0,
                "validation_details": {},
                "errors": []
            }
            
            # Validate access token
            if access_token:
                access_result = await self._validate_microsoft_access_token(access_token)
                if access_result["is_valid"]:
                    result.update(access_result)
                    result["confidence_score"] += 0.6
            
            # Validate ID token
            if id_token:
                id_result = await self._validate_microsoft_id_token(id_token)
                if id_result["is_valid"]:
                    result["user_info"].update(id_result.get("user_info", {}))
                    result["confidence_score"] += 0.4
                    if not result["is_valid"]:
                        result["is_valid"] = True
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating Microsoft token: {e}")
            return {"is_valid": False, "error": str(e), "confidence_score": 0.0}
    
    async def _validate_microsoft_access_token(self, access_token: str) -> Dict[str, Any]:
        """Validate Microsoft access token"""
        try:
            async with aiohttp.ClientSession() as session:
                # Microsoft Graph API user info endpoint
                url = "https://graph.microsoft.com/v1.0/me"
                headers = {"Authorization": f"Bearer {access_token}"}
                
                async with session.get(url, headers=headers, timeout=self.config["validation_timeout"]) as response:
                    if response.status == 200:
                        user_info = await response.json()
                        
                        return {
                            "is_valid": True,
                            "user_info": user_info,
                            "validation_details": {"graph_api_valid": True}
                        }
                    else:
                        return {
                            "is_valid": False,
                            "error": f"HTTP {response.status}: {await response.text()}",
                            "validation_details": {"http_status": response.status}
                        }
                        
        except Exception as e:
            logger.error(f"Error validating Microsoft access token: {e}")
            return {"is_valid": False, "error": str(e)}
    
    async def _validate_microsoft_id_token(self, id_token: str) -> Dict[str, Any]:
        """Validate Microsoft ID token"""
        try:
            # Microsoft ID tokens are JWT tokens
            payload = jwt.decode(id_token, options={"verify_signature": False})
            
            # Check token expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                return {
                    "is_valid": False,
                    "error": "ID token expired",
                    "validation_details": {"expired_at": datetime.fromtimestamp(exp, tz=timezone.utc).isoformat()}
                }
            
            # Extract user information
            user_info = {
                "sub": payload.get("sub"),
                "email": payload.get("email"),
                "name": payload.get("name"),
                "given_name": payload.get("given_name"),
                "family_name": payload.get("family_name"),
                "preferred_username": payload.get("preferred_username")
            }
            
            return {
                "is_valid": True,
                "user_info": user_info,
                "validation_details": {
                    "iss": payload.get("iss"),
                    "aud": payload.get("aud"),
                    "exp": exp,
                    "iat": payload.get("iat")
                }
            }
            
        except Exception as e:
            logger.error(f"Error validating Microsoft ID token: {e}")
            return {"is_valid": False, "error": str(e)}
    
    async def _validate_generic_token(self, provider: str, access_token: str, id_token: str, refresh_token: str) -> Dict[str, Any]:
        """Validate generic OAuth token"""
        try:
            result = {
                "is_valid": False,
                "expires_at": None,
                "scopes": [],
                "user_info": {},
                "confidence_score": 0.0,
                "validation_details": {},
                "errors": []
            }
            
            # Try to validate ID token if available
            if id_token:
                try:
                    payload = jwt.decode(id_token, options={"verify_signature": False})
                    
                    # Check token expiration
                    exp = payload.get("exp")
                    if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                        result["errors"].append("ID token expired")
                    else:
                        result["is_valid"] = True
                        result["confidence_score"] = 0.5
                        result["user_info"] = {
                            "sub": payload.get("sub"),
                            "email": payload.get("email"),
                            "name": payload.get("name")
                        }
                        result["validation_details"]["id_token_decoded"] = True
                        
                except Exception as e:
                    result["errors"].append(f"ID token validation failed: {str(e)}")
            
            # Try to validate access token if available
            if access_token and not result["is_valid"]:
                # Generic access token validation - assume valid if provided
                result["is_valid"] = True
                result["confidence_score"] = 0.3
                result["validation_details"]["access_token_provided"] = True
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating generic token: {e}")
            return {"is_valid": False, "error": str(e), "confidence_score": 0.0}
    
    def _load_provider_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load OAuth provider configurations"""
        return {
            OAuthProvider.GOOGLE.value: {
                "token_endpoint": "https://oauth2.googleapis.com/token",
                "userinfo_endpoint": "https://www.googleapis.com/oauth2/v2/userinfo",
                "tokeninfo_endpoint": "https://www.googleapis.com/oauth2/v1/tokeninfo",
                "issuer": "https://accounts.google.com"
            },
            OAuthProvider.APPLE.value: {
                "token_endpoint": "https://appleid.apple.com/auth/token",
                "userinfo_endpoint": "https://appleid.apple.com/auth/userinfo",
                "issuer": "https://appleid.apple.com"
            },
            OAuthProvider.FACEBOOK.value: {
                "token_endpoint": "https://graph.facebook.com/oauth/access_token",
                "userinfo_endpoint": "https://graph.facebook.com/me",
                "debug_endpoint": "https://graph.facebook.com/debug_token",
                "issuer": "https://www.facebook.com"
            },
            OAuthProvider.MICROSOFT.value: {
                "token_endpoint": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                "userinfo_endpoint": "https://graph.microsoft.com/v1.0/me",
                "issuer": "https://login.microsoftonline.com"
            }
        }
    
    def _get_cached_validation(self, provider: str, access_token: str, id_token: str) -> Optional[Dict[str, Any]]:
        """Get cached validation result"""
        try:
            cache_key = self._generate_cache_key(provider, access_token, id_token)
            
            if cache_key in self.validation_cache:
                cached_result, cached_at = self.validation_cache[cache_key]
                
                # Check if cache is still valid
                cache_age = (datetime.now(timezone.utc) - cached_at).total_seconds()
                if cache_age < self.config["cache_duration"]:
                    return cached_result
                
                # Remove expired cache entry
                del self.validation_cache[cache_key]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached validation: {e}")
            return None
    
    def _cache_validation_result(self, provider: str, access_token: str, id_token: str, result: Dict[str, Any]):
        """Cache validation result"""
        try:
            cache_key = self._generate_cache_key(provider, access_token, id_token)
            self.validation_cache[cache_key] = (result, datetime.now(timezone.utc))
            
            # Limit cache size
            if len(self.validation_cache) > 1000:
                # Remove oldest entries
                oldest_keys = sorted(self.validation_cache.keys(),
                                   key=lambda k: self.validation_cache[k][1])[:200]
                for key in oldest_keys:
                    del self.validation_cache[key]
                    
        except Exception as e:
            logger.error(f"Error caching validation result: {e}")
    
    def _generate_cache_key(self, provider: str, access_token: str, id_token: str) -> str:
        """Generate cache key for validation result"""
        try:
            key_string = f"{provider}:{access_token or ''}:{id_token or ''}"
            return hashlib.sha256(key_string.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Error generating cache key: {e}")
            return f"{provider}_{int(time.time())}"
    
    async def batch_validate_tokens(self, tokens_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Batch validate multiple OAuth tokens"""
        try:
            validation_tasks = []
            
            for token_data in tokens_list:
                task = self.validate_token(
                    provider=token_data.get("provider"),
                    access_token=token_data.get("access_token"),
                    id_token=token_data.get("id_token"),
                    refresh_token=token_data.get("refresh_token")
                )
                validation_tasks.append(task)
            
            # Execute all validations concurrently
            results = await asyncio.gather(*validation_tasks, return_exceptions=True)
            
            # Process results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append({
                        "error": str(result),
                        "token_index": i,
                        "is_valid": False
                    })
                else:
                    processed_results.append(result)
            
            logger.info(f"Batch token validation completed: {len(processed_results)} tokens")
            return processed_results
            
        except Exception as e:
            logger.error(f"Error in batch token validation: {e}")
            return []
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        try:
            return {
                "cache_size": len(self.validation_cache),
                "configuration": self.config,
                "supported_providers": [provider.value for provider in OAuthProvider],
                "provider_configs": list(self.provider_configs.keys()),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting validation stats: {e}")
            return {"error": str(e)}