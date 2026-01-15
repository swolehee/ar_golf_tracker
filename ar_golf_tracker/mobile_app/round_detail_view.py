"""Round detail view component for mobile app.

Displays detailed information about a selected round including shots,
course information, and statistics.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict


class ShotDetail:
    """Represents detailed shot information."""
    
    def __init__(self, shot_data: Dict[str, Any]):
        """Initialize shot detail.
        
        Args:
            shot_data: Shot data from API
        """
        self.id = shot_data['id']
        self.round_id = shot_data['round_id']
        self.hole_number = shot_data['hole_number']
        self.swing_number = shot_data['swing_number']
        self.club_type = shot_data['club_type']
        self.shot_time = self._parse_datetime(shot_data['shot_time'])
        self.gps_lat = shot_data['gps_lat']
        self.gps_lon = shot_data['gps_lon']
        self.gps_accuracy = shot_data['gps_accuracy']
        self.gps_altitude = shot_data.get('gps_altitude')
        self.distance_yards = shot_data.get('distance_yards')
        self.distance_accuracy = shot_data.get('distance_accuracy')
        self.notes = shot_data.get('notes')
    
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
    
    def get_time_string(self) -> str:
        """Get formatted time string.
        
        Returns:
            Formatted time (e.g., "2:30:45 PM")
        """
        if self.shot_time:
            return self.shot_time.strftime("%I:%M:%S %p")
        return ""
    
    def get_club_display_name(self) -> str:
        """Get human-readable club name.
        
        Returns:
            Club display name (e.g., "Driver", "7 Iron")
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
        return club_names.get(self.club_type, self.club_type)
    
    def get_distance_string(self) -> str:
        """Get formatted distance string.
        
        Returns:
            Distance string (e.g., "250 yards") or "N/A"
        """
        if self.distance_yards is not None:
            return f"{int(self.distance_yards)} yards"
        return "N/A"
    
    def get_gps_accuracy_string(self) -> str:
        """Get GPS accuracy description.
        
        Returns:
            Accuracy description (e.g., "High (5m)")
        """
        if self.gps_accuracy < 10:
            level = "High"
        elif self.gps_accuracy < 20:
            level = "Medium"
        else:
            level = "Low"
        return f"{level} ({int(self.gps_accuracy)}m)"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            'id': self.id,
            'hole_number': self.hole_number,
            'swing_number': self.swing_number,
            'club': self.get_club_display_name(),
            'club_type': self.club_type,
            'time': self.get_time_string(),
            'distance': self.get_distance_string(),
            'distance_yards': self.distance_yards,
            'distance_accuracy': self.distance_accuracy,
            'gps_lat': self.gps_lat,
            'gps_lon': self.gps_lon,
            'gps_accuracy': self.get_gps_accuracy_string(),
            'altitude': self.gps_altitude,
            'notes': self.notes
        }


class HoleDetail:
    """Represents detailed hole information with shots."""
    
    def __init__(self, hole_number: int, shots: List[ShotDetail]):
        """Initialize hole detail.
        
        Args:
            hole_number: Hole number
            shots: List of shots on this hole
        """
        self.hole_number = hole_number
        self.shots = sorted(shots, key=lambda s: s.swing_number)
    
    def get_shot_count(self) -> int:
        """Get number of shots on this hole.
        
        Returns:
            Shot count
        """
        return len(self.shots)
    
    def get_total_distance(self) -> Optional[float]:
        """Get total distance for all shots on this hole.
        
        Returns:
            Total distance in yards or None if no distances available
        """
        distances = [s.distance_yards for s in self.shots if s.distance_yards is not None]
        if distances:
            return sum(distances)
        return None
    
    def get_clubs_used(self) -> List[str]:
        """Get list of clubs used on this hole.
        
        Returns:
            List of club display names
        """
        return [shot.get_club_display_name() for shot in self.shots]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        total_distance = self.get_total_distance()
        return {
            'hole_number': self.hole_number,
            'shot_count': self.get_shot_count(),
            'total_distance': f"{int(total_distance)} yards" if total_distance else "N/A",
            'clubs_used': self.get_clubs_used(),
            'shots': [shot.to_dict() for shot in self.shots]
        }


class RoundDetailView:
    """View component for displaying detailed round information."""
    
    def __init__(self):
        """Initialize round detail view."""
        self.round_id: Optional[str] = None
        self.round_data: Optional[Dict[str, Any]] = None
        self.course_data: Optional[Dict[str, Any]] = None
        self.shots: List[ShotDetail] = []
        self.holes: List[HoleDetail] = []
    
    def load_round(self, round_data: Dict[str, Any], shots_data: List[Dict[str, Any]],
                   course_data: Optional[Dict[str, Any]] = None) -> None:
        """Load round data into the view.
        
        Args:
            round_data: Round data from API
            shots_data: List of shot dictionaries from API
            course_data: Optional course data from API
        """
        self.round_id = round_data['id']
        self.round_data = round_data
        self.course_data = course_data
        
        # Load shots
        self.shots = [ShotDetail(shot_data) for shot_data in shots_data]
        
        # Group shots by hole
        self._group_shots_by_hole()
    
    def _group_shots_by_hole(self) -> None:
        """Group shots by hole number."""
        shots_by_hole = defaultdict(list)
        for shot in self.shots:
            shots_by_hole[shot.hole_number].append(shot)
        
        self.holes = [
            HoleDetail(hole_num, shots)
            for hole_num, shots in sorted(shots_by_hole.items())
        ]
    
    def get_round_summary(self) -> Dict[str, Any]:
        """Get summary information for the round.
        
        Returns:
            Dictionary with round summary
        """
        if not self.round_data:
            return {}
        
        start_time = self._parse_datetime(self.round_data.get('start_time'))
        end_time = self._parse_datetime(self.round_data.get('end_time'))
        
        duration = None
        if start_time and end_time:
            delta = end_time - start_time
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            duration = f"{hours}h {minutes}m"
        
        return {
            'round_id': self.round_id,
            'course_name': self.round_data.get('course_name', 'Unknown Course'),
            'date': start_time.strftime("%b %d, %Y") if start_time else "Unknown",
            'start_time': start_time.strftime("%I:%M %p") if start_time else "",
            'duration': duration,
            'total_shots': len(self.shots),
            'holes_played': len(self.holes),
            'weather': self.round_data.get('weather_conditions')
        }
    
    def get_course_info(self) -> Optional[Dict[str, Any]]:
        """Get course information.
        
        Returns:
            Course info dictionary or None
        """
        if not self.course_data:
            return None
        
        return {
            'name': self.course_data.get('name'),
            'address': self.course_data.get('address'),
            'total_holes': self.course_data.get('total_holes'),
            'par': self.course_data.get('par'),
            'yardage': self.course_data.get('yardage'),
            'rating': self.course_data.get('rating'),
            'slope': self.course_data.get('slope')
        }
    
    def get_holes_data(self) -> List[Dict[str, Any]]:
        """Get data for all holes.
        
        Returns:
            List of hole dictionaries
        """
        return [hole.to_dict() for hole in self.holes]
    
    def get_hole_by_number(self, hole_number: int) -> Optional[HoleDetail]:
        """Get hole detail by hole number.
        
        Args:
            hole_number: Hole number
            
        Returns:
            Hole detail or None if not found
        """
        for hole in self.holes:
            if hole.hole_number == hole_number:
                return hole
        return None
    
    def get_shot_by_id(self, shot_id: str) -> Optional[ShotDetail]:
        """Get shot by ID.
        
        Args:
            shot_id: Shot ID
            
        Returns:
            Shot detail or None if not found
        """
        for shot in self.shots:
            if shot.id == shot_id:
                return shot
        return None
    
    def get_shots_by_club(self, club_type: str) -> List[ShotDetail]:
        """Get all shots with a specific club.
        
        Args:
            club_type: Club type (e.g., "DRIVER", "IRON_7")
            
        Returns:
            List of shots with that club
        """
        return [shot for shot in self.shots if shot.club_type == club_type]
    
    def get_shots_by_hole(self, hole_number: int) -> List[ShotDetail]:
        """Get all shots on a specific hole.
        
        Args:
            hole_number: Hole number
            
        Returns:
            List of shots on that hole
        """
        return [shot for shot in self.shots if shot.hole_number == hole_number]
    
    def get_club_usage_summary(self) -> Dict[str, int]:
        """Get summary of club usage.
        
        Returns:
            Dictionary mapping club display names to usage count
        """
        club_counts = defaultdict(int)
        for shot in self.shots:
            club_counts[shot.get_club_display_name()] += 1
        return dict(club_counts)
    
    def get_average_distance_by_club(self) -> Dict[str, float]:
        """Get average distance for each club.
        
        Returns:
            Dictionary mapping club display names to average distance
        """
        club_distances = defaultdict(list)
        for shot in self.shots:
            if shot.distance_yards is not None:
                club_distances[shot.get_club_display_name()].append(shot.distance_yards)
        
        return {
            club: sum(distances) / len(distances)
            for club, distances in club_distances.items()
            if distances
        }
    
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entire view to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            'summary': self.get_round_summary(),
            'course': self.get_course_info(),
            'holes': self.get_holes_data(),
            'club_usage': self.get_club_usage_summary(),
            'average_distances': self.get_average_distance_by_club()
        }
