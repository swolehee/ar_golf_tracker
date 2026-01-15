"""Integration tests for GPS tracking and local storage."""

import pytest
import time
import tempfile
import os
from ar_golf_tracker.ar_glasses.gps_tracking import GPSTrackingService
from ar_golf_tracker.ar_glasses.database import LocalDatabase
from ar_golf_tracker.shared.models import (
    Shot, GPSPosition, ClubType, SyncStatus
)


def test_gps_tracking_service_initialization():
    """Test GPS tracking service can be initialized."""
    service = GPSTrackingService(update_interval=1.0)
    assert service.update_interval == 1.0
    assert service.get_current_position() is None


def test_gps_tracking_service_callbacks():
    """Test GPS tracking service callback registration."""
    service = GPSTrackingService()
    
    callback_called = []
    
    def test_callback(position: GPSPosition):
        callback_called.append(position)
    
    service.on_position_update(test_callback)
    assert test_callback in service._callbacks
    
    service.remove_callback(test_callback)
    assert test_callback not in service._callbacks


def test_local_database_shot_operations():
    """Test creating and retrieving shots with GPS data."""
    # Create temporary database
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name
    
    try:
        db = LocalDatabase(db_path)
        db.initialize_schema()
        
        # Create a shot with GPS position
        gps_pos = GPSPosition(
            latitude=37.7749,
            longitude=-122.4194,
            accuracy=5.0,
            timestamp=int(time.time()),
            altitude=10.0
        )
        
        shot = Shot(
            id="shot-001",
            round_id="round-001",
            hole_number=1,
            swing_number=1,
            club_type=ClubType.DRIVER,
            timestamp=int(time.time()),
            gps_origin=gps_pos,
            sync_status=SyncStatus.PENDING
        )
        
        # Store shot
        db.create_shot(shot)
        
        # Retrieve shot
        retrieved_shot = db.get_shot("shot-001")
        
        assert retrieved_shot is not None
        assert retrieved_shot.id == shot.id
        assert retrieved_shot.gps_origin.latitude == gps_pos.latitude
        assert retrieved_shot.gps_origin.longitude == gps_pos.longitude
        assert retrieved_shot.gps_origin.accuracy == gps_pos.accuracy
        assert retrieved_shot.gps_origin.altitude == gps_pos.altitude
        
        db.close()
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_local_database_multiple_shots_by_hole():
    """Test retrieving multiple shots for a specific hole."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name
    
    try:
        db = LocalDatabase(db_path)
        db.initialize_schema()
        
        # Create multiple shots for hole 1
        for i in range(3):
            gps_pos = GPSPosition(
                latitude=37.7749 + i * 0.001,
                longitude=-122.4194 + i * 0.001,
                accuracy=5.0,
                timestamp=int(time.time()) + i,
                altitude=10.0
            )
            
            shot = Shot(
                id=f"shot-{i:03d}",
                round_id="round-001",
                hole_number=1,
                swing_number=i + 1,
                club_type=ClubType.DRIVER,
                timestamp=int(time.time()) + i,
                gps_origin=gps_pos,
                sync_status=SyncStatus.PENDING
            )
            
            db.create_shot(shot)
        
        # Retrieve all shots for hole 1
        shots = db.get_shots_by_hole("round-001", 1)
        
        assert len(shots) == 3
        assert shots[0].swing_number == 1
        assert shots[1].swing_number == 2
        assert shots[2].swing_number == 3
        
        # Verify GPS accuracy is tracked
        for shot in shots:
            assert shot.gps_origin.accuracy == 5.0
        
        db.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_gps_accuracy_tracking():
    """Test that GPS accuracy is properly stored and retrieved."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name
    
    try:
        db = LocalDatabase(db_path)
        db.initialize_schema()
        
        # Create shots with different GPS accuracies
        accuracies = [3.0, 8.0, 15.0, 25.0]
        
        for i, accuracy in enumerate(accuracies):
            gps_pos = GPSPosition(
                latitude=37.7749,
                longitude=-122.4194,
                accuracy=accuracy,
                timestamp=int(time.time()) + i,
                altitude=10.0
            )
            
            shot = Shot(
                id=f"shot-{i:03d}",
                round_id="round-001",
                hole_number=1,
                swing_number=i + 1,
                club_type=ClubType.DRIVER,
                timestamp=int(time.time()) + i,
                gps_origin=gps_pos,
                sync_status=SyncStatus.PENDING
            )
            
            db.create_shot(shot)
        
        # Retrieve and verify accuracies
        shots = db.get_shots_by_round("round-001")
        
        assert len(shots) == 4
        for i, shot in enumerate(shots):
            assert shot.gps_origin.accuracy == accuracies[i]
        
        db.close()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
