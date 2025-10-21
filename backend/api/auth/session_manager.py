"""
Secure Session Management
Advanced session handling with security features
"""

import os
import secrets
import hashlib
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, Tuple, List
import logging
import json
import threading
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SessionSecurityConfig:
    """Session security configuration"""

    def __init__(self):
        self.session_timeout = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour
        self.extended_timeout = int(os.getenv("EXTENDED_SESSION_TIMEOUT", "7200"))  # 2 hours
        self.max_concurrent_sessions = int(os.getenv("MAX_CONCURRENT_SESSIONS", "5"))
        self.session_cleanup_interval = int(os.getenv("SESSION_CLEANUP_INTERVAL", "300"))  # 5 minutes
        self.enable_session_fixation_protection = os.getenv("ENABLE_SESSION_FIXATION_PROTECTION", "true").lower() == "true"
        self.enable_csrf_protection = os.getenv("ENABLE_CSRF_PROTECTION", "true").lower() == "true"
        self.enable_concurrent_session_control = os.getenv("ENABLE_CONCURRENT_SESSION_CONTROL", "true").lower() == "true"

class SessionData:
    """Session data container"""

    def __init__(self, session_id: str, user_id: str, username: str, role: str,
                 permissions: List[str], ip_address: str = None, user_agent: str = None):
        self.session_id = session_id
        self.user_id = user_id
        self.username = username
        self.role = role
        self.permissions = permissions or []
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.created_at = datetime.now(timezone.utc)
        self.last_accessed_at = datetime.now(timezone.utc)
        self.expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.get_timeout())
        self.is_extended = False
        self.csrf_token = secrets.token_hex(32) if self.is_csrf_enabled() else None
        self.fingerprint = self._generate_fingerprint()
        self.access_count = 0
        self.lock = threading.Lock()

    def get_timeout(self) -> int:
        """Get session timeout based on role"""
        if self.role in ["super_admin", "admin"]:
            return int(os.getenv("ADMIN_SESSION_TIMEOUT", "7200"))  # 2 hours for admins
        return int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour for others

    def is_csrf_enabled(self) -> bool:
        """Check if CSRF protection is enabled"""
        return os.getenv("ENABLE_CSRF_PROTECTION", "true").lower() == "true"

    def _generate_fingerprint(self) -> str:
        """Generate session fingerprint"""
        try:
            data = f"{self.user_id}:{self.ip_address}:{self.user_agent}:{self.created_at.timestamp()}"
            return hashlib.sha256(data.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Error generating session fingerprint: {e}")
            return secrets.token_hex(16)

    def update_access_time(self):
        """Update last accessed time"""
        with self.lock:
            self.last_accessed_at = datetime.now(timezone.utc)
            self.access_count += 1

    def extend_session(self, extend_time: int = None):
        """Extend session timeout"""
        with self.lock:
            if extend_time:
                self.expires_at = datetime.now(timezone.utc) + timedelta(seconds=extend_time)
            else:
                self.expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.get_timeout())
            self.is_extended = True

    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.now(timezone.utc) > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role,
            "permissions": self.permissions,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat(),
            "last_accessed_at": self.last_accessed_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "is_extended": self.is_extended,
            "csrf_token": self.csrf_token,
            "fingerprint": self.fingerprint,
            "access_count": self.access_count
        }

class SessionStore:
    """Session storage backend"""

    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.sessions: Dict[str, SessionData] = {}
        self.user_sessions: Dict[str, Set[str]] = defaultdict(set)
        self.lock = threading.Lock()

    def create_session(self, user_id: str, username: str, role: str,
                      permissions: List[str], ip_address: str = None,
                      user_agent: str = None) -> SessionData:
        """Create new session"""
        session_id = secrets.token_hex(32)

        session = SessionData(
            session_id=session_id,
            user_id=user_id,
            username=username,
            role=role,
            permissions=permissions,
            ip_address=ip_address,
            user_agent=user_agent
        )

        with self.lock:
            self.sessions[session_id] = session
            self.user_sessions[user_id].add(session_id)

        # Store in Redis if available
        if self.redis_client:
            self._save_to_redis(session)

        logger.info(f"Session created: {session_id} for user: {username}")
        return session

    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session by ID"""
        # Try Redis first
        if self.redis_client:
            session = self._load_from_redis(session_id)
            if session:
                return session

        # Fallback to memory
        with self.lock:
            session = self.sessions.get(session_id)

        if session:
            session.update_access_time()

            # Update in Redis if available
            if self.redis_client:
                self._save_to_redis(session)

        return session

    def update_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Update session data"""
        try:
            with self.lock:
                if session_id not in self.sessions:
                    return False

                session = self.sessions[session_id]

                # Update allowed fields
                for field in ["ip_address", "user_agent", "permissions"]:
                    if field in session_data:
                        setattr(session, field, session_data[field])

                session.update_access_time()

            # Update in Redis if available
            if self.redis_client:
                self._save_to_redis(session)

            return True

        except Exception as e:
            logger.error(f"Error updating session: {e}")
            return False

    def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        try:
            with self.lock:
                if session_id not in self.sessions:
                    return False

                session = self.sessions[session_id]

                # Remove from user sessions
                self.user_sessions[session.user_id].discard(session_id)

                # Remove session
                del self.sessions[session_id]

            # Delete from Redis if available
            if self.redis_client:
                self._delete_from_redis(session_id)

            logger.info(f"Session deleted: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False

    def delete_user_sessions(self, user_id: str, exclude_session_id: str = None) -> int:
        """Delete all sessions for a user"""
        deleted_count = 0

        try:
            with self.lock:
                user_session_ids = self.user_sessions.get(user_id, set()).copy()

                for session_id in user_session_ids:
                    if exclude_session_id and session_id == exclude_session_id:
                        continue

                    if self.delete_session(session_id):
                        deleted_count += 1

            logger.info(f"Deleted {deleted_count} sessions for user: {user_id}")
            return deleted_count

        except Exception as e:
            logger.error(f"Error deleting user sessions: {e}")
            return 0

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        expired_sessions = []

        try:
            with self.lock:
                current_time = datetime.now(timezone.utc)

                for session_id, session in self.sessions.items():
                    if session.is_expired():
                        expired_sessions.append(session_id)

                for session_id in expired_sessions:
                    self.delete_session(session_id)

            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
            return len(expired_sessions)

        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
            return 0

    def get_user_session_count(self, user_id: str) -> int:
        """Get number of active sessions for user"""
        with self.lock:
            return len(self.user_sessions.get(user_id, set()))

    def get_user_sessions(self, user_id: str) -> List[SessionData]:
        """Get all sessions for a user"""
        with self.lock:
            session_ids = self.user_sessions.get(user_id, set())
            return [self.sessions[sid] for sid in session_ids if sid in self.sessions]

    def _save_to_redis(self, session: SessionData):
        """Save session to Redis"""
        try:
            if not self.redis_client:
                return

            key = f"session:{session.session_id}"
            data = json.dumps(session.to_dict())

            # Set expiration
            ttl = int((session.expires_at - datetime.now(timezone.utc)).total_seconds())
            if ttl > 0:
                self.redis_client.setex(key, ttl, data)

        except Exception as e:
            logger.error(f"Error saving session to Redis: {e}")

    def _load_from_redis(self, session_id: str) -> Optional[SessionData]:
        """Load session from Redis"""
        try:
            if not self.redis_client:
                return None

            key = f"session:{session_id}"
            data = self.redis_client.get(key)

            if not data:
                return None

            session_dict = json.loads(data)
            session = SessionData(
                session_id=session_dict["session_id"],
                user_id=session_dict["user_id"],
                username=session_dict["username"],
                role=session_dict["role"],
                permissions=session_dict["permissions"],
                ip_address=session_dict.get("ip_address"),
                user_agent=session_dict.get("user_agent")
            )

            # Restore timestamps
            session.created_at = datetime.fromisoformat(session_dict["created_at"])
            session.last_accessed_at = datetime.fromisoformat(session_dict["last_accessed_at"])
            session.expires_at = datetime.fromisoformat(session_dict["expires_at"])
            session.is_extended = session_dict.get("is_extended", False)
            session.csrf_token = session_dict.get("csrf_token")
            session.fingerprint = session_dict.get("fingerprint")
            session.access_count = session_dict.get("access_count", 0)

            return session

        except Exception as e:
            logger.error(f"Error loading session from Redis: {e}")
            return None

    def _delete_from_redis(self, session_id: str):
        """Delete session from Redis"""
        try:
            if not self.redis_client:
                return

            key = f"session:{session_id}"
            self.redis_client.delete(key)

        except Exception as e:
            logger.error(f"Error deleting session from Redis: {e}")

class SessionSecurityManager:
    """Session security management"""

    def __init__(self, session_store: SessionStore, config: SessionSecurityConfig = None):
        self.session_store = session_store
        self.config = config or SessionSecurityConfig()
        self.cleanup_thread = None
        self._start_cleanup_thread()

    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        if self.cleanup_thread is None:
            self.cleanup_thread = threading.Thread(
                target=self._cleanup_loop,
                daemon=True
            )
            self.cleanup_thread.start()

    def _cleanup_loop(self):
        """Background cleanup loop"""
        while True:
            try:
                time.sleep(self.config.session_cleanup_interval)
                self.session_store.cleanup_expired_sessions()
            except Exception as e:
                logger.error(f"Error in session cleanup loop: {e}")

    def validate_session_request(self, session: SessionData, request_ip: str,
                              request_user_agent: str, request_fingerprint: str = None) -> Dict[str, Any]:
        """
        Validate session security requirements

        Args:
            session: Session to validate
            request_ip: Request IP address
            request_user_agent: Request user agent
            request_fingerprint: Request fingerprint

        Returns:
            Validation result
        """
        try:
            issues = []

            # Check IP address consistency
            if session.ip_address and session.ip_address != request_ip:
                issues.append("IP address mismatch")

            # Check user agent consistency
            if session.user_agent and session.user_agent != request_user_agent:
                issues.append("User agent mismatch")

            # Check fingerprint
            if request_fingerprint and session.fingerprint != request_fingerprint:
                issues.append("Fingerprint mismatch")

            # Check session fixation
            if self.config.enable_session_fixation_protection:
                fixation_issues = self._check_session_fixation(session)
                issues.extend(fixation_issues)

            if issues:
                logger.warning(f"Session security issues for {session.session_id}: {issues}")
                return {
                    "valid": False,
                    "issues": issues,
                    "requires_reauth": len(issues) > 1  # Require reauth for multiple issues
                }

            return {"valid": True}

        except Exception as e:
            logger.error(f"Error validating session security: {e}")
            return {"valid": False, "error": "Validation failed"}

    def _check_session_fixation(self, session: SessionData) -> List[str]:
        """Check for session fixation attacks"""
        issues = []

        try:
            # Check for suspicious access patterns
            if session.access_count > 100 and not session.is_extended:
                issues.append("High access count without extension")

            # Check for rapid successive requests
            time_since_creation = (datetime.now(timezone.utc) - session.created_at).total_seconds()
            if time_since_creation < 60 and session.access_count > 10:
                issues.append("Rapid successive requests")

        except Exception as e:
            logger.error(f"Error checking session fixation: {e}")

        return issues

class SessionManager:
    """Main session manager"""

    def __init__(self, redis_client=None):
        self.session_store = SessionStore(redis_client)
        self.security_manager = SessionSecurityManager(self.session_store)
        self.config = SessionSecurityConfig()

    def create_session(self, user_id: str, username: str, role: str,
                      permissions: List[str], ip_address: str = None,
                      user_agent: str = None) -> SessionData:
        """Create new session"""
        # Check concurrent session limit
        if self.config.enable_concurrent_session_control:
            current_sessions = self.session_store.get_user_session_count(user_id)

            if current_sessions >= self.config.max_concurrent_sessions:
                # Delete oldest session
                user_sessions = self.session_store.get_user_sessions(user_id)
                if user_sessions:
                    oldest_session = min(user_sessions, key=lambda s: s.created_at)
                    self.session_store.delete_session(oldest_session.session_id)

        return self.session_store.create_session(
            user_id, username, role, permissions, ip_address, user_agent
        )

    def get_session(self, session_id: str, request_ip: str = None,
                   request_user_agent: str = None, request_fingerprint: str = None) -> Optional[SessionData]:
        """Get and validate session"""
        session = self.session_store.get_session(session_id)

        if not session:
            return None

        # Validate session security
        if request_ip or request_user_agent or request_fingerprint:
            validation = self.security_manager.validate_session_request(
                session, request_ip or "", request_user_agent or "", request_fingerprint
            )

            if not validation["valid"]:
                logger.warning(f"Session validation failed for {session_id}")
                if validation.get("requires_reauth"):
                    self.destroy_session(session_id)
                return None

        return session

    def update_session(self, session_id: str, **kwargs) -> bool:
        """Update session"""
        return self.session_store.update_session(session_id, kwargs)

    def destroy_session(self, session_id: str) -> bool:
        """Destroy session"""
        return self.session_store.delete_session(session_id)

    def destroy_user_sessions(self, user_id: str, exclude_session_id: str = None) -> int:
        """Destroy all user sessions"""
        return self.session_store.delete_user_sessions(user_id, exclude_session_id)

    def extend_session(self, session_id: str, extend_time: int = None) -> bool:
        """Extend session timeout"""
        session = self.session_store.get_session(session_id)
        if session:
            session.extend_session(extend_time)
            return True
        return False

    def cleanup_sessions(self) -> int:
        """Clean up expired sessions"""
        return self.session_store.cleanup_expired_sessions()

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        session = self.session_store.get_session(session_id)
        return session.to_dict() if session else None

    def get_user_sessions_info(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all user sessions information"""
        sessions = self.session_store.get_user_sessions(user_id)
        return [session.to_dict() for session in sessions]

    def validate_csrf_token(self, session_id: str, token: str) -> bool:
        """Validate CSRF token"""
        if not self.config.enable_csrf_protection:
            return True

        session = self.session_store.get_session(session_id)
        if session and session.csrf_token:
            return hmac.compare_digest(session.csrf_token, token)

        return False

    def regenerate_csrf_token(self, session_id: str) -> Optional[str]:
        """Regenerate CSRF token"""
        session = self.session_store.get_session(session_id)
        if session:
            session.csrf_token = secrets.token_hex(32)
            return session.csrf_token
        return None

# Global session manager instance
session_manager = None

def initialize_session_manager(redis_client=None) -> SessionManager:
    """Initialize global session manager"""
    global session_manager
    session_manager = SessionManager(redis_client)
    return session_manager

def get_session_manager() -> SessionManager:
    """Get global session manager"""
    if session_manager is None:
        raise ValueError("Session manager not initialized")
    return session_manager

# Convenience functions
def create_session(user_id: str, username: str, role: str, permissions: List[str],
                  ip_address: str = None, user_agent: str = None) -> SessionData:
    """Create session (global convenience function)"""
    return get_session_manager().create_session(user_id, username, role, permissions, ip_address, user_agent)

def get_session(session_id: str, request_ip: str = None, request_user_agent: str = None,
               request_fingerprint: str = None) -> Optional[SessionData]:
    """Get session (global convenience function)"""
    return get_session_manager().get_session(session_id, request_ip, request_user_agent, request_fingerprint)

def destroy_session(session_id: str) -> bool:
    """Destroy session (global convenience function)"""
    return get_session_manager().destroy_session(session_id)

def validate_csrf_token(session_id: str, token: str) -> bool:
    """Validate CSRF token (global convenience function)"""
    return get_session_manager().validate_csrf_token(session_id, token)