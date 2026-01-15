"""Unit tests for device manager and cross-device sync."""

import pytest
import uuid
from datetime import datetime, timedelta
from ar_golf_tracker.backend.device_manager import DeviceManager
from ar_golf_tracker.backend.database import CloudDatabase


@pytest.fixture
def database():
    """Create test database."""
    db = CloudDatabase(
        host="localhost",
        port=5432,
        database="ar_golf_test",
        user="test_user",
        password="test_password"
    )
    # Note: In real tests, this would use a test database
    # For now, we'll mock the connection
    return db


@pytest.fixture
def mock_connection(monkeypatch):
    """Create mock database connection."""
    from unittest.mock import Mock, MagicMock
    mock_conn = Mock()
    mock_cursor = Mock()
    
    # Create a context manager for cursor
    cursor_context = MagicMock()
    cursor_context.__enter__.return_value = mock_cursor
    cursor_context.__exit__.return_value = None
    mock_conn.cursor.return_value = cursor_context
    
    return mock_conn, mock_cursor


@pytest.fixture
def device_manager(mock_connection):
    """Create device manager with mock connection."""
    mock_conn, _ = mock_connection
    return DeviceManager(mock_conn)


@pytest.fixture
def sample_user_id():
    """Sample user ID."""
    return str(uuid.uuid4())


@pytest.fixture
def sample_device_id():
    """Sample device ID."""
    return "device-12345-ar-glasses"


class TestDeviceRegistration:
    """Test device registration functionality."""
    
    def test_register_device(self, device_manager, mock_connection, sample_user_id, sample_device_id):
        """Test registering a new device."""
        mock_conn, mock_cursor = mock_connection
        device_uuid = str(uuid.uuid4())
        mock_cursor.fetchone.return_value = (device_uuid,)
        
        result = device_manager.register_device(
            user_id=sample_user_id,
            device_id=sample_device_id,
            device_type='AR_GLASSES',
            device_name='My AR Glasses',
            device_info={'os': 'Android', 'version': '1.0.0'}
        )
        
        assert result == device_uuid
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
    
    def test_register_device_updates_existing(self, device_manager, mock_connection, sample_user_id, sample_device_id):
        """Test that registering an existing device updates it."""
        mock_conn, mock_cursor = mock_connection
        device_uuid = str(uuid.uuid4())
        mock_cursor.fetchone.return_value = (device_uuid,)
        
        # Register device twice
        result1 = device_manager.register_device(
            user_id=sample_user_id,
            device_id=sample_device_id,
            device_type='AR_GLASSES'
        )
        
        result2 = device_manager.register_device(
            user_id=sample_user_id,
            device_id=sample_device_id,
            device_type='AR_GLASSES',
            device_name='Updated Name'
        )
        
        # Should return same UUID (upsert behavior)
        assert result1 == device_uuid
        assert result2 == device_uuid
    
    def test_get_user_devices(self, device_manager, mock_connection, sample_user_id):
        """Test getting all devices for a user."""
        mock_conn, mock_cursor = mock_connection
        
        device1_uuid = str(uuid.uuid4())
        device2_uuid = str(uuid.uuid4())
        
        mock_cursor.fetchall.return_value = [
            (device1_uuid, 'device-1', 'AR_GLASSES', 'My Glasses', None, datetime.now(), {}),
            (device2_uuid, 'device-2', 'MOBILE_IOS', 'My iPhone', datetime.now(), datetime.now(), {'theme': 'dark'})
        ]
        
        devices = device_manager.get_user_devices(sample_user_id)
        
        assert len(devices) == 2
        assert devices[0]['device_uuid'] == device1_uuid
        assert devices[0]['device_type'] == 'AR_GLASSES'
        assert devices[1]['device_uuid'] == device2_uuid
        assert devices[1]['device_type'] == 'MOBILE_IOS'
        assert devices[1]['device_preferences'] == {'theme': 'dark'}
    
    def test_get_device_by_id(self, device_manager, mock_connection, sample_user_id, sample_device_id):
        """Test getting device by ID."""
        mock_conn, mock_cursor = mock_connection
        device_uuid = str(uuid.uuid4())
        
        mock_cursor.fetchone.return_value = (
            device_uuid,
            sample_device_id,
            'AR_GLASSES',
            'My Glasses',
            None,
            datetime.now(),
            {'power_saving': True},
            {'os': 'Android'}
        )
        
        device = device_manager.get_device_by_id(sample_user_id, sample_device_id)
        
        assert device is not None
        assert device['device_uuid'] == device_uuid
        assert device['device_id'] == sample_device_id
        assert device['device_preferences'] == {'power_saving': True}
        assert device['device_info'] == {'os': 'Android'}
    
    def test_get_device_by_id_not_found(self, device_manager, mock_connection, sample_user_id):
        """Test getting non-existent device."""
        mock_conn, mock_cursor = mock_connection
        mock_cursor.fetchone.return_value = None
        
        device = device_manager.get_device_by_id(sample_user_id, 'non-existent')
        
        assert device is None


class TestDevicePreferences:
    """Test device-specific preferences."""
    
    def test_update_device_preferences(self, device_manager, mock_connection):
        """Test updating device preferences."""
        mock_conn, mock_cursor = mock_connection
        device_uuid = str(uuid.uuid4())
        preferences = {
            'distance_unit': 'METERS',
            'power_saving_mode': True,
            'auto_sync': False
        }
        
        device_manager.update_device_preferences(device_uuid, preferences)
        
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        
        # Verify preferences were passed correctly
        call_args = mock_cursor.execute.call_args[0]
        assert call_args[1] == (preferences, device_uuid)
    
    def test_get_effective_preferences_user_only(self, device_manager, mock_connection, sample_user_id, sample_device_id):
        """Test getting effective preferences with only user preferences."""
        mock_conn, mock_cursor = mock_connection
        
        user_prefs = {'distance_unit': 'YARDS', 'auto_sync': True}
        device_prefs = {}
        
        mock_cursor.fetchone.side_effect = [(user_prefs,), (device_prefs,)]
        
        effective = device_manager.get_effective_preferences(sample_user_id, sample_device_id)
        
        assert effective == user_prefs
    
    def test_get_effective_preferences_device_overrides(self, device_manager, mock_connection, sample_user_id, sample_device_id):
        """Test that device preferences override user preferences."""
        mock_conn, mock_cursor = mock_connection
        
        user_prefs = {'distance_unit': 'YARDS', 'auto_sync': True, 'theme': 'light'}
        device_prefs = {'distance_unit': 'METERS', 'power_saving': True}
        
        mock_cursor.fetchone.side_effect = [(user_prefs,), (device_prefs,)]
        
        effective = device_manager.get_effective_preferences(sample_user_id, sample_device_id)
        
        # Device preferences should override user preferences
        assert effective['distance_unit'] == 'METERS'  # Overridden
        assert effective['auto_sync'] is True  # From user
        assert effective['theme'] == 'light'  # From user
        assert effective['power_saving'] is True  # From device
    
    def test_get_effective_preferences_no_user_prefs(self, device_manager, mock_connection, sample_user_id, sample_device_id):
        """Test getting effective preferences when user has no preferences."""
        mock_conn, mock_cursor = mock_connection
        
        device_prefs = {'distance_unit': 'METERS'}
        
        mock_cursor.fetchone.side_effect = [(None,), (device_prefs,)]
        
        effective = device_manager.get_effective_preferences(sample_user_id, sample_device_id)
        
        assert effective == device_prefs


class TestCrossDeviceSync:
    """Test cross-device synchronization."""
    
    def test_update_device_sync_timestamp(self, device_manager, mock_connection):
        """Test updating device sync timestamp."""
        mock_conn, mock_cursor = mock_connection
        device_uuid = str(uuid.uuid4())
        
        device_manager.update_device_sync_timestamp(device_uuid)
        
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
    
    def test_log_device_sync(self, device_manager, mock_connection):
        """Test logging device sync."""
        mock_conn, mock_cursor = mock_connection
        device_uuid = str(uuid.uuid4())
        entity_id = str(uuid.uuid4())
        
        device_manager.log_device_sync(
            device_uuid=device_uuid,
            entity_type='shot',
            entity_id=entity_id,
            sync_direction='FROM_CLOUD'
        )
        
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        
        # Verify parameters
        call_args = mock_cursor.execute.call_args[0]
        assert call_args[1] == (device_uuid, 'shot', entity_id, 'FROM_CLOUD')
    
    def test_get_entities_to_sync_rounds(self, device_manager, mock_connection, sample_user_id):
        """Test getting rounds that need to be synced."""
        mock_conn, mock_cursor = mock_connection
        device_uuid = str(uuid.uuid4())
        
        round1_id = str(uuid.uuid4())
        round2_id = str(uuid.uuid4())
        now = datetime.now()
        
        mock_cursor.fetchall.return_value = [
            (round1_id, now),
            (round2_id, now - timedelta(hours=1))
        ]
        
        entities = device_manager.get_entities_to_sync(
            device_uuid=device_uuid,
            user_id=sample_user_id,
            entity_type='round'
        )
        
        assert len(entities) == 2
        assert entities[0]['entity_id'] == round1_id
        assert entities[1]['entity_id'] == round2_id
    
    def test_get_entities_to_sync_shots(self, device_manager, mock_connection, sample_user_id):
        """Test getting shots that need to be synced."""
        mock_conn, mock_cursor = mock_connection
        device_uuid = str(uuid.uuid4())
        
        shot1_id = str(uuid.uuid4())
        shot2_id = str(uuid.uuid4())
        now = datetime.now()
        
        mock_cursor.fetchall.return_value = [
            (shot1_id, now),
            (shot2_id, now - timedelta(minutes=30))
        ]
        
        entities = device_manager.get_entities_to_sync(
            device_uuid=device_uuid,
            user_id=sample_user_id,
            entity_type='shot'
        )
        
        assert len(entities) == 2
        assert entities[0]['entity_id'] == shot1_id
        assert entities[1]['entity_id'] == shot2_id
    
    def test_get_entities_to_sync_with_since(self, device_manager, mock_connection, sample_user_id):
        """Test getting entities updated after a specific time."""
        mock_conn, mock_cursor = mock_connection
        device_uuid = str(uuid.uuid4())
        since = datetime.now() - timedelta(hours=2)
        
        round_id = str(uuid.uuid4())
        now = datetime.now()
        
        mock_cursor.fetchall.return_value = [(round_id, now)]
        
        entities = device_manager.get_entities_to_sync(
            device_uuid=device_uuid,
            user_id=sample_user_id,
            entity_type='round',
            since=since
        )
        
        assert len(entities) == 1
        assert entities[0]['entity_id'] == round_id
        
        # Verify since parameter was passed
        call_args = mock_cursor.execute.call_args[0]
        assert call_args[1][3] == since
    
    def test_deactivate_device(self, device_manager, mock_connection):
        """Test deactivating a device."""
        mock_conn, mock_cursor = mock_connection
        device_uuid = str(uuid.uuid4())
        
        device_manager.deactivate_device(device_uuid)
        
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
    
    def test_get_sync_status(self, device_manager, mock_connection, sample_user_id):
        """Test getting sync status for a device."""
        mock_conn, mock_cursor = mock_connection
        device_uuid = str(uuid.uuid4())
        
        # Mock database responses
        mock_cursor.fetchone.side_effect = [
            (10,),  # total_rounds
            (50,),  # total_shots
            (8,),   # synced_rounds
            (45,)   # synced_shots
        ]
        
        # Mock get_entities_to_sync calls
        device_manager.get_entities_to_sync = lambda *args, **kwargs: [
            {'entity_id': str(uuid.uuid4()), 'updated_at': datetime.now()}
            for _ in range(2 if 'round' in str(args) else 5)
        ]
        
        status = device_manager.get_sync_status(device_uuid, sample_user_id)
        
        assert status['total_rounds'] == 10
        assert status['synced_rounds'] == 8
        assert status['pending_rounds'] == 2
        assert status['total_shots'] == 50
        assert status['synced_shots'] == 45
        assert status['pending_shots'] == 5


class TestMultipleDevices:
    """Test scenarios with multiple devices."""
    
    def test_multiple_devices_same_user(self, device_manager, mock_connection, sample_user_id):
        """Test that a user can have multiple devices."""
        mock_conn, mock_cursor = mock_connection
        
        device1_uuid = str(uuid.uuid4())
        device2_uuid = str(uuid.uuid4())
        device3_uuid = str(uuid.uuid4())
        
        mock_cursor.fetchall.return_value = [
            (device1_uuid, 'device-1', 'AR_GLASSES', 'AR Glasses', None, datetime.now(), {}),
            (device2_uuid, 'device-2', 'MOBILE_IOS', 'iPhone', datetime.now(), datetime.now(), {}),
            (device3_uuid, 'device-3', 'MOBILE_ANDROID', 'Android Phone', datetime.now(), datetime.now(), {})
        ]
        
        devices = device_manager.get_user_devices(sample_user_id)
        
        assert len(devices) == 3
        assert {d['device_type'] for d in devices} == {'AR_GLASSES', 'MOBILE_IOS', 'MOBILE_ANDROID'}
    
    def test_different_preferences_per_device(self, device_manager, mock_connection, sample_user_id):
        """Test that each device can have different preferences."""
        mock_conn, mock_cursor = mock_connection
        
        # AR Glasses prefers meters and power saving
        ar_prefs = {'distance_unit': 'METERS', 'power_saving': True}
        
        # Mobile prefers yards and notifications
        mobile_prefs = {'distance_unit': 'YARDS', 'notifications': True}
        
        user_prefs = {'auto_sync': True}
        
        # Test AR Glasses preferences
        mock_cursor.fetchone.side_effect = [(user_prefs,), (ar_prefs,)]
        ar_effective = device_manager.get_effective_preferences(sample_user_id, 'ar-device')
        
        assert ar_effective['distance_unit'] == 'METERS'
        assert ar_effective['power_saving'] is True
        assert ar_effective['auto_sync'] is True
        
        # Test Mobile preferences
        mock_cursor.fetchone.side_effect = [(user_prefs,), (mobile_prefs,)]
        mobile_effective = device_manager.get_effective_preferences(sample_user_id, 'mobile-device')
        
        assert mobile_effective['distance_unit'] == 'YARDS'
        assert mobile_effective['notifications'] is True
        assert mobile_effective['auto_sync'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
