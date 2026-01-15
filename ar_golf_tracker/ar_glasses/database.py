"""SQLite database utilities for AR glasses local storage."""

import sqlite3
import json
import time
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from ar_golf_tracker.shared.models import (
    Shot, Round, GPSPosition, Distance, ClubType,
    DistanceUnit, DistanceAccuracy, SyncStatus, WeatherConditions
)


class LocalDatabase:
    """Manages SQLite database for local shot storage on AR glasses."""
    
    def __init__(self, db_path: str = "ar_golf_tracker.db", check_same_thread: bool = True):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
            check_same_thread: If False, allows connection to be used across threads
        """
        self.db_path = db_path
        self.check_same_thread = check_same_thread
        self.connection: Optional[sqlite3.Connection] = None
    
    def connect(self) -> sqlite3.Connection:
        """Establish database connection.
        
        Returns:
            SQLite connection object
        """
        if self.connection is None:
            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=self.check_same_thread
            )
            self.connection.row_factory = sqlite3.Row
        return self.connection
    
    def initialize_schema(self) -> None:
        """Create database tables from schema file."""
        schema_path = Path(__file__).parent / "schema.sql"
        
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        conn = self.connect()
        conn.executescript(schema_sql)
        conn.commit()
    
    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def __enter__(self) -> 'LocalDatabase':
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
    
    # Shot operations with GPS data
    
    def create_shot(self, shot: Shot) -> None:
        """Create a new shot record with GPS position.
        
        Args:
            shot: Shot object to store
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO shots (
                id, round_id, hole_number, swing_number, club_type,
                timestamp, gps_lat, gps_lon, gps_accuracy, gps_altitude,
                gps_timestamp, distance_value, distance_unit, distance_accuracy,
                notes, sync_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            shot.id,
            shot.round_id,
            shot.hole_number,
            shot.swing_number,
            shot.club_type.value,
            shot.timestamp,
            shot.gps_origin.latitude,
            shot.gps_origin.longitude,
            shot.gps_origin.accuracy,
            shot.gps_origin.altitude,
            shot.gps_origin.timestamp,
            shot.distance.value if shot.distance else None,
            shot.distance.unit.value if shot.distance else None,
            shot.distance.accuracy.value if shot.distance else None,
            shot.notes,
            shot.sync_status.value
        ))
        
        conn.commit()
    
    def get_shot(self, shot_id: str) -> Optional[Shot]:
        """Retrieve a shot by ID.
        
        Args:
            shot_id: Shot identifier
            
        Returns:
            Shot object or None if not found
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM shots WHERE id = ?", (shot_id,))
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return self._row_to_shot(row)
    
    def get_shots_by_round(self, round_id: str) -> List[Shot]:
        """Retrieve all shots for a round.
        
        Args:
            round_id: Round identifier
            
        Returns:
            List of Shot objects
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM shots WHERE round_id = ? ORDER BY hole_number, swing_number",
            (round_id,)
        )
        
        return [self._row_to_shot(row) for row in cursor.fetchall()]
    
    def get_shots_by_hole(self, round_id: str, hole_number: int) -> List[Shot]:
        """Retrieve all shots for a specific hole.
        
        Args:
            round_id: Round identifier
            hole_number: Hole number
            
        Returns:
            List of Shot objects ordered by swing number
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT * FROM shots 
               WHERE round_id = ? AND hole_number = ? 
               ORDER BY swing_number""",
            (round_id, hole_number)
        )
        
        return [self._row_to_shot(row) for row in cursor.fetchall()]
    
    def update_shot(self, shot: Shot) -> None:
        """Update an existing shot record.
        
        Args:
            shot: Shot object with updated data
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE shots SET
                hole_number = ?,
                swing_number = ?,
                club_type = ?,
                timestamp = ?,
                gps_lat = ?,
                gps_lon = ?,
                gps_accuracy = ?,
                gps_altitude = ?,
                gps_timestamp = ?,
                distance_value = ?,
                distance_unit = ?,
                distance_accuracy = ?,
                notes = ?,
                sync_status = ?
            WHERE id = ?
        """, (
            shot.hole_number,
            shot.swing_number,
            shot.club_type.value,
            shot.timestamp,
            shot.gps_origin.latitude,
            shot.gps_origin.longitude,
            shot.gps_origin.accuracy,
            shot.gps_origin.altitude,
            shot.gps_origin.timestamp,
            shot.distance.value if shot.distance else None,
            shot.distance.unit.value if shot.distance else None,
            shot.distance.accuracy.value if shot.distance else None,
            shot.notes,
            shot.sync_status.value,
            shot.id
        ))
        
        conn.commit()
    
    def delete_shot(self, shot_id: str) -> None:
        """Delete a shot record.
        
        Args:
            shot_id: Shot identifier
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM shots WHERE id = ?", (shot_id,))
        conn.commit()
    
    # Round operations
    
    def create_round(self, round_obj: Round) -> None:
        """Create a new round record.
        
        Args:
            round_obj: Round object to store
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO rounds (
                id, user_id, course_id, course_name, start_time, end_time,
                weather_temperature, weather_wind_speed, weather_wind_direction,
                weather_conditions, sync_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            round_obj.id,
            round_obj.user_id,
            round_obj.course_id,
            round_obj.course_name,
            round_obj.start_time,
            round_obj.end_time,
            round_obj.weather.temperature if round_obj.weather else None,
            round_obj.weather.wind_speed if round_obj.weather else None,
            round_obj.weather.wind_direction if round_obj.weather else None,
            round_obj.weather.conditions if round_obj.weather else None,
            round_obj.sync_status.value
        ))
        
        conn.commit()
    
    def get_round(self, round_id: str) -> Optional[Round]:
        """Retrieve a round by ID with all shots.
        
        Args:
            round_id: Round identifier
            
        Returns:
            Round object with shots or None if not found
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM rounds WHERE id = ?", (round_id,))
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        round_obj = self._row_to_round(row)
        round_obj.shots = self.get_shots_by_round(round_id)
        
        return round_obj
    
    def update_round(self, round_obj: Round) -> None:
        """Update an existing round record.
        
        Args:
            round_obj: Round object with updated data
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE rounds SET
                course_id = ?,
                course_name = ?,
                start_time = ?,
                end_time = ?,
                weather_temperature = ?,
                weather_wind_speed = ?,
                weather_wind_direction = ?,
                weather_conditions = ?,
                sync_status = ?
            WHERE id = ?
        """, (
            round_obj.course_id,
            round_obj.course_name,
            round_obj.start_time,
            round_obj.end_time,
            round_obj.weather.temperature if round_obj.weather else None,
            round_obj.weather.wind_speed if round_obj.weather else None,
            round_obj.weather.wind_direction if round_obj.weather else None,
            round_obj.weather.conditions if round_obj.weather else None,
            round_obj.sync_status.value,
            round_obj.id
        ))
        
        conn.commit()
    
    def delete_round(self, round_id: str) -> None:
        """Delete a round and all associated shots.
        
        Args:
            round_id: Round identifier
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        # Shots will be deleted automatically due to CASCADE
        cursor.execute("DELETE FROM rounds WHERE id = ?", (round_id,))
        conn.commit()
    
    # Helper methods for row conversion
    
    def _row_to_shot(self, row: sqlite3.Row) -> Shot:
        """Convert database row to Shot object.
        
        Args:
            row: SQLite row object
            
        Returns:
            Shot object
        """
        gps_position = GPSPosition(
            latitude=row['gps_lat'],
            longitude=row['gps_lon'],
            accuracy=row['gps_accuracy'],
            timestamp=row['gps_timestamp'],
            altitude=row['gps_altitude']
        )
        
        distance = None
        if row['distance_value'] is not None:
            distance = Distance(
                value=row['distance_value'],
                unit=DistanceUnit(row['distance_unit']),
                accuracy=DistanceAccuracy(row['distance_accuracy'])
            )
        
        return Shot(
            id=row['id'],
            round_id=row['round_id'],
            hole_number=row['hole_number'],
            swing_number=row['swing_number'],
            club_type=ClubType(row['club_type']),
            timestamp=row['timestamp'],
            gps_origin=gps_position,
            distance=distance,
            notes=row['notes'],
            sync_status=SyncStatus(row['sync_status'])
        )
    
    def _row_to_round(self, row: sqlite3.Row) -> Round:
        """Convert database row to Round object.
        
        Args:
            row: SQLite row object
            
        Returns:
            Round object (without shots)
        """
        weather = None
        if row['weather_temperature'] is not None:
            weather = WeatherConditions(
                temperature=row['weather_temperature'],
                wind_speed=row['weather_wind_speed'],
                wind_direction=row['weather_wind_direction'],
                conditions=row['weather_conditions']
            )
        
        return Round(
            id=row['id'],
            user_id=row['user_id'],
            course_id=row['course_id'],
            course_name=row['course_name'],
            start_time=row['start_time'],
            end_time=row['end_time'],
            weather=weather,
            sync_status=SyncStatus(row['sync_status']),
            shots=[]  # Shots loaded separately
        )
    
    # Sync queue operations
    
    def enqueue_sync(
        self,
        entity_type: str,
        entity_id: str,
        operation: str,
        payload: Dict[str, Any]
    ) -> str:
        """Add an operation to the sync queue.
        
        Args:
            entity_type: Type of entity ('ROUND' or 'SHOT')
            entity_id: ID of the entity
            operation: Operation type ('CREATE', 'UPDATE', 'DELETE')
            payload: JSON-serializable entity data
            
        Returns:
            Queue entry ID
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        queue_id = str(uuid.uuid4())
        payload_json = json.dumps(payload)
        
        cursor.execute("""
            INSERT INTO sync_queue (
                id, entity_type, entity_id, operation, payload, retry_count
            ) VALUES (?, ?, ?, ?, ?, 0)
        """, (queue_id, entity_type, entity_id, operation, payload_json))
        
        conn.commit()
        return queue_id
    
    def get_pending_sync_items(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve pending sync queue items.
        
        Args:
            limit: Maximum number of items to retrieve
            
        Returns:
            List of sync queue items as dictionaries
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM sync_queue
            ORDER BY created_at ASC
            LIMIT ?
        """, (limit,))
        
        items = []
        for row in cursor.fetchall():
            items.append({
                'id': row['id'],
                'entity_type': row['entity_type'],
                'entity_id': row['entity_id'],
                'operation': row['operation'],
                'payload': json.loads(row['payload']),
                'retry_count': row['retry_count'],
                'last_retry_at': row['last_retry_at'],
                'created_at': row['created_at']
            })
        
        return items
    
    def update_sync_retry(self, queue_id: str) -> None:
        """Update retry count and timestamp for a sync queue item.
        
        Args:
            queue_id: Sync queue entry ID
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        current_time = int(time.time())
        
        cursor.execute("""
            UPDATE sync_queue
            SET retry_count = retry_count + 1,
                last_retry_at = ?
            WHERE id = ?
        """, (current_time, queue_id))
        
        conn.commit()
    
    def remove_from_sync_queue(self, queue_id: str) -> None:
        """Remove a successfully synced item from the queue.
        
        Args:
            queue_id: Sync queue entry ID
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM sync_queue WHERE id = ?", (queue_id,))
        conn.commit()
    
    def get_sync_queue_size(self) -> int:
        """Get the number of items in the sync queue.
        
        Returns:
            Number of pending sync items
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM sync_queue")
        row = cursor.fetchone()
        
        return row['count'] if row else 0
    
    def clear_old_sync_items(self, max_retries: int = 5) -> int:
        """Remove sync items that have exceeded max retry attempts.
        
        Args:
            max_retries: Maximum number of retry attempts before removal
            
        Returns:
            Number of items removed
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM sync_queue
            WHERE retry_count >= ?
        """, (max_retries,))
        
        removed_count = cursor.rowcount
        conn.commit()
        
        return removed_count
    
    def get_shots_by_sync_status(self, sync_status: SyncStatus) -> List[Shot]:
        """Retrieve shots by sync status.
        
        Args:
            sync_status: Sync status to filter by
            
        Returns:
            List of Shot objects
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM shots WHERE sync_status = ? ORDER BY timestamp",
            (sync_status.value,)
        )
        
        return [self._row_to_shot(row) for row in cursor.fetchall()]
    
    def get_rounds_by_sync_status(self, sync_status: SyncStatus) -> List[Round]:
        """Retrieve rounds by sync status.
        
        Args:
            sync_status: Sync status to filter by
            
        Returns:
            List of Round objects (without shots)
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM rounds WHERE sync_status = ? ORDER BY start_time",
            (sync_status.value,)
        )
        
        return [self._row_to_round(row) for row in cursor.fetchall()]
    
    def update_shot_sync_status(self, shot_id: str, sync_status: SyncStatus) -> None:
        """Update the sync status of a shot.
        
        Args:
            shot_id: Shot identifier
            sync_status: New sync status
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE shots
            SET sync_status = ?
            WHERE id = ?
        """, (sync_status.value, shot_id))
        
        conn.commit()
    
    def update_round_sync_status(self, round_id: str, sync_status: SyncStatus) -> None:
        """Update the sync status of a round.
        
        Args:
            round_id: Round identifier
            sync_status: New sync status
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE rounds
            SET sync_status = ?
            WHERE id = ?
        """, (sync_status.value, round_id))
        
        conn.commit()
