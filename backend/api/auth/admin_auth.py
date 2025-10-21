"""
Admin Authentication with MFA
Multi-factor authentication for admin users
"""

import os
import secrets
import hashlib
import hmac
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, Tuple
import logging
import json
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MFAManager:
    """Multi-factor authentication manager"""

    def __init__(self):
        self.secret_length = 32
        self.time_window = 30  # seconds
        self.allowed_drift = 1  # Allow 1 time window drift

    def generate_secret(self) -> str:
        """Generate new MFA secret"""
        try:
            secret = secrets.token_bytes(self.secret_length)
            return base64.b32encode(secret).decode('utf-8')
        except Exception as e:
            logger.error(f"Error generating MFA secret: {e}")
            raise

    def verify_totp(self, secret: str, token: str, timestamp: int = None) -> bool:
        """
        Verify TOTP token

        Args:
            secret: Base32 encoded secret
            token: TOTP token to verify
            timestamp: Timestamp to check (current time if None)

        Returns:
            True if token is valid
        """
        try:
            if timestamp is None:
                timestamp = int(time.time())

            # Decode secret
            secret_bytes = base64.b32decode(secret)

            # Check current and adjacent time windows
            for time_offset in range(-self.allowed_drift, self.allowed_drift + 1):
                check_time = timestamp + (time_offset * self.time_window)
                expected_token = self._generate_totp(secret_bytes, check_time)

                if hmac.compare_digest(expected_token, token):
                    logger.info("TOTP token verified successfully")
                    return True

            logger.warning("TOTP token verification failed")
            return False

        except Exception as e:
            logger.error(f"Error verifying TOTP: {e}")
            return False

    def _generate_totp(self, secret: bytes, timestamp: int) -> str:
        """Generate TOTP token for given timestamp"""
        try:
            # Get time window
            time_window = int(timestamp / self.time_window)

            # Create HMAC
            hmac_digest = hmac.new(
                secret,
                time_window.to_bytes(8, 'big'),
                hashlib.sha1
            ).digest()

            # Dynamic truncation
            offset = hmac_digest[-1] & 0x0F
            code = ((hmac_digest[offset] & 0x7F) << 24) | \
                   ((hmac_digest[offset + 1] & 0xFF) << 16) | \
                   ((hmac_digest[offset + 2] & 0xFF) << 8) | \
                   (hmac_digest[offset + 3] & 0xFF)

            # Get 6-digit code
            token = str(code % (10 ** 6)).zfill(6)
            return token

        except Exception as e:
            logger.error(f"Error generating TOTP: {e}")
            raise

class PasswordManager:
    """Secure password management"""

    def __init__(self):
        self.min_length = 12
        self.hash_algorithm = "pbkdf2"
        self.iterations = 120000
        self.salt_length = 32

    def hash_password(self, password: str) -> Dict[str, str]:
        """
        Hash password with salt

        Args:
            password: Plain text password

        Returns:
            Dictionary containing hash and metadata
        """
        try:
            # Generate salt
            salt = secrets.token_bytes(self.salt_length)

            # Hash password
            pwdhash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt,
                self.iterations
            )

            return {
                "hash": base64.b64encode(pwdhash).decode('utf-8'),
                "salt": base64.b64encode(salt).decode('utf-8'),
                "algorithm": self.hash_algorithm,
                "iterations": self.iterations,
                "created_at": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error hashing password: {e}")
            raise

    def verify_password(self, password: str, password_hash: Dict[str, str]) -> bool:
        """
        Verify password against hash

        Args:
            password: Plain text password
            password_hash: Password hash data

        Returns:
            True if password is correct
        """
        try:
            # Extract hash data
            stored_hash = base64.b64decode(password_hash["hash"])
            salt = base64.b64decode(password_hash["salt"])
            algorithm = password_hash["algorithm"]
            iterations = password_hash["iterations"]

            # Hash provided password
            pwdhash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt,
                iterations
            )

            # Compare hashes
            return hmac.compare_digest(pwdhash, stored_hash)

        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False

class AdminAuthManager:
    """Admin authentication manager"""

    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        self.mfa_manager = MFAManager()
        self.password_manager = PasswordManager()

        # Session settings
        self.session_timeout = int(os.getenv("ADMIN_SESSION_TIMEOUT", "3600"))  # 1 hour
        self.max_login_attempts = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
        self.lockout_duration = int(os.getenv("LOCKOUT_DURATION", "900"))  # 15 minutes

    def authenticate_admin(self, username: str, password: str, mfa_token: str = None) -> Dict[str, Any]:
        """
        Authenticate admin user

        Args:
            username: Admin username
            password: Admin password
            mfa_token: MFA token (optional)

        Returns:
            Authentication result with user data and tokens
        """
        try:
            # Check if account is locked
            if self._is_account_locked(username):
                return {
                    "success": False,
                    "error": "Account temporarily locked due to multiple failed attempts",
                    "locked_until": self._get_lockout_time(username)
                }

            # Get admin user from database
            admin_user = self._get_admin_user(username)
            if not admin_user:
                self._record_failed_attempt(username)
                return {"success": False, "error": "Invalid credentials"}

            # Verify password
            if not self.password_manager.verify_password(password, admin_user["password_hash"]):
                self._record_failed_attempt(username)
                return {"success": False, "error": "Invalid credentials"}

            # Check if MFA is required
            if admin_user.get("mfa_enabled", False):
                if not mfa_token:
                    return {
                        "success": False,
                        "error": "MFA token required",
                        "mfa_required": True
                    }

                # Verify MFA token
                if not self.mfa_manager.verify_totp(admin_user["mfa_secret"], mfa_token):
                    self._record_failed_attempt(username)
                    return {"success": False, "error": "Invalid MFA token"}

            # Clear failed attempts on successful login
            self._clear_failed_attempts(username)

            # Generate session
            session_data = self._create_admin_session(admin_user)

            logger.info(f"Admin {username} authenticated successfully")
            return {
                "success": True,
                "user": self._sanitize_user_data(admin_user),
                "session": session_data,
                "permissions": admin_user.get("permissions", []),
                "role": admin_user.get("role", "admin")
            }

        except Exception as e:
            logger.error(f"Error authenticating admin: {e}")
            return {"success": False, "error": "Authentication failed"}

    def _get_admin_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get admin user from database"""
        try:
            if not self.mongodb:
                return None

            db = self.mongodb.get_database("zalopay_phishing")
            users_collection = db.admin_users

            user = users_collection.find_one({"username": username, "active": True})
            return user

        except Exception as e:
            logger.error(f"Error getting admin user: {e}")
            return None

    def _record_failed_attempt(self, username: str):
        """Record failed login attempt"""
        try:
            if not self.redis:
                return

            # Increment failed attempts
            attempts_key = f"admin_login_attempts:{username}"
            lockout_key = f"admin_lockout:{username}"

            current_attempts = self.redis.incr(attempts_key)
            self.redis.expire(attempts_key, self.lockout_duration)

            # Lock account if too many attempts
            if current_attempts >= self.max_login_attempts:
                self.redis.setex(lockout_key, self.lockout_duration, "locked")
                logger.warning(f"Admin account {username} locked due to multiple failed attempts")

        except Exception as e:
            logger.error(f"Error recording failed attempt: {e}")

    def _clear_failed_attempts(self, username: str):
        """Clear failed login attempts"""
        try:
            if not self.redis:
                return

            attempts_key = f"admin_login_attempts:{username}"
            lockout_key = f"admin_lockout:{username}"

            self.redis.delete(attempts_key, lockout_key)

        except Exception as e:
            logger.error(f"Error clearing failed attempts: {e}")

    def _is_account_locked(self, username: str) -> bool:
        """Check if account is locked"""
        try:
            if not self.redis:
                return False

            lockout_key = f"admin_lockout:{username}"
            return bool(self.redis.exists(lockout_key))

        except Exception as e:
            logger.error(f"Error checking account lock: {e}")
            return False

    def _get_lockout_time(self, username: str) -> Optional[int]:
        """Get lockout expiration time"""
        try:
            if not self.redis:
                return None

            lockout_key = f"admin_lockout:{username}"
            ttl = self.redis.ttl(lockout_key)
            if ttl > 0:
                return int(time.time()) + ttl

            return None

        except Exception as e:
            logger.error(f"Error getting lockout time: {e}")
            return None

    def _create_admin_session(self, admin_user: Dict[str, Any]) -> Dict[str, Any]:
        """Create admin session"""
        try:
            session_id = secrets.token_hex(32)
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.session_timeout)

            session_data = {
                "session_id": session_id,
                "user_id": str(admin_user["_id"]),
                "username": admin_user["username"],
                "role": admin_user.get("role", "admin"),
                "permissions": admin_user.get("permissions", []),
                "created_at": datetime.now(timezone.utc),
                "expires_at": expires_at,
                "ip_address": None,  # Will be set by calling function
                "user_agent": None   # Will be set by calling function
            }

            # Store session in Redis
            if self.redis:
                session_key = f"admin_session:{session_id}"
                self.redis.setex(session_key, self.session_timeout, json.dumps(session_data))

            return session_data

        except Exception as e:
            logger.error(f"Error creating admin session: {e}")
            raise

    def _sanitize_user_data(self, admin_user: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive data from user object"""
        sanitized = admin_user.copy()

        # Remove sensitive fields
        sensitive_fields = ["password_hash", "mfa_secret", "private_key"]
        for field in sensitive_fields:
            sanitized.pop(field, None)

        return sanitized

    def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Validate admin session

        Args:
            session_id: Session ID to validate

        Returns:
            Session data if valid, None otherwise
        """
        try:
            if not self.redis:
                return None

            session_key = f"admin_session:{session_id}"
            session_data = self.redis.get(session_key)

            if not session_data:
                return None

            session = json.loads(session_data)

            # Check expiration
            expires_at = datetime.fromisoformat(session["expires_at"].replace('Z', '+00:00'))
            if datetime.now(timezone.utc) > expires_at:
                self.redis.delete(session_key)
                return None

            # Extend session
            new_expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.session_timeout)
            session["expires_at"] = new_expires_at

            self.redis.setex(session_key, self.session_timeout, json.dumps(session))

            return session

        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return None

    def invalidate_session(self, session_id: str) -> bool:
        """
        Invalidate admin session

        Args:
            session_id: Session ID to invalidate

        Returns:
            True if successfully invalidated
        """
        try:
            if not self.redis:
                return False

            session_key = f"admin_session:{session_id}"
            deleted = self.redis.delete(session_key)

            if deleted:
                logger.info(f"Admin session {session_id} invalidated")

            return bool(deleted)

        except Exception as e:
            logger.error(f"Error invalidating session: {e}")
            return False

    def setup_mfa(self, username: str) -> Dict[str, Any]:
        """
        Setup MFA for admin user

        Args:
            username: Admin username

        Returns:
            MFA setup data
        """
        try:
            # Get admin user
            admin_user = self._get_admin_user(username)
            if not admin_user:
                return {"success": False, "error": "Admin user not found"}

            # Generate MFA secret
            mfa_secret = self.mfa_manager.generate_secret()

            # Generate backup codes
            backup_codes = self._generate_backup_codes()

            # Update user in database
            if self.mongodb:
                db = self.mongodb.get_database("zalopay_phishing")
                users_collection = db.admin_users

                users_collection.update_one(
                    {"username": username},
                    {
                        "$set": {
                            "mfa_secret": mfa_secret,
                            "backup_codes": backup_codes,
                            "mfa_enabled": False,  # Enable after verification
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )

            logger.info(f"MFA setup initiated for admin: {username}")
            return {
                "success": True,
                "mfa_secret": mfa_secret,
                "backup_codes": backup_codes,
                "qr_code_url": self._generate_qr_code_url(username, mfa_secret)
            }

        except Exception as e:
            logger.error(f"Error setting up MFA: {e}")
            return {"success": False, "error": "Failed to setup MFA"}

    def _generate_backup_codes(self, count: int = 10) -> list:
        """Generate backup codes for MFA"""
        try:
            codes = []
            for _ in range(count):
                code = secrets.token_hex(4)  # 8 character codes
                codes.append(code)

            return codes

        except Exception as e:
            logger.error(f"Error generating backup codes: {e}")
            return []

    def _generate_qr_code_url(self, username: str, secret: str) -> str:
        """Generate QR code URL for MFA setup"""
        try:
            # This would typically use a library like qrcode or pyotp
            # For now, return a placeholder URL
            issuer = "ZaloPay Phishing Platform"
            return f"otpauth://totp/{issuer}:{username}?secret={secret}&issuer={issuer}"

        except Exception as e:
            logger.error(f"Error generating QR code URL: {e}")
            return ""

    def verify_mfa_setup(self, username: str, token: str, backup_code: str = None) -> Dict[str, Any]:
        """
        Verify MFA setup with token or backup code

        Args:
            username: Admin username
            token: MFA token
            backup_code: Backup code (optional)

        Returns:
            Verification result
        """
        try:
            # Get admin user
            admin_user = self._get_admin_user(username)
            if not admin_user or not admin_user.get("mfa_secret"):
                return {"success": False, "error": "MFA not configured"}

            # Verify token
            if token and self.mfa_manager.verify_totp(admin_user["mfa_secret"], token):
                return self._enable_mfa(username)

            # Verify backup code
            if backup_code and self._verify_backup_code(username, backup_code):
                return self._enable_mfa(username)

            return {"success": False, "error": "Invalid token or backup code"}

        except Exception as e:
            logger.error(f"Error verifying MFA setup: {e}")
            return {"success": False, "error": "Verification failed"}

    def _verify_backup_code(self, username: str, code: str) -> bool:
        """Verify backup code"""
        try:
            if not self.mongodb:
                return False

            db = self.mongodb.get_database("zalopay_phishing")
            users_collection = db.admin_users

            # Find and remove backup code
            result = users_collection.update_one(
                {
                    "username": username,
                    "backup_codes": code
                },
                {"$pull": {"backup_codes": code}}
            )

            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Error verifying backup code: {e}")
            return False

    def _enable_mfa(self, username: str) -> Dict[str, Any]:
        """Enable MFA for admin user"""
        try:
            if not self.mongodb:
                return {"success": False, "error": "Database not available"}

            db = self.mongodb.get_database("zalopay_phishing")
            users_collection = db.admin_users

            users_collection.update_one(
                {"username": username},
                {
                    "$set": {
                        "mfa_enabled": True,
                        "mfa_setup_at": datetime.now(timezone.utc)
                    }
                }
            )

            logger.info(f"MFA enabled for admin: {username}")
            return {"success": True, "message": "MFA enabled successfully"}

        except Exception as e:
            logger.error(f"Error enabling MFA: {e}")
            return {"success": False, "error": "Failed to enable MFA"}

# Global admin auth manager instance
admin_auth_manager = None

def initialize_admin_auth(mongodb_connection=None, redis_client=None) -> AdminAuthManager:
    """Initialize global admin auth manager"""
    global admin_auth_manager
    admin_auth_manager = AdminAuthManager(mongodb_connection, redis_client)
    return admin_auth_manager

def get_admin_auth_manager() -> AdminAuthManager:
    """Get global admin auth manager"""
    if admin_auth_manager is None:
        raise ValueError("Admin auth manager not initialized")
    return admin_auth_manager

# Convenience functions
def authenticate_admin(username: str, password: str, mfa_token: str = None) -> Dict[str, Any]:
    """Authenticate admin (global convenience function)"""
    return get_admin_auth_manager().authenticate_admin(username, password, mfa_token)

def validate_admin_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Validate admin session (global convenience function)"""
    return get_admin_auth_manager().validate_session(session_id)

def invalidate_admin_session(session_id: str) -> bool:
    """Invalidate admin session (global convenience function)"""
    return get_admin_auth_manager().invalidate_session(session_id)