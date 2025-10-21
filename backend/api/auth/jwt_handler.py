"""
JWT Token Handler
Secure JWT token generation and validation for authentication
"""

import os
import jwt
import secrets
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, Tuple
import logging
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JWTConfig:
    """JWT configuration settings"""

    def __init__(self):
        self.algorithm = "RS256"
        self.access_token_expire_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.refresh_token_expire_days = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        self.issuer = os.getenv("JWT_ISSUER", "zalopay-phishing-platform")
        self.audience = os.getenv("JWT_AUDIENCE", "zalopay-admin")

class KeyManager:
    """RSA key management for JWT signing"""

    def __init__(self):
        self.private_key = None
        self.public_key = None
        self._load_or_generate_keys()

    def _load_or_generate_keys(self):
        """Load existing keys or generate new ones"""
        try:
            # Try to load existing keys from environment
            private_key_pem = os.getenv("JWT_PRIVATE_KEY")
            public_key_pem = os.getenv("JWT_PUBLIC_KEY")

            if private_key_pem and public_key_pem:
                # Load existing keys
                self.private_key = serialization.load_pem_private_key(
                    private_key_pem.encode(),
                    password=None
                )
                self.public_key = serialization.load_pem_public_key(
                    public_key_pem.encode()
                )
                logger.info("JWT keys loaded from environment")
            else:
                # Generate new keys
                self._generate_keys()
                logger.info("New JWT keys generated")

        except Exception as e:
            logger.error(f"Error loading JWT keys: {e}")
            self._generate_keys()

    def _generate_keys(self):
        """Generate new RSA key pair"""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()

    def get_private_key(self) -> rsa.RSAPrivateKey:
        """Get private key for signing"""
        return self.private_key

    def get_public_key(self) -> rsa.RSAPublicKey:
        """Get public key for verification"""
        return self.public_key

    def get_public_key_pem(self) -> str:
        """Get public key in PEM format"""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

class TokenBlacklist:
    """Token blacklist management using Redis"""

    def __init__(self, redis_client: redis.Redis = None):
        self.redis_client = redis_client
        self.blacklist_prefix = "jwt_blacklist:"

    def add_to_blacklist(self, jti: str, exp: int) -> bool:
        """Add token to blacklist"""
        try:
            if not self.redis_client:
                return False

            # Calculate TTL for blacklist entry
            current_time = int(datetime.now(timezone.utc).timestamp())
            ttl = max(exp - current_time, 0)

            key = f"{self.blacklist_prefix}{jti}"
            self.redis_client.setex(key, ttl, "blacklisted")

            logger.info(f"Token {jti} added to blacklist")
            return True

        except Exception as e:
            logger.error(f"Error adding token to blacklist: {e}")
            return False

    def is_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted"""
        try:
            if not self.redis_client:
                return False

            key = f"{self.blacklist_prefix}{jti}"
            return bool(self.redis_client.exists(key))

        except Exception as e:
            logger.error(f"Error checking blacklist: {e}")
            return False

class JWTHandler:
    """Main JWT handler class"""

    def __init__(self, redis_client: redis.Redis = None):
        self.config = JWTConfig()
        self.key_manager = KeyManager()
        self.blacklist = TokenBlacklist(redis_client)

    def create_access_token(self, data: Dict[str, Any], expires_delta: timedelta = None) -> str:
        """
        Create JWT access token

        Args:
            data: Payload data to encode
            expires_delta: Custom expiration time

        Returns:
            Encoded JWT token
        """
        try:
            # Set default expiration
            if expires_delta:
                expire = datetime.now(timezone.utc) + expires_delta
            else:
                expire = datetime.now(timezone.utc) + timedelta(minutes=self.config.access_token_expire_minutes)

            # Add standard claims
            to_encode = data.copy()
            to_encode.update({
                "iss": self.config.issuer,
                "aud": self.config.audience,
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "type": "access",
                "jti": secrets.token_hex(16)  # Unique token ID
            })

            # Encode token
            private_key = self.key_manager.get_private_key()
            token = jwt.encode(
                to_encode,
                private_key,
                algorithm=self.config.algorithm
            )

            logger.info(f"Access token created for user: {data.get('sub', 'unknown')}")
            return token

        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """
        Create JWT refresh token

        Args:
            data: Payload data to encode

        Returns:
            Encoded JWT refresh token
        """
        try:
            # Refresh token expires in 7 days
            expire = datetime.now(timezone.utc) + timedelta(days=self.config.refresh_token_expire_days)

            # Add standard claims
            to_encode = data.copy()
            to_encode.update({
                "iss": self.config.issuer,
                "aud": self.config.audience,
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "type": "refresh",
                "jti": secrets.token_hex(16)  # Unique token ID
            })

            # Encode token
            private_key = self.key_manager.get_private_key()
            token = jwt.encode(
                to_encode,
                private_key,
                algorithm=self.config.algorithm
            )

            logger.info(f"Refresh token created for user: {data.get('sub', 'unknown')}")
            return token

        except Exception as e:
            logger.error(f"Error creating refresh token: {e}")
            raise

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode JWT token

        Args:
            token: JWT token to verify

        Returns:
            Decoded payload or None if invalid
        """
        try:
            # Decode token
            public_key = self.key_manager.get_public_key()
            payload = jwt.decode(
                token,
                public_key,
                algorithms=[self.config.algorithm],
                audience=self.config.audience,
                issuer=self.config.issuer
            )

            # Check if token is blacklisted
            jti = payload.get("jti")
            if jti and self.blacklist.is_blacklisted(jti):
                logger.warning(f"Token {jti} is blacklisted")
                return None

            # Check token type
            token_type = payload.get("type")
            if token_type not in ["access", "refresh"]:
                logger.warning(f"Invalid token type: {token_type}")
                return None

            logger.info(f"Token verified successfully for user: {payload.get('sub', 'unknown')}")
            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None

    def revoke_token(self, token: str) -> bool:
        """
        Revoke token by adding to blacklist

        Args:
            token: JWT token to revoke

        Returns:
            True if successfully revoked
        """
        try:
            # Verify token first
            payload = self.verify_token(token)
            if not payload:
                return False

            # Add to blacklist
            jti = payload.get("jti")
            exp = payload.get("exp")

            if jti and exp:
                return self.blacklist.add_to_blacklist(jti, exp)

            return False

        except Exception as e:
            logger.error(f"Error revoking token: {e}")
            return False

    def refresh_access_token(self, refresh_token: str) -> Optional[Tuple[str, str]]:
        """
        Create new access token using refresh token

        Args:
            refresh_token: Valid refresh token

        Returns:
            Tuple of (new_access_token, new_refresh_token) or None if invalid
        """
        try:
            # Verify refresh token
            payload = self.verify_token(refresh_token)
            if not payload or payload.get("type") != "refresh":
                logger.warning("Invalid refresh token")
                return None

            # Extract user data
            user_data = {
                "sub": payload.get("sub"),
                "role": payload.get("role"),
                "permissions": payload.get("permissions", [])
            }

            # Create new tokens
            new_access_token = self.create_access_token(user_data)
            new_refresh_token = self.create_refresh_token(user_data)

            # Revoke old refresh token
            self.revoke_token(refresh_token)

            logger.info(f"Access token refreshed for user: {user_data.get('sub', 'unknown')}")
            return new_access_token, new_refresh_token

        except Exception as e:
            logger.error(f"Error refreshing access token: {e}")
            return None

    def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get token information without full verification

        Args:
            token: JWT token

        Returns:
            Token information or None if invalid
        """
        try:
            # Decode without verification for basic info
            unverified_header = jwt.get_unverified_header(token)
            unverified_payload = jwt.decode(token, options={"verify_signature": False})

            return {
                "algorithm": unverified_header.get("alg"),
                "type": unverified_payload.get("type"),
                "exp": unverified_payload.get("exp"),
                "iat": unverified_payload.get("iat"),
                "sub": unverified_payload.get("sub"),
                "role": unverified_payload.get("role")
            }

        except Exception as e:
            logger.error(f"Error getting token info: {e}")
            return None

# Global JWT handler instance
jwt_handler = None

def initialize_jwt_handler(redis_client: redis.Redis = None) -> JWTHandler:
    """Initialize global JWT handler"""
    global jwt_handler
    jwt_handler = JWTHandler(redis_client)
    return jwt_handler

def get_jwt_handler() -> JWTHandler:
    """Get global JWT handler"""
    if jwt_handler is None:
        raise ValueError("JWT handler not initialized")
    return jwt_handler

# Convenience functions
def create_access_token(data: Dict[str, Any], expires_delta: timedelta = None) -> str:
    """Create access token (global convenience function)"""
    return get_jwt_handler().create_access_token(data, expires_delta)

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create refresh token (global convenience function)"""
    return get_jwt_handler().create_refresh_token(data)

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify token (global convenience function)"""
    return get_jwt_handler().verify_token(token)

def revoke_token(token: str) -> bool:
    """Revoke token (global convenience function)"""
    return get_jwt_handler().revoke_token(token)

def refresh_access_token(refresh_token: str) -> Optional[Tuple[str, str]]:
    """Refresh access token (global convenience function)"""
    return get_jwt_handler().refresh_access_token(refresh_token)