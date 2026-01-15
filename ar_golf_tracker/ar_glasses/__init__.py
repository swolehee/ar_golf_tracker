"""AR glasses edge device application modules."""

from ar_golf_tracker.ar_glasses.club_recognition import (
    ClubRecognitionService,
)
from ar_golf_tracker.ar_glasses.swing_detection import (
    SwingDetectionService,
    SwingEvent,
    SwingFeatures,
    IMUReading,
)
from ar_golf_tracker.ar_glasses.gps_tracking import (
    GPSTrackingService,
)
from ar_golf_tracker.ar_glasses.distance_calculator import (
    DistanceCalculationService,
)
from ar_golf_tracker.ar_glasses.shot_manager import (
    ShotManager,
)
from ar_golf_tracker.ar_glasses.shot_recorder import (
    ShotRecorder,
)
from ar_golf_tracker.ar_glasses.database import (
    LocalDatabase,
)

__all__ = [
    'ClubRecognitionService',
    'SwingDetectionService',
    'SwingEvent',
    'SwingFeatures',
    'IMUReading',
    'GPSTrackingService',
    'DistanceCalculationService',
    'ShotManager',
    'ShotRecorder',
    'LocalDatabase',
]
