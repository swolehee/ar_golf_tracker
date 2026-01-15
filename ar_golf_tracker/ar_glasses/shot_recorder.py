"""Shot recording orchestration with swing detection integration."""

from typing import Optional
from ar_golf_tracker.shared.models import ClubType, GPSPosition
from ar_golf_tracker.ar_glasses.swing_detection import SwingDetectionService, SwingEvent
from ar_golf_tracker.ar_glasses.gps_tracking import GPSTrackingService
from ar_golf_tracker.ar_glasses.club_recognition import ClubRecognitionService
from ar_golf_tracker.ar_glasses.shot_manager import ShotManager
from ar_golf_tracker.ar_glasses.database import LocalDatabase


class ShotRecorder:
    """Orchestrates shot recording from swing detection, GPS, and club recognition.
    
    This class integrates multiple services to automatically record shots:
    1. Monitors swing detection for full swings
    2. Captures GPS position at time of swing
    3. Gets current club from club recognition
    4. Creates shot record with all data
    5. Provides user feedback
    """
    
    def __init__(
        self,
        database: LocalDatabase,
        swing_detector: SwingDetectionService,
        gps_tracker: GPSTrackingService,
        club_recognizer: ClubRecognitionService,
        shot_manager: Optional[ShotManager] = None
    ):
        """Initialize shot recorder.
        
        Args:
            database: Local database for shot storage
            swing_detector: Swing detection service
            gps_tracker: GPS tracking service
            club_recognizer: Club recognition service
            shot_manager: Shot manager (creates default if None)
        """
        self.database = database
        self.swing_detector = swing_detector
        self.gps_tracker = gps_tracker
        self.club_recognizer = club_recognizer
        self.shot_manager = shot_manager or ShotManager(database)
        
        # Current round context
        self._current_round_id: Optional[str] = None
        self._current_hole_number: int = 1
        
        # Register swing detection callback
        self.swing_detector.on_swing_detected(self._on_swing_detected)
    
    def start_recording(self, round_id: str, starting_hole: int = 1) -> None:
        """Start recording shots for a round.
        
        Args:
            round_id: Round identifier
            starting_hole: Starting hole number (default 1)
        """
        self._current_round_id = round_id
        self._current_hole_number = starting_hole
        
        # Start all services
        self.swing_detector.start_monitoring()
        self.gps_tracker.start_tracking()
        self.club_recognizer.start_recognition()
    
    def stop_recording(self) -> None:
        """Stop recording shots."""
        # Stop all services
        self.swing_detector.stop_monitoring()
        self.gps_tracker.stop_tracking()
        self.club_recognizer.stop_recognition()
        
        # Clear context
        self._current_round_id = None
    
    def set_hole_number(self, hole_number: int) -> None:
        """Update current hole number.
        
        This should be called when transitioning to a new hole,
        either manually or automatically via course detection.
        
        Args:
            hole_number: New hole number
        """
        self._current_hole_number = hole_number
    
    def _on_swing_detected(self, swing_event: SwingEvent) -> None:
        """Handle swing detection event.
        
        This callback is invoked when the swing detector identifies a swing.
        It filters for full swings and creates shot records.
        
        Args:
            swing_event: Detected swing event
        """
        # Only record full swings (not practice swings)
        if swing_event.swing_type != 'FULL_SWING':
            return
        
        # Check if we have an active round
        if self._current_round_id is None:
            print("Warning: Swing detected but no active round")
            return
        
        # Get current GPS position
        gps_position = self.gps_tracker.get_current_position()
        if gps_position is None:
            print("Warning: GPS position unavailable for shot")
            # Could queue shot for later GPS update
            return
        
        # Get current club
        club_type = self.club_recognizer.get_current_club()
        if club_type is None:
            print("Warning: Club not recognized for shot")
            # Could prompt user or use last known club
            club_type = ClubType.DRIVER  # Default fallback
        
        # Record the shot
        try:
            shot = self.shot_manager.record_shot(
                round_id=self._current_round_id,
                hole_number=self._current_hole_number,
                club_type=club_type,
                gps_position=gps_position,
                notes=f"Confidence: {swing_event.confidence:.2f}"
            )
            
            # Provide feedback to user
            self._provide_feedback(shot, swing_event)
            
        except Exception as e:
            print(f"Error recording shot: {e}")
    
    def _provide_feedback(self, shot, swing_event: SwingEvent) -> None:
        """Provide haptic/visual feedback to user after shot recording.
        
        This would interface with AR glasses hardware to provide:
        - Haptic vibration (short pulse)
        - Visual confirmation (brief overlay)
        - Audio confirmation (optional beep)
        
        Args:
            shot: Recorded shot object
            swing_event: Swing event that triggered recording
        """
        # TODO: Implement actual hardware feedback
        # For now, just log confirmation
        print(f"Shot recorded: Hole {shot.hole_number}, "
              f"Swing {shot.swing_number}, "
              f"Club {shot.club_type.value}")
        
        # In production, this would call platform-specific APIs:
        # - Android: Vibrator.vibrate()
        # - iOS: UIImpactFeedbackGenerator
        # - Meta AR SDK: specific haptic feedback API
        
        # Visual feedback would display brief overlay:
        # "✓ Shot Recorded - Driver - Hole 1"
    
    def manual_record_shot(
        self,
        club_type: ClubType,
        notes: Optional[str] = None
    ) -> None:
        """Manually record a shot (for cases where auto-detection fails).
        
        Args:
            club_type: Club used for the shot
            notes: Optional notes about the shot
        """
        if self._current_round_id is None:
            print("Error: No active round")
            return
        
        gps_position = self.gps_tracker.get_current_position()
        if gps_position is None:
            print("Error: GPS position unavailable")
            return
        
        shot = self.shot_manager.record_shot(
            round_id=self._current_round_id,
            hole_number=self._current_hole_number,
            club_type=club_type,
            gps_position=gps_position,
            notes=notes
        )
        
        print(f"Manual shot recorded: {shot.id}")
    
    def delete_last_shot(self) -> bool:
        """Delete the most recent shot on current hole.
        
        Useful for correcting false positives from swing detection.
        
        Returns:
            True if shot was deleted, False if no shot to delete
        """
        if self._current_round_id is None:
            return False
        
        last_shot = self.shot_manager.get_last_shot_on_hole(
            self._current_round_id,
            self._current_hole_number
        )
        
        if last_shot is None:
            return False
        
        self.shot_manager.delete_shot(last_shot.id)
        print(f"Deleted shot: {last_shot.id}")
        return True
