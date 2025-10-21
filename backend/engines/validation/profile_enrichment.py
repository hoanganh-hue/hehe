"""
Profile Enrichment Engine
Advanced profile enrichment and data aggregation for credential validation
"""

import os
import json
import time
import asyncio
import aiohttp
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple
import logging
import hashlib
import re
from urllib.parse import urlencode, quote

logger = logging.getLogger(__name__)

class DataSource(Enum):
    """Data source enumeration"""
    OAUTH_PROVIDER = "oauth_provider"
    SOCIAL_MEDIA = "social_media"
    PUBLIC_DATABASES = "public_databases"
    COMPANY_WEBSITES = "company_websites"
    PROFESSIONAL_NETWORKS = "professional_networks"
    NEWS_ARTICLES = "news_articles"
    GOVERNMENT_RECORDS = "government_records"
    UNKNOWN = "unknown"

class ProfileEnrichmentEngine:
    """Advanced profile enrichment and data aggregation engine"""
    
    def __init__(self):
        self.config = {
            "enable_social_media_enrichment": os.getenv("ENABLE_SOCIAL_MEDIA_ENRICHMENT", "true").lower() == "true",
            "enable_company_research": os.getenv("ENABLE_COMPANY_RESEARCH", "true").lower() == "true",
            "enable_professional_network_analysis": os.getenv("ENABLE_PROFESSIONAL_NETWORK_ANALYSIS", "true").lower() == "true",
            "enable_news_analysis": os.getenv("ENABLE_NEWS_ANALYSIS", "true").lower() == "true",
            "enable_public_record_search": os.getenv("ENABLE_PUBLIC_RECORD_SEARCH", "true").lower() == "true",
            "enrichment_timeout": int(os.getenv("ENRICHMENT_TIMEOUT", "60")),
            "max_data_sources": int(os.getenv("MAX_DATA_SOURCES", "10")),
            "cache_enrichment_results": os.getenv("CACHE_ENRICHMENT_RESULTS", "true").lower() == "true",
            "cache_duration": int(os.getenv("ENRICHMENT_CACHE_DURATION", "7200"))  # 2 hours
        }
        
        # API keys for external services
        self.api_keys = self._load_api_keys()
        
        # Data source configurations
        self.data_sources = self._load_data_sources()
        
        # Enrichment cache
        self.enrichment_cache = {}
        
        logger.info("Profile enrichment engine initialized")
    
    async def enrich_profile(self, email: str, user_info: Dict[str, Any] = None, 
                           additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Enrich profile with additional data from multiple sources
        
        Args:
            email: Email address
            user_info: Basic user information from OAuth
            additional_data: Additional data to enrich
            
        Returns:
            Enriched profile data
        """
        try:
            # Generate enrichment ID
            enrichment_id = f"enrich_{int(time.time())}"
            
            # Check cache first
            if self.config["cache_enrichment_results"]:
                cached_result = self._get_cached_enrichment(email)
                if cached_result:
                    return cached_result
            
            # Initialize enrichment result
            enrichment_result = {
                "enrichment_id": enrichment_id,
                "email": email,
                "enriched_data": {},
                "data_sources": [],
                "completeness_score": 0.0,
                "confidence_score": 0.0,
                "social_profiles": {},
                "contact_info": {},
                "professional_info": {},
                "company_info": {},
                "news_mentions": [],
                "public_records": [],
                "errors": [],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Start with basic user info
            if user_info:
                enrichment_result["enriched_data"].update(user_info)
                enrichment_result["data_sources"].append(DataSource.OAUTH_PROVIDER.value)
            
            # Add additional data
            if additional_data:
                enrichment_result["enriched_data"].update(additional_data)
            
            # Extract domain for company research
            domain = None
            if "@" in email:
                domain = email.split("@")[1]
            
            # Run enrichment tasks concurrently
            enrichment_tasks = []
            
            # Social media enrichment
            if self.config["enable_social_media_enrichment"]:
                task = self._enrich_social_media(email, user_info)
                enrichment_tasks.append(task)
            
            # Company research
            if self.config["enable_company_research"] and domain:
                task = self._enrich_company_info(domain, email)
                enrichment_tasks.append(task)
            
            # Professional network analysis
            if self.config["enable_professional_network_analysis"]:
                task = self._enrich_professional_network(email, user_info)
                enrichment_tasks.append(task)
            
            # News analysis
            if self.config["enable_news_analysis"]:
                task = self._enrich_news_mentions(email, user_info)
                enrichment_tasks.append(task)
            
            # Public record search
            if self.config["enable_public_record_search"]:
                task = self._enrich_public_records(email, user_info)
                enrichment_tasks.append(task)
            
            # Execute all enrichment tasks
            if enrichment_tasks:
                results = await asyncio.gather(*enrichment_tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, Exception):
                        enrichment_result["errors"].append(str(result))
                    else:
                        self._merge_enrichment_result(enrichment_result, result)
            
            # Calculate scores
            enrichment_result["completeness_score"] = self._calculate_completeness_score(enrichment_result)
            enrichment_result["confidence_score"] = self._calculate_confidence_score(enrichment_result)
            
            # Cache result
            if self.config["cache_enrichment_results"]:
                self._cache_enrichment_result(email, enrichment_result)
            
            logger.info(f"Profile enrichment completed: {email} - {enrichment_result['completeness_score']:.2f}")
            return enrichment_result
            
        except Exception as e:
            logger.error(f"Error enriching profile: {e}")
            return {
                "enrichment_id": enrichment_id if 'enrichment_id' in locals() else None,
                "email": email,
                "error": str(e),
                "completeness_score": 0.0,
                "confidence_score": 0.0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def _enrich_social_media(self, email: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich profile with social media data"""
        try:
            result = {
                "social_profiles": {},
                "data_sources": [DataSource.SOCIAL_MEDIA.value],
                "confidence_score": 0.0
            }
            
            # Extract name for social media search
            name = user_info.get("name") or user_info.get("given_name", "") + " " + user_info.get("family_name", "")
            name = name.strip()
            
            if not name:
                return result
            
            # Search for social media profiles
            social_platforms = ["linkedin", "twitter", "facebook", "instagram", "github"]
            
            for platform in social_platforms:
                try:
                    profile_data = await self._search_social_platform(platform, name, email)
                    if profile_data:
                        result["social_profiles"][platform] = profile_data
                        result["confidence_score"] += 0.1
                except Exception as e:
                    logger.error(f"Error searching {platform}: {e}")
                    continue
            
            return result
            
        except Exception as e:
            logger.error(f"Error enriching social media: {e}")
            return {"data_sources": [DataSource.SOCIAL_MEDIA.value], "error": str(e)}
    
    async def _search_social_platform(self, platform: str, name: str, email: str) -> Optional[Dict[str, Any]]:
        """Search for profile on specific social platform"""
        try:
            if platform == "linkedin":
                return await self._search_linkedin(name, email)
            elif platform == "twitter":
                return await self._search_twitter(name, email)
            elif platform == "github":
                return await self._search_github(name, email)
            else:
                # Generic social media search
                return await self._generic_social_search(platform, name, email)
                
        except Exception as e:
            logger.error(f"Error searching {platform}: {e}")
            return None
    
    async def _search_linkedin(self, name: str, email: str) -> Optional[Dict[str, Any]]:
        """Search LinkedIn profile"""
        try:
            # LinkedIn API requires special permissions
            # This is a simplified implementation
            return {
                "platform": "linkedin",
                "profile_url": f"https://linkedin.com/in/{name.lower().replace(' ', '-')}",
                "confidence": 0.3,
                "data_source": "estimated"
            }
            
        except Exception as e:
            logger.error(f"Error searching LinkedIn: {e}")
            return None
    
    async def _search_twitter(self, name: str, email: str) -> Optional[Dict[str, Any]]:
        """Search Twitter profile"""
        try:
            # Twitter API requires authentication
            # This is a simplified implementation
            return {
                "platform": "twitter",
                "profile_url": f"https://twitter.com/{name.lower().replace(' ', '')}",
                "confidence": 0.3,
                "data_source": "estimated"
            }
            
        except Exception as e:
            logger.error(f"Error searching Twitter: {e}")
            return None
    
    async def _search_github(self, name: str, email: str) -> Optional[Dict[str, Any]]:
        """Search GitHub profile"""
        try:
            # GitHub API allows limited unauthenticated access
            async with aiohttp.ClientSession() as session:
                # Search by email
                url = "https://api.github.com/search/users"
                params = {"q": email}
                
                async with session.get(url, params=params, timeout=self.config["enrichment_timeout"]) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get("total_count", 0) > 0:
                            user = data["items"][0]
                            return {
                                "platform": "github",
                                "username": user.get("login"),
                                "profile_url": user.get("html_url"),
                                "avatar_url": user.get("avatar_url"),
                                "public_repos": user.get("public_repos"),
                                "followers": user.get("followers"),
                                "confidence": 0.8,
                                "data_source": "api"
                            }
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching GitHub: {e}")
            return None
    
    async def _generic_social_search(self, platform: str, name: str, email: str) -> Optional[Dict[str, Any]]:
        """Generic social media search"""
        try:
            # This would integrate with social media search APIs
            return {
                "platform": platform,
                "profile_url": f"https://{platform}.com/{name.lower().replace(' ', '')}",
                "confidence": 0.2,
                "data_source": "estimated"
            }
            
        except Exception as e:
            logger.error(f"Error in generic social search: {e}")
            return None
    
    async def _enrich_company_info(self, domain: str, email: str) -> Dict[str, Any]:
        """Enrich profile with company information"""
        try:
            result = {
                "company_info": {},
                "data_sources": [DataSource.COMPANY_WEBSITES.value],
                "confidence_score": 0.0
            }
            
            # Company research using external APIs
            company_data = await self._research_company(domain)
            if company_data:
                result["company_info"] = company_data
                result["confidence_score"] = 0.7
            
            return result
            
        except Exception as e:
            logger.error(f"Error enriching company info: {e}")
            return {"data_sources": [DataSource.COMPANY_WEBSITES.value], "error": str(e)}
    
    async def _research_company(self, domain: str) -> Optional[Dict[str, Any]]:
        """Research company information"""
        try:
            # Use Clearbit API if available
            if self.api_keys.get("clearbit"):
                return await self._clearbit_company_lookup(domain)
            
            # Use Hunter.io API if available
            if self.api_keys.get("hunter"):
                return await self._hunter_company_lookup(domain)
            
            # Fallback to basic domain analysis
            return await self._basic_domain_analysis(domain)
            
        except Exception as e:
            logger.error(f"Error researching company: {e}")
            return None
    
    async def _clearbit_company_lookup(self, domain: str) -> Optional[Dict[str, Any]]:
        """Clearbit company lookup"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://company.clearbit.com/v2/companies/find?domain={quote(domain)}"
                headers = {"Authorization": f"Bearer {self.api_keys['clearbit']}"}
                
                async with session.get(url, headers=headers, timeout=self.config["enrichment_timeout"]) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        return {
                            "company_name": data.get("name"),
                            "industry": data.get("category", {}).get("industry"),
                            "company_size": data.get("metrics", {}).get("employees"),
                            "founded_year": data.get("foundedYear"),
                            "headquarters": data.get("location"),
                            "technologies": data.get("tech", []),
                            "revenue_range": data.get("metrics", {}).get("estimatedAnnualRevenue"),
                            "social_media": {
                                "twitter": data.get("twitter", {}).get("handle"),
                                "facebook": data.get("facebook", {}).get("handle"),
                                "linkedin": data.get("linkedin", {}).get("handle")
                            },
                            "data_source": "clearbit"
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error with Clearbit lookup: {e}")
            return None
    
    async def _hunter_company_lookup(self, domain: str) -> Optional[Dict[str, Any]]:
        """Hunter.io company lookup"""
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.hunter.io/v2/domain-search"
                params = {
                    "domain": domain,
                    "api_key": self.api_keys["hunter"],
                    "limit": 10
                }
                
                async with session.get(url, params=params, timeout=self.config["enrichment_timeout"]) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        emails = []
                        if data.get("data", {}).get("emails"):
                            for email_data in data["data"]["emails"]:
                                emails.append({
                                    "email": email_data.get("value"),
                                    "type": email_data.get("type"),
                                    "confidence": email_data.get("confidence")
                                })
                        
                        return {
                            "company_emails": emails,
                            "sources": data.get("data", {}).get("sources", []),
                            "data_source": "hunter"
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error with Hunter.io lookup: {e}")
            return None
    
    async def _basic_domain_analysis(self, domain: str) -> Dict[str, Any]:
        """Basic domain analysis"""
        try:
            return {
                "domain": domain,
                "domain_type": "corporate" if "." in domain else "unknown",
                "data_source": "domain_analysis"
            }
            
        except Exception as e:
            logger.error(f"Error in basic domain analysis: {e}")
            return {}
    
    async def _enrich_professional_network(self, email: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich profile with professional network data"""
        try:
            result = {
                "professional_info": {},
                "data_sources": [DataSource.PROFESSIONAL_NETWORKS.value],
                "confidence_score": 0.0
            }
            
            # Extract professional information
            name = user_info.get("name", "")
            company = user_info.get("company", "")
            job_title = user_info.get("job_title", "")
            
            if name:
                result["professional_info"]["name"] = name
                result["confidence_score"] += 0.3
            
            if company:
                result["professional_info"]["company"] = company
                result["confidence_score"] += 0.3
            
            if job_title:
                result["professional_info"]["job_title"] = job_title
                result["confidence_score"] += 0.2
            
            # Add contact information
            if email:
                result["contact_info"] = {
                    "email": email,
                    "email_verified": user_info.get("email_verified", False)
                }
                result["confidence_score"] += 0.2
            
            return result
            
        except Exception as e:
            logger.error(f"Error enriching professional network: {e}")
            return {"data_sources": [DataSource.PROFESSIONAL_NETWORKS.value], "error": str(e)}
    
    async def _enrich_news_mentions(self, email: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich profile with news mentions"""
        try:
            result = {
                "news_mentions": [],
                "data_sources": [DataSource.NEWS_ARTICLES.value],
                "confidence_score": 0.0
            }
            
            # Extract search terms
            name = user_info.get("name", "")
            company = user_info.get("company", "")
            
            search_terms = []
            if name:
                search_terms.append(name)
            if company:
                search_terms.append(company)
            
            # Search for news mentions
            for term in search_terms:
                try:
                    mentions = await self._search_news_mentions(term)
                    if mentions:
                        result["news_mentions"].extend(mentions)
                        result["confidence_score"] += 0.1
                except Exception as e:
                    logger.error(f"Error searching news for {term}: {e}")
                    continue
            
            return result
            
        except Exception as e:
            logger.error(f"Error enriching news mentions: {e}")
            return {"data_sources": [DataSource.NEWS_ARTICLES.value], "error": str(e)}
    
    async def _search_news_mentions(self, term: str) -> List[Dict[str, Any]]:
        """Search for news mentions"""
        try:
            # This would integrate with news APIs like NewsAPI, Google News, etc.
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Error searching news mentions: {e}")
            return []
    
    async def _enrich_public_records(self, email: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich profile with public records"""
        try:
            result = {
                "public_records": [],
                "data_sources": [DataSource.GOVERNMENT_RECORDS.value],
                "confidence_score": 0.0
            }
            
            # Extract search terms
            name = user_info.get("name", "")
            
            if name:
                try:
                    records = await self._search_public_records(name)
                    if records:
                        result["public_records"] = records
                        result["confidence_score"] = 0.5
                except Exception as e:
                    logger.error(f"Error searching public records: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error enriching public records: {e}")
            return {"data_sources": [DataSource.GOVERNMENT_RECORDS.value], "error": str(e)}
    
    async def _search_public_records(self, name: str) -> List[Dict[str, Any]]:
        """Search public records"""
        try:
            # This would integrate with public record APIs
            # For now, return empty list
            return []
            
        except Exception as e:
            logger.error(f"Error searching public records: {e}")
            return []
    
    def _merge_enrichment_result(self, main_result: Dict[str, Any], new_result: Dict[str, Any]):
        """Merge new enrichment result into main result"""
        try:
            # Merge data sources
            if "data_sources" in new_result:
                main_result["data_sources"].extend(new_result["data_sources"])
            
            # Merge social profiles
            if "social_profiles" in new_result:
                main_result["social_profiles"].update(new_result["social_profiles"])
            
            # Merge contact info
            if "contact_info" in new_result:
                main_result["contact_info"].update(new_result["contact_info"])
            
            # Merge professional info
            if "professional_info" in new_result:
                main_result["professional_info"].update(new_result["professional_info"])
            
            # Merge company info
            if "company_info" in new_result:
                main_result["company_info"].update(new_result["company_info"])
            
            # Merge news mentions
            if "news_mentions" in new_result:
                main_result["news_mentions"].extend(new_result["news_mentions"])
            
            # Merge public records
            if "public_records" in new_result:
                main_result["public_records"].extend(new_result["public_records"])
            
            # Merge errors
            if "errors" in new_result:
                main_result["errors"].extend(new_result["errors"])
            
            # Update enriched data
            if "enriched_data" in new_result:
                main_result["enriched_data"].update(new_result["enriched_data"])
            
        except Exception as e:
            logger.error(f"Error merging enrichment result: {e}")
    
    def _calculate_completeness_score(self, enrichment_result: Dict[str, Any]) -> float:
        """Calculate completeness score"""
        try:
            score = 0.0
            max_score = 10.0
            
            # Basic information
            if enrichment_result.get("enriched_data", {}).get("name"):
                score += 1.0
            if enrichment_result.get("enriched_data", {}).get("email"):
                score += 1.0
            
            # Social profiles
            social_profiles = enrichment_result.get("social_profiles", {})
            score += min(len(social_profiles) * 0.5, 2.0)
            
            # Contact information
            contact_info = enrichment_result.get("contact_info", {})
            if contact_info:
                score += 1.0
            
            # Professional information
            professional_info = enrichment_result.get("professional_info", {})
            if professional_info.get("company"):
                score += 1.0
            if professional_info.get("job_title"):
                score += 1.0
            
            # Company information
            company_info = enrichment_result.get("company_info", {})
            if company_info:
                score += 1.0
            
            # News mentions
            news_mentions = enrichment_result.get("news_mentions", [])
            if news_mentions:
                score += 1.0
            
            # Public records
            public_records = enrichment_result.get("public_records", [])
            if public_records:
                score += 1.0
            
            return min(1.0, score / max_score)
            
        except Exception as e:
            logger.error(f"Error calculating completeness score: {e}")
            return 0.0
    
    def _calculate_confidence_score(self, enrichment_result: Dict[str, Any]) -> float:
        """Calculate confidence score"""
        try:
            score = 0.0
            max_score = 10.0
            
            # Data sources
            data_sources = enrichment_result.get("data_sources", [])
            score += min(len(data_sources) * 0.5, 2.0)
            
            # Social profiles confidence
            social_profiles = enrichment_result.get("social_profiles", {})
            for platform, profile in social_profiles.items():
                if isinstance(profile, dict):
                    confidence = profile.get("confidence", 0.0)
                    score += confidence * 0.5
            
            # Company info confidence
            company_info = enrichment_result.get("company_info", {})
            if company_info.get("data_source") == "clearbit":
                score += 1.0
            elif company_info.get("data_source") == "hunter":
                score += 0.8
            elif company_info.get("data_source") == "domain_analysis":
                score += 0.3
            
            # Professional info confidence
            professional_info = enrichment_result.get("professional_info", {})
            if professional_info:
                score += 0.5
            
            # Contact info confidence
            contact_info = enrichment_result.get("contact_info", {})
            if contact_info.get("email_verified"):
                score += 1.0
            elif contact_info.get("email"):
                score += 0.5
            
            # News mentions confidence
            news_mentions = enrichment_result.get("news_mentions", [])
            if news_mentions:
                score += 0.5
            
            # Public records confidence
            public_records = enrichment_result.get("public_records", [])
            if public_records:
                score += 0.5
            
            return min(1.0, score / max_score)
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.0
    
    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys for external services"""
        return {
            "clearbit": os.getenv("CLEARBIT_API_KEY"),
            "hunter": os.getenv("HUNTER_API_KEY"),
            "newsapi": os.getenv("NEWS_API_KEY"),
            "linkedin": os.getenv("LINKEDIN_API_KEY"),
            "twitter": os.getenv("TWITTER_API_KEY")
        }
    
    def _load_data_sources(self) -> Dict[str, Dict[str, Any]]:
        """Load data source configurations"""
        return {
            "social_media": {
                "enabled": True,
                "platforms": ["linkedin", "twitter", "facebook", "instagram", "github"],
                "timeout": 30
            },
            "company_research": {
                "enabled": True,
                "apis": ["clearbit", "hunter"],
                "timeout": 30
            },
            "professional_networks": {
                "enabled": True,
                "platforms": ["linkedin"],
                "timeout": 30
            },
            "news_analysis": {
                "enabled": True,
                "apis": ["newsapi", "google_news"],
                "timeout": 30
            },
            "public_records": {
                "enabled": True,
                "sources": ["government", "court_records"],
                "timeout": 30
            }
        }
    
    def _get_cached_enrichment(self, email: str) -> Optional[Dict[str, Any]]:
        """Get cached enrichment result"""
        try:
            cache_key = hashlib.sha256(email.encode()).hexdigest()
            
            if cache_key in self.enrichment_cache:
                cached_result, cached_at = self.enrichment_cache[cache_key]
                
                # Check if cache is still valid
                cache_age = (datetime.now(timezone.utc) - cached_at).total_seconds()
                if cache_age < self.config["cache_duration"]:
                    return cached_result
                
                # Remove expired cache entry
                del self.enrichment_cache[cache_key]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached enrichment: {e}")
            return None
    
    def _cache_enrichment_result(self, email: str, result: Dict[str, Any]):
        """Cache enrichment result"""
        try:
            cache_key = hashlib.sha256(email.encode()).hexdigest()
            self.enrichment_cache[cache_key] = (result, datetime.now(timezone.utc))
            
            # Limit cache size
            if len(self.enrichment_cache) > 500:
                # Remove oldest entries
                oldest_keys = sorted(self.enrichment_cache.keys(),
                                   key=lambda k: self.enrichment_cache[k][1])[:100]
                for key in oldest_keys:
                    del self.enrichment_cache[key]
                    
        except Exception as e:
            logger.error(f"Error caching enrichment result: {e}")
    
    async def batch_enrich_profiles(self, profiles_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Batch enrich multiple profiles"""
        try:
            enrichment_tasks = []
            
            for profile_data in profiles_list:
                task = self.enrich_profile(
                    email=profile_data.get("email"),
                    user_info=profile_data.get("user_info", {}),
                    additional_data=profile_data.get("additional_data", {})
                )
                enrichment_tasks.append(task)
            
            # Execute all enrichments concurrently
            results = await asyncio.gather(*enrichment_tasks, return_exceptions=True)
            
            # Process results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append({
                        "error": str(result),
                        "profile_index": i,
                        "completeness_score": 0.0,
                        "confidence_score": 0.0
                    })
                else:
                    processed_results.append(result)
            
            logger.info(f"Batch profile enrichment completed: {len(processed_results)} profiles")
            return processed_results
            
        except Exception as e:
            logger.error(f"Error in batch profile enrichment: {e}")
            return []
    
    def get_enrichment_stats(self) -> Dict[str, Any]:
        """Get enrichment statistics"""
        try:
            return {
                "cache_size": len(self.enrichment_cache),
                "configuration": self.config,
                "data_sources": list(self.data_sources.keys()),
                "api_keys_available": {key: bool(value) for key, value in self.api_keys.items()},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting enrichment stats: {e}")
            return {"error": str(e)}