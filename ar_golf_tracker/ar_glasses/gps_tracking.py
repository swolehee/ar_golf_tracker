"""GPS tracking service for AR glasses."""

import time
from typing import Callable, Optional
from threading import Thread, Event, Lock
from ar_golf_tracker.shared.models import GPSPosition


class GPSTrackingService:
    """Manages GPS position tracking with adaptive sampling."""
    
    def __init__(self, update_interval: float = 1.0):
        """Initialize GPS tracking service.
        
        Args:
            update_interval: Base update interval in seconds (default 1 Hz)
        """
        self.update_interval = update_interval
        self._callbacks: list[Callable[[GPSPosition], None]] = []
        self._tracking_thread: Optional[Thread] = None
        self._stop_event = Event()
        self._lock = Lock()
        self._current_position: Optional[GPSPosition] = None
        self._last_position: Optional[GPSPosition] = None
        self._movement_threshold = 1.0  # meters - threshold for detecting movement
        
    def start_tracking(self) -> None:
        """Start GPS position tracking in background thread."""
        if self._tracking_thread is not None and self._tracking_thread.is_alive():
            return  # Already tracking
        
        self._stop_event.clear()
        self._tracking_thread = Thread(target=self._tracking_loop, daemon=True)
        self._tracking_thread.start()
    
    def stop_tracking(self) -> None:
        """Stop GPS position tracking."""
        if self._tracking_thread is None:
            return
        
        self._stop_event.set()
        if self._tracking_thread.is_alive():
            self._tracking_thread.join(timeout=2.0)
        self._tracking_thread = None
    
    def get_current_position(self) -> Optional[GPSPosition]:
        """Get the most recent GPS position.
        
        Returns:
            Current GPS position or None if not available
        """
        with self._lock:
            return self._current_position
    
    def on_position_update(self, callback: Callable[[GPSPosition], None]) -> None:
        """Register callback for position updates.
        
        Args:
            callback: Function to call when position updates
        """
        with self._lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[GPSPosition], None]) -> None:
        """Remove a registered callback.
        
        Args:
            callback: Callback function to remove
        """
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)
    
    def _tracking_loop(self) -> None:
        """Main tracking loop running in background thread."""
        while not self._stop_event.is_set():
            try:
                # Capture GPS position
                position = self._capture_gps_position()
                
                if position:
                    # Update current position
                    with self._lock:
                        self._current_position = position
                    
                    # Notify callbacks
                    self._notify_callbacks(position)
                    
                    # Update last position for movement detection
                    self._last_position = position
                
                # Adaptive sampling: adjust interval based on movement
                interval = self._calculate_adaptive_interval()
                self._stop_event.wait(interval)
                
            except Exception as e:
                # Log error but continue tracking
                print(f"GPS tracking error: {e}")
                self._stop_event.wait(self.update_interval)
    
    def _capture_gps_position(self) -> Optional[GPSPosition]:
        """Capture current GPS position from device.
        
        This is a placeholder that would interface with actual GPS hardware.
        In production, this would use platform-specific GPS APIs.
        
        Returns:
            GPS position with accuracy estimate or None if unavailable
        """
        # TODO: Replace with actual GPS hardware interface
        # For now, return a mock position for testing
        # In production, this would call platform GPS APIs like:
        # - Android: LocationManager.getLastKnownLocation()
        # - iOS: CLLocationManager.location
        # - Meta AR SDK: specific AR glasses GPS API
        
        timestamp = int(time.time())
        
        # Mock implementation - would be replaced with real GPS reading
        # Real implementation would handle:
        # - GPS signal availability
        # - Accuracy estimation from satellite count/signal strength
        # - Altitude from barometric sensor or GPS
        # - Error handling for GPS unavailable
        
        return None  # Return None until real GPS interface is implemented
    
    def _calculate_adaptive_interval(self) -> float:
        """Calculate adaptive sampling interval based on movement.
        
        Reduces GPS sampling frequency when stationary to save battery.
        
        Returns:
            Update interval in seconds
        """
        if self._last_position is None or self._current_position is None:
            return self.update_interval
        
        # Calculate distance moved since last update
        distance_moved = self._calculate_distance(
            self._last_position,
            self._current_position
        )
        
        # If moving, use base interval (1 Hz)
        # If stationary, reduce to 0.2 Hz (every 5 seconds)
        if distance_moved > self._movement_threshold:
            return self.update_interval
        else:
            return self.update_interval * 5.0
    
    def _calculate_distance(self, pos1: GPSPosition, pos2: GPSPosition) -> float:
        """Calculate approximate distance between two GPS positions.
        
        Uses simple Euclidean approximation for short distances.
        For accurate distance calculation, use the Haversine formula
        in the distance calculation service.
        
        Args:
            pos1: First GPS position
            pos2: Second GPS position
            
        Returns:
            Approximate distance in meters
        """
        # Simple approximation for movement detection
        # 1 degree latitude ≈ 111 km
        # 1 degree longitude ≈ 111 km * cos(latitude)
        import math
        
        lat_diff = (pos2.latitude - pos1.latitude) * 111000
        lon_diff = (pos2.longitude - pos1.longitude) * 111000 * math.cos(
            math.radians(pos1.latitude)
        )
        
        return math.sqrt(lat_diff**2 + lon_diff**2)
    
    def _notify_callbacks(self, position: GPSPosition) -> None:
        """Notify all registered callbacks of position update.
        
        Args:
            position: New GPS position
        """
        with self._lock:
            callbacks = self._callbacks.copy()
        
        for callback in callbacks:
            try:
                callback(position)
            except Exception as e:
                print(f"Error in GPS callback: {e}")
    
    def estimate_accuracy(self, position: GPSPosition) -> float:
        """Estimate GPS accuracy based on signal characteristics.
        
        This is a helper method that would use platform-specific APIs
        to determine GPS accuracy from satellite count, signal strength, etc.
        
        Args:
            position: GPS position to estimate accuracy for
            
        Returns:
            Estimated accuracy in meters
        """
        # In production, this would use:
        # - Number of satellites in view
        # - Signal-to-noise ratio
        # - Horizontal dilution of precision (HDOP)
        # - Device-reported accuracy
        
        return position.accuracy
