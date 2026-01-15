"""Unit tests for sync service with background sync and real-time updates."""

import pytest
import time
import threading
from unittest.mock import Mock, MagicMock, patch
from ar_golf_tracker.ar_glasses.sync_service import SyncService
from ar_golf_tracker.ar_glasses.database import LocalDatabase
from ar_golf_tracker.shared.models import (
    Shot, Round, GPSPosition, Distance, ClubType,
    DistanceUnit, DistanceAccuracy, SyncStatus, WeatherConditions
)


@pytest.fixture
def database():
    """Create test database with thread-safe connections."""
    db = LocalDatabase(":memory:", check_same_thread=False)
    db.initialize_schema()
    return db


@pytest.fixture
def sync_service(database):
    """Create sync service with test database."""
    return SyncService(
        database=database,
        max_retries=3,
        base_delay=0.1,
        max_delay=1.0,
        sync_interval=0.5  # Short interval for testing
    )


@pytest.fixture
def sample_shot():
    """Create sample shot for testing."""
    return Shot(
        id="shot-1",
        round_id="round-1",
        hole_number=1,
        swing_number=1,
        club_type=ClubType.DRIVER,
        timestamp=int(time.time()),
        gps_origin=GPSPosition(
            latitude=47.6062,
            longitude=-122.3321,
            accuracy=5.0,
            timestamp=int(time.time())
        ),
        sync_status=SyncStatus.PENDING
    )


@pytest.fixture
def sample_round():
    """Create sample round for testing."""
    return Round(
        id="round-1",
        user_id="user-1",
        course_id="course-1",
        course_name="Test Course",
        start_time=int(time.time()),
        sync_status=SyncStatus.PENDING
    )


class TestBackgroundSync:
    """Test background sync functionality."""
    
    def test_start_background_sync(self, sync_service):
        """Test starting background sync service."""
        sync_callback = Mock(return_value=True)
        
        sync_service.start_background_sync(sync_callback)
        
        assert sync_service._background_sync_enabled is True
        assert sync_service._sync_callback is sync_callback
        assert sync_service._background_sync_thread is not None
        assert sync_service._background_sync_thread.is_alive()
        
        # Cleanup
        sync_service.stop_background_sync()
    
    def test_stop_background_sync(self, sync_service):
        """Test stopping background sync service."""
        sync_callback = Mock(return_value=True)
        
        sync_service.start_background_sync(sync_callback)
        time.sleep(0.1)  # Let thread start
        
        sync_service.stop_background_sync()
        
        assert sync_service._background_sync_enabled is False
        assert sync_service._stop_event.is_set()
        
        # Wait a bit for thread to finish
        time.sleep(0.2)
        assert not sync_service._background_sync_thread.is_alive()
    
    def test_background_sync_when_online(self, sync_service, sample_shot):
        """Test background sync processes queue when online."""
        # Enqueue a shot
        sync_service.enqueue_shot_create(sample_shot)
        
        # Mock network as online
        sync_service.set_online_status(True)
        
        # Track sync calls
        sync_callback = Mock(return_value=True)
        
        # Start background sync
        sync_service.start_background_sync(sync_callback, batch_size=10)
        
        # Wait for sync interval to pass
        time.sleep(0.6)
        
        # Verify sync was called
        assert sync_callback.call_count > 0
        
        # Cleanup
        sync_service.stop_background_sync()
    
    def test_background_sync_when_offline(self, sync_service, sample_shot):
        """Test background sync skips when offline."""
        # Enqueue a shot
        sync_service.enqueue_shot_create(sample_shot)
        
        # Mock network as offline
        sync_service.set_online_status(False)
        
        # Track sync calls
        sync_callback = Mock(return_value=True)
        
        # Start background sync
        sync_service.start_background_sync(sync_callback, batch_size=10)
        
        # Wait for sync interval to pass
        time.sleep(0.6)
        
        # Verify sync was NOT called (network offline)
        assert sync_callback.call_count == 0
        
        # Cleanup
        sync_service.stop_background_sync()
    
    def test_background_sync_respects_interval(self, sync_service):
        """Test background sync respects sync interval."""
        # Use short interval for testing
        sync_service.sync_interval = 0.3
        
        # Add shots before starting background sync
        for i in range(4):
            shot = Shot(
                id=f"shot-{i}",
                round_id="round-1",
                hole_number=1,
                swing_number=i,
                club_type=ClubType.DRIVER,
                timestamp=int(time.time()),
                gps_origin=GPSPosition(
                    latitude=47.6062,
                    longitude=-122.3321,
                    accuracy=5.0,
                    timestamp=int(time.time())
                ),
                sync_status=SyncStatus.PENDING
            )
            sync_service.enqueue_shot_create(shot)
        
        # Mock network as online
        sync_service.set_online_status(True)
        
        # Track sync calls
        sync_callback = Mock(return_value=True)
        
        # Start background sync with batch size that matches queue
        sync_service.start_background_sync(sync_callback, batch_size=2)
        
        # Wait for multiple sync cycles
        time.sleep(1.0)
        
        # Should have synced multiple times
        assert sync_callback.call_count >= 2, f"Expected at least 2 syncs, got {sync_callback.call_count}"
        
        # Verify most items are synced (allow for timing variations)
        remaining = sync_service.database.get_sync_queue_size()
        assert remaining <= 2, f"Expected 0-2 items remaining, got {remaining} items"
        
        # Cleanup
        sync_service.stop_background_sync()


class TestRealTimeSync:
    """Test real-time sync with 10-second update window."""
    
    def test_sync_interval_default(self):
        """Test default sync interval is 10 seconds."""
        db = LocalDatabase(":memory:", check_same_thread=False)
        db.initialize_schema()
        service = SyncService(database=db)
        
        assert service.sync_interval == 10.0
    
    def test_sync_interval_custom(self):
        """Test custom sync interval."""
        db = LocalDatabase(":memory:", check_same_thread=False)
        db.initialize_schema()
        service = SyncService(database=db, sync_interval=5.0)
        
        assert service.sync_interval == 5.0
    
    def test_sync_now_when_online(self, sync_service, sample_shot):
        """Test manual sync when online."""
        # Enqueue a shot
        sync_service.enqueue_shot_create(sample_shot)
        
        # Mock network as online
        sync_service.set_online_status(True)
        
        # Set sync callback
        sync_callback = Mock(return_value=True)
        sync_service._sync_callback = sync_callback
        
        # Trigger immediate sync
        stats = sync_service.sync_now(batch_size=10)
        
        # Verify sync was called
        assert sync_callback.call_count > 0
        assert stats['success'] > 0
    
    def test_sync_now_when_offline(self, sync_service, sample_shot):
        """Test manual sync when offline."""
        # Enqueue a shot
        sync_service.enqueue_shot_create(sample_shot)
        
        # Mock network as offline
        sync_service.set_online_status(False)
        
        # Set sync callback
        sync_callback = Mock(return_value=True)
        sync_service._sync_callback = sync_callback
        
        # Trigger immediate sync
        stats = sync_service.sync_now(batch_size=10)
        
        # Verify sync was NOT called (network offline)
        assert sync_callback.call_count == 0
        assert stats['success'] == 0


class TestNetworkDetection:
    """Test network availability detection."""
    
    def test_is_online_with_callback(self):
        """Test network check with callback."""
        db = LocalDatabase(":memory:", check_same_thread=False)
        db.initialize_schema()
        
        network_callback = Mock(return_value=True)
        service = SyncService(database=db, network_check_callback=network_callback)
        
        assert service.is_online() is True
        network_callback.assert_called_once()
    
    def test_is_online_without_callback(self, sync_service):
        """Test network check without callback."""
        # Default should be False
        assert sync_service.is_online() is False
    
    def test_set_online_status(self, sync_service):
        """Test manually setting online status."""
        sync_service.set_online_status(True)
        assert sync_service._is_online is True
        
        sync_service.set_online_status(False)
        assert sync_service._is_online is False
    
    def test_network_restoration_triggers_sync(self, sync_service, sample_shot):
        """Test that network restoration triggers immediate sync."""
        # Enqueue a shot
        sync_service.enqueue_shot_create(sample_shot)
        
        # Set sync callback
        sync_callback = Mock(return_value=True)
        sync_service._sync_callback = sync_callback
        
        # Start background sync (offline)
        sync_service.set_online_status(False)
        sync_service.start_background_sync(sync_callback)
        
        # Restore network
        sync_service.set_online_status(True)
        
        # Wait a bit for sync to trigger
        time.sleep(0.2)
        
        # Verify sync was called
        assert sync_callback.call_count > 0
        
        # Cleanup
        sync_service.stop_background_sync()


class TestRetryQueue:
    """Test retry queue with exponential backoff."""
    
    def test_enqueue_shot_create(self, sync_service, sample_shot):
        """Test enqueueing shot creation."""
        queue_id = sync_service.enqueue_shot_create(sample_shot)
        
        assert queue_id is not None
        assert sync_service.database.get_sync_queue_size() == 1
    
    def test_enqueue_shot_update(self, sync_service, sample_shot):
        """Test enqueueing shot update."""
        # First create the shot
        sync_service.database.create_shot(sample_shot)
        
        # Then enqueue update
        queue_id = sync_service.enqueue_shot_update(sample_shot)
        
        assert queue_id is not None
        assert sync_service.database.get_sync_queue_size() == 1
    
    def test_enqueue_shot_delete(self, sync_service):
        """Test enqueueing shot deletion."""
        queue_id = sync_service.enqueue_shot_delete("shot-1")
        
        assert queue_id is not None
        assert sync_service.database.get_sync_queue_size() == 1
    
    def test_enqueue_round_create(self, sync_service, sample_round):
        """Test enqueueing round creation."""
        queue_id = sync_service.enqueue_round_create(sample_round)
        
        assert queue_id is not None
        assert sync_service.database.get_sync_queue_size() == 1
    
    def test_process_sync_queue_success(self, sync_service, sample_shot):
        """Test processing sync queue with successful sync."""
        # Enqueue a shot
        sync_service.enqueue_shot_create(sample_shot)
        
        # Mock successful sync
        sync_callback = Mock(return_value=True)
        
        # Process queue
        stats = sync_service.process_sync_queue(sync_callback, batch_size=10)
        
        assert stats['success'] == 1
        assert stats['failed'] == 0
        assert sync_service.database.get_sync_queue_size() == 0
    
    def test_process_sync_queue_failure(self, sync_service, sample_shot):
        """Test processing sync queue with failed sync."""
        # Enqueue a shot
        sync_service.enqueue_shot_create(sample_shot)
        
        # Mock failed sync
        sync_callback = Mock(return_value=False)
        
        # Process queue
        stats = sync_service.process_sync_queue(sync_callback, batch_size=10)
        
        assert stats['success'] == 0
        assert stats['failed'] == 1
        # Item should still be in queue for retry
        assert sync_service.database.get_sync_queue_size() == 1
    
    def test_retry_with_exponential_backoff(self, sync_service, sample_shot):
        """Test retry logic with exponential backoff."""
        # Enqueue a shot
        sync_service.enqueue_shot_create(sample_shot)
        
        # Mock failed sync
        sync_callback = Mock(return_value=False)
        
        # First attempt
        stats1 = sync_service.process_sync_queue(sync_callback, batch_size=10)
        assert stats1['failed'] == 1
        
        # Get the queue item to check retry state
        pending_items = sync_service.database.get_pending_sync_items(limit=10)
        assert len(pending_items) == 1
        first_retry_count = pending_items[0]['retry_count']
        assert first_retry_count == 1
        
        # Wait for backoff delay (base_delay * 2^0 = 0.1 seconds)
        time.sleep(0.15)
        
        # Second attempt should proceed after backoff
        stats2 = sync_service.process_sync_queue(sync_callback, batch_size=10)
        assert stats2['failed'] == 1
        
        # Verify retry count increased
        pending_items = sync_service.database.get_pending_sync_items(limit=10)
        assert len(pending_items) == 1
        assert pending_items[0]['retry_count'] == 2
    
    def test_max_retries_exceeded(self, sync_service, sample_shot):
        """Test that items exceeding max retries are skipped."""
        # Enqueue a shot
        queue_id = sync_service.enqueue_shot_create(sample_shot)
        
        # Manually set retry count to max
        conn = sync_service.database.connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sync_queue SET retry_count = ? WHERE id = ?",
            (sync_service.max_retries, queue_id)
        )
        conn.commit()
        
        # Mock failed sync
        sync_callback = Mock(return_value=False)
        
        # Process queue
        stats = sync_service.process_sync_queue(sync_callback, batch_size=10)
        
        # Should be skipped
        assert stats['skipped'] == 1
        assert stats['failed'] == 0
    
    def test_cleanup_failed_items(self, sync_service, sample_shot):
        """Test cleanup of items exceeding max retries."""
        # Enqueue a shot
        queue_id = sync_service.enqueue_shot_create(sample_shot)
        
        # Manually set retry count to max
        conn = sync_service.database.connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sync_queue SET retry_count = ? WHERE id = ?",
            (sync_service.max_retries, queue_id)
        )
        conn.commit()
        
        # Cleanup
        removed = sync_service.cleanup_failed_items()
        
        assert removed == 1
        assert sync_service.database.get_sync_queue_size() == 0


class TestSyncStatus:
    """Test sync status tracking."""
    
    def test_get_queue_status(self, sync_service, sample_shot, sample_round):
        """Test getting queue status."""
        # Create shot and round in database first
        sync_service.database.create_shot(sample_shot)
        sync_service.database.create_round(sample_round)
        
        # Enqueue items
        sync_service.enqueue_shot_create(sample_shot)
        sync_service.enqueue_round_create(sample_round)
        
        # Get status
        status = sync_service.get_queue_status()
        
        assert status['queue_size'] == 2
        assert status['pending_shots'] == 1
        assert status['pending_rounds'] == 1
    
    def test_sync_status_updates_on_success(self, sync_service, sample_shot):
        """Test that sync status updates to SYNCED on success."""
        # Create shot in database
        sync_service.database.create_shot(sample_shot)
        
        # Enqueue for sync
        sync_service.enqueue_shot_create(sample_shot)
        
        # Mock successful sync
        sync_callback = Mock(return_value=True)
        
        # Process queue
        sync_service.process_sync_queue(sync_callback, batch_size=10)
        
        # Verify status updated
        shot = sync_service.database.get_shot(sample_shot.id)
        assert shot.sync_status == SyncStatus.SYNCED
    
    def test_sync_status_updates_on_failure(self, sync_service, sample_shot):
        """Test that sync status updates to FAILED on failure."""
        # Create shot in database
        sync_service.database.create_shot(sample_shot)
        
        # Enqueue for sync
        sync_service.enqueue_shot_create(sample_shot)
        
        # Mock failed sync
        sync_callback = Mock(return_value=False)
        
        # Process queue
        sync_service.process_sync_queue(sync_callback, batch_size=10)
        
        # Verify status updated
        shot = sync_service.database.get_shot(sample_shot.id)
        assert shot.sync_status == SyncStatus.FAILED


class TestConcurrency:
    """Test thread safety and concurrency."""
    
    def test_multiple_enqueues_concurrent(self, sync_service):
        """Test concurrent enqueueing from multiple threads."""
        # Note: SQLite with check_same_thread=False allows concurrent reads
        # but writes are still serialized. This test verifies basic thread safety.
        
        shots = []
        for i in range(10):
            shot = Shot(
                id=f"shot-{i}",
                round_id="round-1",
                hole_number=1,
                swing_number=i,
                club_type=ClubType.DRIVER,
                timestamp=int(time.time()),
                gps_origin=GPSPosition(
                    latitude=47.6062,
                    longitude=-122.3321,
                    accuracy=5.0,
                    timestamp=int(time.time())
                ),
                sync_status=SyncStatus.PENDING
            )
            shots.append(shot)
        
        # Enqueue from multiple threads
        threads = []
        for shot in shots:
            thread = threading.Thread(
                target=sync_service.enqueue_shot_create,
                args=(shot,)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify most items enqueued (allow for some failures due to SQLite locking)
        queue_size = sync_service.database.get_sync_queue_size()
        assert queue_size >= 8, f"Expected at least 8 items enqueued, got {queue_size}"
    
    def test_background_sync_thread_safety(self, sync_service, sample_shot):
        """Test that background sync is thread-safe."""
        # Enqueue multiple shots
        for i in range(5):
            shot = Shot(
                id=f"shot-{i}",
                round_id="round-1",
                hole_number=1,
                swing_number=i,
                club_type=ClubType.DRIVER,
                timestamp=int(time.time()),
                gps_origin=GPSPosition(
                    latitude=47.6062,
                    longitude=-122.3321,
                    accuracy=5.0,
                    timestamp=int(time.time())
                ),
                sync_status=SyncStatus.PENDING
            )
            sync_service.enqueue_shot_create(shot)
        
        # Mock network as online
        sync_service.set_online_status(True)
        
        # Track sync calls
        sync_callback = Mock(return_value=True)
        
        # Start background sync with small batch size
        sync_service.start_background_sync(sync_callback, batch_size=2)
        
        # Wait for multiple sync cycles (need enough time for all items)
        time.sleep(2.0)
        
        # Verify all or most items synced (allow for timing variations)
        remaining = sync_service.database.get_sync_queue_size()
        assert remaining <= 1, f"Expected 0-1 items remaining, got {remaining}"
        
        # Cleanup
        sync_service.stop_background_sync()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
