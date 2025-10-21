"""
Authentication Middleware
JWT token verification and admin session validation
"""

import logging
from typing import Optional
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware

from api.auth.jwt_handler import JWTHandler
from api.auth.permissions import PermissionManager
from config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)
jwt_handler = JWTHandler()
permission_manager = PermissionManager()

async def get_current_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Dependency to get current authenticated admin user
    Used in FastAPI route dependencies
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials"
        )
    
    try:
        # Decode and verify token
        token_data = jwt_handler.decode_token(credentials.credentials)
        
        # Check if user is admin
        if token_data.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        return {
            "id": token_data["sub"],
            "username": token_data["username"],
            "role": token_data["role"],
            "permissions": token_data.get("permissions", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to authenticate admin user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for protected routes"""
    
    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.protected_paths = [
            "/api/admin",
            "/api/auth/me",
            "/api/auth/change-password"
        ]
        self.public_paths = [
            "/health",
            "/api/auth/login",
            "/api/oauth",
            "/api/capture",
            "/merchant",
            "/admin",
            "/static",
            "/assets",
            "/docs",
            "/openapi.json"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Process request through authentication middleware"""
        try:
            # Check if path requires authentication
            if self._is_protected_path(request.url.path):
                # Extract token from Authorization header
                auth_header = request.headers.get("Authorization")
                
                if not auth_header or not auth_header.startswith("Bearer "):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Missing or invalid authorization header"
                    )
                
                token = auth_header.split(" ")[1]
                
                # Verify token
                try:
                    token_data = jwt_handler.decode_token(token)
                    
                    # Add user info to request state
                    request.state.user = {
                        "id": token_data["sub"],
                        "username": token_data["username"],
                        "role": token_data["role"],
                        "permissions": token_data["permissions"]
                    }
                    
                except Exception as e:
                    logger.warning(f"Token verification failed: {e}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid or expired token"
                    )
            
            # Process request
            response = await call_next(request)
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication middleware error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    def _is_protected_path(self, path: str) -> bool:
        """Check if path requires authentication"""
        # Check if path is in protected paths
        for protected_path in self.protected_paths:
            if path.startswith(protected_path):
                return True
        
        # Check if path is in public paths
        for public_path in self.public_paths:
            if path.startswith(public_path):
                return False
        
        # Default to protected for API routes
        return path.startswith("/api/")

def setup_auth_middleware(app: FastAPI):
    """Setup authentication middleware"""
    try:
        app.add_middleware(AuthenticationMiddleware)
        logger.info("Authentication middleware configured")
        
    except Exception as e:
        logger.error(f"Failed to setup authentication middleware: {e}")
        raise
