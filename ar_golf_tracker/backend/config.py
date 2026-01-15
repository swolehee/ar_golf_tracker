"""Configuration for AR Golf Tracker backend API.

Includes TLS 1.3 configuration and security settings.
"""

import os
from typing import Optional


class APIConfig:
    """Configuration for the API server."""
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # TLS/SSL Configuration
    SSL_ENABLED: bool = os.getenv("SSL_ENABLED", "false").lower() == "true"
    SSL_CERTFILE: Optional[str] = os.getenv("SSL_CERTFILE")
    SSL_KEYFILE: Optional[str] = os.getenv("SSL_KEYFILE")
    
    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "ar_golf_tracker")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    
    # CORS
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")
    
    @classmethod
    def get_ssl_config(cls) -> dict:
        """Get SSL configuration for Uvicorn server.
        
        Returns:
            Dictionary with SSL configuration or empty dict if SSL disabled
        """
        if not cls.SSL_ENABLED or not cls.SSL_CERTFILE or not cls.SSL_KEYFILE:
            return {}
        
        import ssl
        
        return {
            'ssl_keyfile': cls.SSL_KEYFILE,
            'ssl_certfile': cls.SSL_CERTFILE,
            'ssl_version': ssl.PROTOCOL_TLS_SERVER,
            'ssl_cert_reqs': ssl.CERT_NONE,
            # TLS 1.3 cipher suites
            'ssl_ciphers': 'TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_128_GCM_SHA256'
        }
    
    @classmethod
    def validate_config(cls) -> None:
        """Validate configuration settings.
        
        Raises:
            ValueError: If configuration is invalid
        """
        if cls.SSL_ENABLED:
            if not cls.SSL_CERTFILE:
                raise ValueError("SSL_CERTFILE must be set when SSL_ENABLED is true")
            if not cls.SSL_KEYFILE:
                raise ValueError("SSL_KEYFILE must be set when SSL_ENABLED is true")
            
            # Check if files exist
            if not os.path.exists(cls.SSL_CERTFILE):
                raise ValueError(f"SSL certificate file not found: {cls.SSL_CERTFILE}")
            if not os.path.exists(cls.SSL_KEYFILE):
                raise ValueError(f"SSL key file not found: {cls.SSL_KEYFILE}")
