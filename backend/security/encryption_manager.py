"""
Advanced Encryption Manager
Comprehensive encryption system with key rotation, secure token storage, and HSM integration
Updated: 2025-10-18
"""

import os
import json
import secrets
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
import logging
import hashlib
import hmac
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from argon2 import PasswordHasher
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.exceptions import InvalidSignature
import redis

# Lazy import for pymongo to handle OpenSSL compatibility issues
pymongo = None
def _import_pymongo():
    global pymongo
    if pymongo is None:
        try:
            import pymongo
        except Exception as e:
            logger.warning(f"Failed to import pymongo: {e}")
            pymongo = None
    return pymongo

logger = logging.getLogger(__name__)

class KeyRotationManager:
    """Advanced key rotation and management system"""
    
    def __init__(self, mongodb_connection=None, redis_client=None):
        self.mongodb = mongodb_connection
        self.redis = redis_client
        self.key_rotation_interval = int(os.getenv("KEY_ROTATION_INTERVAL", "86400"))  # 24 hours
        self.max_key_age = int(os.getenv("MAX_KEY_AGE", "604800"))  # 7 days
        self.key_rotation_active = False
        self.rotation_thread = None
        
    def start_key_rotation(self):
        """Start automatic key rotation"""
        if self.key_rotation_active:
            return
        
        self.key_rotation_active = True
        self.rotation_thread = threading.Thread(target=self._rotation_loop, daemon=True)
        self.rotation_thread.start()
        logger.info("Key rotation started")
    
    def stop_key_rotation(self):
        """Stop automatic key rotation"""
        self.key_rotation_active = False
        if self.rotation_thread:
            self.rotation_thread.join(timeout=5)
        logger.info("Key rotation stopped")
    
    def _rotation_loop(self):
        """Key rotation loop"""
        while self.key_rotation_active:
            try:
                time.sleep(self.key_rotation_interval)
                self._perform_key_rotation()
            except Exception as e:
                logger.error("Error in key rotation loop: %s", e)
                time.sleep(60)  # Wait before retrying
    
    def _perform_key_rotation(self):
        """Perform key rotation"""
        try:
            current_time = datetime.now(timezone.utc)
            
            # Check for keys that need rotation
            keys_to_rotate = self._get_keys_for_rotation()
            
            for key_id in keys_to_rotate:
                self._rotate_single_key(key_id)
            
            logger.info("Key rotation completed: %d keys rotated", len(keys_to_rotate))
            
        except Exception as e:
            logger.error("Error performing key rotation: %s", e)
    
    def _get_keys_for_rotation(self) -> List[str]:
        """Get keys that need rotation"""
        try:
            if not self.mongodb:
                return []

            pymongo_client = _import_pymongo()
            if not pymongo_client:
                return []

            db = self.mongodb.get_database("zalopay_phishing")
            keys_collection = db.encryption_keys

            # Find keys older than max_key_age
            cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=self.max_key_age)

            cursor = keys_collection.find({
                "created_at": {"$lt": cutoff_time.isoformat()},
                "status": "active"
            })

            return [doc["key_id"] for doc in cursor]
            
        except Exception as e:
            logger.error("Error getting keys for rotation: %s", e)
            return []
    
    def _rotate_single_key(self, key_id: str):
        """Rotate a single key"""
        try:
            # Generate new key
            new_key = self._generate_new_key(key_id)
            
            # Store new key
            self._store_key(new_key)
            
            # Mark old key as rotated
            self._mark_key_rotated(key_id, new_key["key_id"])
            
            logger.info("Key rotated: %s -> %s", key_id, new_key['key_id'])
            
        except Exception as e:
            logger.error("Error rotating key %s: %s", key_id, e)
    
    def _generate_new_key(self, old_key_id: str) -> Dict[str, Any]:
        """Generate new encryption key"""
        try:
            key_id = secrets.token_hex(16)
            key_material = secrets.token_bytes(32)  # 256-bit key
            
            return {
                "key_id": key_id,
                "key_material": base64.b64encode(key_material).decode('utf-8'),
                "algorithm": "AES-256-GCM",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "active",
                "rotated_from": old_key_id,
                "version": 1
            }
            
        except Exception as e:
            logger.error("Error generating new key: %s", e)
            raise
    
    def _store_key(self, key_data: Dict[str, Any]):
        """Store encryption key"""
        try:
            if not self.mongodb:
                return

            pymongo_client = _import_pymongo()
            if not pymongo_client:
                return

            db = self.mongodb.get_database("zalopay_phishing")
            keys_collection = db.encryption_keys

            keys_collection.insert_one(key_data)

            # Cache in Redis
            if self.redis:
                cache_key = f"encryption_key:{key_data['key_id']}"
                self.redis.setex(cache_key, 3600, json.dumps(key_data))

        except Exception as e:
            logger.error(f"Error storing key: {e}")
    
    def _mark_key_rotated(self, old_key_id: str, new_key_id: str):
        """Mark old key as rotated"""
        try:
            if not self.mongodb:
                return

            pymongo_client = _import_pymongo()
            if not pymongo_client:
                return

            db = self.mongodb.get_database("zalopay_phishing")
            keys_collection = db.encryption_keys

            keys_collection.update_one(
                {"key_id": old_key_id},
                {
                    "$set": {
                        "status": "rotated",
                        "rotated_at": datetime.now(timezone.utc).isoformat(),
                        "rotated_to": new_key_id
                    }
                }
            )

        except Exception as e:
            logger.error(f"Error marking key as rotated: {e}")

class SecureTokenStorage:
    """Secure token storage with encryption and access control"""
    
    def __init__(self, encryption_manager, mongodb_connection=None, redis_client=None):
        self.encryption_manager = encryption_manager
        self.mongodb = mongodb_connection
        self.redis = redis_client
        self.token_expiry_default = int(os.getenv("TOKEN_EXPIRY_DEFAULT", "3600"))  # 1 hour
        self.max_tokens_per_user = int(os.getenv("MAX_TOKENS_PER_USER", "10"))
        
    def store_token(self, token_id: str, token_data: Dict[str, Any], 
                   user_id: str = None, expiry_seconds: int = None) -> bool:
        """Store encrypted token"""
        try:
            expiry_seconds = expiry_seconds or self.token_expiry_default
            
            # Encrypt token data
            encrypted_token = self.encryption_manager.encrypt(
                token_data, 
                data_type="oauth_token",
                associated_data=token_id
            )
            
            # Create token record
            token_record = {
                "token_id": token_id,
                "user_id": user_id,
                "encrypted_data": encrypted_token,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=expiry_seconds)).isoformat(),
                "status": "active",
                "access_count": 0,
                "last_accessed": None
            }
            
            # Store in MongoDB
            if self.mongodb:
                self._store_token_in_mongodb(token_record)
            
            # Cache in Redis
            if self.redis:
                self._store_token_in_redis(token_record)
            
            # Clean up old tokens for user
            if user_id:
                self._cleanup_user_tokens(user_id)
            
            logger.info(f"Token stored: {token_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing token: {e}")
            return False
    
    def retrieve_token(self, token_id: str, user_id: str = None) -> Optional[Dict[str, Any]]:
        """Retrieve and decrypt token"""
        try:
            # Try Redis first
            if self.redis:
                token_record = self._get_token_from_redis(token_id)
                if token_record:
                    return self._decrypt_and_update_token(token_record)
            
            # Fallback to MongoDB
            if self.mongodb:
                token_record = self._get_token_from_mongodb(token_id)
                if token_record:
                    return self._decrypt_and_update_token(token_record)
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving token: {e}")
            return None
    
    def revoke_token(self, token_id: str) -> bool:
        """Revoke token"""
        try:
            # Update MongoDB
            if self.mongodb:
                pymongo_client = _import_pymongo()
                if not pymongo_client:
                    return False

                db = self.mongodb.get_database("zalopay_phishing")
                tokens_collection = db.oauth_tokens

                tokens_collection.update_one(
                    {"token_id": token_id},
                    {
                        "$set": {
                            "status": "revoked",
                            "revoked_at": datetime.now(timezone.utc).isoformat()
                        }
                    }
                )

            # Remove from Redis
            if self.redis:
                cache_key = f"oauth_token:{token_id}"
                self.redis.delete(cache_key)

            logger.info(f"Token revoked: {token_id}")
            return True

        except Exception as e:
            logger.error(f"Error revoking token: {e}")
            return False
    
    def _store_token_in_mongodb(self, token_record: Dict[str, Any]):
        """Store token in MongoDB"""
        try:
            if not self.mongodb:
                return

            pymongo_client = _import_pymongo()
            if not pymongo_client:
                return

            db = self.mongodb.get_database("zalopay_phishing")
            tokens_collection = db.oauth_tokens

            tokens_collection.replace_one(
                {"token_id": token_record["token_id"]},
                token_record,
                upsert=True
            )

        except Exception as e:
            logger.error(f"Error storing token in MongoDB: {e}")
    
    def _store_token_in_redis(self, token_record: Dict[str, Any]):
        """Store token in Redis"""
        try:
            if not self.redis:
                return
            
            cache_key = f"oauth_token:{token_record['token_id']}"
            expiry_seconds = int((datetime.fromisoformat(token_record['expires_at']) - 
                                datetime.now(timezone.utc)).total_seconds())
            
            if expiry_seconds > 0:
                self.redis.setex(cache_key, expiry_seconds, json.dumps(token_record))
            
        except Exception as e:
            logger.error(f"Error storing token in Redis: {e}")
    
    def _get_token_from_redis(self, token_id: str) -> Optional[Dict[str, Any]]:
        """Get token from Redis"""
        try:
            if not self.redis:
                return None
            
            cache_key = f"oauth_token:{token_id}"
            token_data = self.redis.get(cache_key)
            
            if token_data:
                return json.loads(token_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting token from Redis: {e}")
            return None
    
    def _get_token_from_mongodb(self, token_id: str) -> Optional[Dict[str, Any]]:
        """Get token from MongoDB"""
        try:
            if not self.mongodb:
                return None

            pymongo_client = _import_pymongo()
            if not pymongo_client:
                return None

            db = self.mongodb.get_database("zalopay_phishing")
            tokens_collection = db.oauth_tokens

            return tokens_collection.find_one({"token_id": token_id, "status": "active"})

        except Exception as e:
            logger.error(f"Error getting token from MongoDB: {e}")
            return None
    
    def _decrypt_and_update_token(self, token_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Decrypt token and update access statistics"""
        try:
            # Check if token is expired
            expires_at = datetime.fromisoformat(token_record['expires_at'])
            if datetime.now(timezone.utc) > expires_at:
                self.revoke_token(token_record['token_id'])
                return None
            
            # Decrypt token data
            decrypted_data = self.encryption_manager.decrypt(
                token_record['encrypted_data'],
                associated_data=token_record['token_id']
            )
            
            # Update access statistics
            self._update_token_access_stats(token_record['token_id'])
            
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Error decrypting token: {e}")
            return None
    
    def _update_token_access_stats(self, token_id: str):
        """Update token access statistics"""
        try:
            if not self.mongodb:
                return
            
            db = self.mongodb.get_database("zalopay_phishing")
            tokens_collection = db.oauth_tokens
            
            tokens_collection.update_one(
                {"token_id": token_id},
                {
                    "$inc": {"access_count": 1},
                    "$set": {"last_accessed": datetime.now(timezone.utc).isoformat()}
                }
            )
            
        except Exception as e:
            logger.error(f"Error updating token access stats: {e}")
    
    def _cleanup_user_tokens(self, user_id: str):
        """Clean up old tokens for user"""
        try:
            if not self.mongodb:
                return
            
            db = self.mongodb.get_database("zalopay_phishing")
            tokens_collection = db.oauth_tokens
            
            # Get user's tokens sorted by creation date
            user_tokens = list(tokens_collection.find(
                {"user_id": user_id, "status": "active"}
            ).sort("created_at", -1))
            
            # Remove excess tokens
            if len(user_tokens) > self.max_tokens_per_user:
                tokens_to_remove = user_tokens[self.max_tokens_per_user:]
                for token in tokens_to_remove:
                    self.revoke_token(token['token_id'])
            
        except Exception as e:
            logger.error(f"Error cleaning up user tokens: {e}")

class HSMIntegration:
    """Hardware Security Module integration (placeholder)"""
    
    def __init__(self):
        self.hsm_enabled = os.getenv("HSM_ENABLED", "false").lower() == "true"
        self.hsm_endpoint = os.getenv("HSM_ENDPOINT")
        
    def generate_key(self, key_type: str = "AES-256") -> Optional[bytes]:
        """Generate key using HSM"""
        if not self.hsm_enabled:
            return None
        
        try:
            # Placeholder for HSM integration
            # In production, this would interface with actual HSM
            logger.info(f"HSM key generation requested: {key_type}")
            return secrets.token_bytes(32)
            
        except Exception as e:
            logger.error(f"Error generating HSM key: {e}")
            return None
    
    def encrypt_with_hsm(self, data: bytes, key_id: str) -> Optional[bytes]:
        """Encrypt data using HSM"""
        if not self.hsm_enabled:
            return None
        
        try:
            # Placeholder for HSM encryption
            logger.info(f"HSM encryption requested for key: {key_id}")
            return data  # Placeholder
            
        except Exception as e:
            logger.error(f"Error encrypting with HSM: {e}")
            return None
    
    def decrypt_with_hsm(self, encrypted_data: bytes, key_id: str) -> Optional[bytes]:
        """Decrypt data using HSM"""
        if not self.hsm_enabled:
            return None
        
        try:
            # Placeholder for HSM decryption
            logger.info(f"HSM decryption requested for key: {key_id}")
            return encrypted_data  # Placeholder
            
        except Exception as e:
            logger.error(f"Error decrypting with HSM: {e}")
            return None

class AdvancedEncryptionManager:
    """Advanced encryption manager with all features"""
    
    def __init__(self, master_key: str = None, mongodb_connection=None, redis_client=None):
        self.master_key = master_key or os.getenv("ENCRYPTION_MASTER_KEY")
        if not self.master_key:
            raise ValueError("Master key is required")
        
        self.mongodb = mongodb_connection
        self.redis = redis_client
        
        # Initialize components
        self.key_rotation_manager = KeyRotationManager(mongodb_connection, redis_client)
        self.hsm_integration = HSMIntegration()
        
        # Initialize base encryption manager
        from encryption import EncryptionManager
        self.base_encryption_manager = EncryptionManager(self.master_key)
        
        # Initialize secure token storage
        self.secure_token_storage = SecureTokenStorage(
            self.base_encryption_manager, 
            mongodb_connection, 
            redis_client
        )
        
        # Key management
        self.active_keys = {}
        self.key_cache = {}
        
        # Initialize with master key
        self._initialize_keys()
        
        # Start key rotation
        self.key_rotation_manager.start_key_rotation()
        
        logger.info("Advanced encryption manager initialized")
    
    def _initialize_keys(self):
        """Initialize encryption keys"""
        try:
            # Generate initial key
            key_id = secrets.token_hex(16)
            key_material = secrets.token_bytes(32)
            
            self.active_keys[key_id] = {
                "key_id": key_id,
                "key_material": key_material,
                "created_at": datetime.now(timezone.utc),
                "status": "active"
            }
            
            # Store in database
            self._store_key(self.active_keys[key_id])
            
            logger.info(f"Initial encryption key created: {key_id}")
            
        except Exception as e:
            logger.error(f"Error initializing keys: {e}")
            raise
    
    def _store_key(self, key_data: Dict[str, Any]):
        """Store encryption key"""
        try:
            if not self.mongodb:
                return

            pymongo_client = _import_pymongo()
            if not pymongo_client:
                return

            db = self.mongodb.get_database("zalopay_phishing")
            keys_collection = db.encryption_keys

            document = {
                "key_id": key_data["key_id"],
                "key_material": base64.b64encode(key_data["key_material"]).decode('utf-8'),
                "algorithm": "AES-256-GCM",
                "created_at": key_data["created_at"].isoformat(),
                "status": key_data["status"],
                "version": 1
            }

            keys_collection.replace_one(
                {"key_id": key_data["key_id"]},
                document,
                upsert=True
            )

        except Exception as e:
            logger.error(f"Error storing key: {e}")
    
    def encrypt_data(self, data: Any, data_type: str = "general", 
                    associated_data: str = None, key_id: str = None) -> Dict[str, str]:
        """Encrypt data with advanced features"""
        try:
            # Use HSM if available and requested
            if self.hsm_integration.hsm_enabled and key_id:
                hsm_encrypted = self.hsm_integration.encrypt_with_hsm(
                    json.dumps(data).encode(), key_id
                )
                if hsm_encrypted:
                    return {
                        "encrypted_data": base64.b64encode(hsm_encrypted).decode('utf-8'),
                        "algorithm": "HSM-AES-256",
                        "key_id": key_id,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
            
            # Use base encryption manager
            encrypted_package = self.base_encryption_manager.encrypt(data, data_type, associated_data)
            
            # Add key information
            if key_id:
                encrypted_package["key_id"] = key_id
            else:
                # Use current active key
                active_key_id = list(self.active_keys.keys())[0]
                encrypted_package["key_id"] = active_key_id
            
            return encrypted_package
            
        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            raise
    
    def decrypt_data(self, encrypted_package: Dict[str, str], 
                    associated_data: str = None) -> Any:
        """Decrypt data with advanced features"""
        try:
            # Check if HSM encrypted
            if encrypted_package.get("algorithm") == "HSM-AES-256":
                key_id = encrypted_package.get("key_id")
                if key_id:
                    encrypted_data = base64.b64decode(encrypted_package["encrypted_data"])
                    decrypted_data = self.hsm_integration.decrypt_with_hsm(encrypted_data, key_id)
                    if decrypted_data:
                        return json.loads(decrypted_data.decode())
            
            # Use base encryption manager
            return self.base_encryption_manager.decrypt(encrypted_package, associated_data)
            
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            raise
    
    def store_oauth_token(self, token_id: str, token_data: Dict[str, Any], 
                         user_id: str = None, expiry_seconds: int = None) -> bool:
        """Store OAuth token securely"""
        return self.secure_token_storage.store_token(token_id, token_data, user_id, expiry_seconds)
    
    def retrieve_oauth_token(self, token_id: str, user_id: str = None) -> Optional[Dict[str, Any]]:
        """Retrieve OAuth token"""
        return self.secure_token_storage.retrieve_token(token_id, user_id)
    
    def revoke_oauth_token(self, token_id: str) -> bool:
        """Revoke OAuth token"""
        return self.secure_token_storage.revoke_token(token_id)
    
    def encrypt_file(self, file_path: str, output_path: str = None,
                    associated_data: str = None) -> str:
        """Encrypt file with advanced features"""
        return self.base_encryption_manager.encrypt_file(file_path, output_path, associated_data)
    
    def decrypt_file(self, encrypted_file_path: str, output_path: str = None,
                    associated_data: str = None) -> str:
        """Decrypt file with advanced features"""
        return self.base_encryption_manager.decrypt_file(encrypted_file_path, output_path, associated_data)
    
    def get_encryption_stats(self) -> Dict[str, Any]:
        """Get encryption system statistics"""
        try:
            stats = {
                "active_keys_count": len(self.active_keys),
                "key_rotation_active": self.key_rotation_manager.key_rotation_active,
                "hsm_enabled": self.hsm_integration.hsm_enabled,
                "master_key_configured": bool(self.master_key),
                "mongodb_connected": bool(self.mongodb),
                "redis_connected": bool(self.redis),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Add key rotation stats
            if self.mongodb:
                pymongo_client = _import_pymongo()
                if pymongo_client:
                    db = self.mongodb.get_database("zalopay_phishing")
                    keys_collection = db.encryption_keys

                    stats["total_keys"] = keys_collection.count_documents({})
                    stats["active_keys"] = keys_collection.count_documents({"status": "active"})
                    stats["rotated_keys"] = keys_collection.count_documents({"status": "rotated"})

            return stats

        except Exception as e:
            logger.error(f"Error getting encryption stats: {e}")
            return {"error": str(e)}
    
    def rotate_keys_manually(self) -> bool:
        """Manually trigger key rotation"""
        try:
            self.key_rotation_manager._perform_key_rotation()
            return True
        except Exception as e:
            logger.error(f"Error in manual key rotation: {e}")
            return False
    
    def cleanup_expired_tokens(self) -> int:
        """Clean up expired tokens"""
        try:
            if not self.mongodb:
                return 0

            pymongo_client = _import_pymongo()
            if not pymongo_client:
                return 0

            db = self.mongodb.get_database("zalopay_phishing")
            tokens_collection = db.oauth_tokens

            # Find expired tokens
            current_time = datetime.now(timezone.utc).isoformat()
            expired_tokens = tokens_collection.find({
                "expires_at": {"$lt": current_time},
                "status": "active"
            })

            count = 0
            for token in expired_tokens:
                self.revoke_oauth_token(token["token_id"])
                count += 1

            logger.info(f"Cleaned up {count} expired tokens")
            return count

        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {e}")
            return 0
    
    def shutdown(self):
        """Shutdown encryption manager"""
        try:
            self.key_rotation_manager.stop_key_rotation()
            logger.info("Advanced encryption manager shutdown")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

# Global advanced encryption manager instance
advanced_encryption_manager = None

def initialize_advanced_encryption_manager(master_key: str = None, 
                                         mongodb_connection=None, 
                                         redis_client=None) -> AdvancedEncryptionManager:
    """Initialize global advanced encryption manager"""
    global advanced_encryption_manager
    advanced_encryption_manager = AdvancedEncryptionManager(master_key, mongodb_connection, redis_client)
    return advanced_encryption_manager

def get_advanced_encryption_manager() -> AdvancedEncryptionManager:
    """Get global advanced encryption manager"""
    if advanced_encryption_manager is None:
        raise ValueError("Advanced encryption manager not initialized")
    return advanced_encryption_manager

# Convenience functions
def encrypt_data_advanced(data: Any, data_type: str = "general", 
                         associated_data: str = None, key_id: str = None) -> Dict[str, str]:
    """Encrypt data with advanced features (global convenience function)"""
    return get_advanced_encryption_manager().encrypt_data(data, data_type, associated_data, key_id)

def decrypt_data_advanced(encrypted_package: Dict[str, str], 
                         associated_data: str = None) -> Any:
    """Decrypt data with advanced features (global convenience function)"""
    return get_advanced_encryption_manager().decrypt_data(encrypted_package, associated_data)

def store_oauth_token_secure(token_id: str, token_data: Dict[str, Any], 
                           user_id: str = None, expiry_seconds: int = None) -> bool:
    """Store OAuth token securely (global convenience function)"""
    return get_advanced_encryption_manager().store_oauth_token(token_id, token_data, user_id, expiry_seconds)

def retrieve_oauth_token_secure(token_id: str, user_id: str = None) -> Optional[Dict[str, Any]]:
    """Retrieve OAuth token securely (global convenience function)"""
    return get_advanced_encryption_manager().retrieve_oauth_token(token_id, user_id)

def revoke_oauth_token_secure(token_id: str) -> bool:
    """Revoke OAuth token securely (global convenience function)"""
    return get_advanced_encryption_manager().revoke_oauth_token(token_id)
