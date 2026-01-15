"""Map visualization component for mobile app.

Displays golf course maps with shot markers and trace lines.
Supports Mapbox GL and Google Maps SDK integration.
"""

from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum


class MapProvider(Enum):
    """Supported map providers."""
    MAPBOX = "mapbox"
    GOOGLE_MAPS = "google_maps"


@dataclass
class MapCoordinate:
    """Represents a geographic coordinate."""
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    
    def to_tuple(self) -> Tuple[float, float]:
        """Convert to (lat, lon) tuple.
        
        Returns:
            Tuple of (latitude, longitude)
        """
        return (self.latitude, self.longitude)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary with lat, lon, and optional altitude
        """
        result = {
            'latitude': self.latitude,
            'longitude': self.longitude
        }
        if self.altitude is not None:
            result['altitude'] = self.altitude
        return result


@dataclass
class MapBounds:
    """Represents map viewport bounds."""
    southwest: MapCoordinate
    northeast: MapCoordinate
    
    def contains(self, coord: MapCoordinate) -> bool:
        """Check if coordinate is within bounds.
        
        Args:
            coord: Coordinate to check
            
        Returns:
            True if coordinate is within bounds
        """
        return (self.southwest.latitude <= coord.latitude <= self.northeast.latitude and
                self.southwest.longitude <= coord.longitude <= self.northeast.longitude)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary with southwest and northeast coordinates
        """
        return {
            'southwest': self.southwest.to_dict(),
            'northeast': self.northeast.to_dict()
        }


class ShotMarker:
    """Represents a shot marker on the map."""
    
    def __init__(self, shot_id: str, coordinate: MapCoordinate, 
                 hole_number: int, swing_number: int, club_type: str,
                 distance: Optional[float] = None, timestamp: Optional[str] = None):
        """Initialize shot marker.
        
        Args:
            shot_id: Unique shot identifier
            coordinate: GPS coordinate of shot
            hole_number: Hole number
            swing_number: Swing number on hole
            club_type: Club type used
            distance: Distance in yards (optional)
            timestamp: Shot timestamp (optional)
        """
        self.shot_id = shot_id
        self.coordinate = coordinate
        self.hole_number = hole_number
        self.swing_number = swing_number
        self.club_type = club_type
        self.distance = distance
        self.timestamp = timestamp
        self.is_selected = False
    
    def get_marker_color(self) -> str:
        """Get marker color based on club type.
        
        Returns:
            Hex color code
        """
        # Color coding by club category
        if self.club_type == 'DRIVER':
            return '#FF0000'  # Red for driver
        elif self.club_type.startswith('WOOD'):
            return '#FF6600'  # Orange for woods
        elif self.club_type.startswith('HYBRID'):
            return '#FFAA00'  # Yellow-orange for hybrids
        elif self.club_type.startswith('IRON'):
            return '#0066FF'  # Blue for irons
        elif 'WEDGE' in self.club_type:
            return '#00AA00'  # Green for wedges
        elif self.club_type == 'PUTTER':
            return '#AA00AA'  # Purple for putter
        else:
            return '#808080'  # Gray for unknown
    
    def get_marker_size(self) -> str:
        """Get marker size based on selection state.
        
        Returns:
            Size descriptor ('small', 'medium', 'large')
        """
        return 'large' if self.is_selected else 'medium'
    
    def get_club_display_name(self) -> str:
        """Get human-readable club name.
        
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
        return club_names.get(self.club_type, self.club_type)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for rendering.
        
        Returns:
            Dictionary representation
        """
        return {
            'shot_id': self.shot_id,
            'coordinate': self.coordinate.to_dict(),
            'hole_number': self.hole_number,
            'swing_number': self.swing_number,
            'club_type': self.club_type,
            'club_name': self.get_club_display_name(),
            'distance': self.distance,
            'timestamp': self.timestamp,
            'color': self.get_marker_color(),
            'size': self.get_marker_size(),
            'is_selected': self.is_selected
        }


class ShotTraceLine:
    """Represents a trace line between consecutive shots."""
    
    def __init__(self, from_marker: ShotMarker, to_marker: ShotMarker):
        """Initialize shot trace line.
        
        Args:
            from_marker: Starting shot marker
            to_marker: Ending shot marker
        """
        self.from_marker = from_marker
        self.to_marker = to_marker
        self.from_coordinate = from_marker.coordinate
        self.to_coordinate = to_marker.coordinate
    
    def get_line_color(self) -> str:
        """Get line color based on starting shot club.
        
        Returns:
            Hex color code
        """
        return self.from_marker.get_marker_color()
    
    def get_line_width(self) -> int:
        """Get line width in pixels.
        
        Returns:
            Line width
        """
        return 3
    
    def get_line_style(self) -> str:
        """Get line style.
        
        Returns:
            Line style ('solid', 'dashed', 'dotted')
        """
        # Use dashed line for putts
        if self.from_marker.club_type == 'PUTTER':
            return 'dashed'
        return 'solid'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for rendering.
        
        Returns:
            Dictionary representation
        """
        return {
            'from_shot_id': self.from_marker.shot_id,
            'to_shot_id': self.to_marker.shot_id,
            'from_coordinate': self.from_coordinate.to_dict(),
            'to_coordinate': self.to_coordinate.to_dict(),
            'color': self.get_line_color(),
            'width': self.get_line_width(),
            'style': self.get_line_style()
        }


class HoleBoundary:
    """Represents a hole boundary polygon on the course."""
    
    def __init__(self, hole_number: int, boundary_coordinates: List[MapCoordinate],
                 tee_box: Optional[MapCoordinate] = None,
                 green: Optional[MapCoordinate] = None):
        """Initialize hole boundary.
        
        Args:
            hole_number: Hole number
            boundary_coordinates: List of coordinates forming the boundary polygon
            tee_box: Tee box location (optional)
            green: Green location (optional)
        """
        self.hole_number = hole_number
        self.boundary_coordinates = boundary_coordinates
        self.tee_box = tee_box
        self.green = green
    
    def get_fill_color(self) -> str:
        """Get polygon fill color.
        
        Returns:
            RGBA color string
        """
        return 'rgba(144, 238, 144, 0.2)'  # Light green with transparency
    
    def get_stroke_color(self) -> str:
        """Get polygon stroke color.
        
        Returns:
            Hex color code
        """
        return '#228B22'  # Forest green
    
    def get_stroke_width(self) -> int:
        """Get stroke width in pixels.
        
        Returns:
            Stroke width
        """
        return 2
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for rendering.
        
        Returns:
            Dictionary representation
        """
        result = {
            'hole_number': self.hole_number,
            'boundary': [coord.to_dict() for coord in self.boundary_coordinates],
            'fill_color': self.get_fill_color(),
            'stroke_color': self.get_stroke_color(),
            'stroke_width': self.get_stroke_width()
        }
        if self.tee_box:
            result['tee_box'] = self.tee_box.to_dict()
        if self.green:
            result['green'] = self.green.to_dict()
        return result


class CourseOverlay:
    """Represents the complete course overlay with all holes."""
    
    def __init__(self, course_id: str, course_name: str):
        """Initialize course overlay.
        
        Args:
            course_id: Course identifier
            course_name: Course name
        """
        self.course_id = course_id
        self.course_name = course_name
        self.holes: List[HoleBoundary] = []
    
    def add_hole(self, hole: HoleBoundary) -> None:
        """Add a hole boundary to the overlay.
        
        Args:
            hole: Hole boundary to add
        """
        self.holes.append(hole)
    
    def get_hole(self, hole_number: int) -> Optional[HoleBoundary]:
        """Get hole boundary by number.
        
        Args:
            hole_number: Hole number
            
        Returns:
            Hole boundary or None if not found
        """
        for hole in self.holes:
            if hole.hole_number == hole_number:
                return hole
        return None
    
    def get_course_bounds(self) -> Optional[MapBounds]:
        """Calculate bounds that encompass all holes.
        
        Returns:
            Map bounds or None if no holes
        """
        if not self.holes:
            return None
        
        all_coords = []
        for hole in self.holes:
            all_coords.extend(hole.boundary_coordinates)
        
        if not all_coords:
            return None
        
        min_lat = min(coord.latitude for coord in all_coords)
        max_lat = max(coord.latitude for coord in all_coords)
        min_lon = min(coord.longitude for coord in all_coords)
        max_lon = max(coord.longitude for coord in all_coords)
        
        return MapBounds(
            southwest=MapCoordinate(min_lat, min_lon),
            northeast=MapCoordinate(max_lat, max_lon)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for rendering.
        
        Returns:
            Dictionary representation
        """
        return {
            'course_id': self.course_id,
            'course_name': self.course_name,
            'holes': [hole.to_dict() for hole in self.holes],
            'bounds': self.get_course_bounds().to_dict() if self.get_course_bounds() else None
        }


class MapVisualization:
    """Main map visualization component for displaying shots on course map."""
    
    def __init__(self, provider: MapProvider = MapProvider.MAPBOX):
        """Initialize map visualization.
        
        Args:
            provider: Map provider to use (Mapbox or Google Maps)
        """
        self.provider = provider
        self.course_overlay: Optional[CourseOverlay] = None
        self.shot_markers: List[ShotMarker] = []
        self.trace_lines: List[ShotTraceLine] = []
        self.selected_shot_id: Optional[str] = None
        self.on_marker_tap: Optional[Callable[[str], None]] = None
        self.filter_hole_numbers: Optional[List[int]] = None
        self.filter_club_types: Optional[List[str]] = None
        self.filter_distance_range: Optional[Tuple[float, float]] = None
    
    def load_course_overlay(self, course_data: Dict[str, Any]) -> None:
        """Load course overlay from course data.
        
        Args:
            course_data: Course data including holes with boundaries
        """
        self.course_overlay = CourseOverlay(
            course_id=course_data['id'],
            course_name=course_data['name']
        )
        
        # Load hole boundaries if available
        if 'holes' in course_data:
            for hole_data in course_data['holes']:
                boundary_coords = []
                
                # Parse fairway polygon if available
                if 'fairway_polygon' in hole_data and hole_data['fairway_polygon']:
                    coords = hole_data['fairway_polygon'].get('coordinates', [])
                    boundary_coords = [
                        MapCoordinate(lat, lon) for lon, lat in coords
                    ]
                
                # Get tee box and green locations
                tee_box = None
                if 'tee_box_location' in hole_data and hole_data['tee_box_location']:
                    tee_box = MapCoordinate(
                        hole_data['tee_box_location']['latitude'],
                        hole_data['tee_box_location']['longitude']
                    )
                
                green = None
                if 'green_location' in hole_data and hole_data['green_location']:
                    green = MapCoordinate(
                        hole_data['green_location']['latitude'],
                        hole_data['green_location']['longitude']
                    )
                
                if boundary_coords or tee_box or green:
                    hole = HoleBoundary(
                        hole_number=hole_data['hole_number'],
                        boundary_coordinates=boundary_coords,
                        tee_box=tee_box,
                        green=green
                    )
                    self.course_overlay.add_hole(hole)
    
    def load_shots(self, shots_data: List[Dict[str, Any]]) -> None:
        """Load shot markers from shot data.
        
        Args:
            shots_data: List of shot dictionaries with GPS coordinates
        """
        self.shot_markers = []
        
        for shot in shots_data:
            # Only add shots with valid GPS coordinates
            if shot.get('gps_lat') is not None and shot.get('gps_lon') is not None:
                coordinate = MapCoordinate(
                    latitude=shot['gps_lat'],
                    longitude=shot['gps_lon'],
                    altitude=shot.get('gps_altitude')
                )
                
                marker = ShotMarker(
                    shot_id=shot['id'],
                    coordinate=coordinate,
                    hole_number=shot['hole_number'],
                    swing_number=shot['swing_number'],
                    club_type=shot['club_type'],
                    distance=shot.get('distance_yards'),
                    timestamp=shot.get('shot_time')
                )
                
                self.shot_markers.append(marker)
        
        # Generate trace lines between consecutive shots on same hole
        self._generate_trace_lines()
    
    def _generate_trace_lines(self) -> None:
        """Generate trace lines between consecutive shots on same hole."""
        self.trace_lines = []
        
        # Group shots by hole
        shots_by_hole: Dict[int, List[ShotMarker]] = {}
        for marker in self.shot_markers:
            if marker.hole_number not in shots_by_hole:
                shots_by_hole[marker.hole_number] = []
            shots_by_hole[marker.hole_number].append(marker)
        
        # Create trace lines for each hole
        for hole_number, markers in shots_by_hole.items():
            # Sort by swing number
            sorted_markers = sorted(markers, key=lambda m: m.swing_number)
            
            # Create lines between consecutive shots
            for i in range(len(sorted_markers) - 1):
                trace_line = ShotTraceLine(sorted_markers[i], sorted_markers[i + 1])
                self.trace_lines.append(trace_line)
    
    def set_shot_filters(self, hole_numbers: Optional[List[int]] = None,
                        club_types: Optional[List[str]] = None,
                        distance_range: Optional[Tuple[float, float]] = None) -> None:
        """Set filters for displayed shots.
        
        Args:
            hole_numbers: List of hole numbers to show (None = all)
            club_types: List of club types to show (None = all)
            distance_range: Tuple of (min, max) distance in yards (None = all)
        """
        self.filter_hole_numbers = hole_numbers
        self.filter_club_types = club_types
        self.filter_distance_range = distance_range
    
    def clear_filters(self) -> None:
        """Clear all shot filters."""
        self.filter_hole_numbers = None
        self.filter_club_types = None
        self.filter_distance_range = None
    
    def _apply_filters(self, marker: ShotMarker) -> bool:
        """Check if marker passes current filters.
        
        Args:
            marker: Shot marker to check
            
        Returns:
            True if marker should be displayed
        """
        # Filter by hole number
        if self.filter_hole_numbers and marker.hole_number not in self.filter_hole_numbers:
            return False
        
        # Filter by club type
        if self.filter_club_types and marker.club_type not in self.filter_club_types:
            return False
        
        # Filter by distance range
        if self.filter_distance_range and marker.distance is not None:
            min_dist, max_dist = self.filter_distance_range
            if not (min_dist <= marker.distance <= max_dist):
                return False
        
        return True
    
    def get_filtered_markers(self) -> List[ShotMarker]:
        """Get shot markers after applying filters.
        
        Returns:
            List of filtered shot markers
        """
        return [marker for marker in self.shot_markers if self._apply_filters(marker)]
    
    def get_filtered_trace_lines(self) -> List[ShotTraceLine]:
        """Get trace lines after applying filters.
        
        Returns:
            List of filtered trace lines
        """
        filtered_markers = self.get_filtered_markers()
        filtered_marker_ids = {marker.shot_id for marker in filtered_markers}
        
        # Only include lines where both endpoints are visible
        return [
            line for line in self.trace_lines
            if line.from_marker.shot_id in filtered_marker_ids
            and line.to_marker.shot_id in filtered_marker_ids
        ]
    
    def select_shot(self, shot_id: str) -> bool:
        """Select a shot marker.
        
        Args:
            shot_id: Shot ID to select
            
        Returns:
            True if shot found and selected
        """
        # Deselect all markers
        for marker in self.shot_markers:
            marker.is_selected = False
        
        # Select the specified marker
        for marker in self.shot_markers:
            if marker.shot_id == shot_id:
                marker.is_selected = True
                self.selected_shot_id = shot_id
                if self.on_marker_tap:
                    self.on_marker_tap(shot_id)
                return True
        
        return False
    
    def deselect_shot(self) -> None:
        """Deselect currently selected shot."""
        for marker in self.shot_markers:
            marker.is_selected = False
        self.selected_shot_id = None
    
    def get_selected_marker(self) -> Optional[ShotMarker]:
        """Get currently selected shot marker.
        
        Returns:
            Selected marker or None
        """
        if self.selected_shot_id:
            for marker in self.shot_markers:
                if marker.shot_id == self.selected_shot_id:
                    return marker
        return None
    
    def set_on_marker_tap_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for when a marker is tapped.
        
        Args:
            callback: Function to call with shot_id when marker is tapped
        """
        self.on_marker_tap = callback
    
    def zoom_to_hole(self, hole_number: int, padding: float = 0.001) -> Optional[MapBounds]:
        """Calculate map bounds to zoom to a specific hole.
        
        Args:
            hole_number: Hole number to zoom to
            padding: Padding around bounds in degrees (default 0.001)
            
        Returns:
            Map bounds or None if hole not found
        """
        # Get shots on this hole
        hole_markers = [m for m in self.shot_markers if m.hole_number == hole_number]
        
        if not hole_markers:
            return None
        
        # Calculate bounds from shot coordinates
        lats = [m.coordinate.latitude for m in hole_markers]
        lons = [m.coordinate.longitude for m in hole_markers]
        
        min_lat = min(lats) - padding
        max_lat = max(lats) + padding
        min_lon = min(lons) - padding
        max_lon = max(lons) + padding
        
        return MapBounds(
            southwest=MapCoordinate(min_lat, min_lon),
            northeast=MapCoordinate(max_lat, max_lon)
        )
    
    def zoom_to_all_shots(self, padding: float = 0.001) -> Optional[MapBounds]:
        """Calculate map bounds to show all shots.
        
        Args:
            padding: Padding around bounds in degrees (default 0.001)
            
        Returns:
            Map bounds or None if no shots
        """
        filtered_markers = self.get_filtered_markers()
        
        if not filtered_markers:
            return None
        
        lats = [m.coordinate.latitude for m in filtered_markers]
        lons = [m.coordinate.longitude for m in filtered_markers]
        
        min_lat = min(lats) - padding
        max_lat = max(lats) + padding
        min_lon = min(lons) - padding
        max_lon = max(lons) + padding
        
        return MapBounds(
            southwest=MapCoordinate(min_lat, min_lon),
            northeast=MapCoordinate(max_lat, max_lon)
        )
    
    def get_shot_count(self) -> int:
        """Get total number of shots.
        
        Returns:
            Shot count
        """
        return len(self.get_filtered_markers())
    
    def get_holes_with_shots(self) -> List[int]:
        """Get list of hole numbers that have shots.
        
        Returns:
            Sorted list of hole numbers
        """
        filtered_markers = self.get_filtered_markers()
        holes = set(marker.hole_number for marker in filtered_markers)
        return sorted(list(holes))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entire visualization to dictionary for rendering.
        
        Returns:
            Dictionary representation
        """
        filtered_markers = self.get_filtered_markers()
        filtered_lines = self.get_filtered_trace_lines()
        
        return {
            'provider': self.provider.value,
            'course_overlay': self.course_overlay.to_dict() if self.course_overlay else None,
            'shot_markers': [marker.to_dict() for marker in filtered_markers],
            'trace_lines': [line.to_dict() for line in filtered_lines],
            'selected_shot_id': self.selected_shot_id,
            'filters': {
                'hole_numbers': self.filter_hole_numbers,
                'club_types': self.filter_club_types,
                'distance_range': self.filter_distance_range
            },
            'bounds': self.zoom_to_all_shots().to_dict() if self.zoom_to_all_shots() else None
        }
