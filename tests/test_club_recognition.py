"""Unit tests for club recognition service."""

import pytest
from unittest.mock import Mock, MagicMock, patch
import numpy as np

from ar_golf_tracker.shared.models import ClubType
from ar_golf_tracker.ar_glasses.club_recognition import ClubRecognitionService


class TestClubRecognitionService:
    """Test suite for ClubRecognitionService."""
    
    def test_initialization(self):
        """Test service initialization with default parameters."""
        service = ClubRecognitionService()
        
        assert service.confidence_threshold == ClubRecognitionService.DEFAULT_CONFIDENCE_THRESHOLD
        assert service.camera_index == 0
        assert service._current_club is None
        assert service._current_confidence == 0.0
        assert not service._is_running
    
    def test_initialization_with_custom_params(self):
        """Test service initialization with custom parameters."""
        service = ClubRecognitionService(
            model_path="custom_model.pt",
            confidence_threshold=0.75,
            camera_index=1
        )
        
        assert service.model_path == "custom_model.pt"
        assert service.confidence_threshold == 0.75
        assert service.camera_index == 1
    
    def test_callback_registration(self):
        """Test registering detection callbacks."""
        service = ClubRecognitionService()
        callback = Mock()
        
        service.on_club_detected(callback)
        
        assert callback in service._detection_callbacks
    
    def test_get_current_club_none_initially(self):
        """Test getting current club returns None initially."""
        service = ClubRecognitionService()
        
        assert service.get_current_club() is None
        assert service.get_current_confidence() == 0.0
    
    def test_is_low_confidence(self):
        """Test low confidence detection."""
        service = ClubRecognitionService()
        
        # No detection
        service._current_confidence = 0.0
        assert not service.is_low_confidence()
        
        # Below low threshold
        service._current_confidence = 0.50
        assert not service.is_low_confidence()
        
        # In low confidence range
        service._current_confidence = 0.70
        assert service.is_low_confidence()
        
        # Above high threshold
        service._current_confidence = 0.90
        assert not service.is_low_confidence()
    
    def test_select_best_detection_single(self):
        """Test selecting best detection with single club."""
        service = ClubRecognitionService()
        
        detections = [
            (ClubType.DRIVER, 0.95, (100, 100, 200, 200))
        ]
        frame_shape = (480, 640, 3)
        
        result = service._select_best_detection(detections, frame_shape)
        
        assert result == (ClubType.DRIVER, 0.95)
    
    def test_select_best_detection_multiple_clubs(self):
        """Test selecting club closest to grip position when multiple detected."""
        service = ClubRecognitionService()
        
        # Frame: 480h x 640w
        # Grip position: (320, 384) - center-bottom
        frame_shape = (480, 640, 3)
        
        detections = [
            # Club far from grip (top-left)
            (ClubType.DRIVER, 0.90, (50, 50, 150, 150)),
            # Club close to grip (center-bottom)
            (ClubType.IRON_7, 0.85, (280, 350, 360, 420)),
            # Club far from grip (top-right)
            (ClubType.PUTTER, 0.88, (500, 50, 600, 150)),
        ]
        
        result = service._select_best_detection(detections, frame_shape)
        
        # Should select IRON_7 as it's closest to grip position
        assert result == (ClubType.IRON_7, 0.85)
    
    def test_select_best_detection_empty(self):
        """Test selecting best detection with no detections."""
        service = ClubRecognitionService()
        
        result = service._select_best_detection([], (480, 640, 3))
        
        assert result is None
    
    def test_update_detection_triggers_callback(self):
        """Test that updating detection triggers registered callbacks."""
        service = ClubRecognitionService()
        callback = Mock()
        service.on_club_detected(callback)
        
        # Update with new detection
        service._update_detection(ClubType.DRIVER, 0.90)
        
        # Callback should be called
        callback.assert_called_once_with(ClubType.DRIVER, 0.90)
        
        # State should be updated
        assert service.get_current_club() == ClubType.DRIVER
        assert service.get_current_confidence() == 0.90
    
    def test_update_detection_no_callback_on_none(self):
        """Test that callbacks are not triggered when detection is None."""
        service = ClubRecognitionService()
        callback = Mock()
        service.on_club_detected(callback)
        
        # Update with None
        service._update_detection(None, 0.0)
        
        # Callback should not be called
        callback.assert_not_called()
    
    def test_update_detection_no_callback_on_same_detection(self):
        """Test that callbacks are not triggered for unchanged detections."""
        service = ClubRecognitionService()
        callback = Mock()
        service.on_club_detected(callback)
        
        # First detection
        service._update_detection(ClubType.DRIVER, 0.90)
        callback.reset_mock()
        
        # Same detection (within 0.05 threshold)
        service._update_detection(ClubType.DRIVER, 0.91)
        
        # Callback should not be called
        callback.assert_not_called()
    
    def test_extract_detections_filters_by_confidence(self):
        """Test that low confidence detections are filtered out."""
        service = ClubRecognitionService()
        
        # Mock YOLO results with tensor-like objects
        mock_tensor1 = Mock()
        mock_tensor1.cpu.return_value.numpy.return_value = np.array([100, 100, 200, 200])
        
        mock_box1 = Mock()
        mock_box1.cls = [0]  # DRIVER
        mock_box1.conf = [0.95]  # High confidence
        mock_box1.xyxy = [mock_tensor1]
        
        mock_tensor2 = Mock()
        mock_tensor2.cpu.return_value.numpy.return_value = np.array([300, 300, 400, 400])
        
        mock_box2 = Mock()
        mock_box2.cls = [1]  # WOOD_3
        mock_box2.conf = [0.50]  # Below threshold
        mock_box2.xyxy = [mock_tensor2]
        
        mock_result = Mock()
        mock_result.boxes = [mock_box1, mock_box2]
        
        detections = service._extract_detections([mock_result])
        
        # Only high confidence detection should be included
        assert len(detections) == 1
        assert detections[0][0] == ClubType.DRIVER
        assert detections[0][1] == 0.95
    
    def test_class_id_mapping_covers_all_clubs(self):
        """Test that class ID mapping includes all club types."""
        # Verify all 17 club types are mapped
        assert len(ClubRecognitionService.CLASS_ID_TO_CLUB_TYPE) == 17
        
        # Verify all ClubType enum values are present
        mapped_clubs = set(ClubRecognitionService.CLASS_ID_TO_CLUB_TYPE.values())
        all_clubs = set(ClubType)
        
        assert mapped_clubs == all_clubs
    
    def test_target_fps_configuration(self):
        """Test that target FPS is configured correctly for power saving."""
        assert ClubRecognitionService.TARGET_FPS == 5
        assert ClubRecognitionService.FRAME_INTERVAL == 0.2  # 1/5 second
