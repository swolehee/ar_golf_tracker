"""Automatic hole transition detection service."""

from typing import Optional
from ar_golf_tracker.shared.models import GPSPosition


class HoleDetector:
    """Detects hole transitions based on GPS proximity to tee boxes."""
    
    def __init__(self, proximity_threshold_meters: float = 20.0):
        """Initialize hole detector.
        
        Args:
            proximity_threshold_meters: Distance threshold for tee box detection (default 20m)
        """
        self.proximity_threshold = proximity_threshold_meters
        self.current_course_id: Optional[str] = None
        self.current_hole_number: int = 1
        self.generic_mode: bool = False
    
    def set_course(self, course_id: Optional[str]) -> None:
        """Set the current course.
        
        Args:
            course_id: Course UUID, or None for generic mode
        """
        self.current_course_id = course_id
        self.generic_mode = (course_id is None)
        self.current_hole_number = 1
    
    def detect_hole_transition(
        self,
        current_position: GPSPosition,
        db_connection
    ) -> Optional[int]:
        """Detect if user has transitioned to a new hole.
        
        Args:
            current_position: Current GPS position
            db_connection: Database connection for spatial queries
        
        Returns:
            New hole number if transition detected, None otherwise
        """
        if self.generic_mode or self.current_course_id is None:
            # In generic mode, no automatic hole detection
            return None
        
        with db_connection.cursor() as cursor:
            # Use the database function to find current hole
            cursor.execute("""
                SELECT find_current_hole(%s, %s, %s, %s)
            """, (
                self.current_course_id,
                current_position.latitude,
                current_position.longitude,
                self.proximity_threshold
            ))
            
            result = cursor.fetchone()
            detected_hole = result[0] if result and result[0] is not None else None
            
            if detected_hole is not None and detected_hole != self.current_hole_number:
                # Hole transition detected
                return detected_hole
        
        return None
    
    def update_hole_number(self, hole_number: int) -> None:
        """Manually update the current hole number.
        
        Args:
            hole_number: New hole number
        """
        self.current_hole_number = hole_number
    
    def increment_hole(self) -> int:
        """Increment to the next hole.
        
        Returns:
            New hole number
        """
        self.current_hole_number += 1
        return self.current_hole_number
    
    def get_current_hole(self) -> int:
        """Get the current hole number.
        
        Returns:
            Current hole number
        """
        return self.current_hole_number
    
    def is_generic_mode(self) -> bool:
        """Check if operating in generic mode (no course data).
        
        Returns:
            True if in generic mode, False otherwise
        """
        return self.generic_mode
    
    def check_and_update_hole(
        self,
        current_position: GPSPosition,
        db_connection
    ) -> tuple[int, bool]:
        """Check for hole transition and update if detected.
        
        Args:
            current_position: Current GPS position
            db_connection: Database connection for spatial queries
        
        Returns:
            Tuple of (current_hole_number, transition_occurred)
        """
        new_hole = self.detect_hole_transition(current_position, db_connection)
        
        if new_hole is not None:
            self.current_hole_number = new_hole
            return (self.current_hole_number, True)
        
        return (self.current_hole_number, False)
