"""Round list view component for mobile app.

Displays completed rounds with date, course, and score information.
Implements round selection for detail view.
"""

from typing import List, Dict, Any, Optional, Callable
from datetime import datetime


class RoundListItem:
    """Represents a single round in the list view."""
    
    def __init__(self, round_data: Dict[str, Any], shots: Optional[List[Dict[str, Any]]] = None):
        """Initialize round list item.
        
        Args:
            round_data: Round data from API
            shots: Optional list of shots for score calculation
        """
        self.id = round_data['id']
        self.course_id = round_data.get('course_id')
        self.course_name = round_data['course_name']
        self.start_time = self._parse_datetime(round_data['start_time'])
        self.end_time = self._parse_datetime(round_data.get('end_time'))
        self.weather_conditions = round_data.get('weather_conditions')
        self.shots = shots or []
        
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
            # Try ISO format
            try:
                return datetime.fromisoformat(dt_value.replace('Z', '+00:00'))
            except ValueError:
                pass
        return None
    
    def get_date_string(self) -> str:
        """Get formatted date string for display.
        
        Returns:
            Formatted date (e.g., "Jan 15, 2024")
        """
        if self.start_time:
            return self.start_time.strftime("%b %d, %Y")
        return "Unknown Date"
    
    def get_time_string(self) -> str:
        """Get formatted time string for display.
        
        Returns:
            Formatted time (e.g., "2:30 PM")
        """
        if self.start_time:
            return self.start_time.strftime("%I:%M %p")
        return ""
    
    def get_duration_string(self) -> str:
        """Get formatted duration string.
        
        Returns:
            Duration string (e.g., "4h 15m") or empty if not available
        """
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        return ""
    
    def calculate_total_shots(self) -> int:
        """Calculate total number of shots in the round.
        
        Returns:
            Total shot count
        """
        return len(self.shots)
    
    def calculate_score(self, course_par: Optional[int] = None) -> Optional[int]:
        """Calculate total score for the round.
        
        Args:
            course_par: Course par (optional, for relative scoring)
            
        Returns:
            Total score (number of shots) or None if no shots
        """
        if not self.shots:
            return None
        return len(self.shots)
    
    def calculate_score_relative_to_par(self, course_par: int) -> Optional[str]:
        """Calculate score relative to par.
        
        Args:
            course_par: Course par
            
        Returns:
            Score relative to par (e.g., "+5", "E", "-2") or None
        """
        score = self.calculate_score()
        if score is None:
            return None
        
        diff = score - course_par
        if diff == 0:
            return "E"
        elif diff > 0:
            return f"+{diff}"
        else:
            return str(diff)
    
    def get_holes_played(self) -> int:
        """Get number of unique holes played.
        
        Returns:
            Number of holes
        """
        if not self.shots:
            return 0
        return len(set(shot['hole_number'] for shot in self.shots))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            'id': self.id,
            'course_id': self.course_id,
            'course_name': self.course_name,
            'date': self.get_date_string(),
            'time': self.get_time_string(),
            'duration': self.get_duration_string(),
            'total_shots': self.calculate_total_shots(),
            'holes_played': self.get_holes_played(),
            'weather': self.weather_conditions
        }


class RoundListView:
    """View component for displaying list of completed rounds."""
    
    def __init__(self):
        """Initialize round list view."""
        self.rounds: List[RoundListItem] = []
        self.selected_round_id: Optional[str] = None
        self.on_round_selected: Optional[Callable[[str], None]] = None
        self.sort_order = 'desc'  # 'desc' for newest first, 'asc' for oldest first
        self.filter_course: Optional[str] = None
    
    def load_rounds(self, rounds_data: List[Dict[str, Any]]) -> None:
        """Load rounds data into the view.
        
        Args:
            rounds_data: List of round dictionaries from API
        """
        self.rounds = [RoundListItem(round_data) for round_data in rounds_data]
        self._apply_sort()
    
    def load_rounds_with_shots(self, rounds_data: List[Dict[str, Any]], 
                               shots_by_round: Dict[str, List[Dict[str, Any]]]) -> None:
        """Load rounds with their associated shots.
        
        Args:
            rounds_data: List of round dictionaries from API
            shots_by_round: Dictionary mapping round_id to list of shots
        """
        self.rounds = [
            RoundListItem(round_data, shots_by_round.get(round_data['id'], []))
            for round_data in rounds_data
        ]
        self._apply_sort()
    
    def _apply_sort(self) -> None:
        """Apply current sort order to rounds."""
        reverse = (self.sort_order == 'desc')
        self.rounds.sort(
            key=lambda r: r.start_time if r.start_time else datetime.min,
            reverse=reverse
        )
    
    def set_sort_order(self, order: str) -> None:
        """Set sort order for rounds.
        
        Args:
            order: 'desc' for newest first, 'asc' for oldest first
        """
        if order in ['desc', 'asc']:
            self.sort_order = order
            self._apply_sort()
    
    def set_course_filter(self, course_name: Optional[str]) -> None:
        """Filter rounds by course name.
        
        Args:
            course_name: Course name to filter by, or None to show all
        """
        self.filter_course = course_name
    
    def get_filtered_rounds(self) -> List[RoundListItem]:
        """Get rounds after applying filters.
        
        Returns:
            Filtered list of rounds
        """
        if self.filter_course:
            return [r for r in self.rounds if r.course_name == self.filter_course]
        return self.rounds
    
    def get_round_count(self) -> int:
        """Get total number of rounds.
        
        Returns:
            Number of rounds
        """
        return len(self.get_filtered_rounds())
    
    def get_round_by_id(self, round_id: str) -> Optional[RoundListItem]:
        """Get round by ID.
        
        Args:
            round_id: Round ID
            
        Returns:
            Round item or None if not found
        """
        for round_item in self.rounds:
            if round_item.id == round_id:
                return round_item
        return None
    
    def select_round(self, round_id: str) -> bool:
        """Select a round for detail view.
        
        Args:
            round_id: Round ID to select
            
        Returns:
            True if round found and selected, False otherwise
        """
        round_item = self.get_round_by_id(round_id)
        if round_item:
            self.selected_round_id = round_id
            if self.on_round_selected:
                self.on_round_selected(round_id)
            return True
        return False
    
    def get_selected_round(self) -> Optional[RoundListItem]:
        """Get currently selected round.
        
        Returns:
            Selected round item or None
        """
        if self.selected_round_id:
            return self.get_round_by_id(self.selected_round_id)
        return None
    
    def clear_selection(self) -> None:
        """Clear round selection."""
        self.selected_round_id = None
    
    def set_on_round_selected_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for when a round is selected.
        
        Args:
            callback: Function to call with round_id when round is selected
        """
        self.on_round_selected = callback
    
    def get_unique_courses(self) -> List[str]:
        """Get list of unique course names from all rounds.
        
        Returns:
            List of course names
        """
        courses = set(r.course_name for r in self.rounds)
        return sorted(list(courses))
    
    def get_rounds_summary(self) -> Dict[str, Any]:
        """Get summary statistics for all rounds.
        
        Returns:
            Dictionary with summary statistics
        """
        filtered_rounds = self.get_filtered_rounds()
        
        if not filtered_rounds:
            return {
                'total_rounds': 0,
                'total_shots': 0,
                'unique_courses': 0,
                'date_range': None
            }
        
        total_shots = sum(r.calculate_total_shots() for r in filtered_rounds)
        dates = [r.start_time for r in filtered_rounds if r.start_time]
        
        date_range = None
        if dates:
            earliest = min(dates)
            latest = max(dates)
            date_range = {
                'earliest': earliest.strftime("%b %d, %Y"),
                'latest': latest.strftime("%b %d, %Y")
            }
        
        return {
            'total_rounds': len(filtered_rounds),
            'total_shots': total_shots,
            'unique_courses': len(self.get_unique_courses()),
            'date_range': date_range
        }
    
    def to_list_data(self) -> List[Dict[str, Any]]:
        """Convert rounds to list data for UI rendering.
        
        Returns:
            List of round dictionaries
        """
        return [round_item.to_dict() for round_item in self.get_filtered_rounds()]
