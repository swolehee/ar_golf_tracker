"""Club recognition service using YOLO object detection."""

import time
from typing import Optional, Callable, List, Tuple
from pathlib import Path
import threading
import queue

try:
    from ultralytics import YOLO
    import cv2
    import numpy as np
except ImportError:
    # Allow module to load even if dependencies not installed
    YOLO = None
    cv2 = None
    np = None

from ar_golf_tracker.shared.models import ClubType


class ClubRecognitionService:
    """
    Service for recognizing golf clubs using YOLO object detection.
    
    Processes camera feed at 5 FPS to identify club types with confidence scoring.
    Supports YOLOv8 or YOLOv11 models trained on golf club dataset.
    """
    
    # Target processing rate (5 FPS for power saving)
    TARGET_FPS = 5
    FRAME_INTERVAL = 1.0 / TARGET_FPS
    
    # Confidence threshold for club detection
    DEFAULT_CONFIDENCE_THRESHOLD = 0.85
    LOW_CONFIDENCE_THRESHOLD = 0.60
    
    # Mapping from YOLO class IDs to ClubType enum
    # This would be configured based on the trained model
    CLASS_ID_TO_CLUB_TYPE = {
        0: ClubType.DRIVER,
        1: ClubType.WOOD_3,
        2: ClubType.WOOD_5,
        3: ClubType.HYBRID_3,
        4: ClubType.HYBRID_4,
        5: ClubType.HYBRID_5,
        6: ClubType.IRON_3,
        7: ClubType.IRON_4,
        8: ClubType.IRON_5,
        9: ClubType.IRON_6,
        10: ClubType.IRON_7,
        11: ClubType.IRON_8,
        12: ClubType.IRON_9,
        13: ClubType.PITCHING_WEDGE,
        14: ClubType.SAND_WEDGE,
        15: ClubType.LOB_WEDGE,
        16: ClubType.PUTTER,
    }
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
        camera_index: int = 0
    ):
        """
        Initialize the club recognition service.
        
        Args:
            model_path: Path to trained YOLO model weights. If None, uses default.
            confidence_threshold: Minimum confidence for club detection (0.0-1.0)
            camera_index: Camera device index (default 0 for primary camera)
        """
        if YOLO is None or cv2 is None:
            raise ImportError(
                "ultralytics and opencv-python are required. "
                "Install with: pip install ultralytics opencv-python"
            )
        
        self.model_path = model_path or "yolov8n.pt"  # Default to YOLOv8 nano
        self.confidence_threshold = confidence_threshold
        self.camera_index = camera_index
        
        # YOLO model (loaded on start)
        self.model: Optional[YOLO] = None
        
        # Camera capture
        self.camera: Optional[cv2.VideoCapture] = None
        
        # Recognition state
        self._is_running = False
        self._recognition_thread: Optional[threading.Thread] = None
        self._frame_queue: queue.Queue = queue.Queue(maxsize=2)
        
        # Current detected club
        self._current_club: Optional[ClubType] = None
        self._current_confidence: float = 0.0
        self._last_detection_time: float = 0.0
        
        # Callbacks
        self._detection_callbacks: List[Callable[[ClubType, float], None]] = []
    
    def start_recognition(self) -> None:
        """
        Start the club recognition service.
        
        Loads the YOLO model, opens camera feed, and begins processing frames
        at 5 FPS in a background thread.
        """
        if self._is_running:
            return
        
        # Load YOLO model
        self.model = YOLO(self.model_path)
        
        # Open camera
        self.camera = cv2.VideoCapture(self.camera_index)
        if not self.camera.isOpened():
            raise RuntimeError(f"Failed to open camera {self.camera_index}")
        
        # Start recognition thread
        self._is_running = True
        self._recognition_thread = threading.Thread(
            target=self._recognition_loop,
            daemon=True
        )
        self._recognition_thread.start()
    
    def stop_recognition(self) -> None:
        """
        Stop the club recognition service.
        
        Stops frame processing, releases camera, and cleans up resources.
        """
        if not self._is_running:
            return
        
        self._is_running = False
        
        # Wait for thread to finish
        if self._recognition_thread:
            self._recognition_thread.join(timeout=2.0)
        
        # Release camera
        if self.camera:
            self.camera.release()
            self.camera = None
        
        # Clear state
        self._current_club = None
        self._current_confidence = 0.0
    
    def on_club_detected(
        self,
        callback: Callable[[ClubType, float], None]
    ) -> None:
        """
        Register a callback for club detection events.
        
        Args:
            callback: Function called with (club_type, confidence) when club detected
        """
        self._detection_callbacks.append(callback)
    
    def get_current_club(self) -> Optional[ClubType]:
        """
        Get the currently detected club type.
        
        Returns:
            ClubType if a club is currently detected, None otherwise
        """
        return self._current_club
    
    def get_current_confidence(self) -> float:
        """
        Get the confidence score of the current detection.
        
        Returns:
            Confidence score (0.0-1.0), or 0.0 if no club detected
        """
        return self._current_confidence
    
    def _recognition_loop(self) -> None:
        """
        Main recognition loop running in background thread.
        
        Captures frames at 5 FPS and processes them for club detection.
        """
        last_frame_time = 0.0
        
        while self._is_running:
            current_time = time.time()
            
            # Throttle to 5 FPS
            if current_time - last_frame_time < self.FRAME_INTERVAL:
                time.sleep(0.01)  # Small sleep to avoid busy waiting
                continue
            
            last_frame_time = current_time
            
            # Capture frame
            ret, frame = self.camera.read()
            if not ret:
                continue
            
            # Process frame for club detection
            self._process_frame(frame)
    
    def _process_frame(self, frame: np.ndarray) -> None:
        """
        Process a single frame for club detection.
        
        Args:
            frame: Camera frame as numpy array (BGR format)
        """
        # Run YOLO inference
        results = self.model(frame, verbose=False)
        
        # Extract detections
        detections = self._extract_detections(results)
        
        if not detections:
            # No clubs detected
            self._update_detection(None, 0.0)
            return
        
        # Handle multiple detections (select closest to grip position)
        best_detection = self._select_best_detection(detections, frame.shape)
        
        if best_detection:
            club_type, confidence = best_detection
            self._update_detection(club_type, confidence)
    
    def _extract_detections(
        self,
        results
    ) -> List[Tuple[ClubType, float, Tuple[float, float, float, float]]]:
        """
        Extract club detections from YOLO results.
        
        Args:
            results: YOLO inference results
            
        Returns:
            List of (club_type, confidence, bbox) tuples
        """
        detections = []
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Get class ID and confidence
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                
                # Filter by confidence threshold
                if confidence < self.LOW_CONFIDENCE_THRESHOLD:
                    continue
                
                # Map class ID to club type
                if class_id not in self.CLASS_ID_TO_CLUB_TYPE:
                    continue
                
                club_type = self.CLASS_ID_TO_CLUB_TYPE[class_id]
                
                # Get bounding box (x1, y1, x2, y2)
                bbox = box.xyxy[0].cpu().numpy()
                
                detections.append((club_type, confidence, tuple(bbox)))
        
        return detections
    
    def _select_best_detection(
        self,
        detections: List[Tuple[ClubType, float, Tuple[float, float, float, float]]],
        frame_shape: Tuple[int, int, int]
    ) -> Optional[Tuple[ClubType, float]]:
        """
        Select the best detection when multiple clubs are visible.
        
        Uses heuristic: club closest to center-bottom of frame (grip position).
        
        Args:
            detections: List of (club_type, confidence, bbox) tuples
            frame_shape: Frame dimensions (height, width, channels)
            
        Returns:
            (club_type, confidence) tuple for best detection, or None
        """
        if not detections:
            return None
        
        if len(detections) == 1:
            club_type, confidence, _ = detections[0]
            return (club_type, confidence)
        
        # Grip position heuristic: center-bottom of frame
        frame_height, frame_width = frame_shape[:2]
        grip_x = frame_width / 2
        grip_y = frame_height * 0.8  # 80% down from top
        
        # Find detection closest to grip position
        best_detection = None
        min_distance = float('inf')
        
        for club_type, confidence, bbox in detections:
            # Calculate bbox center
            x1, y1, x2, y2 = bbox
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            
            # Calculate distance to grip position
            distance = ((center_x - grip_x) ** 2 + (center_y - grip_y) ** 2) ** 0.5
            
            if distance < min_distance:
                min_distance = distance
                best_detection = (club_type, confidence)
        
        return best_detection
    
    def _update_detection(
        self,
        club_type: Optional[ClubType],
        confidence: float
    ) -> None:
        """
        Update current detection state and notify callbacks.
        
        Args:
            club_type: Detected club type, or None if no detection
            confidence: Detection confidence score
        """
        # Check if detection changed
        detection_changed = (
            club_type != self._current_club or
            abs(confidence - self._current_confidence) > 0.05
        )
        
        # Update state
        self._current_club = club_type
        self._current_confidence = confidence
        self._last_detection_time = time.time()
        
        # Notify callbacks if detection changed and confidence is sufficient
        if detection_changed and club_type is not None:
            for callback in self._detection_callbacks:
                try:
                    callback(club_type, confidence)
                except Exception as e:
                    # Log error but don't crash recognition loop
                    print(f"Error in detection callback: {e}")
    
    def is_low_confidence(self) -> bool:
        """
        Check if current detection has low confidence.
        
        Returns:
            True if confidence is below high threshold but above minimum
        """
        return (
            self.LOW_CONFIDENCE_THRESHOLD <= self._current_confidence < 
            self.confidence_threshold
        )
    
    def __enter__(self):
        """Context manager entry."""
        self.start_recognition()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_recognition()
