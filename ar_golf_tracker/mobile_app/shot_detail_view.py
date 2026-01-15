"""Shot detail view component for mobile app.

Displays detailed information about a selected shot when tapped on the map.
Provides filtering capabilities for shots by hole, club, and distance range.
"""

from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ShotFilter:
    """Represents shot filtering criteria."""
    hole_numbers: Optional[List[int]] = None
    club_types: Optional[List[str]] = None
    distance_range: Optional[Tuple[float, float]] = None
    
    def is_empty(self) -> bool:
        """Check if filter has no criteria set.
        
        Returns:
            True if no filters are active
        """
        return (self.hole_numbers is None and 
                self.club_types is None and 
                self.distance_range is None)
    
    def matches(self, shot_data: Dict[str, Any]) -> bool:
        """Check if shot matches filter criteria.
        
        Args:
            shot_data: Shot data dictionary
            
        Returns:
            True if shot matches all active filters
        """
        # Filter by hole number
        if self.hole_numbers is not None:
            if shot_data.get('hole_number') not in self.hole_numbers:
                return False
        
        # Filter by club type
        if self.club_types is not None:
            if shot_data.get('club_type') not in self.club_types:
                return False
        
        # Filter by distance range
        if self.distance_range is not None:
            distance = shot_data.get('distance_yards')
            if distance is None:
                return False
            min_dist, max_dist = self.distance_range
            if not (min_dist <= distance <= max_dist):
                return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            'hole_numbers': self.hole_numbers,
            'club_types': self.club_types,
            'distance_range': self.distance_range
        }


class ShotDetailView:
    """View component for displaying detailed shot information."""
    
    def __init__(self):
        """Initialize shot detail view."""
        self.selected_shot_id: Optional[str] = None
        self.selected_shot_data: Optional[Dict[str, Any]] = None
        self.all_shots: List[Dict[str, Any]] = []
        self.current_filter: ShotFilter = ShotFilter()
        self.on_filter_change: Optional[Callable[[ShotFilter], None]] = None
    
    def load_shots(self, shots_data: List[Dict[str, Any]]) -> None:
        """Load shot data.
        
        Args:
            shots_data: List of shot dictionaries
        """
        self.all_shots = shots_data
    
    def select_shot(self, shot_id: str) -> bool:
        """Select a shot to display details.
        
        Args:
            shot_id: Shot ID to select
            
        Returns:
            True if shot found and selected
        """
        for shot in self.all_shots:
            if shot['id'] == shot_id:
                self.selected_shot_id = shot_id
                self.selected_shot_data = shot
                return True
        return False
    
    def deselect_shot(self) -> None:
        """Deselect currently selected shot."""
        self.selected_shot_id = None
        self.selected_shot_data = None
    
    def get_selected_shot_details(self) -> Optional[Dict[str, Any]]:
        """Get detailed information about selected shot.
        
        Returns:
            Dictionary with formatted shot details or None
        """
        if not self.selected_shot_data:
            return None
        
        shot = self.selected_shot_data
        
        # Format timestamp
        time_str = ""
        if shot.get('shot_time'):
            try:
                dt = self._parse_datetime(shot['shot_time'])
                if dt:
                    time_str = dt.strftime("%I:%M:%S %p")
            except Exception:
                time_str = str(shot['shot_time'])
        
        # Format club name
        club_name = self._get_club_display_name(shot.get('club_type', ''))
        
        # Format distance
        distance_str = "N/A"
        if shot.get('distance_yards') is not None:
            distance_str = f"{int(shot['distance_yards'])} yards"
            if shot.get('distance_accuracy'):
                distance_str += f" ({shot['distance_accuracy']})"
        
        # Format GPS accuracy
        gps_accuracy_str = "N/A"
        if shot.get('gps_accuracy') is not None:
            accuracy = shot['gps_accuracy']
            if accuracy < 10:
                level = "High"
            elif accuracy < 20:
                level = "Medium"
            else:
                level = "Low"
            gps_accuracy_str = f"{level} ({int(accuracy)}m)"
        
        return {
            'shot_id': shot['id'],
            'hole_number': shot.get('hole_number'),
            'swing_number': shot.get('swing_number'),
            'club': club_name,
            'club_type': shot.get('club_type'),
            'timestamp': time_str,
            'distance': distance_str,
            'distance_yards': shot.get('distance_yards'),
            'distance_accuracy': shot.get('distance_accuracy'),
            'gps_location': {
                'latitude': shot.get('gps_lat'),
                'longitude': shot.get('gps_lon'),
                'altitude': shot.get('gps_altitude'),
                'accuracy': gps_accuracy_str
            },
            'notes': shot.get('notes')
        }
    
    def set_filter(self, hole_numbers: Optional[List[int]] = None,
                   club_types: Optional[List[str]] = None,
                   distance_range: Optional[Tuple[float, float]] = None) -> None:
        """Set shot filter criteria.
        
        Args:
            hole_numbers: List of hole numbers to show (None = all)
            club_types: List of club types to show (None = all)
            distance_range: Tuple of (min, max) distance in yards (None = all)
        """
        self.current_filter = ShotFilter(
            hole_numbers=hole_numbers,
            club_types=club_types,
            distance_range=distance_range
        )
        
        # Notify callback if registered
        if self.on_filter_change:
            self.on_filter_change(self.current_filter)
    
    def clear_filter(self) -> None:
        """Clear all shot filters."""
        self.current_filter = ShotFilter()
        
        # Notify callback if registered
        if self.on_filter_change:
            self.on_filter_change(self.current_filter)
    
    def get_current_filter(self) -> ShotFilter:
        """Get current filter settings.
        
        Returns:
            Current shot filter
        """
        return self.current_filter
    
    def get_filtered_shots(self) -> List[Dict[str, Any]]:
        """Get shots that match current filter.
        
        Returns:
            List of filtered shot dictionaries
        """
        if self.current_filter.is_empty():
            return self.all_shots
        
        return [shot for shot in self.all_shots if self.current_filter.matches(shot)]
    
    def get_filtered_shot_count(self) -> int:
        """Get count of shots matching current filter.
        
        Returns:
            Number of filtered shots
        """
        return len(self.get_filtered_shots())
    
    def get_available_holes(self) -> List[int]:
        """Get list of hole numbers that have shots.
        
        Returns:
            Sorted list of hole numbers
        """
        holes = set()
        for shot in self.all_shots:
            if shot.get('hole_number') is not None:
                holes.add(shot['hole_number'])
        return sorted(list(holes))
    
    def get_available_clubs(self) -> List[str]:
        """Get list of club types that have been used.
        
        Returns:
            Sorted list of club types
        """
        clubs = set()
        for shot in self.all_shots:
            if shot.get('club_type'):
                clubs.add(shot['club_type'])
        return sorted(list(clubs))
    
    def get_distance_range(self) -> Optional[Tuple[float, float]]:
        """Get min and max distances from all shots.
        
        Returns:
            Tuple of (min, max) distance or None if no distances
        """
        distances = [
            shot['distance_yards'] 
            for shot in self.all_shots 
            if shot.get('distance_yards') is not None
        ]
        
        if not distances:
            return None
        
        return (min(distances), max(distances))
    
    def filter_by_hole(self, hole_numbers: List[int]) -> None:
        """Filter shots by hole numbers.
        
        Args:
            hole_numbers: List of hole numbers to show
        """
        self.set_filter(
            hole_numbers=hole_numbers,
            club_types=self.current_filter.club_types,
            distance_range=self.current_filter.distance_range
        )
    
    def filter_by_club(self, club_types: List[str]) -> None:
        """Filter shots by club types.
        
        Args:
            club_types: List of club types to show
        """
        self.set_filter(
            hole_numbers=self.current_filter.hole_numbers,
            club_types=club_types,
            distance_range=self.current_filter.distance_range
        )
    
    def filter_by_distance(self, min_distance: float, max_distance: float) -> None:
        """Filter shots by distance range.
        
        Args:
            min_distance: Minimum distance in yards
            max_distance: Maximum distance in yards
        """
        self.set_filter(
            hole_numbers=self.current_filter.hole_numbers,
            club_types=self.current_filter.club_types,
            distance_range=(min_distance, max_distance)
        )
    
    def set_on_filter_change_callback(self, callback: Callable[[ShotFilter], None]) -> None:
        """Set callback for when filter changes.
        
        Args:
            callback: Function to call with new filter when it changes
        """
        self.on_filter_change = callback
    
    def get_shots_by_hole(self, hole_number: int) -> List[Dict[str, Any]]:
        """Get all shots on a specific hole.
        
        Args:
            hole_number: Hole number
            
        Returns:
            List of shots on that hole
        """
        return [
            shot for shot in self.all_shots 
            if shot.get('hole_number') == hole_number
        ]
    
    def get_shots_by_club(self, club_type: str) -> List[Dict[str, Any]]:
        """Get all shots with a specific club.
        
        Args:
            club_type: Club type (e.g., "DRIVER", "IRON_7")
            
        Returns:
            List of shots with that club
        """
        return [
            shot for shot in self.all_shots 
            if shot.get('club_type') == club_type
        ]
    
    def get_shots_in_distance_range(self, min_distance: float, 
                                    max_distance: float) -> List[Dict[str, Any]]:
        """Get all shots within a distance range.
        
        Args:
            min_distance: Minimum distance in yards
            max_distance: Maximum distance in yards
            
        Returns:
            List of shots in that range
        """
        return [
            shot for shot in self.all_shots 
            if shot.get('distance_yards') is not None
            and min_distance <= shot['distance_yards'] <= max_distance
        ]
    
    def _parse_datetime(self, dt_value: Any) -> Optional[datetime]:
        """Parse datetime from various formats.
        
        Args:
            dt_value: Datetime value (string, datetime, or None)
            
        Returns:
            Parsed datetime or None
        """
        if dt_value is None:
            return None
        if isinstance(dt_value, datetime):
            return dt_value
        if isinstance(dt_value, str):
            try:
                return datetime.fromisoformat(dt_value.replace('Z', '+00:00'))
            except ValueError:
                pass
        return None
    
    def _get_club_display_name(self, club_type: str) -> str:
        """Get human-readable club name.
        
        Args:
            club_type: Club type code
            
        Returns:
            Club display name
        """
        club_names = {
            'DRIVER': 'Driver',
            'WOOD_3': '3 Wood',
            'WOOD_5': '5 Wood',
            'HYBRID_3': '3 Hybrid',
            'HYBRID_4': '4 Hybrid',
            'HYBRID_5': '5 Hybrid',
            'IRON_3': '3 Iron',
            'IRON_4': '4 Iron',
            'IRON_5': '5 Iron',
            'IRON_6': '6 Iron',
            'IRON_7': '7 Iron',
            'IRON_8': '8 Iron',
            'IRON_9': '9 Iron',
            'PITCHING_WEDGE': 'Pitching Wedge',
            'SAND_WEDGE': 'Sand Wedge',
            'LOB_WEDGE': 'Lob Wedge',
            'PUTTER': 'Putter'
        }
        return club_names.get(club_type, club_type)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert view state to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            'selected_shot': self.get_selected_shot_details(),
            'current_filter': self.current_filter.to_dict(),
            'filtered_shot_count': self.get_filtered_shot_count(),
            'total_shot_count': len(self.all_shots),
            'available_holes': self.get_available_holes(),
            'available_clubs': self.get_available_clubs(),
            'distance_range': self.get_distance_range()
        }
