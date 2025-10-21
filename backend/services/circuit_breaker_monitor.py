"""
Circuit Breaker Monitoring and Alerting
Monitors circuit breaker states and sends alerts when necessary
"""

import asyncio
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import json

from services.circuit_breaker import circuit_breaker_manager, CircuitBreakerState

logger = logging.getLogger(__name__)

class CircuitBreakerAlertConfig:
    """Alert configuration for circuit breakers"""

    def __init__(self):
        self.enable_alerts = True
        self.alert_channels = ["log"]  # log, webhook, email
        self.alert_on_state_change = True
        self.alert_on_failure_threshold = True
        self.failure_threshold_alert_percentage = 80  # Alert when 80% of threshold reached
        self.monitoring_interval = 30  # seconds
        self.webhook_url = None
        self.email_recipients = []

class CircuitBreakerMonitor:
    """Monitors circuit breaker states and sends alerts"""

    def __init__(self, alert_config: CircuitBreakerAlertConfig = None):
        self.alert_config = alert_config or CircuitBreakerAlertConfig()
        self.monitoring_task = None
        self.is_monitoring = False
        self.alert_history = []
        self.max_alert_history = 1000

        # Track state changes for alerting
        self.previous_states = {}

        logger.info("Circuit breaker monitor initialized")

    async def start_monitoring(self):
        """Start monitoring circuit breakers"""
        if self.is_monitoring:
            logger.warning("Circuit breaker monitoring already running")
            return

        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Circuit breaker monitoring started")

    async def stop_monitoring(self):
        """Stop monitoring circuit breakers"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("Circuit breaker monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                await self._check_circuit_breakers()
                await asyncio.sleep(self.alert_config.monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in circuit breaker monitoring loop: {e}")
                await asyncio.sleep(self.alert_config.monitoring_interval)

    async def _check_circuit_breakers(self):
        """Check all circuit breakers and send alerts if necessary"""
        try:
            all_states = circuit_breaker_manager.get_all_states()

            for name, state_info in all_states.items():
                current_state = state_info["state"]
                stats = state_info["stats"]

                # Check for state changes
                if self.alert_config.alert_on_state_change:
                    await self._check_state_change(name, current_state)

                # Check failure threshold alerts
                if self.alert_config.alert_on_failure_threshold:
                    await self._check_failure_threshold(name, state_info)

                # Update previous state tracking
                self.previous_states[name] = current_state

        except Exception as e:
            logger.error(f"Error checking circuit breakers: {e}")

    async def _check_state_change(self, name: str, current_state: str):
        """Check for state changes and send alerts"""
        try:
            previous_state = self.previous_states.get(name)

            if previous_state and previous_state != current_state:
                state_enum = CircuitBreakerState(current_state)

                # Alert on OPEN state
                if state_enum == CircuitBreakerState.OPEN:
                    await self._send_alert(
                        f"Circuit breaker '{name}' transitioned to OPEN state",
                        "error",
                        {
                            "circuit_breaker": name,
                            "previous_state": previous_state,
                            "current_state": current_state,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    )

                # Alert on recovery (CLOSED state)
                elif state_enum == CircuitBreakerState.CLOSED and previous_state == "open":
                    await self._send_alert(
                        f"Circuit breaker '{name}' recovered - transitioned to CLOSED state",
                        "info",
                        {
                            "circuit_breaker": name,
                            "previous_state": previous_state,
                            "current_state": current_state,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    )

        except Exception as e:
            logger.error(f"Error checking state change for {name}: {e}")

    async def _check_failure_threshold(self, name: str, state_info: Dict[str, Any]):
        """Check if failure threshold alerts should be sent"""
        try:
            stats = state_info["stats"]
            config = state_info["config"]

            failure_threshold = config["failure_threshold"]
            current_failures = stats["failure_count"]

            if failure_threshold > 0:
                failure_percentage = (current_failures / failure_threshold) * 100

                if failure_percentage >= self.alert_config.failure_threshold_alert_percentage:
                    # Check if we already sent an alert recently (within last hour)
                    if not self._should_send_threshold_alert(name):
                        await self._send_alert(
                            f"Circuit breaker '{name}' approaching failure threshold: {current_failures}/{failure_threshold} ({failure_percentage:.1f}%)",
                            "warning",
                            {
                                "circuit_breaker": name,
                                "current_failures": current_failures,
                                "failure_threshold": failure_threshold,
                                "failure_percentage": failure_percentage,
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }
                        )

        except Exception as e:
            logger.error(f"Error checking failure threshold for {name}: {e}")

    def _should_send_threshold_alert(self, name: str) -> bool:
        """Check if threshold alert should be sent (not too recent)"""
        try:
            current_time = datetime.now(timezone.utc)

            # Check last alert for this circuit breaker
            for alert in reversed(self.alert_history):
                if (alert["circuit_breaker"] == name and
                    alert["type"] == "threshold_warning" and
                    (current_time - datetime.fromisoformat(alert["timestamp"])).total_seconds() < 3600):  # 1 hour
                    return False

            return True

        except Exception as e:
            logger.error(f"Error checking threshold alert timing: {e}")
            return True

    async def _send_alert(self, message: str, level: str, data: Dict[str, Any]):
        """Send alert through configured channels"""
        try:
            alert_data = {
                "message": message,
                "level": level,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": data
            }

            # Log alert
            if "log" in self.alert_config.alert_channels:
                await self._send_log_alert(message, level, data)

            # Webhook alert
            if "webhook" in self.alert_config.alert_channels and self.alert_config.webhook_url:
                await self._send_webhook_alert(alert_data)

            # Email alert
            if "email" in self.alert_config.alert_channels and self.alert_config.email_recipients:
                await self._send_email_alert(message, level, data)

            # Store in history
            self.alert_history.append({
                "message": message,
                "level": level,
                "timestamp": alert_data["timestamp"],
                "circuit_breaker": data.get("circuit_breaker"),
                "type": "state_change" if "transitioned" in message else "threshold_warning"
            })

            # Limit history size
            if len(self.alert_history) > self.max_alert_history:
                self.alert_history = self.alert_history[-self.max_alert_history:]

            logger.info(f"Circuit breaker alert sent: {message}")

        except Exception as e:
            logger.error(f"Error sending circuit breaker alert: {e}")

    async def _send_log_alert(self, message: str, level: str, data: Dict[str, Any]):
        """Send alert to logging system"""
        try:
            if level == "error":
                logger.error(f"CIRCUIT_BREAKER_ALERT: {message}", extra={"alert_data": data})
            elif level == "warning":
                logger.warning(f"CIRCUIT_BREAKER_ALERT: {message}", extra={"alert_data": data})
            else:
                logger.info(f"CIRCUIT_BREAKER_ALERT: {message}", extra={"alert_data": data})

        except Exception as e:
            logger.error(f"Error sending log alert: {e}")

    async def _send_webhook_alert(self, alert_data: Dict[str, Any]):
        """Send alert to webhook"""
        try:
            import requests

            payload = {
                "embeds": [{
                    "title": "Circuit Breaker Alert",
                    "description": alert_data["message"],
                    "color": self._get_alert_color(alert_data["level"]),
                    "fields": [
                        {
                            "name": "Level",
                            "value": alert_data["level"].upper(),
                            "inline": True
                        },
                        {
                            "name": "Circuit Breaker",
                            "value": alert_data["data"].get("circuit_breaker", "Unknown"),
                            "inline": True
                        },
                        {
                            "name": "Timestamp",
                            "value": alert_data["timestamp"],
                            "inline": True
                        }
                    ],
                    "timestamp": alert_data["timestamp"]
                }]
            }

            response = requests.post(
                self.alert_config.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code != 204:
                logger.error(f"Webhook alert failed: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"Error sending webhook alert: {e}")

    async def _send_email_alert(self, message: str, level: str, data: Dict[str, Any]):
        """Send alert via email"""
        try:
            # This is a placeholder for email alerting
            # In production, integrate with your email service (SendGrid, SES, etc.)
            logger.info(f"Email alert would be sent: {message} to {self.alert_config.email_recipients}")

        except Exception as e:
            logger.error(f"Error sending email alert: {e}")

    def _get_alert_color(self, level: str) -> int:
        """Get Discord embed color for alert level"""
        colors = {
            "error": 15158332,    # Red
            "warning": 16776960,  # Yellow
            "info": 3447003       # Blue
        }
        return colors.get(level, 3447003)

    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        try:
            current_hour = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
            last_hour_alerts = [
                alert for alert in self.alert_history
                if datetime.fromisoformat(alert["timestamp"]) >= current_hour - timedelta(hours=1)
            ]

            return {
                "is_monitoring": self.is_monitoring,
                "total_alerts": len(self.alert_history),
                "alerts_last_hour": len(last_hour_alerts),
                "alert_channels": self.alert_config.alert_channels,
                "monitoring_interval": self.alert_config.monitoring_interval,
                "alert_history_size": len(self.alert_history),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting monitoring stats: {e}")
            return {"error": "Failed to get statistics"}

# Global circuit breaker monitor
circuit_breaker_monitor = None

def initialize_circuit_breaker_monitor(alert_config: CircuitBreakerAlertConfig = None) -> CircuitBreakerMonitor:
    """Initialize global circuit breaker monitor"""
    global circuit_breaker_monitor
    circuit_breaker_monitor = CircuitBreakerMonitor(alert_config)
    return circuit_breaker_monitor

def get_circuit_breaker_monitor() -> CircuitBreakerMonitor:
    """Get global circuit breaker monitor"""
    if circuit_breaker_monitor is None:
        raise ValueError("Circuit breaker monitor not initialized")
    return circuit_breaker_monitor

# Convenience functions
async def start_circuit_breaker_monitoring():
    """Start circuit breaker monitoring"""
    monitor = get_circuit_breaker_monitor()
    await monitor.start_monitoring()

async def stop_circuit_breaker_monitoring():
    """Stop circuit breaker monitoring"""
    monitor = get_circuit_breaker_monitor()
    await monitor.stop_monitoring()

def get_circuit_breaker_monitoring_stats() -> Dict[str, Any]:
    """Get circuit breaker monitoring statistics"""
    monitor = get_circuit_breaker_monitor()
    return monitor.get_monitoring_stats()