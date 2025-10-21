"""
Key Management System
Key rotation and management for encryption keys
"""

import os
import secrets
import json
import base64
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
import threading
import hashlib
import hmac
from dataclasses import dataclass, asdict
from enum import Enum
import schedule
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KeyStatus(Enum):
    """Key status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    COMPROMISED = "compromised"
    EXPIRED = "expired"
    ROTATED = "rotated"

class KeyType(Enum):
    """Key type enumeration"""
    MASTER_KEY = "master_key"
    AES_KEY = "aes_key"
    HMAC_KEY = "hmac_key"
    RSA_PRIVATE_KEY = "rsa_private_key"
    RSA_PUBLIC_KEY = "rsa_public_key"
    API_KEY = "api_key"
    JWT_SECRET = "jwt_secret"

@dataclass
class EncryptionKey:
    """Encryption key dataclass"""
    key_id: str
    key_type: KeyType
    key_data: str  # Base64 encoded
    status: KeyStatus
    created_at: datetime
    expires_at: Optional[datetime]
    last_used: Optional[datetime]
    use_count: int = 0
    algorithm: str = "AES-256-GCM"
    key_size: int = 256
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class KeyRotationManager:
    """Key rotation management"""

    def __init__(self, master_key: str = None):
        self.master_key = master_key or os.getenv("ENCRYPTION_MASTER_KEY")
        if not self.master_key:
            raise ValueError("Master key is required")

        # Key storage
        self.keys: Dict[str, EncryptionKey] = {}
        self.key_history: List[Dict[str, Any]] = []

        # Rotation settings
        self.rotation_intervals = {
            KeyType.AES_KEY: timedelta(days=90),      # 90 days
            KeyType.HMAC_KEY: timedelta(days=90),     # 90 days
            KeyType.RSA_PRIVATE_KEY: timedelta(days=365),  # 1 year
            KeyType.API_KEY: timedelta(days=180),     # 180 days
            KeyType.JWT_SECRET: timedelta(days=30)    # 30 days
        }

        # Lock for thread safety
        self.lock = threading.Lock()

        # Load existing keys
        self._load_keys()

        # Start rotation scheduler
        self._start_rotation_scheduler()

    def _load_keys(self):
        """Load existing keys from storage"""
        try:
            # In production, this would load from secure storage
            # For now, generate initial keys if none exist
            if not self._has_active_keys():
                self._generate_initial_keys()

        except Exception as e:
            logger.error(f"Error loading keys: {e}")
            raise

    def _has_active_keys(self) -> bool:
        """Check if active keys exist"""
        for key in self.keys.values():
            if key.status == KeyStatus.ACTIVE:
                return True
        return False

    def _generate_initial_keys(self):
        """Generate initial set of keys"""
        try:
            logger.info("Generating initial encryption keys...")

            # Generate AES key
            aes_key_data = secrets.token_bytes(32)  # 256 bits
            self._store_key(KeyType.AES_KEY, aes_key_data, "AES-256")

            # Generate HMAC key
            hmac_key_data = secrets.token_bytes(32)  # 256 bits
            self._store_key(KeyType.HMAC_KEY, hmac_key_data, "HMAC-SHA256")

            # Generate RSA key pair
            rsa_private_data = self._generate_rsa_keypair()
            self._store_key(KeyType.RSA_PRIVATE_KEY, rsa_private_data, "RSA-2048")

            # Generate API key
            api_key_data = secrets.token_urlsafe(32)
            self._store_key(KeyType.API_KEY, api_key_data.encode(), "API-KEY")

            # Generate JWT secret
            jwt_secret_data = secrets.token_urlsafe(64)
            self._store_key(KeyType.JWT_SECRET, jwt_secret_data.encode(), "JWT-HS256")

            logger.info("Initial keys generated successfully")

        except Exception as e:
            logger.error(f"Error generating initial keys: {e}")
            raise

    def _generate_rsa_keypair(self) -> bytes:
        """Generate RSA key pair"""
        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.backends import default_backend

            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )

            # Serialize private key to PEM format
            pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )

            return pem

        except Exception as e:
            logger.error(f"Error generating RSA key pair: {e}")
            raise

    def _store_key(self, key_type: KeyType, key_data: bytes, algorithm: str):
        """Store encryption key"""
        try:
            key_id = self._generate_key_id(key_type)

            # Calculate key size
            key_size = len(key_data) * 8  # Convert bytes to bits

            # Set expiration based on key type
            expires_at = datetime.now(timezone.utc) + self.rotation_intervals.get(key_type, timedelta(days=90))

            key = EncryptionKey(
                key_id=key_id,
                key_type=key_type,
                key_data=base64.b64encode(key_data).decode('utf-8'),
                status=KeyStatus.ACTIVE,
                created_at=datetime.now(timezone.utc),
                expires_at=expires_at,
                last_used=None,
                use_count=0,
                algorithm=algorithm,
                key_size=key_size
            )

            with self.lock:
                self.keys[key_id] = key

            logger.info(f"Key stored: {key_id} ({key_type.value})")

        except Exception as e:
            logger.error(f"Error storing key {key_type.value}: {e}")
            raise

    def _generate_key_id(self, key_type: KeyType) -> str:
        """Generate unique key ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = secrets.token_hex(4).upper()
        return f"{key_type.value.upper()}_{timestamp}_{random_suffix}"

    def get_active_key(self, key_type: KeyType) -> Optional[EncryptionKey]:
        """Get active key for specified type"""
        try:
            with self.lock:
                for key in self.keys.values():
                    if key.key_type == key_type and key.status == KeyStatus.ACTIVE:
                        # Check if key is expired
                        if key.expires_at and datetime.now(timezone.utc) > key.expires_at:
                            key.status = KeyStatus.EXPIRED
                            continue

                        return key

            return None

        except Exception as e:
            logger.error(f"Error getting active key for {key_type.value}: {e}")
            return None

    def get_key_data(self, key_type: KeyType) -> Optional[bytes]:
        """Get raw key data for specified type"""
        try:
            key = self.get_active_key(key_type)
            if key:
                # Update usage statistics
                self._update_key_usage(key.key_id)

                return base64.b64decode(key.key_data)
            else:
                logger.warning(f"No active key found for type: {key_type.value}")
                return None

        except Exception as e:
            logger.error(f"Error getting key data for {key_type.value}: {e}")
            return None

    def _update_key_usage(self, key_id: str):
        """Update key usage statistics"""
        try:
            with self.lock:
                if key_id in self.keys:
                    key = self.keys[key_id]
                    key.last_used = datetime.now(timezone.utc)
                    key.use_count += 1

        except Exception as e:
            logger.error(f"Error updating key usage for {key_id}: {e}")

    def rotate_key(self, key_type: KeyType, reason: str = "scheduled") -> bool:
        """
        Rotate key for specified type

        Args:
            key_type: Type of key to rotate
            reason: Reason for rotation

        Returns:
            bool: True if rotation successful
        """
        try:
            logger.info(f"Rotating key: {key_type.value} (reason: {reason})")

            # Get current active key
            current_key = self.get_active_key(key_type)
            if not current_key:
                logger.warning(f"No active key to rotate for type: {key_type.value}")
                return False

            # Generate new key
            if key_type == KeyType.AES_KEY:
                new_key_data = secrets.token_bytes(32)
                algorithm = "AES-256"
            elif key_type == KeyType.HMAC_KEY:
                new_key_data = secrets.token_bytes(32)
                algorithm = "HMAC-SHA256"
            elif key_type == KeyType.RSA_PRIVATE_KEY:
                new_key_data = self._generate_rsa_keypair()
                algorithm = "RSA-2048"
            elif key_type == KeyType.API_KEY:
                new_key_data = secrets.token_urlsafe(32).encode()
                algorithm = "API-KEY"
            elif key_type == KeyType.JWT_SECRET:
                new_key_data = secrets.token_urlsafe(64).encode()
                algorithm = "JWT-HS256"
            else:
                logger.error(f"Unsupported key type for rotation: {key_type.value}")
                return False

            # Store new key
            self._store_key(key_type, new_key_data, algorithm)

            # Mark old key as rotated
            with self.lock:
                current_key.status = KeyStatus.ROTATED
                current_key.metadata["rotation_reason"] = reason
                current_key.metadata["rotated_at"] = datetime.now(timezone.utc).isoformat()

            # Archive key history
            self._archive_key_history(current_key, reason)

            logger.info(f"Key rotated successfully: {key_type.value}")
            return True

        except Exception as e:
            logger.error(f"Error rotating key {key_type.value}: {e}")
            return False

    def _archive_key_history(self, key: EncryptionKey, reason: str):
        """Archive key to history"""
        try:
            key_history_entry = {
                "key_id": key.key_id,
                "key_type": key.key_type.value,
                "status": key.status.value,
                "created_at": key.created_at.isoformat(),
                "rotated_at": datetime.now(timezone.utc).isoformat(),
                "rotation_reason": reason,
                "use_count": key.use_count,
                "algorithm": key.algorithm,
                "key_size": key.key_size
            }

            self.key_history.append(key_history_entry)

            # Keep only last 100 entries in memory
            if len(self.key_history) > 100:
                self.key_history = self.key_history[-100:]

        except Exception as e:
            logger.error(f"Error archiving key history: {e}")

    def schedule_automatic_rotation(self):
        """Schedule automatic key rotation"""
        try:
            schedule.every(24).hours.do(self._check_and_rotate_keys)

            logger.info("Automatic key rotation scheduled")

        except Exception as e:
            logger.error(f"Error scheduling automatic rotation: {e}")

    def _check_and_rotate_keys(self):
        """Check and rotate expired keys"""
        try:
            logger.debug("Checking for keys that need rotation...")

            for key_type in self.rotation_intervals.keys():
                key = self.get_active_key(key_type)

                if key and key.expires_at:
                    if datetime.now(timezone.utc) >= key.expires_at:
                        logger.info(f"Auto-rotating expired key: {key_type.value}")
                        self.rotate_key(key_type, "automatic_expiry")

        except Exception as e:
            logger.error(f"Error in automatic key rotation check: {e}")

    def _start_rotation_scheduler(self):
        """Start background rotation scheduler"""
        def run_scheduler():
            while True:
                try:
                    schedule.run_pending()
                    time.sleep(3600)  # Check every hour
                except Exception as e:
                    logger.error(f"Error in rotation scheduler: {e}")
                    time.sleep(3600)

        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("Key rotation scheduler started")

    def get_key_info(self) -> Dict[str, Any]:
        """Get information about all keys"""
        try:
            with self.lock:
                keys_info = {}
                for key_id, key in self.keys.items():
                    keys_info[key_id] = {
                        "key_type": key.key_type.value,
                        "status": key.status.value,
                        "created_at": key.created_at.isoformat(),
                        "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                        "last_used": key.last_used.isoformat() if key.last_used else None,
                        "use_count": key.use_count,
                        "algorithm": key.algorithm,
                        "key_size": key.key_size,
                        "days_until_expiry": self._get_days_until_expiry(key)
                    }

                return {
                    "keys": keys_info,
                    "total_keys": len(self.keys),
                    "active_keys": len([k for k in self.keys.values() if k.status == KeyStatus.ACTIVE]),
                    "key_history_count": len(self.key_history)
                }

        except Exception as e:
            logger.error(f"Error getting key info: {e}")
            return {"error": str(e)}

    def _get_days_until_expiry(self, key: EncryptionKey) -> Optional[int]:
        """Get days until key expiry"""
        if not key.expires_at:
            return None

        remaining = key.expires_at - datetime.now(timezone.utc)
        return max(0, remaining.days)

    def revoke_key(self, key_id: str, reason: str = "manual") -> bool:
        """Revoke a key"""
        try:
            with self.lock:
                if key_id in self.keys:
                    key = self.keys[key_id]
                    key.status = KeyStatus.INACTIVE
                    key.metadata["revoked_at"] = datetime.now(timezone.utc).isoformat()
                    key.metadata["revoke_reason"] = reason

                    logger.info(f"Key revoked: {key_id} (reason: {reason})")
                    return True
                else:
                    logger.warning(f"Key not found for revocation: {key_id}")
                    return False

        except Exception as e:
            logger.error(f"Error revoking key {key_id}: {e}")
            return False

    def mark_key_compromised(self, key_id: str, reason: str = "security_incident") -> bool:
        """Mark key as compromised"""
        try:
            with self.lock:
                if key_id in self.keys:
                    key = self.keys[key_id]
                    key.status = KeyStatus.COMPROMISED
                    key.metadata["compromised_at"] = datetime.now(timezone.utc).isoformat()
                    key.metadata["compromise_reason"] = reason

                    # Immediately rotate the compromised key
                    self.rotate_key(key.key_type, f"compromised_key_{reason}")

                    logger.warning(f"Key marked as compromised: {key_id}")
                    return True
                else:
                    logger.warning(f"Key not found for compromise marking: {key_id}")
                    return False

        except Exception as e:
            logger.error(f"Error marking key as compromised {key_id}: {e}")
            return False

    def backup_keys(self, backup_path: str = None) -> str:
        """Backup all keys to secure location"""
        try:
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"./backups/key_backup_{timestamp}.json"

            # Create backup directory if it doesn't exist
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)

            # Prepare backup data
            backup_data = {
                "backup_timestamp": datetime.now(timezone.utc).isoformat(),
                "version": "1.0",
                "keys": {},
                "key_history": self.key_history
            }

            # Export all keys (excluding sensitive metadata)
            with self.lock:
                for key_id, key in self.keys.items():
                    backup_data["keys"][key_id] = {
                        "key_type": key.key_type.value,
                        "key_data": key.key_data,
                        "status": key.status.value,
                        "created_at": key.created_at.isoformat(),
                        "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                        "algorithm": key.algorithm,
                        "key_size": key.key_size,
                        "metadata": key.metadata
                    }

            # Encrypt backup
            from .encryption import initialize_encryption, encrypt_data

            # Initialize encryption with master key
            encryption_manager = initialize_encryption(self.master_key)

            # Encrypt backup data
            encrypted_backup = encryption_manager.encrypt(backup_data, "key_backup")

            # Save encrypted backup
            with open(backup_path, 'w') as f:
                json.dump(encrypted_backup, f, indent=2)

            logger.info(f"Keys backed up to: {backup_path}")
            return backup_path

        except Exception as e:
            logger.error(f"Error backing up keys: {e}")
            raise

    def restore_keys(self, backup_path: str) -> bool:
        """Restore keys from backup"""
        try:
            # Read encrypted backup
            with open(backup_path, 'r') as f:
                encrypted_backup = json.load(f)

            # Decrypt backup
            from .encryption import initialize_encryption, decrypt_data

            encryption_manager = initialize_encryption(self.master_key)
            backup_data = encryption_manager.decrypt(encrypted_backup)

            # Restore keys
            with self.lock:
                for key_id, key_data in backup_data["keys"].items():
                    key = EncryptionKey(
                        key_id=key_id,
                        key_type=KeyType(key_data["key_type"]),
                        key_data=key_data["key_data"],
                        status=KeyStatus(key_data["status"]),
                        created_at=datetime.fromisoformat(key_data["created_at"]),
                        expires_at=datetime.fromisoformat(key_data["expires_at"]) if key_data["expires_at"] else None,
                        algorithm=key_data["algorithm"],
                        key_size=key_data["key_size"],
                        metadata=key_data.get("metadata", {})
                    )

                    self.keys[key_id] = key

                # Restore key history
                self.key_history = backup_data["key_history"]

            logger.info(f"Keys restored from: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Error restoring keys from {backup_path}: {e}")
            return False

    def cleanup_expired_keys(self) -> int:
        """Clean up expired keys"""
        try:
            cleaned_count = 0

            with self.lock:
                keys_to_remove = []

                for key_id, key in self.keys.items():
                    if key.status in [KeyStatus.EXPIRED, KeyStatus.ROTATED]:
                        # Keep rotated keys for 30 days for decryption of old data
                        if key.status == KeyStatus.ROTATED:
                            days_since_rotation = (datetime.now(timezone.utc) - key.created_at).days
                            if days_since_rotation > 30:
                                keys_to_remove.append(key_id)
                        else:
                            keys_to_remove.append(key_id)

                # Remove expired keys
                for key_id in keys_to_remove:
                    del self.keys[key_id]
                    cleaned_count += 1

            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired keys")

            return cleaned_count

        except Exception as e:
            logger.error(f"Error cleaning up expired keys: {e}")
            return 0

    def get_rotation_schedule(self) -> Dict[str, Any]:
        """Get key rotation schedule"""
        try:
            schedule_info = {}

            for key_type, interval in self.rotation_intervals.items():
                key = self.get_active_key(key_type)

                if key and key.expires_at:
                    days_until_rotation = (key.expires_at - datetime.now(timezone.utc)).days
                    next_rotation = key.expires_at

                    schedule_info[key_type.value] = {
                        "interval_days": interval.days,
                        "next_rotation": next_rotation.isoformat(),
                        "days_until_rotation": max(0, days_until_rotation),
                        "current_key_id": key.key_id
                    }
                else:
                    schedule_info[key_type.value] = {
                        "interval_days": interval.days,
                        "next_rotation": "No active key",
                        "days_until_rotation": 0,
                        "current_key_id": None
                    }

            return schedule_info

        except Exception as e:
            logger.error(f"Error getting rotation schedule: {e}")
            return {"error": str(e)}

class KeySecurityMonitor:
    """Monitor key security and usage patterns"""

    def __init__(self, key_manager: KeyRotationManager):
        self.key_manager = key_manager
        self.security_events: List[Dict[str, Any]] = []
        self.lock = threading.Lock()

    def log_security_event(self, event_type: str, key_id: str, details: Dict[str, Any]):
        """Log security event"""
        try:
            event = {
                "event_type": event_type,
                "key_id": key_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": details
            }

            with self.lock:
                self.security_events.append(event)

                # Keep only last 1000 events
                if len(self.security_events) > 1000:
                    self.security_events = self.security_events[-1000:]

            logger.warning(f"Security event: {event_type} for key {key_id}")

        except Exception as e:
            logger.error(f"Error logging security event: {e}")

    def detect_anomalous_usage(self) -> List[Dict[str, Any]]:
        """Detect anomalous key usage patterns"""
        try:
            anomalies = []

            with self.key_manager.lock:
                for key_id, key in self.key_manager.keys.items():
                    if key.status == KeyStatus.ACTIVE:
                        # Check for unusual usage patterns
                        if key.use_count > 10000:  # Very high usage
                            anomalies.append({
                                "key_id": key_id,
                                "anomaly_type": "high_usage",
                                "details": f"Use count: {key.use_count}",
                                "severity": "medium"
                            })

                        # Check for old keys still in use
                        key_age = (datetime.now(timezone.utc) - key.created_at).days
                        if key_age > 60 and key.use_count > 100:
                            anomalies.append({
                                "key_id": key_id,
                                "anomaly_type": "old_key_high_usage",
                                "details": f"Key age: {key_age} days, Use count: {key.use_count}",
                                "severity": "high"
                            })

            return anomalies

        except Exception as e:
            logger.error(f"Error detecting anomalous usage: {e}")
            return []

# Global key manager instance
key_manager = None

def initialize_key_management(master_key: str = None) -> KeyRotationManager:
    """Initialize global key management"""
    global key_manager
    key_manager = KeyRotationManager(master_key)
    return key_manager

def get_key_manager() -> KeyRotationManager:
    """Get global key manager"""
    if key_manager is None:
        raise ValueError("Key manager not initialized")
    return key_manager

# Convenience functions
def get_encryption_key(key_type: KeyType) -> Optional[bytes]:
    """Get encryption key (convenience function)"""
    return get_key_manager().get_key_data(key_type)

def rotate_key(key_type: KeyType, reason: str = "manual") -> bool:
    """Rotate key (convenience function)"""
    return get_key_manager().rotate_key(key_type, reason)