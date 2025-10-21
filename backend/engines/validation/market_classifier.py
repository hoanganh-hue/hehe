"""
Market Classifier
Advanced market segmentation and targeting for credential validation
"""

import os
import json
import re
import time
from datetime import datetime, timezone
from typing import Dict, Optional, Any, List, Tuple
import logging
import hashlib
from enum import Enum

logger = logging.getLogger(__name__)

class MarketSegment(Enum):
    """Market segment enumeration"""
    ENTERPRISE = "enterprise"
    MID_MARKET = "mid_market"
    SMALL_BUSINESS = "small_business"
    STARTUP = "startup"
    CONSUMER = "consumer"
    EDUCATION = "education"
    GOVERNMENT = "government"
    NON_PROFIT = "non_profit"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    TECHNOLOGY = "technology"
    RETAIL = "retail"
    MANUFACTURING = "manufacturing"
    UNKNOWN = "unknown"

class IndustryVertical(Enum):
    """Industry vertical enumeration"""
    TECHNOLOGY = "technology"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    GOVERNMENT = "government"
    RETAIL = "retail"
    MANUFACTURING = "manufacturing"
    CONSULTING = "consulting"
    LEGAL = "legal"
    MEDIA = "media"
    REAL_ESTATE = "real_estate"
    TRAVEL = "travel"
    FOOD_BEVERAGE = "food_beverage"
    AUTOMOTIVE = "automotive"
    ENERGY = "energy"
    TELECOMMUNICATIONS = "telecommunications"
    OTHER = "other"

class MarketClassifier:
    """Advanced market segmentation and targeting classifier"""
    
    def __init__(self):
        self.config = {
            "enable_domain_analysis": os.getenv("ENABLE_DOMAIN_ANALYSIS", "true").lower() == "true",
            "enable_email_pattern_analysis": os.getenv("ENABLE_EMAIL_PATTERN_ANALYSIS", "true").lower() == "true",
            "enable_company_size_estimation": os.getenv("ENABLE_COMPANY_SIZE_ESTIMATION", "true").lower() == "true",
            "enable_industry_classification": os.getenv("ENABLE_INDUSTRY_CLASSIFICATION", "true").lower() == "true",
            "enable_geographic_analysis": os.getenv("ENABLE_GEOGRAPHIC_ANALYSIS", "true").lower() == "true",
            "enable_behavioral_analysis": os.getenv("ENABLE_BEHAVIORAL_ANALYSIS", "true").lower() == "true"
        }
        
        # Load classification models and patterns
        self.domain_patterns = self._load_domain_patterns()
        self.email_patterns = self._load_email_patterns()
        self.industry_keywords = self._load_industry_keywords()
        self.company_size_indicators = self._load_company_size_indicators()
        self.geographic_patterns = self._load_geographic_patterns()
        self.behavioral_patterns = self._load_behavioral_patterns()
        
        logger.info("Market classifier initialized")
    
    def classify_account(self, email: str, domain: str = None, 
                        additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Classify account into market segments
        
        Args:
            email: Email address
            domain: Company domain
            additional_data: Additional account data
            
        Returns:
            Market classification result
        """
        try:
            # Extract domain from email if not provided
            if not domain and "@" in email:
                domain = email.split("@")[1]
            
            classification_result = {
                "email": email,
                "domain": domain,
                "market_segment": MarketSegment.UNKNOWN.value,
                "industry_vertical": IndustryVertical.OTHER.value,
                "company_size_estimate": "unknown",
                "geographic_region": "unknown",
                "targeting_score": 0.0,
                "market_value": 0.0,
                "confidence": 0.0,
                "demographics": {},
                "behavioral_patterns": [],
                "classification_factors": [],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Domain analysis
            if self.config["enable_domain_analysis"] and domain:
                domain_analysis = self._analyze_domain(domain)
                classification_result.update(domain_analysis)
                classification_result["classification_factors"].extend(domain_analysis.get("factors", []))
            
            # Email pattern analysis
            if self.config["enable_email_pattern_analysis"]:
                email_analysis = self._analyze_email_pattern(email)
                classification_result.update(email_analysis)
                classification_result["classification_factors"].extend(email_analysis.get("factors", []))
            
            # Company size estimation
            if self.config["enable_company_size_estimation"]:
                size_analysis = self._estimate_company_size(email, domain, additional_data)
                classification_result.update(size_analysis)
                classification_result["classification_factors"].extend(size_analysis.get("factors", []))
            
            # Industry classification
            if self.config["enable_industry_classification"]:
                industry_analysis = self._classify_industry(email, domain, additional_data)
                classification_result.update(industry_analysis)
                classification_result["classification_factors"].extend(industry_analysis.get("factors", []))
            
            # Geographic analysis
            if self.config["enable_geographic_analysis"]:
                geo_analysis = self._analyze_geographic_location(email, domain, additional_data)
                classification_result.update(geo_analysis)
                classification_result["classification_factors"].extend(geo_analysis.get("factors", []))
            
            # Behavioral analysis
            if self.config["enable_behavioral_analysis"]:
                behavioral_analysis = self._analyze_behavioral_patterns(email, domain, additional_data)
                classification_result.update(behavioral_analysis)
                classification_result["classification_factors"].extend(behavioral_analysis.get("factors", []))
            
            # Calculate overall confidence and targeting score
            classification_result["confidence"] = self._calculate_classification_confidence(classification_result)
            classification_result["targeting_score"] = self._calculate_targeting_score(classification_result)
            classification_result["market_value"] = self._calculate_market_value(classification_result)
            
            logger.info(f"Account classified: {email} -> {classification_result['market_segment']}")
            return classification_result
            
        except Exception as e:
            logger.error(f"Error classifying account: {e}")
            return {
                "email": email,
                "domain": domain,
                "market_segment": MarketSegment.UNKNOWN.value,
                "confidence": 0.0,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _analyze_domain(self, domain: str) -> Dict[str, Any]:
        """Analyze domain for market classification"""
        try:
            analysis = {
                "domain_type": "unknown",
                "domain_quality": "unknown",
                "factors": []
            }
            
            domain_lower = domain.lower()
            
            # Check for common free email providers
            free_providers = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com"]
            if domain_lower in free_providers:
                analysis["domain_type"] = "free_provider"
                analysis["domain_quality"] = "low"
                analysis["factors"].append("Free email provider detected")
                return analysis
            
            # Check for educational institutions
            edu_patterns = [r"\.edu$", r"\.ac\.[a-z]{2,3}$", r"university", r"college", r"school"]
            for pattern in edu_patterns:
                if re.search(pattern, domain_lower):
                    analysis["domain_type"] = "educational"
                    analysis["domain_quality"] = "medium"
                    analysis["factors"].append("Educational institution domain")
                    return analysis
            
            # Check for government domains
            gov_patterns = [r"\.gov$", r"\.gov\.[a-z]{2,3}$", r"government", r"municipal"]
            for pattern in gov_patterns:
                if re.search(pattern, domain_lower):
                    analysis["domain_type"] = "government"
                    analysis["domain_quality"] = "high"
                    analysis["factors"].append("Government domain detected")
                    return analysis
            
            # Check for non-profit organizations
            nonprofit_patterns = [r"\.org$", r"foundation", r"charity", r"nonprofit"]
            for pattern in nonprofit_patterns:
                if re.search(pattern, domain_lower):
                    analysis["domain_type"] = "non_profit"
                    analysis["domain_quality"] = "medium"
                    analysis["factors"].append("Non-profit organization domain")
                    return analysis
            
            # Check for corporate domains
            corporate_patterns = [r"\.com$", r"\.net$", r"\.biz$", r"\.co\.[a-z]{2,3}$"]
            for pattern in corporate_patterns:
                if re.search(pattern, domain_lower):
                    analysis["domain_type"] = "corporate"
                    analysis["domain_quality"] = "high"
                    analysis["factors"].append("Corporate domain detected")
                    return analysis
            
            # Check domain length and complexity
            if len(domain) > 20:
                analysis["factors"].append("Long domain name - likely corporate")
            elif len(domain) < 10:
                analysis["factors"].append("Short domain name - likely small business")
            
            # Check for subdomains
            if domain.count('.') > 1:
                analysis["factors"].append("Subdomain detected - likely enterprise")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing domain: {e}")
            return {"domain_type": "unknown", "factors": [f"Domain analysis error: {str(e)}"]}
    
    def _analyze_email_pattern(self, email: str) -> Dict[str, Any]:
        """Analyze email pattern for classification"""
        try:
            analysis = {
                "email_pattern": "unknown",
                "pattern_quality": "unknown",
                "factors": []
            }
            
            local_part, domain = email.split("@") if "@" in email else ("", "")
            
            # Check for generic patterns
            generic_patterns = [
                r"^admin@", r"^info@", r"^contact@", r"^support@", r"^sales@",
                r"^marketing@", r"^hr@", r"^finance@", r"^legal@"
            ]
            
            for pattern in generic_patterns:
                if re.search(pattern, local_part.lower()):
                    analysis["email_pattern"] = "generic"
                    analysis["pattern_quality"] = "medium"
                    analysis["factors"].append("Generic business email pattern")
                    return analysis
            
            # Check for personal patterns
            personal_patterns = [
                r"^[a-z]+\.[a-z]+@",  # firstname.lastname@
                r"^[a-z]+[0-9]+@",    # name123@
                r"^[a-z]+_[a-z]+@",   # firstname_lastname@
            ]
            
            for pattern in personal_patterns:
                if re.search(pattern, local_part.lower()):
                    analysis["email_pattern"] = "personal"
                    analysis["pattern_quality"] = "high"
                    analysis["factors"].append("Personal email pattern")
                    return analysis
            
            # Check for role-based patterns
            role_patterns = [
                r"ceo@", r"cto@", r"cfo@", r"president@", r"director@",
                r"manager@", r"coordinator@", r"specialist@", r"analyst@"
            ]
            
            for pattern in role_patterns:
                if re.search(pattern, local_part.lower()):
                    analysis["email_pattern"] = "role_based"
                    analysis["pattern_quality"] = "high"
                    analysis["factors"].append("Role-based email pattern")
                    return analysis
            
            # Check for department patterns
            dept_patterns = [
                r"it@", r"hr@", r"finance@", r"marketing@", r"sales@",
                r"engineering@", r"operations@", r"legal@", r"security@"
            ]
            
            for pattern in dept_patterns:
                if re.search(pattern, local_part.lower()):
                    analysis["email_pattern"] = "department"
                    analysis["pattern_quality"] = "high"
                    analysis["factors"].append("Department email pattern")
                    return analysis
            
            # Check for numbered patterns
            if re.search(r"[0-9]", local_part):
                analysis["factors"].append("Numbered email pattern - likely corporate")
            
            # Check for special characters
            if re.search(r"[._-]", local_part):
                analysis["factors"].append("Structured email pattern - likely corporate")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing email pattern: {e}")
            return {"email_pattern": "unknown", "factors": [f"Email pattern analysis error: {str(e)}"]}
    
    def _estimate_company_size(self, email: str, domain: str, additional_data: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate company size based on available data"""
        try:
            analysis = {
                "company_size_estimate": "unknown",
                "size_confidence": 0.0,
                "factors": []
            }
            
            # Use additional data if available
            if additional_data:
                employee_count = additional_data.get("employee_count")
                if employee_count:
                    if employee_count >= 1000:
                        analysis["company_size_estimate"] = "enterprise"
                        analysis["size_confidence"] = 0.9
                        analysis["factors"].append(f"Employee count: {employee_count}")
                    elif employee_count >= 100:
                        analysis["company_size_estimate"] = "mid_market"
                        analysis["size_confidence"] = 0.8
                        analysis["factors"].append(f"Employee count: {employee_count}")
                    elif employee_count >= 10:
                        analysis["company_size_estimate"] = "small_business"
                        analysis["size_confidence"] = 0.7
                        analysis["factors"].append(f"Employee count: {employee_count}")
                    else:
                        analysis["company_size_estimate"] = "startup"
                        analysis["size_confidence"] = 0.6
                        analysis["factors"].append(f"Employee count: {employee_count}")
                    return analysis
            
            # Estimate based on domain analysis
            if domain:
                # Check for enterprise indicators
                enterprise_indicators = [
                    "corp", "corporation", "inc", "incorporated", "ltd", "limited",
                    "enterprise", "global", "international", "worldwide"
                ]
                
                domain_lower = domain.lower()
                for indicator in enterprise_indicators:
                    if indicator in domain_lower:
                        analysis["company_size_estimate"] = "enterprise"
                        analysis["size_confidence"] = 0.6
                        analysis["factors"].append(f"Enterprise indicator in domain: {indicator}")
                        return analysis
                
                # Check for startup indicators
                startup_indicators = [
                    "startup", "lab", "labs", "studio", "works", "ventures"
                ]
                
                for indicator in startup_indicators:
                    if indicator in domain_lower:
                        analysis["company_size_estimate"] = "startup"
                        analysis["size_confidence"] = 0.6
                        analysis["factors"].append(f"Startup indicator in domain: {indicator}")
                        return analysis
            
            # Estimate based on email pattern
            local_part = email.split("@")[0].lower() if "@" in email else ""
            
            # Generic emails suggest larger organizations
            generic_emails = ["admin", "info", "contact", "support", "sales", "marketing"]
            if local_part in generic_emails:
                analysis["company_size_estimate"] = "mid_market"
                analysis["size_confidence"] = 0.5
                analysis["factors"].append("Generic email suggests mid-market size")
                return analysis
            
            # Role-based emails suggest larger organizations
            role_emails = ["ceo", "cto", "cfo", "president", "director", "manager"]
            if local_part in role_emails:
                analysis["company_size_estimate"] = "mid_market"
                analysis["size_confidence"] = 0.6
                analysis["factors"].append("Role-based email suggests mid-market size")
                return analysis
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error estimating company size: {e}")
            return {"company_size_estimate": "unknown", "factors": [f"Size estimation error: {str(e)}"]}
    
    def _classify_industry(self, email: str, domain: str, additional_data: Dict[str, Any]) -> Dict[str, Any]:
        """Classify industry vertical"""
        try:
            analysis = {
                "industry_vertical": IndustryVertical.OTHER.value,
                "industry_confidence": 0.0,
                "factors": []
            }
            
            # Use additional data if available
            if additional_data:
                industry = additional_data.get("industry")
                if industry:
                    industry_lower = industry.lower()
                    for vertical in IndustryVertical:
                        if vertical.value in industry_lower:
                            analysis["industry_vertical"] = vertical.value
                            analysis["industry_confidence"] = 0.9
                            analysis["factors"].append(f"Industry from data: {industry}")
                            return analysis
            
            # Analyze domain for industry keywords
            if domain:
                domain_lower = domain.lower()
                
                for industry, keywords in self.industry_keywords.items():
                    for keyword in keywords:
                        if keyword in domain_lower:
                            analysis["industry_vertical"] = industry
                            analysis["industry_confidence"] = 0.7
                            analysis["factors"].append(f"Industry keyword in domain: {keyword}")
                            return analysis
            
            # Analyze email for industry keywords
            email_lower = email.lower()
            for industry, keywords in self.industry_keywords.items():
                for keyword in keywords:
                    if keyword in email_lower:
                        analysis["industry_vertical"] = industry
                        analysis["industry_confidence"] = 0.6
                        analysis["factors"].append(f"Industry keyword in email: {keyword}")
                        return analysis
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error classifying industry: {e}")
            return {"industry_vertical": IndustryVertical.OTHER.value, "factors": [f"Industry classification error: {str(e)}"]}
    
    def _analyze_geographic_location(self, email: str, domain: str, additional_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze geographic location"""
        try:
            analysis = {
                "geographic_region": "unknown",
                "country": "unknown",
                "geo_confidence": 0.0,
                "factors": []
            }
            
            # Use additional data if available
            if additional_data:
                location = additional_data.get("location")
                country = additional_data.get("country")
                if location or country:
                    analysis["geographic_region"] = self._map_location_to_region(location, country)
                    analysis["country"] = country or "unknown"
                    analysis["geo_confidence"] = 0.8
                    analysis["factors"].append(f"Location from data: {location or country}")
                    return analysis
            
            # Analyze domain for geographic indicators
            if domain:
                domain_lower = domain.lower()
                
                # Check for country-specific TLDs
                country_tlds = {
                    ".vn": "vietnam", ".us": "united_states", ".uk": "united_kingdom",
                    ".ca": "canada", ".au": "australia", ".de": "germany",
                    ".fr": "france", ".jp": "japan", ".cn": "china",
                    ".in": "india", ".br": "brazil", ".mx": "mexico"
                }
                
                for tld, country in country_tlds.items():
                    if domain_lower.endswith(tld):
                        analysis["country"] = country
                        analysis["geographic_region"] = self._map_country_to_region(country)
                        analysis["geo_confidence"] = 0.7
                        analysis["factors"].append(f"Country TLD detected: {tld}")
                        return analysis
                
                # Check for geographic keywords in domain
                geo_keywords = {
                    "vietnam": ["vn", "vietnam", "hanoi", "hochiminh", "saigon"],
                    "united_states": ["usa", "america", "us", "nyc", "california"],
                    "united_kingdom": ["uk", "britain", "london", "england"],
                    "canada": ["ca", "canada", "toronto", "vancouver"],
                    "australia": ["au", "australia", "sydney", "melbourne"]
                }
                
                for country, keywords in geo_keywords.items():
                    for keyword in keywords:
                        if keyword in domain_lower:
                            analysis["country"] = country
                            analysis["geographic_region"] = self._map_country_to_region(country)
                            analysis["geo_confidence"] = 0.6
                            analysis["factors"].append(f"Geographic keyword in domain: {keyword}")
                            return analysis
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing geographic location: {e}")
            return {"geographic_region": "unknown", "factors": [f"Geographic analysis error: {str(e)}"]}
    
    def _analyze_behavioral_patterns(self, email: str, domain: str, additional_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze behavioral patterns"""
        try:
            analysis = {
                "behavioral_patterns": [],
                "behavioral_confidence": 0.0,
                "factors": []
            }
            
            # Use additional data if available
            if additional_data:
                # Check for behavioral indicators
                if additional_data.get("login_frequency"):
                    analysis["behavioral_patterns"].append("frequent_login")
                    analysis["factors"].append("Frequent login pattern detected")
                
                if additional_data.get("device_diversity"):
                    analysis["behavioral_patterns"].append("multi_device")
                    analysis["factors"].append("Multi-device usage pattern")
                
                if additional_data.get("location_diversity"):
                    analysis["behavioral_patterns"].append("multi_location")
                    analysis["factors"].append("Multi-location usage pattern")
                
                if additional_data.get("time_patterns"):
                    analysis["behavioral_patterns"].append("time_consistent")
                    analysis["factors"].append("Consistent time pattern")
            
            # Analyze email for behavioral indicators
            local_part = email.split("@")[0].lower() if "@" in email else ""
            
            # Check for professional indicators
            professional_indicators = ["ceo", "cto", "cfo", "president", "director", "manager", "executive"]
            if any(indicator in local_part for indicator in professional_indicators):
                analysis["behavioral_patterns"].append("professional_role")
                analysis["factors"].append("Professional role indicator")
            
            # Check for technical indicators
            technical_indicators = ["admin", "root", "system", "tech", "it", "dev", "engineer"]
            if any(indicator in local_part for indicator in technical_indicators):
                analysis["behavioral_patterns"].append("technical_role")
                analysis["factors"].append("Technical role indicator")
            
            # Check for business indicators
            business_indicators = ["sales", "marketing", "business", "commercial", "revenue"]
            if any(indicator in local_part for indicator in business_indicators):
                analysis["behavioral_patterns"].append("business_role")
                analysis["factors"].append("Business role indicator")
            
            analysis["behavioral_confidence"] = len(analysis["behavioral_patterns"]) * 0.2
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing behavioral patterns: {e}")
            return {"behavioral_patterns": [], "factors": [f"Behavioral analysis error: {str(e)}"]}
    
    def _calculate_classification_confidence(self, classification_result: Dict[str, Any]) -> float:
        """Calculate overall classification confidence"""
        try:
            confidence_factors = []
            
            # Domain analysis confidence
            if classification_result.get("domain_type") != "unknown":
                confidence_factors.append(0.3)
            
            # Email pattern confidence
            if classification_result.get("email_pattern") != "unknown":
                confidence_factors.append(0.2)
            
            # Company size confidence
            if classification_result.get("company_size_estimate") != "unknown":
                confidence_factors.append(0.2)
            
            # Industry confidence
            if classification_result.get("industry_vertical") != IndustryVertical.OTHER.value:
                confidence_factors.append(0.2)
            
            # Geographic confidence
            if classification_result.get("geographic_region") != "unknown":
                confidence_factors.append(0.1)
            
            return min(1.0, sum(confidence_factors))
            
        except Exception as e:
            logger.error(f"Error calculating classification confidence: {e}")
            return 0.0
    
    def _calculate_targeting_score(self, classification_result: Dict[str, Any]) -> float:
        """Calculate targeting score for exploitation"""
        try:
            score = 0.0
            
            # Market segment scoring
            market_segment = classification_result.get("market_segment", MarketSegment.UNKNOWN.value)
            segment_scores = {
                MarketSegment.ENTERPRISE.value: 0.9,
                MarketSegment.MID_MARKET.value: 0.8,
                MarketSegment.SMALL_BUSINESS.value: 0.6,
                MarketSegment.STARTUP.value: 0.4,
                MarketSegment.CONSUMER.value: 0.2,
                MarketSegment.EDUCATION.value: 0.5,
                MarketSegment.GOVERNMENT.value: 0.7,
                MarketSegment.NON_PROFIT.value: 0.3,
                MarketSegment.HEALTHCARE.value: 0.8,
                MarketSegment.FINANCE.value: 0.9,
                MarketSegment.TECHNOLOGY.value: 0.7
            }
            score += segment_scores.get(market_segment, 0.0) * 0.4
            
            # Industry vertical scoring
            industry_vertical = classification_result.get("industry_vertical", IndustryVertical.OTHER.value)
            industry_scores = {
                IndustryVertical.FINANCE.value: 0.9,
                IndustryVertical.HEALTHCARE.value: 0.8,
                IndustryVertical.TECHNOLOGY.value: 0.7,
                IndustryVertical.GOVERNMENT.value: 0.7,
                IndustryVertical.EDUCATION.value: 0.5,
                IndustryVertical.RETAIL.value: 0.6,
                IndustryVertical.MANUFACTURING.value: 0.6,
                IndustryVertical.CONSULTING.value: 0.7,
                IndustryVertical.LEGAL.value: 0.8
            }
            score += industry_scores.get(industry_vertical, 0.0) * 0.3
            
            # Company size scoring
            company_size = classification_result.get("company_size_estimate", "unknown")
            size_scores = {
                "enterprise": 0.9,
                "mid_market": 0.8,
                "small_business": 0.6,
                "startup": 0.4
            }
            score += size_scores.get(company_size, 0.0) * 0.2
            
            # Behavioral patterns scoring
            behavioral_patterns = classification_result.get("behavioral_patterns", [])
            if "professional_role" in behavioral_patterns:
                score += 0.1
            
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"Error calculating targeting score: {e}")
            return 0.0
    
    def _calculate_market_value(self, classification_result: Dict[str, Any]) -> float:
        """Calculate market value score"""
        try:
            value = 0.0
            
            # Base value from targeting score
            value += classification_result.get("targeting_score", 0.0) * 0.6
            
            # Industry value multiplier
            industry_vertical = classification_result.get("industry_vertical", IndustryVertical.OTHER.value)
            industry_multipliers = {
                IndustryVertical.FINANCE.value: 1.5,
                IndustryVertical.HEALTHCARE.value: 1.3,
                IndustryVertical.TECHNOLOGY.value: 1.2,
                IndustryVertical.GOVERNMENT.value: 1.4,
                IndustryVertical.LEGAL.value: 1.3
            }
            multiplier = industry_multipliers.get(industry_vertical, 1.0)
            value *= multiplier
            
            # Geographic value adjustment
            geographic_region = classification_result.get("geographic_region", "unknown")
            geo_multipliers = {
                "north_america": 1.2,
                "europe": 1.1,
                "asia_pacific": 1.0,
                "latin_america": 0.8,
                "africa": 0.7
            }
            geo_multiplier = geo_multipliers.get(geographic_region, 1.0)
            value *= geo_multiplier
            
            return min(1.0, value)
            
        except Exception as e:
            logger.error(f"Error calculating market value: {e}")
            return 0.0
    
    def _map_location_to_region(self, location: str, country: str) -> str:
        """Map location to geographic region"""
        try:
            if not location and not country:
                return "unknown"
            
            location_lower = (location or "").lower()
            country_lower = (country or "").lower()
            
            # North America
            na_countries = ["united_states", "usa", "canada", "mexico"]
            na_keywords = ["north_america", "america", "us", "usa"]
            
            if any(c in country_lower for c in na_countries) or any(k in location_lower for k in na_keywords):
                return "north_america"
            
            # Europe
            eu_countries = ["united_kingdom", "uk", "germany", "france", "italy", "spain"]
            eu_keywords = ["europe", "european", "eu"]
            
            if any(c in country_lower for c in eu_countries) or any(k in location_lower for k in eu_keywords):
                return "europe"
            
            # Asia Pacific
            ap_countries = ["china", "japan", "korea", "singapore", "australia", "india"]
            ap_keywords = ["asia", "pacific", "asian"]
            
            if any(c in country_lower for c in ap_countries) or any(k in location_lower for k in ap_keywords):
                return "asia_pacific"
            
            # Latin America
            la_countries = ["brazil", "argentina", "chile", "colombia"]
            la_keywords = ["latin_america", "south_america"]
            
            if any(c in country_lower for c in la_countries) or any(k in location_lower for k in la_keywords):
                return "latin_america"
            
            return "unknown"
            
        except Exception as e:
            logger.error(f"Error mapping location to region: {e}")
            return "unknown"
    
    def _map_country_to_region(self, country: str) -> str:
        """Map country to geographic region"""
        return self._map_location_to_region("", country)
    
    def _load_domain_patterns(self) -> Dict[str, List[str]]:
        """Load domain classification patterns"""
        return {
            "enterprise": ["corp", "corporation", "inc", "incorporated", "ltd", "limited", "enterprise", "global", "international"],
            "startup": ["startup", "lab", "labs", "studio", "works", "ventures", "innovations"],
            "educational": ["edu", "university", "college", "school", "academy", "institute"],
            "government": ["gov", "government", "municipal", "state", "federal"],
            "non_profit": ["org", "foundation", "charity", "nonprofit", "ngo"]
        }
    
    def _load_email_patterns(self) -> Dict[str, List[str]]:
        """Load email pattern classifications"""
        return {
            "generic": ["admin", "info", "contact", "support", "sales", "marketing", "hr", "finance", "legal"],
            "personal": ["firstname.lastname", "firstname_lastname", "firstname123"],
            "role_based": ["ceo", "cto", "cfo", "president", "director", "manager", "coordinator", "specialist", "analyst"],
            "department": ["it", "hr", "finance", "marketing", "sales", "engineering", "operations", "legal", "security"]
        }
    
    def _load_industry_keywords(self) -> Dict[str, List[str]]:
        """Load industry classification keywords"""
        return {
            IndustryVertical.TECHNOLOGY.value: ["tech", "software", "it", "digital", "cyber", "ai", "data", "cloud", "saas"],
            IndustryVertical.FINANCE.value: ["bank", "finance", "financial", "investment", "capital", "credit", "loan", "insurance"],
            IndustryVertical.HEALTHCARE.value: ["health", "medical", "hospital", "clinic", "pharma", "biotech", "healthcare"],
            IndustryVertical.EDUCATION.value: ["education", "school", "university", "college", "academy", "learning", "training"],
            IndustryVertical.GOVERNMENT.value: ["government", "gov", "municipal", "state", "federal", "public", "administration"],
            IndustryVertical.RETAIL.value: ["retail", "store", "shop", "commerce", "ecommerce", "marketplace", "shopping"],
            IndustryVertical.MANUFACTURING.value: ["manufacturing", "factory", "production", "industrial", "automotive", "machinery"],
            IndustryVertical.CONSULTING.value: ["consulting", "advisory", "strategy", "management", "professional"],
            IndustryVertical.LEGAL.value: ["legal", "law", "attorney", "lawyer", "law firm", "legal services"],
            IndustryVertical.MEDIA.value: ["media", "news", "publishing", "broadcast", "entertainment", "content"],
            IndustryVertical.REAL_ESTATE.value: ["real estate", "property", "housing", "construction", "development"],
            IndustryVertical.TRAVEL.value: ["travel", "tourism", "hotel", "airline", "vacation", "booking"],
            IndustryVertical.FOOD_BEVERAGE.value: ["food", "restaurant", "beverage", "catering", "dining", "culinary"],
            IndustryVertical.AUTOMOTIVE.value: ["automotive", "car", "vehicle", "auto", "transportation", "mobility"],
            IndustryVertical.ENERGY.value: ["energy", "power", "electricity", "oil", "gas", "renewable", "solar"],
            IndustryVertical.TELECOMMUNICATIONS.value: ["telecom", "communication", "network", "wireless", "broadband", "internet"]
        }
    
    def _load_company_size_indicators(self) -> Dict[str, List[str]]:
        """Load company size indicators"""
        return {
            "enterprise": ["corp", "corporation", "inc", "incorporated", "ltd", "limited", "enterprise", "global", "international", "worldwide"],
            "mid_market": ["company", "group", "holdings", "partners", "associates"],
            "small_business": ["small", "local", "regional", "family"],
            "startup": ["startup", "lab", "labs", "studio", "works", "ventures", "innovations", "tech"]
        }
    
    def _load_geographic_patterns(self) -> Dict[str, List[str]]:
        """Load geographic patterns"""
        return {
            "north_america": ["usa", "america", "us", "canada", "mexico", "north_america"],
            "europe": ["uk", "britain", "england", "germany", "france", "italy", "spain", "europe", "european"],
            "asia_pacific": ["china", "japan", "korea", "singapore", "australia", "india", "asia", "pacific"],
            "latin_america": ["brazil", "argentina", "chile", "colombia", "latin_america", "south_america"],
            "africa": ["africa", "african", "south_africa", "nigeria", "egypt"]
        }
    
    def _load_behavioral_patterns(self) -> Dict[str, List[str]]:
        """Load behavioral patterns"""
        return {
            "professional": ["ceo", "cto", "cfo", "president", "director", "manager", "executive"],
            "technical": ["admin", "root", "system", "tech", "it", "dev", "engineer", "developer"],
            "business": ["sales", "marketing", "business", "commercial", "revenue", "growth"],
            "support": ["support", "help", "service", "customer", "client"]
        }
    
    def batch_classify_accounts(self, accounts_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Batch classify multiple accounts"""
        try:
            classified_accounts = []
            
            for account_data in accounts_data:
                try:
                    classification = self.classify_account(
                        email=account_data.get("email"),
                        domain=account_data.get("domain"),
                        additional_data=account_data.get("additional_data", {})
                    )
                    classified_accounts.append(classification)
                    
                except Exception as e:
                    logger.error(f"Error classifying account: {e}")
                    classified_accounts.append({
                        "email": account_data.get("email"),
                        "error": str(e),
                        "market_segment": MarketSegment.UNKNOWN.value,
                        "confidence": 0.0
                    })
            
            logger.info(f"Batch classification completed: {len(classified_accounts)} accounts")
            return classified_accounts
            
        except Exception as e:
            logger.error(f"Error in batch classification: {e}")
            return []
    
    def get_classification_stats(self) -> Dict[str, Any]:
        """Get classification statistics"""
        try:
            return {
                "market_segments": [segment.value for segment in MarketSegment],
                "industry_verticals": [vertical.value for vertical in IndustryVertical],
                "configuration": self.config,
                "pattern_counts": {
                    "domain_patterns": len(self.domain_patterns),
                    "email_patterns": len(self.email_patterns),
                    "industry_keywords": len(self.industry_keywords),
                    "company_size_indicators": len(self.company_size_indicators),
                    "geographic_patterns": len(self.geographic_patterns),
                    "behavioral_patterns": len(self.behavioral_patterns)
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting classification stats: {e}")
            return {"error": str(e)}