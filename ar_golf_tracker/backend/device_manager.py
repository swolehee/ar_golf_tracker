"""Device management service for cross-device sync.

Handles device registration, device-specific preferences, and tracking
which data has been synced to each device.
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging


logger = logging.getLogger(__name__)


class DeviceManager:
    """Manages device registration and device-specific preferences."""
    
    def __init__(self, db_connection):
        """Initialize device manager.
        
        Args:
            db_connection: Database connection
        """
        self.conn = db_connection
    
    def register_device(
        self,
        user_id: str,
        device_id: str,
        device_type: str,
        device_name: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """Register or update a device for a user.
        
        Args:
            user_id: User ID
            device_id: Unique device identifier
            device_type: Type of device ('AR_GLASSES', 'MOBILE_IOS', 'MOBILE_ANDROID', 'WEB')
            device_name: User-friendly device name
            device_info: Device metadata (OS version, app version, etc.)
            
        Returns:
            Device UUID
        """
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT register_device(%s, %s, %s, %s, %s)",
                (user_id, device_id, device_type, device_name, device_info)
            )
            device_uuid = cursor.fetchone()[0]
        
        self.conn.commit()
        logger.info(f"Registered device {device_id} for user {user_id}")
        return str(device_uuid)
    
    def get_user_devices(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active devices for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of device information dictionaries
        """
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM get_user_devices(%s)",
                (user_id,)
            )
            devices = cursor.fetchall()
        
        return [
            {
                'device_uuid': str(row[0]),
                'device_id': row[1],
                'device_type': row[2],
                'device_name': row[3],
                'last_sync_at': row[4],
                'last_active_at': row[5],
                'device_preferences': row[6] or {}
            }
            for row in devices
        ]
    
    def get_device_by_id(self, user_id: str, device_id: str) -> Optional[Dict[str, Any]]:
        """Get device information by device ID.
        
        Args:
            user_id: User ID
            device_id: Device identifier
            
        Returns:
            Device information or None if not found
        """
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, device_id, device_type, device_name, last_sync_at,
                       last_active_at, device_preferences, device_info
                FROM user_devices
                WHERE user_id = %s AND device_id = %s AND is_active = true
                """,
                (user_id, device_id)
            )
            row = cursor.fetchone()
        
        if not row:
            return None
        
        return {
            'device_uuid': str(row[0]),
            'device_id': row[1],
            'device_type': row[2],
            'device_name': row[3],
            'last_sync_at': row[4],
            'last_active_at': row[5],
            'device_preferences': row[6] or {},
            'device_info': row[7] or {}
        }
    
    def update_device_preferences(
        self,
        device_uuid: str,
        preferences: Dict[str, Any]
    ) -> None:
        """Update device-specific preferences.
        
        Device preferences override user preferences for that specific device.
        
        Args:
            device_uuid: Device UUID
            preferences: Device-specific preferences
        """
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE user_devices
                SET device_preferences = %s, updated_at = NOW()
                WHERE id = %s
                """,
                (preferences, device_uuid)
            )
        
        self.conn.commit()
        logger.info(f"Updated preferences for device {device_uuid}")
    
    def get_effective_preferences(
        self,
        user_id: str,
        device_id: str
    ) -> Dict[str, Any]:
        """Get effective preferences for a device.
        
        Merges user preferences with device-specific preferences,
        with device preferences taking precedence.
        
        Args:
            user_id: User ID
            device_id: Device identifier
            
        Returns:
            Merged preferences dictionary
        """
        with self.conn.cursor() as cursor:
            # Get user preferences
            cursor.execute(
                "SELECT preferences FROM users WHERE id = %s",
                (user_id,)
            )
            user_prefs = cursor.fetchone()
            user_preferences = user_prefs[0] if user_prefs and user_prefs[0] else {}
            
            # Get device preferences
            cursor.execute(
                """
                SELECT device_preferences FROM user_devices
                WHERE user_id = %s AND device_id = %s AND is_active = true
                """,
                (user_id, device_id)
            )
            device_prefs = cursor.fetchone()
            device_preferences = device_prefs[0] if device_prefs and device_prefs[0] else {}
        
        # Merge preferences (device overrides user)
        effective_prefs = {**user_preferences, **device_preferences}
        return effective_prefs
    
    def update_device_sync_timestamp(self, device_uuid: str) -> None:
        """Update the last sync timestamp for a device.
        
        Args:
            device_uuid: Device UUID
        """
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT update_device_sync_timestamp(%s)",
                (device_uuid,)
            )
        
        self.conn.commit()
    
    def log_device_sync(
        self,
        device_uuid: str,
        entity_type: str,
        entity_id: str,
        sync_direction: str
    ) -> None:
        """Log that an entity has been synced to/from a device.
        
        Args:
            device_uuid: Device UUID
            entity_type: Type of entity ('round', 'shot')
            entity_id: Entity ID
            sync_direction: Direction of sync ('TO_CLOUD', 'FROM_CLOUD')
        """
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT log_device_sync(%s, %s, %s, %s)",
                (device_uuid, entity_type, entity_id, sync_direction)
            )
        
        self.conn.commit()
    
    def get_entities_to_sync(
        self,
        device_uuid: str,
        user_id: str,
        entity_type: str,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get entities that need to be synced to a device.
        
        Returns entities that have been updated since the last sync
        to this device.
        
        Args:
            device_uuid: Device UUID
            user_id: User ID
            entity_type: Type of entity ('round', 'shot')
            since: Optional timestamp to filter entities updated after this time
            
        Returns:
            List of entity IDs and update timestamps
        """
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM get_entities_to_sync(%s, %s, %s, %s)",
                (device_uuid, user_id, entity_type, since)
            )
            entities = cursor.fetchall()
        
        return [
            {
                'entity_id': str(row[0]),
                'updated_at': row[1]
            }
            for row in entities
        ]
    
    def deactivate_device(self, device_uuid: str) -> None:
        """Deactivate a device (soft delete).
        
        Args:
            device_uuid: Device UUID
        """
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE user_devices
                SET is_active = false, updated_at = NOW()
                WHERE id = %s
                """,
                (device_uuid,)
            )
        
        self.conn.commit()
        logger.info(f"Deactivated device {device_uuid}")
    
    def get_sync_status(
        self,
        device_uuid: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Get sync status for a device.
        
        Args:
            device_uuid: Device UUID
            user_id: User ID
            
        Returns:
            Sync status information
        """
        # Get total entities for user
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM user_rounds WHERE user_id = %s",
                (user_id,)
            )
            total_rounds = cursor.fetchone()[0]
            
            cursor.execute(
                """
                SELECT COUNT(*) FROM user_shots s
                JOIN user_rounds r ON s.round_id = r.id
                WHERE r.user_id = %s
                """,
                (user_id,)
            )
            total_shots = cursor.fetchone()[0]
        
        # Get synced entities for device
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) FROM device_sync_log
                WHERE device_id = %s AND entity_type = 'round'
                AND sync_direction = 'FROM_CLOUD'
                """,
                (device_uuid,)
            )
            synced_rounds = cursor.fetchone()[0]
            
            cursor.execute(
                """
                SELECT COUNT(*) FROM device_sync_log
                WHERE device_id = %s AND entity_type = 'shot'
                AND sync_direction = 'FROM_CLOUD'
                """,
                (device_uuid,)
            )
            synced_shots = cursor.fetchone()[0]
        
        # Get entities pending sync
        pending_rounds = self.get_entities_to_sync(device_uuid, user_id, 'round')
        pending_shots = self.get_entities_to_sync(device_uuid, user_id, 'shot')
        
        return {
            'total_rounds': total_rounds,
            'synced_rounds': synced_rounds,
            'pending_rounds': len(pending_rounds),
            'total_shots': total_shots,
            'synced_shots': synced_shots,
            'pending_shots': len(pending_shots)
        }
