"""Tests for distance calculation and shot management."""

import pytest
import tempfile
import os
import time
from ar_golf_tracker.ar_glasses.distance_calculator import DistanceCalculationService
from ar_golf_tracker.ar_glasses.shot_manager import ShotManager
from ar_golf_tracker.ar_glasses.database import LocalDatabase
from ar_golf_tracker.shared.models import (
    GPSPosition, DistanceUnit, DistanceAccuracy, ClubType
)


def test_distance_calculator_initialization():
    """Test distance calculator can be initialized with default unit."""
    calc = DistanceCalculationService(default_unit=DistanceUnit.YARDS)
    assert calc.default_unit == DistanceUnit.YARDS


def test_haversine_distance_calculation():
    """Test basic Haversine distance calculation."""
    calc = DistanceCalculationService()
    
    # Two positions approximately 100 meters apart
    pos1 = GPSPosition(
        latitude=37.7749,
        longitude=-122.4194,
        accuracy=5.0,
        timestamp=int(time.time())
    )
    
    pos2 = GPSPosition(
        latitude=37.7758,  # ~100m north
        longitude=-122.4194,
        accuracy=5.0,
        timestamp=int(time.time())
    )
    
    distance = calc.calculate_distance(pos1, pos2, unit=DistanceUnit.METERS)
    
    # Should be approximately 100 meters (allowing for some calculation variance)
    assert 95 <= distance.value <= 105
    assert distance.unit == DistanceUnit.METERS
    assert distance.accuracy == DistanceAccuracy.HIGH


def test_distance_accuracy_classification():
    """Test distance accuracy classification based on GPS accuracy."""
    calc = DistanceCalculationService()
    
    # HIGH accuracy: both positions < 10m
    pos1_high = GPSPosition(37.7749, -122.4194, accuracy=5.0, timestamp=int(time.time()))
    pos2_high = GPSPosition(37.7758, -122.4194, accuracy=8.0, timestamp=int(time.time()))
    
    distance_high = calc.calculate_distance(pos1_high, pos2_high)
    assert distance_high.accuracy == DistanceAccuracy.HIGH
    
    # MEDIUM accuracy: one position 10-20m
    pos1_medium = GPSPosition(37.7749, -122.4194, accuracy=15.0, timestamp=int(time.time()))
    pos2_medium = GPSPosition(37.7758, -122.4194, accuracy=5.0, timestamp=int(time.time()))
    
    distance_medium = calc.calculate_distance(pos1_medium, pos2_medium)
    assert distance_medium.accuracy == DistanceAccuracy.MEDIUM
    
    # LOW accuracy: one position > 20m
    pos1_low = GPSPosition(37.7749, -122.4194, accuracy=25.0, timestamp=int(time.time()))
    pos2_low = GPSPosition(37.7758, -122.4194, accuracy=5.0, timestamp=int(time.time()))
    
    distance_low = calc.calculate_distance(pos1_low, pos2_low)
    assert distance_low.accuracy == DistanceAccuracy.LOW


def test_distance_with_elevation():
    """Test distance calculation includes elevation changes."""
    calc = DistanceCalculationService()
    
    # Two positions with elevation difference
    pos1 = GPSPosition(
        latitude=37.7749,
        longitude=-122.4194,
        accuracy=5.0,
        timestamp=int(time.time()),
        altitude=10.0
    )
    
    pos2 = GPSPosition(
        latitude=37.7758,
        longitude=-122.4194,
        accuracy=5.0,
        timestamp=int(time.time()),
        altitude=50.0  # 40m elevation gain
    )
    
    distance = calc.calculate_distance(pos1, pos2, unit=DistanceUnit.METERS)
    
    # Distance should be greater than horizontal distance due to elevation
    # Horizontal ~100m, vertical 40m, total should be ~sqrt(100^2 + 40^2) ≈ 107m
    assert distance.value > 100
    assert distance.value < 115


def test_yards_to_meters_conversion():
    """Test distance unit conversion."""
    calc = DistanceCalculationService()
    
    pos1 = GPSPosition(37.7749, -122.4194, accuracy=5.0, timestamp=int(time.time()))
    pos2 = GPSPosition(37.7758, -122.4194, accuracy=5.0, timestamp=int(time.time()))
    
    distance_meters = calc.calculate_distance(pos1, pos2, unit=DistanceUnit.METERS)
    distance_yards = calc.calculate_distance(pos1, pos2, unit=DistanceUnit.YARDS)
    
    # 1 meter = 1.09361 yards
    expected_yards = distance_meters.value * 1.09361
    assert abs(distance_yards.value - expected_yards) < 0.2  # Allow small rounding difference


def test_shot_manager_records_shot():
    """Test shot manager can record a shot."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name
    
    try:
        db = LocalDatabase(db_path)
        db.initialize_schema()
        
        manager = ShotManager(db)
        
        gps_pos = GPSPosition(
            latitude=37.7749,
            longitude=-122.4194,
            accuracy=5.0,
            timestamp=int(time.time())
        )
        
        shot = manager.record_shot(
            round_id="round-001",
            hole_number=1,
            club_type=ClubType.DRIVER,
            gps_position=gps_pos
        )
        
        assert shot.id is not None
        assert shot.hole_number == 1
        assert shot.swing_number == 1
        assert shot.club_type == ClubType.DRIVER
        assert shot.distance is None  # First shot has no distance
        
        db.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_shot_manager_calculates_distance_automatically():
    """Test shot manager automatically calculates distance between shots."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name
    
    try:
        db = LocalDatabase(db_path)
        db.initialize_schema()
        
        manager = ShotManager(db, distance_unit=DistanceUnit.YARDS)
        
        # Record first shot
        pos1 = GPSPosition(
            latitude=37.7749,
            longitude=-122.4194,
            accuracy=5.0,
            timestamp=int(time.time())
        )
        
        shot1 = manager.record_shot(
            round_id="round-001",
            hole_number=1,
            club_type=ClubType.DRIVER,
            gps_position=pos1
        )
        
        assert shot1.distance is None
        
        # Record second shot (approximately 100m away)
        pos2 = GPSPosition(
            latitude=37.7758,
            longitude=-122.4194,
            accuracy=5.0,
            timestamp=int(time.time())
        )
        
        shot2 = manager.record_shot(
            round_id="round-001",
            hole_number=1,
            club_type=ClubType.IRON_7,
            gps_position=pos2
        )
        
        # Second shot should have swing number 2
        assert shot2.swing_number == 2
        assert shot2.distance is None  # Current shot doesn't have distance yet
        
        # First shot should now have distance calculated
        updated_shot1 = manager.get_shot(shot1.id)
        assert updated_shot1.distance is not None
        assert updated_shot1.distance.value > 0
        assert updated_shot1.distance.unit == DistanceUnit.YARDS
        assert updated_shot1.distance.accuracy == DistanceAccuracy.HIGH
        
        db.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_shot_manager_multiple_holes():
    """Test shot manager handles shots on different holes correctly."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name
    
    try:
        db = LocalDatabase(db_path)
        db.initialize_schema()
        
        manager = ShotManager(db)
        
        # Record shots on hole 1
        pos1 = GPSPosition(37.7749, -122.4194, accuracy=5.0, timestamp=int(time.time()))
        shot1 = manager.record_shot("round-001", 1, ClubType.DRIVER, pos1)
        
        pos2 = GPSPosition(37.7758, -122.4194, accuracy=5.0, timestamp=int(time.time()))
        shot2 = manager.record_shot("round-001", 1, ClubType.IRON_7, pos2)
        
        # Record shot on hole 2 (should start at swing 1 again)
        pos3 = GPSPosition(37.7770, -122.4200, accuracy=5.0, timestamp=int(time.time()))
        shot3 = manager.record_shot("round-001", 2, ClubType.DRIVER, pos3)
        
        assert shot1.swing_number == 1
        assert shot2.swing_number == 2
        assert shot3.swing_number == 1  # New hole, reset swing number
        
        # Shot 1 should have distance to shot 2
        updated_shot1 = manager.get_shot(shot1.id)
        assert updated_shot1.distance is not None
        
        # Shot 2 should not have distance (no third shot on hole 1)
        updated_shot2 = manager.get_shot(shot2.id)
        assert updated_shot2.distance is None
        
        # Shot 3 should not have distance (first shot on hole 2)
        assert shot3.distance is None
        
        db.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


# Edge case tests for distance calculation

def test_distance_with_missing_altitude_one_position():
    """Test distance calculation when only one position has altitude data."""
    calc = DistanceCalculationService()
    
    # Position 1 has altitude, position 2 does not
    pos1 = GPSPosition(
        latitude=37.7749,
        longitude=-122.4194,
        accuracy=5.0,
        timestamp=int(time.time()),
        altitude=10.0
    )
    
    pos2 = GPSPosition(
        latitude=37.7758,
        longitude=-122.4194,
        accuracy=5.0,
        timestamp=int(time.time())
        # No altitude
    )
    
    distance = calc.calculate_distance(pos1, pos2, unit=DistanceUnit.METERS)
    
    # Should calculate horizontal distance only (no elevation adjustment)
    assert 95 <= distance.value <= 105
    assert distance.accuracy == DistanceAccuracy.HIGH


def test_distance_with_missing_altitude_both_positions():
    """Test distance calculation when both positions lack altitude data."""
    calc = DistanceCalculationService()
    
    # Neither position has altitude
    pos1 = GPSPosition(
        latitude=37.7749,
        longitude=-122.4194,
        accuracy=5.0,
        timestamp=int(time.time())
    )
    
    pos2 = GPSPosition(
        latitude=37.7758,
        longitude=-122.4194,
        accuracy=5.0,
        timestamp=int(time.time())
    )
    
    distance = calc.calculate_distance(pos1, pos2, unit=DistanceUnit.METERS)
    
    # Should calculate horizontal distance only
    assert 95 <= distance.value <= 105
    assert distance.accuracy == DistanceAccuracy.HIGH


def test_distance_accuracy_boundary_high_to_medium():
    """Test distance accuracy at the boundary between HIGH and MEDIUM (10m)."""
    calc = DistanceCalculationService()
    
    # Just above 10m threshold - should be MEDIUM
    pos1 = GPSPosition(37.7749, -122.4194, accuracy=10.1, timestamp=int(time.time()))
    pos2 = GPSPosition(37.7758, -122.4194, accuracy=5.0, timestamp=int(time.time()))
    
    distance = calc.calculate_distance(pos1, pos2)
    assert distance.accuracy == DistanceAccuracy.MEDIUM
    
    # Exactly at 10m - should be HIGH (boundary is exclusive)
    pos1_boundary = GPSPosition(37.7749, -122.4194, accuracy=10.0, timestamp=int(time.time()))
    pos2_boundary = GPSPosition(37.7758, -122.4194, accuracy=5.0, timestamp=int(time.time()))
    
    distance_boundary = calc.calculate_distance(pos1_boundary, pos2_boundary)
    assert distance_boundary.accuracy == DistanceAccuracy.HIGH
    
    # Just below 10m - should be HIGH
    pos1_high = GPSPosition(37.7749, -122.4194, accuracy=9.9, timestamp=int(time.time()))
    pos2_high = GPSPosition(37.7758, -122.4194, accuracy=5.0, timestamp=int(time.time()))
    
    distance_high = calc.calculate_distance(pos1_high, pos2_high)
    assert distance_high.accuracy == DistanceAccuracy.HIGH


def test_distance_accuracy_boundary_medium_to_low():
    """Test distance accuracy at the boundary between MEDIUM and LOW (20m)."""
    calc = DistanceCalculationService()
    
    # Just above 20m threshold - should be LOW
    pos1 = GPSPosition(37.7749, -122.4194, accuracy=20.1, timestamp=int(time.time()))
    pos2 = GPSPosition(37.7758, -122.4194, accuracy=5.0, timestamp=int(time.time()))
    
    distance = calc.calculate_distance(pos1, pos2)
    assert distance.accuracy == DistanceAccuracy.LOW
    
    # Exactly at 20m threshold - should be MEDIUM (boundary is exclusive)
    pos1_boundary = GPSPosition(37.7749, -122.4194, accuracy=20.0, timestamp=int(time.time()))
    pos2_boundary = GPSPosition(37.7758, -122.4194, accuracy=5.0, timestamp=int(time.time()))
    
    distance_boundary = calc.calculate_distance(pos1_boundary, pos2_boundary)
    assert distance_boundary.accuracy == DistanceAccuracy.MEDIUM
    
    # Just below 20m - should be MEDIUM
    pos1_medium = GPSPosition(37.7749, -122.4194, accuracy=19.9, timestamp=int(time.time()))
    pos2_medium = GPSPosition(37.7758, -122.4194, accuracy=5.0, timestamp=int(time.time()))
    
    distance_medium = calc.calculate_distance(pos1_medium, pos2_medium)
    assert distance_medium.accuracy == DistanceAccuracy.MEDIUM


def test_distance_with_very_poor_gps_accuracy():
    """Test distance calculation with very poor GPS accuracy (>50m)."""
    calc = DistanceCalculationService()
    
    # Both positions have very poor accuracy
    pos1 = GPSPosition(37.7749, -122.4194, accuracy=60.0, timestamp=int(time.time()))
    pos2 = GPSPosition(37.7758, -122.4194, accuracy=55.0, timestamp=int(time.time()))
    
    distance = calc.calculate_distance(pos1, pos2, unit=DistanceUnit.METERS)
    
    # Should still calculate distance but mark as LOW accuracy
    assert 95 <= distance.value <= 105
    assert distance.accuracy == DistanceAccuracy.LOW


def test_shots_on_different_holes_no_distance():
    """Test that shots on different holes do not calculate distance between them."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name
    
    try:
        db = LocalDatabase(db_path)
        db.initialize_schema()
        
        manager = ShotManager(db)
        
        # Record last shot on hole 1
        pos1 = GPSPosition(37.7749, -122.4194, accuracy=5.0, timestamp=int(time.time()))
        shot1_hole1 = manager.record_shot("round-001", 1, ClubType.IRON_7, pos1)
        
        # Record first shot on hole 2 (different hole)
        pos2 = GPSPosition(37.7758, -122.4194, accuracy=5.0, timestamp=int(time.time()))
        shot1_hole2 = manager.record_shot("round-001", 2, ClubType.DRIVER, pos2)
        
        # Last shot on hole 1 should NOT have distance calculated
        # (because next shot is on a different hole)
        updated_shot1 = manager.get_shot(shot1_hole1.id)
        assert updated_shot1.distance is None
        
        # First shot on hole 2 should not have distance
        assert shot1_hole2.distance is None
        
        db.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_distance_with_zero_elevation_change():
    """Test distance calculation with altitude data but no elevation change."""
    calc = DistanceCalculationService()
    
    # Both positions at same altitude
    pos1 = GPSPosition(
        latitude=37.7749,
        longitude=-122.4194,
        accuracy=5.0,
        timestamp=int(time.time()),
        altitude=100.0
    )
    
    pos2 = GPSPosition(
        latitude=37.7758,
        longitude=-122.4194,
        accuracy=5.0,
        timestamp=int(time.time()),
        altitude=100.0
    )
    
    distance = calc.calculate_distance(pos1, pos2, unit=DistanceUnit.METERS)
    
    # Should be same as horizontal distance (no elevation adjustment)
    assert 95 <= distance.value <= 105
    assert distance.accuracy == DistanceAccuracy.HIGH
