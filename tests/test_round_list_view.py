"""Unit tests for round list view component."""

import pytest
from datetime import datetime, timedelta
from ar_golf_tracker.mobile_app.round_list_view import (
    RoundListItem,
    RoundListView
)


class TestRoundListItem:
    """Tests for RoundListItem class."""
    
    def test_init_with_basic_data(self):
        """Test initialization with basic round data."""
        round_data = {
            'id': 'round-123',
            'course_id': 'course-456',
            'course_name': 'Pebble Beach',
            'start_time': '2024-01-15T14:30:00Z',
            'end_time': '2024-01-15T18:45:00Z'
        }
        
        item = RoundListItem(round_data)
        
        assert item.id == 'round-123'
        assert item.course_id == 'course-456'
        assert item.course_name == 'Pebble Beach'
        assert item.start_time is not None
        assert item.end_time is not None
    
    def test_init_with_shots(self):
        """Test initialization with shots data."""
        round_data = {
            'id': 'round-123',
            'course_name': 'Augusta National',
            'start_time': '2024-01-15T14:30:00Z'
        }
        shots = [
            {'id': 'shot-1', 'hole_number': 1, 'club_type': 'DRIVER'},
            {'id': 'shot-2', 'hole_number': 1, 'club_type': 'IRON_7'},
            {'id': 'shot-3', 'hole_number': 2, 'club_type': 'DRIVER'}
        ]
        
        item = RoundListItem(round_data, shots)
        
        assert len(item.shots) == 3
        assert item.calculate_total_shots() == 3
    
    def test_get_date_string(self):
        """Test date string formatting."""
        round_data = {
            'id': 'round-123',
            'course_name': 'Test Course',
            'start_time': '2024-01-15T14:30:00Z'
        }
        
        item = RoundListItem(round_data)
        date_str = item.get_date_string()
        
        assert 'Jan' in date_str
        assert '15' in date_str
        assert '2024' in date_str
    
    def test_get_time_string(self):
        """Test time string formatting."""
        round_data = {
            'id': 'round-123',
            'course_name': 'Test Course',
            'start_time': '2024-01-15T14:30:00Z'
        }
        
        item = RoundListItem(round_data)
        time_str = item.get_time_string()
        
        assert 'PM' in time_str or 'AM' in time_str
    
    def test_get_duration_string(self):
        """Test duration calculation."""
        round_data = {
            'id': 'round-123',
            'course_name': 'Test Course',
            'start_time': '2024-01-15T14:30:00Z',
            'end_time': '2024-01-15T18:45:00Z'
        }
        
        item = RoundListItem(round_data)
        duration = item.get_duration_string()
        
        assert 'h' in duration
        assert 'm' in duration
    
    def test_get_duration_string_no_end_time(self):
        """Test duration when end time is missing."""
        round_data = {
            'id': 'round-123',
            'course_name': 'Test Course',
            'start_time': '2024-01-15T14:30:00Z'
        }
        
        item = RoundListItem(round_data)
        duration = item.get_duration_string()
        
        assert duration == ""
    
    def test_calculate_total_shots(self):
        """Test total shots calculation."""
        round_data = {
            'id': 'round-123',
            'course_name': 'Test Course',
            'start_time': '2024-01-15T14:30:00Z'
        }
        shots = [{'id': f'shot-{i}'} for i in range(72)]
        
        item = RoundListItem(round_data, shots)
        
        assert item.calculate_total_shots() == 72
    
    def test_calculate_score(self):
        """Test score calculation."""
        round_data = {
            'id': 'round-123',
            'course_name': 'Test Course',
            'start_time': '2024-01-15T14:30:00Z'
        }
        shots = [{'id': f'shot-{i}'} for i in range(85)]
        
        item = RoundListItem(round_data, shots)
        score = item.calculate_score()
        
        assert score == 85
    
    def test_calculate_score_no_shots(self):
        """Test score calculation with no shots."""
        round_data = {
            'id': 'round-123',
            'course_name': 'Test Course',
            'start_time': '2024-01-15T14:30:00Z'
        }
        
        item = RoundListItem(round_data)
        score = item.calculate_score()
        
        assert score is None
    
    def test_calculate_score_relative_to_par(self):
        """Test relative score calculation."""
        round_data = {
            'id': 'round-123',
            'course_name': 'Test Course',
            'start_time': '2024-01-15T14:30:00Z'
        }
        
        # Test over par
        shots = [{'id': f'shot-{i}'} for i in range(77)]
        item = RoundListItem(round_data, shots)
        assert item.calculate_score_relative_to_par(72) == "+5"
        
        # Test even par
        shots = [{'id': f'shot-{i}'} for i in range(72)]
        item = RoundListItem(round_data, shots)
        assert item.calculate_score_relative_to_par(72) == "E"
        
        # Test under par
        shots = [{'id': f'shot-{i}'} for i in range(69)]
        item = RoundListItem(round_data, shots)
        assert item.calculate_score_relative_to_par(72) == "-3"
    
    def test_get_holes_played(self):
        """Test holes played calculation."""
        round_data = {
            'id': 'round-123',
            'course_name': 'Test Course',
            'start_time': '2024-01-15T14:30:00Z'
        }
        shots = [
            {'id': 'shot-1', 'hole_number': 1},
            {'id': 'shot-2', 'hole_number': 1},
            {'id': 'shot-3', 'hole_number': 2},
            {'id': 'shot-4', 'hole_number': 3},
            {'id': 'shot-5', 'hole_number': 3}
        ]
        
        item = RoundListItem(round_data, shots)
        
        assert item.get_holes_played() == 3
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        round_data = {
            'id': 'round-123',
            'course_id': 'course-456',
            'course_name': 'Test Course',
            'start_time': '2024-01-15T14:30:00Z',
            'end_time': '2024-01-15T18:45:00Z'
        }
        shots = [{'id': f'shot-{i}', 'hole_number': i % 18 + 1} for i in range(72)]
        
        item = RoundListItem(round_data, shots)
        data = item.to_dict()
        
        assert data['id'] == 'round-123'
        assert data['course_name'] == 'Test Course'
        assert data['total_shots'] == 72
        assert data['holes_played'] == 18


class TestRoundListView:
    """Tests for RoundListView class."""
    
    def test_init(self):
        """Test initialization."""
        view = RoundListView()
        
        assert len(view.rounds) == 0
        assert view.selected_round_id is None
        assert view.sort_order == 'desc'
    
    def test_load_rounds(self):
        """Test loading rounds data."""
        view = RoundListView()
        rounds_data = [
            {
                'id': 'round-1',
                'course_name': 'Course A',
                'start_time': '2024-01-15T14:30:00Z'
            },
            {
                'id': 'round-2',
                'course_name': 'Course B',
                'start_time': '2024-01-16T14:30:00Z'
            }
        ]
        
        view.load_rounds(rounds_data)
        
        assert len(view.rounds) == 2
        assert view.rounds[0].id == 'round-2'  # Newest first (desc)
        assert view.rounds[1].id == 'round-1'
    
    def test_load_rounds_with_shots(self):
        """Test loading rounds with shots."""
        view = RoundListView()
        rounds_data = [
            {
                'id': 'round-1',
                'course_name': 'Course A',
                'start_time': '2024-01-15T14:30:00Z'
            }
        ]
        shots_by_round = {
            'round-1': [
                {'id': 'shot-1', 'hole_number': 1},
                {'id': 'shot-2', 'hole_number': 1}
            ]
        }
        
        view.load_rounds_with_shots(rounds_data, shots_by_round)
        
        assert len(view.rounds) == 1
        assert len(view.rounds[0].shots) == 2
    
    def test_set_sort_order_asc(self):
        """Test ascending sort order."""
        view = RoundListView()
        rounds_data = [
            {
                'id': 'round-1',
                'course_name': 'Course A',
                'start_time': '2024-01-15T14:30:00Z'
            },
            {
                'id': 'round-2',
                'course_name': 'Course B',
                'start_time': '2024-01-16T14:30:00Z'
            }
        ]
        view.load_rounds(rounds_data)
        
        view.set_sort_order('asc')
        
        assert view.rounds[0].id == 'round-1'  # Oldest first
        assert view.rounds[1].id == 'round-2'
    
    def test_set_course_filter(self):
        """Test course filtering."""
        view = RoundListView()
        rounds_data = [
            {
                'id': 'round-1',
                'course_name': 'Pebble Beach',
                'start_time': '2024-01-15T14:30:00Z'
            },
            {
                'id': 'round-2',
                'course_name': 'Augusta National',
                'start_time': '2024-01-16T14:30:00Z'
            },
            {
                'id': 'round-3',
                'course_name': 'Pebble Beach',
                'start_time': '2024-01-17T14:30:00Z'
            }
        ]
        view.load_rounds(rounds_data)
        
        view.set_course_filter('Pebble Beach')
        filtered = view.get_filtered_rounds()
        
        assert len(filtered) == 2
        assert all(r.course_name == 'Pebble Beach' for r in filtered)
    
    def test_get_round_count(self):
        """Test round count."""
        view = RoundListView()
        rounds_data = [
            {
                'id': f'round-{i}',
                'course_name': 'Test Course',
                'start_time': '2024-01-15T14:30:00Z'
            }
            for i in range(5)
        ]
        view.load_rounds(rounds_data)
        
        assert view.get_round_count() == 5
    
    def test_get_round_by_id(self):
        """Test getting round by ID."""
        view = RoundListView()
        rounds_data = [
            {
                'id': 'round-123',
                'course_name': 'Test Course',
                'start_time': '2024-01-15T14:30:00Z'
            }
        ]
        view.load_rounds(rounds_data)
        
        round_item = view.get_round_by_id('round-123')
        
        assert round_item is not None
        assert round_item.id == 'round-123'
    
    def test_get_round_by_id_not_found(self):
        """Test getting non-existent round."""
        view = RoundListView()
        view.load_rounds([])
        
        round_item = view.get_round_by_id('nonexistent')
        
        assert round_item is None
    
    def test_select_round(self):
        """Test round selection."""
        view = RoundListView()
        rounds_data = [
            {
                'id': 'round-123',
                'course_name': 'Test Course',
                'start_time': '2024-01-15T14:30:00Z'
            }
        ]
        view.load_rounds(rounds_data)
        
        selected = view.select_round('round-123')
        
        assert selected is True
        assert view.selected_round_id == 'round-123'
    
    def test_select_round_not_found(self):
        """Test selecting non-existent round."""
        view = RoundListView()
        view.load_rounds([])
        
        selected = view.select_round('nonexistent')
        
        assert selected is False
        assert view.selected_round_id is None
    
    def test_get_selected_round(self):
        """Test getting selected round."""
        view = RoundListView()
        rounds_data = [
            {
                'id': 'round-123',
                'course_name': 'Test Course',
                'start_time': '2024-01-15T14:30:00Z'
            }
        ]
        view.load_rounds(rounds_data)
        view.select_round('round-123')
        
        selected = view.get_selected_round()
        
        assert selected is not None
        assert selected.id == 'round-123'
    
    def test_clear_selection(self):
        """Test clearing selection."""
        view = RoundListView()
        rounds_data = [
            {
                'id': 'round-123',
                'course_name': 'Test Course',
                'start_time': '2024-01-15T14:30:00Z'
            }
        ]
        view.load_rounds(rounds_data)
        view.select_round('round-123')
        
        view.clear_selection()
        
        assert view.selected_round_id is None
        assert view.get_selected_round() is None
    
    def test_on_round_selected_callback(self):
        """Test round selection callback."""
        view = RoundListView()
        rounds_data = [
            {
                'id': 'round-123',
                'course_name': 'Test Course',
                'start_time': '2024-01-15T14:30:00Z'
            }
        ]
        view.load_rounds(rounds_data)
        
        callback_called = []
        def callback(round_id):
            callback_called.append(round_id)
        
        view.set_on_round_selected_callback(callback)
        view.select_round('round-123')
        
        assert len(callback_called) == 1
        assert callback_called[0] == 'round-123'
    
    def test_get_unique_courses(self):
        """Test getting unique course names."""
        view = RoundListView()
        rounds_data = [
            {
                'id': 'round-1',
                'course_name': 'Pebble Beach',
                'start_time': '2024-01-15T14:30:00Z'
            },
            {
                'id': 'round-2',
                'course_name': 'Augusta National',
                'start_time': '2024-01-16T14:30:00Z'
            },
            {
                'id': 'round-3',
                'course_name': 'Pebble Beach',
                'start_time': '2024-01-17T14:30:00Z'
            }
        ]
        view.load_rounds(rounds_data)
        
        courses = view.get_unique_courses()
        
        assert len(courses) == 2
        assert 'Pebble Beach' in courses
        assert 'Augusta National' in courses
    
    def test_get_rounds_summary(self):
        """Test rounds summary."""
        view = RoundListView()
        rounds_data = [
            {
                'id': 'round-1',
                'course_name': 'Course A',
                'start_time': '2024-01-15T14:30:00Z'
            },
            {
                'id': 'round-2',
                'course_name': 'Course B',
                'start_time': '2024-01-16T14:30:00Z'
            }
        ]
        shots_by_round = {
            'round-1': [{'id': f'shot-{i}'} for i in range(72)],
            'round-2': [{'id': f'shot-{i}'} for i in range(85)]
        }
        view.load_rounds_with_shots(rounds_data, shots_by_round)
        
        summary = view.get_rounds_summary()
        
        assert summary['total_rounds'] == 2
        assert summary['total_shots'] == 157
        assert summary['unique_courses'] == 2
        assert summary['date_range'] is not None
    
    def test_get_rounds_summary_empty(self):
        """Test rounds summary with no rounds."""
        view = RoundListView()
        
        summary = view.get_rounds_summary()
        
        assert summary['total_rounds'] == 0
        assert summary['total_shots'] == 0
        assert summary['unique_courses'] == 0
        assert summary['date_range'] is None
    
    def test_to_list_data(self):
        """Test conversion to list data."""
        view = RoundListView()
        rounds_data = [
            {
                'id': 'round-1',
                'course_name': 'Test Course',
                'start_time': '2024-01-15T14:30:00Z'
            }
        ]
        view.load_rounds(rounds_data)
        
        list_data = view.to_list_data()
        
        assert len(list_data) == 1
        assert list_data[0]['id'] == 'round-1'
        assert list_data[0]['course_name'] == 'Test Course'
