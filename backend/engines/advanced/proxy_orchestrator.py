"""
Advanced Proxy Orchestrator
Geographic IP assignment, load balancing, and intelligent proxy management
"""

import os
import json
import time
import random
import asyncio
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple, Set
import logging
import ipaddress
import threading
from collections import defaultdict, Counter

from api.capture.proxy_manager import ProxyManager, ProxyInfo, ProxyPool

logger = logging.getLogger(__name__)

class GeographicProfile:
    """Geographic profile for proxy assignment"""
    
    def __init__(self, country: str, region: str = None, city: str = None):
        self.country = country
        self.region = region
        self.city = city
        self.priority_score = 0.0
        self.proxy_count = 0
        self.success_rate = 0.0
        self.avg_response_time = 0.0
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "country": self.country,
            "region": self.region,
            "city": self.city,
            "priority_score": self.priority_score,
            "proxy_count": self.proxy_count,
            "success_rate": self.success_rate,
            "avg_response_time": self.avg_response_time
        }

class ProxyAssignmentStrategy:
    """Proxy assignment strategies"""
    
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    FASTEST_RESPONSE = "fastest_response"
    GEOGRAPHIC_PRIORITY = "geographic_priority"
    LOAD_BALANCED = "load_balanced"
    SESSION_PERSISTENT = "session_persistent"

class VietnameseProxyProfiles:
    """Vietnamese proxy profiles and characteristics"""
    
    VIETNAMESE_CARRIERS = {
        "Viettel": {
            "asn_ranges": ["AS7552"],
            "ip_ranges": ["203.113.0.0/16", "118.70.0.0/16"],
            "mobile_prefixes": ["+8496", "+8497", "+8498"],
            "success_rate": 0.95,
            "avg_response_time": 120
        },
        "Vinaphone": {
            "asn_ranges": ["AS45899"],
            "ip_ranges": ["123.30.0.0/16", "171.244.0.0/16"],
            "mobile_prefixes": ["+8491", "+8494"],
            "success_rate": 0.92,
            "avg_response_time": 135
        },
        "Mobifone": {
            "asn_ranges": ["AS45899"],
            "ip_ranges": ["171.244.0.0/16", "123.30.0.0/16"],
            "mobile_prefixes": ["+8490", "+8493"],
            "success_rate": 0.90,
            "avg_response_time": 140
        }
    }
    
    VIETNAMESE_CITIES = {
        "Ho Chi Minh City": {
            "coordinates": [10.8231, 106.6297],
            "population": 9000000,
            "business_centers": ["District 1", "District 3", "District 7"],
            "proxy_density": "high"
        },
        "Hanoi": {
            "coordinates": [21.0285, 105.8542],
            "population": 8000000,
            "business_centers": ["Ba Dinh", "Hoan Kiem", "Cau Giay"],
            "proxy_density": "high"
        },
        "Da Nang": {
            "coordinates": [16.0544, 108.2022],
            "population": 1200000,
            "business_centers": ["Hai Chau", "Thanh Khe"],
            "proxy_density": "medium"
        },
        "Can Tho": {
            "coordinates": [10.0452, 105.7469],
            "population": 1200000,
            "business_centers": ["Ninh Kieu", "Cai Rang"],
            "proxy_density": "medium"
        }
    }

class ProxyOrchestrator:
    """Advanced proxy orchestration system"""
    
    def __init__(self, proxy_manager: ProxyManager, mongodb_connection=None, redis_client=None):
        self.proxy_manager = proxy_manager
        self.mongodb = mongodb_connection
        self.redis = redis_client
        
        # Assignment strategies
        self.assignment_strategy = ProxyAssignmentStrategy.GEOGRAPHIC_PRIORITY
        self.session_persistence_enabled = True
        self.geographic_targeting_enabled = True
        
        # Geographic profiles
        self.geographic_profiles: Dict[str, GeographicProfile] = {}
        self.vietnamese_profiles = VietnameseProxyProfiles()
        
        # Load balancing
        self.load_balancing_enabled = True
        self.max_sessions_per_proxy = 10
        self.session_affinity_window = 3600  # 1 hour
        
        # Performance tracking
        self.performance_metrics = {
            "total_assignments": 0,
            "successful_assignments": 0,
            "failed_assignments": 0,
            "geographic_hits": 0,
            "load_balanced_assignments": 0
        }
        
        # Session-to-proxy mapping with persistence
        self.session_assignments: Dict[str, Dict[str, Any]] = {}
        
        # Initialize geographic profiles
        self._initialize_geographic_profiles()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _initialize_geographic_profiles(self):
        """Initialize geographic profiles for Vietnamese regions"""
        try:
            # Vietnam profiles
            vietnam_profile = GeographicProfile("VN", "Vietnam", "Ho Chi Minh City")
            vietnam_profile.priority_score = 1.0
            self.geographic_profiles["VN"] = vietnam_profile
            
            # Regional profiles
            for city, data in self.vietnamese_profiles.VIETNAMESE_CITIES.items():
                profile = GeographicProfile("VN", "Vietnam", city)
                profile.priority_score = 0.8 if data["proxy_density"] == "high" else 0.6
                self.geographic_profiles[f"VN_{city.replace(' ', '_')}"] = profile
            
            # Carrier profiles
            for carrier, data in self.vietnamese_profiles.VIETNAMESE_CARRIERS.items():
                profile = GeographicProfile("VN", "Vietnam", f"{carrier} Mobile")
                profile.priority_score = data["success_rate"]
                profile.success_rate = data["success_rate"]
                profile.avg_response_time = data["avg_response_time"]
                self.geographic_profiles[f"VN_{carrier}"] = profile
            
            logger.info(f"Initialized {len(self.geographic_profiles)} geographic profiles")
            
        except Exception as e:
            logger.error(f"Error initializing geographic profiles: {e}")
    
    def _start_background_tasks(self):
        """Start background maintenance tasks"""
        # Performance metrics update thread
        metrics_thread = threading.Thread(target=self._update_performance_metrics, daemon=True)
        metrics_thread.start()
        
        # Session cleanup thread
        cleanup_thread = threading.Thread(target=self._cleanup_expired_sessions, daemon=True)
        cleanup_thread.start()
        
        # Geographic profile update thread
        profile_thread = threading.Thread(target=self._update_geographic_profiles, daemon=True)
        profile_thread.start()
    
    def assign_proxy_for_victim(self, victim_id: str, session_id: str, 
                              geographic_preference: str = "VN",
                              assignment_strategy: str = None) -> Optional[ProxyInfo]:
        """
        Assign proxy for victim with advanced orchestration
        
        Args:
            victim_id: Victim identifier
            session_id: Session identifier
            geographic_preference: Geographic preference (VN, VN_Ho_Chi_Minh_City, etc.)
            assignment_strategy: Assignment strategy override
            
        Returns:
            Assigned proxy or None
        """
        try:
            strategy = assignment_strategy or self.assignment_strategy
            
            # Check for existing session assignment (persistence)
            if self.session_persistence_enabled:
                existing_proxy = self._get_persistent_session_proxy(session_id)
                if existing_proxy and existing_proxy.can_accept_session():
                    logger.info(f"Using persistent proxy for session {session_id}")
                    return existing_proxy
            
            # Get suitable proxies based on strategy
            suitable_proxies = self._get_suitable_proxies(geographic_preference, strategy)
            
            if not suitable_proxies:
                logger.warning(f"No suitable proxies found for geographic preference: {geographic_preference}")
                return None
            
            # Apply assignment strategy
            selected_proxy = self._apply_assignment_strategy(suitable_proxies, strategy, session_id)
            
            if selected_proxy:
                # Update session assignment
                self._update_session_assignment(session_id, selected_proxy, geographic_preference)
                
                # Update performance metrics
                self.performance_metrics["total_assignments"] += 1
                self.performance_metrics["successful_assignments"] += 1
                
                if geographic_preference.startswith("VN"):
                    self.performance_metrics["geographic_hits"] += 1
                
                logger.info(f"Proxy {selected_proxy.get_address()} assigned to victim {victim_id} "
                          f"(session: {session_id}, strategy: {strategy})")
                
                return selected_proxy
            
            return None
            
        except Exception as e:
            logger.error(f"Error assigning proxy for victim {victim_id}: {e}")
            self.performance_metrics["failed_assignments"] += 1
            return None
    
    def _get_suitable_proxies(self, geographic_preference: str, strategy: str) -> List[ProxyInfo]:
        """Get suitable proxies based on geographic preference and strategy"""
        try:
            # Get all healthy proxies
            all_proxies = self.proxy_manager.proxy_pool.get_healthy_proxies()
            
            if not all_proxies:
                return []
            
            # Filter by geographic preference
            if self.geographic_targeting_enabled and geographic_preference:
                filtered_proxies = self._filter_proxies_by_geography(all_proxies, geographic_preference)
            else:
                filtered_proxies = all_proxies
            
            # Apply strategy-specific filtering
            if strategy == ProxyAssignmentStrategy.LEAST_CONNECTIONS:
                filtered_proxies = sorted(filtered_proxies, key=lambda p: p.session_count)
            elif strategy == ProxyAssignmentStrategy.FASTEST_RESPONSE:
                filtered_proxies = sorted(filtered_proxies, 
                                        key=lambda p: p.avg_response_time or 1000)
            elif strategy == ProxyAssignmentStrategy.LOAD_BALANCED:
                filtered_proxies = self._apply_load_balancing_filter(filtered_proxies)
            
            return filtered_proxies
            
        except Exception as e:
            logger.error(f"Error getting suitable proxies: {e}")
            return []
    
    def _filter_proxies_by_geography(self, proxies: List[ProxyInfo], 
                                   geographic_preference: str) -> List[ProxyInfo]:
        """Filter proxies by geographic preference"""
        try:
            filtered_proxies = []
            
            for proxy in proxies:
                if not proxy.country:
                    continue
                
                # Direct country match
                if proxy.country == geographic_preference:
                    filtered_proxies.append(proxy)
                    continue
                
                # Vietnamese region matching
                if geographic_preference.startswith("VN"):
                    if proxy.country == "VN":
                        # Check for specific Vietnamese city/carrier
                        if "_" in geographic_preference:
                            region_part = geographic_preference.split("_", 1)[1]
                            
                            # City matching
                            if region_part in proxy.city or region_part in proxy.region:
                                filtered_proxies.append(proxy)
                                continue
                            
                            # Carrier matching
                            for carrier in self.vietnamese_profiles.VIETNAMESE_CARRIERS:
                                if region_part in carrier:
                                    # Check if proxy IP matches carrier ranges
                                    if self._is_proxy_from_carrier(proxy, carrier):
                                        filtered_proxies.append(proxy)
                                        continue
                        
                        # General Vietnam match
                        filtered_proxies.append(proxy)
            
            return filtered_proxies
            
        except Exception as e:
            logger.error(f"Error filtering proxies by geography: {e}")
            return proxies
    
    def _is_proxy_from_carrier(self, proxy: ProxyInfo, carrier: str) -> bool:
        """Check if proxy is from specific Vietnamese carrier"""
        try:
            if carrier not in self.vietnamese_profiles.VIETNAMESE_CARRIERS:
                return False
            
            carrier_data = self.vietnamese_profiles.VIETNAMESE_CARRIERS[carrier]
            
            # Check IP ranges
            proxy_ip = ipaddress.ip_address(proxy.host)
            for ip_range in carrier_data["ip_ranges"]:
                if proxy_ip in ipaddress.ip_network(ip_range):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking carrier for proxy: {e}")
            return False
    
    def _apply_load_balancing_filter(self, proxies: List[ProxyInfo]) -> List[ProxyInfo]:
        """Apply load balancing filter to proxies"""
        try:
            if not self.load_balancing_enabled:
                return proxies
            
            # Calculate load scores
            load_scores = []
            for proxy in proxies:
                # Load score based on session count and response time
                session_load = proxy.session_count / self.max_sessions_per_proxy
                response_load = (proxy.avg_response_time or 1000) / 1000  # Normalize to seconds
                
                load_score = session_load * 0.7 + response_load * 0.3
                load_scores.append((proxy, load_score))
            
            # Sort by load score (lower is better)
            load_scores.sort(key=lambda x: x[1])
            
            # Return top 50% least loaded proxies
            top_count = max(1, len(load_scores) // 2)
            return [proxy for proxy, _ in load_scores[:top_count]]
            
        except Exception as e:
            logger.error(f"Error applying load balancing filter: {e}")
            return proxies
    
    def _apply_assignment_strategy(self, proxies: List[ProxyInfo], 
                                 strategy: str, session_id: str) -> Optional[ProxyInfo]:
        """Apply specific assignment strategy"""
        try:
            if not proxies:
                return None
            
            if strategy == ProxyAssignmentStrategy.ROUND_ROBIN:
                return self._round_robin_assignment(proxies, session_id)
            elif strategy == ProxyAssignmentStrategy.LEAST_CONNECTIONS:
                return proxies[0]  # Already sorted
            elif strategy == ProxyAssignmentStrategy.FASTEST_RESPONSE:
                return proxies[0]  # Already sorted
            elif strategy == ProxyAssignmentStrategy.GEOGRAPHIC_PRIORITY:
                return self._geographic_priority_assignment(proxies)
            elif strategy == ProxyAssignmentStrategy.LOAD_BALANCED:
                return proxies[0]  # Already filtered
            else:
                # Default to random selection
                return random.choice(proxies)
                
        except Exception as e:
            logger.error(f"Error applying assignment strategy: {e}")
            return random.choice(proxies) if proxies else None
    
    def _round_robin_assignment(self, proxies: List[ProxyInfo], session_id: str) -> ProxyInfo:
        """Round-robin assignment based on session ID"""
        try:
            # Use session ID hash for consistent assignment
            session_hash = int(hashlib.md5(session_id.encode()).hexdigest(), 16)
            index = session_hash % len(proxies)
            return proxies[index]
            
        except Exception as e:
            logger.error(f"Error in round-robin assignment: {e}")
            return proxies[0]
    
    def _geographic_priority_assignment(self, proxies: List[ProxyInfo]) -> ProxyInfo:
        """Geographic priority assignment"""
        try:
            # Score proxies based on geographic profiles
            scored_proxies = []
            
            for proxy in proxies:
                score = 0.5  # Base score
                
                # Country bonus
                if proxy.country == "VN":
                    score += 0.3
                
                # City bonus
                if proxy.city and any(city in proxy.city for city in 
                                    self.vietnamese_profiles.VIETNAMESE_CITIES):
                    score += 0.2
                
                # Performance bonus
                if proxy.successful_requests > 0:
                    success_rate = proxy.successful_requests / proxy.total_requests
                    score += success_rate * 0.2
                
                scored_proxies.append((proxy, score))
            
            # Sort by score and return best
            scored_proxies.sort(key=lambda x: x[1], reverse=True)
            return scored_proxies[0][0]
            
        except Exception as e:
            logger.error(f"Error in geographic priority assignment: {e}")
            return proxies[0]
    
    def _get_persistent_session_proxy(self, session_id: str) -> Optional[ProxyInfo]:
        """Get persistent proxy for session"""
        try:
            if session_id not in self.session_assignments:
                return None
            
            assignment = self.session_assignments[session_id]
            proxy_id = assignment.get("proxy_id")
            
            if not proxy_id:
                return None
            
            # Check if assignment is still valid
            assigned_at = assignment.get("assigned_at")
            if assigned_at:
                assigned_time = datetime.fromisoformat(assigned_at)
                if datetime.now(timezone.utc) - assigned_time > timedelta(seconds=self.session_affinity_window):
                    # Assignment expired
                    del self.session_assignments[session_id]
                    return None
            
            # Get proxy from manager
            return self.proxy_manager.proxy_pool.get_proxy(proxy_id)
            
        except Exception as e:
            logger.error(f"Error getting persistent session proxy: {e}")
            return None
    
    def _update_session_assignment(self, session_id: str, proxy: ProxyInfo, 
                                 geographic_preference: str):
        """Update session assignment with persistence"""
        try:
            assignment = {
                "proxy_id": proxy.get_address(),
                "assigned_at": datetime.now(timezone.utc).isoformat(),
                "geographic_preference": geographic_preference,
                "strategy": self.assignment_strategy
            }
            
            self.session_assignments[session_id] = assignment
            
            # Store in Redis for persistence
            if self.redis:
                key = f"session_assignment:{session_id}"
                self.redis.setex(key, self.session_affinity_window, json.dumps(assignment))
            
            # Store in MongoDB
            if self.mongodb:
                self._store_session_assignment(session_id, assignment)
                
        except Exception as e:
            logger.error(f"Error updating session assignment: {e}")
    
    def _store_session_assignment(self, session_id: str, assignment: Dict[str, Any]):
        """Store session assignment in MongoDB"""
        try:
            if not self.mongodb:
                return
            
            db = self.mongodb.get_database("zalopay_phishing")
            assignments_collection = db.session_assignments
            
            document = {
                "session_id": session_id,
                "assignment": assignment,
                "created_at": datetime.now(timezone.utc),
                "expires_at": datetime.now(timezone.utc) + timedelta(seconds=self.session_affinity_window)
            }
            
            assignments_collection.replace_one(
                {"session_id": session_id},
                document,
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error storing session assignment: {e}")
    
    def release_victim_proxy(self, victim_id: str, session_id: str) -> bool:
        """Release proxy for victim"""
        try:
            # Remove from session assignments
            if session_id in self.session_assignments:
                del self.session_assignments[session_id]
            
            # Remove from Redis
            if self.redis:
                key = f"session_assignment:{session_id}"
                self.redis.delete(key)
            
            # Remove from MongoDB
            if self.mongodb:
                db = self.mongodb.get_database("zalopay_phishing")
                assignments_collection = db.session_assignments
                assignments_collection.delete_one({"session_id": session_id})
            
            # Release from proxy manager
            return self.proxy_manager.release_session_proxy(session_id)
            
        except Exception as e:
            logger.error(f"Error releasing victim proxy: {e}")
            return False
    
    def _update_performance_metrics(self):
        """Update performance metrics periodically"""
        while True:
            try:
                time.sleep(300)  # Update every 5 minutes
                
                # Calculate success rate
                total = self.performance_metrics["total_assignments"]
                if total > 0:
                    success_rate = self.performance_metrics["successful_assignments"] / total
                    self.performance_metrics["success_rate"] = success_rate
                
                # Store metrics in Redis
                if self.redis:
                    key = "proxy_orchestrator_metrics"
                    self.redis.setex(key, 3600, json.dumps(self.performance_metrics))
                
                logger.info(f"Updated performance metrics: {self.performance_metrics}")
                
            except Exception as e:
                logger.error(f"Error updating performance metrics: {e}")
    
    def _cleanup_expired_sessions(self):
        """Clean up expired session assignments"""
        while True:
            try:
                time.sleep(600)  # Clean up every 10 minutes
                
                current_time = datetime.now(timezone.utc)
                expired_sessions = []
                
                for session_id, assignment in self.session_assignments.items():
                    assigned_at = assignment.get("assigned_at")
                    if assigned_at:
                        assigned_time = datetime.fromisoformat(assigned_at)
                        if current_time - assigned_time > timedelta(seconds=self.session_affinity_window):
                            expired_sessions.append(session_id)
                
                # Remove expired sessions
                for session_id in expired_sessions:
                    del self.session_assignments[session_id]
                
                if expired_sessions:
                    logger.info(f"Cleaned up {len(expired_sessions)} expired session assignments")
                
            except Exception as e:
                logger.error(f"Error cleaning up expired sessions: {e}")
    
    def _update_geographic_profiles(self):
        """Update geographic profiles based on performance"""
        while True:
            try:
                time.sleep(1800)  # Update every 30 minutes
                
                # Update proxy counts for each geographic profile
                for profile_key, profile in self.geographic_profiles.items():
                    country = profile.country
                    proxies = self.proxy_manager.proxy_pool.get_healthy_proxies(country)
                    profile.proxy_count = len(proxies)
                    
                    # Calculate success rate for geographic region
                    if proxies:
                        total_requests = sum(p.total_requests for p in proxies)
                        successful_requests = sum(p.successful_requests for p in proxies)
                        
                        if total_requests > 0:
                            profile.success_rate = successful_requests / total_requests
                        
                        # Calculate average response time
                        response_times = [p.avg_response_time for p in proxies if p.avg_response_time]
                        if response_times:
                            profile.avg_response_time = sum(response_times) / len(response_times)
                
                logger.info("Updated geographic profiles")
                
            except Exception as e:
                logger.error(f"Error updating geographic profiles: {e}")
    
    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        return {
            "performance_metrics": self.performance_metrics,
            "geographic_profiles": {k: v.to_dict() for k, v in self.geographic_profiles.items()},
            "active_session_assignments": len(self.session_assignments),
            "assignment_strategy": self.assignment_strategy,
            "session_persistence_enabled": self.session_persistence_enabled,
            "geographic_targeting_enabled": self.geographic_targeting_enabled,
            "load_balancing_enabled": self.load_balancing_enabled,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def set_assignment_strategy(self, strategy: str):
        """Set assignment strategy"""
        if strategy in [ProxyAssignmentStrategy.ROUND_ROBIN, 
                       ProxyAssignmentStrategy.LEAST_CONNECTIONS,
                       ProxyAssignmentStrategy.FASTEST_RESPONSE,
                       ProxyAssignmentStrategy.GEOGRAPHIC_PRIORITY,
                       ProxyAssignmentStrategy.LOAD_BALANCED]:
            self.assignment_strategy = strategy
            logger.info(f"Assignment strategy changed to: {strategy}")
        else:
            logger.error(f"Invalid assignment strategy: {strategy}")
    
    def enable_geographic_targeting(self, enabled: bool):
        """Enable/disable geographic targeting"""
        self.geographic_targeting_enabled = enabled
        logger.info(f"Geographic targeting {'enabled' if enabled else 'disabled'}")
    
    def enable_session_persistence(self, enabled: bool):
        """Enable/disable session persistence"""
        self.session_persistence_enabled = enabled
        logger.info(f"Session persistence {'enabled' if enabled else 'disabled'}")

# Global orchestrator instance
proxy_orchestrator = None

def initialize_proxy_orchestrator(proxy_manager: ProxyManager, 
                                mongodb_connection=None, redis_client=None) -> ProxyOrchestrator:
    """Initialize global proxy orchestrator"""
    global proxy_orchestrator
    proxy_orchestrator = ProxyOrchestrator(proxy_manager, mongodb_connection, redis_client)
    return proxy_orchestrator

def get_proxy_orchestrator() -> ProxyOrchestrator:
    """Get global proxy orchestrator"""
    if proxy_orchestrator is None:
        raise ValueError("Proxy orchestrator not initialized")
    return proxy_orchestrator

# Convenience functions
def assign_proxy_for_victim(victim_id: str, session_id: str, 
                          geographic_preference: str = "VN") -> Optional[ProxyInfo]:
    """Assign proxy for victim (global convenience function)"""
    return get_proxy_orchestrator().assign_proxy_for_victim(victim_id, session_id, geographic_preference)

def release_victim_proxy(victim_id: str, session_id: str) -> bool:
    """Release victim proxy (global convenience function)"""
    return get_proxy_orchestrator().release_victim_proxy(victim_id, session_id)

def get_orchestrator_stats() -> Dict[str, Any]:
    """Get orchestrator stats (global convenience function)"""
    return get_proxy_orchestrator().get_orchestrator_stats()
