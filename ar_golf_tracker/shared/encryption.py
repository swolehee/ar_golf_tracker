"""Encryption utilities for AR Golf Tracker.

Provides AES-256 encryption for data at rest and utilities for TLS 1.3 configuration.
"""

import os
import base64
import json
from typing import Any, Dict, Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, padding as sym_padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


class EncryptionService:
    """Service for encrypting and decrypting data at rest using AES-256.
    
    Features:
    - AES-256-CBC encryption for data at rest
    - PBKDF2 key derivation from passwords
    - Secure random IV generation
    - Base64 encoding for storage
    """
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        """Initialize encryption service.
        
        Args:
            encryption_key: 32-byte encryption key for AES-256.
                          If None, generates a random key (for testing).
        """
        if encryption_key is None:
            # Generate random key for testing/development
            encryption_key = os.urandom(32)
        elif len(encryption_key) != 32:
            raise ValueError("Encryption key must be exactly 32 bytes for AES-256")
        
        self.encryption_key = encryption_key
        self.backend = default_backend()
    
    @staticmethod
    def derive_key_from_password(password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
        """Derive a 32-byte encryption key from a password using PBKDF2.
        
        Args:
            password: User password
            salt: Salt for key derivation. If None, generates random salt.
            
        Returns:
            Tuple of (derived_key, salt)
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(password.encode('utf-8'))
        return key, salt
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext using AES-256-CBC.
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Base64-encoded encrypted data with IV prepended
            Format: base64(iv + ciphertext)
        """
        # Generate random IV (16 bytes for AES)
        iv = os.urandom(16)
        
        # Pad plaintext to block size (128 bits = 16 bytes)
        padder = sym_padding.PKCS7(128).padder()
        padded_data = padder.update(plaintext.encode('utf-8')) + padder.finalize()
        
        # Encrypt
        cipher = Cipher(
            algorithms.AES(self.encryption_key),
            modes.CBC(iv),
            backend=self.backend
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        # Prepend IV to ciphertext and encode as base64
        encrypted_data = iv + ciphertext
        return base64.b64encode(encrypted_data).decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data encrypted with AES-256-CBC.
        
        Args:
            encrypted_data: Base64-encoded encrypted data with IV prepended
            
        Returns:
            Decrypted plaintext string
            
        Raises:
            ValueError: If decryption fails
        """
        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # Extract IV (first 16 bytes) and ciphertext
            iv = encrypted_bytes[:16]
            ciphertext = encrypted_bytes[16:]
            
            # Decrypt
            cipher = Cipher(
                algorithms.AES(self.encryption_key),
                modes.CBC(iv),
                backend=self.backend
            )
            decryptor = cipher.decryptor()
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Unpad
            unpadder = sym_padding.PKCS7(128).unpadder()
            plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
            
            return plaintext.decode('utf-8')
        
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")
    
    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """Encrypt a dictionary by converting to JSON first.
        
        Args:
            data: Dictionary to encrypt
            
        Returns:
            Base64-encoded encrypted JSON
        """
        json_str = json.dumps(data)
        return self.encrypt(json_str)
    
    def decrypt_dict(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt data and parse as JSON dictionary.
        
        Args:
            encrypted_data: Base64-encoded encrypted JSON
            
        Returns:
            Decrypted dictionary
            
        Raises:
            ValueError: If decryption or JSON parsing fails
        """
        json_str = self.decrypt(encrypted_data)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse decrypted data as JSON: {e}")


class TLSConfig:
    """Configuration utilities for TLS 1.3 in transit encryption.
    
    Provides recommended settings for securing API communication.
    """
    
    @staticmethod
    def get_ssl_context_config() -> Dict[str, Any]:
        """Get recommended SSL context configuration for TLS 1.3.
        
        Returns:
            Dictionary with SSL configuration parameters
        """
        import ssl
        
        return {
            'ssl_version': ssl.PROTOCOL_TLS_CLIENT,
            'ssl_minimum_version': ssl.TLSVersion.TLSv1_3,
            'check_hostname': True,
            'verify_mode': ssl.CERT_REQUIRED,
            'ciphers': 'TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_128_GCM_SHA256'
        }
    
    @staticmethod
    def get_requests_session_config() -> Dict[str, Any]:
        """Get configuration for requests library to use TLS 1.3.
        
        Returns:
            Dictionary with requests session configuration
        """
        return {
            'verify': True,  # Verify SSL certificates
            'timeout': 30,   # Connection timeout
        }
    
    @staticmethod
    def get_uvicorn_ssl_config(cert_file: str, key_file: str) -> Dict[str, Any]:
        """Get SSL configuration for Uvicorn server (FastAPI).
        
        Args:
            cert_file: Path to SSL certificate file
            key_file: Path to SSL private key file
            
        Returns:
            Dictionary with Uvicorn SSL configuration
        """
        import ssl
        
        return {
            'ssl_keyfile': key_file,
            'ssl_certfile': cert_file,
            'ssl_version': ssl.PROTOCOL_TLS_SERVER,
            'ssl_cert_reqs': ssl.CERT_NONE,
            'ssl_ciphers': 'TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_128_GCM_SHA256'
        }


def generate_encryption_key() -> bytes:
    """Generate a secure random 32-byte encryption key for AES-256.
    
    Returns:
        32-byte encryption key
    """
    return os.urandom(32)


def save_encryption_key(key: bytes, filepath: str) -> None:
    """Save encryption key to file (base64 encoded).
    
    Args:
        key: Encryption key to save
        filepath: Path to save key file
    """
    encoded_key = base64.b64encode(key).decode('utf-8')
    with open(filepath, 'w') as f:
        f.write(encoded_key)


def load_encryption_key(filepath: str) -> bytes:
    """Load encryption key from file.
    
    Args:
        filepath: Path to key file
        
    Returns:
        Encryption key
        
    Raises:
        FileNotFoundError: If key file doesn't exist
        ValueError: If key file is invalid
    """
    try:
        with open(filepath, 'r') as f:
            encoded_key = f.read().strip()
        return base64.b64decode(encoded_key.encode('utf-8'))
    except FileNotFoundError:
        raise FileNotFoundError(f"Encryption key file not found: {filepath}")
    except Exception as e:
        raise ValueError(f"Failed to load encryption key: {e}")
