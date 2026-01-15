"""Tests for course identification and hole detection services."""

import pytest
from ar_golf_tracker.backend.database import CloudDatabase
from ar_golf_tracker.backend.course_service import CourseService
from ar_golf_tracker.backend.sample_courses import load_sample_courses
from ar_golf_tracker.ar_glasses.hole_detector import HoleDetector
from ar_golf_tracker.shared.models import GPSPosition


@pytest.fixture
def test_db():
    """Create a test database with sample data."""
    db = CloudDatabase(
        host="localhost",
        database="ar_golf_tracker_test",
        user="postgres",
        password=""
    )
    
    try:
        conn = db.connect()
        # Initialize schema
        db.initialize_schema()
        # Load sample courses
        load_sample_courses(db)
        yield db
    finally:
        # Cleanup
        if db.connection and not db.connection.closed:
            with db.connection.cursor() as cursor:
                cursor.execute("DROP TABLE IF EXISTS user_shots CASCADE")
                cursor.execute("DROP TABLE IF EXISTS user_rounds CASCADE")
                cursor.execute("DROP TABLE IF EXISTS holes CASCADE")
                cursor.execute("DROP TABLE IF EXISTS courses CASCADE")
                cursor.execute("DROP TABLE IF EXISTS users CASCADE")
            db.connection.commit()
        db.close()


def test_find_courses_by_location(test_db):
    """Test finding courses near a GPS location."""
    service = CourseService(test_db)
    
    # Search near Pebble Beach (36.5674, -121.9500)
    courses = service.find_courses_by_location(36.5674, -121.9500, radius_meters=1000)
    
    assert len(courses) > 0
    assert courses[0][1] == "Pebble Beach Golf Links"
    assert courses[0][2] < 1000  # Distance should be within radius


def test_identify_course(test_db):
    """Test course identification."""
    service = CourseService(test_db)
    
    # Identify course at Pebble Beach location
    course_id = service.identify_course(36.5674, -121.9500)
    
    assert course_id is not None


def test_load_course(test_db):
    """Test loading complete course data."""
    service = CourseService(test_db)
    
    # Find and load Pebble Beach
    course_id = service.identify_course(36.5674, -121.9500)
    course = service.load_course(course_id)
    
    assert course is not None
    assert course.name == "Pebble Beach Golf Links"
    assert course.total_holes == 18
    assert len(course.holes) == 18
    assert course.holes[0].hole_number == 1


def test_get_course_layout(test_db):
    """Test getting course layout information."""
    service = CourseService(test_db)
    
    # Find and get layout for Pebble Beach
    course_id = service.identify_course(36.5674, -121.9500)
    layout = service.get_course_layout(course_id)
    
    assert layout is not None
    assert layout["course_name"] == "Pebble Beach Golf Links"
    assert len(layout["holes"]) == 18
    assert layout["holes"][0]["hole_number"] == 1


def test_hole_detector_generic_mode():
    """Test hole detector in generic mode."""
    detector = HoleDetector()
    
    # Set to generic mode
    detector.set_course(None)
    
    assert detector.is_generic_mode()
    assert detector.get_current_hole() == 1
    
    # Manual increment should work
    detector.increment_hole()
    assert detector.get_current_hole() == 2


def test_hole_detector_with_course(test_db):
    """Test hole detector with course data."""
    service = CourseService(test_db)
    detector = HoleDetector()
    
    # Find Pebble Beach
    course_id = service.identify_course(36.5674, -121.9500)
    detector.set_course(course_id)
    
    assert not detector.is_generic_mode()
    assert detector.get_current_hole() == 1
    
    # Test position near hole 2 tee box
    position = GPSPosition(
        latitude=36.5681,
        longitude=-121.9506,
        accuracy=5.0,
        timestamp=0
    )
    
    new_hole = detector.detect_hole_transition(position, test_db.connection)
    
    # Should detect transition to hole 2
    if new_hole is not None:
        assert new_hole == 2
