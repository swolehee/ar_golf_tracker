"""Server startup script for AR Golf Tracker API with TLS 1.3 support.

This script starts the FastAPI server with optional TLS 1.3 encryption.
"""

import uvicorn
import logging
from .config import APIConfig


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def start_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
    workers: int = 1
) -> None:
    """Start the API server with TLS 1.3 support.
    
    Args:
        host: Host address to bind to
        port: Port to listen on
        reload: Enable auto-reload for development
        workers: Number of worker processes
    """
    # Validate configuration
    try:
        APIConfig.validate_config()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
    
    # Get SSL configuration
    ssl_config = APIConfig.get_ssl_config()
    
    if ssl_config:
        logger.info("Starting server with TLS 1.3 encryption enabled")
        logger.info(f"Certificate: {APIConfig.SSL_CERTFILE}")
        logger.info(f"Key: {APIConfig.SSL_KEYFILE}")
    else:
        logger.warning("Starting server WITHOUT TLS encryption (development mode)")
        logger.warning("For production, set SSL_ENABLED=true and provide certificate files")
    
    # Server configuration
    config = {
        "app": "ar_golf_tracker.backend.api:app",
        "host": host,
        "port": port,
        "reload": reload,
        "workers": workers,
        "log_level": "info",
    }
    
    # Add SSL configuration if enabled
    config.update(ssl_config)
    
    # Start server
    logger.info(f"Server starting on {host}:{port}")
    uvicorn.run(**config)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Start AR Golf Tracker API server")
    parser.add_argument("--host", default="0.0.0.0", help="Host address")
    parser.add_argument("--port", type=int, default=8000, help="Port number")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers")
    
    args = parser.parse_args()
    
    start_server(
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers
    )
