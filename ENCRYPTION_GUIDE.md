# Encryption Guide for AR Golf Tracker

This guide explains the encryption implementation for the AR Golf Tracker system, covering both data at rest (AES-256) and data in transit (TLS 1.3).

## Overview

The AR Golf Tracker implements a comprehensive encryption strategy to protect user data:

1. **Data at Rest**: AES-256-CBC encryption for local storage on AR glasses
2. **Data in Transit**: TLS 1.3 for secure API communication

This implementation satisfies **Requirement 7.4**: "THE System SHALL encrypt all shot data during transmission and storage"

## Data at Rest Encryption (AES-256)

### Architecture

The `EncryptionService` class provides AES-256-CBC encryption for sensitive data stored locally on AR glasses:

- **Algorithm**: AES-256-CBC (Advanced Encryption Standard with 256-bit keys)
- **Key Derivation**: PBKDF2-HMAC-SHA256 with 100,000 iterations
- **IV Generation**: Secure random 16-byte initialization vector per encryption
- **Padding**: PKCS7 padding for block alignment
- **Encoding**: Base64 encoding for storage

### Usage

#### Basic Encryption/Decryption

```python
from ar_golf_tracker.shared.encryption import EncryptionService

# Create encryption service with random key
service = EncryptionService()

# Encrypt string
plaintext = "Sensitive data"
encrypted = service.encrypt(plaintext)

# Decrypt string
decrypted = service.decrypt(encrypted)
```

#### Dictionary Encryption

```python
# Encrypt dictionary (automatically converts to JSON)
data = {
    'id': 'shot-123',
    'club_type': 'DRIVER',
    'distance': 250.0
}
encrypted = service.encrypt_dict(data)

# Decrypt dictionary
decrypted = service.decrypt_dict(encrypted)
```

#### Password-Based Encryption

```python
from ar_golf_tracker.shared.encryption import EncryptionService

# Derive key from password
password = "user-password"
key, salt = EncryptionService.derive_key_from_password(password)

# Create service with derived key
service = EncryptionService(encryption_key=key)

# Save salt for later (needed to recreate key)
# Store salt securely alongside encrypted data
```

#### Key Management

```python
from ar_golf_tracker.shared.encryption import (
    generate_encryption_key,
    save_encryption_key,
    load_encryption_key
)

# Generate new key
key = generate_encryption_key()

# Save to file
save_encryption_key(key, '/path/to/key.txt')

# Load from file
loaded_key = load_encryption_key('/path/to/key.txt')

# Use loaded key
service = EncryptionService(encryption_key=loaded_key)
```

### Integration with Sync Service

The sync service automatically encrypts data when an `EncryptionService` is provided:

```python
from ar_golf_tracker.ar_glasses.sync_service import SyncService
from ar_golf_tracker.ar_glasses.database import LocalDatabase
from ar_golf_tracker.shared.encryption import EncryptionService

# Create encryption service
encryption_service = EncryptionService()

# Create sync service with encryption
sync_service = SyncService(
    database=database,
    encryption_service=encryption_service
)

# Data is automatically encrypted when enqueued
sync_service.enqueue_shot_create(shot)
sync_service.enqueue_round_create(round_obj)
```

### Encrypted Payload Format

When encryption is enabled, payloads in the sync queue have this format:

```python
{
    'encrypted': True,
    'data': 'base64-encoded-encrypted-json'
}
```

The sync service automatically:
1. Encrypts data when enqueuing (CREATE/UPDATE operations)
2. Decrypts data when processing the queue
3. Handles errors if encryption service is unavailable

## Data in Transit Encryption (TLS 1.3)

### Server Configuration

The API server supports TLS 1.3 for secure communication. Configuration is managed through environment variables:

```bash
# Enable TLS
export SSL_ENABLED=true
export SSL_CERTFILE=/path/to/certificate.pem
export SSL_KEYFILE=/path/to/private-key.pem

# Database configuration
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=ar_golf_tracker
export DB_USER=postgres
export DB_PASSWORD=your-password

# Security
export SECRET_KEY=your-secret-key-for-jwt
```

### Starting the Server with TLS

```python
from ar_golf_tracker.backend.server import start_server

# Start with TLS 1.3 enabled
start_server(
    host="0.0.0.0",
    port=8443,  # Standard HTTPS port
    workers=4
)
```

Or via command line:

```bash
python -m ar_golf_tracker.backend.server --host 0.0.0.0 --port 8443 --workers 4
```

### TLS Configuration Details

The server uses these TLS 1.3 settings:

- **Protocol**: TLS 1.3 (minimum version)
- **Cipher Suites**:
  - TLS_AES_256_GCM_SHA384 (preferred)
  - TLS_CHACHA20_POLY1305_SHA256
  - TLS_AES_128_GCM_SHA256

### Client Configuration

For clients connecting to the API:

```python
from ar_golf_tracker.shared.encryption import TLSConfig
import requests

# Get TLS configuration
tls_config = TLSConfig.get_requests_session_config()

# Create session with TLS 1.3
session = requests.Session()
session.verify = tls_config['verify']

# Make secure request
response = session.get('https://api.example.com/api/v1/rounds')
```

### Certificate Management

For production deployment:

1. **Obtain SSL Certificate**:
   - Use Let's Encrypt for free certificates
   - Or purchase from a Certificate Authority
   - Or use AWS Certificate Manager for AWS deployments

2. **Certificate Files**:
   - `certificate.pem`: Public certificate
   - `private-key.pem`: Private key (keep secure!)
   - `chain.pem`: Certificate chain (if applicable)

3. **Certificate Renewal**:
   - Certificates expire (typically 90 days for Let's Encrypt)
   - Set up automatic renewal
   - Restart server after renewal

### Development Mode

For development without TLS:

```bash
# Disable TLS (not recommended for production)
export SSL_ENABLED=false

# Start server
python -m ar_golf_tracker.backend.server
```

**Warning**: Only use unencrypted connections in development environments. Production deployments MUST use TLS.

## Security Best Practices

### Key Management

1. **Never commit encryption keys to version control**
2. **Use environment variables or secure key management services**
3. **Rotate keys periodically** (e.g., every 90 days)
4. **Use different keys for different environments** (dev/staging/prod)
5. **Store keys in secure locations** with restricted access

### Password-Based Encryption

1. **Use strong passwords** (minimum 12 characters)
2. **Store salts securely** alongside encrypted data
3. **Never store passwords in plaintext**
4. **Use PBKDF2 with high iteration count** (100,000+)

### TLS Configuration

1. **Always use TLS 1.3** (or minimum TLS 1.2)
2. **Use strong cipher suites** (AES-256-GCM preferred)
3. **Keep certificates up to date**
4. **Enable certificate validation** on clients
5. **Use HSTS headers** to enforce HTTPS

### Data Protection

1. **Encrypt sensitive data** before storing locally
2. **Use TLS for all API communication**
3. **Implement proper access controls**
4. **Log security events** (failed decryption, invalid certificates)
5. **Regular security audits**

## Testing

### Running Encryption Tests

```bash
# Test encryption module
pytest tests/test_encryption.py -v

# Test sync service encryption integration
pytest tests/test_sync_encryption.py -v

# Run all tests
pytest tests/ -v
```

### Test Coverage

The encryption implementation includes:

- 24 unit tests for encryption service
- 11 integration tests for sync service encryption
- Tests for key management
- Tests for TLS configuration
- Performance tests

## Troubleshooting

### Common Issues

#### "ModuleNotFoundError: No module named 'cryptography'"

Install the cryptography library:

```bash
pip install cryptography
```

#### "Decryption failed" Error

Possible causes:
- Wrong encryption key
- Corrupted encrypted data
- Data encrypted with different key

Solution: Ensure you're using the same key for encryption and decryption.

#### "SSL certificate verify failed"

For development with self-signed certificates:

```python
# Disable certificate verification (development only!)
session = requests.Session()
session.verify = False
```

For production: Use valid certificates from a trusted CA.

#### "SSL_CERTFILE must be set when SSL_ENABLED is true"

Ensure environment variables are set:

```bash
export SSL_CERTFILE=/path/to/cert.pem
export SSL_KEYFILE=/path/to/key.pem
```

## Performance Considerations

### Encryption Overhead

- **AES-256 encryption**: ~0.01ms per operation
- **100 shots encrypted**: < 1 second
- **Minimal impact** on sync performance

### Optimization Tips

1. **Batch operations**: Encrypt multiple items together when possible
2. **Async encryption**: Use background threads for large datasets
3. **Key caching**: Reuse encryption service instances
4. **Compression**: Consider compressing before encrypting for large payloads

## Compliance

This encryption implementation helps meet:

- **GDPR**: Data protection requirements
- **HIPAA**: If storing health-related data
- **PCI DSS**: If processing payment information
- **SOC 2**: Security controls for service organizations

## References

- [NIST AES Specification](https://csrc.nist.gov/publications/detail/fips/197/final)
- [TLS 1.3 RFC 8446](https://tools.ietf.org/html/rfc8446)
- [PBKDF2 RFC 2898](https://tools.ietf.org/html/rfc2898)
- [Cryptography Library Documentation](https://cryptography.io/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

## Support

For questions or issues:

1. Check this guide first
2. Review test files for examples
3. Check error logs for specific issues
4. Consult security team for production deployments
