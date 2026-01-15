"""Tests for core data models."""

import pytest
from ar_golf_tracker.shared.models import (
    ClubType,
    DistanceUnit,
    DistanceAccuracy,
    SyncStatus,
    GPSPosition,
    Distance,
    Shot,
    Round,
)


def test_club_type_enum():
    """Test ClubType enum has all required club types."""
    assert ClubType.DRIVER.value == "DRIVER"
    assert ClubType.PUTTER.value == "PUTTER"
    assert ClubType.IRON_7.value == "IRON_7"
    assert len(ClubType) == 17  # 14 standard clubs + 3 woods/hybrids


def test_gps_position_creation():
    """Test GPSPosition dataclass creation."""
    pos = GPSPosition(
        latitude=37.7749,
        longitude=-122.4194,
        accuracy=5.0,
        timestamp=1234567890,
        altitude=100.0
    )
    assert pos.latitude == 37.7749
    assert pos.longitude == -122.4194
    assert pos.accuracy == 5.0
    assert pos.altitude == 100.0


def test_distance_creation():
    """Test Distance dataclass with accuracy."""
    distance = Distance(
        value=250.5,
        unit=DistanceUnit.YARDS,
        accuracy=DistanceAccuracy.HIGH
    )
    assert distance.value == 250.5
    assert distance.unit == DistanceUnit.YARDS
    assert distance.accuracy == DistanceAccuracy.HIGH


def test_shot_creation():
    """Test Shot dataclass creation."""
    gps_pos = GPSPosition(
        latitude=37.7749,
        longitude=-122.4194,
        accuracy=5.0,
        timestamp=1234567890
    )
    
    shot = Shot(
        id="shot-123",
        round_id="round-456",
        hole_number=1,
        swing_number=1,
        club_type=ClubType.DRIVER,
        timestamp=1234567890,
        gps_origin=gps_pos,
        sync_status=SyncStatus.PENDING
    )
    
    assert shot.id == "shot-123"
    assert shot.hole_number == 1
    assert shot.club_type == ClubType.DRIVER
    assert shot.distance is None  # Optional field


def test_round_creation():
    """Test Round dataclass creation."""
    round_obj = Round(
        id="round-123",
        user_id="user-456",
        course_id="course-789",
        course_name="Pebble Beach",
        start_time=1234567890,
        sync_status=SyncStatus.PENDING
    )
    
    assert round_obj.id == "round-123"
    assert round_obj.course_name == "Pebble Beach"
    assert len(round_obj.shots) == 0  # Empty list by default
    assert round_obj.end_time is None  # Optional field
