"""Tests for sync queue operations and offline functionality."""

import pytest
import tempfile
import os
import time
from ar_golf_tracker.ar_glasses.database import LocalDatabase
from ar_golf_tracker.ar_glasses.sync_service import SyncService
from ar_golf_tracker.ar_glasses.offline_manager import OfflineManager
from ar_golf_tracker.shared.models import (
    Shot, Round, GPSPosition, ClubType, SyncStatus, DistanceUnit,
    DistanceAccuracy, Distance
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        db_path = tmp.name
    
    db = LocalDatabase(db_path)
    db.initialize_schema()
    
    yield db
    
    db.close()
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def sync_service(temp_db):
    """Create a sync service instance."""
    return SyncService(temp_db)


@pytest.fixture
def offline_manager(temp_db, sync_service):
    """Create an offline manager instance."""
    return OfflineManager(temp_db, sync_service)


def create_test_shot(shot_id="shot-001", round_id="round-001"):
    """Helper to create a test shot."""
    return Shot(
        id=shot_id,
        round_id=round_id,
        hole_number=1,
        swing_number=1,
        club_type=ClubType.DRIVER,
        timestamp=int(time.time()),
        gps_origin=GPSPosition(
            latitude=37.7749,
            longitude=-122.4194,
            accuracy=5.0,
            timestamp=int(time.time())
        ),
        sync_status=SyncStatus.PENDING
    )


def create_test_round(round_id="round-001"):
    """Helper to create a test round."""
    return Round(
        id=round_id,
        user_id="user-001",
        course_id="course-001",
        course_name="Test Golf Course",
        start_time=int(time.time()),
        sync_status=SyncStatus.PENDING
    )


# Sync Queue Tests

def test_enqueue_shot_create(temp_db, sync_service):
    """Test enqueueing a shot creation for sync."""
    shot = create_test_shot()
    
    queue_id = sync_service.enqueue_shot_create(shot)
    
    assert queue_id is not None
    assert temp_db.get_sync_queue_size() == 1
    
    items = temp_db.get_pending_sync_items()
    assert len(items) == 1
    assert items[0]['entity_type'] == 'SHOT'
    assert items[0]['entity_id'] == shot.id
    assert items[0]['operation'] == 'CREATE'


def test_enqueue_shot_update(temp_db, sync_service):
    """Test enqueueing a shot update for sync."""
    shot = create_test_shot()
    
    queue_id = sync_service.enqueue_shot_update(shot)
    
    assert queue_id is not None
    items = temp_db.get_pending_sync_items()
    assert items[0]['operation'] == 'UPDATE'


def test_enqueue_shot_delete(temp_db, sync_service):
    """Test enqueueing a shot deletion for sync."""
    shot_id = "shot-001"
    
    queue_id = sync_service.enqueue_shot_delete(shot_id)
    
    assert queue_id is not None
    items = temp_db.get_pending_sync_items()
    assert items[0]['operation'] == 'DELETE'
    assert items[0]['entity_id'] == shot_id


def test_enqueue_round_operations(temp_db, sync_service):
    """Test enqueueing round operations for sync."""
    round_obj = create_test_round()
    
    # Test create
    queue_id_create = sync_service.enqueue_round_create(round_obj)
    assert queue_id_create is not None
    
    # Test update
    queue_id_update = sync_service.enqueue_round_update(round_obj)
    assert queue_id_update is not None
    
    # Test delete
    queue_id_delete = sync_service.enqueue_round_delete(round_obj.id)
    assert queue_id_delete is not None
    
    assert temp_db.get_sync_queue_size() == 3


def test_get_pending_sync_items(temp_db, sync_service):
    """Test retrieving pending sync items."""
    shot1 = create_test_shot("shot-001")
    shot2 = create_test_shot("shot-002")
    
    sync_service.enqueue_shot_create(shot1)
    sync_service.enqueue_shot_create(shot2)
    
    items = temp_db.get_pending_sync_items(limit=10)
    
    assert len(items) == 2
    assert all('payload' in item for item in items)
    assert all('retry_count' in item for item in items)


def test_sync_queue_ordering(temp_db, sync_service):
    """Test that sync queue items are ordered by creation time."""
    shot1 = create_test_shot("shot-001")
    time.sleep(0.01)  # Small delay to ensure different timestamps
    shot2 = create_test_shot("shot-002")
    time.sleep(0.01)
    shot3 = create_test_shot("shot-003")
    
    sync_service.enqueue_shot_create(shot1)
    sync_service.enqueue_shot_create(shot2)
    sync_service.enqueue_shot_create(shot3)
    
    items = temp_db.get_pending_sync_items()
    
    # Items should be ordered by created_at (oldest first)
    assert items[0]['entity_id'] == 'shot-001'
    assert items[1]['entity_id'] == 'shot-002'
    assert items[2]['entity_id'] == 'shot-003'


# Retry Logic Tests

def test_exponential_backoff_calculation(sync_service):
    """Test exponential backoff delay calculation."""
    # Base delay is 1.0 second
    assert sync_service.calculate_backoff_delay(0) == 1.0
    assert sync_service.calculate_backoff_delay(1) == 2.0
    assert sync_service.calculate_backoff_delay(2) == 4.0
    assert sync_service.calculate_backoff_delay(3) == 8.0
    assert sync_service.calculate_backoff_delay(4) == 16.0
    
    # Should cap at max_delay (60.0 seconds)
    assert sync_service.calculate_backoff_delay(10) == 60.0


def test_update_sync_retry(temp_db, sync_service):
    """Test updating retry count for sync items."""
    shot = create_test_shot()
    queue_id = sync_service.enqueue_shot_create(shot)
    
    # Initial retry count should be 0
    items = temp_db.get_pending_sync_items()
    assert items[0]['retry_count'] == 0
    assert items[0]['last_retry_at'] is None
    
    # Update retry
    temp_db.update_sync_retry(queue_id)
    
    items = temp_db.get_pending_sync_items()
    assert items[0]['retry_count'] == 1
    assert items[0]['last_retry_at'] is not None


def test_process_sync_queue_success(temp_db, sync_service):
    """Test processing sync queue with successful sync."""
    shot = create_test_shot()
    temp_db.create_shot(shot)
    sync_service.enqueue_shot_create(shot)
    
    # Mock sync callback that always succeeds
    def mock_sync_success(entity_type, entity_id, operation, payload):
        return True
    
    stats = sync_service.process_sync_queue(mock_sync_success)
    
    assert stats['success'] == 1
    assert stats['failed'] == 0
    assert temp_db.get_sync_queue_size() == 0
    
    # Shot sync status should be updated
    updated_shot = temp_db.get_shot(shot.id)
    assert updated_shot.sync_status == SyncStatus.SYNCED


def test_process_sync_queue_failure(temp_db, sync_service):
    """Test processing sync queue with failed sync."""
    shot = create_test_shot()
    temp_db.create_shot(shot)
    sync_service.enqueue_shot_create(shot)
    
    # Mock sync callback that always fails
    def mock_sync_failure(entity_type, entity_id, operation, payload):
        return False
    
    stats = sync_service.process_sync_queue(mock_sync_failure)
    
    assert stats['success'] == 0
    assert stats['failed'] == 1
    assert temp_db.get_sync_queue_size() == 1  # Item still in queue
    
    # Retry count should be incremented
    items = temp_db.get_pending_sync_items()
    assert items[0]['retry_count'] == 1
    
    # Shot sync status should be FAILED
    updated_shot = temp_db.get_shot(shot.id)
    assert updated_shot.sync_status == SyncStatus.FAILED


def test_process_sync_queue_max_retries(temp_db, sync_service):
    """Test that items exceeding max retries are skipped."""
    shot = create_test_shot()
    temp_db.create_shot(shot)
    queue_id = sync_service.enqueue_shot_create(shot)
    
    # Simulate max retries reached
    for _ in range(5):
        temp_db.update_sync_retry(queue_id)
    
    def mock_sync(entity_type, entity_id, operation, payload):
        return False
    
    stats = sync_service.process_sync_queue(mock_sync)
    
    assert stats['skipped'] == 1
    assert stats['failed'] == 0


def test_clear_old_sync_items(temp_db, sync_service):
    """Test clearing items that exceeded max retries."""
    shot1 = create_test_shot("shot-001")
    shot2 = create_test_shot("shot-002")
    
    queue_id1 = sync_service.enqueue_shot_create(shot1)
    queue_id2 = sync_service.enqueue_shot_create(shot2)
    
    # Simulate max retries for shot1
    for _ in range(5):
        temp_db.update_sync_retry(queue_id1)
    
    # shot2 has only 1 retry
    temp_db.update_sync_retry(queue_id2)
    
    removed = temp_db.clear_old_sync_items(max_retries=5)
    
    assert removed == 1
    assert temp_db.get_sync_queue_size() == 1
    
    # Only shot2 should remain
    items = temp_db.get_pending_sync_items()
    assert items[0]['entity_id'] == 'shot-002'


# Offline Manager Tests

def test_offline_manager_record_shot_offline(temp_db, sync_service, offline_manager):
    """Test recording a shot when offline."""
    offline_manager.set_online_status(False)
    
    shot = create_test_shot()
    offline_manager.record_shot(shot, auto_sync=True)
    
    # Shot should be saved locally
    saved_shot = temp_db.get_shot(shot.id)
    assert saved_shot is not None
    assert saved_shot.sync_status == SyncStatus.PENDING
    
    # Should be queued for sync
    assert temp_db.get_sync_queue_size() == 1


def test_offline_manager_record_shot_online(temp_db, sync_service, offline_manager):
    """Test recording a shot when online."""
    offline_manager.set_online_status(True)
    
    shot = create_test_shot()
    offline_manager.record_shot(shot, auto_sync=True)
    
    # Shot should be saved locally
    saved_shot = temp_db.get_shot(shot.id)
    assert saved_shot is not None
    
    # Should be queued for sync
    assert temp_db.get_sync_queue_size() == 1


def test_offline_manager_update_shot(temp_db, sync_service, offline_manager):
    """Test updating a shot through offline manager."""
    shot = create_test_shot()
    temp_db.create_shot(shot)
    
    # Update shot
    shot.hole_number = 2
    offline_manager.update_shot(shot, auto_sync=False)
    
    # Verify update
    updated_shot = temp_db.get_shot(shot.id)
    assert updated_shot.hole_number == 2
    
    # Should be queued for sync
    items = temp_db.get_pending_sync_items()
    assert items[0]['operation'] == 'UPDATE'


def test_offline_manager_delete_shot(temp_db, sync_service, offline_manager):
    """Test deleting a shot through offline manager."""
    shot = create_test_shot()
    temp_db.create_shot(shot)
    
    offline_manager.delete_shot(shot.id, auto_sync=False)
    
    # Shot should be deleted locally
    deleted_shot = temp_db.get_shot(shot.id)
    assert deleted_shot is None
    
    # Should be queued for sync
    items = temp_db.get_pending_sync_items()
    assert items[0]['operation'] == 'DELETE'


def test_offline_manager_record_round(temp_db, sync_service, offline_manager):
    """Test recording a round through offline manager."""
    round_obj = create_test_round()
    offline_manager.record_round(round_obj, auto_sync=False)
    
    # Round should be saved locally
    saved_round = temp_db.get_round(round_obj.id)
    assert saved_round is not None
    
    # Should be queued for sync
    assert temp_db.get_sync_queue_size() == 1


def test_offline_manager_get_pending_count(temp_db, sync_service, offline_manager):
    """Test getting pending sync count."""
    shot1 = create_test_shot("shot-001")
    shot2 = create_test_shot("shot-002")
    
    offline_manager.record_shot(shot1, auto_sync=False)
    offline_manager.record_shot(shot2, auto_sync=False)
    
    count = offline_manager.get_pending_sync_count()
    assert count == 2


def test_offline_manager_get_status(temp_db, sync_service, offline_manager):
    """Test getting offline operation status."""
    offline_manager.set_online_status(False)
    
    shot = create_test_shot()
    temp_db.create_shot(shot)
    offline_manager.record_shot(shot, auto_sync=False)
    
    status = offline_manager.get_offline_status()
    
    assert status['is_online'] is False
    assert status['queue_size'] == 1
    assert status['pending_shots'] == 1


def test_offline_manager_sync_when_online(temp_db, sync_service, offline_manager):
    """Test syncing when network becomes available."""
    # Start offline
    offline_manager.set_online_status(False)
    
    shot = create_test_shot()
    temp_db.create_shot(shot)
    offline_manager.record_shot(shot, auto_sync=False)
    
    # Go online
    offline_manager.set_online_status(True)
    
    def mock_sync_success(entity_type, entity_id, operation, payload):
        return True
    
    stats = offline_manager.sync_when_online(mock_sync_success)
    
    assert stats['success'] == 1
    assert stats['offline'] is False
    assert temp_db.get_sync_queue_size() == 0


def test_offline_manager_sync_when_offline(temp_db, sync_service, offline_manager):
    """Test that sync is skipped when offline."""
    offline_manager.set_online_status(False)
    
    shot = create_test_shot()
    temp_db.create_shot(shot)
    offline_manager.record_shot(shot, auto_sync=False)
    
    def mock_sync(entity_type, entity_id, operation, payload):
        return True
    
    stats = offline_manager.sync_when_online(mock_sync)
    
    assert stats['offline'] is True
    assert stats['success'] == 0
    assert temp_db.get_sync_queue_size() == 1  # Still queued


def test_offline_manager_data_continuity(temp_db, sync_service, offline_manager):
    """Test data continuity verification."""
    # Should pass with valid database
    assert offline_manager.ensure_data_continuity() is True


# Sync Status Tests

def test_get_shots_by_sync_status(temp_db):
    """Test retrieving shots by sync status."""
    shot1 = create_test_shot("shot-001")
    shot1.sync_status = SyncStatus.PENDING
    temp_db.create_shot(shot1)
    
    shot2 = create_test_shot("shot-002")
    shot2.sync_status = SyncStatus.SYNCED
    temp_db.create_shot(shot2)
    
    shot3 = create_test_shot("shot-003")
    shot3.sync_status = SyncStatus.FAILED
    temp_db.create_shot(shot3)
    
    pending_shots = temp_db.get_shots_by_sync_status(SyncStatus.PENDING)
    synced_shots = temp_db.get_shots_by_sync_status(SyncStatus.SYNCED)
    failed_shots = temp_db.get_shots_by_sync_status(SyncStatus.FAILED)
    
    assert len(pending_shots) == 1
    assert len(synced_shots) == 1
    assert len(failed_shots) == 1


def test_update_shot_sync_status(temp_db):
    """Test updating shot sync status."""
    shot = create_test_shot()
    shot.sync_status = SyncStatus.PENDING
    temp_db.create_shot(shot)
    
    temp_db.update_shot_sync_status(shot.id, SyncStatus.SYNCED)
    
    updated_shot = temp_db.get_shot(shot.id)
    assert updated_shot.sync_status == SyncStatus.SYNCED


def test_update_round_sync_status(temp_db):
    """Test updating round sync status."""
    round_obj = create_test_round()
    round_obj.sync_status = SyncStatus.PENDING
    temp_db.create_round(round_obj)
    
    temp_db.update_round_sync_status(round_obj.id, SyncStatus.SYNCED)
    
    updated_round = temp_db.get_round(round_obj.id)
    assert updated_round.sync_status == SyncStatus.SYNCED


# Batch Processing Tests

def test_process_sync_queue_batch_limit(temp_db, sync_service):
    """Test that batch processing respects the limit."""
    # Create 15 shots
    for i in range(15):
        shot = create_test_shot(f"shot-{i:03d}")
        temp_db.create_shot(shot)
        sync_service.enqueue_shot_create(shot)
    
    def mock_sync_success(entity_type, entity_id, operation, payload):
        return True
    
    # Process with batch size of 10
    stats = sync_service.process_sync_queue(mock_sync_success, batch_size=10)
    
    assert stats['success'] == 10
    assert temp_db.get_sync_queue_size() == 5  # 5 remaining


def test_multiple_operations_same_entity(temp_db, sync_service):
    """Test multiple operations on the same entity."""
    shot = create_test_shot()
    
    # Create, update, and delete operations
    sync_service.enqueue_shot_create(shot)
    sync_service.enqueue_shot_update(shot)
    sync_service.enqueue_shot_delete(shot.id)
    
    items = temp_db.get_pending_sync_items()
    
    assert len(items) == 3
    assert items[0]['operation'] == 'CREATE'
    assert items[1]['operation'] == 'UPDATE'
    assert items[2]['operation'] == 'DELETE'
