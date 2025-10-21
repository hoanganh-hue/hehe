"""
Network Segmentation and Security
Implements network-level security controls and segmentation
"""

import ipaddress
import asyncio
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import logging
import json

from ..database.redis_client import get_redis_client

logger = logging.getLogger(__name__)

@dataclass
class NetworkRule:
    """Network security rule"""
    rule_id: str
    name: str
    action: str  # allow, deny, log
    source_ips: List[str]
    destination_ips: List[str]
    ports: List[int]
    protocols: List[str]
    priority: int
    enabled: bool = True
    created_at: datetime = None
    updated_at: datetime = None

@dataclass
class SecurityGroup:
    """Security group configuration"""
    group_id: str
    name: str
    description: str
    rules: List[NetworkRule]
    tags: Dict[str, str]
    created_at: datetime = None
    updated_at: datetime = None

@dataclass
class NetworkSegment:
    """Network segment configuration"""
    segment_id: str
    name: str
    cidr: str
    security_groups: List[str]
    allowed_services: List[str]
    isolation_level: str  # public, private, isolated
    created_at: datetime = None
    updated_at: datetime = None

class NetworkSecurityManager:
    """
    Manages network security rules and segmentation
    """
    
    def __init__(self):
        """
        Initialize network security manager
        """
        self.redis_client = None
        self.security_groups = {}
        self.network_segments = {}
        self.firewall_rules = {}
        self.blocked_ips = set()
        self.allowed_ips = set()
        self.suspicious_ips = set()
        self.whitelist_ips = set()
        self.blacklist_ips = set()
        
        # Default security groups
        self._initialize_default_security_groups()
        
        # Default network segments
        self._initialize_default_segments()
    
    async def initialize(self):
        """Initialize network security manager"""
        try:
            self.redis_client = await get_redis_client()
            await self._load_security_configuration()
            logger.info("Network security manager initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis for network security: {e}")
            logger.info("Using local configuration for network security")
    
    def _initialize_default_security_groups(self):
        """Initialize default security groups"""
        try:
            # Admin security group
            admin_rules = [
                NetworkRule(
                    rule_id="admin_ssh",
                    name="Admin SSH Access",
                    action="allow",
                    source_ips=["0.0.0.0/0"],
                    destination_ips=["0.0.0.0/0"],
                    ports=[22],
                    protocols=["tcp"],
                    priority=100
                ),
                NetworkRule(
                    rule_id="admin_https",
                    name="Admin HTTPS Access",
                    action="allow",
                    source_ips=["0.0.0.0/0"],
                    destination_ips=["0.0.0.0/0"],
                    ports=[443],
                    protocols=["tcp"],
                    priority=100
                )
            ]
            
            admin_group = SecurityGroup(
                group_id="admin",
                name="Administrator Access",
                description="Security group for administrator access",
                rules=admin_rules,
                tags={"type": "admin", "environment": "production"}
            )
            
            self.security_groups["admin"] = admin_group
            
            # Application security group
            app_rules = [
                NetworkRule(
                    rule_id="app_http",
                    name="Application HTTP",
                    action="allow",
                    source_ips=["0.0.0.0/0"],
                    destination_ips=["0.0.0.0/0"],
                    ports=[80, 443],
                    protocols=["tcp"],
                    priority=200
                ),
                NetworkRule(
                    rule_id="app_api",
                    name="Application API",
                    action="allow",
                    source_ips=["0.0.0.0/0"],
                    destination_ips=["0.0.0.0/0"],
                    ports=[8000],
                    protocols=["tcp"],
                    priority=200
                )
            ]
            
            app_group = SecurityGroup(
                group_id="application",
                name="Application Services",
                description="Security group for application services",
                rules=app_rules,
                tags={"type": "application", "environment": "production"}
            )
            
            self.security_groups["application"] = app_group
            
            # Database security group
            db_rules = [
                NetworkRule(
                    rule_id="db_mongodb",
                    name="MongoDB Access",
                    action="allow",
                    source_ips=["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"],
                    destination_ips=["0.0.0.0/0"],
                    ports=[27017],
                    protocols=["tcp"],
                    priority=300
                ),
                NetworkRule(
                    rule_id="db_redis",
                    name="Redis Access",
                    action="allow",
                    source_ips=["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"],
                    destination_ips=["0.0.0.0/0"],
                    ports=[6379],
                    protocols=["tcp"],
                    priority=300
                )
            ]
            
            db_group = SecurityGroup(
                group_id="database",
                name="Database Services",
                description="Security group for database services",
                rules=db_rules,
                tags={"type": "database", "environment": "production"}
            )
            
            self.security_groups["database"] = db_group
            
        except Exception as e:
            logger.error(f"Error initializing default security groups: {e}")
    
    def _initialize_default_segments(self):
        """Initialize default network segments"""
        try:
            # Public segment
            public_segment = NetworkSegment(
                segment_id="public",
                name="Public Network",
                cidr="0.0.0.0/0",
                security_groups=["admin", "application"],
                allowed_services=["http", "https", "ssh"],
                isolation_level="public"
            )
            
            self.network_segments["public"] = public_segment
            
            # Private segment
            private_segment = NetworkSegment(
                segment_id="private",
                name="Private Network",
                cidr="10.0.0.0/8",
                security_groups=["application", "database"],
                allowed_services=["mongodb", "redis", "influxdb", "beef"],
                isolation_level="private"
            )
            
            self.network_segments["private"] = private_segment
            
            # Isolated segment
            isolated_segment = NetworkSegment(
                segment_id="isolated",
                name="Isolated Network",
                cidr="172.16.0.0/12",
                security_groups=["database"],
                allowed_services=["mongodb", "redis"],
                isolation_level="isolated"
            )
            
            self.network_segments["isolated"] = isolated_segment
            
        except Exception as e:
            logger.error(f"Error initializing default network segments: {e}")
    
    async def _load_security_configuration(self):
        """Load security configuration from Redis"""
        try:
            if not self.redis_client:
                return
            
            # Load security groups
            security_groups_data = await self.redis_client.get("security_groups")
            if security_groups_data:
                groups_data = json.loads(security_groups_data)
                for group_id, group_data in groups_data.items():
                    self.security_groups[group_id] = self._deserialize_security_group(group_data)
            
            # Load network segments
            segments_data = await self.redis_client.get("network_segments")
            if segments_data:
                segments = json.loads(segments_data)
                for segment_id, segment_data in segments.items():
                    self.network_segments[segment_id] = self._deserialize_network_segment(segment_data)
            
            # Load blocked IPs
            blocked_ips_data = await self.redis_client.get("blocked_ips")
            if blocked_ips_data:
                self.blocked_ips = set(json.loads(blocked_ips_data))
            
            # Load allowed IPs
            allowed_ips_data = await self.redis_client.get("allowed_ips")
            if allowed_ips_data:
                self.allowed_ips = set(json.loads(allowed_ips_data))
            
            # Load suspicious IPs
            suspicious_ips_data = await self.redis_client.get("suspicious_ips")
            if suspicious_ips_data:
                self.suspicious_ips = set(json.loads(suspicious_ips_data))
            
            logger.info("Security configuration loaded from Redis")
            
        except Exception as e:
            logger.error(f"Error loading security configuration: {e}")
    
    async def _save_security_configuration(self):
        """Save security configuration to Redis"""
        try:
            if not self.redis_client:
                return
            
            # Save security groups
            groups_data = {}
            for group_id, group in self.security_groups.items():
                groups_data[group_id] = self._serialize_security_group(group)
            await self.redis_client.set("security_groups", json.dumps(groups_data))
            
            # Save network segments
            segments_data = {}
            for segment_id, segment in self.network_segments.items():
                segments_data[segment_id] = self._serialize_network_segment(segment)
            await self.redis_client.set("network_segments", json.dumps(segments_data))
            
            # Save blocked IPs
            await self.redis_client.set("blocked_ips", json.dumps(list(self.blocked_ips)))
            
            # Save allowed IPs
            await self.redis_client.set("allowed_ips", json.dumps(list(self.allowed_ips)))
            
            # Save suspicious IPs
            await self.redis_client.set("suspicious_ips", json.dumps(list(self.suspicious_ips)))
            
            logger.info("Security configuration saved to Redis")
            
        except Exception as e:
            logger.error(f"Error saving security configuration: {e}")
    
    def _serialize_security_group(self, group: SecurityGroup) -> Dict:
        """Serialize security group to dictionary"""
        return {
            "group_id": group.group_id,
            "name": group.name,
            "description": group.description,
            "rules": [
                {
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "action": rule.action,
                    "source_ips": rule.source_ips,
                    "destination_ips": rule.destination_ips,
                    "ports": rule.ports,
                    "protocols": rule.protocols,
                    "priority": rule.priority,
                    "enabled": rule.enabled,
                    "created_at": rule.created_at.isoformat() if rule.created_at else None,
                    "updated_at": rule.updated_at.isoformat() if rule.updated_at else None
                }
                for rule in group.rules
            ],
            "tags": group.tags,
            "created_at": group.created_at.isoformat() if group.created_at else None,
            "updated_at": group.updated_at.isoformat() if group.updated_at else None
        }
    
    def _deserialize_security_group(self, data: Dict) -> SecurityGroup:
        """Deserialize security group from dictionary"""
        rules = []
        for rule_data in data.get("rules", []):
            rule = NetworkRule(
                rule_id=rule_data["rule_id"],
                name=rule_data["name"],
                action=rule_data["action"],
                source_ips=rule_data["source_ips"],
                destination_ips=rule_data["destination_ips"],
                ports=rule_data["ports"],
                protocols=rule_data["protocols"],
                priority=rule_data["priority"],
                enabled=rule_data.get("enabled", True),
                created_at=datetime.fromisoformat(rule_data["created_at"]) if rule_data.get("created_at") else None,
                updated_at=datetime.fromisoformat(rule_data["updated_at"]) if rule_data.get("updated_at") else None
            )
            rules.append(rule)
        
        return SecurityGroup(
            group_id=data["group_id"],
            name=data["name"],
            description=data["description"],
            rules=rules,
            tags=data.get("tags", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        )
    
    def _serialize_network_segment(self, segment: NetworkSegment) -> Dict:
        """Serialize network segment to dictionary"""
        return {
            "segment_id": segment.segment_id,
            "name": segment.name,
            "cidr": segment.cidr,
            "security_groups": segment.security_groups,
            "allowed_services": segment.allowed_services,
            "isolation_level": segment.isolation_level,
            "created_at": segment.created_at.isoformat() if segment.created_at else None,
            "updated_at": segment.updated_at.isoformat() if segment.updated_at else None
        }
    
    def _deserialize_network_segment(self, data: Dict) -> NetworkSegment:
        """Deserialize network segment from dictionary"""
        return NetworkSegment(
            segment_id=data["segment_id"],
            name=data["name"],
            cidr=data["cidr"],
            security_groups=data["security_groups"],
            allowed_services=data["allowed_services"],
            isolation_level=data["isolation_level"],
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        )
    
    async def check_network_access(self, source_ip: str, destination_ip: str, port: int, protocol: str) -> Tuple[bool, str]:
        """
        Check if network access is allowed
        
        Args:
            source_ip: Source IP address
            destination_ip: Destination IP address
            port: Port number
            protocol: Protocol (tcp, udp, etc.)
            
        Returns:
            Tuple of (allowed, reason)
        """
        try:
            # Check if source IP is blocked
            if source_ip in self.blocked_ips:
                return False, f"Source IP {source_ip} is blocked"
            
            # Check if source IP is whitelisted
            if source_ip in self.whitelist_ips:
                return True, f"Source IP {source_ip} is whitelisted"
            
            # Check if source IP is blacklisted
            if source_ip in self.blacklist_ips:
                return False, f"Source IP {source_ip} is blacklisted"
            
            # Check security group rules
            for group_id, group in self.security_groups.items():
                if not group.enabled:
                    continue
                
                for rule in group.rules:
                    if not rule.enabled:
                        continue
                    
                    # Check if rule matches
                    if self._rule_matches(rule, source_ip, destination_ip, port, protocol):
                        if rule.action == "allow":
                            return True, f"Allowed by rule {rule.rule_id}"
                        elif rule.action == "deny":
                            return False, f"Denied by rule {rule.rule_id}"
            
            # Default deny
            return False, "No matching allow rule found"
            
        except Exception as e:
            logger.error(f"Error checking network access: {e}")
            return False, f"Error checking access: {e}"
    
    def _rule_matches(self, rule: NetworkRule, source_ip: str, destination_ip: str, port: int, protocol: str) -> bool:
        """
        Check if rule matches the request
        
        Args:
            rule: Network rule
            source_ip: Source IP address
            destination_ip: Destination IP address
            port: Port number
            protocol: Protocol
            
        Returns:
            True if rule matches
        """
        try:
            # Check source IP
            source_match = False
            for source_cidr in rule.source_ips:
                if self._ip_in_cidr(source_ip, source_cidr):
                    source_match = True
                    break
            
            if not source_match:
                return False
            
            # Check destination IP
            dest_match = False
            for dest_cidr in rule.destination_ips:
                if self._ip_in_cidr(destination_ip, dest_cidr):
                    dest_match = True
                    break
            
            if not dest_match:
                return False
            
            # Check port
            if port not in rule.ports:
                return False
            
            # Check protocol
            if protocol.lower() not in [p.lower() for p in rule.protocols]:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rule match: {e}")
            return False
    
    def _ip_in_cidr(self, ip: str, cidr: str) -> bool:
        """
        Check if IP is in CIDR range
        
        Args:
            ip: IP address
            cidr: CIDR range
            
        Returns:
            True if IP is in range
        """
        try:
            return ipaddress.ip_address(ip) in ipaddress.ip_network(cidr)
        except Exception:
            return False
    
    async def block_ip(self, ip_address: str, reason: str = "Security violation"):
        """
        Block IP address
        
        Args:
            ip_address: IP address to block
            reason: Reason for blocking
        """
        try:
            self.blocked_ips.add(ip_address)
            await self._save_security_configuration()
            
            logger.warning(f"Blocked IP address {ip_address}: {reason}")
            
        except Exception as e:
            logger.error(f"Error blocking IP: {e}")
    
    async def unblock_ip(self, ip_address: str):
        """
        Unblock IP address
        
        Args:
            ip_address: IP address to unblock
        """
        try:
            self.blocked_ips.discard(ip_address)
            await self._save_security_configuration()
            
            logger.info(f"Unblocked IP address {ip_address}")
            
        except Exception as e:
            logger.error(f"Error unblocking IP: {e}")
    
    async def add_whitelist_ip(self, ip_address: str):
        """
        Add IP to whitelist
        
        Args:
            ip_address: IP address to whitelist
        """
        try:
            self.whitelist_ips.add(ip_address)
            await self._save_security_configuration()
            
            logger.info(f"Added IP to whitelist: {ip_address}")
            
        except Exception as e:
            logger.error(f"Error adding IP to whitelist: {e}")
    
    async def remove_whitelist_ip(self, ip_address: str):
        """
        Remove IP from whitelist
        
        Args:
            ip_address: IP address to remove
        """
        try:
            self.whitelist_ips.discard(ip_address)
            await self._save_security_configuration()
            
            logger.info(f"Removed IP from whitelist: {ip_address}")
            
        except Exception as e:
            logger.error(f"Error removing IP from whitelist: {e}")
    
    async def add_blacklist_ip(self, ip_address: str):
        """
        Add IP to blacklist
        
        Args:
            ip_address: IP address to blacklist
        """
        try:
            self.blacklist_ips.add(ip_address)
            await self._save_security_configuration()
            
            logger.info(f"Added IP to blacklist: {ip_address}")
            
        except Exception as e:
            logger.error(f"Error adding IP to blacklist: {e}")
    
    async def remove_blacklist_ip(self, ip_address: str):
        """
        Remove IP from blacklist
        
        Args:
            ip_address: IP address to remove
        """
        try:
            self.blacklist_ips.discard(ip_address)
            await self._save_security_configuration()
            
            logger.info(f"Removed IP from blacklist: {ip_address}")
            
        except Exception as e:
            logger.error(f"Error removing IP from blacklist: {e}")
    
    async def mark_suspicious_ip(self, ip_address: str, reason: str = "Suspicious activity"):
        """
        Mark IP as suspicious
        
        Args:
            ip_address: IP address
            reason: Reason for marking as suspicious
        """
        try:
            self.suspicious_ips.add(ip_address)
            await self._save_security_configuration()
            
            logger.warning(f"Marked IP as suspicious {ip_address}: {reason}")
            
        except Exception as e:
            logger.error(f"Error marking IP as suspicious: {e}")
    
    async def get_network_statistics(self) -> Dict:
        """
        Get network security statistics
        
        Returns:
            Dictionary of network statistics
        """
        try:
            return {
                "blocked_ips_count": len(self.blocked_ips),
                "allowed_ips_count": len(self.allowed_ips),
                "suspicious_ips_count": len(self.suspicious_ips),
                "whitelist_ips_count": len(self.whitelist_ips),
                "blacklist_ips_count": len(self.blacklist_ips),
                "security_groups_count": len(self.security_groups),
                "network_segments_count": len(self.network_segments),
                "blocked_ips": list(self.blocked_ips),
                "suspicious_ips": list(self.suspicious_ips),
                "whitelist_ips": list(self.whitelist_ips),
                "blacklist_ips": list(self.blacklist_ips)
            }
            
        except Exception as e:
            logger.error(f"Error getting network statistics: {e}")
            return {}

# Global network security manager instance
network_security_manager: Optional[NetworkSecurityManager] = None

async def get_network_security_manager() -> NetworkSecurityManager:
    """Get the global network security manager instance"""
    global network_security_manager
    if network_security_manager is None:
        network_security_manager = NetworkSecurityManager()
        await network_security_manager.initialize()
    return network_security_manager

async def check_network_access(source_ip: str, destination_ip: str, port: int, protocol: str) -> Tuple[bool, str]:
    """Check network access"""
    manager = await get_network_security_manager()
    return await manager.check_network_access(source_ip, destination_ip, port, protocol)

async def block_ip(ip_address: str, reason: str = "Security violation"):
    """Block IP address"""
    manager = await get_network_security_manager()
    await manager.block_ip(ip_address, reason)

async def unblock_ip(ip_address: str):
    """Unblock IP address"""
    manager = await get_network_security_manager()
    await manager.unblock_ip(ip_address)

async def get_network_statistics():
    """Get network statistics"""
    manager = await get_network_security_manager()
    return await manager.get_network_statistics()
