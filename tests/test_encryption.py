"""Tests for encryption functionality.

Tests AES-256 encryption for data at rest and TLS 1.3 configuration.
"""

import pytest
import os
import tempfile
import json
from ar_golf_tracker.shared.encryption import (
    EncryptionService,
    TLSConfig,
    generate_encryption_key,
    save_encryption_key,
    load_encryption_key
)


class TestEncryptionService:
    """Test AES-256 encryption service."""
    
    def test_encrypt_decrypt_string(self):
        """Test basic string encryption and decryption."""
        service = EncryptionService()
        plaintext = "Hello, World!"
        
        # Encrypt
        encrypted = service.encrypt(plaintext)
        assert encrypted != plaintext
        assert len(encrypted) > 0
        
        # Decrypt
        decrypted = service.decrypt(encrypted)
        assert decrypted == plaintext
    
    def test_encrypt_decrypt_long_string(self):
        """Test encryption of longer strings."""
        service = EncryptionService()
        plaintext = "A" * 1000  # 1000 characters
        
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == plaintext
    
    def test_encrypt_decrypt_unicode(self):
        """Test encryption of unicode characters."""
        service = EncryptionService()
        plaintext = "Hello 世界 🌍 Привет"
        
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == plaintext
    
    def test_encrypt_decrypt_empty_string(self):
        """Test encryption of empty string."""
        service = EncryptionService()
        plaintext = ""
        
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == plaintext
    
    def test_encrypt_produces_different_ciphertext(self):
        """Test that encrypting the same plaintext twice produces different ciphertext (due to random IV)."""
        service = EncryptionService()
        plaintext = "Test message"
        
        encrypted1 = service.encrypt(plaintext)
        encrypted2 = service.encrypt(plaintext)
        
        # Different ciphertexts due to random IV
        assert encrypted1 != encrypted2
        
        # But both decrypt to same plaintext
        assert service.decrypt(encrypted1) == plaintext
        assert service.decrypt(encrypted2) == plaintext
    
    def test_decrypt_with_wrong_key_fails(self):
        """Test that decryption with wrong key fails."""
        service1 = EncryptionService()
        service2 = EncryptionService()  # Different key
        
        plaintext = "Secret message"
        encrypted = service1.encrypt(plaintext)
        
        # Decryption with wrong key should fail
        with pytest.raises(ValueError, match="Decryption failed"):
            service2.decrypt(encrypted)
    
    def test_decrypt_invalid_data_fails(self):
        """Test that decrypting invalid data fails."""
        service = EncryptionService()
        
        with pytest.raises(ValueError, match="Decryption failed"):
            service.decrypt("invalid-base64-data")
    
    def test_encrypt_decrypt_dict(self):
        """Test dictionary encryption and decryption."""
        service = EncryptionService()
        data = {
            "id": "123",
            "name": "Test",
            "values": [1, 2, 3],
            "nested": {"key": "value"}
        }
        
        # Encrypt
        encrypted = service.encrypt_dict(data)
        assert isinstance(encrypted, str)
        
        # Decrypt
        decrypted = service.decrypt_dict(encrypted)
        assert decrypted == data
    
    def test_encrypt_decrypt_complex_dict(self):
        """Test encryption of complex dictionary with various data types."""
        service = EncryptionService()
        data = {
            "string": "test",
            "int": 42,
            "float": 3.14,
            "bool": True,
            "null": None,
            "list": [1, "two", 3.0],
            "nested": {
                "deep": {
                    "value": "nested"
                }
            }
        }
        
        encrypted = service.encrypt_dict(data)
        decrypted = service.decrypt_dict(encrypted)
        
        assert decrypted == data
    
    def test_decrypt_dict_invalid_json_fails(self):
        """Test that decrypting non-JSON data as dict fails."""
        service = EncryptionService()
        
        # Encrypt a non-JSON string
        encrypted = service.encrypt("not json")
        
        # Should fail to parse as JSON
        with pytest.raises(ValueError, match="Failed to parse decrypted data as JSON"):
            service.decrypt_dict(encrypted)
    
    def test_custom_encryption_key(self):
        """Test using a custom encryption key."""
        key = os.urandom(32)
        service1 = EncryptionService(encryption_key=key)
        service2 = EncryptionService(encryption_key=key)
        
        plaintext = "Test with custom key"
        
        # Encrypt with service1
        encrypted = service1.encrypt(plaintext)
        
        # Decrypt with service2 (same key)
        decrypted = service2.decrypt(encrypted)
        
        assert decrypted == plaintext
    
    def test_invalid_key_length_raises_error(self):
        """Test that invalid key length raises error."""
        with pytest.raises(ValueError, match="Encryption key must be exactly 32 bytes"):
            EncryptionService(encryption_key=b"short")
    
    def test_derive_key_from_password(self):
        """Test key derivation from password."""
        password = "my-secure-password"
        
        # Derive key
        key1, salt1 = EncryptionService.derive_key_from_password(password)
        
        assert len(key1) == 32  # AES-256 requires 32 bytes
        assert len(salt1) == 16
        
        # Derive again with same password but different salt
        key2, salt2 = EncryptionService.derive_key_from_password(password)
        
        # Different salts produce different keys
        assert salt1 != salt2
        assert key1 != key2
        
        # Same password and salt produce same key
        key3, _ = EncryptionService.derive_key_from_password(password, salt=salt1)
        assert key3 == key1
    
    def test_password_based_encryption(self):
        """Test encryption using password-derived key."""
        password = "my-password"
        key, salt = EncryptionService.derive_key_from_password(password)
        
        service = EncryptionService(encryption_key=key)
        plaintext = "Secret data"
        
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == plaintext
        
        # Can recreate service with same password and salt
        key2, _ = EncryptionService.derive_key_from_password(password, salt=salt)
        service2 = EncryptionService(encryption_key=key2)
        
        decrypted2 = service2.decrypt(encrypted)
        assert decrypted2 == plaintext


class TestKeyManagement:
    """Test encryption key management functions."""
    
    def test_generate_encryption_key(self):
        """Test key generation."""
        key = generate_encryption_key()
        
        assert len(key) == 32
        assert isinstance(key, bytes)
        
        # Generate another key - should be different
        key2 = generate_encryption_key()
        assert key != key2
    
    def test_save_and_load_encryption_key(self):
        """Test saving and loading encryption key."""
        key = generate_encryption_key()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            filepath = f.name
        
        try:
            # Save key
            save_encryption_key(key, filepath)
            
            # Load key
            loaded_key = load_encryption_key(filepath)
            
            assert loaded_key == key
        finally:
            os.unlink(filepath)
    
    def test_load_nonexistent_key_fails(self):
        """Test that loading non-existent key file fails."""
        with pytest.raises(FileNotFoundError):
            load_encryption_key("/nonexistent/path/key.txt")
    
    def test_load_invalid_key_file_fails(self):
        """Test that loading invalid key file fails."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("invalid-key-data")
            filepath = f.name
        
        try:
            with pytest.raises(ValueError, match="Failed to load encryption key"):
                load_encryption_key(filepath)
        finally:
            os.unlink(filepath)


class TestTLSConfig:
    """Test TLS 1.3 configuration utilities."""
    
    def test_get_ssl_context_config(self):
        """Test SSL context configuration."""
        config = TLSConfig.get_ssl_context_config()
        
        assert 'ssl_version' in config
        assert 'ssl_minimum_version' in config
        assert 'check_hostname' in config
        assert 'verify_mode' in config
        assert 'ciphers' in config
        
        # Check TLS 1.3 ciphers are included
        assert 'TLS_AES_256_GCM_SHA384' in config['ciphers']
    
    def test_get_requests_session_config(self):
        """Test requests session configuration."""
        config = TLSConfig.get_requests_session_config()
        
        assert 'verify' in config
        assert config['verify'] is True
        assert 'timeout' in config
    
    def test_get_uvicorn_ssl_config(self):
        """Test Uvicorn SSL configuration."""
        cert_file = "/path/to/cert.pem"
        key_file = "/path/to/key.pem"
        
        config = TLSConfig.get_uvicorn_ssl_config(cert_file, key_file)
        
        assert config['ssl_keyfile'] == key_file
        assert config['ssl_certfile'] == cert_file
        assert 'ssl_version' in config
        assert 'ssl_ciphers' in config
        
        # Check TLS 1.3 ciphers
        assert 'TLS_AES_256_GCM_SHA384' in config['ssl_ciphers']


class TestEncryptionIntegration:
    """Integration tests for encryption in sync workflow."""
    
    def test_shot_data_encryption_roundtrip(self):
        """Test encrypting and decrypting shot data."""
        service = EncryptionService()
        
        shot_data = {
            'id': 'shot-123',
            'round_id': 'round-456',
            'hole_number': 1,
            'swing_number': 1,
            'club_type': 'DRIVER',
            'timestamp': 1234567890,
            'gps_origin': {
                'latitude': 47.6062,
                'longitude': -122.3321,
                'accuracy': 5.0,
                'timestamp': 1234567890,
                'altitude': 100.0
            },
            'distance': {
                'value': 250.0,
                'unit': 'YARDS',
                'accuracy': 'HIGH'
            },
            'notes': 'Great drive!',
            'sync_status': 'PENDING'
        }
        
        # Encrypt
        encrypted = service.encrypt_dict(shot_data)
        
        # Decrypt
        decrypted = service.decrypt_dict(encrypted)
        
        assert decrypted == shot_data
    
    def test_round_data_encryption_roundtrip(self):
        """Test encrypting and decrypting round data."""
        service = EncryptionService()
        
        round_data = {
            'id': 'round-123',
            'user_id': 'user-456',
            'course_id': 'course-789',
            'course_name': 'Pebble Beach',
            'start_time': 1234567890,
            'end_time': 1234571490,
            'weather': {
                'temperature': 72,
                'wind_speed': 10,
                'wind_direction': 'NW',
                'conditions': 'Sunny'
            },
            'sync_status': 'PENDING'
        }
        
        # Encrypt
        encrypted = service.encrypt_dict(round_data)
        
        # Decrypt
        decrypted = service.decrypt_dict(encrypted)
        
        assert decrypted == round_data
    
    def test_encrypted_payload_format(self):
        """Test that encrypted payload has expected format."""
        service = EncryptionService()
        
        data = {'test': 'value'}
        encrypted = service.encrypt_dict(data)
        
        # Create payload as it would be stored
        payload = {'encrypted': True, 'data': encrypted}
        
        assert payload['encrypted'] is True
        assert isinstance(payload['data'], str)
        
        # Decrypt from payload
        decrypted = service.decrypt_dict(payload['data'])
        assert decrypted == data
