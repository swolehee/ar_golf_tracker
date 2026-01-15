"""Integration tests for encryption in sync service.

Tests that sync service correctly encrypts data at rest in the sync queue.
"""

import pytest
import time
from ar_golf_tracker.ar_glasses.sync_service import SyncService
from ar_golf_tracker.ar_glasses.database import LocalDatabase
from ar_golf_tracker.shared.encryption import EncryptionService
from ar_golf_tracker.shared.models import (
    Shot, Round, GPSPosition, Distance, ClubType,
    DistanceUnit, DistanceAccuracy, SyncStatus, WeatherConditions
)


@pytest.fixture
def database():
    """Create test database."""
    db = LocalDatabase(":memory:")
    db.initialize_schema()
    return db


@pytest.fixture
def encryption_service():
    """Create encryption service for testing."""
    return EncryptionService()


@pytest.fixture
def sync_service_with_encryption(database, encryption_service):
    """Create sync service with encryption enabled."""
    return SyncService(
        database=database,
        max_retries=3,
        base_delay=0.1,
        max_delay=1.0,
        encryption_service=encryption_service
    )


@pytest.fixture
def sync_service_without_encryption(database):
    """Create sync service without encryption."""
    return SyncService(
        database=database,
        max_retries=3,
        base_delay=0.1,
        max_delay=1.0
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
        distance=Distance(
            value=250.0,
            unit=DistanceUnit.YARDS,
            accuracy=DistanceAccuracy.HIGH
        ),
        notes="Great drive!",
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
        weather=WeatherConditions(
            temperature=72,
            wind_speed=10,
            wind_direction="NW",
            conditions="Sunny"
        ),
        sync_status=SyncStatus.PENDING
    )


class TestSyncEncryption:
    """Test encryption in sync service."""
    
    def test_enqueue_shot_with_encryption(self, sync_service_with_encryption, sample_shot):
        """Test that shot data is encrypted when enqueued."""
        # Enqueue shot
        queue_id = sync_service_with_encryption.enqueue_shot_create(sample_shot)
        
        assert queue_id is not None
        
        # Get queue item from database
        items = sync_service_with_encryption.database.get_pending_sync_items(limit=1)
        assert len(items) == 1
        
        item = items[0]
        payload = item['payload']
        
        # Verify payload is encrypted
        assert isinstance(payload, dict)
        assert payload.get('encrypted') is True
        assert 'data' in payload
        assert isinstance(payload['data'], str)
        
        # Verify we can decrypt it
        decrypted = sync_service_with_encryption.encryption_service.decrypt_dict(payload['data'])
        assert decrypted['id'] == sample_shot.id
        assert decrypted['club_type'] == sample_shot.club_type.value
    
    def test_enqueue_shot_without_encryption(self, sync_service_without_encryption, sample_shot):
        """Test that shot data is not encrypted when encryption service is not provided."""
        # Enqueue shot
        queue_id = sync_service_without_encryption.enqueue_shot_create(sample_shot)
        
        assert queue_id is not None
        
        # Get queue item from database
        items = sync_service_without_encryption.database.get_pending_sync_items(limit=1)
        assert len(items) == 1
        
        item = items[0]
        payload = item['payload']
        
        # Verify payload is not encrypted
        assert isinstance(payload, dict)
        assert payload.get('encrypted') is not True
        assert payload['id'] == sample_shot.id
    
    def test_enqueue_round_with_encryption(self, sync_service_with_encryption, sample_round):
        """Test that round data is encrypted when enqueued."""
        # Enqueue round
        queue_id = sync_service_with_encryption.enqueue_round_create(sample_round)
        
        assert queue_id is not None
        
        # Get queue item from database
        items = sync_service_with_encryption.database.get_pending_sync_items(limit=1)
        assert len(items) == 1
        
        item = items[0]
        payload = item['payload']
        
        # Verify payload is encrypted
        assert isinstance(payload, dict)
        assert payload.get('encrypted') is True
        assert 'data' in payload
        
        # Verify we can decrypt it
        decrypted = sync_service_with_encryption.encryption_service.decrypt_dict(payload['data'])
        assert decrypted['id'] == sample_round.id
        assert decrypted['course_name'] == sample_round.course_name
    
    def test_process_encrypted_queue_item(self, sync_service_with_encryption, sample_shot):
        """Test that encrypted queue items are decrypted before processing."""
        # Enqueue shot
        sync_service_with_encryption.enqueue_shot_create(sample_shot)
        
        # Mock sync callback
        sync_callback = lambda entity_type, entity_id, operation, payload: True
        
        # Process queue
        stats = sync_service_with_encryption.process_sync_queue(sync_callback)
        
        # Verify item was processed successfully
        assert stats['success'] == 1
        assert stats['failed'] == 0
    
    def test_process_encrypted_queue_without_encryption_service_fails(
        self, sync_service_with_encryption, sample_shot
    ):
        """Test that processing encrypted data without encryption service fails."""
        # Enqueue shot with encryption
        sync_service_with_encryption.enqueue_shot_create(sample_shot)
        
        # Create new sync service without encryption
        sync_service_no_encryption = SyncService(
            database=sync_service_with_encryption.database,
            max_retries=3
        )
        
        # Mock sync callback
        sync_callback = lambda entity_type, entity_id, operation, payload: True
        
        # Process queue - should fail because data is encrypted but no service
        stats = sync_service_no_encryption.process_sync_queue(sync_callback)
        
        # Verify item failed to process
        assert stats['success'] == 0
        assert stats['failed'] == 1
    
    def test_update_operations_with_encryption(self, sync_service_with_encryption, sample_shot):
        """Test that update operations also encrypt data."""
        # Enqueue shot update
        queue_id = sync_service_with_encryption.enqueue_shot_update(sample_shot)
        
        assert queue_id is not None
        
        # Get queue item
        items = sync_service_with_encryption.database.get_pending_sync_items(limit=1)
        item = items[0]
        
        # Verify encrypted
        assert item['payload'].get('encrypted') is True
        assert item['operation'] == 'UPDATE'
    
    def test_round_update_with_encryption(self, sync_service_with_encryption, sample_round):
        """Test that round updates are encrypted."""
        # Enqueue round update
        queue_id = sync_service_with_encryption.enqueue_round_update(sample_round)
        
        assert queue_id is not None
        
        # Get queue item
        items = sync_service_with_encryption.database.get_pending_sync_items(limit=1)
        item = items[0]
        
        # Verify encrypted
        assert item['payload'].get('encrypted') is True
        assert item['operation'] == 'UPDATE'
    
    def test_delete_operations_not_encrypted(self, sync_service_with_encryption):
        """Test that delete operations don't encrypt (only ID needed)."""
        # Enqueue shot delete
        queue_id = sync_service_with_encryption.enqueue_shot_delete("shot-123")
        
        assert queue_id is not None
        
        # Get queue item
        items = sync_service_with_encryption.database.get_pending_sync_items(limit=1)
        item = items[0]
        
        # Delete operations have minimal payload, no encryption needed
        assert item['operation'] == 'DELETE'
        assert item['payload']['id'] == "shot-123"
    
    def test_encryption_preserves_data_integrity(self, sync_service_with_encryption, sample_shot):
        """Test that encryption/decryption preserves all shot data."""
        # Enqueue shot
        sync_service_with_encryption.enqueue_shot_create(sample_shot)
        
        # Get and decrypt
        items = sync_service_with_encryption.database.get_pending_sync_items(limit=1)
        payload = items[0]['payload']
        decrypted = sync_service_with_encryption.encryption_service.decrypt_dict(payload['data'])
        
        # Verify all fields preserved
        assert decrypted['id'] == sample_shot.id
        assert decrypted['round_id'] == sample_shot.round_id
        assert decrypted['hole_number'] == sample_shot.hole_number
        assert decrypted['swing_number'] == sample_shot.swing_number
        assert decrypted['club_type'] == sample_shot.club_type.value
        assert decrypted['timestamp'] == sample_shot.timestamp
        assert decrypted['gps_origin']['latitude'] == sample_shot.gps_origin.latitude
        assert decrypted['gps_origin']['longitude'] == sample_shot.gps_origin.longitude
        assert decrypted['distance']['value'] == sample_shot.distance.value
        assert decrypted['notes'] == sample_shot.notes
    
    def test_multiple_encrypted_items_in_queue(
        self, sync_service_with_encryption, sample_shot, sample_round
    ):
        """Test processing multiple encrypted items."""
        # Enqueue multiple items
        sync_service_with_encryption.enqueue_shot_create(sample_shot)
        sync_service_with_encryption.enqueue_round_create(sample_round)
        
        # Mock sync callback
        processed_items = []
        def sync_callback(entity_type, entity_id, operation, payload):
            processed_items.append({
                'type': entity_type,
                'id': entity_id,
                'operation': operation
            })
            return True
        
        # Process queue
        stats = sync_service_with_encryption.process_sync_queue(sync_callback, batch_size=10)
        
        # Verify both items processed
        assert stats['success'] == 2
        assert stats['failed'] == 0
        assert len(processed_items) == 2


class TestEncryptionPerformance:
    """Test encryption performance characteristics."""
    
    def test_encryption_overhead_acceptable(self, sync_service_with_encryption, sample_shot):
        """Test that encryption doesn't add significant overhead."""
        import time
        
        # Measure time to enqueue 100 shots
        start = time.time()
        for i in range(100):
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
            sync_service_with_encryption.enqueue_shot_create(shot)
        
        elapsed = time.time() - start
        
        # Should complete in reasonable time (< 1 second for 100 items)
        assert elapsed < 1.0
        
        # Verify all items encrypted
        items = sync_service_with_encryption.database.get_pending_sync_items(limit=100)
        assert len(items) == 100
        assert all(item['payload'].get('encrypted') for item in items)
