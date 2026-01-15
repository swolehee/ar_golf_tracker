"""Integration example showing shot detail view with map visualization.

This module demonstrates how the ShotDetailView integrates with MapVisualization
to provide a complete shot viewing and filtering experience.
"""

from typing import Dict, Any, List, Optional
from ar_golf_tracker.mobile_app.map_visualization import MapVisualization, MapProvider
from ar_golf_tracker.mobile_app.shot_detail_view import ShotDetailView, ShotFilter


class IntegratedShotMapView:
    """Integrated view combining map visualization and shot detail view."""
    
    def __init__(self, map_provider: MapProvider = MapProvider.MAPBOX):
        """Initialize integrated view.
        
        Args:
            map_provider: Map provider to use
        """
        self.map_viz = MapVisualization(map_provider)
        self.shot_detail = ShotDetailView()
        
        # Connect callbacks
        self._setup_callbacks()
    
    def _setup_callbacks(self) -> None:
        """Set up callbacks between components."""
        # When a marker is tapped on the map, show shot details
        self.map_viz.set_on_marker_tap_callback(self._on_map_marker_tap)
        
        # When filter changes in shot detail view, update map
        self.shot_detail.set_on_filter_change_callback(self._on_filter_change)
    
    def _on_map_marker_tap(self, shot_id: str) -> None:
        """Handle map marker tap event.
        
        Args:
            shot_id: ID of tapped shot marker
        """
        # Select shot in detail view
        self.shot_detail.select_shot(shot_id)
        
        # Select marker on map
        self.map_viz.select_shot(shot_id)
    
    def _on_filter_change(self, shot_filter: ShotFilter) -> None:
        """Handle filter change event.
        
        Args:
            shot_filter: New filter settings
        """
        # Apply filter to map visualization
        self.map_viz.set_shot_filters(
            hole_numbers=shot_filter.hole_numbers,
            club_types=shot_filter.club_types,
            distance_range=shot_filter.distance_range
        )
    
    def load_round(self, round_data: Dict[str, Any], shots_data: List[Dict[str, Any]],
                   course_data: Optional[Dict[str, Any]] = None) -> None:
        """Load round data into both views.
        
        Args:
            round_data: Round data from API
            shots_data: List of shot dictionaries
            course_data: Optional course data
        """
        # Load course overlay if available
        if course_data:
            self.map_viz.load_course_overlay(course_data)
        
        # Load shots into both views
        self.map_viz.load_shots(shots_data)
        self.shot_detail.load_shots(shots_data)
    
    def select_shot(self, shot_id: str) -> bool:
        """Select a shot in both views.
        
        Args:
            shot_id: Shot ID to select
            
        Returns:
            True if shot found and selected
        """
        # Select in detail view
        detail_success = self.shot_detail.select_shot(shot_id)
        
        # Select on map (without triggering callback to avoid recursion)
        for marker in self.map_viz.shot_markers:
            marker.is_selected = False
        
        for marker in self.map_viz.shot_markers:
            if marker.shot_id == shot_id:
                marker.is_selected = True
                self.map_viz.selected_shot_id = shot_id
                map_success = True
                break
        else:
            map_success = False
        
        return detail_success and map_success
    
    def deselect_shot(self) -> None:
        """Deselect shot in both views."""
        self.shot_detail.deselect_shot()
        self.map_viz.deselect_shot()
    
    def filter_by_hole(self, hole_numbers: List[int]) -> None:
        """Filter shots by hole numbers.
        
        Args:
            hole_numbers: List of hole numbers to show
        """
        self.shot_detail.filter_by_hole(hole_numbers)
        # Filter change callback will update map automatically
    
    def filter_by_club(self, club_types: List[str]) -> None:
        """Filter shots by club types.
        
        Args:
            club_types: List of club types to show
        """
        self.shot_detail.filter_by_club(club_types)
        # Filter change callback will update map automatically
    
    def filter_by_distance(self, min_distance: float, max_distance: float) -> None:
        """Filter shots by distance range.
        
        Args:
            min_distance: Minimum distance in yards
            max_distance: Maximum distance in yards
        """
        self.shot_detail.filter_by_distance(min_distance, max_distance)
        # Filter change callback will update map automatically
    
    def clear_filters(self) -> None:
        """Clear all filters in both views."""
        self.shot_detail.clear_filter()
        # Filter change callback will update map automatically
    
    def zoom_to_hole(self, hole_number: int) -> Optional[Dict[str, Any]]:
        """Zoom map to specific hole.
        
        Args:
            hole_number: Hole number to zoom to
            
        Returns:
            Map bounds dictionary or None
        """
        bounds = self.map_viz.zoom_to_hole(hole_number)
        if bounds:
            return bounds.to_dict()
        return None
    
    def zoom_to_filtered_shots(self) -> Optional[Dict[str, Any]]:
        """Zoom map to show all filtered shots.
        
        Returns:
            Map bounds dictionary or None
        """
        bounds = self.map_viz.zoom_to_all_shots()
        if bounds:
            return bounds.to_dict()
        return None
    
    def get_selected_shot_details(self) -> Optional[Dict[str, Any]]:
        """Get details of currently selected shot.
        
        Returns:
            Shot details dictionary or None
        """
        return self.shot_detail.get_selected_shot_details()
    
    def get_filter_options(self) -> Dict[str, Any]:
        """Get available filter options.
        
        Returns:
            Dictionary with available holes, clubs, and distance range
        """
        return {
            'holes': self.shot_detail.get_available_holes(),
            'clubs': self.shot_detail.get_available_clubs(),
            'distance_range': self.shot_detail.get_distance_range()
        }
    
    def get_current_filter(self) -> Dict[str, Any]:
        """Get current filter settings.
        
        Returns:
            Current filter dictionary
        """
        return self.shot_detail.get_current_filter().to_dict()
    
    def get_shot_count(self) -> Dict[str, int]:
        """Get shot counts.
        
        Returns:
            Dictionary with total and filtered shot counts
        """
        return {
            'total': len(self.shot_detail.all_shots),
            'filtered': self.shot_detail.get_filtered_shot_count()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entire integrated view to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            'map': self.map_viz.to_dict(),
            'shot_detail': self.shot_detail.to_dict()
        }


# Example usage
def example_usage():
    """Example demonstrating integrated shot map view usage."""
    
    # Create integrated view
    view = IntegratedShotMapView()
    
    # Sample round data
    round_data = {
        'id': 'round-123',
        'course_name': 'Pebble Beach',
        'start_time': '2024-01-15T14:30:00Z'
    }
    
    # Sample shots data
    shots_data = [
        {
            'id': 'shot-1',
            'round_id': 'round-123',
            'hole_number': 1,
            'swing_number': 1,
            'club_type': 'DRIVER',
            'shot_time': '2024-01-15T14:30:00Z',
            'gps_lat': 36.5674,
            'gps_lon': -121.9500,
            'gps_accuracy': 5.0,
            'distance_yards': 250.0,
            'distance_accuracy': 'HIGH'
        },
        {
            'id': 'shot-2',
            'round_id': 'round-123',
            'hole_number': 1,
            'swing_number': 2,
            'club_type': 'IRON_7',
            'shot_time': '2024-01-15T14:31:00Z',
            'gps_lat': 36.5680,
            'gps_lon': -121.9505,
            'gps_accuracy': 5.0,
            'distance_yards': 150.0,
            'distance_accuracy': 'HIGH'
        },
        {
            'id': 'shot-3',
            'round_id': 'round-123',
            'hole_number': 2,
            'swing_number': 1,
            'club_type': 'DRIVER',
            'shot_time': '2024-01-15T14:35:00Z',
            'gps_lat': 36.5690,
            'gps_lon': -121.9510,
            'gps_accuracy': 5.0,
            'distance_yards': 270.0,
            'distance_accuracy': 'HIGH'
        }
    ]
    
    # Load round data
    view.load_round(round_data, shots_data)
    
    # Example 1: Select a shot
    print("Example 1: Selecting shot-1")
    view.select_shot('shot-1')
    details = view.get_selected_shot_details()
    print(f"Selected shot: {details['club']} on hole {details['hole_number']}")
    print(f"Distance: {details['distance']}")
    print()
    
    # Example 2: Filter by hole
    print("Example 2: Filtering by hole 1")
    view.filter_by_hole([1])
    shot_count = view.get_shot_count()
    print(f"Showing {shot_count['filtered']} of {shot_count['total']} shots")
    print()
    
    # Example 3: Filter by club
    print("Example 3: Filtering by DRIVER")
    view.clear_filters()
    view.filter_by_club(['DRIVER'])
    shot_count = view.get_shot_count()
    print(f"Showing {shot_count['filtered']} of {shot_count['total']} shots")
    print()
    
    # Example 4: Filter by distance range
    print("Example 4: Filtering by distance 200-300 yards")
    view.clear_filters()
    view.filter_by_distance(200.0, 300.0)
    shot_count = view.get_shot_count()
    print(f"Showing {shot_count['filtered']} of {shot_count['total']} shots")
    print()
    
    # Example 5: Get filter options
    print("Example 5: Available filter options")
    options = view.get_filter_options()
    print(f"Available holes: {options['holes']}")
    print(f"Available clubs: {options['clubs']}")
    print(f"Distance range: {options['distance_range']}")
    print()
    
    # Example 6: Zoom to hole
    print("Example 6: Zooming to hole 1")
    bounds = view.zoom_to_hole(1)
    if bounds:
        print(f"Map bounds: {bounds}")
    print()
    
    # Example 7: Clear filters
    print("Example 7: Clearing all filters")
    view.clear_filters()
    shot_count = view.get_shot_count()
    print(f"Showing {shot_count['filtered']} of {shot_count['total']} shots")


if __name__ == '__main__':
    example_usage()
