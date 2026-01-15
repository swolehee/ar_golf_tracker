"""Data synchronization service with retry logic and exponential backoff."""

import time
import logging
import threading
from typing import Optional, Callable, Dict, Any, List
from ar_golf_tracker.ar_glasses.database import LocalDatabase
from ar_golf_tracker.shared.models import SyncStatus, Shot, Round
from ar_golf_tracker.shared.encryption import EncryptionService


logger = logging.getLogger(__name__)


class SyncService:
    """Manages data synchronization with retry logic and exponential backoff.
    
    Features:
    - Background sync when network available
    - Real-time sync with 10-second update window
    - Retry queue with exponential backoff
    - Automatic sync on network restoration
    """
    
    def __init__(
        self,
        database: LocalDatabase,
        max_retries: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        sync_interval: float = 10.0,
        network_check_callback: Optional[Callable[[], bool]] = None,
        encryption_service: Optional[EncryptionService] = None
    ):
        """Initialize sync service.
        
        Args:
            database: Local database instance
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff
            max_delay: Maximum delay in seconds between retries
            sync_interval: Interval in seconds for real-time sync (default 10.0)
            network_check_callback: Optional callback to check network availability
            encryption_service: Optional encryption service for data at rest
        """
        self.database = database
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.sync_interval = sync_interval
        self.network_check_callback = network_check_callback
        self.encryption_service = encryption_service
        
        # Background sync state
        self._background_sync_enabled = False
        self._background_sync_thread: Optional[threading.Thread] = None
        self._sync_callback: Optional[Callable[[str, str, str, Dict[str, Any]], bool]] = None
        self._stop_event = threading.Event()
        self._is_online = False
        
        # Real-time sync state
        self._last_sync_time = 0.0
    
    def calculate_backoff_delay(self, retry_count: int) -> float:
        """Calculate exponential backoff delay.
        
        Args:
            retry_count: Current retry attempt number
            
        Returns:
            Delay in seconds
        """
        delay = self.base_delay * (2 ** retry_count)
        return min(delay, self.max_delay)
    
    def enqueue_shot_create(self, shot: Shot) -> str:
        """Enqueue a shot creation for sync.
        
        Args:
            shot: Shot object to sync
            
        Returns:
            Queue entry ID
        """
        payload = self._shot_to_dict(shot)
        
        # Encrypt payload if encryption service is available
        if self.encryption_service:
            encrypted_payload = self.encryption_service.encrypt_dict(payload)
            payload = {'encrypted': True, 'data': encrypted_payload}
        
        return self.database.enqueue_sync(
            entity_type='SHOT',
            entity_id=shot.id,
            operation='CREATE',
            payload=payload
        )
    
    def enqueue_shot_update(self, shot: Shot) -> str:
        """Enqueue a shot update for sync.
        
        Args:
            shot: Shot object to sync
            
        Returns:
            Queue entry ID
        """
        payload = self._shot_to_dict(shot)
        
        # Encrypt payload if encryption service is available
        if self.encryption_service:
            encrypted_payload = self.encryption_service.encrypt_dict(payload)
            payload = {'encrypted': True, 'data': encrypted_payload}
        
        return self.database.enqueue_sync(
            entity_type='SHOT',
            entity_id=shot.id,
            operation='UPDATE',
            payload=payload
        )
    
    def enqueue_shot_delete(self, shot_id: str) -> str:
        """Enqueue a shot deletion for sync.
        
        Args:
            shot_id: Shot identifier
            
        Returns:
            Queue entry ID
        """
        payload = {'id': shot_id}
        return self.database.enqueue_sync(
            entity_type='SHOT',
            entity_id=shot_id,
            operation='DELETE',
            payload=payload
        )
    
    def enqueue_round_create(self, round_obj: Round) -> str:
        """Enqueue a round creation for sync.
        
        Args:
            round_obj: Round object to sync
            
        Returns:
            Queue entry ID
        """
        payload = self._round_to_dict(round_obj)
        
        # Encrypt payload if encryption service is available
        if self.encryption_service:
            encrypted_payload = self.encryption_service.encrypt_dict(payload)
            payload = {'encrypted': True, 'data': encrypted_payload}
        
        return self.database.enqueue_sync(
            entity_type='ROUND',
            entity_id=round_obj.id,
            operation='CREATE',
            payload=payload
        )
    
    def enqueue_round_update(self, round_obj: Round) -> str:
        """Enqueue a round update for sync.
        
        Args:
            round_obj: Round object to sync
            
        Returns:
            Queue entry ID
        """
        payload = self._round_to_dict(round_obj)
        
        # Encrypt payload if encryption service is available
        if self.encryption_service:
            encrypted_payload = self.encryption_service.encrypt_dict(payload)
            payload = {'encrypted': True, 'data': encrypted_payload}
        
        return self.database.enqueue_sync(
            entity_type='ROUND',
            entity_id=round_obj.id,
            operation='UPDATE',
            payload=payload
        )
    
    def enqueue_round_delete(self, round_id: str) -> str:
        """Enqueue a round deletion for sync.
        
        Args:
            round_id: Round identifier
            
        Returns:
            Queue entry ID
        """
        payload = {'id': round_id}
        return self.database.enqueue_sync(
            entity_type='ROUND',
            entity_id=round_id,
            operation='DELETE',
            payload=payload
        )
    
    def process_sync_queue(
        self,
        sync_callback: Callable[[str, str, str, Dict[str, Any]], bool],
        batch_size: int = 10
    ) -> Dict[str, int]:
        """Process pending sync queue items with retry logic.
        
        Args:
            sync_callback: Function to call for each sync item.
                          Should accept (entity_type, entity_id, operation, payload)
                          and return True on success, False on failure.
            batch_size: Number of items to process in one batch
            
        Returns:
            Dictionary with sync statistics (success, failed, skipped counts)
        """
        stats = {'success': 0, 'failed': 0, 'skipped': 0}
        
        pending_items = self.database.get_pending_sync_items(limit=batch_size)
        
        for item in pending_items:
            queue_id = item['id']
            retry_count = item['retry_count']
            
            # Skip items that have exceeded max retries
            if retry_count >= self.max_retries:
                logger.warning(
                    f"Skipping sync item {queue_id} - exceeded max retries ({self.max_retries})"
                )
                stats['skipped'] += 1
                continue
            
            # Check if we should retry based on backoff delay
            if retry_count > 0 and item['last_retry_at']:
                delay = self.calculate_backoff_delay(retry_count - 1)
                time_since_retry = time.time() - item['last_retry_at']
                
                if time_since_retry < delay:
                    logger.debug(
                        f"Skipping sync item {queue_id} - waiting for backoff delay"
                    )
                    stats['skipped'] += 1
                    continue
            
            # Decrypt payload if encrypted
            payload = item['payload']
            if isinstance(payload, dict) and payload.get('encrypted'):
                if self.encryption_service:
                    try:
                        payload = self.encryption_service.decrypt_dict(payload['data'])
                    except Exception as e:
                        logger.error(f"Failed to decrypt payload for {queue_id}: {e}")
                        stats['failed'] += 1
                        continue
                else:
                    logger.error(f"Encrypted payload but no encryption service available for {queue_id}")
                    stats['failed'] += 1
                    continue
            
            # Attempt to sync
            try:
                success = sync_callback(
                    item['entity_type'],
                    item['entity_id'],
                    item['operation'],
                    payload
                )
                
                if success:
                    # Remove from queue on success
                    self.database.remove_from_sync_queue(queue_id)
                    
                    # Update entity sync status
                    if item['entity_type'] == 'SHOT':
                        self.database.update_shot_sync_status(
                            item['entity_id'],
                            SyncStatus.SYNCED
                        )
                    elif item['entity_type'] == 'ROUND':
                        self.database.update_round_sync_status(
                            item['entity_id'],
                            SyncStatus.SYNCED
                        )
                    
                    stats['success'] += 1
                    logger.info(f"Successfully synced {item['entity_type']} {item['entity_id']}")
                else:
                    # Update retry count on failure
                    self.database.update_sync_retry(queue_id)
                    
                    # Update entity sync status to FAILED
                    if item['entity_type'] == 'SHOT':
                        self.database.update_shot_sync_status(
                            item['entity_id'],
                            SyncStatus.FAILED
                        )
                    elif item['entity_type'] == 'ROUND':
                        self.database.update_round_sync_status(
                            item['entity_id'],
                            SyncStatus.FAILED
                        )
                    
                    stats['failed'] += 1
                    logger.warning(
                        f"Failed to sync {item['entity_type']} {item['entity_id']} "
                        f"(retry {retry_count + 1}/{self.max_retries})"
                    )
            
            except Exception as e:
                # Update retry count on exception
                self.database.update_sync_retry(queue_id)
                stats['failed'] += 1
                logger.error(
                    f"Exception syncing {item['entity_type']} {item['entity_id']}: {e}",
                    exc_info=True
                )
        
        return stats
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current sync queue status.
        
        Returns:
            Dictionary with queue statistics
        """
        queue_size = self.database.get_sync_queue_size()
        pending_shots = len(self.database.get_shots_by_sync_status(SyncStatus.PENDING))
        pending_rounds = len(self.database.get_rounds_by_sync_status(SyncStatus.PENDING))
        failed_shots = len(self.database.get_shots_by_sync_status(SyncStatus.FAILED))
        failed_rounds = len(self.database.get_rounds_by_sync_status(SyncStatus.FAILED))
        
        return {
            'queue_size': queue_size,
            'pending_shots': pending_shots,
            'pending_rounds': pending_rounds,
            'failed_shots': failed_shots,
            'failed_rounds': failed_rounds
        }
    
    def cleanup_failed_items(self) -> int:
        """Remove items that have exceeded max retry attempts.
        
        Returns:
            Number of items removed
        """
        return self.database.clear_old_sync_items(max_retries=self.max_retries)
    
    def is_online(self) -> bool:
        """Check if network is available.
        
        Returns:
            True if network is available, False otherwise
        """
        if self.network_check_callback:
            self._is_online = self.network_check_callback()
        return self._is_online
    
    def set_online_status(self, is_online: bool) -> None:
        """Manually set online status.
        
        Args:
            is_online: Network availability status
        """
        was_offline = not self._is_online
        self._is_online = is_online
        
        # If transitioning from offline to online, trigger immediate sync
        if was_offline and is_online and self._background_sync_enabled:
            logger.info("Network restored - triggering immediate sync")
            self._trigger_sync()
    
    def start_background_sync(
        self,
        sync_callback: Callable[[str, str, str, Dict[str, Any]], bool],
        batch_size: int = 10
    ) -> None:
        """Start background sync service.
        
        Runs in a separate thread and syncs data when network is available.
        Syncs at regular intervals (default 10 seconds) for real-time updates.
        
        Args:
            sync_callback: Function to call for each sync item
            batch_size: Number of items to process in one batch
        """
        if self._background_sync_enabled:
            logger.warning("Background sync already running")
            return
        
        self._background_sync_enabled = True
        self._sync_callback = sync_callback
        self._stop_event.clear()
        
        # Start background thread
        self._background_sync_thread = threading.Thread(
            target=self._background_sync_loop,
            args=(batch_size,),
            daemon=True,
            name="SyncServiceThread"
        )
        self._background_sync_thread.start()
        logger.info(f"Background sync started with {self.sync_interval}s interval")
    
    def stop_background_sync(self) -> None:
        """Stop background sync service."""
        if not self._background_sync_enabled:
            return
        
        self._background_sync_enabled = False
        self._stop_event.set()
        
        # Wait for thread to finish
        if self._background_sync_thread and self._background_sync_thread.is_alive():
            self._background_sync_thread.join(timeout=5.0)
        
        logger.info("Background sync stopped")
    
    def _background_sync_loop(self, batch_size: int) -> None:
        """Background sync loop that runs in a separate thread.
        
        Args:
            batch_size: Number of items to process in one batch
        """
        while not self._stop_event.is_set():
            try:
                # Check if it's time to sync (10-second window)
                current_time = time.time()
                time_since_last_sync = current_time - self._last_sync_time
                
                if time_since_last_sync >= self.sync_interval:
                    # Check network availability
                    if self.is_online():
                        # Process sync queue
                        if self._sync_callback:
                            stats = self.process_sync_queue(
                                self._sync_callback,
                                batch_size
                            )
                            
                            if stats['success'] > 0 or stats['failed'] > 0:
                                logger.info(
                                    f"Background sync: {stats['success']} succeeded, "
                                    f"{stats['failed']} failed, {stats['skipped']} skipped"
                                )
                    else:
                        logger.debug("Network unavailable - skipping sync")
                    
                    self._last_sync_time = current_time
                
                # Sleep for a short interval before checking again
                self._stop_event.wait(timeout=1.0)
                
            except Exception as e:
                logger.error(f"Error in background sync loop: {e}", exc_info=True)
                # Continue running despite errors
                self._stop_event.wait(timeout=5.0)
    
    def _trigger_sync(self) -> None:
        """Trigger an immediate sync (used when network is restored)."""
        if self._sync_callback and self.is_online():
            try:
                stats = self.process_sync_queue(self._sync_callback, batch_size=10)
                logger.info(
                    f"Immediate sync: {stats['success']} succeeded, "
                    f"{stats['failed']} failed, {stats['skipped']} skipped"
                )
            except Exception as e:
                logger.error(f"Error in immediate sync: {e}", exc_info=True)
    
    def sync_now(self, batch_size: int = 10) -> Dict[str, int]:
        """Manually trigger an immediate sync.
        
        Args:
            batch_size: Number of items to process in one batch
            
        Returns:
            Dictionary with sync statistics
        """
        if not self._sync_callback:
            logger.warning("No sync callback configured")
            return {'success': 0, 'failed': 0, 'skipped': 0}
        
        if not self.is_online():
            logger.warning("Network unavailable - cannot sync")
            return {'success': 0, 'failed': 0, 'skipped': 0}
        
        stats = self.process_sync_queue(self._sync_callback, batch_size)
        self._last_sync_time = time.time()
        return stats
    
    def _shot_to_dict(self, shot: Shot) -> Dict[str, Any]:
        """Convert Shot object to dictionary for JSON serialization.
        
        Args:
            shot: Shot object
            
        Returns:
            Dictionary representation
        """
        return {
            'id': shot.id,
            'round_id': shot.round_id,
            'hole_number': shot.hole_number,
            'swing_number': shot.swing_number,
            'club_type': shot.club_type.value,
            'timestamp': shot.timestamp,
            'gps_origin': {
                'latitude': shot.gps_origin.latitude,
                'longitude': shot.gps_origin.longitude,
                'accuracy': shot.gps_origin.accuracy,
                'timestamp': shot.gps_origin.timestamp,
                'altitude': shot.gps_origin.altitude
            },
            'distance': {
                'value': shot.distance.value,
                'unit': shot.distance.unit.value,
                'accuracy': shot.distance.accuracy.value
            } if shot.distance else None,
            'notes': shot.notes,
            'sync_status': shot.sync_status.value
        }
    
    def _round_to_dict(self, round_obj: Round) -> Dict[str, Any]:
        """Convert Round object to dictionary for JSON serialization.
        
        Args:
            round_obj: Round object
            
        Returns:
            Dictionary representation
        """
        return {
            'id': round_obj.id,
            'user_id': round_obj.user_id,
            'course_id': round_obj.course_id,
            'course_name': round_obj.course_name,
            'start_time': round_obj.start_time,
            'end_time': round_obj.end_time,
            'weather': {
                'temperature': round_obj.weather.temperature,
                'wind_speed': round_obj.weather.wind_speed,
                'wind_direction': round_obj.weather.wind_direction,
                'conditions': round_obj.weather.conditions
            } if round_obj.weather else None,
            'sync_status': round_obj.sync_status.value
        }
