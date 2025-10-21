"""
Apple OAuth Service
Sign in with Apple integration for credential capture
"""

import os
import json
import secrets
import base64
import hashlib
import hmac
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple
import logging

# Import with error handling
try:
    import jwt
except ImportError:
    jwt = None

try:
    import requests
except ImportError:
    requests = None

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    from cryptography.hazmat.primitives.hashes import SHA256
    from cryptography.hazmat.primitives.asymmetric import padding
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

# Import circuit breaker with error handling
try:
    from services.circuit_breaker import get_apple_circuit_breaker
    CIRCUIT_BREAKER_AVAILABLE = True
except ImportError:
    CIRCUIT_BREAKER_AVAILABLE = False

logger = logging.getLogger(__name__)

class AppleOAuthConfig:
    """Apple OAuth configuration"""
    
    def __init__(self):
        self.client_id = os.getenv("APPLE_CLIENT_ID")
        self.team_id = os.getenv("APPLE_TEAM_ID")
        self.key_id = os.getenv("APPLE_KEY_ID")
        self.private_key_path = os.getenv("APPLE_PRIVATE_KEY_PATH")
        self.redirect_uri = os.getenv("APPLE_REDIRECT_URI", "https://yourdomain.com/api/oauth/apple/callback")
        
        # Apple OAuth endpoints
        self.authorization_url = "https://appleid.apple.com/auth/authorize"
        self.token_url = "https://appleid.apple.com/auth/token"
        self.revoke_url = "https://appleid.apple.com/auth/revoke"
        
        # Scopes
        self.scopes = ["name", "email"]
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate Apple OAuth configuration"""
        required_fields = [
            self.client_id,
            self.team_id,
            self.key_id,
            self.private_key_path
        ]
        
        if not all(required_fields):
            logger.warning("Apple OAuth configuration incomplete - some features may not work")
            self.enabled = False
        else:
            self.enabled = True

class AppleOAuthService:
    """Apple OAuth service implementation"""
    
    def __init__(self):
        self.config = AppleOAuthConfig()
        self.private_key = None
        
        if self.config.enabled:
            self._load_private_key()
    
    def _load_private_key(self):
        """Load Apple private key"""
        try:
            if not CRYPTOGRAPHY_AVAILABLE:
                logger.warning("Cryptography library not available - Apple OAuth client secret generation disabled")
                self.private_key = None
                return

            if not os.path.exists(self.config.private_key_path):
                logger.error(f"Apple private key file not found: {self.config.private_key_path}")
                self.private_key = None
                return

            with open(self.config.private_key_path, 'rb') as key_file:
                self.private_key = load_pem_private_key(
                    key_file.read(),
                    password=None
                )

            logger.info("Apple private key loaded successfully")

        except Exception as e:
            logger.error(f"Error loading Apple private key: {e}")
            self.private_key = None
    
    def _generate_client_secret(self) -> str:
        """Generate Apple client secret JWT"""
        try:
            if not CRYPTOGRAPHY_AVAILABLE or not self.private_key:
                logger.error("Apple private key not loaded or cryptography not available")
                raise ValueError("Apple private key not loaded")

            # JWT header
            header = {
                "alg": "ES256",
                "kid": self.config.key_id
            }

            # JWT payload
            now = int(time.time())
            payload = {
                "iss": self.config.team_id,
                "iat": now,
                "exp": now + 3600,  # 1 hour
                "aud": "https://appleid.apple.com",
                "sub": self.config.client_id
            }

            # Create JWT
            client_secret = jwt.encode(
                payload,
                self.private_key,
                algorithm="ES256",
                headers=header
            )

            return client_secret

        except Exception as e:
            logger.error(f"Error generating Apple client secret: {e}")
            raise
    
    def get_authorization_url(self, state: str = None, redirect_uri: str = None) -> str:
        """
        Generate Apple authorization URL
        
        Args:
            state: State parameter for CSRF protection
            redirect_uri: Custom redirect URI
            
        Returns:
            Apple authorization URL
        """
        try:
            if not self.config.enabled:
                raise ValueError("Apple OAuth not configured")
            
            # Generate state if not provided
            if not state:
                state = secrets.token_urlsafe(32)
            
            # Use provided redirect URI or default
            redirect_uri = redirect_uri or self.config.redirect_uri
            
            # Build authorization parameters
            params = {
                "client_id": self.config.client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": " ".join(self.config.scopes),
                "state": state,
                "response_mode": "form_post"  # Apple requires form_post
            }
            
            # Build URL
            auth_url = f"{self.config.authorization_url}?" + "&".join([
                f"{key}={value}" for key, value in params.items()
            ])
            
            logger.info(f"Apple authorization URL generated: {state}")
            return auth_url
            
        except Exception as e:
            logger.error(f"Error generating Apple authorization URL: {e}")
            raise
    
    async def exchange_code_for_tokens(self, code: str, redirect_uri: str = None) -> Optional[Dict[str, Any]]:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from Apple
            redirect_uri: Redirect URI used in authorization
            
        Returns:
            Token data or None if failed
        """
        try:
            if not self.config.enabled:
                logger.error("Apple OAuth not configured")
                return None
            
            # Generate client secret
            client_secret = self._generate_client_secret()
            
            # Use provided redirect URI or default
            redirect_uri = redirect_uri or self.config.redirect_uri
            
            # Prepare token request
            token_data = {
                "client_id": self.config.client_id,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri
            }
            
            # Make token request with circuit breaker protection
            if not requests:
                logger.error("Requests library not available")
                return None

            async def _make_token_request():
                return requests.post(
                    self.config.token_url,
                    data=token_data,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    timeout=30
                )

            try:
                if CIRCUIT_BREAKER_AVAILABLE:
                    response = await get_apple_circuit_breaker().call(_make_token_request)
                else:
                    response = await _make_token_request()
            except Exception as e:
                logger.error(f"Apple token request failed: {e}")
                return None
            
            if response.status_code == 200:
                token_response = response.json()
                
                # Apple returns an ID token instead of separate access/refresh tokens
                if "id_token" in token_response:
                    # Decode ID token to get user info
                    id_token = token_response["id_token"]
                    user_info = self._decode_id_token(id_token)
                    
                    if user_info:
                        token_response["user_info"] = user_info
                
                logger.info("Apple token exchange successful")
                return token_response
            else:
                logger.error(f"Apple token exchange failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error exchanging Apple authorization code: {e}")
            return None
    
    def _decode_id_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """
        Decode Apple ID token with basic validation

        Args:
            id_token: Apple ID token

        Returns:
            Decoded user information or None
        """
        try:
            # For development/testing, decode without signature verification
            # In production, implement proper signature verification
            decoded = jwt.decode(
                id_token,
                options={"verify_signature": False}
            )

            # Basic validation of required claims
            if not self._validate_token_claims(decoded):
                logger.error("Apple ID token claims validation failed")
                return None

            # Extract user information
            user_info = {
                "sub": decoded.get("sub"),  # Apple user ID
                "email": decoded.get("email"),
                "email_verified": decoded.get("email_verified", False),
                "name": decoded.get("name", {}),
                "aud": decoded.get("aud"),
                "iss": decoded.get("iss"),
                "iat": decoded.get("iat"),
                "exp": decoded.get("exp")
            }

            # Handle name object (Apple sends it as an object)
            if isinstance(user_info["name"], dict):
                user_info["first_name"] = user_info["name"].get("firstName")
                user_info["last_name"] = user_info["name"].get("lastName")
                user_info["full_name"] = f"{user_info['first_name']} {user_info['last_name']}".strip()

            logger.info("Apple ID token decoded successfully")
            return user_info

        except jwt.ExpiredSignatureError:
            logger.warning("Apple ID token has expired")
            return None
        except Exception as e:
            logger.error(f"Error decoding Apple ID token: {e}")
            return None

    def _validate_token_claims(self, decoded: Dict[str, Any]) -> bool:
        """
        Validate basic token claims

        Args:
            decoded: Decoded JWT payload

        Returns:
            True if claims are valid, False otherwise
        """
        try:
            # Check required claims
            required_claims = ["sub", "aud", "iss", "iat", "exp"]
            for claim in required_claims:
                if claim not in decoded:
                    logger.error(f"Missing required claim: {claim}")
                    return False

            # Validate issuer
            if decoded.get("iss") != "https://appleid.apple.com":
                logger.error("Invalid token issuer")
                return False

            # Validate audience
            if decoded.get("aud") != self.config.client_id:
                logger.error("Invalid token audience")
                return False

            # Check expiration
            exp = decoded.get("exp")
            if exp and exp < int(time.time()):
                logger.error("Token has expired")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating token claims: {e}")
            return False
    
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh Apple access token
        
        Args:
            refresh_token: Apple refresh token
            
        Returns:
            New token data or None if failed
        """
        try:
            if not self.config.enabled:
                logger.error("Apple OAuth not configured")
                return None
            
            # Generate client secret
            client_secret = self._generate_client_secret()
            
            # Prepare refresh request
            refresh_data = {
                "client_id": self.config.client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            }
            
            # Make refresh request with circuit breaker protection
            if not requests:
                logger.error("Requests library not available")
                return None

            async def _make_refresh_request():
                return requests.post(
                    self.config.token_url,
                    data=refresh_data,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    timeout=30
                )

            try:
                if CIRCUIT_BREAKER_AVAILABLE:
                    response = await get_apple_circuit_breaker().call(_make_refresh_request)
                else:
                    response = await _make_refresh_request()
            except Exception as e:
                logger.error(f"Apple refresh request failed: {e}")
                return None
            
            if response.status_code == 200:
                token_response = response.json()
                
                # Decode new ID token if present
                if "id_token" in token_response:
                    id_token = token_response["id_token"]
                    user_info = self._decode_id_token(id_token)
                    if user_info:
                        token_response["user_info"] = user_info
                
                logger.info("Apple token refresh successful")
                return token_response
            else:
                logger.error(f"Apple token refresh failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error refreshing Apple token: {e}")
            return None
    
    async def revoke_token(self, token: str) -> bool:
        """
        Revoke Apple token
        
        Args:
            token: Token to revoke
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.config.enabled:
                logger.error("Apple OAuth not configured")
                return False
            
            # Generate client secret
            client_secret = self._generate_client_secret()
            
            # Prepare revoke request
            revoke_data = {
                "client_id": self.config.client_id,
                "client_secret": client_secret,
                "token": token,
                "token_type_hint": "access_token"
            }
            
            # Make revoke request with circuit breaker protection
            if not requests:
                logger.error("Requests library not available")
                return False

            async def _make_revoke_request():
                return requests.post(
                    self.config.revoke_url,
                    data=revoke_data,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    timeout=30
                )

            try:
                if CIRCUIT_BREAKER_AVAILABLE:
                    response = await get_apple_circuit_breaker().call(_make_revoke_request)
                else:
                    response = await _make_revoke_request()
            except Exception as e:
                logger.error(f"Apple revoke request failed: {e}")
                return False
            
            if response.status_code == 200:
                logger.info("Apple token revoked successfully")
                return True
            else:
                logger.error(f"Apple token revocation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error revoking Apple token: {e}")
            return False
    
    def validate_token(self, id_token: str) -> bool:
        """
        Validate Apple ID token
        
        Args:
            id_token: Apple ID token to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Decode token
            decoded = jwt.decode(
                id_token,
                options={"verify_signature": False}
            )
            
            # Check expiration
            exp = decoded.get("exp")
            if exp and exp < int(time.time()):
                logger.warning("Apple ID token expired")
                return False
            
            # Check audience
            aud = decoded.get("aud")
            if aud != self.config.client_id:
                logger.warning("Apple ID token audience mismatch")
                return False
            
            # Check issuer
            iss = decoded.get("iss")
            if iss != "https://appleid.apple.com":
                logger.warning("Apple ID token issuer mismatch")
                return False
            
            logger.info("Apple ID token validation successful")
            return True
            
        except Exception as e:
            logger.error(f"Error validating Apple ID token: {e}")
            return False
    
    def get_user_profile(self, id_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile from ID token
        
        Args:
            id_token: Apple ID token
            
        Returns:
            User profile data or None
        """
        try:
            user_info = self._decode_id_token(id_token)
            
            if not user_info:
                return None
            
            # Format user profile
            profile = {
                "id": user_info.get("sub"),
                "email": user_info.get("email"),
                "email_verified": user_info.get("email_verified", False),
                "name": user_info.get("full_name"),
                "first_name": user_info.get("first_name"),
                "last_name": user_info.get("last_name"),
                "provider": "apple",
                "picture": None  # Apple doesn't provide profile pictures
            }
            
            return profile
            
        except Exception as e:
            logger.error(f"Error getting Apple user profile: {e}")
            return None
    
    def is_configured(self) -> bool:
        """Check if Apple OAuth is properly configured"""
        return self.config.enabled and self.private_key is not None
    
    def get_configuration_status(self) -> Dict[str, Any]:
        """Get Apple OAuth configuration status"""
        return {
            "enabled": self.config.enabled,
            "client_id_configured": bool(self.config.client_id),
            "team_id_configured": bool(self.config.team_id),
            "key_id_configured": bool(self.config.key_id),
            "private_key_loaded": self.private_key is not None,
            "redirect_uri": self.config.redirect_uri,
            "scopes": self.config.scopes
        }

# Global Apple OAuth service instance
apple_oauth_service = None

def initialize_apple_oauth_service() -> AppleOAuthService:
    """Initialize global Apple OAuth service"""
    global apple_oauth_service
    apple_oauth_service = AppleOAuthService()
    return apple_oauth_service

def get_apple_oauth_service() -> AppleOAuthService:
    """Get global Apple OAuth service"""
    if apple_oauth_service is None:
        raise ValueError("Apple OAuth service not initialized")
    return apple_oauth_service

# Convenience functions
def get_apple_authorization_url(state: str = None, redirect_uri: str = None) -> str:
    """Get Apple authorization URL (global convenience function)"""
    return get_apple_oauth_service().get_authorization_url(state, redirect_uri)

def exchange_apple_code_for_tokens(code: str, redirect_uri: str = None) -> Optional[Dict[str, Any]]:
    """Exchange Apple authorization code for tokens (global convenience function)"""
    return get_apple_oauth_service().exchange_code_for_tokens(code, redirect_uri)

def revoke_apple_token(token: str) -> bool:
    """Revoke Apple token (global convenience function)"""
    return get_apple_oauth_service().revoke_token(token)
