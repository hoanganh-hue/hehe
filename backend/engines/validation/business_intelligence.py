"""
Business Intelligence Engine
Analyze business accounts and extract valuable intelligence
"""

import os
import json
import re
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple, Set
import logging

# Import with error handling
try:
    import requests
except ImportError:
    requests = None

try:
    from urllib.parse import urlencode, quote
except ImportError:
    urlencode = None
    quote = None

try:
    import hashlib
except ImportError:
    hashlib = None

# Import circuit breaker with error handling
try:
    from services.circuit_breaker import get_clearbit_circuit_breaker, get_hunter_circuit_breaker
    CIRCUIT_BREAKER_AVAILABLE = True
except ImportError:
    CIRCUIT_BREAKER_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BusinessIntelligenceConfig:
    """Business intelligence configuration"""

    def __init__(self):
        self.max_analysis_time = int(os.getenv("MAX_ANALYSIS_TIME", "120"))
        self.enable_linkedin_analysis = os.getenv("ENABLE_LINKEDIN_ANALYSIS", "true").lower() == "true"
        self.enable_company_research = os.getenv("ENABLE_COMPANY_RESEARCH", "true").lower() == "true"
        self.enable_financial_analysis = os.getenv("ENABLE_FINANCIAL_ANALYSIS", "true").lower() == "true"
        self.min_company_size = int(os.getenv("MIN_COMPANY_SIZE", "10"))
        self.max_company_size = int(os.getenv("MAX_COMPANY_SIZE", "10000"))
        self.target_industries = os.getenv("TARGET_INDUSTRIES", "finance,healthcare,technology,government").split(",")
        self.enable_ml_scoring = os.getenv("ENABLE_ML_SCORING", "false").lower() == "true"

class BusinessAccount:
    """Business account data container"""

    def __init__(self, email: str = None, domain: str = None):
        self.email = email
        self.domain = domain
        self.analyzed_at = datetime.now(timezone.utc)

        # Company information
        self.company_name = None
        self.company_domain = None
        self.industry = None
        self.company_size = None
        self.founded_year = None
        self.headquarters = None

        # Financial information
        self.revenue_range = None
        self.funding_stage = None
        self.investors = []
        self.valuation = None

        # Leadership information
        self.ceo_name = None
        self.executives = []
        self.key_employees = []

        # Technology stack
        self.technologies = []
        self.email_provider = None
        self.security_features = []

        # Business metrics
        self.employee_count = None
        self.office_locations = []
        self.website_traffic = None
        self.social_media_presence = {}

        # Risk and value assessment
        self.business_value_score = 0.0
        self.risk_factors = []
        self.opportunity_score = 0.0
        self.market_position = None

        # Intelligence sources
        self.intelligence_sources = []
        self.confidence_level = 0.0

    def calculate_business_value(self) -> float:
        """Calculate business value score"""
        try:
            score = 0.0
            factors = 0

            # Company size factor
            if self.employee_count:
                factors += 1
                if self.employee_count >= 100:
                    score += 0.3
                elif self.employee_count >= 50:
                    score += 0.2
                elif self.employee_count >= 10:
                    score += 0.1

            # Industry factor
            if self.industry:
                factors += 1
                high_value_industries = ["finance", "healthcare", "technology", "legal", "insurance"]
                if any(industry in self.industry.lower() for industry in high_value_industries):
                    score += 0.3
                else:
                    score += 0.1

            # Revenue factor
            if self.revenue_range:
                factors += 1
                revenue_indicators = {
                    "1B+": 0.5,
                    "100M-1B": 0.4,
                    "10M-100M": 0.3,
                    "1M-10M": 0.2,
                    "100K-1M": 0.1
                }
                for indicator, value in revenue_indicators.items():
                    if indicator in self.revenue_range:
                        score += value
                        break

            # Technology sophistication
            if len(self.technologies) > 5:
                factors += 1
                score += 0.2

            # Security features
            security_features = len(self.security_features)
            if security_features > 3:
                factors += 1
                score += 0.1

            # Social media presence
            social_presence = len(self.social_media_presence)
            if social_presence > 2:
                factors += 1
                score += 0.1

            # Normalize score
            if factors > 0:
                self.business_value_score = min(1.0, score)
            else:
                self.business_value_score = 0.0

            return self.business_value_score

        except Exception as e:
            logger.error(f"Error calculating business value: {e}")
            self.business_value_score = 0.0
            return 0.0

    def assess_risks(self) -> List[str]:
        """Assess business risks"""
        risks = []

        try:
            # Small company risk
            if self.employee_count and self.employee_count < 10:
                risks.append("Small company - limited resources")

            # Startup risk
            if self.funding_stage and "seed" in self.funding_stage.lower():
                risks.append("Early-stage startup - high failure risk")

            # Industry-specific risks
            if self.industry:
                industry_risks = {
                    "finance": "Highly regulated industry",
                    "healthcare": "HIPAA compliance requirements",
                    "government": "Security clearance requirements",
                    "legal": "Attorney-client privilege concerns"
                }
                for industry, risk in industry_risks.items():
                    if industry in self.industry.lower():
                        risks.append(risk)

            # Technology risks
            if len(self.technologies) < 3:
                risks.append("Limited technology adoption")

            # Security risks
            if len(self.security_features) < 2:
                risks.append("Minimal security measures")

            self.risk_factors = risks
            return risks

        except Exception as e:
            logger.error(f"Error assessing risks: {e}")
            return []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "email": self.email,
            "domain": self.domain,
            "analyzed_at": self.analyzed_at.isoformat(),
            "company_name": self.company_name,
            "company_domain": self.company_domain,
            "industry": self.industry,
            "company_size": self.company_size,
            "founded_year": self.founded_year,
            "headquarters": self.headquarters,
            "revenue_range": self.revenue_range,
            "funding_stage": self.funding_stage,
            "investors": self.investors,
            "valuation": self.valuation,
            "ceo_name": self.ceo_name,
            "executives": self.executives,
            "key_employees": self.key_employees,
            "technologies": self.technologies,
            "email_provider": self.email_provider,
            "security_features": self.security_features,
            "employee_count": self.employee_count,
            "office_locations": self.office_locations,
            "website_traffic": self.website_traffic,
            "social_media_presence": self.social_media_presence,
            "business_value_score": self.business_value_score,
            "risk_factors": self.risk_factors,
            "opportunity_score": self.opportunity_score,
            "market_position": self.market_position,
            "intelligence_sources": self.intelligence_sources,
            "confidence_level": self.confidence_level
        }

class CompanyResearcher:
    """Company research and intelligence gathering"""

    def __init__(self):
        self.api_keys = self._load_api_keys()

    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys for research services"""
        return {
            "clearbit": os.getenv("CLEARBIT_API_KEY"),
            "hunter": os.getenv("HUNTER_API_KEY"),
            "linkedin": os.getenv("LINKEDIN_API_KEY"),
            "crunchbase": os.getenv("CRUNCHBASE_API_KEY")
        }

    def research_company(self, domain: str, email: str = None) -> Dict[str, Any]:
        """Research company information"""
        company_data = {}

        try:
            # Clearbit company lookup
            if self.api_keys.get("clearbit"):
                clearbit_data = self._clearbit_company_lookup(domain)
                if clearbit_data:
                    company_data.update(clearbit_data)

            # Hunter.io domain search
            if self.api_keys.get("hunter"):
                hunter_data = self._hunter_domain_search(domain)
                if hunter_data:
                    company_data.update(hunter_data)

            # Crunchbase lookup (if available)
            if self.api_keys.get("crunchbase"):
                crunchbase_data = self._crunchbase_lookup(domain)
                if crunchbase_data:
                    company_data.update(crunchbase_data)

            return company_data

        except Exception as e:
            logger.error(f"Error researching company: {e}")
            return {}

    def _clearbit_company_lookup(self, domain: str) -> Optional[Dict[str, Any]]:
        """Clearbit company lookup"""
        try:
            api_key = self.api_keys["clearbit"]
            if not api_key:
                return None

            # Clearbit API for company data
            url = f"https://company.clearbit.com/v2/companies/find?domain={quote(domain)}"
            headers = {"Authorization": f"Bearer {api_key}"}

            if not requests:
                logger.error("Requests library not available")
                return None

            def _make_clearbit_request():
                return requests.get(url, headers=headers, timeout=10)

            try:
                if CIRCUIT_BREAKER_AVAILABLE:
                    response = _make_clearbit_request()
                else:
                    response = _make_clearbit_request()
            except Exception as e:
                logger.error(f"Clearbit API request failed: {e}")
                return None

            if response.status_code == 200:
                data = response.json()

                return {
                    "company_name": data.get("name"),
                    "industry": data.get("category", {}).get("industry"),
                    "company_size": data.get("metrics", {}).get("employees"),
                    "founded_year": data.get("foundedYear"),
                    "headquarters": data.get("location"),
                    "technologies": data.get("tech", []),
                    "revenue_range": data.get("metrics", {}).get("estimatedAnnualRevenue"),
                    "social_media_presence": {
                        "twitter": data.get("twitter", {}).get("handle"),
                        "facebook": data.get("facebook", {}).get("handle"),
                        "linkedin": data.get("linkedin", {}).get("handle")
                    }
                }

            return None

        except Exception as e:
            logger.error(f"Error with Clearbit lookup: {e}")
            return None

    def _hunter_domain_search(self, domain: str) -> Optional[Dict[str, Any]]:
        """Hunter.io domain search"""
        try:
            api_key = self.api_keys["hunter"]
            if not api_key:
                return None

            # Hunter.io domain search API
            url = "https://api.hunter.io/v2/domain-search"
            params = {
                "domain": domain,
                "api_key": api_key,
                "limit": 10
            }

            if not requests:
                logger.error("Requests library not available")
                return None

            def _make_hunter_request():
                return requests.get(url, params=params, timeout=10)

            try:
                if CIRCUIT_BREAKER_AVAILABLE:
                    response = _make_hunter_request()
                else:
                    response = _make_hunter_request()
            except Exception as e:
                logger.error(f"Hunter.io API request failed: {e}")
                return None

            if response.status_code == 200:
                data = response.json()

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
                    "sources": data.get("data", {}).get("sources", [])
                }

            return None

        except Exception as e:
            logger.error(f"Error with Hunter.io domain search: {e}")
            return None

    def _crunchbase_lookup(self, domain: str) -> Optional[Dict[str, Any]]:
        """Crunchbase company lookup"""
        try:
            # Import Crunchbase client with error handling
            try:
                from services.crunchbase_api import get_crunchbase_client
                CRUNCHBASE_CLIENT_AVAILABLE = True
            except ImportError:
                CRUNCHBASE_CLIENT_AVAILABLE = False

            if not CRUNCHBASE_CLIENT_AVAILABLE:
                logger.warning("Crunchbase client not available")
                return None

            # Get Crunchbase client
            crunchbase_client = get_crunchbase_client()

            if not crunchbase_client.is_configured():
                logger.warning("Crunchbase client not configured")
                return None

            # Search for organizations
            organizations = crunchbase_client.search_organizations(domain, limit=5)

            if not organizations:
                logger.info(f"No Crunchbase organizations found for domain: {domain}")
                return None

            # Use the first/best match
            best_match = organizations[0]

            # Get detailed information if available
            if best_match.get("crunchbase_id"):
                try:
                    details = crunchbase_client.get_organization_details(best_match["crunchbase_id"])
                    if details:
                        best_match.update(details)

                    # Get funding information
                    funding = crunchbase_client.get_organization_funding(best_match["crunchbase_id"])
                    if funding:
                        best_match["funding_rounds"] = funding

                except Exception as e:
                    logger.warning(f"Error getting Crunchbase details: {e}")

            # Format for business intelligence
            company_data = {
                "company_name": best_match.get("name"),
                "industry": ", ".join(best_match.get("categories", [])) if best_match.get("categories") else None,
                "company_size": best_match.get("employee_count"),
                "founded_year": best_match.get("founded_year"),
                "headquarters": f"{best_match.get('city', '')}, {best_match.get('country', '')}".strip(", "),
                "revenue_range": None,  # Crunchbase doesn't provide direct revenue data
                "funding_stage": self._determine_funding_stage(best_match),
                "funding_total": best_match.get("funding_total"),
                "website": best_match.get("website"),
                "description": best_match.get("description") or best_match.get("short_description")
            }

            # Remove None values
            company_data = {k: v for k, v in company_data.items() if v is not None}

            logger.info(f"Crunchbase data retrieved for {domain}: {company_data.get('company_name', 'Unknown')}")
            return company_data

        except Exception as e:
            logger.error(f"Error with Crunchbase lookup: {e}")
            return None

    def _determine_funding_stage(self, org_data: Dict[str, Any]) -> Optional[str]:
        """Determine funding stage from Crunchbase data"""
        try:
            funding_total = org_data.get("funding_total", 0)
            funding_rounds = org_data.get("funding_rounds", [])

            if not funding_rounds:
                return None

            # Get the latest funding round
            latest_round = None
            latest_date = None

            for round_data in funding_rounds:
                announced_date = round_data.get("announced_date")
                if announced_date:
                    try:
                        round_date = datetime.fromisoformat(announced_date.replace('Z', '+00:00'))
                        if not latest_date or round_date > latest_date:
                            latest_date = round_date
                            latest_round = round_data
                    except (ValueError, AttributeError):
                        continue

            if latest_round:
                funding_type = latest_round.get("funding_type", "").lower()

                # Map funding types to stages
                if "ipo" in funding_type:
                    return "ipo"
                elif "series c" in funding_type or "series d" in funding_type:
                    return "late_stage"
                elif "series b" in funding_type:
                    return "growth_stage"
                elif "series a" in funding_type:
                    return "early_stage"
                elif "seed" in funding_type or "angel" in funding_type:
                    return "seed"
                elif "pre-seed" in funding_type:
                    return "pre_seed"
                else:
                    return "funded"

            # Fallback based on total funding
            if funding_total:
                if funding_total >= 100000000:  # $100M+
                    return "late_stage"
                elif funding_total >= 10000000:  # $10M+
                    return "growth_stage"
                elif funding_total >= 1000000:  # $1M+
                    return "early_stage"
                else:
                    return "seed"

            return None

        except Exception as e:
            logger.error(f"Error determining funding stage: {e}")
            return None

class EmailProviderAnalyzer:
    """Email provider analysis"""

    def __init__(self):
        self.provider_signatures = self._load_provider_signatures()

    def _load_provider_signatures(self) -> Dict[str, Dict[str, Any]]:
        """Load email provider signatures"""
        return {
            "google": {
                "domains": ["gmail.com", "googlemail.com"],
                "mx_records": ["aspmx.l.google.com"],
                "features": ["2fa", "recovery", "advanced_security"],
                "security_score": 0.9
            },
            "microsoft": {
                "domains": ["outlook.com", "hotmail.com", "live.com", "msn.com"],
                "mx_records": ["outlook-com.olc.protection.outlook.com"],
                "features": ["2fa", "advanced_security"],
                "security_score": 0.8
            },
            "apple": {
                "domains": ["icloud.com", "me.com", "mac.com"],
                "mx_records": ["mx01.mail.icloud.com"],
                "features": ["2fa", "icloud_keychain"],
                "security_score": 0.9
            },
            "yahoo": {
                "domains": ["yahoo.com", "yahoo.co.uk", "yahoo.ca"],
                "mx_records": ["mx-aol.mail.gm0.yahoodns.net"],
                "features": ["2fa"],
                "security_score": 0.6
            },
            "corporate": {
                "patterns": [r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"],
                "exclude_domains": ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"],
                "security_score": 0.7
            }
        }

    def analyze_email_provider(self, email: str) -> Dict[str, Any]:
        """Analyze email provider"""
        try:
            domain = email.split("@")[1].lower() if "@" in email else ""

            analysis = {
                "provider": "unknown",
                "provider_type": "unknown",
                "security_score": 0.5,
                "features": [],
                "is_corporate": False,
                "is_free_provider": True
            }

            # Check each provider
            for provider, config in self.provider_signatures.items():
                if provider == "corporate":
                    continue

                # Check domains
                if domain in config["domains"]:
                    analysis.update({
                        "provider": provider,
                        "provider_type": "free" if provider in ["google", "microsoft", "apple", "yahoo"] else "corporate",
                        "security_score": config["security_score"],
                        "features": config["features"],
                        "is_free_provider": provider in ["google", "microsoft", "apple", "yahoo"],
                        "is_corporate": False
                    })
                    return analysis

            # Check corporate pattern
            corporate_config = self.provider_signatures["corporate"]
            if (domain and
                not any(excluded in domain for excluded in corporate_config["exclude_domains"]) and
                re.match(corporate_config["patterns"][0], email)):
                analysis.update({
                    "provider": "corporate",
                    "provider_type": "corporate",
                    "security_score": corporate_config["security_score"],
                    "is_corporate": True,
                    "is_free_provider": False
                })

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing email provider: {e}")
            return {
                "provider": "unknown",
                "provider_type": "unknown",
                "security_score": 0.5,
                "features": [],
                "is_corporate": False,
                "is_free_provider": True
            }

class BusinessIntelligenceEngine:
    """Main business intelligence engine"""

    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client

        self.config = BusinessIntelligenceConfig()
        self.company_researcher = CompanyResearcher()
        self.email_analyzer = EmailProviderAnalyzer()

        # Analysis cache
        self.analysis_cache: Dict[str, Tuple[BusinessAccount, datetime]] = {}

    def analyze_business_account(self, email: str, domain: str = None,
                               additional_data: Dict[str, Any] = None) -> BusinessAccount:
        """
        Analyze business account

        Args:
            email: Email address
            domain: Company domain
            additional_data: Additional account data

        Returns:
            Business account analysis
        """
        try:
            # Extract domain from email if not provided
            if not domain and "@" in email:
                domain = email.split("@")[1]

            # Check cache
            cache_key = self._generate_cache_key(email, domain)
            cached_account = self._get_cached_analysis(cache_key)
            if cached_account:
                return cached_account

            # Create business account
            account = BusinessAccount(email, domain)

            # Populate with additional data
            if additional_data:
                self._populate_account_from_data(account, additional_data)

            # Analyze email provider
            email_analysis = self.email_analyzer.analyze_email_provider(email)
            account.email_provider = email_analysis["provider"]
            account.security_features = email_analysis["features"]

            # Research company
            if domain:
                company_data = self.company_researcher.research_company(domain, email)
                self._apply_company_data(account, company_data)

            # Calculate business value
            account.calculate_business_value()

            # Assess risks
            account.assess_risks()

            # Calculate opportunity score
            account.opportunity_score = self._calculate_opportunity_score(account)

            # Determine market position
            account.market_position = self._determine_market_position(account)

            # Calculate confidence level
            account.confidence_level = self._calculate_confidence_level(account)

            # Cache result
            self._cache_analysis(cache_key, account)

            # Store in database
            if self.mongodb:
                self._store_business_account(account)

            logger.info(f"Business account analyzed: {email}")
            return account

        except Exception as e:
            logger.error(f"Error analyzing business account: {e}")
            # Return basic account on error
            return BusinessAccount(email, domain)

    def _populate_account_from_data(self, account: BusinessAccount, data: Dict[str, Any]):
        """Populate account from additional data"""
        try:
            # Company info
            if "company_name" in data:
                account.company_name = data["company_name"]
            if "job_title" in data:
                account.job_title = data["job_title"]
            if "department" in data:
                account.department = data["department"]

            # Leadership info
            if "ceo_name" in data:
                account.ceo_name = data["ceo_name"]
            if "executives" in data:
                account.executives = data["executives"]

            # Financial info
            if "revenue" in data:
                account.revenue_range = data["revenue"]
            if "funding" in data:
                account.funding_stage = data["funding"]

        except Exception as e:
            logger.error(f"Error populating account from data: {e}")

    def _apply_company_data(self, account: BusinessAccount, company_data: Dict[str, Any]):
        """Apply company research data"""
        try:
            # Basic company info
            if "company_name" in company_data:
                account.company_name = company_data["company_name"]
            if "industry" in company_data:
                account.industry = company_data["industry"]
            if "company_size" in company_data:
                account.company_size = company_data["company_size"]
            if "founded_year" in company_data:
                account.founded_year = company_data["founded_year"]
            if "headquarters" in company_data:
                account.headquarters = company_data["headquarters"]

            # Financial data
            if "revenue_range" in company_data:
                account.revenue_range = company_data["revenue_range"]

            # Technology data
            if "technologies" in company_data:
                account.technologies = company_data["technologies"]

            # Social media
            if "social_media_presence" in company_data:
                account.social_media_presence.update(company_data["social_media_presence"])

            # Employee data
            if "company_emails" in company_data:
                for email_data in company_data["company_emails"]:
                    if email_data.get("type") in ["personal", "generic"]:
                        account.key_employees.append({
                            "email": email_data["email"],
                            "type": email_data["type"],
                            "confidence": email_data.get("confidence", 0)
                        })

            # Track intelligence source
            account.intelligence_sources.append("company_research")

        except Exception as e:
            logger.error(f"Error applying company data: {e}")

    def _calculate_opportunity_score(self, account: BusinessAccount) -> float:
        """Calculate opportunity score"""
        try:
            score = 0.0

            # Business value factor
            score += account.business_value_score * 0.4

            # Industry alignment
            if account.industry:
                target_industries = [ind.strip().lower() for ind in self.config.target_industries]
                if any(target in account.industry.lower() for target in target_industries):
                    score += 0.3

            # Company size factor
            if account.employee_count:
                if 50 <= account.employee_count <= 1000:
                    score += 0.2
                elif account.employee_count > 1000:
                    score += 0.1

            # Security sophistication
            security_multiplier = len(account.security_features) / 10.0
            score += min(security_multiplier, 0.1)

            return min(1.0, score)

        except Exception as e:
            logger.error(f"Error calculating opportunity score: {e}")
            return 0.0

    def _determine_market_position(self, account: BusinessAccount) -> str:
        """Determine market position"""
        try:
            if not account.employee_count or not account.revenue_range:
                return "unknown"

            # Simple market position classification
            if account.employee_count >= 1000:
                if account.revenue_range and "B" in account.revenue_range:
                    return "enterprise"
                else:
                    return "large_company"
            elif account.employee_count >= 100:
                return "mid_market"
            elif account.employee_count >= 10:
                return "small_business"
            else:
                return "startup"

        except Exception as e:
            logger.error(f"Error determining market position: {e}")
            return "unknown"

    def _calculate_confidence_level(self, account: BusinessAccount) -> float:
        """Calculate confidence level of analysis"""
        try:
            confidence = 0.0
            factors = 0

            # Email provider confidence
            if account.email_provider != "unknown":
                factors += 1
                confidence += 0.2

            # Company data confidence
            if account.company_name:
                factors += 1
                confidence += 0.3

            if account.industry:
                factors += 1
                confidence += 0.2

            if account.employee_count:
                factors += 1
                confidence += 0.2

            # Intelligence sources
            source_confidence = len(account.intelligence_sources) * 0.1
            confidence += min(source_confidence, 0.3)

            return min(1.0, confidence)

        except Exception as e:
            logger.error(f"Error calculating confidence level: {e}")
            return 0.0

    def _generate_cache_key(self, email: str, domain: str) -> str:
        """Generate cache key"""
        key_string = f"{email}:{domain or ''}"
        return hashlib.sha256(key_string.encode()).hexdigest()

    def _get_cached_analysis(self, cache_key: str) -> Optional[BusinessAccount]:
        """Get cached analysis"""
        try:
            if cache_key in self.analysis_cache:
                account, cached_at = self.analysis_cache[cache_key]

                # Check if cache is still valid (24 hours)
                cache_age = (datetime.now(timezone.utc) - cached_at).total_seconds()
                if cache_age < 86400:  # 24 hours
                    return account

                # Remove expired cache entry
                del self.analysis_cache[cache_key]

            return None

        except Exception as e:
            logger.error(f"Error getting cached analysis: {e}")
            return None

    def _cache_analysis(self, cache_key: str, account: BusinessAccount):
        """Cache analysis result"""
        try:
            self.analysis_cache[cache_key] = (account, datetime.now(timezone.utc))

            # Limit cache size
            if len(self.analysis_cache) > 2000:
                # Remove oldest entries
                oldest_keys = sorted(self.analysis_cache.keys(),
                                   key=lambda k: self.analysis_cache[k][1])[:500]
                for key in oldest_keys:
                    del self.analysis_cache[key]

        except Exception as e:
            logger.error(f"Error caching analysis: {e}")

    def _store_business_account(self, account: BusinessAccount):
        """Store business account in database"""
        try:
            if not self.mongodb:
                return

            db = self.mongodb.get_database("zalopay_phishing")
            accounts_collection = db.business_accounts

            document = account.to_dict()
            document["expires_at"] = datetime.now(timezone.utc) + timedelta(days=30)  # Keep for 30 days

            accounts_collection.replace_one(
                {"email": account.email},
                document,
                upsert=True
            )

        except Exception as e:
            logger.error(f"Error storing business account: {e}")

    def batch_analyze_accounts(self, accounts_data: List[Dict[str, Any]]) -> List[BusinessAccount]:
        """Batch analyze multiple business accounts"""
        analyzed_accounts = []

        for account_data in accounts_data:
            try:
                account = self.analyze_business_account(
                    email=account_data.get("email"),
                    domain=account_data.get("domain"),
                    additional_data=account_data.get("additional_data", {})
                )
                analyzed_accounts.append(account)

            except Exception as e:
                logger.error(f"Error in batch analysis: {e}")
                continue

        return analyzed_accounts

    def get_analysis_stats(self) -> Dict[str, Any]:
        """Get analysis statistics"""
        try:
            total_analyzed = len(self.analysis_cache)

            # Calculate averages
            avg_value_score = 0.0
            avg_opportunity_score = 0.0
            industry_distribution = {}
            provider_distribution = {}

            for account, _ in self.analysis_cache.values():
                # Average scores
                avg_value_score += account.business_value_score
                avg_opportunity_score += account.opportunity_score

                # Industry distribution
                if account.industry:
                    industry_distribution[account.industry] = industry_distribution.get(account.industry, 0) + 1

                # Provider distribution
                if account.email_provider:
                    provider_distribution[account.email_provider] = provider_distribution.get(account.email_provider, 0) + 1

            if total_analyzed > 0:
                avg_value_score /= total_analyzed
                avg_opportunity_score /= total_analyzed

            return {
                "total_analyzed": total_analyzed,
                "avg_business_value_score": avg_value_score,
                "avg_opportunity_score": avg_opportunity_score,
                "industry_distribution": industry_distribution,
                "provider_distribution": provider_distribution,
                "cache_size": len(self.analysis_cache),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting analysis stats: {e}")
            return {"error": "Failed to get statistics"}

# Global business intelligence engine instance
business_intelligence_engine = None

def initialize_business_intelligence(mongodb_connection=None, redis_client=None) -> BusinessIntelligenceEngine:
    """Initialize global business intelligence engine"""
    global business_intelligence_engine
    business_intelligence_engine = BusinessIntelligenceEngine(mongodb_connection, redis_client)
    return business_intelligence_engine

def get_business_intelligence_engine() -> BusinessIntelligenceEngine:
    """Get global business intelligence engine"""
    if business_intelligence_engine is None:
        raise ValueError("Business intelligence engine not initialized")
    return business_intelligence_engine

# Convenience functions
def analyze_business_account(email: str, domain: str = None, additional_data: Dict[str, Any] = None) -> BusinessAccount:
    """Analyze business account (global convenience function)"""
    return get_business_intelligence_engine().analyze_business_account(email, domain, additional_data)

def batch_analyze_accounts(accounts_data: List[Dict[str, Any]]) -> List[BusinessAccount]:
    """Batch analyze accounts (global convenience function)"""
    return get_business_intelligence_engine().batch_analyze_accounts(accounts_data)

def get_analysis_stats() -> Dict[str, Any]:
    """Get analysis stats (global convenience function)"""
    return get_business_intelligence_engine().get_analysis_stats()