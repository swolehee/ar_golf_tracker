"""Example usage of map visualization component.

Demonstrates how to use the MapVisualization class to display
golf shots on a course map with trace lines.
"""

from ar_golf_tracker.mobile_app.map_visualization import (
    MapVisualization, MapProvider
)
from ar_golf_tracker.mobile_app.api_client import APIClient


def example_basic_map_visualization():
    """Example: Basic map visualization with shots."""
    print("=== Basic Map Visualization ===\n")
    
    # Initialize map visualization
    viz = MapVisualization(MapProvider.MAPBOX)
    
    # Sample shot data (would come from API in real app)
    shots_data = [
        {
            'id': 'shot1',
            'gps_lat': 36.5674,
            'gps_lon': -121.9500,
            'hole_number': 1,
            'swing_number': 1,
            'club_type': 'DRIVER',
            'distance_yards': 275.0,
            'shot_time': '2024-01-15T10:30:00'
        },
        {
            'id': 'shot2',
            'gps_lat': 36.5680,
            'gps_lon': -121.9505,
            'hole_number': 1,
            'swing_number': 2,
            'club_type': 'IRON_7',
            'distance_yards': 150.0,
            'shot_time': '2024-01-15T10:32:00'
        },
        {
            'id': 'shot3',
            'gps_lat': 36.5685,
            'gps_lon': -121.9508,
            'hole_number': 1,
            'swing_number': 3,
            'club_type': 'PITCHING_WEDGE',
            'distance_yards': 85.0,
            'shot_time': '2024-01-15T10:34:00'
        }
    ]
    
    # Load shots into visualization
    viz.load_shots(shots_data)
    
    print(f"Loaded {viz.get_shot_count()} shots")
    print(f"Generated {len(viz.trace_lines)} trace lines")
    print(f"Holes with shots: {viz.get_holes_with_shots()}")
    
    # Get visualization data for rendering
    viz_data = viz.to_dict()
    print(f"\nShot markers: {len(viz_data['shot_markers'])}")
    print(f"Trace lines: {len(viz_data['trace_lines'])}")
    
    # Example marker data
    if viz_data['shot_markers']:
        marker = viz_data['shot_markers'][0]
        print(f"\nFirst shot marker:")
        print(f"  Club: {marker['club_name']}")
        print(f"  Distance: {marker['distance']} yards")
        print(f"  Color: {marker['color']}")
        print(f"  Coordinate: ({marker['coordinate']['latitude']}, "
              f"{marker['coordinate']['longitude']})")


def example_with_course_overlay():
    """Example: Map visualization with course overlay."""
    print("\n\n=== Map with Course Overlay ===\n")
    
    viz = MapVisualization(MapProvider.MAPBOX)
    
    # Sample course data with hole boundaries
    course_data = {
        'id': 'pebble-beach',
        'name': 'Pebble Beach Golf Links',
        'holes': [
            {
                'hole_number': 1,
                'fairway_polygon': {
                    'coordinates': [
                        [-121.9500, 36.5674],
                        [-121.9505, 36.5680],
                        [-121.9508, 36.5685],
                        [-121.9503, 36.5686]
                    ]
                },
                'tee_box_location': {
                    'latitude': 36.5674,
                    'longitude': -121.9500
                },
                'green_location': {
                    'latitude': 36.5685,
                    'longitude': -121.9508
                }
            }
        ]
    }
    
    # Load course overlay
    viz.load_course_overlay(course_data)
    
    print(f"Course: {viz.course_overlay.course_name}")
    print(f"Holes loaded: {len(viz.course_overlay.holes)}")
    
    # Get course bounds for initial map view
    bounds = viz.course_overlay.get_course_bounds()
    if bounds:
        print(f"\nCourse bounds:")
        print(f"  SW: ({bounds.southwest.latitude}, {bounds.southwest.longitude})")
        print(f"  NE: ({bounds.northeast.latitude}, {bounds.northeast.longitude})")


def example_shot_filtering():
    """Example: Filtering shots by various criteria."""
    print("\n\n=== Shot Filtering ===\n")
    
    viz = MapVisualization()
    
    # Load shots from multiple holes with different clubs
    shots_data = [
        {'id': 'shot1', 'gps_lat': 36.5674, 'gps_lon': -121.9500,
         'hole_number': 1, 'swing_number': 1, 'club_type': 'DRIVER',
         'distance_yards': 275.0},
        {'id': 'shot2', 'gps_lat': 36.5680, 'gps_lon': -121.9505,
         'hole_number': 1, 'swing_number': 2, 'club_type': 'IRON_7',
         'distance_yards': 150.0},
        {'id': 'shot3', 'gps_lat': 36.5700, 'gps_lon': -121.9520,
         'hole_number': 2, 'swing_number': 1, 'club_type': 'DRIVER',
         'distance_yards': 290.0},
        {'id': 'shot4', 'gps_lat': 36.5705, 'gps_lon': -121.9525,
         'hole_number': 2, 'swing_number': 2, 'club_type': 'IRON_5',
         'distance_yards': 180.0}
    ]
    
    viz.load_shots(shots_data)
    print(f"Total shots: {viz.get_shot_count()}")
    
    # Filter by hole number
    viz.set_shot_filters(hole_numbers=[1])
    print(f"Shots on hole 1: {viz.get_shot_count()}")
    
    # Filter by club type
    viz.clear_filters()
    viz.set_shot_filters(club_types=['DRIVER'])
    print(f"Driver shots: {viz.get_shot_count()}")
    
    # Filter by distance range
    viz.clear_filters()
    viz.set_shot_filters(distance_range=(200.0, 300.0))
    print(f"Shots 200-300 yards: {viz.get_shot_count()}")
    
    # Combined filters
    viz.set_shot_filters(hole_numbers=[2], club_types=['DRIVER', 'IRON_5'])
    print(f"Hole 2, Driver or 5-iron: {viz.get_shot_count()}")


def example_shot_selection():
    """Example: Selecting and highlighting shots."""
    print("\n\n=== Shot Selection ===\n")
    
    viz = MapVisualization()
    
    shots_data = [
        {'id': 'shot1', 'gps_lat': 36.5674, 'gps_lon': -121.9500,
         'hole_number': 1, 'swing_number': 1, 'club_type': 'DRIVER',
         'distance_yards': 275.0},
        {'id': 'shot2', 'gps_lat': 36.5680, 'gps_lon': -121.9505,
         'hole_number': 1, 'swing_number': 2, 'club_type': 'IRON_7',
         'distance_yards': 150.0}
    ]
    
    viz.load_shots(shots_data)
    
    # Set up callback for marker taps
    def on_marker_tap(shot_id):
        print(f"  Marker tapped: {shot_id}")
        marker = viz.get_selected_marker()
        if marker:
            print(f"  Club: {marker.get_club_display_name()}")
            print(f"  Distance: {marker.distance} yards")
    
    viz.set_on_marker_tap_callback(on_marker_tap)
    
    # Select a shot
    print("Selecting shot1...")
    viz.select_shot('shot1')
    
    # Get selected marker details
    marker = viz.get_selected_marker()
    if marker:
        print(f"\nSelected marker details:")
        print(f"  Size: {marker.get_marker_size()}")  # 'large' when selected
        print(f"  Color: {marker.get_marker_color()}")
    
    # Deselect
    print("\nDeselecting shot...")
    viz.deselect_shot()
    print(f"Selected shot ID: {viz.selected_shot_id}")  # None


def example_zoom_operations():
    """Example: Zooming to specific areas."""
    print("\n\n=== Zoom Operations ===\n")
    
    viz = MapVisualization()
    
    shots_data = [
        {'id': 'shot1', 'gps_lat': 36.5674, 'gps_lon': -121.9500,
         'hole_number': 1, 'swing_number': 1, 'club_type': 'DRIVER'},
        {'id': 'shot2', 'gps_lat': 36.5680, 'gps_lon': -121.9505,
         'hole_number': 1, 'swing_number': 2, 'club_type': 'IRON_7'},
        {'id': 'shot3', 'gps_lat': 36.5700, 'gps_lon': -121.9520,
         'hole_number': 2, 'swing_number': 1, 'club_type': 'DRIVER'}
    ]
    
    viz.load_shots(shots_data)
    
    # Zoom to specific hole
    bounds = viz.zoom_to_hole(1)
    if bounds:
        print("Zoom to hole 1:")
        print(f"  SW: ({bounds.southwest.latitude:.4f}, "
              f"{bounds.southwest.longitude:.4f})")
        print(f"  NE: ({bounds.northeast.latitude:.4f}, "
              f"{bounds.northeast.longitude:.4f})")
    
    # Zoom to all shots
    bounds = viz.zoom_to_all_shots()
    if bounds:
        print("\nZoom to all shots:")
        print(f"  SW: ({bounds.southwest.latitude:.4f}, "
              f"{bounds.southwest.longitude:.4f})")
        print(f"  NE: ({bounds.northeast.latitude:.4f}, "
              f"{bounds.northeast.longitude:.4f})")


def example_complete_workflow():
    """Example: Complete workflow with API integration."""
    print("\n\n=== Complete Workflow ===\n")
    
    # In a real app, you would:
    # 1. Initialize API client and authenticate
    # api_client = APIClient(base_url="https://api.argolftracker.com")
    # tokens = api_client.login("user@example.com", "password")
    
    # 2. Fetch round data
    # round_id = "round123"
    # round_data = api_client.get_round(round_id)
    # shots_data = api_client.get_round_shots(round_id)
    # course_data = api_client.get_course(round_data['course_id'])
    
    # For this example, use sample data
    viz = MapVisualization(MapProvider.MAPBOX)
    
    # Load course overlay
    course_data = {
        'id': 'pebble-beach',
        'name': 'Pebble Beach Golf Links',
        'holes': []
    }
    viz.load_course_overlay(course_data)
    
    # Load shots
    shots_data = [
        {'id': 'shot1', 'gps_lat': 36.5674, 'gps_lon': -121.9500,
         'hole_number': 1, 'swing_number': 1, 'club_type': 'DRIVER',
         'distance_yards': 275.0, 'shot_time': '2024-01-15T10:30:00'},
        {'id': 'shot2', 'gps_lat': 36.5680, 'gps_lon': -121.9505,
         'hole_number': 1, 'swing_number': 2, 'club_type': 'IRON_7',
         'distance_yards': 150.0, 'shot_time': '2024-01-15T10:32:00'}
    ]
    viz.load_shots(shots_data)
    
    # Get complete visualization data for UI rendering
    viz_data = viz.to_dict()
    
    print(f"Course: {viz_data['course_overlay']['course_name']}")
    print(f"Provider: {viz_data['provider']}")
    print(f"Shot markers: {len(viz_data['shot_markers'])}")
    print(f"Trace lines: {len(viz_data['trace_lines'])}")
    
    # This data would be passed to the UI framework (React Native, etc.)
    # for actual map rendering with Mapbox GL or Google Maps SDK
    print("\nVisualization data ready for UI rendering!")


if __name__ == '__main__':
    example_basic_map_visualization()
    example_with_course_overlay()
    example_shot_filtering()
    example_shot_selection()
    example_zoom_operations()
    example_complete_workflow()
