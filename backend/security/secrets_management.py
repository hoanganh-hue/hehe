"""
Secrets Management
Handles secure storage and retrieval of sensitive data
"""

import os
import json
import base64
import hashlib
import secrets
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import asyncio

from ..database.redis_client import get_redis_client

logger = logging.getLogger(__name__)

class SecretsManager:
    """
    Manages secrets and sensitive data
    """
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize secrets manager
        
        Args:
            master_key: Master encryption key (if None, will be generated)
        """
        self.master_key = master_key or self._generate_master_key()
        self.fernet = Fernet(self.master_key)
        self.redis_client = None
        self.secrets_cache = {}
        self.cache_ttl = 3600  # 1 hour
        self.encryption_key = None
        
        # Initialize encryption key
        self._initialize_encryption_key()
    
    def _generate_master_key(self) -> bytes:
        """
        Generate master encryption key
        
        Returns:
            Master key bytes
        """
        try:
            # Try to load from environment
            env_key = os.getenv("MASTER_ENCRYPTION_KEY")
            if env_key:
                return base64.b64decode(env_key)
            
            # Generate new key
            key = Fernet.generate_key()
            
            # Save to environment file
            self._save_master_key_to_env(key)
            
            return key
            
        except Exception as e:
            logger.error(f"Error generating master key: {e}")
            return Fernet.generate_key()
    
    def _save_master_key_to_env(self, key: bytes):
        """
        Save master key to environment file
        
        Args:
            key: Master key bytes
        """
        try:
            env_file = ".env"
            key_b64 = base64.b64encode(key).decode()
            
            # Read existing env file
            env_content = ""
            if os.path.exists(env_file):
                with open(env_file, "r") as f:
                    env_content = f.read()
            
            # Add or update master key
            if "MASTER_ENCRYPTION_KEY" in env_content:
                # Update existing key
                lines = env_content.split("\n")
                for i, line in enumerate(lines):
                    if line.startswith("MASTER_ENCRYPTION_KEY="):
                        lines[i] = f"MASTER_ENCRYPTION_KEY={key_b64}"
                        break
                env_content = "\n".join(lines)
            else:
                # Add new key
                env_content += f"\nMASTER_ENCRYPTION_KEY={key_b64}\n"
            
            # Write back to file
            with open(env_file, "w") as f:
                f.write(env_content)
            
            logger.info("Master encryption key saved to environment file")
            
        except Exception as e:
            logger.error(f"Error saving master key to env file: {e}")
    
    def _initialize_encryption_key(self):
        """Initialize encryption key for data encryption"""
        try:
            # Derive key from master key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'zalopay_phishing_salt',
                iterations=100000,
                backend=default_backend()
            )
            
            self.encryption_key = base64.urlsafe_b64encode(kdf.derive(self.master_key))
            
        except Exception as e:
            logger.error(f"Error initializing encryption key: {e}")
            self.encryption_key = Fernet.generate_key()
    
    async def initialize(self):
        """Initialize secrets manager with Redis client"""
        try:
            self.redis_client = await get_redis_client()
            logger.info("Secrets manager initialized with Redis")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis for secrets management: {e}")
            logger.info("Using local storage for secrets management")
    
    def _encrypt_data(self, data: str) -> str:
        """
        Encrypt data using Fernet encryption
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data as base64 string
        """
        try:
            encrypted_data = self.fernet.encrypt(data.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            raise
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt data using Fernet decryption
        
        Args:
            encrypted_data: Encrypted data as base64 string
            
        Returns:
            Decrypted data
        """
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            raise
    
    def _generate_secret_id(self, secret_type: str, name: str) -> str:
        """
        Generate unique secret ID
        
        Args:
            secret_type: Type of secret
            name: Secret name
            
        Returns:
            Unique secret ID
        """
        try:
            timestamp = datetime.now().isoformat()
            random_part = secrets.token_hex(8)
            data = f"{secret_type}:{name}:{timestamp}:{random_part}"
            return hashlib.sha256(data.encode()).hexdigest()[:16]
        except Exception as e:
            logger.error(f"Error generating secret ID: {e}")
            return secrets.token_hex(8)
    
    async def store_secret(self, secret_type: str, name: str, value: str, metadata: Optional[Dict] = None) -> str:
        """
        Store a secret
        
        Args:
            secret_type: Type of secret (password, api_key, token, etc.)
            name: Secret name
            value: Secret value
            metadata: Optional metadata
            
        Returns:
            Secret ID
        """
        try:
            secret_id = self._generate_secret_id(secret_type, name)
            
            # Encrypt the secret value
            encrypted_value = self._encrypt_data(value)
            
            # Create secret record
            secret_record = {
                "secret_id": secret_id,
                "secret_type": secret_type,
                "name": name,
                "encrypted_value": encrypted_value,
                "metadata": metadata or {},
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "access_count": 0,
                "last_accessed": None
            }
            
            # Store in Redis if available
            if self.redis_client:
                await self.redis_client.set(
                    f"secret:{secret_id}",
                    json.dumps(secret_record),
                    ex=self.cache_ttl
                )
            
            # Store in local cache
            self.secrets_cache[secret_id] = secret_record
            
            logger.info(f"Stored secret: {secret_type}:{name}")
            return secret_id
            
        except Exception as e:
            logger.error(f"Error storing secret: {e}")
            raise
    
    async def retrieve_secret(self, secret_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a secret by ID
        
        Args:
            secret_id: Secret ID
            
        Returns:
            Secret record or None
        """
        try:
            # Check local cache first
            if secret_id in self.secrets_cache:
                secret_record = self.secrets_cache[secret_id]
            else:
                # Try Redis
                if self.redis_client:
                    secret_data = await self.redis_client.get(f"secret:{secret_id}")
                    if secret_data:
                        secret_record = json.loads(secret_data)
                    else:
                        return None
                else:
                    return None
            
            # Decrypt the value
            decrypted_value = self._decrypt_data(secret_record["encrypted_value"])
            
            # Update access statistics
            secret_record["access_count"] += 1
            secret_record["last_accessed"] = datetime.now(timezone.utc).isoformat()
            
            # Update cache
            self.secrets_cache[secret_id] = secret_record
            
            # Update Redis
            if self.redis_client:
                await self.redis_client.set(
                    f"secret:{secret_id}",
                    json.dumps(secret_record),
                    ex=self.cache_ttl
                )
            
            # Return secret with decrypted value
            result = secret_record.copy()
            result["value"] = decrypted_value
            del result["encrypted_value"]  # Don't expose encrypted value
            
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving secret: {e}")
            return None
    
    async def retrieve_secret_by_name(self, secret_type: str, name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a secret by type and name
        
        Args:
            secret_type: Type of secret
            name: Secret name
            
        Returns:
            Secret record or None
        """
        try:
            # Search in local cache
            for secret_id, secret_record in self.secrets_cache.items():
                if secret_record["secret_type"] == secret_type and secret_record["name"] == name:
                    return await self.retrieve_secret(secret_id)
            
            # Search in Redis
            if self.redis_client:
                pattern = f"secret:*"
                keys = await self.redis_client.keys(pattern)
                
                for key in keys:
                    secret_data = await self.redis_client.get(key)
                    if secret_data:
                        secret_record = json.loads(secret_data)
                        if secret_record["secret_type"] == secret_type and secret_record["name"] == name:
                            return await self.retrieve_secret(secret_record["secret_id"])
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving secret by name: {e}")
            return None
    
    async def update_secret(self, secret_id: str, value: str, metadata: Optional[Dict] = None) -> bool:
        """
        Update a secret
        
        Args:
            secret_id: Secret ID
            value: New secret value
            metadata: Optional metadata
            
        Returns:
            True if successful
        """
        try:
            # Get existing secret
            secret_record = await self.retrieve_secret(secret_id)
            if not secret_record:
                return False
            
            # Encrypt new value
            encrypted_value = self._encrypt_data(value)
            
            # Update record
            secret_record["encrypted_value"] = encrypted_value
            if metadata:
                secret_record["metadata"].update(metadata)
            secret_record["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            # Store updated record
            if self.redis_client:
                await self.redis_client.set(
                    f"secret:{secret_id}",
                    json.dumps(secret_record),
                    ex=self.cache_ttl
                )
            
            self.secrets_cache[secret_id] = secret_record
            
            logger.info(f"Updated secret: {secret_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating secret: {e}")
            return False
    
    async def delete_secret(self, secret_id: str) -> bool:
        """
        Delete a secret
        
        Args:
            secret_id: Secret ID
            
        Returns:
            True if successful
        """
        try:
            # Remove from Redis
            if self.redis_client:
                await self.redis_client.delete(f"secret:{secret_id}")
            
            # Remove from local cache
            if secret_id in self.secrets_cache:
                del self.secrets_cache[secret_id]
            
            logger.info(f"Deleted secret: {secret_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting secret: {e}")
            return False
    
    async def list_secrets(self, secret_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all secrets
        
        Args:
            secret_type: Optional filter by secret type
            
        Returns:
            List of secret records (without values)
        """
        try:
            secrets_list = []
            
            # Get from local cache
            for secret_id, secret_record in self.secrets_cache.items():
                if secret_type is None or secret_record["secret_type"] == secret_type:
                    # Create a copy without the encrypted value
                    record_copy = secret_record.copy()
                    del record_copy["encrypted_value"]
                    secrets_list.append(record_copy)
            
            # Get from Redis if not in cache
            if self.redis_client:
                pattern = f"secret:*"
                keys = await self.redis_client.keys(pattern)
                
                for key in keys:
                    secret_data = await self.redis_client.get(key)
                    if secret_data:
                        secret_record = json.loads(secret_data)
                        if secret_type is None or secret_record["secret_type"] == secret_type:
                            # Check if not already in list
                            if not any(s["secret_id"] == secret_record["secret_id"] for s in secrets_list):
                                record_copy = secret_record.copy()
                                del record_copy["encrypted_value"]
                                secrets_list.append(record_copy)
            
            return secrets_list
            
        except Exception as e:
            logger.error(f"Error listing secrets: {e}")
            return []
    
    async def rotate_secret(self, secret_id: str, new_value: str) -> bool:
        """
        Rotate a secret (update with new value)
        
        Args:
            secret_id: Secret ID
            new_value: New secret value
            
        Returns:
            True if successful
        """
        try:
            # Get existing secret
            secret_record = await self.retrieve_secret(secret_id)
            if not secret_record:
                return False
            
            # Store old value in metadata for audit
            if "previous_values" not in secret_record["metadata"]:
                secret_record["metadata"]["previous_values"] = []
            
            # Add current value to previous values (encrypted)
            secret_record["metadata"]["previous_values"].append(secret_record["encrypted_value"])
            
            # Keep only last 5 previous values
            if len(secret_record["metadata"]["previous_values"]) > 5:
                secret_record["metadata"]["previous_values"] = secret_record["metadata"]["previous_values"][-5:]
            
            # Update with new value
            return await self.update_secret(secret_id, new_value, secret_record["metadata"])
            
        except Exception as e:
            logger.error(f"Error rotating secret: {e}")
            return False
    
    async def get_secret_statistics(self) -> Dict[str, Any]:
        """
        Get secrets management statistics
        
        Returns:
            Dictionary of statistics
        """
        try:
            secrets_list = await self.list_secrets()
            
            stats = {
                "total_secrets": len(secrets_list),
                "secrets_by_type": {},
                "total_access_count": 0,
                "recently_accessed": 0,
                "oldest_secret": None,
                "newest_secret": None
            }
            
            now = datetime.now(timezone.utc)
            recent_threshold = now - timedelta(days=7)
            
            for secret in secrets_list:
                # Count by type
                secret_type = secret["secret_type"]
                stats["secrets_by_type"][secret_type] = stats["secrets_by_type"].get(secret_type, 0) + 1
                
                # Count total access
                stats["total_access_count"] += secret.get("access_count", 0)
                
                # Count recently accessed
                last_accessed = secret.get("last_accessed")
                if last_accessed:
                    last_accessed_dt = datetime.fromisoformat(last_accessed.replace('Z', '+00:00'))
                    if last_accessed_dt > recent_threshold:
                        stats["recently_accessed"] += 1
                
                # Track oldest and newest
                created_at = datetime.fromisoformat(secret["created_at"].replace('Z', '+00:00'))
                if stats["oldest_secret"] is None or created_at < stats["oldest_secret"]:
                    stats["oldest_secret"] = created_at.isoformat()
                if stats["newest_secret"] is None or created_at > stats["newest_secret"]:
                    stats["newest_secret"] = created_at.isoformat()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting secret statistics: {e}")
            return {}

class OAuthSecretsManager:
    """
    Specialized secrets manager for OAuth credentials
    """
    
    def __init__(self, secrets_manager: SecretsManager):
        """
        Initialize OAuth secrets manager
        
        Args:
            secrets_manager: Base secrets manager
        """
        self.secrets_manager = secrets_manager
    
    async def store_oauth_credentials(self, provider: str, client_id: str, client_secret: str, redirect_uri: str, metadata: Optional[Dict] = None) -> str:
        """
        Store OAuth credentials
        
        Args:
            provider: OAuth provider (google, apple, facebook)
            client_id: Client ID
            client_secret: Client secret
            redirect_uri: Redirect URI
            metadata: Optional metadata
            
        Returns:
            Secret ID
        """
        try:
            oauth_data = {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "provider": provider
            }
            
            return await self.secrets_manager.store_secret(
                secret_type="oauth_credentials",
                name=f"{provider}_oauth",
                value=json.dumps(oauth_data),
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error storing OAuth credentials: {e}")
            raise
    
    async def retrieve_oauth_credentials(self, provider: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve OAuth credentials
        
        Args:
            provider: OAuth provider
            
        Returns:
            OAuth credentials or None
        """
        try:
            secret = await self.secrets_manager.retrieve_secret_by_name("oauth_credentials", f"{provider}_oauth")
            if secret:
                return json.loads(secret["value"])
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving OAuth credentials: {e}")
            return None
    
    async def update_oauth_credentials(self, provider: str, client_id: str, client_secret: str, redirect_uri: str) -> bool:
        """
        Update OAuth credentials
        
        Args:
            provider: OAuth provider
            client_id: Client ID
            client_secret: Client secret
            redirect_uri: Redirect URI
            
        Returns:
            True if successful
        """
        try:
            secret = await self.secrets_manager.retrieve_secret_by_name("oauth_credentials", f"{provider}_oauth")
            if not secret:
                return False
            
            oauth_data = {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "provider": provider
            }
            
            return await self.secrets_manager.update_secret(
                secret["secret_id"],
                json.dumps(oauth_data)
            )
            
        except Exception as e:
            logger.error(f"Error updating OAuth credentials: {e}")
            return False

# Global secrets manager instance
secrets_manager: Optional[SecretsManager] = None
oauth_secrets_manager: Optional[OAuthSecretsManager] = None

async def get_secrets_manager() -> SecretsManager:
    """Get the global secrets manager instance"""
    global secrets_manager
    if secrets_manager is None:
        secrets_manager = SecretsManager()
        await secrets_manager.initialize()
    return secrets_manager

async def get_oauth_secrets_manager() -> OAuthSecretsManager:
    """Get the global OAuth secrets manager instance"""
    global oauth_secrets_manager
    if oauth_secrets_manager is None:
        base_manager = await get_secrets_manager()
        oauth_secrets_manager = OAuthSecretsManager(base_manager)
    return oauth_secrets_manager

async def store_secret(secret_type: str, name: str, value: str, metadata: Optional[Dict] = None) -> str:
    """Store a secret"""
    manager = await get_secrets_manager()
    return await manager.store_secret(secret_type, name, value, metadata)

async def retrieve_secret(secret_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a secret by ID"""
    manager = await get_secrets_manager()
    return await manager.retrieve_secret(secret_id)

async def retrieve_secret_by_name(secret_type: str, name: str) -> Optional[Dict[str, Any]]:
    """Retrieve a secret by type and name"""
    manager = await get_secrets_manager()
    return await manager.retrieve_secret_by_name(secret_type, name)

async def update_secret(secret_id: str, value: str, metadata: Optional[Dict] = None) -> bool:
    """Update a secret"""
    manager = await get_secrets_manager()
    return await manager.update_secret(secret_id, value, metadata)

async def delete_secret(secret_id: str) -> bool:
    """Delete a secret"""
    manager = await get_secrets_manager()
    return await manager.delete_secret(secret_id)

async def list_secrets(secret_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all secrets"""
    manager = await get_secrets_manager()
    return await manager.list_secrets(secret_type)

async def get_secret_statistics() -> Dict[str, Any]:
    """Get secret statistics"""
    manager = await get_secrets_manager()
    return await manager.get_secret_statistics()
