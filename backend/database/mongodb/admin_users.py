"""
Admin Users Schema - MongoDB Collection
Admin authentication with MFA and role-based access control
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError, DuplicateKeyError
import logging
import secrets
import hashlib
import hmac
import base64
import pyotp
from bcrypt import hashpw, gensalt, checkpw

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MFAManager:
    """Advanced Multi-Factor Authentication management"""

    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or secrets.token_hex(32)
        self.totp_issuer = "ZaloPay Phishing Platform"
        self.allowed_drift = 2  # Allow 2 time steps drift for TOTP

    def generate_mfa_secret(self) -> str:
        """Generate TOTP secret for MFA"""
        return pyotp.random_base32()

    def generate_qr_uri(self, username: str, issuer: str, secret: str) -> str:
        """Generate QR code URI for authenticator apps"""
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=username,
            issuer_name=issuer
        )

    def verify_totp(self, secret: str, token: str) -> bool:
        """Verify TOTP token with enhanced security"""
        try:
            totp = pyotp.TOTP(secret)

            # Try current time and allow drift
            for drift in range(-self.allowed_drift, self.allowed_drift + 1):
                if totp.verify(token, valid_window=drift):
                    return True

            return False
        except Exception as e:
            logger.error(f"Error verifying TOTP: {e}")
            return False

    def generate_hotp_secret(self) -> str:
        """Generate HOTP secret for counter-based authentication"""
        return pyotp.random_base32()

    def verify_hotp(self, secret: str, token: str, counter: int) -> tuple[bool, int]:
        """Verify HOTP token and return new counter"""
        try:
            hotp = pyotp.HOTP(secret)

            # Try current counter and next few counters
            for i in range(10):  # Allow 10 counter drift
                if hotp.verify(token, counter + i):
                    return True, counter + i + 1

            return False, counter
        except Exception as e:
            logger.error(f"Error verifying HOTP: {e}")
            return False, counter

    def generate_sms_otp(self, length: int = 6) -> str:
        """Generate SMS OTP"""
        digits = "0123456789"
        return ''.join(secrets.choice(digits) for _ in range(length))

    def generate_email_otp(self, length: int = 8) -> str:
        """Generate Email OTP with alphanumeric characters"""
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        return ''.join(secrets.choice(chars) for _ in range(length))

    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes for account recovery"""
        codes = []
        for _ in range(count):
            code = secrets.token_hex(4).upper()
            codes.append(code)
        return codes

    def hash_backup_codes(self, codes: List[str]) -> List[str]:
        """Hash backup codes for secure storage"""
        hashed_codes = []
        for code in codes:
            # Use SHA-256 with salt
            salt = gensalt()
            hashed = hashpw(code.encode(), salt)
            hashed_codes.append(hashed.decode())
        return hashed_codes

    def verify_backup_code(self, plain_code: str, hashed_codes: List[str]) -> bool:
        """Verify backup code"""
        for hashed_code in hashed_codes:
            if checkpw(plain_code.encode(), hashed_code.encode()):
                return True
        return False

class PasswordManager:
    """Password hashing and verification"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with bcrypt"""
        salt = gensalt(rounds=12)
        return hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    @staticmethod
    def generate_temp_password(length: int = 12) -> str:
        """Generate temporary password"""
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*"
        return ''.join(secrets.choice(chars) for _ in range(length))

class AdminUserModel:
    """Admin user management with MFA"""

    def __init__(self, mongo_client: MongoClient, mfa_secret_key: str = None):
        self.db = mongo_client.get_database("zalopay_phishing")
        self.collection: Collection = self.db.admin_users
        self.mfa_manager = MFAManager(mfa_secret_key)
        self._create_indexes()
        self._create_validation_pipeline()

    def _create_indexes(self):
        """Create optimized indexes for admin users"""
        try:
            # Primary indexes
            self.collection.create_index("admin_id", unique=True)
            self.collection.create_index("username", unique=True)
            self.collection.create_index("email", unique=True)

            # Authentication indexes
            self.collection.create_index("status")
            self.collection.create_index("role")
            self.collection.create_index("last_login")

            # Security indexes
            self.collection.create_index("mfa_enabled")
            self.collection.create_index("failed_login_attempts")
            self.collection.create_index("locked_until")

            # Search indexes
            self.collection.create_index([
                ("personal_info.first_name", "text"),
                ("personal_info.last_name", "text"),
                ("username", "text")
            ])

            logger.info("Admin users indexes created successfully")

        except PyMongoError as e:
            logger.error(f"Error creating admin user indexes: {e}")
            raise

    def _create_validation_pipeline(self):
        """Create validation pipeline for admin users"""
        try:
            pipeline = [
                {
                    "$jsonSchema": {
                        "bsonType": "object",
                        "required": [
                            "admin_id", "username", "email", "password_hash",
                            "role", "status", "created_at"
                        ],
                        "properties": {
                            "admin_id": {
                                "bsonType": "string",
                                "pattern": "^ADMIN_[0-9]{8}_[A-Z0-9]{6}$",
                                "description": "Admin ID format: ADMIN_YYYYMMDD_XXXXXX"
                            },
                            "username": {
                                "bsonType": "string",
                                "pattern": "^[a-zA-Z0-9_]{3,32}$",
                                "description": "Username 3-32 chars, alphanumeric and underscore"
                            },
                            "email": {
                                "bsonType": "string",
                                "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
                            },
                            "password_hash": {
                                "bsonType": "string",
                                "minLength": 60,
                                "description": "bcrypt password hash"
                            },
                            "role": {
                                "bsonType": "string",
                                "enum": ["super_admin", "admin", "moderator", "analyst", "viewer"]
                            },
                            "status": {
                                "bsonType": "string",
                                "enum": ["active", "inactive", "suspended", "locked"]
                            },
                            "personal_info": {
                                "bsonType": "object",
                                "properties": {
                                    "first_name": {"bsonType": "string", "minLength": 1},
                                    "last_name": {"bsonType": "string", "minLength": 1},
                                    "phone": {"bsonType": "string"},
                                    "department": {"bsonType": "string"}
                                }
                            },
                            "mfa_enabled": {"bsonType": "bool", "default": False},
                            "mfa_secret": {"bsonType": "string"},
                            "backup_codes": {
                                "bsonType": "array",
                                "items": {"bsonType": "string"}
                            },
                            "permissions": {
                                "bsonType": "array",
                                "items": {"bsonType": "string"},
                                "uniqueItems": True
                            },
                            "failed_login_attempts": {
                                "bsonType": "int",
                                "minimum": 0,
                                "default": 0
                            },
                            "locked_until": {"bsonType": ["date", "null"]},
                            "last_login": {"bsonType": ["date", "null"]},
                            "last_password_change": {"bsonType": ["date", "null"]},
                            "password_expires_at": {"bsonType": ["date", "null"]},
                            "session_timeout": {
                                "bsonType": "int",
                                "minimum": 300,
                                "maximum": 28800,
                                "default": 3600,
                                "description": "Session timeout in seconds (5min - 8hrs)"
                            },
                            "ip_whitelist": {
                                "bsonType": "array",
                                "items": {"bsonType": "string"}
                            },
                            "created_at": {"bsonType": "date"},
                            "updated_at": {"bsonType": "date"},
                            "created_by": {"bsonType": "string"}
                        },
                        "additionalProperties": False
                    }
                }
            ]

            # Apply validation
            self.collection.drop_validation()
            self.db.command("collMod", "admin_users", validator=pipeline[0]["$jsonSchema"])

            logger.info("Admin users validation pipeline created")

        except PyMongoError as e:
            logger.error(f"Error creating admin user validation: {e}")
            raise

    def generate_admin_id(self) -> str:
        """Generate unique admin ID"""
        timestamp = datetime.now().strftime("%Y%m%d")
        random_suffix = secrets.token_hex(3).upper()
        return f"ADMIN_{timestamp}_{random_suffix}"

    def create_admin(self, username: str, email: str, password: str,
                    role: str = "admin", created_by: str = "system",
                    personal_info: Dict[str, Any] = None) -> str:
        """
        Create new admin user

        Args:
            username: Admin username
            email: Admin email
            password: Plain text password
            role: Admin role
            created_by: Who created this admin
            personal_info: Personal information

        Returns:
            str: Admin ID
        """
        try:
            # Generate admin ID
            admin_id = self.generate_admin_id()

            # Hash password
            password_hash = PasswordManager.hash_password(password)

            # Generate backup codes
            backup_codes = self.mfa_manager.generate_backup_codes()
            hashed_backup_codes = self.mfa_manager.hash_backup_codes(backup_codes)

            # Prepare admin document
            admin_doc = {
                "admin_id": admin_id,
                "username": username.lower(),
                "email": email.lower(),
                "password_hash": password_hash,
                "role": role,
                "status": "active",
                "personal_info": personal_info or {},
                "mfa_enabled": False,
                "backup_codes": hashed_backup_codes,
                "permissions": self._get_default_permissions(role),
                "failed_login_attempts": 0,
                "locked_until": None,
                "last_login": None,
                "last_password_change": datetime.now(timezone.utc),
                "password_expires_at": datetime.now(timezone.utc) + timedelta(days=90),
                "session_timeout": 3600,  # 1 hour default
                "ip_whitelist": [],
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "created_by": created_by
            }

            # Insert admin
            result = self.collection.insert_one(admin_doc)

            if result.inserted_id:
                logger.info(f"Admin user created: {admin_id} ({username})")
                return admin_id
            else:
                raise PyMongoError("Failed to create admin user")

        except DuplicateKeyError as e:
            field = str(e).split(" ")[-1].split("_")[0]
            logger.error(f"Duplicate admin {field}: {username if 'username' in field else email}")
            raise ValueError(f"Admin with this {field} already exists")
        except PyMongoError as e:
            logger.error(f"Error creating admin user: {e}")
            raise

    def _get_default_permissions(self, role: str) -> List[str]:
        """Get default permissions for role with granular access control"""
        permissions_map = {
            "super_admin": [
                # Admin management (full access)
                "admin.*",
                # Victim management (full access)
                "victim.*",
                # Campaign management (full access)
                "campaign.*",
                # System administration
                "system.*",
                # Security management
                "security.*",
                # Audit and compliance
                "audit.*",
                # Data management
                "data.*"
            ],
            "admin": [
                # Victim management (create, read, update)
                "victim.create", "victim.read", "victim.update", "victim.export",
                # Campaign management (create, read, update)
                "campaign.create", "campaign.read", "campaign.update", "campaign.execute",
                # Basic system access
                "system.read", "system.audit",
                # Basic security
                "security.alert.read", "security.log.read"
            ],
            "moderator": [
                # Victim management (read, update only)
                "victim.read", "victim.update", "victim.status.update",
                # Campaign management (read, limited update)
                "campaign.read", "campaign.status.update",
                # Basic reporting
                "report.victim.read", "report.campaign.read"
            ],
            "analyst": [
                # Read-only access to most resources
                "victim.read", "campaign.read", "admin.read",
                # Analytics and reporting
                "analytics.*", "report.*",
                # System monitoring (read-only)
                "system.monitor.read", "system.health.read"
            ],
            "viewer": [
                # Minimal read-only access
                "victim.read.basic", "campaign.read.basic",
                "report.summary.read", "dashboard.read"
            ],
            "security_officer": [
                # Security-focused permissions
                "security.*", "audit.*",
                # Read access to operational data
                "victim.read", "campaign.read", "admin.read",
                # No modification permissions
            ]
        }
        return permissions_map.get(role, [])

    def check_permission(self, admin_permissions: List[str], required_permission: str) -> bool:
        """Check if admin has required permission with wildcard support"""
        for permission in admin_permissions:
            if self._permission_matches(permission, required_permission):
                return True
        return False

    def _permission_matches(self, user_permission: str, required_permission: str) -> bool:
        """Check if user permission matches or exceeds required permission"""
        # Exact match
        if user_permission == required_permission:
            return True

        # Wildcard support (*)
        if user_permission.endswith(".*"):
            user_prefix = user_permission[:-2]  # Remove ".*"
            return required_permission.startswith(user_prefix + ".")

        # Hierarchical support (admin.create includes admin.create.victim)
        if "." in required_permission and user_permission in required_permission:
            return True

        return False

    def get_available_permissions(self) -> Dict[str, List[str]]:
        """Get all available permissions organized by category"""
        return {
            "admin": [
                "admin.create", "admin.read", "admin.update", "admin.delete",
                "admin.list", "admin.export", "admin.import"
            ],
            "victim": [
                "victim.create", "victim.read", "victim.update", "victim.delete",
                "victim.export", "victim.import", "victim.status.update",
                "victim.risk.update", "victim.business.update"
            ],
            "campaign": [
                "campaign.create", "campaign.read", "campaign.update", "campaign.delete",
                "campaign.execute", "campaign.pause", "campaign.resume", "campaign.cancel",
                "campaign.clone", "campaign.template.save"
            ],
            "system": [
                "system.read", "system.update", "system.config",
                "system.backup", "system.restore", "system.maintenance",
                "system.monitor.read", "system.health.read", "system.logs.read"
            ],
            "security": [
                "security.alert.read", "security.alert.update", "security.alert.create",
                "security.log.read", "security.log.export", "security.policy.update",
                "security.encryption.manage", "security.key.rotate"
            ],
            "analytics": [
                "analytics.victim.read", "analytics.campaign.read", "analytics.system.read",
                "analytics.report.generate", "analytics.dashboard.read"
            ],
            "audit": [
                "audit.log.read", "audit.log.export", "audit.compliance.read",
                "audit.security.read", "audit.access.read"
            ]
        }

    def expand_wildcard_permissions(self, permissions: List[str]) -> List[str]:
        """Expand wildcard permissions to specific permissions"""
        expanded = []
        available_perms = self.get_available_permissions()

        for permission in permissions:
            if permission.endswith(".*"):
                # Expand wildcard
                prefix = permission[:-2]
                if prefix in available_perms:
                    expanded.extend(available_perms[prefix])
                else:
                    # Try to find matching permissions
                    for category_perms in available_perms.values():
                        for perm in category_perms:
                            if perm.startswith(prefix + "."):
                                expanded.append(perm)
            else:
                expanded.append(permission)

        return list(set(expanded))  # Remove duplicates

    def authenticate_admin(self, username: str, password: str, ip_address: str = None) -> Optional[Dict[str, Any]]:
        """
        Authenticate admin user

        Args:
            username: Admin username
            password: Plain text password
            ip_address: Client IP address

        Returns:
            Dict with admin info or None if authentication fails
        """
        try:
            admin = self.collection.find_one({"username": username.lower()})

            if not admin:
                logger.warning(f"Admin login attempt for non-existent user: {username}")
                return None

            # Check if account is locked
            if admin.get("locked_until") and admin["locked_until"] > datetime.now(timezone.utc):
                logger.warning(f"Admin login attempt for locked account: {username}")
                return None

            # Check if account is active
            if admin.get("status") != "active":
                logger.warning(f"Admin login attempt for inactive account: {username}")
                return None

            # Verify password
            if not PasswordManager.verify_password(password, admin["password_hash"]):
                # Increment failed attempts
                self._increment_failed_attempts(admin["admin_id"])
                logger.warning(f"Invalid password for admin: {username}")
                return None

            # Reset failed attempts on successful login
            self.collection.update_one(
                {"admin_id": admin["admin_id"]},
                {
                    "$set": {
                        "failed_login_attempts": 0,
                        "locked_until": None,
                        "last_login": datetime.now(timezone.utc),
                        "last_ip": ip_address
                    }
                }
            )

            # Remove sensitive data from response
            admin_data = dict(admin)
            del admin_data["password_hash"]
            del admin_data["backup_codes"]
            if "mfa_secret" in admin_data:
                del admin_data["mfa_secret"]

            logger.info(f"Admin authenticated successfully: {username}")
            return admin_data

        except PyMongoError as e:
            logger.error(f"Error authenticating admin {username}: {e}")
            raise

    def _increment_failed_attempts(self, admin_id: str):
        """Increment failed login attempts and lock account if necessary"""
        try:
            admin = self.collection.find_one({"admin_id": admin_id})
            if not admin:
                return

            failed_attempts = admin.get("failed_login_attempts", 0) + 1
            update_data = {"failed_login_attempts": failed_attempts}

            # Lock account after 5 failed attempts for 30 minutes
            if failed_attempts >= 5:
                update_data["locked_until"] = datetime.now(timezone.utc) + timedelta(minutes=30)
                logger.warning(f"Admin account locked due to failed attempts: {admin_id}")

            self.collection.update_one(
                {"admin_id": admin_id},
                {"$set": update_data}
            )

        except PyMongoError as e:
            logger.error(f"Error incrementing failed attempts for {admin_id}: {e}")

    def enable_mfa(self, admin_id: str) -> Dict[str, Any]:
        """
        Enable MFA for admin user

        Returns:
            Dict with MFA setup information
        """
        try:
            # Generate MFA secret
            mfa_secret = self.mfa_manager.generate_mfa_secret()

            # Generate backup codes
            backup_codes = self.mfa_manager.generate_backup_codes()
            hashed_backup_codes = self.mfa_manager.hash_backup_codes(backup_codes)

            # Update admin with MFA data
            result = self.collection.update_one(
                {"admin_id": admin_id},
                {
                    "$set": {
                        "mfa_enabled": True,
                        "mfa_secret": mfa_secret,
                        "backup_codes": hashed_backup_codes,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )

            if result.modified_count > 0:
                # Generate QR URI for authenticator apps
                admin = self.collection.find_one({"admin_id": admin_id})
                qr_uri = self.mfa_manager.generate_qr_uri(
                    username=admin["username"],
                    issuer="ZaloPay Phishing Platform",
                    secret=mfa_secret
                )

                logger.info(f"MFA enabled for admin: {admin_id}")
                return {
                    "mfa_secret": mfa_secret,
                    "qr_uri": qr_uri,
                    "backup_codes": backup_codes
                }
            else:
                raise ValueError("Admin not found")

        except PyMongoError as e:
            logger.error(f"Error enabling MFA for {admin_id}: {e}")
            raise

    def verify_mfa_token(self, admin_id: str, token: str, use_backup: bool = False) -> bool:
        """
        Verify MFA token or backup code

        Args:
            admin_id: Admin user ID
            token: TOTP token or backup code
            use_backup: Whether token is a backup code

        Returns:
            bool: True if token is valid
        """
        try:
            admin = self.collection.find_one({"admin_id": admin_id})

            if not admin or not admin.get("mfa_enabled"):
                return False

            if use_backup:
                # Verify backup code
                return self.mfa_manager.verify_backup_code(token, admin["backup_codes"])
            else:
                # Verify TOTP token
                return self.mfa_manager.verify_totp(admin["mfa_secret"], token)

        except PyMongoError as e:
            logger.error(f"Error verifying MFA token for {admin_id}: {e}")
            return False

    def get_admin_by_id(self, admin_id: str) -> Optional[Dict[str, Any]]:
        """Get admin by ID"""
        try:
            admin = self.collection.find_one({"admin_id": admin_id})

            if admin:
                # Remove sensitive data
                admin_data = dict(admin)
                admin_data.pop("password_hash", None)
                admin_data.pop("mfa_secret", None)
                admin_data.pop("backup_codes", None)
                return admin_data

            return None

        except PyMongoError as e:
            logger.error(f"Error retrieving admin {admin_id}: {e}")
            raise

    def update_admin_role(self, admin_id: str, new_role: str, updated_by: str) -> bool:
        """Update admin role and permissions"""
        try:
            result = self.collection.update_one(
                {"admin_id": admin_id},
                {
                    "$set": {
                        "role": new_role,
                        "permissions": self._get_default_permissions(new_role),
                        "updated_at": datetime.now(timezone.utc),
                        "updated_by": updated_by
                    }
                }
            )

            if result.modified_count > 0:
                logger.info(f"Admin role updated: {admin_id} -> {new_role}")
                return True
            else:
                logger.warning(f"No admin found to update: {admin_id}")
                return False

        except PyMongoError as e:
            logger.error(f"Error updating admin role {admin_id}: {e}")
            raise

    def create_admin_session(self, admin_id: str, ip_address: str = None,
                           user_agent: str = None, device_fingerprint: str = None) -> str:
        """Create new admin session with enhanced tracking"""
        try:
            session_id = secrets.token_hex(32)

            # Extract client information
            client_info = self._extract_client_info(user_agent, ip_address)

            # Create session document
            session_data = {
                "session_id": session_id,
                "admin_id": admin_id,
                "created_at": datetime.now(timezone.utc),
                "last_activity": datetime.now(timezone.utc),
                "expires_at": datetime.now(timezone.utc) + timedelta(hours=8),  # 8 hour default
                "is_active": True,
                "client_info": client_info,
                "device_fingerprint": device_fingerprint,
                "mfa_verified": False,
                "permissions_cache": self._get_cached_permissions(admin_id),
                "activity_log": []
            }

            # Store session in separate collection (would need session collection)
            # For now, store in admin document
            self.collection.update_one(
                {"admin_id": admin_id},
                {
                    "$push": {"active_sessions": session_data},
                    "$set": {"last_login": datetime.now(timezone.utc)}
                }
            )

            logger.info(f"Admin session created: {session_id} for admin {admin_id}")
            return session_id

        except Exception as e:
            logger.error(f"Error creating admin session: {e}")
            raise

    def _get_cached_permissions(self, admin_id: str) -> List[str]:
        """Get cached permissions for admin"""
        try:
            admin = self.collection.find_one({"admin_id": admin_id})
            if admin:
                permissions = admin.get("permissions", [])
                return self.expand_wildcard_permissions(permissions)
            return []
        except Exception as e:
            logger.error(f"Error getting cached permissions for {admin_id}: {e}")
            return []

    def validate_admin_session(self, session_id: str, admin_id: str) -> Dict[str, Any]:
        """Validate admin session and return session info"""
        try:
            admin = self.collection.find_one({"admin_id": admin_id})
            if not admin:
                return {"valid": False, "reason": "admin_not_found"}

            # Find active session
            active_sessions = admin.get("active_sessions", [])
            session = None

            for s in active_sessions:
                if s["session_id"] == session_id:
                    session = s
                    break

            if not session:
                return {"valid": False, "reason": "session_not_found"}

            # Check if session expired
            if session["expires_at"] < datetime.now(timezone.utc):
                self.terminate_admin_session(session_id, admin_id)
                return {"valid": False, "reason": "session_expired"}

            # Check if session is active
            if not session.get("is_active", False):
                return {"valid": False, "reason": "session_inactive"}

            # Update last activity
            self.collection.update_one(
                {"admin_id": admin_id, "active_sessions.session_id": session_id},
                {
                    "$set": {
                        "active_sessions.$.last_activity": datetime.now(timezone.utc),
                        "active_sessions.$.permissions_cache": self._get_cached_permissions(admin_id)
                    }
                }
            )

            return {
                "valid": True,
                "session_id": session_id,
                "admin_id": admin_id,
                "permissions": session["permissions_cache"],
                "mfa_verified": session.get("mfa_verified", False),
                "expires_at": session["expires_at"]
            }

        except Exception as e:
            logger.error(f"Error validating admin session: {e}")
            return {"valid": False, "reason": "validation_error"}

    def terminate_admin_session(self, session_id: str, admin_id: str) -> bool:
        """Terminate admin session"""
        try:
            result = self.collection.update_one(
                {"admin_id": admin_id},
                {
                    "$pull": {"active_sessions": {"session_id": session_id}},
                    "$set": {"updated_at": datetime.now(timezone.utc)}
                }
            )

            if result.modified_count > 0:
                logger.info(f"Admin session terminated: {session_id}")
                return True
            else:
                logger.warning(f"No session found to terminate: {session_id}")
                return False

        except Exception as e:
            logger.error(f"Error terminating admin session: {e}")
            return False

    def terminate_all_admin_sessions(self, admin_id: str) -> int:
        """Terminate all sessions for an admin"""
        try:
            result = self.collection.update_one(
                {"admin_id": admin_id},
                {
                    "$set": {"active_sessions": [], "updated_at": datetime.now(timezone.utc)}
                }
            )

            logger.info(f"All sessions terminated for admin: {admin_id}")
            return result.modified_count

        except Exception as e:
            logger.error(f"Error terminating all sessions for {admin_id}: {e}")
            return 0

    def get_admin_security_profile(self, admin_id: str) -> Dict[str, Any]:
        """Get comprehensive security profile for admin"""
        try:
            admin = self.collection.find_one({"admin_id": admin_id})
            if not admin:
                return {}

            # Calculate password age
            password_age_days = 0
            if admin.get("last_password_change"):
                password_age_days = (datetime.now(timezone.utc) - admin["last_password_change"]).days

            # Get recent login attempts
            recent_logins = self._get_recent_login_attempts(admin_id, days=7)

            # Calculate security score
            security_score = self._calculate_security_score(admin, password_age_days, recent_logins)

            return {
                "admin_id": admin_id,
                "username": admin["username"],
                "role": admin["role"],
                "mfa_enabled": admin.get("mfa_enabled", False),
                "password_age_days": password_age_days,
                "failed_login_attempts": admin.get("failed_login_attempts", 0),
                "account_locked": admin.get("locked_until") is not None and admin["locked_until"] > datetime.now(timezone.utc),
                "recent_login_attempts": recent_logins,
                "active_sessions_count": len(admin.get("active_sessions", [])),
                "security_score": security_score,
                "recommendations": self._generate_security_recommendations(admin, security_score)
            }

        except Exception as e:
            logger.error(f"Error getting security profile for {admin_id}: {e}")
            return {}

    def _get_recent_login_attempts(self, admin_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent login attempts for admin"""
        try:
            # This would require integration with activity logs collection
            # For now, return simulated data based on admin data
            admin = self.collection.find_one({"admin_id": admin_id})
            if not admin:
                return []

            return [{
                "timestamp": admin.get("last_login"),
                "ip_address": admin.get("last_ip"),
                "success": True,
                "mfa_verified": admin.get("mfa_enabled", False)
            }]

        except Exception as e:
            logger.error(f"Error getting recent login attempts for {admin_id}: {e}")
            return []

    def _calculate_security_score(self, admin: Dict[str, Any], password_age_days: int,
                                recent_logins: List[Dict[str, Any]]) -> float:
        """Calculate security score for admin account"""
        score = 100.0

        # MFA factor
        if not admin.get("mfa_enabled", False):
            score -= 30

        # Password age factor
        if password_age_days > 90:
            score -= 20
        elif password_age_days > 60:
            score -= 10

        # Failed login attempts factor
        failed_attempts = admin.get("failed_login_attempts", 0)
        if failed_attempts > 5:
            score -= 25
        elif failed_attempts > 2:
            score -= 15

        # Account lock factor
        if admin.get("locked_until") and admin["locked_until"] > datetime.now(timezone.utc):
            score -= 40

        # Recent successful logins factor
        if not any(login.get("success", False) for login in recent_logins):
            score -= 15

        return max(score, 0.0)

    def _generate_security_recommendations(self, admin: Dict[str, Any], security_score: float) -> List[str]:
        """Generate security recommendations for admin"""
        recommendations = []

        if not admin.get("mfa_enabled", False):
            recommendations.append("Enable multi-factor authentication (MFA)")

        password_age_days = (datetime.now(timezone.utc) - admin.get("last_password_change", datetime.now(timezone.utc))).days
        if password_age_days > 90:
            recommendations.append("Password is older than 90 days - consider updating")

        if admin.get("failed_login_attempts", 0) > 2:
            recommendations.append("Multiple failed login attempts detected - review account security")

        if security_score < 70:
            recommendations.append("Security score is low - implement recommended security measures")

        if not recommendations:
            recommendations.append("Account security is good")

        return recommendations

    def update_admin_password_policy(self, admin_id: str, password_policy: Dict[str, Any]) -> bool:
        """Update password policy for admin"""
        try:
            # Validate password policy
            required_fields = ["min_length", "require_uppercase", "require_lowercase",
                             "require_numbers", "require_symbols", "max_age_days"]

            for field in required_fields:
                if field not in password_policy:
                    raise ValueError(f"Password policy missing required field: {field}")

            result = self.collection.update_one(
                {"admin_id": admin_id},
                {
                    "$set": {
                        "password_policy": password_policy,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )

            if result.modified_count > 0:
                logger.info(f"Password policy updated for admin: {admin_id}")
                return True
            else:
                logger.warning(f"No admin found to update password policy: {admin_id}")
                return False

        except Exception as e:
            logger.error(f"Error updating password policy for {admin_id}: {e}")
            raise

    def get_admin_audit_trail(self, admin_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get audit trail for admin actions"""
        try:
            # This would require integration with activity logs collection
            # For now, return simulated audit data
            admin = self.collection.find_one({"admin_id": admin_id})
            if not admin:
                return []

            # Simulate audit trail based on admin data
            audit_trail = []

            # Login events
            if admin.get("last_login"):
                audit_trail.append({
                    "timestamp": admin["last_login"],
                    "action": "login",
                    "resource_type": "auth",
                    "success": True,
                    "ip_address": admin.get("last_ip"),
                    "details": "Successful login"
                })

            # Permission changes
            if admin.get("updated_at"):
                audit_trail.append({
                    "timestamp": admin["updated_at"],
                    "action": "permissions_updated",
                    "resource_type": "admin",
                    "success": True,
                    "details": f"Permissions updated for role: {admin.get('role', 'unknown')}"
                })

            # Sort by timestamp (most recent first)
            audit_trail.sort(key=lambda x: x["timestamp"], reverse=True)
            return audit_trail[:limit]

        except Exception as e:
            logger.error(f"Error getting audit trail for {admin_id}: {e}")
            return []

    def _extract_client_info(self, user_agent: str = None, ip_address: str = None) -> Dict[str, Any]:
        """Extract client information for session tracking"""
        client_info = {}

        if ip_address:
            client_info["ip_address"] = ip_address
            # Basic VPN detection (simplified)
            if ip_address.startswith(('10.', '172.', '192.168.')):
                client_info["is_vpn"] = True
            else:
                client_info["is_vpn"] = False

        if user_agent:
            client_info["user_agent"] = user_agent
            # Basic browser detection
            ua_lower = user_agent.lower()
            if 'chrome' in ua_lower and 'edg' not in ua_lower:
                client_info["browser"] = "Chrome"
            elif 'firefox' in ua_lower:
                client_info["browser"] = "Firefox"
            elif 'safari' in ua_lower:
                client_info["browser"] = "Safari"
            elif 'edg' in ua_lower:
                client_info["browser"] = "Edge"
            else:
                client_info["browser"] = "Unknown"

        return client_info

    def get_admin_stats(self) -> Dict[str, Any]:
        """Get admin user statistics"""
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_admins": {"$sum": 1},
                        "active_admins": {
                            "$sum": {"$cond": [{"$eq": ["$status", "active"]}, 1, 0]}
                        },
                        "mfa_enabled_count": {
                            "$sum": {"$cond": ["$mfa_enabled", 1, 0]}
                        },
                        "admins_by_role": {
                            "$push": "$role"
                        },
                        "locked_accounts": {
                            "$sum": {
                                "$cond": [
                                    {"$and": [
                                        {"$ne": ["$locked_until", None]},
                                        {"$gt": ["$locked_until", datetime.now(timezone.utc)]}
                                    ]},
                                    1, 0
                                ]
                            }
                        }
                    }
                }
            ]

            result = list(self.collection.aggregate(pipeline))
            if result:
                stats = result[0]
                # Count roles
                role_counts = {}
                for role in stats["admins_by_role"]:
                    role_counts[role] = role_counts.get(role, 0) + 1
                stats["role_distribution"] = role_counts
                del stats["admins_by_role"]
                return stats

            return {}

        except PyMongoError as e:
            logger.error(f"Error getting admin stats: {e}")
            raise