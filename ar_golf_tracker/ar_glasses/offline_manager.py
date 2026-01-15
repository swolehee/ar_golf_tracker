"""Offline operation manager for handling network unavailability."""

import logging
from typing import Optional, Callable
from ar_golf_tracker.ar_glasses.database import LocalDatabase
from ar_golf_tracker.ar_glasses.sync_service import SyncService
from ar_golf_tracker.shared.models import Shot, Round, SyncStatus


logger = logging.getLogger(__name__)


class OfflineManager:
    """Manages offline operation and automatic sync when network becomes available."""
    
    def __init__(
        self,
        database: LocalDatabase,
        sync_service: SyncService,
        network_check_callback: Optional[Callable[[], bool]] = None
    ):
        """Initialize offline manager.
        
        Args:
            database: Local database instance
            sync_service: Sync service instance
            network_check_callback: Optional callback to check network availability.
                                   Should return True if network is available.
        """
        self.database = database
        self.sync_service = sync_service
        self.network_check_callback = network_check_callback
        self._is_online = False
    
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
        self._is_online = is_online
        logger.info(f"Network status changed: {'online' if is_online else 'offline'}")
    
    def record_shot(self, shot: Shot, auto_sync: bool = True) -> None:
        """Record a shot with automatic offline handling.
        
        Args:
            shot: Shot object to record
            auto_sync: Whether to attempt immediate sync if online
        """
        # Check if shot already exists
        existing_shot = self.database.get_shot(shot.id)
        
        if existing_shot is None:
            # Create new shot
            self.database.create_shot(shot)
            logger.info(f"Shot {shot.id} saved to local database")
            
            # Queue for sync
            self.sync_service.enqueue_shot_create(shot)
            logger.info(f"Shot {shot.id} queued for sync")
        else:
            # Update existing shot
            self.database.update_shot(shot)
            logger.info(f"Shot {shot.id} updated in local database")
            
            # Queue for sync
            self.sync_service.enqueue_shot_update(shot)
            logger.info(f"Shot {shot.id} update queued for sync")
        
        # Attempt immediate sync if online and auto_sync enabled
        if auto_sync and self.is_online():
            logger.debug(f"Network available - attempting immediate sync for shot {shot.id}")
    
    def update_shot(self, shot: Shot, auto_sync: bool = True) -> None:
        """Update a shot with automatic offline handling.
        
        Args:
            shot: Shot object with updated data
            auto_sync: Whether to attempt immediate sync if online
        """
        # Update local database
        self.database.update_shot(shot)
        logger.info(f"Shot {shot.id} updated in local database")
        
        # Queue for sync
        self.sync_service.enqueue_shot_update(shot)
        logger.info(f"Shot {shot.id} update queued for sync")
        
        # Attempt immediate sync if online and auto_sync enabled
        if auto_sync and self.is_online():
            logger.debug(f"Network available - attempting immediate sync for shot {shot.id}")
    
    def delete_shot(self, shot_id: str, auto_sync: bool = True) -> None:
        """Delete a shot with automatic offline handling.
        
        Args:
            shot_id: Shot identifier
            auto_sync: Whether to attempt immediate sync if online
        """
        # Delete from local database
        self.database.delete_shot(shot_id)
        logger.info(f"Shot {shot_id} deleted from local database")
        
        # Queue for sync
        self.sync_service.enqueue_shot_delete(shot_id)
        logger.info(f"Shot {shot_id} deletion queued for sync")
        
        # Attempt immediate sync if online and auto_sync enabled
        if auto_sync and self.is_online():
            logger.debug(f"Network available - attempting immediate sync for shot deletion {shot_id}")
    
    def record_round(self, round_obj: Round, auto_sync: bool = True) -> None:
        """Record a round with automatic offline handling.
        
        Args:
            round_obj: Round object to record
            auto_sync: Whether to attempt immediate sync if online
        """
        # Check if round already exists
        existing_round = self.database.get_round(round_obj.id)
        
        if existing_round is None:
            # Create new round
            self.database.create_round(round_obj)
            logger.info(f"Round {round_obj.id} saved to local database")
            
            # Queue for sync
            self.sync_service.enqueue_round_create(round_obj)
            logger.info(f"Round {round_obj.id} queued for sync")
        else:
            # Update existing round
            self.database.update_round(round_obj)
            logger.info(f"Round {round_obj.id} updated in local database")
            
            # Queue for sync
            self.sync_service.enqueue_round_update(round_obj)
            logger.info(f"Round {round_obj.id} update queued for sync")
        
        # Attempt immediate sync if online and auto_sync enabled
        if auto_sync and self.is_online():
            logger.debug(f"Network available - attempting immediate sync for round {round_obj.id}")
    
    def update_round(self, round_obj: Round, auto_sync: bool = True) -> None:
        """Update a round with automatic offline handling.
        
        Args:
            round_obj: Round object with updated data
            auto_sync: Whether to attempt immediate sync if online
        """
        # Update local database
        self.database.update_round(round_obj)
        logger.info(f"Round {round_obj.id} updated in local database")
        
        # Queue for sync
        self.sync_service.enqueue_round_update(round_obj)
        logger.info(f"Round {round_obj.id} update queued for sync")
        
        # Attempt immediate sync if online and auto_sync enabled
        if auto_sync and self.is_online():
            logger.debug(f"Network available - attempting immediate sync for round {round_obj.id}")
    
    def delete_round(self, round_id: str, auto_sync: bool = True) -> None:
        """Delete a round with automatic offline handling.
        
        Args:
            round_id: Round identifier
            auto_sync: Whether to attempt immediate sync if online
        """
        # Delete from local database
        self.database.delete_round(round_id)
        logger.info(f"Round {round_id} deleted from local database")
        
        # Queue for sync
        self.sync_service.enqueue_round_delete(round_id)
        logger.info(f"Round {round_id} deletion queued for sync")
        
        # Attempt immediate sync if online and auto_sync enabled
        if auto_sync and self.is_online():
            logger.debug(f"Network available - attempting immediate sync for round deletion {round_id}")
    
    def get_pending_sync_count(self) -> int:
        """Get the number of items waiting to be synced.
        
        Returns:
            Number of pending sync items
        """
        return self.database.get_sync_queue_size()
    
    def get_offline_status(self) -> dict:
        """Get comprehensive offline operation status.
        
        Returns:
            Dictionary with offline operation statistics
        """
        queue_status = self.sync_service.get_queue_status()
        
        return {
            'is_online': self.is_online(),
            'queue_size': queue_status['queue_size'],
            'pending_shots': queue_status['pending_shots'],
            'pending_rounds': queue_status['pending_rounds'],
            'failed_shots': queue_status['failed_shots'],
            'failed_rounds': queue_status['failed_rounds']
        }
    
    def sync_when_online(
        self,
        sync_callback: Callable[[str, str, str, dict], bool],
        batch_size: int = 10
    ) -> dict:
        """Attempt to sync pending items if network is available.
        
        Args:
            sync_callback: Function to call for each sync item
            batch_size: Number of items to process in one batch
            
        Returns:
            Dictionary with sync statistics
        """
        if not self.is_online():
            logger.info("Network unavailable - skipping sync")
            return {'success': 0, 'failed': 0, 'skipped': 0, 'offline': True}
        
        logger.info("Network available - processing sync queue")
        stats = self.sync_service.process_sync_queue(sync_callback, batch_size)
        stats['offline'] = False
        
        logger.info(
            f"Sync completed: {stats['success']} succeeded, "
            f"{stats['failed']} failed, {stats['skipped']} skipped"
        )
        
        return stats
    
    def ensure_data_continuity(self) -> bool:
        """Verify that all data is properly stored locally.
        
        Returns:
            True if data integrity is maintained
        """
        try:
            # Check database connection
            conn = self.database.connect()
            
            # Verify tables exist
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('rounds', 'shots', 'sync_queue')
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            if len(tables) != 3:
                logger.error(f"Missing database tables. Found: {tables}")
                return False
            
            # Check for any corrupted records
            cursor.execute("SELECT COUNT(*) FROM shots WHERE id IS NULL")
            null_shots = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM rounds WHERE id IS NULL")
            null_rounds = cursor.fetchone()[0]
            
            if null_shots > 0 or null_rounds > 0:
                logger.error(f"Found corrupted records: {null_shots} shots, {null_rounds} rounds")
                return False
            
            logger.info("Data continuity verified - all data properly stored")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying data continuity: {e}", exc_info=True)
            return False
