"""
AES-256-GCM Encryption Engine
High-security encryption for sensitive data
"""

import os
import secrets
from typing import Dict, List, Optional, Any, Tuple
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
import base64
import json
import logging
import hashlib
import hmac
from datetime import datetime, timezone, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KeyManager:
    """Key management for encryption operations"""

    def __init__(self, master_key: str = None):
        self.master_key = master_key or os.getenv("ENCRYPTION_MASTER_KEY")
        if not self.master_key:
            raise ValueError("Master key is required for encryption operations")

        # Generate encryption keys from master key
        self._derive_keys()

    def _derive_keys(self):
        """Derive encryption keys from master key"""
        try:
            # Use PBKDF2 to derive AES key
            salt = b"zalopay_encryption_salt_2024"
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )

            # Derive AES-256 key
            self.aes_key = kdf.derive(self.master_key.encode())

            # Derive HMAC key for integrity
            hmac_salt = b"zalopay_hmac_salt_2024"
            hmac_kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=hmac_salt,
                iterations=100000,
            )
            self.hmac_key = hmac_kdf.derive(self.master_key.encode())

            # Generate RSA key pair for asymmetric encryption
            self.rsa_private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            self.rsa_public_key = self.rsa_private_key.public_key()

            logger.info("Encryption keys derived successfully")

        except Exception as e:
            logger.error(f"Error deriving encryption keys: {e}")
            raise

    def get_aes_key(self) -> bytes:
        """Get AES encryption key"""
        return self.aes_key

    def get_hmac_key(self) -> bytes:
        """Get HMAC key for integrity checking"""
        return self.hmac_key

    def get_rsa_public_key(self) -> rsa.RSAPublicKey:
        """Get RSA public key"""
        return self.rsa_public_key

    def get_rsa_private_key(self) -> rsa.RSAPrivateKey:
        """Get RSA private key"""
        return self.rsa_private_key

class DataEncryption:
    """AES-256-GCM encryption for data protection"""

    def __init__(self, key_manager: KeyManager = None):
        self.key_manager = key_manager or KeyManager()
        self.aes_key = self.key_manager.get_aes_key()
        self.aesgcm = AESGCM(self.aes_key)

    def encrypt_data(self, data: Any, associated_data: str = None) -> Dict[str, str]:
        """
        Encrypt data using AES-256-GCM

        Args:
            data: Data to encrypt (will be JSON serialized)
            associated_data: Additional data for authentication

        Returns:
            Dict containing encrypted data, nonce, and tag
        """
        try:
            # Serialize data to JSON
            if not isinstance(data, str):
                json_data = json.dumps(data, separators=(',', ':'))
            else:
                json_data = data

            # Generate random nonce
            nonce = secrets.token_bytes(12)  # 96 bits for GCM

            # Convert associated data to bytes if provided
            aad = associated_data.encode('utf-8') if associated_data else None

            # Encrypt data
            encrypted_data = self.aesgcm.encrypt(nonce, json_data.encode('utf-8'), aad)

            # Create HMAC for additional integrity
            hmac_value = self._create_hmac(json_data.encode('utf-8'), associated_data)

            return {
                "encrypted_data": base64.b64encode(encrypted_data).decode('utf-8'),
                "nonce": base64.b64encode(nonce).decode('utf-8'),
                "hmac": hmac_value,
                "algorithm": "AES-256-GCM",
                "version": "1.0",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            raise

    def decrypt_data(self, encrypted_package: Dict[str, str], associated_data: str = None) -> Any:
        """
        Decrypt data using AES-256-GCM

        Args:
            encrypted_package: Encrypted data package from encrypt_data
            associated_data: Additional data for authentication

        Returns:
            Decrypted data
        """
        try:
            # Extract components
            encrypted_data = base64.b64decode(encrypted_package["encrypted_data"])
            nonce = base64.b64decode(encrypted_package["nonce"])
            provided_hmac = encrypted_package["hmac"]

            # Verify HMAC first
            json_data = self._verify_hmac(encrypted_data, provided_hmac, associated_data)
            if json_data is None:
                raise ValueError("HMAC verification failed")

            # Convert associated data to bytes if provided
            aad = associated_data.encode('utf-8') if associated_data else None

            # Decrypt data
            decrypted_data = self.aesgcm.decrypt(nonce, encrypted_data, aad)

            # Try to parse as JSON, otherwise return as string
            try:
                return json.loads(decrypted_data.decode('utf-8'))
            except json.JSONDecodeError:
                return decrypted_data.decode('utf-8')

        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            raise

    def _create_hmac(self, data: bytes, associated_data: str = None) -> str:
        """Create HMAC for data integrity"""
        hmac_key = self.key_manager.get_hmac_key()

        # Include associated data in HMAC if provided
        if associated_data:
            combined_data = data + associated_data.encode('utf-8')
        else:
            combined_data = data

        hmac_value = hmac.new(hmac_key, combined_data, hashlib.sha256).digest()
        return base64.b64encode(hmac_value).decode('utf-8')

    def _verify_hmac(self, data: bytes, provided_hmac: str, associated_data: str = None) -> Optional[bytes]:
        """Verify HMAC for data integrity"""
        try:
            expected_hmac = self._create_hmac(data, associated_data)
            if hmac.compare_digest(expected_hmac, provided_hmac):
                return data
            else:
                logger.warning("HMAC verification failed")
                return None
        except Exception as e:
            logger.error(f"Error verifying HMAC: {e}")
            return None

class AsymmetricEncryption:
    """RSA asymmetric encryption for key exchange"""

    def __init__(self, key_manager: KeyManager = None):
        self.key_manager = key_manager or KeyManager()
        self.public_key = self.key_manager.get_rsa_public_key()
        self.private_key = self.key_manager.get_rsa_private_key()

    def encrypt_with_public_key(self, data: bytes) -> bytes:
        """Encrypt data with RSA public key"""
        try:
            encrypted = self.public_key.encrypt(
                data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return encrypted
        except Exception as e:
            logger.error(f"Error encrypting with public key: {e}")
            raise

    def decrypt_with_private_key(self, encrypted_data: bytes) -> bytes:
        """Decrypt data with RSA private key"""
        try:
            decrypted = self.private_key.decrypt(
                encrypted_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return decrypted
        except Exception as e:
            logger.error(f"Error decrypting with private key: {e}")
            raise

    def get_public_key_pem(self) -> str:
        """Get public key in PEM format"""
        try:
            pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            return pem.decode('utf-8')
        except Exception as e:
            logger.error(f"Error getting public key PEM: {e}")
            raise

class SecureDataHandler:
    """High-level secure data handling"""

    def __init__(self, key_manager: KeyManager = None):
        self.key_manager = key_manager or KeyManager()
        self.symmetric_encryption = DataEncryption(self.key_manager)
        self.asymmetric_encryption = AsymmetricEncryption(self.key_manager)

    def encrypt_sensitive_data(self, data: Any, data_type: str = "general",
                              associated_data: str = None) -> Dict[str, str]:
        """
        Encrypt sensitive data with metadata

        Args:
            data: Data to encrypt
            data_type: Type of data (for categorization)
            associated_data: Additional context data

        Returns:
            Encrypted data package with metadata
        """
        try:
            # Add metadata
            enriched_data = {
                "data": data,
                "data_type": data_type,
                "encrypted_at": datetime.now(timezone.utc).isoformat(),
                "version": "1.0"
            }

            # Encrypt
            encrypted_package = self.symmetric_encryption.encrypt_data(
                enriched_data,
                associated_data
            )

            # Add additional metadata
            encrypted_package["data_type"] = data_type
            encrypted_package["original_size"] = len(json.dumps(data))

            return encrypted_package

        except Exception as e:
            logger.error(f"Error encrypting sensitive data: {e}")
            raise

    def decrypt_sensitive_data(self, encrypted_package: Dict[str, str],
                              associated_data: str = None) -> Dict[str, Any]:
        """
        Decrypt sensitive data

        Args:
            encrypted_package: Encrypted data package
            associated_data: Additional context data

        Returns:
            Decrypted data with metadata
        """
        try:
            decrypted_data = self.symmetric_encryption.decrypt_data(
                encrypted_package,
                associated_data
            )

            return decrypted_data

        except Exception as e:
            logger.error(f"Error decrypting sensitive data: {e}")
            raise

    def encrypt_file(self, file_path: str, output_path: str = None,
                    associated_data: str = None) -> str:
        """
        Encrypt file content

        Args:
            file_path: Path to file to encrypt
            output_path: Path for encrypted file (optional)
            associated_data: Additional context data

        Returns:
            Path to encrypted file
        """
        try:
            # Read file
            with open(file_path, 'rb') as f:
                file_data = f.read()

            # Encrypt file data
            encrypted_package = self.symmetric_encryption.encrypt_data(
                base64.b64encode(file_data).decode('utf-8'),
                associated_data
            )

            # Save encrypted data
            if not output_path:
                output_path = file_path + ".encrypted"

            with open(output_path, 'w') as f:
                json.dump(encrypted_package, f, indent=2)

            logger.info(f"File encrypted: {file_path} -> {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error encrypting file {file_path}: {e}")
            raise

    def decrypt_file(self, encrypted_file_path: str, output_path: str = None,
                    associated_data: str = None) -> str:
        """
        Decrypt file content

        Args:
            encrypted_file_path: Path to encrypted file
            output_path: Path for decrypted file (optional)
            associated_data: Additional context data

        Returns:
            Path to decrypted file
        """
        try:
            # Read encrypted file
            with open(encrypted_file_path, 'r') as f:
                encrypted_package = json.load(f)

            # Decrypt data
            decrypted_data = self.symmetric_encryption.decrypt_data(
                encrypted_package,
                associated_data
            )

            # Decode base64
            file_data = base64.b64decode(decrypted_data)

            # Save decrypted file
            if not output_path:
                output_path = encrypted_file_path.replace(".encrypted", ".decrypted")

            with open(output_path, 'wb') as f:
                f.write(file_data)

            logger.info(f"File decrypted: {encrypted_file_path} -> {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error decrypting file {encrypted_file_path}: {e}")
            raise

class PasswordEncryption:
    """Password-based encryption using Scrypt"""

    def __init__(self, key_manager: KeyManager = None):
        self.key_manager = key_manager or KeyManager()

    def derive_key_from_password(self, password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
        """
        Derive encryption key from password using Scrypt

        Args:
            password: User password
            salt: Salt for key derivation (generated if not provided)

        Returns:
            Tuple of (derived_key, salt)
        """
        try:
            if salt is None:
                salt = secrets.token_bytes(32)

            # Use Scrypt for key derivation (memory-hard function)
            kdf = Scrypt(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                N=2**17,  # CPU/memory cost factor
                r=8,      # Block size
                p=1       # Parallelization factor
            )

            derived_key = kdf.derive(password.encode('utf-8'))
            return derived_key, salt

        except Exception as e:
            logger.error(f"Error deriving key from password: {e}")
            raise

    def encrypt_with_password(self, data: Any, password: str,
                             associated_data: str = None) -> Dict[str, str]:
        """
        Encrypt data with password-based key

        Args:
            data: Data to encrypt
            password: Password for key derivation
            associated_data: Additional context data

        Returns:
            Encrypted data package
        """
        try:
            # Derive key from password
            derived_key, salt = self.derive_key_from_password(password)

            # Create temporary AES-GCM with derived key
            aesgcm = AESGCM(derived_key)

            # Serialize data
            if not isinstance(data, str):
                json_data = json.dumps(data, separators=(',', ':'))
            else:
                json_data = data

            # Generate nonce
            nonce = secrets.token_bytes(12)

            # Convert associated data
            aad = associated_data.encode('utf-8') if associated_data else None

            # Encrypt
            encrypted_data = aesgcm.encrypt(nonce, json_data.encode('utf-8'), aad)

            return {
                "encrypted_data": base64.b64encode(encrypted_data).decode('utf-8'),
                "nonce": base64.b64encode(nonce).decode('utf-8'),
                "salt": base64.b64encode(salt).decode('utf-8'),
                "algorithm": "AES-256-GCM-Scrypt",
                "version": "1.0",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error encrypting with password: {e}")
            raise

    def decrypt_with_password(self, encrypted_package: Dict[str, str],
                             password: str, associated_data: str = None) -> Any:
        """
        Decrypt data with password-based key

        Args:
            encrypted_package: Encrypted data package
            password: Password for key derivation
            associated_data: Additional context data

        Returns:
            Decrypted data
        """
        try:
            # Extract components
            encrypted_data = base64.b64decode(encrypted_package["encrypted_data"])
            nonce = base64.b64decode(encrypted_package["nonce"])
            salt = base64.b64decode(encrypted_package["salt"])

            # Derive key from password
            derived_key, _ = self.derive_key_from_password(password, salt)

            # Create AES-GCM with derived key
            aesgcm = AESGCM(derived_key)

            # Convert associated data
            aad = associated_data.encode('utf-8') if associated_data else None

            # Decrypt
            decrypted_data = aesgcm.decrypt(nonce, encrypted_data, aad)

            # Try to parse as JSON
            try:
                return json.loads(decrypted_data.decode('utf-8'))
            except json.JSONDecodeError:
                return decrypted_data.decode('utf-8')

        except Exception as e:
            logger.error(f"Error decrypting with password: {e}")
            raise

class EncryptionManager:
    """Main encryption manager coordinating all encryption operations"""

    def __init__(self, master_key: str = None):
        self.master_key = master_key or os.getenv("ENCRYPTION_MASTER_KEY")
        if not self.master_key:
            raise ValueError("Master key is required")

        # Initialize components
        self.key_manager = KeyManager(self.master_key)
        self.data_encryption = DataEncryption(self.key_manager)
        self.asymmetric_encryption = AsymmetricEncryption(self.key_manager)
        self.secure_handler = SecureDataHandler(self.key_manager)
        self.password_encryption = PasswordEncryption(self.key_manager)

    def encrypt(self, data: Any, data_type: str = "general",
               associated_data: str = None) -> Dict[str, str]:
        """Encrypt data (convenience method)"""
        return self.secure_handler.encrypt_sensitive_data(data, data_type, associated_data)

    def decrypt(self, encrypted_package: Dict[str, str],
               associated_data: str = None) -> Any:
        """Decrypt data (convenience method)"""
        return self.secure_handler.decrypt_sensitive_data(encrypted_package, associated_data)

    def encrypt_file(self, file_path: str, output_path: str = None,
                    associated_data: str = None) -> str:
        """Encrypt file (convenience method)"""
        return self.secure_handler.encrypt_file(file_path, output_path, associated_data)

    def decrypt_file(self, encrypted_file_path: str, output_path: str = None,
                    associated_data: str = None) -> str:
        """Decrypt file (convenience method)"""
        return self.secure_handler.decrypt_file(encrypted_file_path, output_path, associated_data)

    def encrypt_with_password(self, data: Any, password: str,
                             associated_data: str = None) -> Dict[str, str]:
        """Encrypt with password (convenience method)"""
        return self.password_encryption.encrypt_with_password(data, password, associated_data)

    def decrypt_with_password(self, encrypted_package: Dict[str, str],
                             password: str, associated_data: str = None) -> Any:
        """Decrypt with password (convenience method)"""
        return self.password_encryption.decrypt_with_password(encrypted_package, password, associated_data)

    def get_public_key_pem(self) -> str:
        """Get public key for external encryption"""
        return self.asymmetric_encryption.get_public_key_pem()

    def rotate_keys(self) -> bool:
        """Rotate encryption keys (for key rotation scenarios)"""
        try:
            # In a production system, this would involve:
            # 1. Generating new keys
            # 2. Re-encrypting existing data with new keys
            # 3. Securely storing old keys for decryption of legacy data

            logger.info("Key rotation initiated (placeholder implementation)")
            return True

        except Exception as e:
            logger.error(f"Error rotating keys: {e}")
            return False

# Global encryption manager instance
encryption_manager = None

def initialize_encryption(master_key: str = None) -> EncryptionManager:
    """Initialize global encryption manager"""
    global encryption_manager
    encryption_manager = EncryptionManager(master_key)
    return encryption_manager

def get_encryption_manager() -> EncryptionManager:
    """Get global encryption manager"""
    if encryption_manager is None:
        raise ValueError("Encryption manager not initialized")
    return encryption_manager

# Convenience functions
def encrypt_data(data: Any, data_type: str = "general", associated_data: str = None) -> Dict[str, str]:
    """Encrypt data (global convenience function)"""
    return get_encryption_manager().encrypt(data, data_type, associated_data)

def decrypt_data(encrypted_package: Dict[str, str], associated_data: str = None) -> Any:
    """Decrypt data (global convenience function)"""
    return get_encryption_manager().decrypt(encrypted_package, associated_data)