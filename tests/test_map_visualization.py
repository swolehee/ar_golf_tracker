"""Tests for map visualization component."""

import pytest
from ar_golf_tracker.mobile_app.map_visualization import (
    MapProvider, MapCoordinate, MapBounds, ShotMarker, ShotTraceLine,
    HoleBoundary, CourseOverlay, MapVisualization
)


class TestMapCoordinate:
    """Tests for MapCoordinate class."""
    
    def test_coordinate_initialization(self):
        """Test coordinate initialization."""
        coord = MapCoordinate(37.7749, -122.4194, 100.0)
        assert coord.latitude == 37.7749
        assert coord.longitude == -122.4194
        assert coord.altitude == 100.0
    
    def test_coordinate_without_altitude(self):
        """Test coordinate without altitude."""
        coord = MapCoordinate(37.7749, -122.4194)
        assert coord.latitude == 37.7749
        assert coord.longitude == -122.4194
        assert coord.altitude is None
    
    def test_to_tuple(self):
        """Test conversion to tuple."""
        coord = MapCoordinate(37.7749, -122.4194)
        assert coord.to_tuple() == (37.7749, -122.4194)
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        coord = MapCoordinate(37.7749, -122.4194, 100.0)
        result = coord.to_dict()
        assert result['latitude'] == 37.7749
        assert result['longitude'] == -122.4194
        assert result['altitude'] == 100.0
    
    def test_to_dict_without_altitude(self):
        """Test dictionary conversion without altitude."""
        coord = MapCoordinate(37.7749, -122.4194)
        result = coord.to_dict()
        assert result['latitude'] == 37.7749
        assert result['longitude'] == -122.4194
        assert 'altitude' not in result


class TestMapBounds:
    """Tests for MapBounds class."""
    
    def test_bounds_initialization(self):
        """Test bounds initialization."""
        sw = MapCoordinate(37.7, -122.5)
        ne = MapCoordinate(37.8, -122.4)
        bounds = MapBounds(sw, ne)
        assert bounds.southwest == sw
        assert bounds.northeast == ne
    
    def test_contains_coordinate_inside(self):
        """Test contains with coordinate inside bounds."""
        sw = MapCoordinate(37.7, -122.5)
        ne = MapCoordinate(37.8, -122.4)
        bounds = MapBounds(sw, ne)
        coord = MapCoordinate(37.75, -122.45)
        assert bounds.contains(coord) is True
    
    def test_contains_coordinate_outside(self):
        """Test contains with coordinate outside bounds."""
        sw = MapCoordinate(37.7, -122.5)
        ne = MapCoordinate(37.8, -122.4)
        bounds = MapBounds(sw, ne)
        coord = MapCoordinate(37.9, -122.3)
        assert bounds.contains(coord) is False
    
    def test_contains_coordinate_on_boundary(self):
        """Test contains with coordinate on boundary."""
        sw = MapCoordinate(37.7, -122.5)
        ne = MapCoordinate(37.8, -122.4)
        bounds = MapBounds(sw, ne)
        coord = MapCoordinate(37.7, -122.5)
        assert bounds.contains(coord) is True
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        sw = MapCoordinate(37.7, -122.5)
        ne = MapCoordinate(37.8, -122.4)
        bounds = MapBounds(sw, ne)
        result = bounds.to_dict()
        assert 'southwest' in result
        assert 'northeast' in result
        assert result['southwest']['latitude'] == 37.7
        assert result['northeast']['latitude'] == 37.8


class TestShotMarker:
    """Tests for ShotMarker class."""
    
    def test_marker_initialization(self):
        """Test marker initialization."""
        coord = MapCoordinate(37.7749, -122.4194)
        marker = ShotMarker('shot1', coord, 1, 1, 'DRIVER', 250.0, '2024-01-15T10:30:00')
        assert marker.shot_id == 'shot1'
        assert marker.coordinate == coord
        assert marker.hole_number == 1
        assert marker.swing_number == 1
        assert marker.club_type == 'DRIVER'
        assert marker.distance == 250.0
        assert marker.timestamp == '2024-01-15T10:30:00'
        assert marker.is_selected is False
    
    def test_marker_color_driver(self):
        """Test marker color for driver."""
        coord = MapCoordinate(37.7749, -122.4194)
        marker = ShotMarker('shot1', coord, 1, 1, 'DRIVER')
        assert marker.get_marker_color() == '#FF0000'
    
    def test_marker_color_wood(self):
        """Test marker color for woods."""
        coord = MapCoordinate(37.7749, -122.4194)
        marker = ShotMarker('shot1', coord, 1, 1, 'WOOD_3')
        assert marker.get_marker_color() == '#FF6600'
    
    def test_marker_color_iron(self):
        """Test marker color for irons."""
        coord = MapCoordinate(37.7749, -122.4194)
        marker = ShotMarker('shot1', coord, 1, 1, 'IRON_7')
        assert marker.get_marker_color() == '#0066FF'
    
    def test_marker_color_wedge(self):
        """Test marker color for wedges."""
        coord = MapCoordinate(37.7749, -122.4194)
        marker = ShotMarker('shot1', coord, 1, 1, 'PITCHING_WEDGE')
        assert marker.get_marker_color() == '#00AA00'
    
    def test_marker_color_putter(self):
        """Test marker color for putter."""
        coord = MapCoordinate(37.7749, -122.4194)
        marker = ShotMarker('shot1', coord, 1, 1, 'PUTTER')
        assert marker.get_marker_color() == '#AA00AA'
    
    def test_marker_size_normal(self):
        """Test marker size when not selected."""
        coord = MapCoordinate(37.7749, -122.4194)
        marker = ShotMarker('shot1', coord, 1, 1, 'DRIVER')
        assert marker.get_marker_size() == 'medium'
    
    def test_marker_size_selected(self):
        """Test marker size when selected."""
        coord = MapCoordinate(37.7749, -122.4194)
        marker = ShotMarker('shot1', coord, 1, 1, 'DRIVER')
        marker.is_selected = True
        assert marker.get_marker_size() == 'large'
    
    def test_get_club_display_name(self):
        """Test club display name conversion."""
        coord = MapCoordinate(37.7749, -122.4194)
        marker = ShotMarker('shot1', coord, 1, 1, 'IRON_7')
        assert marker.get_club_display_name() == '7 Iron'
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        coord = MapCoordinate(37.7749, -122.4194)
        marker = ShotMarker('shot1', coord, 1, 1, 'DRIVER', 250.0)
        result = marker.to_dict()
        assert result['shot_id'] == 'shot1'
        assert result['hole_number'] == 1
        assert result['swing_number'] == 1
        assert result['club_type'] == 'DRIVER'
        assert result['club_name'] == 'Driver'
        assert result['distance'] == 250.0
        assert 'color' in result
        assert 'size' in result
        assert result['is_selected'] is False


class TestShotTraceLine:
    """Tests for ShotTraceLine class."""
    
    def test_trace_line_initialization(self):
        """Test trace line initialization."""
        coord1 = MapCoordinate(37.7749, -122.4194)
        coord2 = MapCoordinate(37.7750, -122.4195)
        marker1 = ShotMarker('shot1', coord1, 1, 1, 'DRIVER')
        marker2 = ShotMarker('shot2', coord2, 1, 2, 'IRON_7')
        line = ShotTraceLine(marker1, marker2)
        assert line.from_marker == marker1
        assert line.to_marker == marker2
        assert line.from_coordinate == coord1
        assert line.to_coordinate == coord2
    
    def test_line_color_from_marker(self):
        """Test line color matches starting marker."""
        coord1 = MapCoordinate(37.7749, -122.4194)
        coord2 = MapCoordinate(37.7750, -122.4195)
        marker1 = ShotMarker('shot1', coord1, 1, 1, 'DRIVER')
        marker2 = ShotMarker('shot2', coord2, 1, 2, 'IRON_7')
        line = ShotTraceLine(marker1, marker2)
        assert line.get_line_color() == marker1.get_marker_color()
    
    def test_line_width(self):
        """Test line width."""
        coord1 = MapCoordinate(37.7749, -122.4194)
        coord2 = MapCoordinate(37.7750, -122.4195)
        marker1 = ShotMarker('shot1', coord1, 1, 1, 'DRIVER')
        marker2 = ShotMarker('shot2', coord2, 1, 2, 'IRON_7')
        line = ShotTraceLine(marker1, marker2)
        assert line.get_line_width() == 3
    
    def test_line_style_solid(self):
        """Test solid line style for non-putts."""
        coord1 = MapCoordinate(37.7749, -122.4194)
        coord2 = MapCoordinate(37.7750, -122.4195)
        marker1 = ShotMarker('shot1', coord1, 1, 1, 'DRIVER')
        marker2 = ShotMarker('shot2', coord2, 1, 2, 'IRON_7')
        line = ShotTraceLine(marker1, marker2)
        assert line.get_line_style() == 'solid'
    
    def test_line_style_dashed_for_putts(self):
        """Test dashed line style for putts."""
        coord1 = MapCoordinate(37.7749, -122.4194)
        coord2 = MapCoordinate(37.7750, -122.4195)
        marker1 = ShotMarker('shot1', coord1, 1, 1, 'PUTTER')
        marker2 = ShotMarker('shot2', coord2, 1, 2, 'PUTTER')
        line = ShotTraceLine(marker1, marker2)
        assert line.get_line_style() == 'dashed'
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        coord1 = MapCoordinate(37.7749, -122.4194)
        coord2 = MapCoordinate(37.7750, -122.4195)
        marker1 = ShotMarker('shot1', coord1, 1, 1, 'DRIVER')
        marker2 = ShotMarker('shot2', coord2, 1, 2, 'IRON_7')
        line = ShotTraceLine(marker1, marker2)
        result = line.to_dict()
        assert result['from_shot_id'] == 'shot1'
        assert result['to_shot_id'] == 'shot2'
        assert 'from_coordinate' in result
        assert 'to_coordinate' in result
        assert 'color' in result
        assert 'width' in result
        assert 'style' in result


class TestHoleBoundary:
    """Tests for HoleBoundary class."""
    
    def test_hole_boundary_initialization(self):
        """Test hole boundary initialization."""
        coords = [
            MapCoordinate(37.7749, -122.4194),
            MapCoordinate(37.7750, -122.4195),
            MapCoordinate(37.7751, -122.4196)
        ]
        tee = MapCoordinate(37.7749, -122.4194)
        green = MapCoordinate(37.7751, -122.4196)
        hole = HoleBoundary(1, coords, tee, green)
        assert hole.hole_number == 1
        assert len(hole.boundary_coordinates) == 3
        assert hole.tee_box == tee
        assert hole.green == green
    
    def test_hole_boundary_without_tee_green(self):
        """Test hole boundary without tee and green."""
        coords = [
            MapCoordinate(37.7749, -122.4194),
            MapCoordinate(37.7750, -122.4195)
        ]
        hole = HoleBoundary(1, coords)
        assert hole.hole_number == 1
        assert hole.tee_box is None
        assert hole.green is None
    
    def test_get_fill_color(self):
        """Test fill color."""
        coords = [MapCoordinate(37.7749, -122.4194)]
        hole = HoleBoundary(1, coords)
        assert hole.get_fill_color() == 'rgba(144, 238, 144, 0.2)'
    
    def test_get_stroke_color(self):
        """Test stroke color."""
        coords = [MapCoordinate(37.7749, -122.4194)]
        hole = HoleBoundary(1, coords)
        assert hole.get_stroke_color() == '#228B22'
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        coords = [MapCoordinate(37.7749, -122.4194)]
        tee = MapCoordinate(37.7749, -122.4194)
        hole = HoleBoundary(1, coords, tee_box=tee)
        result = hole.to_dict()
        assert result['hole_number'] == 1
        assert 'boundary' in result
        assert 'tee_box' in result
        assert 'fill_color' in result
        assert 'stroke_color' in result


class TestCourseOverlay:
    """Tests for CourseOverlay class."""
    
    def test_course_overlay_initialization(self):
        """Test course overlay initialization."""
        overlay = CourseOverlay('course1', 'Pebble Beach')
        assert overlay.course_id == 'course1'
        assert overlay.course_name == 'Pebble Beach'
        assert len(overlay.holes) == 0
    
    def test_add_hole(self):
        """Test adding holes to overlay."""
        overlay = CourseOverlay('course1', 'Pebble Beach')
        coords = [MapCoordinate(37.7749, -122.4194)]
        hole = HoleBoundary(1, coords)
        overlay.add_hole(hole)
        assert len(overlay.holes) == 1
        assert overlay.holes[0] == hole
    
    def test_get_hole(self):
        """Test getting hole by number."""
        overlay = CourseOverlay('course1', 'Pebble Beach')
        coords = [MapCoordinate(37.7749, -122.4194)]
        hole1 = HoleBoundary(1, coords)
        hole2 = HoleBoundary(2, coords)
        overlay.add_hole(hole1)
        overlay.add_hole(hole2)
        assert overlay.get_hole(1) == hole1
        assert overlay.get_hole(2) == hole2
        assert overlay.get_hole(3) is None
    
    def test_get_course_bounds(self):
        """Test calculating course bounds."""
        overlay = CourseOverlay('course1', 'Pebble Beach')
        coords1 = [
            MapCoordinate(37.7749, -122.4194),
            MapCoordinate(37.7750, -122.4195)
        ]
        coords2 = [
            MapCoordinate(37.7751, -122.4196),
            MapCoordinate(37.7752, -122.4197)
        ]
        overlay.add_hole(HoleBoundary(1, coords1))
        overlay.add_hole(HoleBoundary(2, coords2))
        bounds = overlay.get_course_bounds()
        assert bounds is not None
        assert bounds.southwest.latitude == 37.7749
        assert bounds.northeast.latitude == 37.7752
    
    def test_get_course_bounds_empty(self):
        """Test course bounds with no holes."""
        overlay = CourseOverlay('course1', 'Pebble Beach')
        assert overlay.get_course_bounds() is None
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        overlay = CourseOverlay('course1', 'Pebble Beach')
        coords = [MapCoordinate(37.7749, -122.4194)]
        overlay.add_hole(HoleBoundary(1, coords))
        result = overlay.to_dict()
        assert result['course_id'] == 'course1'
        assert result['course_name'] == 'Pebble Beach'
        assert 'holes' in result
        assert len(result['holes']) == 1


class TestMapVisualization:
    """Tests for MapVisualization class."""
    
    def test_initialization(self):
        """Test map visualization initialization."""
        viz = MapVisualization(MapProvider.MAPBOX)
        assert viz.provider == MapProvider.MAPBOX
        assert viz.course_overlay is None
        assert len(viz.shot_markers) == 0
        assert len(viz.trace_lines) == 0
        assert viz.selected_shot_id is None
    
    def test_load_course_overlay(self):
        """Test loading course overlay."""
        viz = MapVisualization()
        course_data = {
            'id': 'course1',
            'name': 'Pebble Beach',
            'holes': [
                {
                    'hole_number': 1,
                    'fairway_polygon': {
                        'coordinates': [[-122.4194, 37.7749], [-122.4195, 37.7750]]
                    },
                    'tee_box_location': {'latitude': 37.7749, 'longitude': -122.4194},
                    'green_location': {'latitude': 37.7750, 'longitude': -122.4195}
                }
            ]
        }
        viz.load_course_overlay(course_data)
        assert viz.course_overlay is not None
        assert viz.course_overlay.course_id == 'course1'
        assert viz.course_overlay.course_name == 'Pebble Beach'
        assert len(viz.course_overlay.holes) == 1
    
    def test_load_shots(self):
        """Test loading shots."""
        viz = MapVisualization()
        shots_data = [
            {
                'id': 'shot1',
                'gps_lat': 37.7749,
                'gps_lon': -122.4194,
                'hole_number': 1,
                'swing_number': 1,
                'club_type': 'DRIVER',
                'distance_yards': 250.0,
                'shot_time': '2024-01-15T10:30:00'
            },
            {
                'id': 'shot2',
                'gps_lat': 37.7750,
                'gps_lon': -122.4195,
                'hole_number': 1,
                'swing_number': 2,
                'club_type': 'IRON_7',
                'distance_yards': 150.0
            }
        ]
        viz.load_shots(shots_data)
        assert len(viz.shot_markers) == 2
        assert len(viz.trace_lines) == 1  # One line between two shots
    
    def test_load_shots_skips_invalid_gps(self):
        """Test loading shots skips shots without GPS."""
        viz = MapVisualization()
        shots_data = [
            {
                'id': 'shot1',
                'gps_lat': 37.7749,
                'gps_lon': -122.4194,
                'hole_number': 1,
                'swing_number': 1,
                'club_type': 'DRIVER'
            },
            {
                'id': 'shot2',
                'gps_lat': None,
                'gps_lon': None,
                'hole_number': 1,
                'swing_number': 2,
                'club_type': 'IRON_7'
            }
        ]
        viz.load_shots(shots_data)
        assert len(viz.shot_markers) == 1  # Only shot with GPS
    
    def test_trace_lines_generated_per_hole(self):
        """Test trace lines are generated per hole."""
        viz = MapVisualization()
        shots_data = [
            {'id': 'shot1', 'gps_lat': 37.7749, 'gps_lon': -122.4194,
             'hole_number': 1, 'swing_number': 1, 'club_type': 'DRIVER'},
            {'id': 'shot2', 'gps_lat': 37.7750, 'gps_lon': -122.4195,
             'hole_number': 1, 'swing_number': 2, 'club_type': 'IRON_7'},
            {'id': 'shot3', 'gps_lat': 37.7751, 'gps_lon': -122.4196,
             'hole_number': 2, 'swing_number': 1, 'club_type': 'DRIVER'},
            {'id': 'shot4', 'gps_lat': 37.7752, 'gps_lon': -122.4197,
             'hole_number': 2, 'swing_number': 2, 'club_type': 'IRON_7'}
        ]
        viz.load_shots(shots_data)
        assert len(viz.trace_lines) == 2  # One line per hole
    
    def test_set_shot_filters_hole_numbers(self):
        """Test filtering by hole numbers."""
        viz = MapVisualization()
        viz.set_shot_filters(hole_numbers=[1, 3])
        assert viz.filter_hole_numbers == [1, 3]
    
    def test_set_shot_filters_club_types(self):
        """Test filtering by club types."""
        viz = MapVisualization()
        viz.set_shot_filters(club_types=['DRIVER', 'IRON_7'])
        assert viz.filter_club_types == ['DRIVER', 'IRON_7']
    
    def test_set_shot_filters_distance_range(self):
        """Test filtering by distance range."""
        viz = MapVisualization()
        viz.set_shot_filters(distance_range=(100.0, 200.0))
        assert viz.filter_distance_range == (100.0, 200.0)
    
    def test_clear_filters(self):
        """Test clearing all filters."""
        viz = MapVisualization()
        viz.set_shot_filters(hole_numbers=[1], club_types=['DRIVER'])
        viz.clear_filters()
        assert viz.filter_hole_numbers is None
        assert viz.filter_club_types is None
        assert viz.filter_distance_range is None
    
    def test_get_filtered_markers_by_hole(self):
        """Test getting filtered markers by hole."""
        viz = MapVisualization()
        shots_data = [
            {'id': 'shot1', 'gps_lat': 37.7749, 'gps_lon': -122.4194,
             'hole_number': 1, 'swing_number': 1, 'club_type': 'DRIVER'},
            {'id': 'shot2', 'gps_lat': 37.7750, 'gps_lon': -122.4195,
             'hole_number': 2, 'swing_number': 1, 'club_type': 'DRIVER'}
        ]
        viz.load_shots(shots_data)
        viz.set_shot_filters(hole_numbers=[1])
        filtered = viz.get_filtered_markers()
        assert len(filtered) == 1
        assert filtered[0].hole_number == 1
    
    def test_get_filtered_markers_by_club(self):
        """Test getting filtered markers by club type."""
        viz = MapVisualization()
        shots_data = [
            {'id': 'shot1', 'gps_lat': 37.7749, 'gps_lon': -122.4194,
             'hole_number': 1, 'swing_number': 1, 'club_type': 'DRIVER'},
            {'id': 'shot2', 'gps_lat': 37.7750, 'gps_lon': -122.4195,
             'hole_number': 1, 'swing_number': 2, 'club_type': 'IRON_7'}
        ]
        viz.load_shots(shots_data)
        viz.set_shot_filters(club_types=['DRIVER'])
        filtered = viz.get_filtered_markers()
        assert len(filtered) == 1
        assert filtered[0].club_type == 'DRIVER'
    
    def test_get_filtered_markers_by_distance(self):
        """Test getting filtered markers by distance range."""
        viz = MapVisualization()
        shots_data = [
            {'id': 'shot1', 'gps_lat': 37.7749, 'gps_lon': -122.4194,
             'hole_number': 1, 'swing_number': 1, 'club_type': 'DRIVER',
             'distance_yards': 250.0},
            {'id': 'shot2', 'gps_lat': 37.7750, 'gps_lon': -122.4195,
             'hole_number': 1, 'swing_number': 2, 'club_type': 'IRON_7',
             'distance_yards': 150.0}
        ]
        viz.load_shots(shots_data)
        viz.set_shot_filters(distance_range=(200.0, 300.0))
        filtered = viz.get_filtered_markers()
        assert len(filtered) == 1
        assert filtered[0].distance == 250.0
    
    def test_get_filtered_trace_lines(self):
        """Test getting filtered trace lines."""
        viz = MapVisualization()
        shots_data = [
            {'id': 'shot1', 'gps_lat': 37.7749, 'gps_lon': -122.4194,
             'hole_number': 1, 'swing_number': 1, 'club_type': 'DRIVER'},
            {'id': 'shot2', 'gps_lat': 37.7750, 'gps_lon': -122.4195,
             'hole_number': 1, 'swing_number': 2, 'club_type': 'IRON_7'},
            {'id': 'shot3', 'gps_lat': 37.7751, 'gps_lon': -122.4196,
             'hole_number': 2, 'swing_number': 1, 'club_type': 'DRIVER'}
        ]
        viz.load_shots(shots_data)
        viz.set_shot_filters(hole_numbers=[1])
        filtered_lines = viz.get_filtered_trace_lines()
        assert len(filtered_lines) == 1  # Only line on hole 1
    
    def test_select_shot(self):
        """Test selecting a shot."""
        viz = MapVisualization()
        shots_data = [
            {'id': 'shot1', 'gps_lat': 37.7749, 'gps_lon': -122.4194,
             'hole_number': 1, 'swing_number': 1, 'club_type': 'DRIVER'}
        ]
        viz.load_shots(shots_data)
        result = viz.select_shot('shot1')
        assert result is True
        assert viz.selected_shot_id == 'shot1'
        assert viz.shot_markers[0].is_selected is True
    
    def test_select_shot_not_found(self):
        """Test selecting non-existent shot."""
        viz = MapVisualization()
        result = viz.select_shot('nonexistent')
        assert result is False
        assert viz.selected_shot_id is None
    
    def test_select_shot_deselects_others(self):
        """Test selecting shot deselects others."""
        viz = MapVisualization()
        shots_data = [
            {'id': 'shot1', 'gps_lat': 37.7749, 'gps_lon': -122.4194,
             'hole_number': 1, 'swing_number': 1, 'club_type': 'DRIVER'},
            {'id': 'shot2', 'gps_lat': 37.7750, 'gps_lon': -122.4195,
             'hole_number': 1, 'swing_number': 2, 'club_type': 'IRON_7'}
        ]
        viz.load_shots(shots_data)
        viz.select_shot('shot1')
        viz.select_shot('shot2')
        assert viz.shot_markers[0].is_selected is False
        assert viz.shot_markers[1].is_selected is True
    
    def test_deselect_shot(self):
        """Test deselecting shot."""
        viz = MapVisualization()
        shots_data = [
            {'id': 'shot1', 'gps_lat': 37.7749, 'gps_lon': -122.4194,
             'hole_number': 1, 'swing_number': 1, 'club_type': 'DRIVER'}
        ]
        viz.load_shots(shots_data)
        viz.select_shot('shot1')
        viz.deselect_shot()
        assert viz.selected_shot_id is None
        assert viz.shot_markers[0].is_selected is False
    
    def test_get_selected_marker(self):
        """Test getting selected marker."""
        viz = MapVisualization()
        shots_data = [
            {'id': 'shot1', 'gps_lat': 37.7749, 'gps_lon': -122.4194,
             'hole_number': 1, 'swing_number': 1, 'club_type': 'DRIVER'}
        ]
        viz.load_shots(shots_data)
        viz.select_shot('shot1')
        marker = viz.get_selected_marker()
        assert marker is not None
        assert marker.shot_id == 'shot1'
    
    def test_get_selected_marker_none(self):
        """Test getting selected marker when none selected."""
        viz = MapVisualization()
        marker = viz.get_selected_marker()
        assert marker is None
    
    def test_on_marker_tap_callback(self):
        """Test marker tap callback."""
        viz = MapVisualization()
        shots_data = [
            {'id': 'shot1', 'gps_lat': 37.7749, 'gps_lon': -122.4194,
             'hole_number': 1, 'swing_number': 1, 'club_type': 'DRIVER'}
        ]
        viz.load_shots(shots_data)
        
        tapped_shot_id = None
        def callback(shot_id):
            nonlocal tapped_shot_id
            tapped_shot_id = shot_id
        
        viz.set_on_marker_tap_callback(callback)
        viz.select_shot('shot1')
        assert tapped_shot_id == 'shot1'
    
    def test_zoom_to_hole(self):
        """Test zooming to specific hole."""
        viz = MapVisualization()
        shots_data = [
            {'id': 'shot1', 'gps_lat': 37.7749, 'gps_lon': -122.4194,
             'hole_number': 1, 'swing_number': 1, 'club_type': 'DRIVER'},
            {'id': 'shot2', 'gps_lat': 37.7750, 'gps_lon': -122.4195,
             'hole_number': 1, 'swing_number': 2, 'club_type': 'IRON_7'}
        ]
        viz.load_shots(shots_data)
        bounds = viz.zoom_to_hole(1)
        assert bounds is not None
        assert bounds.southwest.latitude < 37.7749
        assert bounds.northeast.latitude > 37.7750
    
    def test_zoom_to_hole_not_found(self):
        """Test zooming to non-existent hole."""
        viz = MapVisualization()
        bounds = viz.zoom_to_hole(99)
        assert bounds is None
    
    def test_zoom_to_all_shots(self):
        """Test zooming to all shots."""
        viz = MapVisualization()
        shots_data = [
            {'id': 'shot1', 'gps_lat': 37.7749, 'gps_lon': -122.4194,
             'hole_number': 1, 'swing_number': 1, 'club_type': 'DRIVER'},
            {'id': 'shot2', 'gps_lat': 37.7752, 'gps_lon': -122.4197,
             'hole_number': 2, 'swing_number': 1, 'club_type': 'DRIVER'}
        ]
        viz.load_shots(shots_data)
        bounds = viz.zoom_to_all_shots()
        assert bounds is not None
        assert bounds.southwest.latitude < 37.7749
        assert bounds.northeast.latitude > 37.7752
    
    def test_zoom_to_all_shots_empty(self):
        """Test zooming with no shots."""
        viz = MapVisualization()
        bounds = viz.zoom_to_all_shots()
        assert bounds is None
    
    def test_get_shot_count(self):
        """Test getting shot count."""
        viz = MapVisualization()
        shots_data = [
            {'id': 'shot1', 'gps_lat': 37.7749, 'gps_lon': -122.4194,
             'hole_number': 1, 'swing_number': 1, 'club_type': 'DRIVER'},
            {'id': 'shot2', 'gps_lat': 37.7750, 'gps_lon': -122.4195,
             'hole_number': 1, 'swing_number': 2, 'club_type': 'IRON_7'}
        ]
        viz.load_shots(shots_data)
        assert viz.get_shot_count() == 2
    
    def test_get_holes_with_shots(self):
        """Test getting holes with shots."""
        viz = MapVisualization()
        shots_data = [
            {'id': 'shot1', 'gps_lat': 37.7749, 'gps_lon': -122.4194,
             'hole_number': 1, 'swing_number': 1, 'club_type': 'DRIVER'},
            {'id': 'shot2', 'gps_lat': 37.7750, 'gps_lon': -122.4195,
             'hole_number': 3, 'swing_number': 1, 'club_type': 'DRIVER'},
            {'id': 'shot3', 'gps_lat': 37.7751, 'gps_lon': -122.4196,
             'hole_number': 1, 'swing_number': 2, 'club_type': 'IRON_7'}
        ]
        viz.load_shots(shots_data)
        holes = viz.get_holes_with_shots()
        assert holes == [1, 3]
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        viz = MapVisualization(MapProvider.MAPBOX)
        course_data = {
            'id': 'course1',
            'name': 'Pebble Beach',
            'holes': []
        }
        shots_data = [
            {'id': 'shot1', 'gps_lat': 37.7749, 'gps_lon': -122.4194,
             'hole_number': 1, 'swing_number': 1, 'club_type': 'DRIVER'}
        ]
        viz.load_course_overlay(course_data)
        viz.load_shots(shots_data)
        result = viz.to_dict()
        assert result['provider'] == 'mapbox'
        assert 'course_overlay' in result
        assert 'shot_markers' in result
        assert 'trace_lines' in result
        assert 'filters' in result
        assert 'bounds' in result
    
    def test_to_dict_with_filters(self):
        """Test dictionary conversion with filters applied."""
        viz = MapVisualization()
        shots_data = [
            {'id': 'shot1', 'gps_lat': 37.7749, 'gps_lon': -122.4194,
             'hole_number': 1, 'swing_number': 1, 'club_type': 'DRIVER'},
            {'id': 'shot2', 'gps_lat': 37.7750, 'gps_lon': -122.4195,
             'hole_number': 2, 'swing_number': 1, 'club_type': 'IRON_7'}
        ]
        viz.load_shots(shots_data)
        viz.set_shot_filters(hole_numbers=[1])
        result = viz.to_dict()
        assert len(result['shot_markers']) == 1
        assert result['filters']['hole_numbers'] == [1]
