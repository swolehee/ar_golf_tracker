"""PostgreSQL database utilities for cloud backend."""

import psycopg2
from psycopg2.extensions import connection as Connection
from pathlib import Path
from typing import Optional


class CloudDatabase:
    """Manages PostgreSQL database connection for cloud backend."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "ar_golf_tracker",
        user: str = "postgres",
        password: str = ""
    ):
        """Initialize database connection parameters.
        
        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection: Optional[Connection] = None
    
    def connect(self) -> Connection:
        """Establish database connection.
        
        Returns:
            PostgreSQL connection object
        """
        if self.connection is None or self.connection.closed:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
        return self.connection
    
    def initialize_schema(self) -> None:
        """Create database tables and PostGIS extension from schema file."""
        schema_path = Path(__file__).parent / "schema.sql"
        
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        conn = self.connect()
        with conn.cursor() as cursor:
            cursor.execute(schema_sql)
        conn.commit()
    
    def close(self) -> None:
        """Close database connection."""
        if self.connection and not self.connection.closed:
            self.connection.close()
    
    def __enter__(self) -> 'CloudDatabase':
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
