"""
Crunchbase API Client
Real implementation for company and funding data retrieval
"""

import os
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple
import logging
import re

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

# Import circuit breaker with error handling
try:
    from services.circuit_breaker import get_crunchbase_circuit_breaker
    CIRCUIT_BREAKER_AVAILABLE = True
except ImportError:
    CIRCUIT_BREAKER_AVAILABLE = False

logger = logging.getLogger(__name__)

class CrunchbaseAPIConfig:
    """Crunchbase API configuration"""

    def __init__(self):
        self.api_key = os.getenv("CRUNCHBASE_API_KEY")
        self.base_url = "https://api.crunchbase.com/api/v4"
        self.timeout = 30
        self.max_retries = 3
        self.retry_delay = 1
        self.rate_limit_per_minute = 100  # Crunchbase free tier limit

        # Validate configuration
        self._validate_config()

    def _validate_config(self):
        """Validate Crunchbase API configuration"""
        if not self.api_key:
            logger.warning("Crunchbase API key not configured - Crunchbase features will be disabled")
            self.enabled = False
        else:
            self.enabled = True

class CrunchbaseAPIClient:
    """Crunchbase API client implementation"""

    def __init__(self):
        self.config = CrunchbaseAPIConfig()
        self.session = None
        self.last_request_time = None
        self.request_count = 0
        self.rate_limit_window_start = None

        if self.config.enabled and requests:
            self.session = requests.Session()
            self.session.headers.update({
                'Authorization': f'Bearer {self.config.api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'ZaloPay-Phishing-Platform/1.0'
            })

    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        try:
            current_time = datetime.now(timezone.utc)

            # Reset window if needed
            if (not self.rate_limit_window_start or
                (current_time - self.rate_limit_window_start).total_seconds() >= 60):
                self.request_count = 0
                self.rate_limit_window_start = current_time

            # Check if we're over the limit
            if self.request_count >= self.config.rate_limit_per_minute:
                logger.warning("Crunchbase API rate limit reached")
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return False

    def _wait_for_rate_limit(self):
        """Wait if rate limit is reached"""
        try:
            if self.rate_limit_window_start:
                time_since_window_start = (datetime.now(timezone.utc) - self.rate_limit_window_start).total_seconds()
                if time_since_window_start < 60:
                    wait_time = 60 - time_since_window_start
                    if wait_time > 0:
                        logger.info(f"Waiting {wait_time:.1f}s for Crunchbase rate limit reset")
                        time.sleep(wait_time)

        except Exception as e:
            logger.error(f"Error waiting for rate limit: {e}")

    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Make API request with error handling and rate limiting"""
        try:
            if not self.config.enabled or not self.session:
                logger.error("Crunchbase API not configured or requests not available")
                return None

            # Check rate limit before making request
            if not self._check_rate_limit():
                logger.warning("Crunchbase API rate limit reached, applying backoff")
                self._wait_for_rate_limit()
                if not self._check_rate_limit():
                    logger.error("Crunchbase API rate limit exceeded after waiting")
                    return None

            url = f"{self.config.base_url}{endpoint}"

            # Update request count and timing
            self.request_count += 1
            self.last_request_time = datetime.now(timezone.utc)

            def _execute_request():
                return self.session.get(url, params=params, timeout=self.config.timeout)

            response = None
            for attempt in range(self.config.max_retries):
                try:
                    # Execute request with circuit breaker protection
                    if CIRCUIT_BREAKER_AVAILABLE:
                        response = _execute_request()
                    else:
                        response = _execute_request()
                    break

                except requests.exceptions.Timeout:
                    if attempt < self.config.max_retries - 1:
                        wait_time = self.config.retry_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Crunchbase API timeout, retrying in {wait_time}s (attempt {attempt + 1}/{self.config.max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Crunchbase API request failed after {self.config.max_retries} attempts due to timeout")
                        return None

                except requests.exceptions.ConnectionError:
                    if attempt < self.config.max_retries - 1:
                        wait_time = self.config.retry_delay * (2 ** attempt)
                        logger.warning(f"Crunchbase API connection error, retrying in {wait_time}s (attempt {attempt + 1}/{self.config.max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Crunchbase API request failed after {self.config.max_retries} attempts due to connection error")
                        return None

                except requests.exceptions.RequestException as e:
                    logger.error(f"Crunchbase API request error: {e}")
                    return None

            if not response:
                logger.error("Crunchbase API request failed - no response")
                return None

            # Handle rate limiting (429)
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                wait_time = int(retry_after) if retry_after else 60
                logger.warning(f"Crunchbase API rate limit hit, waiting {wait_time}s")
                time.sleep(wait_time)
                return None

            # Handle server errors (5xx) with retry
            if 500 <= response.status_code < 600:
                logger.warning(f"Crunchbase API server error: {response.status_code}")
                return None

            # Handle client errors (4xx)
            if 400 <= response.status_code < 500 and response.status_code != 429:
                logger.error(f"Crunchbase API client error: {response.status_code} - {response.text}")
                return None

            # Handle successful response
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing Crunchbase API response JSON: {e}")
                    return None
            else:
                logger.error(f"Crunchbase API unexpected status code: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Unexpected error making Crunchbase API request: {e}")
            return None

    def search_organizations(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for organizations

        Args:
            query: Search query (company name, domain, etc.)
            limit: Maximum results to return

        Returns:
            List of organization data
        """
        try:
            if not query:
                return []

            # Clean and format query
            clean_query = query.strip().lower()

            # Try different search approaches
            results = []

            # 1. Search by name
            name_results = self._search_by_name(clean_query, limit)
            if name_results:
                results.extend(name_results)

            # 2. Search by domain if query looks like a domain
            if self._is_domain_like(clean_query):
                domain_results = self._search_by_domain(clean_query, limit)
                if domain_results:
                    results.extend(domain_results)

            # Remove duplicates and limit results
            seen_names = set()
            unique_results = []
            for result in results:
                name = result.get("name", "").lower()
                if name not in seen_names:
                    seen_names.add(name)
                    unique_results.append(result)
                    if len(unique_results) >= limit:
                        break

            logger.info(f"Crunchbase organization search for '{query}' returned {len(unique_results)} results")
            return unique_results

        except Exception as e:
            logger.error(f"Error searching Crunchbase organizations: {e}")
            return []

    def _search_by_name(self, name: str, limit: int) -> List[Dict[str, Any]]:
        """Search organizations by name"""
        try:
            # Use Crunchbase search API
            endpoint = "/searches/organizations"
            params = {
                "query": name,
                "limit": min(limit, 50),
                "field_ids": "identifier,name,short_description,website,city_name,country_code,funding_total,founded_on,employee_count"
            }

            data = self._make_request(endpoint, params)
            if not data or "entities" not in data:
                return []

            organizations = []
            for entity in data["entities"]:
                org_data = self._parse_organization_entity(entity)
                if org_data:
                    organizations.append(org_data)

            return organizations

        except Exception as e:
            logger.error(f"Error searching Crunchbase by name: {e}")
            return []

    def _search_by_domain(self, domain: str, limit: int) -> List[Dict[str, Any]]:
        """Search organizations by domain"""
        try:
            # Extract domain without protocol
            clean_domain = domain.replace("http://", "").replace("https://", "").split("/")[0]

            # Use Crunchbase search API with domain filter
            endpoint = "/searches/organizations"
            params = {
                "query": clean_domain,
                "limit": min(limit, 50),
                "field_ids": "identifier,name,short_description,website,city_name,country_code,funding_total,founded_on,employee_count"
            }

            data = self._make_request(endpoint, params)
            if not data or "entities" not in data:
                return []

            organizations = []
            for entity in data["entities"]:
                org_data = self._parse_organization_entity(entity)
                if org_data and self._matches_domain(org_data, clean_domain):
                    organizations.append(org_data)

            return organizations

        except Exception as e:
            logger.error(f"Error searching Crunchbase by domain: {e}")
            return []

    def _parse_organization_entity(self, entity: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse organization entity from Crunchbase API response"""
        try:
            properties = entity.get("properties", {})

            # Extract basic information
            identifier = entity.get("identifier", {}).get("value")
            if not identifier:
                return None

            org_data = {
                "crunchbase_id": identifier,
                "name": properties.get("name", ""),
                "short_description": properties.get("short_description", ""),
                "website": properties.get("website", {}).get("value", ""),
                "city": properties.get("city_name", ""),
                "country": properties.get("country_code", ""),
                "founded_year": None,
                "employee_count": None,
                "funding_total": None,
                "last_funding_date": None,
                "categories": [],
                "description": ""
            }

            # Parse founded date
            founded_on = properties.get("founded_on")
            if founded_on:
                try:
                    org_data["founded_year"] = int(founded_on.split("-")[0])
                except (ValueError, AttributeError):
                    pass

            # Parse employee count
            employee_count = properties.get("employee_count")
            if employee_count:
                try:
                    if isinstance(employee_count, str):
                        # Handle ranges like "100-500"
                        numbers = re.findall(r'\d+', employee_count)
                        if numbers:
                            org_data["employee_count"] = int(numbers[0])
                    else:
                        org_data["employee_count"] = int(employee_count)
                except (ValueError, TypeError):
                    pass

            # Parse funding information
            funding_total = properties.get("funding_total", {})
            if funding_total and "value_usd" in funding_total:
                org_data["funding_total"] = funding_total["value_usd"]

            return org_data

        except Exception as e:
            logger.error(f"Error parsing Crunchbase organization entity: {e}")
            return None

    def _matches_domain(self, org_data: Dict[str, Any], domain: str) -> bool:
        """Check if organization data matches the domain"""
        try:
            website = org_data.get("website", "").lower()
            clean_website = website.replace("http://", "").replace("https://", "").split("/")[0]

            # Exact match or subdomain match
            return clean_website == domain or clean_website.endswith(f".{domain}")

        except Exception as e:
            logger.error(f"Error matching domain: {e}")
            return False

    def _is_domain_like(self, query: str) -> bool:
        """Check if query looks like a domain"""
        try:
            # Simple domain pattern check
            domain_pattern = re.compile(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
            return bool(domain_pattern.match(query))

        except Exception as e:
            logger.error(f"Error checking domain pattern: {e}")
            return False

    def get_organization_details(self, organization_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about an organization

        Args:
            organization_id: Crunchbase organization identifier

        Returns:
            Detailed organization data or None
        """
        try:
            if not organization_id:
                return None

            endpoint = f"/entities/organizations/{quote(organization_id)}"
            params = {
                "field_ids": "identifier,name,short_description,description,website,city_name,country_code,funding_total,founded_on,employee_count,categories"
            }

            data = self._make_request(endpoint, params)
            if not data or "properties" not in data:
                return None

            # Parse detailed organization data
            properties = data["properties"]

            detailed_data = {
                "crunchbase_id": data.get("identifier", {}).get("value", ""),
                "name": properties.get("name", ""),
                "short_description": properties.get("short_description", ""),
                "description": properties.get("description", ""),
                "website": properties.get("website", {}).get("value", ""),
                "city": properties.get("city_name", ""),
                "country": properties.get("country_code", ""),
                "founded_year": None,
                "employee_count": None,
                "funding_total": None,
                "categories": []
            }

            # Parse founded date
            founded_on = properties.get("founded_on")
            if founded_on:
                try:
                    detailed_data["founded_year"] = int(founded_on.split("-")[0])
                except (ValueError, AttributeError):
                    pass

            # Parse employee count
            employee_count = properties.get("employee_count")
            if employee_count:
                try:
                    if isinstance(employee_count, str):
                        numbers = re.findall(r'\d+', employee_count)
                        if numbers:
                            detailed_data["employee_count"] = int(numbers[0])
                    else:
                        detailed_data["employee_count"] = int(employee_count)
                except (ValueError, TypeError):
                    pass

            # Parse funding information
            funding_total = properties.get("funding_total", {})
            if funding_total and "value_usd" in funding_total:
                detailed_data["funding_total"] = funding_total["value_usd"]

            # Parse categories
            categories = properties.get("categories", [])
            if categories:
                for category in categories:
                    category_name = category.get("value", "")
                    if category_name:
                        detailed_data["categories"].append(category_name)

            logger.info(f"Crunchbase organization details retrieved: {detailed_data['name']}")
            return detailed_data

        except Exception as e:
            logger.error(f"Error getting Crunchbase organization details: {e}")
            return None

    def get_organization_funding(self, organization_id: str) -> List[Dict[str, Any]]:
        """
        Get funding information for an organization

        Args:
            organization_id: Crunchbase organization identifier

        Returns:
            List of funding rounds or None
        """
        try:
            if not organization_id:
                return []

            endpoint = f"/entities/organizations/{quote(organization_id)}/funding_rounds"
            params = {
                "limit": 20,
                "field_ids": "announced_on,funding_type,money_raised_usd,investor_count"
            }

            data = self._make_request(endpoint, params)
            if not data or "entities" not in data:
                return []

            funding_rounds = []
            for entity in data["entities"]:
                properties = entity.get("properties", {})

                funding_data = {
                    "announced_date": properties.get("announced_on"),
                    "funding_type": properties.get("funding_type", {}).get("value"),
                    "amount_raised_usd": properties.get("money_raised_usd", {}).get("value_usd"),
                    "investor_count": properties.get("investor_count")
                }

                funding_rounds.append(funding_data)

            logger.info(f"Crunchbase funding data retrieved: {len(funding_rounds)} rounds")
            return funding_rounds

        except Exception as e:
            logger.error(f"Error getting Crunchbase funding data: {e}")
            return []

    def is_configured(self) -> bool:
        """Check if Crunchbase API is properly configured"""
        return self.config.enabled and self.session is not None

    def get_configuration_status(self) -> Dict[str, Any]:
        """Get Crunchbase API configuration status"""
        return {
            "enabled": self.config.enabled,
            "api_key_configured": bool(self.config.api_key),
            "base_url": self.config.base_url,
            "rate_limit_per_minute": self.config.rate_limit_per_minute,
            "request_count": self.request_count,
            "last_request_time": self.last_request_time.isoformat() if self.last_request_time else None
        }

# Global Crunchbase API client instance
crunchbase_client = None

def initialize_crunchbase_client() -> CrunchbaseAPIClient:
    """Initialize global Crunchbase API client"""
    global crunchbase_client
    crunchbase_client = CrunchbaseAPIClient()
    return crunchbase_client

def get_crunchbase_client() -> CrunchbaseAPIClient:
    """Get global Crunchbase API client"""
    if crunchbase_client is None:
        raise ValueError("Crunchbase client not initialized")
    return crunchbase_client

# Convenience functions
def search_crunchbase_organizations(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search Crunchbase organizations (global convenience function)"""
    return get_crunchbase_client().search_organizations(query, limit)

def get_crunchbase_organization_details(organization_id: str) -> Optional[Dict[str, Any]]:
    """Get Crunchbase organization details (global convenience function)"""
    return get_crunchbase_client().get_organization_details(organization_id)

def get_crunchbase_organization_funding(organization_id: str) -> List[Dict[str, Any]]:
    """Get Crunchbase organization funding (global convenience function)"""
    return get_crunchbase_client().get_organization_funding(organization_id)