"""
Authentication Router
Admin login, logout, token refresh, and validation endpoints
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from config import settings
from api.auth.admin_auth import AdminAuthManager
from api.auth.jwt_handler import JWTHandler
from api.auth.session_manager import SessionManager
from database.connection import get_database_connection

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str
    remember_me: bool = False

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user_info: dict

class TokenValidationResponse(BaseModel):
    valid: bool
    user_info: Optional[dict] = None
    expires_at: Optional[datetime] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

# Initialize managers
auth_manager = AdminAuthManager()
jwt_handler = JWTHandler()
session_manager = SessionManager()

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, http_request: Request):
    """Admin login endpoint"""
    try:
        # Get client IP and user agent
        client_ip = http_request.client.host
        user_agent = http_request.headers.get("user-agent", "")
        
        # Authenticate user
        user = await auth_manager.authenticate_user(
            request.username, 
            request.password
        )
        
        if not user:
            logger.warning(f"Failed login attempt for username: {request.username} from IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Generate JWT token
        token_data = {
            "sub": str(user["_id"]),
            "username": user["username"],
            "role": user["role"],
            "permissions": user["permissions"]
        }
        
        expires_delta = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        access_token = jwt_handler.create_access_token(
            data=token_data,
            expires_delta=expires_delta
        )
        
        # Create session
        session_id = await session_manager.create_session(
            user_id=str(user["_id"]),
            client_ip=client_ip,
            user_agent=user_agent,
            remember_me=request.remember_me
        )
        
        # Log successful login
        logger.info(f"Successful login for user: {request.username} from IP: {client_ip}")
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.JWT_EXPIRATION_HOURS * 3600,
            user_info={
                "id": str(user["_id"]),
                "username": user["username"],
                "role": user["role"],
                "permissions": user["permissions"],
                "session_id": session_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Admin logout endpoint"""
    try:
        # Decode token to get user info
        token_data = jwt_handler.decode_token(credentials.credentials)
        user_id = token_data.get("sub")
        
        if user_id:
            # Invalidate session
            await session_manager.invalidate_session(user_id)
            
            # Log logout
            logger.info(f"User {user_id} logged out")
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token"""
    try:
        # Validate refresh token
        token_data = jwt_handler.decode_token(request.refresh_token)
        
        # Generate new access token
        new_token_data = {
            "sub": token_data["sub"],
            "username": token_data["username"],
            "role": token_data["role"],
            "permissions": token_data["permissions"]
        }
        
        expires_delta = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        access_token = jwt_handler.create_access_token(
            data=new_token_data,
            expires_delta=expires_delta
        )
        
        return RefreshTokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.JWT_EXPIRATION_HOURS * 3600
        )
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.get("/validate", response_model=TokenValidationResponse)
async def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate access token"""
    try:
        # Decode and validate token
        token_data = jwt_handler.decode_token(credentials.credentials)
        
        # Check if user still exists and is active
        user = await auth_manager.get_user_by_id(token_data["sub"])
        
        if not user or not user.get("is_active", True):
            return TokenValidationResponse(valid=False)
        
        return TokenValidationResponse(
            valid=True,
            user_info={
                "id": str(user["_id"]),
                "username": user["username"],
                "role": user["role"],
                "permissions": user["permissions"]
            },
            expires_at=datetime.fromtimestamp(token_data["exp"])
        )
        
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return TokenValidationResponse(valid=False)

@router.get("/me")
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user information"""
    try:
        # Decode token
        token_data = jwt_handler.decode_token(credentials.credentials)
        user_id = token_data["sub"]
        
        # Get user from database
        user = await auth_manager.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user.get("email"),
            "role": user["role"],
            "permissions": user["permissions"],
            "last_login": user.get("last_login"),
            "is_active": user.get("is_active", True)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Change user password"""
    try:
        # Decode token
        token_data = jwt_handler.decode_token(credentials.credentials)
        user_id = token_data["sub"]
        
        # Change password
        success = await auth_manager.change_password(
            user_id, 
            old_password, 
            new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid old password"
            )
        
        logger.info(f"Password changed for user: {user_id}")
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
