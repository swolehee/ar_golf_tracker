"""Unit tests for shot detail view component."""

import pytest
from ar_golf_tracker.mobile_app.shot_detail_view import (
    ShotFilter,
    ShotDetailView
)


class TestShotFilter:
    """Tests for ShotFilter class."""
    
    def test_init_empty(self):
        """Test initialization with no filters."""
        filter = ShotFilter()
        
        assert filter.hole_numbers is None
        assert filter.club_types is None
        assert filter.distance_range is None
        assert filter.is_empty()
    
    def test_init_with_values(self):
        """Test initialization with filter values."""
        filter = ShotFilter(
            hole_numbers=[1, 2, 3],
            club_types=['DRIVER', 'IRON_7'],
            distance_range=(100.0, 300.0)
        )
        
        assert filter.hole_numbers == [1, 2, 3]
        assert filter.club_types == ['DRIVER', 'IRON_7']
        assert filter.distance_range == (100.0, 300.0)
        assert not filter.is_empty()
    
    def test_matches_no_filters(self):
        """Test matching with no filters (should match all)."""
        filter = ShotFilter()
        shot_data = {
            'id': 'shot-1',
            'hole_number': 1,
            'club_type': 'DRIVER',
            'distance_yards': 250.0
        }
        
        assert filter.matches(shot_data)
    
    def test_matches_hole_filter(self):
        """Test matching with hole number filter."""
        filter = ShotFilter(hole_numbers=[1, 2])
        
        shot1 = {'hole_number': 1, 'club_type': 'DRIVER'}
        shot2 = {'hole_number': 3, 'club_type': 'DRIVER'}
        
        assert filter.matches(shot1)
        assert not filter.matches(shot2)
    
    def test_matches_club_filter(self):
        """Test matching with club type filter."""
        filter = ShotFilter(club_types=['DRIVER', 'IRON_7'])
        
        shot1 = {'hole_number': 1, 'club_type': 'DRIVER'}
        shot2 = {'hole_number': 1, 'club_type': 'PUTTER'}
        
        assert filter.matches(shot1)
        assert not filter.matches(shot2)
    
    def test_matches_distance_filter(self):
        """Test matching with distance range filter."""
        filter = ShotFilter(distance_range=(100.0, 200.0))
        
        shot1 = {'hole_number': 1, 'distance_yards': 150.0}
        shot2 = {'hole_number': 1, 'distance_yards': 250.0}
        shot3 = {'hole_number': 1}  # No distance
        
        assert filter.matches(shot1)
        assert not filter.matches(shot2)
        assert not filter.matches(shot3)
    
    def test_matches_combined_filters(self):
        """Test matching with multiple filters."""
        filter = ShotFilter(
            hole_numbers=[1, 2],
            club_types=['DRIVER'],
            distance_range=(200.0, 300.0)
        )
        
        shot1 = {
            'hole_number': 1,
            'club_type': 'DRIVER',
            'distance_yards': 250.0
        }
        shot2 = {
            'hole_number': 3,  # Wrong hole
            'club_type': 'DRIVER',
            'distance_yards': 250.0
        }
        shot3 = {
            'hole_number': 1,
            'club_type': 'IRON_7',  # Wrong club
            'distance_yards': 250.0
        }
        shot4 = {
            'hole_number': 1,
            'club_type': 'DRIVER',
            'distance_yards': 150.0  # Wrong distance
        }
        
        assert filter.matches(shot1)
        assert not filter.matches(shot2)
        assert not filter.matches(shot3)
        assert not filter.matches(shot4)
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        filter = ShotFilter(
            hole_numbers=[1, 2],
            club_types=['DRIVER'],
            distance_range=(100.0, 200.0)
        )
        
        data = filter.to_dict()
        
        assert data['hole_numbers'] == [1, 2]
        assert data['club_types'] == ['DRIVER']
        assert data['distance_range'] == (100.0, 200.0)


class TestShotDetailView:
    """Tests for ShotDetailView class."""
    
    def test_init(self):
        """Test initialization."""
        view = ShotDetailView()
        
        assert view.selected_shot_id is None
        assert view.selected_shot_data is None
        assert len(view.all_shots) == 0
        assert view.current_filter.is_empty()
    
    def test_load_shots(self):
        """Test loading shot data."""
        view = ShotDetailView()
        shots_data = [
            {
                'id': 'shot-1',
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
        
        view.load_shots(shots_data)
        
        assert len(view.all_shots) == 2
    
    def test_select_shot(self):
        """Test selecting a shot."""
        view = ShotDetailView()
        shots_data = [
            {
                'id': 'shot-123',
                'hole_number': 1,
                'swing_number': 1,
                'club_type': 'DRIVER',
                'shot_time': '2024-01-15T14:30:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0
            }
        ]
        
        view.load_shots(shots_data)
        result = view.select_shot('shot-123')
        
        assert result is True
        assert view.selected_shot_id == 'shot-123'
        assert view.selected_shot_data is not None
    
    def test_select_shot_not_found(self):
        """Test selecting a non-existent shot."""
        view = ShotDetailView()
        view.load_shots([])
        
        result = view.select_shot('nonexistent')
        
        assert result is False
        assert view.selected_shot_id is None
    
    def test_deselect_shot(self):
        """Test deselecting a shot."""
        view = ShotDetailView()
        shots_data = [
            {
                'id': 'shot-123',
                'hole_number': 1,
                'swing_number': 1,
                'club_type': 'DRIVER',
                'shot_time': '2024-01-15T14:30:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0
            }
        ]
        
        view.load_shots(shots_data)
        view.select_shot('shot-123')
        view.deselect_shot()
        
        assert view.selected_shot_id is None
        assert view.selected_shot_data is None
    
    def test_get_selected_shot_details(self):
        """Test getting selected shot details."""
        view = ShotDetailView()
        shots_data = [
            {
                'id': 'shot-123',
                'hole_number': 1,
                'swing_number': 1,
                'club_type': 'DRIVER',
                'shot_time': '2024-01-15T14:30:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0,
                'distance_yards': 250.5,
                'distance_accuracy': 'HIGH',
                'notes': 'Great drive!'
            }
        ]
        
        view.load_shots(shots_data)
        view.select_shot('shot-123')
        details = view.get_selected_shot_details()
        
        assert details is not None
        assert details['shot_id'] == 'shot-123'
        assert details['hole_number'] == 1
        assert details['swing_number'] == 1
        assert details['club'] == 'Driver'
        assert details['club_type'] == 'DRIVER'
        assert '250 yards' in details['distance']
        assert 'HIGH' in details['distance']
        assert details['gps_location']['latitude'] == 36.5674
        assert details['gps_location']['longitude'] == -121.9500
        assert 'High' in details['gps_location']['accuracy']
        assert details['notes'] == 'Great drive!'
    
    def test_get_selected_shot_details_no_selection(self):
        """Test getting details when no shot selected."""
        view = ShotDetailView()
        
        details = view.get_selected_shot_details()
        
        assert details is None
    
    def test_get_selected_shot_details_no_distance(self):
        """Test getting details for shot without distance."""
        view = ShotDetailView()
        shots_data = [
            {
                'id': 'shot-123',
                'hole_number': 1,
                'swing_number': 1,
                'club_type': 'DRIVER',
                'shot_time': '2024-01-15T14:30:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0
            }
        ]
        
        view.load_shots(shots_data)
        view.select_shot('shot-123')
        details = view.get_selected_shot_details()
        
        assert details['distance'] == 'N/A'
    
    def test_set_filter(self):
        """Test setting filter."""
        view = ShotDetailView()
        
        view.set_filter(
            hole_numbers=[1, 2],
            club_types=['DRIVER'],
            distance_range=(100.0, 200.0)
        )
        
        filter = view.get_current_filter()
        assert filter.hole_numbers == [1, 2]
        assert filter.club_types == ['DRIVER']
        assert filter.distance_range == (100.0, 200.0)
    
    def test_clear_filter(self):
        """Test clearing filter."""
        view = ShotDetailView()
        view.set_filter(hole_numbers=[1, 2])
        
        view.clear_filter()
        
        filter = view.get_current_filter()
        assert filter.is_empty()
    
    def test_get_filtered_shots(self):
        """Test getting filtered shots."""
        view = ShotDetailView()
        shots_data = [
            {
                'id': 'shot-1',
                'hole_number': 1,
                'club_type': 'DRIVER',
                'distance_yards': 250.0
            },
            {
                'id': 'shot-2',
                'hole_number': 2,
                'club_type': 'DRIVER',
                'distance_yards': 260.0
            },
            {
                'id': 'shot-3',
                'hole_number': 1,
                'club_type': 'IRON_7',
                'distance_yards': 150.0
            }
        ]
        
        view.load_shots(shots_data)
        view.set_filter(hole_numbers=[1])
        
        filtered = view.get_filtered_shots()
        
        assert len(filtered) == 2
        assert all(s['hole_number'] == 1 for s in filtered)
    
    def test_get_filtered_shots_no_filter(self):
        """Test getting shots with no filter (returns all)."""
        view = ShotDetailView()
        shots_data = [
            {'id': 'shot-1', 'hole_number': 1},
            {'id': 'shot-2', 'hole_number': 2}
        ]
        
        view.load_shots(shots_data)
        filtered = view.get_filtered_shots()
        
        assert len(filtered) == 2
    
    def test_get_filtered_shot_count(self):
        """Test getting filtered shot count."""
        view = ShotDetailView()
        shots_data = [
            {'id': 'shot-1', 'hole_number': 1, 'club_type': 'DRIVER'},
            {'id': 'shot-2', 'hole_number': 2, 'club_type': 'DRIVER'},
            {'id': 'shot-3', 'hole_number': 1, 'club_type': 'IRON_7'}
        ]
        
        view.load_shots(shots_data)
        view.set_filter(club_types=['DRIVER'])
        
        count = view.get_filtered_shot_count()
        
        assert count == 2
    
    def test_get_available_holes(self):
        """Test getting available hole numbers."""
        view = ShotDetailView()
        shots_data = [
            {'id': 'shot-1', 'hole_number': 1},
            {'id': 'shot-2', 'hole_number': 3},
            {'id': 'shot-3', 'hole_number': 1},
            {'id': 'shot-4', 'hole_number': 2}
        ]
        
        view.load_shots(shots_data)
        holes = view.get_available_holes()
        
        assert holes == [1, 2, 3]
    
    def test_get_available_clubs(self):
        """Test getting available club types."""
        view = ShotDetailView()
        shots_data = [
            {'id': 'shot-1', 'club_type': 'DRIVER'},
            {'id': 'shot-2', 'club_type': 'IRON_7'},
            {'id': 'shot-3', 'club_type': 'DRIVER'},
            {'id': 'shot-4', 'club_type': 'PUTTER'}
        ]
        
        view.load_shots(shots_data)
        clubs = view.get_available_clubs()
        
        assert clubs == ['DRIVER', 'IRON_7', 'PUTTER']
    
    def test_get_distance_range(self):
        """Test getting distance range."""
        view = ShotDetailView()
        shots_data = [
            {'id': 'shot-1', 'distance_yards': 250.0},
            {'id': 'shot-2', 'distance_yards': 150.0},
            {'id': 'shot-3', 'distance_yards': 300.0}
        ]
        
        view.load_shots(shots_data)
        range = view.get_distance_range()
        
        assert range == (150.0, 300.0)
    
    def test_get_distance_range_no_distances(self):
        """Test getting distance range when no distances available."""
        view = ShotDetailView()
        shots_data = [
            {'id': 'shot-1', 'hole_number': 1},
            {'id': 'shot-2', 'hole_number': 2}
        ]
        
        view.load_shots(shots_data)
        range = view.get_distance_range()
        
        assert range is None
    
    def test_filter_by_hole(self):
        """Test filtering by hole numbers."""
        view = ShotDetailView()
        shots_data = [
            {'id': 'shot-1', 'hole_number': 1},
            {'id': 'shot-2', 'hole_number': 2},
            {'id': 'shot-3', 'hole_number': 3}
        ]
        
        view.load_shots(shots_data)
        view.filter_by_hole([1, 3])
        
        filtered = view.get_filtered_shots()
        assert len(filtered) == 2
        assert all(s['hole_number'] in [1, 3] for s in filtered)
    
    def test_filter_by_club(self):
        """Test filtering by club types."""
        view = ShotDetailView()
        shots_data = [
            {'id': 'shot-1', 'club_type': 'DRIVER'},
            {'id': 'shot-2', 'club_type': 'IRON_7'},
            {'id': 'shot-3', 'club_type': 'DRIVER'}
        ]
        
        view.load_shots(shots_data)
        view.filter_by_club(['DRIVER'])
        
        filtered = view.get_filtered_shots()
        assert len(filtered) == 2
        assert all(s['club_type'] == 'DRIVER' for s in filtered)
    
    def test_filter_by_distance(self):
        """Test filtering by distance range."""
        view = ShotDetailView()
        shots_data = [
            {'id': 'shot-1', 'distance_yards': 100.0},
            {'id': 'shot-2', 'distance_yards': 200.0},
            {'id': 'shot-3', 'distance_yards': 300.0}
        ]
        
        view.load_shots(shots_data)
        view.filter_by_distance(150.0, 250.0)
        
        filtered = view.get_filtered_shots()
        assert len(filtered) == 1
        assert filtered[0]['distance_yards'] == 200.0
    
    def test_get_shots_by_hole(self):
        """Test getting shots by hole number."""
        view = ShotDetailView()
        shots_data = [
            {'id': 'shot-1', 'hole_number': 1},
            {'id': 'shot-2', 'hole_number': 2},
            {'id': 'shot-3', 'hole_number': 1}
        ]
        
        view.load_shots(shots_data)
        shots = view.get_shots_by_hole(1)
        
        assert len(shots) == 2
        assert all(s['hole_number'] == 1 for s in shots)
    
    def test_get_shots_by_club(self):
        """Test getting shots by club type."""
        view = ShotDetailView()
        shots_data = [
            {'id': 'shot-1', 'club_type': 'DRIVER'},
            {'id': 'shot-2', 'club_type': 'IRON_7'},
            {'id': 'shot-3', 'club_type': 'DRIVER'}
        ]
        
        view.load_shots(shots_data)
        shots = view.get_shots_by_club('DRIVER')
        
        assert len(shots) == 2
        assert all(s['club_type'] == 'DRIVER' for s in shots)
    
    def test_get_shots_in_distance_range(self):
        """Test getting shots in distance range."""
        view = ShotDetailView()
        shots_data = [
            {'id': 'shot-1', 'distance_yards': 100.0},
            {'id': 'shot-2', 'distance_yards': 200.0},
            {'id': 'shot-3', 'distance_yards': 300.0},
            {'id': 'shot-4'}  # No distance
        ]
        
        view.load_shots(shots_data)
        shots = view.get_shots_in_distance_range(150.0, 250.0)
        
        assert len(shots) == 1
        assert shots[0]['distance_yards'] == 200.0
    
    def test_filter_change_callback(self):
        """Test filter change callback."""
        view = ShotDetailView()
        callback_called = []
        
        def callback(filter):
            callback_called.append(filter)
        
        view.set_on_filter_change_callback(callback)
        view.set_filter(hole_numbers=[1, 2])
        
        assert len(callback_called) == 1
        assert callback_called[0].hole_numbers == [1, 2]
    
    def test_filter_change_callback_on_clear(self):
        """Test filter change callback when clearing."""
        view = ShotDetailView()
        callback_called = []
        
        def callback(filter):
            callback_called.append(filter)
        
        view.set_on_filter_change_callback(callback)
        view.set_filter(hole_numbers=[1, 2])
        view.clear_filter()
        
        assert len(callback_called) == 2
        assert callback_called[1].is_empty()
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        view = ShotDetailView()
        shots_data = [
            {
                'id': 'shot-1',
                'hole_number': 1,
                'club_type': 'DRIVER',
                'distance_yards': 250.0,
                'shot_time': '2024-01-15T14:30:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0
            },
            {
                'id': 'shot-2',
                'hole_number': 2,
                'club_type': 'IRON_7',
                'distance_yards': 150.0,
                'shot_time': '2024-01-15T14:35:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0
            }
        ]
        
        view.load_shots(shots_data)
        view.select_shot('shot-1')
        view.set_filter(hole_numbers=[1])
        
        data = view.to_dict()
        
        assert data['selected_shot'] is not None
        assert data['selected_shot']['shot_id'] == 'shot-1'
        assert data['current_filter']['hole_numbers'] == [1]
        assert data['filtered_shot_count'] == 1
        assert data['total_shot_count'] == 2
        assert data['available_holes'] == [1, 2]
        assert 'DRIVER' in data['available_clubs']
        assert data['distance_range'] == (150.0, 250.0)
    
    def test_club_display_names(self):
        """Test club display name formatting."""
        view = ShotDetailView()
        test_cases = [
            ('DRIVER', 'Driver'),
            ('WOOD_3', '3 Wood'),
            ('IRON_7', '7 Iron'),
            ('PITCHING_WEDGE', 'Pitching Wedge'),
            ('PUTTER', 'Putter')
        ]
        
        for club_type, expected_name in test_cases:
            shots_data = [{
                'id': 'shot-1',
                'hole_number': 1,
                'club_type': club_type,
                'shot_time': '2024-01-15T14:30:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': 5.0
            }]
            
            view.load_shots(shots_data)
            view.select_shot('shot-1')
            details = view.get_selected_shot_details()
            
            assert details['club'] == expected_name
    
    def test_gps_accuracy_levels(self):
        """Test GPS accuracy level formatting."""
        view = ShotDetailView()
        test_cases = [
            (5.0, 'High'),
            (15.0, 'Medium'),
            (25.0, 'Low')
        ]
        
        for accuracy, expected_level in test_cases:
            shots_data = [{
                'id': 'shot-1',
                'hole_number': 1,
                'club_type': 'DRIVER',
                'shot_time': '2024-01-15T14:30:00Z',
                'gps_lat': 36.5674,
                'gps_lon': -121.9500,
                'gps_accuracy': accuracy
            }]
            
            view.load_shots(shots_data)
            view.select_shot('shot-1')
            details = view.get_selected_shot_details()
            
            assert expected_level in details['gps_location']['accuracy']
