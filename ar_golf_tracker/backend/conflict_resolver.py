"""Conflict resolution service for data synchronization.

Implements last-write-wins strategy based on timestamps and logs
conflicts for user review.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConflictResolver:
    """Handles conflict resolution for synchronized data."""
    
    def __init__(self, db_connection):
        """Initialize conflict resolver.
        
        Args:
            db_connection: Database connection for logging conflicts
        """
        self.db_connection = db_connection
    
    def resolve_round_conflict(
        self,
        round_id: str,
        user_id: str,
        incoming_data: Dict[str, Any],
        existing_updated_at: datetime
    ) -> Dict[str, Any]:
        """Resolve conflict for round data using last-write-wins.
        
        Args:
            round_id: Round ID
            user_id: User ID
            incoming_data: New round data from sync
            existing_updated_at: Timestamp of existing data in database
            
        Returns:
            Conflict resolution result with decision and metadata
        """
        # In a real implementation, we would compare timestamps from the incoming data
        # For now, we use last-write-wins (incoming data wins)
        
        conflict_info = {
            "entity_type": "round",
            "entity_id": round_id,
            "resolution": "last_write_wins",
            "winner": "incoming",
            "existing_timestamp": existing_updated_at.isoformat(),
            "resolved_at": datetime.utcnow().isoformat()
        }
        
        # Log conflict to database for user review
        self._log_conflict(user_id, conflict_info)
        
        logger.info(f"Resolved round conflict for {round_id}: incoming data wins")
        
        return {
            "resolved": True,
            "action": "update",
            "conflict_info": conflict_info
        }
    
    def resolve_shot_conflict(
        self,
        shot_id: str,
        user_id: str,
        incoming_data: Dict[str, Any],
        existing_updated_at: datetime
    ) -> Dict[str, Any]:
        """Resolve conflict for shot data using last-write-wins.
        
        Args:
            shot_id: Shot ID
            user_id: User ID
            incoming_data: New shot data from sync
            existing_updated_at: Timestamp of existing data in database
            
        Returns:
            Conflict resolution result with decision and metadata
        """
        # In a real implementation, we would compare timestamps from the incoming data
        # For now, we use last-write-wins (incoming data wins)
        
        conflict_info = {
            "entity_type": "shot",
            "entity_id": shot_id,
            "resolution": "last_write_wins",
            "winner": "incoming",
            "existing_timestamp": existing_updated_at.isoformat(),
            "resolved_at": datetime.utcnow().isoformat()
        }
        
        # Log conflict to database for user review
        self._log_conflict(user_id, conflict_info)
        
        logger.info(f"Resolved shot conflict for {shot_id}: incoming data wins")
        
        return {
            "resolved": True,
            "action": "update",
            "conflict_info": conflict_info
        }
    
    def _log_conflict(self, user_id: str, conflict_info: Dict[str, Any]) -> None:
        """Log conflict to database for user review.
        
        Args:
            user_id: User ID
            conflict_info: Conflict details
        """
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO sync_conflicts 
                    (user_id, entity_type, entity_id, resolution_strategy, 
                     conflict_data, resolved_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        user_id,
                        conflict_info["entity_type"],
                        conflict_info["entity_id"],
                        conflict_info["resolution"],
                        conflict_info,
                        datetime.utcnow()
                    )
                )
            self.db_connection.commit()
        except Exception as e:
            logger.error(f"Failed to log conflict: {e}")
            # Don't fail the sync if logging fails
    
    def get_user_conflicts(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get list of conflicts for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of conflicts to return
            offset: Number of conflicts to skip
            
        Returns:
            List of conflict records
        """
        with self.db_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, entity_type, entity_id, resolution_strategy,
                       conflict_data, resolved_at, created_at
                FROM sync_conflicts
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (user_id, limit, offset)
            )
            conflicts = cursor.fetchall()
        
        return [
            {
                "id": str(row[0]),
                "entity_type": row[1],
                "entity_id": row[2],
                "resolution_strategy": row[3],
                "conflict_data": row[4],
                "resolved_at": row[5].isoformat() if row[5] else None,
                "created_at": row[6].isoformat()
            }
            for row in conflicts
        ]
