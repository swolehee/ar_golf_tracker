"""Shot management service with automatic distance calculation."""

from typing import Optional
from ar_golf_tracker.shared.models import (
    Shot, GPSPosition, ClubType, DistanceUnit, SyncStatus
)
from ar_golf_tracker.ar_glasses.database import LocalDatabase
from ar_golf_tracker.ar_glasses.distance_calculator import DistanceCalculationService


class ShotManager:
    """Manages shot recording with automatic distance calculation."""
    
    def __init__(
        self,
        database: LocalDatabase,
        distance_calculator: Optional[DistanceCalculationService] = None,
        distance_unit: DistanceUnit = DistanceUnit.YARDS
    ):
        """Initialize shot manager.
        
        Args:
            database: Local database for shot storage
            distance_calculator: Distance calculation service (creates default if None)
            distance_unit: Default unit for distance calculations
        """
        self.database = database
        self.distance_calculator = distance_calculator or DistanceCalculationService(
            default_unit=distance_unit
        )
    
    def record_shot(
        self,
        round_id: str,
        hole_number: int,
        club_type: ClubType,
        gps_position: GPSPosition,
        shot_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Shot:
        """Record a new shot with automatic distance calculation.
        
        This method:
        1. Retrieves the previous shot on the same hole (if any)
        2. Calculates distance from previous shot to current shot
        3. Updates the previous shot with the calculated distance
        4. Creates and stores the new shot record
        
        Args:
            round_id: Round identifier
            hole_number: Current hole number
            club_type: Club used for the shot
            gps_position: GPS position where shot was taken
            shot_id: Optional shot ID (generates UUID if None)
            notes: Optional notes about the shot
            
        Returns:
            Created Shot object
        """
        import uuid
        import time
        
        # Generate shot ID if not provided
        if shot_id is None:
            shot_id = str(uuid.uuid4())
        
        # Get previous shot on same hole
        previous_shot = self.get_last_shot_on_hole(round_id, hole_number)
        
        # Calculate and update distance for previous shot
        if previous_shot is not None:
            distance = self.distance_calculator.calculate_distance(
                from_position=previous_shot.gps_origin,
                to_position=gps_position
            )
            
            # Update previous shot with calculated distance
            previous_shot.distance = distance
            self.database.update_shot(previous_shot)
        
        # Determine swing number (increment from previous shot or start at 1)
        swing_number = 1
        if previous_shot is not None:
            swing_number = previous_shot.swing_number + 1
        
        # Create new shot record
        new_shot = Shot(
            id=shot_id,
            round_id=round_id,
            hole_number=hole_number,
            swing_number=swing_number,
            club_type=club_type,
            timestamp=int(time.time()),
            gps_origin=gps_position,
            distance=None,  # Distance will be calculated when next shot is recorded
            notes=notes,
            sync_status=SyncStatus.PENDING
        )
        
        # Store new shot
        self.database.create_shot(new_shot)
        
        return new_shot
    
    def get_last_shot_on_hole(
        self,
        round_id: str,
        hole_number: int
    ) -> Optional[Shot]:
        """Get the most recent shot on a specific hole.
        
        Args:
            round_id: Round identifier
            hole_number: Hole number
            
        Returns:
            Most recent Shot on the hole or None if no shots exist
        """
        shots = self.database.get_shots_by_hole(round_id, hole_number)
        
        if not shots:
            return None
        
        # Shots are already ordered by swing_number from database query
        return shots[-1]
    
    def update_shot_distance(
        self,
        shot_id: str,
        to_position: GPSPosition
    ) -> Optional[Shot]:
        """Manually update a shot's distance to a specific position.
        
        This can be used to recalculate distance if GPS position is corrected
        or to calculate distance to a specific target (e.g., pin position).
        
        Args:
            shot_id: Shot identifier
            to_position: Target GPS position
            
        Returns:
            Updated Shot object or None if shot not found
        """
        shot = self.database.get_shot(shot_id)
        
        if shot is None:
            return None
        
        # Calculate distance
        distance = self.distance_calculator.calculate_distance(
            from_position=shot.gps_origin,
            to_position=to_position
        )
        
        # Update shot
        shot.distance = distance
        self.database.update_shot(shot)
        
        return shot
    
    def get_shot(self, shot_id: str) -> Optional[Shot]:
        """Retrieve a shot by ID.
        
        Args:
            shot_id: Shot identifier
            
        Returns:
            Shot object or None if not found
        """
        return self.database.get_shot(shot_id)
    
    def get_shots_by_round(self, round_id: str) -> list[Shot]:
        """Retrieve all shots for a round.
        
        Args:
            round_id: Round identifier
            
        Returns:
            List of Shot objects
        """
        return self.database.get_shots_by_round(round_id)
    
    def get_shots_by_hole(self, round_id: str, hole_number: int) -> list[Shot]:
        """Retrieve all shots for a specific hole.
        
        Args:
            round_id: Round identifier
            hole_number: Hole number
            
        Returns:
            List of Shot objects ordered by swing number
        """
        return self.database.get_shots_by_hole(round_id, hole_number)
    
    def delete_shot(self, shot_id: str) -> None:
        """Delete a shot record.
        
        Args:
            shot_id: Shot identifier
        """
        self.database.delete_shot(shot_id)
