"""Unit tests for round detail view component."""

import pytest
from datetime import datetime
from ar_golf_tracker.mobile_app.round_detail_view import (
    ShotDetail,
    HoleDetail,
    RoundDetailView
)


class TestShotDetail:
    """Tests for ShotDetail class."""
    
    def test_init(self):
        """Test initialization with shot data."""
        shot_data = {
            'id': 'shot-123',
            'round_id': 'round-456',
            'hole_number': 1,
            'swing_number': 1,
            'club_type': 'DRIVER',
            'shot_time': '2024-01-15T14:30:00Z',
            'gps_lat': 36.5674,
            'gps_lon': -121.9500,
            'gps_accuracy': 5.0,
            'gps_altitude': 10.0,
            'distance_yards': 250.5,
            'distance_accuracy': 'HIGH',
            'notes': 'Great drive!'
        }
        
        shot = ShotDetail(shot_data)
        
        assert shot.id == 'shot-123'
        assert shot.round_id == 'round-456'
        assert shot.hole_number == 1
        assert shot.swing_number == 1
        assert shot.club_type == 'DRIVER'
        assert shot.gps_lat == 36.5674
        assert shot.gps_lon == -121.9500
        assert shot.gps_accuracy == 5.0
        assert shot.distance_yards == 250.5
        assert shot.notes == 'Great drive!'
    
    def test_get_club_display_name(self):
        """Test club display name formatting."""
        test_cases = [
            ('DRIVER', 'Driver'),
            ('WOOD_3', '3 Wood'),
            ('IRON_7', '7 Iron'),
            ('PITCHING_WEDGE', 'Pitching Wedge'),
            ('PUTTER', 'Putter')
        ]
        
        for club_type, expected_name in test_cases:
            shot_data = {
                'id': 'shot-123',
                'round_id': 'round-456',
                'hole_number': 1,
                'swing_number': 1,
                'club_type': club_type,
                'shot_time': '2024-01-15T14:30:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0
            }
            shot = ShotDetail(shot_data)
            assert shot.get_club_display_name() == expected_name
    
    def test_get_distance_string(self):
        """Test distance string formatting."""
        shot_data = {
            'id': 'shot-123',
            'round_id': 'round-456',
            'hole_number': 1,
            'swing_number': 1,
            'club_type': 'DRIVER',
            'shot_time': '2024-01-15T14:30:00Z',
            'gps_lat': 36.5674,
            'gps_lon': -121.9500,
            'gps_accuracy': 5.0,
            'distance_yards': 250.7
        }
        
        shot = ShotDetail(shot_data)
        distance_str = shot.get_distance_string()
        
        assert '250 yards' in distance_str
    
    def test_get_distance_string_no_distance(self):
        """Test distance string when distance is not available."""
        shot_data = {
            'id': 'shot-123',
            'round_id': 'round-456',
            'hole_number': 1,
            'swing_number': 1,
            'club_type': 'DRIVER',
            'shot_time': '2024-01-15T14:30:00Z',
            'gps_lat': 36.5674,
            'gps_lon': -121.9500,
            'gps_accuracy': 5.0
        }
        
        shot = ShotDetail(shot_data)
        distance_str = shot.get_distance_string()
        
        assert distance_str == "N/A"
    
    def test_get_gps_accuracy_string(self):
        """Test GPS accuracy string formatting."""
        test_cases = [
            (5.0, 'High'),
            (15.0, 'Medium'),
            (25.0, 'Low')
        ]
        
        for accuracy, expected_level in test_cases:
            shot_data = {
                'id': 'shot-123',
                'round_id': 'round-456',
                'hole_number': 1,
                'swing_number': 1,
                'club_type': 'DRIVER',
                'shot_time': '2024-01-15T14:30:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': accuracy
            }
            shot = ShotDetail(shot_data)
            accuracy_str = shot.get_gps_accuracy_string()
            assert expected_level in accuracy_str
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        shot_data = {
            'id': 'shot-123',
            'round_id': 'round-456',
            'hole_number': 1,
            'swing_number': 1,
            'club_type': 'DRIVER',
            'shot_time': '2024-01-15T14:30:00Z',
            'gps_lat': 36.5674,
            'gps_lon': -121.9500,
            'gps_accuracy': 5.0,
            'distance_yards': 250.5
        }
        
        shot = ShotDetail(shot_data)
        data = shot.to_dict()
        
        assert data['id'] == 'shot-123'
        assert data['hole_number'] == 1
        assert data['club'] == 'Driver'
        assert data['distance_yards'] == 250.5


class TestHoleDetail:
    """Tests for HoleDetail class."""
    
    def test_init(self):
        """Test initialization with shots."""
        shots = [
            ShotDetail({
                'id': 'shot-1',
                'round_id': 'round-456',
                'hole_number': 1,
                'swing_number': 1,
                'club_type': 'DRIVER',
                'shot_time': '2024-01-15T14:30:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0
            }),
            ShotDetail({
                'id': 'shot-2',
                'round_id': 'round-456',
                'hole_number': 1,
                'swing_number': 2,
                'club_type': 'IRON_7',
                'shot_time': '2024-01-15T14:31:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0
            })
        ]
        
        hole = HoleDetail(1, shots)
        
        assert hole.hole_number == 1
        assert len(hole.shots) == 2
    
    def test_shots_sorted_by_swing_number(self):
        """Test that shots are sorted by swing number."""
        shots = [
            ShotDetail({
                'id': 'shot-2',
                'round_id': 'round-456',
                'hole_number': 1,
                'swing_number': 2,
                'club_type': 'IRON_7',
                'shot_time': '2024-01-15T14:31:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0
            }),
            ShotDetail({
                'id': 'shot-1',
                'round_id': 'round-456',
                'hole_number': 1,
                'swing_number': 1,
                'club_type': 'DRIVER',
                'shot_time': '2024-01-15T14:30:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0
            })
        ]
        
        hole = HoleDetail(1, shots)
        
        assert hole.shots[0].swing_number == 1
        assert hole.shots[1].swing_number == 2
    
    def test_get_shot_count(self):
        """Test shot count."""
        shots = [
            ShotDetail({
                'id': f'shot-{i}',
                'round_id': 'round-456',
                'hole_number': 1,
                'swing_number': i,
                'club_type': 'DRIVER',
                'shot_time': '2024-01-15T14:30:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0
            })
            for i in range(1, 5)
        ]
        
        hole = HoleDetail(1, shots)
        
        assert hole.get_shot_count() == 4
    
    def test_get_total_distance(self):
        """Test total distance calculation."""
        shots = [
            ShotDetail({
                'id': 'shot-1',
                'round_id': 'round-456',
                'hole_number': 1,
                'swing_number': 1,
                'club_type': 'DRIVER',
                'shot_time': '2024-01-15T14:30:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0,
                'distance_yards': 250.0
            }),
            ShotDetail({
                'id': 'shot-2',
                'round_id': 'round-456',
                'hole_number': 1,
                'swing_number': 2,
                'club_type': 'IRON_7',
                'shot_time': '2024-01-15T14:31:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0,
                'distance_yards': 150.0
            })
        ]
        
        hole = HoleDetail(1, shots)
        total = hole.get_total_distance()
        
        assert total == 400.0
    
    def test_get_total_distance_no_distances(self):
        """Test total distance when no distances available."""
        shots = [
            ShotDetail({
                'id': 'shot-1',
                'round_id': 'round-456',
                'hole_number': 1,
                'swing_number': 1,
                'club_type': 'DRIVER',
                'shot_time': '2024-01-15T14:30:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0
            })
        ]
        
        hole = HoleDetail(1, shots)
        total = hole.get_total_distance()
        
        assert total is None
    
    def test_get_clubs_used(self):
        """Test clubs used list."""
        shots = [
            ShotDetail({
                'id': 'shot-1',
                'round_id': 'round-456',
                'hole_number': 1,
                'swing_number': 1,
                'club_type': 'DRIVER',
                'shot_time': '2024-01-15T14:30:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0
            }),
            ShotDetail({
                'id': 'shot-2',
                'round_id': 'round-456',
                'hole_number': 1,
                'swing_number': 2,
                'club_type': 'IRON_7',
                'shot_time': '2024-01-15T14:31:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0
            })
        ]
        
        hole = HoleDetail(1, shots)
        clubs = hole.get_clubs_used()
        
        assert clubs == ['Driver', '7 Iron']
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        shots = [
            ShotDetail({
                'id': 'shot-1',
                'round_id': 'round-456',
                'hole_number': 1,
                'swing_number': 1,
                'club_type': 'DRIVER',
                'shot_time': '2024-01-15T14:30:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0,
                'distance_yards': 250.0
            })
        ]
        
        hole = HoleDetail(1, shots)
        data = hole.to_dict()
        
        assert data['hole_number'] == 1
        assert data['shot_count'] == 1
        assert len(data['shots']) == 1


class TestRoundDetailView:
    """Tests for RoundDetailView class."""
    
    def test_init(self):
        """Test initialization."""
        view = RoundDetailView()
        
        assert view.round_id is None
        assert view.round_data is None
        assert len(view.shots) == 0
        assert len(view.holes) == 0
    
    def test_load_round(self):
        """Test loading round data."""
        view = RoundDetailView()
        round_data = {
            'id': 'round-123',
            'course_name': 'Pebble Beach',
            'start_time': '2024-01-15T14:30:00Z',
            'end_time': '2024-01-15T18:45:00Z'
        }
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
                'gps_accuracy': 5.0
            },
            {
                'id': 'shot-2',
                'round_id': 'round-123',
                'hole_number': 1,
                'swing_number': 2,
                'club_type': 'IRON_7',
                'shot_time': '2024-01-15T14:31:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0
            }
        ]
        
        view.load_round(round_data, shots_data)
        
        assert view.round_id == 'round-123'
        assert len(view.shots) == 2
        assert len(view.holes) == 1
    
    def test_load_round_with_course_data(self):
        """Test loading round with course data."""
        view = RoundDetailView()
        round_data = {
            'id': 'round-123',
            'course_name': 'Pebble Beach',
            'start_time': '2024-01-15T14:30:00Z'
        }
        shots_data = []
        course_data = {
            'id': 'course-456',
            'name': 'Pebble Beach',
            'par': 72,
            'yardage': 6800
        }
        
        view.load_round(round_data, shots_data, course_data)
        
        assert view.course_data is not None
        assert view.course_data['par'] == 72
    
    def test_group_shots_by_hole(self):
        """Test grouping shots by hole."""
        view = RoundDetailView()
        round_data = {
            'id': 'round-123',
            'course_name': 'Test Course',
            'start_time': '2024-01-15T14:30:00Z'
        }
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
                'gps_accuracy': 5.0
            },
            {
                'id': 'shot-2',
                'round_id': 'round-123',
                'hole_number': 2,
                'swing_number': 1,
                'club_type': 'DRIVER',
                'shot_time': '2024-01-15T14:35:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0
            },
            {
                'id': 'shot-3',
                'round_id': 'round-123',
                'hole_number': 1,
                'swing_number': 2,
                'club_type': 'IRON_7',
                'shot_time': '2024-01-15T14:31:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0
            }
        ]
        
        view.load_round(round_data, shots_data)
        
        assert len(view.holes) == 2
        hole1 = view.get_hole_by_number(1)
        assert hole1 is not None
        assert hole1.get_shot_count() == 2
    
    def test_get_round_summary(self):
        """Test round summary."""
        view = RoundDetailView()
        round_data = {
            'id': 'round-123',
            'course_name': 'Pebble Beach',
            'start_time': '2024-01-15T14:30:00Z',
            'end_time': '2024-01-15T18:45:00Z'
        }
        shots_data = [
            {
                'id': f'shot-{i}',
                'round_id': 'round-123',
                'hole_number': (i % 18) + 1,
                'swing_number': 1,
                'club_type': 'DRIVER',
                'shot_time': '2024-01-15T14:30:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0
            }
            for i in range(72)
        ]
        
        view.load_round(round_data, shots_data)
        summary = view.get_round_summary()
        
        assert summary['round_id'] == 'round-123'
        assert summary['course_name'] == 'Pebble Beach'
        assert summary['total_shots'] == 72
        assert summary['holes_played'] == 18
        assert summary['duration'] is not None
    
    def test_get_course_info(self):
        """Test course info retrieval."""
        view = RoundDetailView()
        round_data = {
            'id': 'round-123',
            'course_name': 'Pebble Beach',
            'start_time': '2024-01-15T14:30:00Z'
        }
        course_data = {
            'id': 'course-456',
            'name': 'Pebble Beach',
            'address': '1700 17 Mile Dr, Pebble Beach, CA',
            'total_holes': 18,
            'par': 72,
            'yardage': 6828,
            'rating': 75.5,
            'slope': 145
        }
        
        view.load_round(round_data, [], course_data)
        course_info = view.get_course_info()
        
        assert course_info is not None
        assert course_info['name'] == 'Pebble Beach'
        assert course_info['par'] == 72
        assert course_info['yardage'] == 6828
    
    def test_get_course_info_no_data(self):
        """Test course info when no course data available."""
        view = RoundDetailView()
        
        course_info = view.get_course_info()
        
        assert course_info is None
    
    def test_get_shot_by_id(self):
        """Test getting shot by ID."""
        view = RoundDetailView()
        round_data = {
            'id': 'round-123',
            'course_name': 'Test Course',
            'start_time': '2024-01-15T14:30:00Z'
        }
        shots_data = [
            {
                'id': 'shot-123',
                'round_id': 'round-123',
                'hole_number': 1,
                'swing_number': 1,
                'club_type': 'DRIVER',
                'shot_time': '2024-01-15T14:30:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0
            }
        ]
        
        view.load_round(round_data, shots_data)
        shot = view.get_shot_by_id('shot-123')
        
        assert shot is not None
        assert shot.id == 'shot-123'
    
    def test_get_shots_by_club(self):
        """Test getting shots by club type."""
        view = RoundDetailView()
        round_data = {
            'id': 'round-123',
            'course_name': 'Test Course',
            'start_time': '2024-01-15T14:30:00Z'
        }
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
                'gps_accuracy': 5.0
            },
            {
                'id': 'shot-2',
                'round_id': 'round-123',
                'hole_number': 2,
                'swing_number': 1,
                'club_type': 'DRIVER',
                'shot_time': '2024-01-15T14:35:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0
            },
            {
                'id': 'shot-3',
                'round_id': 'round-123',
                'hole_number': 1,
                'swing_number': 2,
                'club_type': 'IRON_7',
                'shot_time': '2024-01-15T14:31:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0
            }
        ]
        
        view.load_round(round_data, shots_data)
        driver_shots = view.get_shots_by_club('DRIVER')
        
        assert len(driver_shots) == 2
        assert all(s.club_type == 'DRIVER' for s in driver_shots)
    
    def test_get_club_usage_summary(self):
        """Test club usage summary."""
        view = RoundDetailView()
        round_data = {
            'id': 'round-123',
            'course_name': 'Test Course',
            'start_time': '2024-01-15T14:30:00Z'
        }
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
                'gps_accuracy': 5.0
            },
            {
                'id': 'shot-2',
                'round_id': 'round-123',
                'hole_number': 2,
                'swing_number': 1,
                'club_type': 'DRIVER',
                'shot_time': '2024-01-15T14:35:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0
            },
            {
                'id': 'shot-3',
                'round_id': 'round-123',
                'hole_number': 1,
                'swing_number': 2,
                'club_type': 'IRON_7',
                'shot_time': '2024-01-15T14:31:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0
            }
        ]
        
        view.load_round(round_data, shots_data)
        usage = view.get_club_usage_summary()
        
        assert usage['Driver'] == 2
        assert usage['7 Iron'] == 1
    
    def test_get_average_distance_by_club(self):
        """Test average distance calculation by club."""
        view = RoundDetailView()
        round_data = {
            'id': 'round-123',
            'course_name': 'Test Course',
            'start_time': '2024-01-15T14:30:00Z'
        }
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
                'distance_yards': 250.0
            },
            {
                'id': 'shot-2',
                'round_id': 'round-123',
                'hole_number': 2,
                'swing_number': 1,
                'club_type': 'DRIVER',
                'shot_time': '2024-01-15T14:35:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0,
                'distance_yards': 270.0
            },
            {
                'id': 'shot-3',
                'round_id': 'round-123',
                'hole_number': 1,
                'swing_number': 2,
                'club_type': 'IRON_7',
                'shot_time': '2024-01-15T14:31:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0,
                'distance_yards': 150.0
            }
        ]
        
        view.load_round(round_data, shots_data)
        averages = view.get_average_distance_by_club()
        
        assert averages['Driver'] == 260.0
        assert averages['7 Iron'] == 150.0
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        view = RoundDetailView()
        round_data = {
            'id': 'round-123',
            'course_name': 'Pebble Beach',
            'start_time': '2024-01-15T14:30:00Z'
        }
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
                'gps_accuracy': 5.0
            }
        ]
        
        view.load_round(round_data, shots_data)
        data = view.to_dict()
        
        assert 'summary' in data
        assert 'holes' in data
        assert 'club_usage' in data
        assert 'average_distances' in data
