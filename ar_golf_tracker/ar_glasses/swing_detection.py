"""Swing detection service using IMU data processing."""

import time
import numpy as np
from typing import Callable, Optional, List, Dict, Any
from dataclasses import dataclass
from threading import Thread, Event, Lock
from collections import deque
import pickle
import os


@dataclass
class IMUReading:
    """Single IMU sensor reading."""
    timestamp: float  # seconds
    accel_x: float    # m/s^2
    accel_y: float    # m/s^2
    accel_z: float    # m/s^2
    gyro_x: float     # rad/s
    gyro_y: float     # rad/s
    gyro_z: float     # rad/s


@dataclass
class SwingFeatures:
    """Extracted features from swing motion."""
    peak_acceleration: float      # m/s^2
    peak_angular_velocity: float  # rad/s
    swing_duration: float         # seconds
    impact_detected: bool
    timestamp: float              # seconds


@dataclass
class SwingEvent:
    """Detected swing event with classification."""
    timestamp: int                # Unix timestamp
    swing_type: str              # 'FULL_SWING' or 'PRACTICE_SWING'
    peak_acceleration: float     # m/s^2
    swing_duration: float        # seconds
    confidence: float            # 0.0 to 1.0


class SwingDetectionService:
    """Processes IMU data to detect and classify golf swings."""
    
    # IMU sampling rate
    SAMPLING_RATE_HZ = 100
    SAMPLING_INTERVAL = 1.0 / SAMPLING_RATE_HZ
    
    # Swing detection thresholds
    ACCEL_THRESHOLD = 20.0  # m/s^2 - minimum peak acceleration for swing
    GYRO_THRESHOLD = 10.0   # rad/s - minimum angular velocity for swing
    
    # Swing timing parameters
    MIN_SWING_DURATION = 0.3  # seconds
    MAX_SWING_DURATION = 2.0  # seconds
    
    # Buffer size for IMU data (2 seconds at 100 Hz)
    BUFFER_SIZE = 200
    
    def __init__(self, classifier_path: Optional[str] = None):
        """Initialize swing detection service.
        
        Args:
            classifier_path: Path to trained classifier model file (optional)
        """
        self._callbacks: List[Callable[[SwingEvent], None]] = []
        self._monitoring_thread: Optional[Thread] = None
        self._stop_event = Event()
        self._lock = Lock()
        
        # Circular buffer for IMU readings
        self._imu_buffer: deque[IMUReading] = deque(maxlen=self.BUFFER_SIZE)
        
        # Swing detection state
        self._in_swing = False
        self._swing_start_time: Optional[float] = None
        self._swing_readings: List[IMUReading] = []
        
        # Load or create classifier
        self._classifier = self._load_classifier(classifier_path)
    
    def start_monitoring(self) -> None:
        """Start monitoring IMU data for swing detection."""
        if self._monitoring_thread is not None and self._monitoring_thread.is_alive():
            return  # Already monitoring
        
        self._stop_event.clear()
        self._monitoring_thread = Thread(target=self._monitoring_loop, daemon=True)
        self._monitoring_thread.start()
    
    def stop_monitoring(self) -> None:
        """Stop monitoring IMU data."""
        if self._monitoring_thread is None:
            return
        
        self._stop_event.set()
        if self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=2.0)
        self._monitoring_thread = None
    
    def on_swing_detected(self, callback: Callable[[SwingEvent], None]) -> None:
        """Register callback for swing detection events.
        
        Args:
            callback: Function to call when swing is detected
        """
        with self._lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[SwingEvent], None]) -> None:
        """Remove a registered callback.
        
        Args:
            callback: Callback function to remove
        """
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)
    
    def calibrate(self, user_profile) -> None:
        """Calibrate swing detection for user's swing characteristics.
        
        Args:
            user_profile: User profile with swing characteristics
        """
        # TODO: Implement calibration logic in future enhancement
        # This would adjust thresholds based on user's typical swing speed,
        # tempo, and dominant hand
        pass
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop running in background thread."""
        while not self._stop_event.is_set():
            try:
                # Capture IMU reading
                reading = self._capture_imu_reading()
                
                if reading:
                    # Add to buffer
                    self._imu_buffer.append(reading)
                    
                    # Process for swing detection
                    self._process_imu_reading(reading)
                
                # Sleep until next sample
                self._stop_event.wait(self.SAMPLING_INTERVAL)
                
            except Exception as e:
                print(f"Swing detection error: {e}")
                self._stop_event.wait(self.SAMPLING_INTERVAL)
    
    def _capture_imu_reading(self) -> Optional[IMUReading]:
        """Capture current IMU sensor reading.
        
        This is a placeholder that would interface with actual IMU hardware.
        In production, this would use platform-specific IMU APIs.
        
        Returns:
            IMU reading or None if unavailable
        """
        # TODO: Replace with actual IMU hardware interface
        # For now, return None for testing
        # In production, this would call platform IMU APIs like:
        # - Android: SensorManager for TYPE_ACCELEROMETER and TYPE_GYROSCOPE
        # - iOS: CMMotionManager for accelerometer and gyroscope
        # - Meta AR SDK: specific AR glasses IMU API
        
        return None  # Return None until real IMU interface is implemented
    
    def _process_imu_reading(self, reading: IMUReading) -> None:
        """Process IMU reading for swing detection.
        
        Args:
            reading: Current IMU reading
        """
        # Calculate magnitude of acceleration and angular velocity
        accel_magnitude = np.sqrt(
            reading.accel_x**2 + reading.accel_y**2 + reading.accel_z**2
        )
        gyro_magnitude = np.sqrt(
            reading.gyro_x**2 + reading.gyro_y**2 + reading.gyro_z**2
        )
        
        # State machine for swing detection
        if not self._in_swing:
            # Check if swing is starting
            if (accel_magnitude > self.ACCEL_THRESHOLD or 
                gyro_magnitude > self.GYRO_THRESHOLD):
                self._start_swing_detection(reading)
        else:
            # Add reading to current swing
            self._swing_readings.append(reading)
            
            # Check if swing has ended
            swing_duration = reading.timestamp - self._swing_start_time
            
            # Swing ends when motion drops below threshold or max duration exceeded
            if (accel_magnitude < self.ACCEL_THRESHOLD * 0.3 and 
                gyro_magnitude < self.GYRO_THRESHOLD * 0.3 and
                swing_duration > self.MIN_SWING_DURATION):
                self._end_swing_detection()
            elif swing_duration > self.MAX_SWING_DURATION:
                # Timeout - reset without detecting swing
                self._reset_swing_detection()
    
    def _start_swing_detection(self, reading: IMUReading) -> None:
        """Start tracking a potential swing.
        
        Args:
            reading: IMU reading that triggered swing start
        """
        self._in_swing = True
        self._swing_start_time = reading.timestamp
        self._swing_readings = [reading]
    
    def _end_swing_detection(self) -> None:
        """Process completed swing and classify it."""
        if not self._swing_readings:
            self._reset_swing_detection()
            return
        
        # Extract features from swing data
        features = self._extract_swing_features(self._swing_readings)
        
        # Classify swing (will be implemented in subtask 6.2)
        swing_event = self._classify_swing(features)
        
        if swing_event:
            # Notify callbacks
            self._notify_callbacks(swing_event)
        
        # Reset for next swing
        self._reset_swing_detection()
    
    def _reset_swing_detection(self) -> None:
        """Reset swing detection state."""
        self._in_swing = False
        self._swing_start_time = None
        self._swing_readings = []
    
    def _extract_swing_features(self, readings: List[IMUReading]) -> SwingFeatures:
        """Extract features from swing IMU data.
        
        Args:
            readings: List of IMU readings during swing
            
        Returns:
            Extracted swing features
        """
        if not readings:
            return SwingFeatures(
                peak_acceleration=0.0,
                peak_angular_velocity=0.0,
                swing_duration=0.0,
                impact_detected=False,
                timestamp=time.time()
            )
        
        # Calculate acceleration magnitudes
        accel_magnitudes = [
            np.sqrt(r.accel_x**2 + r.accel_y**2 + r.accel_z**2)
            for r in readings
        ]
        
        # Calculate angular velocity magnitudes
        gyro_magnitudes = [
            np.sqrt(r.gyro_x**2 + r.gyro_y**2 + r.gyro_z**2)
            for r in readings
        ]
        
        # Extract peak values
        peak_acceleration = max(accel_magnitudes)
        peak_angular_velocity = max(gyro_magnitudes)
        
        # Calculate swing duration
        swing_duration = readings[-1].timestamp - readings[0].timestamp
        
        # Detect impact (sharp acceleration spike followed by deceleration)
        impact_detected = self._detect_impact(accel_magnitudes)
        
        return SwingFeatures(
            peak_acceleration=peak_acceleration,
            peak_angular_velocity=peak_angular_velocity,
            swing_duration=swing_duration,
            impact_detected=impact_detected,
            timestamp=readings[-1].timestamp
        )
    
    def _detect_impact(self, accel_magnitudes: List[float]) -> bool:
        """Detect ball impact from acceleration pattern.
        
        Impact is characterized by a sharp spike in acceleration
        followed by rapid deceleration.
        
        Args:
            accel_magnitudes: List of acceleration magnitudes
            
        Returns:
            True if impact detected, False otherwise
        """
        if len(accel_magnitudes) < 10:
            return False
        
        # Convert to numpy array for easier processing
        accels = np.array(accel_magnitudes)
        
        # Find peak acceleration
        peak_idx = np.argmax(accels)
        
        # Check if peak is not at edges
        if peak_idx < 5 or peak_idx > len(accels) - 5:
            return False
        
        # Check for rapid rise before peak
        pre_peak = accels[peak_idx - 5:peak_idx]
        rise_rate = (accels[peak_idx] - pre_peak[0]) / 5
        
        # Check for rapid fall after peak
        post_peak = accels[peak_idx:peak_idx + 5]
        fall_rate = (accels[peak_idx] - post_peak[-1]) / 5
        
        # Impact has sharp rise and fall
        IMPACT_THRESHOLD = 10.0  # m/s^2 per sample
        return rise_rate > IMPACT_THRESHOLD and fall_rate > IMPACT_THRESHOLD
    
    def _classify_swing(self, features: SwingFeatures) -> Optional[SwingEvent]:
        """Classify swing as full swing or practice swing.
        
        Uses ML classifier (Random Forest) to distinguish between full swings
        and practice swings based on extracted features. The classifier looks
        for ball contact indicators in the IMU data.
        
        Args:
            features: Extracted swing features
            
        Returns:
            SwingEvent if swing is classified, None otherwise
        """
        # Prepare feature vector for classifier
        feature_vector = np.array([
            features.peak_acceleration,
            features.peak_angular_velocity,
            features.swing_duration,
            1.0 if features.impact_detected else 0.0
        ]).reshape(1, -1)
        
        try:
            if self._classifier is not None:
                # Use trained classifier
                prediction = self._classifier.predict(feature_vector)[0]
                confidence = self._classifier.predict_proba(feature_vector)[0]
                
                swing_type = 'FULL_SWING' if prediction == 1 else 'PRACTICE_SWING'
                confidence_score = float(max(confidence))
            else:
                # Fallback to heuristic-based classification
                swing_type, confidence_score = self._heuristic_classification(features)
            
            return SwingEvent(
                timestamp=int(features.timestamp),
                swing_type=swing_type,
                peak_acceleration=features.peak_acceleration,
                swing_duration=features.swing_duration,
                confidence=confidence_score
            )
            
        except Exception as e:
            print(f"Classification error: {e}")
            # Fallback to heuristic
            swing_type, confidence_score = self._heuristic_classification(features)
            return SwingEvent(
                timestamp=int(features.timestamp),
                swing_type=swing_type,
                peak_acceleration=features.peak_acceleration,
                swing_duration=features.swing_duration,
                confidence=confidence_score
            )
    
    def _heuristic_classification(self, features: SwingFeatures) -> tuple[str, float]:
        """Heuristic-based swing classification fallback.
        
        Uses simple rules based on impact detection and swing characteristics.
        
        Args:
            features: Extracted swing features
            
        Returns:
            Tuple of (swing_type, confidence)
        """
        # Full swings have:
        # 1. Impact detected
        # 2. Higher peak acceleration (> 30 m/s^2)
        # 3. Typical duration (0.5-1.5 seconds)
        
        if features.impact_detected:
            # Strong indicator of full swing
            if features.peak_acceleration > 30.0:
                return 'FULL_SWING', 0.85
            else:
                return 'FULL_SWING', 0.70
        else:
            # No impact - likely practice swing
            # But could be a mishit
            if features.peak_acceleration > 35.0:
                # Very high acceleration without impact - possible mishit
                return 'FULL_SWING', 0.60
            else:
                return 'PRACTICE_SWING', 0.75
    
    def _load_classifier(self, classifier_path: Optional[str]) -> Optional[Any]:
        """Load trained swing classifier model.
        
        Args:
            classifier_path: Path to pickled classifier model
            
        Returns:
            Loaded classifier or None if not available
        """
        if classifier_path is None or not os.path.exists(classifier_path):
            return None
        
        try:
            with open(classifier_path, 'rb') as f:
                classifier = pickle.load(f)
            return classifier
        except Exception as e:
            print(f"Failed to load classifier: {e}")
            return None
    
    def train_classifier(
        self,
        training_data: List[Dict[str, Any]],
        save_path: Optional[str] = None
    ) -> None:
        """Train swing classifier on labeled data.
        
        This method trains a Random Forest classifier to distinguish between
        full swings and practice swings based on IMU features.
        
        Args:
            training_data: List of dicts with 'features' and 'label' keys
                          label: 1 for FULL_SWING, 0 for PRACTICE_SWING
            save_path: Optional path to save trained model
        """
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import accuracy_score, classification_report
        except ImportError:
            print("scikit-learn not installed. Cannot train classifier.")
            return
        
        # Extract features and labels
        X = []
        y = []
        
        for sample in training_data:
            features = sample['features']
            X.append([
                features['peak_acceleration'],
                features['peak_angular_velocity'],
                features['swing_duration'],
                1.0 if features['impact_detected'] else 0.0
            ])
            y.append(sample['label'])
        
        X = np.array(X)
        y = np.array(y)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train Random Forest classifier
        classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        classifier.fit(X_train, y_train)
        
        # Evaluate
        y_pred = classifier.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"Classifier accuracy: {accuracy:.2f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred, 
                                   target_names=['PRACTICE_SWING', 'FULL_SWING']))
        
        # Save classifier
        self._classifier = classifier
        
        if save_path:
            with open(save_path, 'wb') as f:
                pickle.dump(classifier, f)
            print(f"Classifier saved to {save_path}")
    
    def _notify_callbacks(self, swing_event: SwingEvent) -> None:
        """Notify all registered callbacks of swing detection.
        
        Args:
            swing_event: Detected swing event
        """
        with self._lock:
            callbacks = self._callbacks.copy()
        
        for callback in callbacks:
            try:
                callback(swing_event)
            except Exception as e:
                print(f"Error in swing detection callback: {e}")
